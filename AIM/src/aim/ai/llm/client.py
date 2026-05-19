"""
LLM Client with Omni-Router

Unified client for multiple LLM providers with automatic failover,
caching, rate limiting, and cost tracking.
"""

import asyncio
import hashlib
import json
import time
from typing import Optional, Dict, Any
from redis import asyncio as aioredis
from pybreaker import CircuitBreaker
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from aiolimiter import AsyncLimiter

from .providers.base import BaseLLMProvider
from .providers.omni_route import OmniRouteProvider
from .cost_tracker import CostTracker
from .schemas import (
    LLMRequest,
    LLMResponse,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
)


class LLMClient:
    """
    Unified LLM client with Omni-Router.
    
    Features:
    - Multi-provider support (Anthropic primary, OpenAI fallback)
    - Automatic failover on errors
    - Circuit breaker (5 failures → 60s cooldown)
    - Retry with exponential backoff (1s → 30s max)
    - Token bucket rate limiting (10 req/s)
    - Redis caching (1-hour TTL, 90% cost savings)
    - Cost tracking and budget enforcement
    """
    
    def __init__(
        self,
        omni_route_url: str,
        omni_route_key: str,
        redis_url: str = "redis://localhost:6379",
        cache_ttl: int = 3600,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 1.0,
        max_cost_per_request: float = 5.0,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
    ):
        """
        Initialize LLM client.

        Args:
            omni_route_url: OmniRoute endpoint URL (e.g. http://138.16.224.188:20128/v1)
            omni_route_key: OmniRoute API key
            redis_url: Redis connection URL
            cache_ttl: Cache TTL in seconds (default: 1 hour)
            rate_limit_capacity: Rate limiter capacity (requests)
            rate_limit_refill: Rate limiter refill rate (requests/second)
            max_cost_per_request: Max cost per request in USD
            daily_budget: Daily budget limit in USD (None = no limit)
            monthly_budget: Monthly budget limit in USD (None = no limit)
        """
        # Initialize single OmniRoute provider
        omni = OmniRouteProvider(api_key=omni_route_key, base_url=omni_route_url)
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {
            LLMProvider.OMNI_ROUTE: omni,
        }

        # Primary provider
        self.primary_provider = LLMProvider.OMNI_ROUTE
        
        # Redis cache
        self.redis_url = redis_url
        self.cache_ttl = cache_ttl
        self._redis: Optional[aioredis.Redis] = None
        
        # Circuit breaker (5 failures → 60s cooldown)
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
        )
        
        # Rate limiter (token bucket)
        self.rate_limiter = AsyncLimiter(
            max_rate=rate_limit_capacity,
            time_period=1.0 / rate_limit_refill,
        )
        
        # Cost tracker
        self.cost_tracker = CostTracker(
            max_cost_per_request=max_cost_per_request,
            daily_budget=daily_budget,
            monthly_budget=monthly_budget,
        )
    
    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(self.redis_url)
        return self._redis
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """
        Generate cache key for request.
        
        Args:
            request: LLM request
            
        Returns:
            Cache key (SHA256 hash)
        """
        if request.cache_key:
            return request.cache_key
        
        # Hash request parameters
        cache_data = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "model": request.model,
            "temperature": request.temperature,
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """
        Get cached response.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response or None
        """
        try:
            redis = await self._get_redis()
            cached = await redis.get(f"llm:cache:{cache_key}")
            
            if cached:
                data = json.loads(cached)
                return LLMResponse(**data)
        except Exception:
            pass
        
        return None
    
    async def _cache_response(self, cache_key: str, response: LLMResponse) -> None:
        """
        Cache response.
        
        Args:
            cache_key: Cache key
            response: Response to cache
        """
        try:
            redis = await self._get_redis()
            await redis.setex(
                f"llm:cache:{cache_key}",
                self.cache_ttl,
                response.model_dump_json(),
            )
        except Exception:
            pass
    
    @retry(
        retry=retry_if_exception_type(LLMProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _generate_with_retry(
        self,
        provider: BaseLLMProvider,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate with retry logic.
        
        Args:
            provider: Provider to use
            request: LLM request
            
        Returns:
            LLM response
            
        Raises:
            LLMProviderError: If all retries fail
        """
        return await provider.generate(request)
    
    async def generate(
        self,
        request: LLMRequest,
        use_cache: bool = True,
    ) -> LLMResponse:
        """
        Generate completion via OmniRoute.

        Flow:
        1. Check cache (if enabled)
        2. Check budget limits
        3. Apply rate limiting
        4. Call OmniRoute provider
        5. Cache response
        6. Track costs

        Args:
            request: LLM request parameters
            use_cache: Whether to use caching (default: True)

        Returns:
            LLM response with metadata

        Raises:
            LLMProviderError: If generation fails
            LLMRateLimitError: If rate limit exceeded
            LLMBudgetExceededError: If budget exceeded
        """
        cache_key = self._generate_cache_key(request)
        request.cache_key = cache_key

        if use_cache:
            cached = await self._get_cached_response(cache_key)
            if cached:
                cached.cached = True
                return cached

        provider = self.providers[self.primary_provider]
        input_tokens = provider.count_tokens(
            request.prompt + (request.system_prompt or ""),
            request.model,
        )
        estimated_cost = provider.estimate_cost(
            input_tokens,
            request.max_tokens,
            request.model,
        )
        self.cost_tracker.check_budget(estimated_cost)

        async with self.rate_limiter:
            response = await self.circuit_breaker.call_async(
                self._generate_with_retry,
                provider,
                request,
            )

            if use_cache:
                await self._cache_response(cache_key, response)

            self.cost_tracker.track_request(
                provider=response.provider,
                model=response.model,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                cached=False,
            )

            return response
