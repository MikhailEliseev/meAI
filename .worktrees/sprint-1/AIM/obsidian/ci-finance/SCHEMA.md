# CI Finance Vault Schema

**Agent:** CI Finance  
**Type:** Competitive Intelligence - Financial Analysis  
**Created:** 2026-05-04

## Purpose

CI Finance анализирует финансовое состояние конкурентов:
- Оценка выручки и прибыли
- Анализ инвестиций и финансирования
- Финансовые показатели (ROI, EBITDA, margins)
- Ценовая политика и маржинальность

## Vault Structure (LLM Wiki Pattern)

### Layer 1: Raw Sources (Immutable)
```
raw/
├── financial-data/         # Финансовые данные
├── spark-reports/          # Отчёты из СПАРК
├── hh-data/               # Данные о вакансиях (косвенная оценка)
└── pricing-data/          # Данные о ценах
```

### Layer 2: Wiki (LLM-Generated Knowledge)
```
wiki/
├── index.md               # Content-oriented каталог
├── log.md                 # Chronological операции
├── concepts/              # Финансовые концепции
├── technologies/          # Методы оценки
├── strategies/            # Стратегии анализа
├── agents/                # Агенты системы
├── workflows/             # Процессы анализа
├── projects/              # Финансовые проекты
├── sources/               # Обработанные источники
└── connections/           # Связи и синтезы
```

### Layer 3: Decisions
```
decisions/
├── estimation-methodology.md  # Методология оценки
├── confidence-scoring.md      # Система confidence scores
└── market-sizing.md          # Методы оценки рынка
```

## Operations

### 1. Ingest
Обработка финансовых данных:
- Парсинг financial reports → wiki/sources/
- Оценка метрик → wiki/concepts/
- Создание профилей → wiki/projects/

### 2. Query
Ответы на финансовые вопросы:
- "Какая выручка у конкурента X?"
- "Какая средняя маржинальность в нише?"
- "Кто получал инвестиции?"

### 3. Lint
Проверка качества:
- Противоречия в оценках
- Устаревшие данные (> 180 дней)
- Missing confidence scores
- Unrealistic estimates

## Frontmatter Convention

```yaml
---
title: "Finance: Competitor Name"
type: financial-analysis
competitor: "Competitor Name"
analysis_date: "2026-05-04"
revenue_estimate: 50000000
profit_estimate: 7500000
margin_percent: 15.0
roi_percent: 25.0
has_funding: true
confidence: 0.75
status: processed
output: "wiki/projects/competitor-name-finance.md"
---
```

## Categories

### Concepts
- Revenue estimation methods
- Profit margin analysis
- ROI calculation
- Market concentration (HHI)

### Technologies
- СПАРК API
- hh.ru scraping
- Financial modeling
- Market sizing techniques

### Strategies
- Employee-based estimation
- Office-size estimation
- Ad-spend estimation
- Market-share estimation

### Agents
- CI Finance (этот агент)
- CI Scout (input: competitor list)
- CI Orchestrator (координатор)

### Workflows
- Financial data collection
- Revenue estimation
- Profitability analysis
- Market sizing

### Projects
- Financial profiles для конкурентов
- Market financial analysis
- Investment activity reports

### Sources
- СПАРК reports
- hh.ru vacancy data
- Pricing data
- Public financial statements

### Connections
- Finance → Scout (получение списка)
- Finance → Pricing (связь с ценами)
- Finance → Strategist (input для стратегии)

## Rules

1. **Immutability:** raw/ никогда не изменяется
2. **Freshness:** Финансовые оценки старше 180 дней помечаются как stale
3. **Confidence:** Каждая оценка имеет confidence score (0.0-1.0)
4. **Traceability:** Каждая оценка ссылается на estimation method
5. **Realism:** Оценки проверяются на реалистичность

## Metrics

- Total companies analyzed
- Average revenue estimate
- Average margin
- Funded companies count
- Market concentration level
