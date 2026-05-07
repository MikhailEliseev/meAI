"""Ads Magister - Advertising specialist agent"""

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


class AdsMagister(BaseMagister):
    """Ads Magister - Advertising specialist

    Domain: Advertising and Campaign Management

    Capabilities:
    - create_campaign: Keyword research and analysis
    - optimize_ads: Content SEO optimization
    - analyze_performance: Technical SEO audit
    - target_audience: Competitor SEO analysis
    - track_conversions: Position tracking
    """

    def __init__(
        self,
        agent_id: str = "ads-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        orchestrators: dict[str, Any] = None,
    ):
        """Initialize Ads Magister

        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            vault_path: Path to Obsidian vault
            database_url: Database URL
            orchestrators: Dict of orchestrator name -> orchestrator instance
                          e.g., {"ci": AdsOrchestrator(...)}
        """
        if vault_path is None:
            vault_path = Path("./obsidian/ads-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="ads",
            domain="ads",
            event_bus=event_bus,
            vault_path=vault_path,
            database_url=database_url,
        )

        # Initialize orchestrators
        if orchestrators is None:
            # Auto-create Ads orchestrator if not provided
            from AIM.src.aim.subagents.ads.orchestrator.ads_orchestrator import AdsOrchestrator

            self.orchestrators = {
                "ads": AdsOrchestrator(
                    agent_id=f"{agent_id}-ads-orchestrator",
                    event_bus=event_bus,
                    database_url=database_url,
                )
            }
        else:
            self.orchestrators = orchestrators

        self.current_task_id = None

    def get_capabilities(self) -> list[str]:
        """Get Ads Magister capabilities"""
        base_capabilities = super().get_capabilities()

        ads_capabilities = [
            "create_campaign",
            "optimize_budget",
            "ab_test",
            "target_audience",
            "optimize_ads",
            "analyze_performance",
            "track_conversions",
        ]

        return base_capabilities + ads_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute SEO-specific task

        Routes to appropriate handler based on action:
        - create_campaign → _handle_campaign_creation()
        - optimize_ads → _handle_ads_optimization()
        - analyze_performance → _handle_performance_analysis()
        """
        self.current_task_id = task.task_id
        action = task.action

        logger.info(f"Ads Magister executing task: {task.task_id}, action: {action}")

        try:
            if action == "create_campaign":
                return await self._handle_campaign_creation(task)
            elif action == "optimize_budget":
                return await self._handle_campaign_creation(task)  # Same handler
            elif action == "ab_test":
                return await self._handle_campaign_creation(task)  # Same handler
            elif action == "target_audience":
                return await self._handle_campaign_creation(task)  # Same handler
            elif action == "optimize_ads":
                return await self._handle_ads_optimization(task)
            elif action == "analyze_performance":
                return await self._handle_performance_analysis(task)
            elif action == "track_conversions":
                return await self._handle_performance_analysis(task)  # Same handler
            else:
                return await self._handle_generic_ads(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return self._create_error_result(task, e)
        finally:
            self.current_task_id = None

    async def _handle_campaign_creation(self, task: Task) -> TaskResult:
        """Handle competitor analysis via Content system"""
        logger.info(f"Handling competitor analysis for task {task.task_id}")

        try:
            # 1. Get orchestrator via dependency injection
            orchestrator = self.orchestrators.get("ads")
            if not orchestrator:
                raise ValueError("Ads orchestrator not registered")

            # 2. Create CI task from Intelligence task
            ads_task_data = {
                "task_id": task.task_id,
                "niche": task.data.get("niche", ""),
                "geo": task.data.get("geo", ""),
                "target_audience": task.data.get("target_audience", ""),
                "price_segment": task.data.get("price_segment", "mid"),
                "tier": task.data.get("depth", "deep"),
                "competitors": task.data.get("competitors", []),            }

            # 3. Set timeout based on tier
            tier = ads_task_data["tier"]
            timeout_seconds = {
                "quick": 900,   # 15 min
                "deep": 2700,   # 45 min
                "full": 5400    # 90 min
            }.get(tier, 2700)

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", f"Starting {tier} CI analysis")

            ads_result = await asyncio.wait_for(
                orchestrator.execute_campaign_creation(
                    ads_task_data,
                    progress_callback=self._publish_progress
                ),
                timeout=timeout_seconds
            )

            # 5. Use result directly (validation removed)
            validated_result = ads_result

            # 6. Store in vault
            await self._store_ads_result(validated_result)

            await self._publish_progress(100, "completed", "CI analysis complete")

            # 7. Return result
            return TaskResult(
                subtask_id=task.task_id,
                agent_id=self.agent_id,
                action=task.data.get("action", "create_campaign"),
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

    def _validate_ads_result(self, result: dict[str, Any]) -> dict[str, Any]:
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

    async def _store_ads_result(self, result: dict[str, Any]) -> None:
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

    async def _handle_ads_optimization(self, task: Task) -> TaskResult:
        """Handle market research task

        TODO: Implement market research logic
        For now, uses generic knowledge search
        """
        logger.info(f"Handling market research for task {task.task_id}")
        return await self._handle_generic_ads(task)

    async def _handle_performance_analysis(self, task: Task) -> TaskResult:
        """Handle trend analysis task

        TODO: Implement trend analysis logic
        For now, uses generic knowledge search
        """
        logger.info(f"Handling trend analysis for task {task.task_id}")
        return await self._handle_generic_ads(task)

    async def _handle_generic_ads(self, task: Task) -> TaskResult:
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
