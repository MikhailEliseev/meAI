# Plan Review (Sonnet 4.6 - Implementation Perspective)

**Date:** 2026-05-09T12:20:00Z  
**Reviewer:** code-reviewer (Sonnet perspective)  
**Document:** PLAN.md v1.0

---

## Executive Summary

The plan is well-structured and executable with realistic scope. The 2-week timeline is achievable for a focused developer. However, there are several practical execution issues around dependencies, testing infrastructure, and coordination logic that need clarification before starting Sprint 1.

---

## Strengths

- **Clear sprint boundaries:** Each sprint delivers one complete subagent with tests
- **Stacked PRs strategy:** Well-defined branching and merge sequence
- **Incremental validation:** Unit + integration tests per sprint prevent big-bang failures
- **Risk mitigation:** Practical strategies for API limits, performance, data quality
- **File structure:** Clean separation of subagents, tests, and models
- **Success criteria:** Measurable checkboxes for each sprint
- **Dependencies explicit:** Python packages and external services listed upfront

---

## Issues Found

### Critical (blocks execution)

**1. Missing Operator delegation logic (Sprint 4 dependency)**
- **Issue:** Plan says "UPDATE operator.py" but current Operator doesn't have SEO Magister delegation logic. Need to clarify:
  - Does Operator already know about SEO Magister?
  - How does Operator route "Analyze SEO: example.com" to SEO Magister?
  - Is there a task routing registry?
- **Impact:** Sprint 4 can't start without understanding current Operator capabilities

**2. SEO Magister coordination algorithm missing**
- **Issue:** "SEO Magister coordination logic" is vague. Need to specify:
  - How does Magister dispatch 3 subagents? (Sequential? Parallel? Hybrid?)
  - How does Magister wait for all results?
  - What happens if 1 subagent fails? (Partial success threshold mentioned in Risk 3)
  - Does Magister use Event Bus or direct calls?
- **Impact:** Can't implement Sprint 4 without this algorithm

**3. Database migration not specified**
- **Issue:** Shows SQL comment but no actual schema. SPEC.md Section 5.3 referenced but need:
  - Full CREATE TABLE statement
  - Migration script location (Alembic? Raw SQL?)
  - Who runs migration? (Developer manually? CI/CD?)
- **Impact:** Can't persist reports without database schema

### Major (complicates execution)

**4. Redis dependency introduced without justification**
- **Issue:** Redis added for "idempotency cache" but:
  - SPEC.md doesn't mention Redis
  - Event Store already provides idempotency (event_id deduplication)
  - Adds infrastructure complexity (local Redis setup, CI/CD Redis)
- **Recommendation:** Use Event Store for idempotency, drop Redis unless there's a specific reason

**5. PostgreSQL mentioned but project uses SQLite**
- **Issue:** "PostgreSQL (for seo_reports table)" but:
  - CLAUDE.md shows `DATABASE_URL=sqlite+aiosqlite:///./data/meai.db`
  - No migration path from SQLite to PostgreSQL specified
  - Adds setup complexity
- **Recommendation:** Use SQLite for MVP, document PostgreSQL as future optimization

**6. Google PageSpeed API key required but no fallback**
- **Issue:** API key required but:
  - What if developer doesn't have key?
  - What if API is down?
  - Should there be a mock mode for development?
- **Recommendation:** Add mock PageSpeed responses for tests, document API key as optional for local dev

**7. Integration tests assume Event Bus is running**
- **Issue:** Tests like `test_technical_agent_events.py` need:
  - Event Bus instance
  - Event Store instance
  - Database connection
  - How to set up test environment? (Docker Compose? Pytest fixtures?)
- **Recommendation:** Add test infrastructure setup guide

### Minor (polish)

**8. Manual tests lack acceptance criteria**
- **Issue:** "Verify report quality" is subjective. Need specific criteria:
  - What makes a report "quality"?
  - How many recommendations minimum?
  - What score range is acceptable?

**9. End-to-end test timeout too generous**
- **Issue:** 10-minute timeout for test is too long for CI/CD
- **Recommendation:** Target 2-3 minutes for test, 10 minutes for production

**10. No rollback strategy for failed sprints**
- **Issue:** If Sprint 2 fails, how to rollback? Stacked PRs make this complex
- **Recommendation:** Document rollback procedure (revert PR, rebase remaining stack)

---

## Implementation Recommendations

### Before Sprint 1

1. **Clarify Operator routing:** Read current `src/meai/agents/operator.py` and document how it routes tasks to Magisters
2. **Design Magister coordination:** Write pseudocode for SEO Magister's dispatch/collect algorithm
3. **Create database schema:** Write full `seo_reports` table DDL and migration script
4. **Set up test infrastructure:** Create pytest fixtures for Event Bus, Event Store, Database
5. **Remove Redis dependency:** Use Event Store for idempotency (simpler)
6. **Stick with SQLite:** Document PostgreSQL as future optimization, not MVP requirement
7. **Add mock PageSpeed:** Create fixture with sample PageSpeed responses for tests

### During Sprints

8. **Sprint 1 Day 1:** Set up test infrastructure first (fixtures, mocks)
9. **Sprint 4 Day 1:** Implement Magister coordination algorithm before Operator changes
10. **Sprint 4 Day 3:** Run manual tests on real websites, document quality criteria

### After Sprint 4

11. **Document rollback procedure:** How to revert stacked PRs if needed
12. **Create runbook:** How to deploy, monitor, troubleshoot SEO workflow
13. **Performance baseline:** Measure actual execution time, optimize if > 5 minutes

---

## Verdict

**NEEDS CLARIFICATION**

The plan is 80% ready to execute. Before starting Sprint 1, need answers to:

1. How does Operator route tasks to SEO Magister? (Critical)
2. What's the Magister coordination algorithm? (Critical)
3. What's the full `seo_reports` table schema? (Critical)
4. Can we drop Redis and use Event Store for idempotency? (Major)
5. Can we use SQLite instead of PostgreSQL for MVP? (Major)

Once these 5 questions are answered, the plan is executable. Estimated clarification time: 1-2 hours.

**Recommendation:** Schedule 30-minute planning session to resolve Critical issues, then proceed to Sprint 1.
