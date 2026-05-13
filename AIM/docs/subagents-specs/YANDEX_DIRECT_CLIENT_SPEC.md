# Yandex Direct API Client Specification

**Version:** 1.0.0  
**Created:** 2026-05-14  
**Parent Magister:** Ads Magister  
**Priority:** P0 (Critical)  
**Status:** Draft

---

## 1. Overview

### 1.1 Purpose

Production-ready Python client for Yandex Direct API v5 with unified interface matching Google Ads Client, enabling seamless multi-platform campaign management through the Services Layer.

**Key Capabilities:**
- Campaign CRUD operations (create, read, update, delete)
- Ad group and ad management
- Keyword and bid management
- Performance metrics collection
- Medical advertising compliance validation
- Resilience patterns for production reliability

### 1.2 Role in System

```
Ads Magister
  ↓
Services Layer (CampaignService, ContentOptimizer, AnalyticsService)
  ↓
Platform Clients Layer
  ├─ Google Ads Client (existing)
  └─ Yandex Direct Client (this spec) ← NEW
```

**Integration Points:**
- **Ads Magister:** Receives campaign parameters, returns results
- **Services Layer:** Unified interface for multi-platform operations
- **Analytics Magister:** Provides performance metrics
- **Content Magister:** Receives ad copy for campaigns

### 1.3 Success Metrics

**Performance:**
- API response time: p95 < 2s, p99 < 5s
- Concurrent connections: ≤ 5 (prevent error 506)
- Daily points usage: < 100,000 (prevent error 152)
- API call reduction: 80-90% via Changes service

**Reliability:**
- Circuit breaker: opens after 5 failures, resets after 60s
- Retry strategy: exponential backoff 1s → 30s max
- Zero retries on error 152 (rate limit)
- Uptime: 99.9% (excluding Yandex API downtime)

**Compliance:**
- Medical ads: 100% have required disclaimer
- Prohibited phrases: 0 in production
- License validation: 100% before campaign creation

**Interface:**
- Method signature match: 100% with Google Ads Client
- Response format: unified across platforms
- Services Layer integration: seamless

### 1.4 Critical Findings from Research

**1. Rate Limits Corrected (CRITICAL):**
- ❌ Initial assumption: "10 requests/second"
- ✅ Actual limit: **5 concurrent connections** + 100,000 points/day
- **Impact:** Requires connection pooling, NOT rate limiting

**2. Production Code Gap:**
- Reference implementation: yandex-ads-mcp (1,871 lines, 120 tools)
- ✅ Excellent for: API structure, OAuth flow, agency accounts
- ❌ Missing: circuit breaker, exponential backoff, rate limit detection, Changes service
- **Solution:** Use yandex-ads-mcp for API structure + add resilience patterns

**3. Medical Compliance:**
- Federal Law 38-FZ Article 24 mandates specific disclaimers
- Prohibited: testimonials, guarantees, targeting minors
- Required: license number, issuing authority, issue date
- **Solution:** MedicalAdValidator class with automated checks

**4. Changes Service Optimization:**
- Official recommendation: use Changes service to reduce API calls by 80-90%
- NOT implemented in yandex-ads-mcp
- **Solution:** Mandatory for monitoring and polling operations

---

## 2. Input Data

### 2.1 Campaign Parameters

**From Ads Magister:**

```python
@dataclass
class CampaignCreateRequest:
    """Campaign creation parameters."""
    
    # Basic info
    name: str                           # Campaign name
    start_date: date                    # Start date (YYYY-MM-DD)
    end_date: date | None = None        # Optional end date
    
    # Budget
    daily_budget_rubles: float          # Daily budget in RUB
    budget_mode: Literal["STANDARD", "DISTRIBUTED"] = "DISTRIBUTED"
    
    # Targeting
    region_ids: list[int]               # Geographic targeting (213=Moscow, 2=SPb, 225=Russia)
    
    # Strategy
    bidding_strategy: BiddingStrategy   # See section 2.2
    
    # Medical compliance (if applicable)
    medical_license: MedicalLicense | None = None
    
    # Tracking
    metrica_counter_id: int | None = None
```

**Example:**
```python
request = CampaignCreateRequest(
    name="Dental Implants Moscow Summer 2026",
    start_date=date(2026, 6, 1),
    daily_budget_rubles=500.0,
    budget_mode="DISTRIBUTED",
    region_ids=[213],  # Moscow
    bidding_strategy=BiddingStrategy(
        type="WB_MAXIMUM_CLICKS",
        weekly_spend_limit_rubles=3500.0
    ),
    medical_license=MedicalLicense(
        number="ЛО-77-01-012345",
        issuing_authority="Росздравнадзор",
        issue_date=date(2024, 1, 15)
    )
)
```

### 2.2 Bidding Strategies

**8 strategies supported:**

```python
@dataclass
class BiddingStrategy:
    """Bidding strategy configuration."""
    
    type: Literal[
        "WB_MAXIMUM_CLICKS",              # Weekly Budget, Maximize Clicks
        "PAY_FOR_CONVERSION",             # CPA Optimization
        "PAY_FOR_CONVERSION_MULTIPLE_GOALS",  # Multi-Goal Optimization
        "WB_MAXIMUM_CONVERSION_RATE",     # Maximize Conversion Rate
        "AVERAGE_CPA",                    # Target CPA Bidding
        "AVERAGE_CPC",                    # Target CPC Bidding
        "HIGHEST_POSITION",               # Premium Placement
        "SERVING_OFF"                     # Manual Bidding Only
    ]
    
    # Strategy-specific parameters
    weekly_spend_limit_rubles: float | None = None
    goal_id: int | None = None
    goal_cpa_rubles: float | None = None
    average_cpa_rubles: float | None = None
```

**Strategy Selection Guide:**

