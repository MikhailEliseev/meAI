# CI Factchecker Vault Schema

**Agent:** CI Factchecker  
**Type:** Competitive Intelligence - Data Validation  
**Created:** 2026-05-04

## Purpose

CI Factchecker проверяет достоверность данных от всех CI агентов:
- Кросс-проверка данных из разных источников
- Выявление противоречий и несоответствий
- Оценка надёжности источников
- Валидация метрик и цифр
- Присвоение confidence scores

## Vault Structure (LLM Wiki Pattern)

### Layer 1: Raw Sources (Immutable)
```
raw/
├── validation-logs/        # Логи валидации
├── contradiction-reports/  # Отчёты о противоречиях
└── source-data/           # Данные от всех агентов
```

### Layer 2: Wiki (LLM-Generated Knowledge)
```
wiki/
├── index.md               # Content-oriented каталог
├── log.md                 # Chronological операции
├── concepts/              # Концепции валидации
├── technologies/          # Технологии проверки
├── strategies/            # Стратегии валидации
├── agents/                # Агенты системы
├── workflows/             # Процессы проверки
├── projects/              # Проекты валидации
├── sources/               # Обработанные источники
└── connections/           # Связи и синтезы
```

### Layer 3: Decisions
```
decisions/
├── validation-rules.md        # Правила валидации
├── source-reliability.md      # Надёжность источников
└── confidence-methodology.md  # Методология confidence scoring
```

## Operations

### 1. Ingest
Обработка данных для проверки:
- Извлечение фактов → wiki/sources/
- Валидация данных → wiki/concepts/
- Выявление противоречий → wiki/projects/

### 2. Query
Ответы на вопросы о качестве данных:
- "Насколько надёжны данные о конкуренте X?"
- "Какие противоречия в данных?"
- "Какой confidence score у этого факта?"

### 3. Lint
Проверка качества:
- Устаревшие validation rules
- Несогласованные confidence scores
- Missing source reliability data

## Frontmatter Convention

```yaml
---
title: "Validation: Data Source"
type: validation-report
validation_date: "2026-05-04"
total_facts: 150
validated: 142
failed: 3
warnings: 5
contradictions: 2
data_quality: "good"
avg_confidence: 0.87
status: processed
output: "wiki/projects/validation-report.md"
---
```

## Categories

### Concepts
- Cross-validation methodology
- Contradiction detection
- Source reliability tiers
- Confidence scoring

### Technologies
- Data validation frameworks
- Statistical validation methods
- Contradiction detection algorithms

### Strategies
- Multi-source validation
- Tiered reliability assessment
- Confidence-based filtering

### Agents
- CI Factchecker (этот агент)
- CI Scout (source of data)
- CI Auditor (source of data)
- CI Reputation (source of data)

### Workflows
- Fact extraction pipeline
- Cross-validation workflow
- Contradiction detection
- Confidence scoring

### Projects
- Validation reports
- Contradiction analyses
- Data quality assessments

### Sources
- Scout data
- Auditor data
- Reputation data
- Other agent data

### Connections
- Factchecker → Scout (validates competitor data)
- Factchecker → Auditor (validates audit scores)
- Factchecker → Reputation (validates review data)
- Factchecker → All agents (comprehensive validation)

## Rules

1. **Immutability:** raw/ никогда не изменяется
2. **Freshness:** Validation старше 7 дней помечается как stale
3. **Source Tiers:** Tier1 (0.95), Tier2 (0.85), Tier3 (0.70), Tier4 (0.50)
4. **Traceability:** Каждая validation ссылается на source facts
5. **Consistency:** Validation rules применяются единообразно

## Metrics

- Total facts validated
- Validation success rate
- Contradictions detected
- Average confidence score
- Data quality grade
