# Technical Design: Keyword Research Agent

**Date:** 2026-05-11
**Feature:** Keyword Research Agent - Full API Integration
**Status:** Design Review Pending
**Product Brief:** [2026-05-11-keyword-research-agent-brief.md](./2026-05-11-keyword-research-agent-brief.md)

---

## Overview

Replace the existing 474-line stub implementation (`AIM/src/aim/subagents/keyword_research_agent.py`) with production-grade Keyword Research Agent featuring:

1. **Three-Layer Architecture:**
   - API Layer: Primary/Fallback pattern with resilience
   - Compliance Layer: Tiered gates with audit trail
   - Prioritization Layer: Adaptive weights with dynamic penalties

2. **Six API Integrations:**
   - Primary: SEMrush (keyword data, volume, difficulty, CPC)
   - Fallback: Ahrefs (keyword data, DR, backlinks)
   - Enrichment: GSC, Yandex Webmaster (position data)
   - Enrichment: Yandex Wordstat, Google Keyword Planner (volume data)

3. **Medical Compliance:**
   - Prohibited language pattern library
   - openFDA API integration (enforcement letters)
   - Risk scoring framework (1-25 scale)
   - Audit trail for regulatory defense

4. **Production Resilience:**
   - Circuit breakers (pybreaker)
   - Retry with exponential backoff (tenacity)
   - Token bucket rate limiting
   - Pydantic schemas for normalization

---

## Technical Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Keyword Research Agent                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              API Layer (Unified Client)               │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Primary: SEMrush  →  Fallback: Ahrefs               │  │
│  │  Enrichment: GSC, Yandex Webmaster, Wordstat, KP     │  │
│  │                                                        │  │
│  │  Resilience:                                          │  │
│  │  • Circuit Breaker (pybreaker)                        │  │
│  │  • Retry + Exponential Backoff (tenacity)            │  │
│  │  • Token Bucket Rate Limiting                         │  │
│  │  • Pydantic Normalization                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Compliance Layer (Tiered Gates)             │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Stage 1: Pattern Matching (<10ms)                    │  │
│  │  Stage 2: openFDA Lookup (cached 24h)                │  │
│  │  Stage 3: Risk Scoring (Likelihood × Severity)       │  │
│  │                                                        │  │
│  │  Actions:                                             │  │
│  │  • CRITICAL (20-25): Block + Log                     │  │
│  │  • HIGH (15-19): Reduce priority 50% + Flag          │  │
│  │  • MEDIUM/LOW (1-14): Pass + Document                │  │
│  │                                                        │  │
│  │  Audit Trail → Event Store                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │      Prioritization Layer (Adaptive Formula)          │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Formula:                                             │  │
│  │  (Volume × Intent × Position) / (Difficulty × Comp)  │  │
│  │                                                        │  │
│  │  Medical Intent Boost:                                │  │
│  │  • Transactional: 40% (vs 30% standard)              │  │
│  │  • Informational: 30%                                 │  │
│  │                                                        │  │
│  │  Dynamic SERP Penalties:                              │  │
│  │  • Track actual CTR by SERP feature                  │  │
│  │  • Auto-adjust penalties (AI Overviews, Snippets)    │  │
│  │                                                        │  │
│  │  Priority Classification:                             │  │
│  │  • P0: 80-100 (immediate action)                     │  │
│  │  • P1: 60-79 (high priority)                         │  │
│  │  • P2: 40-59 (medium priority)                       │  │
│  │  • P3: 0-39 (low priority)                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│                   Results + Audit Trail                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Model Changes

#### New Models (Pydantic)

**1. API Response Schemas:**

```python
# AIM/src/aim/subagents/schemas/api_responses.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SEMrushKeywordData(BaseModel):
    """SEMrush API response schema"""
    keyword: str
    search_volume: int
    keyword_difficulty: float = Field(ge=0, le=100)
    cpc: float = Field(ge=0)
    competition: float = Field(ge=0, le=1)
    intent: Optional[str] = None
    serp_features: List[str] = Field(default_factory=list)
    
class AhrefsKeywordData(BaseModel):
    """Ahrefs API response schema"""
    keyword: str
    search_volume: int
    keyword_difficulty: int = Field(ge=0, le=100)
    cpc: float = Field(ge=0)
    clicks: Optional[int] = None
    parent_topic: Optional[str] = None
    
class GSCPositionData(BaseModel):
    """Google Search Console position data"""
    keyword: str
    position: float = Field(ge=1)
    clicks: int = Field(ge=0)
    impressions: int = Field(ge=0)
    ctr: float = Field(ge=0, le=1)
    
class YandexWebmasterData(BaseModel):
    """Yandex Webmaster position data"""
    keyword: str
    position: float = Field(ge=1)
    shows: int = Field(ge=0)
    clicks: int = Field(ge=0)
```

