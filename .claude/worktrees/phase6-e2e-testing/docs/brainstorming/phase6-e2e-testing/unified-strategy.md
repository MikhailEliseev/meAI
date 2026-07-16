# Unified E2E Testing Strategy

**Date:** 2026-05-14  
**Status:** ✅ Completed - Synthesized from 4 expert analyses  
**Duration:** 40 minutes total brainstorming

---

## Executive Summary

Unified strategy for E2E testing of meAI's three-layer event-driven architecture (Operator → Magisters → Subagents) based on findings from 4 expert analyses:

1. **API Integration Specialist** - VCR pattern, zero-cost testing, resilience patterns
2. **Performance Engineer** - Parallel execution, metrics, load testing
3. **Event Systems Expert** - Async patterns, event flow tracking, error propagation
4. **Testing Architect** - Fixtures, test organization, implementation roadmap

**Key Principles:**
- **Zero-Cost Testing:** VCR.py для replay API calls (запись 1 раз, replay бесконечно)
- **Isolation:** Каждый тест независим (in-memory DB, отдельный Event Bus)
- **Event Flow Tracking:** EventFlowTracker + correlation_id для отслеживания цепочек
- **Performance Validation:** Parallel execution (>= 2.5x speedup), < 35s E2E
- **Comprehensive Coverage:** Unit (30+) + Integration (25+) + E2E (15+) = 70+ tests

---

## 1. Core Testing Infrastructure

### 1.1 VCR Pattern for API Mocking (API Integration Specialist)

**Problem:** Real API calls дорогие ($0.10-0.50 per test) и медленные (5-30s).

**Solution:** pytest-vcr для записи/воспроизведения API responses.

```python
# AIM/tests/conftest.py

import pytest
from pathlib import Path

CASSETTES_DIR = Path(__file__).parent / "cassettes"

@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for zero-cost API testing"""
    return {
        "cassette_library_dir": str(CASSETTES_DIR),
        "record_mode": "once",  # Record once, replay forever
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "filter_headers": [("authorization", "REDACTED"), ("x-api-key", "REDACTED")],
        "serializer": "yaml",
    }

# Usage in tests
@pytest.mark.vcr
async def test_semrush_keyword_expansion():
    """Test with VCR - zero cost after first run"""
    client = SEMrushClient(api_key="test_key")
    result = await client.expand_keywords("dental implants")
    assert len(result) >= 100
```

**Cassette Organization:**
```
AIM/tests/cassettes/
├── semrush/
│   ├── keyword_expansion_success.yaml
│   ├── budget_guard_triggered.yaml
│   └── zero_volume_retry.yaml
├── ahrefs/
│   ├── keyword_expansion_fallback.yaml
│   └── difficulty_normalization.yaml
├── ga4/
│   └── fetch_metrics.yaml
└── yandex_metrica/
    └── fetch_traffic.yaml
```

**Benefits:**
- ✅ Zero cost after first recording
- ✅ Fast execution (< 5s vs 30s with real APIs)
- ✅ Deterministic results (no API flakiness)
- ✅ Offline testing (no network required)

### 1.2 Event Flow Tracking (Event Systems Expert)

**Problem:** Async event chains сложно отслеживать и проверять.

**Solution:** EventFlowTracker с asyncio.Event для синхронизации.

```python
# AIM/tests/helpers/event_flow_tracker.py

import asyncio
from dataclasses import dataclass, field
from meai.events.base import BaseEvent

@dataclass
class EventFlowTracker:
    """Tracks event flow through correlation chains"""
    
    events: dict[str, list[BaseEvent]] = field(default_factory=dict)
    completion_events: dict[str, asyncio.Event] = field(default_factory=dict)
    expected_types: dict[str, set[str]] = field(default_factory=dict)
    
    def track_correlation(self, correlation_id: str, expected_event_types: list[str]):
        """Start tracking a correlation chain"""
        self.events[correlation_id] = []
        self.completion_events[correlation_id] = asyncio.Event()
        self.expected_types[correlation_id] = set(expected_event_types)
    
    def record_event(self, event: BaseEvent):
        """Record event in correlation chain"""
        if event.correlation_id in self.events:
            self.events[event.correlation_id].append(event)
            
            # Check if all expected events received
            received_types = {e.type for e in self.events[event.correlation_id]}
            if received_types >= self.expected_types[event.correlation_id]:
                self.completion_events[event.correlation_id].set()
    
    async def wait_for_completion(
        self, 
        correlation_id: str, 
        timeout: float = 5.0
    ) -> list[BaseEvent]:
        """Wait for correlation chain to complete"""
        await asyncio.wait_for(
            self.completion_events[correlation_id].wait(),
            timeout=timeout
        )
        return sorted(self.events[correlation_id], key=lambda e: e.timestamp)
```

