"""Ads Magister - Advertising specialist agent"""

from pathlib import Path

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import EventBus


class AdsMagister(BaseMagister):
    """Ads Magister - Advertising specialist

    Domain: Advertising (PPC, Display, Social Ads)

    Capabilities:
    - create_campaign: Ad campaign creation
    - optimize_budget: Budget optimization
    - analyze_performance: Campaign performance analysis
    - ab_test: A/B testing
    - target_audience: Audience targeting
    """

    def __init__(
        self,
        agent_id: str = "ads-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Ads Magister"""
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

    def get_capabilities(self) -> list[str]:
        """Get Ads Magister capabilities"""
        base_capabilities = super().get_capabilities()

        ads_capabilities = [
            "create_campaign",
            "optimize_budget",
            "analyze_performance",
            "ab_test",
            "target_audience",
        ]

        return base_capabilities + ads_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute Ads-specific task"""
        capability = task.metadata.get("capability")

        if capability == "create_campaign":
            return await self._handle_create_campaign(task)
        elif capability == "optimize_budget":
            return await self._handle_optimize_budget(task)
        elif capability == "analyze_performance":
            return await self._handle_analyze_performance(task)
        elif capability == "ab_test":
            return await self._handle_ab_test(task)
        elif capability == "target_audience":
            return await self._handle_target_audience(task)
        else:
            return await super().execute_task(task)

    async def _handle_create_campaign(self, task: Task) -> TaskResult:
        """Handle campaign creation task"""
        campaign_type = task.metadata.get("campaign_type", "search")
        budget = task.metadata.get("budget", 0)

        knowledge = await self.search_knowledge(
            query=f"{campaign_type} ad campaign creation",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "campaign_type": campaign_type,
                "budget": budget,
                "knowledge": knowledge,
            },
        )

    async def _handle_optimize_budget(self, task: Task) -> TaskResult:
        """Handle budget optimization task"""
        campaign_id = task.metadata.get("campaign_id", "")
        current_budget = task.metadata.get("current_budget", 0)

        knowledge = await self.search_knowledge(
            query="ad budget optimization strategies",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "campaign_id": campaign_id,
                "current_budget": current_budget,
                "knowledge": knowledge,
            },
        )

    async def _handle_analyze_performance(self, task: Task) -> TaskResult:
        """Handle performance analysis task"""
        campaign_ids = task.metadata.get("campaign_ids", [])

        knowledge = await self.search_knowledge(
            query="ad campaign performance metrics",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "campaigns_analyzed": len(campaign_ids),
                "knowledge": knowledge,
            },
        )

    async def _handle_ab_test(self, task: Task) -> TaskResult:
        """Handle A/B testing task"""
        variants = task.metadata.get("variants", [])

        knowledge = await self.search_knowledge(
            query="ad A/B testing best practices",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "variants_count": len(variants),
                "knowledge": knowledge,
            },
        )

    async def _handle_target_audience(self, task: Task) -> TaskResult:
        """Handle audience targeting task"""
        demographics = task.metadata.get("demographics", {})

        knowledge = await self.search_knowledge(
            query="audience targeting strategies",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "demographics": demographics,
                "knowledge": knowledge,
            },
        )
