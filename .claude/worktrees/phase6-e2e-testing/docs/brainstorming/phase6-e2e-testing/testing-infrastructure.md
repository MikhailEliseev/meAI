# Testing Infrastructure Architecture

**Expert:** Testing Architect  
**Date:** 2026-05-14  
**Focus:** Test infrastructure architecture, fixtures  
**Status:** ✅ Completed

---

## Overview

Архитектура тестовой инфраструктуры для E2E тестирования трёхслойной event-driven системы:

```
Operator (Tactical Layer)
  ↓ Event Bus (P0-P3)
Magisters (Domain Layer)
  ↓ Event Bus (P0-P3)
Subagents (Execution Layer)
```

**Ключевые требования:**
- Изоляция тестов (каждый тест независим)
- Переиспользование фикстур (DRY principle)
- Async event flow tracking (корреляция событий)
- Mock data management (VCR pattern для API)
- Deterministic results (воспроизводимость)

---

## 1. Test Fixtures Architecture

### 1.1 Operator Fixtures

**Базовая фикстура:**

```python
@pytest.fixture
async def operator(event_bus, event_store, db_session):
    """Operator с чистым состоянием для каждого теста."""
    operator = Operator(
        event_bus=event_bus,
        event_store=event_store,
        db_session=db_session,
    )
    await operator.initialize()
    
    yield operator
    
    # Cleanup
    await operator.shutdown()
```

**Фикстура с mock magisters:**

```python
@pytest.fixture
async def operator_with_mock_magisters(operator, mock_seo_magister, mock_content_magister):
    """Operator с mock magisters для изоляции."""
    operator.register_magister("seo", mock_seo_magister)
    operator.register_magister("content", mock_content_magister)
    
    yield operator
```

**Фикстура с реальными magisters:**

```python
@pytest.fixture
async def operator_with_real_magisters(operator, seo_magister, content_magister):
    """Operator с реальными magisters для E2E тестов."""
    operator.register_magister("seo", seo_magister)
    operator.register_magister("content", content_magister)
    
    yield operator
```

### 1.2 Magister Fixtures

**Базовая фикстура SEO Magister:**

```python
@pytest.fixture
async def seo_magister(event_bus, event_store, db_session):
    """SEO Magister с чистым состоянием."""
    magister = SEOMagister(
        event_bus=event_bus,
        event_store=event_store,
        db_session=db_session,
    )
    await magister.initialize()
    
    yield magister
    
    await magister.shutdown()
```

**Фикстура с mock subagents:**

```python
@pytest.fixture
async def seo_magister_with_mock_subagents(seo_magister):
    """SEO Magister с mock subagents для изоляции."""
    mock_keyword_agent = AsyncMock(spec=KeywordResearchAgent)
    mock_competitor_agent = AsyncMock(spec=CompetitorAnalysisAgent)
    
    seo_magister.register_subagent("keyword_research", mock_keyword_agent)
    seo_magister.register_subagent("competitor_analysis", mock_competitor_agent)
    
    yield seo_magister
```

**Фикстура с реальными subagents:**

```python
@pytest.fixture
async def seo_magister_with_real_subagents(
    seo_magister,
    keyword_research_agent,
    competitor_analysis_agent,
):
    """SEO Magister с реальными subagents для E2E тестов."""
    seo_magister.register_subagent("keyword_research", keyword_research_agent)
    seo_magister.register_subagent("competitor_analysis", competitor_analysis_agent)
    
    yield seo_magister
```

### 1.3 Subagent Fixtures

**Базовая фикстура Keyword Research Agent:**

```python
@pytest.fixture
async def keyword_research_agent(event_bus, event_store, db_session):
    """Keyword Research Agent с чистым состоянием."""
    agent = KeywordResearchAgent(
        event_bus=event_bus,
        event_store=event_store,
        db_session=db_session,
    )
    await agent.initialize()
    
    yield agent
    
    await agent.shutdown()
```

**Фикстура с VCR cassettes:**

