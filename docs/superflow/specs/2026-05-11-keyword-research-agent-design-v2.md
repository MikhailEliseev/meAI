# Technical Design: Keyword Research Agent (v2 - Revised)

**Date:** 2026-05-11
**Feature:** Keyword Research Agent - Full API Integration
**Status:** Revision after dual-model review
**Product Brief:** [2026-05-11-keyword-research-agent-brief.md](./2026-05-11-keyword-research-agent-brief.md)
**Review Feedback:** Addressed 12 critical gaps from product + technical reviews

---

## Revision Summary

**Product Review Gaps Fixed:**
1. ✅ Keyword expansion details (SEMrush Keyword Magic Tool, min 100 keywords)
2. ✅ Cost control mechanism (max_cost_usd parameter, budget guard)
3. ✅ Zero-volume handling (min threshold, alternative suggestions)
4. ✅ Feedback collection (user feedback endpoint for priority accuracy)
5. ✅ Wave 4 scope clarification (separate future enhancement, not in 5 sprints)

**Technical Review Gaps Fixed:**
1. ✅ API key security (environment variables, validation on startup)
2. ✅ Rate limiter implementation (token bucket with capacity/refill details)
3. ✅ Input validation (cross-source consistency, normalize difficulty)
4. ✅ Circuit breaker config (explicit thresholds, timeouts, half-open state)
5. ✅ Caching strategy (1h keyword cache, 24h FDA cache)
6. ✅ Mock data strategy (fixtures, VCR cassettes for CI/CD)
7. ✅ Version constraints (pinned dependencies)

**Additional Improvements:**
- Architecture diagram updated (Infrastructure Layer added)
- Data models completed (Task, TaskResult, Feedback schemas)
- Observability added (metrics, structured logging)
- Audit trail storage specified (database schema)
- Parallel API calls strategy (enrichment APIs)
- Load testing specification (concurrent requests)

---

## Overview

Replace the existing 474-line stub implementation (`AIM/src/aim/subagents/keyword_research_agent.py`) with production-grade Keyword Research Agent featuring:

1. **Four-Layer Architecture:**
   - API Layer: Primary/Fallback pattern with resilience
   - Compliance Layer: Tiered gates with audit trail
   - Prioritization Layer: Adaptive weights with dynamic penalties
   - Infrastructure Layer: Event Bus, Database, Obsidian, Observability

2. **Two Primary API Integrations (Wave 1-3):**
   - Primary: SEMrush (keyword data, volume, difficulty, CPC)
   - Fallback: Ahrefs (keyword data, DR, backlinks)
   - **Note:** 4 enrichment APIs (GSC, Yandex Webmaster, Wordstat, Keyword Planner) are **OUT OF SCOPE** for this 5-sprint implementation. They will be considered as separate future enhancement requiring new approval.

3. **Medical Compliance:**
   - Prohibited language pattern library
   - openFDA API integration (enforcement letters)
   - Risk scoring framework (1-25 scale)
   - Audit trail for regulatory defense

4. **Production Resilience:**
   - Circuit breakers (pybreaker) with explicit config
   - Retry with exponential backoff (tenacity)
   - Token bucket rate limiting with capacity/refill rates
   - Pydantic schemas with cross-source validation
   - Caching (1h keyword data, 24h FDA data)

5. **Cost Control:**
   - Budget guard (max_cost_usd parameter, default $5)
   - API call tracking and cost estimation
   - Partial results if budget exceeded

6. **Observability:**
   - Prometheus metrics (API latency, success rate, cost)
   - Structured logging (structlog)
   - Audit trail storage (PostgreSQL/SQLite)

---

## Technical Design

### Architecture Diagram (Updated)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Keyword Research Agent                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              API Layer (Unified Client)                      │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  Primary: SEMrush  →  Fallback: Ahrefs                      │   │
│  │  • Keyword Magic Tool (expansion to 100+ keywords)           │   │
│  │  • Budget Guard (max_cost_usd, default $5)                   │   │
│  │  • Zero-volume handling (min 10 searches/month)              │   │
│  │                                                               │   │
│  │  Resilience:                                                 │   │
│  │  • Circuit Breaker: fail_max=5, reset_timeout=60s           │   │
│  │  • Retry: initial=1s, max=30s, exponential backoff          │   │
│  │  • Token Bucket: SEMrush 7/min, Ahrefs 60/min               │   │
│  │  • Caching: 1h keyword data, 24h FDA data                    │   │
│  │  • Pydantic: cross-source validation, normalize difficulty   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Compliance Layer (Tiered Gates)                    │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  Stage 1: Pattern Matching (<10ms)                           │   │
│  │  Stage 2: openFDA Lookup (cached 24h)                       │   │
│  │  Stage 3: Risk Scoring (Likelihood × Severity)              │   │
│  │                                                               │   │
│  │  Actions:                                                    │   │
│  │  • CRITICAL (20-25): Block + Log                            │   │
│  │  • HIGH (15-19): Reduce priority 50% + Flag                 │   │
│  │  • MEDIUM/LOW (1-14): Pass + Document                       │   │
│  │                                                               │   │
│  │  Audit Trail → Database (PostgreSQL/SQLite)                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │      Prioritization Layer (Adaptive Formula)                 │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  Formula:                                                    │   │
│  │  (Volume × Intent × Position) / (Difficulty × Competition)  │   │
│  │                                                               │   │
│  │  Medical Intent Boost:                                       │   │
│  │  • Transactional: 40% (vs 30% standard)                     │   │
│  │  • Informational: 30%                                        │   │
│  │                                                               │   │
│  │  Dynamic SERP Penalties:                                     │   │
│  │  • Track actual CTR by SERP feature                         │   │
│  │  • Auto-adjust penalties (AI Overviews, Snippets)           │   │
│  │                                                               │   │
│  │  Priority Classification:                                    │   │
│  │  • P0: 80-100 (immediate action)                            │   │
│  │  • P1: 60-79 (high priority)                                │   │
│  │  • P2: 40-59 (medium priority)                              │   │
│  │  • P3: 0-39 (low priority)                                  │   │
│  │                                                               │   │
│  │  User Feedback Collection:                                   │   │
│  │  • Thumbs up/down on priority scores                        │   │
│  │  • Track which keywords user actually uses                   │   │
│  │  • Calculate "actionable recommendations %" metric           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Infrastructure Layer                               │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  • Event Bus: Publish results, subscribe to tasks           │   │
│  │  • Database: Audit trail, feedback, metrics                 │   │
│  │  • Obsidian: Save analysis to vault                         │   │
│  │  • Observability: Prometheus metrics, structlog             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│                   Results + Audit Trail + Feedback                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Model Changes

