---
phase: 4
plan: 04-07
subsystem: hermes-tools/html-reporter
tags: [html, report, llm-sections, strategy, offer, whitefields, experts, content-analysis, fears, sec-01, sec-02, sec-03, sec-04, sec-05, d-01, d-02, d-03, d-04, d-05, d-06, d-07, d-08, d-09, d-10, d-11]

# Dependency graph
requires:
  - "04-02: find_doctor_handles structured_regalia + _merge_doctor_data (provides experts_data shape)"
  - "04-03: run_forum_pains patient_fears_hint (provides content_data.patient_fears)"
  - "04-05: Pass 3 prompt items 7-11 (instructs LLM to pass 5 new kwargs)"
  - "04-06: generate_html_report.py structure + patterns (_build_*_section, _build_report_html signature)"
provides:
  - "5 new HTML section builders in generate_html_report.py"
  - "_build_strategy_section — SEC-01/D-01..03 (5 LLM-generated Strategy directions)"
  - "_build_offer_section — SEC-02/D-04 (Offer steps + CTA)"
  - "_build_whitefields_matrix — SEC-03/D-05..07 (4×4 comparison table, client column highlighted)"
  - "_build_experts_with_regalia — SEC-04/D-08..09 (experts + structured регалии + Instagram metrics)"
  - "_build_content_analysis_with_fears — SEC-05/D-10..11 (per-doctor analysis + top-5 patient fears)"
  - "_build_report_html signature extended with 5 new kwargs: strategy_data, offer_data, whitefields_data, experts_data, content_data"
  - "handle_generate_html_report extracts + passes all 5 new kwargs"
affects:
  - "04-08 (deploy — generate_html_report.py ships via docker cp, 2890 lines total)"
  - "Pass 3 LLM (consumes all 5 new sections via kwargs per Plan 04-05 contract)"
  - "Future reports — all reference HTML sections now renderable (matches 10-section reference)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LLM-content rendering layer — sections render dicts/lists the LLM assembles per Plan 04-05 prompt items 7-11"
    - "D-02 fixed-frame Strategy — 5 direction names are canonical (Контент/Telegram/GEO/Репутация/Кросс-промо); icons map from name"
    - "D-06 honest <3-competitor note — renders when columns_count < 4 (not silently omitted)"
    - "D-09 source-variant rendering — experts_data source field (both/site/instagram_only) drives conditional blocks"
    - "instagram_only always shows note — per plan, note appears even when IG metrics are present (explains absent регалии)"
    - "Top-N list slicing — experts limited to 5, fears limited to 5, themes limited to 5 (DoS mitigation T-04-07-D)"
    - "Empty-string graceful degradation — new sections return '' when data absent (backward compatible)"
    - "XSS-safe via _esc() — all LLM-generated text escaped"
    - "Inline CSS in style attributes — self-contained, no external CSS dependency"
    - "data-aim attribute on each new section for integration testability"

key-files:
  created: []
  modified:
    - AIM/hermes/app/tools/generate_html_report.py (+683 lines — 2207 → 2890, +31% size)

key-decisions:
  - "Each LLM-section builder is a pure function — takes a dict/list, returns HTML string. Same pattern as Plan 04-06 data-section builders"
  - "Empty string on missing data (not exception) — _build_report_html uses `if html: sections.append(html)` pattern"
  - "Strategy direction icons hardcoded by name (D-02 fixed frame): Контент→📝, Telegram→📱, GEO→📍, Репутация→⭐, Кросс-промо→🤝, unknown→💡"
  - "Whitefields client column styled with golden border (border-left/right) + tinted background — visually distinct from competitor columns"
  - "Whitefields matrix uses overflow-x:auto — responsive horizontal scroll on mobile without breaking table structure"
  - "Experts + Content enhanced sections placed BEFORE Whitefields/Strategy/Offer — matches reference order (03 Experts → 04 Content → 07 Whitefields → 09 Strategy → 10 Offer)"
  - "Existing Phase 3 Experts (Key Doctors) + Content Analysis sections still render — new enhanced sections AUGMENT, do not REPLACE (per plan: 'REPLACE or AUGMENT' — chose AUGMENT for safety)"
  - "For source='instagram_only' WITH ig_metrics: append 'Регалии недоступны' note AFTER IG metrics block (not as elif). This ensures the note always appears for instagram_only source, explaining why no регалии badges"
  - "Degree class mapping: ДМН→metric-tag-success (higher rank), КМН→metric-tag-info. Title: профессор/академик→success, доцент/other→info"
  - "Education list sliced to top 3 items — avoids badge clutter when education array is long"
  - "Patient fears total_reviews defaults to 'собранных' when 0/missing — preserves grammatical correctness of Russian blockquote"

