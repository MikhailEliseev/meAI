# CI Research Agent - Спецификация

**Дата:** 2026-05-15  
**Magister:** SEO Magister  
**Приоритет:** P0 (критичный для конкурентного анализа)  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
CI Research Agent проводит глубокий reverse-engineering конкурентов в медицинском маркетинге, используя Industry Benchmark подход. Извлекает growth mechanics, GTM стратегии и transferable patterns для клиентов AIM.

### Что делает:
- ✅ Source Harvest — собирает и структурирует первичные источники о конкурентах (founder interviews, operator posts, case studies)
- ✅ Company Synthesis — создаёт reverse-engineering memos по каждому конкуренту (growth machine, unit economics, competitive advantage)
- ✅ Meta-Synthesis — извлекает cross-company паттерны (growth laws, sales laws, archetypes)
- ✅ Transferability Analysis — определяет что копировать, что адаптировать, что игнорировать
- ✅ API Integration — интегрирует SimilarWeb, Ahrefs, SEMrush, Crunchbase, HealthGrades/Zocdoc для метрик

### Что НЕ делает:
- ❌ Не делает поверхностный competitor analysis ("кто конкуренты и что они делают")
- ❌ Не копирует паттерны без анализа transferability
- ❌ Не использует mock данные (только реальные источники с evidence labels)
- ❌ Не нарушает HIPAA compliance (не собирает patient data без consent)

### Место в иерархии:
```
SEO Magister
    ↓
SEO Orchestrator
    ↓
CI Research Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "ci-research-agent",
  "payload": {
    "industry": "стоматология Москва",
    "client_context": {
      "positioning": "премиум имплантация",
      "budget": 500000,
      "goals": ["увеличить трафик на 50%", "снизить CAC на 30%"]
    },
    "research_depth": "tier1",
    "focus_areas": ["growth", "gtm", "trust", "local_seo"],
    "competitor_list": ["competitor1.ru", "competitor2.ru"],
    "max_competitors": 10
  }
}
```

**Обязательные параметры:**
- `industry` (string) - Индустрия клиента (например: "стоматология Москва", "пластическая хирургия СПб")
- `client_context` (object) - Контекст клиента (позиционирование, бюджет, цели)
- `research_depth` (string) - Глубина анализа: "tier1" (10-20 компаний), "tier2" (5-10 компаний)

