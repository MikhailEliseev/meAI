# Yandex Direct API v5 Python Client - Research Report Outline

## Executive Summary (200-400 words)
- Core research question
- Key findings summary
- Critical corrections (rate limits: 5 connections, not 10 req/s)
- Production-ready recommendations
- Cost analysis preview

---

## 1. Introduction

### 1.1 Research Scope
- Production-ready Yandex Direct API v5 Python client
- Unified interface matching Google Ads Client
- Medical advertising compliance
- Resilience patterns for production

### 1.2 Methodology
- 8-phase deep research (SCOPE → PACKAGE)
- 4 parallel research agents
- 93 evidence items from 4 independent sources
- Cross-reference verification (triangulation)

### 1.3 Key Assumptions Validated
- ✅ API v5 is stable and recommended
- ✅ OAuth 2.0 standard flow works
- ⚠️ CORRECTED: Rate limits are 5 concurrent connections (not 10 req/s)
- ✅ Medical compliance regulations exist (Federal Law 38-FZ)
- ✅ Unified interface is achievable

---

## 2. API Architecture & Authentication

### 2.1 REST API Structure
- Base endpoint: `https://api.direct.yandex.com/json/v5/{service}`
- 18 services: Campaigns, Ads, Keywords, Bids, Reports, etc.
- Request format: `{"method": "...", "params": {...}}`
- Response format: `{"result": {...}}` or `{"error": {...}}`
- [Evidence: evidence_001, evidence_002, repo_001]

### 2.2 OAuth 2.0 Authentication
- Token endpoint: `https://oauth.yandex.com/token`
- Authorization header: `Bearer {token}`
- Optional Client-Login header for agency accounts
- Token refresh mechanism
- [Evidence: evidence_006, evidence_007, evidence_008, repo_004]

**Code Example (from yandex-ads-mcp):**
```python
def _headers():
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json",
    }
    if LOGIN:
        h["Client-Login"] = LOGIN
    return h
```

### 2.3 Rate Limits & Points System
- **CRITICAL CORRECTION:** 5 concurrent connections (not 10 req/s)
- Points system: 100,000 points/day
- Each request costs points (varies by operation)
- Error 152: not enough points (costs 20 points to retry)
- Error 506: too many concurrent connections
- [Evidence: evidence_003, evidence_004, evidence_005, evidence_009, evidence_010]

**Recommendation:** Connection pooling with max 5 connections

### 2.4 Sandbox Mode
- Sandbox URL: `https://api-sandbox.direct.yandex.com/json/v5`
- Environment variable: `YD_SANDBOX=true`
- [Evidence: repo_009]

---

## 3. Campaign Management

### 3.1 Campaign Types
- TEXT_CAMPAIGN (Search)
- UNIFIED_CAMPAIGN (РСЯ - Display Network)
- SMART_BANNER_CAMPAIGN
- MASTER_CAMPAIGN
- [Evidence: evidence_002]

### 3.2 Bidding Strategies (8 types)
1. **WB_MAXIMUM_CLICKS** - Weekly budget, maximize clicks
2. **PAY_FOR_CONVERSION** - CPA optimization with goal
3. **PAY_FOR_CONVERSION_MULTIPLE_GOALS** - Multi-goal optimization
4. **WB_MAXIMUM_CONVERSION_RATE** - Maximize conversion rate
5. **AVERAGE_CPA** - Target CPA bidding
6. **AVERAGE_CPC** - Target CPC bidding
7. **HIGHEST_POSITION** - Premium placement
8. **SERVING_OFF** - Manual bidding only
- [Evidence: evidence_014, repo_005]

**Code Example (from yandex-ads-mcp):**
```python
search_strategy = args.get("strategy_search", "WB_MAXIMUM_CLICKS")
search_obj = {"BiddingStrategyType": search_strategy}

if search_strategy == "WB_MAXIMUM_CLICKS":
    params = {}
    if weekly_limit:
        params["WeeklySpendLimit"] = weekly_limit
    search_obj["WbMaximumClicks"] = params
```

### 3.3 Budget Management
- Budget amounts in micros (1 ruble = 1,000,000 micros)
- Daily budget with STANDARD or DISTRIBUTED mode
- Weekly spend limits for WB_ strategies
- [Evidence: evidence_013, repo_006]

**Code Example:**
```python
def _rubles_to_micros(rubles: float) -> int:
    return int(rubles * 1_000_000)
```

### 3.4 Targeting Options
- Geographic targeting (region IDs)
- Demographics (age, gender)
- Device targeting (mobile, desktop, tablet)
- Bid modifiers (10-1300%)
- [Evidence: evidence_002]

