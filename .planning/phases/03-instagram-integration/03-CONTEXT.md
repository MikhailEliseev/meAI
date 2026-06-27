# Phase 3: Instagram Integration - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Доставить Instagram-анализ для ниш, где он критичен (косметология, пластическая хирургия), с метриками по каждому топ-5 врачу: подписчики, avg лайки, avg просмотры, стиль контента, темы в %, пробелы, потенциал — соответствующими секциям 03 (Experts) и 04 (Content Analysis) референса `ИПХиК (2).html`.

**Внутри scope:**
- Niche detection (является ли клиника Instagram-critical)
- Обязательный Instagram-анализ для critical niche
- Doctor discovery flow (find_doctor_handles + batch Instagram)
- Обработка «нет Instagram» (данные недоступны / handle не найден / приватный профиль)
- Деплой v2 (Perplexity) в контейнер через `docker cp`
- Подключение `run_instagram_content` + `find_doctor_handles` к `engine.py:_TOOL_HANDLERS`

**Вне scope:**
- Адаптация Instagram-инструмента под новые источники данных (Perplexity/DeepSeek уже работает — Plan 01-04 верифицировал)
- Добавление Instagram для non-critical ниш (только optional)
- Instagram Hashtag Analysis (новый инструмент — backlog)
- Instagram Ads Analysis (новый инструмент — backlog)

</domain>

<decisions>
## Implementation Decisions

### Niche Detection

- **D-01:** LLM сама определяет нишу по контексту сайта (через `quick_overview` данные в Pass 1), не используется keyword-list или ОКВЭД.
- **D-02:** Реализация — отдельный мини-LLM-call между Pass 1 (Collect) и Pass 2 (Gap-analyze). Короткий boolean ответ: `instagram_critical: yes/no`. Стоимость: ~5с API time.
- **D-03:** Boundary rule: Instagram-critical = TRUE только если косметология/пластика — **основной профиль** клиники (>50% услуг или заявлен как главный). Если это доп. услуги — niche=non-critical (стоматология с эстетическими процедурами не запускает).

### Mandatory Mechanism

- **D-04:** Многоуровневое принуждение: (1) Pass 1 prompt содержит явное правило «если niche=critical → ОБЯЗАТЕЛЬНО вызови run_instagram_content»; (2) QC gate hard FAIL между Pass 2 и Pass 3, если niche=critical и Instagram не вызван.
- **D-05:** QC gate поведение: hard FAIL — coverage=FAIL даже при 14/15 заполненных пунктах, если Instagram пропущен для critical niche. Pass 3 обязательно пытается добрать.
- **D-06:** Если Instagram вызван, но Perplexity вернул «no data» (handle не в индексе) — LLM должна retry через `find_doctor_handles` с альтернативными handles. Если все retry не дали данных — QC item=filled с reason «handle не найден в Perplexity index, данные недоступны».

### "Нет Instagram" Handling

- **D-07:** В HTML рендерится отдельный блок в секциях 03+04: «Instagram: данные недоступны — {reason}». Причина выбирается из 4 вариантов: «нет аккаунта» / «handle не найден» / «приватный профиль» / «Perplexity outside index». Честно и прозрачно для клиента.
- **D-08:** QC item условный (conditional): если niche=non-critical → status=`not_applicable`, считается как 0 (total=14 вместо 15, не влияет на coverage %). Если niche=critical и данных нет после всех retry → status=`missing` с reason.

### Doctor Discovery Flow

- **D-09:** `find_doctor_handles` — основной источник handles. Скрейпит сайт клиники (staff/doctors pages), возвращает Instagram handles. LLM в Pass 1 вызывает его сразу после `quick_overview`. Handles идут в `run_instagram_content`.
- **D-10:** Adaptive top-5 selection: `find_doctor_handles` возвращает top-N (N=8-10) по позиции на сайте (как клиника себя представляет — обычно титулованные/главные впереди). Если все top-5 сайта оказались без Instagram (профессора без соцсетей) — fallback: LLM mini-call переупорядочивает по `followers_count` (кто реально ведёт соцсети) и берёт top-5 Instagram-active врачей.
- **D-11:** Batch size: один batch-call `run_instagram_content` с топ-8-10 handles (вместо 5). Цель — покрыть «профессоров» (которые могут оказаться вне Instagram) и сохранить реальный top-5 по followers для секции 04. Стоимость: ~90-300с на batch.

