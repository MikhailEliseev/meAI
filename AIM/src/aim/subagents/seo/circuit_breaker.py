"""
Circuit Breaker Pattern for Ads Subagent

Prevents cascading failures by stopping requests to failing services.
Based on: https://github.com/High-Functioning-Solutions/hfs-location-client
Quality Score: 85.0/100
"""

import time
from enum import Enum
from typing import Callable, TypeVar, Any
from threading import Lock

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class SyncCircuitBreaker:
    """Thread-safe synchronous circuit breaker.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Blocking requests after threshold failures
    - HALF_OPEN: Testing if service recovered

    Args:
        failure_threshold: Number of failures before opening circuit (default: 5)
        recovery_timeout: Seconds to wait before testing recovery (default: 60.0)

    Example:
        breaker = SyncCircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

        try:
            result = breaker.call(api_client.fetch, url)
        except CircuitOpenError:
            # Circuit is open, use fallback
            result = cached_response
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float | None = None
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            self._check_recovery()
            return self._state

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from func
        """
        with self._lock:
            self._check_recovery()

            if self._state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"Circuit breaker is open. "
                    f"Failed {self._failure_count} times. "
                    f"Will retry after {self._recovery_timeout}s."
                )

            if self._state == CircuitState.HALF_OPEN:
                # Allow one test request
                pass

        # Execute function (outside lock to avoid blocking)
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def _check_recovery(self) -> None:
        """Check if circuit should transition to HALF_OPEN"""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN

    def _record_success(self) -> None:
        """Record successful call, reset failure count"""
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._last_failure_time = None

    def _record_failure(self) -> None:
        """Record failed call, open circuit if threshold exceeded"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