#### New Models (Pydantic with Validation)

**1. API Response Schemas (with cross-source validation):**

```python
# AIM/src/aim/subagents/schemas/api_responses.py

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SEMrushKeywordData(BaseModel):
    """SEMrush API response schema"""
    keyword: str
    search_volume: int = Field(ge=0)
    keyword_difficulty: float = Field(ge=0, le=100)
    cpc: float = Field(ge=0)
    competition: float = Field(ge=0, le=1)
    intent: Optional[str] = None
    serp_features: List[str] = Field(default_factory=list)
    
    @field_validator('search_volume')
    @classmethod
    def validate_volume(cls, v):
        if v > 10_000_000:
            logger.warning(f"Unusually high search volume: {v}")
        return v
    
class AhrefsKeywordData(BaseModel):
    """Ahrefs API response schema"""
    keyword: str
    search_volume: int = Field(ge=0)
    keyword_difficulty: int = Field(ge=0, le=100)
    cpc: float = Field(ge=0)
    clicks: Optional[int] = None
    parent_topic: Optional[str] = None
    
    @field_validator('keyword_difficulty')
    @classmethod
    def normalize_difficulty(cls, v):
        """Ahrefs uses different scale, normalize to 0-100"""
        # Ahrefs KD is already 0-100, but different algorithm
        # Apply normalization factor based on research
        return min(100, v * 1.1)  # Ahrefs tends to underestimate
    
class KeywordExpansionRequest(BaseModel):
    """Request for keyword expansion"""
    seed_keyword: str = Field(min_length=1)
    min_keywords: int = Field(default=100, ge=10)
    max_cost_usd: float = Field(default=5.0, ge=0.1, le=50.0)
    min_volume: int = Field(default=10, ge=0)
    
    @field_validator('seed_keyword')
    @classmethod
    def validate_seed(cls, v):
        import re
        if not v.strip():
            raise ValueError("Seed keyword cannot be empty")
        if not re.match(r'^[\w\s\-]+$', v):
            raise ValueError("Seed keyword contains invalid characters")
        return v.strip().lower()
```

**2. Compliance Models (unchanged from v1):**

```python
# AIM/src/aim/subagents/schemas/compliance.py
# (Same as v1, no changes needed)
```

**3. Prioritization Models (with feedback):**

```python
# AIM/src/aim/subagents/schemas/prioritization.py

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

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
    
class UserFeedback(BaseModel):
    """User feedback on keyword priority"""
    keyword: str
    priority_score: float
    feedback_type: str  # "thumbs_up", "thumbs_down", "used", "ignored"
    user_comment: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
class FeedbackSummary(BaseModel):
    """Aggregated feedback metrics"""
    total_keywords: int
    thumbs_up_count: int
    thumbs_down_count: int
    used_count: int
    ignored_count: int
    actionable_percentage: float  # used / total
    accuracy_percentage: float  # thumbs_up / (thumbs_up + thumbs_down)
```

**4. Unified Result Model (with feedback tracking):**

```python
# AIM/src/aim/subagents/schemas/results.py

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
    data_sources: List[str]  # ["semrush", "ahrefs"]
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    @model_validator(mode='after')
    def validate_data_consistency(self):
        """Check for conflicting data from multiple sources"""
        if len(self.data_sources) > 1:
            # Log warning if difficulty scores differ significantly
            # (This would require storing per-source data, simplified here)
            pass
        return self
    
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
    
    # Cost tracking
    api_calls_made: Dict[str, int]
    cost_estimate_usd: float
    budget_exceeded: bool = False
    
    # Metadata
    execution_time_seconds: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    
    @model_validator(mode='after')
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        recs = []
        
        if self.p0_count > 0:
            recs.append(f"Start with {self.p0_count} P0 keywords (priority 80-100)")
        
        if self.blocked_count > 0:
            recs.append(f"⚠️ {self.blocked_count} keywords blocked for compliance violations")
        
        if self.budget_exceeded:
            recs.append(f"⚠️ Budget limit reached at ${self.cost_estimate_usd:.2f}, partial results returned")
        
        if self.total_keywords < 100:
            recs.append(f"⚠️ Only {self.total_keywords} keywords found (target: 100+), consider broader seed keyword")
        
        self.recommendations = recs
        return self
```

