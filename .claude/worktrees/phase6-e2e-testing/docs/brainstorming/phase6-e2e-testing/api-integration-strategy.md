# API Integration Testing Strategy

**Expert:** API Integration Specialist  
**Date:** 2026-05-14  
**Focus:** VCR strategy, API mocking, cost optimization

---

## 1. VCR Configuration

### 1.1 pytest-vcr Setup

**Installation:**
```bash
pip install pytest-vcr>=1.0.2
pip install vcrpy>=6.0.0
```

**Configuration (`AIM/tests/conftest.py`):**
```python
"""Pytest configuration with VCR setup"""

import pytest
from pathlib import Path

# VCR cassettes directory
CASSETTES_DIR = Path(__file__).parent / "cassettes"
CASSETTES_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for all tests"""
    return {
        # Cassette storage
        "cassette_library_dir": str(CASSETTES_DIR),
        
        # Record mode: 'once' (record if missing, replay if exists)
        "record_mode": "once",
        
        # Match requests by: method, scheme, host, port, path, query
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        
        # Filter sensitive data
        "filter_headers": [
            ("authorization", "REDACTED"),
            ("x-api-key", "REDACTED"),
        ],
        "filter_query_parameters": [
            ("key", "REDACTED"),
            ("api_key", "REDACTED"),
        ],
        
        # Decode compressed responses
        "decode_compressed_response": True,
        
        # Allow playback repeats
        "allow_playback_repeats": True,
        
        # Serializer (yaml for readability)
        "serializer": "yaml",
    }

@pytest.fixture
def vcr_cassette_name(request):
    """Generate cassette name from test name"""
    # Format: test_module/test_class/test_method.yaml
    parts = []
    
    if request.module:
        parts.append(request.module.__name__.split(".")[-1])
    
    if request.cls:
        parts.append(request.cls.__name__)
    
    parts.append(request.node.name)
    
    return "/".join(parts)
```

### 1.2 Cassette Organization

**Directory Structure:**
```
AIM/tests/cassettes/
├── api_clients/
│   ├── semrush/
│   │   ├── test_keyword_expansion_success.yaml
│   │   ├── test_budget_guard.yaml
│   │   ├── test_zero_volume_retry.yaml
│   │   └── test_pagination.yaml
│   ├── ahrefs/
│   │   ├── test_keyword_expansion_fallback.yaml
│   │   ├── test_difficulty_normalization.yaml
│   │   └── test_parent_topic_detection.yaml
│   ├── ga4/
│   │   ├── test_fetch_metrics.yaml
│   │   ├── test_conversions_api.yaml
│   │   └── test_batch_requests.yaml
│   └── yandex_metrica/
│       ├── test_fetch_traffic.yaml
│       ├── test_goals_tracking.yaml
│       └── test_ecommerce_data.yaml
└── integration/
    ├── test_fallback_chain_semrush_to_ahrefs.yaml
    └── test_multi_source_aggregation.yaml
```

### 1.3 Cassette Update Strategy

**Manual Update (when API changes):**
```bash
# Delete specific cassette
rm AIM/tests/cassettes/api_clients/semrush/test_keyword_expansion_success.yaml

# Re-record with real API
SEMRUSH_API_KEY=real_key pytest AIM/tests/subagents/api_clients/test_semrush.py::test_keyword_expansion_success -v

# Verify cassette created
ls -lh AIM/tests/cassettes/api_clients/semrush/
```

**Automated Update (CI/CD):**
```yaml
# .github/workflows/update-cassettes.yml
name: Update VCR Cassettes

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:  # Manual trigger

jobs:
  update-cassettes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Delete old cassettes
        run: rm -rf AIM/tests/cassettes/
      
      - name: Re-record cassettes
        env:
          SEMRUSH_API_KEY: ${{ secrets.SEMRUSH_API_KEY }}
          AHREFS_API_KEY: ${{ secrets.AHREFS_API_KEY }}
          GA4_CREDENTIALS: ${{ secrets.GA4_CREDENTIALS }}
          YANDEX_METRICA_TOKEN: ${{ secrets.YANDEX_METRICA_TOKEN }}
        run: pytest AIM/tests/ -v --record-mode=all
      
      - name: Create PR with updated cassettes
        uses: peter-evans/create-pull-request@v5
        with:
          title: "chore: update VCR cassettes"
          body: "Automated weekly cassette update"
          branch: update-cassettes
```

