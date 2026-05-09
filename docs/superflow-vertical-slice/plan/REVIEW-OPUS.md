# Plan Review (Opus 4.7)

**Date:** 2026-05-09T12:20:00Z  
**Reviewer:** architect-reviewer (Opus perspective)  
**Document:** PLAN.md v1.0

---

## Executive Summary

The plan is well-structured, comprehensive, and executable within the 2-week timeline. The stacked PRs approach is sound, sprint breakdown is logical, and risk mitigation is thorough. However, there are several critical issues around database choice inconsistency, missing Magister implementation details, and unclear coordination logic that must be addressed before execution.

---

## Strengths

- **Clear vertical slice approach:** Focuses on one complete workflow rather than horizontal layers
- **Logical sprint progression:** Technical → Content → Links → Coordination builds complexity incrementally
- **Comprehensive testing strategy:** Unit, integration, and E2E tests with clear coverage targets
- **Realistic timeline:** 2-3 days per agent + 5 days for coordination is achievable
- **Strong risk mitigation:** Identifies key risks (API limits, coordination complexity, performance) with concrete mitigations
- **Quality-first mindset:** 10-minute execution time aligns with "Quality Over Speed Rule"
- **Event-driven validation:** Each sprint includes Event Bus integration tests
- **Stacked PRs workflow:** Enables parallel review and incremental delivery

---

## Issues Found

### Critical (blocks execution)

**1. Database inconsistency (Section "External Services")**
- Plan mentions PostgreSQL for `seo_reports` table
- Project uses SQLite (per CLAUDE.md and existing codebase)
- **Impact:** Migration script will fail, deployment blocked
- **Fix:** Change to SQLite or justify PostgreSQL migration

**2. Missing SEO Magister implementation baseline (Sprint 4)**
- Plan says "UPDATE seo_magister.py" but doesn't specify current state
- Is SEO Magister already implemented? If yes, where? If no, Sprint 4 scope explodes
- **Impact:** Sprint 4 effort could be 2x-3x underestimated
- **Fix:** Clarify if Magister exists, add creation to Sprint 4 scope if needed

**3. Operator delegation logic undefined (Sprint 4)**
- "Operator delegation logic" is vague
- How does Operator know to route "Analyze SEO" to SEO Magister?
- Is this pattern matching? Event routing? Registry lookup?
- **Impact:** Core coordination mechanism unclear, could derail Sprint 4
- **Fix:** Specify delegation algorithm (e.g., "task.goal pattern → Magister registry lookup")

**4. Result aggregation algorithm missing (Section 4.4 reference)**
- Plan references "Section 4.4 algorithm" but doesn't include it
- Scoring formula mentioned but not defined
- **Impact:** Cannot implement aggregation without algorithm
- **Fix:** Include scoring formula in plan or reference SPEC.md section explicitly

### Major (complicates execution)

**5. Redis dependency introduced without justification**
- Redis added for idempotency cache
- Project currently has no Redis infrastructure
- Idempotency can be handled via Event Store (already implemented)
- **Impact:** Adds deployment complexity, infrastructure cost
- **Recommendation:** Use Event Store for idempotency (check `event_id` duplicates)

**6. Google PageSpeed API key requirement unclear**
- Free tier mentioned (100 requests/day) but no fallback if key missing
- What happens if user doesn't have API key?
- **Impact:** Workflow fails silently or blocks on missing config
- **Fix:** Add fallback (Lighthouse CLI) or make API key optional with degraded mode

**7. Parallel execution not specified (Risk 3 mitigation)**
- "Parallel subagent execution" mentioned but not in Sprint 4 deliverables
- Is this async dispatch or sequential with timeout?
- **Impact:** Performance target (< 10 minutes) may not be met
- **Fix:** Add explicit parallel dispatch logic to Sprint 4 scope