```python
@pytest.fixture
async def keyword_research_agent_with_vcr(keyword_research_agent, vcr_cassette):
    """Keyword Research Agent с VCR для API mocking."""
    keyword_research_agent.api_client.use_cassette(vcr_cassette)
    
    yield keyword_research_agent
```

**Фикстура с mock API client:**

```python
@pytest.fixture
async def keyword_research_agent_with_mock_api(keyword_research_agent):
    """Keyword Research Agent с mock API client для изоляции."""
    mock_api = AsyncMock(spec=SEMrushClient)
    mock_api.expand_keywords.return_value = MOCK_KEYWORD_DATA
    
    keyword_research_agent.api_client = mock_api
    
    yield keyword_research_agent
```

### 1.4 Infrastructure Fixtures

**Event Bus фикстура:**

```python
@pytest.fixture
async def event_bus(db_session):
    """Event Bus с чистым состоянием."""
    bus = EventBus(db_session=db_session)
    await bus.initialize()
    
    yield bus
    
    # Cleanup: очистить все события
    await bus.clear_all()
```

**Event Store фикстура:**

```python
@pytest.fixture
async def event_store(db_session):
    """Event Store с чистым состоянием."""
    store = EventStore(db_session=db_session)
    await store.initialize()
    
    yield store
    
    # Cleanup: очистить все события
    await store.clear_all()
```

**Database Session фикстура:**

```python
@pytest.fixture
async def db_session():
    """Async database session для тестов."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()
```


---

## 2. Event Bus Testing Infrastructure

### 2.1 Event Flow Tracking

**Проблема:** Как отследить цепочку событий в async системе?

**Решение:** Correlation ID + Event Collector

```python
class EventCollector:
    """Собирает события для анализа в тестах."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.collected_events: list[BaseEvent] = []
        self._subscription_id: str | None = None
    
    async def start(self):
        """Начать сбор событий."""
        self._subscription_id = await self.event_bus.subscribe(
            event_type="*",  # Все типы событий
            handler=self._collect_event,
        )
    
    async def stop(self):
        """Остановить сбор событий."""
        if self._subscription_id:
            await self.event_bus.unsubscribe(self._subscription_id)
    
    async def _collect_event(self, event: BaseEvent):
        """Собрать событие."""
        self.collected_events.append(event)
    
    def get_by_correlation(self, correlation_id: str) -> list[BaseEvent]:
        """Получить все события по correlation_id."""
        return [
            e for e in self.collected_events
            if e.correlation_id == correlation_id
        ]
    
    def get_by_type(self, event_type: str) -> list[BaseEvent]:
        """Получить все события по типу."""
        return [
            e for e in self.collected_events
            if e.type == event_type
        ]
```

**Фикстура:**

```python
@pytest.fixture
async def event_collector(event_bus):
    """Event Collector для отслеживания событий."""
    collector = EventCollector(event_bus)
    await collector.start()
    
    yield collector
    
    await collector.stop()
```

**Использование в тестах:**

```python
async def test_operator_delegates_to_magister(
    operator_with_real_magisters,
    event_collector,
):
    """Проверить делегирование задачи от Operator к Magister."""
    # Создать задачу
    task = Task(
        id="task-1",
        description="Analyze competitor keywords",
        capability="seo",
    )
    
    # Делегировать задачу
    await operator_with_real_magisters.receive_task(task)
    
    # Дождаться завершения
    await asyncio.sleep(0.5)
    
    # Проверить цепочку событий
    events = event_collector.get_by_correlation(task.id)
    
    assert len(events) >= 2
    assert events[0].type == "task.created"
    assert events[0].source == "operator"
    assert events[1].type == "task.delegated"
    assert events[1].target == "seo_magister"
```

### 2.2 Async Synchronization Patterns

**Проблема:** Как дождаться завершения async цепочки событий?

**Решение 1: asyncio.Event для синхронизации**