### Deployment

- **D-12:** Деплой через `docker cp` локального v2 (`AIM/hermes/app/tools/run_instagram_content.py`, 718 строк) в контейнер `aim-hermes:/opt/hermes/app/tools/`. Перезапуск gateway (не контейнера). Никаких изменений в образе.
- **D-13:** Добавить две строки в `engine.py:_TOOL_HANDLERS`:
  ```python
  "run_instagram_content": ("app.tools.run_instagram_content", "handle_run_instagram_content"),
  "find_doctor_handles": ("app.tools.find_doctor_handles", "handle_find_doctor_handles"),
  ```
  PipelineEngine fallback path (ORC-05) тоже сможет вызывать эти инструменты.

### Claude's Discretion

- Точная формулировка prompt для mini-call niche detection (boolean да/но)
- Структура HTML-блока «Instagram: данные недоступны» (какие классы design-system использовать)
- Порядок вызовов в Pass 1 (find_doctor_handles до или после run_instagram_content)
- Реализация adaptive top-5 fallback (как именно LLM переупорядочивает)

### Folded Todos

(нет — cross-reference todos не производился)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Research (Instagram findings)
- `.planning/phases/01-research-diagnosis/RESEARCH.md` §4 — Instagram Tool Test findings (v1 broken, v2 working, deploy plan)
- `.planning/phases/01-research-diagnosis/evidence/instagram-tool-test.md` — полное evidence: v1 bug, v2 data shape, field mapping 9.5/10

### Phase 2 Architecture (3-pass orchestrator)
- `.planning/phases/02-3-pass-orchestrator-coverage-checklist/02-VERIFICATION.md` — orchestrator wiring, QC checklist (15 items, item 5 = Instagram), soft QC gate behavior
- `AIM/hermes/app/orchestrator/three_pass.py` — run_three_pass entry point, between-pass hooks
- `AIM/hermes/app/orchestrator/pass_collect.py` — Pass 1 prompt structure (где вставлять Instagram-mandatory правило)
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py` — Pass 2 QC checklist prompt (где вставлять hard FAIL Instagram rule)
- `AIM/hermes/app/orchestrator/qc_checklist.py` — 15-item QC_CHECKLIST (item 5 = Instagram, нужно делать conditional)

### Instagram Tool Implementation
- `AIM/hermes/app/tools/run_instagram_content.py` (718 строк) — v2, Perplexity, БЕЗ изменений (drop-in replacement)
- `AIM/hermes/app/tools/find_doctor_handles.py` (1205 строк) — doctor discovery tool
- `AIM/hermes/app/pipeline/engine.py:_TOOL_HANDLERS` — словарь 22 entries (нужно +2 для Instagram tools)

### Reference HTML Report
- `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html` — canonical design-system (для HTML блока «нет Instagram»)

### Project-Level
- `.planning/PROJECT.md` — Core value, constraints (DeepSeek ~120s, docker cp only)
- `.planning/REQUIREMENTS.md` §Instagram (IG-01..04) — Phase 3 requirements с критериями успеха

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_instagram_content.py` v2 (718 строк) — полностью готов, drop-in замена v1. Никаких изменений в код инструмента не нужно. Возвращает: profile, themes, formats, ER, gaps, recommendations (9.5/10 field coverage для секций 03+04).
- `find_doctor_handles.py` (1205 строк) — скрейпит сайты клиник для doctor discovery. Готов, в продакшене не подключён к `_TOOL_HANDLERS`.
- `app/orchestrator/three_pass.py` (161 строка) — 3-pass цикл. Есть хук между Pass 1 и Pass 2 для mini-call niche detection.
- `app/orchestrator/qc_checklist.py` (193 строки) — 15-item QC_CHECKLIST. Item 5 = Instagram. Нужно добавить `applicable_fn` или `conditional_on_niche` логику для D-08.
- `app/tools/generate_html_report.py` — HTML reporter в design-system AIM. `_build_qc_coverage_section` уже рендерит «данные недоступны» markers для missing items — можно повторить паттерн для Instagram section.

