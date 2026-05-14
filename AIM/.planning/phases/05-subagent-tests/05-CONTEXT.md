---
phase: 5
title: Subagent Tests
created: 2026-05-14
status: ready_for_planning
decisions_count: 6
---

# Phase 5: Subagent Tests - Implementation Context

## Overview

Тестирование domain-specific субагентов (Keyword Research, Competitor Analysis, Content Generation, Campaign Management, Data Collection) с фокусом на business logic, API integration, и production patterns. Глубокое тестирование с максимальным качеством.

**Target:** 15+ tests (3+ per subagent), 4 hours

---

## Decision 1: Test Strategy - Deep Quality Over Speed

**Выбор:** Глубокое тестирование каждого субагента (не поверхностное)

**Детали:**

### Принцип: Quality Over Speed (из CLAUDE.md)
- Каждый субагент тестируется глубоко, не поверхностно
- Проверяем не только "работает ли", но и "работает ли правильно"
- Тестируем edge cases, error handling, compliance, cost control
- Время выполнения не критично (1 минута vs 1 час vs 1 день)

### Что тестируем для каждого субагента:

**1. Business Logic (core functionality):**
- Основная функциональность работает корректно
- Результаты соответствуют ожиданиям
- Алгоритмы работают правильно (clustering, prioritization, etc.)

**2. API Integration (external dependencies):**
- API clients вызываются корректно
- Параметры передаются правильно
- Ответы обрабатываются корректно
- Fallback работает при сбое primary API

**3. Production Patterns (resilience):**
- Circuit breaker срабатывает при сбоях
- Retry logic работает корректно
- Rate limiting соблюдается
- Caching работает (не делаем повторные запросы)
- Budget guard предотвращает перерасход

**4. Compliance (medical domain):**
- FDA/HIPAA compliance проверяется
- Risky keywords блокируются
- Audit trail сохраняется
- Compliance actions выполняются

**5. Error Handling (robustness):**
- Graceful degradation при partial failures
- Понятные error messages
- Не падаем при unexpected input
- Логируем все ошибки

**6. Data Validation (correctness):**
- Input validation работает
- Output validation работает
- Pydantic schemas проверяют типы
- Нет invalid data в результатах

**Why:** Поверхностное тестирование не даёт уверенности в production readiness. Глубокое тестирование находит проблемы до production.

---

## Decision 2: Test Scope - 5 Critical Subagents

**Выбор:** Тестируем 5 критических субагентов (по 3+ теста каждый)

**Детали:**

### 1. Keyword Research Agent (4 tests)

**Файл:** `tests/unit/test_keyword_research_agent.py`

**Тесты:**
1. `test_keyword_expansion_success` - успешное расширение keywords через SEMrush
   - Проверяем: API call, результаты, cost tracking, caching
2. `test_keyword_expansion_with_fallback` - fallback на Ahrefs при сбое SEMrush
   - Проверяем: circuit breaker, fallback logic, результаты
3. `test_compliance_blocking` - блокировка risky keywords (FDA/HIPAA)
   - Проверяем: compliance checker, audit trail, blocked keywords
4. `test_priority_calculation` - расчёт приоритета с medical boost
   - Проверяем: priority calculator, medical boost, tier assignment

**Существующий код:** `src/aim/subagents/keyword_research_agent.py` (production-ready)

### 2. Content Gap Analysis Agent (3 tests)

**Файл:** `tests/unit/test_content_gap_analysis_agent.py`

**Тесты:**
1. `test_gap_detection_success` - обнаружение content gaps через SERP overlap
   - Проверяем: SERP fetching, overlap calculation, gap identification
2. `test_competitor_content_analysis` - анализ контента конкурентов
   - Проверяем: content extraction, quality metrics, recommendations
3. `test_brief_generation` - генерация content brief на основе gaps
   - Проверяем: brief structure, keyword integration, quality guidelines

**Существующий код:** `src/aim/subagents/content_gap_analysis_agent.py`

### 3. Content Writer Agent (3 tests)

**Файл:** `tests/unit/test_content_writer_agent.py`

**Тесты:**
1. `test_content_generation_success` - генерация контента с SEO optimization
   - Проверяем: LLM call, SEO optimization, quality validation
2. `test_content_quality_validation` - проверка качества контента
   - Проверяем: readability, keyword density, structure, compliance
3. `test_content_revision` - ревизия контента на основе feedback
   - Проверяем: feedback processing, revision logic, improvement

**Существующий код:** `src/aim/subagents/content_writer_agent.py`