| Strategy | Use Case | Required Parameters |
|----------|----------|---------------------|
| WB_MAXIMUM_CLICKS | Brand awareness, traffic | weekly_spend_limit |
| PAY_FOR_CONVERSION | Lead generation | goal_id, goal_cpa, weekly_spend_limit |
| AVERAGE_CPA | Maintain specific CPA | goal_id, average_cpa, weekly_spend_limit |
| HIGHEST_POSITION | Maximum visibility | None (uses manual bids) |

### 2.3 Ad Copy and Creatives

**From Content Magister:**

```python
@dataclass
class AdCreateRequest:
    """Ad creation parameters."""
    
    # Ad copy
    title: str                          # Max 35 characters
    title2: str | None = None           # Optional second title
    text: str                           # Max 81 characters
    
    # URLs
    href: str                           # Landing page URL
    display_url_path: str | None = None # Display URL path
    
    # Extensions
    sitelinks: list[Sitelink] | None = None
    callouts: list[str] | None = None
    
    # Mobile
    mobile_href: str | None = None      # Mobile-specific URL
    
    # Tracking
    tracking_params: dict[str, str] | None = None
```

**Medical Compliance Check:**
```python
@dataclass
class MedicalAdValidationResult:
    """Medical ad validation result."""
    
    is_valid: bool
    violations: list[str]
    required_disclaimer_present: bool
    prohibited_phrases_found: list[str]
```

### 2.4 Keywords and Bids

```python
@dataclass
class KeywordCreateRequest:
    """Keyword creation parameters."""
    
    keyword: str                        # Keyword text
    bid_micros: int                     # Bid in micros (1 RUB = 1,000,000 micros)
    
    # Negative keywords
    negative_keywords: list[str] | None = None
```

### 2.5 Medical License Information

```python
@dataclass
class MedicalLicense:
    """Medical license information for compliance."""
    
    number: str                         # License number (e.g., "ЛО-77-01-012345")
    issuing_authority: str              # Issuing authority (e.g., "Росздравнадзор")
    issue_date: date                    # Issue date
    expiry_date: date | None = None     # Optional expiry date
    
    def is_valid(self) -> bool:
        """Check if license is currently valid."""
        if self.expiry_date is None:
            return True
        return date.today() <= self.expiry_date
```

---

## 3. Algorithm and Logic

### 3.1 Architecture Overview

```
YandexDirectClient
  ├─ ConnectionPool (max 5 connections)
  ├─ CircuitBreaker (fail_max=5, reset_timeout=60s)
  ├─ RetryHandler (exponential backoff 1s → 30s)
  ├─ RateLimitDetector (error 152, 506, 1002)
  ├─ PointsBudgetTracker (100k/day)
  ├─ ChangesServiceOptimizer (80-90% API call reduction)
  ├─ MedicalAdValidator (compliance checks)
  └─ UnifiedInterfaceMapper (Google Ads ↔ Yandex Direct)
```

### 3.2 Core Workflow: Campaign Creation

**Step-by-step process:**

```python
async def create_campaign(self, request: CampaignCreateRequest) -> CampaignCreateResult:
    """
    Create Yandex Direct campaign with full resilience and compliance.
    
    Steps:
    1. Validate medical compliance (if applicable)
    2. Check points budget availability
    3. Convert parameters to Yandex format
    4. Make API call with circuit breaker + retry
    5. Handle errors gracefully
    6. Map response to unified format
    7. Return result
    """
    
    # Step 1: Medical compliance validation
    if request.medical_license:
        validation = await self.medical_validator.validate_campaign(request)
        if not validation.is_valid:
            raise MedicalComplianceError(validation.violations)
    
    # Step 2: Check points budget
    if not self.points_tracker.can_make_request(estimated_points=10):
        raise PointsBudgetExceededError("Daily points limit reached")
    
    # Step 3: Convert to Yandex format
    yandex_params = self._map_to_yandex_format(request)
    
    # Step 4: Make API call with resilience
    try:
        response = await self._api_call_with_resilience(
            service="campaigns",
            method="add",
            params=yandex_params
        )
    except RateLimitError as e:
        # Error 152 - DO NOT RETRY
        raise
    except CircuitBreakerError as e:
        # Circuit breaker open - fail fast
        raise
    
    # Step 5: Record points usage
    self.points_tracker.record_request(points_used=10)
    
    # Step 6: Map response to unified format
    result = self._map_to_unified_format(response)
    
    return result
```

### 3.3 Resilience Patterns

**3.3.1 Connection Pooling**

```python
import httpx

class YandexDirectClient:
    def __init__(self, oauth_token: str):
        # Max 5 concurrent connections (Yandex limit)
        limits = httpx.Limits(
            max_connections=5,
            max_keepalive_connections=5
        )
        
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=120.0
        )
```

**Why:** Prevents error 506 (too many concurrent connections)

**3.3.2 Circuit Breaker**

```python
from pybreaker import CircuitBreaker

class YandexDirectClient:
    def __init__(self, oauth_token: str):
        # Open after 5 failures, reset after 60s
        self.breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60
        )
    
    @breaker
    async def _api_call(self, service: str, method: str, params: dict):
        # API call implementation
        pass
```

**States:**
- **CLOSED:** Normal operation, requests pass through
- **OPEN:** After 5 failures, all requests fail immediately (fail fast)
- **HALF_OPEN:** After 60s, allow one test request

**Why:** Prevents cascading failures, gives API time to recover

**3.3.3 Exponential Backoff**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class YandexDirectClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry_if_exception_type=httpx.NetworkError
    )
    async def _api_call_with_retry(self, service: str, method: str, params: dict):
        # API call implementation
        pass
```

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: Wait 1s
- Attempt 3: Wait 2s
- Max wait: 30s

**CRITICAL:** Only retry on network errors, NEVER on API errors (especially error 152)

**3.3.4 Rate Limit Detection**

```python
class YandexDirectClient:
    async def _api_call(self, service: str, method: str, params: dict):
        resp = await self.client.post(url, headers=headers, json=body)
        data = resp.json()
        
        if "error" in data:
            error_code = data["error"].get("error_code")
            
            if error_code == 152:
                # Not enough points - DO NOT RETRY (costs 20 points)
                raise RateLimitError("Daily points limit reached")
            
            elif error_code == 506:
                # Too many connections - reduce connection pool
                raise ConnectionError("Concurrent connection limit exceeded")
            
            elif error_code == 1002:
                # Invalid token - refresh OAuth
                raise AuthenticationError("OAuth token invalid or expired")
            
            else:
                raise APIError(f"API error {error_code}: {data['error'].get('error_string')}")
        
        return data
