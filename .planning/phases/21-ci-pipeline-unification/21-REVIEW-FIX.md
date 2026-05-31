---
phase: 21-ci-pipeline-unification
fixed_at: 2026-05-31T21:00:00Z
review_path: .planning/phases/21-ci-pipeline-unification/21-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 21: Code Review Fix Report

**Fixed at:** 2026-05-31T21:00:00Z
**Source review:** .planning/phases/21-ci-pipeline-unification/21-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (3 Critical, 3 Warning)
- Fixed: 6
- Skipped: 0

## Fixed Issues

### CR-01: Tests assert `_run_quick_analysis` exists but method is absent

**Files modified:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`
**Commit:** 7cb84e0
**Applied fix:** Added `_run_quick_analysis` method that executes phases 1-4 with optimized quick-tier path, and added routing call in `execute_ci_analysis` (when `tier == "quick"`, delegates to the new method). The method reuses the existing `_execute_single_phase` and `_execute_parallel_phase` infrastructure.

---

### CR-02: Tests assert stub methods removed but they still exist

**Files modified:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`
**Commit:** 9375fa5
**Applied fix:** Removed six dead methods from the old execution path:
- `_execute_phase_stub` — dead stub, never called by new code
- `_execute_phases` — old orchestrator loop
- `_execute_phase` — old phase dispatcher
- `_execute_parallel_agents` — old parallel executor (used wrong Task kwargs)
- `_execute_single_agent` — old single-agent executor (used wrong Task kwargs)
- `_delegate_to_agent` — returned stub `{"status": "delegated"}`

Updated `execute_task()` (required by Agent interface) to delegate to `execute_ci_analysis()` instead of the removed `_execute_phases` chain. The `_log_completion` call was replaced with inline state file update.

---

### CR-03: Duplicate `SwotQuadrant` and `StealWorthyTactic` dataclasses in two modules

**Files modified:** `AIM/src/aim/services/ci_marketing_analysis.py`
**Commit:** 665d15b
**Applied fix:** Removed local `SwotQuadrant`, `Tactic`, and `StealWorthyTactic` dataclass definitions from `ci_marketing_analysis.py`. Added import from the canonical location: `from .ci.models import SwotQuadrant, StealWorthyTactic`. Updated `TacticExtractor.extract()` return type and all `Tactic()` constructor calls to use `StealWorthyTactic`. The `Tactic` class (which had identical fields but required `why_it_works`/`how_to_implement` without defaults) was eliminated entirely.

---

### WR-01: `execute_task()` returns fake results via dead old path

**Files modified:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`
**Commit:** 9375fa5 (same as CR-02)
**Applied fix:** Resolved by the CR-02 fix. `execute_task()` now extracts parameters from the Task payload and delegates to `execute_ci_analysis()`, returning a properly populated `TaskResult` with real analysis data. The old chain (`_execute_phases` -> `_execute_phase` -> `_execute_single_agent` -> `_delegate_to_agent`) that returned stub `{"status": "delegated"}` has been fully removed.

---

### WR-02: Relative path in `_generate_reports` silently writes to wrong directory

**Files modified:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`
**Commit:** 90120a9
**Applied fix:** Changed `Path("AIM/reports")` (relative, depends on cwd) to `Path(__file__).resolve().parents[5] / "reports"` (absolute, resolved from module location). The `parents[5]` walks up from `.../AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` to the `AIM/` directory, ensuring reports are always written to `{project_root}/AIM/reports/{task_id}` regardless of the process working directory.

---

### WR-03: Multiple transient `ci.agent.completed` subscribers accumulate during parallel phase execution

**Files modified:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`
**Commit:** f1b41d6
**Applied fix:** Replaced per-phase transient `event_bus.subscribe/unsubscribe` pattern with a single dict-based approach:
1. Added `_phase_pending: Dict[str, asyncio.Event]` instance attribute in `__init__`
2. The persistent `_on_agent_completed` handler now checks `_phase_pending.pop(correlation_id)` and signals the matching Event
3. `_execute_single_phase` registers its Event in `_phase_pending[key]` instead of creating a transient subscriber, and cleans up in the `finally` block

This eliminates the N-callback amplification issue (where 9 parallel agents would fire through all 9 transient subscribers per completion event).

---

_Fixed: 2026-05-31T21:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
