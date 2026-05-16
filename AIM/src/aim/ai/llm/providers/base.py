"""
Base LLM Provider

Abstract base class for LLM provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel

from ..schemas import LLMRequest, LLMResponse, LLMProvider


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str):
        """
        Initialize provider.
        
        Args:
            api_key: API key for the provider
        """
        self.api_key = api_key
    
    @property
    @abstractmethod
    def provider_name(self) -> LLMProvider:
        """Get provider name."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate completion from LLM.
        
        Args:
            request: LLM request parameters
            
        Returns:
            LLM response with metadata
            
        Raises:
            LLMProviderError: If generation fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            model: Model name (for tokenizer selection)
            
        Returns:
            Number of tokens
        """
        pass