---

## 4. Resilience Patterns (Production-Ready)

### 4.1 Connection Pooling
**Problem:** 5 concurrent connections limit
**Solution:** httpx.AsyncClient with connection pool
```python
limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
client = httpx.AsyncClient(limits=limits)
```
**Evidence:** evidence_003, evidence_005

### 4.2 Circuit Breaker Pattern
**Problem:** Cascading failures on API errors
**Solution:** pybreaker library
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
async def api_call():
    # ... API request ...
```
**Gap:** NOT in yandex-ads-mcp (repo_008)
**Recommendation:** MUST implement for production

### 4.3 Retry with Exponential Backoff
**Problem:** Transient errors (network, rate limits)
**Solution:** tenacity library
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30)
)
async def api_call_with_retry():
    # ... API request ...
```
**Gap:** yandex-ads-mcp has basic retry for reports only (repo_003)
**Recommendation:** MUST implement for all API calls

### 4.4 Rate Limit Detection
**Problem:** Error 152 (not enough points) costs 20 points
**Solution:** Detect and handle gracefully
```python
if error_code == 152:
    # Wait until points reset (next day)
    logger.warning("Points exhausted, pausing until reset")
    raise RateLimitError("Daily points limit reached")
```
**Evidence:** evidence_009, evidence_012
**Gap:** NOT in yandex-ads-mcp (repo_008)

### 4.5 Changes Service Optimization
**Problem:** Fetching full data on every request wastes API calls
**Solution:** Use Changes service to check for updates first
**Benefit:** 80-90% reduction in API calls
**Evidence:** evidence_015, evidence_016
**Gap:** NOT in yandex-ads-mcp (repo_001)
**Recommendation:** MUST implement for production efficiency

---

## 5. Medical Advertising Compliance

### 5.1 Federal Law 38-FZ Article 24
- Regulates medical services advertising in Russia
- Applies to: clinics, doctors, medical procedures
- [Evidence: evidence_med_001]

### 5.2 Required Disclaimers
**Mandatory text:**
"Имеются противопоказания. Необходима консультация специалиста"
(There are contraindications. Specialist consultation required)
- [Evidence: evidence_med_002]

### 5.3 Prohibited Content
- ❌ Patient testimonials or healing case references
- ❌ Guarantees of treatment results
- ❌ Targeting minors (under 18)
- ❌ Before/after photos without disclaimers
- [Evidence: evidence_med_003]

### 5.4 Implementation Strategy
```python
class MedicalComplianceValidator:
    REQUIRED_DISCLAIMER = "Имеются противопоказания. Необходима консультация специалиста"
    
    def validate_ad_text(self, text: str) -> bool:
        # Check for prohibited content
        if self._has_testimonials(text):
            return False
        if self._has_guarantees(text):
            return False
        # Check for required disclaimer
        if self.REQUIRED_DISCLAIMER not in text:
            return False
        return True
```

---

## 6. Unified Interface Design

### 6.1 Matching Google Ads Client
**Goal:** Same method signatures for both platforms

**Google Ads Client:**
```python
campaign = await google_client.create_campaign(
    name="Summer Sale",
    budget_usd=50.0,
    channel_type="SEARCH",
    status="PAUSED"
)
```

**Yandex Direct Client (unified):**
```python
campaign = await yandex_client.create_campaign(
    name="Summer Sale",
    budget_usd=50.0,  # Converted to rubles internally
    channel_type="SEARCH",
    status="PAUSED"
)
```

### 6.2 Internal Mapping
- `budget_usd` → convert to rubles → convert to micros
- `channel_type="SEARCH"` → `Type="TEXT_CAMPAIGN"`
- `status="PAUSED"` → `State="OFF"`

### 6.3 Unified Response Format
```python
{
    "campaign_id": "12345",
    "resource_name": "customers/123/campaigns/12345",
    "name": "Summer Sale",
    "status": "PAUSED",
    "budget_usd": 50.0,
    "platform": "yandex_direct"
}
```

---

## 7. Metrics & Reporting

### 7.1 Available Metrics
- Impressions, Clicks, CTR
- Cost (in micros), CPC, CPM
- Conversions, Conversion Rate
- Quality Score
- [Evidence: evidence_002]

### 7.2 Reports API
- 6 report types: ACCOUNT, CAMPAIGN, ADGROUP, AD, CRITERIA, SEARCH_QUERY
- TSV format output
- Async processing (201/202 status codes)
- Retry logic with `retryIn` header
- [Evidence: repo_003]

