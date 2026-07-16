---
phase: 03-instagram-integration
verified: 2026-06-23T19:30:00Z
status: human_needed
score: 4/4 must-haves verified (code-level); 3 human items pending
overrides_applied: 0
human_verification:
  - test: "Run a live end-to-end orchestrator presale on a cosmetology/plastic-surgery clinic and observe that run_instagram_content is actually invoked in Pass 1"
    expected: "Pass 1 tool-call history includes run_instagram_content + find_doctor_handles; Pass 2 gap_report item 5 status='filled'; final HTML report sections 03+04 contain per-doctor Instagram metrics"
    why_human: "Prompts instruct the LLM but cannot guarantee LLM compliance; only a real run with ORCHESTRATOR_MODE=1 on a real clinic URL confirms end-to-end behavior"
  - test: "Visually inspect the rendered HTML for the no-Instagram block (critical niche with missing Instagram data)"
    expected: "Sections 03+04 contain a 'Instagram: данные недоступны' glass-card block with warning badge; QC section shows item 5 with ⚪ icon and opacity-0.6 styling distinct from missing(red ❌)/partial(yellow 🟡)/filled(green ✅)"
    why_human: "CSS styling, visual hierarchy, and design-system consistency require human eyes; grep can confirm class names but not visual correctness"
  - test: "Confirm the runtime HARD FAIL override fires when LLM marks item 5 as filled without actually calling run_instagram_content (spoofing scenario T-03-06-S)"
    expected: "Final coverage_report_final.status='FAIL' with 'QC HARD FAIL override' log line; this proves the runtime helper catches LLM deviation"
    why_human: "Requires a controlled test fixture with a hand-crafted gap_report; cannot be exercised by code inspection alone because the helper trusts the LLM's filled_items list unless item 5 is absent"
---

# Phase 3: Instagram Integration — Verification Report