patterns-established:
  - "Pattern: LLM-content section builders — dict/list → HTML with _esc on all LLM-generated text"
  - "Pattern: source-variant conditional rendering — single source field drives multiple display variants"
  - "Pattern: D-06 honest note for partial data — explicit note when structural minimum not met"
  - "Pattern: fixed-frame + LLM-content hybrid — D-02 Strategy has fixed direction NAMES but LLM-generated CONTENT per direction"
  - "Pattern: section ordering follows reference HTML (ИПХиК (2).html) — 03/04/07/09/10 in code assembly order"

requirements-completed: [SEC-01, SEC-02, SEC-03, SEC-04, SEC-05]

# Metrics
duration: 13min
started: 2026-06-24T01:02:37Z
completed: 2026-06-24T01:16:22Z
tasks: 3
files_modified: 1
lines_added: 683
commits:
  - "c50f5a7: feat(04-07): add Strategy + Offer HTML sections (SEC-01, SEC-02)"
  - "44cfc6b: feat(04-07): add Whitefields 4×4 comparison matrix HTML section (SEC-03)"
  - "d339468: feat(04-07): add Experts+регалии + Content+fears HTML sections (SEC-04, SEC-05)"
---

# Phase 4 Plan 04-07: HTML LLM Sections Summary

**5 new LLM-content HTML section renderers added to `generate_html_report.py` (+683 lines, 2207→2890 total): Strategy with 5 LLM-generated directions (SEC-01/D-02 fixed frame), Offer with steps + CTA (SEC-02), Whitefields 4×4 matrix with client column highlighted (SEC-03/D-05..07), Experts with structured регалии + Instagram metrics handling 3 source variants (SEC-04/D-08..09), and Content Analysis with per-doctor themes + top-5 patient fears with mention counts (SEC-05/D-10..11). All sections gracefully degrade to empty string/honest blocks; XSS-safe via `_esc()`; positioned per reference report order (03/04/07/09/10).**

## Performance

- **Duration:** ~13 min (PLAN_START 01:02:37Z → PLAN_END 01:16:22Z, 824s)
- **Started:** 2026-06-24T01:02:37Z
- **Completed:** 2026-06-24T01:16:22Z
- **Tasks:** 3 (Task 1: Strategy+Offer; Task 2: Whitefields; Task 3: Experts+Content)
- **Files modified:** 1 (`generate_html_report.py`)
- **Lines added:** 683 (2207 → 2890, +31%)
- **Commits:** 3 (atomic per task)

## What Was Built

### 5 new section builders in `AIM/hermes/app/tools/generate_html_report.py`

#### 1. `_build_strategy_section(strategy_data: dict | None) -> str` (SEC-01, D-01..03)

Renders the Strategy section with 5 LLM-generated directions. Per D-02, the 5 direction names are FIXED as the frame (Контент, Telegram, GEO, Репутация, Кросс-промо), but each direction's CONTENT is LLM-generated for the specific clinic.

- Direction icons mapped from name: Контент→📝, Telegram→📱, GEO→📍, Репутация→⭐, Кросс-промо→🤝, unknown→💡
- Each direction renders: name + icon, basis (per D-03: конкуренты/content_gaps/страхи/reputation), ordered list of steps, expected_impact as metric-tag
- D-02 strict 5-direction limit (`directions[:5]`)
- Honest block "Стратегия не сгенерирована — недостаточно данных" when directions list is empty
- Empty string when strategy_data is None (section not rendered)

#### 2. `_build_offer_section(offer_data: dict | None) -> str` (SEC-02, D-04)

Renders the "Что AIM может сделать для клиники" section with LLM-generated offer steps + prominent CTA block.

- Each step renders: service name, description, timeline as metric-tag (⏱ prefix)
- CTA rendered in highlighted accent-colored box with larger font
- Per D-04: follows same LLM-generation pattern as Strategy — concrete steps + CTA from collected data
- Honest block when steps list empty; empty string when offer_data None

