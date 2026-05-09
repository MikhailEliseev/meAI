# Technical Specification: SEO Analysis Workflow

**Version:** 1.1 (Critical fixes applied)  
**Date:** 2026-05-09  
**Status:** ✅ READY FOR IMPLEMENTATION

---

## 1. Overview

### 1.1 Purpose
Implement end-to-end SEO competitor analysis workflow that demonstrates meAI system capabilities and validates event-driven architecture.

### 1.2 Scope
- **In Scope:**
  - Technical SEO Agent implementation
  - Content SEO Agent implementation
  - Links SEO Agent implementation
  - Operator coordination logic
  - SEO Magister coordination logic
  - Event Bus integration
  - Result aggregation
  - Report generation

- **Out of Scope:**
  - Positions tracking (future sprint)
  - Backlink analysis (future sprint)
  - Keyword research (exists, needs integration)
  - UI/Dashboard (future sprint)

### 1.3 Success Criteria
- [ ] User can request SEO analysis via Architect
- [ ] Operator delegates to SEO Magister
- [ ] SEO Magister coordinates 3 Subagents
- [ ] All Subagents execute and return results
- [ ] Results aggregated into comprehensive report
- [ ] Report delivered to user
- [ ] All events logged in Event Store
- [ ] End-to-end test passes

---

## 2. Research Findings

### 2.1 SEO Best Practices

**Quality Standards:**
- Deep analysis: 10-30 minutes per competitor (not superficial 1-second checks)
- Comprehensive: 50+ data points per competitor
- Medical marketing: HIPAA compliance, E-E-A-T signals, medical schema

**API Strategy:**
- **Phase 1 (MVP):** Google PageSpeed Insights API (free) + HTTP scraping
- **Phase 2 (Production):** Serpstat API ($69/month) for positions + backlinks
- **Future:** Ahrefs API for comprehensive data

### 2.2 Agent Coordination Patterns