**Опциональные параметры:**
- `focus_areas` (array) - Приоритеты анализа: ["growth", "gtm", "pricing", "trust", "expansion"]
- `competitor_list` (array) - Список конкурентов для анализа (если известны)
- `max_competitors` (int) - Максимальное количество конкурентов для анализа (default: 10)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "ci-research-agent",
  "payload": {
    "status": "success",
    "result": {
      "benchmark_report_path": "obsidian/seo-magister/wiki/ci-research/YYYY-MM-DD-industry/",
      "competitors_analyzed": 10,
      "growth_laws": [
        {
          "law": "Niche-first wedge",
          "prevalence": 0.8,
          "description": "80% конкурентов начали с узкой ниши",
          "transferability": "copy",
          "preconditions": ["clear niche definition", "high willingness to pay"]
        }
      ],
      "sales_laws": [
        {
          "law": "Free consultation converts",
          "prevalence": 0.6,
          "description": "60% используют бесплатную консультацию",
          "transferability": "copy",
          "preconditions": ["low consultation cost", "high trust requirement"]
        }
      ],
      "archetypes": [
        {
          "name": "SEO + GMB dominators",
          "members": ["competitor1.ru", "competitor2.ru"],
          "characteristics": ["4.5+ GMB rating", "top 3 organic", "video testimonials"]
        }
      ],
      "do_copy": [
        {
          "pattern": "Video testimonials on homepage",
          "impact": 8,
          "confidence": 9,
          "ease": 7,
          "ice_score": 168,
          "implementation": "Снять 5-10 видео отзывов пациентов с consent"
        }
      ],
      "dont_copy": [
        {
          "pattern": "Celebrity endorsements",
          "reason": "Requires unique relationships and high budget",
          "alternative": "Focus on verified patient reviews instead"
        }
      ],
      "sequencing_roadmap": [
        {
          "phase": 1,
          "duration": "1-2 weeks",
          "patterns": ["GMB optimization", "Review generation"],
          "expected_impact": "Local visibility +30%"
        }
      ]
    },
    "metrics": {
      "execution_time_ms": 3600000,
      "competitors_analyzed": 10,
      "sources_collected": 520,
      "evidence_quality_score": 2.3,
      "api_cost_usd": 11.50
    },
    "errors": []
  }
}
```

**Структура результата:**
- `benchmark_report_path` (string) - Путь к полному benchmark report в Obsidian vault
- `competitors_analyzed` (int) - Количество проанализированных конкурентов
- `growth_laws` (array) - Извлечённые growth laws с prevalence и transferability
- `sales_laws` (array) - Извлечённые sales laws с prevalence и transferability
- `archetypes` (array) - Кластеры конкурентов по growth mechanics
- `do_copy` (array) - Паттерны для копирования с ICE scoring
- `dont_copy` (array) - Паттерны для игнорирования с обоснованием
- `sequencing_roadmap` (array) - Последовательность внедрения паттернов

**Метрики:**
- `execution_time_ms` - Время выполнения в миллисекундах (~1 час для tier1)
- `competitors_analyzed` - Количество проанализированных конкурентов
- `sources_collected` - Количество собранных источников
- `evidence_quality_score` - Качество evidence (1.0-3.0, target >2.0)
- `api_cost_usd` - Стоимость API calls (~$1.15 per competitor)

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Source Harvest (2-3 часа на 10 конкурентов)

**1.1 Competitor Discovery:**
- Если `competitor_list` не предоставлен → использовать SEMrush Competitor Discovery API
- Фильтровать по `industry` и географии
- Ранжировать по Domain Rating (Ahrefs) и Traffic (SimilarWeb)
- Выбрать top N конкурентов (N = `max_competitors`)

**1.2 Primary Sources Collection (Tier 1):**
- Founder interviews: поиск через Google/Yandex (`"founder interview" + competitor_domain`)
- Operator posts: LinkedIn, Twitter, Habr, VC.ru
- Company case studies: официальный сайт, партнёрские сайты
- Product demos: YouTube, Vimeo
- Customer testimonials: сайт, HealthGrades, Zocdoc

**1.3 Secondary Sources Collection (Tier 2):**
- Industry reports: поиск через Google Scholar, ResearchGate
- News articles: поиск через Google News, Yandex News
- Conference talks: поиск через YouTube, SlideShare
- Webinars: поиск через сайт конкурента

**1.4 Tertiary Sources Collection (Tier 3):**
- Wikipedia entries
- Generic blog posts
- Social media mentions

**1.5 Evidence Labeling:**
- Для каждого claim добавить evidence label:
  - `[E]` - directly sourced evidence (Tier 1)
  - `[I]` - inference from sourced facts
  - `[UV]` - unverified estimate
  - `[OQ]` - open question (needs investigation)
  - `[H]` - hypothesis to test

**1.6 API Data Collection:**
- SimilarWeb: traffic, sources, engagement, bounce rate
- Ahrefs: backlinks, organic keywords, Domain Rating, referring domains
- SEMrush: paid keywords, ad copy, competitor discovery
- Crunchbase: funding, team size, milestones
- HealthGrades/Zocdoc: reviews, ratings, booking patterns

**1.7 Evidence Archive Structure:**
```
obsidian/seo-magister/wiki/ci-research/YYYY-MM-DD-industry/
├── source-harvest/
│   ├── competitor1.ru/
│   │   ├── company.md              # Профиль конкурента
│   │   ├── sources/                # Первичные источники
│   │   │   ├── founder-interview-2024-01-15.md
│   │   │   ├── case-study-implants.md
│   │   │   └── ...
│   │   └── people/                 # Ключевые люди
│   │       ├── founder-ivan-petrov.md
│   │       └── cmo-maria-sidorova.md
│   ├── competitor2.ru/
│   └── ...
```

### Шаг 2: Company Synthesis (3-4 часа на 10 конкурентов)

**2.1 Growth Machine Reverse-Engineering:**

Для каждого конкурента извлечь:

**Initial Wedge:**
- С чего начали? (niche, segment, geography)
- Почему это сработало? (timing, demand, competition)
- Evidence: `[E]` founder interview / `[I]` inferred from early content

**Target Buyer/User:**
- Decision maker (кто принимает решение о покупке)
- End user (кто использует услугу)
- Blocker (кто может заблокировать покупку)
- Evidence: `[E]` case studies / `[I]` inferred from marketing

**AARRR Framework:**

1. **Acquisition** (как привлекают):
   - Primary channel: SEO, PPC, Social, Referral, Direct
   - CAC estimate: `[E]` from case study / `[UV]` unverified
   - Tactics: specific tactics used (e.g., "GMB optimization", "Instagram ads")

2. **Activation** (как конвертируют):
   - Conversion mechanism: free consultation, virtual tour, discount
   - Conversion rate: `[E]` / `[UV]`
   - Tactics: landing page, CTA, trust signals

3. **Retention** (как удерживают):
   - Retention mechanism: loyalty program, subscription, follow-up care
   - Churn rate: `[E]` / `[UV]`
   - Tactics: email campaigns, SMS reminders, personalized offers

4. **Revenue** (как монетизируют):
   - ACV (Average Contract Value): `[E]` from pricing page / `[UV]`
   - LTV (Lifetime Value): `[I]` calculated from ACV × retention
   - Payback period: `[I]` CAC / (ACV × gross margin)

5. **Referral** (как масштабируют):
   - Referral mechanism: referral program, word of mouth, partnerships
   - Referral rate: `[E]` / `[UV]`
   - Tactics: incentives, social proof, ambassador programs

**2.2 Competitive Advantage Analysis:**

**Core Motion (1-2 sentences):**
- Как они на самом деле выигрывают в рынке?
- Example: "Доминируют в локальном SEO через 4.8★ GMB рейтинг и 500+ видео отзывов"

**Competitive Moats:**
- Network effects: `[E]` / `[I]`
- Switching costs: `[E]` / `[I]`
- Brand/reputation: `[E]` / `[I]`
- Proprietary data/tech: `[E]` / `[I]`

**Risks & Fragilities:**
- Dependency risks (single channel, single supplier)
- Competitive risks (new entrants, price wars)
- Operational risks (key person dependency, scalability limits)

**2.3 Company Synthesis Memo:**

Создать memo по шаблону (Appendix C из research report):
```markdown
# [Competitor Name] - Competitive Intelligence Memo

## Executive Summary
[2-3 sentences: What they do, how they win, why it matters]

