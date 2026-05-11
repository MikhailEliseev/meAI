"""Tests for base API client with resilience patterns"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pybreaker import CircuitBreakerError

from AIM.src.aim.subagents.api_clients.base import (
    APIClientBase,
    TokenBucketRateLimiter,
)


class MockAPIClient(APIClientBase):
    """Mock API client for testing"""

    async def expand_keywords(
        self,
        seed_keyword: str,
        max_keywords: int = 100,
        min_volume: int = 10,
        max_cost_usd: float = 5.0,
    ):
        return []


@pytest.fixture
def mock_client():
    """Create mock API client"""
    client = MockAPIClient(
        api_key="test_key",
        base_url="https://api.example.com",
        rate_limit_capacity=5,
        rate_limit_refill=1.0,
        cache_ttl=60,
    )
    yield client
    asyncio.run(client.close())


@pytest.mark.asyncio
async def test_token_bucket_rate_limiter():
    """Test token bucket rate limiter enforces rate limits"""
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate=1.0)

    # Should allow 3 immediate requests
    start = time.time()
    await limiter.acquire(1)
    await limiter.acquire(1)
    await limiter.acquire(1)
    elapsed = time.time() - start

    # Should be nearly instant
    assert elapsed < 0.1

    # 4th request should wait ~1 second
    start = time.time()
    await limiter.acquire(1)
    elapsed = time.time() - start

    # Should wait for refill
    assert elapsed >= 0.9  # Allow some timing variance


@pytest.mark.asyncio
async def test_rate_limiting_enforced(mock_client):
    """Test rate limiting is enforced on API calls"""
    with patch.object(mock_client.client, "request") as mock_request:
        mock_request.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"result": "ok"},
        )
        mock_request.return_value.raise_for_status = MagicMock()

        # Make 6 requests (capacity is 5)
        start = time.time()
        for _ in range(6):
            await mock_client._make_request("GET", "/test")
        elapsed = time.time() - start

        # Should take at least 1 second due to rate limiting
        assert elapsed >= 0.9


@pytest.mark.asyncio
async def test_circuit_breaker_configuration(mock_client):
    """Test circuit breaker is configured with correct parameters"""
    # Verify circuit breaker configuration
    assert mock_client.circuit_breaker.fail_max == 5
    assert mock_client.circuit_breaker.reset_timeout == 60
    assert mock_client.circuit_breaker.name == "MockAPIClient"

    # Verify circuit breaker is initially closed
    from pybreaker import STATE_CLOSED
    assert mock_client.circuit_breaker.current_state == STATE_CLOSED


@pytest.mark.asyncio
async def test_caching_reduces_api_calls(mock_client):
    """Test caching reduces duplicate API calls"""
    with patch.object(mock_client.client, "request") as mock_request:
        mock_response = AsyncMock(
            status_code=200,
            json=lambda: {"result": "cached_data"},
        )
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        # First request should hit API
        result1 = await mock_client._make_request(
            "GET", "/test", params={"q": "test"}
        )
        assert result1 == {"result": "cached_data"}
        assert mock_request.call_count == 1

        # Second identical request should use cache
        result2 = await mock_client._make_request(
            "GET", "/test", params={"q": "test"}
        )
        assert result2 == {"result": "cached_data"}
        assert mock_request.call_count == 1  # No additional call


@pytest.mark.asyncio
async def test_retry_with_exponential_backoff(mock_client):
    """Test retry with exponential backoff on failures"""
    with patch.object(mock_client.client, "request") as mock_request:
        # Fail twice, then succeed
        mock_request.side_effect = [
            httpx.HTTPError("Temporary error"),
            httpx.HTTPError("Temporary error"),
            AsyncMock(
                status_code=200,
                json=lambda: {"result": "success"},
                raise_for_status=MagicMock(),
            ),
        ]

        start = time.time()
        result = await mock_client._make_request("GET", "/test")
        elapsed = time.time() - start

        # Should succeed after retries
        assert result == {"result": "success"}
        assert mock_request.call_count == 3

        # Should have waited for exponential backoff (1s + 2s = ~3s)
        assert elapsed >= 2.0


@pytest.mark.asyncio
async def test_metrics_tracked(mock_client):
    """Test Prometheus metrics are tracked"""
    from AIM.src.aim.subagents.api_clients.base import api_calls_total

    with patch.object(mock_client.client, "request") as mock_request:
        mock_response = AsyncMock(
            status_code=200,
            json=lambda: {"result": "ok"},
        )
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        # Get initial count
        initial_count = api_calls_total.labels(
            client="MockAPIClient",
            endpoint="/test",
            status="success",
        )._value.get()

        # Make request
        await mock_client._make_request("GET", "/test")

        # Check metric incremented
        final_count = api_calls_total.labels(
            client="MockAPIClient",
            endpoint="/test",
            status="success",
        )._value.get()

        assert final_count == initial_count + 1


@pytest.mark.asyncio
async def test_structured_logging(mock_client, capsys):
    """Test structured logging is used"""
    with patch.object(mock_client.client, "request") as mock_request:
        mock_response = AsyncMock(
            status_code=200,
            json=lambda: {"result": "ok"},
        )
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        await mock_client._make_request("GET", "/test")

        # Check stdout contains structured log output
        captured = capsys.readouterr()
        assert "api_request_success" in captured.out
        assert "endpoint=/test" in captured.out
