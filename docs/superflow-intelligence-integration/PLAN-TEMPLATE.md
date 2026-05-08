# Intelligence Magister Integration - Implementation Plan

**Version:** 1.0  
**Date:** 2026-05-06  
**Status:** Draft  
**Based on:** SPEC.md v1.0

---

## Sprint Overview

| Sprint | Goal | Duration | Files Modified | Tests |
|--------|------|----------|----------------|-------|
| 1 | Intelligence Magister Interface | 1.5h | 1 file | 5 tests |
| 2 | CIOrchestrator Integration | 1h | 1 file | 3 tests |
| 3 | Operator & E2E | 1h | 1 file | 2 tests |

**Total:** 3.5 hours, 3 files, 10 tests

---

## Sprint 1: Intelligence Magister Interface

### Goal
Implement Intelligence Magister task routing and CI delegation interface.

### Tasks
1. [ ] Implement `execute_task()` routing logic
2. [ ] Implement `_handle_competitor_analysis()`
3. [ ] Implement `_store_ci_result()`
4. [ ] Add timeout handling
5. [ ] Add retry logic
6. [ ] Unit tests (5 tests)

### Files Modified
- `src/meai/agents/magisters/intelligence_magister.py` (+150 lines)

### Tests
- `test_execute_task_routing()` - Routes to correct handler
- `test_handle_competitor_analysis()` - CI delegation works
- `test_store_ci_result()` - Vault storage works
- `test_timeout_handling()` - Timeout returns error result
- `test_retry_logic()` - Retries on transient errors

### Success Criteria
- [ ] All unit tests pass
- [ ] Intelligence Magister accepts tasks
- [ ] Routes "monitor_competitors" to CI handler
- [ ] Returns mock results (CI not integrated yet)

---

## Sprint 2: CIOrchestrator Integration

### Goal
Refactor CIOrchestrator to work with Intelligence Magister.

### Tasks
1. [ ] Add `execute_ci_analysis()` interface
2. [ ] Implement `_select_phases()` tier logic
3. [ ] Refactor result aggregation
4. [ ] Add error handling for partial results
5. [ ] Integration tests (3 tests)

### Files Modified
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (+100 lines)

### Tests
- `test_execute_ci_analysis()` - Full CI flow works
- `test_tier_selection()` - Correct phases for each tier
- `test_partial_results()` - Handles agent failures gracefully

### Success Criteria
- [ ] All integration tests pass
- [ ] Intelligence Magister → CIOrchestrator works
- [ ] CI agents execute and return results
- [ ] Results are aggregated correctly

---

## Sprint 3: Operator & E2E

### Goal
Complete integration and end-to-end testing.

### Tasks
1. [ ] Enhance Operator CI detection
2. [ ] End-to-end test (Operator → Intelligence → CI)
3. [ ] Performance test (tier timing)
4. [ ] Documentation update

### Files Modified
- `src/meai/agents/operator.py` (+30 lines)

### Tests
- `test_operator_to_ci_e2e()` - Full flow works
- `test_tier_performance()` - Meets timing requirements

### Success Criteria
- [ ] All E2E tests pass
- [ ] Performance within tier limits
- [ ] Documentation complete
- [ ] Ready for PR

---

## Dependencies

### Sprint 1 → Sprint 2
- Sprint 2 needs Sprint 1 interface complete

### Sprint 2 → Sprint 3
- Sprint 3 needs Sprint 2 CI integration working

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| CI timeout | 1 | Configurable timeouts per tier |
| Parallel failures | 2 | Partial result collection |
| Performance issues | 3 | Performance tests, tier system |

---

## Rollback Plan

If integration fails:
1. Revert Intelligence Magister changes
2. CIOrchestrator remains standalone
3. No impact on existing CI system

---

**Status:** Waiting for spec review  
**Next:** Execute sprints after approval