```python
class EventWaiter:
    """Ожидает конкретное событие."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._events: dict[str, asyncio.Event] = {}
        self._results: dict[str, BaseEvent] = {}
    
    async def wait_for(
        self,
        event_type: str,
        correlation_id: str,
        timeout: float = 5.0,
    ) -> BaseEvent:
        """Дождаться события с timeout."""
        # Создать Event для синхронизации
        event_key = f"{event_type}:{correlation_id}"
        self._events[event_key] = asyncio.Event()
        
        # Подписаться на событие
        subscription_id = await self.event_bus.subscribe(
            event_type=event_type,
            handler=lambda e: self._handle_event(e, event_key),
        )
        
        try:
            # Дождаться события с timeout
            await asyncio.wait_for(
                self._events[event_key].wait(),
                timeout=timeout,
            )
            return self._results[event_key]
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Event {event_type} with correlation {correlation_id} "
                f"not received within {timeout}s"
            )
        finally:
            await self.event_bus.unsubscribe(subscription_id)
    
    async def _handle_event(self, event: BaseEvent, event_key: str):
        """Обработать событие."""
        self._results[event_key] = event
        self._events[event_key].set()
```

**Использование:**

```python
async def test_magister_completes_task(
    seo_magister_with_real_subagents,
    event_bus,
):
    """Проверить завершение задачи Magister."""
    waiter = EventWaiter(event_bus)
    
    # Создать задачу
    task = Task(id="task-1", description="Research keywords")
    
    # Делегировать задачу
    await seo_magister_with_real_subagents.receive_task(task)
    
    # Дождаться завершения
    completion_event = await waiter.wait_for(
        event_type="task.completed",
        correlation_id=task.id,
        timeout=10.0,
    )
    
    assert completion_event.source == "seo_magister"
    assert completion_event.metadata["status"] == "success"
```

**Решение 2: Event Store replay для проверки**

```python
async def test_event_chain_integrity(
    operator_with_real_magisters,
    event_store,
):
    """Проверить целостность цепочки событий."""
    # Создать задачу
    task = Task(id="task-1", description="Analyze competitor")
    
    # Делегировать задачу
    await operator_with_real_magisters.receive_task(task)
    
    # Дождаться завершения
    await asyncio.sleep(1.0)
    
    # Получить все события по correlation_id
    events = await event_store.get_by_correlation(task.id)
    
    # Проверить последовательность
    assert events[0].type == "task.created"
    assert events[1].type == "task.delegated"
    assert events[2].type == "task.started"
    assert events[-1].type == "task.completed"
    
    # Проверить reply_to chain
    for i in range(1, len(events)):
        assert events[i].reply_to == events[i-1].id
```

### 2.3 Priority Testing

**Проблема:** Как проверить, что P0 события обрабатываются раньше P3?

**Решение:** Timestamp analysis

```python
async def test_priority_ordering(event_bus, event_collector):
    """Проверить приоритизацию событий."""
    # Опубликовать события в обратном порядке приоритета
    await event_bus.publish(
        BaseEvent(
            type="low_priority",
            source="test",
            priority=3,  # P3 - lowest
        )
    )
    await event_bus.publish(
        BaseEvent(
            type="high_priority",
            source="test",
            priority=0,  # P0 - highest
        )
    )
    await event_bus.publish(
        BaseEvent(
            type="medium_priority",
            source="test",
            priority=1,  # P1
        )
    )
    
    # Дождаться обработки
    await asyncio.sleep(0.5)
    
    # Проверить порядок обработки
    events = event_collector.collected_events
    
    assert events[0].type == "high_priority"  # P0 first
    assert events[1].type == "medium_priority"  # P1 second
    assert events[2].type == "low_priority"  # P3 last
```

### 2.4 Error Propagation Testing

**Проблема:** Как проверить, что ошибки субагента доходят до Operator?

**Решение:** Error event tracking

