---
vault: ci-scout
created: 2026-05-04
agent_type: scout
role: Market Discovery and Competitor Clustering
---

# CI Scout Vault Schema

## Структура

Этот vault следует LLM Wiki pattern от Andrej Karpathy.

### Три слоя:

1. **raw/** — Источники (immutable)
   - WebSearch результаты
   - Данные из каталогов (Zoon, 2GIS, Яндекс.Карты)
   - VK/Telegram данные

2. **wiki/** — Структурированное знание (LLM-generated)
   - **index.md** — Content-oriented каталог
   - **log.md** — Chronological запись операций
   - **concepts/** — Концепции (clustering, market mapping)
   - **technologies/** — Технологии (WebSearch, WebFetch)
   - **strategies/** — Стратегии поиска
   - **agents/** — Связи с другими агентами
   - **workflows/** — Процессы discovery
   - **projects/** — Проекты клиентов
   - **sources/** — Обработанные источники
   - **connections/** — Синтезы

3. **decisions/** — Решения по кластеризации
   - Выбор TOP конкурентов
   - Определение кластеров

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
- **log.md** — хронология всех операций
