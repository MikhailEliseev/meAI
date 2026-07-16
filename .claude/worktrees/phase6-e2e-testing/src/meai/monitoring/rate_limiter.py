"""Rate limiter for API calls"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter using sliding window algorithm"""

    def __init__(self, max_requests: int, window: timedelta):
        """Initialize Rate Limiter

        Args:
            max_requests: Maximum requests allowed in window
            window: Time window for rate limiting
        """
        self.max_requests = max_requests
        self.window = window
        self.requests: list[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Try to acquire a request slot

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        async with self._lock:
            now = datetime.now(timezone.utc)

            # Remove old requests outside window
            cutoff = now - self.window
            self.requests = [req for req in self.requests if req > cutoff]

            # Check if we can make request
            if len(self.requests) >= self.max_requests:
                logger.warning(
                    "rate_limit.exceeded",
                    current=len(self.requests),
                    max=self.max_requests,
                )
                return False

            # Add request
            self.requests.append(now)
            logger.debug(
                "rate_limit.acquired",
                current=len(self.requests),
                max=self.max_requests,
            )
            return True

    def get_remaining(self) -> int:
        """Get remaining requests in current window

        Returns:
            Number of remaining requests
        """
        now = datetime.now(timezone.utc)
        cutoff = now - self.window

        # Count requests in window
        active_requests = sum(1 for req in self.requests if req > cutoff)
        return max(0, self.max_requests - active_requests)

    def get_wait_time(self) -> float:
        """Get wait time until next available slot

        Returns:
            Wait time in seconds (0 if slot available)
        """
        if self.get_remaining() > 0:
            return 0.0

        now = datetime.now(timezone.utc)
        cutoff = now - self.window

        # Find oldest request in window
        active_requests = [req for req in self.requests if req > cutoff]
        if not active_requests:
            return 0.0

        oldest = min(active_requests)
        wait_until = oldest + self.window
        wait_seconds = (wait_until - now).total_seconds()

        return max(0.0, wait_seconds)

    def reset(self) -> None:
        """Reset rate limiter"""
        self.requests.clear()
        logger.info("rate_limit.reset")

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics

        Returns:
            Statistics dictionary
        """
        now = datetime.now(timezone.utc)
        cutoff = now - self.window
        active_requests = sum(1 for req in self.requests if req > cutoff)

        return {
            "total_requests": len(self.requests),
            "active_requests": active_requests,
            "remaining": self.get_remaining(),
            "max_requests": self.max_requests,
            "window_seconds": self.window.total_seconds(),
        }
