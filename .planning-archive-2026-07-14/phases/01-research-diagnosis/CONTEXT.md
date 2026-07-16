# Phase 1: Research & Diagnosis — Context

**Created:** 2026-06-22 by orchestrator (pre-planning investigation)
**Source:** Direct investigation of aim-hermes container via `ssh aim` during project initialization

---

## Что уже известно (предварительное исследование)

### Три версии SOUL.md — эволюция

| Версия | Где лежит | Строк | Фаз | Роль LLM | Результат |
|--------|-----------|-------|-----|----------|-----------|
| v3 (ранняя) | `skills/aim/SOUL.backup.md` локально | 327 | 14 | Интерпретатор | Короткие отчёты — LLM не обогащает |
| v3 (расширенная) | `/opt/hermes-data/SOUL.md` на сервере | 344 | 16 | Интерпретатор | НЕ ИСПОЛЬЗУЕТСЯ (HERMES_HOME указывает на /opt/data) |
| v4 (текущая) | `/opt/data/SOUL.md` в контейнере | 668 | 0 (каталог 40+ tools) | Оркестратор "свободный художник" | ~30% покрытия — LLM пропускает инструменты |

### Какая версия РЕАЛЬНО работает

- `HERMES_HOME=/opt/data` (внутри контейнера aim-hermes)
- `copy_soul.sh` при старте копирует `skills/aim/SOUL.md` → `/opt/data/SOUL.md` (volume `aim_hermes_data`)
- В контейнере сейчас **v4, 668 строк, 38 KB**
- Файл `/opt/hermes-data/SOUL.md` на хосте (v3, 344 строки) — мёртвый груз, не используется

### Рассинхрон фаз (корень хаоса)

| Источник | Фаз | Описание |
|----------|-----|----------|
| `phases.py` в коде (контейнер) | **13** | 0–12: PERPLEXITY → COMPETITORS → TECH_AUDIT → SOCIAL → CONTENT → KEY_PERSONS → SMI → FORUM_PAINS → FINANCE → CONTENT_PLAN → HTML_BUILD → QC → PRESENTATION |
| `aim-scout/SKILL.md` локально | **14** | 0–13 (та же последовательность, но нумерация смещена) |
| Серверная v3 SOUL.md | **16** | 0, 0.5, 0.75, 0.8, 1, 2, 3, 3.2, 3.5, 3.6, 4, 5, 6, 7, 8, 9, 10 — с фазами Instagram/Ads/Telegram, которых нет в коде |
| `engine.py:_TOOL_HANDLERS` | — | **19 инструментов** (подмножество из 40+ зарегистрированных для LLM) |

### Реальный код пайплайна (`/opt/hermes/app/pipeline/phases.py` в контейнере)

```
Phase 0:  PERPLEXITY      [perplexity_search]
Phase 0:  PRE-FLIGHT      []
Phase 1:  COMPETITORS     [find_competitors, run_ci_analysis]
Phase 2:  TECH AUDIT      [run_pagespeed, run_seo_audit]
Phase 3:  SOCIAL          [run_review_platforms]
Phase 4:  CONTENT         [run_content_analysis]
Phase 5:  KEY PERSONS     [run_hh_analysis, run_doctor_dossiers]
Phase 6:  SMI             [run_smi_mentions]
Phase 7:  FORUM PAINS     [web_search]
Phase 8:  FINANCE         [find_company_financials]
Phase 9:  CONTENT PLAN    [run_content_gaps]
Phase 10: HTML BUILD      [generate_html_report]
Phase 11: QC CRITIQUE     []
Phase 12: PRESENTATION    [publish_scout_report]
```

### Инструменты — разрыв между LLM-registry и pipeline-handlers

**`register_all_tools()` в `app/tools/__init__.py`** регистрирует для LLM **40+ инструментов**.

**`engine.py:_TOOL_HANDLERS`** (реестр вызываемых хендлеров) содержит **только 19**:

```
web_search, run_pagespeed, run_seo_audit, find_competitors,
run_review_platforms, run_content_analysis, run_hh_analysis,
run_doctor_dossiers, run_ci_analysis, run_smi_mentions,
run_content_gaps, find_company_financials, generate_html_report,
publish_scout_report, perplexity_search, perplexity_deep_analyze,
firecrawl_extract, firecrawl_batch_scrape, firecrawl_agent,
crawlee_scrape, crawlee_search, scrapy_crawl
```

**PipelineEngine не может вызвать инструменты, которых нет в `_TOOL_HANDLERS`:**

