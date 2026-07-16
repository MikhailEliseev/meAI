# CI Pipeline — Полный аудит системы конкурентной разведки

**Дата аудита:** 2026-05-29
**Проект:** meAI / AIM (AI-first medical marketing agency)
**Автор аудита:** Claude Code (по запросу Михаила Елисеева)

---

## 1. Что такое AIM и зачем ему конкурентная разведка

**AIM** — AI-first агентство медицинского маркетинга (iamaim.ru). Работает ТОЛЬКО в коммерческой медицине (ООО, АО, ЗАО, ИП), без государственных учреждений.

**Конкурентная разведка (CI)** — один из ключевых продуктов агентства. Используется на двух уровнях:

1. **Пресс-релизный уровень** — быстрый анализ при первом контакте с клиентом. Показываем, что мы уже знаем его рынок. Запускается через Hermes (AI-ассистент агентства).
2. **Полный CI** — глубокий анализ для платящих клиентов. 16 фаз, 23 агента, до 90 минут работы.

---

## 2. Архитектура системы (как оно устроено)

```
meAI/                              # Command Center
├── AIM/                           # Agency application
│   ├── src/aim/
│   │   ├── api/                   # FastAPI endpoints
│   │   │   ├── competitors.py     # /api/competitors/*
│   │   │   └── seo.py            # /api/seo/*
│   │   ├── services/
│   │   │   ├── ci_marketing_analysis.py  # ⭐ Пресс-релизный анализатор
│   │   │   └── ci/               # Новый pipeline (сервисы)
│   │   │       ├── pipeline_runner.py    # Новый оркестратор
│   │   │       ├── comparison_matrix.py  # Матрица сравнения
│   │   │       ├── dialogue_manager.py   # LLM-диалог с клиентом
│   │   │       ├── models.py            # Модели данных
│   │   │       ├── seo_auditor.py       # SEO аудит
│   │   │       ├── social_scanner.py    # Сканер соцсетей
│   │   │       ├── review_collector.py  # Сбор отзывов
│   │   │       ├── doctor_extractor.py  # Извлечение врачей
│   │   │       ├── article_scanner.py   # Поиск публикаций
│   │   │       ├── apify_social_finder.py
│   │   │       └── telegram_channel_finder.py
│   │   └── subagents/competitive_intel/
│   │       ├── orchestrator/
│   │       │   └── ci_orchestrator.py   # ⭐ Полный CI оркестратор
│   │       └── agents/                  # 22 агента (файлы .py)
│   │           ├── ci_scout.py          # Поиск конкурентов
│   │           ├── ci_auditor.py        # Аудит сайтов
│   │           ├── ci_deep_analyzer.py  # Глубокий анализ
│   │           ├── ci_reputation.py     # Репутация
│   │           ├── ci_finance.py        # Финансы
│   │           ├── ci_vacancies.py      # Вакансии
│   │           ├── ci_tech_real.py      # Технологии
│   │           ├── ci_site_crawler.py   # Краулер сайтов
│   │           ├── ci_content_improved.py # Контент
│   │           ├── ci_pricing.py        # Цены
│   │           ├── ci_ecosystem.py      # Экосистема
│   │           ├── ci_backlink.py       # Бэклинки
│   │           ├── ci_rank_tracker.py   # Ранкинг
│   │           ├── ci_factchecker.py    # Проверка фактов
│   │           ├── ci_strategist.py     # Стратегия
│   │           ├── ci_prioritizer.py    # Приоритизация
│   │           ├── ci_marketing_strategy.py
│   │           ├── ci_offer_generator.py # Генерация КП
│   │           ├── ci_qa_validator.py
│   │           ├── ci_url_validator.py
│   │           └── business_report.py
│   ├── hermes/app/tools/
│   │   ├── run_ci_analysis.py    # Hermes tool: пресс-релиз
│   │   └── run_seo_audit.py      # Hermes tool: SEO аудит
│   └── docs/
├── src/meai/                      # Framework
│   ├── agents/base_agent.py       # Agent, Task, TaskResult
│   └── events/event_bus.py        # EventBus (async messaging)
```

---

## 3. Два параллельных CI-пайплайна