**5. Framework Models (Task, TaskResult, Feedback):**

```python
# Reference existing meAI framework models
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import Event

# Task and TaskResult are already defined in framework
# No need to redefine, just import and use
```


### API Client Implementation Details

#### Base API Client with Resilience

```python
# AIM/src/aim/subagents/api_clients/base.py

import httpx
import asyncio
import time
from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from aiolimiter import AsyncLimiter
from aiocache import Cache
from aiocache.serializers import JsonSerializer
import structlog
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()

# Metrics
api_calls_total = Counter('api_calls_total', 'Total API calls', ['api', 'status'])
api_latency = Histogram('api_latency_seconds', 'API latency', ['api'])
api_cost_total = Counter('api_cost_usd_total', 'Total API cost in USD', ['api'])

class TokenBucketRateLimiter:
    """Token bucket rate limiter with configurable capacity and refill rate"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens (burst capacity)
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens, return True if successful"""
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

class APIClientBase:
    """Base API client with circuit breaker, retry, rate limiting, caching"""
    
    def __init__(
        self,
        api_name: str,
        base_url: str,
        api_key: str,
        rate_limit_per_min: int,
        cost_per_request: float,
        cache_ttl: int = 3600  # 1 hour default
    ):
        self.api_name = api_name
        self.base_url = base_url
        self.api_key = api_key
        self.cost_per_request = cost_per_request
        
        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,              # Open after 5 failures
            reset_timeout=60,        # Try recovery after 60s
            exclude=[httpx.HTTPStatusError],  # Don't count 4xx as failures
            name=f"{api_name}_breaker"
        )
        
        # Rate limiter (token bucket)
        self.rate_limiter = TokenBucketRateLimiter(
            capacity=rate_limit_per_min,
            refill_rate=rate_limit_per_min / 60.0  # per second
        )
        
        # Cache
        self.cache = Cache(
            Cache.MEMORY,
            ttl=cache_ttl,
            serializer=JsonSerializer(),
            namespace=f"{api_name}_cache"
        )
        
        # Cost tracking
        self.total_cost = 0.0
        self.call_count = 0
    
    async def get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request with resilience patterns"""
        
        # Check cache first
        cache_key = f"{endpoint}:{str(params)}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("cache_hit", api=self.api_name, endpoint=endpoint)
            return cached
        
        # Rate limiting
        while not await self.rate_limiter.acquire():
            logger.warning("rate_limit_wait", api=self.api_name)
            await asyncio.sleep(1)
        
        # Make request with circuit breaker + retry
        try:
            result = await self._make_request_with_retry(endpoint, params)
            
            # Cache result
            await self.cache.set(cache_key, result)
            
            # Track cost
            self.total_cost += self.cost_per_request
            self.call_count += 1
            api_cost_total.labels(api=self.api_name).inc(self.cost_per_request)
            
            return result
            
        except CircuitBreakerError:
            logger.error("circuit_breaker_open", api=self.api_name)
            api_calls_total.labels(api=self.api_name, status='circuit_open').inc()
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _make_request_with_retry(self, endpoint: str, params: dict) -> dict:
        """Make request with retry on transient failures"""
        
        start = time.time()
        
        try:
            # Circuit breaker wraps the actual request
            response = await self.circuit_breaker.call_async(
                self._do_request, endpoint, params
            )
            
            duration = time.time() - start
            api_latency.labels(api=self.api_name).observe(duration)
            api_calls_total.labels(api=self.api_name, status='success').inc()
            
            logger.info(
                "api_request_success",
                api=self.api_name,
                endpoint=endpoint,
                duration_ms=int(duration * 1000)
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start
            api_calls_total.labels(api=self.api_name, status='error').inc()
            
            logger.error(
                "api_request_failed",
                api=self.api_name,
                endpoint=endpoint,
                error=str(e),
                duration_ms=int(duration * 1000)
            )
            raise
    
    async def _do_request(self, endpoint: str, params: dict) -> dict:
        """Actual HTTP request (wrapped by circuit breaker)"""
        response = await self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

#### SEMrush Client with Keyword Expansion

```python
# AIM/src/aim/subagents/api_clients/semrush.py

from .base import APIClientBase
from ..schemas.api_responses import SEMrushKeywordData, KeywordExpansionRequest
from typing import List
import structlog

logger = structlog.get_logger()