## Company Snapshot
- Founded: [Year] [E/I/UV]
- Team Size: [Number] [E/I/UV]
- Revenue: [Estimate] [E/I/UV]
- Customers: [Number] [E/I/UV]

## Core Motion
[1-2 sentences: How they actually win]

## Initial Wedge
[Specific niche/segment] [E/I/UV]

## Growth Machine
[AARRR breakdown with evidence labels]

## Unit Economics
| Metric | Estimate | Evidence |
|--------|----------|----------|
| ACV | $X,XXX | [E/I/UV] |
| CAC | $XXX | [E/I/UV] |
| LTV | $X,XXX | [E/I/UV] |
| Payback | X months | [E/I/UV] |

## Why They Won
[Factor analysis with weighted scores]

## Competitive Moats
[List with evidence]

## Risks & Fragilities
[List with evidence]

## Transferable Patterns
[Pattern | Transferability | Preconditions | Risk]

## Sources
[Tier 1/2/3 sources with links]

## Open Questions
[OQ: Questions needing investigation]
```

Сохранить в:
```
obsidian/seo-magister/wiki/ci-research/YYYY-MM-DD-industry/
└── synthesis/
    ├── competitor1.ru/
    │   └── playbook-analysis.md
    ├── competitor2.ru/
    └── ...
```

### Шаг 3: Meta-Synthesis (2-3 часа)

**3.1 Growth Laws Extraction:**

Для каждого паттерна:
1. Подсчитать prevalence (% конкурентов использующих)
2. Если prevalence ≥ 30% (3+ из 10) → это Growth Law
3. Документировать:
   - Law name
   - Prevalence (%)
   - Description
   - Observed in (list of competitors)
   - Preconditions (что нужно для работы)
   - Boundary conditions (когда НЕ работает)

**Примеры Growth Laws:**
- "Niche-first wedge" (80% prevalence)
- "SEO + GMB dominance" (70% prevalence)
- "Video testimonials convert" (60% prevalence)
- "Free consultation lowers barrier" (60% prevalence)

**3.2 Sales Laws Extraction:**

Аналогично Growth Laws, но фокус на sales cycle:
- Decision maker patterns
- Sales cycle length
- Pilot/POC structure
- Pricing strategies

**3.3 Archetypes Definition:**

Кластеризация конкурентов по growth mechanics:
1. Идентифицировать 2-5 distinct clusters
2. Для каждого archetype:
   - Name (descriptive)
   - Members (list of competitors)
   - Core characteristics
   - Growth mechanics
   - When this archetype works

**Примеры Archetypes:**
- "SEO + GMB Dominators" (40% конкурентов)
- "Instagram + Influencer Players" (30% конкурентов)
- "Referral Network Builders" (20% конкурентов)

**3.4 Pattern Matrix:**

Создать таблицу competitor × pattern:
```markdown
| Competitor | Initial Wedge | Acquisition | Conversion | Retention | Trust Signal | Local SEO | Referral |
|------------|---------------|-------------|------------|-----------|--------------|-----------|----------|
| Comp A | Dentists Moscow | SEO + GMB | Free consult | Loyalty | Video | 4.8★ | 10% bonus |
| Comp B | Plastic surgery | Instagram | Virtual | Follow-up | Photos | 4.5★ | 3 free |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

Рассчитать prevalence для каждого pattern.

**3.5 Cross-Company Insights:**

Синтезировать insights across competitors:
- Universal patterns (работают для всех)
- Niche patterns (работают для specific segments)
- Emerging patterns (новые, но перспективные)
- Deprecated patterns (устаревшие)

Сохранить в:
```
obsidian/seo-magister/wiki/ci-research/YYYY-MM-DD-industry/
└── meta-synthesis/
    ├── growth-laws.md
    ├── sales-laws.md
    ├── archetypes.md
    ├── pattern-matrix.yaml
    └── company-comparison-table.md
```

### Шаг 4: Transferability Analysis (1-2 часа)

**4.1 Copy/Adapt/Ignore Classification:**

Для каждого pattern определить transferability:

**DO COPY (High transferability):**
- Prevalence >60%
- Preconditions met (check against `client_context`)
- No unique advantages required
- Low implementation risk
- Clear ROI

**ADAPT (Medium transferability):**
- Prevalence 40-60%
- Some preconditions met
- Requires customization
- Medium implementation risk
- Uncertain ROI

**DON'T COPY (Low transferability):**
- Prevalence <40%
- Preconditions not met
- Requires unique advantages (celebrity, proprietary tech)
- High implementation risk
- Negative ROI

**4.2 ICE Scoring (для DO COPY patterns):**

```
ICE Score = Impact × Confidence × Ease
```

- **Impact** (1-10): Насколько сильно повлияет на метрики клиента
- **Confidence** (1-10): Насколько уверены что сработает
- **Ease** (1-10): Насколько легко внедрить

Ранжировать patterns по ICE score (descending).

**4.3 Sequencing Roadmap:**

Создать roadmap внедрения:

**Phase 1 (Quick Wins, 1-2 weeks):**
- High ICE score (>150)
- Low implementation risk
- Fast time to value

**Phase 2 (Medium-term, 1-2 months):**
- Medium ICE score (100-150)
- Medium implementation risk
- Requires some setup

**Phase 3 (Long-term, 3-6 months):**
- Lower ICE score (<100) but strategic
- High implementation risk
- Requires significant investment