```

**Error Handling Matrix:**

| Error Code | Description | Action | Retry? |
|------------|-------------|--------|--------|
| 152 | Not enough points | Wait until next day | ❌ NO (costs 20 points) |
| 506 | Too many connections | Reduce connections | ❌ NO |
| 1002 | Invalid token | Refresh OAuth | ✅ YES (after refresh) |
| Network error | Transient failure | Exponential backoff | ✅ YES (max 3 attempts) |

### 3.4 Changes Service Optimization

**Problem:** Polling campaigns for updates is expensive (1 API call per campaign)

**Solution:** Use Changes service to check for modifications first

```python
async def get_campaigns_optimized(self, campaign_ids: list[int]) -> list[Campaign]:
    """
    Get campaigns with 80-90% API call reduction.
    
    Steps:
    1. Check Changes service for modified campaigns
    2. Only fetch campaigns that changed
    3. Return cached data for unchanged campaigns
    """
    
    # Step 1: Check for changes
    changes = await self._api_call(
        service="changes",
        method="checkCampaigns",
        params={"CampaignIds": campaign_ids}
    )
    
    # Step 2: Identify changed campaigns
    changed_ids = [
        c["CampaignId"] 
        for c in changes["result"]["Campaigns"]
        if c["Changed"]
    ]
    
    if not changed_ids:
        # No changes - return cached data
        return self._get_cached_campaigns(campaign_ids)
    
    # Step 3: Fetch only changed campaigns
    campaigns = await self._api_call(
        service="campaigns",
        method="get",
        params={
            "SelectionCriteria": {"Ids": changed_ids},
            "FieldNames": ["Id", "Name", "Status", "State", "Statistics"]
        }
    )
    
    # Step 4: Update cache
    self._update_cache(campaigns["result"]["Campaigns"])
    
    # Step 5: Return all campaigns (cached + fresh)
    return self._get_cached_campaigns(campaign_ids)
```

**Impact:** 80-90% reduction in API calls for monitoring operations

### 3.5 Medical Compliance Validation

```python
class MedicalAdValidator:
    """Validate medical advertising compliance (Federal Law 38-FZ Article 24)."""
    
    REQUIRED_DISCLAIMER = "Имеются противопоказания. Необходима консультация специалиста"
    
    PROHIBITED_PHRASES = [
        "гарантируем",           # guarantee
        "100% результат",        # 100% result
        "отзывы пациентов",      # patient reviews
        "лучше чем",             # better than
        "вылечим",               # will cure
        "избавим от",            # will get rid of
        "навсегда",              # forever
        "без боли",              # painless (if absolute)
        "быстро",                # quickly (if absolute)
        "дешево",                # cheap (if comparative)
        # ... 20 more phrases
    ]
    
    async def validate_ad_text(self, text: str) -> MedicalAdValidationResult:
        """
        Validate medical ad compliance.
        
        Checks:
        1. Required disclaimer present
        2. No prohibited phrases
        3. No targeting minors (checked via keywords)
        4. No patient testimonials
        """
        violations = []
        
        # Check 1: Required disclaimer
        disclaimer_present = self.REQUIRED_DISCLAIMER in text
        if not disclaimer_present:
            violations.append("Missing required disclaimer")
        
        # Check 2: Prohibited phrases
        text_lower = text.lower()
        found_phrases = []
        for phrase in self.PROHIBITED_PHRASES:
            if phrase in text_lower:
                found_phrases.append(phrase)
                violations.append(f"Prohibited phrase: {phrase}")
        
        return MedicalAdValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            required_disclaimer_present=disclaimer_present,
            prohibited_phrases_found=found_phrases
        )
    
    async def validate_campaign(self, request: CampaignCreateRequest) -> MedicalAdValidationResult:
        """Validate entire campaign for medical compliance."""
        
        # Check license validity
        if not request.medical_license.is_valid():
            return MedicalAdValidationResult(
                is_valid=False,
                violations=["Medical license expired"],
                required_disclaimer_present=False,
                prohibited_phrases_found=[]
            )
        
        # Additional checks...
        return MedicalAdValidationResult(is_valid=True, violations=[], required_disclaimer_present=True, prohibited_phrases_found=[])
```

### 3.6 Unified Interface Mapping

**Goal:** Match Google Ads Client interface for seamless Services Layer integration

```python
# Internal mapping: Yandex ↔ Google
STATUS_MAP = {
    # Yandex → Google
    "ACCEPTED": "ENABLED",
    "DRAFT": "PAUSED",
    "MODERATION": "PENDING",
    "SUSPENDED": "PAUSED",
    "ARCHIVED": "REMOVED",
    
    # Google → Yandex
    "ENABLED": "ACCEPTED",
    "PAUSED": "SUSPENDED",
    "REMOVED": "ARCHIVED",
}

CAMPAIGN_TYPE_MAP = {
    # Yandex → Google
    "TEXT_CAMPAIGN": "SEARCH",
    "UNIFIED_CAMPAIGN": "DISPLAY",
    "SMART_BANNER_CAMPAIGN": "SMART_DISPLAY",
    
    # Google → Yandex
    "SEARCH": "TEXT_CAMPAIGN",
    "DISPLAY": "UNIFIED_CAMPAIGN",
}

