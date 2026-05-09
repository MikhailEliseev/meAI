# Plan Review: Aggregated Feedback

**Date:** 2026-05-09T12:21:00Z  
**Reviewers:** Opus 4.7 (architect-reviewer) + Sonnet 4.6 (code-reviewer)  
**Document:** PLAN.md v1.0

---

## Executive Summary

**Opus verdict:** APPROVED WITH CHANGES  
**Sonnet verdict:** NEEDS CLARIFICATION

**Consensus:** Plan is 80% ready to execute. Timeline is realistic, sprint breakdown is logical, but 4 critical issues must be resolved before Sprint 1.

**Priority:** Fix 4 critical issues (1-2 hours) → proceed to execution.

---

## Critical Issues (Both Reviewers Agree)

### 1. Database Choice: SQLite vs PostgreSQL ⚠️
**Impact:** Blocks Sprint 4 (report persistence)  
**Issue:** Plan mentions PostgreSQL, but project uses SQLite

**Decision: Use SQLite for MVP**
- CLAUDE.md specifies: `DATABASE_URL=sqlite+aiosqlite:///./data/meai.db`
- No infrastructure change needed
- PostgreSQL = future optimization (not MVP requirement)

**Fix:**
```markdown
# Change line 235 in PLAN.md
- PostgreSQL (for seo_reports table)
+ SQLite (existing infrastructure)

# Change line 156-160 (database migration)
CREATE TABLE seo_reports (
    id TEXT PRIMARY KEY,  -- UUID as TEXT in SQLite
    url TEXT NOT NULL,
    analyzed_at TEXT NOT NULL,  -- ISO8601 timestamp
    score REAL,
    technical_data TEXT,  -- JSON as TEXT in SQLite
    content_data TEXT,
    links_data TEXT,
    summary TEXT,
    recommendations TEXT,  -- JSON array as TEXT
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

### 2. SEO Magister Baseline Undefined ⚠️
**Impact:** Sprint 4 scope unclear, effort underestimated  
**Issue:** Plan says "UPDATE seo_magister.py" but doesn't specify current state

**Decision: SEO Magister exists but needs coordination logic**
- File exists: `AIM/src/aim/magisters/seo_magister.py`
- Has: `identify_subagents()`, `aggregate_results()` stubs
- Missing: Event Bus coordination, dispatch logic, result collection

**Fix:**
```markdown
# Add to Sprint 4 scope (line 136-147)

**Deliverables:**
1. SEO Magister coordination logic:
   - Implement `coordinate_analysis()` method
   - Implement `dispatch_subagents()` via Event Bus
   - Implement `collect_results()` with timeout
   - Implement `aggregate_results()` with scoring formula (SPEC.md 4.4)
2. Operator delegation logic:
   - Pattern matching: "Analyze SEO: {url}" → SEO Magister
   - Event Bus task routing
3. Result aggregation + report generation
4. Report persistence (SQLite + Obsidian)
5. End-to-end test
6. Documentation
```

---

### 3. Operator Routing Logic Undefined ⚠️
**Impact:** Core coordination mechanism unclear  
**Issue:** How does Operator know to route "Analyze SEO" to SEO Magister?

**Decision: Pattern matching + Magister registry**

**Fix:**
```python
# Add to Sprint 4 deliverables

class Operator:
    def __init__(self):
        self.magister_registry = {
            "seo": "seo-magister",
            "content": "content-magister",
            "ads": "ads-magister"
        }
    
    async def route_task(self, task: Task) -> str:
        """Route task to appropriate Magister"""
        
        # Pattern matching
        if "seo" in task.goal.lower() or "analyze seo" in task.goal.lower():
            return self.magister_registry["seo"]
        elif "content" in task.goal.lower():
            return self.magister_registry["content"]
        elif "ads" in task.goal.lower():
            return self.magister_registry["ads"]
        else:
            raise ValueError(f"Unknown task type: {task.goal}")
```

---

### 4. Scoring Algorithm Not Included ⚠️
**Impact:** Cannot implement aggregation  
**Issue:** Plan references "Section 4.4 algorithm" but doesn't include it

**Decision: Include scoring formula from SPEC.md**

**Fix:**
```markdown
# Add new section after Risk Mitigation (line 350)

## Scoring Algorithm

**Formula (from SPEC.md Section 4.4):**