### 4. Ads Campaign Creator Agent (3 tests)

**Файл:** `tests/unit/test_ads_campaign_creator_agent.py`

**Тесты:**
1. `test_campaign_creation_success` - создание кампании в Яндекс.Директ
   - Проверяем: Yandex Direct API call, campaign structure, budget allocation
2. `test_ad_copy_generation` - генерация ad copy с compliance
   - Проверяем: ad copy quality, compliance check, character limits
3. `test_bid_strategy_optimization` - оптимизация bid strategy
   - Проверяем: bid calculation, budget optimization, ROI prediction

**Существующий код:** `src/aim/subagents/ads_campaign_creator_agent.py`

### 5. Analytics Agent (3 tests)

**Файл:** `tests/unit/test_analytics_agent.py`

**Тесты:**
1. `test_metrics_collection_success` - сбор метрик из GA4/Yandex.Metrica
   - Проверяем: API calls, data aggregation, storage
2. `test_data_validation` - валидация собранных данных
   - Проверяем: data quality, outlier detection, completeness
3. `test_report_generation` - генерация отчёта с insights
   - Проверяем: report structure, insights quality, recommendations

**Существующий код:** `src/aim/subagents/analytics_agent.py`

**Total:** 16 tests (4+3+3+3+3)

**Why:** Эти 5 субагентов критичны для работы агентства. Каждый тест проверяет ключевую функциональность.

---

## Decision 3: Mocking Strategy - Hybrid with Real Business Logic

**Выбор:** Гибридный подход (real business logic + mocked external APIs)

**Детали:**

### Unit Tests (16 tests)

**Что мокируем:**
- ✅ External API clients (SEMrush, Ahrefs, GA4, Yandex)
- ✅ LLM calls (OpenAI, Anthropic)
- ✅ Database operations (SQLAlchemy)
- ✅ File system operations (Obsidian vault writes)

**Что НЕ мокируем (real code):**
- ❌ Business logic субагента (execute_task, analyze, process)
- ❌ Compliance checker (FDA/HIPAA rules)
- ❌ Priority calculator (scoring algorithms)
- ❌ Data validation (Pydantic schemas)
- ❌ Error handling (try/except blocks)
- ❌ Cost tracking (budget guard)

**Pattern:**
```python
@pytest.fixture
def mock_api_clients():
    """Mock external API clients"""
    return {
        "semrush": AsyncMock(spec=SEMrushClient),
        "ahrefs": AsyncMock(spec=AhrefsClient),
        "ga4": AsyncMock(spec=GA4Client),
        "yandex": AsyncMock(spec=YandexMetricaClient),
    }

@pytest.fixture
def keyword_research_agent(mock_api_clients):
    """Real agent with mocked API clients"""
    agent = KeywordResearchAgent(
        skip_api_validation=True,  # Skip API key check
    )
    # Inject mocked clients
    agent.semrush_client = mock_api_clients["semrush"]
    agent.ahrefs_client = mock_api_clients["ahrefs"]
    return agent
```

**Why:** Unit tests проверяют business logic в изоляции, но используют реальный код субагента (не моки).

---

## Decision 4: Test Data Strategy - Realistic Medical Domain Data

**Выбор:** Реалистичные данные из medical marketing domain

**Детали:**

### Mock Data Fixtures

**Файл:** `tests/fixtures/subagent_data.py`

**Keyword Research Data:**
```python
MEDICAL_KEYWORDS = [
    {
        "keyword": "dental implants cost",
        "volume": 12000,
        "difficulty": 65,
        "cpc": 8.50,
        "intent": "commercial",
        "compliance_risk": "low",
    },
    {
        "keyword": "buy oxycodone online",  # Risky keyword
        "volume": 5000,
        "difficulty": 45,
        "cpc": 12.00,
        "intent": "transactional",
        "compliance_risk": "high",  # Should be blocked
    },
    {
        "keyword": "teeth whitening near me",
        "volume": 8000,
        "difficulty": 55,
        "cpc": 6.20,
        "intent": "local",
        "compliance_risk": "low",
    },
]
```

**Content Gap Data:**
```python
COMPETITOR_CONTENT = [
    {
        "url": "https://competitor.com/dental-implants-guide",
        "title": "Complete Guide to Dental Implants",
        "word_count": 2500,
        "keywords": ["dental implants", "implant cost", "implant procedure"],
        "quality_score": 85,
    },
]
```

**Analytics Data:**
```python
GA4_METRICS = {
    "sessions": 15000,
    "users": 12000,
    "bounce_rate": 0.45,
    "avg_session_duration": 180,
    "conversions": 150,
    "conversion_rate": 0.01,
}
```

