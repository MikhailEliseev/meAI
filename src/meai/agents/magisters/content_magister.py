"""Content Magister - Content creation specialist agent"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import EventBus, Message

logger = logging.getLogger(__name__)


class ContentMagister(BaseMagister):
    """Content Magister - Content creation specialist

    Domain: Content Creation and Optimization

    Capabilities:
    - generate_content: Keyword research and analysis
    - optimize_content: Content SEO optimization
    - analyze_readability: Technical SEO audit
    - generate_ideas: Competitor SEO analysis
    - check_quality: Position tracking
    """

    def __init__(
        self,
        agent_id: str = "content-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        orchestrators: dict[str, Any] = None,
    ):
        """Initialize Content Magister

        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            vault_path: Path to Obsidian vault
            database_url: Database URL
            orchestrators: Dict of orchestrator name -> orchestrator instance
                          e.g., {"ci": ContentOrchestrator(...)}
        """
        if vault_path is None:
            vault_path = Path("./obsidian/content-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="content",
            domain="content",
            event_bus=event_bus,
            vault_path=vault_path,
            database_url=database_url,
        )

        # Initialize orchestrators
        if orchestrators is None:
            # Auto-create Content orchestrator if not provided
            from AIM.src.aim.subagents.content.orchestrator.content_orchestrator import ContentOrchestrator

            self.orchestrators = {
                "content": ContentOrchestrator(
                    agent_id=f"{agent_id}-content-orchestrator",
                    event_bus=event_bus,
                    database_url=database_url,
                )
            }
        else:
            self.orchestrators = orchestrators

        self.current_task_id = None

    def get_capabilities(self) -> list[str]:
        """Get Content Magister capabilities"""
        base_capabilities = super().get_capabilities()

        seo_capabilities = [
            "generate_content",
            "optimize_content",
            "analyze_readability",
            "generate_ideas",
            "check_quality",
        ]

        return base_capabilities + seo_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute SEO-specific task

        Routes to appropriate handler based on action:
        - generate_content → _handle_content_generation()
        - optimize_content → _handle_content_optimization()
        - analyze_readability → _handle_readability_analysis()
        """
        self.current_task_id = task.task_id
        action = task.data.get("action", "")

        logger.info(f"Content Magister executing task: {task.task_id}, action: {action}")

        try:
            if action == "generate_content":
                return await self._handle_content_generation(task)
            elif action == "optimize_content":
                return await self._handle_content_optimization(task)
            elif action == "analyze_readability":
                return await self._handle_readability_analysis(task)
            else:
                return await self._handle_generic_content(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return self._create_error_result(task, e)
        finally:
            self.current_task_id = None

    async def _handle_content_generation(self, task: Task) -> TaskResult:
        """Handle content generation via Content orchestrator"""
        logger.info(f"Handling content generation for task {task.task_id}")

        try:
            # 1. Get orchestrator via dependency injection
            orchestrator = self.orchestrators.get("content")
            if not orchestrator:
                raise ValueError("Content orchestrator not registered")

            # 2. Create Content task data
            content_task_data = {
                "task_id": task.task_id,
                "content_type": "keyword",
                "target": task.data.get("target", ""),
                "niche": task.data.get("niche", ""),
                "geo": task.data.get("geo", ""),
            }

            # 3. Set timeout
            timeout_seconds = 300  # 5 min

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting content generation")

            content_result = await asyncio.wait_for(
                orchestrator.execute_content_generation(
                    content_task_data,
                    progress_callback=self._publish_progress
                ),
                timeout=timeout_seconds
            )

            # 5. Validate result
            validated_result = self._validate_content_result(content_result)

            # 6. Store in vault
            await self._store_content_result(validated_result)

            await self._publish_progress(100, "completed", "Content generation complete")

            # 7. Return result
            return TaskResult(
                subtask_id=task.task_id,
                agent_id=self.agent_id,
                action=task.data.get("action", "generate_content"),
                status="success",
                result=validated_result,
                error=None,
                duration_seconds=content_result.get("execution_time_seconds", 0),
                completed_at=datetime.now(timezone.utc)
            )

        except asyncio.TimeoutError:
            logger.error(f"Content generation timed out after {timeout_seconds}s")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Content generation failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _publish_progress(self, phase: int, status: str, message: str) -> None:
        """Publish progress update via Event Bus

        Args:
            phase: Phase number (0-100 for percentage, or phase number)
            status: Status string (started, in_progress, completed, failed)
            message: Human-readable progress message
        """
        if not self.event_bus or not self.current_task_id:
            return

        try:
            await self.event_bus.publish(Message(
                from_agent=self.agent_id,
                to_agent="operator-1",
                message_type="task_progress",
                priority=2,  # P2 = Normal
                payload={
                    "task_id": self.current_task_id,
                    "agent_id": self.agent_id,
                    "phase": phase,
                    "status": status,
                    "message": message
                },
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
            logger.debug(f"Progress published: phase={phase}, status={status}")
        except Exception as e:
            logger.warning(f"Failed to publish progress: {e}")

    def _validate_content_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Validate Content result structure

        Args:
            result: Content result dictionary

        Returns:
            Validated result

        Raises:
            ValueError: If validation fails
        """
        logger.debug("Validating Content result")

        try:
            # Validate required fields
            if not result.get("task_id"):
                raise ValueError("Missing task_id in Content result")

            # Check for errors
            if result.get("errors"):
                raise ValueError(f"Content generation had errors: {result['errors']}")

            # Validate results exist
            if not result.get("results"):
                raise ValueError("Missing results in Content result")

            logger.info(f"Content result validated: {result.get('content_type', 'unknown')} generation")
            return result

        except (ValueError, KeyError) as e:
            logger.error(f"Content result validation failed: {e}")
            raise ValueError(f"Invalid Content result: {e}")
            reports = result.get("reports", {})
            if reports:
                for report_type, path in reports.items():
                    if path and not Path(path).exists():
                        logger.warning(f"Report file not found: {path}")

            logger.info(f"CI result validated: {competitors_analyzed} competitors analyzed")
            return result

        except (ValueError, KeyError) as e:
            logger.error(f"CI result validation failed: {e}")
            raise ValueError(f"Invalid CI result: {e}")

    async def _store_content_result(self, result: dict[str, Any]) -> None:
        """Store Content result in Obsidian vault

        Args:
            result: Validated Content result
        """
        try:
            task_id = result.get("task_id", "unknown")
            content_type = result.get("content_type", "unknown")
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

            filename = f"{timestamp}-content-{content_type}-{task_id}.md"
            filepath = Path(self.vault_path) / "results" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Create markdown content
            content = f"""# Content Generation Result

**Task ID:** {task_id}
**Content Type:** {content_type}
**Timestamp:** {timestamp}

## Results

```json
{result}
```

## Summary

- Execution Time: {result.get('execution_time_seconds', 0)}s
- Status: {'Success' if not result.get('errors') else 'Failed'}
"""

            filepath.write_text(content)
            logger.info(f"Content result stored: {filepath}")

        except Exception as e:
            logger.error(f"Failed to store Content result: {e}", exc_info=True)
            # Don't raise - storage failure shouldn't fail the task

    async def _handle_content_optimization(self, task: Task) -> TaskResult:
        """Handle content optimization via Content orchestrator"""
        logger.info(f"Handling content optimization for task {task.task_id}")

        try:
            orchestrator = self.orchestrators.get("content")
            if not orchestrator:
                raise ValueError("Content orchestrator not registered")

            content_task_data = {
                "task_id": task.task_id,
                "content_type": "content",
                "target": task.data.get("target", ""),
                "niche": task.data.get("niche", ""),
                "geo": task.data.get("geo", ""),
            }

            await self._publish_progress(0, "started", "Starting content optimization")

            content_result = await asyncio.wait_for(
                orchestrator.execute_content_generation(content_task_data, progress_callback=self._publish_progress),
                timeout=300
            )

            validated_result = self._validate_content_result(content_result)
            await self._store_content_result(validated_result)
            await self._publish_progress(100, "completed", "Content optimization complete")

            return TaskResult(
                subtask_id=task.task_id,
                agent_id=self.agent_id,
                action=task.data.get("action", "optimize_content"),
                status="success",
                result=validated_result,
                error=None,
                duration_seconds=content_result.get("execution_time_seconds", 0),
                completed_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Content optimization failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_readability_analysis(self, task: Task) -> TaskResult:
        """Handle readability analysis via Content orchestrator"""
        logger.info(f"Handling readability analysis for task {task.task_id}")

        try:
            orchestrator = self.orchestrators.get("content")
            if not orchestrator:
                raise ValueError("Content orchestrator not registered")

            content_task_data = {
                "task_id": task.task_id,
                "content_type": "technical",
                "target": task.data.get("target", ""),
                "niche": task.data.get("niche", ""),
                "geo": task.data.get("geo", ""),
            }

            await self._publish_progress(0, "started", "Starting readability analysis")

            content_result = await asyncio.wait_for(
                orchestrator.execute_content_generation(content_task_data, progress_callback=self._publish_progress),
                timeout=300
            )

            validated_result = self._validate_content_result(content_result)
            await self._store_content_result(validated_result)
            await self._publish_progress(100, "completed", "Readability analysis complete")

            return TaskResult(
                subtask_id=task.task_id,
                agent_id=self.agent_id,
                action=task.data.get("action", "analyze_readability"),
                status="success",
                result=validated_result,
                error=None,
                duration_seconds=content_result.get("execution_time_seconds", 0),
                completed_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Readability analysis failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_generic_content(self, task: Task) -> TaskResult:
        """Handle generic intelligence task via knowledge search

        Falls back to hybrid search when no specific handler exists
        """
        logger.info(f"Handling generic intelligence for task {task.task_id}")

        try:
            # Use hybrid search from BaseMagister
            query = task.description
            results = await self.search_knowledge(
                query=query,
                search_local=True,
                search_teacher=True,
                search_researcher=False,  # Don't trigger researcher for generic tasks
            )

            return TaskResult(
                subtask_id=task.task_id,
                agent_id=self.agent_id,
                action=task.data.get("action", "generic"),
                status="success",
                result={
                    "query": query,
                    "results": results,
                    "source": "knowledge_search"
                },
                error=None,
                duration_seconds=0.0,
                completed_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Generic intelligence task failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    def _create_timeout_result(self, task: Task, timeout_seconds: int) -> TaskResult:
        """Create timeout error result"""
        return TaskResult(
            subtask_id=task.task_id,
            agent_id=self.agent_id,
            action=task.data.get("action", "unknown"),
            status="failed",
            result={},
            error=f"Task timed out after {timeout_seconds} seconds",
            duration_seconds=float(timeout_seconds),
            completed_at=datetime.now(timezone.utc)
        )

    def _create_error_result(self, task: Task, error: Exception) -> TaskResult:
        """Create error result"""
        return TaskResult(
            subtask_id=task.task_id,
            agent_id=self.agent_id,
            action=task.data.get("action", "unknown"),
            status="failed",
            result={},
            error=f"{type(error).__name__}: {str(error)}",
            duration_seconds=0.0,
            completed_at=datetime.now(timezone.utc)
        )