| Инструмент | Зарегистрирован для LLM | В _TOOL_HANDLERS | В v3 SOUL | В aim-scout SKILL |
|------------|:---:|:---:|:---:|:---:|
| `run_instagram_content` | ✅ | ❌ | ❌ | ✅ Фаза 5 |
| `find_doctor_handles` | ✅ | ❌ | ❌ | ✅ Фаза 5 |
| `run_ads_intelligence` | ✅ | ❌ | ✅ Фаза 0.8 | ❌ |
| `run_ads_report` | ✅ | ❌ | ❌ | ❌ |
| `run_tech_seo_audit` | ✅ | ❌ | ❌ | ✅ Фаза 2 |
| `run_lighthouse` | ✅ | ❌ | ❌ | ❌ |
| `run_prescan` | ✅ | ❌ | ❌ | ❌ |
| `quick_overview` | ✅ | ❌ | ❌ | ❌ |
| `geo_optimizer_tools` | ✅ | ❌ | ❌ | ❌ |
| `present_competitors` | ✅ | ❌ | ❌ | ❌ |
| `finalize_research` | ✅ | ❌ | ❌ | ❌ |
| `run_validation_check` | ✅ | ❌ | ❌ | ❌ |
| `post_report` | ✅ | ❌ | ❌ | ❌ |
| `orchestrate` | ✅ | ❌ | ❌ | ❌ |
| `run_aim_scout` / `run_full_scout` / `run_background_pipeline` | ✅ | ❌ | ❌ | ❌ |

### Список tools-файлов в контейнере

```
__init__.py, _ddg.py, _search_fallback.py, bitrix_scraper.py,
collect_contact.py, crawlee_web.py, deep_research_merge.py,
engine.py, escalate_to_manager.py, external_api.py,
finalize_research.py, find_company_financials.py, find_competitors.py,
firecrawl_key_bank.py, firecrawl_web.py, generate_html_report.py,
geo_optimizer_tools.py, get_lead_pipeline.py, orchestrate.py,
perplexity_tools.py, post_report.py, present_competitors.py,
publish_scout_report.py, qualify_lead.py, quality_gate.py,
quick_overview.py, read_report_reference.py, run_ads_intelligence.py,
run_ads_report.py, run_aim_scout.py, run_background_pipeline.py,
run_ci_analysis.py, run_content_analysis.py, run_content_gaps.py,
run_doctor_dossiers.py, run_full_scout.py, run_hh_analysis.py,
run_instagram_content.py, run_lighthouse.py, run_pagespeed.py,
run_prescan.py, run_review_platforms.py, run_seo_audit.py,
run_smi_mentions.py, run_tech_seo_audit.py, run_validation_check.py,
run_web_search.py, scrapy_runner.py, send_telegram_file.py,
service_categorizer.py, session_archive.py, shell_exec.py,
show_all_leads.py, show_project_status.py, telegram_tools.py,
test_deep_research_merge.py, test_presale_pipeline.py,
test_service_categorizer.py, update_knowledge.py, web_scraper.py
```

### Референс `ИПХиК (2).html` — целевой идеал

10 секций, 965 строк, 78 KB:

1. About (ОКВЭД, лицензии, динамика выручки за 3 года)
2. Market (таблица 8 конкурентов: выручка, тренд, хирурги, Instagram + gap-блоки)
3. Experts (ТОП-5 врачей: ФИО, регалии, подписчики, avg лайки/просмотры, стиль)
4. Content Analysis (по каждому врачу: стиль, темы, пробелы, потенциал + Топ-5 страхов)
5. Media (Forbes, RBC, Vademecum, Kommersant — с конкретными ссылками и датами)
6. Competitors (детальные карточки 8 клиник: выручка, год, хирурги, Instagram, специфика)
7. Whitefields (матрица: клиент vs 3-5 конкурентов по полям)
8. Presence (тех. аудит: что хорошо, что исправить, приоритеты)
9. Strategy (5 направлений: контент, Telegram, GEO, репутация, кросс-промо)
10. Offer («Что AIM может сделать для клиники»)

### Корневые причины 30% покрытия (гипотезы для исследования)

1. **Instagram полностью отсутствует** — критично для косметологии/пластики (40% контента референса)
2. **Нет фаз Strategy и Offer** — отчёт заканчивается на данных, без рекомендаций
3. **Динамика выручки** — только текущий год, не 3 года
4. **СМИ-ссылки** — счётчики вместо конкретных публикаций
5. **Интерпретация недостаточно глубокая** — узкие промпты, «дамп метрик» вместо нарратива
6. **HTML BUILD не связывает секции** — страхи пациентов (04) не ведут к стратегии (09)
7. **SOUL.md даёт слишком много свободы** — LLM решает «не обязательно» и пропускает

---

## Что нужно исследовать в Phase 1

### RES-01: Корневая причина пропуска инструментов

Пользователь сказал: «Не знаю — надо исследовать» почему LLM v4 пропускает. Нужно:

1. **Анализ логов 3-5 последних прогонов** Hermes на сервере (`/opt/data/sessions-archive/`)
   - Какие инструменты LLM вызывала?
   - Какие пропустила?
   - В каких случаях обрезала вывод?
   - Timestamps, tool names, sequence

