# Phase 6: End-to-End Integration Testing - Technical Specification

**Version:** 1.0  
**Date:** 2026-05-14  
**Status:** Draft  
**Governance:** Critical  
**Git Workflow:** solo_single_pr

---

## Executive Summary

This specification defines the implementation of comprehensive end-to-end (E2E) integration testing for meAI's three-layer event-driven architecture (Operator → Magisters → Subagents). The testing infrastructure will validate full workflows from user request to final result, including real API integrations, async event flow, error propagation, and parallel execution.

**Key Objectives:**
1. **Zero-Cost Testing** - VCR.py pattern for API replay (record once, replay forever)
2. **Event Flow Validation** - Track async event chains through correlation IDs
3. **Performance Benchmarks** - < 35s E2E, >= 2.5x parallel speedup
4. **Comprehensive Coverage** - 70+ tests (30 unit + 25 integration + 15 E2E)

**Success Criteria:**
- ✅ 100% test pass rate
- ✅ < 5s execution time with VCR
- ✅ $0 API costs after initial recording
- ✅ >= 2.5x speedup for parallel Magisters

**Estimated Effort:** 17 hours (7 phases)

---

## 1. Architecture Overview

### 1.1 System Under Test

```
┌─────────────────────────────────────────────────────────────┐
│                         Operator                            │
│  (Tactical Layer - Task Decomposition & Coordination)       │
└────────────────┬────────────────────────────────────────────┘
                 │ Event Bus (P0-P3 Priority)
                 ├──────────┬──────────┬──────────┬──────────┐
                 ▼          ▼          ▼          ▼          ▼
         ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
         │    SEO    │ │  Content  │ │    Ads    │ │ Analytics │
         │ Magister  │ │ Magister  │ │ Magister  │ │ Magister  │
         └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
               │             │             │             │
         Event Bus     Event Bus     Event Bus     Event Bus
               │             │             │             │
         ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
         │ Subagents │ │ Subagents │ │ Subagents │ │ Subagents │
         │  (P1-P3)  │ │  (P1-P3)  │ │  (P1-P3)  │ │  (P1-P3)  │
         └───────────┘ └───────────┘ └───────────┘ └───────────┘
              │             │             │             │
         ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
         │   API   │   │   API   │   │   API   │   │   API   │
         │ Clients │   │ Clients │   │ Clients │   │ Clients │
         └─────────┘   └─────────┘   └─────────┘   └─────────┘
              │             │             │             │
         SEMrush      OpenAI       Google Ads      GA4
         Ahrefs       Anthropic    Meta Ads        Yandex
```

**Key Components:**
- **Event Bus** - Priority-based async messaging (P0-P3)
- **Event Store** - Immutable audit log for event replay
- **Operator** - Task decomposition and Magister coordination
- **Magisters** - Domain-specific orchestrators (SEO, Content, Ads, Analytics)
- **Subagents** - Specialized execution units (keyword research, content generation, etc.)
- **API Clients** - External service integrations with resilience patterns

### 1.2 Testing Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    E2E Tests (15+)                          │
│  Full workflow: Operator → Magisters → Subagents → Result  │
│  - SEO workflow (keyword research → optimization)           │
│  - Content workflow (generation → editing → publishing)     │
│  - Ads workflow (campaign creation → optimization)          │
│  - Multi-Magister parallel execution                        │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│              Integration Tests (25+)                        │
│  Component interactions:                                    │
│  - Operator ↔ Magister communication                        │
│  - Magister ↔ Subagent delegation                           │
│  - Event Bus ↔ Event Store persistence                      │
│  - API Client ↔ Fallback chains                             │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│                  Unit Tests (30+)                           │
│  Individual components:                                     │
│  - Event Bus (priority queue, pub/sub)                      │
│  - Event Store (append, query, replay)                      │
│  - API Clients (request/response, retry, circuit breaker)   │
│  - Base classes (Agent, Magister, Subagent)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Testing Infrastructure

### 2.1 VCR Pattern for API Mocking

**Objective:** Zero-cost API testing after initial recording.

**Implementation:**

```python
# AIM/tests/conftest.py

import pytest
from pathlib import Path
import vcr

CASSETTES_DIR = Path(__file__).parent / "cassettes"
CASSETTES_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for zero-cost API testing"""
    return {
        # Storage
        "cassette_library_dir": str(CASSETTES_DIR),
        
        # Record mode: 'once' (record if missing, replay if exists)
        "record_mode": "once",
        
        # Match requests by: method, scheme, host, port, path, query
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        
        # Filter sensitive data
        "filter_headers": [
            ("authorization", "REDACTED"),
            ("x-api-key", "REDACTED"),
        ],
        "filter_query_parameters": [
            ("key", "REDACTED"),
            ("api_key", "REDACTED"),
        ],
        
        # Decode compressed responses
        "decode_compressed_response": True,
        
        # Allow playback repeats
        "allow_playback_repeats": True,
        
        # Serializer (yaml for readability)
        "serializer": "yaml",
    }

@pytest.fixture
def vcr_cassette_name(request):
    """Generate cassette name from test name"""
    parts = []
    
    if request.module:
        parts.append(request.module.__name__.split(".")[-1])
    
    if request.cls:
        parts.append(request.cls.__name__)
    
    parts.append(request.node.name)
    
    return "/".join(parts)
```

**Cassette Organization:**

```
AIM/tests/cassettes/
├── semrush/
│   ├── keyword_expansion_success.yaml
│   ├── budget_guard_triggered.yaml
│   ├── zero_volume_retry.yaml
│   └── pagination_handling.yaml
├── ahrefs/
│   ├── keyword_expansion_fallback.yaml
│   ├── difficulty_normalization.yaml
│   └── parent_topic_detection.yaml
├── ga4/
│   ├── fetch_metrics_success.yaml
│   ├── conversions_api.yaml
│   └── batch_requests.yaml
└── yandex_metrica/
    ├── fetch_traffic_success.yaml
    └── error_handling.yaml
```

**Usage Example:**

```python
@pytest.mark.vcr
async def test_semrush_keyword_expansion():
    """Test with VCR - zero cost after first run"""
    client = SEMrushClient(api_key="test_key")
    result = await client.expand_keywords("dental implants", max_keywords=100)
    
    assert len(result) >= 100
    assert result[0].keyword == "dental implants"
    assert result[0].volume > 0
```

**Benefits:**
- ✅ Zero cost after first recording
- ✅ Fast execution (< 5s vs 30s with real APIs)
- ✅ Deterministic results (no API flakiness)
- ✅ Offline testing (no network required)

### 2.2 Event Flow Tracking

**Objective:** Track async event chains through correlation IDs.

**Implementation:**