```python
# Extract component scores
technical_score = technical["performance"]["page_speed_score"]
content_score = content["content_quality"]["readability_score"]
broken_count = links["broken_links"]["count"]
links_score = max(0, 100 - (broken_count * 5))

# Weighted average
overall_score = (
    technical_score * 0.4 +
    content_score * 0.3 +
    links_score * 0.3
)

# Generate recommendations
recommendations = []
if technical_score < 70:
    recommendations.append("Optimize page performance")
if content_score < 60:
    recommendations.append("Improve content readability")
if broken_count > 0:
    recommendations.append(f"Fix {broken_count} broken links")
```
```

---

## Major Issues (Should Fix)

### 5. Redis Dependency Unnecessary
**Both reviewers agree:** Use Event Store for idempotency

**Fix:**
```markdown
# Remove from dependencies (line 224)
- redis>=5.0.0

# Remove from environment variables (line 230)
- REDIS_URL=redis://localhost:6379/0

# Update idempotency implementation in SPEC.md reference
Use Event Store event_id deduplication instead of Redis cache
```

---

### 6. PageSpeed API Key Fallback Missing
**Fix:**
```markdown
# Add to Sprint 1 scope (line 34)

**API Key Handling:**
- If GOOGLE_PAGESPEED_API_KEY present: use PageSpeed API
- If missing: use Lighthouse CLI (fallback)
- Log warning: "Using Lighthouse CLI (slower, no mobile metrics)"
- Tests: use mock PageSpeed responses (no API key needed)
```

---

### 7. Parallel Execution Not Specified
**Fix:**
```markdown
# Add to Sprint 4 deliverables (line 137)

**Parallel Subagent Execution:**
```python
async def dispatch_subagents(self, url: str, correlation_id: str):
    """Dispatch 3 subagents in parallel"""
    
    tasks = [
        self._dispatch_agent("technical-agent", url, correlation_id),
        self._dispatch_agent("content-agent", url, correlation_id),
        self._dispatch_agent("links-agent", url, correlation_id)
    ]
    
    # Wait for all with timeout (5 minutes per agent)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle partial success (70% threshold = 2/3 agents)
    successful = [r for r in results if not isinstance(r, Exception)]
    if len(successful) >= 2:
        return successful
    else:
        raise CoordinationError("Insufficient successful agents")
```
```

---

### 8. Obsidian Report Format Undefined
**Fix:**
```markdown
# Add to Sprint 4 deliverables (line 203)

**Obsidian Report Format:**
- Location: `AIM/obsidian/seo-magister/wiki/reports/YYYY-MM-DD-{domain}.md`
- Format: Markdown with frontmatter

Example:
```markdown
---
url: https://example.com
analyzed_at: 2026-05-09T12:00:00Z
score: 78.5
status: completed
---

# SEO Analysis: example.com

## Summary
- **Overall Score:** 78.5/100
- **Technical:** 85/100
- **Content:** 65/100
- **Links:** 80/100

## Recommendations
1. Optimize page performance (PageSpeed < 70)
2. Improve content readability
3. Fix 2 broken links

## Details
[Full technical, content, links data...]
```

- Update `seo-magister/wiki/index.md` with new report link
```

---

## Minor Issues (Polish)

- Manual test criteria (add specific quality checks)
- E2E test timeout (reduce from 10 min to 2-3 min for CI/CD)
- Rollback strategy (document revert procedure for stacked PRs)
- Test infrastructure setup (add pytest fixtures guide)

---

## Recommended Action Plan

### Phase 1: Fix Critical Issues (1-2 hours)
1. ✅ Change PostgreSQL → SQLite (update dependencies, schema)
2. ✅ Clarify SEO Magister scope (add coordination methods)
3. ✅ Specify Operator routing (pattern matching + registry)
4. ✅ Include scoring algorithm (from SPEC.md)

### Phase 2: Address Major Issues (1 hour)
5. ✅ Remove Redis dependency (use Event Store)
6. ✅ Add PageSpeed API fallback (Lighthouse CLI)
7. ✅ Specify parallel execution (asyncio.gather)
8. ✅ Define Obsidian format (LLM Wiki compliance)

### Phase 3: Polish (30 min)
9. Add manual test criteria
10. Reduce E2E test timeout
11. Document rollback strategy

---

## Final Verdict

**Status:** APPROVED WITH CHANGES

**Next Steps:**
1. Apply 8 fixes to PLAN.md (2-3 hours total)
2. Quick re-review (30 min)
3. User final approval
4. Generate Autonomy Charter
5. Begin Sprint 1

**Estimated Total Effort:** 3-4 hours to production-ready plan

**Impact if skipped:** 20-30% Sprint 4 time wasted on clarifications and rework

---

**Recommendation:** Apply critical fixes now (1-2 hours), defer minor polish to Sprint 4.
