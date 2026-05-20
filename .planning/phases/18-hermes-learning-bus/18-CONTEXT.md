# Phase 18: System Integration — Hermes Learning Bus — Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

## Phase Boundary

Связать Hermes (знаниевый хаб), Teacher (внешнее обучение) и Magisters в одну когерентную систему. Hermes становится центральной шиной обучения:
- Слушает EventBus — execution-события CI-агентов попадают в raw/executions/
- Принимает обогащённые знания от Teacher — внешние исследования → wiki/patterns/
- Отдаёт контекст Magisters перед делегированием — чтобы решения были informed
- Knowledge loop замкнут: execution → capture → learn → improve → next execution

**Результат:** Система перестаёт быть набором разрозненных инструментов и становится единым адаптивным организмом.

## Current State (As-Is)

### Что уже есть

**Hermes (AIM/hermes/):**
- FastAPI-приложение с 3 режимами (PRESALE/ACTIVE/ADMIN)
- 6 MCP tools: run_seo_audit, run_content_analysis, run_ads_report, show_project_status, collect_contact, show_all_leads
- SOUL.md с identity, режимами, WOW-стратегией, Token Economy, Lead Dossier
- Telegram gateway для клиентской коммуникации
- OmniRoute (DeepSeek) как LLM-провайдер
- **НЕ слушает EventBus** — не получает execution-события от CI-агентов
- **НЕ имеет knowledge pipeline** от Teacher
- **Magisters НЕ запрашивают контекст** у Hermes перед делегированием

**Teacher Agent (src/meai/agents/teacher.py):**
- Qdrant-векторное хранилище знаний (4 коллекции: seo, content, ads, general)
- FallbackStorage (SQLite) при недоступности Qdrant
- EmbeddingsModel (bge-m3) для векторизации
- Quality scoring (min 60/100) для фильтрации знаний
- **НЕ подключён к Hermes** — знания лежат в Qdrant, но Hermes их не видит
- **НЕ запускается автоматически** — требуется ручной вызов
- **НЕ следит за GitHub/industry** в реальном времени

**Magisters (AIM/src/aim/magisters/):**
- SEO, Content, Ads, Analytics Magisters — координируют субагентов
- SEO Magister: TechnicalSEOAgent + ContentSEOAgent + LinksSEOAgent
- Content Magister: CI-агенты через orchestrator
- Ads Magister: управление рекламными кампаниями
- **НЕ запрашивают контекст** у Hermes перед запуском
- **НЕ сохраняют execution experience** в Hermes
- **Работают изолированно** — каждый сам по себе

**EventBus (src/meai/events/event_bus.py):**
- P0-P3 приоритеты
- Async messaging
- **CI-агенты НЕ публикуют** execution-события
- **Hermes НЕ подписан** на события

**CI Orchestrator (AIM/src/aim/subagents/competitive_intel/orchestrator/):**
- Direct Execution Path работает (через API)
- 16+ CI-агентов wired (все реальные, 0 random)
- **НЕ публикует execution-события** в EventBus
- **НЕ сохраняет результаты** в Hermes vault

### Ключевой разрыв

```
CI Agents ──(execute)──> Results ──(save to JSON)──> AIM/data/*.json
                                │
                                └──(NO EVENT)──> EventBus ──(NO SUBSCRIPTION)──> Hermes

Teacher ──(store)──> Qdrant ──(NO CONNECTION)──> Hermes

Magisters ──(delegate)──> Subagents ──(NO CONTEXT QUERY)──> Hermes
```

Система работает, но компоненты не связаны. Каждый инструмент сам по себе.

## Target State (To-Be)

```
CI Agents ──(execute)──> Results ──(publish event)──> EventBus
                                                           │
                                                           └──> Hermes.ingest(event)
                                                                     │
                                                                     ├──> raw/executions/
                                                                     ├──> wiki/patterns/ (LLM-generated)
                                                                     └──> decisions/rules/

Teacher ──(research)──> Knowledge ──(store)──> Qdrant
                                                    │
                                                    └──> Hermes.query("pattern:X")
                                                                     │
                                                                     └──> wiki/patterns/

Magisters ──(query context)──> Hermes ──(return)──> informed context
     │                                                      │
     └──(delegate with context)──> Subagents ──(better decisions)
```

## Implementation Decisions

### D-01: Hermes EventBus Listener (LOCKED)
- Hermes подписывается на CI-execution события через EventBus
- При получении события — сохраняет в raw/executions/
- Запускает LLM-ingest: raw → wiki (structured knowledge)
- Извлекает паттерны, ошибки, успешные стратегии
- **Почему EventBus, а не прямой вызов:** асинхронность, отказоустойчивость, не блокирует CI-пайплайн

### D-02: Teacher → Hermes Knowledge Pipeline (LOCKED)
- Teacher сохраняет знания в Qdrant (уже умеет)
- Hermes получает query-интерфейс к Qdrant
- При старте или периодически — Hermes запрашивает свежие знания у Teacher
- Teacher обогащает wiki/patterns/ внешними исследованиями
- **Формат:** Hermes.query("domain:seo pattern:competitive_analysis") → Qdrant search → wiki/ update

### D-03: Magisters → Hermes Context Query (LOCKED)
- Перед делегированием субагенту, Magister запрашивает контекст у Hermes
- Hermes возвращает: релевантные паттерны, прошлый опыт, best practices
- Magister добавляет контекст в task payload для субагента
- **Протокол:** HTTP (Hermes FastAPI) или прямой вызов (если в одном процессе)

### D-04: Step-by-Step Activation Sequence (LOCKED)
- User запускает инструмент (например, SEO-аудит)
- Hermes получает событие, записывает в raw/
- После выполнения — Hermes анализирует результат, обновляет wiki/
- Teacher (по расписанию) обогащает wiki/ внешними данными
- Следующий запуск того же инструмента — Magister получает обогащённый контекст
- Цикл замыкается: каждый запуск делает систему умнее

### D-05: Knowledge Loop Closure (LOCKED)
- execution → EventBus event → Hermes raw/executions/
- raw/executions/ → LLM ingest → wiki/patterns/
- Teacher → Qdrant → Hermes wiki/patterns/ (enrichment)
- wiki/patterns/ → decisions/rules/ (validated patterns)
- decisions/rules/ → Magister context query → better execution
- better execution → execution (loop closed)

## Claude's Discretion

- Архитектура EventBus-подписки (новый subscriber или расширение Hermes)
- Формат execution-событий (какие поля, структура)
- Query-интерфейс Magisters → Hermes (REST API endpoints)
- Периодичность Teacher→Hermes синхронизации
- Структура raw/executions/ и wiki/patterns/ в Hermes vault

## Specific Ideas

Из запроса пользователя:
1. «Hermes сам записывал тот путь, который мы с ним пройдем» — execution capture
2. «Обучился на тех или иных инструментах, которые у него доступны» — pattern extraction
3. «Я буду вызывать Гермеса с запросом того или иного инструмента или полного цикла» — step-by-step activation
4. «Всё было связано в одну цепь» — knowledge loop closure
5. «Система не рабочая, набор разрозненных инструментов» → «система работает как одно целое»

## Deferred Ideas

- Real-time GitHub monitoring Teacher (фаза 19)
- Автоматический запуск CI-анализа по расписанию (фаза 19)
- Hermes-driven autonomous optimization (фаза 20+)

---

*Phase: 18-hermes-learning-bus*
*Context gathered: 2026-05-20*
