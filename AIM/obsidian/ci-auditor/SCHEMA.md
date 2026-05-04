# CI Auditor Vault Schema

**Agent:** CI Auditor  
**Type:** Competitive Intelligence - Website Audit  
**Created:** 2026-05-04

## Purpose

CI Auditor проводит глубокий аудит сайтов конкурентов по 4 направлениям:
- Technical (скорость, мобильность, SEO)
- Content (структура, качество, ключевые слова)
- UX/UI (юзабилити, конверсия, CTA)
- Marketing (каналы, воронки, лид-магниты)

## Vault Structure (LLM Wiki Pattern)

### Layer 1: Raw Sources (Immutable)
```
raw/
├── audit-reports/          # Сырые данные аудитов
├── pagespeed-data/         # PageSpeed Insights данные
├── screenshots/            # Скриншоты сайтов
└── crawl-data/             # Данные краулинга
```

### Layer 2: Wiki (LLM-Generated Knowledge)
```
wiki/
├── index.md               # Content-oriented каталог
├── log.md                 # Chronological операции
├── concepts/              # Концепции аудита
├── technologies/          # Технологии и инструменты
├── strategies/            # Стратегии аудита
├── agents/                # Агенты системы
├── workflows/             # Процессы аудита
├── projects/              # Проекты аудита
├── sources/               # Обработанные источники
└── connections/           # Связи и синтезы
```

### Layer 3: Decisions
```
decisions/
├── audit-methodology.md   # Методология аудита
├── scoring-system.md      # Система оценок
└── gap-analysis.md        # Анализ gaps
```

## Operations

### 1. Ingest
Обработка сырых данных аудита:
- Парсинг audit reports → wiki/sources/
- Извлечение insights → wiki/concepts/
- Создание audit profiles → wiki/projects/

### 2. Query
Ответы на вопросы об аудитах:
- "Какие слабые места у конкурента X?"
- "Какой средний PageSpeed в нише?"
- "Где gaps для нашего клиента?"

### 3. Lint
Проверка качества:
- Противоречия в оценках
- Устаревшие данные (> 30 дней)
- Orphan audit reports
- Missing dimensions

## Frontmatter Convention

```yaml
---
title: "Audit: Competitor Name"
type: audit-report
competitor: "Competitor Name"
audit_date: "2026-05-04"
audit_type: "deep"
dimensions: ["technical", "content", "ux_ui", "marketing"]
total_score: 78.5
grade: "B"
status: processed
output: "wiki/projects/competitor-name-audit.md"
---
```

## Categories

### Concepts
- Audit dimensions (technical, content, UX/UI, marketing)
- Scoring methodology
- Gap analysis framework
- Competitive benchmarking

### Technologies
- PageSpeed Insights
- Lighthouse
- Screaming Frog
- GTmetrix
- WebPageTest

### Strategies
- Quick audit (technical + content)
- Deep audit (+ UX/UI)
- Full audit (+ marketing)
- Continuous monitoring

### Agents
- CI Auditor (этот агент)
- CI Scout (поставщик списка конкурентов)
- CI Orchestrator (координатор)

### Workflows
- Competitor audit pipeline
- Score calculation
- Gap identification
- Report generation

### Projects
- Audit reports для конкретных конкурентов
- Market benchmarks
- Gap opportunities

### Sources
- Raw audit data
- PageSpeed reports
- Crawl results

### Connections
- Audit → Scout (получение списка конкурентов)
- Audit → Reputation (связь с репутацией)
- Audit → Strategist (input для стратегии)

## Rules

1. **Immutability:** raw/ никогда не изменяется
2. **Freshness:** Аудиты старше 30 дней помечаются как stale
3. **Completeness:** Каждый audit должен иметь все dimensions для своего типа
4. **Traceability:** Каждая wiki страница ссылается на raw source
5. **Consistency:** Scoring system единообразен для всех аудитов

## Metrics

- Total audits conducted
- Average market score
- Dimensions coverage
- Gaps identified
- Stale audits (> 30 days)
