"""Base API Client with Resilience Patterns

Provides circuit breaker, retry with exponential backoff, rate limiting, caching,
metrics, and structured logging for all API clients.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
import structlog
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from prometheus_client import Counter, Histogram
from pybreaker import CircuitBreaker
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Prometheus metrics
api_calls_total = Counter(
    "api_calls_total",
    "Total API calls",
    ["client", "endpoint", "status"],
)

api_latency = Histogram(
    "api_latency_seconds",
    "API call latency",
    ["client", "endpoint"],
)

api_cost_total = Counter(
    "api_cost_total",
    "Total API cost in USD",
    ["client", "endpoint"],
)

logger = structlog.get_logger()


class TokenBucketRateLimiter:
    """Token bucket rate limiter for API calls

    Args:
        capacity: Maximum number of tokens (requests)
        refill_rate: Tokens added per second
    """

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary

        Args:
            tokens: Number of tokens to acquire
        """
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill

                # Refill tokens
                self.tokens = min(
                    self.capacity,
                    self.tokens + elapsed * self.refill_rate
                )
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Wait for next refill
                wait_time = (tokens - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)


class APIClientBase(ABC):
    """Base class for API clients with resilience patterns

    Features:
    - Circuit breaker (fail_max=5, reset_timeout=60s)
    - Retry with exponential backoff (1s → 30s max)
    - Token bucket rate limiting
    - 1h cache for API responses
    - Prometheus metrics
    - Structured logging

    Args:
        api_key: API key for authentication
        base_url: Base URL for API
        rate_limit_capacity: Max requests in bucket
        rate_limit_refill: Requests per second refill rate
        cache_ttl: Cache TTL in seconds (default 3600 = 1h)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        rate_limit_capacity: int,
        rate_limit_refill: float,
        cache_ttl: int = 3600,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.cache_ttl = cache_ttl

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

        # Rate limiter
        self.rate_limiter = TokenBucketRateLimiter(
            capacity=rate_limit_capacity,
            refill_rate=rate_limit_refill,
        )

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
            name=self.__class__.__name__,
        )

        # Cache
        self.cache = Cache(
            Cache.MEMORY,
            serializer=JsonSerializer(),
            ttl=cache_ttl,
        )

        # Logger
        self.logger = logger.bind(client=self.__class__.__name__)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make HTTP request with resilience patterns

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            json: JSON body

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        # Check cache for GET requests
        if method == "GET" and params:
            cache_key = f"{endpoint}:{str(params)}"
            cached = await self.cache.get(cache_key)
            if cached:
                self.logger.info("cache_hit", endpoint=endpoint)
                return cached

        # Rate limiting
        await self.rate_limiter.acquire()

        # Retry with exponential backoff
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            reraise=True,
        ):
            with attempt:
                # Circuit breaker
                with self.circuit_breaker:
                    start_time = time.time()

                    try:
                        response = await self.client.request(
                            method=method,
                            url=endpoint,
                            params=params,
                            json=json,
                        )
                        response.raise_for_status()

                        duration = time.time() - start_time

                        # Metrics
                        api_calls_total.labels(
                            client=self.__class__.__name__,
                            endpoint=endpoint,
                            status="success",
                        ).inc()

                        api_latency.labels(
                            client=self.__class__.__name__,
                            endpoint=endpoint,
                        ).observe(duration)

                        # Logging
                        self.logger.info(
                            "api_request_success",
                            endpoint=endpoint,
                            duration=duration,
                            attempt=attempt.retry_state.attempt_number,
                        )

                        result = response.json()

                        # Cache GET responses
                        if method == "GET" and params:
                            await self.cache.set(cache_key, result)

                        return result

                    except httpx.HTTPError as e:
                        duration = time.time() - start_time

                        # Metrics
                        api_calls_total.labels(
                            client=self.__class__.__name__,
                            endpoint=endpoint,
                            status="error",
                        ).inc()

                        # Logging
                        self.logger.error(
                            "api_request_error",
                            endpoint=endpoint,
                            error=str(e),
                            duration=duration,
                            attempt=attempt.retry_state.attempt_number,
                        )

                        raise

    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

    @abstractmethod
    async def expand_keywords(
        self,
        seed_keyword: str,
        max_keywords: int = 100,
        min_volume: int = 10,
        max_cost_usd: float = 5.0,
    ) -> list[dict[str, Any]]:
        """Expand seed keyword into related keywords

        Args:
            seed_keyword: Seed keyword to expand
            max_keywords: Maximum keywords to return
            min_volume: Minimum search volume
            max_cost_usd: Maximum cost in USD

        Returns:
            List of keyword data dictionaries
        """
        pass
