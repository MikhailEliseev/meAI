"""Task execution events for Pre-Sale and Active Work phases.

This module defines all task execution events:
- TaskCreatedEvent (Pre-Sale & General) - P2 priority
- TaskAssignedEvent (Active Work) - P2 priority
- TaskStartedEvent - P2 priority
- TaskProgressEvent - P2 priority
- TaskCompletedEvent - P2 priority
- TaskFailedEvent - P1 priority (needs attention)
- TaskBlockedEvent - P2 priority

All events inherit from BaseEvent and use Pydantic v2 syntax.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent


class Deliverable(BaseModel):
    """Deliverable model for task completion.

    Represents a deliverable artifact from a completed task.
    Can be a file (file_path) or a URL (url).
    """

    type: str = Field(..., description="Deliverable type (report, data, dashboard, etc.)")
    title: str = Field(..., description="Deliverable title")
    description: str = Field(..., description="Deliverable description")
    file_path: str | None = Field(default=None, description="Path to deliverable file")
    url: str | None = Field(default=None, description="URL to deliverable resource")
    requires_approval: bool = Field(default=False, description="Whether deliverable requires approval")


# ============================================================================
# Pre-Sale & General Events
# ============================================================================


class TaskCreatedData(BaseModel):
    """Data for TaskCreatedEvent."""

    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister responsible for task")
    capability: str = Field(..., description="Capability to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    deadline: datetime | None = Field(default=None, description="Task deadline")
    dependencies: list[str] = Field(default_factory=list, description="Task dependencies (task IDs)")


class TaskCreatedEvent(BaseEvent):
    """Task created event (Pre-Sale & General).

    Emitted when a new task is created.
    Priority: P2 (normal)
    """

    type: Literal["task.created"] = "task.created"
    priority: int = Field(default=2, ge=0, le=3)
    data: TaskCreatedData


# ============================================================================
# Active Work (Sprint) Events
# ============================================================================


class TaskAssignedData(BaseModel):
    """Data for TaskAssignedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister assigned to task")
    capability: str = Field(..., description="Capability to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    deadline: datetime | None = Field(default=None, description="Task deadline")
    dependencies: list[str] = Field(default_factory=list, description="Task dependencies (task IDs)")


class TaskAssignedEvent(BaseEvent):
    """Task assigned event (Active Work).

    Emitted when a task is assigned to a magister in a sprint.
    Priority: P2 (normal)
    """

    type: Literal["task.assigned"] = "task.assigned"
    priority: int = Field(default=2, ge=0, le=3)
    data: TaskAssignedData


class TaskStartedData(BaseModel):
    """Data for TaskStartedEvent."""

    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister executing task")
    started_at: datetime = Field(..., description="Task start timestamp")


class TaskStartedEvent(BaseEvent):
    """Task started event.

    Emitted when a magister starts executing a task.
    Priority: P2 (normal)
    """

    type: Literal["task.started"] = "task.started"
    priority: int = Field(default=2, ge=0, le=3)
    data: TaskStartedData


class TaskProgressData(BaseModel):
    """Data for TaskProgressEvent."""

    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister executing task")
    progress_percent: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current step description")


class TaskProgressEvent(BaseEvent):
    """Task progress event.

    Emitted when a task makes progress.
    Priority: P2 (normal)
    """

    type: Literal["task.progress"] = "task.progress"
    priority: int = Field(default=2, ge=0, le=3)
    data: TaskProgressData


class TaskCompletedData(BaseModel):
    """Data for TaskCompletedEvent."""

    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister that completed task")
    completed_at: datetime = Field(..., description="Task completion timestamp")
    deliverables: list[Deliverable] = Field(default_factory=list, description="Task deliverables")
    summary: str = Field(..., description="Task completion summary")


class TaskCompletedEvent(BaseEvent):
    """Task completed event.

    Emitted when a task is successfully completed.
    Priority: P2 (normal)
    """

    type: Literal["task.completed"] = "task.completed"
    priority: int = Field(default=2, ge=0, le=3)
    data: TaskCompletedData


class TaskFailedData(BaseModel):
    """Data for TaskFailedEvent."""

    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister that failed task")
    failed_at: datetime = Field(..., description="Task failure timestamp")
    error_type: str = Field(..., description="Error type (from ErrorType enum)")
    error_message: str = Field(..., description="Error message")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    is_retryable: bool = Field(default=True, description="Whether task can be retried")


class TaskFailedEvent(BaseEvent):
    """Task failed event.

    Emitted when a task fails.
    Priority: P1 (high - needs attention)
    """

    type: Literal["task.failed"] = "task.failed"
    priority: int = Field(default=1, ge=0, le=3)
    data: TaskFailedData


class TaskBlockedData(BaseModel):
    """Data for TaskBlockedEvent."""

    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister with blocked task")
    blocked_at: datetime = Field(..., description="Task blocked timestamp")
    blocked_by: list[str] = Field(..., description="Blocking task IDs")
    reason: str = Field(..., description="Reason for blocking")


class TaskBlockedEvent(BaseEvent):
    """Task blocked event.

    Emitted when a task is blocked by dependencies.
    Priority: P2 (normal)
    """

    type: Literal["task.blocked"] = "task.blocked"
    priority: int = Field(default=2, ge=0, le=3)
    data: TaskBlockedData
