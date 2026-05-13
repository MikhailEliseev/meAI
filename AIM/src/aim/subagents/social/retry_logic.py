"""
Retry Logic with Exponential Backoff for Ads Subagent

Handles transient errors with exponential backoff strategy.
Based on production-ready patterns from GitHub.
"""

import asyncio
import time
from typing import Callable, TypeVar, Any
from functools import wraps
import logging

T = TypeVar("T")

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted"""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retry with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 30.0)
        backoff_factor: Multiplier for delay (default: 2.0)
        exceptions: Tuple of exceptions to catch (default: all exceptions)

    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        async def fetch_data(url: str):
            return await api_client.get(url)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Retry exhausted after {max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # Should never reach here, but for type safety
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Retry exhausted after {max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # Should never reach here, but for type safety
            raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class RetryPolicy:
    """Configurable retry policy for programmatic use.

    Example:
        policy = RetryPolicy(max_attempts=3, initial_delay=1.0)

        result = await policy.execute_async(api_client.fetch, url)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions

    async def execute_async(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Execute async function with retry policy"""
        delay = self.initial_delay
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e

                if attempt == self.max_attempts:
                    logger.error(
                        f"Retry exhausted after {self.max_attempts} attempts: {e}",
                        exc_info=True
                    )
                    raise RetryExhaustedError(
                        f"Failed after {self.max_attempts} attempts: {str(e)}"
                    ) from e

                logger.warning(
                    f"Attempt {attempt}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)
                delay = min(delay * self.backoff_factor, self.max_delay)

        raise last_exception

    def execute_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Execute sync function with retry policy"""
        delay = self.initial_delay
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e

                if attempt == self.max_attempts:
                    logger.error(
                        f"Retry exhausted after {self.max_attempts} attempts: {e}",
                        exc_info=True
                    )
                    raise RetryExhaustedError(
                        f"Failed after {self.max_attempts} attempts: {str(e)}"
                    ) from e

                logger.warning(
                    f"Attempt {attempt}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                time.sleep(delay)
                delay = min(delay * self.backoff_factor, self.max_delay)

        raise last_exception
