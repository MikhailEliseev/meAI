"""Tests for error handling and recovery events.

This module tests all error handling events:
- ErrorOccurredEvent (P0 - FIXED)
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
    """Test ErrorOccurredEvent with fixed P0 priority."""

    def test_error_occurred_structure(self):
        """Test ErrorOccurredEvent has correct structure."""
        data = ErrorOccurredData(
            error_type=ErrorType.API_FAILURE,
            error_severity=ErrorSeverity.CRITICAL,
            error_message="Database connection lost",
            stack_trace="Traceback (most recent call last)...",
            context={"database": "postgresql", "host": "db.example.com"},
        )

        event = ErrorOccurredEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "error.occurred"
        assert event.priority == 0  # P0 - FIXED
        assert event.data.error_severity == ErrorSeverity.CRITICAL
        assert event.data.error_type == ErrorType.API_FAILURE
        assert event.data.error_message == "Database connection lost"
        assert event.data.stack_trace is not None
        assert event.data.context["database"] == "postgresql"

    def test_error_occurred_minimal(self):
        """Test ErrorOccurredEvent with minimal data."""
        data = ErrorOccurredData(
            error_type=ErrorType.TIMEOUT,
            error_severity=ErrorSeverity.HIGH,
            error_message="API request timeout after 30s",
        )

        event = ErrorOccurredEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.priority == 0  # P0 - FIXED
        assert event.data.error_severity == ErrorSeverity.HIGH
        assert event.data.stack_trace is None
        assert event.data.context == {}

    def test_error_occurred_with_context(self):
        """Test ErrorOccurredEvent with rich context."""
        data = ErrorOccurredData(
            error_type=ErrorType.NETWORK,
            error_severity=ErrorSeverity.MEDIUM,
            error_message="Network connection failed",
            stack_trace="Full stack trace here...",
            context={
                "url": "https://api.example.com/data",
                "method": "GET",
                "status_code": None,
                "attempt": 2,
            },
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
            retry_attempt=2,
            max_retries=5,
            retry_strategy="exponential_backoff",
            next_retry_at=datetime(2026, 5, 8, 14, 30, 0, tzinfo=UTC),
        )

        event = ErrorRetryAttemptedEvent(
            source="seo-magister",
            target="operator",
            data=data,
        )

        assert event.type == "error.retry_attempted"
        assert event.priority == 1  # P1 - high priority
        assert event.data.original_error_id == "error_001"
        assert event.data.retry_attempt == 2
        assert event.data.max_retries == 5
        assert event.data.retry_strategy == "exponential_backoff"
        assert event.data.next_retry_at == datetime(2026, 5, 8, 14, 30, 0, tzinfo=UTC)

    def test_error_retry_attempted_first_retry(self):
        """Test ErrorRetryAttemptedEvent for first retry."""
        data = ErrorRetryAttemptedData(
            original_error_id="error_002",
            retry_attempt=1,
            max_retries=3,
            retry_strategy="linear",
        )

        event = ErrorRetryAttemptedEvent(
            source="content-magister",
            target="operator",
            data=data,
        )

        assert event.data.retry_attempt == 1
        assert event.data.max_retries == 3
        assert event.data.next_retry_at is None


class TestErrorResolvedEvent:
    """Test ErrorResolvedEvent (P2 priority)."""

    def test_error_resolved_by_retry(self):
        """Test ErrorResolvedEvent resolved by retry."""
        data = ErrorResolvedData(
            original_error_id="error_001",
            resolution_method="retry",
            resolution_time=datetime(2026, 5, 8, 14, 35, 0, tzinfo=UTC),
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
            resolution_method="manual",
            resolution_time=datetime(2026, 5, 8, 15, 0, 0, tzinfo=UTC),
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
            resolution_method="automatic",
            resolution_time=datetime(2026, 5, 8, 15, 30, 0, tzinfo=UTC),
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
            resolution_method="workaround",
            resolution_time=datetime(2026, 5, 8, 16, 0, 0, tzinfo=UTC),
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
            escalation_reason="Max retries exceeded, manual intervention required",
            escalated_to="operator",
            escalation_level=1,
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
        assert "Max retries exceeded" in event.data.escalation_reason
        assert event.data.escalation_level == 1

    def test_error_escalated_to_user(self):
        """Test ErrorEscalatedEvent escalated to user."""
        data = ErrorEscalatedData(
            original_error_id="error_002",
            escalation_reason="Missing required configuration: API key not found",
            escalated_to="user",
            escalation_level=2,
        )

        event = ErrorEscalatedEvent(
            source="operator",
            target="user",
            data=data,
        )

        assert event.data.escalated_to == "user"
        assert "Missing required configuration" in event.data.escalation_reason
        assert event.data.escalation_level == 2


class TestRollbackInitiatedEvent:
    """Test RollbackInitiatedEvent (P0 priority)."""

    def test_rollback_initiated_structure(self):
        """Test RollbackInitiatedEvent has correct structure."""
        data = RollbackInitiatedData(
            reason="Critical error in deployment, rolling back to stable state",
            target_snapshot_id="snapshot_2026-05-08_10-00",
            affected_components=["seo-magister", "content-magister", "ads-magister"],
        )

        event = RollbackInitiatedEvent(
            source="operator",
            target=["seo-magister", "content-magister", "ads-magister"],
            data=data,
        )

        assert event.type == "rollback.initiated"
        assert event.priority == 0  # P0 - critical
        assert "Critical error" in event.data.reason
        assert event.data.target_snapshot_id == "snapshot_2026-05-08_10-00"
        assert len(event.data.affected_components) == 3

    def test_rollback_initiated_single_component(self):
        """Test RollbackInitiatedEvent with single component."""
        data = RollbackInitiatedData(
            reason="Automatic rollback triggered by health check failure",
            target_snapshot_id="snapshot_2026-05-08_12-00",
            affected_components=["seo-magister"],
        )

        event = RollbackInitiatedEvent(
            source="system",
            target="operator",
            data=data,
        )

        assert "Automatic rollback" in event.data.reason
        assert len(event.data.affected_components) == 1


class TestRollbackCompletedEvent:
    """Test RollbackCompletedEvent (P0 priority)."""

    def test_rollback_completed_structure(self):
        """Test RollbackCompletedEvent has correct structure."""
        data = RollbackCompletedData(
            rollback_id="rollback_001",
            success=True,
            restored_snapshot_id="snapshot_2026-05-08_10-00",
            rollback_duration=120.5,
            notes="Rollback completed successfully",
        )

        event = RollbackCompletedEvent(
            source="operator",
            target=["seo-magister", "content-magister", "ads-magister"],
            data=data,
        )

        assert event.type == "rollback.completed"
        assert event.priority == 0  # P0 - critical
        assert event.data.rollback_id == "rollback_001"
        assert event.data.success is True
        assert event.data.restored_snapshot_id == "snapshot_2026-05-08_10-00"
        assert event.data.rollback_duration == 120.5
        assert event.data.notes == "Rollback completed successfully"

    def test_rollback_completed_failed(self):
        """Test RollbackCompletedEvent with failure."""
        data = RollbackCompletedData(
            rollback_id="rollback_002",
            success=False,
            restored_snapshot_id="snapshot_2026-05-08_12-00",
            rollback_duration=45.2,
            notes="Rollback failed: database restore error",
        )

        event = RollbackCompletedEvent(
            source="operator",
            target="seo-magister",
            data=data,
        )

        assert event.data.success is False
        assert "failed" in event.data.notes


class TestEventSerialization:
    """Test event serialization and deserialization."""

    def test_error_occurred_serialization(self):
        """Test ErrorOccurredEvent can be serialized and deserialized."""
        data = ErrorOccurredData(
            error_type=ErrorType.API_FAILURE,
            error_severity=ErrorSeverity.CRITICAL,
            error_message="Database connection lost",
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
        assert event_dict["data"]["error_severity"] == "CRITICAL"

        # Deserialize from dict
        event_restored = ErrorOccurredEvent.model_validate(event_dict)
        assert event_restored.type == "error.occurred"
        assert event_restored.data.error_type == ErrorType.API_FAILURE
        assert event_restored.data.error_severity == ErrorSeverity.CRITICAL

    def test_rollback_initiated_serialization(self):
        """Test RollbackInitiatedEvent can be serialized and deserialized."""
        data = RollbackInitiatedData(
            reason="Critical error",
            target_snapshot_id="snapshot_001",
            affected_components=["seo-magister"],
        )

        event = RollbackInitiatedEvent(
            source="operator",
            target="system",
            data=data,
        )

        # Serialize to dict
        event_dict = event.model_dump()
        assert event_dict["type"] == "rollback.initiated"
        assert event_dict["data"]["target_snapshot_id"] == "snapshot_001"

        # Deserialize from dict
        event_restored = RollbackInitiatedEvent.model_validate(event_dict)
        assert event_restored.type == "rollback.initiated"
        assert event_restored.data.target_snapshot_id == "snapshot_001"


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
                error_type=error_type,
                error_severity=ErrorSeverity.MEDIUM,
                error_message=f"Test error: {error_type.value}",
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
        severities = [
            ErrorSeverity.CRITICAL,
            ErrorSeverity.HIGH,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.LOW,
        ]

        for severity in severities:
            data = ErrorOccurredData(
                error_type=ErrorType.UNKNOWN,
                error_severity=severity,
                error_message=f"Test error with {severity.value} severity",
            )

            event = ErrorOccurredEvent(
                source="test-component",
                target="operator",
                data=data,
            )

            assert event.data.error_severity == severity
            assert event.priority == 0  # P0 - FIXED
