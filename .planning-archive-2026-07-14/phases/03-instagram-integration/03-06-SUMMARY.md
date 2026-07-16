---
phase: 03-instagram-integration
plan: 06
subsystem: orchestrator
tags: [orchestrator, qc-gate, hard-fail, conditional-checklist, coverage-reporter, three-pass, runtime-enforcement, instagram-mandatory]

# Dependency graph
requires:
  - phase: 03-instagram-integration
    provides: 03-03 — qc_checklist helpers (is_niche_instagram_critical, applicable_items) + item 5 conditional_on_niche flag
  - phase: 02-3-pass-orchestrator-coverage-checklist
    provides: ORC-01..05 — 3-pass orchestrator core (three_pass.py, coverage_reporter.py, qc_checklist.py)
provides:
  - CoverageReport.not_applicable_items field (new dataclass field, default empty list)
  - three_pass._apply_niche_conditional_coverage(report, niche) helper with 3 branches
  - Helper wired BOTH after Pass 2 calc_coverage AND after Pass 3 final calc_coverage
  - Runtime hard-FAIL override (D-05): critical niche + item 5 missing → status='FAIL' regardless of filled count
  - Runtime conditional-total (D-08): non-critical niche → total_items=14, item 5 in not_applicable_items
  - 6 unit tests (test_conditional_coverage.py) covering all 3 branches + asdict contract
  - IG-02 fully satisfied (combined with Plan 03-03 prompt layer)
affects: [03-05, phase-04, phase-08]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure Python stdlib (ast, dataclasses, logging, unittest)
  patterns:
  - "Runtime hard-FAIL override pattern: helper mutates CoverageReport post-calc_coverage, independent of LLM self-evaluation"
  - "Lazy import inside helper body: is_niche_instagram_critical + applicable_items + PASS_THRESHOLD imported from qc_checklist at call time (matches Plan 03-03 module self-sufficiency convention)"
  - "Same helper called at 2 sites: after Pass 2 (for missing_for_pass3) + after Pass 3 (for final report). Reuses niche_for_coverage variable computed once."
  - "Three-branch dispatch: unknown (identity return) → critical (HARD FAIL check) → non-critical (conditional total)"
  - "Defensive double-check for item 5 filled: 'in filled_items AND not in missing_items' — handles corrupt state where LLM listed item 5 in both buckets"
  - "Synthetic missing_items entry: when HARD FAIL fires and item 5 is absent from missing_items, helper appends synthetic entry so Pass 3 sees it in missing_for_pass3 and tries to fill on next round"
  - "asdict() contract preserved: not_applicable_items defaults to empty list, Phase 2 callers unaffected"
  - "unittest standard library: no pytest dependency (matches test_deep_research_merge.py + test_service_categorizer.py convention)"

key-files:
  created:
  - AIM/hermes/app/orchestrator/test_conditional_coverage.py (234 lines)
  modified:
  - AIM/hermes/app/orchestrator/coverage_reporter.py (+19 lines: not_applicable_items field + docstring)
  - AIM/hermes/app/orchestrator/three_pass.py (+153 lines: _apply_niche_conditional_coverage helper + 2 wire sites + module docstring)

key-decisions:
  - "Helper returns the SAME CoverageReport instance (mutates in place) — preserves identity for callers that compare before/after"
  - "Lazy import inside helper body (from app.orchestrator.qc_checklist import ...) — matches Plan 03-03 module self-sufficiency pattern, avoids top-level circular import risk if qc_checklist ever grows"
  - "niche_for_coverage computed once from state.niche with 'or unknown' fallback — handles empty string (mini-call not run) same as 'unknown' (mini-call failed)"
  - "Synthetic missing_items entry for HARD FAIL case includes 'detail': '' key — preserves dict shape that calc_coverage produces, Pass 3 renderer expects"
  - "Non-critical branch keeps filled_count unchanged (item 5 was never in filled_items per Plan 03-03 prompt instructions to mark it not_applicable)"
  - "Warning log uses 'HARD FAIL' English tag + Russian-adjacent context (niche=X, filled=N/15) — greppable audit trail for T-03-06-R mitigation"
  - "assertLogs context manager in tests catches WARNING-level log — confirms audit trail is emitted, not just the status mutation"
  - "Two extra tests beyond plan (default-empty + asdict key contract) — explicit backward-compat verification for Phase 2 callers"

