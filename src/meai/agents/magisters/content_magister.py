"""Content Magister - Content marketing specialist agent"""

from pathlib import Path
from typing import Any

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import EventBus


class ContentMagister(BaseMagister):
    """Content Magister - Content marketing specialist

    Domain: Content Marketing

    Capabilities:
    - generate_content: Content creation
    - edit_content: Content editing and improvement
    - plan_content: Content calendar planning
    - analyze_performance: Content performance analysis
    - optimize_for_seo: SEO content optimization
    """

    def __init__(
        self,
        agent_id: str = "content-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Content Magister"""
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

    def get_capabilities(self) -> list[str]:
        """Get Content Magister capabilities"""
        base_capabilities = super().get_capabilities()

        content_capabilities = [
            "generate_content",
            "edit_content",
            "plan_content",
            "analyze_performance",
            "optimize_for_seo",
        ]

        return base_capabilities + content_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute Content-specific task"""
        capability = task.metadata.get("capability")

        if capability == "generate_content":
            return await self._handle_generate_content(task)
        elif capability == "edit_content":
            return await self._handle_edit_content(task)
        elif capability == "plan_content":
            return await self._handle_plan_content(task)
        elif capability == "analyze_performance":
            return await self._handle_analyze_performance(task)
        elif capability == "optimize_for_seo":
            return await self._handle_optimize_for_seo(task)
        else:
            return await super().execute_task(task)

    async def _handle_generate_content(self, task: Task) -> TaskResult:
        """Handle content generation task"""
        topic = task.metadata.get("topic", "")
        content_type = task.metadata.get("content_type", "article")

        knowledge = await self.search_knowledge(
            query=f"content writing {content_type} {topic}",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "topic": topic,
                "content_type": content_type,
                "knowledge": knowledge,
            },
        )

    async def _handle_edit_content(self, task: Task) -> TaskResult:
        """Handle content editing task"""
        content = task.metadata.get("content", "")

        knowledge = await self.search_knowledge(
            query="content editing best practices",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "content_length": len(content),
                "knowledge": knowledge,
            },
        )

    async def _handle_plan_content(self, task: Task) -> TaskResult:
        """Handle content planning task"""
        timeframe = task.metadata.get("timeframe", "month")

        knowledge = await self.search_knowledge(
            query=f"content calendar planning {timeframe}",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "timeframe": timeframe,
                "knowledge": knowledge,
            },
        )

    async def _handle_analyze_performance(self, task: Task) -> TaskResult:
        """Handle content performance analysis task"""
        content_ids = task.metadata.get("content_ids", [])

        knowledge = await self.search_knowledge(
            query="content performance metrics analysis",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "content_analyzed": len(content_ids),
                "knowledge": knowledge,
            },
        )

    async def _handle_optimize_for_seo(self, task: Task) -> TaskResult:
        """Handle SEO optimization task"""
        content = task.metadata.get("content", "")
        keywords = task.metadata.get("keywords", [])

        knowledge = await self.search_knowledge(
            query="SEO content optimization techniques",
            search_local=True,
            search_teacher=True,
        )

        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={
                "content_length": len(content),
                "keywords": keywords,
                "knowledge": knowledge,
            },
        )
