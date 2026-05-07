"""
Content Orchestrator - Coordinates Content generation tasks

Real implementation with ContentWriterAgent integration.
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
import asyncio
import logging
from pathlib import Path

from meai.agents.base_agent import Agent, Task, TaskResult, TaskStatus
from meai.events.event_bus import EventBus

# Import ContentWriterAgent
import sys
aim_path = Path(__file__).parent.parent.parent.parent
if str(aim_path) not in sys.path:
    sys.path.insert(0, str(aim_path))

from aim.subagents.content_writer_agent import ContentWriterAgent

logger = logging.getLogger(__name__)


class ContentOrchestrator(Agent):
    """Content Orchestrator - Coordinates Content generation tasks

    Responsibilities:
    - Execute Content generation tasks
    - Coordinate SEO agents
    - Provide progress callbacks
    - Aggregate results
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "AIM/obsidian/content-orchestrator"
    ):
        super().__init__(agent_id, database_url, vault_path)
        self.event_bus = event_bus

    def get_capabilities(self) -> list[str]:
        """Get Content Orchestrator capabilities"""
        return [
            "content_generation",
            "content_optimization",
            "technical_audit"
        ]

    async def execute_content_generation(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute Content generation

        Args:
            task_data: Task data dict with:
                - task_id: Task identifier
                - content_type: "keyword" | "content" | "technical"
                - target: URL or keyword
                - niche: Business niche
                - geo: Geographic location
            progress_callback: Async callback for progress updates
                               Called with (step: int, status: str, message: str)

        Returns:
            Dict with Content generation results:
                - task_id: Task identifier
                - content_type: Analysis type used
                - results: Analysis results dict
                - execution_time_seconds: Total execution time
                - errors: List of error messages
        """
        start_time = datetime.now()
        content_type = task_data.get("content_type", "keyword")
        task_id = task_data.get("task_id", "unknown")

        try:
            # Progress update: starting
            if progress_callback:
                await progress_callback(1, "in_progress", f"Starting {content_type} analysis")

            # Execute analysis based on type
            if content_type == "keyword":
                results = await self._execute_content_generation(task_data, progress_callback)
            elif content_type == "content":
                results = await self._execute_content_optimization(task_data, progress_callback)
            elif content_type == "technical":
                results = await self._execute_readability_analysis(task_data, progress_callback)
            else:
                results = {"error": f"Unknown analysis type: {content_type}"}

            # Progress update: completed
            if progress_callback:
                await progress_callback(2, "completed", "Analysis complete")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Return structured result
            return {
                "task_id": task_id,
                "content_type": content_type,
                "results": results,
                "execution_time_seconds": int(execution_time),
                "errors": []
            }

        except Exception as e:
            logger.error(f"Content generation failed: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "content_type": content_type,
                "results": {},
                "execution_time_seconds": 0,
                "errors": [f"Content generation failed: {str(e)}"]
            }

    async def _execute_content_generation(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute content generation using ContentWriterAgent"""

        topic = task_data.get("target", "") or task_data.get("topic", "")
        content_type = task_data.get("content_type", "article")
        niche = task_data.get("niche", "")

        if not topic:
            return {
                "status": "error",
                "error": "'topic' or 'target' is required"
            }

        # Progress update
        if progress_callback:
            await progress_callback(1, "in_progress", "Initializing content generation")

        # Create ContentWriterAgent
        content_agent = ContentWriterAgent(
            agent_id=f"content-writer-{task_data.get('task_id', 'unknown')}",
            event_bus=self.event_bus
        )

        # Prepare task for agent
        agent_task = Task(
            task_id=task_data.get("task_id", "unknown"),
            subtask_id=f"content-{task_data.get('task_id', 'unknown')}",
            action="write_content",
            payload={
                "topic": topic,
                "content_type": content_type,
                "niche": niche,
                "tone": task_data.get("tone", "professional"),
                "length": task_data.get("length", "medium")
            },
            priority=1
        )

        # Progress update
        if progress_callback:
            await progress_callback(2, "in_progress", "Generating content")

        # Execute content generation
        result = await content_agent.execute_task(agent_task)

        # Progress update
        if progress_callback:
            await progress_callback(3, "completed", "Content generation complete")

        # Return results
        if result.status == "success":
            return {
                "topic": topic,
                "content_type": content_type,
                "content": result.result.get("content", ""),
                "word_count": result.result.get("word_count", 0),
                "status": "completed"
            }
        else:
            return {
                "status": "error",
                "error": result.error or "Content generation failed"
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
            "content_type": task.payload.get("content_type", "keyword"),
            "target": task.payload.get("target", ""),
            "niche": task.payload.get("niche", ""),
            "geo": task.payload.get("geo", "")
        }

        # Execute analysis
        result = await self.execute_content_generation(task_data)

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