patterns-established:
  - "Runtime override post-calc_coverage: niche-aware helper wraps niche-unaware calc_coverage output. Separation of concerns — calc_coverage stays deterministic given gap_report; helper layers niche logic on top."
  - "Helper function placement: module-level (not inside async run_three_pass) — unit-testable without async mocking"
  - "Identity-preserving mutation pattern: helper returns same instance after in-place mutation — simpler than creating a new CoverageReport"
  - "Three-branch dispatch in coverage helpers: unknown (safe fallback) → critical (hard override) → non-critical (conditional logic). Tests cover all 3 + edge cases."

requirements-completed: [IG-02]

# Metrics
duration: 4.5min
completed: 2026-06-23
---

# Phase 3 Plan 06: Runtime Hard-FAIL Override + Conditional-Total Summary

**Three_pass.py now mutates CoverageReport post-calc_coverage via a new `_apply_niche_conditional_coverage(report, niche)` helper: critical niches (plastic_surgery/cosmetology) trigger HARD FAIL when Instagram item 5 is missing regardless of other 14 items filled; non-critical niches drop item 5 from total (14 vs 15) and populate a new `CoverageReport.not_applicable_items` field for Plan 03-05 HTML rendering; unknown niche returns input unchanged as safe fallback. Helper is wired at BOTH post-Pass-2 and post-Pass-3 calc_coverage sites. Runtime enforcement completes what Plan 03-03 started at the prompt layer — the LLM is told to FAIL itself, this helper catches any deviation. 6 unit tests pass in 0.002s.**

## Performance

- **Duration:** ~4.5 min (start 18:03:24Z, end 18:08:00Z)
- **Tasks:** 3/3 complete (all `type="auto"`, no checkpoints)
- **Files modified:** 2 (coverage_reporter.py, three_pass.py)
- **Files created:** 1 (test_conditional_coverage.py, 234 lines)
- **Commits:** 3 task commits + 1 final docs commit
- **Test runtime:** 0.002s for 6 unit tests

## Accomplishments

- `CoverageReport.not_applicable_items: list[dict] = field(default_factory=list)` field added between `partial_items` and `coverage_pct` (preserves dataclass field ordering for asdict() stability)
- `_apply_niche_conditional_coverage(report, niche) -> CoverageReport` helper at module level in three_pass.py
- Helper wired at 2 call sites:
  - After Pass 2 `calc_coverage(state.gap_report)` — coverage flows into `state.collected_data["coverage_report_after_pass2"]` and `missing_for_pass3` (Pass 3 sees HARD FAIL synthesized item 5)
  - After Pass 3 `final_coverage = calc_coverage(state.gap_report)` — final coverage report reflects niche-conditional logic for HTML rendering
- Three branches:
  - **Unknown niche** (`"unknown"`): returns report unchanged (safe fallback for mini-call failure)
  - **Critical niche** (`"plastic_surgery"`, `"cosmetology"`): if item 5 not in filled_items (or in missing_items) → forces `status='FAIL'`, synthesizes missing_items entry if absent, logs `QC HARD FAIL override` warning
  - **Non-critical niche**: drops item 5 from total (14 vs 15), populates `not_applicable_items=[{id:5, name:..., reason:"not_applicable for non-critical niche (X)"}]`, filters missing_items to exclude id==5, recomputes coverage_pct with new denominator, re-evaluates PASS/FAIL against PASS_THRESHOLD (0.80)
