---
name: aim-scout
version: 2.0.0
description: >-
  AIM Scout — глубокая разведка клиники. Primary mode: 3-pass LLM-orchestrator
  with 18-item QC checklist (ORCHESTRATOR_MODE=1). Fallback mode: PipelineEngine
  14 фаз (ORCHESTRATOR_MODE=0 или unset). v2.0: orchestrator-first per Phase 2
  design.
triggers:
  - Клиент прислал URL клиники ("https://...")
  - Команда /scout выполнена
  - Запрос "сделай разведку", "проанализируй сайт", "проверь клинику"
  - run_aim_scout tool invoked
  - Админ сказал "запусти скаут для [url]"
---

# AIM Scout — 3-pass LLM-orchestrator с QC-чеклистом

Ты запускаешь **глубокую разведку клиники** через один из двух режимов. Режим
выбирается переменной окружения `ORCHESTRATOR_MODE`:

- **Primary (по умолчанию, `ORCHESTRATOR_MODE=1`):** 3-pass LLM-оркестратор —
  LLM выбирает инструменты по ситуации, 3 прохода (Сбор → Гэп-анализ по
  QC-чеклисту → Допосбор + Сборка HTML). Реализация:
  `app/orchestrator/three_pass.py:run_three_pass`.
- **Fallback (`ORCHESTRATOR_MODE=0` или не задан):** PipelineEngine —
  Python-controlled 14-фазный пайплайн. LEGACY mode per Plan 06-02 D-06.
  Реализация: `app/pipeline/engine.py:PipelineEngine.execute`.

Оба режима разделяют `_TOOL_HANDLERS` (26 инструментов в
`app/pipeline/engine.py`) — PipelineEngine может вызвать любой из 26,
оркестратор тоже. Режим выбирает порядок и логику принятия решений, не
набор инструментов.

## РЕЖИМЫ ЗАПУСКА

### Primary: 3-pass оркестратор (ORCHESTRATOR_MODE=1)

3-pass цикл реализован в `app/orchestrator/three_pass.py` и разбит на 3
отдельных вызова `AIAgent.run_conversation()` на одной `session_id` (история
SQLite сохраняется между проходами):

1. **Pass 1 СБОР** (`pass_collect.py`) — LLM вызывает инструменты из
   каталога 26 _TOOL_HANDLERS по ситуации (не жёсткая последовательность).
   Цель: собрать сырьё для всех 18 пунктов QC_CHECKLIST v1.2.0.
2. **Niche detection mini-call** (`niche_detector.py`) — короткий LLM-вызов
   между Pass 1 и Pass 2. Классифицирует клинику как `plastic_surgery` /
   `cosmetology` / `dental` / `general_medicine` / `other` / `unknown`.
   Возвращает `{instagram_critical, niche, reason}`. Результат сохраняется
   в `state.niche` и `state.collected_data["niche_detection"]`.
3. **Pass 2 ГЭП-АНАЛИЗ** (`pass_gap_analyze.py`) — LLM сравнивает
   `collected_data` против 18-item `QC_CHECKLIST v1.2.0` (см. модуль
   `app/orchestrator/qc_checklist.py`). Каждый пункт помечается как
   `filled` / `partial` / `missing` / `not_applicable`. Результат —
   `state.gap_report` + `CoverageReport` (PASS при ≥80% покрытия).
4. **Pass 3 ДОПОСБОР + СБОРКА** (`pass_fill_assemble.py`) — LLM заполняет
   пробелы из `missing_for_pass3`, затем генерирует финальный HTML через
   `generate_html_report`. Финальный coverage пересчитывается после Pass 3.

**Soft QC gate** (QC-02): если coverage <80% после Pass 2 — Pass 3
продолжается, warning в логе. NON-blocking per ORC-04 — отчёт ВСЕГДА
генерируется, пробелы помечаются «данные недоступны».

**Instagram HARD-FAIL** (Phase 3): для critical niches
(`CRITICAL_NICHES = ("plastic_surgery", "cosmetology")`) — если пункт 5
(Instagram analysis) не заполнен, `_apply_niche_conditional_coverage`
помечает coverage как FAIL независимо от остальных пунктов.

### Fallback: PipelineEngine 14 фаз (LEGACY, ORCHESTRATOR_MODE=0)

Этот режим включается ТОЛЬКО если `ORCHESTRATOR_MODE` не задан или =0. По
умолчанию используется 3-pass оркестратор.

```python
from app.pipeline.engine import PipelineEngine

engine = PipelineEngine()
result = await engine.execute(
    session_id="auto-generated",
    client_url="https://iphk.ru",
    client_name="Институт пластической хирургии",
    mode="presale"
)
```

**Или** вызови tool `run_aim_scout` с теми же параметрами — он делает то же
самое.

## Fallback Mode: PipelineEngine 14 фаз (LEGACY, ORCHESTRATOR_MODE=0)

