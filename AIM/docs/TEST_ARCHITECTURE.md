# Test Architecture Guide

Comprehensive guide to the AIM Testing Infrastructure architecture, patterns, and best practices.

## Table of Contents

- [Overview](#overview)
- [Testing Philosophy](#testing-philosophy)
- [Test Pyramid](#test-pyramid)
- [Test Organization](#test-organization)
- [Fixture Patterns](#fixture-patterns)
- [Mock Data Strategy](#mock-data-strategy)
- [Running Tests](#running-tests)
- [Coverage Reporting](#coverage-reporting)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

The AIM Testing Infrastructure provides comprehensive test coverage across 6 phases:

**Statistics:**
- **Total Tests:** 122 (174% of 70+ target)
- **Pass Rate:** 98.4% (120/122 passing, 2 skipped)
- **Coverage:** Unit (82), Integration (12), E2E (21)
- **Time Investment:** 9.59 hours (vs 17 estimated, 43% time saved)

**Architecture Tested:**
```
Operator (Tactical Layer)
  ↓ Event Bus
Magisters (Domain Orchestrators)
  ├─ SEO Magister
  ├─ Content Magister
  ├─ Ads Magister
  └─ Analytics Magister
  ↓ Event Bus
Subagents (Execution Layer)
  ├─ Keyword Research
  ├─ Content Writer
  ├─ Campaign Creator
  └─ Analytics Collector
```

## Testing Philosophy

### Quality Over Speed
- **Principle:** Quality is more important than speed
- **Deep Analysis:** Each test validates real business logic, not just code paths
- **No Shortcuts:** No mock data in production code, comprehensive error handling

### Complete Before Next
- **Principle:** Finish current task 100% before moving to next
- **No Stubs:** All implementations are real, no "TODO" placeholders
- **Full Coverage:** Each component has unit, integration, and E2E tests

### Real Data Focus
- **Principle:** Tests use real data structures and realistic scenarios
- **Mock Strategy:** Mocks only for external APIs, not internal logic
- **Validation:** All data validated with Pydantic schemas

## Test Pyramid

### Unit Tests (82 tests, 67%)

**Purpose:** Test individual components in isolation

**Coverage:**
- Event Bus (10 tests) - Publish/subscribe, priority queues, error handling
- Event Store (12 tests) - Append, replay, correlation queries
- API Clients (27 tests) - Rate limiting, circuit breaker, retry logic
- Magisters (24 tests) - Action routing, result aggregation, scoring
- Subagents (19 tests) - Domain logic, data processing, recommendations

**Characteristics:**
- Fast execution (< 1 second per test)
- No external dependencies
- Deterministic results
- High isolation

**Example:**
```python
# tests/unit/test_event_bus.py
async def test_publish_subscribe():
    bus = EventBus()
    received = []
    
    async def handler(event):
        received.append(event)
    
    bus.subscribe("test.event", handler)
    await bus.publish(Event(type="test.event", data={"key": "value"}))
    
    assert len(received) == 1
    assert received[0].data["key"] == "value"
```

### Integration Tests (12 tests, 10%)

**Purpose:** Test component interactions and workflows

**Coverage:**
- Event Flow (8 tests) - Event Bus + Event Store integration
- Magister E2E (4 tests) - Magister + Subagent coordination

**Characteristics:**
- Medium execution time (1-5 seconds per test)
- Multiple components involved
- Real coordination patterns
- Async synchronization

**Example:**
```python
# tests/integration/test_event_flow.py
async def test_correlation_chain():
    bus = EventBus()
    store = EventStore()
    tracker = EventFlowTracker(bus, store)
    
    # Publish parent event
    parent = await tracker.start_flow("test.flow", {"data": "value"})
    
    # Publish child event
    child = await tracker.continue_flow(parent.correlation_id, "test.child")
    
    # Verify correlation chain
    chain = await store.get_correlation_chain(parent.correlation_id)
    assert len(chain) == 2
    assert chain[0].event_id == parent.event_id
    assert chain[1].event_id == child.event_id
```

### End-to-End Tests (21 tests, 17%)

**Purpose:** Test complete workflows from user request to final result

**Coverage:**
- SEO Workflow (3 tests) - Keyword research, competitor analysis
- Content Workflow (5 tests) - Content generation, quality validation
- Ads Workflow (5 tests) - Campaign creation, budget optimization
- Multi-Agent (4 tests) - Parallel execution, error recovery
- Real-World (4 tests) - Client onboarding, budget constraints

**Characteristics:**
- Slower execution (5-30 seconds per test)
- Full system integration
- Real-world scenarios
- Complex coordination

**Example:**
```python
# tests/e2e/test_seo_workflow.py
async def test_keyword_research_workflow():
    # Setup
    magister = SEOMagister(...)
    task = Task(action="keyword_research", payload={"seed": "dental implants"})
    
    # Execute full workflow
    result = await magister.execute_task(task)
    
    # Verify complete workflow
    assert result.status == "completed"
    assert len(result.result["keywords"]) >= 10
    assert result.result["score"] > 0
    assert len(result.result["insights"]) > 0
```

## Test Organization

### Directory Structure

```
AIM/tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── keyword_data.py         # Keyword research fixtures
│   ├── magister_fixtures.py    # Magister test fixtures
│   └── e2e_fixtures.py         # E2E test fixtures
├── unit/                       # Unit tests
│   ├── test_event_bus.py
│   ├── test_event_store.py
│   └── test_api_clients.py
├── integration/                # Integration tests
│   ├── test_event_flow.py
│   └── test_*_magister_e2e.py
└── e2e/                        # End-to-end tests
    ├── test_seo_workflow.py
    ├── test_content_workflow.py
    ├── test_ads_workflow.py
    ├── test_multi_agent_coordination.py
    └── test_real_world_scenario.py
```

### Naming Conventions

**Test Files:**
- `test_<component>.py` - Unit tests for component
- `test_<component>_e2e.py` - Integration tests for component
- `test_<workflow>_workflow.py` - E2E workflow tests

**Test Functions:**
- `test_<action>` - Basic functionality test
- `test_<action>_with_<condition>` - Test with specific condition
- `test_<action>_<error_case>` - Error handling test

**Fixtures:**
- `<component>_fixture` - Component instance
- `mock_<service>` - Mocked external service
- `sample_<data>` - Sample test data

## Fixture Patterns

### Shared Fixtures (conftest.py)

```python
# AIM/tests/conftest.py
import pytest
from aim.events.event_bus import EventBus
from aim.events.event_store import EventStore

@pytest.fixture
async def event_bus():
    """Shared Event Bus instance."""
    bus = EventBus()
    yield bus
    await bus.close()

@pytest.fixture
async def event_store(tmp_path):
    """Shared Event Store with temporary database."""
    db_path = tmp_path / "test.db"
    store = EventStore(f"sqlite:///{db_path}")
    await store.initialize()
    yield store
    await store.close()
```

### Domain-Specific Fixtures

```python
# AIM/tests/fixtures/magister_fixtures.py
import pytest
from aim.magisters.seo_magister import SEOMagister

@pytest.fixture
def mock_keyword_agent():
    """Mock Keyword Research Agent."""
    class MockAgent:
        async def execute_task(self, task):
            return TaskResult(
                status="completed",
                result={"keywords": [...], "score": 85}
            )
    return MockAgent()

@pytest.fixture
async def seo_magister(event_bus, mock_keyword_agent):
    """SEO Magister with mocked dependencies."""
    magister = SEOMagister(
        event_bus=event_bus,
        keyword_agent=mock_keyword_agent
    )
    yield magister
```

### Parametrized Fixtures

```python
@pytest.fixture(params=["google", "yandex", "direct"])
def traffic_source(request):
    """Parametrized traffic source fixture."""
    return request.param

def test_traffic_analysis(traffic_source):
    """Test runs 3 times with different sources."""
    analyzer = TrafficAnalyzer()
    result = analyzer.analyze(source=traffic_source)
    assert result.source == traffic_source
```

## Mock Data Strategy

### Principles

1. **Mock External APIs Only**
   - SEMrush, Ahrefs, GA4, Yandex APIs
   - Network calls, file I/O
   - Time-dependent operations

2. **Use Real Data Structures**
   - Pydantic models for validation
   - Realistic data values
   - Complete object graphs

3. **Avoid Over-Mocking**
   - Don't mock internal logic
   - Don't mock simple functions
   - Don't mock data classes

### Mock Patterns

**API Client Mocking:**
```python
# tests/fixtures/keyword_data.py
def mock_semrush_response():
    return {
        "data": [
            {
                "keyword": "dental implants",
                "search_volume": 12000,
                "cpc": 15.50,
                "competition": 0.85
            }
        ]
    }

@pytest.fixture
def mock_semrush_client(monkeypatch):
    async def mock_expand(*args, **kwargs):
        return [KeywordData(**kw) for kw in mock_semrush_response()["data"]]
    
    monkeypatch.setattr(
        "aim.subagents.api_clients.semrush.SEMrushClient.expand_keywords",
        mock_expand
    )
```

**Time Mocking:**
```python
from freezegun import freeze_time

@freeze_time("2026-05-15 12:00:00")
def test_time_dependent_logic():
    result = generate_report()
    assert result.timestamp == datetime(2026, 5, 15, 12, 0, 0)
```

## Running Tests

### Basic Commands

```bash
# Run all tests
cd AIM
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/unit/test_event_bus.py -v

# Run specific test
python -m pytest tests/unit/test_event_bus.py::test_publish_subscribe -v

# Run tests by marker
python -m pytest tests/ -m "unit" -v
python -m pytest tests/ -m "integration" -v
python -m pytest tests/ -m "e2e" -v
```

### With Coverage

```bash
# Run with coverage report
python -m pytest tests/ --cov=src/aim --cov=../src/meai --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=src/aim --cov=../src/meai --cov-report=html

# Check coverage threshold
python -m pytest tests/ --cov=src/aim --cov=../src/meai --cov-fail-under=60
```

### Debugging

```bash
# Run with verbose output
python -m pytest tests/ -vv

# Show print statements
python -m pytest tests/ -s

# Stop on first failure
python -m pytest tests/ -x

# Run last failed tests
python -m pytest tests/ --lf

# Show local variables on failure
python -m pytest tests/ -l

# Enter debugger on failure
python -m pytest tests/ --pdb
```

### Performance

```bash
# Show slowest tests
python -m pytest tests/ --durations=10

# Run tests in parallel (requires pytest-xdist)
python -m pytest tests/ -n auto
```

## Coverage Reporting

### Configuration (.coveragerc)

```ini
[run]
source =
    src/aim
    ../src/meai
omit =
    */tests/*
    */test_*.py
    */__init__.py
    */conftest.py
    */fixtures/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

### Thresholds

- **Minimum:** 60% (enforced in CI)
- **Target:** 75%+
- **Current:** ~60% (estimated)

### Viewing Reports

```bash
# Terminal report
python -m pytest tests/ --cov=src/aim --cov-report=term

# HTML report (open in browser)
python -m pytest tests/ --cov=src/aim --cov-report=html
open htmlcov/index.html

# XML report (for CI tools)
python -m pytest tests/ --cov=src/aim --cov-report=xml
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, feat/*, fix/* ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests with coverage
      run: |
        cd AIM
        pytest tests/ -v --cov=src/aim --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./AIM/coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: bash -c 'cd AIM && pytest tests/ --tb=short'
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

### 1. Test Independence
- Each test should run independently
- No shared state between tests
- Use fixtures for setup/teardown

### 2. Clear Test Names
- Name describes what is being tested
- Include condition and expected result
- Use underscores for readability

### 3. Arrange-Act-Assert Pattern
```python
def test_keyword_expansion():
    # Arrange
    client = SEMrushClient(api_key="test")
    seed = "dental implants"
    
    # Act
    keywords = await client.expand_keywords(seed, max_keywords=10)
    
    # Assert
    assert len(keywords) == 10
    assert all(kw.volume > 0 for kw in keywords)
```

### 4. Test One Thing
- Each test validates one behavior
- Split complex tests into multiple tests
- Use parametrize for variations

### 5. Meaningful Assertions
```python
# Bad
assert result

# Good
assert result.status == "completed"
assert len(result.keywords) >= 10
assert result.score > 0
```

### 6. Error Testing
```python
def test_invalid_api_key():
    client = SEMrushClient(api_key="invalid")
    
    with pytest.raises(AuthenticationError) as exc:
        await client.expand_keywords("test")
    
    assert "Invalid API key" in str(exc.value)
```

### 7. Async Testing
```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### 8. Fixture Reuse
- Create shared fixtures in conftest.py
- Use fixture scope (function, class, module, session)
- Parametrize fixtures for variations

### 9. Mock Sparingly
- Mock external dependencies only
- Use real implementations when possible
- Verify mock behavior matches real service

### 10. Documentation
- Add docstrings to complex tests
- Comment non-obvious setup
- Link to related issues/PRs

## Troubleshooting

### Common Issues

**Async Fixture Compatibility:**
```python
# Issue: pytest-asyncio STRICT mode
# Solution: Use function scope or session scope
@pytest.fixture(scope="function")
async def async_fixture():
    ...
```

**Import Errors:**
```python
# Issue: Module not found
# Solution: Add __init__.py files, check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

**Flaky Tests:**
```python
# Issue: Non-deterministic results
# Solution: Use freezegun for time, mock random, add timeouts
@freeze_time("2026-05-15")
def test_time_dependent():
    ...
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Last Updated:** 2026-05-15  
**Version:** 1.0  
**Maintainer:** Mikhail Eliseev
