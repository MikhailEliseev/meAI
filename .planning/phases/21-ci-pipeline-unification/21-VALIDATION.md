# Phase 21: Nyquist Validation

**Date:** 2026-05-31
**Purpose:** Validate that all requirements are covered by plans with concrete verifications.

---

## Requirement Coverage Matrix

| Requirement | Description | Plan | Task | Verification |
|-------------|-------------|------|------|-------------|
| D-05 | Replace direct `agent.execute_task()` with EventBus publish | 21-02, Task 1 | Removes fallback code, uses EventBus-only delegation | `grep -n "agent.execute_task(task)"` returns no match in `_execute_single_phase` |
| D-06 | Each CI agent subscribes to EventBus events | 21-01, Task 1 | Calls `agent.initialize()` which starts `_listen_for_tasks()` poll loop | Python assertion: `agent._listener_task is not None and not done()` |
| D-07 | Results collected via EventBus response events | 21-01, Task 2 | Bridges `report_result()` to publish `ci.agent.completed` Event | Python test: `ci.agent.completed` Event received with correct `correlation_id` |

## Requirement-to-Verification Traceability

### D-05: EventBus Publish Instead of Direct Calls

**Plan:** 21-02 (Remove dead fallback)
**Task:** 1 (Remove dead EventBus fallback)
**Verification:**
- **Automated:** `grep -n "agent.execute_task(task)" ci_orchestrator.py` — must NOT appear in `_execute_single_phase`
- **Automated:** `grep -c "asyncio.wait_for(completion_event.wait()" ci_orchestrator.py` — must be exactly 1
- **Rationale:** If `_execute_single_phase` never calls `agent.execute_task(task)`, D-05 is satisfied

### D-06: CI Agents Subscribe to EventBus

**Plan:** 21-01 (Agent EventBus initialization)
**Task:** 1 (Make `_get_agent()` async and call `agent.initialize()`)
**Verification:**
- **Automated:** Python test that creates orchestrator, gets agent via `_get_agent()`, asserts `_listener_task` is active
- **Automated:** Python test that publishes `task.request` Message, waits 3s, asserts `ci.agent.completed` Event received
- **Rationale:** If agent's poll loop is running and picks up Messages, D-06 is satisfied

### D-07: Results via EventBus Response Events

**Plan:** 21-01 (Agent EventBus initialization)
**Task:** 2 (Bridge agent completion to `ci.agent.completed` Events)
**Verification:**
- **Automated:** Python test subscribes to `ci.agent.completed`, publishes `task.request`, asserts Event received with correct fields
- **Automated:** `_on_agent_completed` handler stores result in `self._completed_results` — verified by checking the dict after test run
- **Rationale:** If `ci.agent.completed` Events are published with `correlation_id` and collected by the persistent handler, D-07 is satisfied

## Plan-Level Nyquist Check

### 21-01-PLAN.md (Wave 1)

| Task | Has `<verify>` | Has `<automated>` | Type | Gate |
|------|---------------|-------------------|------|------|
| Task 1: Make `_get_agent()` async + call `initialize()` | Yes | Python script (`asyncio.run(test())`) | Functional | Asserts `_listener_task` is active |
| Task 2: Bridge `report_result` → `ci.agent.completed` | Yes | Python script (`asyncio.run(test())`) | Functional | Asserts Event received with correct payload |

### 21-02-PLAN.md (Wave 2)

| Task | Has `<verify>` | Has `<automated>` | Type | Gate |
|------|---------------|-------------------|------|------|
| Task 1: Remove dead fallback | Yes | `grep` count checks | Structural | Confirms no direct `agent.execute_task()` |
| Task 2: Run full test suite | Yes | `pytest ... -v --timeout=120` | Regression | All 49 tests pass |

## Gap Analysis

| Gap Type | Status |
|----------|--------|
| Missing requirement coverage | None — all 3 remaining requirements (D-05, D-06, D-07) covered by plans |
| Missing automated verification | None — every task has an automated verification |
| Unreachable artifact | None — all artifacts in `files_modified` are existing files being modified (not created) |
| Missing Nyquist gate | None — all verifications satisfy the Nyquist rule |

## Previous Checks (Already Implemented Features)

These items have been verified by the plan-checker as already done and are NOT re-planned:

- D-01 through D-04: Verified (unified orchestrator, tier routing, thin proxy)
- D-08 through D-09: Verified (UnifiedCiResult and SwotQuadrant in ci/models.py)
- D-10 through D-11: Verified (API unification with tier parameter, deprecation headers)

## Validation Result

**PASS.** All 3 remaining requirements (D-05, D-06, D-07) are covered by 2 plans with 4 tasks.
Every task has an automated verification. No gaps found.
