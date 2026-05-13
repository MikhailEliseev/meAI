"""
Ads Orchestrator - Coordinates Campaign creation tasks

Real implementation with Google Ads API integration via Services Layer.
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
import asyncio
import logging
from pathlib import Path

from meai.agents.base_agent import Agent, Task, TaskResult, TaskStatus
from meai.events.event_bus import EventBus

# Import real services
import sys
aim_path = Path(__file__).parent.parent.parent.parent
if str(aim_path) not in sys.path:
    sys.path.insert(0, str(aim_path))

from AIM.src.aim.subagents.ads.services.campaign_service import CampaignService
from AIM.src.aim.subagents.ads.services.content_optimizer import ContentOptimizer
from AIM.src.aim.subagents.ads.services.analytics_service import AnalyticsService
from AIM.src.aim.subagents.ads.config.settings import AdsSettings

logger = logging.getLogger(__name__)


class AdsOrchestrator(Agent):
    """Ads Orchestrator - Coordinates Campaign management tasks

    Responsibilities:
    - Execute Campaign creation via CampaignService
    - Optimize ad content via ContentOptimizer
    - Track performance via AnalyticsService
    - Provide progress callbacks
    - Aggregate results

    Uses real Google Ads API integration (no mock data).
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "AIM/obsidian/ads-orchestrator"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ads_orchestrator",
            database_url=database_url,
            vault_path=vault_path
        )
        self.event_bus = event_bus

        # Initialize real services
        self.settings = AdsSettings()
        self.campaign_service = CampaignService(settings=self.settings)
        self.content_optimizer = ContentOptimizer(settings=self.settings)
        self.analytics_service = AnalyticsService(settings=self.settings)

    def get_capabilities(self) -> list[str]:
        """Get Ads Orchestrator capabilities"""
        return [
            "campaign_creation",
            "content_optimization",
            "performance_analytics"
        ]

    async def execute_campaign_creation(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute Campaign creation

        Args:
            task_data: Task data dict with:
                - task_id: Task identifier
                - campaign_type: "campaign" | "optimization" | "analytics"
                - target: Campaign name or campaign ID
                - niche: Business niche
                - geo: Geographic location
                - budget: Campaign budget (for creation)
            progress_callback: Async callback for progress updates
                               Called with (step: int, status: str, message: str)

        Returns:
            Dict with Campaign creation results:
                - task_id: Task identifier
                - campaign_type: Analysis type used
                - results: Analysis results dict
                - execution_time_seconds: Total execution time
                - errors: List of error messages
        """
        start_time = datetime.now()
        campaign_type = task_data.get("campaign_type", "campaign")
        task_id = task_data.get("task_id", "unknown")

        try:
            # Progress update: starting
            if progress_callback:
                await progress_callback(1, "in_progress", f"Starting {campaign_type} operation")

            # Execute operation based on type
            if campaign_type == "campaign":
                results = await self._execute_campaign_creation(task_data, progress_callback)
            elif campaign_type == "optimization":
                results = await self._execute_content_optimization(task_data, progress_callback)
            elif campaign_type == "analytics":
                results = await self._execute_performance_analytics(task_data, progress_callback)
            else:
                results = {"error": f"Unknown operation type: {campaign_type}"}

            # Progress update: completed
            if progress_callback:
                await progress_callback(2, "completed", "Operation complete")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Return structured result
            return {
                "task_id": task_id,
                "campaign_type": campaign_type,
                "results": results,
                "status": results.get("status", "completed"),
                "execution_time_seconds": int(execution_time),
                "errors": []
            }

        except Exception as e:
            logger.error(f"Campaign operation failed: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "campaign_type": campaign_type,
                "results": {},
                "execution_time_seconds": 0,
                "errors": [f"Campaign operation failed: {str(e)}"]
            }

    async def _execute_campaign_creation(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute campaign creation using CampaignService (REAL API)"""

        campaign_name = task_data.get("target", "") or task_data.get("campaign_name", "")
        budget_usd = task_data.get("budget", 50.0)
        channel_type = task_data.get("channel_type", "SEARCH")
        status = task_data.get("status", "PAUSED")

        if not campaign_name:
            return {
                "status": "error",
                "error": "'campaign_name' or 'target' is required"
            }

        # Progress update
        if progress_callback:
            await progress_callback(1, "in_progress", "Creating campaign via Google Ads API")

        try:
            # Create campaign via REAL API
            campaign = await self.campaign_service.create_campaign_with_validation(
                name=campaign_name,
                budget_usd=budget_usd,
                channel_type=channel_type,
                status=status,
                validate_budget=True,
            )

            # Progress update
            if progress_callback:
                await progress_callback(2, "completed", "Campaign created successfully")

            # Return REAL results from API
            return {
                "campaign_name": campaign["name"],
                "campaign_id": campaign["resource_name"].split("/")[-1],
                "resource_name": campaign["resource_name"],
                "budget_usd": budget_usd,
                "budget_micros": campaign["budget_amount_micros"],
                "channel_type": channel_type,
                "status": campaign["status"],
                "validation": campaign["validation"],
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Campaign creation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": f"Campaign creation failed: {str(e)}"
            }

    async def _execute_content_optimization(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute content optimization using ContentOptimizer (REAL API)"""

        campaign_id = task_data.get("target", "") or task_data.get("campaign_id", "")

        if not campaign_id:
            return {
                "status": "error",
                "error": "'campaign_id' is required for optimization"
            }

        if progress_callback:
            await progress_callback(1, "in_progress", "Analyzing campaign performance")

        try:
            # Get REAL performance analysis from API
            analysis = await self.content_optimizer.analyze_campaign_performance(
                campaign_id=campaign_id,
                date_range="LAST_30_DAYS",
            )

            if progress_callback:
                await progress_callback(2, "in_progress", "Generating optimization suggestions")

            # Get REAL optimization suggestions
            suggestions = await self.content_optimizer.suggest_optimizations(
                campaign_id=campaign_id,
            )

            if progress_callback:
                await progress_callback(3, "completed", "Optimization analysis complete")

            # Return REAL results from API
            return {
                "campaign_id": campaign_id,
                "campaign_name": analysis["campaign_name"],
                "current_metrics": analysis["metrics"],
                "health_score": analysis["overall_health"],
                "recommendations": analysis["recommendations"],
                "quick_wins": suggestions["quick_wins"],
                "long_term": suggestions["long_term"],
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Content optimization failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": f"Content optimization failed: {str(e)}"
            }

    async def _execute_performance_analytics(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute performance analytics using AnalyticsService (REAL API)"""

        campaign_id = task_data.get("target", "") or task_data.get("campaign_id", "")

        if not campaign_id:
            return {
                "status": "error",
                "error": "'campaign_id' is required for analytics"
            }

        if progress_callback:
            await progress_callback(1, "in_progress", "Fetching performance metrics")

        try:
            # Get REAL performance metrics from API
            performance = await self.analytics_service.get_campaign_performance(
                campaign_id=campaign_id,
                date_range="LAST_30_DAYS",
            )

            if progress_callback:
                await progress_callback(2, "in_progress", "Calculating ROI")

            # Calculate REAL ROI from API data
            roi_analysis = await self.analytics_service.calculate_roi(
                campaign_id=campaign_id,
                date_range="LAST_30_DAYS",
            )

            if progress_callback:
                await progress_callback(3, "completed", "Analytics complete")

            # Return REAL results from API
            return {
                "campaign_id": campaign_id,
                "campaign_name": performance["campaign_name"],
                "raw_metrics": performance["raw_metrics"],
                "calculated_metrics": performance["calculated_metrics"],
                "business_metrics": performance["business_metrics"],
                "roi_analysis": roi_analysis,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Performance analytics failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": f"Performance analytics failed: {str(e)}"
            }

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute task (required by Agent base class)"""

        # Convert Task to task_data dict
        task_data = {
            "task_id": task.task_id,
            "campaign_type": task.data.get("campaign_type", "campaign"),
            "target": task.data.get("target", ""),
            "campaign_id": task.data.get("campaign_id", ""),
            "campaign_name": task.data.get("campaign_name", ""),
            "budget": task.data.get("budget", 50.0),
            "channel_type": task.data.get("channel_type", "SEARCH"),
            "status": task.data.get("status", "PAUSED"),
            "niche": task.data.get("niche", ""),
            "geo": task.data.get("geo", "")
        }

        # Execute operation
        result = await self.execute_campaign_creation(task_data)

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

    async def close(self) -> None:
        """Close orchestrator and cleanup services"""
        self.campaign_service.close()
        self.content_optimizer.close()
        self.analytics_service.close()
        logger.info("ads_orchestrator_closed")
