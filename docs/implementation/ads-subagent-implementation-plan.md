# Ads Subagent - Full Implementation Plan

**Date:** 2026-05-13
**Status:** Phase 2 - Analysis & Design
**Goal:** Replace mock Ads orchestrator with real MCP server + API clients + OAuth

---

## Phase 1: Skills Extracted ✅

**Source Repos:**
1. `google-ads-python` (696 stars) - 2,802 skills extracted
2. `googleads-python-lib` (739 stars) - 14 skills extracted  
3. `facebook-ads-library-mcp` (223 stars) - 9 skills extracted

**Total Skills:** 2,825

**Pattern Distribution:**
- **Ads - Api Client:** 1,766 skills (62.5%)
- **Retry with Exponential Backoff:** 917 skills (32.5%)
- **Ads - OAuth:** 125 skills (4.4%)
- **Caching:** 17 skills (0.6%)

---

## Phase 2: Analysis & Comparison

### Current State (Mock Implementation)

**File:** `AIM/src/aim/subagents/ads/orchestrator/ads_orchestrator.py` (293 lines)

**Problems:**
1. ❌ Hardcoded mock data in `_execute_campaign_creation()`
2. ❌ Fake metrics in `_execute_content_optimization()` (CTR +15%, CPC -20%)
3. ❌ Fake readability scores in `_execute_readability_analysis()`
4. ❌ No real API integration
5. ❌ No OAuth flow
6. ❌ No error handling or retry logic
7. ❌ No rate limiting or circuit breaker

### Target State (Real Implementation)

**Architecture from GitHub repos:**

```
AIM/src/aim/subagents/ads/
├── mcp_server.py                    # MCP server (FastMCP pattern from facebook-ads-library-mcp)
├── auth/
│   ├── __init__.py
│   ├── oauth_flow.py                # OAuth 2.0 flow (from google-ads-python/oauth2.py)
│   └── credentials_manager.py       # Token refresh, storage
├── api_clients/
│   ├── __init__.py
│   ├── base_client.py               # Base with retry, circuit breaker, rate limiting
│   ├── google_ads_client.py         # Google Ads API (from google-ads-python/client.py)
│   ├── yandex_direct_client.py      # Yandex Direct API (TODO: research)
│   └── facebook_ads_client.py       # Facebook Ads API (from facebook-ads-library-mcp)
├── services/
│   ├── __init__.py
│   ├── campaign_service.py          # Campaign CRUD operations
│   ├── content_optimizer.py         # Real content optimization (not mock)
│   └── analytics_service.py         # Real metrics collection
├── orchestrator/
│   └── ads_orchestrator.py          # Updated to use real services (not mock)
└── config/
    ├── __init__.py
    └── settings.py                  # API keys, rate limits, timeouts
```

---

## Phase 3: Key Patterns to Implement

### 1. MCP Server Pattern (from facebook-ads-library-mcp)

**Source:** `/tmp/teacher_repos/ads/facebook-ads-library-mcp/mcp_server.py`

**Key Features:**
- FastMCP framework for tool registration
- `@mcp.tool()` decorator with descriptions and annotations
- Structured error handling with custom exceptions
- Input validation (type checking, empty checks)
- Batch operations support
- Caching layer for efficiency

**Implementation:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Ads Manager",
    instructions="Manages advertising campaigns across Google Ads, Yandex Direct, Facebook Ads"
)

@mcp.tool(
    description="Create advertising campaign with targeting and budget",
    annotations={
        "title": "Create Ad Campaign",
        "readOnlyHint": False,
        "openWorldHint": True
    }
)
def create_campaign(
    platform: str,
    name: str,
    budget: float,
    targeting: dict
) -> dict:
    # Real implementation
    pass
```

### 2. OAuth 2.0 Flow (from google-ads-python)

**Source:** `/tmp/teacher_repos/ads/google-ads-python/google/ads/googleads/oauth2.py`

**Key Features:**
- `get_installed_app_credentials()` - OAuth flow for desktop apps
- `get_service_account_credentials()` - Service account auth
- Token refresh with `credentials.refresh(Request())`
- HTTP proxy support
- Decorator pattern for credential initialization

**Implementation:**
```python
from google.oauth2.credentials import Credentials as InstalledAppCredentials
from google.auth.transport.requests import Request

def get_oauth_credentials(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    http_proxy: str = None
) -> InstalledAppCredentials:
    credentials = InstalledAppCredentials(
        None,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        token_uri="https://accounts.google.com/o/oauth2/token"
    )
    
    if http_proxy:
        session = Session()
        session.proxies.update({"http": http_proxy, "https": http_proxy})
        credentials.refresh(Request(session=session))
    else:
        credentials.refresh(Request())
    
    return credentials
