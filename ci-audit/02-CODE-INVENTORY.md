# CI System — Инвентаризация всех файлов

Каждый файл оценен по статусу:
- ✅ **PRODUCTION** — реально работает, используется в pipeline
- ⚠️ **NEEDS REVIEW** — файл существует, зарегистрирован, но логика не проверена
- ❌ **STUB** — заглушка, файла нет или возвращает пустые данные
- 🗑️ **DEAD CODE** — существует, но не вызывается

## Оркестраторы

| Файл | Строк | Статус | Описание |
|------|-------|--------|----------|
| `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` | 939 | ⚠️ | Главный оркестратор. 16 фаз, 23 агента, 3 tier'а. Два пути выполнения. |

## API Endpoints

| Файл | Строк | Статус | Описание |
|------|-------|--------|----------|
| `AIM/src/aim/api/competitors.py` | 408 | ✅ | `/find`, `/save`, `/analyze`, `/analyze/stream` |
| `AIM/src/aim/api/seo.py` | 179 | ⚠️ | `/audit` + polling. In-memory task store. |

## Hermes Tools

| Файл | Строк | Статус | Описание |
|------|-------|--------|----------|
| `AIM/hermes/app/tools/run_ci_analysis.py` | 267 | ✅ | Вызывает `/api/competitors/analyze/stream`, ретранслирует SSE |
| `AIM/hermes/app/tools/run_seo_audit.py` | 253 | ⚠️ | Вызывает `/api/seo/audit`, компактит результат. Проблема: читает phase_7 при quick |

## Сервисы (ci/ папка)

| Файл | Строк | Статус | Описание |
|------|-------|--------|----------|
| `AIM/src/aim/services/ci/pipeline_runner.py` | ~800 | ✅ | Новый оркестратор сбора данных. Parallel scraping + collectors |
| `AIM/src/aim/services/ci/comparison_matrix.py` | 169 | ✅ | Построение ComparisonMatrix для LLM |
| `AIM/src/aim/services/ci/dialogue_manager.py` | ~600 | ✅ | LLM-диалог с клиентом (system prompt + fallback) |
| `AIM/src/aim/services/ci/models.py` | 192 | ✅ | Датаклассы: CompetitorFull, SeoAuditResult, DoctorInfo, etc. |
| `AIM/src/aim/services/ci/seo_auditor.py` | ~250 | ✅ | SEO аудит: httpx + BeautifulSoup, 10+ проверок |
| `AIM/src/aim/services/ci/social_scanner.py` | ~1200 | ✅ | Поиск соцсетей: Instagram, Telegram, VK, TikTok |
| `AIM/src/aim/services/ci/review_collector.py` | ~500 | ✅ | Сбор отзывов: Yandex Maps + ProDoctorov |
| `AIM/src/aim/services/ci/doctor_extractor.py` | 414 | ✅ | Извлечение врачей из HTML + influence_score |
| `AIM/src/aim/services/ci/article_scanner.py` | ~650 | ✅ | Поиск научных публикаций (elibrary, cyberleninka, pubmed) |
| `AIM/src/aim/services/ci/apify_social_finder.py` | ~550 | ⚠️ | Apify-клиент для поиска соцсетей |
| `AIM/src/aim/services/ci/telegram_channel_finder.py` | ~200 | ⚠️ | Поиск Telegram-каналов |

## Агенты (competitive_intel/agents/)

### Phase 1-4 (Quick Tier) — считаются работающими

| Файл | Строк | Статус | Фаза | Описание |
|------|-------|--------|------|----------|
| `ci_scout.py` | 751 | ✅ | 1 | Поиск конкурентов: DaData + Google Maps + scoring |
| `ci_auditor.py` | 1062 | ✅ | 2 | Аудит сайтов: 28 scorer'ов, 4 dimensions |
| `ci_deep_analyzer.py` | 2411 | ⚠️ | 3 | Самый большой файл. Глубокий анализ контента |
| `ci_reputation.py` | 638 | ⚠️ | 4 | Репутационный анализ: отзывы, рейтинги |

### Phase 5 (Parallel) — 9 агентов

