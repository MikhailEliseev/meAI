# Ads Subagent - Google Ads Campaign Management

Production-ready Google Ads integration with real API calls, resilience patterns, and comprehensive analytics.

## Architecture

```
ads/
├── config/
│   └── settings.py              # Configuration management
├── auth/
│   └── oauth_flow.py            # OAuth 2.0 authentication
├── api_clients/
│   ├── base_client.py           # Base client with resilience patterns
│   └── google_ads_client.py     # Google Ads API integration
├── services/
│   ├── campaign_service.py      # Campaign CRUD operations
│   ├── content_optimizer.py     # A/B testing and optimization
│   └── analytics_service.py     # Performance tracking and ROI
├── orchestrator/
│   └── ads_orchestrator.py      # High-level coordination
└── mcp_server.py                # MCP server with tools
```

## Features

### 1. Real API Integration
- **Google Ads API v24** - Production gRPC integration
- **OAuth 2.0** - Installed app credentials with token refresh
- **No mock data** - All operations use real API calls

### 2. Resilience Patterns
- **Circuit Breaker** - Opens after 5 failures, resets after 60s
- **Retry with Exponential Backoff** - 3 attempts, 1s → 30s max
- **Rate Limiting** - Token bucket (10 req/s default)
- **Response Caching** - 1 hour TTL

### 3. Services Layer

#### CampaignService
- Create campaigns with validation
- Update campaign settings
- Manage budgets
- Bulk operations

#### ContentOptimizer
- A/B testing analysis (real metrics)
- CTR/CPC optimization
- Performance recommendations
- Health score calculation

#### AnalyticsService
- Real-time metrics collection
- ROI calculation
- Performance tracking
- Trend analysis
- Custom reporting

### 4. MCP Server
- `create_campaign` - Create new campaigns
- `get_campaign_metrics` - Fetch performance data
- `list_campaigns` - List all campaigns
- `update_campaign_status` - Enable/pause/remove campaigns

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `google-ads>=24.0.0` - Google Ads API
- `google-auth>=2.0.0` - OAuth 2.0
- `httpx>=0.27.0` - HTTP client
- `tenacity>=8.2.0` - Retry logic
- `pybreaker>=1.0.0` - Circuit breaker
- `aiolimiter>=1.1.0` - Rate limiting
- `aiocache>=0.12.0` - Caching
- `prometheus-client>=0.20.0` - Metrics
- `structlog>=24.1.0` - Logging
- `mcp>=1.0.0` - MCP framework
- `fastmcp>=0.2.0` - FastMCP

### 2. Configure Environment

Create `.env` file:

```bash
# Google Ads API Credentials
ADS_GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
ADS_GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
ADS_GOOGLE_ADS_CLIENT_SECRET=your_client_secret
ADS_GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
ADS_GOOGLE_ADS_CUSTOMER_ID=1234567890
ADS_GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890  # Optional

# Rate Limiting
ADS_RATE_LIMIT_CAPACITY=10
ADS_RATE_LIMIT_REFILL=1.0

# Circuit Breaker
ADS_CIRCUIT_BREAKER_FAIL_MAX=5
ADS_CIRCUIT_BREAKER_RESET_TIMEOUT=60

# Caching
ADS_CACHE_ENABLED=true
ADS_CACHE_TTL=3600

# Logging
ADS_LOG_API_REQUESTS=true
ADS_LOG_API_RESPONSES=false
```

### 3. Get Google Ads Credentials

1. **Developer Token**: Apply at https://ads.google.com/aw/apicenter
2. **OAuth Credentials**: Create at https://console.cloud.google.com/apis/credentials
3. **Refresh Token**: Use `google-ads-python` authentication flow

## Usage

### Campaign Service

```python
from AIM.src.aim.subagents.ads.services.campaign_service import CampaignService
from AIM.src.aim.subagents.ads.config.settings import AdsSettings

# Initialize
settings = AdsSettings()
service = CampaignService(settings=settings)

# Create campaign
campaign = await service.create_campaign_with_validation(
    name="Summer Sale 2026",
    budget_usd=50.0,
    channel_type="SEARCH",
    status="PAUSED",
)

print(f"Campaign created: {campaign['resource_name']}")
print(f"Campaign ID: {campaign['resource_name'].split('/')[-1]}")

# Get campaign summary
summary = await service.get_campaign_summary(
    campaign_id="111111",
    include_metrics=True,
)

print(f"Impressions: {summary['metrics']['impressions']}")
print(f"Clicks: {summary['metrics']['clicks']}")
print(f"CTR: {summary['metrics']['ctr']}%")

# Close service
service.close()
```

