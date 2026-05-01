# Spec Review Summary - meAI Core Foundation

**Date:** 2026-05-01T17:17:45Z  
**Review Type:** Dual-Model (Split-Focus Claude)  
**Governance:** Critical Mode

---

## Overall Assessment: CONCERNS FOUND

Both reviewers identified significant concerns that should be addressed before implementation.

**Architecture Review:** CONCERNS (3 blockers, 5 high priority)  
**Implementation Review:** CONCERNS (3 blockers, 5 high priority)

---

## Critical Issues (BLOCKERS)

### 1. Event Store vs Event Bus Confusion ⚠️ CRITICAL

**Problem:**
- Spec uses "events" and "messages" interchangeably
- Unclear if Event Store and Event Bus are the same or different
- Event replay mechanism not clearly defined

**Impact:** Data flow confusion, potential data loss

**Recommendation:**
```
Clarify data flow:
- Events = immutable facts (Event Store, SQLite events table)
- Messages = commands between agents (Event Bus, SQLite messages table)
- Event Store: append-only log for audit
- Event Bus: async queue for agent communication
```

---

### 2. Missing Dependencies in pyproject.toml ⚠️ CRITICAL

**Problem:**
- `structlog`, `aiofiles`, `aiolimiter` referenced in plan but not in dependencies
- Code won't run without these

**Impact:** Implementation blocked

**Recommendation:**
```toml
# Add to pyproject.toml
dependencies = [
    "structlog>=24.1.0",
    "aiofiles>=23.2.1",
    "aiolimiter>=1.1.0",
    "alembic>=1.13.1",
]
```

---

### 3. Event Sourcing Complexity ⚠️ CRITICAL

**Problem:**
- Event replay logic is complex and error-prone
- Missing: event versioning, idempotency, snapshot compaction
- No handling for concurrent writes

**Impact:** Data corruption risk

**Recommendation:**
- Add Event Sourcing Design Doc before Task 5
- Define event versioning strategy
- Add idempotency keys
- Document concurrent write handling

---

## High Priority Issues

### 4. Timeline Too Optimistic

**Problem:** 3-4 weeks for 25 tasks with strict TDD is tight

**Recommendation:** Adjust to 5-6 weeks OR defer Tasks 21-25 to Phase 2

---

### 5. Telegram Integration Ambiguity

**Problem:** Marked "optional" but in success criteria #13

**Recommendation:** Clarify: Required for MVP or post-MVP?

---

### 6. Component Ownership Unclear

**Problem:** Who owns SYSTEM.md? Agent Factory, System Registry, or Architect?

**Recommendation:** Document ownership (suggest: System Registry owns, others request changes)

---

### 7. Missing Priority Queue Task

**Problem:** Priority Queue mentioned but no dedicated task

**Recommendation:** Add explicit task or merge into Event Bus (Task 6)

---

### 8. Integration Testing Too Late

**Problem:** E2E test (Task 18) runs after deployment, not after each phase

**Recommendation:** Add phase-level integration tests after Tasks 7, 14, 17, 25

---

## Medium Priority Issues

### 9. Test Time Expectation Unrealistic

**Problem:** "< 30s total" for 150+ async tests is impossible

**Recommendation:** Adjust to 2-3 minutes

---

### 10. Event Bus Durability

**Problem:** In-memory asyncio.Queue loses messages on crash

**Recommendation:** Persist to SQLite before processing

---

### 11. Scalability Limits Not Documented

**Problem:** No guidance on max agents, events/min, etc.

**Recommendation:** Add "MVP Limits" section (suggest: max 20 agents)

---

### 12. Missing Interface Contracts

**Problem:** No clear boundaries between layers

**Recommendation:** Add `src/meai/interfaces/` with Protocol definitions

---

## Positive Findings ✅

1. **Technology choices are sound** (SQLite, FastAPI, Pydantic, structlog)
2. **Layer separation is clear** (with minor coupling concerns)
3. **TDD approach is well-defined**
4. **Safety mechanisms are comprehensive**
5. **Documentation plan is thorough**

---

## Recommendations

### Before Implementation Starts:

1. ✅ **Fix pyproject.toml** - Add missing dependencies
2. ✅ **Clarify Event Store vs Event Bus** - Write 1-page data flow doc
3. ✅ **Add Event Sourcing Design Doc** - Versioning, idempotency, snapshots
4. ✅ **Clarify Telegram requirement** - MVP or post-MVP?
5. ✅ **Adjust timeline** - 5-6 weeks realistic

### During Implementation:

6. ✅ **Add phase-level integration tests** - After Tasks 7, 14, 17, 25
7. ✅ **Document component ownership** - Who owns what
8. ✅ **Add async patterns guide** - Cancellation, timeouts, TaskGroup
9. ✅ **Add error handling strategy** - Retries, circuit breakers

---

## Decision Required

**Option A: Fix Critical Issues First** (Recommended)
- Address 3 blockers before starting
- Update spec with clarifications
- Re-review updated spec
- Then proceed to implementation
- **Time:** +2-3 days for fixes, then 5-6 weeks implementation

**Option B: Start with Reduced Scope**
- Implement Tasks 1-20 only (foundation + deployment)
- Defer Tasks 21-25 (Core Components) to Phase 2
- Address blockers during Phase 2 planning
- **Time:** 3-4 weeks for Phase 1, then plan Phase 2

**Option C: Proceed As-Is with Risks**
- Start implementation with current spec
- Address issues as they arise
- Higher risk of rework
- **Time:** 3-4 weeks (optimistic), likely 5-6 weeks with rework

---

## Next Steps

**Waiting for your decision:**

1. Which option do you prefer? (A/B/C)
2. Should Telegram be required for MVP?
3. Are you OK with 5-6 weeks timeline?

After decision:
- Update spec based on your choices
- Create implementation plan
- Plan review (dual-model)
- Final approval
- Start Phase 2 (Execution)

---

**Review Complete:** 2026-05-01T17:17:45Z