```python
# AIM/tests/helpers/event_flow_tracker.py

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Set
from uuid import UUID

from meai.events.base import BaseEvent

@dataclass
class EventFlowTracker:
    """Tracks event flow through correlation chains"""
    
    events: Dict[str, List[BaseEvent]] = field(default_factory=dict)
    completion_events: Dict[str, asyncio.Event] = field(default_factory=dict)
    expected_types: Dict[str, Set[str]] = field(default_factory=dict)
    
    def track_correlation(
        self, 
        correlation_id: str, 
        expected_event_types: List[str]
    ) -> None:
        """Start tracking a correlation chain
        
        Args:
            correlation_id: Correlation ID to track
            expected_event_types: List of event types expected in chain
        """
        self.events[correlation_id] = []
        self.completion_events[correlation_id] = asyncio.Event()
        self.expected_types[correlation_id] = set(expected_event_types)
    
    def record_event(self, event: BaseEvent) -> None:
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
    ) -> List[BaseEvent]:
        """Wait for correlation chain to complete
        
        Args:
            correlation_id: Correlation ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            List of events in chronological order
            
        Raises:
            asyncio.TimeoutError: If chain doesn't complete in time
        """
        await asyncio.wait_for(
            self.completion_events[correlation_id].wait(),
            timeout=timeout
        )
        return sorted(
            self.events[correlation_id],
            key=lambda e: e.timestamp
        )
    
    def get_flow_summary(self, correlation_id: str) -> List[tuple]:
        """Get event flow summary: (timestamp, type, source→target)"""
        events = self.events.get(correlation_id, [])
        return [
            (e.timestamp.isoformat(), e.type, f"{e.source}→{e.target}")
            for e in sorted(events, key=lambda e: e.timestamp)
        ]
```

**Usage Example:**

```python
@pytest.mark.asyncio
async def test_operator_to_subagent_flow(operator, event_bus):
    """Test complete flow: Operator → Magister → Subagent"""
    
    tracker = EventFlowTracker()
    correlation_id = str(uuid4())
    
    # Track expected flow
    tracker.track_correlation(
        correlation_id,
        expected_event_types=[
            "task.created",
            "task.delegated",
            "task.started",
            "task.completed"
        ]
    )
    
    # Subscribe to events
    async def record_handler(event: BaseEvent):
        tracker.record_event(event)
    
    for event_type in ["task.created", "task.delegated", "task.started", "task.completed"]:
        event_bus.subscribe(event_type, record_handler)
    
    # Execute workflow
    task = Task(
        id=correlation_id,
        goal="Analyze SEO for example.com",
        priority=1
    )
    await operator.receive_task(task)
    
    # Wait for completion
    events = await tracker.wait_for_completion(correlation_id, timeout=10.0)
    
    # Verify flow
    assert len(events) == 4
    assert events[0].type == "task.created"
    assert events[1].type == "task.delegated"
    assert events[2].type == "task.started"
    assert events[3].type == "task.completed"
    
    # Verify correlation chain
    assert all(e.correlation_id == correlation_id for e in events)
    
    # Verify reply chain
    assert events[1].reply_to == str(events[0].id)
    assert events[2].reply_to == str(events[1].id)
    assert events[3].reply_to == str(events[2].id)
```


### 2.3 Test Fixtures Architecture

**Objective:** Provide isolated, reusable test components.

**Fixture Hierarchy:**

```
Session Scope (shared across test session):
  ├─ vcr_config (VCR configuration)
  └─ test_data_dir (mock data directory)

Function Scope (isolated per test):
  ├─ event_bus (in-memory Event Bus)
  ├─ event_store (in-memory Event Store)
  ├─ database (in-memory SQLite)
  ├─ operator (Operator instance)
  ├─ magisters
  │   ├─ seo_magister
  │   ├─ content_magister
  │   ├─ ads_magister
  │   └─ analytics_magister
  └─ subagents
      ├─ keyword_research_agent
      ├─ onpage_optimizer_agent
      ├─ content_generator_agent
      └─ ... (20+ subagents)
```

**Implementation:**

```python
# AIM/tests/conftest.py

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from meai.events.event_bus import EventBus
from meai.events.event_store import EventStore
from meai.agents.operator import Operator
from aim.magisters.seo_magister_v2 import SEOMagisterV2
from aim.subagents.keyword_research import KeywordResearchAgent

# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
async def database():
    """Isolated in-memory database per test"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

# ============================================================================
# EVENT BUS FIXTURES
# ============================================================================

@pytest.fixture
async def event_bus(database):
    """Isolated Event Bus per test"""
    bus = EventBus(db_session=database)
    await bus.initialize()
    
    yield bus
    
    # Cleanup
    await bus.clear_all()
    await bus.close()

@pytest.fixture
async def event_store(database):
    """Isolated Event Store per test"""
    store = EventStore(db_session=database)
    await store.initialize()
    
    yield store
    
    # Cleanup
    await store.clear_all()
    await store.close()

# ============================================================================
# OPERATOR FIXTURES
# ============================================================================

@pytest.fixture
async def operator(event_bus, event_store, database):
    """Operator with isolated dependencies"""
    op = Operator(
        operator_id=f"test-operator-{uuid4().hex[:8]}",
        event_bus=event_bus,
        event_store=event_store,
        db_session=database,
    )
    await op.initialize()
    
    yield op
    
    await op.shutdown()

@pytest.fixture
async def operator_with_mock_magisters(operator):
    """Operator with mock magisters for isolation"""
    from unittest.mock import AsyncMock
    
    mock_seo = AsyncMock(spec=SEOMagisterV2)
    mock_content = AsyncMock()
    mock_ads = AsyncMock()
    mock_analytics = AsyncMock()
    
    operator.register_magister("seo", mock_seo)
    operator.register_magister("content", mock_content)
    operator.register_magister("ads", mock_ads)
    operator.register_magister("analytics", mock_analytics)
    
    yield operator

@pytest.fixture
async def operator_with_real_magisters(
    operator,
    seo_magister,
    content_magister,
    ads_magister,
    analytics_magister
):
    """Operator with real magisters for E2E tests"""
    operator.register_magister("seo", seo_magister)
    operator.register_magister("content", content_magister)
    operator.register_magister("ads", ads_magister)
    operator.register_magister("analytics", analytics_magister)
    
    yield operator

# ============================================================================
# MAGISTER FIXTURES
# ============================================================================

@pytest.fixture
async def seo_magister(event_bus, event_store, database):
    """SEO Magister with isolated dependencies"""
    magister = SEOMagisterV2(
        magister_id=f"seo-magister-{uuid4().hex[:8]}",
        event_bus=event_bus,
        event_store=event_store,
        db_session=database,
    )
    await magister.initialize()
    
    yield magister
    
    await magister.shutdown()

@pytest.fixture
async def seo_magister_with_mock_subagents(seo_magister):
    """SEO Magister with mock subagents for isolation"""
    from unittest.mock import AsyncMock
    
    mock_keyword_research = AsyncMock(spec=KeywordResearchAgent)
    mock_onpage_optimizer = AsyncMock()
    mock_competitor_analysis = AsyncMock()
    
    seo_magister.register_subagent("keyword_research", mock_keyword_research)
    seo_magister.register_subagent("onpage_optimizer", mock_onpage_optimizer)
    seo_magister.register_subagent("competitor_analysis", mock_competitor_analysis)
    
    yield seo_magister

@pytest.fixture
async def seo_magister_with_real_subagents(
    seo_magister,
    keyword_research_agent,
    onpage_optimizer_agent,
    competitor_analysis_agent
):
    """SEO Magister with real subagents for E2E tests"""
    seo_magister.register_subagent("keyword_research", keyword_research_agent)
    seo_magister.register_subagent("onpage_optimizer", onpage_optimizer_agent)
    seo_magister.register_subagent("competitor_analysis", competitor_analysis_agent)
    
    yield seo_magister

# ============================================================================
# SUBAGENT FIXTURES
# ============================================================================

@pytest.fixture
async def keyword_research_agent(event_bus, event_store, database):
    """Keyword Research Agent with isolated dependencies"""
    agent = KeywordResearchAgent(
        agent_id=f"keyword-research-{uuid4().hex[:8]}",
        event_bus=event_bus,
        event_store=event_store,
        db_session=database,
    )
    await agent.initialize()
    
    yield agent
    
    await agent.shutdown()

@pytest.fixture
async def keyword_research_agent_with_vcr(keyword_research_agent, vcr_cassette):
    """Keyword Research Agent with VCR for API mocking"""
    keyword_research_agent.api_client.use_cassette(vcr_cassette)
    
    yield keyword_research_agent

@pytest.fixture
async def keyword_research_agent_with_mock_api(keyword_research_agent):
    """Keyword Research Agent with mock API client"""
    from unittest.mock import AsyncMock
    from aim.tests.fixtures.keyword_data import MOCK_KEYWORD_SET_SMALL
    
    mock_api = AsyncMock()
    mock_api.expand_keywords.return_value = MOCK_KEYWORD_SET_SMALL
    
    keyword_research_agent.api_client = mock_api
    
    yield keyword_research_agent

# ============================================================================
# TEST UTILITIES
# ============================================================================

@pytest.fixture
async def event_collector(event_bus):
    """Event Collector for tracking events"""
    from aim.tests.helpers.event_flow_tracker import EventFlowTracker
    
    tracker = EventFlowTracker()
    
    yield tracker

@pytest.fixture
def task_factory():
    """Factory for creating test tasks"""
    from meai.agents.operator import Task, TaskStatus
    from datetime import datetime
    
    def _create(
        goal: str,
        priority: int = 2,
        capability: str = "seo",
        **kwargs
    ):
        return Task(
            task_id=kwargs.get("task_id", f"task-{uuid4().hex[:8]}"),
            source=kwargs.get("source", "user"),
            goal=goal,
            description=kwargs.get("description", goal),
            capability=capability,
            priority=priority,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **kwargs
        )
    
    return _create

@pytest.fixture
def event_factory():
    """Factory for creating test events"""
    from meai.events.base import BaseEvent
    from datetime import datetime, UTC
    
    def _create(
        event_type: str,
        source: str,
        target: str,
        **kwargs
    ):
        return BaseEvent(
            type=event_type,
            source=source,
            target=target,
            priority=kwargs.get("priority", 2),
            correlation_id=kwargs.get("correlation_id", str(uuid4())),
            reply_to=kwargs.get("reply_to"),
            metadata=kwargs.get("metadata", {}),
            timestamp=kwargs.get("timestamp", datetime.now(UTC)),
        )
    
    return _create
```