**Code Example (from yandex-ads-mcp):**
```python
for attempt in range(30):
    resp = await client.post(url, headers=headers, json=body, timeout=120)
    if resp.status_code == 200:
        return resp.text
    elif resp.status_code in (201, 202):
        retry_in = int(resp.headers.get("retryIn", 5))
        await asyncio.sleep(retry_in)
        continue
```

---

## 8. Implementation Guide

### 8.1 Project Structure
```
yandex_direct_client/
├── __init__.py
├── client.py              # Main YandexDirectClient class
├── auth.py                # OAuth 2.0 flow
├── services/
│   ├── campaigns.py       # Campaign management
│   ├── ads.py             # Ad management
│   ├── keywords.py        # Keyword management
│   └── reports.py         # Reporting
├── resilience/
│   ├── circuit_breaker.py
│   ├── retry.py
│   └── rate_limiter.py
├── compliance/
│   └── medical.py         # Medical advertising validation
└── schemas/
    └── responses.py       # Pydantic models
```

### 8.2 Dependencies
```
httpx>=0.27.0              # HTTP client with connection pooling
pybreaker>=1.0.0           # Circuit breaker
tenacity>=8.2.0            # Retry logic
pydantic>=2.0.0            # Data validation
structlog>=24.1.0          # Structured logging
```

### 8.3 Configuration
```python
class YandexDirectSettings(BaseSettings):
    oauth_token: str
    client_login: Optional[str] = None
    use_sandbox: bool = False
    max_connections: int = 5
    max_points_per_day: int = 100_000
    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 60
```

---

## 9. Code Examples

### 9.1 Basic Client Usage
```python
from yandex_direct_client import YandexDirectClient

client = YandexDirectClient(
    oauth_token="YOUR_TOKEN",
    client_login="agency_login"  # Optional
)

# Create campaign
campaign = await client.create_campaign(
    name="Medical Clinic - Moscow",
    budget_usd=100.0,
    channel_type="SEARCH",
    strategy="WB_MAXIMUM_CLICKS",
    weekly_spend_limit=700.0,
    region_ids=[213],  # Moscow
)

# Get metrics
metrics = await client.get_campaign_metrics(
    campaign_id=campaign["campaign_id"],
    date_range="LAST_30_DAYS"
)

print(f"Impressions: {metrics['impressions']}")
print(f"Clicks: {metrics['clicks']}")
print(f"CTR: {metrics['ctr']}%")
```

### 9.2 Medical Compliance Validation
```python
from yandex_direct_client.compliance import MedicalComplianceValidator

validator = MedicalComplianceValidator()

ad_text = """
Стоматологическая клиника в Москве.
Лечение зубов без боли.
Имеются противопоказания. Необходима консультация специалиста.
"""

if validator.validate_ad_text(ad_text):
    # Create ad
    ad = await client.create_ad(
        ad_group_id=12345,
        title="Стоматология Москва",
        text=ad_text,
        href="https://example.com"
    )
else:
    print("Ad text violates medical advertising regulations")
```

### 9.3 Resilience Patterns in Action
```python
from yandex_direct_client import YandexDirectClient
from yandex_direct_client.exceptions import RateLimitError, CircuitBreakerError

client = YandexDirectClient(oauth_token="TOKEN")

try:
    campaigns = await client.list_campaigns()
except RateLimitError as e:
    # Daily points limit reached
    logger.warning(f"Rate limit: {e}")
    # Wait until next day or use cached data
except CircuitBreakerError as e:
    # Circuit breaker opened after 5 failures
    logger.error(f"Circuit breaker: {e}")
    # Fallback to degraded mode
```

---

## 10. Testing Strategy

### 10.1 Sandbox Testing
- Use `YD_SANDBOX=true` for development
- Sandbox URL: `https://api-sandbox.direct.yandex.com/json/v5`
- No real money spent
- [Evidence: repo_009]

### 10.2 Unit Tests
- Mock API responses
- Test resilience patterns (circuit breaker, retry)
- Test compliance validation
- Test budget conversion

### 10.3 Integration Tests
- Real API calls to sandbox
- Test OAuth flow
- Test campaign creation end-to-end
- Test error handling (152, 506, 1002)

---

## 11. Cost Analysis

### 11.1 API Costs
- **Yandex Direct API:** FREE (no per-request charges)
- **Rate limits:** 100,000 points/day (free tier)
- **Sandbox:** Unlimited testing (free)

### 11.2 Development Costs
- OAuth setup: 1-2 hours
- Client implementation: 20-30 hours
- Resilience patterns: 10-15 hours
- Medical compliance: 5-10 hours
- Testing: 10-15 hours
- **Total:** 46-72 hours

