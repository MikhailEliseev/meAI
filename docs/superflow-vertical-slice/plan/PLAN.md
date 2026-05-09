# Implementation Plan: SEO Analysis Workflow

**Version:** 1.1  
**Date:** 2026-05-09  
**Based on:** SPEC.md v1.1  
**Status:** Ready for Execution

---

## Overview

**Goal:** Implement end-to-end SEO Analysis workflow (Vertical Slice)

**Timeline:** 2 weeks (4 sprints × 2-3 days each)

**Approach:** Stacked PRs (each sprint = separate branch stacking on previous)

**Success Criteria:**
- User requests "Analyze SEO: example.com"
- System delivers comprehensive report in < 10 minutes
- All events logged in Event Store
- Tests passing (unit + integration)

---

## Sprint Breakdown

### Sprint 1: Technical SEO Agent (Days 1-3)
**Branch:** `feat/seo-vertical-slice/sprint-1-technical-agent`  
**Base:** `main`

**Deliverables:**
1. Technical SEO Agent implementation
2. Google PageSpeed API integration
3. robots.txt + sitemap.xml parsing
4. Meta tags extraction
5. Schema.org validation
6. Unit tests
7. Integration test with Event Bus

**Files to create:**
```
AIM/src/aim/subagents/seo/technical_agent.py
AIM/tests/subagents/seo/test_technical_agent.py
AIM/tests/integration/test_technical_agent_events.py
```

**Dependencies:**
- `aiohttp` (HTTP requests)
- `beautifulsoup4` (HTML parsing)
- `lxml` (XML parsing)

**API Key Handling:**
- If GOOGLE_PAGESPEED_API_KEY present: use PageSpeed API
- If missing: use Lighthouse CLI (fallback)
- Log warning: "Using Lighthouse CLI (slower, no mobile metrics)"
- Tests: use mock PageSpeed responses (no API key needed)

**Success Criteria:**
- [ ] Agent receives `subtask.assigned` event
- [ ] Analyzes robots.txt, sitemap, meta, performance, schema
- [ ] Returns structured result (Section 4.1 format)
- [ ] Publishes `subtask.completed` event
- [ ] All unit tests pass
- [ ] Integration test with Event Bus passes

---

### Sprint 2: Content SEO Agent (Days 4-6)
**Branch:** `feat/seo-vertical-slice/sprint-2-content-agent`  
**Base:** `feat/seo-vertical-slice/sprint-1-technical-agent`

**Deliverables:**
1. Content SEO Agent implementation
2. Header structure analysis (h1-h6)
3. Keyword density calculation
4. Readability scoring (Flesch-Kincaid)
5. Content quality metrics
6. Unit tests
7. Integration test with Event Bus

**Files to create:**
```
AIM/src/aim/subagents/seo/content_agent.py
AIM/tests/subagents/seo/test_content_agent.py
AIM/tests/integration/test_content_agent_events.py
```

**Dependencies:**
- `textstat` (readability metrics)
- `beautifulsoup4` (HTML parsing)

**Success Criteria:**
- [ ] Agent receives `subtask.assigned` event
- [ ] Analyzes headers, keywords, readability, structure
- [ ] Returns structured result (Section 4.2 format)
- [ ] Publishes `subtask.completed` event
- [ ] All unit tests pass
- [ ] Integration test with Event Bus passes

---

### Sprint 3: Links SEO Agent (Days 7-9)
**Branch:** `feat/seo-vertical-slice/sprint-3-links-agent`  
**Base:** `feat/seo-vertical-slice/sprint-2-content-agent`

**Deliverables:**
1. Links SEO Agent implementation
2. Internal links mapping
3. External links analysis
4. Broken links detection
5. Anchor text analysis
6. Unit tests
7. Integration test with Event Bus

**Files to create:**
```
AIM/src/aim/subagents/seo/links_agent.py
AIM/tests/subagents/seo/test_links_agent.py
AIM/tests/integration/test_links_agent_events.py
```

**Dependencies:**
- `aiohttp` (HTTP requests for link checking)
- `beautifulsoup4` (HTML parsing)

**Success Criteria:**
- [ ] Agent receives `subtask.assigned` event
- [ ] Analyzes internal, external, broken links, anchor text
- [ ] Returns structured result (Section 4.3 format)
- [ ] Publishes `subtask.completed` event
- [ ] All unit tests pass
- [ ] Integration test with Event Bus passes

---