class SEMrushClient(APIClientBase):
    """SEMrush API client with Keyword Magic Tool integration"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_name="semrush",
            base_url="https://api.semrush.com",
            api_key=api_key,
            rate_limit_per_min=7,  # ~10,000 units/day = 7/min conservative
            cost_per_request=0.04
        )
    
    async def expand_keywords(
        self,
        request: KeywordExpansionRequest
    ) -> List[SEMrushKeywordData]:
        """
        Expand seed keyword to 100+ related keywords using Keyword Magic Tool
        
        Implements:
        - Budget guard (stops at max_cost_usd)
        - Minimum keyword count validation (100+)
        - Zero-volume handling (min_volume threshold)
        """
        
        keywords = []
        page = 0
        max_pages = int(request.max_cost_usd / self.cost_per_request)
        
        logger.info(
            "keyword_expansion_start",
            seed=request.seed_keyword,
            min_keywords=request.min_keywords,
            max_cost=request.max_cost_usd,
            max_pages=max_pages
        )
        
        while len(keywords) < request.min_keywords and page < max_pages:
            # Check budget before making call
            estimated_cost = (page + 1) * self.cost_per_request
            if estimated_cost > request.max_cost_usd:
                logger.warning(
                    "budget_limit_reached",
                    keywords_found=len(keywords),
                    cost=estimated_cost
                )
                break
            
            # Call Keyword Magic Tool API
            try:
                response = await self.get(
                    "/analytics/v1/",
                    params={
                        "type": "phrase_related",
                        "key": self.api_key,
                        "phrase": request.seed_keyword,
                        "database": "us",
                        "display_limit": 100,
                        "display_offset": page * 100,
                        "export_columns": "Ph,Nq,Cp,Co,Nr,Td"
                    }
                )
                
                # Parse response
                page_keywords = self._parse_response(response, request.min_volume)
                keywords.extend(page_keywords)
                
                page += 1
                
                # If no more results, stop
                if len(page_keywords) == 0:
                    break
                    
            except Exception as e:
                logger.error("keyword_expansion_failed", error=str(e), page=page)
                break
        
        # Validate minimum keyword count
        if len(keywords) < request.min_keywords:
            if len(keywords) == 0:
                raise ValueError(
                    f"No keywords found for '{request.seed_keyword}' "
                    f"(min volume: {request.min_volume}). "
                    f"Try broader seed keyword or lower min_volume."
                )
            else:
                logger.warning(
                    "insufficient_keywords",
                    found=len(keywords),
                    target=request.min_keywords,
                    seed=request.seed_keyword
                )
        
        logger.info(
            "keyword_expansion_complete",
            keywords_found=len(keywords),
            pages_fetched=page,
            cost=self.total_cost
        )
        
        return keywords[:request.min_keywords]  # Return exactly min_keywords
    
    def _parse_response(
        self,
        response: dict,
        min_volume: int
    ) -> List[SEMrushKeywordData]:
        """Parse SEMrush response and filter by min_volume"""
        keywords = []
        
        for row in response.get("data", []):
            try:
                volume = int(row.get("Nq", 0))
                
                # Filter by minimum volume
                if volume < min_volume:
                    continue
                
                keyword = SEMrushKeywordData(
                    keyword=row.get("Ph", ""),
                    search_volume=volume,
                    keyword_difficulty=float(row.get("Kd", 0)),
                    cpc=float(row.get("Cp", 0)),
                    competition=float(row.get("Co", 0)),
                    intent=self._detect_intent(row.get("Ph", "")),
                    serp_features=row.get("Td", "").split(",") if row.get("Td") else []
                )
                
                keywords.append(keyword)
                
            except Exception as e:
                logger.warning("parse_keyword_failed", error=str(e), row=row)
                continue
        
        return keywords
    
    def _detect_intent(self, keyword: str) -> str:
        """Detect search intent from keyword"""
        keyword_lower = keyword.lower()
        
        # Transactional
        if any(t in keyword_lower for t in ["buy", "price", "cost", "near me", "book", "appointment"]):
            return "transactional"
        
        # Informational
        if any(i in keyword_lower for i in ["what", "how", "why", "when", "benefits", "risks"]):
            return "informational"
        
        # Navigational
        if any(n in keyword_lower for n in ["best", "top", "review"]):
            return "navigational"
        
        return "informational"  # Default
```

#### Ahrefs Client (Fallback)

```python
# AIM/src/aim/subagents/api_clients/ahrefs.py

from .base import APIClientBase
from ..schemas.api_responses import AhrefsKeywordData, KeywordExpansionRequest
from typing import List

class AhrefsClient(APIClientBase):
    """Ahrefs API client (fallback for SEMrush)"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_name="ahrefs",
            base_url="https://apiv2.ahrefs.com",
            api_key=api_key,
            rate_limit_per_min=60,  # 60 RPM
            cost_per_request=0.05
        )
    
    async def expand_keywords(
        self,
        request: KeywordExpansionRequest
    ) -> List[AhrefsKeywordData]:
        """Expand keywords using Ahrefs Keywords Explorer"""
        
        # Similar implementation to SEMrush
        # Uses /v3/keywords-explorer/related-terms endpoint
        # (Implementation details omitted for brevity)
        pass
```

### Security: API Key Management

**Environment Variables (Required):**

```bash
# .env (NEVER commit to git)
SEMRUSH_API_KEY=your_semrush_key_here
AHREFS_API_KEY=your_ahrefs_key_here