def _map_to_unified_format(self, yandex_response: dict) -> Campaign:
    """Map Yandex response to unified format."""
    
    campaign = yandex_response["Campaigns"][0]
    
    return Campaign(
        id=str(campaign["Id"]),
        name=campaign["Name"],
        status=STATUS_MAP.get(campaign["Status"], "UNKNOWN"),
        type=CAMPAIGN_TYPE_MAP.get(campaign["Type"], "UNKNOWN"),
        budget=self._convert_micros_to_usd(campaign["DailyBudget"]["Amount"]),
        currency="USD",  # Internal unified currency
        # ... more fields
    )
```

---

## 4. Output Data

### 4.1 Campaign Creation Result

```python
@dataclass
class CampaignCreateResult:
    """Campaign creation result in unified format."""
    
    # Campaign info
    campaign_id: str                    # Yandex campaign ID
    name: str                           # Campaign name
    status: CampaignStatus              # Unified status
    
    # Moderation
    moderation_status: ModerationStatus
    moderation_message: str | None = None
    
    # Tracking
    created_at: datetime
    points_used: int                    # API points consumed
    
    # Errors (if any)
    warnings: list[str] = field(default_factory=list)
```

**Example:**
```python
result = CampaignCreateResult(
    campaign_id="12345678",
    name="Dental Implants Moscow Summer 2026",
    status=CampaignStatus.PENDING_MODERATION,
    moderation_status=ModerationStatus.PENDING,
    created_at=datetime.now(),
    points_used=10,
    warnings=[]
)
```

### 4.2 Performance Metrics

```python
@dataclass
class CampaignMetrics:
    """Campaign performance metrics in unified format."""
    
    campaign_id: str
    date_range: DateRange
    
    # Traffic metrics
    impressions: int
    clicks: int
    ctr: float                          # Click-through rate (%)
    
    # Cost metrics
    cost_usd: float                     # Converted from RUB
    cpc_usd: float                      # Cost per click
    cpm_usd: float                      # Cost per 1000 impressions
    
    # Conversion metrics
    conversions: int
    conversion_rate: float              # Conversion rate (%)
    cpa_usd: float                      # Cost per acquisition
    
    # ROI metrics
    revenue_usd: float | None = None
    roas: float | None = None           # Return on ad spend
```

### 4.3 Error Reports

```python
@dataclass
class APIErrorReport:
    """Detailed API error report."""
    
    error_code: int                     # Yandex error code
    error_message: str                  # Error description
    error_detail: str | None = None     # Additional details
    
    # Context
    service: str                        # API service (e.g., "campaigns")
    method: str                         # API method (e.g., "add")
    request_params: dict                # Request parameters (sanitized)
    
    # Timing
    timestamp: datetime
    retry_count: int                    # Number of retries attempted
    
    # Resolution
    is_retryable: bool                  # Can this error be retried?
    recommended_action: str             # What to do next
```

---

## 5. Success Metrics and KPIs

### 5.1 Performance Metrics

**API Response Time:**
- p50: < 500ms
- p95: < 2s
- p99: < 5s

**Throughput:**
- Concurrent connections: ≤ 5 (hard limit)
- Requests per day: < 100,000 points
- API call reduction: 80-90% via Changes service

**Resource Usage:**
- Memory: < 512 MB per client instance
- CPU: < 10% average, < 50% peak

### 5.2 Reliability Metrics

**Circuit Breaker:**
- Failure threshold: 5 consecutive failures
- Reset timeout: 60 seconds
- Half-open test: 1 request

**Retry Strategy:**
- Max attempts: 3
- Backoff: exponential (1s → 2s → 4s, max 30s)
- Retry rate: < 5% of total requests

**Error Handling:**
- Error 152 retries: 0 (NEVER retry)
- Error 506 occurrences: < 1% of requests
- Token refresh success rate: > 99%

**Uptime:**
- Client availability: 99.9%
- Excluding Yandex API downtime

### 5.3 Compliance Metrics

**Medical Advertising:**
- Disclaimer presence: 100% of medical ads
- Prohibited phrases: 0 in production
- License validation: 100% before campaign creation
- Moderation rejection rate: < 5%

**Data Quality:**
- Response validation: 100% (Pydantic schemas)
- Currency conversion accuracy: 100%
- Status mapping accuracy: 100%

### 5.4 Business Metrics

**Cost Efficiency:**
- API calls saved: 80-90% via Changes service
- Points usage: < 80% of daily limit (buffer for spikes)
- Cost per campaign: < $0.01 (API is free, but points are limited)

**Campaign Performance:**
- Campaign creation success rate: > 95%
- Moderation approval rate: > 95% (for compliant ads)
- Time to first impression: < 24 hours (after moderation)

---

## 6. Communication Patterns

### 6.1 Event Bus Integration

**Events Published:**

```python
# Campaign lifecycle events
CampaignCreatedEvent(campaign_id, name, status, points_used)
CampaignUpdatedEvent(campaign_id, changes, points_used)
CampaignDeletedEvent(campaign_id, reason)

# Moderation events
ModerationPendingEvent(campaign_id, submitted_at)
ModerationApprovedEvent(campaign_id, approved_at)
ModerationRejectedEvent(campaign_id, reason, rejected_at)

# Performance events
MetricsCollectedEvent(campaign_id, metrics, date_range)
BudgetThresholdReachedEvent(campaign_id, spent_percentage)

# Error events
RateLimitReachedEvent(points_used, points_remaining, reset_time)
CircuitBreakerOpenedEvent(service, failure_count, reset_time)
APIErrorEvent(error_code, error_message, service, method)
```

**Events Subscribed:**

```python
# From Ads Magister
CreateCampaignRequestedEvent(request_params)
UpdateCampaignRequestedEvent(campaign_id, updates)
DeleteCampaignRequestedEvent(campaign_id)

# From Analytics Magister
MetricsRequestedEvent(campaign_ids, date_range)
PerformanceReportRequestedEvent(campaign_ids, metrics)

# From Content Magister
AdCopyGeneratedEvent(campaign_id, ad_copy)
```

### 6.2 API Communication

**Request Format:**

```python
# Yandex Direct API v5 uses JSON-RPC style
POST https://api.direct.yandex.com/json/v5/{service}