```python
async def test_error_propagation(
    operator_with_real_magisters,
    event_collector,
):
    """Проверить распространение ошибок вверх по иерархии."""
    # Создать задачу, которая вызовет ошибку
    task = Task(
        id="task-1",
        description="Invalid task that will fail",
        capability="seo",
    )
    
    # Делегировать задачу
    await operator_with_real_magisters.receive_task(task)
    
    # Дождаться обработки
    await asyncio.sleep(1.0)
    
    # Проверить цепочку ошибок
    events = event_collector.get_by_correlation(task.id)
    error_events = [e for e in events if e.type == "task.failed"]
    
    assert len(error_events) >= 1
    
    # Проверить, что ошибка дошла до Operator
    operator_error = next(
        (e for e in error_events if e.target == "operator"),
        None,
    )
    assert operator_error is not None
    assert "error" in operator_error.metadata
```


---

## 3. Test Data Management

### 3.1 Mock Data Organization

**Структура:**

```
tests/
├── fixtures/
│   ├── __init__.py
│   ├── keyword_data.py          # Keyword research mock data
│   ├── competitor_data.py       # Competitor analysis mock data
│   ├── content_data.py          # Content generation mock data
│   ├── ads_data.py              # Ads campaign mock data
│   └── analytics_data.py        # Analytics mock data
└── cassettes/                   # VCR cassettes для API
    ├── semrush/
    │   ├── keyword_magic_tool.yaml
    │   └── domain_overview.yaml
    ├── ahrefs/
    │   ├── keywords_explorer.yaml
    │   └── site_explorer.yaml
    ├── ga4/
    │   └── run_report.yaml
    └── yandex_metrica/
        └── get_stats.yaml
```

**Паттерн mock data файла:**

```python
# tests/fixtures/keyword_data.py

from aim.subagents.schemas.api_responses import KeywordDataUnified

# Константы для переиспользования
MOCK_KEYWORD_1 = KeywordDataUnified(
    keyword="dental implants",
    volume=12000,
    difficulty=75,
    cpc=15.50,
    intent="commercial",
    trend="stable",
)

MOCK_KEYWORD_2 = KeywordDataUnified(
    keyword="dental implants cost",
    volume=8000,
    difficulty=65,
    cpc=12.30,
    intent="commercial",
    trend="growing",
)

# Наборы данных для разных сценариев
MOCK_KEYWORD_SET_SMALL = [MOCK_KEYWORD_1, MOCK_KEYWORD_2]

MOCK_KEYWORD_SET_LARGE = [
    MOCK_KEYWORD_1,
    MOCK_KEYWORD_2,
    # ... 98 more keywords
]

# Edge cases
MOCK_KEYWORD_ZERO_VOLUME = KeywordDataUnified(
    keyword="rare medical term",
    volume=0,
    difficulty=10,
    cpc=0.0,
    intent="informational",
    trend="stable",
)

MOCK_KEYWORD_HIGH_DIFFICULTY = KeywordDataUnified(
    keyword="best dentist",
    volume=50000,
    difficulty=95,
    cpc=25.00,
    intent="commercial",
    trend="stable",
)

# API response formats
SEMRUSH_MOCK_RESPONSE = {
    "data": [
        {
            "keyword": "dental implants",
            "search_volume": 12000,
            "keyword_difficulty": 75,
            "cpc": 15.50,
            "intent": "C",
            "trend": [12000, 12100, 11900, 12000],
        }
    ]
}

AHREFS_MOCK_RESPONSE = {
    "keywords": [
        {
            "keyword": "dental implants",
            "volume": 12000,
            "difficulty": 75,
            "cpc": 15.50,
            "parent_topic": "dental procedures",
        }
    ]
}
```

### 3.2 VCR Pattern для API Mocking

**Установка pytest-vcr:**

```bash
pip install pytest-vcr
```

**Конфигурация в conftest.py:**

```python
import pytest
import vcr

@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration для всех тестов."""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",  # Record once, replay forever
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "cassette_library_dir": "tests/cassettes",
    }

@pytest.fixture
def vcr_cassette_name(request):
    """Автоматическое имя cassette по имени теста."""
    return f"{request.node.name}.yaml"
```

**Использование в тестах:**

