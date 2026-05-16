"""
OpenAI GPT Provider

Implementation for OpenAI GPT-4 API (fallback provider).
"""

import time
from typing import Optional, Type
from pydantic import BaseModel
import openai
from openai import AsyncOpenAI

from .base import BaseLLMProvider
from ..schemas import (
    LLMRequest,
    LLMResponse,
    LLMProvider,
    LLMProviderError,
)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT provider implementation.
    
    Features:
    - GPT-4 Turbo/GPT-4/GPT-3.5 support
    - Structured output with JSON mode
    - Token counting with tiktoken
    """
    
    # Pricing per 1M tokens (as of 2026-05)
    PRICING = {
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }
    
    def __init__(self, api_key: str):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
        """
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
    
    @property
    def provider_name(self) -> LLMProvider:
        """Get provider name."""
        return LLMProvider.OPENAI
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate completion from GPT.
        
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
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Build request kwargs
            kwargs = {
                "model": request.model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            
            # Add JSON mode if structured output requested
            if request.response_format:
                kwargs["response_format"] = {"type": "json_object"}
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(**kwargs)
            
            # Extract content
            content = response.choices[0].message.content or ""
            
            # Calculate tokens and cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
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
            
        except openai.APIError as e:
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
            # Default to GPT-4 Turbo pricing if model unknown
            model = "gpt-4-turbo"
        
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            model: Model name (for tokenizer selection)
            
        Returns:
            Number of tokens
        """
        try:
            import tiktoken
            
            # Get encoding for model
            if "gpt-4" in model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")
            
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4
