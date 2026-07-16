"""Client interaction events for communication and approval flow.

This module defines all client interaction events:
- ClientCommunicationRecordedEvent (P2 priority) - Communication tracking
- ClientApprovalRequestedEvent (P1 priority) - Approval requests
- ClientApprovalApprovedEvent (P1 priority) - Approvals
- ClientApprovalRejectedEvent (P1 priority) - Rejections with severity
- ClientRevisionRequestedEvent (P1 priority) - Revision requests
- ClientReviewRequestedEvent (P1 priority) - Sprint review requests
- ClientFeedbackReceivedEvent (P1 priority) - Sprint feedback

All events inherit from BaseEvent and use Pydantic v2 syntax.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from meai.events.base import BaseEvent
from meai.events.task_events import Deliverable


class DeliverableRevision(BaseModel):
    """Deliverable revision model for client feedback.

    Represents a revision request for a deliverable.
    """

    deliverable_id: str = Field(..., description="Deliverable identifier")
    revision_type: Literal["minor", "major"] = Field(..., description="Revision type")
    requested_changes: list[str] = Field(..., description="List of requested changes")
    deadline: datetime | None = Field(default=None, description="Revision deadline")


# ============================================================================
# Communication Events
# ============================================================================


class ClientCommunicationData(BaseModel):
    """Data for ClientCommunicationRecordedEvent."""

    project_id: str = Field(..., description="Project identifier")
    communication_id: str = Field(..., description="Communication identifier")
    communication_type: Literal["email", "call", "meeting", "chat"] = Field(
        ..., description="Communication type"
    )
    direction: Literal["inbound", "outbound"] = Field(..., description="Communication direction")
    participants: list[str] = Field(..., description="Communication participants")
    summary: str = Field(..., description="Communication summary")
    action_items: list[str] = Field(default_factory=list, description="Action items from communication")
    recorded_at: datetime = Field(..., description="Communication timestamp")
    related_to: str | None = Field(default=None, description="Related entity (proposal, sprint, etc.)")


class ClientCommunicationRecordedEvent(BaseEvent):
    """Client communication recorded event.

    Emitted when a client communication is recorded.
    Priority: P2 (normal)
    """

    type: Literal["client.communication.recorded"] = "client.communication.recorded"
    priority: int = Field(default=2, ge=0, le=3)
    data: ClientCommunicationData


# ============================================================================
# Approval Flow Events
# ============================================================================


class ClientApprovalRequestedData(BaseModel):
    """Data for ClientApprovalRequestedEvent."""

    project_id: str = Field(..., description="Project identifier")
    approval_id: str = Field(..., description="Approval identifier")
    deliverable_id: str = Field(..., description="Deliverable identifier")
    deliverable_title: str = Field(..., description="Deliverable title")
    deliverable_description: str = Field(..., description="Deliverable description")
    deliverable_url: str = Field(..., description="Deliverable URL")
    requested_at: datetime = Field(..., description="Approval request timestamp")
    deadline: datetime | None = Field(default=None, description="Approval deadline")


class ClientApprovalRequestedEvent(BaseEvent):
    """Client approval requested event.

    Emitted when a deliverable is submitted for client approval.
    Priority: P1 (high)
    """

    type: Literal["client.approval.requested"] = "client.approval.requested"
    priority: int = Field(default=1, ge=0, le=3)
    data: ClientApprovalRequestedData


class ClientApprovalApprovedData(BaseModel):
    """Data for ClientApprovalApprovedEvent."""

    project_id: str = Field(..., description="Project identifier")
    approval_id: str = Field(..., description="Approval identifier")
    deliverable_id: str = Field(..., description="Deliverable identifier")
    approved_at: datetime = Field(..., description="Approval timestamp")
    approved_by: str = Field(..., description="Client who approved")
    feedback: str | None = Field(default=None, description="Client feedback")


class ClientApprovalApprovedEvent(BaseEvent):
    """Client approval approved event.

    Emitted when a client approves a deliverable.
    Priority: P1 (high)
    """

    type: Literal["client.approval.approved"] = "client.approval.approved"
    priority: int = Field(default=1, ge=0, le=3)
    data: ClientApprovalApprovedData


class ClientApprovalRejectedData(BaseModel):
    """Data for ClientApprovalRejectedEvent."""

    project_id: str = Field(..., description="Project identifier")
    approval_id: str = Field(..., description="Approval identifier")
    deliverable_id: str = Field(..., description="Deliverable identifier")
    rejected_at: datetime = Field(..., description="Rejection timestamp")
    rejected_by: str = Field(..., description="Client who rejected")
    reason: str = Field(..., description="Rejection reason")
    severity: Literal["minor", "major", "critical"] = Field(..., description="Rejection severity")
    requested_changes: list[str] = Field(..., description="List of requested changes")


class ClientApprovalRejectedEvent(BaseEvent):
    """Client approval rejected event.

    Emitted when a client rejects a deliverable.
    Priority: P1 (high)
    """

    type: Literal["client.approval.rejected"] = "client.approval.rejected"
    priority: int = Field(default=1, ge=0, le=3)
    data: ClientApprovalRejectedData


class ClientRevisionRequestedData(BaseModel):
    """Data for ClientRevisionRequestedEvent."""

    project_id: str = Field(..., description="Project identifier")
    revision_id: str = Field(..., description="Revision identifier")
    deliverable_id: str = Field(..., description="Deliverable identifier")
    revision: DeliverableRevision = Field(..., description="Revision details")
    requested_at: datetime = Field(..., description="Revision request timestamp")
    requested_by: str = Field(..., description="Client who requested revision")


class ClientRevisionRequestedEvent(BaseEvent):
    """Client revision requested event.

    Emitted when a client requests revisions to a deliverable.
    Priority: P1 (high)
    """

    type: Literal["client.revision.requested"] = "client.revision.requested"
    priority: int = Field(default=1, ge=0, le=3)
    data: ClientRevisionRequestedData


# ============================================================================
# Sprint Review Events
# ============================================================================


class ClientReviewRequestedData(BaseModel):
    """Data for ClientReviewRequestedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    review_id: str = Field(..., description="Review identifier")
    deliverables: list[Deliverable] = Field(..., description="Sprint deliverables for review")
    review_deadline: datetime = Field(..., description="Review deadline")
    requested_at: datetime = Field(..., description="Review request timestamp")