```python
@pytest.mark.vcr
async def test_semrush_keyword_expansion(keyword_research_agent):
    """Тест с автоматической записью/воспроизведением API."""
    # Первый запуск: реальный API call, запись в cassette
    # Последующие запуски: воспроизведение из cassette (zero cost)
    
    keywords = await keyword_research_agent.expand_keywords(
        seed_keyword="dental implants",
        max_keywords=100,
    )
    
    assert len(keywords) >= 100
    assert keywords[0].keyword == "dental implants"
```

**Организация cassettes по API client:**

```python
@pytest.mark.vcr(cassette_name="semrush/keyword_magic_tool.yaml")
async def test_semrush_api():
    """Тест с явным указанием cassette."""
    pass

@pytest.mark.vcr(cassette_name="ahrefs/keywords_explorer.yaml")
async def test_ahrefs_api():
    """Тест с явным указанием cassette."""
    pass
```

### 3.3 Fixture Composition

**Проблема:** Как переиспользовать фикстуры для разных сценариев?

**Решение:** Композиция фикстур

```python
# Базовые фикстуры
@pytest.fixture
def mock_keyword_data():
    """Базовые mock данные для keywords."""
    return MOCK_KEYWORD_SET_SMALL

@pytest.fixture
def mock_competitor_data():
    """Базовые mock данные для competitors."""
    return MOCK_COMPETITOR_SET

# Композитные фикстуры
@pytest.fixture
def seo_analysis_data(mock_keyword_data, mock_competitor_data):
    """Полный набор данных для SEO анализа."""
    return {
        "keywords": mock_keyword_data,
        "competitors": mock_competitor_data,
    }

@pytest.fixture
async def seo_magister_with_mock_data(
    seo_magister,
    seo_analysis_data,
):
    """SEO Magister с предзагруженными mock данными."""
    # Inject mock data
    seo_magister._keyword_cache = seo_analysis_data["keywords"]
    seo_magister._competitor_cache = seo_analysis_data["competitors"]
    
    yield seo_magister
```

### 3.4 Parametrized Tests для Edge Cases

**Проблема:** Как тестировать множество edge cases без дублирования кода?

**Решение:** pytest.mark.parametrize

```python
@pytest.mark.parametrize(
    "keyword_data,expected_result",
    [
        (MOCK_KEYWORD_ZERO_VOLUME, "suggest_alternatives"),
        (MOCK_KEYWORD_HIGH_DIFFICULTY, "warn_high_difficulty"),
        (MOCK_KEYWORD_NEGATIVE_CPC, "reject_invalid"),
        (MOCK_KEYWORD_MISSING_INTENT, "infer_intent"),
    ],
    ids=[
        "zero_volume",
        "high_difficulty",
        "negative_cpc",
        "missing_intent",
    ],
)
async def test_keyword_validation_edge_cases(
    keyword_research_agent,
    keyword_data,
    expected_result,
):
    """Тест edge cases для keyword validation."""
    result = await keyword_research_agent.validate_keyword(keyword_data)
    assert result.action == expected_result
```

### 3.5 Factory Pattern для Test Data

**Проблема:** Как создавать сложные test objects с вариациями?

**Решение:** Factory functions

```python
def create_task(
    task_id: str = "task-1",
    description: str = "Test task",
    capability: str = "seo",
    priority: int = 1,
    **kwargs,
) -> Task:
    """Factory для создания Task с defaults."""
    return Task(
        id=task_id,
        description=description,
        capability=capability,
        priority=priority,
        **kwargs,
    )

def create_keyword_data(
    keyword: str = "test keyword",
    volume: int = 1000,
    difficulty: int = 50,
    **kwargs,
) -> KeywordDataUnified:
    """Factory для создания KeywordDataUnified с defaults."""
    return KeywordDataUnified(
        keyword=keyword,
        volume=volume,
        difficulty=difficulty,
        cpc=10.0,
        intent="informational",
        trend="stable",
        **kwargs,
    )
```

**Использование:**