Система имеет ДВА независимых пайплайна конкурентной разведки, которые частично пересекаются по функциональности, но построены по-разному:

| Характеристика | Pipeline 1 (Пресс-релизный) | Pipeline 2 (Полный CI) |
|---|---|---|
| **Точка входа** | `POST /api/competitors/analyze/stream` | `POST /api/seo/audit` |
| **Hermes tool** | `run_ci_analysis` | `run_seo_audit` |
| **Оркестратор** | `CiMarketingAnalyzer` → `PipelineRunner` | `CIOrchestrator` |
| **Ключевой файл** | `ci_marketing_analysis.py` (964 строки) | `ci_orchestrator.py` (939 строк) |
| **Кол-во фаз** | 3 шага (pipeline → matrix → chat) | 16 фаз |
| **Кол-во агентов** | ~5 коллекторов в pipeline | 22 агента (зарегистрировано) |
| **Время работы** | ~30-60 секунд | quick: ~15 мин, deep: ~45 мин, full: ~90 мин |
| **Tier'ы** | Нет | quick (1-4), deep (1-9), full (1-16) |
| **LLM** | Нет (структурный summary) | DialogueManager (LLM-диалог) |
| **Результат** | chat_summary, feature_matrix, pricing_comparison, positioning_map, tactics, recommendation | WOW-цифры, инсайты, competitors, actions |

---

## 4. Pipeline 1: Пресс-релизный (run_ci_analysis)

### Полный путь вызова

```
Пользователь (в чате Hermes)
  → Hermes решает использовать tool "run_ci_analysis"
    → POST /api/competitors/analyze/stream (SSE streaming)
      → CiMarketingAnalyzer.analyze()
        → PipelineRunner.run()
          → Parallel: SEO audit + social scan + financials + website crawl + reviews
        → ComparisonMatrixBuilder.build()
        → _chat_summary_from_matrix() [структурный, без LLM]
        → _top_rec_from_matrix() [базовая строка]
      ← SSE: progress events + result
    ← {chat_summary, feature_matrix, pricing_comparison, positioning_map, steal_worthy_tactics, top_recommendation}
  → Hermes показывает результат клиенту
```

### Пошагово что происходит внутри PipelineRunner.run():

**Шаг 1 — Поиск конкурентов**
```python
# pipeline_runner.py:116-148
if named_competitors:  # URLs переданы напрямую
    competitors = self._named_urls_to_competitors(named_competitors)
else:
    competitors = await self._find_competitors(client_url, named)
    # → CompetitorMatcher.find_competitors()
    # → DaData + Google Maps + rusprofile
```

**Шаг 2 — Параллельный сбор данных (5 коллекторов per competitor)**
```python
# pipeline_runner.py:164-171
results = await asyncio.gather(
    self._collect_financials(comp),    # bo.nalog.gov.ru
    self._collect_seo(url, name),      # SeoAuditor (httpx + BS4)
    self._collect_social(name),        # SocialScanner
    self._collect_website(comp),       # website crawl + feature extract
    self._collect_reviews(name),       # Yandex + ProDoctorov reviews
)
```

**Шаг 3 — Врачи-лидеры (если нашлись doctor_names)**
```python
# pipeline_runner.py:199-206
if doctor_names:
    full.doctors = await self._collect_doctors(doctor_names, full.name)
    # → DoctorExtractor: social profiles + articles + influence_score
```

**Шаг 4 — Матрица сравнения**
```python
# ci_marketing_analysis.py:802-805
builder = ComparisonMatrixBuilder()
matrix = builder.build(url, client_features, collected)
# → ComparisonMatrix: client + competitors (20+ параметров)
```

**Шаг 5 — Генерация ответа**
```python
# ci_marketing_analysis.py:808-813
chat_summary = self._chat_summary_from_matrix(matrix)  # Структурный текст
feature_matrix = self._feature_matrix_legacy(matrix)
pricing = self._pricing_legacy(matrix)
positioning = self._positioning_legacy(matrix)
# ⚠️ steal_worthy_tactics = []  ВСЕГДА ПУСТОЙ!
# ⚠️ top_recommendation = базовая строка
```