---

## 2. Mock Data Management

### 2.1 Fixture Strategy

**Centralized Fixtures (`AIM/tests/fixtures/`):**

```python
# AIM/tests/fixtures/api_responses.py
"""Realistic API response fixtures"""

from typing import Any

# SEMrush responses
def semrush_keyword_response(
    seed: str = "dental implants",
    count: int = 5,
    min_volume: int = 1000,
) -> dict[str, Any]:
    """Generate realistic SEMrush response"""
    keywords = []
    for i in range(count):
        keywords.append({
            "Ph": f"{seed} {i}" if i > 0 else seed,
            "Nq": min_volume + (i * 500),
            "Cp": 10.0 + (i * 2.5),
            "Co": 0.5 + (i * 0.1),
            "Nr": 1000000 - (i * 100000),
            "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
        })
    
    return {"data": keywords}

# GA4 responses
def ga4_metrics_response(
    property_id: str = "123456789",
    date_range: tuple[str, str] = ("2026-05-01", "2026-05-14"),
) -> dict[str, Any]:
    """Generate realistic GA4 response"""
    return {
        "dimensionHeaders": [
            {"name": "date"},
            {"name": "pagePath"},
        ],
        "metricHeaders": [
            {"name": "sessions", "type": "TYPE_INTEGER"},
            {"name": "totalUsers", "type": "TYPE_INTEGER"},
            {"name": "screenPageViews", "type": "TYPE_INTEGER"},
            {"name": "bounceRate", "type": "TYPE_FLOAT"},
        ],
        "rows": [
            {
                "dimensionValues": [
                    {"value": "20260501"},
                    {"value": "/services/dental-implants"},
                ],
                "metricValues": [
                    {"value": "150"},
                    {"value": "120"},
                    {"value": "450"},
                    {"value": "0.35"},
                ],
            },
            {
                "dimensionValues": [
                    {"value": "20260502"},
                    {"value": "/services/dental-implants"},
                ],
                "metricValues": [
                    {"value": "180"},
                    {"value": "145"},
                    {"value": "540"},
                    {"value": "0.32"},
                ],
            },
        ],
        "rowCount": 2,
    }

# Yandex Metrica responses
def yandex_metrica_traffic_response(
    counter_id: str = "12345678",
) -> dict[str, Any]:
    """Generate realistic Yandex Metrica response"""
    return {
        "query": {
            "ids": [int(counter_id)],
            "dimensions": ["ym:s:date", "ym:s:startURL"],
            "metrics": ["ym:s:visits", "ym:s:users", "ym:s:pageviews"],
            "date1": "2026-05-01",
            "date2": "2026-05-14",
        },
        "data": [
            {
                "dimensions": [
                    {"name": "2026-05-01"},
                    {"name": "https://example.com/services/dental-implants"},
                ],
                "metrics": [150.0, 120.0, 450.0],
            },
            {
                "dimensions": [
                    {"name": "2026-05-02"},
                    {"name": "https://example.com/services/dental-implants"},
                ],
                "metrics": [180.0, 145.0, 540.0],
            },
        ],
        "total_rows": 2,
    }
```

### 2.2 Mock Data Consistency

**Validation Against Real Data:**

```python
# AIM/tests/fixtures/validators.py
"""Validate mock data matches real API schemas"""

from pydantic import ValidationError
from AIM.src.aim.subagents.schemas.api_responses import (
    SEMrushKeywordData,
    AhrefsKeywordData,
    GA4MetricsData,
    YandexMetricaData,
)

def validate_semrush_mock(mock_data: dict) -> bool:
    """Validate SEMrush mock matches real schema"""
    try:
        for row in mock_data["data"]:
            # Parse as if real API response
            keyword = row.get("Ph", "").strip()
            volume = int(row.get("Nq", 0))
            cpc = float(row.get("Cp", 0.0))
            competition = float(row.get("Co", 0.0))
            
            # Validate with Pydantic
            SEMrushKeywordData(
                keyword=keyword,
                volume=volume,
                cpc=cpc,
                competition=competition,
                trend=row.get("Td", ""),
            )
        return True
    except (ValidationError, ValueError, KeyError) as e:
        print(f"Mock validation failed: {e}")
        return False

# Run validation in tests
def test_mock_data_validity():
    """Ensure all mock data is valid"""
    from AIM.tests.fixtures.api_responses import (
        semrush_keyword_response,
        ga4_metrics_response,
        yandex_metrica_traffic_response,
    )
    
    assert validate_semrush_mock(semrush_keyword_response())
    # Add validators for other APIs
```