#### 3. `_build_whitefields_matrix(whitefields_data: dict | None) -> str` (SEC-03, D-05..07)

Renders the 4×4 comparison matrix as an HTML `<table>`.

- D-05: 4 categories (Услуги/Цены/Врачи/Digital presence) × 4 columns (client + 3 competitors)
- Client column styled with golden border (`border-left/right: 2px solid var(--accent)`) + tinted background
- Category cells styled with uppercase + small font (visually distinct from data cells)
- D-06: honest "Менее 3 конкурентов найдено — матрица неполная" note when columns_count < 4
- D-07: cells filled from already-collected data (no extra API calls); missing cells show "—"
- Responsive: `overflow-x: auto` on container for mobile horizontal scroll
- Cell key format: `"{category}_{col_index}"` (e.g., "Услуги_0" for client column)

#### 4. `_build_experts_with_regalia(experts_data: list | None) -> str` (SEC-04, D-08..09)

Renders enhanced Experts section with structured регалии + Instagram metrics, handling 3 source variants per D-09 merge logic.

- **Регалии badges (D-08):**
  - Degree: ДМН → `metric-tag-success` (higher rank), КМН → `metric-tag-info`
  - Title: профессор/академик → `metric-tag-success`, доцент/other → `metric-tag-info`
  - Experience: `Стаж N лет` as `metric-tag-info`
  - Education: rendered as text line (top 3 items to avoid clutter)
- **Instagram metrics (D-09):** followers/avg_likes/avg_views as metric grid + content_style as text
- **Source variants:**
  - `both` — renders регалии + IG metrics (no note)
  - `site` — renders регалии + "Instagram не обнаружен" note
  - `instagram_only` — renders IG metrics + "Регалии недоступны — врач не на сайте клиники" note (ALWAYS shown for this source, even when IG metrics present)
- Top-5 expert limit (`experts_data[:5]`) — DoS mitigation per T-04-07-D
- Source indicator at card bottom: "Источник: Сайт + Instagram" / "Только сайт клиники" / "Только Instagram"

#### 5. `_build_content_analysis_with_fears(content_data: dict | None) -> str` (SEC-05, D-10..11)

Renders per-doctor Instagram content analysis + top-5 patient fears in a single combined section.

- **Part 1 — Per-doctor analysis:** name, style, themes (as `metric-tag-info` badges with %), gaps (comma-separated), potential
- **Part 2 — Top-5 patient fears (D-10, D-11):**
  - Each fear rendered with `metric-tag-warning` badge showing mention_count
  - Context text (optional) — explains mention count (e.g., "47 упоминаний из 120 отзывов")
  - Blockquote header: "На основе {total_reviews} отзывов с ПроДокторов, Otzovik, IRecommend, Woman.ru"
  - 🔥 emoji on header
  - Top-5 limit (`patient_fears[:5]`)
- Honest note when fears not collected: "Страхи пациентов не собраны — run_forum_pains не вызван или не дал данных"
- Section skips entirely when both lists empty (graceful degradation)

### Section ordering in `_build_report_html`

| Position | Section | Phase | Source |
|----------|---------|-------|--------|
| 1 | Hero | 2 | existing |
| 2 | Executive Summary + clinic_metrics (DAT-04) | 4 | Plan 04-06 |
| 3 | Revenue dynamics (DAT-01) | 4 | Plan 04-06 |
| 4 | Market Research | 2 | existing |
| 5 | Competitor Table | 1 | existing |
| 6 | CI Analysis (gaps/advantages) | 1 | existing |
| 7 | Competitor Cards (DAT-03) | 4 | Plan 04-06 |
| 8 | Key Doctors (Phase 3) | 1/3 | existing |
| 9 | Media URLs (DAT-02) | 4 | Plan 04-06 |
| 10 | PageSpeed | 1 | existing |
| 11 | SEO Audit | 1 | existing |
| 12 | Content Analysis (Phase 3) | 1/3 | existing |
| 13 | Reviews + Ratings (DAT-05) | 4 | Plan 04-06 |
| 14 | SMI Mentions | 1 | existing |
| 15 | Forum Pains | 1 | existing |
| 16 | Financial | 1 | existing |
| 17 | Instagram | 1 | existing |
| 18 | Executive Insights | 1 | existing |
| **19** | **Experts+регалии (SEC-04)** | **4** | **new** |
| **20** | **Content+страхи (SEC-05)** | **4** | **new** |
| **21** | **Whitefields matrix (SEC-03)** | **4** | **new** |
| **22** | **Strategy (SEC-01)** | **4** | **new** |
| **23** | **Offer (SEC-02)** | **4** | **new** |
| 24 | CTA | 2 | existing |
| 25 | Footer | 2 | existing |
| 26 | QC Coverage (optional) | 2 | existing |

