---
phase: 4
title: Magister Tests
created: 2026-05-14
status: ready_for_planning
decisions_count: 5
---

# Phase 4: Magister Tests - Implementation Context

## Overview

Тестирование 4 Magisters (SEO, Content, Ads, Analytics) с фокусом на orchestration workflows, parallel execution, и error handling. Гибридный подход: unit tests для изолированной логики + integration tests для E2E flows.

**Target:** 24 tests (16 unit + 8 integration), 3 hours

---

## Decision 1: Mocking Strategy

**Выбор:** Гибридный подход (разные стратегии для unit/integration)

**Детали:**

### Unit Tests (16 tests)
- **Полная изоляция** через AsyncMock
- **Dependency injection** через pytest fixtures
- **Модификация Magister.__init__:**
  ```python
  class SEOMagister:
      def __init__(
          self,
          timeout: int = 600,
          technical_agent: TechnicalSEOAgent | None = None,
          content_agent: ContentSEOAgent | None = None,
          links_agent: LinksSEOAgent | None = None,
      ):
          self.technical_agent = technical_agent or TechnicalSEOAgent()
          self.content_agent = content_agent or ContentSEOAgent()
          self.links_agent = links_agent or LinksSEOAgent()
          self.timeout = timeout
  ```

- **Pytest fixture pattern:**
  ```python
  @pytest.fixture
  def mock_subagents():
      return {
          "technical": AsyncMock(spec=TechnicalSEOAgent),
          "content": AsyncMock(spec=ContentSEOAgent),
          "links": AsyncMock(spec=LinksSEOAgent),
      }
  
  @pytest.fixture
  def seo_magister(mock_subagents):
      return SEOMagister(
          technical_agent=mock_subagents["technical"],
          content_agent=mock_subagents["content"],
          links_agent=mock_subagents["links"],
      )
  ```

### Integration Tests (8 tests)
- **Реальные subagents** (TechnicalSEOAgent, ContentSEOAgent, LinksSEOAgent)
- **Мокируем только API clients** (SEMrush, Ahrefs, Playwright)
- **Проверяем E2E flow:** Magister → Subagents → API clients (mocked)

**Why:** Unit tests проверяют orchestration logic в изоляции, integration tests проверяют реальное взаимодействие компонентов.

---

## Decision 2: Test Scope & Distribution

**Выбор:** 4 unit на Magister + 2 integration на Magister (максимальное покрытие)

**Детали:**

### Unit Tests (4 per Magister × 4 Magisters = 16 tests)

**SEOMagister (4 tests):**
1. `test_seo_magister_success` - успешная координация 3 subagents
2. `test_seo_magister_timeout` - timeout 600s срабатывает
3. `test_seo_magister_partial_failure` - 1 из 3 subagents падает
4. `test_seo_magister_full_failure` - все 3 subagents падают

**ContentMagister (4 tests):**
1. `test_content_magister_success` - успешная координация subagents
2. `test_content_magister_timeout` - timeout срабатывает
3. `test_content_magister_partial_failure` - частичный сбой
4. `test_content_magister_full_failure` - полный сбой

**AdsMagister (4 tests):**
1. `test_ads_magister_success` - успешная координация subagents
2. `test_ads_magister_timeout` - timeout срабатывает
3. `test_ads_magister_partial_failure` - частичный сбой
4. `test_ads_magister_full_failure` - полный сбой

**AnalyticsMagister (4 tests):**
1. `test_analytics_magister_success` - успешная координация subagents
2. `test_analytics_magister_timeout` - timeout срабатывает
3. `test_analytics_magister_partial_failure` - частичный сбой
4. `test_analytics_magister_full_failure` - полный сбой

### Integration Tests (2 per Magister × 4 Magisters = 8 tests)

**SEOMagister (2 tests):**
1. `test_seo_magister_e2e_success` - полный E2E flow с реальными subagents
2. `test_seo_magister_e2e_error` - E2E flow с ошибкой в API client

**ContentMagister (2 tests):**
1. `test_content_magister_e2e_success` - полный E2E flow
2. `test_content_magister_e2e_error` - E2E flow с ошибкой