---

## 3. Resilience Pattern Testing

### 3.1 Circuit Breaker Lifecycle Testing

```python
# AIM/tests/subagents/api_clients/test_circuit_breaker.py
"""Test circuit breaker lifecycle"""

import pytest
from unittest.mock import patch, AsyncMock
from pybreaker import STATE_CLOSED, STATE_OPEN, STATE_HALF_OPEN
import httpx

from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after fail_max failures"""
    client = SEMrushClient(api_key="test_key")
    
    with patch.object(client.client, "request") as mock_request:
        # Simulate 5 consecutive failures
        mock_request.side_effect = httpx.HTTPError("API down")
        
        # Make 5 requests (fail_max=5)
        for i in range(5):
            try:
                await client._make_request("GET", "/test")
            except:
                pass
        
        # Circuit breaker should be open
        assert client.circuit_breaker.current_state == STATE_OPEN
    
    await client.close()

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker transitions to half-open after reset_timeout"""
    client = SEMrushClient(api_key="test_key")
    
    # Manually open circuit breaker
    client.circuit_breaker._state = STATE_OPEN
    client.circuit_breaker._opened = time.time() - 61  # 61 seconds ago
    
    with patch.object(client.client, "request") as mock_request:
        mock_response = AsyncMock(
            status_code=200,
            json=lambda: {"result": "ok"},
        )
        mock_response.raise_for_status = lambda: None
        mock_request.return_value = mock_response
        
        # Should transition to half-open and allow request
        result = await client._make_request("GET", "/test")
        
        assert result == {"result": "ok"}
        assert client.circuit_breaker.current_state == STATE_CLOSED
    
    await client.close()
```

### 3.2 Retry Logic Testing

```python
# AIM/tests/subagents/api_clients/test_retry.py
"""Test retry with exponential backoff"""

import pytest
import time
from unittest.mock import patch, AsyncMock
import httpx

from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient

@pytest.mark.asyncio
async def test_retry_exponential_backoff_timing():
    """Test retry waits with exponential backoff"""
    client = SEMrushClient(api_key="test_key")
    
    with patch.object(client.client, "request") as mock_request:
        # Fail twice, succeed third time
        mock_request.side_effect = [
            httpx.HTTPError("Temporary error"),
            httpx.HTTPError("Temporary error"),
            AsyncMock(
                status_code=200,
                json=lambda: {"result": "success"},
                raise_for_status=lambda: None,
            ),
        ]
        
        start = time.time()
        result = await client._make_request("GET", "/test")
        elapsed = time.time() - start
        
        # Should succeed after 3 attempts
        assert result == {"result": "success"}
        assert mock_request.call_count == 3
        
        # Exponential backoff: 1s + 2s = 3s (with some variance)
        assert 2.5 <= elapsed <= 4.0
    
    await client.close()
```

### 3.3 Rate Limiting Testing

```python
# AIM/tests/subagents/api_clients/test_rate_limiting.py
"""Test token bucket rate limiting"""

import pytest
import time
from AIM.src.aim.subagents.api_clients.base import TokenBucketRateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_allows_burst():
    """Test rate limiter allows burst up to capacity"""
    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=1.0)
    
    # Should allow 5 immediate requests
    start = time.time()
    for _ in range(5):
        await limiter.acquire(1)
    elapsed = time.time() - start
    
    # Should be nearly instant (< 100ms)
    assert elapsed < 0.1
```

---

## 4. Cost Optimization

### 4.1 VCR Replay (Zero Cost)

