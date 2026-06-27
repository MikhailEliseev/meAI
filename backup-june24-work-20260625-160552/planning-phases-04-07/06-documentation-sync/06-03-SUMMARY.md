---
phase: 06-documentation-sync
plan: 03
subsystem: testing
tags: [unit-tests, unittest, pytest, regression-guard, grep-audit, documentation-sync, engine, tool-handlers]

# Dependency graph
requires:
  - phase: 06-documentation-sync
    provides: Plan 06-01 SOUL.md v5 rewrite + Plan 06-02 SKILL.md v2.0.0/phases.py LEGACY (cleaned phantom phases)
  - phase: 04-new-sections-data-depth
    provides: _TOOL_HANDLERS registry at 26 entries (Phase 4 added run_forum_pains + run_media_urls)
provides:
  - pytest-discoverable + unittest-runnable regression guard for _TOOL_HANDLERS count drift
  - Objective audit evidence that zero phantom phase IDs (0.5/0.75/0.8/3.2) exist in active runtime docs
  - Container-deployed test file at /opt/hermes/app/pipeline/test_engine_handlers.py
  - 5-section audit report documenting 88 grep invocations across 11 files × 8 patterns
affects: [future-tool-additions, phase-transitions, phase-7-niche-testing]

# Tech tracking
tech-stack:
  added: []  # No new libraries — unittest is stdlib
  patterns:
  - "Regression guard via MIN_HANDLERS constant — bump when new tools are intentionally added"
  - "unittest.TestCase over plain pytest functions when container lacks pytest (stdlib portability)"
  - "Grep audit pattern: META-references (requirement text, audit log, historical context) are not bugs"
  - "Word-boundary regex \\b0\\.8\\b correctly excludes 0.80 coverage threshold (PASS_THRESHOLD)"

key-files:
  created:
  - AIM/hermes/app/pipeline/test_engine_handlers.py
  - .planning/phases/06-documentation-sync/06-PHANTOM-PHASE-AUDIT.md
  modified: []  # No source files modified — test verifies existing engine.py behavior

key-decisions:
  - "Rule 3 refactor: container Python 3.11.15 lacks pytest → use unittest.TestCase (stdlib). Plan said `python -m pytest` but intent was test-must-pass-in-container; unittest satisfies intent without adding dependency. Test remains pytest-discoverable if/when pytest is installed."
  - "MIN_HANDLERS constant (26) makes future bumps a one-line change — D-08 enforcement lives in one named place."
  - "META-references preserved: PROJECT.md line 72, STATE.md line 146, REQUIREMENTS.md line 70 all reference phantom phases as audit trail / requirement text / historical context — explicitly NOT cleaned up, they document the problem Phase 6 solved."
  - "SOUL.backup.md match `0.80` flagged as false positive — PASS_THRESHOLD coverage value, not phase ID. Word-boundary regex correctly excludes it."

patterns-established:
  - "Container-deployed test pattern: cat local.py | ssh aim 'docker exec -i aim-hermes tee remote.py' > /dev/null — pipe-through-stdin, no docker cp needed"
  - "unittest invocation in container: `python -m unittest app.pipeline.test_engine_handlers -v` (uses Python module path, not file path)"
  - "Phantom phase grep pattern: `\\b(0\\.5|0\\.75|0\\.8|3\\.2)\\b` for numeric + `(Phase|Фаза|фаза)\\s+(0\\.5|...)` for phase-context (catches English+Russian)"
  - "META-vs-active distinction: requirements text, audit logs, historical context = META references (preserve); actual phase IDs in operational docs = phantom phases (clean)"

requirements-completed: [SYN-04, SYN-05]

# Metrics
duration: 8min
completed: 2026-06-24
---

# Phase 6 Plan 06-03: _TOOL_HANDLERS Assertion Test + Phantom Phase Audit Summary

**4-test unittest regression guard for _TOOL_HANDLERS (26 entries) deployed to container + 88-pattern grep audit confirming zero phantom phases (0.5/0.75/0.8/3.2) in active runtime documentation**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-24T04:46:04Z
- **Completed:** 2026-06-24T04:54:32Z
- **Tasks:** 3/3
- **Files modified:** 2 created, 0 modified source files

## Accomplishments
- Created `AIM/hermes/app/pipeline/test_engine_handlers.py` — 4 unittest tests asserting _TOOL_HANDLERS count ≥ 26, value tuple structure, critical Phase 3-5 tools present, all handler modules importable
- Performed comprehensive grep audit across 11 files × 8 patterns (88 invocations) and documented verdict: **PASS — zero phantom phase IDs in active runtime documentation**
- Deployed test file to container `/opt/hermes/app/pipeline/test_engine_handlers.py` (md5 byte-for-byte match `7fda54d3c2dd82770108f3f3c4b8c17b`)
- Verified all 4 tests pass inside container Python 3.11.15 via `python -m unittest -v` (0.143s)
- Final Phase 6 integration confirmed: orchestrator imports OK, QC_CHECKLIST v1.2.0, _TOOL_HANDLERS=26, PHASES=14

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_engine_handlers.py with _TOOL_HANDLERS count assertion (per D-08)** — `8f53eb9` (test) — initial pytest-style version with 4 module-level test functions
2. **Task 2: Run phantom phase grep audit across all documentation files (per D-07, D-10)** — `6411d3e` (docs) — 135-line audit report with 5 sections, verdict PASS
3. **Task 3: Deploy test_engine_handlers.py to container and run pytest inside container Python 3.11** — `910bc47` (fix) — Rule 3 refactor from pytest to unittest (container lacks pytest)

