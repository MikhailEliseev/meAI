---
title: "CI Research Agent Vault Schema"
type: vault-schema
created: 2026-05-15T22:50
status: active
---

# CI Research Agent Vault Schema

**Цель:** Хранение и обработка результатов Industry Benchmark Research по LLM Wiki паттерну.

**Паттерн:** raw/ (источники) → wiki/ (структурированное знание) → decisions/ (стратегические решения)

---

## Структура Vault

```
ci-research/
├── raw/                          # Слой 1: Исходные данные (immutable)
│   └── benchmarks/               # Benchmark reports от CI Research Agent
│       └── YYYY-MM-DD_industry/  # Папка по дате и индустрии
│           ├── manifest.json     # Метаданные исследования
│           ├── competitors/      # Данные по конкурентам
│           ├── sources/          # Собранные источники
│           └── report.json       # Полный отчёт
│
├── wiki/                         # Слой 2: Структурированное знание
│   ├── index.md                  # Content-oriented каталог
│   ├── log.md                    # Chronological запись операций
│   ├── concepts/                 # Концепции и паттерны
│   │   ├── growth-laws.md        # Growth Laws (prevalence ≥30%)
│   │   ├── sales-laws.md         # Sales Laws
│   │   └── archetypes.md         # Industry Archetypes
│   ├── technologies/             # Технологии и инструменты
│   │   ├── api-integrations.md   # SEMrush, Ahrefs, etc.
│   │   └── scraping-tools.md     # Playwright, Trafilatura
│   ├── strategies/               # Стратегии и методы
│   │   ├── source-harvest.md     # Tier 1/2/3 methodology
│   │   ├── unit-economics.md     # ACV, CAC, LTV, payback
│   │   └── transferability.md    # Copy/Adapt/Ignore framework
│   ├── agents/                   # Агенты системы
│   │   └── ci-research-agent.md  # CI Research Agent profile
│   ├── workflows/                # Процессы и workflow
│   │   ├── 4-layer-methodology.md # Source → Company → Meta → Application
│   │   └── ice-scoring.md        # Impact × Confidence × Ease
│   ├── projects/                 # Проекты (benchmark по индустриям)
│   │   ├── dental-clinics.md     # Dental clinics benchmark
│   │   ├── beauty-salons.md      # Beauty salons benchmark
│   │   └── fitness-centers.md    # Fitness centers benchmark
│   ├── sources/                  # Обработанные источники
│   │   └── competitor-profiles.md # Профили конкурентов
│   └── connections/              # Связи и синтезы
│       └── cross-industry-patterns.md # Паттерны между индустриями
│
└── decisions/                    # Слой 3: Стратегические решения
    ├── copy-patterns.md          # Что копировать (ICE > 400)
    ├── ignore-patterns.md        # Что игнорировать (unique advantages)
    └── sequencing-roadmap.md     # 3-phase implementation plan
```

---

## Операции (Обязательные)

### 1. Ingest (raw/ → wiki/)

**Триггер:** Новый benchmark report от CI Research Agent

**Процесс:**
1. Сохранить raw данные в `raw/benchmarks/YYYY-MM-DD_industry/`
2. Извлечь Growth Laws → `wiki/concepts/growth-laws.md`
3. Извлечь Sales Laws → `wiki/concepts/sales-laws.md`
4. Извлечь Archetypes → `wiki/concepts/archetypes.md`
5. Создать project page → `wiki/projects/{industry}.md`
6. Обновить connections → `wiki/connections/cross-industry-patterns.md`
7. Обновить `wiki/index.md` и `wiki/log.md`

**Формат log.md:**
```markdown
## [2026-05-15 22:50] ingest | Dental clinics benchmark
- Competitors: 5
- Growth Laws: 3
- Copy Patterns: 8 (ICE > 400)
- Output: [[dental-clinics]]
```

### 2. Query (вопрос → wiki/ → ответ)

