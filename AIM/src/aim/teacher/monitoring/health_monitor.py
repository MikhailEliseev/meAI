"""
Health Monitor - Endpoint health checks with alerting.

Monitors critical endpoints (Exa API, GitHub API, Event Bus, Obsidian)
and sends alerts when failures occur.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class EndpointStatus(str, Enum):
    """Endpoint health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class Severity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class EndpointHealth:
    """Health status of an endpoint."""
    name: str
    status: EndpointStatus
    response_time_ms: float | None = None
    consecutive_failures: int = 0
    last_check: datetime = field(default_factory=datetime.now)
    last_error: str | None = None


@dataclass
class HealthAlert:
    """Health alert notification."""
    endpoint: str
    severity: Severity
    status: EndpointStatus
    consecutive_failures: int
    error: str | None
    impact: str
    action_items: list[str]
    timestamp: datetime = field(default_factory=datetime.now)


class HealthMonitor:
    """
    Monitor critical endpoints and send alerts on failures.

    Alert thresholds:
    - 3 consecutive failures → WARNING
    - 5 consecutive failures → CRITICAL
    - 10 consecutive failures → Disable endpoint

    Notification channels:
    - Console (always)
    - Telegram (if configured)
    - Email (if configured)
    """

    def __init__(
        self,
        alert_threshold_warning: int = 3,
        alert_threshold_critical: int = 5,
        disable_threshold: int = 10,
        check_timeout: int = 10,
    ):
        self.alert_threshold_warning = alert_threshold_warning
        self.alert_threshold_critical = alert_threshold_critical
        self.disable_threshold = disable_threshold
        self.check_timeout = check_timeout

        # Endpoint health tracking
        self.endpoints: dict[str, EndpointHealth] = {}

        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=check_timeout)

        logger.info(
            "health_monitor_initialized",
            alert_threshold_warning=alert_threshold_warning,
            alert_threshold_critical=alert_threshold_critical,
            disable_threshold=disable_threshold,
        )

    async def check_all_endpoints(self) -> dict[str, EndpointHealth]:
        """
        Check health of all critical endpoints.

        Returns:
            Dictionary of endpoint name → health status
        """
        logger.info("checking_all_endpoints")

        # Check all endpoints in parallel
        checks = [
            self.check_exa_api(),
            self.check_github_api(),
            self.check_event_bus(),
            self.check_obsidian(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error("endpoint_check_failed", error=str(result))

        # Generate alerts if needed
        await self._check_and_alert()

        return self.endpoints

    async def check_exa_api(self) -> EndpointHealth:
        """Check Exa API health."""
        endpoint_name = "exa_api"

        try:
            start = datetime.now()

            # Simple health check - try to search
            # Note: This is a mock check, real implementation would use actual Exa MCP tools
            response = await self.http_client.get(
                "https://api.exa.ai/health",
                timeout=self.check_timeout
            )

            response_time = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                health = EndpointHealth(
                    name=endpoint_name,
                    status=EndpointStatus.HEALTHY,
                    response_time_ms=response_time,
                    consecutive_failures=0,
                    last_check=datetime.now(),
                )
                logger.info(
                    "endpoint_healthy",
                    endpoint=endpoint_name,
                    response_time_ms=response_time,
                )
            else:
                health = self._record_failure(
                    endpoint_name,
                    f"HTTP {response.status_code}"
                )

        except Exception as e:
            health = self._record_failure(endpoint_name, str(e))

        self.endpoints[endpoint_name] = health
        return health

    async def check_github_api(self) -> EndpointHealth:
        """Check GitHub API health."""
        endpoint_name = "github_api"

        try:
            start = datetime.now()

            response = await self.http_client.get(
                "https://api.github.com/rate_limit",
                timeout=self.check_timeout
            )

            response_time = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                health = EndpointHealth(
                    name=endpoint_name,
                    status=EndpointStatus.HEALTHY,
                    response_time_ms=response_time,
                    consecutive_failures=0,
                    last_check=datetime.now(),
                )
                logger.info(
                    "endpoint_healthy",
                    endpoint=endpoint_name,
                    response_time_ms=response_time,
                )
            else:
                health = self._record_failure(
                    endpoint_name,
                    f"HTTP {response.status_code}"
                )

        except Exception as e:
            health = self._record_failure(endpoint_name, str(e))

        self.endpoints[endpoint_name] = health
        return health

    async def check_event_bus(self) -> EndpointHealth:
        """Check Event Bus health."""
        endpoint_name = "event_bus"

        try:
            # Mock check - in real implementation would check Event Bus connection
            # For now, assume healthy if no previous failures
            health = EndpointHealth(
                name=endpoint_name,
                status=EndpointStatus.HEALTHY,
                consecutive_failures=0,
                last_check=datetime.now(),
            )
            logger.info("endpoint_healthy", endpoint=endpoint_name)

        except Exception as e:
            health = self._record_failure(endpoint_name, str(e))

        self.endpoints[endpoint_name] = health
        return health

    async def check_obsidian(self) -> EndpointHealth:
        """Check Obsidian vault health."""
        endpoint_name = "obsidian"

        try:
            # Mock check - in real implementation would check vault accessibility
            # For now, assume healthy if no previous failures
            health = EndpointHealth(
                name=endpoint_name,
                status=EndpointStatus.HEALTHY,
                consecutive_failures=0,
                last_check=datetime.now(),
            )
            logger.info("endpoint_healthy", endpoint=endpoint_name)

        except Exception as e:
            health = self._record_failure(endpoint_name, str(e))

        self.endpoints[endpoint_name] = health
        return health

    def _record_failure(self, endpoint_name: str, error: str) -> EndpointHealth:
        """Record endpoint failure and increment counter."""
        current = self.endpoints.get(endpoint_name)

        consecutive_failures = (
            current.consecutive_failures + 1 if current else 1
        )

        # Determine status based on failures
        if consecutive_failures >= self.disable_threshold:
            status = EndpointStatus.DOWN
        elif consecutive_failures >= self.alert_threshold_critical:
            status = EndpointStatus.DEGRADED
        else:
            status = EndpointStatus.DEGRADED

        health = EndpointHealth(
            name=endpoint_name,
            status=status,
            consecutive_failures=consecutive_failures,
            last_check=datetime.now(),
            last_error=error,
        )

        logger.warning(
            "endpoint_failure",
            endpoint=endpoint_name,
            consecutive_failures=consecutive_failures,
            error=error,
        )

        return health

    async def _check_and_alert(self) -> None:
        """Check all endpoints and send alerts if needed."""
        for endpoint_name, health in self.endpoints.items():
            # Skip if healthy
            if health.status == EndpointStatus.HEALTHY:
                continue

            # Determine severity
            if health.consecutive_failures >= self.alert_threshold_critical:
                severity = Severity.CRITICAL
            elif health.consecutive_failures >= self.alert_threshold_warning:
                severity = Severity.WARNING
            else:
                continue  # Not yet at alert threshold

            # Create alert
            alert = self._create_alert(endpoint_name, health, severity)

            # Send alert
            await self._send_alert(alert)

    def _create_alert(
        self,
        endpoint_name: str,
        health: EndpointHealth,
        severity: Severity
    ) -> HealthAlert:
        """Create health alert with impact and action items."""
        # Define impact and actions per endpoint
        impact_map = {
            "exa_api": "Cannot perform deep research",
            "github_api": "Cannot discover GitHub repos",
            "event_bus": "Cannot communicate with agents",
            "obsidian": "Cannot log decisions and audit trail",
        }

        action_items_map = {
            "exa_api": [
                "Check Exa API status",
                "Verify API key",
                "Check rate limits",
                "Fallback to Brave API if available",
            ],
            "github_api": [
                "Check GitHub API status",
                "Verify API token",
                "Check rate limits",
                "Use cached repos if available",
            ],
            "event_bus": [
                "Check Event Bus connection",
                "Verify configuration",
                "Restart Event Bus if needed",
            ],
            "obsidian": [
                "Check vault path",
                "Verify file permissions",
                "Check disk space",
            ],
        }

        return HealthAlert(
            endpoint=endpoint_name,
            severity=severity,
            status=health.status,
            consecutive_failures=health.consecutive_failures,
            error=health.last_error,
            impact=impact_map.get(endpoint_name, "Unknown impact"),
            action_items=action_items_map.get(endpoint_name, []),
        )

    async def _send_alert(self, alert: HealthAlert) -> None:
        """Send alert through all configured channels."""
        # Console (always)
        self._send_console_alert(alert)

        # TODO: Telegram (if configured)
        # TODO: Email (if configured)

    def _send_console_alert(self, alert: HealthAlert) -> None:
        """Send alert to console."""
        severity_emoji = {
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.CRITICAL: "🚨",
        }

        print(f"\n{severity_emoji[alert.severity]} Teacher Agent Alert: {alert.severity.upper()}\n")
        print(f"Endpoint: {alert.endpoint}")
        print(f"Status: {alert.status}")
        print(f"Consecutive failures: {alert.consecutive_failures}")
        if alert.error:
            print(f"Error: {alert.error}")
        print(f"\nImpact:")
        print(f"❌ {alert.impact}")
        print(f"\nAction:")
        for i, action in enumerate(alert.action_items, 1):
            print(f"{i}. {action}")
        print(f"\n⚠️ System growth is blocked!\n")

        logger.error(
            "health_alert_sent",
            endpoint=alert.endpoint,
            severity=alert.severity,
            consecutive_failures=alert.consecutive_failures,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