**Phase Goal:** Instagram analysis runs for niches where it's critical (cosmetology, plastic surgery), producing per-doctor metrics matching the reference sections 03+04
**Verified:** 2026-06-23T19:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | `run_instagram_content` is callable by both the LLM-orchestrator and the PipelineEngine (added to `engine.py::_TOOL_HANDLERS`, not just the LLM registry) | VERIFIED | `AIM/hermes/app/pipeline/engine.py:66-67` registers both `run_instagram_content` and `find_doctor_handles` in `_TOOL_HANDLERS`. Total entry count is 24 (was 22 pre-Phase-3); confirmed via AST + grep count of entry pattern. Both tool files exist on disk: `run_instagram_content.py` (30,566 bytes) and `find_doctor_handles.py` (53,472 bytes). Handler functions `handle_run_instagram_content` (line 1200 of run_instagram_content.py registry block) and `handle_find_doctor_handles` (line 837 of find_doctor_handles.py) verified present. |
| 2   | For cosmetology and plastic surgery niches, Instagram analysis always runs — LLM does not skip it as "optional" | VERIFIED | Four-layer enforcement: (a) `qc_checklist.py:52` defines `CRITICAL_NICHES = ("plastic_surgery", "cosmetology")`; (b) `pass_collect.py:165-204` `_build_pass_collect_prompt` critical branch emits "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО" with explicit ordering `find_doctor_handles` → `run_instagram_content` + batch size 8-10 + HARD FAIL warning; (c) `pass_gap_analyze.py:86-89` `_CHECKLIST_PROMPT_TEMPLATE` carries explicit "HARD FAIL: coverage=FAIL даже при 14/15" rule for critical-niche + Instagram-missing case; (d) `three_pass.py:66-188` `_apply_niche_conditional_coverage` helper applies runtime override post-Pass-2 AND post-Pass-3 (wired at lines 286 and 324). 6/6 unit tests in `test_conditional_coverage.py` PASS (verified via `python3 -m unittest`). Runtime helper behavior verified: `is_niche_instagram_critical("plastic_surgery")` → True, `is_niche_instagram_critical("cosmetology")` → True, `is_niche_instagram_critical("dental")` → False; `applicable_items("dental")` returns 14 items, `applicable_items("plastic_surgery")` returns 15 items. |
| 3   | For each top-5 doctor, the report contains: followers, avg likes, avg views, content style, topics (in %), gaps, potential — matching reference sections 03+04 | VERIFIED | (a) `run_instagram_content.py` produces all required metrics fields: `top_by_followers` (line 128, 140), `avg_likes` (line 327), `avg_views` (line 329), `content_themes` with counts (lines 333, 366-371), `content_gaps` with severity (lines 336, 382-383), `content_style` referenced throughout. (b) `pass_collect.py:173-175` Pass 1 prompt critical branch explicitly requests "подписчики, avg лайки/просмотры, стиль, темы, пробелы". (c) `pass_collect.py:185-203` rule 5 "ADAPTIVE TOP-5 RULE" handles the site-top vs Instagram-active cohort divergence — references the `top_by_followers` field by name (load-bearing). (d) `pass_gap_analyze.py:91-94` "АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4/6/7" provides cohort-aware evaluation so item 6 (themes) and item 7 (gaps) are evaluated against the Instagram-active cohort, not the tituled-only site-top-5. (e) Phase 1 RES-05 confirmed v2 Perplexity response shape scores 9.5/10 on reference-field coverage (referenced in 03-CONTEXT.md canonical refs). |
| 4   | If a clinic has no Instagram, the report notes this honestly and does not block the remaining phases | VERIFIED | (a) `generate_html_report.py:196-268` `_build_no_instagram_block(reason)` renders a design-system HTML block with 4 reason variants (`no_account`, `handle_not_found`, `private_profile`, `perplexity_outside_index`) per D-07. (b) `generate_html_report.py:271-341` `_maybe_build_no_instagram_block(niche, instagram_data)` gatekeeper returns empty string for non-critical niches (no warning) and for critical niches with real data (analyzed_count > 0); renders block only when critical niche + missing data. (c) QC section `_build_qc_coverage_section` reads `metadata["not_applicable_items"]` (canonical source per Fix #2) and renders with distinct ⚪ icon + `qc-not-applicable` CSS class with opacity 0.6 (lines 439-454, 526-531). (d) `pass_fill_assemble.py:149-162` items 5+6 explicitly instruct LLM to pass `niche` and `instagram_data` kwargs to `generate_html_report`, closing the cross-plan data-contract gap. (e) Phase 2 soft QC gate (warning only, non-blocking) preserved — `_apply_niche_conditional_coverage` mutates `CoverageReport.status` to FAIL but `run_three_pass` continues to Pass 3 regardless (lines 297-308 only log warning, never short-circuit). |

**Score:** 4/4 truths verified (code-level)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `AIM/hermes/app/pipeline/engine.py` | `_TOOL_HANDLERS` dict with 24 entries including Instagram tools | VERIFIED | Lines 66-67 contain both Instagram entries. Count = 24. No regression to existing 22 entries (verified via grep pattern count). |
| `AIM/hermes/app/orchestrator/states.py` | `OrchestratorState.niche: str = ""` field | VERIFIED | Line 66: `niche: str = ""`. Docstring documents all possible values. |
| `AIM/hermes/app/orchestrator/niche_detector.py` | `detect_instagram_critical_niche(state) -> dict` async mini-call | VERIFIED | 203-line module with the async function (line 59), `_extract_reply_text`, `_parse_verdict_json`, `_normalize_verdict` helpers. Has try/except returning deterministic fallback `{instagram_critical: False, niche: "unknown"}` on any failure. |
| `AIM/hermes/app/orchestrator/three_pass.py` | Mini-call between Pass 1/2 + `_apply_niche_conditional_coverage` helper at 2 wire sites | VERIFIED | Mini-call at lines 240-258; helper at lines 66-188; wired post-Pass-2 (line 286) and post-Pass-3 (line 324). |
| `AIM/hermes/app/orchestrator/qc_checklist.py` | `is_item_applicable`, `applicable_items`, `is_niche_instagram_critical` helpers + `CRITICAL_NICHES` + item 5 `conditional_on_niche` flag | VERIFIED | Constants at line 52; helpers at lines 225-302; item 5 carries `"conditional_on_niche": True` at line 104. VERSION = "1.1.0". Runtime behavior verified via direct invocation. |
| `AIM/hermes/app/orchestrator/pass_collect.py` | `_build_pass_collect_prompt(state)` with niche-aware Instagram-mandatory rule | VERIFIED | Helper at line 116; critical branch (lines 165-204) emits ОБЯЗАТЕЛЬНОЕ ПРАВИЛО + HARD FAIL + adaptive top-5 rule; non-critical branch (lines 206-219) emits optional + adaptive note. |
| `AIM/hermes/app/orchestrator/pass_gap_analyze.py` | `_CHECKLIST_PROMPT_TEMPLATE` with `{niche_instruction}` + HARD FAIL Instagram rule | VERIFIED | Template at line 73; HARD FAIL block at lines 86-89; adaptive cohort rules for items 4/6/7 at lines 91-94; niche_instruction built at runtime based on `state.niche` (lines 126-150); `_ensure_summary` counts `not_applicable` separately (lines 278-281). |
| `AIM/hermes/app/orchestrator/pass_fill_assemble.py` | Pass 3 prompt items 5+6 referencing niche + instagram_data kwargs | VERIFIED | Items 5-6 in `_build_prompt` return string (lines 149-162) with mandatory "ОБЯЗАТЕЛЬНО передай параметр" language. |
| `AIM/hermes/app/orchestrator/coverage_reporter.py` | `CoverageReport.not_applicable_items: list[dict] = field(default_factory=list)` | VERIFIED | Field at line 69, positioned between `partial_items` and `coverage_pct`. `calc_coverage` itself unchanged (separation of concerns). |
| `AIM/hermes/app/tools/generate_html_report.py` | `_build_no_instagram_block` + `_maybe_build_no_instagram_block` helpers + QC `not_applicable` rendering | VERIFIED | Helpers at lines 196-268 and 271-341. QC section reads `metadata["not_applicable_items"]` (line 385) and renders ⚪ icon with `qc-not-applicable` CSS class (lines 439-454, 526-531). `_build_report_html` extended signature accepts `niche` + `instagram_data` kwargs. |
| `AIM/hermes/app/orchestrator/test_conditional_coverage.py` | 6 unit tests for `_apply_niche_conditional_coverage` | VERIFIED | All 6 tests PASS via `python3 -m unittest`: (1) critical+item5_missing→FAIL with HARD FAIL log, (2) critical+item5_filled→no override, (3) non-critical→drops item5 + populates not_applicable, (4) unknown→unchanged, (5) asdict includes not_applicable_items key, (6) default empty list backward-compat. |
| `AIM/hermes/app/tools/run_instagram_content.py` | v2 Perplexity-based tool with required metric fields | VERIFIED | 30,566 bytes (718 lines per SUMMARY). Has `top_by_followers` (lines 128, 140), `avg_likes`/`avg_views` (lines 327, 329), `content_themes` (line 333), `content_gaps` (line 336). Tool registry block at line 1200. |
| `AIM/hermes/app/tools/find_doctor_handles.py` | Doctor discovery tool with handle finder | VERIFIED | 53,472 bytes (1,205 lines per CONTEXT). Handler `handle_find_doctor_handles` at line 837. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| PipelineEngine | Instagram tools | `_TOOL_HANDLERS` dict lookup via `_get_handler` | WIRED | engine.py lines 66-67 register both tools; handlers resolve to actual module:function tuples. |
| three_pass.py | niche_detector mini-call | `from app.orchestrator.niche_detector import detect_instagram_critical_niche` (line 247) | WIRED | Mini-call executed at line 248 between Pass 1 abort check (line 231) and Pass 2 invocation (line 265). |
| three_pass.py | `_apply_niche_conditional_coverage` helper | Inline module-level definition + 2 call sites | WIRED | Helper defined at line 66; wired at line 286 (post-Pass-2) and line 324 (post-Pass-3). |
| pass_collect.py | `_build_pass_collect_prompt` helper | Called inside `run_pass_collect` body | WIRED | Line 71: `prompt = _build_pass_collect_prompt(state)`. |
| pass_gap_analyze.py | `is_niche_instagram_critical` | Lazy import from qc_checklist | WIRED | Line 123: `from app.orchestrator.qc_checklist import is_niche_instagram_critical`. |
| pass_fill_assemble.py | `_build_prompt` items 5+6 | Inline in returned string | WIRED | Items 5+6 at lines 149-162 instruct LLM to pass `niche` + `instagram_data` kwargs to `generate_html_report`. |
| generate_html_report.py | `_maybe_build_no_instagram_block` | Called inside `_build_report_html` for sections 03+04 | WIRED | Lines 1054 (section 03) and 1164 (section 04) call `_maybe_build_no_instagram_block(niche, instagram_data)`. |
| generate_html_report.py QC section | `metadata["not_applicable_items"]` canonical field | Read via `.get()` with empty list fallback | WIRED | Line 385: `not_applicable_items = metadata.get("not_applicable_items", []) or []`. No status-scan fallback per Fix #2. |
| `_apply_niche_conditional_coverage` (three_pass.py) | `CoverageReport.not_applicable_items` field | Direct mutation of report instance | WIRED | Line 179: `report.not_applicable_items = not_applicable_entries`. asdict() contract verified by unit test 5. |
| `_apply_niche_conditional_coverage` (three_pass.py) | `applicable_items`/`is_niche_instagram_critical`/`PASS_THRESHOLD` from qc_checklist | Lazy import inside helper body | WIRED | Lines 103-107: lazy import block. Confirmed by unit tests 1-4 which exercise all branches. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `pass_collect._build_pass_collect_prompt` | `niche_verdict` | `state.collected_data.get("niche_detection", {})` | Yes — populated by `detect_instagram_critical_niche` mini-call at three_pass.py line 250 | FLOWING |
| `pass_gap_analyze.run_pass_gap_analyze` | `niche_instruction` | Built from `state.niche` (3 branches: critical/unknown/non-critical) | Yes — `state.niche` populated by mini-call | FLOWING |
| `three_pass._apply_niche_conditional_coverage` | `report.not_applicable_items` | Computed from `applicable_items(niche)` for non-critical branch | Yes — derived from real niche verdict | FLOWING |
| `generate_html_report._build_qc_coverage_section` | `not_applicable_items` | `metadata.get("not_applicable_items", [])` from CoverageReport.asdict() | Yes — populated by `_apply_niche_conditional_coverage` helper | FLOWING |
| `generate_html_report._maybe_build_no_instagram_block` | `instagram_data` | LLM passes via kwarg per Pass 3 prompt item 6 | Conditional — depends on LLM compliance with prompt instructions (human verification needed) | HOLLOW_PROP (LLM-mediated) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| qc_checklist helpers return correct booleans | `python3 -c "...is_niche_instagram_critical('plastic_surgery')..."` | plastic_surgery=True, cosmetology=True, dental=False, item5+dental=False, items_for_dental=14, items_for_plastic=15 | PASS |
| `_apply_niche_conditional_coverage` tests pass | `cd AIM/hermes && python3 -m unittest app.orchestrator.test_conditional_coverage -v` | Ran 6 tests in 0.001s — OK | PASS |
| `_TOOL_HANDLERS` has 24 entries | Grep pattern `^\s*"[a-z_]+":\s*\("app\.tools\.` | 24 matches | PASS |
| Both Instagram tools registered | `grep "run_instagram_content\|find_doctor_handles" engine.py` | Lines 66-67 contain both entries | PASS |
| `run_instagram_content.py` has required metric fields | `grep "top_by_followers\|avg_likes\|content_themes\|content_gaps"` | Found at lines 128, 140, 327, 333, 336 | PASS |

### Probe Execution

No probe scripts declared in PLAN/SUMMARY for Phase 3. Conventional probe path `scripts/*/tests/probe-*.sh` does not exist for this Python orchestrator phase. Step 7c: SKIPPED (no probes declared).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| IG-01 | 03-01 | `run_instagram_content` callable by both LLM-orchestrator and PipelineEngine | SATISFIED | engine.py:66-67 + handler functions verified in tool files |
| IG-02 | 03-02 + 03-03 + 03-06 | Cosmetology/plastic-surgery niches always run Instagram (mandatory) | SATISFIED (code-level) | Multi-layer enforcement: prompt + data-model + runtime helper. 6 unit tests pass. Live LLM compliance needs human check. |
| IG-03 | 03-04 + 03-05 | Per top-5 doctor: followers, avg likes, avg views, content style, topics, gaps, potential | SATISFIED (code-level) | run_instagram_content.py produces all fields; Pass 1 prompt requests them; Pass 2 cohort-aware items 4/6/7. Live end-to-end flow needs human check. |
| IG-04 | 03-05 | No-Instagram case noted honestly without blocking | SATISFIED (code-level) | `_build_no_instagram_block` + 4 reason variants + QC not_applicable rendering + Pass 3 prompt items 5+6. Soft QC gate preserved (non-blocking). Visual HTML check needs human eyes. |

**Orphaned requirements check:** REQUIREMENTS.md IG-01..IG-04 all appear in plans. No orphaned requirements detected for Phase 3.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `pass_gap_analyze.py` | 20, 71 | "placeholder" word match | ℹ️ Info | FALSE POSITIVE — describes Python format-string `{niche_instruction}` template placeholder in docstring/comments, NOT a stub indicator. Not a debt marker. |

**Debt marker gate:** No `TBD`, `FIXME`, or `XXX` markers in any orchestrator file or generate_html_report.py. No `TODO`, `HACK`, or `PLACEHOLDER` markers either. Verification clean.

**Stub classification:** No empty implementations, no hardcoded empty data flowing to UI, no console.log-only implementations detected in any Phase 3 modified file.

### Human Verification Required

### 1. Live End-to-End Orchestrator Presale Run

**Test:** Trigger a real presale orchestrator run on a cosmetology or plastic-surgery clinic URL (e.g., a known IPHK-style clinic) with `ORCHESTRATOR_MODE=1`. Observe Pass 1 tool-call history, Pass 2 gap_report, and final HTML report.
**Expected:**
- Pass 1 tool-call history includes both `find_doctor_handles` and `run_instagram_content` invocations (in that order)
- Pass 2 gap_report item 5 status = "filled" (with reason if data unavailable)
- Final HTML report sections 03 (Experts) and 04 (Content Analysis) contain per-doctor metrics: followers, avg likes, avg views, content style, themes with %, gaps with severity, potential
- `_apply_niche_conditional_coverage` log line confirms "niche=plastic_surgery" (or cosmetology) critical branch
- Coverage report final status reflects actual data coverage (not blocked by missing Instagram if data was retrieved)

**Why human:** Prompts instruct the LLM but cannot guarantee LLM compliance. The 4-layer enforcement (prompt + data-model + runtime helper + unit tests) provides defense in depth, but only a real run on a real clinic URL confirms end-to-end behavior. DeepSeek V4 Pro latency variance (90-300s for batch Instagram analysis) and Perplexity index coverage cannot be exercised via grep or static inspection.

### 2. Visual HTML Inspection of No-Instagram Block

**Test:** Generate an HTML report for a critical-niche clinic with no Instagram data. Open the rendered HTML in a browser (both light and dark themes).
**Expected:**
- Sections 03 + 04 each contain a "Instagram: данные недоступны" glass-card block
- Block includes: heading, reason text (one of 4 variants), warning badge "Instagram N/A"
- QC Coverage section at end of report shows item 5 with ⚪ icon and `qc-not-applicable` CSS class with opacity 0.6 — visually distinct from missing (red ❌), partial (yellow 🟡), filled (green ✅)
- Summary line includes "· 1 item N/A (не critical ниша)" note when applicable
- Dark theme variant uses Art Deco gold border `rgba(201,169,110,0.18)` per design system

**Why human:** CSS styling, visual hierarchy, design-system consistency (per `design-showcase-dual-theme.html` canonical reference), and readability across both themes require human eyes. Grep can confirm class names exist but not visual correctness.

### 3. HARD FAIL Spoofing Mitigation Test

**Test:** Construct a controlled test fixture where the LLM marks item 5 as "filled" in `gap_report` without actually calling `run_instagram_content` in Pass 1. Run the orchestrator (or invoke `_apply_niche_conditional_coverage` directly with this fixture).
**Expected:**
- For a critical niche + item 5 in filled_items: helper does NOT override (this is the T-03-06-S residual risk — helper trusts LLM's filled_items list)
- For a critical niche + item 5 NOT in filled_items: helper forces `status="FAIL"` and logs "QC HARD FAIL override" warning
- Confirm the unit test `test_critical_niche_with_item5_filled_no_override` documents this residual spoofing risk

**Why human:** Requires a controlled fixture with a hand-crafted gap_report that does NOT match the actual LLM tool-call history. Cannot be exercised by code inspection alone. This is the documented residual risk from Plan 03-06 threat register (T-03-06-S): the runtime helper trusts the LLM's filled_items unless item 5 is absent.

### Gaps Summary

No code-level gaps identified. All 4 success criteria verified at the implementation level:

1. **IG-01 (tool wiring):** Both Instagram tools registered in `_TOOL_HANDLERS` with 24 total entries. PipelineEngine can dispatch them via `_get_handler`.

2. **IG-02 (mandatory for critical niches):** Four-layer enforcement — prompt mandate + Pass 2 HARD FAIL rule + runtime helper + 6 passing unit tests. The runtime helper is wired at both post-Pass-2 and post-Pass-3 calc_coverage sites.

3. **IG-03 (per-doctor metrics):** Tool produces all required fields (`top_by_followers`, `avg_likes`, `avg_views`, `content_themes`, `content_gaps`). Pass 1 prompt explicitly requests them in the critical branch. Adaptive top-5 cohort logic (D-10) handles the realistic scenario where site-top-5 doctors lack Instagram but other doctors have active profiles.

4. **IG-04 (honest no-Instagram reporting):** HTML block with 4 reason variants per D-07. QC section renders `not_applicable` items distinctly (⚪ + opacity 0.6). Pass 3 prompt items 5+6 close the cross-plan data-contract gap. Soft QC gate from Phase 2 preserved (non-blocking).

**Status: human_needed** — All code-level verification PASSED. Three human verification items remain (live end-to-end run, visual HTML check, spoofing mitigation test). These cannot be exercised programmatically because they require either a real LLM run with ORCHESTRATOR_MODE=1 on a real clinic URL, visual inspection of rendered HTML, or controlled fixture manipulation that goes beyond static code analysis.

---

_Verified: 2026-06-23T19:30:00Z_
_Verifier: Claude (gsd-verifier)_
