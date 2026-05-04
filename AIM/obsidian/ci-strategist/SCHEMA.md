# CI Strategist Vault Schema

**Agent:** CI Strategist  
**Type:** Competitive Intelligence - Strategic Synthesis  
**Created:** 2026-05-04

## Purpose

CI Strategist синтезирует данные от всех CI агентов и генерирует:
- Стратегические рекомендации
- Позиционирование
- Дифференциацию
- Конкурентные преимущества
- Go-to-Market стратегию

## Vault Structure (LLM Wiki Pattern)

### Layer 1: Raw Sources (Immutable)
```
raw/
├── phase-results/          # Результаты от всех фаз CI
│   ├── scout/
│   ├── auditor/
│   ├── reputation/
│   └── other-agents/
└── client-context/         # Контекст клиента
```

### Layer 2: Wiki (LLM-Generated Knowledge)
```
wiki/
├── index.md               # Content-oriented каталог
├── log.md                 # Chronological операции
├── concepts/              # Стратегические концепции
├── technologies/          # Фреймворки и методологии
├── strategies/            # Стратегии и подходы
├── agents/                # Агенты системы
├── workflows/             # Процессы синтеза
├── projects/              # Стратегические проекты
├── sources/               # Обработанные источники
└── connections/           # Связи и синтезы
```

### Layer 3: Decisions
```
decisions/
├── positioning-framework.md      # Фреймворк позиционирования
├── differentiation-strategy.md   # Стратегия дифференциации
├── competitive-advantage.md      # Конкурентные преимущества
└── gtm-strategy.md              # Go-to-Market стратегия
```

## Operations

### 1. Ingest
Обработка результатов от всех агентов:
- Агрегация insights → wiki/sources/
- Синтез стратегий → wiki/strategies/
- Создание рекомендаций → wiki/projects/

### 2. Query
Ответы на стратегические вопросы:
- "Как позиционировать клиента?"
- "Какие конкурентные преимущества?"
- "Какая GTM стратегия оптимальна?"

### 3. Lint
Проверка качества:
- Противоречия в рекомендациях
- Несвязанные стратегии
- Missing rationale
- Устаревшие данные (> 90 дней)

## Frontmatter Convention

```yaml
---
title: "Strategy: Client Name"
type: strategic-synthesis
client: "Client Name"
synthesis_date: "2026-05-04"
positioning: "Цифровой лидер"
differentiation: "Онлайн-запись + персональный подход"
competitive_advantages: 3
gtm_channels: ["SEO", "Яндекс.Директ", "Telegram"]
recommendations: 5
status: processed
output: "wiki/projects/client-name-strategy.md"
---
```

## Categories

### Concepts
- Positioning frameworks (price/quality/service/innovation)
- Differentiation types (product/service/channel/brand)
- Competitive advantage sources (cost/differentiation/focus)
- GTM components (segment/value prop/channels/pricing)

### Technologies
- Strategy frameworks (Porter, Blue Ocean, SWOT)
- Positioning tools
- Competitive analysis methodologies

### Strategies
- Positioning strategy
- Differentiation strategy
- Competitive advantage strategy
- Go-to-Market strategy

### Agents
- CI Strategist (этот агент)
- CI Scout (input: market data)
- CI Auditor (input: audit data)
- CI Reputation (input: reputation data)

### Workflows
- Strategic synthesis pipeline
- Positioning development
- Differentiation design
- GTM planning

### Projects
- Strategic plans для конкретных клиентов
- Market positioning maps
- GTM roadmaps

### Sources
- Scout insights
- Auditor insights
- Reputation insights
- Other agent insights

### Connections
- Strategist → Scout (market insights)
- Strategist → Auditor (quality insights)
- Strategist → Reputation (reputation insights)
- Strategist → All agents (comprehensive synthesis)

## Rules

1. **Immutability:** raw/ никогда не изменяется
2. **Freshness:** Стратегии старше 90 дней помечаются как stale
3. **Completeness:** Каждая стратегия должна иметь positioning + differentiation + advantages + GTM
4. **Traceability:** Каждая рекомендация ссылается на source insights
5. **Consistency:** Все компоненты стратегии согласованы между собой

## Metrics

- Total strategies generated
- Recommendations by priority
- Average confidence score
- Strategy implementation rate
- Stale strategies (> 90 days)