**4.4 Risk Assessment:**

Для каждого pattern документировать:
- Implementation risks
- Mitigation strategies
- Fallback options

Сохранить в:
```
obsidian/seo-magister/wiki/ci-research/YYYY-MM-DD-industry/
└── application/
    ├── do-copy-dont-copy.md
    ├── sequencing-roadmap.md
    └── priority-matrix.md
```

### Шаг 5: Формирование результата

**5.1 Benchmark Report README:**

Создать executive summary:
```markdown
# Competitive Intelligence Benchmark: [Industry]

**Date:** YYYY-MM-DD
**Competitors Analyzed:** 10
**Evidence Quality:** 2.3/3.0
**API Cost:** $11.50

## Key Findings

### Growth Laws (5)
1. Niche-first wedge (80% prevalence) → DO COPY
2. SEO + GMB dominance (70%) → DO COPY
3. Video testimonials (60%) → DO COPY
4. Free consultation (60%) → DO COPY
5. Loyalty programs (50%) → ADAPT

### Sales Laws (5)
[List]

### Archetypes (3)
[List]

### Top Recommendations (ICE >150)
1. [Pattern] (ICE: 168) - [Implementation]
2. [Pattern] (ICE: 154) - [Implementation]
3. [Pattern] (ICE: 147) - [Implementation]

### Don't Copy
1. [Pattern] - [Reason]
2. [Pattern] - [Reason]

## Sequencing Roadmap
[Phase 1/2/3 breakdown]

## Full Report Structure
- source-harvest/ (520 sources)
- synthesis/ (10 company memos)
- meta-synthesis/ (laws, archetypes, matrix)
- application/ (do-copy, roadmap, priorities)
```

**5.2 Метрики:**
- `execution_time_ms` - фактическое время выполнения
- `competitors_analyzed` - количество конкурентов
- `sources_collected` - количество источников
- `evidence_quality_score` - (Tier1×3 + Tier2×2 + Tier3×1) / Total
- `api_cost_usd` - сумма API calls

**5.3 Событие результата:**
Сформировать событие `subagent.task.completed` с полным результатом.

### Шаг 6: Отправка результата

1. Отправить событие через Event Bus
2. Логировать в Event Store
3. Сохранить в Obsidian vault (уже сохранено на предыдущих шагах)
4. Обновить `wiki/log.md` в SEO Magister vault

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**SimilarWeb API:**
- API endpoint: `https://api.similarweb.com/v1/`
- Аутентификация: API key
- Rate limit: 100 requests/day (free tier), 10,000/day (paid)
- Cost: $0.25 per competitor (traffic + engagement + sources)
- Документация: https://developer.similarweb.com/

**Ahrefs API:**
- API endpoint: `https://api.ahrefs.com/v3/`
- Аутентификация: API key
- Rate limit: 500 requests/day (Lite), 2,000/day (Standard)
- Cost: $0.40 per competitor (backlinks + keywords + DR + referring domains)
- Документация: https://ahrefs.com/api/documentation

**SEMrush API:**
- API endpoint: `https://api.semrush.com/`
- Аутентификация: API key
- Rate limit: 10,000 units/day (Pro), 30,000/day (Guru)
- Cost: $0.25 per competitor (paid keywords + ad copy + competitor discovery)
- Документация: https://www.semrush.com/api-documentation/

**Crunchbase API:**
- API endpoint: `https://api.crunchbase.com/api/v4/`
- Аутентификация: API key
- Rate limit: 200 requests/minute
- Cost: $0.10 per competitor (company data + funding)
- Документация: https://data.crunchbase.com/docs

**HealthGrades API:**
- API endpoint: `https://api.healthgrades.com/v1/`
- Аутентификация: API key
- Rate limit: 1,000 requests/day
- Cost: $0.10 per provider (reviews + ratings)
- Документация: https://developer.healthgrades.com/

**Zocdoc API:**
- API endpoint: `https://api.zocdoc.com/v1/`
- Аутентификация: OAuth 2.0
- Rate limit: 500 requests/hour
- Cost: $0.05 per provider (reviews + booking patterns)
- Документация: https://developer.zocdoc.com/

### Внутренние зависимости:

- **Event Bus** (обязательно) - для получения задач и отправки результатов
- **Event Store** (обязательно) - для audit trail
- **Obsidian vault** (обязательно) - для хранения benchmark reports
- **API Clients Layer** (обязательно) - базовые клиенты с circuit breaker, retry, rate limiting
- **Keyword Research Agent** (опционально) - для поиска конкурентов через SEMrush

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Evidence Quality:**
- Метрика: Evidence Quality Score = (Tier1_claims × 3 + Tier2_claims × 2 + Tier3_claims × 1) / Total_claims
- Целевое значение: >2.0 (majority Tier 1-2 sources)
- Как измерять: Подсчитать evidence labels в company memos

**Pattern Extraction:**
- Метрика: Количество извлечённых growth laws
- Целевое значение: 5-10 laws
- Как измерять: Подсчитать laws с prevalence ≥30%

**Transferability Rate:**
- Метрика: % patterns marked "Copy"
- Целевое значение: >50%
- Как измерять: (DO COPY patterns / Total patterns) × 100%

### Производительность:

**Скорость:**
- Среднее время выполнения: < 2 часа (tier2), < 4 часа (tier1)
- 95-й перцентиль: < 3 часа (tier2), < 6 часов (tier1)
- Максимальное время: < 8 часов

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99% (если некоторые API недоступны)
- Failure rate: < 1%

