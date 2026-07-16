---
phase: 4
plan: 04-06
subsystem: hermes-tools/html-reporter
tags: [html, report, data-sections, revenue, media, ratings, competitor-cards, clinic-metrics, dat-01, dat-02, dat-03, dat-04, dat-05]

# Dependency graph
requires:
  - "04-01: find_company_financials revenue_dynamics + clinic_metrics output fields"
  - "04-03: run_media_urls tool (registered, returns all_mentions + pr_needed)"
  - "04-04: QC checklist 18 items (revenue_dynamics, clinic_metrics, ratings references)"
  - "04-05: Pass 3 prompt kwargs contract (ratings_extracted, okved_humanized, competitor_cards)"
provides:
  - "5 new HTML section builders in generate_html_report.py"
  - "_build_revenue_dynamics_section — DAT-01/D-13..14 (3-year table + blockquote, strict rule)"
  - "_build_clinic_metrics_block — DAT-04/D-21 (clinic metrics grid in About section)"
  - "_build_media_urls_section — DAT-02/D-17..18 (simple hyperlink list, honest pr_needed block)"
  - "_build_ratings_section — DAT-05/D-22 (2-platform rating cards with stars + themes)"
  - "_build_competitor_cards_section — DAT-03/D-20 (detailed glass-card grid per competitor)"
  - "All 5 sections wired into _build_report_html at correct positions"
affects:
  - "04-07 (HTML LLM Sections — same file, appends Strategy/Offer/Whitefields/Experts+страхи renderers)"
  - "04-08 (deploy — generate_html_report.py ships via docker cp)"
  - "Pass 3 LLM (consumes all 5 new sections via kwargs per Plan 04-05 contract)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Strict-rule rendering layer (D-13) — HTML enforces <3-year rule even if data layer slips"
    - "LLM-deferred humanization (D-21) — okved_humanized kwarg filled by Pass 3 LLM at report-time"
    - "Simple-list MVP guard (D-17) — explicit comment 'NOT card-grid with logos' prevents scope creep"
    - "Empty-string graceful degradation — new sections return '' when data absent, _build_report_html unchanged"
    - "Trend class mapping dict — растущая/стабильная/падающая → metric-tag-success/info/danger"
    - "DoS mitigation via list slicing — cards[:10] limit per T-04-06-D threat register"
    - "XSS-safe via _esc() — all user-facing text wrapped (competitor names, media titles, review themes)"
    - "Inline CSS in style attributes — new sections self-contained, no external CSS file dependency"

key-files:
  created: []
  modified:
    - AIM/hermes/app/tools/generate_html_report.py (+527 lines — 1681 → 2207 lines, +31% size)

key-decisions:
  - "Each section builder is a pure function — takes a dict, returns HTML string. No side effects, no I/O — easy to unit-test"
  - "Empty string on missing data (not exception) — _build_report_html caller can `if html: sections.append(html)` pattern"
  - "Inline CSS in style attributes (not external classes) — keeps new sections self-contained, avoids dependencies on design-showcase-dual-theme.html"
  - "Trend class mapping uses 7-key dict (3 Russian × 3 English + fallback) — covers LLM variance in language"
  - "Competitor cards section placed AFTER CI Analysis (gaps/advantages) — preserves narrative flow: table → gaps → detailed cards"
  - "Media URLs section placed AFTER Key Doctors, BEFORE PageSpeed — matches reference report section order (5 Media before 8 Presence)"
  - "Ratings section placed AFTER existing Reviews — both cover reputation, complementary (Reviews = text, Ratings = structured)"
  - "Revenue dynamics placed AFTER About (Executive Summary), BEFORE Market — matches reference section order (1 About → 1b Revenue → 2 Market)"
  - "Clinic metrics block inserted INSIDE About section (no <section> wrapper) — per plan 'goes INSIDE the About section'"
  - "Competitor cards fallback: checks both competitors and ci_analysis dicts for competitor_cards — LLM may populate either per Plan 04-05 item 9"

