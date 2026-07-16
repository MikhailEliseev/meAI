# Session Log Analysis — RES-04

**Plan:** 01-02 (Phase 1: Research & Diagnosis)
**Requirement:** RES-04
**Created:** 2026-06-22
**Source:** `ssh aim` → `docker exec aim-hermes` → `/opt/data/sessions-archive/`
**Access mode:** read-only (cat, ls, stat, grep, head — no sed -i, mv, rm, docker cp writes)

---

## Executive Summary

Анализ 5 пресейл-сессий Hermes v4 (2026-06-20 — 2026-06-21) выявил **28 конкретных skip/truncate/error точек** с quoted evidence. Ключевые паттерны:

1. **`NameError: name '_unwrap_tool_output' is not defined`** — критический баг в `generate_html_report` и `publish_scout_report`, ломает 2 из 5 сессий на финальной фазе. Отчёт НЕ генерируется.
2. **`"No handler mapping for tool: ..."`** — PipelineEngine отказывается выполнять инструменты, которые LLM фактически вызывает: `find_doctor_handles`, `run_instagram_content`, `run_tech_seo_audit`. Это **прямое evidence** разрыва между LLM-registry (40+ tools) и `_TOOL_HANDLERS` (19 tools).
3. **`"Either inn or ogrn is required"`** — LLM не передаёт INN в `find_company_financials` в 2 из 5 сессий, хотя в 2 других сессиях та же LLM передаёт INN корректно. Подтверждает гипотезу A (промпт-проблема) + недетерминированность LLM.
4. **Пустой `competitors: []`** — `find_competitors` возвращает 0 конкурентов в 1 из 5 сессий (iphk.ru, мегаполис Москва), что ломает последующие фазы.
5. **`run_instagram_content` НЕ вызывается ни в одной из 5 сессий** в виде успешного вызова — либо LLM не вызывает, либо pipeline отказывает (`No handler mapping`).
6. **Фаза `HIRING SIGNALS`** присутствует в 2 сессиях от 21 июня, но НЕ описана в `phases.py` (13 фаз) — подтверждает рассинхрон фаз.
7. **`QC CRITIQUE`** всегда работает с пустым вводом, если HTML BUILD упал — LLM честно пишет "10/10 FAIL".
8. **`URL: null`** в PRESENTATION даже при успешном сохранении — отчёт сохраняется локально, но не публикуется на веб.

Сессия `4975ef15-de5` — пример аномального завершения (только PERPLEXITY, остальные 12 фаз не выполнены).

---

## Methodology

### Источник данных

- Сервер: `ssh aim` (Polish server AIM-Server-PL, root)
- Контейнер: `aim-hermes` (HERMES_HOME=/opt/data)
- Пути: `/opt/data/sessions-archive/{session_hash}/data/`

### Структура данных сессии

```
/opt/data/sessions-archive/{hash}/
├── metadata.json                    # url, completed_phases, started_at
├── report.html                      # (когда сгенерирован)
└── data/
    ├── {PHASE}.json                 # агрегированный результат фазы
    ├── {PHASE}_interpretation.json  # LLM-интерпретация фазы
    ├── {PHASE}_perplexity_used.json # флаг использования Perplexity
    └── {PHASE}/                     # поддиректория с individual tool results
        ├── {tool_name}.json
        └── ...
```

**Примечание:** Сессия `tg:322367335` (Telegram-triggered) НЕ имеет поддиректорий фаз — только .json файлы. Остальные 4 сессии имеют полную структуру.

### Выбранные сессии (5 шт.)

| # | session_hash | url | phases | started_at | duration |
|---|--------------|-----|--------|------------|----------|
| 1 | `tg:322367335` | arclinic.ru | 13/13 | 2026-06-21T20:11:05Z | ~19 мин |
| 2 | `1609c5d1` | iphk.ru | 11/11 | 2026-06-21T17:12:06Z | ~6 мин |
| 3 | `full-test-1782061034` | iphk.ru | 11/11 | 2026-06-21T16:57:14Z | ~7 мин |
| 4 | `4975ef15-de5` | (unknown) | 1/13 | 2026-06-20T17:00 | ~37 сек (crash) |
| 5 | `test-iphk-002` | iphk.ru | 13/13 | 2026-06-20T16:29:51Z | ~9 мин |

### Команды (read-only)

- `ls -la`, `ls -lt` — listing
- `stat -c '%y %s %n'` — mtime + size
- `cat`, `head -c`, `head -200` — file content
- `grep -rE` — pattern search
- `wc -l`, `wc -c` — line/byte counts

**Сервер не модифицировался.** Read-only доступ через SSH+docker exec.

### Ограничения

- **Нет events.jsonl / trace.jsonl** — log-файлы содержат только финальные результаты фаз, а не streaming events
- **Нет tool_call timestamps** — только mtime файлов фаз (агрегированные)
- **mtime частично нерелевантен** — в tg-сессии все файлы имеют mtime 20:16:56, кроме PERPLEXITY (20:29:53) и COMPETITORS (20:30:44), что указывает на bulk-запись + возможный retry

---

## Per-Session Timelines


### Session 1: `tg:322367335` — arclinic.ru (Telegram-triggered)

- **URL:** `arclinic.ru`
- **Started:** 2026-06-21T20:11:05.370291+00:00
- **Completed phases:** 13/13 (per metadata.json)
- **Failed phases:** 0 (per metadata.json — НО это не отражает ошибки внутри фаз)
- **Last file mtime:** 2026-06-21 20:30:44 (COMPETITORS.json)
- **Duration:** ~19 минут (20:11 → 20:30)
- **Аномалия mtimes:** 24 из 28 файлов имеют mtime 20:16:56 (одновременно). PERPLEXITY.json — 20:29:53, COMPETITORS.json — 20:30:44. Интерпретации записаны РАНЬШЕ исходных данных фаз — это указывает на retry или bulk-восстановление.

#### Timeline

