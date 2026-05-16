"""
Tests for LLM schemas.
"""

import pytest
from pydantic import ValidationError

from aim.ai.llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMProvider,
    LLMModel,
    LLMError,
    LLMProviderError,
    LLMCostEstimate,
)


class TestLLMRequest:
    """Test LLMRequest schema."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = LLMRequest(
            prompt="What is AI?",
            system_prompt="You are a helpful assistant.",
            model="claude-sonnet-4",
            max_tokens=1000,
            temperature=0.7,
        )
        
        assert request.prompt == "What is AI?"
        assert request.system_prompt == "You are a helpful assistant."
        assert request.model == "claude-sonnet-4"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7
    
    def test_default_values(self):
        """Test default values."""
        request = LLMRequest(prompt="Test")
        
        assert request.model == "claude-sonnet-4"
        assert request.max_tokens == 4096
        assert request.temperature == 0.7
        assert request.system_prompt is None
        assert request.response_format is None
    
    def test_empty_prompt_fails(self):
        """Test empty prompt validation."""
        with pytest.raises(ValidationError):
            LLMRequest(prompt="")
    
    def test_whitespace_prompt_fails(self):
        """Test whitespace-only prompt validation."""
        with pytest.raises(ValidationError):
            LLMRequest(prompt="   ")
    
    def test_invalid_model_fails(self):
        """Test invalid model validation."""
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Test", model="invalid-model")
    
    def test_max_tokens_validation(self):
        """Test max_tokens bounds."""
        # Valid
        request = LLMRequest(prompt="Test", max_tokens=1000)
        assert request.max_tokens == 1000
        
        # Too low
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Test", max_tokens=0)
        
        # Too high
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Test", max_tokens=300000)
    
    def test_temperature_validation(self):
        """Test temperature bounds."""
        # Valid
        request = LLMRequest(prompt="Test", temperature=1.0)
        assert request.temperature == 1.0
        
        # Too low
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Test", temperature=-0.1)
        
        # Too high
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Test", temperature=2.1)


class TestLLMResponse:
    """Test LLMResponse schema."""
    
    def test_valid_response(self):
        """Test valid response creation."""
        response = LLMResponse(
            content="AI is artificial intelligence.",
            model="claude-sonnet-4",
            provider=LLMProvider.ANTHROPIC,
            tokens_used=150,
            input_tokens=50,
            output_tokens=100,
            cost_usd=0.0015,
            cached=False,
            latency_ms=1200,
        )
        
        assert response.content == "AI is artificial intelligence."
        assert response.model == "claude-sonnet-4"
        assert response.provider == LLMProvider.ANTHROPIC
        assert response.tokens_used == 150
        assert response.cost_usd == 0.0015
        assert response.cached is False
    
    def test_cached_response(self):
        """Test cached response flag."""
        response = LLMResponse(
            content="Cached content",
            model="claude-sonnet-4",
            provider=LLMProvider.ANTHROPIC,
            tokens_used=100,
            input_tokens=50,
            output_tokens=50,
            cost_usd=0.0,
            cached=True,
            latency_ms=50,
            cache_key="abc123",
        )
        
        assert response.cached is True
        assert response.cache_key == "abc123"


class TestLLMProvider:
    """Test LLMProvider enum."""
    
    def test_provider_values(self):
        """Test provider enum values."""
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OPENAI.value == "openai"


class TestLLMModel:
    """Test LLMModel enum."""
    
    def test_claude_models(self):
        """Test Claude model values."""
        assert LLMModel.CLAUDE_OPUS.value == "claude-opus-4"
        assert LLMModel.CLAUDE_SONNET.value == "claude-sonnet-4"
        assert LLMModel.CLAUDE_HAIKU.value == "claude-haiku-4"
    
    def test_gpt_models(self):
        """Test GPT model values."""
        assert LLMModel.GPT4_TURBO.value == "gpt-4-turbo"
        assert LLMModel.GPT4.value == "gpt-4"
        assert LLMModel.GPT35_TURBO.value == "gpt-3.5-turbo"


class TestLLMErrors:
    """Test LLM error classes."""
    
    def test_llm_error(self):
        """Test base LLM error."""
        error = LLMError("Something went wrong")
        assert str(error) == "Something went wrong"
    
    def test_provider_error(self):
        """Test provider-specific error."""
        error = LLMProviderError(LLMProvider.ANTHROPIC, "API error")
        assert str(error) == "[anthropic] API error"
        assert error.provider == LLMProvider.ANTHROPIC


class TestLLMCostEstimate:
    """Test LLMCostEstimate schema."""
    
    def test_cost_estimate(self):
        """Test cost estimate creation."""
        estimate = LLMCostEstimate(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            input_tokens=1000,
            output_tokens=500,
            input_cost_usd=0.003,
            output_cost_usd=0.0075,
            total_cost_usd=0.0105,
        )
        
        assert estimate.provider == LLMProvider.ANTHROPIC
        assert estimate.total_cost_usd == 0.0105