Headers:
  Authorization: Bearer {oauth_token}
  Accept-Language: ru
  Content-Type: application/json
  Client-Login: {client_login}  # For agency accounts

Body:
{
  "method": "add",
  "params": {
    "Campaigns": [...]
  }
}
```

**Response Format:**

```python
# Success
{
  "result": {
    "AddResults": [
      {"Id": 12345678}
    ]
  }
}

# Error
{
  "error": {
    "error_code": 152,
    "error_string": "Not enough points",
    "error_detail": "Daily limit reached"
  }
}
```

### 6.3 Logging and Monitoring

**Structured Logging (structlog):**

```python
logger.info(
    "campaign_created",
    campaign_id=campaign_id,
    name=name,
    status=status,
    points_used=points_used,
    duration_ms=duration_ms
)

logger.error(
    "api_error",
    error_code=error_code,
    error_message=error_message,
    service=service,
    method=method,
    retry_count=retry_count
)
```

**Prometheus Metrics:**

```python
# Counters
yandex_api_requests_total{service, method, status}
yandex_api_errors_total{error_code, service}
yandex_circuit_breaker_opens_total{service}

# Gauges
yandex_points_remaining
yandex_active_connections
yandex_circuit_breaker_state{service}  # 0=closed, 1=open, 2=half_open

# Histograms
yandex_api_request_duration_seconds{service, method}
yandex_retry_attempts{service, method}
```


---

## 7. Error Handling

### 7.1 Error Classification

**Critical Errors (Fail Fast):**
- Error 152: Not enough points → DO NOT RETRY (costs 20 points)
- Error 506: Too many connections → Reduce connection pool
- Error 1002: Invalid token → Refresh OAuth token
- Circuit breaker open → Fail immediately

**Retryable Errors (Exponential Backoff):**
- Network errors (connection timeout, DNS failure)
- HTTP 5xx errors (server errors)
- Transient API errors

**Non-Retryable Errors (Fail Immediately):**
- HTTP 4xx errors (client errors)
- Validation errors (invalid parameters)
- Medical compliance violations

### 7.2 Error Handling Matrix

| Error Type | Error Code | Action | Retry? | Backoff |
|------------|------------|--------|--------|---------|
| Rate limit | 152 | Wait until next day | ❌ NO | N/A |
| Too many connections | 506 | Reduce connections | ❌ NO | N/A |
| Invalid token | 1002 | Refresh OAuth | ✅ YES | Immediate |
| Network error | N/A | Exponential backoff | ✅ YES | 1s → 30s |
| Server error | 5xx | Exponential backoff | ✅ YES | 1s → 30s |
| Client error | 4xx | Fail immediately | ❌ NO | N/A |
| Validation error | N/A | Fail immediately | ❌ NO | N/A |

### 7.3 Error Recovery Strategies

**Strategy 1: Circuit Breaker Recovery**

```python
class CircuitBreakerRecovery:
    """Recover from circuit breaker open state."""
    
    async def recover(self):
        """
        Recovery steps:
        1. Wait for reset timeout (60s)
        2. Circuit breaker enters HALF_OPEN state
        3. Allow one test request
        4. If success → CLOSED, if failure → OPEN again
        """
        
        if self.breaker.current_state == "open":
            logger.warning(
                "circuit_breaker_open",
                service=self.service,
                reset_time=self.breaker.reset_time
            )
            
            # Wait for reset timeout
            await asyncio.sleep(60)
            
            # Test request will be attempted automatically
            # by circuit breaker in HALF_OPEN state
```

**Strategy 2: OAuth Token Refresh**

```python
class OAuthTokenRefresh:
    """Refresh OAuth token on error 1002."""
    
    async def refresh_token(self):
        """
        Refresh steps:
        1. Detect error 1002 (invalid token)
        2. Request new token from OAuth endpoint
        3. Update client with new token
        4. Retry original request
        """
        
        try:
            # Request new token
            new_token = await self._request_new_token()
            
            # Update client
            self.oauth_token = new_token
            self.client.headers["Authorization"] = f"Bearer {new_token}"
            
            logger.info("oauth_token_refreshed")
            
        except Exception as e:
            logger.error("oauth_token_refresh_failed", error=str(e))
            raise AuthenticationError("Failed to refresh OAuth token")
```

**Strategy 3: Points Budget Recovery**

```python
class PointsBudgetRecovery:
    """Recover from points budget exhaustion."""
    
    async def recover(self):
        """
        Recovery steps:
        1. Detect error 152 (not enough points)
        2. Calculate time until reset (next day)
        3. Pause all operations until reset
        4. Resume operations after reset
        """
        
        if self.points_tracker.used_points >= self.points_tracker.max_points:
            reset_time = self.points_tracker.reset_time
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            
            logger.warning(
                "points_budget_exhausted",
                used_points=self.points_tracker.used_points,
                max_points=self.points_tracker.max_points,
                reset_time=reset_time,
                wait_seconds=wait_seconds
            )
            
            # Pause operations
            await asyncio.sleep(wait_seconds)
            
            # Reset points tracker
            self.points_tracker.used_points = 0
            self.points_tracker.reset_time = datetime.now() + timedelta(days=1)
            
            logger.info("points_budget_reset")
```

### 7.4 Error Logging and Monitoring

**Structured Error Logging:**

```python
logger.error(
    "api_error",
    error_code=error_code,
    error_message=error_message,
    error_detail=error_detail,
    service=service,
    method=method,
    request_params=sanitized_params,  # Remove sensitive data
    retry_count=retry_count,
    is_retryable=is_retryable,
    recommended_action=recommended_action,
    timestamp=datetime.now().isoformat()
)
```

**Error Metrics:**

```python
# Prometheus counters
yandex_api_errors_total{error_code="152", service="campaigns"} 5
yandex_api_errors_total{error_code="506", service="campaigns"} 2
yandex_api_errors_total{error_code="1002", service="campaigns"} 1