### Content Optimizer

```python
from AIM.src.aim.subagents.ads.services.content_optimizer import ContentOptimizer

# Initialize
optimizer = ContentOptimizer(settings=settings)

# Analyze performance
analysis = await optimizer.analyze_campaign_performance(
    campaign_id="111111",
    date_range="LAST_30_DAYS",
)

print(f"Health Score: {analysis['overall_health']['score']}/100")
print(f"Status: {analysis['overall_health']['status']}")

# Get optimization suggestions
suggestions = await optimizer.suggest_optimizations(
    campaign_id="111111",
)

print("Quick Wins:")
for win in suggestions["quick_wins"]:
    print(f"  - {win['action']}: {win['description']}")

# Compare campaigns (A/B testing)
comparison = await optimizer.compare_campaigns(
    campaign_ids=["111111", "222222"],
    date_range="LAST_30_DAYS",
)

print(f"Winner: {comparison['winner']['campaign_name']}")
print(f"Health Score: {comparison['winner']['health_score']}")

optimizer.close()
```

### Analytics Service

```python
from AIM.src.aim.subagents.ads.services.analytics_service import AnalyticsService

# Initialize
analytics = AnalyticsService(settings=settings)

# Get performance metrics
performance = await analytics.get_campaign_performance(
    campaign_id="111111",
    date_range="LAST_30_DAYS",
)

print(f"Impressions: {performance['raw_metrics']['impressions']}")
print(f"Clicks: {performance['raw_metrics']['clicks']}")
print(f"Cost: ${performance['raw_metrics']['cost_usd']}")
print(f"Conversions: {performance['raw_metrics']['conversions']}")
print(f"ROI: {performance['business_metrics']['roi']}%")
print(f"ROAS: {performance['business_metrics']['roas']}")

# Calculate ROI
roi_analysis = await analytics.calculate_roi(
    campaign_id="111111",
    date_range="LAST_30_DAYS",
)

print(f"Total Cost: ${roi_analysis['financial_summary']['total_cost']}")
print(f"Total Revenue: ${roi_analysis['financial_summary']['total_revenue']}")
print(f"Total Profit: ${roi_analysis['financial_summary']['total_profit']}")
print(f"ROI: {roi_analysis['financial_summary']['roi_percentage']}%")

# Generate report
report = await analytics.generate_performance_report(
    campaign_ids=["111111", "222222", "333333"],
    date_range="LAST_30_DAYS",
)

print(f"Total Campaigns: {len(report['campaigns'])}")
print(f"Total Cost: ${report['summary']['raw_metrics']['cost_usd']}")
print(f"Total ROI: {report['summary']['business_metrics']['roi']}%")

analytics.close()
```

## Testing

```bash
# Run all tests
pytest AIM/tests/subagents/ads/ -v

# Run specific test file
pytest AIM/tests/subagents/ads/services/test_campaign_service.py -v

# Run with coverage
pytest AIM/tests/subagents/ads/ --cov=AIM/src/aim/subagents/ads
```

Test coverage:
- `test_campaign_service.py` - 11 tests
- `test_content_optimizer.py` - 9 tests
- `test_analytics_service.py` - 10 tests
- **Total: 30 tests, ~986 lines**

## Monitoring

### Prometheus Metrics

Available metrics:
- `ads_api_requests_total` - Total API requests
- `ads_api_request_duration_seconds` - Request duration
- `ads_circuit_breaker_state_changes` - Circuit breaker events

### Structured Logging

All operations logged with context via `structlog`.

## Cost Analysis

### API Costs
- Google Ads API: **Free** (no per-request charges)
- Rate limits: 15,000 requests/day per developer token

### Typical Usage
- Campaign creation: 2 API calls
- Metrics fetch: 1 API call
- Optimization analysis: 1-2 API calls

## Production Checklist

- [ ] OAuth credentials configured
- [ ] Developer token approved
- [ ] Rate limits configured
- [ ] Circuit breaker tuned
- [ ] Caching enabled
- [ ] Monitoring setup
- [ ] Tests passing (30+ tests)

## References

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [google-ads-python](https://github.com/googleads/google-ads-python)
- [MCP Protocol](https://modelcontextprotocol.io/)