### 2.4 Performance Metrics

**Objective:** Measure and validate performance benchmarks.

**Implementation:**

```python
# AIM/tests/helpers/performance_metrics.py

import time
import psutil
from dataclasses import dataclass
from typing import Optional

@dataclass
class PerformanceMetrics:
    """Performance metrics for E2E tests"""
    
    start_time: float
    end_time: float
    peak_memory_mb: float
    cpu_percent: float
    
    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds"""
        return self.end_time - self.start_time
    
    def assert_within_limits(
        self,
        max_duration_s: float,
        max_memory_mb: float,
    ) -> None:
        """Assert metrics within acceptable limits
        
        Args:
            max_duration_s: Maximum allowed duration in seconds
            max_memory_mb: Maximum allowed memory in MB
            
        Raises:
            AssertionError: If metrics exceed limits
        """
        assert self.duration_seconds <= max_duration_s, \
            f"Duration {self.duration_seconds:.2f}s exceeds limit {max_duration_s}s"
        
        assert self.peak_memory_mb <= max_memory_mb, \
            f"Memory {self.peak_memory_mb:.2f}MB exceeds limit {max_memory_mb}MB"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging"""
        return {
            "duration_s": round(self.duration_seconds, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "cpu_percent": round(self.cpu_percent, 2),
        }


@pytest.fixture
def performance_tracker():
    """Track performance metrics during test"""
    process = psutil.Process()
    
    # Record start state
    start_time = time.time()
    start_memory = process.memory_info().rss / 1024 / 1024
    
    yield
    
    # Record end state
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024
    peak_memory = max(start_memory, end_memory)
    cpu_percent = process.cpu_percent()
    
    # Create metrics object
    metrics = PerformanceMetrics(
        start_time=start_time,
        end_time=end_time,
        peak_memory_mb=peak_memory,
        cpu_percent=cpu_percent,
    )
    
    return metrics
```

**Usage Example:**

```python
@pytest.mark.asyncio
async def test_seo_workflow_performance(
    operator_with_real_magisters,
    performance_tracker,
    task_factory
):
    """Test SEO workflow meets performance benchmarks"""
    
    # Execute workflow
    task = task_factory(
        goal="Complete SEO analysis for example.com",
        capability="seo"
    )
    await operator_with_real_magisters.receive_task(task)
    await operator_with_real_magisters.execute()
    
    # Get metrics
    metrics = performance_tracker
    
    # Assert benchmarks
    metrics.assert_within_limits(
        max_duration_s=30.0,  # SEO Magister benchmark
        max_memory_mb=200.0,
    )
    
    # Log metrics
    print(f"Performance: {metrics.to_dict()}")
```


---

## 3. Test Organization

### 3.1 Directory Structure