### Ключевые сервисы нового pipeline:

| Сервис | Файл | Размер | Назначение |
|--------|------|--------|------------|
| PipelineRunner | `pipeline_runner.py` | 31KB | Оркестрация сбора данных |
| ComparisonMatrixBuilder | `comparison_matrix.py` | 6.5KB | Построение матрицы для LLM |
| DialogueManager | `dialogue_manager.py` | 23KB | LLM-диалог с клиентом |
| SeoAuditor | `seo_auditor.py` | 9KB | Технический SEO аудит |
| SocialScanner | `social_scanner.py` | 43KB | Поиск соцсетей |
| ReviewCollector | `review_collector.py` | 17.5KB | Сбор отзывов |
| DoctorExtractor | `doctor_extractor.py` | 17KB | Извлечение врачей + influence |
| ArticleScanner | `article_scanner.py` | 23KB | Поиск научных публикаций |

### Старый rule-based код (всё ещё в ci_marketing_analysis.py, но НЕ вызывается):

```python
# Эти классы ЕСТЬ в файле, но analyze() их НЕ использует:
self.scraper = CompetitorPageScraper()    # строки 113-232
self.feature_mapper = FeatureMapper()      # строки 237-376
self.pricing_analyzer = PricingAnalyzer()  # строки 378-498
self.positioning_mapper = PositioningMapper()  # строки 500-622
self.swot_engine = SwotEngine()            # строки 624-710
self.tactic_extractor = TacticExtractor()  # строки 712-756
```

**Весь старый код (~650 строк) — мёртвый груз. Новый `analyze()` использует только `PipelineRunner` + `ComparisonMatrixBuilder`.**

### Что возвращает пресс-релизный pipeline:

```json
{
  "chat_summary": "## Анализ конкурентов\nПроанализировано: **3 конкурентов**\n...",
  "feature_matrix": {
    "competitors": [{"name": "...", "features": ["booking", "chat"]}]
  },
  "pricing_comparison": {
    "competitors": [{"name": "...", "has_pricing": true, "revenue": 50000000}]
  },
  "positioning_map": {
    "competitors": [{"name": "...", "positioning": "премиум-стоматология..."}]
  },
  "steal_worthy_tactics": [],  // ⚠️ ВСЕГДА ПУСТОЙ
  "top_recommendation": "Соберите данные о конкурентах...",  // ⚠️ ЗАГЛУШКА
  "duration_seconds": 31.5
}
```

### Ключевые проблемы Pipeline 1:

1. **steal_worthy_tactics всегда пустой** — TacticExtractor не вызывается
2. **top_recommendation — заглушка** — всегда возвращает "Соберите данные о конкурентах для получения рекомендаций."
3. **SWOT не считается** — SwotEngine существует, но не вызывается из analyze()
4. **chat_summary — структурный, не LLM** — `_chat_summary_from_matrix()` просто форматирует данные в markdown, без анализа
5. **Старый rule-based код не удалён** — ~650 строк мёртвого кода в том же файле


---

## 5. Pipeline 2: Полный CI (run_seo_audit)

### Полный путь вызова

```
Пользователь (в чате Hermes)
  → Hermes решает использовать tool "run_seo_audit"
    → POST /api/seo/audit (запуск async задачи)
      → asyncio.create_task() → _run_audit_background()
        → CIOrchestrator.execute_ci_analysis()
          → Phase 1: ci-scout (поиск конкурентов)
          → Phase 2: ci-auditor (аудит сайтов)
          → Phase 3: ci-deep-analyzer (глубокий анализ)
          → Phase 4: ci-reputation (репутация)
          → Phase 5: 9 агентов параллельно
          → Phase 6-9: factchecker, strategist, prioritizer
          → Phase 10-16: TW agent'ы + offer generator
    ← GET /api/seo/audit/{task_id} (polling каждые 2 сек)
      → _compact_audit_result() сжимает ~18K → ~2K токенов
  → Hermes показывает 3 WOW-цифры + инсайты
```

### Tier definition (ci_orchestrator.py:46-49):

