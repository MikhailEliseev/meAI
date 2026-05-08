"""Sprint execution events for Active Work phase.

This module defines all sprint execution events across 4 sub-phases:

Phase 2.1 (Sprint Planning):
- SprintPlanningStartedEvent - P1 priority
- SprintPlanCreatedEvent - P1 priority
- SprintApprovedEvent - P1 priority

Phase 2.3 (Sprint Review):
- SprintReviewStartedEvent - P1 priority
- SprintReportGeneratedEvent - P1 priority

Phase 2.4 (Sprint Retrospective):
- SprintRetrospectiveStartedEvent - P2 priority
- SprintLessonsLearnedEvent - P2 priority
- SprintCompletedEvent - P2 priority

All events inherit from BaseEvent and use Pydantic v2 syntax.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent
from meai.events.task_events import Deliverable


# ============================================================================
# Models
# ============================================================================


class SprintTask(BaseModel):
    """Sprint task model.

    Represents a task within a sprint with estimation and dependencies.
    """

    task_id: str = Field(..., description="Task identifier")
    magister: str = Field(..., description="Magister assigned to task")
    capability: str = Field(..., description="Capability to execute")
    description: str = Field(..., description="Task description")
    estimated_hours: int = Field(..., ge=0, description="Estimated hours")
    priority: str = Field(..., description="Task priority (high, medium, low)")
    dependencies: list[str] = Field(default_factory=list, description="Task dependencies (task IDs)")


class TaskDependency(BaseModel):
    """Task dependency model.

    Represents dependencies between tasks with type classification.
    """

    task_id: str = Field(..., description="Task identifier")
    depends_on: list[str] = Field(..., description="List of task IDs this task depends on")
    dependency_type: Literal["blocking", "soft"] = Field(
        ..., description="Dependency type: blocking (must complete) or soft (preferred)"
    )


class SprintSummary(BaseModel):
    """Sprint summary model.

    Aggregated sprint results and statistics.
    """

    completed_tasks: int = Field(..., ge=0, description="Number of completed tasks")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks")
    completion_rate: float = Field(..., ge=0.0, le=1.0, description="Completion rate (0.0-1.0)")
    hours_planned: int = Field(..., ge=0, description="Planned hours")
    hours_actual: int = Field(..., ge=0, description="Actual hours spent")
    achievements: list[str] = Field(default_factory=list, description="Sprint achievements")
    challenges: list[str] = Field(default_factory=list, description="Sprint challenges")


class SprintMetrics(BaseModel):
    """Sprint metrics model.

    Performance metrics for sprint evaluation.
    """

    velocity: int = Field(..., ge=0, description="Sprint velocity (tasks completed)")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0.0-1.0)")
    client_satisfaction: float = Field(..., ge=0.0, le=5.0, description="Client satisfaction (0.0-5.0)")
    magister_performance: dict[str, float] = Field(
        default_factory=dict, description="Magister performance scores (magister -> score)"
    )


class ActionItem(BaseModel):
    """Action item model.

    Represents an action item from retrospective.
    """

    description: str = Field(..., description="Action item description")
    assignee: str = Field(..., description="Assignee (magister or operator)")
    deadline: datetime | None = Field(default=None, description="Action item deadline")
    priority: str = Field(..., description="Priority (high, medium, low)")


# ============================================================================
# Phase 2.1: Sprint Planning Events
# ============================================================================


class SprintPlanningStartedData(BaseModel):
    """Data for SprintPlanningStartedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    sprint_number: int = Field(..., ge=1, description="Sprint number")
    start_date: datetime = Field(..., description="Sprint start date")
    end_date: datetime = Field(..., description="Sprint end date")
    available_hours: int = Field(..., ge=0, description="Available hours for sprint")


class SprintPlanningStartedEvent(BaseEvent):
    """Sprint planning started event.

    Emitted when sprint planning phase begins.
    Priority: P1 (high)
    """

    type: Literal["sprint.planning.started"] = "sprint.planning.started"
    priority: int = Field(default=1, ge=0, le=3)
    data: SprintPlanningStartedData