**Why:** Реалистичные данные из medical domain помогают найти domain-specific проблемы.

---

## Decision 5: Error Handling Testing - All Failure Scenarios

**Выбор:** Тестируем все критические failure scenarios

**Детали:**

### Scenario 1: API Failures (circuit breaker)

**Test:**
```python
@pytest.mark.asyncio
async def test_keyword_expansion_api_failure(keyword_research_agent, mock_api_clients):
    # SEMrush fails 5 times (circuit breaker opens)
    mock_api_clients["semrush"].expand_keywords.side_effect = [
        ConnectionError("API timeout"),
        ConnectionError("API timeout"),
        ConnectionError("API timeout"),
        ConnectionError("API timeout"),
        ConnectionError("API timeout"),
    ]
    
    # Ahrefs fallback succeeds
    mock_api_clients["ahrefs"].expand_keywords.return_value = [
        {"keyword": "dental implants", "volume": 10000}
    ]
    
    result = await keyword_research_agent.execute_task(task)
    
    # Проверяем fallback сработал
    assert result.status == "success"
    assert result.data["source"] == "ahrefs"
    assert mock_api_clients["ahrefs"].expand_keywords.call_count == 1
```

### Scenario 2: Compliance Violations (blocking)

**Test:**
```python
@pytest.mark.asyncio
async def test_compliance_blocking(keyword_research_agent):
    task = Task(
        task_id="test-123",
        task_type="keyword_research",
        parameters={"seed_keyword": "buy oxycodone online"},  # Risky
    )
    
    result = await keyword_research_agent.execute_task(task)
    
    # Проверяем блокировку
    assert result.status == "blocked"
    assert "compliance" in result.error.lower()
    assert result.data["risk_level"] == "high"
    assert result.data["blocked_keywords"] == ["buy oxycodone online"]
```

### Scenario 3: Budget Overrun (guard)

**Test:**
```python
@pytest.mark.asyncio
async def test_budget_guard(keyword_research_agent, mock_api_clients):
    # Mock expensive API call ($10 per request)
    mock_api_clients["semrush"].expand_keywords.return_value = []
    mock_api_clients["semrush"].get_cost.return_value = 10.0
    
    task = Task(
        task_id="test-123",
        task_type="keyword_research",
        parameters={"seed_keyword": "dental implants", "max_cost_usd": 5.0},
    )
    
    result = await keyword_research_agent.execute_task(task)
    
    # Проверяем блокировку по бюджету
    assert result.status == "failed"
    assert "budget" in result.error.lower()
    assert keyword_research_agent.total_cost_usd == 0.0  # No charge
```

### Scenario 4: Invalid Input (validation)

**Test:**
```python
@pytest.mark.asyncio
async def test_invalid_input(keyword_research_agent):
    task = Task(
        task_id="test-123",
        task_type="keyword_research",
        parameters={"seed_keyword": ""},  # Empty keyword
    )
    
    result = await keyword_research_agent.execute_task(task)
    
    # Проверяем валидацию
    assert result.status == "failed"
    assert "invalid" in result.error.lower()
```

**Why:** Тестируем все критические failure scenarios для production readiness.

---

## Decision 6: Implementation Requirements

**Модификации кода:**

### 1. Subagent Dependency Injection (если нужно)

**Проверить файлы:**
- `src/aim/subagents/keyword_research_agent.py`
- `src/aim/subagents/content_gap_analysis_agent.py`
- `src/aim/subagents/content_writer_agent.py`
- `src/aim/subagents/ads_campaign_creator_agent.py`
- `src/aim/subagents/analytics_agent.py`

**Pattern (если нужно добавить):**
```python
class KeywordResearchAgent(Agent):
    def __init__(
        self,
        agent_id: str = "keyword-research-agent",
        semrush_client: Optional[SEMrushClient] = None,
        ahrefs_client: Optional[AhrefsClient] = None,
        skip_api_validation: bool = False,
    ):
        self.semrush_client = semrush_client or SEMrushClient(...)
        self.ahrefs_client = ahrefs_client or AhrefsClient(...)
```

### 2. Test Files Structure

**Создать:**
- `tests/fixtures/subagent_data.py` (mock data)
- `tests/unit/test_keyword_research_agent.py` (4 tests)
- `tests/unit/test_content_gap_analysis_agent.py` (3 tests)
- `tests/unit/test_content_writer_agent.py` (3 tests)
- `tests/unit/test_ads_campaign_creator_agent.py` (3 tests)
- `tests/unit/test_analytics_agent.py` (3 tests)

