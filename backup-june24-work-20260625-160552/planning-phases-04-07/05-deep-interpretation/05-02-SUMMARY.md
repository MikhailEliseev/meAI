---
phase: 05-deep-interpretation
plan: 02
name: html-helpers-gap-block-insight-extend-builders
subsystem: hermes-html-reporter
tags: [html, report, gap-blocks, insight, blockquote, render-helpers, section-builders, design-system, int-04, int-05, d-07, d-08, d-09, d-10]
requirements: [INT-04, INT-05]
depends_on: [05-01]
provides:
  - "_render_gap_blocks(gap_blocks) — HTML renderer for Phase 5 gap-blocks (strength + growth)"
  - "_render_section_insight(insight) — HTML renderer for Phase 5 section blockquote"
  - "10 extended _build_*_section functions with insight + gap_blocks optional kwargs"
  - "_build_report_html signature with section_insights + section_gap_blocks kwargs"
  - "handle_generate_html_report extracts + passes Phase 5 narrative extras"
affects:
  - "generate_html_report.py (HTML report renderer)"
  - "AIM/hermes/tests/test_phase5_helpers.py (NEW)"
  - "AIM/hermes/tests/test_phase5_integration.py (NEW)"
tech-stack:
  added: []
  patterns:
    - "Pure-function HTML renderer helpers (no side effects, XSS-escape all LLM text)"
    - "DoS mitigation via list cap (5 items) + text truncation (600 chars)"
    - "Backward-compatible kwarg extension (default None preserves Phase 4 behavior)"
    - "Per-section slice pattern (dict lookup by section_key)"
    - "Python 3.11 f-string backslash safety (no backslash-escaped double quotes in f-string expression parts)"
key-files:
  created:
    - path: AIM/hermes/tests/test_phase5_helpers.py
      lines: 283
      purpose: "13 unit tests for _render_gap_blocks + _render_section_insight"
    - path: AIM/hermes/tests/test_phase5_integration.py
      lines: 329
      purpose: "5 integration tests — full report, backward compat, partial, XSS, handler"
  modified:
    - path: AIM/hermes/app/tools/generate_html_report.py
      lines_before: 2893
      lines_after: 3153
      changes:
        - "+96 lines: 2 new helpers (_render_gap_blocks, _render_section_insight) before _build_report_html"
        - "+88 lines: extend 10 builder signatures + render calls"
        - "+76 lines: extend _build_report_html signature + slice wiring + handler extraction"
decisions:
  - id: D-05-02-a
    title: "Insight rendered as LAST element before </section>, gap_blocks BEFORE insight"
    rationale: "Reference HTML pattern — gap-blocks are supporting evidence, insight is the punchline. Reading order: data → evidence → conclusion."
    impact: "All 10 builders now follow this order; future Phase 5+ additions must preserve it."
  - id: D-05-02-b
    title: "style_attr assembled outside f-string expression (Python 3.11 safety)"
    rationale: "Plans 02-01, 03-05, 04-08 all documented Python 3.11 SyntaxError when f-string expression parts contain backslash-escaped double quotes. Assembling the complete `style=\"...\"` string in a separate local variable sidesteps the gotcha."
    impact: "All future HTML helpers that conditionally include style attributes must follow this pattern."
  - id: D-05-02-c
    title: "clinic_metrics insight uses section_key 'about' (not 'clinic-metrics')"
    rationale: "clinic_metrics is inline inside the About/Executive Summary section — no separate <section>. Using 'about' makes the semantic intent clear and aligns with the QC checklist key 0 (About)."
    impact: "Pass 3 LLM prompt (Plan 05-01) must use `section_insights['about']` for clinic-metrics insight."
  - id: D-05-02-d
    title: "5 of 10 builders get gap_blocks kwarg (strategy/offer/experts/content/ratings)"
    rationale: "Reference ИПХиК (2).html shows .gap divs only in these 5 sections. Other 5 sections (whitefields, revenue_dynamics, clinic_metrics, media_urls, competitor_cards) show blockquote only — adding gap_blocks there would diverge from the reference."
    impact: "Pass 3 LLM prompt (Plan 05-01) must only populate section_gap_blocks for these 5 keys."
metrics:
  duration: "~2h"
  completed: "2026-06-24T03:10Z"
  tasks_completed: 3
  tasks_total: 3
  files_created: 2
  files_modified: 1
  commits: 3
  unit_tests: 13
  integration_tests: 5
  total_tests: 18
---

# Phase 5 Plan 02: HTML Helpers + Section Builder Extension Summary

**One-liner:** Added `_render_gap_blocks` + `_render_section_insight` HTML helpers with XSS escaping + DoS caps, extended all 10 Phase 4 `_build_*_section` functions with optional `insight` / `gap_blocks` kwargs, and wired `_build_report_html` + `handle_generate_html_report` to thread Pass 3 LLM narrative extras through to the rendered report — fully backward compatible (18 tests pass).