patterns-established:
  - "Pattern: pure HTML section builders — same signature pattern as _build_no_instagram_block (Phase 3)"
  - "Pattern: data-aim attribute on <section> for testability — data-aim=\"revenue-dynamics\", \"media-urls\", etc."
  - "Pattern: glass-card inline style for new sections — consistent with Phase 3 _build_no_instagram_block styling"
  - "Pattern: graceful degradation via empty string — sections return '' instead of partial/broken HTML when data missing"

requirements-completed: [DAT-01, DAT-02, DAT-03, DAT-04, DAT-05]

# Metrics
duration: 8min
started: 2026-06-24T00:44:46Z
completed: 2026-06-24T00:52:50Z
tasks: 3
files_modified: 1
lines_added: 527
commits:
  - "45243f8: feat(04-06): revenue dynamics + clinic metrics HTML sections (DAT-01, DAT-04)"
  - "6c2b2a1: feat(04-06): media URLs + ratings HTML sections (DAT-02, DAT-05)"
  - "f7dcff1: feat(04-06): competitor cards HTML section (DAT-03, D-20)"
---

# Phase 4 Plan 04-06: HTML Data Sections Summary

**5 new HTML section renderers added to `generate_html_report.py` (+527 lines, 1681→2207 total): revenue dynamics 3-year table + blockquote (DAT-01/D-13..14), clinic metrics grid in About (DAT-04/D-21), media URLs simple hyperlink list (DAT-02/D-17..18), ratings cards with stars + themes (DAT-05/D-22), competitor cards with all D-20 fields (DAT-03). All sections gracefully degrade to empty/honest blocks when data absent; XSS-safe via `_esc()`; consistent with Phase 3 design-system glass-card pattern.**

## Performance

- **Duration:** ~8 min (PLAN_START 00:44:46Z → PLAN_END 00:52:50Z, 484s)
- **Started:** 2026-06-24T00:44:46Z
- **Completed:** 2026-06-24T00:52:50Z
- **Tasks:** 3 (Task 1: revenue+clinic; Task 2: media+ratings; Task 3: competitor cards)
- **Files modified:** 1 (`generate_html_report.py`)
- **Lines added:** 527 (1681 → 2207, +31%)
- **Commits:** 3 (atomic per task)

## What Was Built

### 5 new section builders in `AIM/hermes/app/tools/generate_html_report.py`

#### 1. `_build_revenue_dynamics_section(financials: dict) -> str` (DAT-01, D-13..14)

Reads `financials["revenue_dynamics"]` (Plan 04-01 output). Enforces D-13 strict <3-year rule at the rendering layer:
- `dynamics_available=False` → honest "Динамика выручки недоступна — {reason}" block, NO table
- `dynamics_available=True` → 3-year table (Year, Revenue, YoY %) + blockquote with summary_text per D-14
- YoY % rendered with green (`+26.5%`) for positive, red (`-15.2%`) for negative, dim em-dash for None (oldest year)

#### 2. `_build_clinic_metrics_block(financials: dict) -> str` (DAT-04, D-21)

Reads `financials["clinic_metrics"]` (Plan 04-01 output). Renders metric grid INSIDE the About section (no `<section>` wrapper):
- Revenue (formatted via `_fmt_revenue_short` — "4.3 млрд ₽")
- Profit
- Employees count
- Status badge (Действующее → success green, other → warning orange)
- ОКВЭД — LLM-humanized via `okved_humanized` per D-21 (Pass 3 LLM translates 86.21 → "Общая медицинская практика"); falls back to raw code + description when LLM forgets

#### 3. `_build_media_urls_section(data: dict) -> str` (DAT-02, D-17..18)

Reads `data["media_urls"]` (Plan 04-03 run_media_urls output). Returns empty string when key absent (backward compatible with Phase 3 sessions):
- 0 mentions → D-18 honest block "В СМИ не упоминалась за последние 3 года" with `pr_needed` flag and PR recommendation feedback to Strategy section
- >0 mentions → D-17 SIMPLE LIST of hyperlinks (NOT card-grid with logos): `<source tag> <hyperlinked title> <date>` per line, MVP scope guard explicit in code comment

#### 4. `_build_ratings_section(reviews: dict) -> str` (DAT-05, D-22..23)