### Sprint 4: Operator Coordination (Days 10-14)
**Branch:** `feat/seo-vertical-slice/sprint-4-coordination`  
**Base:** `feat/seo-vertical-slice/sprint-3-links-agent`

**Deliverables:**
1. SEO Magister coordination logic:
   - Implement `coordinate_analysis()` method
   - Implement `dispatch_subagents()` via Event Bus (parallel execution)
   - Implement `collect_results()` with timeout
   - Implement `aggregate_results()` with scoring formula (Section 4.4)
2. Operator delegation logic:
   - Pattern matching: "Analyze SEO: {url}" → SEO Magister
   - Event Bus task routing via Magister registry
3. Result aggregation + report generation
4. Report persistence (SQLite + Obsidian)
5. End-to-end test
6. Documentation

**Files to update:**
```
AIM/src/aim/magisters/seo_magister.py
src/meai/agents/operator.py
```

**Files to create:**
```
AIM/tests/integration/test_seo_workflow_e2e.py
AIM/src/aim/models/seo_report.py
docs/workflows/seo-analysis.md
```

**Database migration:**
```sql
-- Create seo_reports table (Section 5.3) - SQLite
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

**Success Criteria:**
- [ ] Operator receives task from user
- [ ] Operator routes task to SEO Magister via pattern matching
- [ ] SEO Magister dispatches 3 subagents in parallel
- [ ] All 3 subagents execute and return results
- [ ] SEO Magister aggregates results (scoring formula)
- [ ] Report saved to database + Obsidian (LLM Wiki format)
- [ ] Operator returns report to user
- [ ] All events logged in Event Store
- [ ] End-to-end test passes (< 10 minutes)

**Operator Routing Logic:**
```python
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

---

## File Structure

```
AIM/
├── src/aim/
│   ├── magisters/
│   │   └── seo_magister.py          # UPDATE (Sprint 4)
│   ├── subagents/
│   │   └── seo/
│   │       ├── __init__.py
│   │       ├── technical_agent.py   # NEW (Sprint 1)
│   │       ├── content_agent.py     # NEW (Sprint 2)
│   │       └── links_agent.py       # NEW (Sprint 3)
│   └── models/
│       └── seo_report.py            # NEW (Sprint 4)
├── tests/
│   ├── subagents/
│   │   └── seo/
│   │       ├── test_technical_agent.py   # NEW (Sprint 1)
│   │       ├── test_content_agent.py     # NEW (Sprint 2)
│   │       └── test_links_agent.py       # NEW (Sprint 3)
│   └── integration/
│       ├── test_technical_agent_events.py  # NEW (Sprint 1)
│       ├── test_content_agent_events.py    # NEW (Sprint 2)
│       ├── test_links_agent_events.py      # NEW (Sprint 3)
│       └── test_seo_workflow_e2e.py        # NEW (Sprint 4)
└── obsidian/
    └── seo-magister/
        └── wiki/
            └── reports/              # NEW (Sprint 4)
                └── index.md

src/meai/
└── agents/
    └── operator.py                   # UPDATE (Sprint 4)
```

---

## Dependencies

### Python Packages
```bash
# Add to AIM/requirements.txt
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
textstat>=0.7.3
```

### Environment Variables
```bash
# Add to .env
GOOGLE_PAGESPEED_API_KEY=your_key_here  # Optional, falls back to Lighthouse CLI
```

### External Services
- SQLite (existing infrastructure, no setup needed)

---

## Testing Strategy

### Unit Tests (Per Sprint)
**Coverage target:** 80%+

**Test structure:**
```python
# test_technical_agent.py
async def test_analyze_robots_txt():
    """Test robots.txt parsing"""
    
async def test_analyze_sitemap():
    """Test sitemap.xml parsing"""
    
async def test_get_page_speed():
    """Test PageSpeed API call (mocked)"""
    
async def test_extract_meta_tags():
    """Test meta tags extraction"""
    
async def test_validate_schema():
    """Test Schema.org validation"""
```

### Integration Tests (Per Sprint)
**Test event-driven coordination:**

```python
# test_technical_agent_events.py
async def test_technical_agent_receives_task():
    """Test agent subscribes to subtask.assigned"""
    
async def test_technical_agent_publishes_result():
    """Test agent publishes subtask.completed"""
    
async def test_technical_agent_idempotency():
    """Test duplicate task handling"""
```

### End-to-End Test (Sprint 4)
**Test full workflow:**

