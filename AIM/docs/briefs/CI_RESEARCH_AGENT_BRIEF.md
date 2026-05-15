# Бриф: CI Research Agent (Competitor Intelligence)

**Дата:** 2026-05-15  
**Приоритет:** P0 (критичный для конкурентного анализа)  
**Родительский Magister:** SEO Magister

## Назначение

CI Research Agent проводит глубокий reverse-engineering конкурентов в медицинском маркетинге, используя Industry Benchmark подход. Цель — не просто описать конкурентов, а извлечь их growth mechanics, GTM стратегии, и transferable patterns для клиентов AIM.

**Ключевое отличие от обычного competitor analysis:**
- Не "кто конкуренты и что они делают"
- А "как они выросли, почему это сработало, что можно скопировать"

## Контекст и специфика

### Медицинская специфика
- Конкуренты в healthcare/medical marketing (клиники, медцентры, врачи)
- Compliance: HIPAA, медицинская реклама, этика
- Trust architecture критична (пациенты доверяют жизнь)
- Длинный sales cycle (пациент исследует месяцами)
- Reputation-first adoption (отзывы, кейсы, сертификаты)

### Industry Benchmark подход (из spec)
**4 слоя анализа:**
1. **Source Harvest** — структурированный архив первичных источников
2. **Company Synthesis** — reverse-engineering memo по каждому конкуренту
3. **Meta-Synthesis** — growth laws, archetypes, pattern matrix
4. **Application Layer** — что копировать, что адаптировать, что игнорировать

**Evidence discipline:**
- [E] = directly sourced evidence
- [I] = inference from sourced facts
- [UV] = unverified estimate
- [OQ] = open question
- [H] = hypothesis to test

### Проблемы, которые решает
1. Клиенты не понимают, почему конкуренты успешны
2. Поверхностный анализ ("у них красивый сайт") не даёт actionable insights
3. Копирование без понимания механики приводит к провалу
4. Нет структуры для извлечения transferable patterns

## Интеграции

### Входные данные
**От пользователя (через Operator):**
- `industry` — индустрия клиента (например: "стоматология Москва")
- `client_context` — контекст клиента (позиционирование, бюджет, цели)
- `research_depth` — глубина анализа (tier 1: 10-20 компаний, tier 2: 5-10)
- `focus_areas` — приоритеты (growth, GTM, pricing, trust, expansion)

**От других агентов:**
- Keyword Research Agent → ключевые слова для поиска конкурентов
- Technical SEO Agent → технические метрики конкурентов
- Content Gap Agent → контент-стратегии конкурентов

### Выходные данные
**Структурированный benchmark report:**
```
benchmark-report/
  README.md                          # Executive summary
  source-harvest/
    <competitor>/
      company.md                     # Профиль конкурента
      sources/                       # Первичные источники
      people/                        # Ключевые люди
  synthesis/
    <competitor>/
      playbook-analysis.md           # Reverse-engineering memo
  meta-synthesis/
    growth-laws.md                   # Паттерны роста
    sales-laws.md                    # Паттерны продаж
    archetypes.md                    # Архетипы конкурентов
    pattern-matrix.yaml              # Матрица паттернов
    company-comparison-table.md      # Сравнительная таблица
  application/
    do-copy-dont-copy.md             # Что копировать
    sequencing-roadmap.md            # Последовательность внедрения
    priority-matrix.md               # Приоритеты
```

**События через Event Bus:**
- `ci.research.started` → начало исследования
- `ci.source.harvested` → источник обработан
- `ci.company.synthesized` → конкурент проанализирован
- `ci.meta.synthesized` → cross-company анализ готов
- `ci.research.completed` → benchmark report готов

### Связанные агенты
**Upstream (получает данные):**
- Keyword Research Agent — ключевые слова
- Technical SEO Agent — технические метрики
- Content Gap Agent — контент-стратегии

**Downstream (передаёт данные):**
- SEO Magister — growth laws для SEO
- Content Magister — контент-паттерны
- Ads Magister — GTM стратегии

### Внешние API/сервисы
**Для Source Harvest:**
- SimilarWeb API — трафик, источники, engagement
- Ahrefs API — backlinks, organic keywords, DR
- SEMrush API — paid keywords, ad copy, competitors
- Google Search API — SERP analysis, featured snippets
- Crunchbase API — funding, team, milestones
- LinkedIn API — team size, key hires, org structure

**Для медицинской специфики:**
- HealthGrades API — отзывы пациентов, рейтинги врачей
- Zocdoc API — booking patterns, availability
- Google My Business API — local presence, reviews

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Source Harvest методология**
   - Как собирать первичные источники (founder interviews, podcasts, operator posts)
   - Как структурировать архив (company.md, sources/, people/)
   - Как отличать evidence от inference
   - Приоритет источников (primary > secondary > tertiary)

2. **Growth Machine Reverse-Engineering**
   - Как извлечь initial wedge (с чего начали)
   - Как понять target buyer/user
   - Как декомпозировать growth system (acquisition → conversion → expansion)
   - Как выявить unit economics (ACV, CAC, LTV, payback)

3. **Medical Marketing Specifics**
   - Trust architecture в healthcare (сертификаты, кейсы, отзывы)
   - Compliance constraints (HIPAA, медицинская реклама)
   - Patient journey (awareness → consideration → decision → retention)
   - Reputation-first adoption patterns

4. **Pattern Extraction**
   - Как создавать growth laws (что повторяется у 3+ конкурентов)
   - Как создавать sales laws (паттерны продаж)
   - Как определять archetypes (кластеры похожих стратегий)
   - Как строить pattern matrix (competitor x pattern)

5. **Transferability Analysis**
   - Как определить что можно копировать
   - Как определить что нужно адаптировать
   - Как определить что НЕ копировать (unique advantages)
   - Как определить preconditions для копирования

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **Sales Cycle Reverse-Engineering**
   - Кто покупает (decision maker)
   - Кто использует (end user)
   - Кто блокирует (procurement, legal)
   - Pilot/POC структура

2. **Implementation/Deployment Model**
   - Onboarding sequence
   - Time to value
   - Customer success motion
   - Scale-up path

3. **Competitive Moats**
   - Network effects
   - Switching costs
   - Brand/reputation
   - Proprietary data/tech

4. **API Integration Patterns**
   - Как интегрировать SimilarWeb, Ahrefs, SEMrush
   - Rate limiting, caching, cost optimization
   - Fallback strategies при недоступности API

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. **Publishing Layer**
   - Как публиковать benchmark как сайт
   - Public vs private layers
   - Content model для публикации

2. **Funding Analysis**
   - Funding rounds (только если есть operator quotes/metrics)
   - Investor profiles (низкий приоритет)

3. **Product Features**
   - Детальный feature comparison (не критично для growth mechanics)

## Дополнительные материалы

**Исходный spec:** Industry Benchmark Research Spec (предоставлен пользователем)

**Ключевые концепции из spec:**
- Evidence labels: [E], [I], [UV], [OQ], [H]
- Source priority: primary/operator > secondary > tertiary
- 4-layer structure: harvest → synthesis → meta-synthesis → application
- Quality gates: growth machine explained, evidence separated, transferability identified

**Связанные спецификации:**
- Keyword Research Agent (для поиска конкурентов)
- Technical SEO Agent (для технических метрик)
- Content Gap Agent (для контент-анализа)

**TODO из других агентов:**
- Нет (новый агент)

---

**Следующий шаг:** Этап 2 — Целевое исследование (deep-research)