class ClientReviewRequestedEvent(BaseEvent):
    """Client review requested event.

    Emitted when sprint deliverables are submitted for client review.
    Priority: P1 (high)
    """

    type: Literal["client.review.requested"] = "client.review.requested"
    priority: int = Field(default=1, ge=0, le=3)
    data: ClientReviewRequestedData


class ClientFeedbackReceivedData(BaseModel):
    """Data for ClientFeedbackReceivedEvent."""

    project_id: str = Field(..., description="Project identifier")
    sprint_id: str = Field(..., description="Sprint identifier")
    review_id: str = Field(..., description="Review identifier")
    feedback_id: str = Field(..., description="Feedback identifier")
    overall_feedback: str = Field(..., description="Overall client feedback")
    approved_deliverables: list[str] = Field(
        default_factory=list, description="List of approved deliverable IDs"
    )
    revision_requests: list[DeliverableRevision] = Field(
        default_factory=list, description="List of revision requests"
    )
    received_at: datetime = Field(..., description="Feedback received timestamp")
    received_from: str = Field(..., description="Client who provided feedback")


class ClientFeedbackReceivedEvent(BaseEvent):
    """Client feedback received event.

    Emitted when client provides feedback on sprint deliverables.
    Priority: P1 (high)
    """

    type: Literal["client.feedback.received"] = "client.feedback.received"
    priority: int = Field(default=1, ge=0, le=3)
    data: ClientFeedbackReceivedData