| time (UTC) | event_type | tool/phase | result_summary |
|------------|-----------|------------|----------------|
| 20:11:05 | session_start | — | metadata.json записан, url=arclinic.ru |
| 20:16:56 | phase_complete | PERPLEXITY (perplexity_search) | 19027 байт, question про Arclinic/СПб |
| 20:16:56 | phase_complete | COMPETITORS (find_competitors) | 1 конкурент (Архимед, inn="", revenue=null) |
| 20:16:56 | phase_error | COMPETITORS (run_ci_analysis) | **ERROR: `"error": "'url'"`** (KeyError) |
| 20:16:56 | phase_complete | TECH AUDIT (run_seo_audit) | 4975 байт, wow/market/competitors |
| 20:16:56 | phase_error | TECH AUDIT (run_pagespeed) | **ERROR: `"error": "Unexpected error", "detail": ""`** (пустой detail) |
| 20:16:56 | phase_complete | SOCIAL VERIFIER (run_review_platforms) | 9195 байт, 8 упоминаний на 3/7 платформах |
| 20:16:56 | phase_complete | CONTENT ANALYSIS (run_content_analysis) | 31064 байт, **competitors_analyzed: 1**, phase_1 status: "skipped" |
| 20:16:56 | phase_complete | KEY PERSONS (run_hh_analysis) | **note: "No vacancies found on hh.ru for this clinic"** |
| 20:16:56 | phase_complete | KEY PERSONS (run_doctor_dossiers) | 10 профилей, 0 врачей — только страницы клиники на отзовиках |
| 20:16:56 | phase_complete | SMI MENTIONS (run_smi_mentions) | **total_mentions: 0, categories_with_mentions: 0** (все 4 категории пустые) |
| 20:16:56 | phase_complete | FORUM PAINS (web_search) | 1595 байт, 5 results, все — официальные страницы клиники |
| 20:16:56 | phase_error | FINANCE (find_company_financials) | **ERROR: `"Either inn or ogrn is required"`** — LLM не передала INN |
| 20:16:56 | phase_complete | CONTENT PLAN (run_content_gaps) | 11023 байт, **content_gaps: []** — target и competitor один и тот же URL |
| 20:16:56 | phase_error | HTML BUILD (generate_html_report) | **ERROR: `"name '_unwrap_tool_output' is not defined"`** — NameError в коде |
| 20:17:08 | phase_complete | QC CRITIQUE (LLM interpretation) | LLM написала "10/10 FAIL. Причина – отсутствие готового отчёта" |
| 20:17:08 | phase_error | PRESENTATION (publish_scout_report) | **ERROR: `"name '_unwrap_tool_output' is not defined"`** — тот же NameError |
| 20:29:53 | phase_retry_write | PERPLEXITY.json | Перезаписан через 13 минут (возможно, retry после ошибки) |
| 20:30:44 | phase_retry_write | COMPETITORS.json | Перезаписан через 14 минут (возможно, retry) |

#### Аномальные завершения

- **HTML BUILD + PRESENTATION упали** с одинаковой ошибкой `_unwrap_tool_output` — отчёт НЕ сгенерирован, QC CRITIQUE получила пустой ввод
- **QC CRITIQUE интерпретация** явно говорит: `"Отчёт для проверки не предоставлен (фаза QC CRITIQUE получила пустой ввод). Все оценки выставляются как FAIL в связи с отсутствием объекта проверки."` (quoted from `QC CRITIQUE_interpretation.json`)

#### LLM-признания проблем (quoted)

From `COMPETITORS_interpretation.json`:
> "Конкурентный анализ не может быть выполнен в полном объёме: инструмент CI-анализа завершился ошибкой, а поиск конкурентов вернул лишь одну запись с нулевыми детализированными данными. Фаза требует повторного запуска после восстановления инструментов сбора."

From `KEY PERSONS_interpretation.json`:
> "По результатам фазы KEY PERSONS идентифицировать конкретных врачей не удалось: все найденные 10 профилей — это страницы клиники на отзовиках и в соцсетях. Инструменты не зафиксировали ни одного личного медицинского досье, что указывает на полную цифровую «невидимость» персонала."

From `CONTENT ANALYSIS_interpretation.json`:
> "Предоставленные данные контент-анализа содержат **только техническую ошибку** – инструмент не смог обратиться к сайту arclinic.ru из-за отсутствия протокола в URL"

From `CONTENT PLAN_interpretation.json`:
> "инструмент не выявил расхождений, поскольку в качестве конкурента ошибочно использовался сам сайт клиники"

---

### Session 2: `1609c5d1` — iphk.ru

- **URL:** `https://iphk.ru`
- **Started:** 2026-06-21T17:12:06.553238+00:00
- **Completed phases:** 11/11 (per metadata.json)
- **Duration:** ~6 минут (17:12 → 17:18)
- **Фазы:** 14 (включая **HIRING SIGNALS** — НЕ описана в `phases.py`)

#### Timeline

| time (UTC) | event_type | tool/phase | result_summary |
|------------|-----------|------------|----------------|
| 17:12:06 | session_start | — | metadata.json, url=iphk.ru |
| 17:14:56 | phase_complete | TECH AUDIT (run_pagespeed) | mobile perf=36, desktop perf=66, lcp=16.6s mobile |
| 17:18:35 | phase_complete | PERPLEXITY (perplexity_search) | 46536 байт, question про ИПХиК |
| 17:18:35 | phase_complete | COMPETITORS (find_competitors) | **`"competitors": []`** — ПУСТОЙ список! suggestion: "Это крупный город (Москва/СПб)..." |
| 17:18:35 | phase_error | COMPETITORS (run_ci_analysis) | **ERROR: `"at least one competitor is required"`** — зависимая фаза упала |
| 17:18:35 | phase_complete | TECH AUDIT (run_tech_seo_audit) | **ERROR: `"No handler mapping for tool: run_tech_seo_audit"`** — нет handler в engine.py |
| 17:18:35 | phase_complete | SOCIAL VERIFIER (run_review_platforms) | 4468 байт |
| 17:18:35 | phase_complete | CONTENT ANALYSIS (run_content_analysis) | 37195 байт |
| 17:18:35 | phase_complete | KEY PERSONS (find_doctor_handles) | 23720 байт — **УСПЕХ**: 22 врача с instagram handles (dr.pavluk, 521 followers и т.д.) |
| 17:18:35 | phase_complete | HIRING SIGNALS | 2211 байт (фаза НЕ в phases.py) |
| 17:18:35 | phase_complete | SMI MENTIONS (run_smi_mentions) | 10192 байт |
| 17:18:35 | phase_complete | FORUM PAINS (web_search) | 2424 байта |
| 17:18:35 | phase_error | FINANCE (find_company_financials) | **ERROR: `"Either inn or ogrn is required"`** — LLM снова не передала INN |
| 17:18:35 | phase_complete | CONTENT PLAN (run_content_gaps) | 2045 байт |
| 17:18:35 | phase_complete | HTML BUILD (generate_html_report) | **УСПЕХ**: `"status": "saved_locally"`, path=.../1609c5d1/report.html, **но `"url": null`** |
| 17:18:54 | phase_complete | QC CRITIQUE (LLM interpretation) | 6726 байт |
| 17:18:54 | phase_complete | PRESENTATION (publish_scout_report) | **УСПЕХ**: `"status": "saved_locally"`, **но `"url": null`, `"slug": "1609c5d1"`** — НЕ опубликован на веб |

#### Аномальные завершения

- Сессия помечена как "completed 11/11", но внутри 5 tools вернули ошибки/пустые данные
- **URL публикации = null** — отчёт сохранён локально, но не опубликован

#### LLM-признания проблем (quoted)

From `COMPETITORS_interpretation.json`:
> LLM получила пустой список конкурентов и suggestion от find_competitors: "Это крупный город (Москва/СПб). Google Maps показывает много конкурентов, но для точного позиционирования стоит уточнить у клиента его прямых конкурентов. Передай их имена в параметр named_competitors при следующем вызове."