**Usage in E2E tests:**
```python
@pytest.mark.asyncio
async def test_operator_to_subagent_flow(operator, event_bus):
    """Test complete flow: Operator → Magister → Subagent"""
    
    tracker = EventFlowTracker()
    correlation_id = str(uuid4())
    
    # Track expected flow
    tracker.track_correlation(
        correlation_id,
        expected_event_types=["task.created", "task.delegated", "task.completed"]
    )
    
    # Subscribe to events
    async def record_handler(event: BaseEvent):
        tracker.record_event(event)
    
    event_bus.subscribe("task.created", record_handler)
    event_bus.subscribe("task.delegated", record_handler)
    event_bus.subscribe("task.completed", record_handler)
    
    # Execute workflow
    task = Task(id=correlation_id, goal="Analyze SEO")
    await operator.receive_task(task)
    
    # Wait for completion
    events = await tracker.wait_for_completion(correlation_id, timeout=10.0)
    
    # Verify flow
    assert len(events) == 3
    assert events[0].type == "task.created"
    assert events[1].type == "task.delegated"
    assert events[2].type == "task.completed"
```

### 1.3 Test Fixtures Architecture (Testing Architect)

**Problem:** Тесты должны быть изолированы, но переиспользовать компоненты.

**Solution:** Fixture hierarchy с function-scoped изоляцией.

```python
# AIM/tests/conftest.py

@pytest.fixture
async def event_bus():
    """Isolated Event Bus per test"""
    bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await bus.initialize()
    yield bus
    await bus.close()

@pytest.fixture
async def event_store(event_bus):
    """Isolated Event Store per test"""
    store = EventStore(database_url="sqlite+aiosqlite:///:memory:")
    await store.initialize()
    event_bus.set_event_store(store)
    yield store
    await store.close()

@pytest.fixture
async def operator(event_bus, event_store):
    """Operator with isolated dependencies"""
    op = Operator(
        operator_id="test-operator-1",
        event_bus=event_bus,
        event_store=event_store,
    )
    await op.initialize()
    yield op
    await op.shutdown()

@pytest.fixture
def seo_magister():
    """SEO Magister instance"""
    return SEOMagisterV2()

@pytest.fixture
def task_factory():
    """Factory for creating test tasks"""
    def _create(goal: str, priority: int = 2, **kwargs):
        return Task(
            task_id=f"task-{uuid4().hex[:8]}",
            source="user",
            goal=goal,
            priority=priority,
            status=TaskStatus.RECEIVED,
            **kwargs
        )
    return _create
```

**Fixture Hierarchy:**
```
Session Scope (shared):
  └─ vcr_config, test_data_dir

Function Scope (isolated per test):
  ├─ event_bus (in-memory)
  ├─ event_store (in-memory)
  ├─ database (in-memory SQLite)
  ├─ operator
  ├─ magisters (seo, content, ads, analytics)
  └─ subagents (keyword_research, onpage_optimizer, etc.)
```

### 1.4 Performance Metrics (Performance Engineer)

**Problem:** Как измерять и валидировать производительность?

**Solution:** Встроенные метрики + benchmarks.

