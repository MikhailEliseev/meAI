# Board Memo: Vertical Slice — SEO Analysis Workflow

**Date:** 2026-05-09  
**From:** Product Team (Claude Opus 4.7)  
**To:** Stakeholders (Mikhail)  
**Re:** Implementation of End-to-End SEO Analysis Workflow  
**Status:** ✅ APPROVED FOR IMPLEMENTATION

---

## Executive Summary

**Problem:** meAI system has excellent architecture (9/10) but incomplete implementation (6/10). No working end-to-end workflows. Cannot deliver value to clients.

**Solution:** Implement Vertical Slice — complete SEO Analysis workflow from user request to final report. Demonstrates full system capabilities: Architect → Operator → SEO Magister → 3 Subagents → Report.

**Impact:** 
- First working feature that validates architecture
- Proves event-driven coordination works
- Delivers real value (competitor SEO analysis)
- Foundation for future workflows

**Approach:**
- 4 sprints: Technical Agent → Content Agent → Links Agent → Operator Coordination
- Event-driven via Event Bus with correlation IDs
- Partial success handling (70% threshold)
- Deep analysis (10-30 minutes per competitor)
- Free APIs for MVP, paid tier later

**Timeline:** 2 weeks (4 sprints × 2-3 days each)

**Risk:** Medium (new coordination patterns, API integration, medical compliance)

**Success Criteria:** User requests "Analyze SEO: example.com" → receives comprehensive report in < 10 minutes

---

## Background

### Current State
- ✅ Event Bus + Event Store (immutable audit log)
- ✅ 9 Magisters with business logic
- ✅ CI Deep Analyzer (world-class implementation)
- ❌ No end-to-end workflows
- ❌ Operator doesn't coordinate
- ❌ Magisters don't delegate
- ❌ Most Subagents are stubs

### Why This Matters
- Architecture is 9/10, but implementation is 6/10
- Cannot deliver value to clients without working workflows
- Need to validate architecture with real use case
- First step toward production-ready system

---

## Proposed Solution

### Workflow Overview

```
USER: "Проанализируй SEO конкурента example.com"
  ↓
ARCHITECT: Strategic decision → "Delegate to SEO Magister"
  ↓
OPERATOR: Tactical coordination → Create task for SEO Magister
  ↓
SEO MAGISTER: Domain coordination → Delegate to 3 Subagents
  ↓
SUBAGENTS: Execute analysis
  ├─ Technical Agent: robots.txt, sitemap, meta, performance
  ├─ Content Agent: headers, keywords, structure, quality
  └─ Links Agent: internal, external, broken links
  ↓
SEO MAGISTER: Aggregate results → Create comprehensive report
  ↓
OPERATOR: Collect results → Send to USER
  ↓
USER: Receives complete SEO analysis report ✅
```

### Components to Implement

**Sprint 1: Technical SEO Agent**
- robots.txt analysis
- sitemap.xml parsing
- meta tags extraction
- performance check (Google PageSpeed API)
- Schema.org validation

**Sprint 2: Content SEO Agent**
- Header structure (h1-h6)
- Keyword density
- Content quality metrics
- Word count & readability
- Content structure analysis

**Sprint 3: Links SEO Agent**
- Internal links mapping
- External links analysis
- Broken links detection
- Anchor text analysis
- Link quality assessment

**Sprint 4: Operator Coordination**
- Task delegation via Event Bus
- Result collection from Magisters
- Result aggregation
- Report generation
- Error handling

---

## Research Findings

### SEO Best Practices

**Components Analysis:**
- **Technical SEO:** robots.txt, sitemap.xml, meta tags, performance (PageSpeed), Schema.org
- **Content SEO:** headers (h1-h6), keyword density, readability (Flesch-Kincaid), structure
- **Links SEO:** internal links, external links, broken links, anchor text analysis

**API Recommendations:**
- **Free Tier (MVP):** Google PageSpeed Insights API, direct HTTP scraping
- **Paid Tier (Production):** Serpstat API ($69/month) for positions + backlinks
- **Future:** Ahrefs API for comprehensive data

**Quality Standards:**
- **Deep Analysis:** 10-30 minutes per competitor (not 1 second!)
- **Medical Marketing:** HIPAA compliance, E-E-A-T signals, medical schema
- **Comprehensive:** 50+ data points per competitor

### Agent Coordination Patterns

**Key Patterns Identified:**
1. **Correlation IDs:** Track entire workflow across all events
2. **Reply-To Pattern:** Standardize request-response flows
3. **Partial Success Handling:** 70%+ success threshold (don't fail on 1 agent)
4. **Event Naming:** `<domain>.<entity>.<action>` convention
5. **Idempotency:** Prevent duplicate processing on retries

**Implementation Recommendations:**
- Add correlation_id tracking to all events
- Implement reply_to field for responses
- Add partial success aggregation (70% threshold)
- Standardize event names across system
- Add idempotency keys to prevent duplicates

**Testing Strategy:**
- Mock Magisters for Operator testing
- Integration tests with real Event Bus
- Timeout handling tests
- Partial failure scenarios

---

## Technical Approach

### Event-Driven Coordination

**Task Assignment:**
```python
# Operator → SEO Magister
await event_bus.publish(Event(
    event_type="task.assigned",
    payload={
        "magister": "seo-magister",
        "action": "analyze_competitor",
        "url": "example.com"
    },
    priority=EventPriority.P1
))
```

**Subagent Delegation:**
```python
# SEO Magister → Subagents
for agent in ["technical", "content", "links"]:
    await event_bus.publish(Event(
        event_type="subtask.assigned",
        payload={
            "agent": f"{agent}-agent",
            "url": url,
            "correlation_id": task_id
        },
        priority=EventPriority.P2
    ))
```

**Result Collection:**
```python
# Wait for all subagents
results = await collect_results(
    correlation_id=task_id,
    expected_agents=3,
    timeout=300  # 5 minutes
)

# Aggregate
report = await aggregate_results(results)
```

### API Integration Strategy

**Phase 1 (Free APIs):**
- Google PageSpeed Insights API
- Basic web scraping (BeautifulSoup)
- robots.txt / sitemap.xml parsing

**Phase 2 (Freemium APIs):**
- Serpstat API (free tier: 10 requests/day)
- Moz API (free tier: 10 requests/month)

**Phase 3 (Paid APIs):**
- Ahrefs API (backlinks, DR, keywords)
- SEMrush API (comprehensive data)

---

## Success Metrics

### Technical Metrics
- ✅ End-to-end workflow completes successfully
- ✅ All 3 subagents execute and return results
- ✅ Results aggregated correctly
- ✅ Report generated in < 5 minutes
- ✅ All events logged in Event Store

### Business Metrics
- ✅ Can analyze real competitor websites
- ✅ Report provides actionable insights
- ✅ Quality comparable to manual analysis
- ✅ Can be shown to potential clients

### Quality Metrics
- ✅ Deep analysis (50+ data points)
- ✅ No silent failures
- ✅ Proper error handling
- ✅ Comprehensive logging

---

## Risks & Mitigation

### Risk 1: API Rate Limits
- **Impact:** High
- **Probability:** Medium
- **Mitigation:** Start with free APIs, implement rate limiting, add retry logic

### Risk 2: Coordination Complexity
- **Impact:** High
- **Probability:** Medium
- **Mitigation:** Start simple (synchronous), add async later, comprehensive testing

### Risk 3: Result Aggregation
- **Impact:** Medium
- **Probability:** Low
- **Mitigation:** Clear result format, validation, partial failure handling

### Risk 4: Performance
- **Impact:** Low
- **Probability:** Low
- **Mitigation:** Quality over speed (5-10 minutes acceptable), parallel execution

---

## Timeline

### Week 1
- **Days 1-2:** Sprint 1 (Technical Agent)
- **Days 3-4:** Sprint 2 (Content Agent)
- **Days 5-7:** Sprint 3 (Links Agent)

### Week 2
- **Days 8-10:** Sprint 4 (Operator Coordination)
- **Days 11-12:** Integration testing
- **Days 13-14:** Polish & documentation

---

## Decisions Made

### 1. API Strategy
**Decision:** Start with free APIs, add paid tier later
- **Phase 1 (MVP):** Google PageSpeed Insights API + HTTP scraping
- **Phase 2 (Production):** Serpstat API ($69/month) for positions + backlinks
- **Rationale:** Validate workflow first, then add depth

### 2. Coordination Approach
**Decision:** Async with correlation IDs and partial success
- Event-driven via Event Bus (already implemented)
- Correlation IDs track entire workflow
- 70% success threshold for partial results
- **Rationale:** Resilient to individual agent failures

### 3. Report Format
**Decision:** Structured JSON + Markdown summary
- JSON for programmatic access
- Markdown for human readability
- Store in Obsidian vault for history
- **Rationale:** Best of both worlds

### 4. Error Handling
**Decision:** Graceful degradation with partial results
- Timeout: 5 minutes for Subagents, 10 minutes for Magister
- Retry: 3 attempts with exponential backoff
- Partial success: Continue if 70%+ agents succeed
- **Rationale:** Deliver value even with failures

### 5. Testing Approach
**Decision:** Mock Magisters + Integration tests
- Unit tests for each agent
- Mock Magisters for Operator testing
- Integration tests with real Event Bus
- Manual tests on real websites
- **Rationale:** Fast feedback + real validation

---

## Recommendation

**✅ APPROVED — Proceed with implementation** using Standard governance mode and Stacked PRs workflow.

**Next Steps:**
1. ✅ Research findings reviewed
2. ✅ Technical approach finalized
3. ⏳ Write detailed specification
4. ⏳ Dual-model spec review
5. ⏳ Write implementation plan
6. ⏳ Dual-model plan review
7. ⏳ User final approval
8. ⏳ Generate Autonomy Charter
9. ⏳ Begin Sprint 1 (Technical SEO Agent)

---

**Status:** ✅ APPROVED  
**Date Approved:** 2026-05-09T11:50:00Z