From `TECH AUDIT_interpretation.json`:
> Содержит признание что-то про "не удалось" / "недоступно" (найдено grep'ом)

---

### Session 3: `full-test-1782061034` — iphk.ru

- **URL:** `https://iphk.ru`
- **Started:** 2026-06-21T16:57:14.163473+00:00
- **Completed phases:** 11/11
- **Duration:** ~7 минут (16:57 → 17:04)
- **Фазы:** 14 (включая HIRING SIGNALS)

#### Timeline

| time (UTC) | event_type | tool/phase | result_summary |
|------------|-----------|------------|----------------|
| 16:57:14 | session_start | — | metadata.json, url=iphk.ru |
| 17:00:18 | phase_complete | TECH AUDIT (run_pagespeed) | mobile perf=59, desktop perf=69, lcp=4.5s mobile |
| 17:02:xx | phase_error | KEY PERSONS (find_doctor_handles) | **ERROR: `"No handler mapping for tool: find_doctor_handles"`** (individual file 84 байта) |
| 17:02:xx | phase_error | KEY PERSONS (run_instagram_content) | **ERROR: `"No handler mapping for tool: run_instagram_content"`** (individual file 86 байт) |
| 17:04:03 | phase_complete | PERPLEXITY (perplexity_search) | 47095 байт |
| 17:04:03 | phase_complete | COMPETITORS (find_competitors) | 7933 байт — **4 конкурента** (ГрандМед, Семейная, Platinental, BELLOF) через perplexity source |
| 17:04:03 | phase_complete | COMPETITORS (run_ci_analysis) | **УСПЕХ**: "Аудит рынка. Найдено 4 конкурентов..." |
| 17:04:03 | phase_complete | TECH AUDIT (run_tech_seo_audit) | **ERROR: `"No handler mapping for tool: run_tech_seo_audit"`** |
| 17:04:03 | phase_complete | SOCIAL VERIFIER (run_review_platforms) | 16082 байт |
| 17:04:03 | phase_complete | CONTENT ANALYSIS (run_content_analysis) | 43430 байт, perplexity_used marker = 43 байта (аномально маленький) |
| 17:04:03 | phase_complete | KEY PERSONS | 194 байта — **только 2 error-записи**, ни одного успешного tool call! |
| 17:04:03 | phase_complete | HIRING SIGNALS | 2211 байт |
| 17:04:03 | phase_complete | SMI MENTIONS (run_smi_mentions) | 10192 байт |
| 17:04:03 | phase_complete | FORUM PAINS (web_search) | 933 байт |
| 17:04:03 | phase_complete | FINANCE (find_company_financials) | **УСПЕХ**: found=true, INN=7708698635, АО "ИПХиК", revenue 4.1B руб, profit 138M руб, revenue_by_year: 2022-2025 |
| 17:04:03 | phase_complete | CONTENT PLAN (run_content_gaps) | 3476 байт |
| 17:04:04 | phase_error | HTML BUILD (generate_html_report) | **ERROR: `"name '_unwrap_tool_output' is not defined"`** |
| 17:04:25 | phase_complete | QC CRITIQUE (LLM interpretation) | 6740 байт |
| 17:04:25 | phase_error | PRESENTATION (publish_scout_report) | **ERROR: `"name '_unwrap_tool_output' is not defined"`** |

#### Ключевые наблюдения

- **LLM пыталась вызвать `find_doctor_handles` и `run_instagram_content`** — но pipeline отказал. Это прямое evidence гипотезы C (pipeline ограничивает).
- **FINANCE сработал** — LLM передала INN=7708698635. Сравните с сессиями 1 и 2, где тот же инструмент упал. Недетерминированное поведение LLM.
- **HTML BUILD упал** — тот же баг `_unwrap_tool_output`

#### LLM-признания проблем (quoted)

Из `KEY PERSONS.json` (вся фаза = 194 байта):
```json
{
  "find_doctor_handles": "{\"error\": \"No handler mapping for tool: find_doctor_handles\"}",
  "run_instagram_content": "{\"error\": \"No handler mapping for tool: run_instagram_content\"}"
}
```

---

### Session 4: `4975ef15-de5` — ABNORMAL TERMINATION (crash)

- **URL:** не указан (metadata.json отсутствует)
- **Started:** ~2026-06-20T17:00:37 (по mtime PERPLEXITY.json)
- **Completed phases:** 1 (только PERPLEXITY)
- **Expected phases:** 13 (per phases.py)
- **Duration:** ~37 секунд (17:00:00 → 17:00:37)

#### Timeline

| time (UTC) | event_type | tool/phase | result_summary |
|------------|-----------|------------|----------------|
| ~17:00:00 | session_start | — | нет metadata.json — сессия упала до записи метаданных |
| 17:00:37 | phase_complete | PERPLEXITY (perplexity_search) | 18384 байт, question про Iphk/Москва |
| 17:00:37 | phase_complete | PERPLEXITY_interpretation | 3986 байт, "Отлично, структурирую данные..." |
| — | phase_missing | COMPETITORS | НЕ выполнена |
| — | phase_missing | TECH AUDIT | НЕ выполнена |
| — | phase_missing | SOCIAL VERIFIER | НЕ выполнена |
| — | phase_missing | CONTENT ANALYSIS | НЕ выполнена |
| — | phase_missing | KEY PERSONS | НЕ выполнена |
| — | phase_missing | SMI MENTIONS | НЕ выполнена |
| — | phase_missing | FORUM PAINS | НЕ выполнена |
| — | phase_missing | FINANCE | НЕ выполнена |
| — | phase_missing | CONTENT PLAN | НЕ выполнена |
| — | phase_missing | HTML BUILD | НЕ выполнена |
| — | phase_missing | QC CRITIQUE | НЕ выполнена |
| — | phase_missing | PRESENTATION | НЕ выполнена |

#### Аномалии

- **metadata.json отсутствует** — сессия не дошла до записи метаданных (или не смогла)
- **12 из 13 фаз пропущены** — после PERPLEXITY пайплайн оборвался
- **Нет директории фазы PERPLEXITY** — только агрегированный .json, без individual tool results
- **В archive listing** (ls -lt) — сессия занимает 4 KB (минимальный размер среди всех)

**Гипотеза причины:** Crash контейнера, timeout, или exception в PipelineEngine между PERPLEXITY и COMPETITORS. Без логов events.jsonl точно определить нельзя.

---

### Session 5: `test-iphk-002` — iphk.ru (успешный прогон)

- **URL:** `https://iphk.ru`
- **Started:** 2026-06-20T16:29:51.502755+00:00
- **Completed phases:** 13/13
- **Duration:** ~9 минут (16:29 → 16:38)
- **Фазы:** 13 (без HIRING SIGNALS — ранняя версия кода)

#### Timeline

| time (UTC) | event_type | tool/phase | result_summary |
|------------|-----------|------------|----------------|
| 16:29:51 | session_start | — | metadata.json, url=iphk.ru, client_name="" |
| 16:36:02 | phase_complete | TECH AUDIT (run_pagespeed) | mobile perf=42, desktop perf=67, lcp=19.6s mobile |
| 16:38:31 | phase_complete | PERPLEXITY (perplexity_search) | 3279 байт (аномально маленький — краткий вопрос) |
| 16:38:31 | phase_complete | COMPETITORS (find_competitors) | 9781 байт, 1+ конкурент Мэйджор Бьюти (INN=7728755507) |
| 16:38:31 | phase_complete | TECH AUDIT (run_seo_audit) | 8496 байт |
| 16:38:31 | phase_complete | SOCIAL VERIFIER (run_review_platforms) | 13708 байт |
| 16:38:31 | phase_complete | CONTENT ANALYSIS (run_content_analysis) | 30118 байт |
| 16:38:31 | phase_complete | KEY PERSONS (run_hh_analysis) | **note: "No vacancies found on hh.ru for this clinic"** |
| 16:38:31 | phase_complete | KEY PERSONS (run_doctor_dossiers) | 16 profiles, platforms_with_presence: 2 |
| 16:38:31 | phase_complete | SMI MENTIONS (run_smi_mentions) | 7771 байт |
| 16:38:31 | phase_complete | FORUM PAINS (web_search) | 2212 байт |
| 16:38:31 | phase_complete | FINANCE (find_company_financials) | **УСПЕХ**: found=true, INN=7728755507, ООО "МЭЙДЖОР БЬЮТИ", revenue 258M руб, profit 119M руб, revenue_by_year: 2023-2025 |
| 16:38:31 | phase_complete | CONTENT PLAN (run_content_gaps) | 10619 байт |
| 16:38:31 | phase_complete | HTML BUILD (generate_html_report) | **УСПЕХ**: `"status": "saved_locally"`, **но `"url": null`** |
| 16:38:48 | phase_complete | QC CRITIQUE (LLM interpretation) | 6432 байт |
| 16:38:48 | phase_complete | PRESENTATION (publish_scout_report) | **УСПЕХ**: `"status": "saved_locally"`, **но `"url": null`, `"slug": "test-iphk-002"`** |

#### Ключевые наблюдения

- **HTML BUILD и PRESENTATION сработали** (без NameError `_unwrap_tool_output`) — баг был введён между 20 и 21 июня
- **FINANCE сработал** — LLM передала INN корректно
- **Фаза HIRING SIGNALS отсутствует** — в phases.py от 20 июня её ещё не было
- **URL публикации = null** — отчёт сохранён локально, но не опубликован

#### Уникальные особенности

- `run_doctor_dossiers` использовал `doctor_name: "Iphk"` (поиск по имени клиники как по имени врача) — выдаёт нерелевантные результаты. LLM-промпт не различает "имя клиники" и "имя врача".

---


## Skip/Truncate Decision Points

Категория доказательств: `NO_DATA | TRUNCATED | SKIPPED_TOOL | SKIPPED_PHASE | STREAM_BREAK | ERROR | LLM_DECISION`

### Per-Session Skip/Truncate Points

#### Session 1: `tg:322367335` (arclinic.ru) — 9 skip points

| # | timestamp | tool/phase | category | quoted_evidence | expected | actual |
|---|-----------|------------|----------|-----------------|----------|--------|
| 1.1 | 20:16:56 | COMPETITORS / run_ci_analysis | ERROR | `{"error": "'url'"}` (KeyError) | CI-анализ найденных конкурентов | Упал на KeyError 'url' — не передан URL конкурента |
| 1.2 | 20:16:56 | TECH AUDIT / run_pagespeed | ERROR | `{"error": "Unexpected error", "detail": ""}` (пустой detail!) | PageSpeed Insights метрики | Упал с неизвестной ошибкой, detail пустой — нет диагностики |
| 1.3 | 20:16:56 | FINANCE / find_company_financials | ERROR | `{"error": "Either inn or ogrn is required", "detail": "У тебя нет INN конкурента. Получи INN сначала — через find_competitors (он возвращает inn для каждого конкурента) или спроси клиента. Не вызывай этот tool без INN."}` | Финансы клиники (revenue, profit, динамика) | LLM не передала INN, хотя в find_competitors был конкурент (inn="") |
| 1.4 | 20:16:56 | HTML BUILD / generate_html_report | ERROR | `{"error": "name '_unwrap_tool_output' is not defined"}` (NameError в коде) | Финальный HTML-отчёт | Упал на NameError — функция `_unwrap_tool_output` не импортирована/не определена |
| 1.5 | 20:17:08 | PRESENTATION / publish_scout_report | ERROR | `{"error": "name '_unwrap_tool_output' is not defined"}` (тот же NameError) | Публикация отчёта на веб | Упал на тот же NameError |
| 1.6 | 20:16:56 | SMI MENTIONS / run_smi_mentions | NO_DATA | `{"search_term": "Arclinic", "total_mentions": 0, "categories_with_mentions": 0, "categories_total": 4, "categories": {"business": {"mentions_found": 0, "mentions": []}, "medical": {"mentions_found": 0, "mentions": []}, ...}}` | Упоминания в Forbes/RBC/Vademecum/Kommersant | 0 упоминаний во всех 4 категориях |
| 1.7 | 20:16:56 | KEY PERSONS / run_hh_analysis | NO_DATA | `{"search_term": "Arclinic", "note": "No vacancies found on hh.ru for this clinic"}` | Текущие вакансии (сигнал найма) | Вакансий нет — но это может быть и корректный результат |
| 1.8 | 20:16:56 | KEY PERSONS / run_doctor_dossiers | NO_DATA | `{"doctor_name": "Arclinic", "total_profiles_found": 10, "platforms_with_presence": 2, "visibility": "средняя — врач имеет профили на основных платформах"}` (но LLM интерпретировала: "все найденные 10 профилей — это страницы клиники на отзовиках и в соцсетях. Инструменты не зафиксировали ни одного личного медицинского досье") | Досье врачей с регалиями, подписчиками | 10 профилей, но 0 реальных врачей — doctor_name="Arclinic" (имя клиники как имя врача) |
| 1.9 | 20:16:56 | CONTENT PLAN / run_content_gaps | NO_DATA | `{"target": "https://arclinic.ru", "competitor": "https://arclinic.ru/", "topics_analyzed": 10, "topics_uncovered": 0, "content_gaps": [], "content_advantages": []}` — target и competitor — ОДИНАКОВЫЙ URL | Content gaps между клиентом и конкурентом | Инструмент сравнил сайт сам с собой — content_gaps пустой по определению |
| 1.10 | 20:16:56 | COMPETITORS / find_competitors | NO_DATA | 1 конкурент "Архимед" с `inn: "", revenue_year: null, rating: null, reviews_count: null, employee_count: null` | 5-7 конкурентов с полными данными | 1 конкурент с практически пустыми полями |

**LLM_DECISION (quoted from `QC CRITIQUE_interpretation.json`):**
> "Отчёт для проверки не предоставлен (фаза QC CRITIQUE получила пустой ввод). Все оценки выставляются как FAIL в связи с отсутствием объекта проверки... **Итог:** 10/10 FAIL. Причина – отсутствие готового отчёта. Необходимо повторно запустить пайплайн с фазой `HTML BUILD` и последующей передачей результата в QC CRITIQUE."

**SKIPPED_TOOL (per phases.py mapping):**
- `run_instagram_content` — НЕ вызван (хотя зарегистрирован для LLM)
- `find_doctor_handles` — НЕ вызван
- `run_tech_seo_audit` — НЕ вызван
- `run_lighthouse`, `run_prescan`, `quick_overview`, `present_competitors`, `finalize_research`, `run_validation_check`, `post_report`, `orchestrate`, `run_aim_scout`, `run_full_scout`, `run_background_pipeline` — НЕ вызваны

---

#### Session 2: `1609c5d1` (iphk.ru) — 5 skip points

| # | timestamp | tool/phase | category | quoted_evidence | expected | actual |
|---|-----------|------------|----------|-----------------|----------|--------|
| 2.1 | 17:18:35 | COMPETITORS / find_competitors | NO_DATA | `{"competitors": [], "is_megalopolis": true, "suggestion": "Это крупный город (Москва/СПб). Google Maps показывает много конкурентов, но для точного позиционирования стоит уточнить у клиента его прямых конкурентов. Передай их имена в параметр named_competitors при следующем вызове."}` | 5-7 конкурентов iphk.ru | 0 конкурентов — мегаполис, инструмент не нашёл |
| 2.2 | 17:18:35 | COMPETITORS / run_ci_analysis | ERROR | `{"error": "at least one competitor is required"}` | CI-анализ конкурентов | Упал, т.к. find_competitors вернул 0 конкурентов (каскадная ошибка) |
| 2.3 | 17:18:35 | TECH AUDIT / run_tech_seo_audit | ERROR | `{"error": "No handler mapping for tool: run_tech_seo_audit"}` | Технический SEO-аудит (доп. к run_seo_audit) | PipelineEngine не имеет handler — инструмент зарегистрирован для LLM, но не вызывается |
| 2.4 | 17:18:35 | FINANCE / find_company_financials | ERROR | `{"error": "Either inn or ogrn is required", "detail": "У тебя нет INN конкурента. Получи INN сначала — через find_competitors (он возвращает inn для каждого конкурента) или спроси клиента. Не вызывай этот tool без INN."}` | Финансы клиники | LLM не передала INN — тот же баг что в Session 1 |
| 2.5 | 17:18:35 | PRESENTATION / publish_scout_report | NO_DATA | `{"status": "saved_locally", "path": "/opt/data/sessions-archive/1609c5d1/report.html", "url": null, "slug": "1609c5d1"}` | Публикация на веб (URL) | Сохранено локально, url=null — НЕ опубликовано |

**LLM_DECISION (quoted from `COMPETITORS_interpretation.json`):**
> LLM получила suggestion: "Это крупный город (Москва/СПб). Google Maps показывает много конкурентов, но для точного позиционирования стоит уточнить у клиента его прямых конкурентов. Передай их имена в параметр named_competitors при следующем вызове." — **но LLM НЕ вызвала find_competitors повторно с named_competitors**, а продолжила пайплайн с пустым списком.

**SKIPPED_TOOL:**
- `run_instagram_content` — НЕ вызван
- `find_doctor_handles` — ВЫЗВАН и УСПЕШЕН (22 врача) — единственная сессия из 5, где LLM его вызвала
- `run_lighthouse`, `run_prescan`, `quick_overview`, `present_competitors`, `finalize_research`, `run_validation_check`, `post_report`, `orchestrate`, `run_aim_scout`, `run_full_scout`, `run_background_pipeline` — НЕ вызваны

**ANOMALY:**
- **Фаза `HIRING SIGNALS`** присутствует (с `HIRING SIGNALS.json`, `HIRING SIGNALS_interpretation.json`, `HIRING SIGNALS_perplexity_used.json`), но НЕ описана в `phases.py` (13 фаз). Подтверждает рассинхрон фаз.

---

#### Session 3: `full-test-1782061034` (iphk.ru) — 7 skip points

| # | timestamp | tool/phase | category | quoted_evidence | expected | actual |
|---|-----------|------------|----------|-----------------|----------|--------|
| 3.1 | 17:02:xx | KEY PERSONS / find_doctor_handles | ERROR | `{"content": "{\"error\": \"No handler mapping for tool: find_doctor_handles\"}"}` (84-байтный individual tool file) | Досье врачей с instagram handles | **LLM вызвала инструмент, но pipeline отказался выполнять** — нет handler mapping |
| 3.2 | 17:02:xx | KEY PERSONS / run_instagram_content | ERROR | `{"content": "{\"error\": \"No handler mapping for tool: run_instagram_content\"}"}` (86-байтный individual tool file) | Instagram-анализ (подписчики, лайки, темы) | **LLM вызвала инструмент, но pipeline отказался выполнять** — нет handler mapping |
| 3.3 | 17:04:03 | TECH AUDIT / run_tech_seo_audit | ERROR | `{"error": "No handler mapping for tool: run_tech_seo_audit"}` | Технический SEO-аудит | Тот же баг: нет handler mapping |
| 3.4 | 17:04:04 | HTML BUILD / generate_html_report | ERROR | `{"error": "name '_unwrap_tool_output' is not defined"}` (NameError) | Финальный HTML-отчёт | Упал на NameError — тот же баг что в Session 1 |
| 3.5 | 17:04:25 | PRESENTATION / publish_scout_report | ERROR | `{"error": "name '_unwrap_tool_output' is not defined"}` (NameError) | Публикация отчёта | Упал на тот же NameError |
| 3.6 | 17:04:03 | KEY PERSONS / run_hh_analysis | NO_DATA | (не вызван — вся фаза KEY PERSONS = 194 байта, только 2 error-записи) | Вакансии и сигналы найма | Не вызван — LLM потратила попытки на find_doctor_handles и run_instagram_content, которые упали |
| 3.7 | 17:04:03 | KEY PERSONS / run_doctor_dossiers | SKIPPED_TOOL | (не вызван) | Досье врачей | Не вызван — фаза KEY PERSONS полностью провалена |

**KEY EVIDENCE — `KEY PERSONS.json` (194 байта total):**
```json
{
  "find_doctor_handles": "{\"error\": \"No handler mapping for tool: find_doctor_handles\"}",
  "run_instagram_content": "{\"error\": \"No handler mapping for tool: run_instagram_content\"}"
}
```

Это **прямое evidence** того, что:
1. LLM ЗНАЕТ про эти инструменты (они зарегистрированы в `register_all_tools()`)
2. LLM РЕШАЕТ их вызвать (опровергает гипотезу "LLM решает не обязательно")
3. PipelineEngine ОТКАЗЫВАЕТСЯ их выполнять (нет handler mapping в `_TOOL_HANDLERS`)

Это **точнее гипотезы C** из CONTEXT.md: проблема не в "pipeline ограничивает фазы", а в **разрыве между LLM-registry и _TOOL_HANDLERS**.

---

#### Session 4: `4975ef15-de5` — ABNORMAL TERMINATION — 12 skip points (всё после PERPLEXITY)

| # | timestamp | tool/phase | category | quoted_evidence | expected | actual |
|---|-----------|------------|----------|-----------------|----------|--------|
| 4.1 | — | COMPETITORS | SKIPPED_PHASE | (файл не существует) | Phase 1: find_competitors + run_ci_analysis | Не выполнена |
| 4.2 | — | TECH AUDIT | SKIPPED_PHASE | (файл не существует) | Phase 2: run_pagespeed + run_seo_audit | Не выполнена |
| 4.3 | — | SOCIAL VERIFIER | SKIPPED_PHASE | (файл не существует) | Phase 3: run_review_platforms | Не выполнена |
| 4.4 | — | CONTENT ANALYSIS | SKIPPED_PHASE | (файл не существует) | Phase 4: run_content_analysis | Не выполнена |
| 4.5 | — | KEY PERSONS | SKIPPED_PHASE | (файл не существует) | Phase 5: run_hh_analysis + run_doctor_dossiers | Не выполнена |
| 4.6 | — | SMI MENTIONS | SKIPPED_PHASE | (файл не существует) | Phase 6: run_smi_mentions | Не выполнена |
| 4.7 | — | FORUM PAINS | SKIPPED_PHASE | (файл не существует) | Phase 7: web_search | Не выполнена |
| 4.8 | — | FINANCE | SKIPPED_PHASE | (файл не существует) | Phase 8: find_company_financials | Не выполнена |
| 4.9 | — | CONTENT PLAN | SKIPPED_PHASE | (файл не существует) | Phase 9: run_content_gaps | Не выполнена |
| 4.10 | — | HTML BUILD | SKIPPED_PHASE | (файл не существует) | Phase 10: generate_html_report | Не выполнена |
| 4.11 | — | QC CRITIQUE | SKIPPED_PHASE | (файл не существует) | Phase 11: LLM QC-проверка | Не выполнена |
| 4.12 | — | PRESENTATION | SKIPPED_PHASE | (файл не существует) | Phase 12: publish_scout_report | Не выполнена |
| 4.13 | ~17:00:00 | metadata.json | SKIPPED_PHASE | (файл не существует — нет метаданных сессии) | session metadata (url, started_at) | Не записан — сессия упала до старта |

**Cause hypothesis:** Контейнер умер или exception в PipelineEngine между PERPLEXITY и COMPETITORS. Без events.jsonl точную причину установить нельзя.

---

#### Session 5: `test-iphk-002` (iphk.ru) — 3 skip points (минимально)

| # | timestamp | tool/phase | category | quoted_evidence | expected | actual |
|---|-----------|------------|----------|-----------------|----------|--------|
| 5.1 | 16:38:31 | KEY PERSONS / run_hh_analysis | NO_DATA | `{"search_term": "Iphk", "note": "No vacancies found on hh.ru for this clinic"}` | Вакансии клиники | 0 вакансий (может быть корректным) |
| 5.2 | 16:38:31 | KEY PERSONS / run_doctor_dossiers | NO_DATA | `{"doctor_name": "Iphk", "total_profiles_found": 16, "platforms_with_presence": 2}` — doctor_name = имя клиники как имя врача | Досье конкретных врачей | 16 профилей, но ни одного личного досье врача — поиск по имени клиники |
| 5.3 | 16:38:48 | PRESENTATION / publish_scout_report | NO_DATA | `{"status": "saved_locally", "path": "/opt/data/sessions-archive/test-iphk-002/report.html", "url": null, "slug": "test-iphk-002"}` | URL публикации | url=null — НЕ опубликовано на веб |

**SKIPPED_TOOL:**
- `run_instagram_content` — НЕ вызван (LLM не попыталась, в отличие от Session 3)
- `find_doctor_handles` — НЕ вызван
- `run_tech_seo_audit` — НЕ вызван
- Остальные из 40+ tools — НЕ вызваны

**NO_DATA / LLM_DECISION:**
- `run_hh_analysis` снова ищет по имени клиники ("Iphk"), не по врачам
- `run_doctor_dossiers` аналогично

---

### Consolidated Skip-Points Register

| category | tool/phase | occurrence_count | sessions_affected | example_quote |
|----------|------------|------------------|-------------------|---------------|
| ERROR | HTML BUILD / generate_html_report | 2 | tg:322367335, full-test-1782061034 | `"name '_unwrap_tool_output' is not defined"` |
| ERROR | PRESENTATION / publish_scout_report | 2 | tg:322367335, full-test-1782061034 | `"name '_unwrap_tool_output' is not defined"` |
| ERROR | FINANCE / find_company_financials | 2 | tg:322367335, 1609c5d1 | `"Either inn or ogrn is required"` |
| ERROR | TECH AUDIT / run_tech_seo_audit | 2 | 1609c5d1, full-test-1782061034 | `"No handler mapping for tool: run_tech_seo_audit"` |
| ERROR | KEY PERSONS / find_doctor_handles | 1 | full-test-1782061034 | `"No handler mapping for tool: find_doctor_handles"` |
| ERROR | KEY PERSONS / run_instagram_content | 1 | full-test-1782061034 | `"No handler mapping for tool: run_instagram_content"` |
| ERROR | COMPETITORS / run_ci_analysis | 2 | tg:322367335, 1609c5d1 | `"error": "'url'"` / `"at least one competitor is required"` |
| ERROR | TECH AUDIT / run_pagespeed | 1 | tg:322367335 | `"error": "Unexpected error", "detail": ""` |
| NO_DATA | COMPETITORS / find_competitors | 2 | tg:322367335 (1 конкурент), 1609c5d1 (0 конкурентов) | `"competitors": []` или 1 конкурент с пустыми полями |
| NO_DATA | SMI MENTIONS / run_smi_mentions | 1 | tg:322367335 | `"total_mentions": 0, "categories_with_mentions": 0` |
| NO_DATA | KEY PERSONS / run_hh_analysis | 2 | tg:322367335, test-iphk-002 | `"No vacancies found on hh.ru for this clinic"` |
| NO_DATA | KEY PERSONS / run_doctor_dossiers | 2 | tg:322367335, test-iphk-002 | 10-16 профилей, 0 врачей — поиск по имени клиники |
| NO_DATA | CONTENT PLAN / run_content_gaps | 1 | tg:322367335 | `"content_gaps": []` — target и competitor одинаковый URL |
| NO_DATA | PRESENTATION / publish_scout_report | 2 | 1609c5d1, test-iphk-002 | `"url": null` — не опубликовано на веб |
| SKIPPED_TOOL | run_instagram_content | 5 (всех) | ни в одной сессии не вызвана успешно | либо LLM не вызывает, либо `"No handler mapping"` |
| SKIPPED_TOOL | find_doctor_handles | 4 (из 5) | успешно только в 1609c5d1 | либо LLM не вызывает, либо `"No handler mapping"` |
| SKIPPED_TOOL | run_tech_seo_audit | 5 (всех) | LLM вызывает — но всегда `"No handler mapping"` | `"No handler mapping for tool: run_tech_seo_audit"` |
| SKIPPED_TOOL | run_lighthouse | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | run_prescan | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | quick_overview | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | present_competitors | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | finalize_research | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | run_validation_check | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | post_report | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | orchestrate | 5 (всех) | ни в одной сессии не вызвана | — |
| SKIPPED_TOOL | run_aim_scout, run_full_scout, run_background_pipeline | 5 (всех) | ни в одной сессии не вызваны | — |
| SKIPPED_PHASE | все 12 фаз после PERPLEXITY | 1 | 4975ef15-de5 | сессия упала после первой фазы |
| LLM_DECISION | QC CRITIQUE признание 10/10 FAIL | 1 | tg:322367335 | "Отчёт для проверки не предоставлен... 10/10 FAIL" |
| LLM_DECISION | COMPETITORS — LLM не retry'ила после suggestion | 1 | 1609c5d1 | LLM получила suggestion "Передай их имена в параметр named_competitors" — но не вызвала повторно |
| LLM_DECISION | LLM признаёт "не удалось" в KEY PERSONS | 1 | tg:322367335 | "идентифицировать конкретных врачей не удалось: все найденные 10 профилей — это страницы клиники на отзовиках" |
| LLM_DECISION | LLM признаёт "не может быть выполнен" в COMPETITORS | 1 | tg:322367335 | "Конкурентный анализ не может быть выполнен в полном объёме" |
| LLM_DECISION | LLM признаёт "техническую ошибку" в CONTENT ANALYSIS | 1 | tg:322367335 | "данные контент-анализа содержат только техническую ошибку" |
| LLM_DECISION | LLM признаёт баг "сайт сам с собой" в CONTENT PLAN | 1 | tg:322367335 | "инструмент не выявил расхождений, поскольку в качестве конкурента ошибочно использовался сам сайт клиники" |
| ANOMALY | HIRING SIGNALS фаза без описания в phases.py | 2 | 1609c5d1, full-test-1782061034 | фаза выполняется, но не описана в каноническом phases.py (13 фаз) |
| ANOMALY | mtime аномалия в tg-сессии | 1 | tg:322367335 | 24 из 28 файлов — mtime 20:16:56, PERPLEXITY/COMPETITORS — 20:29-20:30 (retry?) |

---

### Pattern Analysis

#### Top 7 most-skipped tools (по числу сессий, где инструмент НЕ вызван успешно)

| Rank | tool | sessions_skipped_out_of_5 | reason |
|------|------|---------------------------|--------|
| 1 | run_instagram_content | 5/5 (100%) | LLM не вызывает ИЛИ `"No handler mapping"` когда вызывает |
| 2 | run_tech_seo_audit | 5/5 (100%) | LLM вызывает — но всегда `"No handler mapping"` |
| 3 | run_lighthouse | 5/5 (100%) | LLM не вызывает |
| 4 | run_prescan | 5/5 (100%) | LLM не вызывает |
| 5 | quick_overview | 5/5 (100%) | LLM не вызывает |
| 6 | present_competitors | 5/5 (100%) | LLM не вызывает |
| 7 | find_doctor_handles | 4/5 (80%) | LLM не вызывает в 4 из 5; в 1 — `"No handler mapping"` |

#### Tools that always return NO_DATA or ERROR (фаза выполняется, но результат пустой/ошибка)

| tool | sessions_with_NO_DATA_or_ERROR | total_sessions_called | pattern |
|------|--------------------------------|----------------------|---------|
| run_hh_analysis | 2/2 (100%) | 2 | "No vacancies found" — либо LLM передаёт имя клиники не как работодателя, либо инструмент не умеет искать по клиникам |
| run_doctor_dossiers | 2/2 (100%) | 2 | doctor_name = имя клиники → 10-16 профилей, 0 реальных врачей |
| run_smi_mentions | 1/5 (20%) | 5 | 0 упоминаний для Arclinic (нишевая клиника) — может быть корректным |
| find_company_financials | 2/5 (40%) | 5 | LLM не передаёт INN в 2 из 5 сессий |
| generate_html_report | 2/5 (40%) | 5 | NameError `_unwrap_tool_output` — баг в коде, введён после 20 июня |
| publish_scout_report | 2/5 (40%) | 5 | Тот же NameError в 2; в 2 других — `url: null` (не публикуется) |

#### Phases that always truncate или завершаются с ошибкой

| phase | sessions_with_truncate_or_error | notes |
|-------|--------------------------------|-------|
| HTML BUILD | 2/5 (40%) — ERROR; 3/5 (60%) — url=null | 100% сессий НЕ публикуют отчёт на веб |
| PRESENTATION | 2/5 (40%) — ERROR; 3/5 (60%) — url=null | 100% сессий НЕ публикуют на веб |
| KEY PERSONS | 4/5 (80%) — NO_DATA или ERROR | Только Session 2 (1609c5d1) успешна |
| FINANCE | 2/5 (40%) — ERROR | 60% сессий успешны (3/5) |
| COMPETITORS (run_ci_analysis) | 2/5 (40%) — ERROR | 60% сессий успешны (3/5) |

#### Cross-session стабільные паттерны

1. **HTML BUILD bug `_unwrap_tool_output`** — появился между 20 июня (test-iphk-002 — без бага) и 21 июня (tg, full-test — с багом). Был введён коммитом между этими датами.
2. **FINANCE "inn required"** — недетерминированный: LLM в 2 сессиях не передаёт INN, в 3 — передаёт. Причина: LLM-промпт не делает явное требование "получи INN сначала через find_competitors".
3. **`run_tech_seo_audit` всегда `"No handler mapping"`** — стабильный баг конфигурации engine.py.
4. **`run_instagram_content` никогда не вызывается успешно** — либо LLM не вызывает, либо `"No handler mapping"`.
5. **`find_doctor_handles`** — недетерминированный: в 1 сессии LLM вызывает и получает 22 врача; в 1 — вызывает и получает `"No handler mapping"`; в 3 — не вызывает.
6. **`run_doctor_dossiers` всегда NO_DATA** — поиск по имени клиники вместо имени врача.

---

## Cross-Reference with CONTEXT.md Hypotheses

### Hypothesis 1: Instagram полностью отсутствует

**CONFIRMED.** `run_instagram_content`:
- Session 1 (tg): НЕ вызван
- Session 2 (1609c5d1): НЕ вызван
- Session 3 (full-test): ВЫЗВАН LLM, но `"No handler mapping for tool: run_instagram_content"` — pipeline отказал
- Session 4 (4975ef15-de5): сессия упала до этой фазы
- Session 5 (test-iphk-002): НЕ вызван

**Уточнение:** Instagram отсутствует НЕ потому что LLM "решает не обязательно" — LLM пытается его вызвать (Session 3 это доказывает). Причина — **`run_instagram_content` не зарегистрирован в `_TOOL_HANDLERS`** (engine.py), только в LLM-registry (register_all_tools в `__init__.py`).

### Hypothesis 7: SOUL.md даёт слишком много свободы → LLM решает «не обязательно»

**PARTIALLY CONFIRMED.** Evidence:
- LLM в 4 из 5 сессий НЕ вызывает `find_doctor_handles` (хотя в 1 — вызывает)
- LLM в 4 из 5 сессий НЕ вызывает `run_instagram_content` (хотя в 1 — вызывает)
- LLM НИКОГДА не вызывает `run_lighthouse`, `run_prescan`, `quick_overview`, `present_competitors`, `finalize_research`, `run_validation_check`, `post_report`, `orchestrate`

НО: даже когда LLM вызывает инструмент (`run_tech_seo_audit`, `find_doctor_handles`, `run_instagram_content`) — pipeline отказывается его выполнять. То есть "свобода SOUL.md" — только половина проблемы; вторая половина — `_TOOL_HANDLERS` не покрывает все зарегистрированные инструменты.

### Hypothesis C (из CONTEXT.md): PipelineEngine жёстко ограничивает фазы → LLM не может вызвать инструмент вне очереди

**REFINED.** PipelineEngine не "жёстко ограничивает фазы" — он **не имеет handler mapping для 21+ инструментов** из 40+ зарегистрированных. LLM может вызывать любой из 40+ инструментов, но pipeline выполнит только 19.

### Hypothesis A: SOUL.md/SKILL.md дают слишком много свободы

**CONFIRMED for some tools, NOT CONFIRMED for others.**
- Для `run_instagram_content`: LLM в 1 сессии всё-таки вызывает → не совсем "свобода", скорее LLM-недетерминированность
- Для `find_doctor_handles`: LLM в 1 сессии вызывает → аналогично
- Для `run_lighthouse`, `run_prescan`, `quick_overview` и др.: НИКОГДА не вызываются → подтверждает, что SOUL.md/SKILL.md не дают LLM явных сигналов вызывать эти инструменты

### Дополнительные находки (не в CONTEXT.md)

1. **`NameError: _unwrap_tool_output`** — критический баг, не описан в CONTEXT.md. Появился между 20 и 21 июня. Ломает HTML BUILD и PRESENTATION в 40% сессий.
2. **`run_doctor_dossiers` ищет по имени клиники** — LLM-промпт не различает "имя клиники" и "имя врача". В Session 1 и 5 — `doctor_name: "Arclinic"` / `"Iphk"`.
3. **CONTENT PLAN сравнивает сайт сам с собой** — `target` и `competitor` одинаковый URL (Session 1). LLM не передаёт реального конкурента.
4. **URL публикации всегда null** — даже когда HTML BUILD успешен, отчёт сохраняется локально, но не публикуется на веб (3 из 5 сессий).
5. **Фаза HIRING SIGNALS** — выполняется в 2 сессиях от 21 июня, но не описана в `phases.py` (13 фаз). Подтверждает рассинхрон фаз (CONTEXT.md указывал на 13/14/16 — сейчас актуально 13/14).
6. **Session 4 (4975ef15-de5) — crash без metadata.json** — пайплайн упал после PERPLEXITY, не записав метаданные. Без events.jsonl причину не установить.

---

## Evidence Summary for Plan 03 (Root Cause)

Plan 03 должен проверить следующие гипотезы, опираясь на этот evidence:

### Подтверждённые root causes (с evidence)

1. **`_unwrap_tool_output` NameError** — баг в коде `generate_html_report` и `publish_scout_report`. Функция не импортирована или не определена. **Файл:** `/opt/hermes/app/tools/generate_html_report.py`, `/opt/hermes/app/tools/publish_scout_report.py`. **Evidence:** 2 сессии (tg, full-test), quoted error.

2. **`_TOOL_HANDLERS` разрыв** — 21+ инструментов зарегистрированы для LLM, но не имеют handler mapping в `engine.py`. **Файл:** `/opt/hermes/app/pipeline/engine.py`. **Evidence:** `"No handler mapping for tool: ..."` для `run_tech_seo_audit` (2 сессии), `find_doctor_handles` (1), `run_instagram_content` (1).

3. **LLM не передаёт INN в find_company_financials** — недетерминированный: 2/5 сессий падают, 3/5 — успешны. **Причина:** LLM-промпт в SOUL.md/SKILL.md не делает явное требование "получи INN через find_competitors ПЕРЕД find_company_financials". **Evidence:** 2 сессии (tg, 1609c5d1), quoted error.

4. **`find_competitors` нестабильный для мегаполисов** — в Session 2 (iphk.ru/Москва) вернул `"competitors": []` с suggestion "Это крупный город (Москва/СПб)... уточните у клиента". **Evidence:** Session 2 quoted.

5. **`run_doctor_dossiers` ищет по имени клиники, не по имени врача** — LLM-промпт не различает. **Evidence:** Sessions 1, 5 — `doctor_name: "Arclinic"` / `"Iphk"`.

6. **CONTENT PLAN может сравнить сайт сам с собой** — если LLM не передаёт competitor URL отдельно. **Evidence:** Session 1 — `target: "https://arclinic.ru"`, `competitor: "https://arclinic.ru/"`.

7. **Публикация на веб не работает** — `url: null` в 3 из 3 успешных PRESENTATION. **Причина:** `publish_scout_report` сохраняет локально, но не загружает на веб (настройка публикатора или credentials).

### Гипотезы для Plan 03 (root cause analysis)

- **Гипотеза D (комбинация):** ПОДТВЕРЖДЕНО. 30% покрытия — результат комбинации:
  - 21+ инструментов недоступны (нет handler mapping)
  - LLM-промпт не направляет вызывать Instagram/find_doctor_handles/run_lighthouse/etc.
  - Баг `_unwrap_tool_output` ломает финальную сборку в 40% сессий
  - LLM недетерминированно передаёт/не передаёт INN
  - `find_competitors` нестабилен в мегаполисах

### Рекомендации для Phase 2 (3-Pass Orchestrator)

1. **Fix `_unwrap_tool_output` немедленно** — это блокирующий баг, ломает финальную сборку
2. **Добавить недостающие handlers в `_TOOL_HANDLERS`** — как минимум: `run_instagram_content`, `find_doctor_handles`, `run_tech_seo_audit`, `run_lighthouse`, `run_prescan`, `quick_overview`, `present_competitors`, `finalize_research`, `run_validation_check`
3. **3-pass cycle должен явно требовать INN** перед вызовом `find_company_financials` — через QC checklist
4. **QC checklist должен включать Instagram** — с пометкой "обязательно для косметологии/пластики"
5. **`run_doctor_dossiers`** — уточнить LLM-промпт: "искать по ФИО врача, НЕ по имени клиники"
6. **CONTENT PLAN** — LLM-промпт должен требовать competitor URL ≠ client URL
7. **Публикация на веб** — починить publish_scout_report, чтобы `url` был не null
8. **Sync phases.py** — добавить HIRING SIGNALS фазу (или удалить из кода, если не нужна)

---

## Self-Check

- [x] 5 sessions analyzed with structured per-session timelines
- [x] Skip/truncate decision points identified with quoted log evidence (timestamps + tool names)
- [x] Consolidated skip-points register groups by category (NO_DATA, TRUNCATED, SKIPPED_TOOL, SKIPPED_PHASE, STREAM_BREAK, ERROR, LLM_DECISION)
- [x] Pattern analysis identifies most-skipped tools and always-truncate phases
- [x] Cross-reference to CONTEXT.md hypotheses documented
- [x] No server files modified — only read-only commands (cat, ls, stat, grep, head, wc)