**8. Obsidian persistence format undefined (Sprint 4)**
- "Report saved to database + Obsidian" but no format specified
- Which vault? Which file structure? LLM Wiki pattern compliance?
- **Impact:** Violates "LLM Wiki Pattern Fundamental" rule from CLAUDE.md
- **Fix:** Specify report format (e.g., `seo-magister/wiki/reports/YYYY-MM-DD-domain.md`)

### Minor (polish)

**9. Manual test checklist incomplete**
- "Verify report quality" is subjective
- No criteria for what constitutes quality
- **Recommendation:** Add specific quality checks (e.g., "50+ data points", "actionable recommendations")

**10. Event Store query assertion weak**
- `assert len(events) >= 8` is fragile (what if more events added?)
- **Recommendation:** Check for specific event types instead of count

**11. Branch naming inconsistent**
- Uses `feat/seo-vertical-slice/sprint-X` but could be clearer
- **Recommendation:** Add component name (e.g., `feat/seo-vertical-slice/01-technical-agent`)

**12. Success metrics overlap**
- Technical, Business, Quality metrics have redundancy
- "Deep analysis (50+ data points)" appears in Quality but not Technical
- **Recommendation:** Consolidate into single checklist with categories

---

## Recommendations

### 1. Clarify Database Strategy (CRITICAL)
**Decision needed:** SQLite or PostgreSQL?
- If SQLite: Update dependencies, use existing infrastructure
- If PostgreSQL: Add migration plan, justify complexity increase

### 2. Define SEO Magister Baseline (CRITICAL)
**Add to Sprint 4 scope:**
- Create `AIM/src/aim/magisters/seo_magister.py` (if not exists)
- Implement subagent dispatch logic
- Implement result aggregation with scoring formula
- Add Magister unit tests

### 3. Specify Operator Routing Logic (CRITICAL)
**Add to Sprint 4 deliverables:**
- Task pattern matching: "Analyze SEO: {url}" → SEO Magister
- Magister registry lookup mechanism
- Error handling for unknown task patterns

### 4. Include Scoring Algorithm (CRITICAL)
**Add to Plan (new section after Risk Mitigation):**
- Technical score: (robots + sitemap + meta + performance + schema) / 5
- Content score: (headers + keywords + readability + structure) / 4
- Links score: (internal + external + broken + anchors) / 4
- Overall score: (technical * 0.4) + (content * 0.3) + (links * 0.3)

### 5. Remove Redis Dependency
- Remove `redis>=5.0.0` from dependencies
- Use Event Store for idempotency: check `event_id` before processing

### 6. Add API Key Fallback
**Add to Sprint 1 scope:**
- If GOOGLE_PAGESPEED_API_KEY missing: use Lighthouse CLI
- Log warning: "Using Lighthouse CLI (slower, no mobile metrics)"

### 7. Specify Parallel Execution
**Add to Sprint 4 deliverables:**
- Async dispatch: `asyncio.gather()` for 3 subagents
- Timeout per agent: 5 minutes
- Partial success: proceed if 2/3 agents complete

### 8. Define Obsidian Report Format
**Add to Sprint 4 deliverables:**
- Report location: `AIM/obsidian/seo-magister/wiki/reports/YYYY-MM-DD-{domain}.md`
- Format: Markdown with frontmatter (score, url, date, status)
- Update `seo-magister/wiki/index.md` with new report link

---

## Verdict

**APPROVED WITH CHANGES**

The plan is fundamentally sound and executable, but requires critical fixes before Sprint 1 begins:

**Must fix before execution:**
1. Database choice (SQLite vs PostgreSQL)
2. SEO Magister baseline clarification
3. Operator routing logic specification
4. Scoring algorithm inclusion

**Should fix for quality:**
5. Remove Redis dependency
6. Add API key fallback
7. Specify parallel execution
8. Define Obsidian format

**Nice to have:**
9. Polish manual test criteria
10. Improve event assertions
11. Consolidate success metrics

**Estimated fix time:** 2-4 hours (mostly documentation updates)

**Recommendation:** Address critical issues, then proceed to Autonomy Charter generation. The plan demonstrates strong architectural thinking and realistic execution strategy.