```
AIM/tests/
├── conftest.py                  # Global fixtures and configuration
├── __init__.py
│
├── fixtures/                    # Mock data
│   ├── __init__.py
│   ├── keyword_data.py          # Keyword research mock data
│   ├── seo_reports.py           # SEO analysis mock data
│   ├── content_data.py          # Content generation mock data
│   ├── ads_data.py              # Ads campaign mock data
│   └── analytics_data.py        # Analytics mock data
│
├── factories/                   # Data generators
│   ├── __init__.py
│   ├── task_factory.py          # Task creation factory
│   ├── event_factory.py         # Event creation factory
│   └── report_factory.py        # Report creation factory
│
├── helpers/                     # Test utilities
│   ├── __init__.py
│   ├── event_flow_tracker.py   # Event flow tracking
│   ├── performance_metrics.py  # Performance measurement
│   └── event_assertions.py     # Event assertion helpers
│
├── cassettes/                   # VCR recordings
│   ├── semrush/
│   │   ├── keyword_expansion_success.yaml
│   │   ├── budget_guard_triggered.yaml
│   │   └── zero_volume_retry.yaml
│   ├── ahrefs/
│   │   ├── keyword_expansion_fallback.yaml
│   │   └── difficulty_normalization.yaml
│   ├── ga4/
│   │   ├── fetch_metrics_success.yaml
│   │   └── conversions_api.yaml
│   └── yandex_metrica/
│       └── fetch_traffic_success.yaml
│
├── unit/                        # Unit tests (30+)
│   ├── __init__.py
│   ├── test_event_bus.py        # Event Bus tests
│   ├── test_event_store.py      # Event Store tests
│   ├── test_operator.py         # Operator tests
│   └── api_clients/
│       ├── __init__.py
│       ├── test_base.py         # Base API client tests
│       ├── test_semrush.py      # SEMrush client tests
│       ├── test_ahrefs.py       # Ahrefs client tests
│       ├── test_ga4.py          # GA4 client tests
│       └── test_yandex.py       # Yandex Metrica client tests
│
├── integration/                 # Integration tests (25+)
│   ├── __init__.py
│   ├── test_operator_magister.py      # Operator ↔ Magister
│   ├── test_magister_subagent.py      # Magister ↔ Subagent
│   ├── test_event_bus_store.py        # Event Bus ↔ Event Store
│   ├── test_api_fallback_chains.py    # API fallback chains
│   └── test_error_propagation.py      # Error propagation
│
└── e2e/                         # E2E tests (15+)
    ├── __init__.py
    ├── test_seo_workflow.py           # SEO workflow E2E
    ├── test_content_workflow.py       # Content workflow E2E
    ├── test_ads_workflow.py           # Ads workflow E2E
    ├── test_analytics_workflow.py     # Analytics workflow E2E
    ├── test_multi_magister_parallel.py # Parallel execution
    └── test_performance.py            # Performance benchmarks
```

### 3.2 Naming Conventions

**Test Files:**
- `test_<component>.py` — Unit tests for component
- `test_<component1>_<component2>.py` — Integration tests
- `test_<workflow>_workflow.py` — E2E workflow tests

**Test Functions:**
- `test_<action>_<expected_result>` — Standard pattern
- `test_<component>_<scenario>_<outcome>` — Complex scenarios

**Examples:**
```python
# Unit test
def test_event_bus_publishes_event_with_priority()

# Integration test
def test_operator_delegates_to_magister_successfully()

# E2E test
def test_seo_workflow_completes_with_real_apis()

# Edge case
def test_magister_handles_subagent_failure_gracefully()

# Performance test
def test_parallel_magisters_complete_within_timeout()
```

### 3.3 Test Markers

**Configuration (pytest.ini):**

```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (medium speed)
    e2e: End-to-end tests (slow, full workflow)
    vcr: Tests using VCR for API mocking
    real_api: Tests requiring real API calls (expensive)
    slow: Tests taking > 5 seconds
    parallel: Tests for parallel execution validation
    
asyncio_mode = auto
```

**Usage:**

```python
@pytest.mark.unit
async def test_event_bus_priority_queue():
    """Fast unit test"""
    pass

@pytest.mark.integration
@pytest.mark.vcr
async def test_magister_with_subagents():
    """Integration test with VCR"""
    pass

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.real_api
async def test_full_seo_workflow_with_real_apis():
    """Expensive E2E test with real APIs"""
    pass
```

**Run Strategies:**

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

# Specific workflow
pytest tests/e2e/test_seo_workflow.py

# With coverage
pytest --cov=aim --cov-report=html
```

---

## 4. Test Scenarios

### 4.1 Unit Tests (30+)

#### 4.1.1 Event Bus Tests

**File:** `tests/unit/test_event_bus.py`

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_publishes_event():
    """Test Event Bus publishes event successfully"""
    bus = EventBus()
    await bus.initialize()
    
    event = BaseEvent(
        type="test.event",
        source="test",
        target="handler"
    )
    
    event_id = await bus.publish(event)
    
    assert event_id is not None
    assert isinstance(event_id, str)
    
    await bus.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_priority_ordering():
    """Test Event Bus processes events by priority (P0 > P1 > P2 > P3)"""
    bus = EventBus()
    await bus.initialize()
    
    processing_order = []
    
    async def handler(event: BaseEvent):
        processing_order.append((event.priority, event.id))
    
    bus.subscribe("test.priority", handler)
    
    # Publish in mixed order
    for priority in [3, 1, 0, 2, 3, 0, 1, 2]:
        event = BaseEvent(
            type="test.priority",
            source="test",
            target="handler",
            priority=priority
        )
        await bus.publish(event)
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Verify P0 processed before P1, P1 before P2, etc.
    priorities = [p for p, _ in processing_order]
    
    # Group by priority
    by_priority = {0: [], 1: [], 2: [], 3: []}
    for i, p in enumerate(priorities):
        by_priority[p].append(i)
    
    # Check ordering
    for p in range(3):
        if by_priority[p] and by_priority[p + 1]:
            max_p = max(by_priority[p])
            min_p_plus_1 = min(by_priority[p + 1])
            assert max_p < min_p_plus_1, \
                f"P{p} events not processed before P{p+1}"
    
    await bus.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_pub_sub_pattern():
    """Test Event Bus pub/sub pattern with multiple subscribers"""
    bus = EventBus()
    await bus.initialize()
    
    received_events = {"handler1": [], "handler2": [], "handler3": []}
    
    async def handler1(event: BaseEvent):
        received_events["handler1"].append(event)
    
    async def handler2(event: BaseEvent):
        received_events["handler2"].append(event)
    
    async def handler3(event: BaseEvent):
        received_events["handler3"].append(event)
    
    # Subscribe all handlers
    bus.subscribe("test.pubsub", handler1)
    bus.subscribe("test.pubsub", handler2)
    bus.subscribe("test.pubsub", handler3)
    
    # Publish event
    event = BaseEvent(
        type="test.pubsub",
        source="test",
        target="all"
    )
    await bus.publish(event)
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify all handlers received event
    assert len(received_events["handler1"]) == 1
    assert len(received_events["handler2"]) == 1
    assert len(received_events["handler3"]) == 1
    
    await bus.close()
```

**Additional Event Bus Tests:**
- `test_event_bus_unsubscribe()`
- `test_event_bus_mark_processed()`
- `test_event_bus_mark_failed()`
- `test_event_bus_get_events_by_status()`
- `test_event_bus_clear_all()`

#### 4.1.2 Event Store Tests