**AdsMagister (2 tests):**
1. `test_ads_magister_e2e_success` - полный E2E flow
2. `test_ads_magister_e2e_error` - E2E flow с ошибкой

**AnalyticsMagister (2 tests):**
1. `test_analytics_magister_e2e_success` - полный E2E flow
2. `test_analytics_magister_e2e_error` - E2E flow с ошибкой

**Total:** 24 tests (16 unit + 8 integration)

**Why:** 4 unit tests покрывают все критические сценарии (success, timeout, partial failure, full failure), 2 integration tests проверяют E2E flow (success + error).

---

## Decision 3: Parallel Execution Testing

**Выбор:** Глубокая проверка (timing + race conditions + cancellation)

**Детали:**

### Hybrid Approach: asyncio.Event + time.monotonic()

**Pattern:**
```python
@pytest.mark.asyncio
async def test_seo_magister_parallel_execution(seo_magister, mock_subagents):
    # Шаг 1: Синхронизация через asyncio.Event
    start_event = asyncio.Event()
    
    async def delayed_mock(delay: float):
        await start_event.wait()  # Ждём сигнала
        await asyncio.sleep(delay)
        return {"score": 100}
    
    mock_subagents["technical"].analyze.side_effect = lambda url, cid: delayed_mock(0.1)
    mock_subagents["content"].analyze.side_effect = lambda url, cid: delayed_mock(0.1)
    mock_subagents["links"].analyze.side_effect = lambda url, cid: delayed_mock(0.1)
    
    # Шаг 2: Измерение времени через time.monotonic()
    start_time = time.monotonic()
    
    # Запускаем координацию (asyncio.gather внутри)
    task = asyncio.create_task(
        seo_magister.coordinate_analysis("https://example.com", "test-123")
    )
    
    # Даём задаче стартовать
    await asyncio.sleep(0.01)
    
    # Отправляем сигнал всем mock'ам одновременно
    start_event.set()
    
    # Ждём завершения
    result = await task
    elapsed = time.monotonic() - start_time
    
    # Шаг 3: Проверка параллельности
    # Если параллельно: ~0.1s (max из 3 задач)
    # Если последовательно: ~0.3s (сумма 3 задач)
    assert elapsed < 0.2, f"Execution took {elapsed}s, expected < 0.2s (parallel)"
    assert elapsed > 0.09, f"Execution took {elapsed}s, expected > 0.09s (not instant)"
    
    # Проверяем что все 3 subagents вызваны
    assert mock_subagents["technical"].analyze.call_count == 1
    assert mock_subagents["content"].analyze.call_count == 1
    assert mock_subagents["links"].analyze.call_count == 1
```

**Что проверяем:**
1. **Timing:** Параллельное выполнение быстрее последовательного
2. **Race conditions:** asyncio.Event гарантирует одновременный старт
3. **Cancellation:** Если один subagent отменён, другие продолжают

**Why:** asyncio.Event синхронизирует mock'и для детерминированного теста, time.monotonic() измеряет реальное время выполнения.

---

## Decision 4: Error Handling Scenarios

**Выбор:** Все 4 сценария (timeout, partial failures, full failures, different error types)

**Детали:**

### Scenario 1: Timeout Handling (asyncio.TimeoutError)

**Test:**
```python
@pytest.mark.asyncio
async def test_seo_magister_timeout(seo_magister, mock_subagents):
    # Mock subagent зависает на 700s (больше timeout 600s)
    async def slow_mock():
        await asyncio.sleep(700)
        return {"score": 100}
    
    mock_subagents["technical"].analyze.side_effect = slow_mock
    mock_subagents["content"].analyze.return_value = {"score": 80}
    mock_subagents["links"].analyze.return_value = {"score": 90}
    
    # Ожидаем asyncio.TimeoutError
    with pytest.raises(asyncio.TimeoutError):
        await seo_magister.coordinate_analysis("https://example.com", "test-123")
```