### 3. Pytest Fixtures

**Создать:** `tests/fixtures/subagent_fixtures.py`

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_api_clients():
    return {
        "semrush": AsyncMock(spec=SEMrushClient),
        "ahrefs": AsyncMock(spec=AhrefsClient),
        "ga4": AsyncMock(spec=GA4Client),
        "yandex": AsyncMock(spec=YandexMetricaClient),
        "openai": AsyncMock(spec=OpenAIClient),
    }

@pytest.fixture
def keyword_research_agent(mock_api_clients):
    agent = KeywordResearchAgent(skip_api_validation=True)
    agent.semrush_client = mock_api_clients["semrush"]
    agent.ahrefs_client = mock_api_clients["ahrefs"]
    return agent

# Аналогично для других субагентов
```

---

## Success Criteria

**Phase 5 считается завершённой когда:**

1. ✅ **16+ tests passing** (4+3+3+3+3)
2. ✅ **All 5 subagents tested** (Keyword Research, Content Gap, Content Writer, Ads Campaign, Analytics)
3. ✅ **Business logic validated** (не только API calls)
4. ✅ **Production patterns tested** (circuit breaker, retry, rate limiting, caching, budget guard)
5. ✅ **Compliance tested** (FDA/HIPAA blocking, audit trail)
6. ✅ **Error handling verified** (API failures, compliance violations, budget overrun, invalid input)
7. ✅ **Deep quality achieved** (не поверхностное тестирование)

**Metrics:**
- Test coverage: 70%+ для субагентов
- Test execution time: < 60 seconds
- No flaky tests (deterministic через AsyncMock)
- All edge cases covered

---

## Notes for Researcher

**Что исследовать:**

1. **Existing subagent implementations:**
   - Читай `src/aim/subagents/*.py` для понимания текущей архитектуры
   - Проверь как реализованы API clients, compliance, prioritization
   - Найди все production patterns (circuit breaker, retry, etc.)

2. **Existing test patterns:**
   - Читай `tests/unit/test_api_clients.py` для примеров AsyncMock
   - Читай `tests/unit/test_seo_magister.py` для примеров dependency injection
   - Проверь как сейчас используются pytest fixtures

3. **Medical domain specifics:**
   - Найди примеры medical keywords (dental, cosmetic, etc.)
   - Проверь compliance rules (FDA/HIPAA)
   - Найди примеры risky keywords для блокировки

**Что НЕ исследовать:**
- Не ищи новые библиотеки (используем существующие)
- Не ищи альтернативные подходы к тестированию (решения уже приняты)
- Не исследуй Magister implementations (фокус на субагентах)

---

## Notes for Planner

**Приоритеты:**

1. **Сначала создай mock data** (subagent_data.py)
2. **Потом создай fixtures** (subagent_fixtures.py)
3. **Потом пиши тесты по порядку:**
   - Keyword Research Agent (4 tests) - самый критичный
   - Content Gap Analysis Agent (3 tests)
   - Content Writer Agent (3 tests)
   - Ads Campaign Creator Agent (3 tests)
   - Analytics Agent (3 tests)

**Порядок тестов внутри каждого субагента:**
1. Success case (happy path)
2. API failure (circuit breaker + fallback)
3. Compliance/validation (domain-specific)
4. Error handling (edge cases)

**Atomic commits:**
- Commit 1: Create mock data and fixtures
- Commit 2: Keyword Research Agent tests (4 tests)
- Commit 3: Content Gap Analysis Agent tests (3 tests)
- Commit 4: Content Writer Agent tests (3 tests)
- Commit 5: Ads Campaign Creator Agent tests (3 tests)
- Commit 6: Analytics Agent tests (3 tests)

**Estimated time:** 4 hours (0.5h fixtures + 3.5h tests)

---

## References

**Code to read:**
- `src/aim/subagents/keyword_research_agent.py` (production implementation)
- `src/aim/subagents/content_gap_analysis_agent.py`
- `src/aim/subagents/content_writer_agent.py`
- `src/aim/subagents/ads_campaign_creator_agent.py`
- `src/aim/subagents/analytics_agent.py`
- `tests/unit/test_api_clients.py` (AsyncMock examples)
- `tests/unit/test_seo_magister.py` (dependency injection examples)

**Dependencies:**
- pytest >= 9.0
- pytest-asyncio >= 1.3
- unittest.mock (stdlib)

**No new dependencies needed.**
