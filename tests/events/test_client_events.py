"""Tests for client interaction events.

This module tests all client interaction events:
- ClientCommunicationRecordedEvent (P2 priority)
- ClientApprovalRequestedEvent (P1 priority)
- ClientApprovalApprovedEvent (P1 priority)
- ClientApprovalRejectedEvent (P1 priority)
- ClientRevisionRequestedEvent (P1 priority)
- ClientReviewRequestedEvent (P1 priority)
- ClientFeedbackReceivedEvent (P1 priority)
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from meai.events.client_events import (
    ClientApprovalApprovedData,
    ClientApprovalApprovedEvent,
    ClientApprovalRejectedData,
    ClientApprovalRejectedEvent,
    ClientApprovalRequestedData,
    ClientApprovalRequestedEvent,
    ClientCommunicationData,
    ClientCommunicationRecordedEvent,
    ClientFeedbackReceivedData,
    ClientFeedbackReceivedEvent,
    ClientRevisionRequestedData,
    ClientRevisionRequestedEvent,
    ClientReviewRequestedData,
    ClientReviewRequestedEvent,
    DeliverableRevision,
)


class TestDeliverableRevision:
    """Test DeliverableRevision model."""

    def test_deliverable_revision_minor(self):
        """Test deliverable revision with minor changes."""
        revision = DeliverableRevision(
            deliverable_id="deliv_001",
            revision_type="minor",
            requested_changes=["Fix typo in section 3", "Update chart colors"],
            deadline=datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC),
        )

        assert revision.deliverable_id == "deliv_001"
        assert revision.revision_type == "minor"
        assert len(revision.requested_changes) == 2
        assert revision.deadline == datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)

    def test_deliverable_revision_major(self):
        """Test deliverable revision with major changes."""
        revision = DeliverableRevision(
            deliverable_id="deliv_002",
            revision_type="major",
            requested_changes=[
                "Restructure entire report",
                "Add competitive analysis section",
                "Revise recommendations",
            ],
            deadline=datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC),
        )

        assert revision.deliverable_id == "deliv_002"
        assert revision.revision_type == "major"
        assert len(revision.requested_changes) == 3

    def test_deliverable_revision_no_deadline(self):
        """Test deliverable revision without deadline."""
        revision = DeliverableRevision(
            deliverable_id="deliv_003",
            revision_type="minor",
            requested_changes=["Update logo"],
        )

        assert revision.deliverable_id == "deliv_003"
        assert revision.deadline is None


class TestClientCommunicationRecordedEvent:
    """Test ClientCommunicationRecordedEvent."""

    def test_communication_email_outbound(self):
        """Test email communication outbound."""
        data = ClientCommunicationData(
            project_id="proj_123",
            communication_id="comm_001",
            communication_type="email",
            direction="outbound",
            participants=["client@example.com", "manager@aim.com"],
            summary="Sent project proposal and timeline",
            action_items=["Client to review proposal by Friday", "Schedule follow-up call"],
            recorded_at=datetime(2026, 5, 8, 10, 0, 0, tzinfo=UTC),
            related_to="proposal_v1",
        )

        event = ClientCommunicationRecordedEvent(
            source="operator",
            target="project-manager",
            data=data,
        )

        assert event.type == "client.communication.recorded"
        assert event.priority == 2
        assert event.source == "operator"
        assert event.target == "project-manager"
        assert isinstance(event.id, UUID)
        assert event.data.project_id == "proj_123"
        assert event.data.communication_type == "email"
        assert event.data.direction == "outbound"
        assert len(event.data.participants) == 2
        assert len(event.data.action_items) == 2

    def test_communication_call_inbound(self):
        """Test call communication inbound."""
        data = ClientCommunicationData(
            project_id="proj_456",
            communication_id="comm_002",
            communication_type="call",
            direction="inbound",
            participants=["client@example.com"],
            summary="Client called with urgent request for competitor analysis",
            action_items=["Start competitor analysis immediately"],
            recorded_at=datetime(2026, 5, 8, 14, 30, 0, tzinfo=UTC),
        )

        event = ClientCommunicationRecordedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.data.communication_type == "call"
        assert event.data.direction == "inbound"
        assert event.data.related_to is None

    def test_communication_meeting(self):
        """Test meeting communication."""
        data = ClientCommunicationData(
            project_id="proj_789",
            communication_id="comm_003",
            communication_type="meeting",
            direction="outbound",
            participants=["client@example.com", "ceo@example.com", "manager@aim.com"],
            summary="Sprint review meeting - presented deliverables",
            action_items=["Client to provide feedback by Monday", "Schedule next sprint planning"],
            recorded_at=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
            related_to="sprint_001",
        )

        event = ClientCommunicationRecordedEvent(
            source="operator",
            target="project-manager",
            data=data,
        )

        assert event.data.communication_type == "meeting"
        assert len(event.data.participants) == 3

    def test_communication_chat(self):
        """Test chat communication."""
        data = ClientCommunicationData(
            project_id="proj_101",
            communication_id="comm_004",
            communication_type="chat",
            direction="inbound",
            participants=["client@example.com"],
            summary="Quick question about report deadline",
            action_items=[],
            recorded_at=datetime(2026, 5, 8, 16, 0, 0, tzinfo=UTC),
        )

        event = ClientCommunicationRecordedEvent(
            source="operator",
            target="project-manager",
            data=data,
        )

        assert event.data.communication_type == "chat"
        assert len(event.data.action_items) == 0


class TestClientApprovalRequestedEvent:
    """Test ClientApprovalRequestedEvent."""

    def test_approval_requested(self):
        """Test approval requested event."""
        data = ClientApprovalRequestedData(
            project_id="proj_123",
            approval_id="appr_001",
            deliverable_id="deliv_001",
            deliverable_title="SEO Strategy Report",
            deliverable_description="Comprehensive SEO strategy for Q2 2026",
            deliverable_url="https://aim.com/deliverables/deliv_001",
            requested_at=datetime(2026, 5, 8, 10, 0, 0, tzinfo=UTC),
            deadline=datetime(2026, 5, 10, 17, 0, 0, tzinfo=UTC),
        )

        event = ClientApprovalRequestedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "client.approval.requested"
        assert event.priority == 1
        assert event.data.project_id == "proj_123"
        assert event.data.deliverable_title == "SEO Strategy Report"
        assert event.data.deadline is not None

    def test_approval_requested_no_deadline(self):
        """Test approval requested without deadline."""
        data = ClientApprovalRequestedData(
            project_id="proj_456",
            approval_id="appr_002",
            deliverable_id="deliv_002",
            deliverable_title="Content Calendar",
            deliverable_description="Monthly content calendar",
            deliverable_url="https://aim.com/deliverables/deliv_002",
            requested_at=datetime(2026, 5, 8, 11, 0, 0, tzinfo=UTC),
        )

        event = ClientApprovalRequestedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.data.deadline is None


class TestClientApprovalApprovedEvent:
    """Test ClientApprovalApprovedEvent."""

    def test_approval_approved(self):
        """Test approval approved event."""
        data = ClientApprovalApprovedData(
            project_id="proj_123",
            approval_id="appr_001",
            deliverable_id="deliv_001",
            approved_at=datetime(2026, 5, 9, 14, 0, 0, tzinfo=UTC),
            approved_by="client@example.com",
            feedback="Excellent work! Ready to proceed.",
        )

        event = ClientApprovalApprovedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.type == "client.approval.approved"
        assert event.priority == 1
        assert event.data.approval_id == "appr_001"
        assert event.data.approved_by == "client@example.com"
        assert event.data.feedback is not None

    def test_approval_approved_no_feedback(self):
        """Test approval approved without feedback."""
        data = ClientApprovalApprovedData(
            project_id="proj_456",
            approval_id="appr_002",
            deliverable_id="deliv_002",
            approved_at=datetime(2026, 5, 9, 15, 0, 0, tzinfo=UTC),
            approved_by="ceo@example.com",
        )

        event = ClientApprovalApprovedEvent(
            source="operator",
            target="content-magister",
            data=data,
        )

        assert event.data.feedback is None


class TestClientApprovalRejectedEvent:
    """Test ClientApprovalRejectedEvent."""

    def test_approval_rejected_minor(self):
        """Test approval rejected with minor severity."""
        data = ClientApprovalRejectedData(
            project_id="proj_123",
            approval_id="appr_003",
            deliverable_id="deliv_003",
            rejected_at=datetime(2026, 5, 9, 16, 0, 0, tzinfo=UTC),
            rejected_by="client@example.com",
            reason="Some typos and formatting issues",
            severity="minor",
            requested_changes=["Fix typos in section 2", "Adjust chart formatting"],
        )

        event = ClientApprovalRejectedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.type == "client.approval.rejected"
        assert event.priority == 1
        assert event.data.severity == "minor"
        assert len(event.data.requested_changes) == 2

    def test_approval_rejected_major(self):
        """Test approval rejected with major severity."""
        data = ClientApprovalRejectedData(
            project_id="proj_456",
            approval_id="appr_004",
            deliverable_id="deliv_004",
            rejected_at=datetime(2026, 5, 9, 17, 0, 0, tzinfo=UTC),
            rejected_by="ceo@example.com",
            reason="Missing key sections and analysis",
            severity="major",
            requested_changes=[
                "Add competitive analysis section",
                "Include ROI projections",
                "Revise recommendations",
            ],
        )

        event = ClientApprovalRejectedEvent(
            source="operator",
            target="content-magister",
            data=data,
        )

        assert event.data.severity == "major"
        assert len(event.data.requested_changes) == 3

    def test_approval_rejected_critical(self):
        """Test approval rejected with critical severity."""
        data = ClientApprovalRejectedData(
            project_id="proj_789",
            approval_id="appr_005",
            deliverable_id="deliv_005",
            rejected_at=datetime(2026, 5, 9, 18, 0, 0, tzinfo=UTC),
            rejected_by="client@example.com",
            reason="Completely wrong approach - needs full rework",
            severity="critical",
            requested_changes=["Complete rework required"],
        )

        event = ClientApprovalRejectedEvent(
            source="operator",
            target="ads-magister",
            data=data,
        )

        assert event.data.severity == "critical"


class TestClientRevisionRequestedEvent:
    """Test ClientRevisionRequestedEvent."""

    def test_revision_requested_minor(self):
        """Test revision requested with minor changes."""
        revision = DeliverableRevision(
            deliverable_id="deliv_001",
            revision_type="minor",
            requested_changes=["Update chart colors", "Fix typo"],
            deadline=datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC),
        )

        data = ClientRevisionRequestedData(
            project_id="proj_123",
            revision_id="rev_001",
            deliverable_id="deliv_001",
            revision=revision,
            requested_at=datetime(2026, 5, 9, 10, 0, 0, tzinfo=UTC),
            requested_by="client@example.com",
        )

        event = ClientRevisionRequestedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.type == "client.revision.requested"
        assert event.priority == 1
        assert event.data.revision.revision_type == "minor"
        assert len(event.data.revision.requested_changes) == 2

    def test_revision_requested_major(self):
        """Test revision requested with major changes."""
        revision = DeliverableRevision(
            deliverable_id="deliv_002",
            revision_type="major",
            requested_changes=["Restructure report", "Add new analysis"],
            deadline=datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC),
        )

        data = ClientRevisionRequestedData(
            project_id="proj_456",
            revision_id="rev_002",
            deliverable_id="deliv_002",
            revision=revision,
            requested_at=datetime(2026, 5, 9, 11, 0, 0, tzinfo=UTC),
            requested_by="ceo@example.com",
        )

        event = ClientRevisionRequestedEvent(
            source="operator",
            target="content-magister",
            data=data,
        )

        assert event.data.revision.revision_type == "major"


class TestClientReviewRequestedEvent:
    """Test ClientReviewRequestedEvent."""

    def test_review_requested_single_deliverable(self):
        """Test review requested with single deliverable."""
        from meai.events.task_events import Deliverable

        deliverable = Deliverable(
            type="report",
            title="SEO Analysis Report",
            description="Comprehensive SEO analysis",
            url="https://aim.com/reports/seo_001",
            requires_approval=True,
        )

        data = ClientReviewRequestedData(
            project_id="proj_123",
            sprint_id="sprint_001",
            review_id="review_001",
            deliverables=[deliverable],
            review_deadline=datetime(2026, 5, 12, 17, 0, 0, tzinfo=UTC),
            requested_at=datetime(2026, 5, 10, 10, 0, 0, tzinfo=UTC),
        )

        event = ClientReviewRequestedEvent(
            source="operator",
            target="project-manager",
            data=data,
        )

        assert event.type == "client.review.requested"
        assert event.priority == 1
        assert event.data.sprint_id == "sprint_001"
        assert len(event.data.deliverables) == 1
        assert event.data.deliverables[0].requires_approval is True

    def test_review_requested_multiple_deliverables(self):
        """Test review requested with multiple deliverables."""
        from meai.events.task_events import Deliverable

        deliverables = [
            Deliverable(
                type="report",
                title="SEO Report",
                description="SEO analysis",
                url="https://aim.com/reports/seo_001",
                requires_approval=True,
            ),
            Deliverable(
                type="dashboard",
                title="Analytics Dashboard",
                description="Real-time analytics",
                url="https://analytics.aim.com/dashboard",
                requires_approval=False,
            ),
            Deliverable(
                type="document",
                title="Content Calendar",
                description="Monthly content plan",
                file_path="/deliverables/content_calendar.pdf",
                requires_approval=True,
            ),
        ]

        data = ClientReviewRequestedData(
            project_id="proj_456",
            sprint_id="sprint_002",
            review_id="review_002",
            deliverables=deliverables,
            review_deadline=datetime(2026, 5, 15, 17, 0, 0, tzinfo=UTC),
            requested_at=datetime(2026, 5, 12, 10, 0, 0, tzinfo=UTC),
        )

        event = ClientReviewRequestedEvent(
            source="operator",
            target="project-manager",
            data=data,
        )

        assert len(event.data.deliverables) == 3


class TestClientFeedbackReceivedEvent:
    """Test ClientFeedbackReceivedEvent."""

    def test_feedback_received_with_revisions(self):
        """Test feedback received with revision requests."""
        revisions = [
            DeliverableRevision(
                deliverable_id="deliv_001",
                revision_type="minor",
                requested_changes=["Fix typo", "Update chart"],
                deadline=datetime(2026, 5, 13, 12, 0, 0, tzinfo=UTC),
            ),
            DeliverableRevision(
                deliverable_id="deliv_002",
                revision_type="major",
                requested_changes=["Add competitive analysis"],
                deadline=datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC),
            ),
        ]

        data = ClientFeedbackReceivedData(
            project_id="proj_123",
            sprint_id="sprint_001",
            review_id="review_001",
            feedback_id="feedback_001",
            overall_feedback="Good work overall, but needs some improvements",
            approved_deliverables=["deliv_003"],
            revision_requests=revisions,
            received_at=datetime(2026, 5, 11, 14, 0, 0, tzinfo=UTC),
            received_from="client@example.com",
        )

        event = ClientFeedbackReceivedEvent(
            source="operator",
            target=["seo-magister", "content-magister"],
            data=data,
        )

        assert event.type == "client.feedback.received"
        assert event.priority == 1
        assert event.data.review_id == "review_001"
        assert len(event.data.approved_deliverables) == 1
        assert len(event.data.revision_requests) == 2
        assert event.data.revision_requests[0].revision_type == "minor"
        assert event.data.revision_requests[1].revision_type == "major"

    def test_feedback_received_all_approved(self):
        """Test feedback received with all deliverables approved."""
        data = ClientFeedbackReceivedData(
            project_id="proj_456",
            sprint_id="sprint_002",
            review_id="review_002",
            feedback_id="feedback_002",
            overall_feedback="Excellent work! All deliverables approved.",
            approved_deliverables=["deliv_004", "deliv_005", "deliv_006"],
            revision_requests=[],
            received_at=datetime(2026, 5, 13, 15, 0, 0, tzinfo=UTC),
            received_from="ceo@example.com",
        )

        event = ClientFeedbackReceivedEvent(
            source="operator",
            target="project-manager",
            data=data,
        )

        assert len(event.data.approved_deliverables) == 3
        assert len(event.data.revision_requests) == 0

    def test_feedback_received_no_approvals(self):
        """Test feedback received with no approvals."""
        revisions = [
            DeliverableRevision(
                deliverable_id="deliv_007",
                revision_type="major",
                requested_changes=["Complete rework required"],
                deadline=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
            ),
        ]

        data = ClientFeedbackReceivedData(
            project_id="proj_789",
            sprint_id="sprint_003",
            review_id="review_003",
            feedback_id="feedback_003",
            overall_feedback="Needs significant improvements",
            approved_deliverables=[],
            revision_requests=revisions,
            received_at=datetime(2026, 5, 14, 16, 0, 0, tzinfo=UTC),
            received_from="client@example.com",
        )

        event = ClientFeedbackReceivedEvent(
            source="operator",
            target="ads-magister",
            data=data,
        )

        assert len(event.data.approved_deliverables) == 0
        assert len(event.data.revision_requests) == 1