```python
self.tiers = {
    "quick": {"phases": range(1, 5), "time": "15 min", "cost": "low"},
    "deep":  {"phases": range(1, 10), "time": "45 min", "cost": "medium"},
    "full":  {"phases": range(1, 17), "time": "90 min", "cost": "high"}
}
```

### Agent mapping (ci_orchestrator.py:53-71):

```python
self.phase_agents = {
    1: "ci-scout",                    # Поиск конкурентов
    2: "ci-auditor",                  # Аудит сайтов (28 проверок)
    3: "ci-deep-analyzer",            # Глубокий анализ
    4: "ci-reputation",               # Репутационный анализ
    5: [                               # ПАРАЛЛЕЛЬНАЯ ФАЗА (9 агентов):
        "ci-finance",                  # Финансовая отчётность (bo.nalog.gov.ru)
        "ci-vacancies",                # Анализ вакансий (hh.ru)
        "ci-tech",                     # Технологический стек
        "ci-site-crawler",             # Краулер сайтов
        "ci-content",                  # Контент-анализ
        "ci-pricing",                  # Анализ цен
        "ci-ecosystem",                # Экосистема (соцсети, сервисы)
        "ci-backlink",                 # Бэклинки
        "ci-rank-tracker"             # Позиции в поиске
    ],
    6: "ci-factchecker",              # Проверка собранных фактов
    7: "ci-strategist",               # Стратегический анализ (часть 1)
    8: "ci-strategist",               # Стратегический анализ (часть 2)
    9: "ci-prioritizer",              # Приоритизация действий
    10: "ci-marketing-strategy",       # Маркетинговая стратегия
    11: "tw-competitor-scout",         # ❌ STUB — TW: поиск рекламы
    12: "tw-creative-collector",       # ❌ STUB — TW: сбор креативов
    13: "tw-creative-analyzer",        # ❌ STUB — TW: анализ креативов
    14: "tw-pattern-finder",           # ❌ STUB — TW: поиск паттернов
    15: "tw-traffic-analyzer",         # ❌ STUB — TW: анализ трафика
    16: "ci-offer-generator"           # Генерация КП
}
```

### Как происходит делегирование агенту:

```python
# ci_orchestrator.py:321-385 — _execute_single_phase()
agent = self._get_agent(agent_name)   # Импорт + создание инстанса

if agent is None:                      # TW агенты возвращают None
    return {"status": "stub", ...}     # ЗАГЛУШКА

task = Task(...)
result = await agent.execute_task(task)  # Реальное выполнение
```

### _get_agent() — что реально импортируется:

```python
# ci_orchestrator.py:76-150
# 17 агентов импортируются из aim.subagents.competitive_intel.agents.*
# 5 TW агентов (строки 141-143):
else:
    return None  # ← TW agent'ы не существуют в коде
```

### Ключевая проблема: _delegate_to_agent()

```python
# ci_orchestrator.py:861-890 — ВТОРОЙ метод делегирования
async def _delegate_to_agent(self, agent_id: str, task: Task) -> Dict:
    # Публикует событие в EventBus и...
    await self.event_bus.publish(Event(...))
    
    # TODO: Ждать результат от агента через Event Bus
    # Пока возвращаем заглушку
    return {"agent_id": agent_id, "status": "delegated", "task_id": task.id}
```

**Этот метод вызывается из execute_task() → _execute_single_agent() — второй путь выполнения, который НИКОГДА не ждёт реальный ответ от агента.**

### Что происходит при SEO аудите на практике:

1. **seo.py запускает `tier: "quick"`** (только фазы 1-4)
2. Phase 1 (scout) — находит конкурентов ✅
3. Phase 2 (auditor) — аудит сайтов ✅
4. Phase 3 (deep-analyzer) — глубокий анализ ⚠️
5. Phase 4 (reputation) — репутация ⚠️
6. **Phases 5-16 НЕ выполняются при quick**

**НО!** `_compact_audit_result()` пытается читать phase_7 (strategist) для WOW-цифр:

```python
# run_seo_audit.py:56-58
phase7 = findings.get("phase_7", {})  # ← Не существует при quick!
strat_result = phase7.get("result", {}) if isinstance(phase7, dict) else {}
estimates = strat_result.get("estimates", {}) or {}
# → estimates ВСЕГДА ПУСТЫЕ при quick tier!
```