**2. Compliance Models:**

```python
# AIM/src/aim/subagents/schemas/compliance.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
class ComplianceCheckResult(BaseModel):
    """Result of compliance check"""
    keyword: str
    risk_level: RiskLevel
    risk_score: int = Field(ge=1, le=25)
    likelihood: int = Field(ge=1, le=5)
    severity: int = Field(ge=1, le=5)
    flagged_patterns: List[str] = Field(default_factory=list)
    fda_enforcement_match: Optional[str] = None
    action_taken: str  # "blocked", "priority_reduced", "passed"
    rationale: str
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    
class AuditTrailEntry(BaseModel):
    """Audit trail entry for regulatory defense"""
    keyword: str
    compliance_result: ComplianceCheckResult
    original_priority: float
    adjusted_priority: Optional[float] = None
    decision: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**3. Prioritization Models:**

```python
# AIM/src/aim/subagents/schemas/prioritization.py

from pydantic import BaseModel, Field
from typing import Optional, Dict
from enum import Enum

class PriorityTier(str, Enum):
    P0 = "P0"  # 80-100
    P1 = "P1"  # 60-79
    P2 = "P2"  # 40-59
    P3 = "P3"  # 0-39
    
class KeywordPriority(BaseModel):
    """Keyword priority calculation"""
    keyword: str
    priority_score: float = Field(ge=0, le=100)
    priority_tier: PriorityTier
    
    # Components
    volume_score: float
    intent_score: float
    position_score: float
    difficulty_score: float
    competition_score: float
    
    # Adjustments
    compliance_penalty: float = Field(default=0)
    serp_penalty: float = Field(default=0)
    
    # Metadata
    serp_features: list[str] = Field(default_factory=list)
    intent_type: str  # "transactional", "informational", "navigational"
```

**4. Unified Result Model:**

```python
# AIM/src/aim/subagents/schemas/results.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class KeywordAnalysisResult(BaseModel):
    """Complete keyword analysis result"""
    keyword: str
    
    # API Data
    search_volume: int
    keyword_difficulty: float
    cpc: float
    competition: float
    position: Optional[float] = None
    
    # Compliance
    compliance_check: ComplianceCheckResult
    
    # Prioritization
    priority: KeywordPriority
    
    # Metadata
    data_sources: List[str]  # ["semrush", "ahrefs", "gsc"]
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
class KeywordResearchReport(BaseModel):
    """Final report with all keywords"""
    seed_keyword: str
    total_keywords: int
    keywords: List[KeywordAnalysisResult]
    
    # Summary stats
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int
    blocked_count: int
    
    # Audit trail
    audit_trail: List[AuditTrailEntry]
    
    # Metadata
    execution_time_seconds: float
    api_calls_made: Dict[str, int]
    cost_estimate_usd: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)