```python
# AIM/tests/helpers/performance_metrics.py

import time
import psutil
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """Performance metrics for E2E tests"""
    
    start_time: float
    end_time: float
    peak_memory_mb: float
    cpu_percent: float
    
    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time
    
    def assert_within_limits(
        self,
        max_duration_s: float,
        max_memory_mb: float,
    ):
        """Assert metrics within acceptable limits"""
        assert self.duration_seconds <= max_duration_s, \
            f"Duration {self.duration_seconds:.2f}s exceeds limit {max_duration_s}s"
        assert self.peak_memory_mb <= max_memory_mb, \
            f"Memory {self.peak_memory_mb:.2f}MB exceeds limit {max_memory_mb}MB"


@pytest.fixture
def performance_tracker():
    """Track performance metrics during test"""
    process = psutil.Process()
    
    start_time = time.time()
    start_memory = process.memory_info().rss / 1024 / 1024
    
    yield
    
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024
    peak_memory = max(start_memory, end_memory)
    
    metrics = PerformanceMetrics(
        start_time=start_time,
        end_time=end_time,
        peak_memory_mb=peak_memory,
        cpu_percent=process.cpu_percent(),
    )
    
    return metrics
```

**Performance Benchmarks:**
- SEO Magister: < 30s, < 200 MB
- Content Magister: < 25s, < 150 MB
- Ads Magister: < 20s, < 100 MB
- Analytics Magister: < 15s, < 100 MB
- **All parallel: < 35s, speedup >= 2.5x**

---

## 2. Test Organization

### 2.1 Directory Structure

```
AIM/tests/
├── conftest.py                  # Global fixtures
├── fixtures/                    # Mock data
│   ├── keyword_data.py
│   ├── seo_reports.py
│   └── analytics_data.py
├── factories/                   # Data generators
│   ├── task_factory.py
│   └── event_factory.py
├── helpers/                     # Test utilities
│   ├── event_flow_tracker.py
│   ├── performance_metrics.py
│   └── event_assertions.py
├── cassettes/                   # VCR recordings
│   ├── semrush/
│   ├── ahrefs/
│   ├── ga4/
│   └── yandex_metrica/
├── unit/                        # Unit tests (30+)
│   ├── test_event_bus.py
│   ├── test_event_store.py
│   └── api_clients/
│       ├── test_semrush.py
│       └── test_ahrefs.py
├── integration/                 # Integration tests (25+)
│   ├── test_operator_magister.py
│   ├── test_magister_subagent.py
│   └── test_event_flow.py
└── e2e/                         # E2E tests (15+)
    ├── test_seo_workflow.py
    ├── test_content_workflow.py
    ├── test_ads_workflow.py
    └── test_multi_magister_parallel.py
```

### 2.2 Test Markers

```python
# pytest.ini

[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (medium speed)
    e2e: End-to-end tests (slow, full workflow)
    vcr: Tests using VCR for API mocking
    real_api: Tests requiring real API calls (expensive)
    slow: Tests taking > 5 seconds
    parallel: Tests for parallel execution validation
```

**Run strategies:**
```bash
# Fast feedback (unit only, < 10s)
pytest -m unit

# Pre-commit (unit + integration with VCR, < 30s)
pytest -m "unit or integration" -m "not real_api"

# Full suite (all tests, < 5 min)
pytest

# Performance tests only
pytest -m parallel

# Real API tests (expensive, CI only)
pytest -m real_api
```

---

## 3. Implementation Roadmap

### Phase 1: Infrastructure Setup (2h)

**Tasks:**
1. Create `AIM/tests/conftest.py` with base fixtures
2. Install pytest-vcr and configure
3. Create directory structure
4. Add pytest markers

**Deliverables:**
- ✅ Base fixtures (event_bus, event_store, operator)
- ✅ VCR configuration
- ✅ Directory structure
- ✅ pytest.ini with markers

### Phase 2: Event Flow Testing (3h)

**Tasks:**
1. Implement EventFlowTracker
2. Create event_bus fixtures
3. Write unit tests for Event Bus (priority, pub/sub)
4. Write integration tests for event flow

**Deliverables:**
- ✅ EventFlowTracker in tests/helpers/
- ✅ tests/unit/test_event_bus.py (10+ tests)
- ✅ tests/integration/test_event_flow.py (5+ tests)

### Phase 3: API Integration with VCR (3h)

**Tasks:**
1. Record cassettes for SEMrush, Ahrefs, GA4, Yandex
2. Create API client fixtures with VCR
3. Write unit tests for API clients
4. Test fallback chains (SEMrush → Ahrefs → Mock)

**Deliverables:**
- ✅ Cassettes in tests/cassettes/
- ✅ tests/unit/api_clients/ (15+ tests)
- ✅ Fallback chain tests

