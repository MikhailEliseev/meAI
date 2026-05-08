"""Project lifecycle events for Event Bus architecture.

This module provides events for all project lifecycle phases:
- Phase -1 (Pre-Sale): Project creation and initial setup
- Phase 0 (Setup): Infrastructure setup
- Phase 1 (Baseline): Baseline data collection
- Phase 1.5 (Strategy Planning): Strategy planning and approval
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent, ProjectStatus


# ============================================================================
# Phase -1 (Pre-Sale) - Project Creation
# ============================================================================


class ProjectCreatedData(BaseModel):
    """Data model for project creation."""

    project_id: str = Field(..., description="Unique project identifier")
    client_name: str = Field(..., description="Client company name")
    client_domain: str = Field(..., description="Client website domain")
    client_contact: str = Field(..., description="Client contact email")
    industry: str = Field(..., description="Client industry")
    initial_status: ProjectStatus = Field(..., description="Initial project status")
    source: str = Field(..., description="Lead source (e.g., 'Website Form', 'Referral')")
    created_at: datetime = Field(..., description="Project creation timestamp")
    notes: str | None = Field(default=None, description="Additional notes")


class ProjectCreatedEvent(BaseEvent):
    """Event emitted when a new project is created.

    Phase: -1 (Pre-Sale)
    Priority: P1 (High)
    """

    type: Literal["project.created"] = "project.created"
    priority: int = Field(default=1, ge=0, le=3)
    data: ProjectCreatedData = Field(..., description="Project creation data")


# ============================================================================
# Phase 0 (Setup) - Infrastructure Setup
# ============================================================================


class SetupTask(BaseModel):
    """Model for infrastructure setup task."""

    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of setup task (e.g., 'obsidian_vault', 'database')")
    description: str = Field(..., description="Task description")
    assigned_to: str = Field(..., description="Agent assigned to this task")


class InfrastructureSetupStartedEvent(BaseEvent):
    """Event emitted when infrastructure setup begins.

    Phase: 0 (Setup)
    Priority: P1 (High)
    """

    type: Literal["infrastructure.setup.started"] = "infrastructure.setup.started"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    tasks: list[SetupTask] = Field(..., description="List of setup tasks to execute")


class InfrastructureSetupCompletedEvent(BaseEvent):
    """Event emitted when infrastructure setup is completed.

    Phase: 0 (Setup)
    Priority: P1 (High)
    """

    type: Literal["infrastructure.setup.completed"] = "infrastructure.setup.completed"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    completed_tasks: list[str] = Field(..., description="List of completed task IDs")
    setup_summary: str = Field(..., description="Summary of setup completion")


# ============================================================================
# Phase 1 (Baseline) - Baseline Data Collection
# ============================================================================


class BaselineTask(BaseModel):
    """Model for baseline collection task."""

    task_id: str = Field(..., description="Unique task identifier")
    domain: str = Field(..., description="Domain (e.g., 'SEO', 'Content', 'Ads')")
    metric_type: str = Field(..., description="Type of metrics to collect")
    description: str = Field(..., description="Task description")
    assigned_to: str = Field(..., description="Magister assigned to this task")


class BaselineCollectionStartedEvent(BaseEvent):
    """Event emitted when baseline data collection begins.

    Phase: 1 (Baseline)
    Priority: P1 (High)
    """

    type: Literal["baseline.collection.started"] = "baseline.collection.started"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    tasks: list[BaselineTask] = Field(..., description="List of baseline collection tasks")


class BaselineDataCollectedEvent(BaseEvent):
    """Event emitted when baseline data is collected from a domain.

    Phase: 1 (Baseline)
    Priority: P1 (High)
    """

    type: Literal["baseline.data.collected"] = "baseline.data.collected"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    domain: str = Field(..., description="Domain that collected the data")
    metrics: dict[str, Any] = Field(..., description="Collected metrics data")
    collection_timestamp: datetime = Field(..., description="When data was collected")


class BaselineAggregationCompletedEvent(BaseEvent):
    """Event emitted when all baseline data is aggregated.

    Phase: 1 (Baseline)
    Priority: P1 (High)
    """

    type: Literal["baseline.aggregation.completed"] = "baseline.aggregation.completed"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    aggregated_data: dict[str, Any] = Field(..., description="Aggregated baseline data from all domains")
    summary: str = Field(..., description="Summary of baseline data collection")


# ============================================================================
# Phase 1.5 (Strategy Planning) - Strategy Planning and Approval
# ============================================================================


class StrategyPlanningStartedEvent(BaseEvent):
    """Event emitted when strategy planning begins.

    Phase: 1.5 (Strategy Planning)
    Priority: P1 (High)
    """

    type: Literal["strategy.planning.started"] = "strategy.planning.started"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    baseline_summary: dict[str, Any] = Field(..., description="Summary of baseline data for planning")


class StrategyProposalReadyEvent(BaseEvent):
    """Event emitted when strategy proposal is ready for review.

    Phase: 1.5 (Strategy Planning)
    Priority: P1 (High)
    """

    type: Literal["strategy.proposal.ready"] = "strategy.proposal.ready"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    proposal: dict[str, Any] = Field(..., description="Strategy proposal data")


class StrategyReviewRequestedEvent(BaseEvent):
    """Event emitted when strategy review is requested from user.

    Phase: 1.5 (Strategy Planning)
    Priority: P1 (High)
    """

    type: Literal["strategy.review.requested"] = "strategy.review.requested"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    proposal: dict[str, Any] = Field(..., description="Strategy proposal for review")
    review_deadline: datetime = Field(..., description="Deadline for review")


class StrategyModification(BaseModel):
    """Model for strategy modification."""

    field: str = Field(..., description="Field being modified")
    old_value: Any = Field(..., description="Previous value")
    new_value: Any = Field(..., description="New value")
    reason: str = Field(..., description="Reason for modification")


class StrategyModifiedEvent(BaseEvent):
    """Event emitted when strategy is modified based on user feedback.

    Phase: 1.5 (Strategy Planning)
    Priority: P1 (High)
    """

    type: Literal["strategy.modified"] = "strategy.modified"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    modifications: list[StrategyModification] = Field(..., description="List of modifications made")


class StrategyApprovedEvent(BaseEvent):
    """Event emitted when strategy is approved by user.

    Phase: 1.5 (Strategy Planning)
    Priority: P1 (High)
    """

    type: Literal["strategy.approved"] = "strategy.approved"
    priority: int = Field(default=1, ge=0, le=3)
    project_id: str = Field(..., description="Project identifier")
    final_strategy: dict[str, Any] = Field(..., description="Final approved strategy")
    approval_timestamp: datetime = Field(..., description="When strategy was approved")
