# Spec Review: Aggregated Feedback

**Date:** 2026-05-09T12:11:00Z  
**Reviewers:** Opus 4.7 (architect-reviewer) + Sonnet 4.6 (code-reviewer)  
**Document:** SPEC.md v1.0

---

## Executive Summary

**Opus verdict:** APPROVED WITH CHANGES  
**Sonnet verdict:** NEEDS CLARIFICATION

**Consensus:** Specification has strong architectural foundation but requires critical fixes before implementation. Both reviewers identified overlapping issues around event specifications, medical compliance, and implementation details.

**Priority:** Fix 7 critical issues (4-6 hours) → proceed to implementation.

---

## Critical Issues (Both Reviewers Agree)

### 1. Missing `reply_to` field in events ⚠️
**Impact:** Response routing ambiguous, blocks coordination  
**Sections:** 2.2, 6.1-6.4  
**Fix:** Add `reply_to: str` field to all event specifications

**Example:**
```python
{
    "event_type": "task.assigned",
    "source": "operator",
    "target": "seo-magister",
    "reply_to": "operator",  # ← ADD THIS
    "correlation_id": "task-123",
    ...
}
```

### 2. Idempotency mechanism underspecified ⚠️
**Impact:** Retry logic won't work correctly, duplicate processing  
**Sections:** 2.2, 7.3  
**Fix:** Specify idempotency implementation (cache/database, TTL, key format)

**Example:**
```python
# Add to each agent spec (4.1-4.3)
async def execute_task(self, subtask: Subtask):
    # Check idempotency
    cache_key = f"subtask:{subtask.subtask_id}"
    if cached := await redis.get(cache_key):
        return cached
    
    # Execute
    result = await self._do_work(subtask)
    
    # Cache result (TTL: 1 hour)
    await redis.setex(cache_key, 3600, result)
    return result
```

### 3. Event subscription pattern undefined ⚠️
**Impact:** Blocks Operator/Magister coordination implementation  
**Sections:** 4.4-4.5  
**Fix:** Specify how agents subscribe to events (polling? callback? WebSocket?)

**Recommendation:** Polling with exponential backoff
```python
async def wait_for_completion(self, correlation_id: str, timeout: int):
    deadline = time.time() + timeout
    interval = 1  # start with 1 second
    
    while time.time() < deadline:
        events = await event_bus.get_events(
            event_type="task.completed",
            correlation_id=correlation_id,
            status="pending"
        )
        if events:
            return events[0]
        
        await asyncio.sleep(interval)
        interval = min(interval * 1.5, 10)  # max 10 seconds
    
    raise TimeoutError(f"No response for {correlation_id}")
```

### 4. Aggregation logic not specified ⚠️
**Impact:** Core feature undefined, blocks implementation  
**Section:** 4.4  
**Fix:** Add scoring formula and recommendation generation rules

**Example:**
```python
async def aggregate_results(self, results: list[dict]) -> dict:
    # Extract scores
    technical_score = results[0]["results"]["performance"]["page_speed_score"]
    content_score = results[1]["results"]["content_quality"]["readability_score"]
    links_score = 100 - (results[2]["results"]["broken_links"]["count"] * 5)
    
    # Weighted average
    overall_score = (
        technical_score * 0.4 +
        content_score * 0.3 +
        links_score * 0.3
    )
    
    # Generate recommendations
    recommendations = []
    if technical_score < 70:
        recommendations.append("Optimize page performance (PageSpeed < 70)")
    if content_score < 60:
        recommendations.append("Improve content readability")
    if links_score < 80:
        recommendations.append("Fix broken links")
    
    return {
        "score": overall_score,
        "recommendations": recommendations,
        "technical": results[0],
        "content": results[1],
        "links": results[2]
    }
```

### 5. API authentication details missing ⚠️
**Impact:** Can't implement API calls without credentials  
**Sections:** 4.1-4.3  
**Fix:** Specify environment variables and API configuration

**Add to spec:**
```bash
# .env
GOOGLE_PAGESPEED_API_KEY=your_key_here
SERPSTAT_API_KEY=your_key_here  # Phase 2

# API endpoints
PAGESPEED_API_URL=https://www.googleapis.com/pagespeedonline/v5/runPagespeed
```

