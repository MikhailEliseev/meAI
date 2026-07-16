# HH Agent Vault Schema

## Purpose

Этот vault хранит данные конкурентной разведки через HeadHunter API.

## Structure

### Layer 1: Raw Sources (Immutable)

```
raw/
└── snapshots/           # Снимки вакансий по датам
    ├── 2026-05-04/
    │   ├── {employer_id}.json
    │   └── ...
    └── 2026-05-11/
```

**Правила:**
- Снимки создаются автоматически при мониторинге
- Формат: JSON массив объектов Vacancy
- Никогда не изменяются после создания
- Хранятся минимум 90 дней

### Layer 2: Wiki (LLM-Generated Knowledge)

```
wiki/
├── index.md              # Каталог всех страниц
├── log.md                # Хронология операций
├── competitors/          # Профили конкурентов
│   └── {competitor_name}.md
├── vacancies/            # Анализ отдельных вакансий
│   └── {vacancy_id}.md
├── technologies/         # Тренды технологий
│   └── {tech_name}.md
├── strategies/           # Стратегии конкурентов
│   └── {strategy_name}.md
├── insights/             # Инсайты и выводы
│   └── report-{date}.md
└── alerts/               # Важные изменения
    └── {date}.md
```

**Правила:**
- Все файлы имеют frontmatter с `status: processed`
- Каждая операция записывается в `log.md`
- `index.md` обновляется при добавлении новых страниц

### Layer 3: Decisions

```
decisions/
└── {decision_name}.md    # Стратегические решения на основе CI
```

**Правила:**
- Создаются только на основе значимых инсайтов
- Содержат рекомендации для AIM Agency

## Frontmatter Standards

### Competitor Profile

```yaml
---
employer_id: "123456"
name: "Competitor Name"
industry: "IT"
website: "https://example.com"
monitored_since: "2026-05-04"
status: processed
---
```

### Vacancy Analysis

```yaml
---
vacancy_id: "123456"
name: "Position Name"
employer: "Competitor Name"
analyzed_at: "2026-05-04T19:00:00+03:00"
status: processed
---
```

### Alert

```yaml
---
date: "2026-05-04"
changes_count: 5
status: processed
---
```

### Report

```yaml
---
date: "2026-05-04"
type: weekly_report
status: processed
---
```

## Operations

### Ingest (Monitor)

1. Fetch vacancies from HH API
2. Save snapshot to `raw/snapshots/{date}/{employer_id}.json`
3. Update `log.md` with operation timestamp

### Query (Analyze)

1. Read snapshot from `raw/`
2. Extract insights
3. Create/update page in `wiki/`
4. Update `index.md`

### Lint (Health Check)

1. Check for orphaned snapshots (no wiki pages)
2. Check for stale data (>90 days)
3. Validate frontmatter consistency
4. Report gaps in monitoring

## Monitoring Schedule

- **Daily:** Monitor competitors (collect snapshots)
- **Daily:** Detect changes (compare with previous day)
- **Weekly:** Generate report (aggregate insights)
- **Monthly:** Cleanup old snapshots (>90 days)

## Competitors List

Список отслеживаемых конкурентов хранится в коде агента (`HHAgent.competitors`).

Для добавления нового конкурента:
1. Найти `employer_id` на hh.ru
2. Добавить в список `competitors`
3. Создать профиль в `wiki/competitors/{name}.md`