Reads `reviews["ratings_extracted"]` (Pass 3 LLM extracts structured ratings per Plan 04-05 item 15):
- Empty string when ratings_extracted absent (backward compatible)
- Renders grid of glass-card rating cards: platform name, star rating (★/☆), numeric rating, review count, positive themes (green tags), negative themes (orange tags)
- Star math: full_stars = int(rating), empty_stars = max(0, 5 - full_stars)

#### 5. `_build_competitor_cards_section(competitors: dict) -> str` (DAT-03, D-20)

Reads `competitors["competitor_cards"]` (Pass 3 LLM populates per Plan 04-05 item 9; fallback checks `ci_analysis` dict):
- Empty string when competitor_cards absent
- Renders grid of detailed glass-cards per competitor with ALL D-20 fields:
  - Name, year_founded, revenue_latest (formatted), revenue_trend (color-coded tag), surgeons_count
  - Instagram block (conditional — only if handle exists, with followers K/M formatting)
  - LLM-generated specialization (italic text-dim)
- Trend class mapping: растущая/растущий/growing → success; стабильная/стабильный/stable → info; падающая/падающий/declining → danger
- DoS mitigation per T-04-06-D threat register: cards[:10] slice (top 10 only)

### Section ordering in `_build_report_html`

| Position | Section | Phase | Source |
|----------|---------|-------|--------|
| 1 | Hero | 2 | existing |
| 2 | Executive Summary + clinic_metrics_html (DAT-04) | 4 | **new** |
| 3 | Revenue dynamics (DAT-01) | 4 | **new** |
| 4 | Market Research | 2 | existing |
| 5 | Competitor Table | 1 | existing |
| 6 | CI Analysis (gaps/advantages) | 1 | existing |
| 7 | Competitor Cards (DAT-03) | 4 | **new** |
| 8 | Key Doctors | 1 | existing |
| 9 | Media URLs (DAT-02) | 4 | **new** |
| 10 | PageSpeed | 1 | existing |
| 11 | SEO Audit | 1 | existing |
| 12 | Content Analysis | 1 | existing |
| 13 | Reviews + Ratings (DAT-05) | 4 | **new** |
| 14 | SMI Mentions | 1 | existing |
| 15 | Forum Pains | 1 | existing |
| 16 | Financial | 1 | existing |
| 17 | Instagram | 1 | existing |
| 18 | Executive Insights | 1 | existing |
| 19 | CTA | 2 | existing |
| 20 | Footer | 2 | existing |
| 21 | QC Coverage (optional) | 2 | existing |

## Task Commits

Each task committed atomically:

1. **Task 1:** `feat(04-06): add revenue dynamics + clinic metrics HTML sections (DAT-01, DAT-04)` — `45243f8`
2. **Task 2:** `feat(04-06): add media URLs + ratings HTML sections (DAT-02, DAT-05)` — `6c2b2a1`
3. **Task 3:** `feat(04-06): add competitor cards HTML section (DAT-03, D-20)` — `f7dcff1`

## Verification Results

| Check | Result |
|-------|--------|
| AST parse: `generate_html_report.py` syntax valid | OK |
| All 5 new functions present in source | OK |
| Existing functions preserved (`_build_no_instagram_block`, `_build_qc_coverage_section`, `_build_competitor_table`) | OK |
| `_build_report_html` function signature unchanged | OK |
| `_build_report_html({}, 'Test')` returns valid HTML | OK |
| Test 1.1: revenue dynamics D-13 honest block (dynamics_available=False) | OK |
| Test 1.2: revenue dynamics D-14 table + blockquote (dynamics_available=True) | OK |
| Test 1.3: revenue dynamics empty financials handled | OK |
| Test 1.4: clinic metrics renders revenue + status | OK |
| Test 1.5: clinic metrics okved_humanized (D-21) | OK |
| Test 2.1: media URLs D-17 hyperlink list | OK |
| Test 2.2: media URLs D-18 honest 0-mentions block | OK |
| Test 2.3: media URLs empty data returns empty string | OK |
| Test 2.4: ratings section with 2 platforms (ПроДокторов + Яндекс.Карты) | OK |
| Test 2.5: ratings empty reviews returns empty string | OK |
| Test 3.1: full competitor card with all D-20 fields | OK |
| Test 3.2: trend class mapping (падающая → danger) | OK |
| Test 3.3: empty competitor cards returns empty string | OK |
| Test 3.4: DoS mitigation — 20 cards input → 10 cards rendered | OK |
| Test 3.5: Instagram followers K-format (25000 → 25K) | OK |
| Full integration: `_build_report_html` with all Phase 4 data | OK |
| Section ordering: Hero → Revenue → Media → Ratings | OK |
| All 5 data-aim attributes present in assembled HTML | OK |

