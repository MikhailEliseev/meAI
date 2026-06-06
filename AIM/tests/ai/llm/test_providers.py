"""
Tests for LLM providers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aim.ai.llm.providers.anthropic import AnthropicProvider
from src.aim.ai.llm.providers.openai import OpenAIProvider
from src.aim.ai.llm.schemas import LLMRequest, LLMProvider


class TestAnthropicProvider:
    """Test AnthropicProvider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = AnthropicProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
        assert provider.provider_name == LLMProvider.ANTHROPIC
    
    def test_estimate_cost_sonnet(self):
        """Test cost estimation for Sonnet."""
        provider = AnthropicProvider(api_key="test-key")
        
        # 1000 input + 500 output tokens
        cost = provider.estimate_cost(1000, 500, "claude-sonnet-4")
        
        # $3/1M input + $15/1M output
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.0001
    
    def test_estimate_cost_opus(self):
        """Test cost estimation for Opus."""
        provider = AnthropicProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "claude-opus-4")
        
        # $15/1M input + $75/1M output
        expected = (1000 / 1_000_000) * 15.0 + (500 / 1_000_000) * 75.0
        assert abs(cost - expected) < 0.0001
    
    def test_estimate_cost_haiku(self):
        """Test cost estimation for Haiku."""
        provider = AnthropicProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "claude-haiku-4")
        
        # $0.25/1M input + $1.25/1M output
        expected = (1000 / 1_000_000) * 0.25 + (500 / 1_000_000) * 1.25
        assert abs(cost - expected) < 0.0001
    
    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model defaults to Sonnet."""
        provider = AnthropicProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "unknown-model")
        
        # Should default to Sonnet pricing
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.0001
    

class TestOpenAIProvider:
    """Test OpenAIProvider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
        assert provider.provider_name == LLMProvider.OPENAI
    
    def test_estimate_cost_gpt4_turbo(self):
        """Test cost estimation for GPT-4 Turbo."""
        provider = OpenAIProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "gpt-4-turbo")
        
        # $10/1M input + $30/1M output
        expected = (1000 / 1_000_000) * 10.0 + (500 / 1_000_000) * 30.0
        assert abs(cost - expected) < 0.0001
    
    def test_estimate_cost_gpt4(self):
        """Test cost estimation for GPT-4."""
        provider = OpenAIProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "gpt-4")
        
        # $30/1M input + $60/1M output
        expected = (1000 / 1_000_000) * 30.0 + (500 / 1_000_000) * 60.0
        assert abs(cost - expected) < 0.0001
    
    def test_estimate_cost_gpt35_turbo(self):
        """Test cost estimation for GPT-3.5 Turbo."""
        provider = OpenAIProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "gpt-3.5-turbo")
        
        # $0.5/1M input + $1.5/1M output
        expected = (1000 / 1_000_000) * 0.5 + (500 / 1_000_000) * 1.5
        assert abs(cost - expected) < 0.0001
    
    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model defaults to GPT-4 Turbo."""
        provider = OpenAIProvider(api_key="test-key")
        
        cost = provider.estimate_cost(1000, 500, "unknown-model")
        
        # Should default to GPT-4 Turbo pricing
        expected = (1000 / 1_000_000) * 10.0 + (500 / 1_000_000) * 30.0
        assert abs(cost - expected) < 0.0001
    
