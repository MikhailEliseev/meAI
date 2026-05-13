"""
Rate Limiting with Token Bucket for Ads Subagent

Prevents API rate limit violations using token bucket algorithm.
Based on production-ready patterns from GitHub.
"""

import asyncio
import time
from typing import Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded"""
    pass


class TokenBucketRateLimiter:
    """Token bucket rate limiter for controlling request rate.

    Algorithm:
    - Bucket has capacity for N tokens
    - Tokens refill at rate R per second
    - Each request consumes 1 token
    - If no tokens available, request is blocked or rejected

    Args:
        capacity: Maximum number of tokens (burst size)
        refill_rate: Tokens added per second
        initial_tokens: Initial number of tokens (default: capacity)

    Example:
        limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)

        # Async usage
        await limiter.acquire_async()
        result = await api_client.fetch(url)

        # Sync usage
        limiter.acquire_sync()
        result = api_client.fetch(url)
    """

    def __init__(
        self,
        capacity: int = 10,
        refill_rate: float = 1.0,
        initial_tokens: Optional[int] = None
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = initial_tokens if initial_tokens is not None else capacity
        self._last_refill = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self._last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate

        # Update tokens (capped at capacity)
        self._tokens = min(self.capacity, self._tokens + tokens_to_add)
        self._last_refill = now

    def try_acquire(self) -> bool:
        """Try to acquire a token without blocking.

        Returns:
            True if token acquired, False otherwise
        """
        with self._lock:
            self._refill()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            else:
                return False

    async def acquire_async(self, timeout: Optional[float] = None) -> None:
        """Acquire a token, waiting if necessary (async).

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Raises:
            RateLimitExceededError: If timeout is reached
        """
        start_time = time.time()

        while True:
            if self.try_acquire():
                return

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitExceededError(
                        f"Rate limit exceeded. Timeout after {timeout}s."
                    )

            # Wait before retry (small delay to avoid busy loop)
            await asyncio.sleep(0.01)

    def acquire_sync(self, timeout: Optional[float] = None) -> None:
        """Acquire a token, waiting if necessary (sync).

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Raises:
            RateLimitExceededError: If timeout is reached
        """
        start_time = time.time()

        while True:
            if self.try_acquire():
                return

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitExceededError(
                        f"Rate limit exceeded. Timeout after {timeout}s."
                    )

            # Wait before retry (small delay to avoid busy loop)
            time.sleep(0.01)

    @property
    def available_tokens(self) -> float:
        """Get current number of available tokens"""
        with self._lock:
            self._refill()
            return self._tokens

    def reset(self) -> None:
        """Reset rate limiter to initial state"""
        with self._lock:
            self._tokens = self.capacity
            self._last_refill = time.time()


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for precise rate control.

    Algorithm:
    - Track timestamps of recent requests
    - Allow max N requests per window (e.g., 100 requests per minute)
    - Slide window forward as time passes

    Args:
        max_requests: Maximum requests per window
        window_seconds: Window size in seconds

    Example:
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)

        await limiter.acquire_async()
        result = await api_client.fetch(url)
    """

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []
        self._lock = Lock()

    def _clean_old_requests(self) -> None:
        """Remove requests outside the current window"""
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old requests
        self._requests = [ts for ts in self._requests if ts > cutoff]

    def try_acquire(self) -> bool:
        """Try to acquire a slot without blocking.

        Returns:
            True if slot acquired, False otherwise
        """
        with self._lock:
            self._clean_old_requests()

            if len(self._requests) < self.max_requests:
                self._requests.append(time.time())
                return True
            else:
                return False

    async def acquire_async(self, timeout: Optional[float] = None) -> None:
        """Acquire a slot, waiting if necessary (async).

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Raises:
            RateLimitExceededError: If timeout is reached
        """
        start_time = time.time()

        while True:
            if self.try_acquire():
                return

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitExceededError(
                        f"Rate limit exceeded. Timeout after {timeout}s."
                    )

            # Wait before retry
            await asyncio.sleep(0.1)

    def acquire_sync(self, timeout: Optional[float] = None) -> None:
        """Acquire a slot, waiting if necessary (sync).

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Raises:
            RateLimitExceededError: If timeout is reached
        """
        start_time = time.time()

        while True:
            if self.try_acquire():
                return

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitExceededError(
                        f"Rate limit exceeded. Timeout after {timeout}s."
                    )

            # Wait before retry
            time.sleep(0.1)

    @property
    def current_usage(self) -> int:
        """Get current number of requests in window"""
        with self._lock:
            self._clean_old_requests()
            return len(self._requests)

    def reset(self) -> None:
        """Reset rate limiter to initial state"""
        with self._lock:
            self._requests.clear()