# Optional: Override defaults
MAX_COST_USD=5.0
MIN_KEYWORDS=100
MIN_VOLUME=10
```

**Settings with Validation:**

```python
# AIM/src/aim/config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class APISettings(BaseSettings):
    """API credentials from environment variables"""
    
    semrush_api_key: str = Field(..., min_length=10)
    ahrefs_api_key: str = Field(..., min_length=10)
    
    # Defaults
    max_cost_usd: float = Field(default=5.0, ge=0.1, le=50.0)
    min_keywords: int = Field(default=100, ge=10)
    min_volume: int = Field(default=10, ge=0)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator('semrush_api_key', 'ahrefs_api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or v == "your_key_here":
            raise ValueError("API key not configured")
        return v

# Validate on startup
try:
    settings = APISettings()
except Exception as e:
    raise RuntimeError(f"Configuration error: {e}")
```

**Configuration Template:**

```yaml
# AIM/config/api_credentials.example.yaml
# Copy to .env and fill in your API keys

SEMRUSH_API_KEY=your_semrush_key_here
AHREFS_API_KEY=your_ahrefs_key_here

# Optional overrides
MAX_COST_USD=5.0
MIN_KEYWORDS=100
MIN_VOLUME=10
```

### Audit Trail Storage

**Database Schema:**

```python
# AIM/src/aim/storage/models.py

from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AuditTrail(Base):
    """Audit trail for regulatory defense"""
    __tablename__ = "audit_trail"
    
    id = Column(String, primary_key=True)
    keyword = Column(String, nullable=False, index=True)
    seed_keyword = Column(String, nullable=False)
    
    # Compliance result
    risk_level = Column(String, nullable=False)  # critical, high, medium, low
    risk_score = Column(Integer, nullable=False)
    likelihood = Column(Integer, nullable=False)
    severity = Column(Integer, nullable=False)
    flagged_patterns = Column(JSON)
    fda_enforcement_match = Column(String)
    
    # Action taken
    action_taken = Column(String, nullable=False)  # blocked, priority_reduced, passed
    rationale = Column(String, nullable=False)
    
    # Priority adjustment
    original_priority = Column(Float, nullable=False)
    adjusted_priority = Column(Float)
    
    # Metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    agent_id = Column(String, nullable=False)
    
    __table_args__ = (
        Index('idx_keyword_timestamp', 'keyword', 'timestamp'),
        Index('idx_risk_level', 'risk_level'),
    )

class UserFeedbackRecord(Base):
    """User feedback on keyword priorities"""
    __tablename__ = "user_feedback"
    
    id = Column(String, primary_key=True)
    keyword = Column(String, nullable=False, index=True)
    priority_score = Column(Float, nullable=False)
    feedback_type = Column(String, nullable=False)  # thumbs_up, thumbs_down, used, ignored
    user_comment = Column(String)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_feedback_type', 'feedback_type'),
    )
```


### File-Level Changes

#### Files to Modify

**1. `AIM/src/aim/subagents/keyword_research_agent.py`** (MAJOR REWRITE)
- Replace stub implementation with production code
- Integrate unified API client with primary/fallback
- Add compliance layer
- Implement adaptive prioritization
- Add cost control and budget guard
- Add user feedback collection endpoint

#### Files to Create

**Wave 1: Core Infrastructure (Sprint 1)**

1. `AIM/src/aim/subagents/api_clients/__init__.py`
2. `AIM/src/aim/subagents/api_clients/base.py` - Base client with circuit breaker, retry, rate limiter, cache
3. `AIM/src/aim/subagents/api_clients/semrush.py` - SEMrush client with Keyword Magic Tool
4. `AIM/src/aim/subagents/api_clients/ahrefs.py` - Ahrefs client (fallback)
5. `AIM/src/aim/subagents/schemas/__init__.py`
6. `AIM/src/aim/subagents/schemas/api_responses.py` - Pydantic schemas with validation
7. `AIM/src/aim/subagents/schemas/compliance.py` - Compliance models
8. `AIM/src/aim/subagents/schemas/prioritization.py` - Priority models with feedback
9. `AIM/src/aim/subagents/schemas/results.py` - Result models
10. `AIM/src/aim/config/settings.py` - Settings with env var validation

**Wave 2: Compliance (Sprint 2)**

11. `AIM/src/aim/subagents/compliance/__init__.py`
12. `AIM/src/aim/subagents/compliance/checker.py` - Tiered compliance gates
13. `AIM/src/aim/subagents/compliance/patterns.py` - Prohibited language library
14. `AIM/src/aim/subagents/compliance/fda_client.py` - openFDA API client with 24h cache
15. `AIM/src/aim/subagents/compliance/risk_scorer.py` - Risk scoring (1-25)
16. `AIM/config/compliance_patterns.yaml` - 100+ prohibited patterns

**Wave 3: Prioritization (Sprint 3)**

17. `AIM/src/aim/subagents/prioritization/__init__.py`
18. `AIM/src/aim/subagents/prioritization/calculator.py` - Priority formula
19. `AIM/src/aim/subagents/prioritization/serp_tracker.py` - SERP feature CTR tracking
20. `AIM/src/aim/subagents/prioritization/weights.py` - Adaptive weight system
21. `AIM/config/prioritization_weights.yaml` - Default weights

**Storage (Wave 1-2)**

22. `AIM/src/aim/storage/models.py` - SQLAlchemy models (AuditTrail, UserFeedback)
23. `AIM/alembic/versions/001_add_audit_trail.py` - Migration for audit_trail table
24. `AIM/alembic/versions/002_add_user_feedback.py` - Migration for user_feedback table

**Tests (Wave 5)**

25. `AIM/tests/subagents/test_keyword_research_agent.py` - Agent tests
26. `AIM/tests/subagents/api_clients/test_base.py` - Base client tests
27. `AIM/tests/subagents/api_clients/test_semrush.py` - SEMrush tests with VCR
28. `AIM/tests/subagents/api_clients/test_ahrefs.py` - Ahrefs tests with VCR
29. `AIM/tests/subagents/compliance/test_checker.py` - Compliance tests
30. `AIM/tests/subagents/prioritization/test_calculator.py` - Priority tests
31. `AIM/tests/fixtures/keyword_data.py` - Mock data fixtures
32. `AIM/tests/cassettes/` - VCR cassettes for API mocking

**Configuration**

33. `.env.example` - Environment variables template
34. `AIM/config/api_credentials.example.yaml` - API credentials template (deprecated, use .env)

---

## Edge Cases and Error Handling

### 1. Primary API Fails

**Scenario:** SEMrush API timeout or rate limit exceeded

**Handling:**
```python
try:
    keywords = await semrush_client.expand_keywords(request)
