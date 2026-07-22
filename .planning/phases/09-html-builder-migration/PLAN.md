# PLAN.md — Phase 9: HTML Builder Migration

> **Phase:** 9
> **Milestone:** 2 (v3 Feature Parity)
> **Created:** 2026-07-22
> **REQ:** REQ-1.1, REQ-1.2

---

## Goal

Перенести HTML builder из v1 (`build_report.py`, 1580 строк) в v2. Создать модуль `hermes-v2/app/report_builder/` с чистой функцией `build_report_html(data, title) → str`. Адаптировать под v2 формат данных (`collected_results`).

## Architecture

```
hermes-v2/app/report_builder/
├── __init__.py          # exports build_report_html
├── builder.py           # build_report_html(data, title) → HTML string
├── markdown_engine.py   # _markdown_to_html + утилиты (строки 19-607 v1)
├── css.py               # _CANONICAL_CSS константа (строки 613-1204 v1)
├── revenue_block.py     # _build_revenue_vs_competitors_block (адаптированный)
└── adapter.py           # v2 collected_results → v1-shape data dict
```

## Data Flow

```
collected_results (v2)           v1-shape data dict
┌─────────────────────┐         ┌──────────────────────────┐
│ "find_competitors"  │──┐  ┌──▶│ "COMPETITORS_interp":    │
│ "quick_overview"    │  │  │   │   {"content": "<md>"}    │
│ "extract_clinic_..."│  ├──┤   │ "FINANCE_interp":        │
│ "run_review_platf." │  │  │   │   {"content": "<md>"}    │
│ "company_financials"│──┘  │   │ "FINANCE":               │
└─────────────────────┘      └──▶│   {"find_company_fin.":  │
                                  │    "<JSON>"}             │
                                  └──────────┬───────────────┘
                                             │
                                             ▼
                                  build_report_html(data, title)
                                             │
                                             ▼
                                  <html>... AIM Design System ...</html>
```

## Tasks

### Task 1: markdown_engine.py — перенос парсера (as-is)

**Files:**
- Create: `AIM/hermes-v2/app/report_builder/markdown_engine.py`
- Source: `AIM/hermes/app/tools/build_report.py:19-607`

**What:** Перенести утилиты (`_esc`, `_fmt_num`, `_fmt_revenue_short`, `_fmt_instagram`) и markdown-движок (`_extract_stats_block`, `_parse_stats_items`, `_markdown_table_to_html`, `_inline_markdown`, `_markdown_to_html`, `_interpretation_to_html`). Без изменений — чистые функции.

**Test:** `tests/test_report_markdown.py` — перенос `test_build_report_parser.py` из v1, проверка `_markdown_to_html` на типовых markdown.

### Task 2: css.py — CSS константа (as-is)

**Files:**
- Create: `AIM/hermes-v2/app/report_builder/css.py`
- Source: `AIM/hermes/app/tools/build_report.py:613-1204`

**What:** Перенести `_CANONICAL_CSS` как строковую константу. Убрать `_THEME_TOGGLE_SCRIPT` (не используется в WP).

### Task 3: revenue_block.py — адаптация источника данных

**Files:**
- Create: `AIM/hermes-v2/app/report_builder/revenue_block.py`
- Source: `AIM/hermes/app/tools/build_report.py:1327-1482` (адаптировать!)

**What:** Перенести `_build_revenue_vs_competitors_block`, но изменить чтение данных:
- v1: `data["FINANCE"]["find_company_financials"]` → v2: `collected_results.get("company_financials")`
- v1: `data["COMPETITORS"]["find_competitors"]` → v2: `collected_results.get("find_competitors")`
- v1: `company.latest_revenue` → v2: `fin_data.get("revenue")` (плоский ключ)
- Конкуренты: те же поля (`revenue_year`, `brand_name`, `inn`)

**Test:** `tests/test_revenue_block.py` — мок collected_results → проверка HTML таблицы.

### Task 4: adapter.py — мост v2 → v1-shape

**Files:**
- Create: `AIM/hermes-v2/app/report_builder/adapter.py`

**What:** Функция `build_data_dict(collected_results, profile_cache, messages) → dict`:
- Мапит v2 tool-имена на v1 phase-ключи
- Использует `_build_formatted_blocks` вывод как interpretation content
- Собирает metadata (company_name, url) из profile_cache

**Mapping:**
```
v2 tool                    → v1 phase_key      → label
extract_clinic_profile     → PROFILE            → "Профиль клиники"
quick_overview             → OVERVIEW           → "Обзор"
find_competitors           → COMPETITORS        → "Конкуренты"
run_review_platforms       → REVIEWS            → "Отзывы пациентов"
company_financials         → FINANCE            → "Финансы"
(client_audit from find_c) → TECH_AUDIT         → "Технический аудит"
```

**Test:** `tests/test_report_adapter.py` — мок collected_results → проверка data dict структуры.

### Task 5: builder.py + __init__.py — финальная сборка

**Files:**
- Create: `AIM/hermes-v2/app/report_builder/builder.py`
- Create: `AIM/hermes-v2/app/report_builder/__init__.py`

**What:** `build_report_html(data, title) → str` — перенос из v1 (строки 1485-1574). Использует markdown_engine + css + revenue_block. Адаптированный phase_order.

**Test:** `tests/test_report_builder.py` — integration: adapter → builder → валидный HTML.

### Task 6: Ручной smoke-тест

**What:** Через Python скрипт на сервере:
1. Вызвать `chat_with_tools` для arclinic.ru
2. Собрать `collected_results`
3. Вызвать `build_data_dict` → `build_report_html`
4. Сохранить HTML в файл
5. Открыть в браузере

---

## Risks

1. **CSS конфликты с WordPress** — v1 уже решено через `aim-report-scope` namespace + wpautop-совместимость (минификация в одну строку). Переносим как есть.
2. **Шрифты Playfair Display + Jost** — подключаются WP-плагином, не в HTML. Проверить что плагин активен.
3. **revenue_block JSON структура** — v2 `company_financials` имеет плоские ключи (`revenue`), v1 — вложенные (`company.latest_revenue`). Адаптация в Task 3.
4. **Размер CSS (~570 строк)** — переносим как константу, не оптимизируем.
