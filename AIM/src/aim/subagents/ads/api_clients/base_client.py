"""
Base API Client with Resilience Patterns.

Implements:
- Circuit Breaker (pybreaker)
- Retry with Exponential Backoff (tenacity)
- Rate Limiting (aiolimiter)
- Response Caching (aiocache)
- Structured Logging (structlog)
- Prometheus Metrics

Based on patterns extracted from google-ads-python and existing base.py.
"""

import asyncio
from typing import Any, Dict, Optional

import httpx
import structlog
from aiocache import Cache
from aiolimiter import AsyncLimiter
from prometheus_client import Counter, Histogram
from pybreaker import CircuitBreaker
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.aim.subagents.ads.config.settings import AdsSettings

logger = structlog.get_logger(__name__)

# Prometheus metrics
api_requests_total = Counter(
    "ads_api_requests_total",
    "Total API requests",
    ["client", "method", "status"]
)

api_request_duration = Histogram(
    "ads_api_request_duration_seconds",
    "API request duration",
    ["client", "method"]
)

circuit_breaker_state = Counter(
    "ads_circuit_breaker_state_changes",
    "Circuit breaker state changes",
    ["client", "state"]
)


class APIError(Exception):
    """Base exception for API errors."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class AuthenticationError(APIError):
    """Authentication failed."""
    pass


class CircuitBreakerOpenError(APIError):
    """Circuit breaker is open."""
    pass


class BaseAPIClient:
    """
    Base API client with resilience patterns.

    Features:
    - Circuit breaker: Opens after 5 failures, resets after 60s
    - Retry: 3 attempts with exponential backoff (1s → 30s)
    - Rate limiting: Token bucket (10 req/s by default)
    - Caching: 1 hour TTL by default
    - Metrics: Prometheus counters and histograms
    - Logging: Structured logs with context
    """

    def __init__(
        self,
        base_url: str,
        settings: Optional[AdsSettings] = None,
        client_name: str = "base",
    ):
        """
        Initialize base API client.

        Args:
            base_url: Base URL for API endpoints
            settings: Configuration settings (uses defaults if None)
            client_name: Client identifier for metrics/logs
        """
        self.base_url = base_url
        self.settings = settings or AdsSettings()
        self.client_name = client_name

        # HTTP client
        self.http_client = httpx.AsyncClient(
            base_url=base_url,
            timeout=self.settings.api_timeout,
            follow_redirects=True,
        )

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            fail_max=self.settings.circuit_breaker_fail_max,
            reset_timeout=self.settings.circuit_breaker_reset_timeout,
            listeners=[self._on_circuit_breaker_state_change],
        )

        # Rate limiter (token bucket)
        self.rate_limiter = AsyncLimiter(
            max_rate=self.settings.rate_limit_capacity,
            time_period=1.0 / self.settings.rate_limit_refill,
        )

        # Cache
        self.cache = Cache(Cache.MEMORY) if self.settings.cache_enabled else None

        logger.info(
            "api_client_initialized",
            client=client_name,
            base_url=base_url,
            circuit_breaker_fail_max=self.settings.circuit_breaker_fail_max,
            rate_limit_capacity=self.settings.rate_limit_capacity,
            cache_enabled=self.settings.cache_enabled,
        )

    def _on_circuit_breaker_state_change(
        self,
        old_state: str,
        new_state: str,
        **kwargs: Any
    ) -> None:
        """Circuit breaker state change callback."""
        logger.warning(
            "circuit_breaker_state_changed",
            client=self.client_name,
            old_state=old_state,
            new_state=new_state,
        )
        circuit_breaker_state.labels(
            client=self.client_name,
            state=new_state
        ).inc()

    async def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.cache:
            return None

        try:
            value = await self.cache.get(cache_key)
            if value is not None:
                logger.debug("cache_hit", key=cache_key, client=self.client_name)
            return value
        except Exception as e:
            logger.warning("cache_get_failed", error=str(e), key=cache_key)
            return None

    async def _set_cached(
        self,
        cache_key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        if not self.cache:
            return

        try:
            await self.cache.set(
                cache_key,
                value,
                ttl=ttl or self.settings.cache_ttl
            )
            logger.debug("cache_set", key=cache_key, client=self.client_name)
        except Exception as e:
            logger.warning("cache_set_failed", error=str(e), key=cache_key)

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=2,
            min=1,
            max=30
        ),
        reraise=True,
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Retries on timeout and network errors only.
        Does NOT retry on 4xx/5xx (handled by circuit breaker).

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx.request()

        Returns:
            HTTP response

        Raises:
            httpx.TimeoutException: Request timed out after retries
            httpx.NetworkError: Network error after retries
        """
        url = f"{self.base_url}{endpoint}"

        if self.settings.log_api_requests:
            logger.info(
                "api_request_start",
                client=self.client_name,
                method=method,
                url=url,
            )

        with api_request_duration.labels(
            client=self.client_name,
            method=method
        ).time():
            response = await self.http_client.request(method, endpoint, **kwargs)

        if self.settings.log_api_responses:
            logger.debug(
                "api_response_received",
                client=self.client_name,
                method=method,
                url=url,
                status_code=response.status_code,
            )

        api_requests_total.labels(
            client=self.client_name,
            method=method,
            status=response.status_code
        ).inc()

        return response

    async def request(
        self,
        method: str,
        endpoint: str,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make API request with full resilience stack.

        Flow:
        1. Check cache (if cache_key provided)
        2. Acquire rate limit token
        3. Execute through circuit breaker
        4. Retry on transient failures
        5. Cache response (if cache_key provided)

        Args:
            method: HTTP method
            endpoint: API endpoint path
            cache_key: Optional cache key for response caching
            cache_ttl: Optional cache TTL (overrides default)
            **kwargs: Additional arguments for httpx.request()

        Returns:
            Parsed JSON response

        Raises:
            CircuitBreakerOpenError: Circuit breaker is open
            RateLimitError: Rate limit exceeded
            AuthenticationError: Authentication failed (401)
            APIError: Other API errors
        """
        # Check cache first
        if cache_key:
            cached = await self._get_cached(cache_key)
            if cached is not None:
                return cached

        # Rate limiting
        try:
            async with self.rate_limiter:
                # Circuit breaker + retry
                try:
                    response = await self.circuit_breaker.call_async(
                        self._make_request,
                        method,
                        endpoint,
                        **kwargs
                    )
                except Exception as e:
                    if "CircuitBreakerError" in str(type(e)):
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker open for {self.client_name}"
                        )
                    raise

        except asyncio.TimeoutError:
            raise RateLimitError(
                f"Rate limit exceeded for {self.client_name}"
            )

        # Handle HTTP errors
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed (401)")
        elif response.status_code == 429:
            raise RateLimitError("API rate limit exceeded (429)")
        elif response.status_code >= 400:
            raise APIError(
                f"API error: {response.status_code} - {response.text}"
            )

        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(
                "json_parse_failed",
                client=self.client_name,
                error=str(e),
                response_text=response.text[:200]
            )
            raise APIError(f"Failed to parse JSON response: {e}")

        # Cache response
        if cache_key:
            await self._set_cached(cache_key, data, ttl=cache_ttl)

        return data

    async def get(
        self,
        endpoint: str,
        cache_key: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """GET request."""
        return await self.request("GET", endpoint, cache_key=cache_key, **kwargs)

    async def post(
        self,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """POST request (no caching)."""
        return await self.request("POST", endpoint, **kwargs)

    async def put(
        self,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """PUT request (no caching)."""
        return await self.request("PUT", endpoint, **kwargs)

    async def delete(
        self,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """DELETE request (no caching)."""
        return await self.request("DELETE", endpoint, **kwargs)

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self.http_client.aclose()
        if self.cache:
            await self.cache.close()

        logger.info("api_client_closed", client=self.client_name)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