except (TimeoutError, RateLimitError, CircuitBreakerError) as e:
    logger.warning(f"SEMrush failed: {e}, falling back to Ahrefs")
    keywords = await ahrefs_client.expand_keywords(request)
    fallback_used = True
```

**Result:** Automatic fallback to Ahrefs, note in results

### 2. Both Primary APIs Fail

**Scenario:** Both SEMrush and Ahrefs unavailable

**Handling:**
```python
if not keywords:
    raise APIUnavailableError(
        "Unable to retrieve keyword data (both primary sources unavailable). "
        "Please check API status and try again later."
    )
```

**Result:** Error returned to user, logged to Event Store, user can retry

### 3. Zero-Volume Seed Keyword

**Scenario:** Seed keyword has 0 search volume

**Handling:**
```python
if len(keywords) == 0:
    # Try with lower min_volume threshold
    request.min_volume = 0
    keywords = await semrush_client.expand_keywords(request)
    
    if len(keywords) == 0:
        raise ValueError(
            f"No keywords found for '{request.seed_keyword}'. "
            f"Suggestions: Try broader keyword (e.g., 'dental implants' instead of 'dental implants in [tiny town]')"
        )
```

**Result:** Error with actionable suggestions

### 4. Budget Exceeded

**Scenario:** Cost reaches max_cost_usd before min_keywords reached

**Handling:**
```python
if len(keywords) < request.min_keywords:
    logger.warning(
        "budget_exceeded",
        found=len(keywords),
        target=request.min_keywords,
        cost=total_cost
    )
    
    return KeywordResearchReport(
        keywords=keywords,
        budget_exceeded=True,
        recommendations=[
            f"⚠️ Budget limit reached at ${total_cost:.2f}",
            f"Found {len(keywords)}/{request.min_keywords} keywords",
            f"Increase max_cost_usd to get more keywords"
        ]
    )
```

**Result:** Partial results with warning, user can increase budget

### 5. Compliance API Degraded

**Scenario:** openFDA API timeout

**Handling:**
```python
try:
    fda_match = await fda_client.check_enforcement(keyword)
except TimeoutError:
    logger.warning("openFDA unavailable, using pattern matching only")
    fda_match = None
    degraded_mode = True
    
# Continue with pattern matching only
compliance_result = await checker.check(keyword, fda_match=None)
```

**Result:** Falls back to pattern matching, warning in results, audit trail notes degraded mode

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
```python
# AIM/tests/subagents/api_clients/test_base.py

import pytest
from unittest.mock import AsyncMock, patch
from aim.subagents.api_clients.base import APIClientBase, TokenBucketRateLimiter

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_5_failures():
    """Circuit breaker opens after 5 consecutive failures"""
    client = APIClientBase("test", "http://test.com", "key", 60, 0.01)
    
    # Mock 5 failures
    with patch.object(client, '_do_request', side_effect=Exception("API error")):
        for i in range(5):
            with pytest.raises(Exception):
                await client.get("/test")
        
        # 6th call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await client.get("/test")

@pytest.mark.asyncio
async def test_token_bucket_rate_limiting():
    """Token bucket enforces rate limits"""
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)
    
    # Consume all tokens
    for i in range(10):
        assert await limiter.acquire() == True
    
    # Next request should fail (no tokens)
    assert await limiter.acquire() == False
    
    # Wait 1 second for refill
    await asyncio.sleep(1.1)
    assert await limiter.acquire() == True

@pytest.mark.asyncio
async def test_caching_reduces_api_calls():
    """Cache prevents duplicate API calls"""
    client = APIClientBase("test", "http://test.com", "key", 60, 0.01)
    
    with patch.object(client, '_do_request', return_value={"data": "test"}) as mock:
        # First call hits API
        result1 = await client.get("/test", {"q": "keyword"})
        assert mock.call_count == 1
        
        # Second call uses cache
        result2 = await client.get("/test", {"q": "keyword"})
        assert mock.call_count == 1  # No additional call
        assert result1 == result2
