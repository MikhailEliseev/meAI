"""Error handling and recovery events.

This module provides events for error handling, retry logic, and rollback operations:
- ErrorOccurredEvent: Error detection (P0 priority - FIXED)
- ErrorRetryAttemptedEvent: Retry attempt tracking
- ErrorResolvedEvent: Error resolution confirmation
- ErrorEscalatedEvent: Error escalation to operator or user
- RollbackInitiatedEvent: Rollback operation start
- RollbackCompletedEvent: Rollback operation completion
"""

from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent, ErrorSeverity, ErrorType


class ErrorOccurredData(BaseModel):
    """Data for ErrorOccurredEvent."""

    error_type: ErrorType = Field(..., description="Type of error")
    error_severity: ErrorSeverity = Field(..., description="Error severity level")
    error_message: str = Field(..., description="Human-readable error message")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional error context")


class ErrorOccurredEvent(BaseEvent):
    """Event emitted when an error occurs.

    Priority: P0 (critical) - FIXED.
    """

    type: str = Field(default="error.occurred", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: ErrorOccurredData


class ErrorRetryAttemptedData(BaseModel):
    """Data for ErrorRetryAttemptedEvent."""

    original_error_id: str = Field(..., description="ID of the original error event")
    retry_attempt: int = Field(..., description="Current retry attempt number")
    max_retries: int = Field(..., description="Maximum retry attempts")
    retry_strategy: str = Field(..., description="Retry strategy being used")
    next_retry_at: Optional[datetime] = Field(default=None, description="When next retry will be attempted")


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
    resolution_method: str = Field(..., description="How error was resolved")
    resolution_time: datetime = Field(..., description="When error was resolved")
    notes: Optional[str] = Field(default=None, description="Additional resolution notes")


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
    escalation_reason: str = Field(..., description="Reason for escalation")
    escalated_to: str = Field(..., description="Who error is escalated to")
    escalation_level: int = Field(..., description="Escalation level")


class ErrorEscalatedEvent(BaseEvent):
    """Event emitted when an error is escalated.

    Priority: P0 (critical) - requires immediate attention.
    """

    type: str = Field(default="error.escalated", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: ErrorEscalatedData


class RollbackInitiatedData(BaseModel):
    """Data for RollbackInitiatedEvent."""

    reason: str = Field(..., description="Reason for rollback")
    target_snapshot_id: str = Field(..., description="Target snapshot to restore")
    affected_components: list[str] = Field(..., description="Components affected by rollback")


class RollbackInitiatedEvent(BaseEvent):
    """Event emitted when a rollback operation is initiated.

    Priority: P0 (critical) - rollback is a critical operation.
    """

    type: str = Field(default="rollback.initiated", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: RollbackInitiatedData


class RollbackCompletedData(BaseModel):
    """Data for RollbackCompletedEvent."""

    rollback_id: str = Field(..., description="Rollback operation ID")
    success: bool = Field(..., description="Whether rollback succeeded")
    restored_snapshot_id: str = Field(..., description="Snapshot that was restored")
    rollback_duration: float = Field(..., description="Duration of rollback in seconds")
    notes: Optional[str] = Field(default=None, description="Additional notes about rollback")


class RollbackCompletedEvent(BaseEvent):
    """Event emitted when a rollback operation completes.

    Priority: P0 (critical) - rollback completion is critical information.
    """

    type: str = Field(default="rollback.completed", frozen=True)
    priority: int = Field(default=0, frozen=True)  # P0 - critical
    data: RollbackCompletedData