```python
async def test_operator_handles_multiple_tasks():
    """Тест обработки множества задач."""
    tasks = [
        create_task(task_id=f"task-{i}", capability="seo")
        for i in range(10)
    ]
    
    for task in tasks:
        await operator.receive_task(task)
    
    # Assertions...
```


---

## 4. Test Organization

### 4.1 Directory Structure

```
tests/
├── conftest.py                  # Глобальные фикстуры и конфигурация
├── fixtures/                    # Mock data и test data
│   ├── __init__.py
│   ├── keyword_data.py
│   ├── competitor_data.py
│   ├── content_data.py
│   ├── ads_data.py
│   └── analytics_data.py
├── cassettes/                   # VCR cassettes для API
│   ├── semrush/
│   ├── ahrefs/
│   ├── ga4/
│   └── yandex_metrica/
├── unit/                        # Unit tests (изолированные)
│   ├── test_event_bus.py
│   ├── test_event_store.py
│   ├── test_base_agent.py
│   └── api_clients/
│       ├── test_base.py
│       ├── test_semrush.py
│       └── test_ahrefs.py
├── integration/                 # Integration tests (2-3 компонента)
│   ├── test_operator_magister.py
│   ├── test_magister_subagent.py
│   └── test_event_flow.py
└── e2e/                         # End-to-end tests (полный workflow)
    ├── test_seo_workflow.py
    ├── test_content_workflow.py
    ├── test_ads_workflow.py
    └── test_multi_magister_workflow.py
```

### 4.2 Naming Conventions

**Test Files:**
- `test_<component>.py` — Unit tests для компонента
- `test_<component1>_<component2>.py` — Integration tests
- `test_<workflow>_workflow.py` — E2E tests

**Test Functions:**
- `test_<action>_<expected_result>` — Базовый паттерн
- `test_<component>_<action>_<condition>` — С условием
- `test_<workflow>_<scenario>` — Workflow сценарий

**Примеры:**

```python
# Unit test
async def test_event_bus_publishes_event()

# Integration test
async def test_operator_delegates_to_magister_successfully()

# E2E test
async def test_seo_workflow_completes_with_real_apis()

# Edge case
async def test_magister_handles_subagent_failure_gracefully()

# Performance test
async def test_parallel_magisters_complete_within_timeout()
```

### 4.3 Test Markers

**Конфигурация в pytest.ini:**

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
```

**Использование:**

```python
@pytest.mark.unit
async def test_event_bus_priority_queue():
    """Fast unit test."""
    pass

@pytest.mark.integration
@pytest.mark.vcr
async def test_magister_with_subagents():
    """Integration test with VCR."""
    pass

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.real_api
async def test_full_seo_workflow_with_real_apis():
    """Expensive E2E test with real APIs."""
    pass
```

**Запуск тестов по маркерам:**

```bash
# Только unit tests (быстрые)
pytest -m unit

# Integration + E2E (без real API)
pytest -m "integration or e2e" -m "not real_api"

# Все тесты кроме slow
pytest -m "not slow"

# Только VCR tests (zero cost)
pytest -m vcr
```

### 4.4 Test Isolation Strategy

**Уровни изоляции:**

1. **Database Isolation** — каждый тест получает чистую in-memory БД
2. **Event Bus Isolation** — каждый тест получает свой Event Bus
3. **Event Store Isolation** — каждый тест получает свой Event Store
4. **Agent Isolation** — каждый тест создаёт новые экземпляры агентов

**Реализация через фикстуры:**

```python
@pytest.fixture
async def isolated_test_environment():
    """Полностью изолированное окружение для теста."""
    # Create isolated components
    db_session = await create_test_db_session()
    event_bus = EventBus(db_session=db_session)
    event_store = EventStore(db_session=db_session)
    
    await event_bus.initialize()
    await event_store.initialize()
    
    yield {
        "db_session": db_session,
        "event_bus": event_bus,
        "event_store": event_store,
    }
    
    # Cleanup
    await event_bus.clear_all()
    await event_store.clear_all()
    await db_session.close()