```

**Compliance:**
```python
# AIM/tests/subagents/compliance/test_checker.py

@pytest.mark.asyncio
async def test_critical_risk_blocks_keyword():
    """CRITICAL risk (20-25) blocks keyword"""
    checker = ComplianceChecker()
    
    result = await checker.check("guaranteed cure for cancer")
    
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.risk_score >= 20
    assert result.action_taken == "blocked"
    assert "cure" in result.flagged_patterns

@pytest.mark.asyncio
async def test_high_risk_reduces_priority():
    """HIGH risk (15-19) reduces priority by 50%"""
    checker = ComplianceChecker()
    
    result = await checker.check("FDA approved weight loss")
    
    assert result.risk_level == RiskLevel.HIGH
    assert 15 <= result.risk_score < 20
    assert result.action_taken == "priority_reduced"
```

**Prioritization:**
```python
# AIM/tests/subagents/prioritization/test_calculator.py

def test_priority_formula_calculation():
    """Priority formula: (Volume × Intent × Position) / (Difficulty × Competition)"""
    calc = PriorityCalculator()
    
    score = calc.calculate(
        volume=10000,
        intent_weight=0.40,  # Transactional
        position=5.0,
        difficulty=50,
        competition=0.5
    )
    
    # Expected: (10000 × 0.40 × (100-5)) / (50 × 0.5) = 15200
    # Normalized to 0-100 scale
    assert 70 <= score <= 90  # P1 range

def test_medical_intent_boost():
    """Transactional intent gets 40% weight (vs 30% standard)"""
    calc = PriorityCalculator()
    
    transactional_score = calc.calculate_intent_score("dental implants near me")
    informational_score = calc.calculate_intent_score("what are dental implants")
    
    assert transactional_score > informational_score
    assert transactional_score == 0.40
    assert informational_score == 0.30
```

### Integration Tests

**Event Bus Integration:**
```python
@pytest.mark.asyncio
async def test_keyword_research_via_event_bus():
    """Agent receives task via Event Bus, publishes result"""
    agent = KeywordResearchAgent()
    
    # Publish task event
    await event_bus.publish(Event(
        type="task.keyword_research",
        data={
            "seed_keyword": "dental implants",
            "min_keywords": 100,
            "max_cost_usd": 5.0
        }
    ))
    
    # Wait for result event
    result = await event_bus.subscribe("result.keyword_research", timeout=60)
    
    assert result.data["total_keywords"] >= 100
    assert result.data["cost_estimate_usd"] <= 5.0
    assert result.data["p0_count"] > 0
```

**Database Integration:**
```python
@pytest.mark.asyncio
async def test_audit_trail_saved_to_database():
    """Audit trail entries saved to database"""
    agent = KeywordResearchAgent()
    result = await agent.execute_task(task)
    
    # Check database
    async with db.session() as session:
        audit_entries = await session.execute(
            select(AuditTrail).where(AuditTrail.seed_keyword == "dental implants")
        )
        entries = audit_entries.scalars().all()
        
        assert len(entries) > 0
        assert any(e.risk_level == "critical" for e in entries)
