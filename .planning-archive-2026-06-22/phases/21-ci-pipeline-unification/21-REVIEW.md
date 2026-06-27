---
phase: 21-ci-pipeline-unification
reviewed: 2026-05-31T20:45:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py
  - AIM/src/aim/services/ci/models.py
  - AIM/src/aim/services/ci_marketing_analysis.py
  - AIM/tests/subagents/test_ci_pipeline_integration.py
findings:
  critical: 3
  warning: 3
  info: 2
  total: 8
status: issues_found
---

# Phase 21: Code Review Report

**Reviewed:** 2026-05-31T20:45:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 21 aimed to convert CI agents to real EventBus delegation and remove the old direct `agent.execute_task()` fallback path. The core changes — making `_get_agent()` async with `initialize()`, injecting shared EventBus, bridging `report_result` to publish `ci.agent.completed` Events, and building the new `_execute_single_phase` path — are structurally sound. However, three problems block this phase from shipping:

1. **Tests assert the old code was removed, but it wasn't.** Three methods (`_delegate_to_agent`, `_execute_single_agent`, `_execute_phase_stub`) and one string reference (`_run_quick_analysis`) are asserted absent but still exist in the source. These tests will fail.

2. **Duplicate data model classes** between `ci/models.py` and `ci_marketing_analysis.py` (`SwotQuadrant`, `StealWorthyTactic`). Two separate definitions with identical field names means `isinstance()` checks and static type analysis will silently break at module boundaries.

3. **Dead code from the old execution path** remains in the class (`_delegate_to_agent`, `_execute_single_agent`, `_execute_parallel_agents`, `_execute_phase`, `_execute_phases`, `_execute_phase_stub`). The `execute_task()` Agent-interface method still routes through this dead path and returns fake results.

---

## Critical Issues

### CR-01: Tests assert `_run_quick_analysis` exists but method is absent

**File:** `AIM/tests/subagents/test_ci_pipeline_integration.py:626`
**Issue:** The test `test_orchestrator_tier_routing_has_quick_path` asserts:
```python
src = inspect.getsource(CIOrchestrator.execute_ci_analysis)
assert "_run_quick_analysis" in src
```
The string `_run_quick_analysis` does not appear anywhere in `CIOrchestrator.execute_ci_analysis` or anywhere else in `ci_orchestrator.py`. This test will fail with `AssertionError`.

**Fix:** Either add a `_run_quick_analysis` method and call it from `execute_ci_analysis` when `tier == "quick"`, or remove the assertion if quick-path routing is handled differently:
```python
# Option A: Add the method and route to it
async def _run_quick_analysis(self, task_data: dict, correlation_id: str) -> dict:
    """Run phases 1-4 only."""
    ...

# Option B: Remove the assertion — the tier-based phase selection
# already handles quick path via self.tiers["quick"]["phases"]
assert "tier" in src and "quick" in src
```

---

### CR-02: Tests assert stub methods removed but they still exist

**File:** `AIM/tests/subagents/test_ci_pipeline_integration.py:514-518`
**Issue:** The test `test_path2_stubs_removed` asserts three methods do NOT exist on `CIOrchestrator`:
```python
assert not hasattr(CIOrchestrator, "_delegate_to_agent")
assert not hasattr(CIOrchestrator, "_execute_single_agent")
assert not hasattr(CIOrchestrator, "_execute_phase_stub")
```
All three methods ARE defined in `ci_orchestrator.py`:
- `_delegate_to_agent` — line 970
- `_execute_single_agent` — line 942
- `_execute_phase_stub` — line 713

These tests will fail. The Phase 21 description says "Removed EventBus fallback", but the old code path was left in place.

**Fix:** Remove the six dead methods from `ci_orchestrator.py`:
- `_delegate_to_agent` (lines 970-999)
- `_execute_single_agent` (lines 942-968)
- `_execute_parallel_agents` (lines 893-940)
- `_execute_phase` (lines 865-891)
- `_execute_phases` (lines 840-863)
- `_execute_phase_stub` (lines 713-730)

Then update or remove `execute_task` (lines 732-774) since it routes through `_execute_phases` which will no longer exist. If `execute_task` is still needed as the Agent-interface method, it should delegate to `execute_ci_analysis` instead.

---

### CR-03: Duplicate `SwotQuadrant` and `StealWorthyTactic` dataclasses in two modules

**Files:**
- `AIM/src/aim/services/ci/models.py:186,195`
- `AIM/src/aim/services/ci_marketing_analysis.py:56,74`

**Issue:** Both `ci/models.py` and `ci_marketing_analysis.py` define their own `SwotQuadrant` and `StealWorthyTactic` dataclasses with identical field names. These are DIFFERENT Python classes. Any code that performs `isinstance(obj, SwotQuadrant)` using one module's import on an object constructed with the other module's class will return `False`. Static type checkers (mypy/pyright) will flag type mismatches at module boundaries.

This matters because:
- `ci/models.py:SwotQuadrant` is used by `UnifiedCiResult.aggregate_swot`
- `ci_marketing_analysis.py:SwotQuadrant` is used by `CiAnalysisResult.aggregate_swot` and `SwotEngine`
- The test file imports from BOTH modules (lines 24-29 and line 636)
- If the orchestrator mixes data from both analysis paths, type checks will silently fail

**Fix:** Consolidate into a single definition in `ci/models.py` and import from there everywhere:
```python
# In ci_marketing_analysis.py — REMOVE local SwotQuadrant, StealWorthyTactic, Tactic
# Add import:
from .ci.models import SwotQuadrant, StealWorthyTactic
```