# Error rate
yandex_api_error_rate{service="campaigns"} 0.05  # 5% error rate
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test Coverage:**
- Connection pooling: max 5 connections enforced
- Circuit breaker: opens after 5 failures, resets after 60s
- Exponential backoff: 1s → 2s → 4s → max 30s
- Rate limit detection: error 152, 506, 1002 handled correctly
- Medical compliance: disclaimer check, prohibited phrases detection
- Currency conversion: RUB ↔ USD accurate
- Status mapping: Yandex ↔ Google correct

**Example Test:**

```python
@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Circuit breaker should open after 5 consecutive failures."""
    
    client = YandexDirectClient(oauth_token="test_token")
    
    # Simulate 5 failures
    for i in range(5):
        with pytest.raises(APIError):
            await client._api_call("campaigns", "get", {})
    
    # Circuit breaker should be open
    assert client.breaker.current_state == "open"
    
    # Next request should fail immediately
    with pytest.raises(CircuitBreakerError):
        await client._api_call("campaigns", "get", {})
```

### 8.2 Integration Tests

**Test Scenarios:**
- Campaign CRUD operations in sandbox
- OAuth token refresh flow
- Medical compliance validation end-to-end
- Changes service optimization
- Error handling (152, 506, 1002)

**Example Test:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_campaign_in_sandbox():
    """Should create campaign in Yandex Direct sandbox."""
    
    client = YandexDirectClient(
        oauth_token=os.getenv("YANDEX_SANDBOX_TOKEN"),
        use_sandbox=True
    )
    
    request = CampaignCreateRequest(
        name="Test Campaign",
        start_date=date.today(),
        daily_budget_rubles=100.0,
        region_ids=[213],  # Moscow
        bidding_strategy=BiddingStrategy(
            type="WB_MAXIMUM_CLICKS",
            weekly_spend_limit_rubles=700.0
        )
    )
    
    result = await client.create_campaign(request)
    
    assert result.campaign_id is not None
    assert result.status == CampaignStatus.PENDING_MODERATION
    assert result.points_used > 0