### 11.3 Operational Costs
- API calls: FREE
- Server hosting: $10-50/month (depending on scale)
- Monitoring: $0-20/month (Prometheus + Grafana)

---

## 12. Limitations & Caveats

### 12.1 Reference Code Limitations
- yandex-ads-mcp lacks production resilience patterns
- No circuit breaker implementation
- No Changes service optimization
- Basic error handling only

### 12.2 API Limitations
- 5 concurrent connections (strict limit)
- 100,000 points/day (can be exhausted quickly)
- Error retries cost 20 points each
- Reports are async (polling required)

### 12.3 Medical Compliance
- Regulations may change (monitor Federal Law 38-FZ)
- Manual review recommended for sensitive content
- Automated validation is a safety net, not a guarantee

---

## 13. Recommendations

### 13.1 Must Implement
1. ✅ Connection pooling (max 5 connections)
2. ✅ Circuit breaker pattern
3. ✅ Exponential backoff with jitter
4. ✅ Rate limit detection (error 152, 506)
5. ✅ Changes service optimization (80-90% API call reduction)
6. ✅ Medical compliance validation layer

### 13.2 Should Implement
1. ✅ Structured logging (structlog)
2. ✅ Prometheus metrics
3. ✅ Sandbox mode for testing
4. ✅ Unified interface with Google Ads Client

### 13.3 Nice to Have
1. ⚪ Async batch operations
2. ⚪ Caching layer (Redis)
3. ⚪ Webhook notifications
4. ⚪ Admin dashboard

---

## 14. Future Research

### 14.1 Advanced Features
- Dynamic remarketing
- Lookalike audiences
- Smart banners optimization
- Master campaigns (multi-goal)

### 14.2 Yandex Metrica Integration
- Goal tracking
- Conversion attribution
- Cohort analysis
- Custom segments

### 14.3 Wordstat API
- Keyword research
- Traffic forecasting
- Seasonal trends
- Regional distribution

---

## 15. Bibliography

### Official Documentation
1. Yandex Direct API v5 Documentation - https://yandex.ru/dev/direct/doc/
2. OAuth 2.0 Yandex - https://yandex.ru/dev/id/doc/
3. Federal Law 38-FZ Article 24 - https://www.consultant.ru/document/cons_doc_LAW_58968/

### GitHub Repositories
4. yandex-ads-mcp - https://github.com/Yurich-ru/yandex-ads-mcp (120 tools, MCP integration)
5. tapi-yandex-direct - Python library for Yandex Direct API

### Research Sources
6. Agent 1: Medical Compliance Research (15 evidence items)
7. Agent 3: API Documentation Analysis (68 evidence items)
8. Repository Analysis: yandex-ads-mcp (10 evidence items)
9. Search Results: Production patterns, resilience, Python implementations

**Total Sources:** 9 primary sources
**Total Evidence Items:** 93
**Average Credibility:** 87/100
**Contradictions Resolved:** 1 (rate limits)
**Gaps Identified:** 2 (resilience patterns, Changes service)

---

## Appendix A: Error Codes Reference

| Code | Description | Action |
|------|-------------|--------|
| 152 | Not enough points | Wait until next day, don't retry (costs 20 points) |
| 506 | Too many connections | Reduce concurrent connections to max 5 |
| 1002 | Invalid token | Refresh OAuth token |
| 201 | Report created (offline) | Poll with `retryIn` header |
| 202 | Report processing | Poll with `retryIn` header |

[Evidence: evidence_009, evidence_010, evidence_011, repo_003]

---

## Appendix B: Bidding Strategies Comparison

| Strategy | Use Case | Parameters | Best For |
|----------|----------|------------|----------|
| WB_MAXIMUM_CLICKS | Maximize traffic | weekly_spend_limit | Brand awareness |
| PAY_FOR_CONVERSION | CPA optimization | goal_id, goal_cpa, weekly_limit | Lead generation |
| WB_MAXIMUM_CONVERSION_RATE | Maximize CR | goal_id, weekly_limit | E-commerce |
| AVERAGE_CPA | Target CPA | goal_id, average_cpa, weekly_limit | Performance marketing |
| AVERAGE_CPC | Target CPC | weekly_limit | Budget control |

[Evidence: evidence_014, repo_005]

---

**Report Status:** Outline Complete ✅
**Next Phase:** Phase 5 (SYNTHESIZE) - Write full report sections
**Estimated Report Size:** 30-40 KB (8,000-10,000 words)
**Target Delivery:** 2026-05-14
