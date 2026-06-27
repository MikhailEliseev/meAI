# Phase 21: CI Pipeline Unification -- Context

**Gathered:** 2026-05-29
**Updated:** 2026-05-31 (plan regeneration)
**Status:** Ready for execution (regenerated plans)
**Source:** CI Pipeline Audit (15 issues: 5 CRITICAL, 6 HIGH, 4 LOW)

## Plan Checker Findings (2026-05-31)

The plan-checker audited the original 5-wave plans against the codebase and found that
**~90% of the planned work was ALREADY IMPLEMENTED**. The plans have been regenerated
to focus ONLY on the remaining gap: D-05/D-06/D-07 (EventBus delegation).

### Already Implemented (DO NOT RE-PLAN)

| Wave | Problem | What | Status |
|------|---------|------|--------|
| W1 | L4 | `UnifiedCiResult` + `SwotQuadrant` in `ci/models.py:8,28` | **DONE** |
| W2 | H1 | Pipeline merge: `_run_quick_analysis()`, tier routing, `_extract_*`/`_generate_*` in orchestrator | **DONE** |
| W2 | D-04 | CiMarketingAnalyzer is thin proxy (158 lines, uses `__new__` trick) | **DONE** |
| W4 | D-10/D-11 | `/api/seo/audit` accepts `?tier=quick\|deep`, deprecation header on old endpoint, SSE stream endpoint | **DONE** |
| W5 | Tests | `TestUnifiedArchitecture` class exists, 49 tests across 11 classes | **DONE** |

### Remaining Gap: EventBus Delegation (D-05/D-06/D-07)

Current state in `ci_orchestrator.py:910-990`:
1. Publishes `task.request` Message to EventBus -- correct
2. Waits 10s for `ci.agent.completed` callback -- ALWAYS TIMES OUT
3. Falls back to `agent.execute_task(task)` -- direct call, defeats EventBus purpose

**Root causes:**
1. `_get_agent()` never calls `agent.initialize()` -- agent's `_listen_for_tasks()` poll loop never starts
2. Agents publish `agent.result` Messages (to `"operator"`), not `ci.agent.completed` Events -- type mismatch with orchestrator's subscription
3. `correlation_id` not threaded through to agent's result publication

**Regenerated plans (2 waves):**
- **21-01-PLAN.md** -- Wave 1: Agent EventBus Initialization (initialize + bridge completion events)
- **21-02-PLAN.md** -- Wave 2: Remove dead fallback + verify all 49 tests pass

<domain>
## Phase Boundary

Унификация двух параллельных CI-пайплайнов в единую архитектуру:

1. **CiMarketingAnalyzer** (press-release pipeline, `/api/competitors/analyze/stream`)
   - Быстрый анализ (~10 сек)
   - Генерирует SWOT, тактики, WOW-цифры, chat_summary
   - Использует PipelineRunner → ComparisonMatrix → локальный анализ

2. **CIOrchestrator** (16-phase pipeline, `/api/seo/audit`)
   - Глубокий анализ (1-10 минут)
   - 16 фаз, каждая через отдельного агента
   - Использует EventBus + агентов

**Проблема H1:** Два пайплайна делают похожие вещи, но с разной архитектурой и моделями данных.

**Проблема H6:** EventBus-делегирование в CIOrchestrator — stub (Path 2 никогда не вызывается, Path 1 вызывает agent.execute_task напрямую).

**Что должно быть на выходе:**
- Единый CIOrchestrator с tier-параметром (quick/deep)
- Quick tier → быстрый PipelineRunner + локальный анализ (текущий CiMarketingAnalyzer)
- Deep tier → полный 16-фазный анализ (текущий CIOrchestrator)
- Реальное EventBus-делегирование вместо прямых вызовов
- Единые модели данных
</domain>

<decisions>
## Implementation Decisions