### ЧТО НА САМОМ ДЕЛЕ ВОЗВРАЩАЕТ SEO АУДИТ:

```json
{
  "wow": {
    "patients_per_month": null,      // ← ПУСТО (phase_7 не выполнялась)
    "time_to_result_weeks": null,    // ← ПУСТО
    "cost_per_patient_rub": null     // ← ПУСТО
  },
  "market": {
    "competitive_intensity": "unknown",  // ← ПУСТО
    "digital_maturity": "unknown",
    "niche_size": "unknown"
  },
  "competitors": [],     // ← Может быть пустым
  "insights": [],        // ← ПУСТО
  "opportunities": [],   // ← ПУСТО
  "actions": [],         // ← ПУСТО
  "meta": {
    "tier": "quick",
    "phases": 4,
    "time_seconds": 15,
    "quality_score": {"score": 0, "confidence": "low"}
  }
}
```

### ДВА пути выполнения в CIOrchestrator:

```python
# Путь 1 (используется из seo.py):
async def execute_ci_analysis(task_data)  # строка 152
  → _execute_single_phase()               # строка 321
    → _get_agent() → agent.execute_task()  # РЕАЛЬНОЕ выполнение

# Путь 2 (execute_task - стандартный интерфейс Agent):
async def execute_task(task)              # строка 623
  → _execute_phases(tier, payload)         # строка 731
    → _execute_single_agent()              # строка 833
      → _delegate_to_agent()               # строка 861
        → return {"status": "delegated"}   # STUB! Не ждёт ответа
```

Эти два пути НЕ СОВМЕСТИМЫ. Путь 1 использует `_get_agent()` и реально выполняет агентов. Путь 2 использует `_delegate_to_agent()` и возвращает заглушку.


---

## 6. Инвентаризация агентов: что реально работает

| # | Агент | Файл | Строк | Реальный? | Что делает |
|---|-------|------|-------|-----------|------------|
| 1 | ci_scout | `ci_scout.py` | 751 | ✅ Да | Поиск конкурентов (DaData + Google Maps) |
| 2 | ci_auditor | `ci_auditor.py` | 1062 | ✅ Да | 28 проверок сайта (technical, content, UX, marketing) |
| 3 | ci_deep_analyzer | `ci_deep_analyzer.py` | 2411 | ⚠️ Файл огромный | Глубокий анализ, надо проверить логику |
| 4 | ci_reputation | `ci_reputation.py` | 638 | ⚠️ Проверить | Репутационный анализ (отзывы, рейтинги) |
| 5 | ci_finance | `ci_finance.py` | 475 | ⚠️ Проверить | Финансы через bo.nalog.gov.ru |
| 6 | ci_vacancies | `ci_vacancies.py` | 522 | ⚠️ Проверить | Вакансии через hh.ru |
| 7 | ci_tech_real | `ci_tech_real.py` | 1035 | ⚠️ Проверить | Технологический стек |
| 8 | ci_site_crawler | `ci_site_crawler.py` | 600 | ⚠️ Проверить | Краулер сайтов |
| 9 | ci_content_improved | `ci_content_improved.py` | 710 | ⚠️ Проверить | Контент-анализ |
| 10 | ci_pricing | `ci_pricing.py` | 589 | ⚠️ Проверить | Анализ цен |
| 11 | ci_ecosystem | `ci_ecosystem.py` | 715 | ⚠️ Проверить | Экосистема (соцсети, сервисы) |
| 12 | ci_backlink | `ci_backlink.py` | 628 | ⚠️ Проверить | Бэклинки |
| 13 | ci_rank_tracker | `ci_rank_tracker.py` | 591 | ⚠️ Проверить | Позиции в поиске |
| 14 | ci_factchecker | `ci_factchecker.py` | 657 | ⚠️ Проверить | Проверка фактов |
| 15 | ci_strategist | `ci_strategist.py` | 776 | ⚠️ Проверить | Стратегический анализ |
| 16 | ci_prioritizer | `ci_prioritizer.py` | 480 | ⚠️ Проверить | Приоритизация |
| 17 | ci_marketing_strategy | `ci_marketing_strategy.py` | 515 | ⚠️ Проверить | Маркетинговая стратегия |
| 18 | ci_offer_generator | `ci_offer_generator.py` | 520 | ⚠️ Проверить | Генерация КП |
| 19 | tw-competitor-scout | — | — | ❌ STUB | TW: поиск рекламы конкурентов |
| 20 | tw-creative-collector | — | — | ❌ STUB | TW: сбор креативов |
| 21 | tw-creative-analyzer | — | — | ❌ STUB | TW: анализ креативов |
| 22 | tw-pattern-finder | — | — | ❌ STUB | TW: поиск паттернов |
| 23 | tw-traffic-analyzer | — | — | ❌ STUB | TW: анализ трафика |