```

### 4.5 Conftest.py Organization

**Структура conftest.py:**

```python
# tests/conftest.py

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")

# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
async def db_session():
    """Async database session для тестов."""
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
async def event_bus(db_session):
    """Event Bus с чистым состоянием."""
    bus = EventBus(db_session=db_session)
    await bus.initialize()
    
    yield bus
    
    await bus.clear_all()

@pytest.fixture
async def event_store(db_session):
    """Event Store с чистым состоянием."""
    store = EventStore(db_session=db_session)
    await store.initialize()
    
    yield store
    
    await store.clear_all()

# ============================================================================
# OPERATOR FIXTURES
# ============================================================================

@pytest.fixture
async def operator(event_bus, event_store, db_session):
    """Operator с чистым состоянием."""
    operator = Operator(
        event_bus=event_bus,
        event_store=event_store,
        db_session=db_session,
    )
    await operator.initialize()
    
    yield operator
    
    await operator.shutdown()

# ============================================================================
# MAGISTER FIXTURES
# ============================================================================

@pytest.fixture
async def seo_magister(event_bus, event_store, db_session):
    """SEO Magister с чистым состоянием."""
    magister = SEOMagister(
        event_bus=event_bus,
        event_store=event_store,
        db_session=db_session,
    )
    await magister.initialize()
    
    yield magister
    
    await magister.shutdown()

# ============================================================================
# SUBAGENT FIXTURES
# ============================================================================

@pytest.fixture
async def keyword_research_agent(event_bus, event_store, db_session):
    """Keyword Research Agent с чистым состоянием."""
    agent = KeywordResearchAgent(
        event_bus=event_bus,
        event_store=event_store,
        db_session=db_session,
    )
    await agent.initialize()
    
    yield agent
    
    await agent.shutdown()

# ============================================================================
# TEST UTILITIES
# ============================================================================

@pytest.fixture
async def event_collector(event_bus):
    """Event Collector для отслеживания событий."""
    collector = EventCollector(event_bus)
    await collector.start()
    
    yield collector
    
    await collector.stop()

@pytest.fixture
def event_waiter(event_bus):
    """Event Waiter для синхронизации."""
    return EventWaiter(event_bus)
