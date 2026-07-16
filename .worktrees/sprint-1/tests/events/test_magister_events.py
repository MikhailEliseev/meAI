"""Tests for inter-magister communication events.

Tests the request/response pattern and dependency management events
that enable magisters to communicate and coordinate work.
"""

import pytest
from uuid import uuid4

from meai.events.magister_events import (
    MagisterDataRequestEvent,
    MagisterDataRequestData,
    MagisterDataResponseEvent,
    MagisterDataResponseData,
    MagisterDependencyBlockedEvent,
    MagisterDependencyBlockedData,
    MagisterDependencyResolvedEvent,
    MagisterDependencyResolvedData,
)


class TestMagisterDataRequestEvent:
    """Test MagisterDataRequestEvent creation and validation."""

    def test_create_basic_request(self):
        """Test creating a basic data request."""
        data = MagisterDataRequestData(
            project_id="proj-123",
            requesting_magister="content-magister",
            target_magister="seo-magister",
            data_type="keyword_research",
            parameters={"topic": "medical marketing"},
            urgency="medium",
        )

        event = MagisterDataRequestEvent(
            source="content-magister",
            target="seo-magister",
            data=data,
        )

        assert event.type == "magister.data.request"
        assert event.priority == 2
        assert event.data.project_id == "proj-123"
        assert event.data.requesting_magister == "content-magister"
        assert event.data.target_magister == "seo-magister"
        assert event.data.data_type == "keyword_research"
        assert event.data.urgency == "medium"
        assert event.data.deadline is None

    def test_request_with_deadline(self):
        """Test request with deadline."""
        data = MagisterDataRequestData(
            project_id="proj-123",
            requesting_magister="content-magister",
            target_magister="seo-magister",
            data_type="keyword_research",
            parameters={},
            urgency="high",
            deadline="2026-05-10T12:00:00Z",
        )

        event = MagisterDataRequestEvent(
            source="content-magister",
            target="seo-magister",
            data=data,
        )

        assert event.data.urgency == "high"
        assert event.data.deadline == "2026-05-10T12:00:00Z"

    def test_request_urgency_validation(self):
        """Test that urgency must be valid literal."""
        # Valid urgencies should work
        for urgency in ["low", "medium", "high"]:
            data = MagisterDataRequestData(
                project_id="proj-123",
                requesting_magister="content-magister",
                target_magister="seo-magister",
                data_type="test",
                parameters={},
                urgency=urgency,
            )
            assert data.urgency == urgency


class TestMagisterDataResponseEvent:
    """Test MagisterDataResponseEvent creation and validation."""

    def test_create_successful_response(self):
        """Test creating a successful response."""
        request_id = str(uuid4())

        data = MagisterDataResponseData(
            project_id="proj-123",
            request_id=request_id,
            responding_magister="seo-magister",
            requesting_magister="content-magister",
            data={"keywords": ["medical marketing", "healthcare SEO"]},
            status="success",
        )

        event = MagisterDataResponseEvent(
            source="seo-magister",
            target="content-magister",
            data=data,
            reply_to=request_id,
        )

        assert event.type == "magister.data.response"
        assert event.priority == 2
        assert event.reply_to == request_id
        assert event.data.request_id == request_id
        assert event.data.status == "success"
        assert event.data.notes is None

    def test_create_partial_response(self):
        """Test creating a partial response with notes."""
        request_id = str(uuid4())

        data = MagisterDataResponseData(
            project_id="proj-123",
            request_id=request_id,
            responding_magister="seo-magister",
            requesting_magister="content-magister",
            data={"keywords": ["medical marketing"]},
            status="partial",
            notes="Only found 1 keyword, need more time for full research",
        )

        event = MagisterDataResponseEvent(
            source="seo-magister",
            target="content-magister",
            data=data,
            reply_to=request_id,
        )

        assert event.data.status == "partial"
        assert event.data.notes == "Only found 1 keyword, need more time for full research"

    def test_create_failed_response(self):
        """Test creating a failed response."""
        request_id = str(uuid4())

        data = MagisterDataResponseData(
            project_id="proj-123",
            request_id=request_id,
            responding_magister="seo-magister",
            requesting_magister="content-magister",
            data={},
            status="failed",
            notes="API rate limit exceeded",
        )

        event = MagisterDataResponseEvent(
            source="seo-magister",
            target="content-magister",
            data=data,
            reply_to=request_id,
        )

        assert event.data.status == "failed"
        assert event.data.notes == "API rate limit exceeded"

    def test_response_status_validation(self):
        """Test that status must be valid literal."""
        request_id = str(uuid4())

        # Valid statuses should work
        for status in ["success", "partial", "failed"]:
            data = MagisterDataResponseData(
                project_id="proj-123",
                request_id=request_id,
                responding_magister="seo-magister",
                requesting_magister="content-magister",
                data={},
                status=status,
            )
            assert data.status == status

    def test_reply_to_correlation(self):
        """Test that reply_to field correctly links to request."""
        request_id = str(uuid4())

        # Create request
        request_data = MagisterDataRequestData(
            project_id="proj-123",
            requesting_magister="content-magister",
            target_magister="seo-magister",
            data_type="keyword_research",
            parameters={},
            urgency="medium",
        )
        request_event = MagisterDataRequestEvent(
            source="content-magister",
            target="seo-magister",
            data=request_data,
        )
        request_event.id = request_id  # Set specific ID for testing

        # Create response
        response_data = MagisterDataResponseData(
            project_id="proj-123",
            request_id=request_id,
            responding_magister="seo-magister",
            requesting_magister="content-magister",
            data={"keywords": []},
            status="success",
        )
        response_event = MagisterDataResponseEvent(
            source="seo-magister",
            target="content-magister",
            data=response_data,
            reply_to=request_id,
        )

        # Verify correlation
        assert response_event.reply_to == str(request_event.id)
        assert response_event.data.request_id == str(request_event.id)


