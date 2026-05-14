# API Integration Guide

Comprehensive guide to integrating external APIs in the AIM Testing Infrastructure.

## Table of Contents

- [Overview](#overview)
- [API Clients](#api-clients)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Cost Management](#cost-management)

## Overview

AIM integrates with multiple external APIs for keyword research, analytics, and advertising:

**Integrated APIs:**
- **SEMrush API** - Keyword research, competition analysis
- **Ahrefs API** - Backlink analysis, keyword data (fallback)
- **Google Analytics 4** - Traffic analysis, conversions, attribution
- **Yandex Metrica** - Russian market analytics (fallback)
- **PageSpeed Insights** - Performance metrics, Core Web Vitals
- **Yandex Direct** - Campaign management, budget optimization

**Architecture:**
```
Application Layer
  ↓
API Clients (with resilience patterns)
  ├─ Circuit Breaker (fail-fast after 5 failures)
  ├─ Retry Logic (exponential backoff 1s → 30s)
  ├─ Rate Limiting (token bucket)
  └─ Caching (1-hour TTL)
  ↓
External APIs
```

## API Clients

### Base Client Pattern

All API clients inherit from `BaseAPIClient` which provides:

- **Circuit Breaker** - Fail-fast after consecutive failures
- **Retry Logic** - Exponential backoff with jitter
- **Rate Limiting** - Token bucket algorithm
- **Response Caching** - 1-hour TTL by default
- **Metrics** - Prometheus-compatible metrics
- **Logging** - Structured logging with context

**Example:**
```python
from aim.subagents.api_clients.base import BaseAPIClient

class MyAPIClient(BaseAPIClient):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            base_url="https://api.example.com",
            rate_limit_capacity=10,  # 10 requests
            rate_limit_refill=1.0,   # per second
            **kwargs
        )
        self.api_key = api_key
    
    async def fetch_data(self, query: str) -> dict:
        """Fetch data with automatic retry and caching."""
        return await self._request(
            method="GET",
            endpoint="/data",
            params={"q": query, "key": self.api_key}
        )
```

### SEMrush API

**Purpose:** Keyword research and competition analysis

**Setup:**

1. **Get API Key**
   - Sign up at [SEMrush](https://www.semrush.com/api/)
   - Navigate to API section
   - Generate API key

2. **Configure Environment**
   ```bash
   # AIM/.env
   SEMRUSH_API_KEY=your_api_key_here
   ```

3. **Usage**
   ```python
   from aim.subagents.api_clients.semrush import SEMrushClient
   
   client = SEMrushClient(api_key=os.getenv("SEMRUSH_API_KEY"))
   
   # Expand keywords
   keywords = await client.expand_keywords(
       seed_keyword="dental implants",
       max_keywords=100,
       min_volume=10,
       max_cost_usd=5.0
   )
   
   # Close client
   await client.close()
   ```

**API Endpoints:**
- `keyword_magic_tool` - Keyword expansion
- `phrase_related` - Related keywords
- `phrase_questions` - Question keywords

**Cost:** $0.01 per API call

**Rate Limits:** 
- 10 requests per second (configurable)
- 40,000 API units per day

**Response Format:**
```python
@dataclass
class SEMrushKeywordData:
    keyword: str
    search_volume: int
    cpc: float
    competition: float
    intent: str  # informational, commercial, transactional
    difficulty: int  # 0-100
```

### Ahrefs API

**Purpose:** Backlink analysis, keyword data (fallback for SEMrush)

**Setup:**

1. **Get API Key**
   - Sign up at [Ahrefs](https://ahrefs.com/api)
   - Generate API token

2. **Configure Environment**
   ```bash
   # AIM/.env
   AHREFS_API_KEY=your_api_key_here
   ```

3. **Usage**
   ```python
   from aim.subagents.api_clients.ahrefs import AhrefsClient
   
   client = AhrefsClient(api_key=os.getenv("AHREFS_API_KEY"))
   
   # Expand keywords
   keywords = await client.expand_keywords(
       seed_keyword="dental implants",
       max_keywords=100
   )
   
   await client.close()
   ```

**API Endpoints:**
- `keywords_explorer` - Keyword data
- `backlinks` - Backlink analysis
- `domain_rating` - Domain authority

**Cost:** $0.02 per API call

**Rate Limits:** 5 requests per second

**Response Format:**
```python
@dataclass
class AhrefsKeywordData:
    keyword: str
    search_volume: int
    cpc: float
    difficulty: int  # 0-100
    parent_topic: str
```

### Google Analytics 4

**Purpose:** Traffic analysis, conversions, attribution

**Setup:**

1. **Create Service Account**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing
   - Enable Google Analytics Data API
   - Create Service Account:
     - IAM & Admin > Service Accounts > Create
     - Download JSON key file

2. **Grant Access**
   - Open GA4 property
   - Admin > Property Access Management
   - Add service account email
   - Grant "Viewer" role

3. **Configure Environment**
   ```bash
   # AIM/.env
   GA4_PROPERTY_ID=123456789
   GA4_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
   
   # OR for cloud deployments
   GA4_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
   ```

4. **Usage**
   ```python
   from aim.subagents.api_clients.ga4_client import GA4Client
   
   client = GA4Client(
       property_id=os.getenv("GA4_PROPERTY_ID"),
       credentials_path=os.getenv("GA4_SERVICE_ACCOUNT_FILE")
   )
   
   # Get traffic sources
   traffic = await client.get_traffic_sources(
       start_date="2026-05-01",
       end_date="2026-05-14"
   )
   
   # Get conversions
   conversions = await client.get_conversions(
       start_date="2026-05-01",
       end_date="2026-05-14"
   )
   
   await client.close()
   ```

**API Endpoints:**
- `runReport` - Custom reports
- `batchRunReports` - Multiple reports

**Cost:** Free (quota-based)

**Rate Limits:**
- 10 requests per second per property
- 25,000 tokens per day per property

**Response Format:**
```python
@dataclass
class TrafficSource:
    source: str  # google, yandex, direct, referral
    medium: str  # organic, cpc, referral
    sessions: int
    users: int
    bounce_rate: float
    avg_session_duration: float
```

### Yandex Metrica

**Purpose:** Russian market analytics (fallback for GA4)

**Setup:**

1. **Get OAuth Token**
   - Go to [Yandex OAuth](https://oauth.yandex.ru/)
   - Register application
   - Get OAuth token with `metrika:read` scope

2. **Configure Environment**
   ```bash
   # AIM/.env
   YANDEX_METRICA_TOKEN=your_oauth_token_here
   YANDEX_METRICA_COUNTER_ID=12345678
   ```

3. **Usage**
   ```python
   from aim.subagents.api_clients.yandex_metrica_client import YandexMetricaClient
   
   client = YandexMetricaClient(
       oauth_token=os.getenv("YANDEX_METRICA_TOKEN"),
       counter_id=os.getenv("YANDEX_METRICA_COUNTER_ID")
   )
   
   # Get traffic sources
   traffic = await client.get_traffic_sources(
       start_date="2026-05-01",
       end_date="2026-05-14"
   )
   
   await client.close()
   ```

**API Endpoints:**
- `stat/v1/data` - Statistics data
- `management/v1/counters` - Counter management

**Cost:** Free

**Rate Limits:** 10 requests per second

**Response Format:**
```python
@dataclass
class YandexTrafficSource:
    source: str  # yandex, google, direct
    visits: int
    users: int
    bounce_rate: float
    avg_visit_duration: float
```

### PageSpeed Insights

**Purpose:** Performance metrics, Core Web Vitals

**Setup:**

1. **Get API Key** (optional, increases quota)
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable PageSpeed Insights API
   - Create API key

2. **Configure Environment**
   ```bash
   # AIM/.env
   PAGESPEED_API_KEY=your_api_key_here  # Optional
   ```

3. **Usage**
   ```python
   from aim.subagents.api_clients.pagespeed_client import PageSpeedClient
   
   client = PageSpeedClient(api_key=os.getenv("PAGESPEED_API_KEY"))
   
   # Analyze page
   result = await client.analyze_page(
       url="https://example.com",
       strategy="mobile"  # or "desktop"
   )
   
   await client.close()
   ```

**API Endpoints:**
- `runpagespeed` - Page analysis

**Cost:** Free

**Rate Limits:**
- Without key: 400 requests per minute
- With key: 25,000 requests per day

**Response Format:**
```python
@dataclass
class PageSpeedResult:
    performance_score: int  # 0-100
    lcp: float  # Largest Contentful Paint (seconds)
    cls: float  # Cumulative Layout Shift
    fcp: float  # First Contentful Paint (seconds)
    ttfb: float  # Time to First Byte (seconds)
```

### Yandex Direct

**Purpose:** Campaign management, budget optimization

**Setup:**

1. **Get OAuth Token**
   - Go to [Yandex OAuth](https://oauth.yandex.ru/)
   - Register application
   - Get OAuth token with `direct:api` scope

2. **Configure Environment**
   ```bash
   # AIM/.env
   YANDEX_DIRECT_TOKEN=your_oauth_token_here
   ```

3. **Usage**
   ```python
   from aim.subagents.api_clients.yandex_direct_client import YandexDirectClient
   
   client = YandexDirectClient(
       oauth_token=os.getenv("YANDEX_DIRECT_TOKEN")
   )
   
   # Get campaigns
   campaigns = await client.get_campaigns()
   
   # Get campaign stats
   stats = await client.get_campaign_stats(
       campaign_ids=[123, 456],
       start_date="2026-05-01",
       end_date="2026-05-14"
   )
   
   await client.close()
   ```

**API Endpoints:**
- `campaigns` - Campaign management
- `reports` - Statistics reports

**Cost:** Free

**Rate Limits:** 10 requests per second

**Response Format:**
```python
@dataclass
class CampaignStats:
    campaign_id: int
    impressions: int
    clicks: int
    cost: float  # in microroubles
    conversions: int
    ctr: float
    cpc: float
    cpa: float
```

## Authentication

### API Key Authentication

**Pattern:**
```python
class APIKeyClient(BaseAPIClient):
    def __init__(self, api_key: str):
        super().__init__(base_url="https://api.example.com")
        self.api_key = api_key
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        # Add API key to headers
        headers = kwargs.get("headers", {})
        headers["X-API-Key"] = self.api_key
        kwargs["headers"] = headers
        
        return await super()._request(method, endpoint, **kwargs)
```

**Used by:** SEMrush, Ahrefs, PageSpeed Insights

### OAuth 2.0 Authentication

**Pattern:**
```python
class OAuthClient(BaseAPIClient):
    def __init__(self, oauth_token: str):
        super().__init__(base_url="https://api.example.com")
        self.oauth_token = oauth_token
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        # Add OAuth token to headers
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.oauth_token}"
        kwargs["headers"] = headers
        
        return await super()._request(method, endpoint, **kwargs)
```

**Used by:** Yandex Metrica, Yandex Direct

### Service Account Authentication

**Pattern:**
```python
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient

class ServiceAccountClient:
    def __init__(self, credentials_path: str):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
        self.client = BetaAnalyticsDataClient(credentials=credentials)
```

**Used by:** Google Analytics 4

## Rate Limiting

### Token Bucket Algorithm

**Implementation:**
```python
from aiolimiter import AsyncLimiter

class RateLimitedClient(BaseAPIClient):
    def __init__(self, capacity: int, refill_rate: float):
        super().__init__(base_url="https://api.example.com")
        self.rate_limiter = AsyncLimiter(
            max_rate=capacity,
            time_period=1.0 / refill_rate
        )
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        # Acquire token before request
        async with self.rate_limiter:
            return await super()._request(method, endpoint, **kwargs)
```

**Configuration:**
```python
# SEMrush: 10 requests per second
client = SEMrushClient(
    api_key="...",
    rate_limit_capacity=10,
    rate_limit_refill=1.0
)

# Ahrefs: 5 requests per second
client = AhrefsClient(
    api_key="...",
    rate_limit_capacity=5,
    rate_limit_refill=1.0
)
```

### Handling Rate Limit Errors

```python
async def _request(self, method: str, endpoint: str, **kwargs):
    try:
        return await super()._request(method, endpoint, **kwargs)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Rate limit exceeded
            retry_after = int(e.response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limit exceeded, retry after {retry_after}s")
            await asyncio.sleep(retry_after)
            return await self._request(method, endpoint, **kwargs)
        raise
```

## Error Handling

### Circuit Breaker Pattern

**Purpose:** Fail-fast when service is down

**Implementation:**
```python
from pybreaker import CircuitBreaker

class ResilientClient(BaseAPIClient):
    def __init__(self):
        super().__init__(base_url="https://api.example.com")
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,           # Open after 5 failures
            reset_timeout=60,     # Try again after 60s
            exclude=[httpx.HTTPStatusError]  # Don't count 4xx errors
        )
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        return await self.circuit_breaker.call_async(
            super()._request,
            method,
            endpoint,
            **kwargs
        )
```

### Retry with Exponential Backoff

**Purpose:** Retry transient failures

**Implementation:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class RetryClient(BaseAPIClient):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(httpx.TimeoutException)
    )
    async def _request(self, method: str, endpoint: str, **kwargs):
        return await super()._request(method, endpoint, **kwargs)
```

### Fallback Strategy

**Purpose:** Use alternative data source when primary fails

**Implementation:**
```python
class FallbackClient:
    def __init__(self, primary: APIClient, fallback: APIClient):
        self.primary = primary
        self.fallback = fallback
    
    async def fetch_data(self, query: str) -> dict:
        try:
            return await self.primary.fetch_data(query)
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            return await self.fallback.fetch_data(query)
```

**Example:**
```python
# GA4 → Yandex Metrica → Mock
traffic_data = await self._fetch_with_fallback(
    primary=lambda: ga4_client.get_traffic_sources(...),
    fallback=lambda: yandex_client.get_traffic_sources(...),
    mock=lambda: self._generate_mock_traffic()
)
```

## Testing

### Mocking API Responses

**Pattern:**
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_semrush_client(monkeypatch):
    """Mock SEMrush API client."""
    async def mock_expand(*args, **kwargs):
        return [
            KeywordData(
                keyword="dental implants",
                search_volume=12000,
                cpc=15.50,
                competition=0.85
            )
        ]
    
    monkeypatch.setattr(
        "aim.subagents.api_clients.semrush.SEMrushClient.expand_keywords",
        mock_expand
    )

async def test_keyword_expansion(mock_semrush_client):
    """Test keyword expansion with mocked API."""
    agent = KeywordResearchAgent(api_key="test")
    keywords = await agent.expand_keywords("dental")
    
    assert len(keywords) > 0
    assert keywords[0].keyword == "dental implants"
```

### VCR Cassettes (Record/Replay)

**Purpose:** Record real API responses for offline testing

**Setup:**
```bash
pip install pytest-vcr
```

**Usage:**
```python
import pytest

@pytest.mark.vcr
async def test_real_api_call():
    """Test with real API (recorded once)."""
    client = SEMrushClient(api_key=os.getenv("SEMRUSH_API_KEY"))
    keywords = await client.expand_keywords("dental")
    
    assert len(keywords) > 0
```

**Cassette Location:**
```
tests/fixtures/vcr_cassettes/
└── test_real_api_call.yaml
```

### Testing Rate Limiting

```python
async def test_rate_limiting():
    """Test rate limiter prevents exceeding limits."""
    client = SEMrushClient(
        api_key="test",
        rate_limit_capacity=2,
        rate_limit_refill=1.0
    )
    
    start = time.time()
    
    # First 2 requests should be immediate
    await client.expand_keywords("test1")
    await client.expand_keywords("test2")
    
    # Third request should wait ~1 second
    await client.expand_keywords("test3")
    
    duration = time.time() - start
    assert duration >= 1.0  # Rate limiter delayed third request
```

## Cost Management

### Budget Guards

**Purpose:** Prevent exceeding API cost budgets

**Implementation:**
```python
class BudgetGuardedClient(BaseAPIClient):
    def __init__(self, max_cost_usd: float, cost_per_request: float):
        super().__init__(base_url="https://api.example.com")
        self.max_cost_usd = max_cost_usd
        self.cost_per_request = cost_per_request
        self.total_cost = 0.0
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        # Check budget before request
        if self.total_cost + self.cost_per_request > self.max_cost_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.total_cost:.2f} / ${self.max_cost_usd:.2f}"
            )
        
        result = await super()._request(method, endpoint, **kwargs)
        self.total_cost += self.cost_per_request
        
        return result
```

**Usage:**
```python
client = SEMrushClient(
    api_key="...",
    max_cost_usd=5.0,  # $5 budget
    cost_per_request=0.01  # $0.01 per call
)

# Will stop after 500 requests
keywords = await client.expand_keywords("dental", max_keywords=1000)
```

### Cost Tracking

**Metrics:**
```python
from prometheus_client import Counter, Histogram

api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["client", "endpoint", "status"]
)

api_cost_usd = Counter(
    "api_cost_usd_total",
    "Total API cost in USD",
    ["client"]
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    ["client", "endpoint"]
)
```

**Tracking:**
```python
async def _request(self, method: str, endpoint: str, **kwargs):
    start = time.time()
    
    try:
        result = await super()._request(method, endpoint, **kwargs)
        api_requests_total.labels(
            client=self.__class__.__name__,
            endpoint=endpoint,
            status="success"
        ).inc()
        return result
    except Exception as e:
        api_requests_total.labels(
            client=self.__class__.__name__,
            endpoint=endpoint,
            status="error"
        ).inc()
        raise
    finally:
        duration = time.time() - start
        api_request_duration.labels(
            client=self.__class__.__name__,
            endpoint=endpoint
        ).observe(duration)
        
        api_cost_usd.labels(
            client=self.__class__.__name__
        ).inc(self.cost_per_request)
```

### Cost Optimization

**1. Response Caching**
```python
from aiocache import cached

@cached(ttl=3600)  # Cache for 1 hour
async def expand_keywords(self, seed: str) -> list[KeywordData]:
    """Cached keyword expansion."""
    return await self._request("GET", "/keywords", params={"seed": seed})
```

**2. Batch Requests**
```python
async def expand_keywords_batch(
    self,
    seeds: list[str]
) -> dict[str, list[KeywordData]]:
    """Expand multiple keywords in one request."""
    # Single API call for multiple seeds
    response = await self._request(
        "POST",
        "/keywords/batch",
        json={"seeds": seeds}
    )
    return response
```

**3. Incremental Updates**
```python
async def get_traffic_incremental(
    self,
    last_update: datetime
) -> TrafficData:
    """Fetch only new data since last update."""
    return await self._request(
        "GET",
        "/traffic",
        params={
            "start_date": last_update.isoformat(),
            "end_date": datetime.now().isoformat()
        }
    )
```

## API Cost Summary

| API | Cost | Rate Limit | Free Tier |
|-----|------|------------|-----------|
| SEMrush | $0.01/call | 10 req/s | No |
| Ahrefs | $0.02/call | 5 req/s | No |
| GA4 | Free | 10 req/s | 25K tokens/day |
| Yandex Metrica | Free | 10 req/s | Unlimited |
| PageSpeed | Free | 400 req/min | 25K req/day with key |
| Yandex Direct | Free | 10 req/s | Unlimited |

**Estimated Monthly Costs:**
- **Development:** $0 (all mocked)
- **Testing:** $5-10 (limited real API calls)
- **Production:** $50-200 (depends on usage)

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: 401 Unauthorized
Solution: Check API key/token is correct and not expired
```

**2. Rate Limit Exceeded**
```
Error: 429 Too Many Requests
Solution: Increase rate_limit_capacity or reduce request frequency
```

**3. Timeout Errors**
```
Error: httpx.TimeoutException
Solution: Increase timeout or check network connectivity
```

**4. Invalid Response**
```
Error: JSONDecodeError
Solution: Check API endpoint and response format
```

## References

- [SEMrush API Docs](https://www.semrush.com/api-documentation/)
- [Ahrefs API Docs](https://ahrefs.com/api/documentation)
- [GA4 API Docs](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Yandex Metrica API](https://yandex.ru/dev/metrika/)
- [PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started)
- [Yandex Direct API](https://yandex.ru/dev/direct/)

---

**Last Updated:** 2026-05-15  
**Version:** 1.0  
**Maintainer:** Mikhail Eliseev