**Note:** The 5 new LLM-sections are placed in the reference's logical order (03 Experts → 04 Content → 07 Whitefields → 09 Strategy → 10 Offer) but appear AFTER existing data sections and BEFORE CTA. This is an AUGMENTATION strategy: existing Phase 3 Experts/Content sections still render, and the new enhanced sections add depth below. This preserves backward compatibility and gives the reader both summary (existing) and detailed (new) views.

### `_build_report_html` signature evolution

```python
def _build_report_html(
    data: dict,
    title: str,
    coverage_metadata: dict | None = None,        # Phase 2
    niche: str = "unknown",                        # Phase 3
    instagram_data: dict | None = None,            # Phase 3
    strategy_data: dict | None = None,             # Phase 4 / Plan 04-07 Task 1 (SEC-01)
    offer_data: dict | None = None,                # Phase 4 / Plan 04-07 Task 1 (SEC-02)
    whitefields_data: dict | None = None,          # Phase 4 / Plan 04-07 Task 2 (SEC-03)
    experts_data: list | None = None,              # Phase 4 / Plan 04-07 Task 3 (SEC-04)
    content_data: dict | None = None,              # Phase 4 / Plan 04-07 Task 3 (SEC-05)
) -> str:
```

All 5 new kwargs default to None — backward compatible with all Phase 2/3 callers.

### `handle_generate_html_report` extraction

The handler was extended to extract all 5 new kwargs from `kwargs` dict (or from positional dict fallback when LLM passes a single args dict). All 5 kwargs are then passed through to `_build_report_html`. This wiring is essential for end-to-end functionality — without it, the LLM could pass the kwargs but they'd never reach the section builders (Rule 2 auto-add critical functionality).

## Task Commits

Each task committed atomically:

1. **Task 1:** `feat(04-07): add Strategy + Offer HTML sections (SEC-01, SEC-02)` — `c50f5a7` (+209 lines)
2. **Task 2:** `feat(04-07): add Whitefields 4×4 comparison matrix HTML section (SEC-03)` — `44cfc6b` (+151 lines)
3. **Task 3:** `feat(04-07): add Experts+регалии + Content+fears HTML sections (SEC-04, SEC-05)` — `d339468` (+330 lines)

## Verification Results

### Task 1 Verification (10 tests)

| Check | Result |
|-------|--------|
| AST parse: `generate_html_report.py` syntax valid | OK |
| Test 1: Strategy with 5 directions (D-02 frame) | OK |
| Test 2: Strategy None → empty string | OK |
| Test 3: Strategy empty dict graceful | OK |
| Test 4: Strategy empty directions honest block | OK |
| Test 5: Offer section with steps + CTA | OK |
| Test 6: Offer None → empty string | OK |
| Test 7: Offer empty steps honest block | OK |
| Test 8: Backward compat `_build_report_html({}, 'Test')` | OK |
| Test 9: Full report with strategy + offer — section ordering | OK |
| Test 10: XSS safety — HTML in direction name/steps/impact | OK |

### Task 2 Verification (7 tests)

| Check | Result |
|-------|--------|
| AST parse | OK |
| Test 1: Full 4×4 matrix with all 4 categories + 4 columns | OK |
| Test 2: None → empty string | OK |
| Test 3: D-06 honest note for <3 competitors | OK |
| Test 4: Empty categories → empty string | OK |
| Test 5: XSS safety on category/column/cell values | OK |
| Test 6: `_build_report_html` signature correct (8 params) | OK |
| Test 7: Section ordering Whitefields → Strategy → CTA | OK |

### Task 3 Verification (8 tests)

| Check | Result |
|-------|--------|
| AST parse | OK |
| Test 1: Experts with all 3 source variants (both/site/instagram_only) | OK |
| Test 2: instagram_only without IG metrics (just note) | OK |
| Test 3: Content analysis with fears + mention counts | OK |
| Test 4: None cases (both functions) | OK |
| Test 5: `_build_report_html` signature correct (10 params) | OK |
| Test 6: Full report section ordering (Experts → Content → Whitefields → Strategy → Offer → CTA) | OK |
| Test 7: Backward compat — no new sections without kwargs | OK |
| Test 8: XSS safety on expert names/regalia/fears | OK |

### Regression + Integration Tests

| Check | Result |
|-------|--------|
| All Plan 04-06 functions preserved | OK |
| All Phase 3 functions preserved | OK |
| All 5 Plan 04-07 functions present | OK |
| `_build_report_html` has 10 params | OK |
| `handle_generate_html_report` exists | OK |
| Full integration: 11 data-aim attributes in single HTML output | OK |
| Phase 3 Instagram no-data block still conditionally renders | OK |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical functionality] `handle_generate_html_report` not wiring new kwargs**

- **Found during:** Task 1 (applied to all 3 tasks)
- **Issue:** Plan only mentions modifying `_build_report_html` signature, but `handle_generate_html_report` (the actual LLM-callable entry point) also needs to extract the new kwargs from `**kwargs` and pass them through to `_build_report_html`. Without this wiring, LLM could pass `strategy_data="..."` but it would be silently dropped.
- **Fix:** Added kwargs extraction (`kwargs.get("strategy_data")`, etc.) for all 5 new kwargs in `handle_generate_html_report`, with positional-dict fallback (same pattern as existing `niche`/`instagram_data`). Then added all 5 kwargs to the `_build_report_html()` call inside the handler.
- **Files modified:** `AIM/hermes/app/tools/generate_html_report.py` (handler section)
- **Commits:** Applied in all 3 task commits (Task 1: strategy+offer, Task 2: +whitefields, Task 3: +experts+content)
- **Classification:** Rule 2 (auto-add missing critical functionality) — without this, the feature would not work end-to-end despite section builders being correct.

**2. [Rule 1 - Bug] `instagram_only` source note never shown when IG metrics present**

- **Found during:** Task 3 verification
- **Issue:** Initial conditional structure was `if ig_metrics: ... elif source == 'site': ... elif source == 'instagram_only': ...`. For `source='instagram_only'` WITH ig_metrics, the first branch triggered and the "Регалии недоступны" note was never shown — but per plan spec, the note should ALWAYS appear for instagram_only source (it explains why no регалии badges).
- **Fix:** Added post-conditional block: if `source == 'instagram_only'` AND ig_metrics present AND ig_block was rendered, append the "Регалии недоступны" note after the IG metrics. The original `elif source == 'instagram_only'` branch still handles the case where ig_metrics is None.
- **Files modified:** `AIM/hermes/app/tools/generate_html_report.py` (inside `_build_experts_with_regalia`)
- **Commit:** `d339468` (Task 3)
- **Classification:** Rule 1 (auto-fix bug) — logic error in conditional structure.

**Total deviations:** 2 (both auto-fixed inline, no checkpoint needed)

## Issues Encountered

- **Local-env limitation (not a bug):** Importing `generate_html_report` requires `tools.registry` from `hermes-agent` package, which isn't pip-installed locally (only inside Docker container). Same issue noted in Plan 04-03 and Plan 04-06 SUMMARYs. Worked around by stubbing `tools` and `app.tools.session_archive` modules + loading `generate_html_report` via `importlib.util.spec_from_file_location` directly from file path. Code follows production pattern; will resolve inside `aim-hermes` container.

## User Setup Required

None — pure Python code changes, no external services or environment variables. Deployment happens in Plan 04-08 (Wave 5).

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-04-07-X (XSS — untrusted LLM-generated text in strategy steps, fears, offer descriptions, matrix cells, expert names/регалии) | **mitigate** — every user-facing string wrapped in `_esc()`; verified with XSS test cases in all 3 tasks; URLs escaped in href attributes (none in this plan, but pattern preserved) |
| T-04-07-T (Tampering — LLM could inject `<script>` tags into Strategy/Offer/Whitefields content) | **mitigate** — `_esc()` converts `<`, `>`, `&`, `"` to HTML entities, preventing script injection even if LLM tries; verified with dedicated XSS tests |
| T-04-07-I (Info disclosure — LLM-generated content reveals competitive analysis) | **accept** — data already in LLM's Pass 1 history; rendering doesn't expose new data, just formats what LLM already produced |
| T-04-07-D (DoS — large strategy/fears/experts data → large HTML) | **mitigate** — top-N slicing: directions[:5] (D-02), experts[:5], fears[:5], themes[:5], education[:3], cards already limited to 10 in Plan 04-06 |
| T-04-07-E (EoP — not applicable) | **accept** — pure HTML string generation, no privilege change |
| T-04-07-SC (Supply chain — no new packages) | **accept** — pure Python stdlib + existing `_esc`/`_fmt_num`/`_fmt_revenue_short` helpers |

