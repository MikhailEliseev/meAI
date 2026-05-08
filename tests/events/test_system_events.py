"""Tests for system monitoring and data events."""

from datetime import datetime, timedelta

import pytest

from meai.events.system_events import (
    AgentUnresponsiveEvent,
    DataVersionArchivedEvent,
    DataVersionComparedEvent,
    DataVersionCreatedEvent,
    ReminderEvent,
    SystemHealthCheckEvent,
    SystemPerformanceDegradedEvent,
    SystemResourceLowEvent,
)


class TestSystemHealthCheckEvent:
    """Tests for SystemHealthCheckEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        now = datetime.now()
        event = SystemHealthCheckEvent(
            source="system-monitor",
            target="operator",
            component="event-bus",
            status="healthy",
            metrics={"latency_ms": 50, "queue_size": 10},
            checked_at=now,
        )

        assert event.type == "system.health_check"
        assert event.priority == 3
        assert event.component == "event-bus"
        assert event.status == "healthy"
        assert event.metrics == {"latency_ms": 50, "queue_size": 10}
        assert event.checked_at == now

    def test_degraded_status(self):
        """Test event with degraded status."""
        event = SystemHealthCheckEvent(
            source="system-monitor",
            target="operator",
            component="database",
            status="degraded",
            metrics={"connection_pool": 80},
            checked_at=datetime.now(),
        )

        assert event.status == "degraded"

    def test_unhealthy_status(self):
        """Test event with unhealthy status."""
        event = SystemHealthCheckEvent(
            source="system-monitor",
            target="operator",
            component="api",
            status="unhealthy",
            metrics={"error_rate": 0.5},
            checked_at=datetime.now(),
        )

        assert event.status == "unhealthy"


class TestSystemPerformanceDegradedEvent:
    """Tests for SystemPerformanceDegradedEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        event = SystemPerformanceDegradedEvent(
            source="system-monitor",
            target="operator",
            component="event-bus",
            metric_name="latency_ms",
            current_value=500.0,
            threshold_value=200.0,
            severity="warning",
        )

        assert event.type == "system.performance_degraded"
        assert event.priority == 1
        assert event.component == "event-bus"
        assert event.metric_name == "latency_ms"
        assert event.current_value == 500.0
        assert event.threshold_value == 200.0
        assert event.severity == "warning"

    def test_critical_severity(self):
        """Test event with critical severity."""
        event = SystemPerformanceDegradedEvent(
            source="system-monitor",
            target="operator",
            component="database",
            metric_name="query_time",
            current_value=5000.0,
            threshold_value=1000.0,
            severity="critical",
        )

        assert event.severity == "critical"


class TestSystemResourceLowEvent:
    """Tests for SystemResourceLowEvent."""

    def test_memory_resource(self):
        """Test event for low memory."""
        event = SystemResourceLowEvent(
            source="system-monitor",
            target="operator",
            resource_type="memory",
            current_usage=0.95,
            threshold=0.90,
            component="event-bus",
        )

        assert event.type == "system.resource_low"
        assert event.priority == 1
        assert event.resource_type == "memory"
        assert event.current_usage == 0.95
        assert event.threshold == 0.90
        assert event.component == "event-bus"

    def test_disk_resource(self):
        """Test event for low disk space."""
        event = SystemResourceLowEvent(
            source="system-monitor",
            target="operator",
            resource_type="disk",
            current_usage=0.88,
            threshold=0.85,
            component="database",
        )

        assert event.resource_type == "disk"

    def test_cpu_resource(self):
        """Test event for high CPU usage."""
        event = SystemResourceLowEvent(
            source="system-monitor",
            target="operator",
            resource_type="cpu",
            current_usage=0.92,
            threshold=0.80,
            component="orchestrator",
        )

        assert event.resource_type == "cpu"

    def test_connections_resource(self):
        """Test event for low connections."""
        event = SystemResourceLowEvent(
            source="system-monitor",
            target="operator",
            resource_type="connections",
            current_usage=0.95,
            threshold=0.90,
            component="database",
        )

        assert event.resource_type == "connections"