```python
# test_seo_workflow_e2e.py
async def test_seo_analysis_workflow():
    """Test complete workflow from user request to report"""
    
    # 1. User requests analysis
    task = Task(
        task_id="test-task-1",
        goal="Analyze SEO: example.com",
        ...
    )
    
    # 2. Operator receives task
    await operator.receive_task(task)
    
    # 3. Wait for completion (max 10 minutes)
    result = await asyncio.wait_for(
        operator.get_user_report(task.task_id),
        timeout=600
    )
    
    # 4. Verify result
    assert result["status"] == "completed"
    assert result["score"] > 0
    assert len(result["recommendations"]) > 0
    
    # 5. Verify Event Store
    events = await event_store.query(
        correlation_id=task.task_id
    )
    assert len(events) >= 8  # 2 operator + 6 subagent events
```

### Manual Tests (Sprint 4)
- [ ] Real website: example.com
- [ ] Medical website: clinic.example.com
- [ ] Competitor: competitor.example.com
- [ ] Verify report quality
- [ ] Verify performance (< 10 minutes)

---

## Risk Mitigation

### Risk 1: API Rate Limits
**Mitigation:**
- Use free tier (100 requests/day)
- Implement rate limiting (10 requests/minute)
- Add retry logic with exponential backoff
- Cache PageSpeed results (1 hour TTL)

### Risk 2: Coordination Complexity
**Mitigation:**
- Start with synchronous coordination (Sprint 4)
- Add async optimization later if needed
- Comprehensive integration tests
- Mock Magisters for Operator testing

### Risk 3: Performance
**Mitigation:**
- Quality over speed (10 minutes acceptable)
- Parallel subagent execution
- Timeout handling (5 minutes per agent)
- Partial success delivery (70% threshold)

### Risk 4: Data Quality
**Mitigation:**
- Validate all scraped data
- Handle missing data gracefully
- Provide partial results when possible
- Log all errors to Event Store

---

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

**Rationale:**
- **Technical (40%):** Performance is critical for SEO rankings
- **Content (30%):** Quality content drives engagement
- **Links (30%):** Link structure affects crawlability and authority

**Implementation:**
- SEO Magister implements this formula in `aggregate_results()` method
- Each component score normalized to 0-100 scale
- Overall score rounded to 1 decimal place
- Recommendations generated based on thresholds

---

## Git Workflow (Stacked PRs)

### Branch Strategy
```
main
  └── feat/seo-vertical-slice/sprint-1-technical-agent
        └── feat/seo-vertical-slice/sprint-2-content-agent
              └── feat/seo-vertical-slice/sprint-3-links-agent
                    └── feat/seo-vertical-slice/sprint-4-coordination
```

### PR Sequence
1. **PR #1:** Sprint 1 → main (Technical Agent)
2. **PR #2:** Sprint 2 → Sprint 1 (Content Agent)
3. **PR #3:** Sprint 3 → Sprint 2 (Links Agent)
4. **PR #4:** Sprint 4 → Sprint 3 (Coordination)

### Merge Strategy
- Review PR #1 → merge to main
- Rebase PR #2 onto main → review → merge
- Rebase PR #3 onto main → review → merge
- Rebase PR #4 onto main → review → merge

---

## Success Metrics

### Technical Metrics
- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] End-to-end test passes
- [ ] Performance < 10 minutes
- [ ] All events logged in Event Store

### Business Metrics
- [ ] Can analyze real competitor websites
- [ ] Report provides actionable insights
- [ ] Quality comparable to manual analysis
- [ ] Can be shown to potential clients

### Quality Metrics
- [ ] Deep analysis (50+ data points)
- [ ] No silent failures
- [ ] Proper error handling
- [ ] Comprehensive logging

---

## Timeline

### Week 1
- **Days 1-3:** Sprint 1 (Technical Agent)
- **Days 4-6:** Sprint 2 (Content Agent)
- **Day 7:** Sprint 3 start (Links Agent)

### Week 2
- **Days 8-9:** Sprint 3 complete (Links Agent)
- **Days 10-12:** Sprint 4 (Coordination)
- **Days 13-14:** Integration testing + polish

---

## Next Steps

1. ✅ Spec review complete (v1.1)
2. ✅ Plan review complete (v1.1 - all critical fixes applied)
3. ⏳ User approval
4. ⏳ Generate Autonomy Charter
5. ⏳ Begin Sprint 1

---

**Status:** Ready for Execution  
**Next:** User approval → Autonomy Charter → Sprint 1