## Decisions Made

- **Pure-function section builders** — each takes a dict, returns HTML string. No side effects, no I/O. Same pattern as Phase 3 `_build_no_instagram_block`. Easy to unit-test.
- **Empty-string graceful degradation** — sections return `""` when data is absent. `_build_report_html` uses `if html: sections.append(html)` pattern (clinic_metrics is inline, so it's wrapped in the About section with `elif` fallback).
- **Inline CSS via `style` attributes** — new sections are self-contained, no external CSS file dependency. Consistent with Phase 3 `_build_no_instagram_block` styling pattern. Trade-off: slight HTML size increase vs deployment simplicity.
- **Trend class mapping dict (7 keys)** — covers 3 Russian (растущая/стабильная/падающая) + 3 English (growing/stable/declining) + 2 gender variants (растущий/стабильный/падающий) + fallback. LLM may use any; we tolerate variance.
- **Competitor cards fallback to `ci_analysis`** — Plan 04-05 item 9 says LLM populates competitor_cards, but doesn't specify which dict. We check `competitors.competitor_cards` first, then fall back to `ci_analysis.competitor_cards`. Defensive — handles either placement.
- **Section ordering follows reference report** — Hero → About → Revenue (1b) → Market (2) → Competitor Cards (6) → Media (5) → Ratings → ... matches `ИПХиК (2).html` section order.
- **D-13 enforced at rendering layer too** — even if data layer (Plan 04-01) somehow slips and sends partial data, the HTML builder will render the honest block when `dynamics_available=False`. Defense in depth.
- **DoS mitigation per T-04-06-D** — `cards[:10]` slice. If LLM sends 50 competitor cards (hallucination burst), only 10 render. Rest are silently dropped (could be logged if needed).
- **`data-aim` attribute on each new section** — enables integration test assertions like `assert 'data-aim="revenue-dynamics"' in html`. Light-weight testability hook.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written. No Rules 1-3 triggered. No architectural changes (Rule 4) triggered.

**Total deviations:** 0

## Issues Encountered

- **Local-env limitation (not a bug):** Importing `generate_html_report` requires `tools.registry` from `hermes-agent` package, which isn't pip-installed locally (only inside Docker container). Same issue noted in Plan 04-03 SUMMARY.md. Worked around by stubbing `tools` and `app.tools.session_archive` modules in the verification scripts. Code follows production pattern; will resolve inside `aim-hermes` container.

## User Setup Required

None — pure Python code changes, no external services or environment variables. Deployment happens in Plan 04-08 (Wave 5).

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-04-06-X (XSS — untrusted competitor names, media titles, review themes) | **mitigate** — every user-facing string wrapped in `_esc()`; URLs escaped in href attributes; existing pattern from `_build_no_instagram_block` followed consistently |
| T-04-06-T (Tampering — revenue table could show wrong YoY %) | **accept** — formatting only; data validated upstream in Plan 04-01 `_format_revenue_dynamics` with 12 unit tests |
| T-04-06-D (DoS — large competitor cards list → large HTML) | **mitigate** — `cards[:10]` slice in `_build_competitor_cards_section`; verified with 20-card input → 10-card output |
| T-04-06-E (EoP — not applicable) | **accept** — pure HTML string generation, no privilege change |
| T-04-06-SC (Supply chain — no new packages) | **accept** — pure Python stdlib + existing `_esc`/`_fmt_revenue_short`/`_fmt_num` helpers |

## Known Stubs

**None.** All 5 section builders contain real rendering logic — no hardcoded empty values flowing to UI, no placeholder text, no TODO/FIXME markers.

The intentionally defensive patterns (`okved_humanized` fallback to raw code, `instagram_handle` conditional block, empty-string graceful degradation) are documented design decisions per D-21 (LLM may forget to translate OKVED) and have clear resolution paths (Pass 3 LLM contract per Plan 04-05).

## Threat Surface Scan

**No new threat surface introduced.** The trust boundary is unchanged — the HTML reporter still produces a self-contained HTML page from session archive data. The 5 new section builders read from existing data fields (no new external API calls, no new file access patterns, no new auth paths). XSS surface is mitigated by consistent `_esc()` usage verified in threat model compliance section above.

## Next Phase Readiness

- **Ready for downstream consumers:**
  - **04-07 (HTML LLM Sections — Strategy/Offer/Whitefields/Experts+страхи):** Same file, same pattern. Can append `_build_strategy_section`, `_build_offer_section`, etc. after `_build_competitor_cards_section`. No file conflicts — different section builders, different insertion points in `_build_report_html`.
  - **04-08 (Deploy):** `generate_html_report.py` (now 2207 lines) ships via `docker cp` to `aim-hermes` container. No new pip dependencies, no schema migrations, no container restart needed (Python lazy-imports handlers).
- **No blockers** — code is local-only (not deployed), deployment happens in Plan 04-08 (Wave 5).

## Phase 4 Progress After Plan 04-06

- Wave 1: ✅ 04-01 (revenue_dynamics + clinic_metrics tool layer)
- Wave 1: ✅ 04-02 (structured_regalia + _merge_doctor_data)
- Wave 1: ✅ 04-03 (run_forum_pains + run_media_urls tools)
- Wave 2: ✅ 04-04 (Pass 1+2 prompts + QC checklist 15→18)
- Wave 2: ✅ 04-05 (Pass 3 prompt with 9 section generation rules)
- **Wave 3: ✅ 04-06 (HTML Data Sections — this plan)**
- Wave 4: ⏳ 04-07 (HTML LLM Sections — Strategy/Offer/Whitefields rendering)
- Wave 5: ⏳ 04-08 (Deploy + end-to-end validation)

**Phase 4 status: 6/8 plans done. 2 plans remaining.**

## Self-Check: PASSED

- ✓ `AIM/hermes/app/tools/generate_html_report.py` — file exists, AST parses cleanly, 2207 lines (was 1681 — +527 for 5 new sections + wiring)
- ✓ All 5 new functions present (`_build_revenue_dynamics_section`, `_build_clinic_metrics_block`, `_build_media_urls_section`, `_build_ratings_section`, `_build_competitor_cards_section`)
- ✓ All 3 commits found in git log:
  - `45243f8` — Task 1: revenue + clinic metrics
  - `6c2b2a1` — Task 2: media + ratings
  - `f7dcff1` — Task 3: competitor cards
- ✓ All 22 verification assertions pass (5 + 5 + 5 per task + 7 integration)
- ✓ Regression: Phase 3 `_build_no_instagram_block`, `_maybe_build_no_instagram_block`, `_build_qc_coverage_section` unchanged
- ✓ Regression: `_build_report_html` signature unchanged
- ✓ Regression: existing sections (Hero, Market, Competitors table, Key Doctors, PageSpeed, etc.) preserved
- ✓ DAT-01 SATISFIED at HTML layer (revenue dynamics with strict D-13 rule + D-14 table/blockquote)
- ✓ DAT-02 SATISFIED at HTML layer (media URLs as D-17 simple list + D-18 honest pr_needed block)
- ✓ DAT-03 SATISFIED at HTML layer (competitor cards with all D-20 fields)
- ✓ DAT-04 SATISFIED at HTML layer (clinic metrics block in About + D-21 OKVED humanization)
- ✓ DAT-05 SATISFIED at HTML layer (ratings with 2-platform minimum per D-22)
- ✓ Final file size: 2207 lines (was 1681 — +527 lines, +31% size increase)
- ✓ SUMMARY.md created at expected path `.planning/phases/04-new-sections-data-depth/04-06-SUMMARY.md`
- ✓ STATE.md, ROADMAP.md, REQUIREMENTS.md updated to reflect 6/8 plans done

---
*Phase: 04-new-sections-data-depth*
*Completed: 2026-06-24T00:52:50Z*
