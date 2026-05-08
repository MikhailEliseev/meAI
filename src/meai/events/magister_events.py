"""Inter-magister communication events.

This module provides events for magisters to communicate and coordinate:
- Request/Response pattern for data exchange
- Dependency management for blocked/resolved states

All events use P2 (normal) priority.
"""

from typing import Literal

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent


# Request/Response Pattern


class MagisterDataRequestData(BaseModel):
    """Data payload for magister data request."""

    project_id: str = Field(..., description="Project ID")
    requesting_magister: str = Field(..., description="Magister requesting data")
    target_magister: str = Field(..., description="Magister being requested from")
    data_type: str = Field(..., description="Type of data being requested")
    parameters: dict = Field(default_factory=dict, description="Request parameters")
    urgency: Literal["low", "medium", "high"] = Field(..., description="Request urgency")
    deadline: str | None = Field(default=None, description="Optional deadline (ISO 8601)")


class MagisterDataRequestEvent(BaseEvent):
    """Event for magister requesting data from another magister.

    Used when one magister needs data from another to complete their work.
    The target magister should respond with MagisterDataResponseEvent.
    """

    type: Literal["magister.data.request"] = "magister.data.request"
    priority: int = Field(default=2, ge=0, le=3)
    data: MagisterDataRequestData


class MagisterDataResponseData(BaseModel):
    """Data payload for magister data response."""

    project_id: str = Field(..., description="Project ID")
    request_id: str = Field(..., description="ID of the request being responded to")
    responding_magister: str = Field(..., description="Magister responding")
    requesting_magister: str = Field(..., description="Magister that made the request")
    data: dict = Field(default_factory=dict, description="Response data")
    status: Literal["success", "partial", "failed"] = Field(..., description="Response status")
    notes: str | None = Field(default=None, description="Optional notes about the response")


class MagisterDataResponseEvent(BaseEvent):
    """Event for magister responding to a data request.

    Uses reply_to field to link back to the original request.
    Status indicates whether the request was fully satisfied.
    """

    type: Literal["magister.data.response"] = "magister.data.response"
    priority: int = Field(default=2, ge=0, le=3)
    data: MagisterDataResponseData


# Dependency Management


class MagisterDependencyBlockedData(BaseModel):
    """Data payload for magister dependency blocked."""

    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID that is blocked")
    blocked_magister: str = Field(..., description="Magister that is blocked")
    blocking_magister: str = Field(..., description="Magister causing the block")
    reason: str = Field(..., description="Reason for the block")
    estimated_unblock: str | None = Field(
        default=None, description="Estimated unblock time (ISO 8601)"
    )


class MagisterDependencyBlockedEvent(BaseEvent):
    """Event for magister reporting a dependency block.

    Sent when a magister cannot proceed because they are waiting
    for another magister to complete work.
    """

    type: Literal["magister.dependency.blocked"] = "magister.dependency.blocked"
    priority: int = Field(default=2, ge=0, le=3)
    data: MagisterDependencyBlockedData


class MagisterDependencyResolvedData(BaseModel):
    """Data payload for magister dependency resolved."""

    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID that was blocked")
    blocked_magister: str = Field(..., description="Magister that was blocked")
    blocking_magister: str = Field(..., description="Magister that was blocking")
    resolved_at: str = Field(..., description="When the dependency was resolved (ISO 8601)")


class MagisterDependencyResolvedEvent(BaseEvent):
    """Event for magister reporting a dependency resolution.

    Sent when a magister completes work that was blocking another magister.
    The blocked magister can now proceed with their work.
    """

    type: Literal["magister.dependency.resolved"] = "magister.dependency.resolved"
    priority: int = Field(default=2, ge=0, le=3)
    data: MagisterDependencyResolvedData
