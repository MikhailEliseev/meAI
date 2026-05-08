"""Tests for task execution events.

This module tests all task execution events for Pre-Sale and Active Work phases:
- TaskCreatedEvent (Pre-Sale & General)
- TaskAssignedEvent (Active Work)
- TaskStartedEvent
- TaskProgressEvent
- TaskCompletedEvent with Deliverable model
- TaskFailedEvent (P1 priority)
- TaskBlockedEvent
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from meai.events.task_events import (
    Deliverable,
    TaskAssignedData,
    TaskAssignedEvent,
    TaskBlockedData,
    TaskBlockedEvent,
    TaskCompletedData,
    TaskCompletedEvent,
    TaskCreatedData,
    TaskCreatedEvent,
    TaskFailedData,
    TaskFailedEvent,
    TaskProgressData,
    TaskProgressEvent,
    TaskStartedData,
    TaskStartedEvent,
)


class TestDeliverable:
    """Test Deliverable model."""

    def test_deliverable_with_file(self):
        """Test deliverable with file path."""
        deliverable = Deliverable(
            type="report",
            title="SEO Analysis Report",
            description="Comprehensive SEO analysis for example.com",
            file_path="/path/to/report.pdf",
            requires_approval=True,
        )

        assert deliverable.type == "report"
        assert deliverable.title == "SEO Analysis Report"
        assert deliverable.description == "Comprehensive SEO analysis for example.com"
        assert deliverable.file_path == "/path/to/report.pdf"
        assert deliverable.url is None
        assert deliverable.requires_approval is True

    def test_deliverable_with_url(self):
        """Test deliverable with URL."""
        deliverable = Deliverable(
            type="dashboard",
            title="Analytics Dashboard",
            description="Real-time analytics dashboard",
            url="https://analytics.example.com/dashboard",
            requires_approval=False,
        )

        assert deliverable.type == "dashboard"
        assert deliverable.url == "https://analytics.example.com/dashboard"
        assert deliverable.file_path is None
        assert deliverable.requires_approval is False

    def test_deliverable_minimal(self):
        """Test deliverable with minimal fields."""
        deliverable = Deliverable(
            type="data",
            title="Keyword Research Data",
            description="Keyword research results",
        )

        assert deliverable.type == "data"
        assert deliverable.title == "Keyword Research Data"
        assert deliverable.file_path is None
        assert deliverable.url is None
        assert deliverable.requires_approval is False


class TestTaskCreatedEvent:
    """Test TaskCreatedEvent (Pre-Sale & General)."""

    def test_task_created_event_structure(self):
        """Test TaskCreatedEvent has correct structure."""
        data = TaskCreatedData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            capability="keyword_research",
            parameters={"domain": "example.com", "competitors": ["competitor1.com"]},
            deadline=datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC),
            dependencies=["task_000"],
        )

        event = TaskCreatedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.type == "task.created"
        assert event.source == "operator"
        assert event.target == "seo-magister"
        assert event.priority == 2  # P2 - normal
        assert isinstance(event.id, UUID)
        assert isinstance(event.timestamp, datetime)

        # Check data
        assert event.data.project_id == "proj_123"
        assert event.data.task_id == "task_001"
        assert event.data.magister == "seo-magister"
        assert event.data.capability == "keyword_research"
        assert event.data.parameters["domain"] == "example.com"
        assert event.data.deadline == datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC)
        assert event.data.dependencies == ["task_000"]

    def test_task_created_event_optional_fields(self):
        """Test TaskCreatedEvent with optional fields."""
        data = TaskCreatedData(
            project_id="proj_123",
            task_id="task_001",
            magister="content-magister",
            capability="generate_article",
            parameters={"topic": "AI in Healthcare"},
        )

        event = TaskCreatedEvent(
            source="operator",
            target="content-magister",
            data=data,
        )

        assert event.data.deadline is None
        assert event.data.dependencies == []


class TestTaskAssignedEvent:
    """Test TaskAssignedEvent (Active Work)."""

    def test_task_assigned_event_structure(self):
        """Test TaskAssignedEvent has correct structure."""
        data = TaskAssignedData(
            project_id="proj_123",
            sprint_id="sprint_001",
            task_id="task_001",
            magister="seo-magister",
            capability="competitor_analysis",
            parameters={"competitors": ["competitor1.com", "competitor2.com"]},
            deadline=datetime(2026, 5, 20, 18, 0, 0, tzinfo=UTC),
            dependencies=["task_000"],
        )

        event = TaskAssignedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.type == "task.assigned"
        assert event.source == "operator"
        assert event.target == "seo-magister"
        assert event.priority == 2  # P2 - normal
        assert isinstance(event.id, UUID)

        # Check data
        assert event.data.project_id == "proj_123"
        assert event.data.sprint_id == "sprint_001"
        assert event.data.task_id == "task_001"
        assert event.data.magister == "seo-magister"
        assert event.data.capability == "competitor_analysis"
        assert event.data.deadline == datetime(2026, 5, 20, 18, 0, 0, tzinfo=UTC)


class TestTaskStartedEvent:
    """Test TaskStartedEvent."""

    def test_task_started_event_structure(self):
        """Test TaskStartedEvent has correct structure."""
        data = TaskStartedData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            started_at=datetime(2026, 5, 8, 10, 0, 0, tzinfo=UTC),
        )

        event = TaskStartedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "task.started"
        assert event.source == "seo-magister"
        assert event.target == "operator"
        assert event.priority == 2  # P2 - normal
        assert event.data.project_id == "proj_123"
        assert event.data.task_id == "task_001"
        assert event.data.magister == "seo-magister"
        assert event.data.started_at == datetime(2026, 5, 8, 10, 0, 0, tzinfo=UTC)


class TestTaskProgressEvent:
    """Test TaskProgressEvent."""

    def test_task_progress_event_structure(self):
        """Test TaskProgressEvent has correct structure."""
        data = TaskProgressData(
            project_id="proj_123",
            task_id="task_001",
            magister="content-magister",
            progress_percent=45,
            current_step="Generating article outline",
        )

        event = TaskProgressEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.type == "task.progress"
        assert event.source == "content-magister"
        assert event.target == "operator"
        assert event.priority == 2  # P2 - normal
        assert event.data.progress_percent == 45
        assert event.data.current_step == "Generating article outline"

    def test_task_progress_validation(self):
        """Test progress_percent validation (0-100)."""
        # Valid progress
        data = TaskProgressData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            progress_percent=0,
            current_step="Starting",
        )
        assert data.progress_percent == 0

        data = TaskProgressData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            progress_percent=100,
            current_step="Completed",
        )
        assert data.progress_percent == 100

        # Invalid progress - should raise validation error
        with pytest.raises(ValueError):
            TaskProgressData(
                project_id="proj_123",
                task_id="task_001",
                magister="seo-magister",
                progress_percent=101,
                current_step="Invalid",
            )

        with pytest.raises(ValueError):
            TaskProgressData(
                project_id="proj_123",
                task_id="task_001",
                magister="seo-magister",
                progress_percent=-1,
                current_step="Invalid",
            )


class TestTaskCompletedEvent:
    """Test TaskCompletedEvent."""

    def test_task_completed_event_structure(self):
        """Test TaskCompletedEvent has correct structure."""
        deliverables = [
            Deliverable(
                type="report",
                title="SEO Analysis Report",
                description="Comprehensive SEO analysis",
                file_path="/reports/seo_analysis.pdf",
                requires_approval=True,
            ),
            Deliverable(
                type="data",
                title="Keyword Research Data",
                description="Keyword research results in JSON",
                file_path="/data/keywords.json",
                requires_approval=False,
            ),
        ]

        data = TaskCompletedData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            completed_at=datetime(2026, 5, 8, 15, 30, 0, tzinfo=UTC),
            deliverables=deliverables,
            summary="Successfully completed keyword research and competitor analysis",
        )

        event = TaskCompletedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "task.completed"
        assert event.source == "seo-magister"
        assert event.target == "operator"
        assert event.priority == 2  # P2 - normal
        assert event.data.project_id == "proj_123"
        assert event.data.task_id == "task_001"
        assert event.data.completed_at == datetime(2026, 5, 8, 15, 30, 0, tzinfo=UTC)
        assert len(event.data.deliverables) == 2
        assert event.data.deliverables[0].requires_approval is True
        assert event.data.deliverables[1].requires_approval is False
        assert "Successfully completed" in event.data.summary

    def test_task_completed_event_no_deliverables(self):
        """Test TaskCompletedEvent with no deliverables."""
        data = TaskCompletedData(
            project_id="proj_123",
            task_id="task_001",
            magister="ads-magister",
            completed_at=datetime(2026, 5, 8, 16, 0, 0, tzinfo=UTC),
            deliverables=[],
            summary="Task completed without deliverables",
        )

        event = TaskCompletedEvent(
            source="ads-magister",
            target="operator",
            data=data,
        )

        assert len(event.data.deliverables) == 0


class TestTaskFailedEvent:
    """Test TaskFailedEvent (P1 priority)."""

    def test_task_failed_event_structure(self):
        """Test TaskFailedEvent has correct structure."""
        data = TaskFailedData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            failed_at=datetime(2026, 5, 8, 14, 0, 0, tzinfo=UTC),
            error_type="API_FAILURE",
            error_message="Failed to fetch competitor data: API rate limit exceeded",
            retry_count=3,
            is_retryable=True,
        )

        event = TaskFailedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "task.failed"
        assert event.source == "seo-magister"
        assert event.target == "operator"
        assert event.priority == 1  # P1 - high priority, needs attention
        assert event.data.project_id == "proj_123"
        assert event.data.task_id == "task_001"
        assert event.data.error_type == "API_FAILURE"
        assert "rate limit" in event.data.error_message
        assert event.data.retry_count == 3
        assert event.data.is_retryable is True

    def test_task_failed_event_non_retryable(self):
        """Test TaskFailedEvent with non-retryable error."""
        data = TaskFailedData(
            project_id="proj_123",
            task_id="task_002",
            magister="content-magister",
            failed_at=datetime(2026, 5, 8, 14, 30, 0, tzinfo=UTC),
            error_type="VALIDATION",
            error_message="Invalid parameters: missing required field 'topic'",
            retry_count=0,
            is_retryable=False,
        )

        event = TaskFailedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.data.error_type == "VALIDATION"
        assert event.data.is_retryable is False
        assert event.priority == 1  # Still P1 - needs attention


class TestTaskBlockedEvent:
    """Test TaskBlockedEvent."""

    def test_task_blocked_event_structure(self):
        """Test TaskBlockedEvent has correct structure."""
        data = TaskBlockedData(
            project_id="proj_123",
            task_id="task_002",
            magister="content-magister",
            blocked_at=datetime(2026, 5, 8, 11, 0, 0, tzinfo=UTC),
            blocked_by=["task_001"],
            reason="Waiting for keyword research data from task_001",
        )

        event = TaskBlockedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.type == "task.blocked"
        assert event.source == "content-magister"
        assert event.target == "operator"
        assert event.priority == 2  # P2 - normal
        assert event.data.project_id == "proj_123"
        assert event.data.task_id == "task_002"
        assert event.data.blocked_by == ["task_001"]
        assert "Waiting for" in event.data.reason

    def test_task_blocked_event_multiple_blockers(self):
        """Test TaskBlockedEvent with multiple blocking tasks."""
        data = TaskBlockedData(
            project_id="proj_123",
            task_id="task_005",
            magister="ads-magister",
            blocked_at=datetime(2026, 5, 8, 12, 0, 0, tzinfo=UTC),
            blocked_by=["task_001", "task_003", "task_004"],
            reason="Waiting for SEO data, content strategy, and budget approval",
        )

        event = TaskBlockedEvent(
            source="ads-magister",
            target="operator",
            data=data,
        )

        assert len(event.data.blocked_by) == 3
        assert "task_001" in event.data.blocked_by
        assert "task_003" in event.data.blocked_by
        assert "task_004" in event.data.blocked_by


class TestEventSerialization:
    """Test event serialization and deserialization."""

    def test_task_created_event_serialization(self):
        """Test TaskCreatedEvent can be serialized and deserialized."""
        data = TaskCreatedData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            capability="keyword_research",
            parameters={"domain": "example.com"},
        )

        event = TaskCreatedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        # Serialize to dict
        event_dict = event.model_dump()
        assert event_dict["type"] == "task.created"
        assert event_dict["data"]["project_id"] == "proj_123"

        # Deserialize from dict
        event_restored = TaskCreatedEvent.model_validate(event_dict)
        assert event_restored.type == "task.created"
        assert event_restored.data.project_id == "proj_123"
        assert event_restored.data.task_id == "task_001"

    def test_task_completed_event_serialization(self):
        """Test TaskCompletedEvent with deliverables can be serialized."""
        deliverables = [
            Deliverable(
                type="report",
                title="Analysis Report",
                description="Detailed analysis",
                file_path="/reports/analysis.pdf",
                requires_approval=True,
            )
        ]

        data = TaskCompletedData(
            project_id="proj_123",
            task_id="task_001",
            magister="seo-magister",
            completed_at=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
            deliverables=deliverables,
            summary="Task completed successfully",
        )

        event = TaskCompletedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        # Serialize to dict
        event_dict = event.model_dump()
        assert len(event_dict["data"]["deliverables"]) == 1
        assert event_dict["data"]["deliverables"][0]["type"] == "report"

        # Deserialize from dict
        event_restored = TaskCompletedEvent.model_validate(event_dict)
        assert len(event_restored.data.deliverables) == 1
        assert event_restored.data.deliverables[0].requires_approval is True