```

### File-Level Changes

#### Files to Modify

**1. `AIM/src/aim/subagents/keyword_research_agent.py`** (MAJOR REWRITE)
- Replace stub implementation with production code
- Add unified API client with primary/fallback
- Integrate compliance layer
- Implement adaptive prioritization
- Add resilience patterns (circuit breaker, retry, rate limiting)

**2. `AIM/src/aim/subagents/__init__.py`**
- Export new schemas
- Export KeywordResearchAgent

#### Files to Create

**Wave 1: Core Infrastructure**

1. `AIM/src/aim/subagents/api_clients/__init__.py`
2. `AIM/src/aim/subagents/api_clients/base.py` - Base API client with resilience
3. `AIM/src/aim/subagents/api_clients/semrush.py` - SEMrush client
4. `AIM/src/aim/subagents/api_clients/ahrefs.py` - Ahrefs client
5. `AIM/src/aim/subagents/api_clients/rate_limiter.py` - Token bucket implementation

**Wave 2: Compliance**

6. `AIM/src/aim/subagents/compliance/__init__.py`
7. `AIM/src/aim/subagents/compliance/checker.py` - Tiered compliance gates
8. `AIM/src/aim/subagents/compliance/patterns.py` - Prohibited language library
9. `AIM/src/aim/subagents/compliance/fda_client.py` - openFDA API client
10. `AIM/src/aim/subagents/compliance/risk_scorer.py` - Risk scoring (1-25)

**Wave 3: Prioritization**

11. `AIM/src/aim/subagents/prioritization/__init__.py`
12. `AIM/src/aim/subagents/prioritization/calculator.py` - Priority formula
13. `AIM/src/aim/subagents/prioritization/serp_tracker.py` - SERP feature CTR tracking
14. `AIM/src/aim/subagents/prioritization/weights.py` - Adaptive weight system

**Wave 4: Enrichment APIs**

15. `AIM/src/aim/subagents/api_clients/gsc.py` - Google Search Console client
16. `AIM/src/aim/subagents/api_clients/yandex_webmaster.py` - Yandex Webmaster client
17. `AIM/src/aim/subagents/api_clients/yandex_wordstat.py` - Yandex Wordstat client
18. `AIM/src/aim/subagents/api_clients/keyword_planner.py` - Google Keyword Planner client

**Schemas (Wave 1)**

19. `AIM/src/aim/subagents/schemas/__init__.py`
20. `AIM/src/aim/subagents/schemas/api_responses.py`
21. `AIM/src/aim/subagents/schemas/compliance.py`
22. `AIM/src/aim/subagents/schemas/prioritization.py`
23. `AIM/src/aim/subagents/schemas/results.py`

**Tests (Wave 5)**

24. `AIM/tests/subagents/test_keyword_research_agent.py`
25. `AIM/tests/subagents/api_clients/test_semrush.py`
26. `AIM/tests/subagents/api_clients/test_ahrefs.py`
27. `AIM/tests/subagents/compliance/test_checker.py`
28. `AIM/tests/subagents/prioritization/test_calculator.py`

**Configuration**

29. `AIM/config/api_credentials.example.yaml` - API credentials template
30. `AIM/config/compliance_patterns.yaml` - Prohibited language patterns
31. `AIM/config/prioritization_weights.yaml` - Default weights

---

## Edge Cases and Error Handling

### 1. Primary API Fails

**Scenario:** SEMrush API timeout or rate limit exceeded

**Handling:**
```python
try:
    data = await semrush_client.get_keywords(seed)
except (TimeoutError, RateLimitError) as e:
    logger.warning(f"SEMrush failed: {e}, falling back to Ahrefs")
    circuit_breaker.record_failure()
    data = await ahrefs_client.get_keywords(seed)
```

**Result:** Automatic fallback to Ahrefs, user sees note in results

### 2. Both Primary APIs Fail

**Scenario:** Both SEMrush and Ahrefs unavailable

**Handling:**
```python
if not semrush_data and not ahrefs_data:
    raise APIUnavailableError(
        "Unable to retrieve keyword data (both primary sources unavailable)"
    )
```

**Result:** Error returned to user, logged to Event Store, user can retry

### 3. Compliance API Degraded

**Scenario:** openFDA API timeout

**Handling:**
```python
try:
    fda_match = await fda_client.check_enforcement(keyword)
except TimeoutError:
    logger.warning("openFDA unavailable, using pattern matching only")
    fda_match = None
    degraded_mode = True
```

**Result:** Falls back to pattern matching, warning in results, audit trail notes degraded mode

### 4. Partial Enrichment Data

**Scenario:** GSC returns data but Yandex Webmaster fails

**Handling:**
```python
position_data = {}
if gsc_data:
    position_data['gsc'] = gsc_data
if yandex_data:
    position_data['yandex'] = yandex_data

# Use whatever data is available
if position_data:
    priority.position_score = calculate_position_score(position_data)
else:
    priority.position_score = 50  # Neutral score
```

**Result:** Graceful degradation, uses available data, notes missing sources

### 5. Invalid Seed Keyword

**Scenario:** User provides empty string or special characters only

**Handling:**
```python
if not seed_keyword or not seed_keyword.strip():
    raise ValueError("Seed keyword cannot be empty")
    
if not re.match(r'^[\w\s\-]+$', seed_keyword):
    raise ValueError("Seed keyword contains invalid characters")
```

**Result:** Validation error returned immediately, no API calls made

### 6. Circuit Breaker Open

**Scenario:** API has failed 5 times, circuit breaker opens

**Handling:**
```python
if circuit_breaker.current_state == STATE_OPEN:
    logger.info(f"Circuit breaker open for {api_name}, skipping")
    return None  # Trigger fallback