**File:** `tests/unit/test_event_store.py`

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_store_append():
    """Test Event Store appends event"""
    store = EventStore()
    await store.initialize()
    
    event = BaseEvent(
        type="test.event",
        source="test",
        target="store"
    )
    
    await store.append(event)
    
    # Retrieve event
    retrieved = await store.get_by_id(str(event.id))
    
    assert retrieved is not None
    assert retrieved.id == event.id
    assert retrieved.type == event.type
    
    await store.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_store_immutability():
    """Test Event Store is append-only (no updates/deletes)"""
    store = EventStore()
    await store.initialize()
    
    # Create and store event
    original_event = BaseEvent(
        type="test.immutable",
        source="test",
        target="store",
        metadata={"value": "original"}
    )
    await store.append(original_event)
    
    # Retrieve event
    retrieved = await store.get_by_id(str(original_event.id))
    assert retrieved.metadata["value"] == "original"
    
    # Try to "update" by creating new event with same ID (should fail)
    modified_event = BaseEvent(
        id=original_event.id,
        type="test.immutable",
        source="test",
        target="store",
        metadata={"value": "modified"}
    )
    
    with pytest.raises(Exception):  # Duplicate ID rejected
        await store.append(modified_event)
    
    # Original event should be unchanged
    retrieved_again = await store.get_by_id(str(original_event.id))
    assert retrieved_again.metadata["value"] == "original"
    
    await store.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_store_get_by_correlation():
    """Test Event Store retrieves events by correlation ID"""
    store = EventStore()
    await store.initialize()
    
    correlation_id = str(uuid4())
    
    # Create correlation chain
    event1 = BaseEvent(
        type="task.created",
        source="operator",
        target="magister",
        correlation_id=correlation_id
    )
    await store.append(event1)
    
    event2 = BaseEvent(
        type="task.delegated",
        source="magister",
        target="subagent",
        correlation_id=correlation_id,
        reply_to=str(event1.id)
    )
    await store.append(event2)
    
    event3 = BaseEvent(
        type="task.completed",
        source="subagent",
        target="magister",
        correlation_id=correlation_id,
        reply_to=str(event2.id)
    )
    await store.append(event3)
    
    # Retrieve correlation chain
    chain = await store.get_by_correlation(correlation_id)
    
    assert len(chain) == 3
    assert chain[0].type == "task.created"
    assert chain[1].type == "task.delegated"
    assert chain[2].type == "task.completed"
    
    # Verify reply chain
    assert chain[1].reply_to == str(chain[0].id)
    assert chain[2].reply_to == str(chain[1].id)
    
    await store.close()
```

**Additional Event Store Tests:**
- `test_event_store_replay()`
- `test_event_store_get_by_type()`
- `test_event_store_get_by_source()`
- `test_event_store_chronological_order()`

#### 4.1.3 API Client Tests

**File:** `tests/unit/api_clients/test_semrush.py`

```python
@pytest.mark.unit
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_semrush_keyword_expansion():
    """Test SEMrush keyword expansion with VCR"""
    client = SEMrushClient(api_key="test_key")
    
    result = await client.expand_keywords(
        seed_keyword="dental implants",
        max_keywords=100
    )
    
    assert len(result) >= 100
    assert result[0].keyword == "dental implants"
    assert result[0].volume > 0
    assert result[0].difficulty >= 0
    assert result[0].cpc >= 0
    
    await client.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_semrush_budget_guard():
    """Test SEMrush budget guard prevents overspending"""
    client = SEMrushClient(
        api_key="test_key",
        budget_limit=10.0  # $10 limit
    )
    
    # Mock expensive operation
    with pytest.raises(BudgetExceededError):
        await client.expand_keywords(
            seed_keyword="test",
            max_keywords=10000  # Would exceed budget
        )
    
    await client.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_semrush_retry_on_rate_limit():
    """Test SEMrush retries on rate limit (429)"""
    from unittest.mock import AsyncMock, patch
    
    client = SEMrushClient(api_key="test_key")
    
    # Mock API to return 429 twice, then success
    mock_response = AsyncMock()
    mock_response.status = 429
    mock_response.headers = {"Retry-After": "1"}
    
    with patch.object(client, '_make_request') as mock_request:
        mock_request.side_effect = [
            RateLimitError("Rate limit exceeded"),
            RateLimitError("Rate limit exceeded"),
            {"data": [{"keyword": "test", "volume": 1000}]}
        ]
        
        result = await client.expand_keywords("test")
        
        # Verify 3 attempts (2 retries + 1 success)
        assert mock_request.call_count == 3
        assert len(result) == 1
    
    await client.close()
```

**Additional API Client Tests:**
- `test_ahrefs_keyword_expansion_fallback()`
- `test_ga4_fetch_metrics()`
- `test_yandex_fetch_traffic()`
- `test_circuit_breaker_opens_on_failures()`
- `test_circuit_breaker_half_open_recovery()`


### 4.2 Integration Tests (25+)

#### 4.2.1 Operator ↔ Magister Tests

**File:** `tests/integration/test_operator_magister.py`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_operator_delegates_to_magister(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """Test Operator delegates task to appropriate Magister"""
    
    # Create SEO task
    task = task_factory(
        goal="Analyze SEO for example.com",
        capability="seo"
    )
    
    # Delegate task
    await operator_with_real_magisters.receive_task(task)
    
    # Wait for delegation
    await asyncio.sleep(0.5)
    
    # Verify delegation event
    events = event_collector.get_by_correlation(task.task_id)
    
    assert len(events) >= 2
    assert events[0].type == "task.created"
    assert events[0].source == "operator"
    assert events[1].type == "task.delegated"
    assert events[1].target == "seo-magister"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_operator_receives_magister_result(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """Test Operator receives result from Magister"""
    
    task = task_factory(goal="Analyze SEO", capability="seo")
    
    await operator_with_real_magisters.receive_task(task)
    await operator_with_real_magisters.execute()
    
    # Wait for completion
    await asyncio.sleep(2.0)
    
    # Verify completion event
    events = event_collector.get_by_correlation(task.task_id)
    completion_events = [e for e in events if e.type == "task.completed"]
    
    assert len(completion_events) >= 1
    assert completion_events[-1].target == "operator"
    assert "result" in completion_events[-1].metadata


@pytest.mark.integration
@pytest.mark.asyncio
async def test_operator_handles_magister_failure(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """Test Operator handles Magister failure gracefully"""
    
    # Create task that will fail
    task = task_factory(
        goal="Invalid task that will fail",
        capability="seo"
    )
    
    await operator_with_real_magisters.receive_task(task)
    await operator_with_real_magisters.execute()
    
    # Wait for error propagation
    await asyncio.sleep(1.0)
    
    # Verify error event
    events = event_collector.get_by_correlation(task.task_id)
    error_events = [e for e in events if e.type == "task.failed"]
    
    assert len(error_events) >= 1
    assert error_events[-1].target == "operator"
    assert "error" in error_events[-1].metadata
```

#### 4.2.2 Magister ↔ Subagent Tests

**File:** `tests/integration/test_magister_subagent.py`

