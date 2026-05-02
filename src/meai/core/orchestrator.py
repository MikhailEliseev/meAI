"""Orchestrator - async coordination of components"""

import asyncio
from typing import Any, Callable, Coroutine
import structlog

logger = structlog.get_logger()


class Orchestrator:
    """Coordinate async operations across components"""

    def __init__(self):
        self.components: dict[str, Callable[[], Coroutine[Any, Any, dict]]] = {}
        self.tasks: list[asyncio.Task] = []

    def register_component(
        self,
        name: str,
        health_check: Callable[[], Coroutine[Any, Any, dict]],
    ) -> None:
        """Register component for orchestration"""
        self.components[name] = health_check
        logger.debug("orchestrator.component_registered", component=name)

    async def check_all_components(self) -> dict[str, dict]:
        """Check health of all components in parallel"""
        results = {}

        tasks = []
        for name, check_func in self.components.items():
            task = asyncio.create_task(check_func())
            tasks.append((name, task))

        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error("orchestrator.check_failed", component=name, error=str(e))
                results[name] = {"status": "error", "error": str(e)}

        return results

    async def execute_workflow(
        self,
        workflow: list[Callable[[], Coroutine[Any, Any, Any]]],
    ) -> list[Any]:
        """Execute workflow steps sequentially"""
        results = []

        for i, step in enumerate(workflow):
            logger.info("orchestrator.workflow_step", step=i + 1, total=len(workflow))
            try:
                result = await step()
                results.append(result)
            except Exception as e:
                logger.error("orchestrator.workflow_failed", step=i + 1, error=str(e))
                raise

        return results

    async def execute_parallel(
        self,
        operations: list[Callable[[], Coroutine[Any, Any, Any]]],
    ) -> list[Any]:
        """Execute operations in parallel"""
        tasks = [asyncio.create_task(op()) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