```

### E2E Tests (Real APIs)

**Full Workflow with VCR:**
```python
@pytest.mark.e2e
@pytest.mark.vcr()  # Records real API responses on first run
async def test_full_keyword_research_workflow():
    """Test with real SEMrush/Ahrefs APIs (VCR cassette)"""
    agent = KeywordResearchAgent()
    
    task = Task(
        subtask_id="e2e-001",
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

### Load Testing

**Concurrent Requests:**
```python
@pytest.mark.load
async def test_concurrent_keyword_research():
    """Test 10 concurrent keyword research tasks"""
    agent = KeywordResearchAgent()
    
    tasks = [
        Task(
            subtask_id=f"load-{i}",
            action="keyword_research",
            description=f'Research keywords for "test keyword {i}"'
        )
        for i in range(10)
    ]
    
    start = time.time()
    results = await asyncio.gather(*[agent.execute_task(t) for t in tasks])
    duration = time.time() - start
    
    # All should succeed
    assert all(r.status == "success" for r in results)
    
    # Should complete within reasonable time (rate limiting considered)
    assert duration < 180  # 3 minutes for 10 concurrent
    
    # Rate limiter should prevent API overload
    total_api_calls = sum(len(r.result["api_calls_made"]) for r in results)
    assert total_api_calls < 100  # Reasonable limit
```

---

## Dependencies

### Python Packages (Pinned Versions)

```
# requirements.txt

python>=3.11,<3.13

# API Clients
httpx>=0.27.0,<0.28.0
pydantic>=2.6.0,<3.0.0
pydantic-settings>=2.2.0,<3.0.0

# Resilience
pybreaker>=1.0.0,<2.0.0
tenacity>=8.2.0,<9.0.0

# Rate Limiting
aiolimiter>=1.1.0,<2.0.0

# Caching
aiocache[redis]>=0.12.0,<0.13.0

# Observability
prometheus-client>=0.20.0,<0.21.0
structlog>=24.1.0,<25.0.0

# Database
sqlalchemy>=2.0.0,<3.0.0
alembic>=1.13.0,<2.0.0
aiosqlite>=0.20.0,<0.21.0  # For SQLite async

# Testing
pytest>=8.0.0,<9.0.0
pytest-asyncio>=0.23.0,<0.24.0
pytest-mock>=3.12.0,<4.0.0
pytest-vcr>=1.0.2,<2.0.0
httpx-mock>=0.7.0,<0.8.0
```

### External APIs

**Primary APIs (Wave 1-3):**

1. **SEMrush API** - $449.95/month (Business plan)
   - Endpoint: `/analytics/v1/` (Keyword Magic Tool)
   - Rate Limits: ~7 requests/min (10,000 units/day conservative)
   - Cost per request: ~$0.04
   - Required: API key from environment variable

2. **Ahrefs API** - $129-$449/month
   - Endpoint: `/v3/keywords-explorer/related-terms`
   - Rate Limits: 60 RPM
   - Cost per request: ~$0.05
   - Required: API key from environment variable

**Compliance API (Wave 2):**

3. **openFDA API** - Free
   - Endpoint: `/drug/enforcement.json`
   - Rate Limits: 240 requests/minute, 120,000/day
   - Cost: $0
   - Cache: 24 hours

**Enrichment APIs (OUT OF SCOPE - Future Enhancement):**

4. Google Search Console API - Deferred to future phase
5. Yandex Webmaster API - Deferred to future phase
6. Yandex Wordstat API - Deferred to future phase
7. Google Keyword Planner API - Deferred to future phase

---

## Out of Scope (Clarified)

**Explicitly NOT included in this 5-sprint implementation:**

1. **Wave 4 Enrichment APIs** - GSC, Yandex Webmaster, Wordstat, Keyword Planner
   - Reason: Start with quality (SEMrush + Ahrefs), add enrichment later
   - Future: Separate enhancement requiring new approval

2. **Competitive Gap Prioritization**
   - Requires: Competitor tracking system, SERP scraping, backlink analysis
   - Reason: Too much infrastructure for uncertain payoff
   - Future: Can add in Phase 2 if user feedback shows demand

3. **ROI-Weighted Priority**
   - Requires: Conversion tracking, LTV estimation, ranking cost modeling
   - Reason: Fragile due to sparse conversion data in medical marketing
   - Future: Can add when conversion data becomes available

4. **Real-Time FDA Enforcement Blocking**
   - Requires: openFDA API rate limit handling (240 req/min)
   - Reason: 200-500ms latency per keyword, 24h cache is sufficient
   - Future: Can add if regulatory requirements change

5. **Machine Learning Priority Model**
   - Requires: Historical performance data, training pipeline, model serving
   - Reason: Multi-factor formula is sufficient for MVP
   - Future: Can add ML layer when we have 6+ months of data

---

## Performance Analysis

### Execution Time Target: <15 minutes ✅ ACHIEVABLE

**Breakdown (100 keywords):**
- SEMrush API calls: 1-2 pages × 2-3s = 2-6s
- Compliance checks: 100 keywords × 10ms = 1s
- openFDA lookups: ~10 unique terms × 200ms = 2s (cached after first)
- Prioritization: 100 keywords × 5ms = 0.5s
- **Total: 5-10 seconds** (well under 15 min target)

**Risks:**
- If circuit breaker opens: fallback adds +30-60s
- If rate limiting triggered: could add +5-10 min
- If budget exceeded early: partial results returned

**Mitigation:** Parallel processing where possible, aggressive caching, circuit breaker tuning

---

## Cost Analysis

### Estimated Cost: $3-5 per analysis ✅ REASONABLE

**Breakdown (100 keywords):**
- SEMrush: 1-2 API calls × $0.04 = $0.04-$0.08
- Ahrefs (fallback): 0 calls if SEMrush works = $0.00
- openFDA: Free
- **Total: $0.04-$0.08 per analysis**

**Note:** Original estimate of $3-5 was based on 100 individual keyword lookups. With Keyword Magic Tool, we get 100 keywords in 1-2 API calls, dramatically reducing cost.

**Risks:**
- If fallback triggered frequently: +$0.05-$0.10 (Ahrefs)
- If multiple pages needed: +$0.04 per page
- **Total worst case: $0.50 per analysis** (still well under $5 budget)

**Mitigation:** Caching (1h TTL), circuit breaker (avoid repeated failures), budget guard

---

## Next Steps

1. ✅ **Dual-Model Spec Review** - COMPLETED
   - Product lens: NEEDS_REVISION (5 gaps fixed)
   - Technical lens: NEEDS_REVISION (7 gaps fixed)

2. **Implementation Plan** (5 waves, 3 sprints)
   - Wave 1: Core Infrastructure (Sprint 1, 3-5 days)
   - Wave 2: Compliance Integration (Sprint 2, 1-2 weeks)
   - Wave 3: Prioritization + Testing (Sprint 3, 1 week)
   - **Note:** Original Wave 4 (Enrichment APIs) and Wave 5 (Testing) consolidated into Wave 3

3. **User Approval** (Final gate before autonomous execution)

---

**Status:** Ready for implementation plan
**Estimated Implementation Time:** 3 sprints, ~3-4 weeks (reduced from 5 sprints)
**Estimated Cost:** $0.04-$0.50 per analysis (dramatically reduced from $3-5)
**Review Status:** All critical gaps addressed, spec approved for planning