**Проверяем:**
- Timeout 600s срабатывает корректно
- asyncio.TimeoutError пробрасывается наверх
- Другие subagents не блокируют timeout

### Scenario 2: Partial Failures (1 of 3 subagents fails)

**Test:**
```python
@pytest.mark.asyncio
async def test_seo_magister_partial_failure(seo_magister, mock_subagents):
    # 1 subagent падает, 2 успешны
    mock_subagents["technical"].analyze.side_effect = ValueError("API error")
    mock_subagents["content"].analyze.return_value = {"score": 80}
    mock_subagents["links"].analyze.return_value = {"score": 90}
    
    result = await seo_magister.coordinate_analysis("https://example.com", "test-123")
    
    # Проверяем graceful degradation
    assert result["status"] == "partial_success"
    assert "technical" in result["errors"]
    assert result["content_score"] == 80
    assert result["links_score"] == 90
```

**Проверяем:**
- Magister продолжает работу при частичном сбое
- Ошибки логируются в результате
- Успешные результаты агрегируются

### Scenario 3: Full Failures (all subagents fail)

**Test:**
```python
@pytest.mark.asyncio
async def test_seo_magister_full_failure(seo_magister, mock_subagents):
    # Все 3 subagents падают
    mock_subagents["technical"].analyze.side_effect = ValueError("API error")
    mock_subagents["content"].analyze.side_effect = ConnectionError("Network error")
    mock_subagents["links"].analyze.side_effect = RuntimeError("Unknown error")
    
    with pytest.raises(RuntimeError, match="All subagents failed"):
        await seo_magister.coordinate_analysis("https://example.com", "test-123")
```

**Проверяем:**
- Magister выбрасывает исключение при полном сбое
- Все ошибки логируются
- Нет partial results при полном сбое

### Scenario 4: Different Error Types

**Test:**
```python
@pytest.mark.asyncio
async def test_seo_magister_different_error_types(seo_magister, mock_subagents):
    # Разные типы ошибок от subagents
    mock_subagents["technical"].analyze.side_effect = ValueError("Invalid URL")
    mock_subagents["content"].analyze.side_effect = ConnectionError("Network timeout")
    mock_subagents["links"].analyze.side_effect = KeyError("Missing API key")
    
    with pytest.raises(RuntimeError) as exc_info:
        await seo_magister.coordinate_analysis("https://example.com", "test-123")
    
    # Проверяем что все типы ошибок залогированы
    error_msg = str(exc_info.value)
    assert "ValueError" in error_msg
    assert "ConnectionError" in error_msg
    assert "KeyError" in error_msg
```

**Проверяем:**
- Magister корректно обрабатывает разные типы исключений
- Все типы ошибок логируются
- Не теряется информация о причинах сбоя

**Why:** Покрываем все критические error scenarios для production readiness.

---

## Decision 5: Implementation Requirements

**Модификации кода:**

### 1. Magister Dependency Injection

**Файлы для изменения:**
- `src/aim/magisters/seo_magister.py`
- `src/aim/magisters/content_magister.py`
- `src/aim/magisters/ads_magister.py`
- `src/aim/magisters/analytics_magister.py`

**Pattern:**
```python
class SEOMagister:
    def __init__(
        self,
        timeout: int = 600,
        technical_agent: TechnicalSEOAgent | None = None,
        content_agent: ContentSEOAgent | None = None,
        links_agent: LinksSEOAgent | None = None,
    ):
        self.technical_agent = technical_agent or TechnicalSEOAgent()
        self.content_agent = content_agent or ContentSEOAgent()
        self.links_agent = links_agent or LinksSEOAgent()
        self.timeout = timeout
```

### 2. Test Files Structure

**Создать:**
- `tests/unit/test_seo_magister.py` (4 tests)
- `tests/unit/test_content_magister.py` (4 tests)
- `tests/unit/test_ads_magister.py` (4 tests)
- `tests/unit/test_analytics_magister.py` (4 tests)
- `tests/integration/test_seo_magister_e2e.py` (2 tests)
- `tests/integration/test_content_magister_e2e.py` (2 tests)
- `tests/integration/test_ads_magister_e2e.py` (2 tests)
- `tests/integration/test_analytics_magister_e2e.py` (2 tests)