**Cost Efficiency:**
- API cost per competitor: < $1.50
- Total cost for tier1 (10 competitors): < $15.00
- Total cost for tier2 (20 competitors): < $30.00

### Бизнес-метрики:

**Влияние на клиента:**
- Implementation success rate: >50% of "Copy" patterns successfully implemented
- Time to insight: <2 hours from request to actionable recommendations
- ROI: Client metrics improve by >20% after implementing top 3 recommendations

**Влияние на AIM:**
- Client retention: Clients using CI Research have >80% retention rate
- Upsell rate: >30% of clients order follow-up CI Research
- NPS: >8.0 for CI Research deliverables


---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешное выполнение (tier2, 5 конкурентов)

**Входные данные:**
```json
{
  "industry": "стоматология Москва",
  "client_context": {
    "positioning": "премиум имплантация",
    "budget": 500000,
    "goals": ["увеличить трафик на 50%", "снизить CAC на 30%"]
  },
  "research_depth": "tier2",
  "focus_areas": ["growth", "trust", "local_seo"],
  "max_competitors": 5
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "benchmark_report_path": "obsidian/seo-magister/wiki/ci-research/2026-05-15-stomatology-moscow/",
    "competitors_analyzed": 5,
    "growth_laws": [
      {
        "law": "Niche-first wedge",
        "prevalence": 0.8,
        "description": "80% конкурентов начали с узкой ниши (имплантация, виниры, брекеты)",
        "transferability": "copy",
        "preconditions": ["clear niche definition", "high willingness to pay in niche"]
      },
      {
        "law": "SEO + GMB dominance",
        "prevalence": 1.0,
        "description": "100% конкурентов доминируют в локальном SEO через GMB",
        "transferability": "copy",
        "preconditions": ["GMB profile setup", "review generation system"]
      },
      {
        "law": "Video testimonials convert",
        "prevalence": 0.6,
        "description": "60% используют видео отзывы на главной странице",
        "transferability": "copy",
        "preconditions": ["patient consent", "video production capability"]
      }
    ],
    "sales_laws": [
      {
        "law": "Free consultation lowers barrier",
        "prevalence": 0.8,
        "description": "80% предлагают бесплатную консультацию",
        "transferability": "copy",
        "preconditions": ["low consultation cost", "high trust requirement"]
      }
    ],
    "archetypes": [
      {
        "name": "SEO + GMB Dominators",
        "members": ["implant-center.ru", "dental-premium.ru"],
        "characteristics": ["4.8+ GMB rating", "top 3 organic", "500+ reviews", "video testimonials"]
      },
      {
        "name": "Instagram + Influencer Players",
        "members": ["smile-clinic.ru"],
        "characteristics": ["50K+ Instagram followers", "influencer partnerships", "before/after photos"]
      }
    ],
    "do_copy": [
      {
        "pattern": "Video testimonials on homepage",
        "impact": 8,
        "confidence": 9,
        "ease": 7,
        "ice_score": 504,
        "implementation": "Снять 5-10 видео отзывов пациентов с consent, разместить на главной"
      },
      {
        "pattern": "GMB optimization with 4.8+ rating",
        "impact": 9,
        "confidence": 10,
        "ease": 8,
        "ice_score": 720,
        "implementation": "Оптимизировать GMB профиль, запустить систему генерации отзывов"
      },
      {
        "pattern": "Free consultation CTA",
        "impact": 7,
        "confidence": 9,
        "ease": 9,
        "ice_score": 567,
        "implementation": "Добавить CTA 'Бесплатная консультация' на все страницы"
      }
    ],
    "dont_copy": [
      {
        "pattern": "Celebrity endorsements",
        "reason": "Requires unique relationships and budget >1M RUB",
        "alternative": "Focus on verified patient reviews and doctor credentials instead"
      }
    ],
    "sequencing_roadmap": [
      {
        "phase": 1,
        "duration": "1-2 weeks",
        "patterns": ["GMB optimization", "Free consultation CTA"],
        "expected_impact": "Local visibility +30%, Conversion rate +15%"
      },
      {
        "phase": 2,
        "duration": "2-4 weeks",
        "patterns": ["Video testimonials", "Review generation system"],
        "expected_impact": "Trust signals +40%, Conversion rate +20%"
      }
    ]
  },
  "metrics": {
    "execution_time_ms": 7200000,
    "competitors_analyzed": 5,
    "sources_collected": 260,
    "evidence_quality_score": 2.4,
    "api_cost_usd": 5.75
  },
  "errors": []
}
```

### Пример 2: Частичный успех (API недоступен)

**Входные данные:**
```json
{
  "industry": "пластическая хирургия СПб",
  "client_context": {
    "positioning": "безопасная пластика",
    "budget": 800000,
    "goals": ["увеличить доверие", "снизить отказы"]
  },
  "research_depth": "tier1",
  "max_competitors": 10
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "benchmark_report_path": "obsidian/seo-magister/wiki/ci-research/2026-05-15-plastic-surgery-spb/",
    "competitors_analyzed": 10,
    "growth_laws": [
      {
        "law": "Before/after photos dominate",
        "prevalence": 0.9,
        "description": "90% используют before/after фото с consent",
        "transferability": "copy",
        "preconditions": ["patient consent", "professional photography"]
      }
    ],
    "sales_laws": [],
    "archetypes": [],
    "do_copy": [],
    "dont_copy": [],
    "sequencing_roadmap": []
  },
  "metrics": {
    "execution_time_ms": 14400000,
    "competitors_analyzed": 10,
    "sources_collected": 480,
    "evidence_quality_score": 2.1,
    "api_cost_usd": 9.20
  },
  "errors": [
    {
      "code": "EXTERNAL_API_ERROR",
      "message": "HealthGrades API unavailable",
      "details": {
        "api": "HealthGrades",
        "status_code": 503,
        "retry_attempts": 3
      }
    }
  ]
}
```

