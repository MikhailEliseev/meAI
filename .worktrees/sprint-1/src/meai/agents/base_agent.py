"""Base Agent class for all autonomous agents

All agents (SEO, Content, Ads) inherit from this base class.
Provides common functionality for task execution, result reporting, and learning.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from meai.events.event_bus import EventBus, Message
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database


class TaskStatus(str, Enum):
    """Task execution status"""

    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task received from Operator"""

    task_id: str
    subtask_id: str
    parent_task_id: str
    action: str
    description: str
    priority: int
    status: TaskStatus
    created_at: datetime
    received_at: datetime
    data: dict[str, Any] = None  # Additional task data

    def __post_init__(self):
        """Initialize data dict if not provided"""
        if self.data is None:
            self.data = {}


@dataclass
class TaskResult:
    """Result of task execution"""

    subtask_id: str
    agent_id: str
    action: str
    status: str  # "success" or "failed"
    result: dict[str, Any]
    error: str | None
    duration_seconds: float
    completed_at: datetime


@dataclass
class Feedback:
    """Feedback from Operator or user"""

    feedback_id: str
    subtask_id: str
    rating: int  # 1-5
    comment: str
    created_at: datetime


class Agent(ABC):
    """Base class for all autonomous agents

    All agents must implement:
    - execute_task() — core task execution logic
    - get_capabilities() — list of actions this agent can perform

    Agents automatically:
    - Listen for tasks from Operator via Event Bus
    - Execute tasks autonomously
    - Report results back to Operator
    - Store everything in vault and database
    - Learn from feedback
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        database_url: str,
        vault_path: str = "./obsidian",
    ):
        """Initialize agent

        Args:
            agent_id: Unique agent identifier (e.g., "seo-agent")
            agent_type: Agent type (e.g., "seo", "content", "ads")
            database_url: Database connection URL
            vault_path: Path to Obsidian vault root
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.db = Database(database_url)
        self.vault = ObsidianVault(vault_path)
        self.event_bus = EventBus(database_url)

        # Active tasks tracking
        self.active_tasks: dict[str, Task] = {}

        # Performance metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_duration = 0.0

    async def initialize(self) -> None:
        """Initialize agent components"""
        await self.db.connect()
        await self.vault.initialize()
        await self.event_bus.initialize()

        # Create database tables
        await self._create_tables()

        # Start listening for tasks
        # In real implementation, would start background task listener

    async def shutdown(self) -> None:
        """Shutdown agent"""
        await self.event_bus.close()
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create agent database tables"""
        # Replace dashes with underscores for SQL table names
        table_prefix = self.agent_id.replace("-", "_")

        async with self.db.session() as session:
            await session.execute(
                text(f"""
                CREATE TABLE IF NOT EXISTS {table_prefix}_tasks (
                    task_id TEXT PRIMARY KEY,
                    subtask_id TEXT NOT NULL,
                    parent_task_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    received_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
                """)
            )

            await session.execute(
                text(f"""
                CREATE TABLE IF NOT EXISTS {table_prefix}_results (
                    result_id TEXT PRIMARY KEY,
                    subtask_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    duration_seconds REAL,
                    completed_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.execute(
                text(f"""
                CREATE TABLE IF NOT EXISTS {table_prefix}_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    subtask_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.commit()

    @abstractmethod
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute task (must be implemented by subclass)

        Args:
            task: Task to execute

        Returns:
            Task result with status and data

        Example:
            async def execute_task(self, task: Task) -> TaskResult:
                if task.action == "analyze_competitors":
                    result = await self._analyze_competitors(task)
                elif task.action == "keyword_research":
                    result = await self._keyword_research(task)
                else:
                    raise ValueError(f"Unknown action: {task.action}")

                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="success",
                    result=result,
                    error=None,
                    duration_seconds=10.5,
                    completed_at=datetime.now(timezone.utc)
                )
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get list of actions this agent can perform

        Returns:
            List of action names

        Example:
            def get_capabilities(self) -> list[str]:
                return [
                    "analyze_competitors",
                    "keyword_research",
                    "optimize_content",
                    "monitor_rankings"
                ]
        """
        pass

    async def receive_task(self, task: Task) -> None:
        """Receive task from Operator

        Args:
            task: Task to execute

        Steps:
        1. Validate task
        2. Store in database
        3. Write to vault
        4. Execute task
        5. Report result
        """
        # Update status
        task.status = TaskStatus.RECEIVED
        task.received_at = datetime.now(timezone.utc)

        # Store in database
        await self._store_task(task)

        # Write to vault
        await self._write_task_to_vault(task)

        # Track active task
        self.active_tasks[task.subtask_id] = task

        # Execute task
        await self._execute_and_report(task)

    async def _execute_and_report(self, task: Task) -> None:
        """Execute task and report result

        Args:
            task: Task to execute
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Update status to in_progress
            task.status = TaskStatus.IN_PROGRESS
            await self._update_task_status(task, start_time)

            # Execute task (implemented by subclass)
            result = await self.execute_task(task)

            # Update status to completed
            task.status = TaskStatus.COMPLETED
            await self._update_task_status(task, completed_at=result.completed_at)

            # Update metrics
            self.tasks_completed += 1
            self.total_duration += result.duration_seconds

            # Store result
            await self._store_result(result)

            # Write result to vault
            await self._write_result_to_vault(result)

            # Report to Operator
            await self.report_result(result)

        except Exception as e:
            # Task failed
            task.status = TaskStatus.FAILED
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            await self._update_task_status(task, completed_at=end_time)

            # Update metrics
            self.tasks_failed += 1

            # Create failure result
            result = TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={},
                error=str(e),
                duration_seconds=duration,
                completed_at=end_time,
            )

            # Store result
            await self._store_result(result)

            # Write result to vault
            await self._write_result_to_vault(result)

            # Report failure to Operator
            await self.report_result(result)

        finally:
            # Remove from active tasks
            self.active_tasks.pop(task.subtask_id, None)

    async def report_result(self, result: TaskResult) -> None:
        """Report result to Operator

        Args:
            result: Task result to report
        """
        # Create message
        message = Message(
            from_agent=self.agent_id,
            to_agent="operator",
            message_type="agent.result",
            priority=1,
            payload={
                "subtask_id": result.subtask_id,
                "agent_id": result.agent_id,
                "action": result.action,
                "status": result.status,
                "result": result.result,
                "error": result.error,
                "duration_seconds": result.duration_seconds,
                "completed_at": result.completed_at.isoformat(),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Publish to Event Bus
        await self.event_bus.publish(message)

    async def learn_from_feedback(self, feedback: Feedback) -> None:
        """Learn from feedback (can be overridden by subclass)

        Args:
            feedback: Feedback from Operator or user

        Default implementation just stores feedback.
        Subclasses can override to implement learning logic.
        """
        # Replace dashes with underscores for SQL table names
        table_prefix = self.agent_id.replace("-", "_")

        # Store feedback in database
        async with self.db.session() as session:
            await session.execute(
                text(f"""
                INSERT INTO {table_prefix}_feedback
                (feedback_id, subtask_id, rating, comment, created_at)
                VALUES (:feedback_id, :subtask_id, :rating, :comment, :created_at)
                """),
                {
                    "feedback_id": feedback.feedback_id,
                    "subtask_id": feedback.subtask_id,
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "created_at": feedback.created_at,
                },
            )
            await session.commit()

        # Write to vault
        await self._write_feedback_to_vault(feedback)

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get agent performance metrics

        Returns:
            Performance metrics
        """
        total_tasks = self.tasks_completed + self.tasks_failed
        success_rate = (
            self.tasks_completed / total_tasks if total_tasks > 0 else 0.0
        )
        avg_duration = (
            self.total_duration / self.tasks_completed
            if self.tasks_completed > 0
            else 0.0
        )

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_tasks": total_tasks,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
            "total_duration_seconds": self.total_duration,
        }

    async def _store_task(self, task: Task) -> None:
        """Store task in database"""
        table_prefix = self.agent_id.replace("-", "_")

        async with self.db.session() as session:
            await session.execute(
                text(f"""
                INSERT INTO {table_prefix}_tasks
                (task_id, subtask_id, parent_task_id, action, description,
                 priority, status, created_at, received_at)
                VALUES (:task_id, :subtask_id, :parent_task_id, :action, :description,
                        :priority, :status, :created_at, :received_at)
                """),
                {
                    "task_id": task.task_id,
                    "subtask_id": task.subtask_id,
                    "parent_task_id": task.parent_task_id,
                    "action": task.action,
                    "description": task.description,
                    "priority": task.priority,
                    "status": task.status.value,
                    "created_at": task.created_at,
                    "received_at": task.received_at,
                },
            )
            await session.commit()

    async def _update_task_status(
        self,
        task: Task,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Update task status in database"""
        table_prefix = self.agent_id.replace("-", "_")

        async with self.db.session() as session:
            if started_at:
                await session.execute(
                    text(f"""
                    UPDATE {table_prefix}_tasks
                    SET status = :status, started_at = :started_at
                    WHERE subtask_id = :subtask_id
                    """),
                    {
                        "status": task.status.value,
                        "started_at": started_at,
                        "subtask_id": task.subtask_id,
                    },
                )
            elif completed_at:
                await session.execute(
                    text(f"""
                    UPDATE {table_prefix}_tasks
                    SET status = :status, completed_at = :completed_at
                    WHERE subtask_id = :subtask_id
                    """),
                    {
                        "status": task.status.value,
                        "completed_at": completed_at,
                        "subtask_id": task.subtask_id,
                    },
                )
            else:
                await session.execute(
                    text(f"""
                    UPDATE {table_prefix}_tasks
                    SET status = :status
                    WHERE subtask_id = :subtask_id
                    """),
                    {"status": task.status.value, "subtask_id": task.subtask_id},
                )

            await session.commit()

    async def _store_result(self, result: TaskResult) -> None:
        """Store result in database"""
        table_prefix = self.agent_id.replace("-", "_")

        async with self.db.session() as session:
            await session.execute(
                text(f"""
                INSERT INTO {table_prefix}_results
                (result_id, subtask_id, action, status, result, error,
                 duration_seconds, completed_at)
                VALUES (:result_id, :subtask_id, :action, :status, :result, :error,
                        :duration_seconds, :completed_at)
                """),
                {
                    "result_id": f"result-{uuid4().hex[:8]}",
                    "subtask_id": result.subtask_id,
                    "action": result.action,
                    "status": result.status,
                    "result": json.dumps(result.result),
                    "error": result.error,
                    "duration_seconds": result.duration_seconds,
                    "completed_at": result.completed_at,
                },
            )
            await session.commit()

    async def _write_task_to_vault(self, task: Task) -> None:
        """Write task to vault"""
        content = f"""---
subtask_id: {task.subtask_id}
parent_task_id: {task.parent_task_id}
action: {task.action}
priority: P{task.priority}
status: {task.status.value}
created: {task.created_at.isoformat()}
received: {task.received_at.isoformat()}
---

# Task: {task.action}

## Description
{task.description}

## Priority
P{task.priority}

## Status
{task.status.value}
"""

        await self.vault.write_file(
            f"{self.agent_id}/tasks/{task.subtask_id}.md", content
        )

    async def _write_result_to_vault(self, result: TaskResult) -> None:
        """Write result to vault"""
        content = f"""---
subtask_id: {result.subtask_id}
action: {result.action}
status: {result.status}
duration: {result.duration_seconds}s
completed: {result.completed_at.isoformat()}
---

# Result: {result.action}

## Status
{result.status.upper()}

## Duration
{result.duration_seconds:.2f} seconds

## Result
```json
{json.dumps(result.result, indent=2)}
```

## Error
{result.error if result.error else "None"}
"""

        await self.vault.write_file(
            f"{self.agent_id}/results/{result.subtask_id}.md", content
        )

    async def _write_feedback_to_vault(self, feedback: Feedback) -> None:
        """Write feedback to vault"""
        content = f"""---
feedback_id: {feedback.feedback_id}
subtask_id: {feedback.subtask_id}
rating: {feedback.rating}/5
created: {feedback.created_at.isoformat()}
---

# Feedback

## Rating
{"⭐" * feedback.rating} ({feedback.rating}/5)

## Comment
{feedback.comment}
"""

        await self.vault.write_file(
            f"{self.agent_id}/feedback/{feedback.feedback_id}.md", content
        )