### Established Patterns
- **Orchestrator-first:** LLM вызывает инструменты напрямую через registry (49 tools), `_TOOL_HANDLERS` — fallback для PipelineEngine. Подключение Instagram tools к `_TOOL_HANDLERS` не блокирует orchestrator, но включает fallback path.
- **Soft QC gate:** Phase 2 использует warning-only QC gate между Pass 2 и Pass 3. Phase 3 вводит **hard FAIL** для critical Instagram item (новый паттерн — компромисс: мягкость для остальных 14 items, жёсткость для Instagram-critical).
- **Mini-call pattern:** Между проходами — короткие LLM-вызовы для извлечения boolean/structured данных (новый паттерн для Phase 3, ранее не использовался в orchestrator).
- **Honest reporting:** «данные недоступны: {reason}» вместо прочерков — established pattern из Phase 2 ORC-04.

### Integration Points
- `app/orchestrator/three_pass.py:82` — после `run_pass_collect`, перед `run_pass_gap_analyze` — вставка mini-call niche detection.
- `app/orchestrator/pass_collect.py` — prompt augmentation с Instagram-mandatory правилом для critical niche.
- `app/orchestrator/pass_gap_analyze.py` — prompt augmentation с Instagram hard-FAIL правилом.
- `app/orchestrator/qc_checklist.py:QC_CHECKLIST[4]` (item 5 Instagram) — добавить `conditional_on_niche` flag.
- `app/pipeline/engine.py:_TOOL_HANDLERS` — 2 новые entry (run_instagram_content + find_doctor_handles).
- `app/tools/generate_html_report.py` — `_build_no_instagram_block(reason)` новый helper или inline render.

</code_context>

<specifics>
## Specific Ideas

- **Профессора без Instagram — нормально.** Пользователь явно обозначил: топ-5 по позиции сайта часто = титулованные эксперты (КМН, профессора), у которых нет соцсетей. Это естественная ситуация для клиник — мы не penalize, а показываем честно «регалии на сайте, Instagram отсутствует». Поэтому выборка Instagram-active врачей может отличаться от top-5 экспертов клиники.
- **Adaptive fallback**: если все top-5 по сайту без IG — переупорядочиваем по followers_count из batch-результатов, выбираем top-5 Instagram-active. Это даёт реальное покрытие для секции Content Analysis.
- **Batch of 8-10**: вместо 5 — покрыть обе выборки (эксперты + Instagram-active) одним batch-call. ~90-300с на batch в Perplexity (по наблюдениям Plan 01-04).

</specifics>

<deferred>
## Deferred Ideas

- **Instagram Hashtag Analysis** (новый инструмент, отдельная секция) — backlog, Phase 9+
- **Instagram Ads Analysis** (расходы на продвижение постов врачей) — backlog, Phase 9+
- **Reels Performance Analysis** (отдельный анализ Reels vs Posts) — backlog, Phase 9+
- **TikTok/YouTube Doctors Analysis** — другой домен, не Phase 3 scope
- **Instagram API integration (официальный)** — сейчас Perplexity (web search), можно later через Instagram Graph API. Требует Business Account клиники.
- **Auto-discovery doctor names через content_analysis**: мы выбрали find_doctor_handles как primary, но если handle не найден — content_analysis упоминает врачей по имени. Можно в future добавить web_search "{doctor name} {clinic} instagram".

</deferred>

---

*Phase: 3-Instagram Integration*
*Context gathered: 2026-06-23*