### Пример 3: Ошибка (невалидные входные данные)

**Входные данные:**
```json
{
  "industry": "",
  "client_context": {},
  "research_depth": "invalid_tier"
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 100,
    "competitors_analyzed": 0,
    "sources_collected": 0,
    "evidence_quality_score": 0.0,
    "api_cost_usd": 0.0
  },
  "errors": [
    {
      "code": "INVALID_INPUT",
      "message": "industry is required and cannot be empty",
      "details": {
        "param": "industry",
        "value": ""
      }
    },
    {
      "code": "INVALID_INPUT",
      "message": "research_depth must be 'tier1' or 'tier2'",
      "details": {
        "param": "research_depth",
        "value": "invalid_tier"
      }
    }
  ]
}
```

---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Действие: Вернуть failure сразу, не начинать обработку
- Retry: Нет
- Примеры:
  - `industry` пустой или отсутствует
  - `research_depth` не "tier1" или "tier2"
  - `max_competitors` < 1 или > 50

**Ошибка внешнего API:**
- Код: `EXTERNAL_API_ERROR`
- Действие: Retry с exponential backoff (1s → 2s → 4s)
- Retry: До 3 попыток
- Fallback: Продолжить без данных этого API, вернуть partial_success
- Примеры:
  - SimilarWeb API 503 Service Unavailable
  - Ahrefs API 429 Rate Limit Exceeded
  - HealthGrades API timeout

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с обработанными конкурентами
- Retry: Нет
- Примеры:
  - Source harvest занял >2 часа для tier2
  - Company synthesis занял >4 часа для tier1

**Недостаточно источников:**
- Код: `INSUFFICIENT_SOURCES`
- Действие: Вернуть partial_success с warning
- Retry: Нет
- Примеры:
  - Найдено <10 sources per competitor (target: 50+)
  - Evidence quality score <1.5 (target: >2.0)

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать stack trace, вернуть failure
- Retry: Нет
- Примеры:
  - Ошибка парсинга JSON
  - Ошибка записи в Obsidian vault
  - Ошибка Event Bus

### Graceful degradation:

**При частичном сбое API:**
1. Продолжить обработку без данных этого API
2. Пометить affected metrics как `[UV]` unverified
3. Вернуть partial_success
4. Указать в errors какой API недоступен

**При timeout:**
1. Обработать максимум конкурентов за доступное время
2. Вернуть partial_success с обработанными данными
3. Указать сколько конкурентов не обработано
4. Позволить Orchestrator решить: retry или принять partial result

**При недостаточном качестве evidence:**
1. Завершить обработку
2. Вернуть success с warning
3. Указать evidence_quality_score в metrics
4. Рекомендовать manual review

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От SEO Magister:**
- Best practices по competitor analysis
- Актуальные техники reverse-engineering
- Обновления алгоритмов Google/Yandex
- Новые источники данных (API, tools)

**Из собственного опыта:**
- Успешные кейсы (какие patterns сработали для клиентов)
- Неудачные попытки (какие patterns не сработали)
- Метрики результатов (implementation success rate, ROI)
- Feedback от клиентов (что было полезно, что нет)

**Из Obsidian vault:**
- Исторические benchmark reports
- Паттерны и инсайты из прошлых исследований
- Корреляции между patterns и client success
- Evolution of patterns over time

### Адаптация:

**Когда адаптироваться:**
- Evidence quality score падает ниже 2.0
- Implementation success rate падает ниже 50%
- Появляются новые API или data sources
- Изменяются алгоритмы Google/Yandex (major updates)
- Клиенты запрашивают новые focus_areas

**Как адаптироваться:**
1. Получить обновлённые знания от SEO Magister
2. Протестировать новый подход на 1-2 конкурентах
3. Сравнить метрики до/после (evidence quality, transferability rate)
4. Если улучшение >10% → применить к остальным конкурентам
5. Обновить алгоритм работы в спецификации

**Примеры адаптации:**
- Добавить новый API (например, Google My Business API)
- Изменить evidence labeling (добавить новый тип `[V]` verified)
- Обновить transferability criteria (новые preconditions)
- Добавить новый focus_area (например, "ai_integration")

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `subagent.task.assigned`
- Все исходящие события `subagent.task.completed`
- Correlation ID для трейсинга
- Timestamp для каждого события

**В Obsidian vault (обязательно):**
- Полный benchmark report (source-harvest, synthesis, meta-synthesis, application)
- Метрики производительности (execution_time, sources_collected, evidence_quality)
- Инсайты и паттерны (growth laws, sales laws, archetypes)
- API costs и usage statistics

**В системные логи (опционально):**
- Debug информация (API requests/responses)
- Ошибки и warnings (API failures, timeouts)
- Performance traces (time per competitor, time per step)

