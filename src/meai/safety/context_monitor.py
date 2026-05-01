"""Context monitor - enforce 40% rule and prevent context explosion"""

from typing import Any
import structlog

logger = structlog.get_logger()


class ContextMonitor:
    """Monitor context usage and enforce limits"""

    def __init__(
        self,
        max_tokens: int = 200000,
        warning_threshold: float = 0.4,
        critical_threshold: float = 0.5,
    ):
        """Initialize Context Monitor

        Args:
            max_tokens: Maximum tokens allowed
            warning_threshold: Warning threshold (0.0-1.0)
            critical_threshold: Critical threshold for auto-compact (0.0-1.0)
        """
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        self.current_tokens = 0
        self.warned = False

    def track_usage(self, tokens: int) -> None:
        """Track token usage

        Args:
            tokens: Current token count
        """
        self.current_tokens = tokens

        usage_percent = self.get_usage_percent()

        if usage_percent >= self.critical_threshold:
            logger.error(
                "context.critical",
                tokens=tokens,
                max_tokens=self.max_tokens,
                percent=usage_percent,
            )
        elif usage_percent >= self.warning_threshold and not self.warned:
            logger.warning(
                "context.warning",
                tokens=tokens,
                max_tokens=self.max_tokens,
                percent=usage_percent,
            )
            self.warned = True

    def get_usage_percent(self) -> float:
        """Get current usage as percentage

        Returns:
            Usage percentage (0.0-1.0)
        """
        return self.current_tokens / self.max_tokens

    def should_warn(self) -> bool:
        """Check if warning threshold exceeded

        Returns:
            True if warning threshold exceeded
        """
        return self.get_usage_percent() >= self.warning_threshold

    def should_compact(self) -> bool:
        """Check if auto-compact should trigger

        Returns:
            True if critical threshold exceeded
        """
        return self.get_usage_percent() >= self.critical_threshold

    def reset(self) -> None:
        """Reset tracking"""
        self.current_tokens = 0
        self.warned = False
        logger.info("context.reset")

    def get_remaining_tokens(self) -> int:
        """Get remaining tokens

        Returns:
            Number of remaining tokens
        """
        return self.max_tokens - self.current_tokens

    def get_status(self) -> dict[str, Any]:
        """Get current status

        Returns:
            Status dictionary with current state
        """
        usage_percent = self.get_usage_percent()

        if usage_percent >= self.critical_threshold:
            status = "critical"
        elif usage_percent >= self.warning_threshold:
            status = "warning"
        else:
            status = "ok"

        return {
            "status": status,
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": usage_percent,
            "remaining_tokens": self.get_remaining_tokens(),
        }
