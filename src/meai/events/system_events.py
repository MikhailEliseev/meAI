"""System monitoring and data versioning events.

This module contains events for system health monitoring, performance tracking,
resource management, agent monitoring, data versioning, and reminders.
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from meai.events.base import BaseEvent


class SystemHealthCheckEvent(BaseEvent):
    """Event for system health check results.

    Attributes:
        component: Component being checked (e.g., "event-bus", "database")
        status: Health status (healthy/degraded/unhealthy)
        metrics: Health metrics dictionary
        checked_at: Timestamp of health check
    """

    type: str = Field(default="system.health_check", frozen=True)
    priority: int = Field(default=3, ge=0, le=3, frozen=True)

    component: str
    status: str
    metrics: dict[str, Any]
    checked_at: datetime


class SystemPerformanceDegradedEvent(BaseEvent):
    """Event for performance degradation detection.

    Attributes:
        component: Component with degraded performance
        metric_name: Name of the degraded metric
        current_value: Current metric value
        threshold_value: Threshold that was exceeded
        severity: Severity level (warning/critical)
    """

    type: str = Field(default="system.performance_degraded", frozen=True)
    priority: int = Field(default=1, ge=0, le=3, frozen=True)

    component: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str


class SystemResourceLowEvent(BaseEvent):
    """Event for low system resource detection.

    Attributes:
        resource_type: Type of resource (memory/disk/cpu/connections)
        current_usage: Current usage level (0.0-1.0)
        threshold: Threshold that was exceeded (0.0-1.0)
        component: Component affected by low resource
    """

    type: str = Field(default="system.resource_low", frozen=True)
    priority: int = Field(default=1, ge=0, le=3, frozen=True)

    resource_type: str
    current_usage: float
    threshold: float
    component: str


class AgentUnresponsiveEvent(BaseEvent):
    """Event for unresponsive agent detection.

    Attributes:
        agent_id: ID of unresponsive agent
        agent_type: Type of agent (seo/content/ads)
        last_seen: Timestamp when agent was last seen
        timeout_seconds: Timeout threshold in seconds
    """

    type: str = Field(default="system.agent_unresponsive", frozen=True)
    priority: int = Field(default=0, ge=0, le=3, frozen=True)

    agent_id: str
    agent_type: str
    last_seen: datetime
    timeout_seconds: int


class DataVersionCreatedEvent(BaseEvent):
    """Event for data version creation.

    Attributes:
        data_type: Type of data being versioned
        version_id: Version identifier
        created_by: Agent or user who created the version
        changes_summary: Summary of changes in this version
    """

    type: str = Field(default="data.version_created", frozen=True)
    priority: int = Field(default=2, ge=0, le=3, frozen=True)

    data_type: str
    version_id: str
    created_by: str
    changes_summary: str


class DataVersionComparedEvent(BaseEvent):
    """Event for data version comparison.

    Attributes:
        data_type: Type of data being compared
        version_a: First version identifier
        version_b: Second version identifier
        differences: Dictionary of differences between versions
    """

    type: str = Field(default="data.version_compared", frozen=True)
    priority: int = Field(default=2, ge=0, le=3, frozen=True)

    data_type: str
    version_a: str
    version_b: str
    differences: dict[str, Any]


class DataVersionArchivedEvent(BaseEvent):
    """Event for data version archival.

    Attributes:
        data_type: Type of data being archived
        version_id: Version identifier
        archived_at: Timestamp of archival
        reason: Reason for archival
    """

    type: str = Field(default="data.version_archived", frozen=True)
    priority: int = Field(default=3, ge=0, le=3, frozen=True)

    data_type: str
    version_id: str
    archived_at: datetime
    reason: str


class ReminderEvent(BaseEvent):
    """Event for scheduled reminders.

    Attributes:
        reminder_type: Type of reminder (task_deadline/health_check/general)
        scheduled_for: When the reminder should fire
        message: Reminder message
        context: Additional context dictionary
    """

    type: str = Field(default="system.reminder", frozen=True)
    priority: int = Field(default=2, ge=0, le=3, frozen=True)

    reminder_type: str
    scheduled_for: datetime
    message: str
    context: dict[str, Any]