```

### 8.3 Load Tests

**Test Scenarios:**
- Concurrent requests: verify max 5 connections enforced
- Points budget: verify 100k/day limit respected
- Circuit breaker: verify opens under load
- Changes service: verify API call reduction

**Example Test:**

```python
@pytest.mark.load
@pytest.mark.asyncio
async def test_concurrent_connections_limit():
    """Should enforce max 5 concurrent connections."""
    
    client = YandexDirectClient(oauth_token="test_token")
    
    # Attempt 10 concurrent requests
    tasks = [
        client.get_campaigns([i])
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Some requests should fail with ConnectionError (error 506)
    errors = [r for r in results if isinstance(r, ConnectionError)]
    assert len(errors) > 0
```

### 8.4 Medical Compliance Tests

**Test Scenarios:**
- Required disclaimer present
- Prohibited phrases detected
- License validation
- Age targeting restrictions

**Example Test:**

```python
@pytest.mark.asyncio
async def test_medical_ad_validation_missing_disclaimer():
    """Should reject medical ad without required disclaimer."""
    
    validator = MedicalAdValidator()
    
    ad_text = "Лечение зубов в Москве. Опытные врачи."
    
    result = await validator.validate_ad_text(ad_text)
    
    assert not result.is_valid
    assert "Missing required disclaimer" in result.violations
    assert not result.required_disclaimer_present
```

---

## 9. Usage Examples

### 9.1 Basic Campaign Creation

```python
from AIM.src.aim.subagents.yandex_direct_client import YandexDirectClient
from AIM.src.aim.subagents.schemas.campaign import CampaignCreateRequest, BiddingStrategy

# Initialize client
client = YandexDirectClient(
    oauth_token=os.getenv("YANDEX_DIRECT_TOKEN"),
    use_sandbox=False  # Production
)

# Create campaign
request = CampaignCreateRequest(
    name="Summer Sale 2026",
    start_date=date(2026, 6, 1),
    end_date=date(2026, 8, 31),
    daily_budget_rubles=500.0,
    budget_mode="DISTRIBUTED",
    region_ids=[213],  # Moscow
    bidding_strategy=BiddingStrategy(
        type="WB_MAXIMUM_CLICKS",
        weekly_spend_limit_rubles=3500.0
    )
)

result = await client.create_campaign(request)

print(f"Campaign created: {result.campaign_id}")
print(f"Status: {result.status}")
print(f"Points used: {result.points_used}")
```

### 9.2 Medical Campaign with Compliance

```python
from AIM.src.aim.subagents.schemas.medical import MedicalLicense

# Medical license
license = MedicalLicense(
    number="ЛО-77-01-012345",
    issuing_authority="Росздравнадзор",
    issue_date=date(2024, 1, 15)
)

# Create medical campaign
request = CampaignCreateRequest(
    name="Dental Implants Moscow",
    start_date=date.today(),
    daily_budget_rubles=1000.0,
    region_ids=[213],
    bidding_strategy=BiddingStrategy(
        type="HIGHEST_POSITION"
    ),
    medical_license=license  # Required for medical campaigns
)

# Validate compliance before creation
validator = MedicalAdValidator()
validation = await validator.validate_campaign(request)

if not validation.is_valid:
    print(f"Compliance violations: {validation.violations}")
    return

# Create campaign
result = await client.create_campaign(request)
print(f"Medical campaign created: {result.campaign_id}")
```

### 9.3 Optimized Campaign Monitoring

```python
# Get campaigns with Changes service optimization
campaign_ids = [12345678, 87654321, 11223344]

# First call: fetches all campaigns (3 API calls)
campaigns = await client.get_campaigns_optimized(campaign_ids)

# Subsequent calls: only fetches changed campaigns (1 API call + cache)
# 80-90% API call reduction
campaigns = await client.get_campaigns_optimized(campaign_ids)

for campaign in campaigns:
    print(f"{campaign.name}: {campaign.status}")
```

### 9.4 Performance Metrics Collection

```python
from datetime import date, timedelta

# Define date range
date_range = DateRange(
    start_date=date.today() - timedelta(days=7),
    end_date=date.today()
)

# Get metrics
metrics = await client.get_campaign_metrics(
    campaign_ids=[12345678],
    date_range=date_range
)

for metric in metrics:
    print(f"Campaign: {metric.campaign_id}")
    print(f"Impressions: {metric.impressions}")
    print(f"Clicks: {metric.clicks}")
    print(f"CTR: {metric.ctr:.2f}%")
    print(f"Cost: ${metric.cost_usd:.2f}")
    print(f"CPC: ${metric.cpc_usd:.2f}")
    print(f"Conversions: {metric.conversions}")
    print(f"CPA: ${metric.cpa_usd:.2f}")
```

### 9.5 Error Handling

```python
from AIM.src.aim.subagents.exceptions import (
    RateLimitError,
    CircuitBreakerError,
    MedicalComplianceError
)

try:
    result = await client.create_campaign(request)
    
except RateLimitError as e:
    # Error 152: Daily points limit reached
    print(f"Rate limit reached: {e}")
    print(f"Reset time: {client.points_tracker.reset_time}")
    # Wait until next day
    
except CircuitBreakerError as e:
    # Circuit breaker open
    print(f"Circuit breaker open: {e}")
    print("API is down, try again later")
    # Fail fast, don't retry
    
except MedicalComplianceError as e:
    # Medical compliance violation
    print(f"Compliance violation: {e.violations}")
    # Fix ad copy and retry
    
except APIError as e:
    # Other API errors
    print(f"API error {e.error_code}: {e.error_message}")
    # Handle based on error code
```

---

## 10. Dependencies and Integration

### 10.1 Python Dependencies

```python
# requirements.txt

# HTTP client
httpx>=0.27.0,<0.28.0

# Resilience patterns
pybreaker>=1.0.0,<2.0.0          # Circuit breaker
tenacity>=8.2.0,<9.0.0            # Retry with exponential backoff
aiolimiter>=1.1.0,<2.0.0          # Rate limiting (for internal use)

# Caching
aiocache[redis]>=0.12.0,<0.13.0  # Response caching

# Monitoring
prometheus-client>=0.20.0         # Metrics
structlog>=24.1.0                 # Structured logging

# Data validation
pydantic>=2.0.0,<3.0.0           # Request/response schemas

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
```

### 10.2 External Services

**Yandex Direct API v5:**
- Base URL: `https://api.direct.yandex.com/json/v5`
- Sandbox URL: `https://api-sandbox.direct.yandex.com/json/v5`
- Rate limits: 5 concurrent connections, 100k points/day
- Cost: FREE (no per-request charges)

**Yandex OAuth:**
- Authorization URL: `https://oauth.yandex.ru/authorize`
- Token URL: `https://oauth.yandex.ru/token`
- Required scope: `direct:api`
- Cost: FREE

**Redis (Optional):**
- For response caching
- TTL: 1 hour (configurable)
- Cost: $10-50/month (hosting)

**Prometheus (Optional):**
- For metrics collection
- Self-hosted or managed
- Cost: FREE (self-hosted) or $20-100/month (managed)

### 10.3 Environment Variables

```bash
# .env

# Yandex Direct API
YANDEX_DIRECT_TOKEN=your_oauth_token_here
YANDEX_DIRECT_CLIENT_LOGIN=client_login  # For agency accounts
YANDEX_DIRECT_USE_SANDBOX=false          # true for testing

# Rate limiting
YANDEX_DIRECT_MAX_CONNECTIONS=5
YANDEX_DIRECT_MAX_POINTS_PER_DAY=100000

# Circuit breaker
YANDEX_DIRECT_CIRCUIT_BREAKER_FAIL_MAX=5
YANDEX_DIRECT_CIRCUIT_BREAKER_RESET_TIMEOUT=60

# Retry
YANDEX_DIRECT_RETRY_MAX_ATTEMPTS=3
YANDEX_DIRECT_RETRY_MAX_WAIT=30

# Caching
YANDEX_DIRECT_CACHE_TTL=3600             # 1 hour
REDIS_URL=redis://localhost:6379/0       # Optional

# Monitoring
PROMETHEUS_PORT=9090                     # Optional
LOG_LEVEL=INFO
```

### 10.4 Integration with Services Layer

**Unified Interface:**

```python
# Services Layer uses unified interface
from AIM.src.aim.services.campaign_service import CampaignService

service = CampaignService()

# Same interface for both platforms
google_campaigns = await service.list_campaigns(platform="google")
yandex_campaigns = await service.list_campaigns(platform="yandex")

# Unified response format
for campaign in google_campaigns + yandex_campaigns:
    print(f"{campaign.name}: {campaign.status}")
```

**Internal Mapping:**

```python
# CampaignService internally maps to platform-specific clients
class CampaignService:
    def __init__(self):
        self.google_client = GoogleAdsClient(...)
        self.yandex_client = YandexDirectClient(...)
    
    async def list_campaigns(self, platform: str):
        if platform == "google":
            return await self.google_client.list_campaigns()
        elif platform == "yandex":
            return await self.yandex_client.list_campaigns()
```

---

## 11. Deployment

### 11.1 Docker Container

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY AIM/src/aim/subagents/yandex_direct_client/ ./yandex_direct_client/
COPY AIM/src/aim/subagents/schemas/ ./schemas/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "yandex_direct_client"]
```

### 11.2 Kubernetes Deployment

```yaml
# deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: yandex-direct-client
spec:
  replicas: 2
  selector:
    matchLabels:
      app: yandex-direct-client
  template:
    metadata:
      labels:
        app: yandex-direct-client
    spec:
      containers:
      - name: yandex-direct-client
        image: aim/yandex-direct-client:1.0.0
        env:
        - name: YANDEX_DIRECT_TOKEN
          valueFrom:
            secretKeyRef:
              name: yandex-direct-secrets
              key: oauth-token
        - name: YANDEX_DIRECT_MAX_CONNECTIONS
          value: "5"
        - name: YANDEX_DIRECT_MAX_POINTS_PER_DAY
          value: "100000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### 11.3 Monitoring Setup

