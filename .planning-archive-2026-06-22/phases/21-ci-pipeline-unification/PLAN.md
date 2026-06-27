---
phase: 21-ci-pipeline-unification
type: execute
waves: 2
depends_on: []
files_modified:
  - AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py
  - AIM/tests/subagents/test_ci_pipeline_integration.py
autonomous: true
---

# Phase 21: CI Pipeline Unification (Regenerated)

> **Goal:** Make EventBus delegation real -- CI agents subscribe to the shared EventBus,
> pick up `task.request` Messages, and publish `ci.agent.completed` Events.
> Remove the dead fallback to direct `agent.execute_task()`.

**Regenerated:** 2026-05-31 after plan-checker found ~90% of original plans already implemented.
**Reads:** 21-CONTEXT.md (user decisions, LOCKED), 21-RESEARCH.md (technical analysis)
**Remaining gap:** D-05/D-06/D-07 (EventBus delegation)

---

## What's Already Done (from original 5-wave plan)

| Wave | Problem | What | Status |
|------|---------|------|--------|
| W1 | L4 | `UnifiedCiResult` + `SwotQuadrant` in `ci/models.py` | DONE |
| W2 | H1 | Pipeline merge: `_run_quick_analysis()`, tier routing, `_extract_*` | DONE |
| W2 | D-04 | CiMarketingAnalyzer thin proxy (158 lines, `__new__` trick) | DONE |
| W4 | D-10/D-11 | API unification: `?tier=quick|deep`, deprecation header, SSE stream | DONE |
| W5 | Tests | `TestUnifiedArchitecture` class, 49 tests across 11 classes | DONE |

## Remaining Gap: EventBus Delegation

```
Current _execute_single_phase() flow (ci_orchestrator.py:910-990):

  Publish task.request Message ──► EventBus ──► Agent (poll loop NOT running)
                                                   │
  Wait 10s for ci.agent.completed ◄── NEVER ARRIVES (no one publishes it)
       │
       └── TIMEOUT ──► Fallback: agent.execute_task(task)  ← DIRECT CALL
                           │
                           └── Publish ci.agent.completed manually
```

**Root causes:**
1. `_get_agent()` never calls `agent.initialize()` → poll loop never starts
2. `report_result()` publishes `agent.result` Message, not `ci.agent.completed` Event
3. `correlation_id` not threaded through to agent's result publication

## Regenerated Wave Plan

| Wave | Plan | What | Files Changed |
|------|------|------|---------------|
| W1 | [21-01-PLAN.md](./21-01-PLAN.md) | Agent EventBus initialization + completion event bridge | ci_orchestrator.py |
| W2 | [21-02-PLAN.md](./21-02-PLAN.md) | Remove dead fallback + verify 49 tests pass | ci_orchestrator.py, test_ci_pipeline_integration.py |

## Key Decisions (LOCKED, from CONTEXT.md)

- D-05: EventBus publish instead of agent.execute_task()
- D-06: CI agents subscribe to EventBus
- D-07: Results via EventBus response events

(Decisions D-01 through D-04 and D-08 through D-11 are already implemented.)

## Must-Haves

### Truths
- "Each CI agent subscribes to EventBus events via its background poll loop"
- "Orchestrator publishes task.request Messages that agents pick up and process"
- "Agents publish ci.agent.completed Events on the shared EventBus after execution"
- "EventBus delegation path NEVER falls back to direct agent.execute_task()"
- "All 49 existing CI pipeline integration tests pass"

### Artifacts
- path: "AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py"
  provides: "EventBus-only agent delegation, agent lifecycle management"
  patterns: ["await agent.initialize()", "ci.agent.completed", "asyncio.wait_for"]
  missing_patterns: ["agent.execute_task(task)"]

### Key Links
- from: "ci_orchestrator._get_agent()"
  to: "agent.initialize()"
  via: "await agent.initialize() call after EventBus injection"
  pattern: "agent\\.initialize\\(\\)"
- from: "ci_orchestrator._execute_single_phase()"
  to: "agent via EventBus task.request Message"
  via: "agent._listen_for_tasks() poll loop"
  pattern: "task\\.request"
- from: "agent report_result bridge"
  to: "ci_orchestrator._on_agent_completed()"
  via: "ci.agent.completed Event on shared EventBus"
  pattern: "ci\\.agent\\.completed"

---

## Detailed Plans

- [21-01-PLAN.md](./21-01-PLAN.md) — Wave 1: Agent EventBus Initialization + Completion Bridge
- [21-02-PLAN.md](./21-02-PLAN.md) — Wave 2: Remove Dead Fallback + Test Verification