**Итого:**
- ✅ Точно работает: 2 из 23 (scout, auditor)
- ⚠️ Файлы есть, надо проверить логику: 16 из 23
- ❌ Stubs (файлов нет): 5 из 23

**Примечание:** агенты ci_qa_validator, ci_url_validator, business_report есть в файлах, но НЕ зарегистрированы в phase_agents словаре оркестратора.

---

## 7. Модели данных

### Основные модели (ci/models.py, 192 строки):

```python
SeoAuditResult        # SEO аудит: score, issues, title, meta, h1/h2/h3, ssl, og_tags...
SocialProfile         # Соцсеть: platform, handle, subscribers, posts_last_month, avg_likes...
SocialScanResult      # Скан всех соцсетей: instagram, telegram, vk, tiktok
ArticleInfo           # Научная публикация: title, authors, journal, year, doi, citations
ArticleSearchResult   # Результат поиска публикаций
DoctorSocialResult    # Соцсети одного врача
DoctorInfo            # Полный профиль врача: name, specialty, social, articles, influence_score
ServicePrice          # Цена услуги: name, price_min, price_max, category
PricingData           # Все цены: services[], categories_found[], total_services
CompetitorFull        # ВСЁ по одному конкуренту: name, url, inn, financials, seo, social, doctors...
ComparisonMatrix      # Компактная матрица для LLM (~5000 токенов): client + competitors[]
PipelineProgress      # Прогресс-событие: stage, message, competitor_name, details
```

### Модели пресс-релизного анализатора (ci_marketing_analysis.py):

```python
ScrapedPageData       # Результат скрапинга: title, h1, meta, ctas, pricing_indicators...
SwotQuadrant          # SWOT: strengths[], weaknesses[], opportunities[], threats[]
Tactic                # Тактика: source_competitor, tactic_description, why_it_works...
CiAnalysisResult      # Финальный результат: chat_summary, feature_matrix, pricing_comparison...
```

---

## 8. Точки входа (API)

### 8.1 /api/competitors/find — поиск конкурентов
- **Метод:** POST
- **Вход:** `{url, count, named_competitors?}`
- **Выход:** `{competitors: CompetitorJson[], is_megalopolis}`
- **Реализация:** `CompetitorMatcher.find_competitors()` → DaData + Google Maps

### 8.2 /api/competitors/analyze — пресс-релиз (без SSE)
- **Метод:** POST
- **Вход:** `{url, specialization, city, services, competitors[], client_revenue?, client_rating?}`
- **Выход:** `CiAnalysisResult` (JSON)
- **Реализация:** `CiMarketingAnalyzer.analyze()`

### 8.3 /api/competitors/analyze/stream — пресс-релиз (SSE streaming)
- **Метод:** POST
- **Вход:** тот же что /analyze
- **Выход:** SSE stream: `{type: "progress"|"result"|"error"}`
- **Используется:** Hermes `run_ci_analysis` tool

### 8.4 /api/seo/audit — полный CI (async)
- **Метод:** POST
- **Вход:** `{url, competitors?, niche?, tier?}`
- **Выход:** `{task_id, status: "pending", status_url}`
- **Реализация:** `asyncio.create_task(_run_audit_background())`
- **Проблема:** In-memory task store (`_tasks: dict`), теряется при перезапуске