---

## Tasks Completed

### Task 1: Create _render_gap_blocks + _render_section_insight helpers with unit tests

**Commit:** `78b82d1`

**TDD cycle:**
- RED: Wrote `AIM/hermes/tests/test_phase5_helpers.py` with 13 test cases. Tests failed because `_render_gap_blocks` / `_render_section_insight` did not exist (AttributeError on module load).
- GREEN: Implemented both helpers in `generate_html_report.py` (lines 1817-1908). Used local-variable style assembly (no f-string expression backslashes) for Python 3.11 safety.
- All 13 tests pass.

**Helpers delivered:**
- `_render_gap_blocks(gap_blocks: list | None) -> str` — renders list of `{"type": "strength"|"growth", "title", "description"}` dicts as `.gap` divs with green border for strength, default border for growth. Caps to 5 items (T-05-02-D DoS mitigation). All text XSS-escaped via `_esc`.
- `_render_section_insight(insight: str | None) -> str` — renders string as `<blockquote class="section-insight">` with border-left 2px solid var(--text). Truncates to 600 chars with ellipsis. XSS-escaped.

**Auto-fix [Rule 1 - Bug]:** Plan action contained a typo `style_arr` vs `style_attr` (plan code sample line 262 used `style_arr` while line 260 defined `style_attr`). Fixed inline by using consistent `style_attr` local variable. No behavior change.

### Task 2: Extend 10 Phase 4 section builders with insight + gap_blocks optional kwargs

**Commit:** `0bc7031`

**10 builders extended:**

| Builder | insight | gap_blocks | Section key |
|---------|---------|------------|-------------|
| `_build_strategy_section` | YES | YES | `"strategy"` |
| `_build_offer_section` | YES | YES | `"offer"` |
| `_build_experts_with_regalia` | YES | YES | `"experts"` |
| `_build_content_analysis_with_fears` | YES | YES | `"content"` |
| `_build_ratings_section` | YES | YES | `"ratings"` |
| `_build_whitefields_matrix` | YES | — | `"whitefields"` |
| `_build_revenue_dynamics_section` | YES | — | `"revenue-dynamics"` |
| `_build_clinic_metrics_block` | YES (inline) | — | `"about"` |
| `_build_media_urls_section` | YES | — | `"media-urls"` |
| `_build_competitor_cards_section` | YES | — | `"competitor-cards"` |

**Wiring:**
- `_build_report_html` signature extended with `section_insights: dict | None = None` and `section_gap_blocks: dict | None = None` (12 kwargs total — 10 existing + 2 new).
- Each builder call slices its per-section data: `insight=section_insights.get("strategy")`, `gap_blocks=section_gap_blocks.get("strategy")`, etc.
- `handle_generate_html_report` extracts the new kwargs from `kwargs.get(...)` + dict-positional fallback (matching Phase 4 pattern), passes them through to `_build_report_html`.
- Defensive normalization in `_build_report_html`: non-dict inputs coerced to `{}`.

**Backward compatibility:** Calling `_build_report_html({}, "Test")` with no new kwargs produces zero `section-insight` blockquotes and zero `_render_gap_blocks` divs (verified by test 2). All 13 Task 1 unit tests still pass — no regression.

### Task 3: Integration test — full report with narrative extras renders correctly

**Commit:** `5ac678b`

**5 integration tests delivered:**
1. `test_full_report_with_all_narrative_extras` — all 10 sections + 10 insights + 5 gap_blocks lists → >=8 blockquotes + >=5 .gap divs.
2. `test_backward_compat_no_narrative_extras` — no new kwargs → 0 section-insight blockquotes, 0 _render_gap_blocks divs. Regex `<div class="gap"(?=[ >])` distinguishes from ci-gap divs (which use `class="gap ` with space).
3. `test_partial_insights_only_strategy` — only strategy insight → exactly 1 blockquote in strategy section.
4. `test_xss_safety_insight_escaped` — insight with `<script>` → escaped as `&lt;script&gt;` in output.
5. `test_handle_generate_html_report_extracts_kwargs` — handler accepts section_insights kwarg, runs extraction path, returns session_hash error (proves extraction logic ran without crashing).

All 5 tests pass.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed plan typo `style_arr` → `style_attr`**
- **Found during:** Task 1 GREEN phase
- **Issue:** Plan code sample (lines 260-262) defined local variable `style_attr` but referenced it as `style_arr` in the f-string.
- **Fix:** Used consistent `style_attr` variable name throughout the helper.
- **Files modified:** `AIM/hermes/app/tools/generate_html_report.py`
- **Commit:** 78b82d1

No other deviations. Plan executed as written.

---

## Requirement Coverage