## Files Created/Modified

- `AIM/hermes/app/pipeline/test_engine_handlers.py` — NEW — 4 unittest tests guarding _TOOL_HANDLERS registry drift. Uses MIN_HANDLERS=26 constant + CRITICAL_TOOL_NAMES frozenset (run_instagram_content, find_doctor_handles, run_forum_pains, run_media_urls). Pattern follows `app/orchestrator/test_conditional_coverage.py`.
- `.planning/phases/06-documentation-sync/06-PHANTOM-PHASE-AUDIT.md` — NEW — 135-line audit report documenting grep results across 11 files × 8 patterns. Verdict PASS. Documents 3 META-references (intentional) + 1 false positive (0.80 coverage threshold).
- `aim-hermes` container `/opt/hermes/app/pipeline/test_engine_handlers.py` — DEPLOYED — md5 `7fda54d3c2dd82770108f3f3c4b8c17b` matches local

## Decisions Made

- **Rule 3 unittest refactor:** Container has Python 3.11.15 + stdlib but pytest is NOT installed. Plan required `python -m pytest`; pytest unavailable. Chose to refactor test from plain pytest functions to `unittest.TestCase` class (stdlib-only). Rationale: (a) matches existing pattern in `test_conditional_coverage.py`; (b) unittest tests remain pytest-discoverable if/when pytest is installed; (c) avoids adding new container dependency; (d) satisfies plan intent ("test must pass inside container Python 3.11").
- **MIN_HANDLERS constant pattern:** Used module-level constant `MIN_HANDLERS = 26` instead of magic number, making future tool additions a one-line bump. Same pattern for `CRITICAL_TOOL_NAMES` frozenset.
- **META-references preserved, not cleaned:** Three textual matches in PROJECT.md/STATE.md/REQUIREMENTS.md were intentionally left in place. They reference phantom phases in META context (requirement text, audit log, historical v3 description) — removing them would erase the audit trail documenting what Phase 6 solved.
- **False-positive identification:** SOUL.backup.md match `0.80` correctly identified as PASS_THRESHOLD coverage value, not phantom phase. Word-boundary regex `\b0\.8\b` excludes `0.80` (zero follows 8).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Container lacks pytest — refactored test to unittest**
- **Found during:** Task 3 (deploy + pytest inside container)
- **Issue:** Plan verification step `ssh aim "docker exec aim-hermes python -m pytest ..."` failed with `No module named pytest`. Container Python 3.11.15 has stdlib only — pytest was never installed in this image.
- **Fix:** Refactored `test_engine_handlers.py` from plain pytest functions to `unittest.TestCase` class. unittest is stdlib, always available. The test is still pytest-discoverable for future use (pytest can run unittest.TestCase natively).
- **Files modified:** `AIM/hermes/app/pipeline/test_engine_handlers.py` (142 → 166 lines)
- **Verification:** `python -m unittest app.pipeline.test_engine_handlers -v` inside container: 4 tests pass in 0.143s
- **Committed in:** `910bc47` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Refactor was necessary for plan verification to pass. No scope creep — test behavior identical, only framework adapter changed. Plan intent ("assertion test must run inside container Python 3.11") fully satisfied.

## Issues Encountered

- pytest not in container image — resolved via Rule 3 unittest refactor (above).
- Word-boundary regex learning: initial plain `0\.5|0\.75|0\.8|3\.2` would have caught `0.80` as substring of `0.8`. Used `\b(0\.5|0\.75|0\.8|3\.2)\b` form for numeric patterns to exclude version-like decimals. Documented in audit report Section 3.

## User Setup Required

None — no external service configuration required. All work performed against existing container + local repo.

## Next Phase Readiness

- **Phase 6 COMPLETE** — all 3 plans (06-01 SOUL.md, 06-02 SKILL.md/phases.py, 06-03 test+audit) delivered. SYN-01..05 all satisfied.
- **Phase 7 (Test on 3 Niches) ready** — orchestrator + documentation + tests all in sync. Real-world validation can begin.
- **No blockers** — container healthy (uptime 164001s = ~45h, no restart needed during Phase 6).
- **Test cadence recommendation:** Re-run phantom phase grep audit before each phase transition (5-second check). Optionally extend `test_engine_handlers.py` with similar guards for QC_CHECKLIST version + CRITICAL_NICHES tuple.

## Container Verification Snapshot

```
Container: aim-hermes (Python 3.11.15)
Test file md5: 7fda54d3c2dd82770108f3f3c4b8c17b
unittest result: Ran 4 tests in 0.143s — OK
Integration check: orchestrator=OK qc_version=1.2.0 handlers=26 phases=14
Health: {"status":"ok","hermes":"healthy","uptime_seconds":164001}
```

## Self-Check: PASSED

- FOUND: AIM/hermes/app/pipeline/test_engine_handlers.py
- FOUND: .planning/phases/06-documentation-sync/06-PHANTOM-PHASE-AUDIT.md
- FOUND: .planning/phases/06-documentation-sync/06-03-SUMMARY.md
- FOUND: 8f53eb9 (Task 1 test commit)
- FOUND: 6411d3e (Task 2 docs commit)
- FOUND: 910bc47 (Task 3 unittest refactor commit)

All artifacts and commits verified present.

---
*Phase: 06-documentation-sync*
*Completed: 2026-06-24*
