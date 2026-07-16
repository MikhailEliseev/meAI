"""Health check system"""

from datetime import datetime, timezone
from typing import Callable, Coroutine, Any
import structlog

logger = structlog.get_logger()


class HealthChecker:
    """System health checker"""

    def __init__(self):
        """Initialize Health Checker"""
        self.components: dict[str, Callable[[], Coroutine[Any, Any, dict]]] = {}
        self.start_time = datetime.now(timezone.utc)

    def register_component(
        self,
        name: str,
        health_check: Callable[[], Coroutine[Any, Any, dict]],
    ) -> None:
        """Register component health check

        Args:
            name: Component name
            health_check: Async function that returns health status dict
        """
        self.components[name] = health_check
        logger.debug("health.component_registered", component=name)

    async def check_health(self) -> dict[str, Any]:
        """Check health of all components

        Returns:
            Health status dictionary with overall status and component details
        """
        components_health = {}
        overall_healthy = True

        for name, check_func in self.components.items():
            try:
                result = await check_func()
                components_health[name] = result

                if result.get("status") != "healthy":
                    overall_healthy = False

            except Exception as e:
                logger.error("health.check_failed", component=name, error=str(e))
                components_health[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                overall_healthy = False

        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": components_health,
        }

    async def check_component(self, name: str) -> dict[str, Any]:
        """Check health of specific component

        Args:
            name: Component name

        Returns:
            Component health status dictionary
        """
        if name not in self.components:
            return {"status": "unknown", "error": "Component not registered"}

        try:
            return await self.components[name]()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