2. **Проверка 4 гипотез:**
   - **Гипотеза A (промпт-проблема):** SOUL.md/SKILL.md дают слишком много свободы → LLM решает «не обязательно»
   - **Гипотеза B (модель не вытягивает):** DeepSeek V4 Pro не справляется с большим контекстом → таймаут, обрезка, потеря фокуса
   - **Гипотеза C (pipeline ограничивает):** PipelineEngine жёстко ограничивает фазы → LLM не может вызвать инструмент вне очереди
   - **Гипотеза D (комбинация):** несколько причин одновременно

3. **Доказательства:** конкретные логи, метрики, цитаты из SOUL.md/SKILL.md

### RES-02: Измерить tool coverage

Сколько из 40+ инструментов LLM вызывает за типичный прогон пресейла?

- Взять 3-5 последних сессий из `/opt/data/sessions-archive/`
- Для каждой: подсчитать уникальные tool calls
- Усреднить
- Получить базовую метрику: «X из 40+ tools» (сейчас гипотеза ~14, нужно подтвердить)

### RES-03: Измерить section coverage

Сколько из 10 секций референса фактически появляются в отчётах v4?

- Взять 3-5 последних HTML-отчётов
- Для каждого: отметить какие из 10 секций референса присутствуют (хоть в каком-то виде)
- Усреднить
- Получить базовую метрику: «Y из 10 sections» (сейчас гипотеза ~3, нужно подтвердить)

### RES-04: Анализ логов сессий

3-5 сессий из `/opt/data/sessions-archive/` — детальный разбор:

- Какие фазы PipelineEngine выполнил?
- Где LLM обрезала вывод?
- Какие инструменты вернули NO_DATA?
- Какие инструменты вернули ошибку?
- Где LLM решила «не обязательно» и пропустила?
- Конкретные timestamps и tool names

### RES-05: Ручной тест run_instagram_content

Инструмент существует, зарегистрирован для LLM, но не подключён к pipeline.

- Вызвать `run_instagram_content` вручную на 1 клинике (например, iphk.ru)
- Проверить: работает ли? Какие данные возвращает?
- Нужен ли отдельный handler в `engine.py:_TOOL_HANDLERS`?
- Какие данные нужны для секций 03 (Experts) и 04 (Content Analysis) референса?

---

## Ограничения Phase 1

- **Только исследование** — не править код, SOUL, SKILL в этой фазе
- **Доступ к серверу:** `ssh aim`, контейнер `aim-hermes`
- **Логи:** `/opt/data/sessions-archive/` (session_hash директории)
- **Контейнер live:** нельзя ломать работающий пресейл-поток
- **Бюджет:** 1-2 недели (Research Phase)

## Deliverables Phase 1

1. **RESEARCH.md** в `.planning/phases/01-research-diagnosis/` — полный отчёт с:
   - Подтверждённая корневая причина (с доказательствами)
   - Baseline tool coverage (X/40+)
   - Baseline section coverage (Y/10)
   - Логи 3-5 сессий с конкретными skip-точками
   - Результат ручного теста `run_instagram_content`
2. **Рекомендации для Phase 2** — на что обращать внимание при построении 3-проходного оркестратора

---

## Архитектурный контекст

### Deploy-инфраструктура

- **Сервер:** Польша, `ssh aim`, Docker-контейнер `aim-hermes`
- **HERMES_HOME:** `/opt/data` (volume `aim_hermes_data`)
- **SOUL.md в контейнере:** `/opt/data/SOUL.md` (сейчас v4, 668 строк)
- **Skills:** `/opt/hermes/skills/` (ro-монтирование из `/opt/aim/AIM/hermes/skills`)
- **Деплой:** `docker cp` + перезапуск gateway (нельзя пересобирать образ)
- **Контейнер live:** `docker ps` → `aim-hermes Up 27 minutes (healthy)`

### Модель

- DeepSeek V4 Pro (`LLM_MODEL=ds/deepseek-v4-pro`)
- Стримы рвутся на ~120с — long-running фазы нужно бить
- `max_tokens: 16000`, `max_iterations: 25`

### Связанные файлы (для планов Phase 1)

- `/opt/hermes/app/pipeline/engine.py` — PipelineEngine, _TOOL_HANDLERS (19 инструментов)
- `/opt/hermes/app/pipeline/phases.py` — 13 фаз
- `/opt/hermes/app/tools/__init__.py` — register_all_tools (40+ инструментов)
- `/opt/hermes/app/tools/run_instagram_content.py` — Instagram-инструмент (тестируем в RES-05)
- `/opt/data/SOUL.md` — текущая v4 (668 строк)
- `/opt/data/sessions-archive/` — логи прогонов (для RES-02, RES-03, RES-04)

---
*Context created: 2026-06-22*