class SprintPlanCreatedData(BaseModel):
    """Data for SprintPlanCreatedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    tasks: list[SprintTask] = Field(..., description="Sprint tasks")
    dependencies: list[TaskDependency] = Field(default_factory=list, description="Task dependencies")
    total_estimated_hours: int = Field(..., ge=0, description="Total estimated hours")
    requires_approval: bool = Field(default=True, description="Whether plan requires approval")


class SprintPlanCreatedEvent(BaseEvent):
    """Sprint plan created event.

    Emitted when sprint plan is created with tasks and dependencies.
    Priority: P1 (high)
    """

    type: Literal["sprint.plan.created"] = "sprint.plan.created"
    priority: int = Field(default=1, ge=0, le=3)
    data: SprintPlanCreatedData


class SprintApprovedData(BaseModel):
    """Data for SprintApprovedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    approved_by: str = Field(..., description="Approver (user or operator)")
    approved_at: datetime = Field(..., description="Approval timestamp")
    comments: str | None = Field(default=None, description="Approval comments")


class SprintApprovedEvent(BaseEvent):
    """Sprint approved event.

    Emitted when sprint plan is approved.
    Priority: P1 (high)
    """

    type: Literal["sprint.approved"] = "sprint.approved"
    priority: int = Field(default=1, ge=0, le=3)
    data: SprintApprovedData


# ============================================================================
# Phase 2.3: Sprint Review Events
# ============================================================================


class SprintReviewStartedData(BaseModel):
    """Data for SprintReviewStartedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    review_date: datetime = Field(..., description="Review date")


class SprintReviewStartedEvent(BaseEvent):
    """Sprint review started event.

    Emitted when sprint review phase begins.
    Priority: P1 (high)
    """

    type: Literal["sprint.review.started"] = "sprint.review.started"
    priority: int = Field(default=1, ge=0, le=3)
    data: SprintReviewStartedData


class SprintReportGeneratedData(BaseModel):
    """Data for SprintReportGeneratedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    summary: SprintSummary = Field(..., description="Sprint summary")
    metrics: SprintMetrics = Field(..., description="Sprint metrics")
    deliverables: list[Deliverable] = Field(default_factory=list, description="Sprint deliverables")
    generated_at: datetime = Field(..., description="Report generation timestamp")


class SprintReportGeneratedEvent(BaseEvent):
    """Sprint report generated event.

    Emitted when sprint report is generated with summary and metrics.
    Priority: P1 (high)
    """

    type: Literal["sprint.report.generated"] = "sprint.report.generated"
    priority: int = Field(default=1, ge=0, le=3)
    data: SprintReportGeneratedData


# ============================================================================
# Phase 2.4: Sprint Retrospective Events
# ============================================================================


class SprintRetrospectiveStartedData(BaseModel):
    """Data for SprintRetrospectiveStartedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    retrospective_date: datetime = Field(..., description="Retrospective date")


class SprintRetrospectiveStartedEvent(BaseEvent):
    """Sprint retrospective started event.

    Emitted when sprint retrospective phase begins.
    Priority: P2 (normal)
    """

    type: Literal["sprint.retrospective.started"] = "sprint.retrospective.started"
    priority: int = Field(default=2, ge=0, le=3)
    data: SprintRetrospectiveStartedData


class SprintLessonsLearnedData(BaseModel):
    """Data for SprintLessonsLearnedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    what_went_well: list[str] = Field(default_factory=list, description="What went well")
    what_needs_improvement: list[str] = Field(
        default_factory=list, description="What needs improvement"
    )
    action_items: list[ActionItem] = Field(default_factory=list, description="Action items")


class SprintLessonsLearnedEvent(BaseEvent):
    """Sprint lessons learned event.

    Emitted when sprint retrospective lessons are documented.
    Priority: P2 (normal)
    """

    type: Literal["sprint.lessons.learned"] = "sprint.lessons.learned"
    priority: int = Field(default=2, ge=0, le=3)
    data: SprintLessonsLearnedData


class SprintCompletedData(BaseModel):
    """Data for SprintCompletedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    completed_at: datetime = Field(..., description="Sprint completion timestamp")
    final_status: str = Field(..., description="Final sprint status")
    next_sprint_id: str | None = Field(default=None, description="Next sprint identifier")


class SprintCompletedEvent(BaseEvent):
    """Sprint completed event.

    Emitted when sprint is fully completed (after retrospective).
    Priority: P2 (normal)
    """

    type: Literal["sprint.completed"] = "sprint.completed"
    priority: int = Field(default=2, ge=0, le=3)
    data: SprintCompletedData
