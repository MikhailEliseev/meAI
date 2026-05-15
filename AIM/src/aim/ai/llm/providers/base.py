"""Base provider interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional

from aim.ai.llm.schemas import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """Initialize provider.

        Args:
            api_key: API key for provider (if needed)
            base_url: Base URL for API (if custom)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM.

        Args:
            request: LLM request with messages and parameters

        Returns:
            LLM response with content and metadata

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name (claude, gemini, deepseek)."""
        pass

    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get default model name for this provider."""
        pass


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        error_type: str = "unknown",
        retryable: bool = False,
    ):
        """Initialize error.

        Args:
            message: Error message
            provider: Provider that failed
            error_type: Type of error (rate_limit, timeout, etc)
            retryable: Whether error is retryable
        """
        super().__init__(message)
        self.provider = provider
        self.error_type = error_type
        self.retryable = retryable