| # | Фаза | Инструменты | Таймаут | NO_DATA |
|---|------|------------|---------|---------|
| 0 | PERPLEXITY | `perplexity_search` | 120s | ❌ |
| 1 | COMPETITORS | `find_competitors` + `run_ci_analysis` | 600s | ❌ |
| 2 | TECH AUDIT | `run_pagespeed` + `run_tech_seo_audit` | 300s | ❌ |
| 3 | SOCIAL VERIFIER | `run_review_platforms` | 180s | ✅ |
| 4 | CONTENT ANALYSIS | `run_content_analysis` | 120s | ❌ |
| 5 | KEY PERSONS | `find_doctor_handles` + `run_instagram_content` | 240s | ❌ |
| 6 | HIRING SIGNALS | `run_hh_analysis` | 90s | ✅ |
| 7 | SMI MENTIONS | `run_smi_mentions` | 120s | ✅ |
| 8 | FORUM PAINS | `web_search` | 120s | ✅ |
| 9 | FINANCE | `find_company_financials` | 60s | ✅ |
| 10 | CONTENT PLAN | `run_content_gaps` | 120s | ✅ |
| 11 | HTML BUILD | `generate_html_report` | 120s | ❌ |
| 12 | QC CRITIQUE | LLM-проверка | 90s | ❌ |
| 13 | PRESENTATION | `publish_scout_report` | 60s | ❌ |

## Каталог инструментов (26 _TOOL_HANDLERS)

`PipelineEngine._TOOL_HANDLERS` (в `app/pipeline/engine.py`) содержит 26
инструментов. Этот список — исчерпывающий для обоих режимов (оркестратор +
PipelineEngine). LLM может вызвать любой из них в оркестраторе;
PipelineEngine — только те, что перечислены в `Phase.tools` для текущей фазы.

**Search & Research (5):**
- `web_search` — общий веб-поиск ( Brave-based )
- `perplexity_search` — Perplexity sonar-pro для глубоких вопросов
- `perplexity_deep_analyze` — расширенный анализ Perplexity
- `firecrawl_extract` — extract контента с одного URL
- `firecrawl_batch_scrape` — batched scrape нескольких URL

**Scraping (4):**
- `firecrawl_agent` — agent-based scraping сложных страниц
- `crawlee_scrape` — Crawlee single-page scrape
- `crawlee_search` — Crawlee site search
- `scrapy_crawl` — Scrapy spider для структурированного краулинга

**Audit (3):**
- `run_pagespeed` — Google PageSpeed Insights (mobile + desktop)
- `run_seo_audit` — технический SEO-аудит (meta, headings, Schema.org)
- `find_competitors` — поиск конкурентов через Apify

**Review (1):**
- `run_review_platforms` — рейтинги и отзывы (ПроДокторов, Яндекс.Карты)

**Content (2):**
- `run_content_analysis` — анализ контент-тем сайта клиники
- `run_content_gaps` — анализ контентных пробелов

**People (3):**
- `find_doctor_handles` — поиск ФИО врачей + Instagram-ников
- `run_doctor_dossiers` — детальные досье на врачей
- `run_instagram_content` — Instagram-анализ (подписчики, ER, темы)

**Market (2):**
- `run_ci_analysis` — CI-анализ конкурентов по 5 полям
- `run_hh_analysis` — анализ вакансий hh.ru

**Media (2):**
- `run_smi_mentions` — счётчики упоминаний в СМИ
- `run_media_urls` — конкретные URL из Forbes/RBC/Vademecum/Kommersant/ТАСС

**Patients (1):**
- `run_forum_pains` — топ-5 страхов пациентов с форумов

**Finance (1):**
- `find_company_financials` — выручка / прибыль / ОКВЭД из ГИР БО

**Report (2):**
- `generate_html_report` — сборка HTML-отчёта в дизайн-системе AIM
- `publish_scout_report` — публикация HTML в WordPress

**ИТОГО: 26 инструментов** (соответствует размеру `_TOOL_HANDLERS` dict).

## Iron Rules

1. **Не прерываешься для подтверждений.** Получил URL → запустил режим →
   показал результат. Автоматический режим для пользователя — без
   промежуточных вопросов «продолжить?» / «показать?».
2. **Не прерываешься.** Пайплайн / оркестратор идут 5-15 минут. Жди.
3. **Не выдумываешь данные.** Нет данных → честно говоришь «данные
   недоступны» (orchestrator помечает пункт `missing` с reason).
4. **Только коммерческая медицина.** Никаких ГАУЗ, ГБУЗ, ГУЗ, МУЗ, МБУЗ —
   только ООО, АО, ЗАО, ИП. Фильтр в `competitor_matcher.py`.
5. **Инфраструктурные ошибки — не для клиента.** Кредиты, ключи, лимиты,
   402/429 — наши проблемы, клиент видит только результат.
6. **В оркестраторе (по умолчанию)** — LLM решает какие инструменты
   вызывать, основываясь на ситуации и нише. QC_CHECKLIST v1.2.0
   направляет решение (Pass 2 highlight missing), не заменяет его.

## Завершение

Когда PipelineEngine завершил работу **ИЛИ** когда оркестратор завершил
Pass 3:

1. Проверь `metadata.json` — `completed_phases`, `failed_phases`.
2. Проверь `report.html` существует.
3. Если published — дай клиенту ссылку на WordPress (из `PRESENTATION.json`
   или из `state.published_url` для orchestrator).
4. Если saved_locally — скажи где лежит файл.
5. Для оркестратора: проверь `state.collected_data["coverage_report_final"]`
   — если status=FAIL, предупреди user-а (но НЕ клиента), что coverage
   ниже 80%, и покажи missing items list.