### Architecture
- **D-01:** Единый CIOrchestrator с `execute_ci_analysis(task_data, tier)` -- [LOCKED]
- **D-02:** Quick tier (tier="quick") → PipelineRunner + ComparisonMatrix + локальный анализ (~10 сек) -- [LOCKED]
- **D-03:** Deep tier (tier="deep") → 16-фазный agent-пайплайн через EventBus -- [LOCKED]
- **D-04:** CiMarketingAnalyzer становится внутренним методом CIOrchestrator (`_run_quick_analysis`) -- [LOCKED]

### EventBus Delegation
- **D-05:** Заменить прямые вызовы `agent.execute_task(task)` на `event_bus.publish(task_event)` + agent подписка -- [LOCKED]
- **D-06:** Каждый CI-агент подписывается на свой тип событий через EventBus -- [LOCKED]
- **D-07:** Результаты агентов собираются через EventBus ответные события -- [LOCKED]

### Data Models
- **D-08:** Единые модели в `ci/models.py` для обоих tier-ов -- [LOCKED] ✅ DONE
- **D-09:** Quick tier возвращает тот же формат результата, что и deep tier (с флагом `is_quick=True`) -- [LOCKED] ✅ DONE

### API
- **D-10:** Единый эндпоинт `/api/seo/audit` с параметром `tier` (quick/deep) -- [LOCKED] ✅ DONE
- **D-11:** `/api/competitors/analyze/stream` становится алиасом на `/api/seo/audit?tier=quick` -- [LOCKED] ✅ DONE

### Claude's Discretion
- Точная структура EventBus-сообщений для агентов
- Механизм таймаутов для deep tier
- Формат прогресс-сообщений
- Миграция существующих тестов
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CI Core
- `AIM/src/aim/services/ci_marketing_analysis.py` — Текущий press-release pipeline (thin proxy)
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` — Основной оркестратор (1230 строк)
- `AIM/src/aim/services/ci/wow_estimator.py` — Общий WOW-калькулятор
- `AIM/src/aim/services/ci/models.py` — Модели данных (UnifiedCiResult, SwotQuadrant, etc.)

### EventBus
- `src/meai/events/event_bus.py` — EventBus (P0-P3, async messaging)
- `src/meai/events/event_store.py` — Immutable audit log

### API
- `AIM/src/aim/api/seo.py` — SEO audit endpoint
- `AIM/src/aim/api/competitors.py` — Competitors analyze endpoint

### Tests
- `AIM/tests/subagents/test_ci_pipeline_integration.py` — Интеграционные тесты CI (49 тестов)

### Agents
- `src/meai/agents/base_agent.py` — Agent, Task, TaskResult
</canonical_refs>

<specifics>
## Specific Ideas

### H1: Дублирование пайплайнов -- ✅ DONE
- CiMarketingAnalyzer (~158 строк, была 545) → thin proxy через `__new__` trick
- CIOrchestrator (~1230 строк) → основной, tier-ветвление на строке 729
- Общие компоненты (wow_estimator, models) унифицированы

### H6: EventBus-делегирование (stub) -- ⏳ IN PROGRESS (plans 21-01, 21-02)
- Текущий код: EventBus path всегда падает в timeout → fallback к `agent.execute_task(task)`
- Целевой код: `await self.event_bus.publish(task_request_message)` + agent poll loop + `ci.agent.completed` Event
- Нужно: вызвать `agent.initialize()` для запуска poll loop, bridge `report_result` → `ci.agent.completed` Event

### L4: Разные модели данных -- ✅ DONE
- UnifiedCiResult в ci/models.py с полями для обоих tier-ов
</specifics>

<deferred>
## Deferred Ideas

- Миграция ci_deep_analyzer (2411 строк) — работает, рефакторинг L1 отложен
- Полная замена PipelineRunner на EventBus для quick tier — quick tier остаётся синхронным
</deferred>

---
*Phase: 21-ci-pipeline-unification*
*Context gathered: 2026-05-29, updated: 2026-05-31 (plan regeneration)*
