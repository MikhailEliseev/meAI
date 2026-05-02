"""Intelligence Magister - Market intelligence specialist agent"""

from pathlib import Path

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import EventBus


class IntelligenceMagister(BaseMagister):
    """Intelligence Magister - Market intelligence specialist

    Domain: Market Intelligence and Strategic Insights

    Capabilities:
    - research_market: Market research
    - analyze_trends: Trend analysis
    - monitor_competitors: Competitor monitoring
    - identify_opportunities: Opportunity identification
    - strategic_insights: Strategic recommendations
    """

    def __init__(
        self,
        agent_id: str = "intelligence-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Intelligence Magister"""
        if vault_path is None:
            vault_path = Path("./obsidian/intelligence-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="intelligence",
            domain="intelligence",
            event_bus=event_bus,
            vault_path=vault_path,
            database_url=database_url,
        )

    def get_capabilities(self) -> list[str]:
        """Get Intelligence Magister capabilities"""
        base_capabilities = super().get_capabilities()

        intelligence_capabilities = [
            "research_market",
            "analyze_trends",
            "monitor_competitors",
            "identify_opportunities",
            "strategic_insights",
        ]

        return base_capabilities + intelligence_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute Intelligence-specific task"""
        capability = task.metadata.get("capability")

        if capability == "research_market":
            return await self._handle_research_market(task)
        elif capability == "analyze_trends":
            return await self._handle_analyze_trends(task)
        elif capability == "monitor_competitors":
            return await self._handle_monitor_competitors(task)
        elif capability == "identify_opportunities":
            return await self._handle_identify_opportunities(task)
        elif capability == "strategic_insights":
            return await self._handle_strategic_insights(task)
        else:
            return await super().execute_task(task)

    async def _handle_research_market(self, task: Task) -> TaskResult:
        """Handle market research task"""
        market = task.metadata.get("market", "")
        industry = task.metadata.get("industry", "")

        knowledge = await self.search_knowledge(
            query=f"{market} {industry} market research",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "market": market,
                "industry": industry,
                "knowledge": knowledge,
            },
        )

    async def _handle_analyze_trends(self, task: Task) -> TaskResult:
        """Handle trend analysis task"""
        industry = task.metadata.get("industry", "")
        timeframe = task.metadata.get("timeframe", "year")

        knowledge = await self.search_knowledge(
            query=f"{industry} industry trends {timeframe}",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "industry": industry,
                "timeframe": timeframe,
                "knowledge": knowledge,
            },
        )

    async def _handle_monitor_competitors(self, task: Task) -> TaskResult:
        """Handle competitor monitoring task"""
        competitors = task.metadata.get("competitors", [])

        knowledge = await self.search_knowledge(
            query="competitive intelligence monitoring",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "competitors_count": len(competitors),
                "knowledge": knowledge,
            },
        )

    async def _handle_identify_opportunities(self, task: Task) -> TaskResult:
        """Handle opportunity identification task"""
        market = task.metadata.get("market", "")

        knowledge = await self.search_knowledge(
            query=f"{market} market opportunities",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "market": market,
                "knowledge": knowledge,
            },
        )

    async def _handle_strategic_insights(self, task: Task) -> TaskResult:
        """Handle strategic insights task"""
        context = task.metadata.get("context", "")

        knowledge = await self.search_knowledge(
            query=f"strategic insights {context}",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "context": context,
                "knowledge": knowledge,
            },
        )