- 6 unit tests in test_conditional_coverage.py (all PASS):
  1. `test_critical_niche_with_item5_missing_forces_fail` — D-05 HARD FAIL override (uses `assertLogs` for WARNING-level greppable audit trail)
  2. `test_critical_niche_with_item5_filled_no_override` — edge case: critical + filled → no override
  3. `test_non_critical_niche_drops_item5_and_populates_not_applicable` — D-08 conditional total (14 vs 15)
  4. `test_unknown_niche_returns_report_unchanged` — identity check + field equality
  5. `test_coverage_report_asdict_includes_not_applicable_items` — Plan 03-05 consumer contract
  6. `test_coverage_report_default_not_applicable_items_is_empty_list` — Phase 2 backward-compat
- Lazy import pattern inside helper body (`from app.orchestrator.qc_checklist import ...`) — matches Plan 03-03 module self-sufficiency convention
- Module docstrings updated to document Phase 3 / D-05 + D-08 semantics

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend CoverageReport dataclass with not_applicable_items field** — `de442fd` (feat)
2. **Task 2: Add _apply_niche_conditional_coverage helper + wire after Pass 2 + Pass 3** — `9d00948` (feat)
3. **Task 3: Add 6 unit tests for _apply_niche_conditional_coverage** — `d5aa6d4` (test)

**Plan metadata commit:** created after this SUMMARY.

## Files Modified

### `AIM/hermes/app/orchestrator/coverage_reporter.py` (+19 lines, -0 lines)

- Module docstring: added Phase 3 / D-08 paragraph documenting the new field + rationale for keeping calc_coverage niche-unaware
- `CoverageReport` dataclass:
  - New field `not_applicable_items: list[dict] = field(default_factory=list)` positioned AFTER `partial_items` and BEFORE `coverage_pct`
  - Docstring updated with Attributes entry for `not_applicable_items` (purpose, who populates it, HTML consumer)
