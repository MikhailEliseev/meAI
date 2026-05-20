# Phase 18: System Integration — Research

**Date:** 2026-05-20
**Status:** Complete

## Research Summary

Phase 18 — внутренняя интеграция существующих компонентов. Внешний research не требуется: все компоненты уже реализованы, нужно связать их в одну цепь.

## Integration Points (Code-Level)

### 1. EventBus — Subscription Mechanism

**Файл:** `src/meai/events/event_bus.py`

Текущий API:
```python
# Subscribe (line 433)
event_bus.subscribe(event_type: str, handler: Callable[[Event], Awaitable[None]])

# Publish (line 454)
await event_bus.publish(event: Event | Message | BaseEvent)

# Get events by target (line 328)
await event_bus.get_events(target="hermes", event_type="ci.execution.completed")
```

**Интеграция:** Hermes подписывается на `ci.execution.*` события. При публикации — EventBus автоматически вызывает handler. Альтернативно — polling через `get_events(target="hermes")`.

### 2. CI Orchestrator — Event Publishing

**Файл:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`

Уже использует EventBus (line 802):
```python
await self.event_bus.publish(
    event_type=f"task.{agent_id}",
    payload=task.to_dict(),
    priority=1
)
```

**Интеграция:** Добавить публикацию `ci.execution.completed` после выполнения каждого агента (в `execute_ci_analysis()`).

### 3. Hermes — Vault Structure

**Файл:** `AIM/hermes/app/main.py` (FastAPI), `AIM/hermes/skills/aim/SOUL.md`

Текущая структура:
```
AIM/hermes/
├── app/
│   ├── main.py          # FastAPI (3 endpoints)
│   ├── agent_wrapper.py  # AIAgent runner
│   ├── telegram_gateway.py
│   └── tools/            # 6 MCP tools
└── skills/aim/
    ├── SOUL.md
    ├── services.md
    ├── processes.md
    └── kpi.md
```

**Интеграция:** Добавить в Hermes vault LLM Wiki структуру:
```
AIM/hermes/
└── knowledge/
    ├── raw/executions/     # Execution-события от CI
    ├── wiki/patterns/      # LLM-извлечённые паттерны
    ├── wiki/learnings/     # Обогащённые знания от Teacher
    └── decisions/rules/    # Валидированные правила
```

### 4. Teacher — Qdrant Knowledge

**Файл:** `src/meai/agents/teacher.py`

Текущие коллекции: seo_knowledge, content_knowledge, ads_knowledge, general_knowledge

API:
```python
teacher.evaluate_knowledge(source, content, domain)
teacher.store_knowledge(knowledge_item)
teacher.search_knowledge(query, domain, limit)
```

**Интеграция:** Hermes получает query-метод для поиска в Qdrant через Teacher.

### 5. Magisters — Context Query

**Файлы:** `AIM/src/aim/magisters/seo_magister_with_ci.py`, `content_magister_with_ci.py`, `ads_magister_with_ci.py`

Уже имеют `ci_integration` (CIMagisterIntegration).

**Интеграция:** Добавить `hermes_context` query перед делегированием субагентам.

## Technical Decisions

### Decision 1: Push vs Pull для EventBus

**Push (subscribe):** Hermes handler вызывается мгновенно. Риск: handler падает → событие потеряно.
**Pull (polling):** Hermes периодически забирает события. Надёжнее, но с задержкой.

**Решение:** Push + retry. Handler пишет в raw/executions/ и возвращает 200. Если handler упал → EventBus помечает как failed → Hermes перечитывает failed при старте.

### Decision 2: HTTP vs Direct Import для Magisters → Hermes

**HTTP:** Magister → `GET /api/hermes/context?domain=seo&action=audit`
**Direct:** `from hermes.knowledge import query_context`

**Решение:** HTTP. Hermes — отдельный процесс (FastAPI на uvicorn). Прямой импорт невозможен без запуска в том же процессе.

### Decision 3: Teacher → Hermes Sync Frequency

**Решение:** On-demand + scheduled. При старте Hermes запрашивает свежие знания у Teacher. Далее — по расписанию (каждые 4 часа) или при получении execution-события.

## Endpoints to Add

### Hermes FastAPI (новые endpoints)

```
POST /api/knowledge/ingest      — Принять execution-событие, сохранить в raw/executions/
GET  /api/knowledge/context     — Magister query: вернуть релевантные паттерны/правила
GET  /api/knowledge/status      — Статус knowledge loop (сколько событий, паттернов)
POST /api/knowledge/learn       — Запустить LLM-ingest: raw → wiki (по требованию)
GET  /api/knowledge/search      — Поиск по знаниям (из Qdrant через Teacher)
```

### Teacher CLI/API (новые методы)

```
teacher.sync_to_hermes(domain)  — Отправить свежие знания в Hermes
teacher.search_external(query)  — Поиск во внешних источниках (GitHub, web)
```

## Activation Sequence

1. Hermes.FastAPI стартует → подписывается на EventBus (`ci.execution.*`)
2. User → API `/api/seo/audit` → CI Orchestrator → CI Agents
3. CI Agent completes → публикует `ci.execution.completed` в EventBus
4. EventBus → Hermes handler → raw/executions/{correlation_id}.json
5. Hermes запускает LLM-ingest → wiki/patterns/{pattern_name}.md
6. Teacher (по расписанию) → обогащает wiki/patterns/ внешними данными
7. Следующий вызов → Magister запрашивает `GET /api/knowledge/context?domain=seo`
8. Hermes возвращает релевантные паттерны → Magister добавляет в task payload
9. Subagent получает enriched task → better execution
10. Результат → EventBus → цикл замыкается