| Файл | Строк | Статус | Назначение |
|------|-------|--------|------------|
| `ci_finance.py` | 475 | ⚠️ | Финансы: bo.nalog.gov.ru (ФНС) |
| `ci_vacancies.py` | 522 | ⚠️ | Вакансии: hh.ru парсинг |
| `ci_tech_real.py` | 1035 | ⚠️ | Технологический стек: Wappalyzer-like |
| `ci_site_crawler.py` | 600 | ⚠️ | Краулер: обход страниц сайта |
| `ci_content_improved.py` | 710 | ⚠️ | Контент: анализ текстов, keyword density |
| `ci_pricing.py` | 589 | ⚠️ | Цены: извлечение из HTML |
| `ci_ecosystem.py` | 715 | ⚠️ | Экосистема: соцсети, сервисы, интеграции |
| `ci_backlink.py` | 628 | ⚠️ | Бэклинки: анализ ссылочного профиля |
| `ci_rank_tracker.py` | 591 | ⚠️ | Ранкинг: позиции в поиске |

### Phase 6-10 (Deep Tier)

| Файл | Строк | Статус | Фаза | Назначение |
|------|-------|--------|------|------------|
| `ci_factchecker.py` | 657 | ⚠️ | 6 | Проверка собранных фактов |
| `ci_strategist.py` | 776 | ⚠️ | 7-8 | Стратегический анализ |
| `ci_prioritizer.py` | 480 | ⚠️ | 9 | Приоритизация действий |
| `ci_marketing_strategy.py` | 515 | ⚠️ | 10 | Маркетинговая стратегия |

### Phase 11-15 (TW агенты) — STUBS

| Агент | Файл | Статус |
|------|------|--------|
| `tw-competitor-scout` | Не существует | ❌ |
| `tw-creative-collector` | Не существует | ❌ |
| `tw-creative-analyzer` | Не существует | ❌ |
| `tw-pattern-finder` | Не существует | ❌ |
| `tw-traffic-analyzer` | Не существует | ❌ |

### Phase 16

| Файл | Строк | Статус | Назначение |
|------|-------|--------|------------|
| `ci_offer_generator.py` | 520 | ⚠️ | Генерация коммерческого предложения |

### Незарегистрированные агенты (есть в папке, но не в phase_agents)

| Файл | Строк | Статус |
|------|-------|--------|
| `ci_qa_validator.py` | 582 | 🗑️ Не используется |
| `ci_url_validator.py` | 414 | 🗑️ Не используется |
| `business_report.py` | 374 | 🗑️ Не используется |

## Пресс-релизный анализатор

| Файл | Строк | Статус | Описание |
|------|-------|--------|----------|
| `AIM/src/aim/services/ci_marketing_analysis.py` | 964 | ⚠️ | 2-in-1: старый rule-based код + новый pipeline-адаптер |

### Классы внутри (статус вызова):

| Класс | Строки | Вызывается? | Статус |
|-------|--------|-------------|--------|
| `CompetitorPageScraper` | 113-232 | ❌ (ранее да) | 🗑️ Заменён PipelineRunner |
| `FeatureMapper` | 237-376 | ❌ | 🗑️ Заменён ComparisonMatrixBuilder |
| `PricingAnalyzer` | 378-498 | ❌ | 🗑️ Заменён _pricing_legacy |
| `PositioningMapper` | 500-622 | ❌ | 🗑️ Заменён _positioning_legacy |
| `SwotEngine` | 624-710 | ❌ | 🗑️ SWOT не считается |
| `TacticExtractor` | 712-756 | ❌ | 🗑️ Тактики всегда [] |
| `ReportFormatter` | — | ❌ | 🗑️ |
| `CiMarketingAnalyzer` | 758-964 | ✅ | Использует PipelineRunner + ComparisonMatrixBuilder |

## Статистика

| Категория | Количество |
|-----------|------------|
| ✅ PRODUCTION (точно работает) | 9 файлов |
| ⚠️ NEEDS REVIEW (файл есть, логика не проверена) | 16 файлов |
| ❌ STUB (файлов нет) | 5 агентов |
| 🗑️ DEAD CODE (не вызывается) | 7 классов + 3 агента |
| **Всего строк кода** | **~15,000** |
| **Строк мёртвого кода** | **~1,100** |
