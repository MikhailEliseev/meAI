"""Tests for error handling and recovery events.

This module tests all error handling events:
- ErrorOccurredEvent (P0 if critical, otherwise based on severity)
- ErrorRetryAttemptedEvent (P1)
- ErrorResolvedEvent (P2)
- ErrorEscalatedEvent (P0)
- RollbackInitiatedEvent (P0)
- RollbackCompletedEvent (P0)
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from meai.events.base import ErrorSeverity, ErrorType
from meai.events.error_events import (
    ErrorEscalatedData,
    ErrorEscalatedEvent,
    ErrorOccurredData,
    ErrorOccurredEvent,
    ErrorResolvedData,
    ErrorResolvedEvent,
    ErrorRetryAttemptedData,
    ErrorRetryAttemptedEvent,
    RollbackCompletedData,
    RollbackCompletedEvent,
    RollbackInitiatedData,
    RollbackInitiatedEvent,
)


class TestErrorOccurredEvent:
    """Test ErrorOccurredEvent with dynamic priority based on severity."""

    def test_error_occurred_critical_priority(self):
        """Test ErrorOccurredEvent with CRITICAL severity gets P0 priority."""
        data = ErrorOccurredData(
            project_id="proj_123",
            task_id="task_001",
            component="seo-magister",
            error_type=ErrorType.API_FAILURE,
            severity=ErrorSeverity.CRITICAL,
            error_message="Database connection lost",
            stack_trace="Traceback (most recent call last)...",
            context={"database": "postgresql", "host": "db.example.com"},
            retry_possible=True,
            retry_count=0,
            max_retries=3,
        )

        event = ErrorOccurredEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "error.occurred"
        assert event.priority == 0  # P0 for CRITICAL
        assert event.data.severity == ErrorSeverity.CRITICAL
        assert event.data.error_type == ErrorType.API_FAILURE
        assert event.data.component == "seo-magister"
        assert event.data.retry_possible is True
        assert event.data.retry_count == 0
        assert event.data.max_retries == 3

    def test_error_occurred_high_priority(self):
        """Test ErrorOccurredEvent with HIGH severity gets P1 priority."""
        data = ErrorOccurredData(
            component="content-magister",
            error_type=ErrorType.TIMEOUT,
            severity=ErrorSeverity.HIGH,
            error_message="API request timeout after 30s",
            retry_possible=True,
            retry_count=1,
            max_retries=3,
        )

        event = ErrorOccurredEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.priority == 1  # P1 for HIGH
        assert event.data.severity == ErrorSeverity.HIGH
        assert event.data.project_id is None
        assert event.data.task_id is None

    def test_error_occurred_medium_priority(self):
        """Test ErrorOccurredEvent with MEDIUM severity gets P2 priority."""
        data = ErrorOccurredData(
            component="ads-magister",
            error_type=ErrorType.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            error_message="Rate limit exceeded, retry after 60s",
            retry_possible=True,
            retry_count=0,
            max_retries=5,
        )

        event = ErrorOccurredEvent(
            source="ads-magister",
            target="operator",
            data=data,
        )

        assert event.priority == 2  # P2 for MEDIUM
        assert event.data.severity == ErrorSeverity.MEDIUM

    def test_error_occurred_low_priority(self):
        """Test ErrorOccurredEvent with LOW severity gets P3 priority."""
        data = ErrorOccurredData(
            component="analytics-magister",
            error_type=ErrorType.VALIDATION,
            severity=ErrorSeverity.LOW,
            error_message="Optional field validation warning",
            retry_possible=False,
            retry_count=0,
            max_retries=0,
        )

        event = ErrorOccurredEvent(
            source="analytics-magister",
            target="operator",
            data=data,
        )

        assert event.priority == 3  # P3 for LOW
        assert event.data.severity == ErrorSeverity.LOW
        assert event.data.retry_possible is False

    def test_error_occurred_with_context(self):
        """Test ErrorOccurredEvent with rich context."""
        data = ErrorOccurredData(
            project_id="proj_123",
            task_id="task_001",
            component="seo-magister",
            error_type=ErrorType.NETWORK,
            severity=ErrorSeverity.HIGH,
            error_message="Network connection failed",
            stack_trace="Full stack trace here...",
            context={
                "url": "https://api.example.com/data",
                "method": "GET",
                "status_code": None,
                "attempt": 2,
            },
            retry_possible=True,
            retry_count=2,
            max_retries=5,
        )

        event = ErrorOccurredEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.data.context["url"] == "https://api.example.com/data"
        assert event.data.context["attempt"] == 2
        assert event.data.stack_trace is not None


class TestErrorRetryAttemptedEvent:
    """Test ErrorRetryAttemptedEvent (P1 priority)."""

    def test_error_retry_attempted_structure(self):
        """Test ErrorRetryAttemptedEvent has correct structure."""
        data = ErrorRetryAttemptedData(
            original_error_id="error_001",
            component="seo-magister",
            retry_number=2,
            max_retries=5,
            attempted_at=datetime(2026, 5, 8, 14, 30, 0, tzinfo=UTC),
        )

        event = ErrorRetryAttemptedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "error.retry_attempted"
        assert event.priority == 1  # P1 - high priority
        assert event.data.original_error_id == "error_001"
        assert event.data.component == "seo-magister"
        assert event.data.retry_number == 2
        assert event.data.max_retries == 5
        assert event.data.attempted_at == datetime(2026, 5, 8, 14, 30, 0, tzinfo=UTC)

    def test_error_retry_attempted_first_retry(self):
        """Test ErrorRetryAttemptedEvent for first retry."""
        data = ErrorRetryAttemptedData(
            original_error_id="error_002",
            component="content-magister",
            retry_number=1,
            max_retries=3,
            attempted_at=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
        )

        event = ErrorRetryAttemptedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.data.retry_number == 1
        assert event.data.max_retries == 3


class TestErrorResolvedEvent:
    """Test ErrorResolvedEvent (P2 priority)."""

    def test_error_resolved_by_retry(self):
        """Test ErrorResolvedEvent resolved by retry."""
        data = ErrorResolvedData(
            original_error_id="error_001",
            component="seo-magister",
            resolved_at=datetime(2026, 5, 8, 14, 35, 0, tzinfo=UTC),
            resolution_method="retry",
            notes="Successfully resolved after 3rd retry",
        )

        event = ErrorResolvedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "error.resolved"
        assert event.priority == 2  # P2 - normal
        assert event.data.original_error_id == "error_001"
        assert event.data.resolution_method == "retry"
        assert event.data.notes == "Successfully resolved after 3rd retry"

    def test_error_resolved_by_manual(self):
        """Test ErrorResolvedEvent resolved manually."""
        data = ErrorResolvedData(
            original_error_id="error_002",
            component="content-magister",
            resolved_at=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
            resolution_method="manual",
            notes="User provided missing API key",
        )

        event = ErrorResolvedEvent(
            source="operator",
            target="content-magister",
            data=data,
        )

        assert event.data.resolution_method == "manual"
        assert "User provided" in event.data.notes

    def test_error_resolved_by_automatic(self):
        """Test ErrorResolvedEvent resolved automatically."""
        data = ErrorResolvedData(
            original_error_id="error_003",
            component="ads-magister",
            resolved_at=datetime(2026, 5, 8, 15, 30, 0, tzinfo=UTC),
            resolution_method="automatic",
        )

        event = ErrorResolvedEvent(
            source="ads-magister",
            target="operator",
            data=data,
        )

        assert event.data.resolution_method == "automatic"
        assert event.data.notes is None

    def test_error_resolved_by_workaround(self):
        """Test ErrorResolvedEvent resolved by workaround."""
        data = ErrorResolvedData(
            original_error_id="error_004",
            component="analytics-magister",
            resolved_at=datetime(2026, 5, 8, 16, 0, 0, tzinfo=UTC),
            resolution_method="workaround",
            notes="Used alternative API endpoint",
        )

        event = ErrorResolvedEvent(
            source="analytics-magister",
            target="operator",
            data=data,
        )

        assert event.data.resolution_method == "workaround"


class TestErrorEscalatedEvent:
    """Test ErrorEscalatedEvent (P0 priority)."""

    def test_error_escalated_to_operator(self):
        """Test ErrorEscalatedEvent escalated to operator."""
        data = ErrorEscalatedData(
            original_error_id="error_001",
            component="seo-magister",
            escalated_to="operator",
            escalated_at=datetime(2026, 5, 8, 14, 40, 0, tzinfo=UTC),
            reason="Max retries exceeded, manual intervention required",
            suggested_actions=[
                "Check API credentials",
                "Verify network connectivity",
                "Contact API provider support",
            ],
        )

        event = ErrorEscalatedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "error.escalated"
        assert event.priority == 0  # P0 - critical
        assert event.data.original_error_id == "error_001"
        assert event.data.escalated_to == "operator"
        assert "Max retries exceeded" in event.data.reason
        assert len(event.data.suggested_actions) == 3

    def test_error_escalated_to_user(self):
        """Test ErrorEscalatedEvent escalated to user."""
        data = ErrorEscalatedData(
            original_error_id="error_002",
            component="content-magister",
            escalated_to="user",
            escalated_at=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
            reason="Missing required configuration: API key not found",
            suggested_actions=[
                "Provide API key in configuration",
                "Check environment variables",
            ],
        )

        event = ErrorEscalatedEvent(
            source="operator",
            target="user",
            data=data,
        )

        assert event.data.escalated_to == "user"
        assert "Missing required configuration" in event.data.reason
        assert len(event.data.suggested_actions) == 2


class TestRollbackInitiatedEvent:
    """Test RollbackInitiatedEvent (P0 priority)."""

    def test_rollback_initiated_structure(self):
        """Test RollbackInitiatedEvent has correct structure."""
        data = RollbackInitiatedData(
            project_id="proj_123",
            rollback_id="rollback_001",
            reason="Critical error in deployment, rolling back to stable state",
            target_state="snapshot_2026-05-08_10-00",
            initiated_by="operator",
            initiated_at=datetime(2026, 5, 8, 14, 0, 0, tzinfo=UTC),
        )

        event = RollbackInitiatedEvent(
            source="operator",
            target=["seo-magister", "content-magister", "ads-magister"],
            data=data,
        )

        assert event.type == "rollback.initiated"
        assert event.priority == 0  # P0 - critical
        assert event.data.project_id == "proj_123"
        assert event.data.rollback_id == "rollback_001"
        assert "Critical error" in event.data.reason
        assert event.data.target_state == "snapshot_2026-05-08_10-00"
        assert event.data.initiated_by == "operator"

    def test_rollback_initiated_by_system(self):
        """Test RollbackInitiatedEvent initiated by system."""
        data = RollbackInitiatedData(
            project_id="proj_456",
            rollback_id="rollback_002",
            reason="Automatic rollback triggered by health check failure",
            target_state="snapshot_2026-05-08_12-00",
            initiated_by="system",
            initiated_at=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
        )

        event = RollbackInitiatedEvent(
            source="system",
            target="operator",
            data=data,
        )

        assert event.data.initiated_by == "system"
        assert "Automatic rollback" in event.data.reason


class TestRollbackCompletedEvent:
    """Test RollbackCompletedEvent (P0 priority)."""

    def test_rollback_completed_structure(self):
        """Test RollbackCompletedEvent has correct structure."""
        data = RollbackCompletedData(
            project_id="proj_123",
            rollback_id="rollback_001",
            completed_at=datetime(2026, 5, 8, 14, 10, 0, tzinfo=UTC),
            restored_state="snapshot_2026-05-08_10-00",
            affected_components=[
                "seo-magister",
                "content-magister",
                "ads-magister",
                "database",
            ],
        )

        event = RollbackCompletedEvent(
            source="operator",
            target=["seo-magister", "content-magister", "ads-magister"],
            data=data,
        )

        assert event.type == "rollback.completed"
        assert event.priority == 0  # P0 - critical
        assert event.data.project_id == "proj_123"
        assert event.data.rollback_id == "rollback_001"
        assert event.data.restored_state == "snapshot_2026-05-08_10-00"
        assert len(event.data.affected_components) == 4
        assert "database" in event.data.affected_components

    def test_rollback_completed_single_component(self):
        """Test RollbackCompletedEvent with single component."""
        data = RollbackCompletedData(
            project_id="proj_456",
            rollback_id="rollback_002",
            completed_at=datetime(2026, 5, 8, 15, 5, 0, tzinfo=UTC),
            restored_state="snapshot_2026-05-08_12-00",
            affected_components=["seo-magister"],
        )

        event = RollbackCompletedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert len(event.data.affected_components) == 1
        assert event.data.affected_components[0] == "seo-magister"


class TestEventSerialization:
    """Test event serialization and deserialization."""

    def test_error_occurred_serialization(self):
        """Test ErrorOccurredEvent can be serialized and deserialized."""
        data = ErrorOccurredData(
            project_id="proj_123",
            component="seo-magister",
            error_type=ErrorType.API_FAILURE,
            severity=ErrorSeverity.CRITICAL,
            error_message="Database connection lost",
            retry_possible=True,
            retry_count=0,
            max_retries=3,
        )

        event = ErrorOccurredEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        # Serialize to dict
        event_dict = event.model_dump()
        assert event_dict["type"] == "error.occurred"
        assert event_dict["data"]["error_type"] == "API_FAILURE"
        assert event_dict["data"]["severity"] == "CRITICAL"

        # Deserialize from dict
        event_restored = ErrorOccurredEvent.model_validate(event_dict)
        assert event_restored.type == "error.occurred"
        assert event_restored.data.error_type == ErrorType.API_FAILURE
        assert event_restored.data.severity == ErrorSeverity.CRITICAL

    def test_rollback_initiated_serialization(self):
        """Test RollbackInitiatedEvent can be serialized and deserialized."""
        data = RollbackInitiatedData(
            project_id="proj_123",
            rollback_id="rollback_001",
            reason="Critical error",
            target_state="snapshot_001",
            initiated_by="operator",
            initiated_at=datetime(2026, 5, 8, 14, 0, 0, tzinfo=UTC),
        )

        event = RollbackInitiatedEvent(
            source="operator",
            target="system",
            data=data,
        )

        # Serialize to dict
        event_dict = event.model_dump()
        assert event_dict["type"] == "rollback.initiated"
        assert event_dict["data"]["rollback_id"] == "rollback_001"

        # Deserialize from dict
        event_restored = RollbackInitiatedEvent.model_validate(event_dict)
        assert event_restored.type == "rollback.initiated"
        assert event_restored.data.rollback_id == "rollback_001"
        assert event_restored.data.initiated_by == "operator"


class TestErrorTypeEnum:
    """Test ErrorType enum usage in events."""

    def test_all_error_types(self):
        """Test all ErrorType enum values work in ErrorOccurredEvent."""
        error_types = [
            ErrorType.VALIDATION,
            ErrorType.TIMEOUT,
            ErrorType.API_FAILURE,
            ErrorType.DATA_MISSING,
            ErrorType.PERMISSION_DENIED,
            ErrorType.RATE_LIMIT,
            ErrorType.NETWORK,
            ErrorType.UNKNOWN,
        ]

        for error_type in error_types:
            data = ErrorOccurredData(
                component="test-component",
                error_type=error_type,
                severity=ErrorSeverity.MEDIUM,
                error_message=f"Test error: {error_type.value}",
                retry_possible=True,
                retry_count=0,
                max_retries=3,
            )

            event = ErrorOccurredEvent(
                source="test-component",
                target="operator",
                data=data,
            )

            assert event.data.error_type == error_type


class TestErrorSeverityEnum:
    """Test ErrorSeverity enum usage in events."""

    def test_all_severity_levels(self):
        """Test all ErrorSeverity enum values work in ErrorOccurredEvent."""
        severity_to_priority = {
            ErrorSeverity.CRITICAL: 0,
            ErrorSeverity.HIGH: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.LOW: 3,
        }

        for severity, expected_priority in severity_to_priority.items():
            data = ErrorOccurredData(
                component="test-component",
                error_type=ErrorType.UNKNOWN,
                severity=severity,
                error_message=f"Test error with {severity.value} severity",
                retry_possible=False,
                retry_count=0,
                max_retries=0,
            )

            event = ErrorOccurredEvent(
                source="test-component",
                target="operator",
                data=data,
            )

            assert event.data.severity == severity
            assert event.priority == expected_priority
