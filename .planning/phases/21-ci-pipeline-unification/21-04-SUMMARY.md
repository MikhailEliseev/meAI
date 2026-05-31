---
phase: 21-ci-pipeline-unification
plan: 04
subsystem: api
tags: [fastapi, sse, ci-orchestrator, singleton, gap-closure]

# Dependency graph
requires: []
provides:
  - "/api/competitors/analyze/stream SSE endpoint now reuses SEO API's singleton CIOrchestrator via _get_orchestrator()"
  - "/api/competitors/analyze endpoint also uses shared orchestrator; standalone _run_quick_ci_analysis deleted"
  - "SSE stream emits progress events via CIOrchestrator progress_callback bridge"

affects: [hermes-tools]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pattern: inline import _get_orchestrator from aim.api.seo — avoids import-time side effects"
    - "pattern: _extract_named_urls helper extracts URL strings from mixed CompetitorMatch/dict/str objects"
    - "pattern: progress_callback bridge maps CIOrchestrator (phase_num, status, msg) to SSE progress events"

key-files:
  modified:
    - AIM/src/aim/api/competitors.py

key-decisions:
  - "Use inline import of _get_orchestrator (not top-level) to avoid import-time EventBus initialization"
  - "Handle dict results from execute_ci_analysis with .get() defaults for backward-compatible response format"
  - "Extract steal_worthy_tactics and feature_matrix from findings when not present at result top level"

requirements-completed: [D-11]

# Metrics
duration: 3min
completed: 2026-05-31
---

# Phase 21 Plan 04: SSE Stream Alias via Shared CIOrchestrator Summary

**Converted /api/competitors/analyze/stream from standalone CIOrchestrator-per-request to true SSE alias reusing SEO API's singleton via _get_orchestrator() — closing gap SC7.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-31T20:10:58Z
- **Completed:** 2026-05-31T20:14:19Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Deleted standalone `_run_quick_ci_analysis` function that created EventBus + CIOrchestrator per request
- Both `/analyze` and `/analyze/stream` now call `execute_ci_analysis(task_data, progress_callback)` via shared singleton
- Added `_extract_named_urls` helper to extract URLs from mixed `CompetitorMatch`/dict/str objects
- SSE progress callback bridge maps CIOrchestrator `(phase_num, status, message)` to SSE progress events
- Backward-compatible response format with dict `.get()` fallbacks for missing fields
- Removed dead `HTTPException` import

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite /analyze/stream to use shared CIOrchestrator singleton** — `6026f23` (feat)
2. **Task 2: Remove dead imports and verify both endpoints work** — `eb25601` (chore)

## Files Created/Modified

- `AIM/src/aim/api/competitors.py` — Deleted `_run_quick_ci_analysis`, added `_extract_named_urls`, rewrote `/analyze` and `/analyze/stream` endpoints to use shared orchestrator singleton

## Decisions Made

- Used inline import `from aim.api.seo import _get_orchestrator` inside endpoint functions (not top-level) to avoid import-time EventBus initialization side effects
- Response mapping uses `result.get("field", default)` throughout — handles the fact that `execute_ci_analysis` returns a dict with `findings`, `reports`, `errors` but not `chat_summary`, `feature_matrix` directly (those were from the old CiMarketingAnalyzer pipeline)
- Added fallback extraction of `steal_worthy_tactics` and `feature_matrix` from `findings` sub-dicts when not present at result top level

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Initial attempt to remove `status` import caused `NameError` — restored it since it's used in route decorators (`status.HTTP_200_OK`)
- Initial route verification used wrong path prefix (`/analyze/stream` vs `/api/competitors/analyze/stream`) — corrected

## Threat Flags

None — this change reduces attack surface by eliminating per-request EventBus creation. The STRIDE threats documented in the plan (T-21-13, T-21-14, T-21-15) are accept/mitigate dispositions with no new exposure.

## Known Stubs

None — no stubs or placeholders introduced. Response fields default to empty when not produced by the CIOrchestrator's quick tier, which is intentional (the unified pipeline produces structured findings rather than the old CiMarketingAnalyzer format).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Gap SC7 is closed: `/api/competitors/analyze/stream` is now a true alias reusing the shared CIOrchestrator singleton
- Hermes tool `run_ci_analysis.py` remains backward-compatible with the SSE event format
- Phase 21 pipeline unification is now complete across all 4 plans

---
*Phase: 21-ci-pipeline-unification*
*Completed: 2026-05-31*