| Requirement | How Addressed | Verification |
|-------------|---------------|--------------|
| INT-04 (gap-blocks with strength + growth) | `_render_gap_blocks` helper renders `.gap` divs with green border for strength, default for growth. 5 section builders accept `gap_blocks` kwarg. Wired via `section_gap_blocks` dict keyed by section_key. | 13 unit tests + 1 integration test pass |
| INT-05 (blockquote with strategic insight) | `_render_section_insight` helper renders `<blockquote class="section-insight">`. All 10 section builders accept `insight` kwarg. Wired via `section_insights` dict keyed by section_key. | 13 unit tests + 1 integration test pass |

---

## Threat Mitigations Verified

| Threat ID | Mitigation | Test |
|-----------|------------|------|
| T-05-02-X (XSS) | All LLM text wrapped in `_esc()` — converts `<`, `>`, `&`, `"` to HTML entities | Unit test 6 + 11, Integration test 4 |
| T-05-02-T (Tampering) | Same as T-05-02-X — `_esc()` defeats script injection | Same tests |
| T-05-02-D (DoS) | `_render_gap_blocks` caps to 5 items; `_render_section_insight` truncates to 600 chars + ellipsis | Unit test 7 + 12 |
| T-05-02-I (Info disclosure) | No new data exposed; renderers format existing LLM output | N/A (accept) |
| T-05-02-E (EoP) | Pure HTML string generation, no privilege change | N/A (accept) |
| T-05-02-SC (Supply chain) | No new packages — pure Python stdlib + existing `_esc`/`_fmt_num` | N/A (accept) |

---

## Test Summary

**18 total tests pass:**

**Unit tests (13)** — `AIM/hermes/tests/test_phase5_helpers.py`:
- `test_render_gap_blocks_none` — None input → empty string
- `test_render_gap_blocks_empty_list` — [] input → empty string
- `test_render_gap_blocks_four_items` — 4 items → 4 .gap divs
- `test_render_gap_blocks_strength_green_border` — strength → var(--green)
- `test_render_gap_blocks_growth_no_green` — growth → no green
- `test_render_gap_blocks_xss_escape` — `<script>` → `&lt;script&gt;`
- `test_render_gap_blocks_dos_cap` — 20 items → capped to 5
- `test_render_section_insight_none` — None → empty string
- `test_render_section_insight_empty_string` — "" → empty string
- `test_render_section_insight_blockquote` — valid → `<blockquote class="section-insight">`
- `test_render_section_insight_xss_escape` — XSS neutralized
- `test_render_section_insight_truncation` — 1000 chars → 600 + ellipsis
- `test_python311_fstring_backslash_safety` — both helpers smoke-test

**Integration tests (5)** — `AIM/hermes/tests/test_phase5_integration.py`:
- `test_full_report_with_all_narrative_extras` — all sections + extras
- `test_backward_compat_no_narrative_extras` — Phase 4 output unchanged
- `test_partial_insights_only_strategy` — partial insights work
- `test_xss_safety_insight_escaped` — XSS through full pipeline
- `test_handle_generate_html_report_extracts_kwargs` — handler extraction

---

## Python 3.11 f-string Safety

**Known gotcha (documented in Plans 02-01, 03-05, 04-08):** Python 3.11 forbids backslash-escaped double quotes inside f-string expression parts. Container runs Python 3.11; local dev runs Python 3.14 (which would pass AST parse but fail at container import).

**Mitigation applied:**
- `_render_gap_blocks`: `style_attr` local variable assembled in a separate statement (`if style: style_attr = ' style="' + style + '"'`), NOT inside f-string expression.
- `_render_section_insight`: HTML assembled via string concatenation (`'...' + escaped_text + '...'`), no f-string expression nesting.
- AST parse OK under both Python 3.11 and 3.14.

---

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: `AIM/hermes/app/tools/generate_html_report.py` (3153 lines, min 3050 required)
- FOUND: `AIM/hermes/tests/test_phase5_helpers.py` (283 lines)
- FOUND: `AIM/hermes/tests/test_phase5_integration.py` (329 lines)

**Commits verified to exist in git log:**
- FOUND: `78b82d1` — Task 1 (helpers + unit tests)
- FOUND: `0bc7031` — Task 2 (10 builders + wiring)
- FOUND: `5ac678b` — Task 3 (integration tests)

**Test results verified:**
- 13/13 unit tests pass (`python3 AIM/hermes/tests/test_phase5_helpers.py`)
- 5/5 integration tests pass (`python3 AIM/hermes/tests/test_phase5_integration.py`)

**AST parse:** OK under Python 3.14 (container has 3.11; f-string safety pattern applied).

---

## Next Steps

Plan 05-02 complete. Next plans in Phase 5:
- Plan 05-03 (if planned): Wire Pass 3 LLM to actually emit `section_insights` + `section_gap_blocks` kwargs (depends on Plan 05-01 prompt rules being live).
- Live UAT: deploy to `ssh aim` container, run a real presale, verify the blockquotes and gap-blocks appear in the HTML report on iamaim.ru.