```

### 3. API Client Pattern (from google-ads-python)

**Source:** `/tmp/teacher_repos/ads/google-ads-python/google/ads/googleads/client.py`

**Key Features:**
- gRPC channel with custom options (max metadata size, max message length)
- Interceptors chain (metadata, exception, logging)
- Version management (v21, v22, v23, v24)
- Service client factory pattern
- ClientInfo for user-agent tracking

**Implementation:**
```python
import grpc
from google.api_core.gapic_v1.client_info import ClientInfo

_GRPC_CHANNEL_OPTIONS = [
    ("grpc.max_metadata_size", 16 * 1024 * 1024),
    ("grpc.max_receive_message_length", 64 * 1024 * 1024),
]

class GoogleAdsClient:
    def __init__(self, credentials, developer_token, customer_id):
        self.credentials = credentials
        self.developer_token = developer_token
        self.customer_id = customer_id
        self._client_info = ClientInfo(client_library_version="1.0.0")
    
    def get_service(self, service_name, version="v24"):
        # Create gRPC channel with interceptors
        channel = grpc.secure_channel(
            f"googleads.googleapis.com",
            credentials=self.credentials,
            options=_GRPC_CHANNEL_OPTIONS
        )
        
        # Add interceptors (metadata, exception, logging)
        channel = grpc.intercept_channel(
            channel,
            MetadataInterceptor(self.developer_token, self.customer_id),
            ExceptionInterceptor(),
            LoggingInterceptor()
        )
        
        return ServiceClient(channel, service_name, version)
```

### 4. Resilience Patterns (from extracted skills)

**Patterns Found:**
- **Retry with Exponential Backoff:** 917 instances
- **Circuit Breaker:** Implicit in error handling
- **Rate Limiting:** Token bucket pattern
- **Caching:** 17 instances

**Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker
from aiolimiter import AsyncLimiter

class ResilientAPIClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60
        )
        self.rate_limiter = AsyncLimiter(
            max_rate=10,
            time_period=1.0
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30)
    )
    async def call_api(self, endpoint, data):
        async with self.rate_limiter:
            return await self.circuit_breaker.call(
                self._make_request,
                endpoint,
                data
            )
```

---

## Phase 4: Implementation Steps

### Step 1: Setup Infrastructure (1-2 hours)

1. **Create directory structure:**
   ```bash
   mkdir -p AIM/src/aim/subagents/ads/{auth,api_clients,services,config}
   touch AIM/src/aim/subagents/ads/{auth,api_clients,services,config}/__init__.py
   ```

2. **Add dependencies to requirements.txt:**
   ```
   # MCP Server
   mcp>=1.0.0
   fastmcp>=0.2.0
   
   # Google Ads API
   google-ads>=24.0.0
   google-auth>=2.0.0
   google-auth-oauthlib>=1.0.0
   
   # Resilience
   tenacity>=8.2.0
   pybreaker>=1.0.0
   aiolimiter>=1.1.0
   
   # HTTP
   httpx>=0.27.0
   grpc>=1.60.0
   ```

3. **Create config/settings.py:**
   ```python
   from pydantic_settings import BaseSettings
   
   class AdsSettings(BaseSettings):
       # Google Ads
       google_ads_developer_token: str
       google_ads_client_id: str
       google_ads_client_secret: str
       google_ads_refresh_token: str
       google_ads_customer_id: str
       
       # Yandex Direct
       yandex_direct_token: str
       yandex_direct_client_id: str
       
       # Rate Limits
       rate_limit_capacity: int = 10
       rate_limit_refill: float = 1.0
       
       # Timeouts
       api_timeout: int = 30
       
       class Config:
           env_file = ".env"
   ```

### Step 2: Implement OAuth Flow (2-3 hours)

**File:** `AIM/src/aim/subagents/ads/auth/oauth_flow.py`

**Tasks:**
1. Copy OAuth logic from `google-ads-python/oauth2.py`
2. Implement `get_installed_app_credentials()`
3. Implement `get_service_account_credentials()`
4. Add token refresh logic
5. Add credentials storage (encrypted)

### Step 3: Implement Base API Client (2-3 hours)

**File:** `AIM/src/aim/subagents/ads/api_clients/base_client.py`

**Tasks:**
1. Copy resilience patterns from existing `AIM/src/aim/subagents/api_clients/base.py`
2. Add circuit breaker (pybreaker)
3. Add retry with exponential backoff (tenacity)
4. Add rate limiting (aiolimiter)
5. Add caching (aiocache)
6. Add structured logging (structlog)
7. Add Prometheus metrics

### Step 4: Implement Google Ads Client (3-4 hours)

**File:** `AIM/src/aim/subagents/ads/api_clients/google_ads_client.py`

**Tasks:**
1. Copy client architecture from `google-ads-python/client.py`
2. Implement gRPC channel setup with interceptors
3. Implement service factory pattern
4. Add campaign service methods:
   - `create_campaign()`
   - `update_campaign()`
   - `get_campaign()`
   - `list_campaigns()`