**Триггер:** Вопрос от пользователя или агента

**Процесс:**
1. Поиск в `wiki/` по категориям
2. Чтение релевантных страниц
3. Синтез ответа с цитатами
4. Создание новой страницы (если нужно)
5. Обновление `wiki/log.md`

**Формат log.md:**
```markdown
## [2026-05-15 22:55] query | What are common acquisition channels in dental?
- Sources: [[dental-clinics]], [[growth-laws]]
- Answer: SEO (80%), Google Ads (60%), Referrals (40%)
- Output: [[dental-acquisition-channels]]
```

### 3. Lint (проверка здоровья)

**Триггер:** Еженедельно или по запросу

**Проверки:**
- Противоречия между страницами
- Orphan pages (нет ссылок)
- Gaps (missing data)
- Устаревшие данные (> 6 месяцев)

**Формат log.md:**
```markdown
## [2026-05-15 23:00] lint | Health check
- Contradictions: 0
- Orphans: 2 ([[old-page-1]], [[old-page-2]])
- Gaps: 1 (missing fitness-centers benchmark)
- Stale: 0
```

---

## Специальные Файлы

### wiki/index.md

Content-oriented каталог всех страниц с статистикой:

```markdown
# CI Research Vault Index

**Last Updated:** 2026-05-15 22:50  
**Total Pages:** 15  
**Total Benchmarks:** 3

## Concepts (3)
- [[growth-laws]] — 12 laws across 3 industries
- [[sales-laws]] — 8 laws
- [[archetypes]] — 4 archetypes

## Projects (3)
- [[dental-clinics]] — 5 competitors, 8 copy patterns
- [[beauty-salons]] — 4 competitors, 6 copy patterns
- [[fitness-centers]] — 3 competitors, 5 copy patterns

## Connections (1)
- [[cross-industry-patterns]] — 5 universal patterns
```

### wiki/log.md

Chronological запись всех операций:

```markdown
# CI Research Vault Log

## [2026-05-15 22:50] ingest | Dental clinics benchmark
- Competitors: 5
- Growth Laws: 3
- Output: [[dental-clinics]]

## [2026-05-15 22:55] query | Common acquisition channels
- Sources: [[dental-clinics]], [[growth-laws]]
- Output: [[dental-acquisition-channels]]
```

---

## Frontmatter Стандарт

Все страницы в `wiki/` ОБЯЗАНЫ иметь frontmatter:

```yaml
---
title: "Page Title"
type: concept | technology | strategy | agent | workflow | project | source | connection
created: YYYY-MM-DDTHH:MM
updated: YYYY-MM-DDTHH:MM
status: active | archived | draft
tags: [tag1, tag2, tag3]
sources: [[[source1]], [[source2]]]  # Ссылки на raw/ или другие wiki/ страницы
---
```

---

## Правила Обработки

1. **ВСЕГДА проверяй frontmatter `status: processed`** перед чтением
2. Если `status: processed` → читай wiki/ (из поля `output`)
3. Если нет → читай raw/ и обрабатывай
4. **Immutability:** raw/ НИКОГДА не изменяется после создания
5. **Linking:** Используй `[[page-name]]` для связей между страницами
6. **Versioning:** При обновлении страницы обновляй `updated:` в frontmatter

---

## Метрики Здоровья

**Цель:** Vault должен быть актуальным, связным, без противоречий

**Метрики:**
- **Coverage:** % индустрий с benchmark (target: 80%)
- **Freshness:** Средний возраст benchmark (target: < 6 месяцев)
- **Connectivity:** Среднее количество связей на страницу (target: > 3)
- **Consistency:** % страниц без противоречий (target: 100%)

**Проверка:** Еженедельно через Lint операцию

---

**Версия:** 1.0.0  
**Дата создания:** 2026-05-15  
**Автор:** CI Research Agent  
**Статус:** ✅ Готов к использованию