```yaml
# prometheus-config.yaml

scrape_configs:
  - job_name: 'yandex-direct-client'
    static_configs:
      - targets: ['yandex-direct-client:9090']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Grafana Dashboard:**
- API request rate
- Error rate by error code
- Circuit breaker state
- Points usage (daily)
- Response time (p50, p95, p99)
- Active connections

---

## 12. Changelog

### Version 1.0.0 (2026-05-14)

**Initial Release:**
- Production-ready Yandex Direct API v5 client
- Unified interface matching Google Ads Client
- Resilience patterns (circuit breaker, exponential backoff, rate limit detection)
- Medical advertising compliance validation
- Changes service optimization (80-90% API call reduction)
- Comprehensive test coverage
- Docker and Kubernetes deployment

**Key Features:**
- Campaign CRUD operations
- Ad group and ad management
- Keyword and bid management
- Performance metrics collection
- OAuth 2.0 authentication
- Agency account support

**Research Base:**
- Deep research report: 2,218 lines, 65 KB
- 93 evidence items, 87/100 avg credibility
- 18+ code examples
- Production code analysis: yandex-ads-mcp (1,871 lines, 120 tools)

---

## 13. TODO and Future Enhancements

### Phase 1: Core Implementation (Current)
- ✅ Connection pooling (max 5 connections)
- ✅ Circuit breaker pattern
- ✅ Exponential backoff retry
- ✅ Rate limit detection
- ✅ Medical compliance validator
- ✅ Changes service optimization
- ✅ Unified interface design

### Phase 2: Advanced Features (Next Sprint)
- ⏳ Advanced retargeting (lookalike audiences)
- ⏳ Deep Yandex Metrica integration (goals, segments)
- ⏳ Wordstat API integration (keyword research)
- ⏳ Automated bid optimization
- ⏳ A/B testing framework
- ⏳ Budget pacing algorithms

### Phase 3: Production Hardening (Future)
- ⏳ Multi-region deployment
- ⏳ Disaster recovery
- ⏳ Advanced monitoring (APM, distributed tracing)
- ⏳ Performance optimization (caching strategies)
- ⏳ Security hardening (secrets management, audit logging)

### Phase 4: AI Integration (Future)
- ⏳ AI-powered ad copy generation
- ⏳ Automated campaign optimization
- ⏳ Predictive analytics
- ⏳ Anomaly detection

---

## Appendix A: Research Report Summary

**Full Report:** `~/Documents/Yandex_Direct_API_Research_20260514/Yandex_Direct_API_Research_Report.md`

**Key Findings:**

1. **Rate Limits Corrected:**
   - Initial assumption: 10 req/s
   - Actual limit: 5 concurrent connections + 100k points/day
   - Impact: Connection pooling required

2. **Production Code Gap:**
   - yandex-ads-mcp: excellent API structure, missing resilience patterns
   - Solution: Use yandex-ads-mcp + add circuit breaker, retry, rate limit detection

3. **Medical Compliance:**
   - Federal Law 38-FZ Article 24
   - Required disclaimer, prohibited phrases, license validation
   - Solution: MedicalAdValidator class

4. **Changes Service:**
   - 80-90% API call reduction
   - NOT implemented in yandex-ads-mcp
   - Solution: Mandatory for monitoring

**Statistics:**
- Research duration: 41 minutes (8 phases)
- Evidence items: 93 from 4 sources
- Average credibility: 87/100
- Code examples: 18+
- Report size: 2,218 lines, 65 KB

**Sources:**
- Official Yandex Direct API documentation
- yandex-ads-mcp repository (1,871 lines, 120 tools)
- Federal Law 38-FZ (medical advertising)
- Production best practices

---

## Appendix B: API Reference

### B.1 Campaign Methods

```python
# Create campaign
async def create_campaign(
    self,
    request: CampaignCreateRequest
) -> CampaignCreateResult

# Get campaigns
async def get_campaigns(
    self,
    campaign_ids: list[int]
) -> list[Campaign]

# Update campaign
async def update_campaign(
    self,
    campaign_id: int,
    updates: CampaignUpdateRequest
) -> CampaignUpdateResult

# Delete campaign
async def delete_campaign(
    self,
    campaign_id: int
) -> CampaignDeleteResult

# Get campaigns optimized (with Changes service)
async def get_campaigns_optimized(
    self,
    campaign_ids: list[int]
) -> list[Campaign]
```

### B.2 Metrics Methods

```python
# Get campaign metrics
async def get_campaign_metrics(
    self,
    campaign_ids: list[int],
    date_range: DateRange
) -> list[CampaignMetrics]

# Get performance report
async def get_performance_report(
    self,
    campaign_ids: list[int],
    metrics: list[str],
    date_range: DateRange
) -> PerformanceReport
```

### B.3 Medical Compliance Methods

```python
# Validate ad text
async def validate_ad_text(
    self,
    text: str
) -> MedicalAdValidationResult

# Validate campaign
async def validate_campaign(
    self,
    request: CampaignCreateRequest
) -> MedicalAdValidationResult
```

---

## Appendix C: Error Codes Reference

| Code | Description | Action | Retry? |
|------|-------------|--------|--------|
| 152 | Not enough points | Wait until next day | ❌ NO |
| 506 | Too many connections | Reduce connections | ❌ NO |
| 1002 | Invalid token | Refresh OAuth | ✅ YES |
| 53 | Campaign not found | Check campaign ID | ❌ NO |
| 54 | Campaign archived | Cannot modify | ❌ NO |
| 201 | Report in queue | Poll for completion | ✅ YES |
| 202 | Report processing | Poll for completion | ✅ YES |

---

**End of Specification**

**Version:** 1.0.0  
**Last Updated:** 2026-05-14  
**Status:** Ready for Implementation