```

**Result:** Skip failing API for 60s, automatic recovery when circuit closes

---

## Testing Strategy

### Unit Tests (80%+ coverage)

**API Clients:**
- Test circuit breaker behavior (fail_max=5, reset after 60s)
- Test retry with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max)
- Test token bucket rate limiting (refill rate, burst capacity)
- Test Pydantic schema validation (valid/invalid data)

**Compliance:**
- Test pattern matching (100+ prohibited patterns)
- Test risk scoring (Likelihood × Severity = 1-25)
- Test action determination (CRITICAL=block, HIGH=reduce 50%, MEDIUM/LOW=pass)
- Test audit trail creation

**Prioritization:**
- Test formula calculation with known inputs
- Test medical intent boost (40% transactional vs 30% standard)
- Test SERP penalty application
- Test priority tier classification (P0-P3)

### Integration Tests

**Event Bus Integration:**
```python
async def test_keyword_research_via_event_bus():
    # Publish task event
    await event_bus.publish(Event(
        type="task.keyword_research",
        data={"seed_keyword": "dental implants"}
    ))
    
    # Wait for result event
    result = await event_bus.subscribe("result.keyword_research")
    
    assert result.data["total_keywords"] > 100
    assert result.data["p0_count"] > 0
```

**Obsidian Integration:**
```python
async def test_audit_trail_saved_to_vault():
    result = await agent.execute_task(task)
    
    # Check vault for audit trail
    vault_path = "AIM/obsidian/seo-magister/raw/keyword-research/"
    audit_file = f"{vault_path}/audit-{task.subtask_id}.md"
    
    assert os.path.exists(audit_file)
    content = open(audit_file).read()
    assert "compliance_check" in content
```

**Database Integration:**
```python
async def test_results_saved_to_database():
    result = await agent.execute_task(task)
    
    # Check database
    async with db.session() as session:
        saved = await session.get(TaskResult, result.subtask_id)
        assert saved.status == "success"
        assert saved.result["total_keywords"] > 100
```

### E2E Tests (Real APIs)

**Full Workflow:**
```python
@pytest.mark.e2e
@pytest.mark.requires_api_keys
async def test_full_keyword_research_workflow():
    """Test with real SEMrush/Ahrefs APIs"""
    agent = KeywordResearchAgent(
        semrush_api_key=os.getenv("SEMRUSH_API_KEY"),
        ahrefs_api_key=os.getenv("AHREFS_API_KEY")
    )
    
    task = Task(
        subtask_id="test-001",
        action="keyword_research",
        description='Research keywords for "dental implants near me"'
    )
    
    result = await agent.execute_task(task)
    
    assert result.status == "success"
    assert result.result["total_keywords"] >= 100
    assert result.result["p0_count"] > 0
    assert result.duration_seconds < 900  # < 15 min
    assert result.result["cost_estimate_usd"] < 5.0
```

### Performance Benchmarks

**Execution Time:**
```python
@pytest.mark.benchmark
async def test_execution_time_standard_analysis():
    """Standard analysis (3 competitors) < 15 min"""
    start = time.time()
    result = await agent.execute_task(task)
    duration = time.time() - start
    
    assert duration < 900  # 15 minutes
```

**API Call Efficiency:**
```python
@pytest.mark.benchmark
async def test_api_call_count():
    """Minimize API calls for cost efficiency"""
    with mock.patch('httpx.AsyncClient.get') as mock_get:
        await agent.execute_task(task)
        
        # SEMrush: 1 call (keyword overview)
        # Ahrefs: 0 calls (fallback not triggered)
        # openFDA: ~10 calls (cached after first)
        assert mock_get.call_count < 15
```

---

## Out of Scope

**Explicitly NOT included in this implementation:**

1. **Competitive Gap Prioritization**
   - Requires: Competitor tracking system, SERP scraping, backlink analysis
   - Reason: Too much infrastructure for uncertain payoff
   - Future: Can add in Phase 2 if user feedback shows demand

2. **ROI-Weighted Priority**
   - Requires: Conversion tracking, LTV estimation, ranking cost modeling
   - Reason: Fragile due to sparse conversion data in medical marketing
   - Future: Can add when conversion data becomes available

3. **Real-Time FDA Enforcement Blocking**
   - Requires: openFDA API rate limit handling (240 req/min)
   - Reason: 200-500ms latency per keyword, 24h cache is sufficient
   - Future: Can add if regulatory requirements change

4. **All 6 APIs in Wave 1**
   - Reason: Start with quality (SEMrush + Ahrefs), add enrichment later
   - Future: Wave 4 adds GSC, Yandex Webmaster, Wordstat, Keyword Planner

5. **Machine Learning Priority Model**
   - Requires: Historical performance data, training pipeline, model serving
   - Reason: Multi-factor formula is sufficient for MVP
   - Future: Can add ML layer when we have 6+ months of data

---

## Dependencies

### Python Packages (add to `requirements.txt`)

```
# API Clients
httpx>=0.27.0  # Async HTTP client
pydantic>=2.0.0  # Data validation