```python
@pytest.mark.integration
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_magister_delegates_to_subagent(
    seo_magister_with_real_subagents,
    event_collector,
    task_factory
):
    """Test Magister delegates subtask to Subagent"""
    
    task = task_factory(
        goal="Research keywords for dental implants",
        capability="seo"
    )
    
    await seo_magister_with_real_subagents.receive_task(task)
    
    # Wait for delegation
    await asyncio.sleep(0.5)
    
    # Verify delegation to keyword research subagent
    events = event_collector.get_by_correlation(task.task_id)
    delegation_events = [e for e in events if e.type == "subtask.delegated"]
    
    assert len(delegation_events) >= 1
    assert "keyword-research" in delegation_events[0].target


@pytest.mark.integration
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_magister_aggregates_subagent_results(
    seo_magister_with_real_subagents,
    event_collector,
    task_factory
):
    """Test Magister aggregates results from multiple Subagents"""
    
    task = task_factory(
        goal="Complete SEO analysis",
        capability="seo"
    )
    
    await seo_magister_with_real_subagents.receive_task(task)
    await seo_magister_with_real_subagents.execute()
    
    # Wait for completion
    await asyncio.sleep(3.0)
    
    # Verify aggregation
    events = event_collector.get_by_correlation(task.task_id)
    completion_event = next(
        (e for e in events if e.type == "task.completed"),
        None
    )
    
    assert completion_event is not None
    assert "aggregated_results" in completion_event.metadata
    assert len(completion_event.metadata["aggregated_results"]) >= 2
```

#### 4.2.3 Event Flow Tests

