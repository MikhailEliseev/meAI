"""Analytics Magister - Analytics specialist agent"""

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


class AnalyticsMagister(BaseMagister):
    """Analytics Magister - Analytics specialist

    Domain: Analytics and Metrics

    Capabilities:
    - track_metrics: Keyword research and analysis
    - analyze_data: Content SEO optimization
    - generate_reports: Technical SEO audit
    - segment_users: Competitor SEO analysis
    - monitor_kpis: Position tracking
    """

    def __init__(
        self,
        agent_id: str = "analytics-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        orchestrators: dict[str, Any] = None,
    ):
        """Initialize Analytics Magister

        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            vault_path: Path to Obsidian vault
            database_url: Database URL
            orchestrators: Dict of orchestrator name -> orchestrator instance
                          e.g., {"ci": AnalyticsOrchestrator(...)}
        """
        if vault_path is None:
            vault_path = Path("./obsidian/analytics-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="analytics",
            domain="analytics",
            event_bus=event_bus,
            vault_path=vault_path,
            database_url=database_url,
        )

        self.orchestrators = orchestrators or {}
        self.current_task_id = None

    def get_capabilities(self) -> list[str]:
        """Get Analytics Magister capabilities"""
        base_capabilities = super().get_capabilities()

        seo_capabilities = [
            "track_metrics",
            "analyze_data",
            "generate_reports",
            "segment_users",
            "monitor_kpis",
        ]

        return base_capabilities + seo_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute SEO-specific task

        Routes to appropriate handler based on action:
        - track_metrics → _handle_metrics_tracking()
        - analyze_data → _handle_data_analysis()
        - generate_reports → _handle_report_generation()
        """
        self.current_task_id = task.task_id
        action = task.data.get("action", "")

        logger.info(f"Analytics Magister executing task: {task.task_id}, action: {action}")

        try:
            if action == "track_metrics":
                return await self._handle_metrics_tracking(task)
            elif action == "analyze_data":
                return await self._handle_data_analysis(task)
            elif action == "generate_reports":
                return await self._handle_report_generation(task)
            else:
                return await self._handle_generic_analytics(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return self._create_error_result(task, e)
        finally:
            self.current_task_id = None

    async def _handle_metrics_tracking(self, task: Task) -> TaskResult:
        """Handle competitor analysis via Content system"""
        logger.info(f"Handling competitor analysis for task {task.task_id}")

        try:
            # 1. Get orchestrator via dependency injection
            orchestrator = self.orchestrators.get("ci")
            if not orchestrator:
                raise ValueError("CI orchestrator not registered")

            # 2. Create CI task from Intelligence task
            ci_task_data = {
                "task_id": task.task_id,
                "niche": task.data.get("niche", ""),
                "geo": task.data.get("geo", ""),
                "segment_users": task.data.get("segment_users", ""),
                "price_segment": task.data.get("price_segment", "mid"),
                "tier": task.data.get("depth", "deep"),
                "competitors": task.data.get("competitors", []),
                "deadline": task.deadline,
            }

            # 3. Set timeout based on tier
            tier = ci_task_data["tier"]
            timeout_seconds = {
                "quick": 900,   # 15 min
                "deep": 2700,   # 45 min
                "full": 5400    # 90 min
            }.get(tier, 2700)

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", f"Starting {tier} CI analysis")

            ci_result = await asyncio.wait_for(
                orchestrator.execute_ci_analysis(
                    ci_task_data,
                    progress_callback=self._publish_progress
                ),
                timeout=timeout_seconds
            )

            # 5. Validate result
            validated_result = self._validate_analytics_result(ci_result)

            # 6. Store in vault
            await self._store_analytics_result(validated_result)

            await self._publish_progress(100, "completed", "CI analysis complete")

            # 7. Return result
            return TaskResult(
                subtask_id=task.task_id,
                agent_id=self.agent_id,
                action=task.data.get("action", "track_metrics"),
                status="success",
                result=validated_result,
                error=None,
                duration_seconds=(datetime.now(timezone.utc) - datetime.now(timezone.utc)).total_seconds(),
                completed_at=datetime.now(timezone.utc)
            )

        except asyncio.TimeoutError:
            logger.error(f"CI analysis timed out after {timeout_seconds}s")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}", exc_info=True)
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

    def _validate_analytics_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Validate CI result structure

        Args:
            result: CI result dictionary

        Returns:
            Validated result

        Raises:
            ValueError: If validation fails
        """
        logger.debug("Validating CI result")

        try:
            # Validate required fields
            if not result.get("task_id"):
                raise ValueError("Missing task_id in CI result")

            if not result.get("findings"):
                raise ValueError("Missing findings in CI result")

            competitors_analyzed = result.get("competitors_analyzed", 0)
            if competitors_analyzed < 1:
                raise ValueError("No competitors analyzed")

            # Validate reports exist if specified
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

    async def _store_analytics_result(self, result: dict[str, Any]) -> None:
        """Store CI result in Obsidian vault

        Args:
            result: Validated CI result
        """
        try:
            # Create markdown file in vault
            task_id = result.get("task_id", "unknown")
            result_file = self.vault_path / "wiki" / "sources" / f"ci-{task_id}.md"

            # Format findings for markdown
            findings = result.get("findings", {})
            findings_json = json.dumps(findings, indent=2, ensure_ascii=False)

            # Create content
            content = f"""---
type: ci-analysis
task_id: {task_id}
tier: {result.get('tier', 'unknown')}
date: {datetime.now(timezone.utc).isoformat()}
status: processed
competitors_analyzed: {result.get('competitors_analyzed', 0)}
execution_time: {result.get('execution_time_seconds', 0)}s
---

# CI Analysis: {task_id}

## Summary
- **Tier:** {result.get('tier', 'unknown')}
- **Phases:** {result.get('phases_executed', [])}
- **Competitors:** {result.get('competitors_analyzed', 0)}
- **Time:** {result.get('execution_time_seconds', 0)}s

## Findings

```json
{findings_json}
```

## Reports
- **PDF:** {result.get('reports', {}).get('pdf_path', 'N/A')}
- **HTML:** {result.get('reports', {}).get('html_path', 'N/A')}

## Errors
{result.get('errors', [])}
"""

            # Write to vault
            result_file.parent.mkdir(parents=True, exist_ok=True)
            result_file.write_text(content, encoding='utf-8')

            logger.info(f"CI result stored in vault: {result_file}")

        except Exception as e:
            logger.error(f"Failed to store CI result: {e}", exc_info=True)
            # Don't raise - storage failure shouldn't fail the task

    async def _handle_data_analysis(self, task: Task) -> TaskResult:
        """Handle market research task

        TODO: Implement market research logic
        For now, uses generic knowledge search
        """
        logger.info(f"Handling market research for task {task.task_id}")
        return await self._handle_generic_analytics(task)

    async def _handle_report_generation(self, task: Task) -> TaskResult:
        """Handle trend analysis task

        TODO: Implement trend analysis logic
        For now, uses generic knowledge search
        """
        logger.info(f"Handling trend analysis for task {task.task_id}")
        return await self._handle_generic_analytics(task)

    async def _handle_generic_analytics(self, task: Task) -> TaskResult:
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
