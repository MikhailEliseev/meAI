# src/meai/agents/magisters/base_magister.py
"""Base Magister class with hybrid search capabilities"""

from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime, timezone

from meai.agents.base_agent import Agent, Task, TaskResult, TaskStatus
from meai.events.event_bus import EventBus
from meai.agents.teacher import TeacherAgent
from meai.memory.obsidian import ObsidianVault


class BaseMagister(Agent, ABC):
    """
    Base class for all Magister agents.

    Magisters are domain specialists with:
    - Local memory (Obsidian vault)
    - Hybrid search: local → Teacher → Researcher
    - Domain-specific capabilities
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="magister",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.event_bus = event_bus
        self.teacher = teacher

    @abstractmethod
    def get_domain(self) -> str:
        """Return the domain this Magister specializes in"""
        pass

    async def search_local(self, query: str) -> list[dict[str, Any]]:
        """
        Search local Obsidian vault.

        Args:
            query: Search query

        Returns:
            List of matching notes with content and metadata
        """
        return await self.vault.search(query)

    async def hybrid_search(self, query: str) -> dict[str, Any]:
        """
        Hybrid search: local → Teacher → Researcher.

        1. Search local vault first
        2. If not found, query Teacher's Qdrant
        3. If still not found, request Researcher to find new knowledge

        Args:
            query: Search query

        Returns:
            Dict with source and results
        """
        # Step 1: Search local vault
        local_results = await self.search_local(query)
        if local_results:
            return {
                "source": "local",
                "results": local_results,
            }

        # Step 2: Query Teacher
        teacher_task = Task(
            task_id=f"magister-query-{datetime.now(timezone.utc).timestamp()}",
            subtask_id=f"magister-query-{datetime.now(timezone.utc).timestamp()}",
            parent_task_id=f"magister-query-{datetime.now(timezone.utc).timestamp()}",
            action="handle_magister_query",
            description=f"{query}|{self.get_domain()}|{self.agent_id}",
            priority=2,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
        )

        teacher_result = await self.teacher.execute_task(teacher_task)

        if teacher_result.status == "success" and teacher_result.result.get("results"):
            return {
                "source": "teacher",
                "results": teacher_result.result["results"],
            }

        # Step 3: Request Researcher (async, don't wait)
        await self.request_research(query)

        return {
            "source": "researcher_requested",
            "results": [],
            "message": "Research requested, check back later",
        }

    async def request_research(self, topic: str) -> None:
        """
        Request Researcher to find new knowledge.

        Args:
            topic: Research topic
        """
        from meai.events.event_bus import Event

        event = Event(
            event_type="research_request",
            payload={
                "topic": topic,
                "domain": self.get_domain(),
                "magister_id": self.agent_id,
                "requested_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        await self.event_bus.publish(event)

    async def store_knowledge(
        self,
        content: str,
        topic: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Store knowledge in local vault.

        Args:
            content: Knowledge content
            topic: Topic/title
            metadata: Optional metadata

        Returns:
            Path to created note
        """
        note_metadata = {
            "topic": topic,
            "domain": self.get_domain(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }

        return await self.vault.write_note(
            content=content,
            folder="knowledge",
            metadata=note_metadata,
        )

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute a task. Subclasses should override to add domain-specific actions.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        try:
            if task.action == "search":
                results = await self.hybrid_search(task.description)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=results,
                )

            elif task.action == "store_knowledge":
                # Parse: content|topic|metadata_json
                parts = task.description.split("|", 2)
                content = parts[0]
                topic = parts[1] if len(parts) > 1 else "unknown"
                metadata = eval(parts[2]) if len(parts) > 2 else {}

                path = await self.store_knowledge(content, topic, metadata)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result={"path": path},
                )

            else:
                return TaskResult(
                    task_id=task.task_id,
                    status="failed",
                    error=f"Unknown action: {task.action}",
                )

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
            )
