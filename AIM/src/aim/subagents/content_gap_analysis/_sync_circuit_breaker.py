cuitState
from hfs_location_client.exceptions import CircuitOpenError

T = TypeVar("T")


class SyncCircuitBreaker:
    """Thread-safe synchronous circuit breaker."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: