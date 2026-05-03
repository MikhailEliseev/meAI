"""Base Magister class for coordinating Subagents

Magisters are the coordination layer between Operator and Subagents.
They receive tasks from Operator, delegate to Subagents, aggregate results,
and report back to Operator.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from meai.events.event_bus import EventBus, Message
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database


@dataclass
class SubagentTask:
    """Task for a Subagent"""

    task_id: str
    magister_id: str
    subagent_id: str
    action: str
    description: str
    priority: int
    created_at: datetime
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    status: str = "pending"  # pending, in_progress, completed, failed


@dataclass
class MagisterResult:
    """Aggregated result from Magister"""

    result_id: str
    operator_task_id: str
    magister_id: str
    summary: str
    subagent_results: list[dict[str, Any]]
    insights: list[str]
    issues: list[str]
    created_at: datetime


class BaseMagister(ABC):
    """Base class for all Magisters

    Responsibilities:
    - Subscribe to magister_task events from Operator
    - Receive tasks from Operator
    - Delegate to Subagents
    - Collect results from Subagents
    - Aggregate results
    - Report back to Operator
    """

    def __init__(
        self,
        magister_id: str,
        database_url: str,
        vault_path: str = "./obsidian",
    ):
        """Initialize Magister

        Args:
            magister_id: Unique Magister ID (e.g., "seo-magister-1")
            database_url: Database connection URL
            vault_path: Path to Obsidian vault root
        """
        self.magister_id = magister_id
        self.db = Database(database_url)
        self.vault = ObsidianVault(vault_path)
        self.event_bus = EventBus(database_url)

        # Active tasks tracking
        self.active_tasks: dict[str, SubagentTask] = {}

    async def initialize(self) -> None:
        """Initialize Magister components"""
        await self.db.connect()
        await self.vault.initialize()
        await self.event_bus.initialize()

        # Subscribe to magister_task events
        await self._subscribe_to_events()

    async def shutdown(self) -> None:
        """Shutdown Magister"""
        await self.event_bus.close()
        await self.db.disconnect()

    async def _subscribe_to_events(self) -> None:
        """Subscribe to magister_task events from Operator"""
        # Magisters use message polling pattern
        # They poll for messages with message_type="magister_task"
        pass

    async def poll_and_process_tasks(self) -> None:
        """Poll for tasks from Operator and process them

        This method should be called periodically to check for new tasks.
        """
        # Get pending messages for this Magister
        messages = await self.event_bus.get_messages(
            agent_id=self.magister_id,
            status="pending",
            limit=50,
        )

        for message in messages:
            if message.message_type == "magister_task":
                try:
                    await self._handle_magister_task(message)
                    await self.event_bus.mark_processed(message.message_id)
                except Exception as e:
                    await self.event_bus.mark_failed(
                        message.message_id,
                        str(e),
                    )

    async def _handle_magister_task(self, message: Message) -> None:
        """Handle magister_task from Operator

        Args:
            message: Message from Operator

        Steps:
        1. Extract task details
        2. Store subtask_id from Operator
        3. Identify required Subagents
        4. Delegate to Subagents
        5. Track task with operator_task_id and subtask_id
        """
        payload = message.payload

        # Store both operator_task_id and subtask_id for result tracking
        operator_task_id = payload.get("operator_task_id", payload["parent_task_id"])
        operator_subtask_id = payload["subtask_id"]  # This is what Operator expects back!

        # Identify required Subagents for this task
        subagents = await self.identify_subagents(payload["action"])

        # Delegate to each Subagent
        for subagent_id in subagents:
            subagent_task = SubagentTask(
                task_id=f"subtask-{uuid4().hex[:8]}",
                magister_id=self.magister_id,
                subagent_id=subagent_id,
                action=payload["action"],
                description=payload["description"],
                priority=message.priority,
                created_at=datetime.now(timezone.utc),
            )

            # Store both IDs in task for later
            subagent_task.result = {
                "operator_task_id": operator_task_id,
                "operator_subtask_id": operator_subtask_id,
            }

            await self.delegate_to_subagent(subagent_task)
            self.active_tasks[subagent_task.task_id] = subagent_task

    @abstractmethod
    async def identify_subagents(self, action: str) -> list[str]:
        """Identify which Subagents are needed for this action

        Args:
            action: Action to perform

        Returns:
            List of Subagent IDs
        """
        pass

    async def delegate_to_subagent(self, task: SubagentTask) -> None:
        """Delegate task to Subagent

        Args:
            task: Task for Subagent

        Steps:
        1. Create subagent_task message
        2. Publish to Event Bus
        3. Write to vault
        """
        # Create message for Subagent
        message = Message(
            from_agent=self.magister_id,
            to_agent=task.subagent_id,
            message_type="subagent_task",
            priority=task.priority,
            payload={
                "task_id": task.task_id,
                "action": task.action,
                "description": task.description,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Publish to Event Bus
        await self.event_bus.publish(message)

        # Write to vault
        await self._write_delegation_to_vault(task)

    async def poll_and_collect_results(self) -> None:
        """Poll for results from Subagents and process them

        This method should be called periodically to check for completed tasks.
        """
        # Get pending messages for this Magister
        messages = await self.event_bus.get_messages(
            agent_id=self.magister_id,
            status="pending",
            limit=50,
        )

        for message in messages:
            if message.message_type == "subagent_result":
                try:
                    await self._handle_subagent_result(message)
                    await self.event_bus.mark_processed(message.message_id)
                except Exception as e:
                    await self.event_bus.mark_failed(
                        message.message_id,
                        str(e),
                    )

    async def _handle_subagent_result(self, message: Message) -> None:
        """Handle result from Subagent

        Args:
            message: Message from Subagent

        Steps:
        1. Update task with result
        2. Check if all Subagents completed
        3. If yes, aggregate and report to Operator
        """
        payload = message.payload

        # Update task
        task_id = payload["task_id"]
        operator_task_id = None
        operator_subtask_id = None

        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]

            # Extract IDs before updating result
            if task.result:
                operator_task_id = task.result.get("operator_task_id")
                operator_subtask_id = task.result.get("operator_subtask_id")

            # Update with new result
            task.result = payload["result"]
            task.status = payload["status"]
            task.completed_at = datetime.now(timezone.utc)

            # Store IDs back for aggregation
            if operator_task_id:
                task.result["_operator_task_id"] = operator_task_id
            if operator_subtask_id:
                task.result["_operator_subtask_id"] = operator_subtask_id

        # Check if all tasks for this operator task are completed
        if operator_task_id and await self._all_subagents_completed(operator_task_id):
            await self._aggregate_and_report(operator_task_id, operator_subtask_id)

    async def _all_subagents_completed(self, operator_task_id: str) -> bool:
        """Check if all Subagents for an operator task are completed

        Args:
            operator_task_id: Operator task ID

        Returns:
            True if all completed
        """
        # Check only tasks related to this operator_task_id
        related_tasks = []
        for task in self.active_tasks.values():
            if task.result and task.result.get("_operator_task_id") == operator_task_id:
                related_tasks.append(task)

        if not related_tasks:
            return False

        # All related tasks must be completed
        for task in related_tasks:
            if task.status not in ["completed", "failed"]:
                return False

        return True

    async def _aggregate_and_report(self, operator_task_id: str, operator_subtask_id: str) -> None:
        """Aggregate Subagent results and report to Operator

        Args:
            operator_task_id: Operator task ID
            operator_subtask_id: Operator subtask ID (what Operator expects back)

        Steps:
        1. Collect all Subagent results
        2. Aggregate into summary
        3. Extract insights and issues
        4. Send to Operator with correct subtask_id
        """
        # Collect results
        subagent_results = []
        for task in self.active_tasks.values():
            if task.result:
                # Clean internal IDs from result
                result_copy = {k: v for k, v in task.result.items() if not k.startswith("_")}
                subagent_results.append({
                    "subagent_id": task.subagent_id,
                    "action": task.action,
                    "result": result_copy,
                })

        # Aggregate
        result = await self.aggregate_results(subagent_results)

        # Create MagisterResult
        magister_result = MagisterResult(
            result_id=f"result-{uuid4().hex[:8]}",
            operator_task_id=operator_task_id,
            magister_id=self.magister_id,
            summary=result["summary"],
            subagent_results=subagent_results,
            insights=result.get("insights", []),
            issues=result.get("issues", []),
            created_at=datetime.now(timezone.utc),
        )

        # Send to Operator with correct subtask_id
        await self._report_to_operator(magister_result, operator_subtask_id)

    @abstractmethod
    async def aggregate_results(
        self,
        subagent_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate Subagent results into summary

        Args:
            subagent_results: List of Subagent results

        Returns:
            Aggregated result with summary, insights, issues
        """
        pass

    async def _report_to_operator(self, result: MagisterResult, operator_subtask_id: str) -> None:
        """Report aggregated result to Operator

        Args:
            result: Aggregated result
            operator_subtask_id: Operator's subtask ID (what it expects back)

        Steps:
        1. Create magister_result message with correct subtask_id
        2. Publish to Event Bus
        3. Write to vault
        """
        # Create message for Operator
        message = Message(
            from_agent=self.magister_id,
            to_agent="operator",
            message_type="task_result",
            priority=0,  # High priority for results
            payload={
                "subtask_id": operator_subtask_id,  # Use Operator's subtask_id!
                "parent_task_id": result.operator_task_id,
                "status": "completed",
                "result": {
                    "summary": result.summary,
                    "insights": result.insights,
                    "issues": result.issues,
                    "subagent_results": result.subagent_results,
                },
                "completed_at": result.created_at.isoformat(),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Publish to Event Bus
        await self.event_bus.publish(message)

        # Write to vault
        await self._write_result_to_vault(result)

    async def _write_delegation_to_vault(self, task: SubagentTask) -> None:
        """Write delegation to vault

        Args:
            task: Subagent task
        """
        content = f"""---
task_id: {task.task_id}
magister_id: {task.magister_id}
subagent_id: {task.subagent_id}
action: {task.action}
status: {task.status}
created: {task.created_at.isoformat()}
---

# Delegation: {task.action}

## Subagent
{task.subagent_id}

## Action
{task.action}

## Description
{task.description}

## Priority
P{task.priority}

## Status
{task.status}
"""

        await self.vault.write_file(
            f"{self.magister_id}/delegations/{task.task_id}.md",
            content,
        )

    async def _write_result_to_vault(self, result: MagisterResult) -> None:
        """Write result to vault

        Args:
            result: Magister result
        """
        content = f"""---
result_id: {result.result_id}
operator_task_id: {result.operator_task_id}
magister_id: {result.magister_id}
created: {result.created_at.isoformat()}
---

# Result: {result.operator_task_id}

## Summary
{result.summary}

## Insights
{chr(10).join(f"- {insight}" for insight in result.insights) if result.insights else "None"}

## Issues
{chr(10).join(f"- {issue}" for issue in result.issues) if result.issues else "None"}

## Subagent Results
{chr(10).join(f"### {r['subagent_id']}{chr(10)}- **Action:** {r['action']}{chr(10)}- **Result:** {json.dumps(r['result'], indent=2)}{chr(10)}" for r in result.subagent_results)}
"""

        await self.vault.write_file(
            f"{self.magister_id}/results/{result.result_id}.md",
            content,
        )
