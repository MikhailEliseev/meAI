# AIM Project — Refactor Analysis

**Дата создания:** 30 июня 2026
**Сервер анализа:** `aim` (78.17.128.169) — Polish production server
**Аналитик:** Claude Code (на основе полного SSH-аудита)

---

## Зачем эта папка

Полная инвентаризация и фиксация сути проекта AIM перед рефакторингом и полной переделкой. Документы основаны **только на фактическом состоянии** сервера и кода — не на PLAN-документах, CLAUDE.md или SESSION.md (которые содержат много устаревшего).

## Структура документов

| # | Файл | Содержание |
|---|------|-----------|
| **00** | **[PROJECT-CONTEXT](00-PROJECT-CONTEXT.md)** | **ГЛАВНЫЙ ЯКОРЬ — читать первым. История, цель, боль, решения Михаила** |
| 01 | [EXECUTIVE-SUMMARY](01-EXECUTIVE-SUMMARY.md) | Однопроходная выжимка для быстрого контекста |
| 02 | [AS-IS-ARCHITECTURE](02-AS-IS-ARCHITECTURE.md) | Текущая архитектура как она есть — контейнеры, потоки данных, зависимости |
| 03 | [WORKING-COMPONENTS](03-WORKING-COMPONENTS.md) | Что реально работает в production прямо сейчас |
| 04 | [BROKEN-COMPONENTS](04-BROKEN-COMPONENTS.md) | Что не работает по задумке (с severity) |
| 05 | [DEAD-CODE-INVENTORY](05-DEAD-CODE-INVENTORY.md) | Zombie/legacy код, дубликаты, мусор |
| 06 | [FILE-INVENTORY](06-FILE-INVENTORY.md) | Полный инвентарь значимых файлов и директорий |
| 07 | [DIVERGENCE-FROM-DOCS](07-DIVERGENCE-FROM-DOCS.md) | Расхождения между CLAUDE.md/SESSION.md и реальностью |
| 08 | [TARGET-ARCHITECTURE](08-TARGET-ARCHITECTURE.md) | Целевая архитектура (TO-BE) для переделки |
| 09 | [REFACTOR-ROADMAP](09-REFACTOR-ROADMAP.md) | Дорожная карта рефакторинга по фазам |
| 10 | [DECISIONS-NEEDED](10-DECISIONS-NEEDED.md) | Вопросы, требующие решения от владельца продукта |
| **11** | **[RECOMMENDATION](11-RECOMMENDATION.md)** | Моя аналитика — почему Путь C (radical simplification) |
| **12** | **[DECISIONS-RESOLVED](12-DECISIONS-RESOLVED.md)** | Ответы Михаила от 30 июня 2026 |

## Ключевые тезисы (TL;DR)

1. **Production работает частично** — чат с Hermes отвечает, но 7 backend-сервисов (leads, sales, onboarding, analytics, gdpr) не могут писать в БД из-за нарушенной авторизации PostgreSQL
2. **SESSION.md и CLAUDE.md врут о состоянии** — Phase 09 не задеплоена (404), HeadroomGuard не запущен, 67 tools вместо описанных 33
3. **Огромное наследие мёртвого кода** — 19 magister-файлов, 133 subagent-файла, EventBus, ci-orchestrator (все неиспользуемы)
4. **Дубликаты** — meai framework в 2 местах, frontend локально + в Docker, node_modules в продакшен-теме
5. **Целевая архитектура = LLM-orchestrator** — Hermes (LLM) вызывает tools по ситуации, без жёсткого pipeline

## Куда идти primero

- Прочитать `01-EXECUTIVE-SUMMARY.md` — это 5 минут
- Для планирования рефакторинга — `09-REFACTOR-ROADMAP.md`
- Для архитектурных решений — `10-DECISIONS-NEEDED.md`

---

*Все цифры в документах — результаты измерений на сервере 30.06.2026. Документы не нужно обновлять — это снимок состояния на момент анализа.*