```

---

## 5. Implementation Roadmap

### Phase 1: Infrastructure Setup (2 hours)

**Цель:** Создать базовую тестовую инфраструктуру

**Задачи:**
1. Создать `tests/conftest.py` с базовыми фикстурами
2. Создать `tests/fixtures/` с mock data
3. Настроить pytest.ini с маркерами
4. Создать структуру директорий (unit/, integration/, e2e/)

**Deliverables:**
- ✅ conftest.py с db_session, event_bus, event_store фикстурами
- ✅ pytest.ini с маркерами (unit, integration, e2e, vcr, real_api, slow)
- ✅ Структура директорий tests/

### Phase 2: Event Bus Testing (3 hours)

**Цель:** Реализовать инфраструктуру для тестирования Event Bus

**Задачи:**
1. Создать EventCollector для отслеживания событий
2. Создать EventWaiter для async синхронизации
3. Написать unit tests для Event Bus (priority, pub/sub)
4. Написать integration tests для event flow

**Deliverables:**
- ✅ EventCollector class в tests/utils/event_collector.py
- ✅ EventWaiter class в tests/utils/event_waiter.py
- ✅ tests/unit/test_event_bus.py (10+ tests)
- ✅ tests/integration/test_event_flow.py (5+ tests)

### Phase 3: Operator & Magister Fixtures (2 hours)

**Цель:** Создать фикстуры для Operator и Magisters

**Задачи:**
1. Создать operator фикстуры (базовая, с mock magisters, с реальными)
2. Создать magister фикстуры (базовая, с mock subagents, с реальными)
3. Написать integration tests для Operator → Magister

**Deliverables:**
- ✅ Operator фикстуры в conftest.py
- ✅ Magister фикстуры в conftest.py
- ✅ tests/integration/test_operator_magister.py (8+ tests)

### Phase 4: Subagent Fixtures & VCR (3 hours)

**Цель:** Создать фикстуры для субагентов и настроить VCR

**Задачи:**
1. Создать subagent фикстуры (базовая, с VCR, с mock API)
2. Настроить pytest-vcr
3. Записать cassettes для основных API (SEMrush, Ahrefs, GA4)
4. Написать integration tests для Magister → Subagent

**Deliverables:**
- ✅ Subagent фикстуры в conftest.py
- ✅ VCR конфигурация в conftest.py
- ✅ tests/cassettes/ с записанными cassettes
- ✅ tests/integration/test_magister_subagent.py (10+ tests)

### Phase 5: E2E Tests (4 hours)

**Цель:** Написать end-to-end тесты для полных workflow

**Задачи:**
1. Написать E2E тест для SEO workflow (Operator → SEO Magister → Subagents)
2. Написать E2E тест для Content workflow
3. Написать E2E тест для Ads workflow
4. Написать E2E тест для параллельного выполнения 4 Magisters

**Deliverables:**
- ✅ tests/e2e/test_seo_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_content_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_ads_workflow.py (5+ scenarios)
- ✅ tests/e2e/test_multi_magister_workflow.py (3+ scenarios)

### Phase 6: Error Handling & Edge Cases (2 hours)

**Цель:** Тестирование error propagation и edge cases

**Задачи:**
1. Написать тесты для error propagation (subagent → magister → operator)
2. Написать тесты для edge cases (timeout, retry, circuit breaker)
3. Написать тесты для graceful degradation (fallback chains)

**Deliverables:**
- ✅ tests/integration/test_error_propagation.py (8+ tests)
- ✅ tests/integration/test_edge_cases.py (10+ tests)

### Phase 7: Documentation & CI Integration (1 hour)

**Цель:** Документация и интеграция в CI

**Задачи:**
1. Написать README.md для tests/
2. Создать GitHub Actions workflow для тестов
3. Настроить coverage reporting

**Deliverables:**
- ✅ tests/README.md с инструкциями
- ✅ .github/workflows/tests.yml
- ✅ Coverage badge в README

---

## 6. Success Criteria

**Infrastructure:**
- ✅ conftest.py с 15+ фикстурами
- ✅ EventCollector и EventWaiter utilities
- ✅ VCR конфигурация с cassettes для всех API
- ✅ Структура директорий (unit/, integration/, e2e/)

**Test Coverage:**
- ✅ Unit tests: 30+ tests (Event Bus, Event Store, Base classes)
- ✅ Integration tests: 25+ tests (Operator ↔ Magister ↔ Subagent)
- ✅ E2E tests: 15+ tests (полные workflows)
- ✅ Total: 70+ tests

**Quality:**
- ✅ Все тесты проходят (100% pass rate)
- ✅ Изоляция тестов (каждый тест независим)
- ✅ Deterministic results (воспроизводимость)
- ✅ Fast execution (< 30s для unit+integration с VCR)

**Documentation:**
- ✅ README.md с инструкциями по запуску
- ✅ Комментарии в фикстурах
- ✅ Примеры использования в docstrings

---

## 7. Estimated Effort

**Total:** 17 hours

| Phase | Hours | Priority |
|-------|-------|----------|
| 1. Infrastructure Setup | 2h | P0 |
| 2. Event Bus Testing | 3h | P0 |
| 3. Operator & Magister Fixtures | 2h | P0 |
| 4. Subagent Fixtures & VCR | 3h | P1 |
| 5. E2E Tests | 4h | P1 |
| 6. Error Handling & Edge Cases | 2h | P2 |
| 7. Documentation & CI | 1h | P2 |

**Можно распараллелить:**
- Phase 1-2 (Infrastructure + Event Bus) — последовательно
- Phase 3-4 (Fixtures) — можно параллельно после Phase 2
- Phase 5-6 (E2E + Errors) — можно параллельно после Phase 4

**Минимальный путь (P0 only):** 7 hours  
**Полный путь (P0+P1+P2):** 17 hours