## Known Stubs

**None.** All 5 section builders contain real rendering logic — no hardcoded empty values flowing to UI, no placeholder text, no TODO/FIXME markers.

The intentionally defensive patterns are documented design decisions:
- Empty string on None (section not rendered — backward compatible)
- Honest "недостаточно данных" blocks on empty data (ORC-04 principle)
- "Страхи пациентов не собраны — run_forum_pains не вызван или не дал данных" (honest note when forum_pains tool wasn't called)

These have clear resolution paths via the Pass 3 LLM contract (Plan 04-05 items 7-11).

## Threat Surface Scan

**No new threat surface introduced.** The trust boundary is unchanged — the HTML reporter still produces a self-contained HTML page from session archive data + LLM-generated kwargs. The 5 new section builders read from LLM-populated data structures (no new external API calls, no new file access patterns, no new auth paths). XSS surface is mitigated by consistent `_esc()` usage verified in threat model compliance section above.

## Decisions Made

- **Augment vs Replace for Experts/Content sections:** Plan said "REPLACE or AUGMENT" — chose AUGMENT (existing Phase 3 sections still render, new enhanced sections add depth below). This is safer (backward compatible with Pass 3 LLM forgetting to populate new kwargs) and gives the reader both summary (existing) and detailed (new) views. Trade-off: slight HTML size increase.
- **Section positioning follows reference order (03/04/07/09/10):** Placed all 5 new sections in reference's logical order AFTER existing data sections, BEFORE CTA. This avoids disrupting the existing 18-section flow and groups all LLM-generated content together at the end (narrative flow: data → interpretations → recommendations).
- **Each section is a pure function:** Takes dict/list, returns HTML string. Same pattern as Phase 3 `_build_no_instagram_block` and Plan 04-06 data sections. Easy to unit-test, no side effects, no I/O.
- **Empty-string graceful degradation:** Sections return `""` when data is absent. `_build_report_html` uses `if html: sections.append(html)` pattern. This is critical for backward compatibility — Phase 3 sessions don't have the new kwargs and won't see broken/empty sections.
- **Inline CSS via `style` attributes:** Self-contained sections, no external CSS dependency. Consistent with Phase 3 + Plan 04-06 patterns. Trade-off: slight HTML size increase vs deployment simplicity.
- **`data-aim` attribute on each new section:** Enables integration test assertions like `assert 'data-aim="strategy"' in html`. Light-weight testability hook. Pattern from Plan 04-06.
- **Direction icons hardcoded by name (D-02 fixed frame):** The 5 canonical direction names are known at code-time, so icon mapping is a simple dict lookup. Unknown direction names fall back to 💡 emoji. This is a design decision: the LLM is instructed to use the 5 fixed names per Plan 04-05 item 7.
- **instagram_only note logic refactor:** Initial conditional structure had a bug where the "Регалии недоступны" note was unreachable for `source='instagram_only'` with ig_metrics present. Fixed by adding a post-conditional append block (Rule 1 auto-fix). The fix ensures the note ALWAYS appears for instagram_only source, per plan spec.
- **Whitefields client column styling:** Used golden border + tinted background (not full background color) — preserves table readability in both light and dark themes. Tested with `client-column` class in light/dark via inline CSS.

## Phase 4 Progress After Plan 04-07

- Wave 1: ✅ 04-01 (revenue_dynamics + clinic_metrics tool layer)
- Wave 1: ✅ 04-02 (structured_regalia + _merge_doctor_data)
- Wave 1: ✅ 04-03 (run_forum_pains + run_media_urls tools)
- Wave 2: ✅ 04-04 (Pass 1+2 prompts + QC checklist 15→18)
- Wave 2: ✅ 04-05 (Pass 3 prompt with 9 section generation rules)
- Wave 3: ✅ 04-06 (HTML Data Sections — revenue/media/ratings/competitor cards/clinic metrics)
- **Wave 4: ✅ 04-07 (HTML LLM Sections — this plan)**
- Wave 5: ⏳ 04-08 (Deploy + end-to-end validation)

**Phase 4 status: 7/8 plans done. 1 plan remaining (04-08 deploy).**

## Next Phase Readiness

- **Ready for downstream consumers:**
  - **04-08 (Deploy):** `generate_html_report.py` (now 2890 lines, +31% from 2207) ships via `docker cp` to `aim-hermes` container. No new pip dependencies, no schema migrations, no container restart needed (Python lazy-imports handlers).
  - **End-to-end validation:** Pass 3 LLM will receive Plan 04-05 prompt items 7-11 instructing it to populate `strategy_data`, `offer_data`, `whitefields_data`, `experts_data`, `content_data` kwargs. When LLM passes these to `generate_html_report`, the new sections will render.
- **No blockers** — code is local-only (not deployed), deployment happens in Plan 04-08 (Wave 5).

## Self-Check: PASSED

- ✓ `AIM/hermes/app/tools/generate_html_report.py` — file exists, AST parses cleanly, 2890 lines (was 2207 — +683 for 5 new sections + wiring)
- ✓ All 5 new functions present (`_build_strategy_section`, `_build_offer_section`, `_build_whitefields_matrix`, `_build_experts_with_regalia`, `_build_content_analysis_with_fears`)
- ✓ All 3 commits found in git log:
  - `c50f5a7` — Task 1: Strategy + Offer sections
  - `44cfc6b` — Task 2: Whitefields matrix
  - `d339468` — Task 3: Experts + Content with fears
- ✓ All Task 1 verification assertions pass (10/10)
- ✓ All Task 2 verification assertions pass (7/7)
- ✓ All Task 3 verification assertions pass (8/8)
- ✓ Regression: Phase 3 functions (`_build_no_instagram_block`, `_maybe_build_no_instagram_block`, `_build_qc_coverage_section`, `_build_competitor_table`) preserved
- ✓ Regression: Plan 04-06 functions (`_build_revenue_dynamics_section`, `_build_clinic_metrics_block`, `_build_media_urls_section`, `_build_ratings_section`, `_build_competitor_cards_section`) preserved
- ✓ `_build_report_html` signature has 10 params (5 existing + 5 new)
- ✓ `handle_generate_html_report` extracts + passes all 5 new kwargs
- ✓ Full integration test: 11 data-aim attributes render in single HTML output
- ✓ SEC-01 SATISFIED at HTML layer (Strategy with 5 LLM-generated directions, D-02 fixed frame)
- ✓ SEC-02 SATISFIED at HTML layer (Offer with steps + CTA, D-04 pattern)
- ✓ SEC-03 SATISFIED at HTML layer (Whitefields 4×4 matrix, D-05 categories, D-06 honest <3-competitor note, D-07 from-collected-data)
- ✓ SEC-04 SATISFIED at HTML layer (Experts with structured регалии + IG metrics, D-08 site scrape, D-09 merge by ФИО)
- ✓ SEC-05 SATISFIED at HTML layer (Content analysis + top-5 patient fears with mention counts, D-10 forums, D-11 from review texts)
- ✓ XSS-safe: all LLM-generated text wrapped in `_esc()`
- ✓ Backward compatible: Phase 3 callers work without new kwargs (no new sections render)
- ✓ SUMMARY.md created at expected path `.planning/phases/04-new-sections-data-depth/04-07-SUMMARY.md`

---
*Phase: 04-new-sections-data-depth*
*Completed: 2026-06-24T01:16:22Z*

## Self-Check: PASSED

Verified 2026-06-24T01:17:00Z:

- ✓ `AIM/hermes/app/tools/generate_html_report.py` exists (2890 lines)
- ✓ `.planning/phases/04-new-sections-data-depth/04-07-SUMMARY.md` exists
- ✓ Commit `c50f5a7` (Task 1: Strategy + Offer) found in git log
- ✓ Commit `44cfc6b` (Task 2: Whitefields matrix) found in git log
- ✓ Commit `d339468` (Task 3: Experts + Content with fears) found in git log
- ✓ All 5 new functions present in source: `_build_strategy_section`, `_build_offer_section`, `_build_whitefields_matrix`, `_build_experts_with_regalia`, `_build_content_analysis_with_fears`