# Resilience
pybreaker>=1.0.0  # Circuit breaker
tenacity>=8.2.0  # Retry with exponential backoff

# Rate Limiting
aiolimiter>=1.1.0  # Token bucket rate limiter

# Caching
aiocache>=0.12.0  # Async caching (for openFDA 24h cache)

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
httpx-mock>=0.7.0  # Mock httpx requests
```

### External APIs

**Primary APIs (required):**
1. **SEMrush API** - $449.95/month (Business plan)
   - Endpoints: keyword_overview, keyword_magic_tool
   - Rate Limits: 10,000-40,000 units/day
   - Cost per request: ~$0.04

2. **Ahrefs API** - $129-$449/month
   - Endpoints: keywords_data, keywords_for_site
   - Rate Limits: 60 RPM
   - Cost per request: ~$0.05

**Compliance API (free):**
3. **openFDA API** - Free
   - Endpoint: /drug/enforcement.json
   - Rate Limits: 240 requests/minute, 120,000/day
   - Cost: $0

**Enrichment APIs (optional, Wave 4):**
4. **Google Search Console API** - Free
   - Endpoint: searchanalytics.query
   - Rate Limits: 1,200 QPM per site
   - Cost: $0

5. **Yandex Webmaster API** - Free
   - Endpoint: /user/{userId}/hosts/{hostId}/search-queries/popular
   - Rate Limits: 100 requests/day
   - Cost: $0

6. **Yandex Wordstat API** - ~$50/month
   - Endpoint: GetWordstatReport
   - Rate Limits: 10 reports/minute
   - Cost per request: ~$0.02

7. **Google Keyword Planner API** - Free (requires Google Ads account)
   - Endpoint: KeywordPlanService.GenerateKeywordIdeas
   - Rate Limits: 15,000 operations/day
   - Cost: $0

### Configuration Files

**API Credentials Template:**
```yaml
# AIM/config/api_credentials.example.yaml
semrush:
  api_key: "YOUR_SEMRUSH_API_KEY"
  base_url: "https://api.semrush.com"
  
ahrefs:
  api_key: "YOUR_AHREFS_API_KEY"
  base_url: "https://apiv2.ahrefs.com"
  
google_search_console:
  credentials_file: "path/to/gsc-credentials.json"
  
yandex_webmaster:
  oauth_token: "YOUR_YANDEX_OAUTH_TOKEN"
  user_id: "YOUR_USER_ID"
```

**Prohibited Language Patterns:**
```yaml
# AIM/config/compliance_patterns.yaml
prohibited_patterns:
  - pattern: "cure|cures|curing"
    severity: 5
    rationale: "FDA prohibits disease cure claims"
    
  - pattern: "guaranteed|guarantee"
    severity: 4
    rationale: "Absolute outcome claims prohibited"
    
  - pattern: "FDA approved|FDA cleared"
    severity: 5
    rationale: "Misrepresentation of FDA status"
    
  # ... 100+ patterns total
```

**Prioritization Weights:**
```yaml
# AIM/config/prioritization_weights.yaml
intent_weights:
  transactional: 0.40  # Medical marketing boost
  informational: 0.30
  navigational: 0.20
  
serp_penalties:
  ai_overview: 0.50  # 50% CTR reduction
  featured_snippet: 0.30
  people_also_ask: 0.15
  
priority_thresholds:
  p0_min: 80
  p1_min: 60
  p2_min: 40
  p3_min: 0
```

---

## Next Steps

1. **Dual-Model Spec Review** (Standard governance)
   - Product lens: deep-product-reviewer agent
   - Technical lens: secondary provider (Codex) or deep-spec-reviewer

2. **Implementation Plan** (5 waves, 5 sprints)
   - Wave 1: Core Infrastructure (Sprint 1)
   - Wave 2: Compliance Integration (Sprint 2)
   - Wave 3: Prioritization Formula (Sprint 3)
   - Wave 4: Optional Enrichment (Sprint 4)
   - Wave 5: Testing & Deployment (Sprint 5)

3. **User Approval** (Final gate before autonomous execution)

---

**Status:** Ready for dual-model review
**Estimated Implementation Time:** 4-6 weeks (5 sprints)
**Estimated Cost:** ~$3-5 per analysis (SEMrush + Ahrefs API costs)