class TestAgentUnresponsiveEvent:
    """Tests for AgentUnresponsiveEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        last_seen = datetime.now() - timedelta(minutes=5)
        event = AgentUnresponsiveEvent(
            source="system-monitor",
            target="operator",
            agent_id="seo-agent-001",
            agent_type="seo",
            last_seen=last_seen,
            timeout_seconds=300,
        )

        assert event.type == "system.agent_unresponsive"
        assert event.priority == 0
        assert event.agent_id == "seo-agent-001"
        assert event.agent_type == "seo"
        assert event.last_seen == last_seen
        assert event.timeout_seconds == 300

    def test_different_agent_types(self):
        """Test event for different agent types."""
        event = AgentUnresponsiveEvent(
            source="system-monitor",
            target="operator",
            agent_id="content-agent-002",
            agent_type="content",
            last_seen=datetime.now() - timedelta(minutes=10),
            timeout_seconds=600,
        )

        assert event.agent_type == "content"


class TestDataVersionCreatedEvent:
    """Tests for DataVersionCreatedEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        event = DataVersionCreatedEvent(
            source="data-manager",
            target="operator",
            data_type="competitor_analysis",
            version_id="v1.2.3",
            created_by="seo-agent",
            changes_summary="Added 5 new competitors, updated pricing data",
        )

        assert event.type == "data.version_created"
        assert event.priority == 2
        assert event.data_type == "competitor_analysis"
        assert event.version_id == "v1.2.3"
        assert event.created_by == "seo-agent"
        assert event.changes_summary == "Added 5 new competitors, updated pricing data"

    def test_different_data_types(self):
        """Test event for different data types."""
        event = DataVersionCreatedEvent(
            source="data-manager",
            target="operator",
            data_type="content_strategy",
            version_id="v2.0.0",
            created_by="content-agent",
            changes_summary="Major revision of content calendar",
        )

        assert event.data_type == "content_strategy"


class TestDataVersionComparedEvent:
    """Tests for DataVersionComparedEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        differences = {
            "added": ["competitor_x", "competitor_y"],
            "removed": ["competitor_z"],
            "modified": {"pricing": "updated"},
        }
        event = DataVersionComparedEvent(
            source="data-manager",
            target="operator",
            data_type="competitor_analysis",
            version_a="v1.2.2",
            version_b="v1.2.3",
            differences=differences,
        )

        assert event.type == "data.version_compared"
        assert event.priority == 2
        assert event.data_type == "competitor_analysis"
        assert event.version_a == "v1.2.2"
        assert event.version_b == "v1.2.3"
        assert event.differences == differences

    def test_empty_differences(self):
        """Test event with no differences."""
        event = DataVersionComparedEvent(
            source="data-manager",
            target="operator",
            data_type="content_strategy",
            version_a="v1.0.0",
            version_b="v1.0.0",
            differences={},
        )

        assert event.differences == {}


class TestDataVersionArchivedEvent:
    """Tests for DataVersionArchivedEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        archived_at = datetime.now()
        event = DataVersionArchivedEvent(
            source="data-manager",
            target="operator",
            data_type="competitor_analysis",
            version_id="v1.0.0",
            archived_at=archived_at,
            reason="Superseded by v2.0.0",
        )

        assert event.type == "data.version_archived"
        assert event.priority == 3
        assert event.data_type == "competitor_analysis"
        assert event.version_id == "v1.0.0"
        assert event.archived_at == archived_at
        assert event.reason == "Superseded by v2.0.0"

    def test_different_reasons(self):
        """Test event with different archive reasons."""
        event = DataVersionArchivedEvent(
            source="data-manager",
            target="operator",
            data_type="content_strategy",
            version_id="v0.9.0",
            archived_at=datetime.now(),
            reason="Outdated and no longer relevant",
        )

        assert event.reason == "Outdated and no longer relevant"


class TestReminderEvent:
    """Tests for ReminderEvent."""

    def test_creation(self):
        """Test event creation with all fields."""
        scheduled_for = datetime.now() + timedelta(hours=1)
        context = {"task_id": "task-123", "priority": "high"}
        event = ReminderEvent(
            source="scheduler",
            target="operator",
            reminder_type="task_deadline",
            scheduled_for=scheduled_for,
            message="Task deadline approaching in 1 hour",
            context=context,
        )

        assert event.type == "system.reminder"
        assert event.priority == 2
        assert event.reminder_type == "task_deadline"
        assert event.scheduled_for == scheduled_for
        assert event.message == "Task deadline approaching in 1 hour"
        assert event.context == context

    def test_different_reminder_types(self):
        """Test event for different reminder types."""
        event = ReminderEvent(
            source="scheduler",
            target="operator",
            reminder_type="health_check",
            scheduled_for=datetime.now() + timedelta(minutes=30),
            message="Run system health check",
            context={"component": "all"},
        )

        assert event.reminder_type == "health_check"

    def test_empty_context(self):
        """Test event with empty context."""
        event = ReminderEvent(
            source="scheduler",
            target="operator",
            reminder_type="general",
            scheduled_for=datetime.now() + timedelta(days=1),
            message="Daily standup reminder",
            context={},
        )

        assert event.context == {}
