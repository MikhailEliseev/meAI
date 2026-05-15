"""LLM Client with cost tracking, rate limiting, and caching.

Main interface for all LLM operations in AIM agency.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from aim.ai.llm.providers.base import BaseLLMProvider, LLMProviderError
from aim.ai.llm.providers.omnirouter import OmniRouterProvider
from aim.ai.llm.schemas import LLMMessage, LLMRequest, LLMResponse


class LLMClient:
    """Main LLM client with cost tracking, rate limiting, and caching."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        omnirouter_url: str = "http://localhost:8000",
        max_cost_per_request: float = 5.0,
        daily_budget: float = 50.0,
        monthly_budget: float = 450.0,
        rate_limit_rpm: int = 60,
        cache_ttl: int = 3600,
        enable_cache: bool = True,
    ):
        """Initialize LLM client.

        Args:
            provider: LLM provider (if None, uses OmniRouterProvider)
            omnirouter_url: Omni-Router server URL
            max_cost_per_request: Max cost per request in USD
            daily_budget: Daily budget in USD
            monthly_budget: Monthly budget in USD
            rate_limit_rpm: Rate limit in requests per minute
            cache_ttl: Cache TTL in seconds (default: 1 hour)
            enable_cache: Whether to enable caching
        """
        self.provider = provider or OmniRouterProvider(base_url=omnirouter_url)
        self.max_cost_per_request = max_cost_per_request
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.rate_limit_rpm = rate_limit_rpm
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache

        # Cost tracking
        self.total_cost = 0.0
        self.daily_cost = 0.0
        self.monthly_cost = 0.0
        self.last_reset_day = time.strftime("%Y-%m-%d")
        self.last_reset_month = time.strftime("%Y-%m")

        # Rate limiting (token bucket)
        self.tokens = rate_limit_rpm
        self.last_refill = time.time()

        # Cache (in-memory for now, can be Redis later)
        self.cache: Dict[str, tuple[LLMResponse, float]] = {}

        # Metrics
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        bypass_cache: bool = False,
    ) -> LLMResponse:
        """Generate response from LLM.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            system_prompt: System prompt
            response_format: Structured output format
            metadata: Request metadata
            bypass_cache: Skip cache lookup

        Returns:
            LLM response

        Raises:
            BudgetExceededError: If budget exceeded
            RateLimitError: If rate limit exceeded
            LLMProviderError: If generation fails
        """
        # Reset budgets if needed
        self._reset_budgets()

        # Check rate limit
        await self._check_rate_limit()

        # Create request
        request = LLMRequest(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            response_format=response_format,
            metadata=metadata or {},
        )

        # Check cache
        if self.enable_cache and not bypass_cache:
            cache_key = self._get_cache_key(request)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                self.cache_hits += 1
                cached_response.cached = True
                return cached_response

        self.cache_misses += 1

        # Generate response
        try:
            response = await self.provider.generate(request)
        except LLMProviderError as e:
            # Log error and re-raise
            print(f"LLM Provider Error: {e}")
            raise

        # Check cost
        if response.cost_usd > self.max_cost_per_request:
            raise BudgetExceededError(
                f"Request cost ${response.cost_usd:.4f} exceeds max ${self.max_cost_per_request}"
            )

        # Update costs
        self.total_cost += response.cost_usd
        self.daily_cost += response.cost_usd
        self.monthly_cost += response.cost_usd

        # Check budgets
        if self.daily_cost > self.daily_budget:
            raise BudgetExceededError(
                f"Daily budget ${self.daily_budget} exceeded (spent ${self.daily_cost:.2f})"
            )

        if self.monthly_cost > self.monthly_budget:
            raise BudgetExceededError(
                f"Monthly budget ${self.monthly_budget} exceeded (spent ${self.monthly_cost:.2f})"
            )

        # Update metrics
        self.request_count += 1

        # Cache response
        if self.enable_cache:
            cache_key = self._get_cache_key(request)
            self._put_in_cache(cache_key, response)

        return response

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text from simple prompt (convenience method).

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Generated text
        """
        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.generate(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics.

        Returns:
            Metrics dictionary
        """
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0.0
        )

        return {
            "request_count": self.request_count,
            "total_cost": self.total_cost,
            "daily_cost": self.daily_cost,
            "monthly_cost": self.monthly_cost,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache),
        }

    async def close(self):
        """Close client and cleanup resources."""
        if hasattr(self.provider, "close"):
            await self.provider.close()

    def _reset_budgets(self):
        """Reset daily/monthly budgets if needed."""
        current_day = time.strftime("%Y-%m-%d")
        current_month = time.strftime("%Y-%m")

        if current_day != self.last_reset_day:
            self.daily_cost = 0.0
            self.last_reset_day = current_day

        if current_month != self.last_reset_month:
            self.monthly_cost = 0.0
            self.last_reset_month = current_month

    async def _check_rate_limit(self):
        """Check and enforce rate limit (token bucket algorithm)."""
        # Refill tokens
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = elapsed * (self.rate_limit_rpm / 60.0)
        self.tokens = min(self.rate_limit_rpm, self.tokens + refill_amount)
        self.last_refill = now

        # Check if we have tokens
        if self.tokens < 1:
            wait_time = (1 - self.tokens) / (self.rate_limit_rpm / 60.0)
            raise RateLimitError(
                f"Rate limit exceeded. Wait {wait_time:.1f}s before next request"
            )

        # Consume token
        self.tokens -= 1

    def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request.

        Args:
            request: LLM request

        Returns:
            Cache key (hash of request)
        """
        # Create deterministic string from request
        key_data = {
            "messages": [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "system_prompt": request.system_prompt,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[LLMResponse]:
        """Get response from cache.

        Args:
            key: Cache key

        Returns:
            Cached response or None
        """
        if key not in self.cache:
            return None

        response, timestamp = self.cache[key]

        # Check if expired
        if time.time() - timestamp > self.cache_ttl:
            del self.cache[key]
            return None

        return response

    def _put_in_cache(self, key: str, response: LLMResponse):
        """Put response in cache.

        Args:
            key: Cache key
            response: LLM response
        """
        self.cache[key] = (response, time.time())


class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""

    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass
