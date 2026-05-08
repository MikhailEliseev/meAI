"""Error handling and recovery events.

This module provides events for error handling, retry logic, and rollback operations:
- ErrorOccurredEvent: Error detection with dynamic priority based on severity
- ErrorRetryAttemptedEvent: Retry attempt tracking
- ErrorResolvedEvent: Error resolution confirmation
- ErrorEscalatedEvent: Error escalation to operator or user
- RollbackInitiatedEvent: Rollback operation start
- RollbackCompletedEvent: Rollback operation completion
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent, ErrorSeverity, ErrorType


class ErrorOccurredData(BaseModel):
    """Data for ErrorOccurredEvent."""

    project_id: str | None = Field(default=None, description="Project ID if error is project-specific")
    task_id: str | None = Field(default=None, description="Task ID if error is task-specific")
    component: str = Field(..., description="Component where error occurred")
    error_type: ErrorType = Field(..., description="Type of error")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    error_message: str = Field(..., description="Human-readable error message")
    stack_trace: str | None = Field(default=None, description="Stack trace if available")
    context: dict = Field(default_factory=dict, description="Additional error context")
    retry_possible: bool = Field(..., description="Whether error can be retried")
    retry_count: int = Field(..., description="Current retry count")
    max_retries: int = Field(..., description="Maximum retry attempts")


class ErrorOccurredEvent(BaseEvent):
    """Event emitted when an error occurs.

    Priority is dynamically set based on severity:
    - CRITICAL: P0
    - HIGH: P1
    - MEDIUM: P2
    - LOW: P3
    """

    type: str = Field(default="error.occurred", frozen=True)
    data: ErrorOccurredData

    def __init__(self, **data):
        """Initialize with dynamic priority based on severity."""
        # Extract severity to determine priority
        event_data = data.get("data")
        if event_data:
            severity = event_data.severity if isinstance(event_data, ErrorOccurredData) else event_data.get("severity")
            if severity:
                # Map severity to priority
                severity_to_priority = {
                    ErrorSeverity.CRITICAL: 0,
                    ErrorSeverity.HIGH: 1,
                    ErrorSeverity.MEDIUM: 2,
                    ErrorSeverity.LOW: 3,
                }
                # Convert string to enum if needed
                if isinstance(severity, str):
                    severity = ErrorSeverity(severity)
                data["priority"] = severity_to_priority.get(severity, 2)

        super().__init__(**data)


class ErrorRetryAttemptedData(BaseModel):
    """Data for ErrorRetryAttemptedEvent."""

    original_error_id: str = Field(..., description="ID of the original error event")
    component: str = Field(..., description="Component attempting retry")
    retry_number: int = Field(..., description="Current retry attempt number")
    max_retries: int = Field(..., description="Maximum retry attempts")
    attempted_at: datetime = Field(..., description="When retry was attempted")


class ErrorRetryAttemptedEvent(BaseEvent):
    """Event emitted when an error retry is attempted.

    Priority: P1 (high) - retry attempts need monitoring.
    """

    type: str = Field(default="error.retry_attempted", frozen=True)
    priority: int = Field(default=1, frozen=True)  # P1 - high priority
    data: ErrorRetryAttemptedData


class ErrorResolvedData(BaseModel):
    """Data for ErrorResolvedEvent."""

    original_error_id: str = Field(..., description="ID of the original error event")
    component: str = Field(..., description="Component where error was resolved")
    resolved_at: datetime = Field(..., description="When error was resolved")
    resolution_method: Literal["retry", "manual", "automatic", "workaround"] = Field(
        ..., description="How error was resolved"
    )
    notes: str | None = Field(default=None, description="Additional resolution notes")


class ErrorResolvedEvent(BaseEvent):
    """Event emitted when an error is resolved.

    Priority: P2 (normal) - informational.
    """

    type: str = Field(default="error.resolved", frozen=True)
    priority: int = Field(default=2, frozen=True)  # P2 - normal
    data: ErrorResolvedData


class ErrorEscalatedData(BaseModel):
    """Data for ErrorEscalatedEvent."""

    original_error_id: str = Field(..., description="ID of the original error event")
    component: str = Field(..., description="Component escalating the error")
    escalated_to: Literal["operator", "user"] = Field(..., description="Who error is escalated to")
    escalated_at: datetime = Field(..., description="When error was escalated")
    reason: str = Field(..., description="Reason for escalation")
    suggested_actions: list[str] = Field(..., description="Suggested actions to resolve")


class ErrorEscalatedEvent(BaseEvent):
    """Event emitted when an error is escalated.

    Priority: P0 (critical) - requires immediate attention.
    """

    type: str = Field(default="error.escalated", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: ErrorEscalatedData


class RollbackInitiatedData(BaseModel):
    """Data for RollbackInitiatedEvent."""

    project_id: str = Field(..., description="Project being rolled back")
    rollback_id: str = Field(..., description="Unique rollback operation ID")
    reason: str = Field(..., description="Reason for rollback")
    target_state: str = Field(..., description="Target state/snapshot to restore")
    initiated_by: str = Field(..., description="Who initiated rollback (operator/system/user)")
    initiated_at: datetime = Field(..., description="When rollback was initiated")


class RollbackInitiatedEvent(BaseEvent):
    """Event emitted when a rollback operation is initiated.

    Priority: P0 (critical) - rollback is a critical operation.
    """

    type: str = Field(default="rollback.initiated", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: RollbackInitiatedData


class RollbackCompletedData(BaseModel):
    """Data for RollbackCompletedEvent."""

    project_id: str = Field(..., description="Project that was rolled back")
    rollback_id: str = Field(..., description="Rollback operation ID")
    completed_at: datetime = Field(..., description="When rollback completed")
    restored_state: str = Field(..., description="State/snapshot that was restored")
    affected_components: list[str] = Field(..., description="Components affected by rollback")


class RollbackCompletedEvent(BaseEvent):
    """Event emitted when a rollback operation completes.

    Priority: P0 (critical) - rollback completion is critical information.
    """

    type: str = Field(default="rollback.completed", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: RollbackCompletedData