### 8.5 /api/seo/audit/{task_id} — polling
- **Метод:** GET
- **Вход:** task_id
- **Выход:** `{task_id, status, progress, result?, error?}`

---

## 9. Полный список проблем (ранжировано по критичности)

### 🔴 CRITICAL — система не работает

| # | Проблема | Где | Описание |
|---|----------|-----|----------|
| C1 | **TW агенты не реализованы** | `ci_orchestrator.py:141-143` | 5 фаз (11-15) — stubs. `_get_agent()` возвращает None |
| C2 | **Два несовместимых пути выполнения** | `ci_orchestrator.py` | `execute_ci_analysis()` vs `execute_task()` — один работает, другой stubs |
| C3 | **SEO аудит всегда возвращает пустые WOW-цифры** | `run_seo_audit.py:56-58` | `_compact_audit_result` читает phase_7, которая не выполняется при quick |
| C4 | **steal_worthy_tactics всегда пустой** | `ci_marketing_analysis.py:822` | TacticExtractor не вызывается, всегда `[]` |
| C5 | **top_recommendation — заглушка** | `ci_marketing_analysis.py:954-956` | Всегда "Соберите данные о конкурентах..." |

### 🟡 HIGH — система работает неполноценно

| # | Проблема | Где | Описание |
|---|----------|-----|----------|
| H1 | **Дублирование пайплайнов** | Вся система | CiMarketingAnalyzer + CIOrchestrator делают похожие вещи по-разному |
| H2 | **Старый код не удалён** | `ci_marketing_analysis.py` | 650 строк rule-based кода (CompetitorPageScraper, SwotEngine, TacticExtractor) — мёртвый груз |
| H3 | **SWOT не считается** | `ci_marketing_analysis.py:624-710` | SwotEngine существует, но не вызывается |
| H4 | **chat_summary без LLM** | `ci_marketing_analysis.py:836-924` | Структурная сборка markdown, без реального анализа |
| H5 | **In-memory task store** | `seo.py:33` | `_tasks` теряется при перезапуске сервера |
| H6 | **Нет реального EventBus-делегирования** | `ci_orchestrator.py:861-890` | `_delegate_to_agent()` публикует событие и сразу возвращает stub |

### 🟢 LOW — технический долг

| # | Проблема | Где | Описание |
|---|----------|-----|----------|
| L1 | **ci_deep_analyzer — 2411 строк** | `ci_deep_analyzer.py` | Самый большой файл, вероятно нуждается в рефакторинге |
| L2 | **3 агента не зарегистрированы** | `ci_orchestrator.py:53-71` | ci_qa_validator, ci_url_validator, business_report есть но не используются |
| L3 | **Мёртвый код `_execute_phase_stub()`** | `ci_orchestrator.py:604-621` | Помечен TODO, нигде не вызывается |
| L4 | **Разные модели данных** | `models.py` vs `ci_marketing_analysis.py` | Два набора датаклассов для одного и того же |

---

## 10. Ключевые файлы для понимания системы

| Приоритет | Файл | Строк | Зачем читать |
|-----------|------|-------|--------------|
| 1 | `ci_orchestrator.py` | 939 | Главный оркестратор — 16 фаз, все агенты, два пути выполнения |
| 2 | `ci_marketing_analysis.py` | 964 | Пресс-релизный анализатор — старый + новый код |
| 3 | `pipeline_runner.py` | ~800 | Новый pipeline — поиск + сбор данных |
| 4 | `ci_auditor.py` | 1062 | Лучший пример РАБОТАЮЩЕГО агента |
| 5 | `competitors.py` | 408 | API endpoints для поиска и анализа |
| 6 | `seo.py` | 179 | API endpoint для полного CI |
| 7 | `run_ci_analysis.py` | 267 | Hermes tool: пресс-релиз |
| 8 | `run_seo_audit.py` | 253 | Hermes tool: SEO аудит |
| 9 | `models.py` | 192 | Все датаклассы |
| 10 | `comparison_matrix.py` | 169 | Матрица сравнения для LLM |
| 11 | `dialogue_manager.py` | ~600 | LLM-диалог с клиентом |
| 12 | `doctor_extractor.py` | 414 | Извлечение врачей + influence scoring |

