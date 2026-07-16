# CI Reputation Vault Schema

**Agent:** CI Reputation  
**Type:** Competitive Intelligence - Reputation Analysis  
**Created:** 2026-05-04

## Purpose

CI Reputation анализирует репутацию конкурентов через:
- Отзывы (Яндекс.Карты, 2GIS, Prodoctorov, Zoon, НаПоправку)
- Sentiment analysis (позитив/негатив/нейтрал)
- Topic analysis (что хвалят/ругают)
- Репутационные риски и возможности

## Vault Structure (LLM Wiki Pattern)

### Layer 1: Raw Sources (Immutable)
```
raw/
├── reviews/                # Сырые отзывы из источников
│   ├── yandex-maps/
│   ├── 2gis/
│   ├── prodoctorov/
│   ├── zoon/
│   └── napopravku/
├── social-mentions/        # Упоминания в соцсетях
└── media-mentions/         # Упоминания в медиа
```

### Layer 2: Wiki (LLM-Generated Knowledge)
```
wiki/
├── index.md               # Content-oriented каталог
├── log.md                 # Chronological операции
├── concepts/              # Концепции репутации
├── technologies/          # Технологии анализа
├── strategies/            # Стратегии мониторинга
├── agents/                # Агенты системы
├── workflows/             # Процессы анализа
├── projects/              # Проекты анализа
├── sources/               # Обработанные источники
└── connections/           # Связи и синтезы
```

### Layer 3: Decisions
```
decisions/
├── sentiment-methodology.md   # Методология sentiment analysis
├── topic-taxonomy.md          # Таксономия тем отзывов
└── scoring-system.md          # Система reputation scoring
```

## Operations

### 1. Ingest
Обработка сырых отзывов:
- Парсинг reviews → wiki/sources/
- Sentiment classification → wiki/concepts/
- Topic extraction → wiki/concepts/
- Reputation profiles → wiki/projects/

### 2. Query
Ответы на вопросы о репутации:
- "Какая репутация у конкурента X?"
- "Что чаще всего хвалят/ругают в нише?"
- "Какие репутационные риски у лидеров?"

### 3. Lint
Проверка качества:
- Противоречия в sentiment
- Устаревшие отзывы (> 90 дней)
- Orphan review data
- Missing sentiment classification

## Frontmatter Convention

```yaml
---
title: "Reputation: Competitor Name"
type: reputation-analysis
competitor: "Competitor Name"
analysis_date: "2026-05-04"
total_reviews: 450
avg_rating: 4.3
reputation_score: 78.5
grade: "B"
sentiment:
  positive: 72
  negative: 15
  neutral: 13
status: processed
output: "wiki/projects/competitor-name-reputation.md"
---
```

## Categories

### Concepts
- Sentiment analysis (positive/negative/neutral)
- Topic modeling (service, doctors, price, etc.)
- Reputation scoring methodology
- Review source weighting

### Technologies
- NLP для sentiment analysis
- Topic modeling (LDA, BERT)
- Review aggregation APIs
- Social listening tools

### Strategies
- Multi-source review collection
- Weighted reputation scoring
- Continuous reputation monitoring
- Crisis detection

### Agents
- CI Reputation (этот агент)
- CI Scout (поставщик списка конкурентов)
- CI Orchestrator (координатор)

### Workflows
- Review collection pipeline
- Sentiment analysis workflow
- Topic extraction workflow
- Reputation scoring

### Projects
- Reputation reports для конкретных конкурентов
- Market reputation benchmarks
- Reputation risks and opportunities

### Sources
- Яндекс.Карты reviews
- 2GIS reviews
- Prodoctorov reviews
- Zoon reviews
- НаПоправку reviews

### Connections
- Reputation → Scout (получение списка конкурентов)
- Reputation → Auditor (связь с качеством сайта)
- Reputation → Strategist (input для стратегии)

## Rules

1. **Immutability:** raw/ никогда не изменяется
2. **Freshness:** Отзывы старше 90 дней помечаются как stale
3. **Source Weighting:** Яндекс.Карты (30%), 2GIS (25%), Prodoctorov (20%), Zoon (15%), НаПоправку (10%)
4. **Traceability:** Каждая wiki страница ссылается на raw reviews
5. **Consistency:** Sentiment classification единообразна для всех источников

## Metrics

- Total reviews analyzed
- Average market reputation
- Sentiment distribution
- Topic coverage
- Stale reviews (> 90 days)
- Reputation risks identified