### Phase 4: Operator & Magister Tests (2h)

**Tasks:**
1. Create operator and magister fixtures
2. Write integration tests for Operator → Magister
3. Test task delegation and completion

**Deliverables:**
- ✅ Operator/Magister fixtures
- ✅ tests/integration/test_operator_magister.py (8+ tests)

### Phase 5: E2E Workflows (4h)

**Tasks:**
1. Write E2E test for SEO workflow
2. Write E2E test for Content workflow
3. Write E2E test for Ads workflow
4. Write E2E test for parallel Magisters

**Deliverables:**
- ✅ tests/e2e/test_seo_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_content_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_ads_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_multi_magister_parallel.py (3+ scenarios)

### Phase 6: Performance & Load Testing (2h)

**Tasks:**
1. Implement PerformanceMetrics tracker
2. Write parallel execution tests
3. Write load tests (10, 50, 100 concurrent tasks)
4. Validate performance benchmarks

**Deliverables:**
- ✅ PerformanceMetrics in tests/helpers/
- ✅ tests/e2e/test_performance.py (5+ tests)
- ✅ Performance benchmarks validated

### Phase 7: Documentation & CI (1h)

**Tasks:**
1. Write tests/README.md
2. Create GitHub Actions workflow
3. Setup coverage reporting

**Deliverables:**
- ✅ tests/README.md
- ✅ .github/workflows/tests.yml
- ✅ Coverage badge

**Total Time:** 17 hours

---

## 4. Success Criteria

### 4.1 Test Coverage

- ✅ **Unit tests:** 30+ tests (Event Bus, Event Store, API clients)
- ✅ **Integration tests:** 25+ tests (Operator ↔ Magister ↔ Subagent)
- ✅ **E2E tests:** 15+ tests (full workflows)
- ✅ **Total:** 70+ tests

### 4.2 Performance

- ✅ **Parallel speedup:** >= 2.5x for 4 Magisters
- ✅ **E2E duration:** < 35s real, < 5s with VCR
- ✅ **Memory:** < 500 MB peak
- ✅ **Throughput:** >= 2 workflows/sec

### 4.3 Quality

- ✅ **Pass rate:** 100%
- ✅ **Isolation:** Each test independent
- ✅ **Deterministic:** Reproducible results
- ✅ **Fast feedback:** Unit tests < 10s

### 4.4 Cost

- ✅ **API costs:** $0 after initial cassette recording
- ✅ **CI time:** < 5 min for full suite
- ✅ **Developer time:** < 30s for pre-commit checks

---

## 5. Key Patterns Summary

### 5.1 VCR Pattern (API Integration)

```python
@pytest.mark.vcr
async def test_api_call():
    """Zero-cost API testing with VCR"""
    result = await api_client.call()
    assert result is not None
```

### 5.2 Event Flow Pattern (Event Systems)

```python
async def test_event_flow():
    """Track event correlation chains"""
    tracker = EventFlowTracker()
    tracker.track_correlation(correlation_id, ["created", "completed"])
    # ... execute workflow ...
    events = await tracker.wait_for_completion(correlation_id)
    assert len(events) == 2
```

### 5.3 Performance Pattern (Performance)

```python
async def test_performance(performance_tracker):
    """Validate performance benchmarks"""
    # ... execute workflow ...
    metrics = performance_tracker
    metrics.assert_within_limits(max_duration_s=35, max_memory_mb=500)
```

### 5.4 Fixture Pattern (Testing Architect)

```python
@pytest.fixture
async def isolated_component():
    """Isolated component per test"""
    component = Component()
    await component.initialize()
    yield component
    await component.cleanup()
```

---

## 6. Next Steps

1. **Approve Strategy** - Review and approve unified strategy
2. **Phase 1 Execution** - Start with infrastructure setup (2h)
3. **Iterative Implementation** - Execute phases 2-7 (15h)
4. **Validation** - Verify success criteria met
5. **Documentation** - Complete tests/README.md

**Estimated Total:** 17 hours implementation + 2 hours validation = **19 hours**

**Priority:** High (blocks Phase 6 completion)

---

**Status:** ✅ Strategy Complete - Ready for Implementation