### 6. SEO Report persistence not specified ⚠️
**Impact:** Can't store/retrieve reports  
**Section:** 5.3  
**Fix:** Specify database schema + Obsidian vault structure

**Database schema:**
```sql
CREATE TABLE seo_reports (
    id UUID PRIMARY KEY,
    url TEXT NOT NULL,
    analyzed_at TIMESTAMP NOT NULL,
    score FLOAT,
    technical_data JSONB,
    content_data JSONB,
    links_data JSONB,
    recommendations TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_seo_reports_url ON seo_reports(url);
CREATE INDEX idx_seo_reports_analyzed_at ON seo_reports(analyzed_at DESC);
```

**Obsidian vault:**
```
AIM/obsidian/seo-magister/wiki/reports/
├── 2026-05-09-example-com.md
├── 2026-05-09-competitor1-com.md
└── index.md
```

### 7. Event Store integration missing ⚠️
**Impact:** Audit trail incomplete, can't debug workflows  
**Sections:** 3.2, 6.x  
**Fix:** Specify Event Store write operations

**Add to each event emission:**
```python
# After publishing event
await event_bus.publish(event)

# Event Bus automatically writes to Event Store
# No additional code needed in agents
```

**Query patterns for debugging:**
```python
# Get all events for workflow
events = await event_store.query(
    correlation_id="task-123",
    order_by="timestamp"
)

# Get failed events
failed = await event_store.query(
    event_type="task.failed",
    time_range=(start, end)
)
```

---

## Major Issues (Should Fix)

### 8. HIPAA compliance not operationalized
**Opus:** Critical  
**Sonnet:** Not mentioned  
**Fix:** Add Section 10.1 with PHI detection, encryption, audit logging

### 9. Medical schema validation incomplete
**Opus:** Major  
**Sonnet:** Not mentioned  
**Fix:** Expand Technical Agent to validate medical-specific schema types

### 10. E-E-A-T validation missing
**Opus:** Major  
**Sonnet:** Not mentioned  
**Fix:** Add E-E-A-T metrics to Content Agent output

### 11. Performance vs Quality conflict
**Opus:** Not mentioned  
**Sonnet:** Major  
**Fix:** Clarify MVP (5 min) vs Production (30 min) targets

### 12. PageSpeed API response structure not documented
**Opus:** Not mentioned  
**Sonnet:** Major  
**Fix:** Add API integration appendix with request/response examples

### 13. Compensation strategy missing
**Opus:** Major  
**Sonnet:** Not mentioned  
**Fix:** Add Section 7.4 for checkpoint/resume logic

### 14. Rate limiting not enforced
**Opus:** Major  
**Sonnet:** Not mentioned  
**Fix:** Specify rate limiter implementation

---

## Minor Issues (Nice to Have)

- Event versioning (Opus #12)
- Performance monitoring (Opus #11)
- Circuit breaker pattern (Opus #14)
- Report format specification (Opus #15)
- Correlation ID generation (Opus #13)
- Terminology consistency (Sonnet)
- URL validation completeness (Sonnet)

---

## Recommended Action Plan

### Phase 1: Fix Critical Issues (4-6 hours)
1. ✅ Add `reply_to` field to all events (30 min)
2. ✅ Specify idempotency mechanism (1 hour)
3. ✅ Document event subscription pattern (1 hour)
4. ✅ Add aggregation algorithm (1 hour)
5. ✅ Specify API authentication (30 min)
6. ✅ Define report persistence (1 hour)
7. ✅ Document Event Store integration (30 min)

### Phase 2: Address Major Issues (2-3 hours)
8. Add HIPAA compliance section
9. Expand medical schema validation
10. Add E-E-A-T metrics
11. Clarify performance targets
12. Document API responses
13. Add compensation strategy
14. Specify rate limiting

### Phase 3: Polish (1 hour)
- Fix terminology consistency
- Add event versioning
- Complete URL validation rules

---

## Final Verdict

**Status:** APPROVED WITH CHANGES

**Next Steps:**
1. Fix 7 critical issues (Priority 1)
2. Address major issues (Priority 2)
3. Quick re-review (30 min)
4. Proceed to implementation plan

**Estimated Total Effort:** 7-10 hours of spec refinement

**Impact if skipped:** 30-40% implementation time wasted on clarifications and rework

---

**Recommendation:** Fix critical issues now, defer major/minor to implementation phase if time-constrained.