### 3. Pytest Fixtures

**Создать:** `tests/fixtures/magister_fixtures.py`

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_seo_subagents():
    return {
        "technical": AsyncMock(spec=TechnicalSEOAgent),
        "content": AsyncMock(spec=ContentSEOAgent),
        "links": AsyncMock(spec=LinksSEOAgent),
    }

@pytest.fixture
def seo_magister(mock_seo_subagents):
    return SEOMagister(
        technical_agent=mock_seo_subagents["technical"],
        content_agent=mock_seo_subagents["content"],
        links_agent=mock_seo_subagents["links"],
    )

# Аналогично для Content, Ads, Analytics Magisters
```

---

## Success Criteria

**Phase 4 считается завершённой когда:**

1. ✅ **24 tests passing** (16 unit + 8 integration)
2. ✅ **All 4 Magisters tested** (SEO, Content, Ads, Analytics)
3. ✅ **All error scenarios covered** (timeout, partial, full, different types)
4. ✅ **Parallel execution verified** (timing + race conditions)
5. ✅ **Dependency injection implemented** (pytest fixtures)
6. ✅ **Integration tests use real subagents** (only API clients mocked)

**Metrics:**
- Test coverage: 70%+ для Magisters
- Test execution time: < 30 seconds
- No flaky tests (deterministic через asyncio.Event)

---

## Notes for Researcher

**Что исследовать:**

1. **Existing Magister implementations:**
   - Читай `src/aim/magisters/*.py` для понимания текущей архитектуры
   - Проверь как сейчас реализован `coordinate_analysis()`
   - Найди все места где используется `asyncio.gather()`

2. **Existing test patterns:**
   - Читай `tests/unit/test_api_clients.py` для примеров AsyncMock
   - Читай `tests/integration/test_event_flow.py` для примеров asyncio.Event
   - Проверь как сейчас используются pytest fixtures

3. **Error handling patterns:**
   - Найди все места где обрабатываются исключения в Magisters
   - Проверь как сейчас реализован timeout через `asyncio.wait_for()`
   - Найди примеры graceful degradation при partial failures

**Что НЕ исследовать:**
- Не ищи новые библиотеки (используем unittest.mock + pytest-asyncio)
- Не ищи альтернативные подходы к тестированию (решения уже приняты)
- Не исследуй subagent implementations (фокус на Magisters)

---

## Notes for Planner

**Приоритеты:**

1. **Сначала модифицируй Magisters** (dependency injection)
2. **Потом создай pytest fixtures** (mock_subagents)
3. **Потом пиши unit tests** (16 tests, изолированная логика)
4. **Потом пиши integration tests** (8 tests, E2E flow)

**Порядок Magisters:**
1. SEOMagister (самый сложный, 3 subagents)
2. ContentMagister
3. AdsMagister
4. AnalyticsMagister

**Atomic commits:**
- Commit 1: Modify all 4 Magisters (dependency injection)
- Commit 2: Create pytest fixtures
- Commit 3: SEOMagister unit tests (4 tests)
- Commit 4: SEOMagister integration tests (2 tests)
- Commit 5: ContentMagister tests (6 tests)
- Commit 6: AdsMagister tests (6 tests)
- Commit 7: AnalyticsMagister tests (6 tests)

**Estimated time:** 3 hours (0.5h modifications + 2.5h tests)

---

## References

**Code to read:**
- `src/aim/magisters/seo_magister.py` (orchestration pattern)
- `src/aim/magisters/content_magister.py`
- `src/aim/magisters/ads_magister.py`
- `src/aim/magisters/analytics_magister.py`
- `tests/unit/test_api_clients.py` (AsyncMock examples)
- `tests/integration/test_event_flow.py` (asyncio.Event examples)

**Dependencies:**
- pytest >= 9.0
- pytest-asyncio >= 1.3
- unittest.mock (stdlib)

**No new dependencies needed.**