### Формат логов:

```
[2026-05-15 18:54:16] [INFO] [ci-research-agent] [uuid-1234] Starting source harvest for 5 competitors
[2026-05-15 19:12:34] [INFO] [ci-research-agent] [uuid-1234] Collected 260 sources (52 per competitor avg)
[2026-05-15 19:45:22] [WARN] [ci-research-agent] [uuid-1234] HealthGrades API unavailable, continuing without
[2026-05-15 20:23:11] [INFO] [ci-research-agent] [uuid-1234] Completed company synthesis for 5 competitors
[2026-05-15 20:54:16] [INFO] [ci-research-agent] [uuid-1234] Task completed: 5 competitors, 3 growth laws, 1 sales law
```

### Obsidian vault log entry:

```markdown
## [2026-05-15 20:54] ci-research | Completed benchmark for стоматология Москва

**Competitors:** 5  
**Sources:** 260 (52 avg)  
**Evidence Quality:** 2.4/3.0  
**Growth Laws:** 3  
**Sales Laws:** 1  
**Archetypes:** 2  
**API Cost:** $5.75  
**Duration:** 2h  

**Top Recommendations:**
1. GMB optimization (ICE: 720)
2. Video testimonials (ICE: 504)
3. Free consultation CTA (ICE: 567)

**Report:** [[2026-05-15-stomatology-moscow/README.md]]
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**

**Валидация входных данных:**
- `test_validate_input_valid()` - корректные данные проходят
- `test_validate_input_missing_industry()` - ошибка если industry отсутствует
- `test_validate_input_invalid_research_depth()` - ошибка если research_depth невалиден
- `test_validate_input_max_competitors_out_of_range()` - ошибка если max_competitors < 1 или > 50

**Source Harvest:**
- `test_source_harvest_primary_sources()` - собирает Tier 1 sources
- `test_source_harvest_secondary_sources()` - собирает Tier 2 sources
- `test_source_harvest_evidence_labeling()` - правильно проставляет [E], [I], [UV]
- `test_source_harvest_api_integration()` - интегрируется с SimilarWeb, Ahrefs, SEMrush

**Company Synthesis:**
- `test_company_synthesis_growth_machine()` - извлекает AARRR framework
- `test_company_synthesis_unit_economics()` - оценивает ACV, CAC, LTV, payback
- `test_company_synthesis_competitive_advantage()` - определяет core motion и moats
- `test_company_synthesis_memo_format()` - создаёт memo по шаблону

**Meta-Synthesis:**
- `test_meta_synthesis_growth_laws()` - извлекает growth laws с prevalence ≥30%
- `test_meta_synthesis_sales_laws()` - извлекает sales laws
- `test_meta_synthesis_archetypes()` - кластеризует конкурентов
- `test_meta_synthesis_pattern_matrix()` - создаёт competitor × pattern таблицу

**Transferability Analysis:**
- `test_transferability_copy_adapt_ignore()` - классифицирует patterns
- `test_transferability_ice_scoring()` - рассчитывает ICE scores
- `test_transferability_sequencing_roadmap()` - создаёт roadmap

**Обработка ошибок:**
- `test_error_handling_invalid_input()` - возвращает failure при невалидных данных
- `test_error_handling_api_failure()` - retry с exponential backoff
- `test_error_handling_timeout()` - возвращает partial_success при timeout
- `test_error_handling_graceful_degradation()` - продолжает без failed API

### Integration тесты:

**Обязательные сценарии:**

**Event Bus Integration:**
- `test_integration_receive_task_from_orchestrator()` - получает задачу
- `test_integration_send_result_to_orchestrator()` - отправляет результат
- `test_integration_correlation_id_preserved()` - сохраняет correlation_id

**Event Store Integration:**
- `test_integration_log_to_event_store()` - логирует события
- `test_integration_event_store_audit_trail()` - создаёт audit trail

**Obsidian Integration:**
- `test_integration_save_to_obsidian_vault()` - сохраняет benchmark report
- `test_integration_obsidian_vault_structure()` - создаёт правильную структуру
- `test_integration_obsidian_log_entry()` - добавляет запись в wiki/log.md

**API Integration:**
- `test_integration_similarweb_api()` - интегрируется с SimilarWeb
- `test_integration_ahrefs_api()` - интегрируется с Ahrefs
- `test_integration_semrush_api()` - интегрируется с SEMrush
- `test_integration_crunchbase_api()` - интегрируется с Crunchbase
- `test_integration_healthgrades_api()` - интегрируется с HealthGrades

### E2E тесты:

**Обязательные сценарии:**

**Полный цикл (tier2, 5 конкурентов):**
- `test_e2e_tier2_5_competitors()` - полный цикл от задачи до результата
- Проверки:
  - Задача получена от Orchestrator
  - Source harvest завершён (260 sources)
  - Company synthesis завершён (5 memos)
  - Meta-synthesis завершён (3 growth laws, 1 sales law, 2 archetypes)
  - Transferability analysis завершён (3 do_copy, 1 dont_copy, 2-phase roadmap)
  - Результат отправлен Orchestrator
  - Benchmark report сохранён в Obsidian
  - Execution time < 3 hours
  - API cost < $7.00

**Обработка ошибок:**
- `test_e2e_api_failure_graceful_degradation()` - продолжает при API failure
- `test_e2e_timeout_partial_success()` - возвращает partial_success при timeout

**Граничные случаи:**
- `test_e2e_single_competitor()` - работает с 1 конкурентом
- `test_e2e_max_competitors()` - работает с 50 конкурентами (tier1 max)
- `test_e2e_no_sources_found()` - обрабатывает случай когда источники не найдены

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен (Redis/RabbitMQ)
- Event Store доступен (PostgreSQL/SQLite)
- Obsidian vault доступен (filesystem)
- Internet connection (для API calls)

**Зависимости:**
```
httpx>=0.27.0              # HTTP client для API calls
pybreaker>=1.0.0           # Circuit breaker
tenacity>=8.2.0            # Retry logic
aiolimiter>=1.1.0          # Rate limiting
aiocache[redis]>=0.12.0    # Caching
beautifulsoup4>=4.12.0     # HTML parsing для source harvest
trafilatura>=1.6.0         # Text extraction
pydantic>=2.0.0            # Data validation
structlog>=24.1.0          # Structured logging
prometheus-client>=0.20.0  # Metrics
```

**Конфигурация:**
```env
# Subagent ID
SUBAGENT_ID=ci-research-agent