class TestMagisterDependencyBlockedEvent:
    """Test MagisterDependencyBlockedEvent creation and validation."""

    def test_create_blocked_event(self):
        """Test creating a dependency blocked event."""
        data = MagisterDependencyBlockedData(
            project_id="proj-123",
            task_id="task-456",
            blocked_magister="content-magister",
            blocking_magister="seo-magister",
            reason="Waiting for keyword research to complete",
        )

        event = MagisterDependencyBlockedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.type == "magister.dependency.blocked"
        assert event.priority == 2
        assert event.data.blocked_magister == "content-magister"
        assert event.data.blocking_magister == "seo-magister"
        assert event.data.reason == "Waiting for keyword research to complete"
        assert event.data.estimated_unblock is None

    def test_blocked_event_with_estimate(self):
        """Test blocked event with estimated unblock time."""
        data = MagisterDependencyBlockedData(
            project_id="proj-123",
            task_id="task-456",
            blocked_magister="content-magister",
            blocking_magister="seo-magister",
            reason="Waiting for keyword research",
            estimated_unblock="2026-05-09T10:00:00Z",
        )

        event = MagisterDependencyBlockedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.data.estimated_unblock == "2026-05-09T10:00:00Z"


class TestMagisterDependencyResolvedEvent:
    """Test MagisterDependencyResolvedEvent creation and validation."""

    def test_create_resolved_event(self):
        """Test creating a dependency resolved event."""
        data = MagisterDependencyResolvedData(
            project_id="proj-123",
            task_id="task-456",
            blocked_magister="content-magister",
            blocking_magister="seo-magister",
            resolved_at="2026-05-08T15:30:00Z",
        )

        event = MagisterDependencyResolvedEvent(
            source="seo-magister",
            target="content-magister",
            data=data,
        )

        assert event.type == "magister.dependency.resolved"
        assert event.priority == 2
        assert event.data.blocked_magister == "content-magister"
        assert event.data.blocking_magister == "seo-magister"
        assert event.data.resolved_at == "2026-05-08T15:30:00Z"

    def test_resolved_event_targets_blocked_magister(self):
        """Test that resolved event targets the blocked magister."""
        data = MagisterDependencyResolvedData(
            project_id="proj-123",
            task_id="task-456",
            blocked_magister="content-magister",
            blocking_magister="seo-magister",
            resolved_at="2026-05-08T15:30:00Z",
        )

        event = MagisterDependencyResolvedEvent(
            source="seo-magister",
            target="content-magister",
            data=data,
        )

        assert event.target == "content-magister"
        assert event.source == "seo-magister"


class TestMagisterEventIntegration:
    """Test integration scenarios between magister events."""

    def test_request_response_flow(self):
        """Test complete request-response flow."""
        # Step 1: Content Magister requests data from SEO Magister
        request_data = MagisterDataRequestData(
            project_id="proj-123",
            requesting_magister="content-magister",
            target_magister="seo-magister",
            data_type="keyword_research",
            parameters={"topic": "medical marketing"},
            urgency="high",
        )
        request_event = MagisterDataRequestEvent(
            source="content-magister",
            target="seo-magister",
            data=request_data,
        )

        # Step 2: SEO Magister responds with data
        response_data = MagisterDataResponseData(
            project_id="proj-123",
            request_id=str(request_event.id),
            responding_magister="seo-magister",
            requesting_magister="content-magister",
            data={"keywords": ["medical marketing", "healthcare SEO"]},
            status="success",
        )
        response_event = MagisterDataResponseEvent(
            source="seo-magister",
            target="content-magister",
            data=response_data,
            reply_to=str(request_event.id),
        )

        # Verify flow
        assert response_event.reply_to == str(request_event.id)
        assert response_event.data.request_id == str(request_event.id)
        assert response_event.source == request_event.target
        assert response_event.target == request_event.source

    def test_dependency_blocked_resolved_flow(self):
        """Test complete dependency blocked-resolved flow."""
        # Step 1: Content Magister is blocked
        blocked_data = MagisterDependencyBlockedData(
            project_id="proj-123",
            task_id="task-456",
            blocked_magister="content-magister",
            blocking_magister="seo-magister",
            reason="Waiting for keyword research",
            estimated_unblock="2026-05-09T10:00:00Z",
        )
        blocked_event = MagisterDependencyBlockedEvent(
            source="content-magister",
            target="operator",
            data=blocked_data,
        )

        # Step 2: SEO Magister completes work and resolves dependency
        resolved_data = MagisterDependencyResolvedData(
            project_id="proj-123",
            task_id="task-456",
            blocked_magister="content-magister",
            blocking_magister="seo-magister",
            resolved_at="2026-05-08T15:30:00Z",
        )
        resolved_event = MagisterDependencyResolvedEvent(
            source="seo-magister",
            target="content-magister",
            data=resolved_data,
        )

        # Verify flow
        assert blocked_event.data.blocked_magister == resolved_event.data.blocked_magister
        assert blocked_event.data.blocking_magister == resolved_event.data.blocking_magister
        assert blocked_event.data.task_id == resolved_event.data.task_id
        assert resolved_event.target == blocked_event.data.blocked_magister