**Key Patterns:**
1. **Correlation IDs:** Track entire workflow across all events (`correlation_id` field)
2. **Reply-To Pattern:** Standardize request-response flows (`reply_to` field)
3. **Partial Success:** 70%+ success threshold (don't fail entire task on 1 agent failure)
4. **Event Naming:** `<domain>.<entity>.<action>` convention
5. **Idempotency:** Prevent duplicate processing on retries (`subtask_id` as key)

**Implementation Requirements:**
- Add `correlation_id` to all events (workflow tracking)
- Add `reply_to` field for responses
- Implement partial success aggregation (70% threshold)
- Standardize event names across system
- Add idempotency checks in agents

---

## 3. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                         USER                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      ARCHITECT                          │
│  - Receives: "Analyze SEO competitor: example.com"     │
│  - Decides: "Delegate to SEO Magister"                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      OPERATOR                           │
│  - Creates task for SEO Magister                       │
│  - Publishes: task.assigned event                      │
│  - Waits for: task.completed event                     │
│  - Aggregates results                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    SEO MAGISTER                         │
│  - Receives: task.assigned event                       │
│  - Identifies needed Subagents (3)                     │
│  - Publishes: subtask.assigned events (3x)            │
│  - Waits for: subtask.completed events (3x)           │
│  - Aggregates Subagent results                         │
│  - Publishes: task.completed event                     │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  TECHNICAL  │ │   CONTENT   │ │    LINKS    │
│    AGENT    │ │    AGENT    │ │    AGENT    │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 2.2 Event Flow

```
1. USER → ARCHITECT
   Input: "Analyze SEO: example.com"

2. ARCHITECT → OPERATOR
   Event: architect.decision
   Payload: {action: "delegate_seo", url: "example.com"}

3. OPERATOR → EVENT BUS
   Event: task.assigned
   Target: seo-magister
   Priority: P1
   Payload: {action: "analyze_competitor", url: "example.com"}

4. SEO MAGISTER → EVENT BUS (3x)
   Event: subtask.assigned
   Targets: [technical-agent, content-agent, links-agent]
   Priority: P2
   Payload: {url: "example.com", correlation_id: "task-123"}

5. SUBAGENTS → EVENT BUS (3x)
   Event: subtask.completed
   Source: [technical-agent, content-agent, links-agent]
   Priority: P2
   Payload: {results: {...}, correlation_id: "task-123"}

6. SEO MAGISTER → EVENT BUS
   Event: task.completed
   Source: seo-magister
   Priority: P1
   Payload: {report: {...}, correlation_id: "task-123"}

7. OPERATOR → USER
   Output: Comprehensive SEO Report
```

---

## 4. Component Specifications

### 4.1 Technical SEO Agent

**File:** `AIM/src/aim/subagents/seo/technical_agent.py`

**Responsibilities:**
- Analyze robots.txt
- Parse sitemap.xml
- Extract meta tags
- Check page performance
- Validate Schema.org markup

**Input:**
```python
{
    "url": "https://example.com",
    "correlation_id": "task-123"
}
```

**Output:**
```python
{
    "agent": "technical-agent",
    "url": "https://example.com",
    "correlation_id": "task-123",
    "timestamp": "2026-05-09T12:00:00Z",
    "results": {
        "robots_txt": {
            "exists": true,
            "allows_crawling": true,
            "sitemap_url": "https://example.com/sitemap.xml"
        },
        "sitemap": {
            "exists": true,
            "url_count": 150,
            "last_modified": "2026-05-01"
        },
        "meta_tags": {
            "title": "Example Medical Clinic",
            "description": "...",
            "keywords": ["medical", "clinic"],
            "og_tags": {...}
        },
        "performance": {
            "page_speed_score": 85,
            "first_contentful_paint": 1.2,
            "largest_contentful_paint": 2.5,
            "cumulative_layout_shift": 0.1
        },
        "schema": {
            "has_schema": true,
            "types": ["Organization", "MedicalClinic"],
            "valid": true
        }
    },
    "status": "success",
    "duration_seconds": 15.3
}
```

**API Configuration:**

```bash
# .env
GOOGLE_PAGESPEED_API_KEY=your_key_here

# API endpoint
PAGESPEED_API_URL=https://www.googleapis.com/pagespeedonline/v5/runPagespeed
```

**API Request Example:**

```python
import aiohttp

async def get_page_speed(url: str) -> dict:
    """Get PageSpeed Insights data"""
    
    api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY")
    api_url = os.getenv("PAGESPEED_API_URL")
    
    params = {
        "url": url,
        "key": api_key,
        "category": "performance",
        "strategy": "mobile"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params=params) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                raise APIQuotaExceeded("PageSpeed API quota exceeded")
            else:
                raise APIError(f"PageSpeed API error: {response.status}")
```

**APIs Used:**
- Google PageSpeed Insights API (free)
- Direct HTTP requests (robots.txt, sitemap.xml)
- BeautifulSoup (meta tags, schema)

**Error Handling:**
- Timeout: 30 seconds per check
- Retry: 3 attempts with exponential backoff
- Partial failure: Continue with available data

---

### 4.2 Content SEO Agent

**File:** `AIM/src/aim/subagents/seo/content_agent.py`

**Responsibilities:**
- Extract header structure
- Analyze keyword usage
- Calculate content quality metrics
- Assess readability
- Evaluate content structure

**Input:**
```python
{
    "url": "https://example.com",
    "correlation_id": "task-123"
}
```

**Output:**
```python
{
    "agent": "content-agent",
    "url": "https://example.com",
    "correlation_id": "task-123",
    "timestamp": "2026-05-09T12:00:00Z",
    "results": {
        "headers": {
            "h1": ["Main Title"],
            "h2": ["Section 1", "Section 2"],
            "h3": ["Subsection 1.1", "Subsection 1.2"],
            "structure_score": 8.5
        },
        "keywords": {
            "primary": ["medical", "clinic"],
            "density": {"medical": 2.5, "clinic": 1.8},
            "distribution": "good"
        },
        "content_quality": {
            "word_count": 1500,
            "unique_words": 450,
            "readability_score": 65,
            "paragraph_count": 12,
            "avg_paragraph_length": 125
        },
        "structure": {
            "has_intro": true,
            "has_conclusion": true,
            "has_cta": true,
            "sections": 5
        }
    },
    "status": "success",
    "duration_seconds": 8.7
}
```

**APIs Used:**
- Direct HTTP requests + BeautifulSoup
- Readability algorithms (Flesch-Kincaid)

---

### 4.3 Links SEO Agent

**File:** `AIM/src/aim/subagents/seo/links_agent.py`

**Responsibilities:**
- Map internal links
- Analyze external links
- Detect broken links
- Evaluate anchor text
- Assess link quality

**Input:**
```python
{
    "url": "https://example.com",
    "correlation_id": "task-123"
}
```

**Output:**
```python
{
    "agent": "links-agent",
    "url": "https://example.com",
    "correlation_id": "task-123",
    "timestamp": "2026-05-09T12:00:00Z",
    "results": {
        "internal_links": {
            "count": 45,
            "unique_pages": 30,
            "depth_distribution": {1: 10, 2: 20, 3: 15}
        },
        "external_links": {
            "count": 12,
            "domains": ["wikipedia.org", "nih.gov"],
            "nofollow_count": 3
        },
        "broken_links": {
            "count": 2,
            "urls": ["https://example.com/old-page"]
        },
        "anchor_text": {
            "branded": 15,
            "exact_match": 8,
            "partial_match": 12,
            "generic": 10
        }
    },
    "status": "success",
    "duration_seconds": 12.1
}
```

---

### 4.4 SEO Magister Coordination

**File:** `AIM/src/aim/magisters/seo_magister.py` (update existing)

**New Methods:**

```python
async def coordinate_analysis(self, url: str, correlation_id: str) -> dict:
    """Coordinate SEO analysis across 3 Subagents
    
    1. Identify needed Subagents
    2. Dispatch tasks via Event Bus
    3. Wait for results (with timeout)
    4. Aggregate results
    5. Generate report
    """
    
async def dispatch_subagents(self, url: str, correlation_id: str) -> list[str]:
    """Dispatch tasks to Subagents via Event Bus"""
    
async def collect_results(self, correlation_id: str, timeout: int = 300) -> list[dict]:
    """Collect results from Subagents with timeout"""
    
async def aggregate_results(self, results: list[dict]) -> dict:
    """Aggregate Subagent results into comprehensive report
    
    Scoring formula:
    - Technical: 40% weight (performance, schema, meta)
    - Content: 30% weight (readability, structure, keywords)
    - Links: 30% weight (internal, external, broken)
    
    Overall score = weighted average (0-100)
    """
    
    # Extract individual scores
    technical = results[0]["results"]
    content = results[1]["results"]
    links = results[2]["results"]
    
    # Calculate component scores
    technical_score = technical["performance"]["page_speed_score"]
    
    content_score = content["content_quality"]["readability_score"]
    
    # Links score: 100 - (broken_links * 5)
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
        recommendations.append("Optimize page performance (PageSpeed < 70)")
    if content_score < 60:
        recommendations.append("Improve content readability")
    if broken_count > 0:
        recommendations.append(f"Fix {broken_count} broken links")
    if not technical["schema"]["has_schema"]:
        recommendations.append("Add Schema.org markup")
    if content["headers"]["structure_score"] < 7:
        recommendations.append("Improve header structure")
    
    return {
        "score": round(overall_score, 1),
        "recommendations": recommendations,
        "technical": technical,
        "content": content,
        "links": links,
        "summary": {
            "technical_score": technical_score,
            "content_score": content_score,
            "links_score": links_score
        }
    }
```

---

### 4.5 Operator Coordination

**File:** `src/meai/agents/operator.py` (update existing)

**New Methods:**

```python
async def delegate_to_magister(self, magister_id: str, task: Task) -> TaskResult:
    """Delegate task to Magister via Event Bus
    
    1. Publish task.assigned event
    2. Wait for task.completed event
    3. Return result
    """
    
async def wait_for_completion(self, correlation_id: str, timeout: int = 600) -> dict:
    """Wait for Magister to complete task"""
```

---

## 5. Data Models

### 5.1 Task

```python
@dataclass
class Task:
    task_id: str
    action: str
    payload: dict[str, Any]
    priority: EventPriority
    correlation_id: str | None = None
    created_at: datetime
```

### 5.2 TaskResult

```python
@dataclass
class TaskResult:
    task_id: str
    agent_id: str
    status: str  # "success" | "failed" | "partial"
    results: dict[str, Any]
    error: str | None = None
    duration_seconds: float
    completed_at: datetime
```

### 5.3 SEO Report

```python
@dataclass
class SEOReport:
    url: str
    analyzed_at: datetime
    technical: dict  # from Technical Agent
    content: dict    # from Content Agent
    links: dict      # from Links Agent
    summary: dict    # aggregated insights
    recommendations: list[str]
    score: float     # overall SEO score (0-100)
```

**Report Persistence:**

**Database Schema:**
```sql
CREATE TABLE seo_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    analyzed_at TIMESTAMP NOT NULL,
    score FLOAT,
    technical_data JSONB,
    content_data JSONB,
    links_data JSONB,
    summary JSONB,
    recommendations TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_seo_reports_url ON seo_reports(url);
CREATE INDEX idx_seo_reports_analyzed_at ON seo_reports(analyzed_at DESC);
```

**Obsidian Vault Structure:**
```
AIM/obsidian/seo-magister/wiki/reports/
├── 2026-05-09-example-com.md
├── 2026-05-09-competitor1-com.md
├── index.md  # Catalog of all reports
└── ...
```

**Report Format:**
- **Database:** Structured JSON for queries and analytics
- **Obsidian:** Markdown for human readability and history
- **User delivery:** JSON via API + Markdown summary

---

## 6. Event Specifications

### 6.1 task.assigned

```python
{
    "event_type": "task.assigned",
    "event_id": "evt-abc123",
    "timestamp": "2026-05-09T12:00:00Z",
    "source": "operator",
    "target": "seo-magister",
    "reply_to": "operator",  # Where to send result
    "priority": 1,  # P1
    "correlation_id": "task-123",
    "idempotency_key": "task-123",  # Prevent duplicate processing
    "payload": {
        "action": "analyze_competitor",
        "url": "https://example.com"
    }
}
```

### 6.2 subtask.assigned

```python
{
    "event_type": "subtask.assigned",
    "event_id": "evt-def456",
    "timestamp": "2026-05-09T12:00:05Z",
    "source": "seo-magister",
    "target": "technical-agent",
    "reply_to": "seo-magister",  # Where to send result
    "priority": 2,  # P2
    "correlation_id": "task-123",
    "idempotency_key": "subtask-tech-123",  # Prevent duplicate processing
    "payload": {
        "url": "https://example.com"
    }
}
```

### 6.3 subtask.completed

```python
{
    "event_type": "subtask.completed",
    "event_id": "evt-ghi789",
    "timestamp": "2026-05-09T12:00:20Z",
    "source": "technical-agent",
    "target": "seo-magister",  # From reply_to field
    "priority": 2,  # P2
    "correlation_id": "task-123",
    "idempotency_key": "subtask-tech-123",  # Same as request
    "payload": {
        "status": "success",
        "results": {...}
    }
}
```

### 6.4 task.completed

```python
{
    "event_type": "task.completed",
    "event_id": "evt-jkl012",
    "timestamp": "2026-05-09T12:01:00Z",
    "source": "seo-magister",
    "target": "operator",  # From reply_to field
    "priority": 1,  # P1
    "correlation_id": "task-123",
    "idempotency_key": "task-123",  # Same as request
    "payload": {
        "status": "success",
        "report": {...}
    }
}
```

### 6.5 Event Subscription Pattern

**How agents wait for responses:**

```python
async def wait_for_completion(
    self, 
    correlation_id: str, 
    timeout: int = 300
) -> dict:
    """Wait for task completion with exponential backoff polling"""
    
    deadline = time.time() + timeout
    interval = 1  # Start with 1 second
    
    while time.time() < deadline:
        # Poll Event Bus for completion events
        events = await self.event_bus.get_events(
            event_type="task.completed",
            correlation_id=correlation_id,
            status="pending"
        )
        
        if events:
            # Mark as processed
            await self.event_bus.mark_processed(events[0].id)
            return events[0].payload
        
        # Exponential backoff (max 10 seconds)
        await asyncio.sleep(interval)
        interval = min(interval * 1.5, 10)
    
    raise TimeoutError(f"No response for {correlation_id} after {timeout}s")
```

**Event Bus methods:**

```python
class EventBus:
    async def get_events(
        self,
        event_type: str | None = None,
        correlation_id: str | None = None,
        target: str | None = None,
        status: str = "pending"
    ) -> list[BaseEvent]:
        """Query events with filters"""
        
    async def mark_processed(self, event_id: str) -> None:
        """Mark event as processed (prevents re-delivery)"""
```

### 6.6 Event Store Integration

**Purpose:** Immutable audit log for all events

**Automatic Logging:**
- Event Bus automatically writes all events to Event Store
- No additional code needed in agents
- All events persisted with full payload

**Event Store Operations:**

```python
# Event Bus publishes event
await event_bus.publish(event)
# ↓ Automatically writes to Event Store

# Query patterns for debugging
events = await event_store.query(
    correlation_id="task-123",
    order_by="timestamp"
)

# Get failed events
failed = await event_store.query(
    event_type="task.failed",
    time_range=(start_time, end_time)
)

# Replay workflow
workflow_events = await event_store.query(
    correlation_id="task-123"
)
for event in workflow_events:
    print(f"{event.timestamp}: {event.source} → {event.target}")
```

**Retention Policy:**
- All events: 90 days
- Critical events (failures, security): 1 year
- Automatic cleanup via Event Store background job

---

## 7. Error Handling

### 7.1 Timeout Handling

```python
# Operator waits max 10 minutes
OPERATOR_TIMEOUT = 600

# SEO Magister waits max 5 minutes for Subagents
MAGISTER_TIMEOUT = 300

# Subagents have max 30 seconds per operation
SUBAGENT_TIMEOUT = 30
```

### 7.2 Partial Failure

If 1-2 Subagents fail:
- Continue with available results
- Mark report as "partial"
- Include error details
- Still deliver value

If all 3 Subagents fail:
- Return error to Operator
- Log to Event Store
- Notify user

### 7.3 Retry Strategy

```python
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # exponential backoff

# Retry delays: 1s, 2s, 4s
```

### 7.4 Idempotency Implementation

**Purpose:** Prevent duplicate processing on retries

**Mechanism:** Redis cache with TTL

```python
class Agent:
    async def execute_task(self, subtask: Subtask) -> TaskResult:
        """Execute task with idempotency check"""
        
        # Check cache
        cache_key = f"subtask:{subtask.subtask_id}"
        if cached := await self.redis.get(cache_key):
            return json.loads(cached)
        
        # Execute
        result = await self._do_work(subtask)
        
        # Cache result (TTL: 1 hour)
        await self.redis.setex(
            cache_key, 
            3600, 
            json.dumps(result)
        )
        
        return result
```

**Configuration:**
- Storage: Redis (in-memory cache)
- Key format: `subtask:{subtask_id}`
- TTL: 3600 seconds (1 hour)
- Cleanup: Automatic (Redis TTL expiration)

---

## 8. Testing Strategy

### 8.1 Unit Tests

- [ ] Technical Agent: test each check independently
- [ ] Content Agent: test parsing and metrics
- [ ] Links Agent: test link extraction
- [ ] SEO Magister: test coordination logic
- [ ] Operator: test delegation logic

### 8.2 Integration Tests

- [ ] Event Bus: test event publishing/subscribing
- [ ] End-to-end: test full workflow
- [ ] Timeout: test timeout handling
- [ ] Partial failure: test with 1 agent failing

### 8.3 Manual Tests

- [ ] Real website analysis
- [ ] Report quality check
- [ ] Performance measurement

---

## 9. Performance Requirements

- **Total analysis time:** < 5 minutes
- **Technical Agent:** < 30 seconds
- **Content Agent:** < 15 seconds
- **Links Agent:** < 20 seconds
- **Aggregation:** < 5 seconds

---

## 10. Security Considerations

- [ ] Validate URLs (no localhost, no internal IPs)
- [ ] Rate limiting (max 10 requests/minute per domain)
- [ ] Timeout all HTTP requests
- [ ] Sanitize all scraped content
- [ ] No execution of JavaScript from scraped pages

---

## 11. Future Enhancements

- Positions tracking (Serpstat API)
- Backlink analysis (Ahrefs API)
- Competitor comparison
- Historical tracking
- Automated recommendations
- Visual reports (charts, graphs)

---

**Status:** ✅ READY FOR IMPLEMENTATION  
**Version:** 1.1 (Critical fixes applied)  
**Date:** 2026-05-09T12:17:00Z

**Changes from v1.0:**
- ✅ Added `reply_to` field to all events (6.1-6.4)
- ✅ Added `idempotency_key` field to all events (6.1-6.4)
- ✅ Documented event subscription pattern (6.5)
- ✅ Added Event Store integration (6.6)
- ✅ Specified idempotency implementation (7.4)
- ✅ Detailed aggregation algorithm (4.4)
- ✅ Added API configuration (4.1)
- ✅ Specified report persistence (5.3)

**Next Step:** Write implementation plan
