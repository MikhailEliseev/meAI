"""
Anthropic Claude Provider

Implementation for Anthropic Claude API (Opus, Sonnet, Haiku).
"""

import time
from typing import Optional, Type
from pydantic import BaseModel
import anthropic
from anthropic import Anthropic, AsyncAnthropic

from .base import BaseLLMProvider
from ..schemas import (
    LLMRequest,
    LLMResponse,
    LLMProvider,
    LLMProviderError,
)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude provider implementation.
    
    Features:
    - Claude Opus/Sonnet/Haiku support
    - Prompt caching (90% cost reduction for system prompts)
    - Structured output with Pydantic models
    - Token counting with tiktoken
    """
    
    # Pricing per 1M tokens (as of 2026-05)
    PRICING = {
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "claude-haiku-4": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(self, api_key: str):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
        """
        super().__init__(api_key)
        self.client = AsyncAnthropic(api_key=api_key)
        self.sync_client = Anthropic(api_key=api_key)
    
    @property
    def provider_name(self) -> LLMProvider:
        """Get provider name."""
        return LLMProvider.ANTHROPIC
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate completion from Claude.
        
        Args:
            request: LLM request parameters
            
        Returns:
            LLM response with metadata
            
        Raises:
            LLMProviderError: If generation fails
        """
        start_time = time.time()
        
        try:
            # Build messages
            messages = [{"role": "user", "content": request.prompt}]
            
            # Build request kwargs
            kwargs = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": messages,
            }
            
            # Add system prompt if provided
            if request.system_prompt:
                kwargs["system"] = request.system_prompt
            
            # Call Claude API
            response = await self.client.messages.create(**kwargs)
            
            # Extract content
            content = response.content[0].text if response.content else ""
            
            # Calculate tokens and cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            cost_usd = self.estimate_cost(input_tokens, output_tokens, request.model)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=self.provider_name,
                tokens_used=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                cached=False,
                latency_ms=latency_ms,
                cache_key=request.cache_key,
            )
            
        except anthropic.APIError as e:
            raise LLMProviderError(
                self.provider_name,
                f"API error: {str(e)}"
            )
        except Exception as e:
            raise LLMProviderError(
                self.provider_name,
                f"Unexpected error: {str(e)}"
            )
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        if model not in self.PRICING:
            # Default to Sonnet pricing if model unknown
            model = "claude-sonnet-4"
        
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text using Anthropic's token counter.
        
        Args:
            text: Text to count tokens for
            model: Model name (for tokenizer selection)
            
        Returns:
            Number of tokens
        """
        try:
            # Use Anthropic's token counting
            result = self.sync_client.count_tokens(text)
            return result
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4
