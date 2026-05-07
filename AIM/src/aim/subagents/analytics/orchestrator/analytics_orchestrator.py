"""
Analytics Orchestrator - Coordinates Metrics tracking tasks

Real implementation with AnalyticsAgent integration.
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
import asyncio
import logging
from pathlib import Path

from meai.agents.base_agent import Agent, Task, TaskResult, TaskStatus
from meai.events.event_bus import EventBus

# Import AnalyticsAgent
import sys
aim_path = Path(__file__).parent.parent.parent.parent
if str(aim_path) not in sys.path:
    sys.path.insert(0, str(aim_path))

from aim.subagents.analytics_agent import AnalyticsAgent

logger = logging.getLogger(__name__)


class AnalyticsOrchestrator(Agent):
    """Analytics Orchestrator - Coordinates Campaign creation tasks

    Responsibilities:
    - Execute Campaign creation tasks
    - Coordinate SEO agents
    - Provide progress callbacks
    - Aggregate results
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "AIM/obsidian/analytics-orchestrator"
    ):
        super().__init__(agent_id, database_url, vault_path)
        self.event_bus = event_bus

    def get_capabilities(self) -> list[str]:
        """Get Analytics Orchestrator capabilities"""
        return [
            "content_generation",
            "content_optimization",
            "technical_audit"
        ]

    async def execute_metrics_tracking(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute Campaign creation

        Args:
            task_data: Task data dict with:
                - task_id: Task identifier
                - metrics_type: "keyword" | "content" | "technical"
                - target: URL or keyword
                - niche: Business niche
                - geo: Geographic location
            progress_callback: Async callback for progress updates
                               Called with (step: int, status: str, message: str)

        Returns:
            Dict with Campaign creation results:
                - task_id: Task identifier
                - metrics_type: Analysis type used
                - results: Analysis results dict
                - execution_time_seconds: Total execution time
                - errors: List of error messages
        """
        start_time = datetime.now()
        metrics_type = task_data.get("metrics_type", "keyword")
        task_id = task_data.get("task_id", "unknown")

        try:
            # Progress update: starting
            if progress_callback:
                await progress_callback(1, "in_progress", f"Starting {metrics_type} analysis")

            # Execute analysis based on type
            if metrics_type == "keyword":
                results = await self._execute_metrics_tracking(task_data, progress_callback)
            elif metrics_type == "content":
                results = await self._execute_content_optimization(task_data, progress_callback)
            elif metrics_type == "technical":
                results = await self._execute_readability_analysis(task_data, progress_callback)
            else:
                results = {"error": f"Unknown analysis type: {metrics_type}"}

            # Progress update: completed
            if progress_callback:
                await progress_callback(2, "completed", "Analysis complete")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Return structured result
            return {
                "task_id": task_id,
                "metrics_type": metrics_type,
                "results": results,
                "execution_time_seconds": int(execution_time),
                "errors": []
            }

        except Exception as e:
            logger.error(f"Campaign creation failed: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "metrics_type": metrics_type,
                "results": {},
                "execution_time_seconds": 0,
                "errors": [f"Campaign creation failed: {str(e)}"]
            }

    async def _execute_metrics_tracking(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute metrics tracking using AnalyticsAgent"""

        metrics_type = task_data.get("metrics_type", "kpi")
        source = task_data.get("source", "") or task_data.get("target", "")

        # Progress update
        if progress_callback:
            await progress_callback(1, "in_progress", "Initializing metrics tracking")

        # Create AnalyticsAgent
        analytics_agent = AnalyticsAgent(
            agent_id=f"analytics-{task_data.get('task_id', 'unknown')}",
            event_bus=self.event_bus
        )

        # Prepare task for agent
        agent_task = Task(
            task_id=task_data.get("task_id", "unknown"),
            subtask_id=f"metrics-{task_data.get('task_id', 'unknown')}",
            action="track_metrics",
            payload={
                "metrics_type": metrics_type,
                "source": source
            },
            priority=1
        )

        # Progress update
        if progress_callback:
            await progress_callback(2, "in_progress", "Tracking metrics")

        # Execute metrics tracking
        result = await analytics_agent.execute_task(agent_task)

        # Progress update
        if progress_callback:
            await progress_callback(3, "completed", "Metrics tracking complete")

        # Return results
        if result.status == "success":
            return {
                "metrics_type": metrics_type,
                "source": source,
                "metrics": result.result.get("metrics", {}),
                "status": "completed"
            }
        else:
            return {
                "status": "error",
                "error": result.error or "Metrics tracking failed"
            }

    async def _execute_content_optimization(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute content optimization (stub)"""

        # Stub implementation
        await asyncio.sleep(0.1)

        return {
            "status": "stub",
            "message": "Content optimization not implemented yet"
        }

    async def _execute_readability_analysis(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute technical SEO audit (stub)"""

        # Stub implementation
        await asyncio.sleep(0.1)

        return {
            "status": "stub",
            "message": "Technical audit not implemented yet"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute task (required by Agent base class)"""

        # Convert Task to task_data dict
        task_data = {
            "task_id": task.task_id,
            "metrics_type": task.payload.get("metrics_type", "keyword"),
            "target": task.payload.get("target", ""),
            "niche": task.payload.get("niche", ""),
            "geo": task.payload.get("geo", "")
        }

        # Execute analysis
        result = await self.execute_metrics_tracking(task_data)

        # Return TaskResult
        return TaskResult(
            subtask_id=task.subtask_id,
            agent_id=self.agent_id,
            action=task.action,
            status="success" if not result["errors"] else "failed",
            result=result,
            error=result["errors"][0] if result["errors"] else None,
            duration_seconds=result["execution_time_seconds"],
            completed_at=datetime.now(timezone.utc)
        )