**Default Test Mode:**
```python
# AIM/tests/conftest.py (addition)

@pytest.fixture(autouse=True)
def ensure_vcr_replay(request, vcr):
    """Ensure tests use VCR replay by default (zero cost)"""
    # Skip for tests marked with @pytest.mark.live_api
    if "live_api" in request.keywords:
        return
    
    # Verify VCR is in replay mode
    if vcr.record_mode not in ["none", "once"]:
        pytest.fail(
            f"Test {request.node.name} is not using VCR replay. "
            "This will incur API costs. Use @pytest.mark.live_api if intentional."
        )
```

### 4.2 Budget Guard Testing

```python
# AIM/tests/subagents/api_clients/test_budget.py
"""Test budget guards prevent cost overruns"""

import pytest
from unittest.mock import patch
from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient
from AIM.tests.fixtures.api_responses import semrush_keyword_response

@pytest.mark.asyncio
@pytest.mark.vcr
async def test_budget_guard_stops_at_limit():
    """Test budget guard stops at max_cost_usd"""
    client = SEMrushClient(api_key="test_key")
    
    with patch.object(client, "_make_request") as mock_request:
        # Return full page each time (would trigger pagination)
        mock_request.return_value = semrush_keyword_response(count=100)
        
        keywords = await client.expand_keywords(
            seed_keyword="test",
            max_keywords=1000,  # Request many
            min_volume=10,
            max_cost_usd=0.03,  # But limit budget to 3 requests
        )
        
        # Should stop after 3 requests ($0.01 each)
        assert mock_request.call_count <= 3
        assert len(keywords) <= 300
    
    await client.close()
```

---

## 5. Implementation Examples

### 5.1 Complete Test with VCR

```python
# AIM/tests/subagents/api_clients/test_semrush_vcr.py
"""SEMrush tests with VCR (zero cost)"""

import pytest
from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient

@pytest.mark.vcr
@pytest.mark.asyncio
async def test_keyword_expansion_with_vcr():
    """Test keyword expansion using VCR cassette (zero cost)"""
    client = SEMrushClient(api_key="test_key")
    
    # First run: records to cassette
    # Subsequent runs: replays from cassette (zero cost)
    keywords = await client.expand_keywords(
        seed_keyword="dental implants",
        max_keywords=10,
        min_volume=100,
        max_cost_usd=1.0,
    )
    
    # Assertions
    assert len(keywords) == 10
    assert all(kw["volume"] >= 100 for kw in keywords)
    assert all("keyword" in kw for kw in keywords)
    assert all("difficulty" in kw for kw in keywords)
    assert all("intent" in kw for kw in keywords)
    
    await client.close()
```

### 5.2 Cassette Example

```yaml
# AIM/tests/cassettes/api_clients/semrush/test_keyword_expansion_with_vcr.yaml
version: 1
interactions:
- request:
    method: GET
    uri: https://api.semrush.com/analytics/v1/?type=phrase_related&key=REDACTED&phrase=dental+implants&database=us&display_limit=100&display_offset=0&export_columns=Ph%2CNq%2CCp%2CCo%2CNr%2CTd&display_filter=%2B%7CNq%7CGt%7C100
    body: null
    headers:
      accept:
      - '*/*'
      accept-encoding:
      - gzip, deflate
      connection:
      - keep-alive
      user-agent:
      - python-httpx/0.27.0
  response:
    status:
      code: 200
      message: OK
    headers:
      content-type:
      - application/json
      cache-control:
      - no-cache
    body:
      string: '{"data":[{"Ph":"dental implants","Nq":5000,"Cp":12.50,"Co":0.85,"Nr":1500000,"Td":"0,0,0,0,0,0,0,0,0,0,0,0"},{"Ph":"dental implants cost","Nq":3000,"Cp":15.00,"Co":0.90,"Nr":800000,"Td":"0,0,0,0,0,0,0,0,0,0,0,0"}]}'
```

---

## Summary

**Key Benefits:**

1. **Zero Cost Testing:** VCR replay eliminates API costs for 99% of test runs
2. **Deterministic:** Same cassette = same results every time
3. **Fast:** No network calls = tests run in milliseconds
4. **Realistic:** Cassettes contain real API responses
5. **Safe:** Sensitive data filtered automatically

**Implementation Priority:**

1. Week 1: Setup pytest-vcr configuration
2. Week 2: Record cassettes for all API clients
3. Week 3: Implement resilience pattern tests
4. Week 4: Add cost tracking and budget guards