# Event Bus
EVENT_BUS_URL=redis://localhost:6379/0

# Event Store
EVENT_STORE_URL=postgresql://localhost:5432/aim

# Obsidian Vault
OBSIDIAN_VAULT_PATH=/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/obsidian/seo-magister

# API Keys
SIMILARWEB_API_KEY=your_key_here
AHREFS_API_KEY=your_key_here
SEMRUSH_API_KEY=your_key_here
CRUNCHBASE_API_KEY=your_key_here
HEALTHGRADES_API_KEY=your_key_here
ZOCDOC_API_KEY=your_key_here

# Rate Limits
RATE_LIMIT_CAPACITY=10
RATE_LIMIT_REFILL=1.0

# Timeouts
SOURCE_HARVEST_TIMEOUT_SECONDS=7200    # 2 hours
COMPANY_SYNTHESIS_TIMEOUT_SECONDS=14400  # 4 hours
TOTAL_TIMEOUT_SECONDS=28800            # 8 hours

# Quality Gates
MIN_SOURCES_PER_COMPETITOR=10
TARGET_EVIDENCE_QUALITY_SCORE=2.0
MIN_GROWTH_LAWS=3
```

### Мониторинг:

**Метрики для алертов:**

**Success Rate:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Action: Investigate errors, check API availability

**Execution Time:**
- Avg execution time > 3 hours (tier2) → Warning
- Avg execution time > 6 hours (tier1) → Warning
- 95th percentile > 4 hours (tier2) → Critical
- 95th percentile > 8 hours (tier1) → Critical
- Action: Optimize source harvest, check API latency

**Evidence Quality:**
- Evidence quality score < 2.0 → Warning
- Evidence quality score < 1.5 → Critical
- Action: Improve source collection, add more Tier 1 sources

**API Cost:**
- API cost > $2.00 per competitor → Warning
- API cost > $3.00 per competitor → Critical
- Action: Optimize API usage, check for redundant calls

**Pattern Extraction:**
- Growth laws < 3 → Warning
- Growth laws < 1 → Critical
- Action: Increase competitor count, improve pattern detection

### Health Check:

**Endpoint:** `/health/ci-research-agent`

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "event_bus": "ok",
    "event_store": "ok",
    "obsidian_vault": "ok",
    "similarweb_api": "ok",
    "ahrefs_api": "ok",
    "semrush_api": "ok",
    "crunchbase_api": "ok",
    "healthgrades_api": "degraded",
    "zocdoc_api": "ok"
  },
  "metrics": {
    "tasks_completed_24h": 12,
    "avg_execution_time_ms": 10800000,
    "avg_evidence_quality_score": 2.3,
    "avg_api_cost_usd": 11.20
  }
}
```

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `SEO_MAGISTER_SPEC.md` - Спецификация родительского SEO Magister
- `SEO_ORCHESTRATOR_SPEC.md` - Спецификация родительского SEO Orchestrator
- `KEYWORD_RESEARCH_AGENT_SPEC.md` - Спецификация Keyword Research Agent (для поиска конкурентов)

### Код:
- `AIM/src/aim/subagents/seo/ci_research_agent.py` - Реализация
- `AIM/tests/subagents/seo/test_ci_research_agent.py` - Тесты

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- API Clients Layer (circuit breaker, retry, rate limiting)

### Research:
- `~/Documents/CI_Research_Agent_20260515/CI_Research_Report.md` - Deep research report (126.5 pages)
- `AIM/docs/briefs/CI_RESEARCH_AGENT_BRIEF.md` - Brief для этого агента

### Паттерны:
- Industry Benchmark Research Spec (user-provided)
- LLM Wiki Pattern (Karpathy) - для Obsidian vault structure
- Evidence Labeling System ([E], [I], [UV], [OQ], [H])

---

**Дата создания:** 2026-05-15  
**Автор:** meAI Architect (via spec-writer v2.0)  
**Версия:** 1.0  
**Статус:** Draft

**Research Cost:** $0.84 (exa-research model)  
**Research Duration:** ~15 minutes  
**Specification Size:** ~50 KB, ~1,100 lines

**Next Steps:**
1. Review specification with user
2. Archive research in obsidian/deep-research vault
3. Implement CI Research Agent
4. Create tests (unit, integration, E2E)
5. Deploy to production

