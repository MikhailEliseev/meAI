"""Tests for LLM Client with cost tracking, rate limiting, and caching."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aim.ai.llm.client import BudgetExceededError, LLMClient, RateLimitError
from aim.ai.llm.providers.base import LLMProviderError
from aim.ai.llm.schemas import LLMMessage, LLMResponse


@pytest.fixture
def mock_provider():
    """Mock LLM provider."""
    provider = AsyncMock()
    provider.generate.return_value = LLMResponse(
        content="Test response",
        model="claude/opus",
        provider="claude",
        finish_reason="stop",
        usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        cost_usd=0.01,
        cached=False,
        latency_ms=500,
        metadata={},
    )
    return provider


@pytest.fixture
def client(mock_provider):
    """LLM client with mock provider."""
    return LLMClient(
        provider=mock_provider,
        max_cost_per_request=1.0,
        daily_budget=10.0,
        monthly_budget=100.0,
        rate_limit_rpm=60,
        cache_ttl=3600,
        enable_cache=True,
    )


@pytest.mark.asyncio
async def test_generate_success(client, mock_provider):
    """Test successful generation."""
    messages = [LLMMessage(role="user", content="Hello")]

    response = await client.generate(messages)

    assert response.content == "Test response"
    assert response.model == "claude/opus"
    assert response.cost_usd == 0.01
    assert client.request_count == 1
    assert client.total_cost == 0.01
    mock_provider.generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_with_system_prompt(client, mock_provider):
    """Test generation with system prompt."""
    messages = [LLMMessage(role="user", content="Hello")]
    system_prompt = "You are a helpful assistant"

    await client.generate(messages, system_prompt=system_prompt)

    call_args = mock_provider.generate.call_args[0][0]
    assert call_args.system_prompt == system_prompt


@pytest.mark.asyncio
async def test_generate_text_convenience(client, mock_provider):
    """Test generate_text convenience method."""
    text = await client.generate_text("Hello")

    assert text == "Test response"
    mock_provider.generate.assert_called_once()


@pytest.mark.asyncio
async def test_cache_hit(client, mock_provider):
    """Test cache hit on duplicate request."""
    messages = [LLMMessage(role="user", content="Hello")]

    # First request
    response1 = await client.generate(messages)
    assert client.cache_misses == 1
    assert client.cache_hits == 0

    # Second request (should hit cache)
    response2 = await client.generate(messages)
    assert client.cache_misses == 1
    assert client.cache_hits == 1
    assert response2.cached is True
    assert response2.content == response1.content

    # Provider called only once
    assert mock_provider.generate.call_count == 1


@pytest.mark.asyncio
async def test_cache_bypass(client, mock_provider):
    """Test cache bypass flag."""
    messages = [LLMMessage(role="user", content="Hello")]

    # First request
    await client.generate(messages)

    # Second request with bypass_cache
    await client.generate(messages, bypass_cache=True)

    # Provider called twice
    assert mock_provider.generate.call_count == 2
    assert client.cache_misses == 2


@pytest.mark.asyncio
async def test_cache_expiration(client, mock_provider):
    """Test cache expiration after TTL."""
    client.cache_ttl = 1  # 1 second TTL
    messages = [LLMMessage(role="user", content="Hello")]

    # First request
    await client.generate(messages)

    # Wait for cache to expire
    await asyncio.sleep(1.1)

    # Second request (cache expired)
    await client.generate(messages)

    # Provider called twice
    assert mock_provider.generate.call_count == 2


@pytest.mark.asyncio
async def test_cost_per_request_exceeded(client, mock_provider):
    """Test max cost per request enforcement."""
    mock_provider.generate.return_value.cost_usd = 2.0  # Exceeds max_cost_per_request=1.0
    messages = [LLMMessage(role="user", content="Hello")]

    with pytest.raises(BudgetExceededError) as exc_info:
        await client.generate(messages)

    assert "Request cost $2.0000 exceeds max $1.0" in str(exc_info.value)


@pytest.mark.asyncio
async def test_daily_budget_exceeded(client, mock_provider):
    """Test daily budget enforcement."""
    client.daily_budget = 0.02
    messages = [LLMMessage(role="user", content="Hello")]

    # First request (cost $0.01)
    await client.generate(messages)

    # Second request (cost $0.01, total $0.02)
    await client.generate(messages, bypass_cache=True)

    # Third request (would exceed daily budget)
    with pytest.raises(BudgetExceededError) as exc_info:
        await client.generate(messages, bypass_cache=True)

    assert "Daily budget" in str(exc_info.value)


@pytest.mark.asyncio
async def test_monthly_budget_exceeded(client, mock_provider):
    """Test monthly budget enforcement."""
    client.monthly_budget = 0.02
    messages = [LLMMessage(role="user", content="Hello")]

    # First request (cost $0.01)
    await client.generate(messages)

    # Second request (cost $0.01, total $0.02)
    await client.generate(messages, bypass_cache=True)

    # Third request (would exceed monthly budget)
    with pytest.raises(BudgetExceededError) as exc_info:
        await client.generate(messages, bypass_cache=True)

    assert "Monthly budget" in str(exc_info.value)


@pytest.mark.asyncio
async def test_rate_limit_enforcement(client):
    """Test rate limiting with token bucket."""
    client.rate_limit_rpm = 2  # 2 requests per minute
    client.tokens = 2  # Start with 2 tokens
    messages = [LLMMessage(role="user", content="Hello")]

    # First request (1 token left)
    await client.generate(messages)

    # Second request (0 tokens left)
    await client.generate(messages, bypass_cache=True)

    # Third request (no tokens, should raise)
    with pytest.raises(RateLimitError) as exc_info:
        await client.generate(messages, bypass_cache=True)

    assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_rate_limit_refill(client):
    """Test rate limiter token refill."""
    client.rate_limit_rpm = 60  # 1 request per second
    client.tokens = 0  # No tokens
    messages = [LLMMessage(role="user", content="Hello")]

    # Wait for refill (1 second = 1 token)
    await asyncio.sleep(1.1)

    # Should succeed after refill
    await client.generate(messages)
    assert client.request_count == 1


@pytest.mark.asyncio
async def test_provider_error_handling(client, mock_provider):
    """Test provider error handling."""
    mock_provider.generate.side_effect = LLMProviderError(
        message="API error",
        provider="omnirouter",
        error_type="server_error",
        retryable=True,
    )
    messages = [LLMMessage(role="user", content="Hello")]

    with pytest.raises(LLMProviderError) as exc_info:
        await client.generate(messages)

    assert exc_info.value.provider == "omnirouter"
    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_metrics(client, mock_provider):
    """Test metrics collection."""
    messages = [LLMMessage(role="user", content="Hello")]

    # First request
    await client.generate(messages)

    # Second request (cache hit)
    await client.generate(messages)

    metrics = client.get_metrics()

    assert metrics["request_count"] == 1  # Only 1 actual request
    assert metrics["cache_hits"] == 1
    assert metrics["cache_misses"] == 1
    assert metrics["cache_hit_rate"] == 0.5
    assert metrics["total_cost"] == 0.01
    assert metrics["cache_size"] == 1


@pytest.mark.asyncio
async def test_budget_reset_daily(client):
    """Test daily budget reset."""
    client.daily_cost = 5.0
    client.last_reset_day = "2026-01-01"

    # Trigger reset
    with patch("time.strftime", return_value="2026-01-02"):
        client._reset_budgets()

    assert client.daily_cost == 0.0
    assert client.last_reset_day == "2026-01-02"


@pytest.mark.asyncio
async def test_budget_reset_monthly(client):
    """Test monthly budget reset."""
    client.monthly_cost = 50.0
    client.last_reset_month = "2026-01"

    # Trigger reset
    with patch("time.strftime", side_effect=["2026-02-01", "2026-02"]):
        client._reset_budgets()

    assert client.monthly_cost == 0.0
    assert client.last_reset_month == "2026-02"