**File:** `tests/integration/test_event_flow.py`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_event_flow_operator_to_subagent(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """Test complete event flow: Operator → Magister → Subagent → Result"""
    
    tracker = EventFlowTracker()
    correlation_id = str(uuid4())
    
    # Track expected flow
    tracker.track_correlation(
        correlation_id,
        expected_event_types=[
            "task.created",
            "task.delegated",
            "subtask.delegated",
            "subtask.completed",
            "task.completed"
        ]
    )
    
    # Subscribe to all events
    async def record_handler(event: BaseEvent):
        tracker.record_event(event)
    
    for event_type in tracker.expected_types[correlation_id]:
        event_bus.subscribe(event_type, record_handler)
    
    # Execute workflow
    task = task_factory(
        task_id=correlation_id,
        goal="Complete SEO analysis",
        capability="seo"
    )
    await operator_with_real_magisters.receive_task(task)
    await operator_with_real_magisters.execute()
    
    # Wait for completion
    events = await tracker.wait_for_completion(correlation_id, timeout=10.0)
    
    # Verify complete flow
    assert len(events) == 5
    assert events[0].type == "task.created"
    assert events[1].type == "task.delegated"
    assert events[2].type == "subtask.delegated"
    assert events[3].type == "subtask.completed"
    assert events[4].type == "task.completed"
    
    # Verify reply chain
    for i in range(1, len(events)):
        assert events[i].reply_to == str(events[i-1].id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_propagation_subagent_to_operator(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """Test error propagates: Subagent → Magister → Operator"""
    
    error_tracker = ErrorChainTracker()
    correlation_id = str(uuid4())
    error_tracker.track_error_chain(correlation_id)
    
    # Subscribe to error events
    async def error_handler(event: BaseEvent):
        error_tracker.record_error(event)
    
    event_bus.subscribe("task.failed", error_handler)
    event_bus.subscribe("error.reported", error_handler)
    
    # Create task that will fail
    task = task_factory(
        task_id=correlation_id,
        goal="Invalid task that will fail",
        capability="seo"
    )
    
    await operator_with_real_magisters.receive_task(task)
    await operator_with_real_magisters.execute()
    
    # Wait for error propagation
    errors = await error_tracker.wait_for_error(correlation_id, timeout=5.0)
    
    # Verify error chain
    assert len(errors) >= 2
    assert errors[0].type == "task.failed"
    assert errors[0].source.startswith("subagent")
    assert errors[-1].type == "error.reported"
    assert errors[-1].target == "operator"
```

### 4.3 E2E Tests (15+)

#### 4.3.1 SEO Workflow E2E

**File:** `tests/e2e/test_seo_workflow.py`

```python
@pytest.mark.e2e
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_seo_workflow_keyword_research_to_optimization(
    operator_with_real_magisters,
    event_collector,
    performance_tracker,
    task_factory
):
    """E2E: Complete SEO workflow from keyword research to optimization"""
    
    # Create SEO task
    task = task_factory(
        goal="Complete SEO analysis and optimization for example.com",
        capability="seo",
        resources={
            "url": "https://example.com",
            "seed_keyword": "dental implants"
        }
    )
    
    # Execute workflow
    await operator_with_real_magisters.receive_task(task)
    await operator_with_real_magisters.execute()
    
    # Wait for completion
    await asyncio.sleep(5.0)
    
    # Verify workflow completion
    events = event_collector.get_by_correlation(task.task_id)
    completion_event = next(
        (e for e in events if e.type == "task.completed"),
        None
    )
    
    assert completion_event is not None
    assert completion_event.metadata["status"] == "success"
    
    # Verify result structure
    result = completion_event.metadata["result"]
    assert "keyword_research" in result
    assert "onpage_optimization" in result
    assert "competitor_analysis" in result
    
    # Verify performance
    metrics = performance_tracker
    metrics.assert_within_limits(
        max_duration_s=30.0,  # SEO Magister benchmark
        max_memory_mb=200.0
    )


@pytest.mark.e2e
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_seo_workflow_with_api_fallback(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """E2E: SEO workflow with API fallback (SEMrush → Ahrefs → Mock)"""
    
    # Mock SEMrush failure
    with patch('aim.api_clients.semrush.SEMrushClient.expand_keywords') as mock_semrush:
        mock_semrush.side_effect = APIError("SEMrush unavailable")
        
        # Create task
        task = task_factory(
            goal="Research keywords",
            capability="seo",
            resources={"seed_keyword": "dental implants"}
        )
        
        # Execute workflow
        await operator_with_real_magisters.receive_task(task)
        await operator_with_real_magisters.execute()
        
        # Wait for completion
        await asyncio.sleep(3.0)
        
        # Verify fallback to Ahrefs
        events = event_collector.get_by_correlation(task.task_id)
        api_events = [e for e in events if "api_call" in e.metadata]
        
        assert any("ahrefs" in e.metadata.get("api_provider", "") for e in api_events)
        
        # Verify completion despite SEMrush failure
        completion_event = next(
            (e for e in events if e.type == "task.completed"),
            None
        )
        assert completion_event is not None
```

#### 4.3.2 Multi-Magister Parallel E2E

**File:** `tests/e2e/test_multi_magister_parallel.py`

```python
@pytest.mark.e2e
@pytest.mark.parallel
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_four_magisters_parallel_execution(
    operator_with_real_magisters,
    event_collector,
    performance_tracker,
    task_factory
):
    """E2E: Test 4 Magisters execute in parallel with >= 2.5x speedup"""
    
    # Create tasks for all 4 Magisters
    tasks = [
        task_factory(goal="SEO analysis", capability="seo"),
        task_factory(goal="Content generation", capability="content"),
        task_factory(goal="Ads campaign", capability="ads"),
        task_factory(goal="Analytics report", capability="analytics"),
    ]
    
    # Execute all tasks
    for task in tasks:
        await operator_with_real_magisters.receive_task(task)
    
    await operator_with_real_magisters.execute()
    
    # Wait for all completions
    await asyncio.sleep(10.0)
    
    # Verify all completed
    for task in tasks:
        events = event_collector.get_by_correlation(task.task_id)
        completion_event = next(
            (e for e in events if e.type == "task.completed"),
            None
        )
        assert completion_event is not None
    
    # Verify performance: parallel should be < 35s (vs ~100s sequential)
    metrics = performance_tracker
    assert metrics.duration_seconds < 35.0, \
        f"Parallel execution took {metrics.duration_seconds}s, expected < 35s"
    
    # Calculate speedup
    # Sequential estimate: 30s (SEO) + 25s (Content) + 20s (Ads) + 15s (Analytics) = 90s
    sequential_estimate = 90.0
    speedup = sequential_estimate / metrics.duration_seconds
    
    assert speedup >= 2.5, \
        f"Speedup {speedup:.2f}x is below target 2.5x"


@pytest.mark.e2e
@pytest.mark.parallel
@pytest.mark.asyncio
async def test_parallel_magisters_handle_concurrent_errors(
    operator_with_real_magisters,
    event_collector,
    task_factory
):
    """E2E: Test parallel Magisters handle errors independently"""
    
    # Create tasks: 2 valid, 2 invalid
    tasks = [
        task_factory(goal="Valid SEO task", capability="seo"),
        task_factory(goal="Invalid content task", capability="content"),  # Will fail
        task_factory(goal="Valid ads task", capability="ads"),
        task_factory(goal="Invalid analytics task", capability="analytics"),  # Will fail
    ]
    
    # Execute all tasks
    for task in tasks:
        await operator_with_real_magisters.receive_task(task)
    
    await operator_with_real_magisters.execute()
    
    # Wait for all completions/failures
    await asyncio.sleep(10.0)
    
    # Verify: 2 completed, 2 failed
    completed_count = 0
    failed_count = 0
    
    for task in tasks:
        events = event_collector.get_by_correlation(task.task_id)
        
        if any(e.type == "task.completed" for e in events):
            completed_count += 1
        elif any(e.type == "task.failed" for e in events):
            failed_count += 1
    
    assert completed_count == 2, f"Expected 2 completed, got {completed_count}"
    assert failed_count == 2, f"Expected 2 failed, got {failed_count}"
```

#### 4.3.3 Performance Benchmarks E2E

**File:** `tests/e2e/test_performance.py`

```python
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_load_testing_100_concurrent_tasks(
    operator_with_real_magisters,
    performance_tracker,
    task_factory
):
    """E2E: Load test with 100 concurrent tasks"""
    
    # Create 100 tasks
    tasks = [
        task_factory(
            goal=f"Task {i}",
            capability=["seo", "content", "ads", "analytics"][i % 4]
        )
        for i in range(100)
    ]
    
    # Submit all tasks
    for task in tasks:
        await operator_with_real_magisters.receive_task(task)
    
    # Execute
    await operator_with_real_magisters.execute()
    
    # Wait for completion
    await asyncio.sleep(60.0)
    
    # Count successes
    success_count = 0
    for task in tasks:
        events = event_collector.get_by_correlation(task.task_id)
        if any(e.type == "task.completed" for e in events):
            success_count += 1
    
    # Verify >= 95% success rate
    success_rate = success_count / len(tasks)
    assert success_rate >= 0.95, \
        f"Success rate {success_rate:.2%} below target 95%"
    
    # Verify throughput >= 2 workflows/sec
    metrics = performance_tracker
    throughput = success_count / metrics.duration_seconds
    assert throughput >= 2.0, \
        f"Throughput {throughput:.2f} workflows/s below target 2.0"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_memory_leak_detection(
    operator_with_real_magisters,
    task_factory
):
    """E2E: Detect memory leaks over 10 iterations"""
    
    import psutil
    process = psutil.Process()
    
    memory_samples = []
    
    for i in range(10):
        # Record memory before
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Execute workflow
        task = task_factory(goal=f"Iteration {i}", capability="seo")
        await operator_with_real_magisters.receive_task(task)
        await operator_with_real_magisters.execute()
        
        # Wait for completion
        await asyncio.sleep(2.0)
        
        # Record memory after
        mem_after = process.memory_info().rss / 1024 / 1024
        memory_samples.append(mem_after - mem_before)
    
    # Calculate average memory delta
    avg_delta = sum(memory_samples) / len(memory_samples)
    
    # Verify < 1 MB leak per iteration
    assert avg_delta < 1.0, \
        f"Memory leak detected: {avg_delta:.2f} MB per iteration"
```


---

## 5. Implementation Roadmap

### 5.1 Phase Overview

**Total Estimated Effort:** 17 hours across 7 phases

| Phase | Description | Effort | Priority |
|-------|-------------|--------|----------|
| 1 | Infrastructure Setup | 2h | P0 |
| 2 | Event Flow Testing | 3h | P0 |
| 3 | API Integration with VCR | 3h | P1 |
| 4 | Operator & Magister Tests | 2h | P0 |
| 5 | E2E Workflows | 4h | P1 |
| 6 | Performance & Load Testing | 2h | P2 |
| 7 | Documentation & CI | 1h | P2 |

### 5.2 Phase 1: Infrastructure Setup (2h)

**Objective:** Create base testing infrastructure.

**Tasks:**
1. Create `AIM/tests/conftest.py` with base fixtures
2. Install pytest-vcr and configure
3. Create directory structure (unit/, integration/, e2e/)
4. Add pytest.ini with markers
5. Create helpers/ directory with utilities

**Deliverables:**
- ✅ conftest.py with database, event_bus, event_store fixtures
- ✅ VCR configuration
- ✅ Directory structure
- ✅ pytest.ini with markers
- ✅ EventFlowTracker in helpers/

**Acceptance Criteria:**
- All fixtures can be imported
- pytest discovers test directories
- VCR configuration loads without errors

### 5.3 Phase 2: Event Flow Testing (3h)

**Objective:** Implement Event Bus and Event Store testing.

**Tasks:**
1. Implement EventFlowTracker helper
2. Create event_bus fixtures
3. Write unit tests for Event Bus (10+ tests)
4. Write unit tests for Event Store (8+ tests)
5. Write integration tests for event flow (5+ tests)

**Deliverables:**
- ✅ EventFlowTracker in tests/helpers/
- ✅ tests/unit/test_event_bus.py (10+ tests)
- ✅ tests/unit/test_event_store.py (8+ tests)
- ✅ tests/integration/test_event_flow.py (5+ tests)

**Acceptance Criteria:**
- All Event Bus tests pass
- All Event Store tests pass
- Event flow tracking works correctly

### 5.4 Phase 3: API Integration with VCR (3h)

**Objective:** Set up VCR for zero-cost API testing.

**Tasks:**
1. Record cassettes for SEMrush, Ahrefs, GA4, Yandex
2. Create API client fixtures with VCR
3. Write unit tests for API clients (15+ tests)
4. Test fallback chains (SEMrush → Ahrefs → Mock)
5. Test resilience patterns (circuit breaker, retry)

**Deliverables:**
- ✅ Cassettes in tests/cassettes/
- ✅ tests/unit/api_clients/ (15+ tests)
- ✅ Fallback chain tests
- ✅ Resilience pattern tests

**Acceptance Criteria:**
- All API client tests pass with VCR
- Zero API costs after initial recording
- Fallback chains work correctly

### 5.5 Phase 4: Operator & Magister Tests (2h)

**Objective:** Test Operator and Magister interactions.

**Tasks:**
1. Create operator and magister fixtures
2. Write integration tests for Operator → Magister (8+ tests)
3. Test task delegation and completion
4. Test error handling

**Deliverables:**
- ✅ Operator/Magister fixtures in conftest.py
- ✅ tests/integration/test_operator_magister.py (8+ tests)
- ✅ tests/integration/test_magister_subagent.py (8+ tests)

**Acceptance Criteria:**
- Operator delegates tasks correctly
- Magisters receive and process tasks
- Error propagation works

### 5.6 Phase 5: E2E Workflows (4h)

**Objective:** Write end-to-end workflow tests.

**Tasks:**
1. Write E2E test for SEO workflow (5+ scenarios)
2. Write E2E test for Content workflow (5+ scenarios)
3. Write E2E test for Ads workflow (5+ scenarios)
4. Write E2E test for parallel Magisters (3+ scenarios)

**Deliverables:**
- ✅ tests/e2e/test_seo_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_content_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_ads_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_multi_magister_parallel.py (3+ scenarios)

**Acceptance Criteria:**
- All E2E workflows complete successfully
- Performance benchmarks met (< 35s)
- Parallel speedup >= 2.5x

### 5.7 Phase 6: Performance & Load Testing (2h)

**Objective:** Validate performance benchmarks.

**Tasks:**
1. Implement PerformanceMetrics tracker
2. Write parallel execution tests
3. Write load tests (10, 50, 100 concurrent tasks)
4. Validate performance benchmarks
5. Test memory leak detection

**Deliverables:**
- ✅ PerformanceMetrics in tests/helpers/
- ✅ tests/e2e/test_performance.py (5+ tests)
- ✅ Performance benchmarks validated

**Acceptance Criteria:**
- Parallel speedup >= 2.5x
- E2E duration < 35s (< 5s with VCR)
- Success rate >= 95% under load
- No memory leaks detected

### 5.8 Phase 7: Documentation & CI (1h)

**Objective:** Document testing and set up CI.

**Tasks:**
1. Write tests/README.md with instructions
2. Create GitHub Actions workflow
3. Setup coverage reporting
4. Add coverage badge to README

**Deliverables:**
- ✅ tests/README.md
- ✅ .github/workflows/tests.yml
- ✅ Coverage badge in README

**Acceptance Criteria:**
- Documentation is clear and complete
- CI runs all tests automatically
- Coverage reports generated

---

## 6. Success Criteria

### 6.1 Test Coverage

- ✅ **Unit tests:** 30+ tests (Event Bus, Event Store, API clients)
- ✅ **Integration tests:** 25+ tests (Operator ↔ Magister ↔ Subagent)
- ✅ **E2E tests:** 15+ tests (full workflows)
- ✅ **Total:** 70+ tests

### 6.2 Performance

- ✅ **Parallel speedup:** >= 2.5x for 4 Magisters
- ✅ **E2E duration:** < 35s real, < 5s with VCR
- ✅ **Memory:** < 500 MB peak, < 1 MB leak per 10 iterations
- ✅ **Throughput:** >= 2 workflows/sec
- ✅ **Success rate:** >= 95% under 100 concurrent tasks

### 6.3 Quality

- ✅ **Pass rate:** 100%
- ✅ **Isolation:** Each test independent
- ✅ **Deterministic:** Reproducible results
- ✅ **Fast feedback:** Unit tests < 10s

### 6.4 Cost

- ✅ **API costs:** $0 after initial cassette recording
- ✅ **CI time:** < 5 min for full suite
- ✅ **Developer time:** < 30s for pre-commit checks

---

## 7. Dependencies

### 7.1 Python Packages

```txt
# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-vcr>=1.0.2
vcrpy>=6.0.0

# Performance
psutil>=5.9.0

# Mocking
pytest-mock>=3.12.0
```

### 7.2 Existing Components

- ✅ Event Bus (`meai.events.event_bus`)
- ✅ Event Store (`meai.events.event_store`)
- ✅ Base Event (`meai.events.base`)
- ✅ Operator (`meai.agents.operator`)
- ✅ Magisters (`aim.magisters.*`)
- ✅ Subagents (`aim.subagents.*`)
- ✅ API Clients (`aim.api_clients.*`)

---

## 8. Risk Mitigation

### 8.1 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limits during cassette recording | High | Medium | Record cassettes in off-peak hours, use test API keys |
| Flaky async tests | Medium | High | Use EventFlowTracker with timeouts, add retry logic |
| Memory leaks in long-running tests | High | Low | Implement memory leak detection, monitor peak usage |
| CI timeout on slow tests | Medium | Medium | Use VCR for CI, mark slow tests with @pytest.mark.slow |

### 8.2 Mitigation Strategies

**API Rate Limits:**
- Record cassettes during off-peak hours
- Use separate test API keys with higher limits
- Implement exponential backoff in recording script

**Flaky Tests:**
- Use EventFlowTracker with generous timeouts (10s)
- Add retry logic for async operations
- Isolate tests completely (no shared state)

**Memory Leaks:**
- Run memory leak detection in CI
- Monitor peak memory usage per test
- Add cleanup in fixture teardown

**CI Timeouts:**
- Use VCR for all CI runs (zero API calls)
- Mark slow tests with @pytest.mark.slow
- Run slow tests separately in nightly builds

---

## 9. Appendix

### 9.1 Key Patterns Summary

**VCR Pattern:**
```python
@pytest.mark.vcr
async def test_api_call():
    result = await api_client.call()
    assert result is not None
```

**Event Flow Pattern:**
```python
tracker = EventFlowTracker()
tracker.track_correlation(correlation_id, ["created", "completed"])
events = await tracker.wait_for_completion(correlation_id)
assert len(events) == 2
```

**Performance Pattern:**
```python
async def test_performance(performance_tracker):
    # ... execute workflow ...
    metrics = performance_tracker
    metrics.assert_within_limits(max_duration_s=35, max_memory_mb=500)
```

**Fixture Pattern:**
```python
@pytest.fixture
async def isolated_component():
    component = Component()
    await component.initialize()
    yield component
    await component.cleanup()
```

### 9.2 References

- **Brainstorming Docs:** `docs/brainstorming/phase6-e2e-testing/`
- **Unified Strategy:** `docs/brainstorming/phase6-e2e-testing/unified-strategy.md`
- **API Integration Strategy:** `docs/brainstorming/phase6-e2e-testing/api-integration-strategy.md`
- **Performance Testing:** `docs/brainstorming/phase6-e2e-testing/performance-testing.md`
- **Testing Infrastructure:** `docs/brainstorming/phase6-e2e-testing/testing-infrastructure.md`

---

**Document Status:** Draft  
**Next Step:** Review and approval  
**Estimated Implementation:** 17 hours (7 phases)

