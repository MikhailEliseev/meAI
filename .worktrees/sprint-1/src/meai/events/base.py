"""Base event model and core enums for Event Bus architecture.

This module provides the foundation for all events in the meAI system:
- BaseEvent: Base Pydantic model that all events inherit from
- ProjectStatus: Enum for project lifecycle stages
- ErrorType: Enum for error categorization
- ErrorSeverity: Enum for error severity levels
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    """Project lifecycle status enum.

    Represents the stages a project goes through from lead to completion.
    """

    LEAD = "LEAD"
    PRE_SALE = "PRE_SALE"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    PROPOSAL_FOLLOW_UP = "PROPOSAL_FOLLOW_UP"
    CONTRACT_SIGNED = "CONTRACT_SIGNED"
    SETUP = "SETUP"
    BASELINE = "BASELINE"
    STRATEGY_PLANNING = "STRATEGY_PLANNING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class ErrorType(str, Enum):
    """Error type categorization enum.

    Used to classify different types of errors in the system.
    """

    VALIDATION = "VALIDATION"
    TIMEOUT = "TIMEOUT"
    API_FAILURE = "API_FAILURE"
    DATA_MISSING = "DATA_MISSING"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK = "NETWORK"
    UNKNOWN = "UNKNOWN"


class ErrorSeverity(str, Enum):
    """Error severity level enum.

    Indicates the impact level of an error.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BaseEvent(BaseModel):
    """Base event model for all events in the system.

    All events inherit from this base class and must provide:
    - type: Event type identifier (e.g., "task.created", "project.updated")
    - source: Agent/component that created the event
    - target: Agent/component(s) that should receive the event (string or list)

    Optional fields:
    - priority: Event priority (0=highest, 3=lowest, default=2)
    - correlation_id: ID to correlate related events
    - reply_to: ID of event this is replying to
    - metadata: Additional event-specific data

    Auto-generated fields:
    - id: Unique event identifier (UUID)
    - timestamp: Event creation timestamp
    """

    model_config = ConfigDict()

    id: UUID = Field(default_factory=uuid4)
    type: str = Field(..., description="Event type identifier")
    source: str = Field(..., description="Event source (agent/component)")
    target: str | list[str] = Field(..., description="Event target(s)")
    priority: int = Field(default=2, ge=0, le=3, description="Priority (0=highest, 3=lowest)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = Field(default=None, description="Correlation ID for related events")
    reply_to: str | None = Field(default=None, description="ID of event being replied to")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event data")
