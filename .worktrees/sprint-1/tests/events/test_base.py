"""Tests for BaseEvent model and core enums."""

import pytest
from datetime import datetime
from uuid import UUID

from meai.events.base import (
    BaseEvent,
    ProjectStatus,
    ErrorType,
    ErrorSeverity,
)


class TestBaseEvent:
    """Test BaseEvent model."""

    def test_base_event_creation_with_required_fields(self):
        """Test creating BaseEvent with only required fields."""
        event = BaseEvent(
            type="test.event",
            source="test_source",
            target="test_target",
        )

        assert event.type == "test.event"
        assert event.source == "test_source"
        assert event.target == "test_target"
        assert event.priority == 2  # default priority
        assert isinstance(event.id, UUID)
        assert isinstance(event.timestamp, datetime)
        assert event.correlation_id is None
        assert event.reply_to is None
        assert event.metadata == {}

    def test_base_event_with_correlation_id_and_reply_to(self):
        """Test BaseEvent with correlation_id and reply_to."""
        correlation_id = "corr-123"
        reply_to = "original-event-id"

        event = BaseEvent(
            type="test.event",
            source="test_source",
            target="test_target",
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        assert event.correlation_id == correlation_id
        assert event.reply_to == reply_to

    def test_base_event_priority_levels(self):
        """Test all priority levels (0-3)."""
        for priority in [0, 1, 2, 3]:
            event = BaseEvent(
                type="test.event",
                source="test_source",
                target="test_target",
                priority=priority,
            )
            assert event.priority == priority

    def test_base_event_with_single_target(self):
        """Test BaseEvent with single target as string."""
        event = BaseEvent(
            type="test.event",
            source="test_source",
            target="single_target",
        )

        assert event.target == "single_target"

    def test_base_event_with_multiple_targets(self):
        """Test BaseEvent with multiple targets as list."""
        targets = ["target1", "target2", "target3"]

        event = BaseEvent(
            type="test.event",
            source="test_source",
            target=targets,
        )

        assert event.target == targets
        assert len(event.target) == 3

    def test_base_event_with_metadata(self):
        """Test BaseEvent with custom metadata."""
        metadata = {
            "key1": "value1",
            "key2": 42,
            "key3": {"nested": "data"},
        }

        event = BaseEvent(
            type="test.event",
            source="test_source",
            target="test_target",
            metadata=metadata,
        )

        assert event.metadata == metadata


class TestProjectStatus:
    """Test ProjectStatus enum."""

    def test_project_status_values(self):
        """Test all ProjectStatus enum values exist."""
        expected_statuses = [
            "LEAD",
            "PRE_SALE",
            "PROPOSAL_SENT",
            "PROPOSAL_FOLLOW_UP",
            "CONTRACT_SIGNED",
            "SETUP",
            "BASELINE",
            "STRATEGY_PLANNING",
            "ACTIVE",
            "PAUSED",
            "CLOSED_WON",
            "CLOSED_LOST",
        ]

        for status in expected_statuses:
            assert hasattr(ProjectStatus, status)
            assert isinstance(getattr(ProjectStatus, status), ProjectStatus)

    def test_project_status_enum_members(self):
        """Test ProjectStatus enum has correct number of members."""
        assert len(ProjectStatus) == 12


class TestErrorType:
    """Test ErrorType enum."""

    def test_error_type_values(self):
        """Test all ErrorType enum values exist."""
        expected_types = [
            "VALIDATION",
            "TIMEOUT",
            "API_FAILURE",
            "DATA_MISSING",
            "PERMISSION_DENIED",
            "RATE_LIMIT",
            "NETWORK",
            "UNKNOWN",
        ]

        for error_type in expected_types:
            assert hasattr(ErrorType, error_type)
            assert isinstance(getattr(ErrorType, error_type), ErrorType)

    def test_error_type_enum_members(self):
        """Test ErrorType enum has correct number of members."""
        assert len(ErrorType) == 8


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test all ErrorSeverity enum values exist."""
        expected_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for severity in expected_severities:
            assert hasattr(ErrorSeverity, severity)
            assert isinstance(getattr(ErrorSeverity, severity), ErrorSeverity)

    def test_error_severity_enum_members(self):
        """Test ErrorSeverity enum has correct number of members."""
        assert len(ErrorSeverity) == 4
