---
vault: ci-orchestrator
created: 2026-05-04
agent_type: orchestrator
role: Координатор конкурентной разведки
---

# CI Orchestrator Vault Schema

## Структура

Этот vault следует LLM Wiki pattern от Andrej Karpathy.

### Три слоя:

1. **raw/** — Источники (immutable)
   - Запросы пользователей
   - Результаты от агентов
   - Внешние данные

2. **wiki/** — Структурированное знание (LLM-generated)
   - **index.md** — Content-oriented каталог
   - **log.md** — Chronological запись операций
   - **concepts/** — Концепции CI (tiers, phases, clustering)
   - **technologies/** — Технологии (WebSearch, WebFetch, Event Bus)
   - **strategies/** — Стратегии координации
   - **agents/** — 23 агента системы
   - **workflows/** — Процессы (16 фаз)
   - **projects/** — Проекты клиентов
   - **sources/** — Обработанные источники
   - **connections/** — Связи и синтезы

3. **decisions/** — Стратегические решения
   - Выбор tier для анализа
   - Routing решения (skip phases)
   - Gate approvals/rejections

## Операции

### Ingest
raw/ → wiki/ (создание/обновление страниц по категориям)

### Query
вопрос → чтение wiki/ → ответ с цитатами → новая страница

### Lint
проверка противоречий, orphans, gaps, устаревших данных

## Правила

- Всегда проверяй frontmatter `status: processed` перед чтением
- Если `status: processed` → читай wiki/ (из поля `output`)
- Если нет → читай raw/ и обрабатывай
- Обновляй log.md при каждой операции

## Специальные файлы

- **index.md** — каталог всех страниц с статистикой
- **log.md** — хронология всех операций (формат: `## [YYYY-MM-DD HH:MM] operation | Description`)
