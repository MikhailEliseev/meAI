"""Event Bus - All event types for meAI system.

This module exports all event classes and enums for easy importing:
- Base event model and enums
- Project lifecycle events
- Task execution events
- Sprint events
- Client interaction events
- Inter-magister communication events
- Error handling events
- System monitoring and data events
"""

from meai.events.base import (
    BaseEvent,
    ErrorSeverity,
    ErrorType,
    ProjectStatus,
)
from meai.events.client_events import (
    ClientApprovalApprovedEvent,
    ClientApprovalRejectedEvent,
    ClientApprovalRequestedEvent,
    ClientCommunicationRecordedEvent,
    ClientFeedbackReceivedEvent,
    ClientRevisionRequestedEvent,
    ClientReviewRequestedEvent,
)
from meai.events.error_events import (
    ErrorEscalatedEvent,
    ErrorOccurredEvent,
    ErrorResolvedEvent,
    ErrorRetryAttemptedEvent,
    RollbackCompletedEvent,
    RollbackInitiatedEvent,
)
from meai.events.event_bus import Event, EventBus, EventPriority
from meai.events.magister_events import (
    MagisterDataRequestEvent,
    MagisterDataResponseEvent,
    MagisterDependencyBlockedEvent,
    MagisterDependencyResolvedEvent,
)
from meai.events.project_events import (
    BaselineAggregationCompletedEvent,
    BaselineCollectionStartedEvent,
    BaselineDataCollectedEvent,
    InfrastructureSetupCompletedEvent,
    InfrastructureSetupStartedEvent,
    ProjectCreatedEvent,
    StrategyApprovedEvent,
    StrategyModifiedEvent,
    StrategyPlanningStartedEvent,
    StrategyProposalReadyEvent,
    StrategyReviewRequestedEvent,
)
from meai.events.sprint_events import (
    SprintApprovedEvent,
    SprintCompletedEvent,
    SprintLessonsLearnedEvent,
    SprintPlanCreatedEvent,
    SprintPlanningStartedEvent,
    SprintReportGeneratedEvent,
    SprintRetrospectiveStartedEvent,
    SprintReviewStartedEvent,
)
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
from meai.events.task_events import (
    TaskAssignedEvent,
    TaskBlockedEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskFailedEvent,
    TaskProgressEvent,
    TaskStartedEvent,
)

__all__ = [
    # Base
    "BaseEvent",
    "ProjectStatus",
    "ErrorType",
    "ErrorSeverity",
    # Event Bus
    "EventBus",
    "Event",
    "EventPriority",
    # Project Events
    "ProjectCreatedEvent",
    "InfrastructureSetupStartedEvent",
    "InfrastructureSetupCompletedEvent",
    "BaselineCollectionStartedEvent",
    "BaselineDataCollectedEvent",
    "BaselineAggregationCompletedEvent",
    "StrategyPlanningStartedEvent",
    "StrategyProposalReadyEvent",
    "StrategyReviewRequestedEvent",
    "StrategyModifiedEvent",
    "StrategyApprovedEvent",
    # Task Events
    "TaskCreatedEvent",
    "TaskAssignedEvent",
    "TaskStartedEvent",
    "TaskProgressEvent",
    "TaskCompletedEvent",
    "TaskFailedEvent",
    "TaskBlockedEvent",
    # Sprint Events
    "SprintPlanningStartedEvent",
    "SprintPlanCreatedEvent",
    "SprintApprovedEvent",
    "SprintReviewStartedEvent",
    "SprintReportGeneratedEvent",
    "SprintRetrospectiveStartedEvent",
    "SprintLessonsLearnedEvent",
    "SprintCompletedEvent",
    # Client Events
    "ClientCommunicationRecordedEvent",
    "ClientApprovalRequestedEvent",
    "ClientApprovalApprovedEvent",
    "ClientApprovalRejectedEvent",
    "ClientRevisionRequestedEvent",
    "ClientReviewRequestedEvent",
    "ClientFeedbackReceivedEvent",
    # Magister Events
    "MagisterDataRequestEvent",
    "MagisterDataResponseEvent",
    "MagisterDependencyBlockedEvent",
    "MagisterDependencyResolvedEvent",
    # Error Events
    "ErrorOccurredEvent",
    "ErrorRetryAttemptedEvent",
    "ErrorResolvedEvent",
    "ErrorEscalatedEvent",
    "RollbackInitiatedEvent",
    "RollbackCompletedEvent",
    # System Events
    "SystemHealthCheckEvent",
    "SystemPerformanceDegradedEvent",
    "SystemResourceLowEvent",
    "AgentUnresponsiveEvent",
    "DataVersionCreatedEvent",
    "DataVersionComparedEvent",
    "DataVersionArchivedEvent",
    "ReminderEvent",
]
