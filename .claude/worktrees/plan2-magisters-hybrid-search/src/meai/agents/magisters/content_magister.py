# src/meai/agents/magisters/content_magister.py
"""Content Magister - Content creation specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class ContentMagister(BaseMagister):
    """Content Magister - specializes in content creation and editing"""

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
    ):
        """Initialize Content Magister

        Args:
            agent_id: Unique agent identifier
            database_url: Database URL
            vault_path: Path to Obsidian vault
            event_bus: Event bus for communication
            teacher: Teacher agent reference
        """
        super().__init__(
            agent_id=agent_id,
            database_url=database_url,
            vault_path=vault_path,
            event_bus=event_bus,
            teacher=teacher,
        )

    def get_domain(self) -> str:
        """Return content domain"""
        return "content"

    def get_capabilities(self) -> list[str]:
        """Return Content Magister capabilities"""
        return [
            "search",
            "store_knowledge",
            "generate_content",
            "edit_content",
            "plan_content",
        ]

    async def generate_content(
        self,
        topic: str,
        content_type: str,
        target_length: int = 500,
    ) -> dict[str, Any]:
        """
        Generate content for a topic.

        Args:
            topic: Content topic
            content_type: Type of content (article, social_post, etc.)
            target_length: Target length in words

        Returns:
            Generated content
        """
        # Search for content guidelines
        query = f"content generation {content_type} {topic}"
        results = await self.hybrid_search(query)

        # Generate content based on guidelines
        content = self._generate_from_guidelines(
            topic=topic,
            content_type=content_type,
            target_length=target_length,
            guidelines=results,
        )

        return {
            "status": "success",
            "topic": topic,
            "content_type": content_type,
            "content": content,
            "word_count": len(content.split()),
            "source": results.get("source", "unknown"),
        }

    async def edit_content(
        self,
        content: str,
        edit_instructions: str,
    ) -> dict[str, Any]:
        """
        Edit existing content.

        Args:
            content: Content to edit
            edit_instructions: Instructions for editing

        Returns:
            Edited content
        """
        # Simple editing: apply basic improvements
        edited = content.strip()

        changes = []

        # Fix double spaces
        if "  " in edited:
            edited = " ".join(edited.split())
            changes.append("Fixed spacing")

        # Ensure proper capitalization at start
        if edited and not edited[0].isupper():
            edited = edited[0].upper() + edited[1:]
            changes.append("Fixed capitalization")

        # Ensure ends with punctuation
        if edited and edited[-1] not in ".!?":
            edited += "."
            changes.append("Added punctuation")

        return {
            "status": "success",
            "original_length": len(content),
            "edited_length": len(edited),
            "edited_content": edited,
            "changes_made": changes,
        }

    async def plan_content(
        self,
        topic: str,
        timeframe: str,
        content_types: list[str],
    ) -> dict[str, Any]:
        """
        Plan content calendar.

        Args:
            topic: Content topic
            timeframe: Planning timeframe (weekly, monthly, etc.)
            content_types: Types of content to plan

        Returns:
            Content plan
        """
        # Search for planning best practices
        query = f"content planning {timeframe} {topic}"
        results = await self.hybrid_search(query)

        # Generate plan
        plan = self._generate_content_plan(
            topic=topic,
            timeframe=timeframe,
            content_types=content_types,
            best_practices=results,
        )

        return {
            "status": "success",
            "topic": topic,
            "timeframe": timeframe,
            "content_types": content_types,
            "plan": plan,
            "source": results.get("source", "unknown"),
        }

    def _generate_from_guidelines(
        self,
        topic: str,
        content_type: str,
        target_length: int,
        guidelines: dict[str, Any],
    ) -> str:
        """Generate content from guidelines"""
        # Simple generation: create placeholder content
        content = f"# {topic.title()}\n\n"
        content += f"This is a {content_type} about {topic}.\n\n"

        # Add content from guidelines if available
        for result in guidelines.get("results", [])[:2]:
            snippet = result.get("content", "")[:200]
            content += f"{snippet}\n\n"

        # Pad to target length
        words = content.split()
        while len(words) < target_length:
            words.append("content")

        return " ".join(words[:target_length])

    def _generate_content_plan(
        self,
        topic: str,
        timeframe: str,
        content_types: list[str],
        best_practices: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Generate content plan"""
        plan = []

        for i, content_type in enumerate(content_types, 1):
            plan.append({
                "week": str(i),
                "content_type": content_type,
                "topic": f"{topic} - Part {i}",
                "status": "planned",
            })

        return plan

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute Content-specific tasks.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        try:
            if task.action == "generate_content":
                # Parse: topic|content_type|target_length
                parts = task.description.split("|")
                topic = parts[0]
                content_type = parts[1] if len(parts) > 1 else "article"
                target_length = int(parts[2]) if len(parts) > 2 else 500

                result = await self.generate_content(topic, content_type, target_length)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "edit_content":
                # Parse: content|instructions
                parts = task.description.split("|", 1)
                content = parts[0]
                instructions = parts[1] if len(parts) > 1 else "improve"

                result = await self.edit_content(content, instructions)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "plan_content":
                # Parse: topic|timeframe|content_types_json
                parts = task.description.split("|")
                topic = parts[0]
                timeframe = parts[1] if len(parts) > 1 else "monthly"
                content_types = eval(parts[2]) if len(parts) > 2 else ["article"]

                result = await self.plan_content(topic, timeframe, content_types)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            else:
                # Delegate to base class
                return await super().execute_task(task)

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
            )