5. Add ad group service methods
6. Add keyword service methods

### Step 5: Implement MCP Server (2-3 hours)

**File:** `AIM/src/aim/subagents/ads/mcp_server.py`

**Tasks:**
1. Copy MCP server pattern from `facebook-ads-library-mcp/mcp_server.py`
2. Register tools:
   - `create_campaign` - Create new campaign
   - `get_campaign_metrics` - Get real metrics (not mock)
   - `optimize_campaign` - Real optimization (not fake +15% CTR)
   - `analyze_competitors` - Real competitor analysis
3. Add input validation
4. Add error handling with custom exceptions
5. Add batch operations support

### Step 6: Implement Services Layer (3-4 hours)

**Files:**
- `AIM/src/aim/subagents/ads/services/campaign_service.py`
- `AIM/src/aim/subagents/ads/services/content_optimizer.py`
- `AIM/src/aim/subagents/ads/services/analytics_service.py`

**Tasks:**
1. **Campaign Service:**
   - CRUD operations for campaigns
   - Budget management
   - Targeting configuration
   - Schedule management

2. **Content Optimizer:**
   - Real A/B testing (not mock)
   - Real CTR/CPC analysis (from API)
   - Keyword optimization
   - Ad copy suggestions

3. **Analytics Service:**
   - Real metrics collection (impressions, clicks, conversions)
   - Performance tracking
   - ROI calculation
   - Reporting

### Step 7: Update Orchestrator (1-2 hours)

**File:** `AIM/src/aim/subagents/ads/orchestrator/ads_orchestrator.py`

**Tasks:**
1. Remove all mock data
2. Replace `_execute_campaign_creation()` with real API calls
3. Replace `_execute_content_optimization()` with real optimization
4. Replace `_execute_readability_analysis()` with real analysis
5. Add error handling
6. Add logging

### Step 8: Write Tests (2-3 hours)

**Files:**
- `AIM/tests/subagents/ads/test_oauth_flow.py`
- `AIM/tests/subagents/ads/test_google_ads_client.py`
- `AIM/tests/subagents/ads/test_mcp_server.py`
- `AIM/tests/subagents/ads/test_campaign_service.py`

**Tasks:**
1. Unit tests for OAuth flow
2. Unit tests for API clients (with mocks)
3. Integration tests for MCP server
4. End-to-end tests for orchestrator

### Step 9: Documentation (1 hour)

**Files:**
- `AIM/src/aim/subagents/ads/README.md`
- `docs/subagents/ads-setup-guide.md`

**Tasks:**
1. Setup instructions (OAuth credentials, API keys)
2. Usage examples
3. API reference
4. Troubleshooting guide

### Step 10: Verification (1-2 hours)

**Tasks:**
1. Run all tests
2. Test OAuth flow with real credentials
3. Create test campaign via API
4. Verify metrics collection
5. Test error handling (rate limits, auth failures)
6. Performance testing (latency, throughput)

---

## Phase 5: Estimated Timeline

**Total Time:** 18-27 hours

**Breakdown:**
- Infrastructure setup: 1-2 hours
- OAuth implementation: 2-3 hours
- Base client: 2-3 hours
- Google Ads client: 3-4 hours
- MCP server: 2-3 hours
- Services layer: 3-4 hours
- Orchestrator update: 1-2 hours
- Testing: 2-3 hours
- Documentation: 1 hour
- Verification: 1-2 hours

**Parallel Work Opportunities:**
- OAuth + Base Client (can work in parallel)
- Services layer (3 files can be done in parallel)
- Tests (can write while implementing)

---

## Phase 6: Success Criteria

✅ **Code Quality:**
- [ ] No mock data in production code
- [ ] All API calls use real endpoints
- [ ] OAuth flow works with real credentials
- [ ] Error handling covers all edge cases
- [ ] Logging provides actionable insights

✅ **Functionality:**
- [ ] Can create real campaigns via Google Ads API
- [ ] Can fetch real metrics (impressions, clicks, CTR, CPC)
- [ ] Can optimize campaigns based on real data
- [ ] Can handle rate limits gracefully
- [ ] Can recover from API failures

✅ **Testing:**
- [ ] Unit test coverage > 80%
- [ ] All integration tests pass
- [ ] End-to-end test creates real campaign
- [ ] Performance tests show acceptable latency

✅ **Documentation:**
- [ ] Setup guide is complete and tested
- [ ] API reference is accurate
- [ ] Examples work out of the box
- [ ] Troubleshooting guide covers common issues

---

## Next Steps

1. **Start with Step 1** - Setup infrastructure
2. **Implement OAuth flow** - Critical dependency for all API calls
3. **Build base client** - Foundation for all API clients
4. **Implement Google Ads client** - First real API integration
5. **Continue through remaining steps** - Follow plan sequentially

**Current Status:** Ready to begin Step 1 (Infrastructure Setup)