- `calc_coverage` function: **UNCHANGED** (separation of concerns — niche filtering lives in the helper, not in calc_coverage)
- `format_coverage_text` function: **UNCHANGED** (HTML reporter's job to render not_applicable_items, per plan)

### `AIM/hermes/app/orchestrator/three_pass.py` (+153 lines, -5 lines)

- Module docstring: added Phase 3 / D-05 + D-08 paragraph documenting the helper + 3-branch semantics
- Import block: added `CoverageReport` to the coverage_reporter import (needed for type hint)
- New module-level function `_apply_niche_conditional_coverage(report: CoverageReport, niche: str) -> CoverageReport`:
  - Lazy imports `PASS_THRESHOLD`, `applicable_items`, `is_niche_instagram_critical` from qc_checklist
  - Branch 1: `niche == "unknown"` → returns report unchanged (safe fallback, debug log)
  - Branch 2: `is_niche_instagram_critical(niche)` → HARD FAIL check:
    - `item5_filled = 5 in filled_items and 5 not in [m.id for m in missing_items]`
    - If not filled → `report.status = "FAIL"`, synthesize missing_items entry if absent, `logger.warning` with "QC HARD FAIL override" + "forcing coverage=FAIL" keywords
    - If filled → `logger.info` "no override"
  - Branch 3: non-critical → conditional total (D-08):
    - `applicable_total = len(applicable_items(niche))` → 14 for non-critical
    - Populate `not_applicable_entries` with item 5 entry if 5 not in applicable_ids
    - Filter `missing_items` to exclude id==5
    - Recompute `coverage_pct = filled_count / applicable_total`
    - Re-evaluate `status = "PASS" if new_pct >= PASS_THRESHOLD else "FAIL"`
    - `logger.info` with new total + coverage + status
- `run_three_pass` body:
  - After `coverage_after_p2 = calc_coverage(state.gap_report)` (line 281): new helper call with `niche_for_coverage = state.niche or "unknown"`
  - After `final_coverage = calc_coverage(state.gap_report)` (line 320): same helper call (reuses `niche_for_coverage`)
- Pass 1 invocation: **UNCHANGED** (including mini-call from Plan 03-02)
- Pass 2 invocation: **UNCHANGED**
- Pass 3 invocation: **UNCHANGED**
- Exception handling / fallback: **UNCHANGED**

## Files Created

### `AIM/hermes/app/orchestrator/test_conditional_coverage.py` (234 lines)

- Module docstring documents Phase 3 / D-05 + D-08 runtime hard-FAIL + conditional-total testing
- Imports: `dataclasses`, `logging`, `unittest`, `CoverageReport`, `_apply_niche_conditional_coverage`
- `TestApplyNicheConditionalCoverage` class extends `unittest.TestCase`
- `setUp` builds a base CoverageReport with 14/15 filled, PASS status — shared fixture
- 6 test methods (all pass):
  - `test_critical_niche_with_item5_missing_forces_fail` — uses `assertLogs` for WARNING
  - `test_critical_niche_with_item5_filled_no_override` — edge case
  - `test_non_critical_niche_drops_item5_and_populates_not_applicable` — D-08
  - `test_unknown_niche_returns_report_unchanged` — identity check + 6-field equality
  - `test_coverage_report_asdict_includes_not_applicable_items` — Plan 03-05 contract
  - `test_coverage_report_default_not_applicable_items_is_empty_list` — Phase 2 backward-compat
- `__main__` block runs `unittest.main()`

## Function Signatures Introduced

```python
# three_pass.py
def _apply_niche_conditional_coverage(
    report: CoverageReport, niche: str,
) -> CoverageReport:
    """Mutates report in place based on niche; returns same instance."""
```

## Runtime Behavior Matrix

| Niche | Item 5 in filled? | Item 5 in missing? | Helper action | Result status |
|-------|-------------------|--------------------|---------------|---------------|
| plastic_surgery | NO | NO | Synthesize missing entry, force FAIL | FAIL |
| plastic_surgery | NO | YES | Force FAIL | FAIL |
| plastic_surgery | YES | NO | No override | unchanged |
| plastic_surgery | YES | YES | Treat as not filled → force FAIL | FAIL |
| cosmetology | (any of above) | (any of above) | Same as plastic_surgery | same |
| dental | (any) | (any) | Drop item 5 from total (14), populate not_applicable | recomputed vs 14 |
| general_medicine | (any) | (any) | Same as dental | recomputed vs 14 |
| other | (any) | (any) | Same as dental | recomputed vs 14 |
| unknown | (any) | (any) | Return report unchanged | unchanged |
| "" (not set) | (any) | (any) | Treated as unknown → return unchanged | unchanged |

## Verification Artifacts

| Check | Result |
|-------|--------|
| `coverage_reporter.py` AST parse | OK (CoverageReport has 7 fields including not_applicable_items, positioned AFTER partial_items, BEFORE coverage_pct) |
| `three_pass.py` AST parse | OK (helper function defined at module level; 4 occurrences of `_apply_niche_conditional_coverage` = 1 def + 2 call sites + 1 docstring reference) |
| `test_conditional_coverage.py` AST parse | OK (6 test methods, TestApplyNicheConditionalCoverage class) |
| Helper wired AFTER Pass 2 calc_coverage | Yes (`helper_call_idx > pass2_calc_idx`) |
| Helper wired AFTER Pass 3 calc_coverage | Yes (`helper_call_idx > pass3_calc_idx`) |
| `is_niche_instagram_critical` imported | Yes (lazy, inside helper body) |
| `applicable_items` imported | Yes (lazy, inside helper body) |
| `PASS_THRESHOLD` imported | Yes (lazy, inside helper body) |
| Hard FAIL keywords present | Yes (`"HARD FAIL"` + `"forcing coverage=FAIL"`) |
| `not_applicable_items` populated | Yes (in non-critical branch) |
| All 6 unit tests pass | Yes (0.002s, `python3 -m unittest`) |
| Regression: `ORCHESTRATOR_MODE=0` default path | Yes — helper only runs inside `run_three_pass` which only fires when ORCHESTRATOR_MODE=1 |
| Regression: calc_coverage itself unchanged | Yes — only asdict output shape changes (new key) |
| Regression: format_coverage_text unchanged | Yes — does not render not_applicable_items (HTML renderer's job in Plan 03-05) |
| Regression: Pass 1 invocation unchanged | Yes |
| Regression: Pass 2 invocation unchanged | Yes |
| Regression: Pass 3 invocation unchanged | Yes |
| Regression: Mini-call from Plan 03-02 unchanged | Yes (lines 240-258 byte-identical) |
| Regression: Phase 2 callers (default CoverageReport) | Yes — `not_applicable_items` defaults to empty list |
| Post-commit deletion check | None (no tracked files deleted across 3 commits) |
| Untracked file check | None created by this plan (existing untracked files unchanged) |

## Test Output

```
test_critical_niche_with_item5_filled_no_override ... ok
test_critical_niche_with_item5_missing_forces_fail ... ok
test_non_critical_niche_drops_item5_and_populates_not_applicable ... ok
test_unknown_niche_returns_report_unchanged ... ok
test_coverage_report_asdict_includes_not_applicable_items ... ok
test_coverage_report_default_not_applicable_items_is_empty_list ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.002s

OK
```

## Decisions Made

1. **Helper mutates in place + returns same instance** — Simpler than creating a new CoverageReport. Callers that want before/after comparison can `dataclasses.replace(report)` first. Identity preservation makes "unknown niche returns report unchanged" testable via `assertIs`.

2. **Lazy import inside helper body** — Imports `PASS_THRESHOLD`, `applicable_items`, `is_niche_instagram_critical` at call time, not at module top. Matches the convention established by Plan 03-03 (which used the same pattern in `pass_gap_analyze.run_pass_gap_analyze`). Trade-off: 3 extra lines per call; benefit: avoids any future circular-import risk if `qc_checklist` grows dependencies.

3. **`niche_for_coverage = state.niche or "unknown"` computed once** — Handles the "" case (mini-call not yet run) and the "unknown" case (mini-call failed) identically. Computed at the first call site and reused at the second. Avoids redundant `or` operations.

4. **Defensive double-check for item 5 filled** — `5 in filled_items AND 5 not in missing_items`. Handles corrupt state where LLM (incorrectly) lists item 5 in BOTH filled_items and missing_items. The helper treats this as "not filled" → HARD FAIL fires. This is intentional: when in doubt, FAIL the report rather than falsely PASS.

5. **Synthetic missing_items entry includes `"detail": ""`** — Preserves dict shape that calc_coverage produces. Pass 3 renderer iterates missing_items and reads `m.get("detail", "")` — synthetic entry matches this contract.

6. **Non-critical branch keeps filled_count unchanged** — Per Plan 03-03 Pass 2 prompt, the LLM is instructed to mark item 5 as `not_applicable` (4th status value), NOT as `filled`. So item 5 was never in filled_items for non-critical niches. The helper does NOT remove item 5 from filled_items (defensive — if LLM mistakenly filled it, the high coverage is acceptable for a non-critical niche).

7. **Two extra tests beyond plan spec** — Plan required 5 tests; we have 6. The extras:
   - `test_coverage_report_default_not_applicable_items_is_empty_list` — explicit Phase 2 backward-compat verification
   - These make the data-contract guarantees visible in test output, not just in code comments.

8. **`assertLogs("app.orchestrator.three_pass", level="WARNING")`** — Catches the audit-trail log. Plan acceptance criteria required "logs a warning with 'HARD FAIL' or 'forcing coverage=FAIL'". The test verifies the log is actually emitted (T-03-06-R mitigation), not just that status is mutated.

## Deviations from Plan

None — plan executed exactly as written. All 3 tasks followed the action steps verbatim:

- Task 1: Added `not_applicable_items: list[dict] = field(default_factory=list)` between `partial_items` and `coverage_pct`; updated dataclass docstring + module docstring; calc_coverage logic untouched ✓
- Task 2: Defined `_apply_niche_conditional_coverage` at module level with 3 branches (unknown / critical / non-critical); wired after Pass 2 calc_coverage (line 281→286) AND after Pass 3 calc_coverage (line 320→324); `niche_for_coverage = state.niche or "unknown"` computed once; Pass 1/2/3 invocation logic unchanged ✓
- Task 3: Created test_conditional_coverage.py with 6 test methods (plan required 5 — added 1 extra for backward-compat verification); all tests pass via `python3 -m unittest` ✓

## Known Stubs

None. The helper is fully implemented across all 3 branches with unit test coverage. No placeholder values, no TODO/FIXME, no hardcoded empty buckets that flow to UI rendering.

## Threat Flags

None. The threat surface (Python helper function + dataclass field) is fully covered by the plan's existing threat model:

- T-03-06-S (Spoofing — LLM falsely marks item 5 as filled): partially mitigated — helper trusts `5 in filled_items` check; if LLM outright fabricates filled status, this check trusts the LLM. Plan 03-03 prompt rule + Perplexity cost logs provide additional signals. Full cross-check against actual tool-call history is a future hardening (documented in plan threat register).
- T-03-06-T (Tampering — state.niche overwritten): accept — OrchestratorState is single-threaded per session; niche set once by Plan 03-02 mini-call.
- T-03-06-R (Repudiation — hard-FAIL not logged): mitigated by `logger.warning("QC HARD FAIL override: ...")` with niche + filled count. Test verifies warning is emitted via `assertLogs`.
- T-03-06-I (Info disclosure — niche label in logs): accept — niche derived from public clinic website data.
- T-03-06-D (DoS): accept — helper adds O(15) operations per coverage calc.
- T-03-06-E (EoP): N/A — no privilege change.

## User Setup Required

None — purely additive orchestrator change, opt-in via `ORCHESTRATOR_MODE=1` (default OFF). Production presale flow unaffected. No deployment required for this plan (changes are Python helper + dataclass field; they take effect next time the orchestrator runs).

## Next Phase Readiness

- **Ready for Plan 03-04** (Adaptive top-5 doctor selection) — `state.collected_data["niche_detection"]` from Plan 03-02 + Instagram batch results from Pass 1 (mandated by Plan 03-03 prompt for critical niches) provide the inputs Plan 03-04 needs for followers_count-based reordering fallback (D-10).
- **Ready for Plan 03-05** (HTML rendering) — `CoverageReport.not_applicable_items` field is populated by this plan's helper. Plan 03-05 HTML can read it via `metadata.get("not_applicable_items", [])` (asdict contract verified by test). The HTML QC section can render not-applicable items with distinct icon (⚪) + gray styling, separate from filled/missing/partial.
- **IG-02 fully SATISFIED** — combined with Plan 03-03 prompt layer:
  - Plan 03-03: LLM is INSTRUCTED to mark item 5 missing (HARD FAIL rule in Pass 2 prompt)
  - Plan 03-06 (this plan): runtime ENFORCES HARD FAIL even if LLM deviates
  - Result: for plastic_surgery/cosmetology clinics, missing Instagram analysis guarantees coverage=FAIL in the final report regardless of what LLM self-evaluation says.

## Self-Check: PASSED

- FOUND: `AIM/hermes/app/orchestrator/coverage_reporter.py` (with `not_applicable_items: list[dict] = field(default_factory=list)` field positioned between `partial_items` and `coverage_pct`)
- FOUND: `AIM/hermes/app/orchestrator/three_pass.py` (with `_apply_niche_conditional_coverage` helper at module level, wired after Pass 2 calc_coverage at line 286 and after Pass 3 calc_coverage at line 324)
- FOUND: `AIM/hermes/app/orchestrator/test_conditional_coverage.py` (6 test methods, all PASS via `python3 -m unittest`)
- FOUND: commit `de442fd` (Task 1: feat — CoverageReport not_applicable_items field)
- FOUND: commit `9d00948` (Task 2: feat — _apply_niche_conditional_coverage helper + 2 wire sites)
- FOUND: commit `d5aa6d4` (Task 3: test — 6 unit tests for all 3 branches + asdict contract)

---
*Phase: 03-instagram-integration*
*Completed: 2026-06-23*
