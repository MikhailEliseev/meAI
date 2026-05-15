"""Tests for Omni-Router provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from aim.ai.llm.providers.base import LLMProviderError
from aim.ai.llm.providers.omnirouter import OmniRouterProvider
from aim.ai.llm.schemas import LLMMessage, LLMRequest


@pytest.fixture
def provider():
    """Omni-Router provider instance."""
    return OmniRouterProvider(
        base_url="http://localhost:8000",
        api_key="test-key",
        timeout=60,
    )


@pytest.fixture
def mock_response():
    """Mock successful API response."""
    return {
        "choices": [
            {
                "message": {"content": "Test response"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
        "model": "claude/opus",
        "cached": False,
        "metadata": {},
    }


@pytest.mark.asyncio
async def test_generate_success(provider, mock_response):
    """Test successful generation."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        temperature=0.7,
        max_tokens=4096,
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )

        response = await provider.generate(request)

        assert response.content == "Test response"
        assert response.model == "claude/opus"
        assert response.provider == "claude"
        assert response.finish_reason == "stop"
        assert response.usage["input_tokens"] == 100
        assert response.usage["output_tokens"] == 50
        assert response.cost_usd > 0
        assert response.cached is False


@pytest.mark.asyncio
async def test_generate_with_system_prompt(provider, mock_response):
    """Test generation with system prompt."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        system_prompt="You are a helpful assistant",
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )

        await provider.generate(request)

        # Check that system prompt was added to messages
        call_args = mock_post.call_args[1]["json"]
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][0]["content"] == "You are a helpful assistant"


@pytest.mark.asyncio
async def test_generate_with_model_preference(provider, mock_response):
    """Test generation with model preference."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model="claude/opus",
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )

        await provider.generate(request)

        call_args = mock_post.call_args[1]["json"]
        assert call_args["model"] == "claude/opus"


@pytest.mark.asyncio
async def test_generate_with_response_format(provider, mock_response):
    """Test generation with structured output format."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        response_format={"type": "json_object"},
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )

        await provider.generate(request)

        call_args = mock_post.call_args[1]["json"]
        assert call_args["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_generate_with_metadata(provider, mock_response):
    """Test generation with metadata."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        metadata={"user_id": "123", "session_id": "abc"},
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )

        await provider.generate(request)

        call_args = mock_post.call_args[1]["json"]
        assert call_args["metadata"] == {"user_id": "123", "session_id": "abc"}


@pytest.mark.asyncio
async def test_generate_with_api_key(provider, mock_response):
    """Test that API key is sent in headers."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )

        await provider.generate(request)

        call_args = mock_post.call_args[1]["headers"]
        assert call_args["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_generate_http_error(provider):
    """Test HTTP error handling."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_response.json.return_value = {"error": "Internal server error"}

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(request)

        assert exc_info.value.provider == "omnirouter"
        assert exc_info.value.error_type == "server_error"
        assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_generate_rate_limit_error(provider):
    """Test rate limit error handling."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_response.json.return_value = {"error": "Rate limit exceeded"}

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(request)

        assert exc_info.value.error_type == "rate_limit"
        assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_generate_authentication_error(provider):
    """Test authentication error handling."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid API key"
    mock_response.json.return_value = {"error": "Invalid API key"}

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(request)

        assert exc_info.value.error_type == "authentication"
        assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_generate_timeout_error(provider):
    """Test timeout error handling."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(request)

        assert exc_info.value.error_type == "timeout"
        assert exc_info.value.retryable is True
        assert "timeout after 60s" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_generate_connection_error(provider):
    """Test connection error handling."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    with patch.object(provider.client, "post") as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(request)

        assert exc_info.value.error_type == "connection"
        assert exc_info.value.retryable is True
        assert "Cannot connect to Omni-Router" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_calculate_cost():
    """Test cost calculation."""
    provider = OmniRouterProvider()

    # Test with typical usage
    cost = provider.calculate_cost(input_tokens=1000, output_tokens=500)

    # Input: 1000 tokens * $3/MTok = $0.003
    # Output: 500 tokens * $15/MTok = $0.0075
    # Total: $0.0105
    assert cost == pytest.approx(0.0105, rel=1e-6)


@pytest.mark.asyncio
async def test_get_provider_name():
    """Test provider name."""
    provider = OmniRouterProvider()
    assert provider.get_provider_name() == "omnirouter"


@pytest.mark.asyncio
async def test_get_model_name():
    """Test default model name."""
    provider = OmniRouterProvider()
    assert provider.get_model_name() == "omnirouter/auto"


@pytest.mark.asyncio
async def test_close(provider):
    """Test client cleanup."""
    with patch.object(provider.client, "aclose") as mock_close:
        await provider.close()
        mock_close.assert_called_once()