Also remove the redundant `Tactic` class (line 64-71 in `ci_marketing_analysis.py`) — `StealWorthyTactic` has the same fields and is the canonical name.

---

## Warnings

### WR-01: `execute_task()` returns fake results via dead old path

**File:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py:732-774`
**Issue:** The `execute_task()` method (required by the `Agent` interface) routes through `_execute_phases` → `_execute_phase` → `_execute_single_agent` / `_execute_parallel_agents` → `_delegate_to_agent`. The `_delegate_to_agent` method publishes an event to the EventBus but returns a static stub (`{"status": "delegated", "task_id": ...}`) without waiting for actual agent completion. Every phase will return `status: "delegated"` with no real data.

Additionally, the `Task` constructor in the old path uses `id=` and `type=` (lines 912-913, 959-960) which are NOT valid field names for the `Task` dataclass (which has `task_id`, `subtask_id`, etc.). If this code path is ever reached, it will raise `TypeError`.

Any code that calls `agent.execute_task(task)` will receive a `TaskResult` filled with placeholder stubs instead of real CI analysis data.

**Fix:** Same as CR-02 — remove the dead methods and have `execute_task` delegate to `execute_ci_analysis`:
```python
async def execute_task(self, task: Task) -> TaskResult:
    try:
        task_data = {
            "task_id": task.task_id,
            "niche": task.data.get("niche", ""),
            "geo": task.data.get("geo", ""),
            "tier": self._detect_tier(task.data),
            "competitors": task.data.get("competitors", []),
        }
        result = await self.execute_ci_analysis(task_data)
        return TaskResult(
            task_id=task.task_id,
            status="completed" if not result.get("errors") else "failed",
            result=result,
        )
    except Exception as e:
        return TaskResult(
            task_id=task.task_id,
            status="failed",
            result={"error": str(e)},
        )
```

---

### WR-02: Relative path in `_generate_reports` silently writes to wrong directory

**File:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py:599`
**Issue:** The report directory uses a relative path:
```python
reports_dir = Path("AIM/reports") / task_id
```
If the process working directory is not the project root, reports will be written to an unexpected location. There is no error raised — the directory is silently created wherever `AIM/reports/` resolves.

**Fix:** Use an absolute path resolved from the module location:
```python
from pathlib import Path
_REPORTS_ROOT = Path(__file__).parent.parent.parent.parent.parent / "AIM" / "reports"
reports_dir = _REPORTS_ROOT / task_id
```

---

### WR-03: Multiple transient `ci.agent.completed` subscribers accumulate during parallel phase execution

**File:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py:480-485,510-543`
**Issue:** During parallel phase execution (Phase 5), each agent spawns a `_execute_single_phase` call that subscribes a transient `on_agent_completed` handler. All N handlers process every `ci.agent.completed` event via `correlation_id` filtering. While functionally correct (only the matching correlation_id triggers the `Event.set()`), this means every agent completion fires through all N transient subscribers. The persistent `_on_agent_completed` handler also processes every event (line 85).

For N=9 parallel agents (Phase 5), this means 10 subscriber callbacks per completion event. Not a correctness issue at small scale, but the pattern signals a design gap — a single subscriber with an in-memory correlation-to-Event mapping would be cleaner.

**Fix:** Replace per-phase transient subscribers with a single dict-based approach:
```python
# Class-level: _phase_pending: dict[str, asyncio.Event] = {}
# In _execute_single_phase:
self._phase_pending[phase_correlation] = asyncio.Event()
# In persistent _on_agent_completed:
event = self._phase_pending.pop(correlation_id, None)
if event:
    event.set()
```
This avoids N transient subscriptions and cleanup concerns.

---

## Info

### IN-01: Dead code from old execution path not cleaned up

**File:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py:713-730,840-999`
**Issue:** Six methods remain from the pre-Phase-21 execution path. They are either dead code (unreachable from the new `execute_ci_analysis` path) or broken (returning stubs through the `execute_task` path). The Phase 21 description states "Removed EventBus fallback — EventBus delegation is now the ONLY path", but the old code was not removed.

Affected methods:
- `_execute_phase_stub` (line 713) — dead, never called
- `execute_task` (line 732) — routes through broken old path
- `_execute_phases` (line 840) — old orchestrator, unused by new path
- `_execute_phase` (line 865) — old dispatcher
- `_execute_parallel_agents` (line 893) — constructs Task with wrong kwargs
- `_execute_single_agent` (line 942) — constructs Task with wrong kwargs
- `_delegate_to_agent` (line 970) — returns stub, has TODO comment `# Пока возвращаем заглушку`

**Fix:** Remove all seven methods. See CR-02 for specifics.

---

### IN-02: Unused `SwotQuadrant` import in test file

**File:** `AIM/tests/subagents/test_ci_pipeline_integration.py:26`
**Issue:** The import line reads:
```python
from aim.services.ci_marketing_analysis import (
    CiAnalysisResult,
    SwotQuadrant,
    StealWorthyTactic,
    _tactic_impact_effort,
)
```
`SwotQuadrant` is imported but never referenced by name in the test functions. The `TestUnifiedArchitecture` class later imports it again from `aim.services.ci.models` (line 636). This unused import adds noise and suggests the test author wasn't sure which module the class lives in — a symptom of the duplicate class problem (CR-03).

**Fix:** Remove `SwotQuadrant` from the `ci_marketing_analysis` import. After consolidating the duplicate dataclasses (CR-03), all imports should come from `aim.services.ci.models`.

---

_Reviewed: 2026-05-31T20:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
