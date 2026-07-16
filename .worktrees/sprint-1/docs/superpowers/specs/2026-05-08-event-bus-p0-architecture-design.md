# Event Bus Architecture - P0 Magisters Design

**Date:** 2026-05-08  
**Status:** Design Complete  
**Scope:** P0 Magisters (Operator, Brand, Content, Analytics)  
**Author:** meAI Architect

---

## Executive Summary

This document specifies the Event Bus architecture for the meAI system, focusing on P0 Magisters (Operator, Brand Magister, Content Magister, Analytics Magister). The Event Bus enables asynchronous, priority-based communication between system components across the entire project lifecycle.

### Key Decisions

1. **Strict Typing with Flexibility** - Pydantic models with optional fields
2. **Priority-Based Queue** - P0 (critical) to P3 (low) for event routing
3. **Correlation Chains** - correlation_id and reply_to for request/response patterns
4. **Phase-Based Events** - Events organized by project lifecycle phases
5. **Comprehensive Error Handling** - Retry, escalation, and rollback mechanisms
6. **Inter-Magister Communication** - Explicit data request/response patterns
7. **Client Approval Flow** - Structured approval/rejection/revision workflow
8. **System Monitoring** - Health checks and performance monitoring

### Project Lifecycle Phases

- **Phase -1: Pre-Sale** - Lead qualification and proposal generation
- **Phase 0: Setup** - Infrastructure creation
- **Phase 1: Baseline** - Initial data collection
- **Phase 1.5: Strategy Planning** - Strategy development and approval
- **Phase 2+: Active Work** - Sprint-based execution

---

## 1. Architecture Overview

### 1.1 Three-Layer Hierarchy

```
YOU (Human)
  ↓ strategic questions
ARCHITECT (Strategy Layer)
  ↓ strategic decisions
OPERATOR (Tactical Layer)
  ↓ task delegation via Event Bus
MAGISTERS (Execution Layer)
  ↓ results via Event Bus
OPERATOR
  ↓ aggregated report
YOU
```

### 1.2 Event-Driven Communication

All communication between components happens through the Event Bus:
- **Asynchronous** - Non-blocking message passing
- **Priority-Based** - Critical events processed first
- **Auditable** - All events stored in Event Store
- **Replayable** - System state can be reconstructed from events

### 1.3 Component Responsibilities

**Event Bus:**
- Route events based on target and priority
- Maintain priority queue (P0-P3)
- Handle subscriptions and broadcasts
- Ensure delivery guarantees

**Event Store:**
- Persist all events immutably
- Support event replay for debugging
- Enable snapshot/restore for rollback
- Provide audit trail

**Magisters:**
- Subscribe to relevant event types
- Process events asynchronously
- Emit result events
- Handle errors gracefully

---

## 2. Base Event Schema

### 2.1 BaseEvent Model

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

class BaseEvent(BaseModel):
    """Base event model for all events in the system"""
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str  # Format: "category.action.status"
    
    # Routing
    source: str  # Component that emitted the event
    target: str | List[str]  # Target component(s)
    priority: int = 2  # 0=P0 (critical), 1=P1 (high), 2=P2 (normal), 3=P3 (low)
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Correlation
    correlation_id: Optional[str] = None  # Links related events
    reply_to: Optional[str] = None  # For request/response pattern
    
    # Extensibility
    metadata: Optional[Dict[str, Any]] = None
```

### 2.2 Event Categories

Events are organized into categories using dot notation:

- **project.*** - Project lifecycle events
- **task.*** - Task execution events
- **data.*** - Data collection and processing events
- **magister.*** - Inter-magister communication events
- **client.*** - Client interaction events
- **system.*** - System health and monitoring events
- **error.*** - Error and recovery events
- **reminder.*** - Scheduled reminder events

### 2.3 Priority Levels

| Priority | Level | Use Cases | Examples |
|----------|-------|-----------|----------|
| P0 | Critical | System errors, critical failures | error.occurred (critical), system.agent.unresponsive |
| P1 | High | Client approvals, task failures | client.approval.requested, task.failed |
| P2 | Normal | Task progress, data collection | task.progress, data.collected |
| P3 | Low | Monitoring, health checks | system.health.check, reminder.scheduled |

---

## 3. Project Lifecycle Phases


### 3.1 Phase -1: Pre-Sale

**Goal:** Qualify lead and generate compelling proposal through comprehensive public analysis.

**Key Principle:** Maximum public analysis using all available Magisters and tools to create competitive advantage.

#### 3.1.1 Events

**ProjectCreatedEvent**
```python
class ProjectStatus(str, Enum):
    LEAD = "lead"
    PRE_SALE = "pre-sale"
    PROPOSAL_SENT = "proposal_sent"
    PROPOSAL_FOLLOW_UP = "proposal_follow_up"
    CONTRACT_SIGNED = "contract_signed"
    SETUP = "setup"
    BASELINE = "baseline"
    STRATEGY_PLANNING = "strategy_planning"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class ProjectCreatedEvent(BaseEvent):
    """New project created in Pre-Sale phase"""
    type: Literal["project.created"]
    priority: int = 1  # P1 - High priority
    data: ProjectCreatedData

class ProjectCreatedData(BaseModel):
    project_id: str
    client_name: str
    client_domain: str
    client_contact: str
    industry: str
    initial_status: ProjectStatus = ProjectStatus.LEAD
    source: str  # "inbound", "outbound", "referral"
    created_at: datetime
    notes: Optional[str] = None
```

**TaskCreatedEvent**
```python
class TaskCreatedEvent(BaseEvent):
    """Task created for Magister execution"""
    type: Literal["task.created"]
    priority: int = 2  # P2 - Normal
    data: TaskCreatedData

class TaskCreatedData(BaseModel):
    project_id: str
    task_id: str
    magister: str  # Target magister
    capability: str  # Capability to execute
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    dependencies: List[str] = []  # Other task_ids
```

**ProposalGenerationStartedEvent**
```python
class ProposalGenerationStartedEvent(BaseEvent):
    """Operator started generating proposal"""
    type: Literal["project.proposal.generation_started"]
    priority: int = 1  # P1 - High
    data: ProposalGenerationStartedData

class ProposalGenerationStartedData(BaseModel):
    project_id: str
    analysis_results: Dict[str, Any]  # Results from all Magisters
    custdev_insights: Dict[str, Any]  # From Brand Magister
    competitive_analysis: Dict[str, Any]  # From Intelligence Magister
    estimated_completion: datetime
```

**ReminderEvent**
```python
class ReminderEvent(BaseEvent):
    """Scheduled reminder for follow-up"""
    type: Literal["reminder.scheduled"]
    priority: int = 3  # P3 - Low
    data: ReminderData

class ReminderData(BaseModel):
    project_id: str
    reminder_type: Literal["1_month", "2_months", "3_months"]
    scheduled_for: datetime
    action: str  # What to do when reminder fires
    context: Dict[str, Any]
```

#### 3.1.2 Flow

```
1. YOU creates lead → ProjectCreatedEvent (status=lead)
2. Operator analyzes → Multiple TaskCreatedEvents for Magisters
3. Magisters execute → TaskCompletedEvents with results
4. Operator aggregates → ProposalGenerationStartedEvent
5. Proposal ready → ProjectStatusChangedEvent (status=proposal_sent)
6. If no response → ReminderEvent (1 month, 2 months, 3 months)
7. Client responds → ProjectStatusChangedEvent (status=contract_signed or closed_lost)
8. Operator learns from outcome
```

---

### 3.2 Phase 0: Setup

**Goal:** Create infrastructure (folders, vaults, API connections) without data analysis.

#### 3.2.1 Events

**InfrastructureSetupStartedEvent**
```python
class InfrastructureSetupStartedEvent(BaseEvent):
    """Operator started infrastructure setup"""
    type: Literal["project.setup.started"]
    priority: int = 1  # P1 - High
    data: InfrastructureSetupStartedData

class InfrastructureSetupStartedData(BaseModel):
    project_id: str
    setup_tasks: List[SetupTask]
    estimated_completion: datetime

class SetupTask(BaseModel):
    task_type: Literal["vault", "folder", "api_connection", "database"]
    description: str
    magister: Optional[str] = None  # Which magister needs this
```

**InfrastructureSetupCompletedEvent**
```python
class InfrastructureSetupCompletedEvent(BaseEvent):
    """Infrastructure setup completed"""
    type: Literal["project.setup.completed"]
    priority: int = 1  # P1 - High
    data: InfrastructureSetupCompletedData

class InfrastructureSetupCompletedData(BaseModel):
    project_id: str
    completed_at: datetime
    created_vaults: List[str]
    created_folders: List[str]
    connected_apis: List[str]
    ready_for_baseline: bool
```

#### 3.2.2 Flow

```
1. Contract signed → ProjectStatusChangedEvent (status=setup)
2. Operator starts setup → InfrastructureSetupStartedEvent
3. Create vaults for each Magister
4. Create project folders
5. Connect APIs (Analytics, Ads platforms, etc.)
6. Setup complete → InfrastructureSetupCompletedEvent
7. Ready for Baseline → ProjectStatusChangedEvent (status=baseline)
```

---


### 3.3 Phase 1: Baseline

**Goal:** Collect comprehensive data from all connected systems to establish baseline metrics.

**Frequency:**
- **Initial baseline** - Full data collection at project start
- **Monthly reports** - Lightweight data collection every month
- **Quarterly full baseline** - Complete re-baseline every 3 months

#### 3.3.1 Events

**BaselineCollectionStartedEvent**
```python
class BaselineCollectionStartedEvent(BaseEvent):
    """Baseline data collection started"""
    type: Literal["project.baseline.started"]
    priority: int = 1  # P1 - High
    data: BaselineCollectionStartedData

class BaselineCollectionStartedData(BaseModel):
    project_id: str
    baseline_type: Literal["initial", "monthly", "quarterly"]
    collection_tasks: List[BaselineTask]
    estimated_completion: datetime

class BaselineTask(BaseModel):
    magister: str
    data_source: str  # "google_analytics", "yandex_metrika", etc.
    metrics: List[str]
    time_range: str  # "last_30_days", "last_90_days", etc.
```

**BaselineDataCollectedEvent**
```python
class BaselineDataCollectedEvent(BaseEvent):
    """Magister collected baseline data"""
    type: Literal["data.baseline.collected"]
    priority: int = 2  # P2 - Normal
    data: BaselineDataCollectedData

class BaselineDataCollectedData(BaseModel):
    project_id: str
    magister: str
    data_source: str
    metrics: Dict[str, Any]
    time_range: str
    collected_at: datetime
    data_quality: Literal["complete", "partial", "failed"]
    notes: Optional[str] = None
```

**BaselineAggregationCompletedEvent**
```python
class BaselineAggregationCompletedEvent(BaseEvent):
    """All baseline data aggregated"""
    type: Literal["project.baseline.aggregation_completed"]
    priority: int = 1  # P1 - High
    data: BaselineAggregationCompletedData

class BaselineAggregationCompletedData(BaseModel):
    project_id: str
    baseline_id: str
    baseline_type: Literal["initial", "monthly", "quarterly"]
    aggregated_metrics: Dict[str, Any]
    completed_at: datetime
    vault_path: str  # Where baseline is stored
    ready_for_strategy: bool
```

#### 3.3.2 Flow

```
1. Setup complete → ProjectStatusChangedEvent (status=baseline)
2. Operator starts baseline → BaselineCollectionStartedEvent
3. Magisters collect data → Multiple BaselineDataCollectedEvents
4. Analytics Magister aggregates → BaselineAggregationCompletedEvent
5. Baseline stored in vaults
6. Ready for strategy → ProjectStatusChangedEvent (status=strategy_planning)
```

---

### 3.4 Phase 1.5: Strategy Planning

**Goal:** Develop marketing strategy based on baseline data and get client approval.

**Key Feature:** Strategy is a living document with versioning and modification tracking.

#### 3.4.1 Events

**StrategyPlanningStartedEvent**
```python
class StrategyPlanningStartedEvent(BaseEvent):
    """Strategy planning phase started"""
    type: Literal["project.strategy.planning_started"]
    priority: int = 1  # P1 - High
    data: StrategyPlanningStartedData

class StrategyPlanningStartedData(BaseModel):
    project_id: str
    baseline_id: str  # Which baseline to use
    planning_deadline: datetime
    assigned_magisters: List[str]
```

**StrategyProposalReadyEvent**
```python
class StrategyProposalReadyEvent(BaseEvent):
    """Strategy proposal ready for review"""
    type: Literal["project.strategy.proposal_ready"]
    priority: int = 1  # P1 - High
    data: StrategyProposalReadyData

class StrategyProposalReadyData(BaseModel):
    project_id: str
    strategy_id: str
    version: str  # "1.0"
    strategy_document_path: str
    key_recommendations: List[str]
    estimated_budget: float
    estimated_timeline_months: int
    created_at: datetime
```

**StrategyReviewRequestedEvent**
```python
class StrategyReviewRequestedEvent(BaseEvent):
    """Strategy review requested from client"""
    type: Literal["project.strategy.review_requested"]
    priority: int = 1  # P1 - High
    data: StrategyReviewRequestedData

class StrategyReviewRequestedData(BaseModel):
    project_id: str
    strategy_id: str
    version: str
    review_deadline: datetime
    meeting_scheduled: Optional[datetime] = None
```

**ClientCommunicationRecordedEvent**
```python
class ClientCommunicationRecordedEvent(BaseEvent):
    """Client communication recorded"""
    type: Literal["project.communication.recorded"]
    priority: int = 2  # P2 - Normal
    data: ClientCommunicationData

class ClientCommunicationData(BaseModel):
    project_id: str
    communication_id: str
    communication_type: Literal["email", "call", "meeting", "chat"]
    direction: Literal["inbound", "outbound"]
    participants: List[str]
    summary: str
    action_items: List[str]
    recorded_at: datetime
    related_to: Optional[str] = None  # strategy_id, sprint_id, etc.
```

**StrategyModifiedEvent**
```python
class StrategyModifiedEvent(BaseEvent):
    """Strategy modified based on feedback"""
    type: Literal["project.strategy.modified"]
    priority: int = 1  # P1 - High
    data: StrategyModifiedData

class StrategyModifiedData(BaseModel):
    project_id: str
    strategy_id: str
    previous_version: str
    new_version: str
    modifications: List[StrategyModification]
    modified_by: str
    modified_at: datetime
    reason: str

class StrategyModification(BaseModel):
    section: str
    change_type: Literal["added", "removed", "modified"]
    description: str
    impact: Literal["minor", "major"]
```

**StrategyApprovedEvent**
```python
class StrategyApprovedEvent(BaseEvent):
    """Strategy approved by client"""
    type: Literal["project.strategy.approved"]
    priority: int = 1  # P1 - High
    data: StrategyApprovedData

class StrategyApprovedData(BaseModel):
    project_id: str
    strategy_id: str
    version: str
    approved_by: str
    approved_at: datetime
    comments: Optional[str] = None
    ready_for_execution: bool
```

#### 3.4.2 Flow

```
1. Baseline complete → ProjectStatusChangedEvent (status=strategy_planning)
2. Operator starts planning → StrategyPlanningStartedEvent
3. Magisters contribute → Strategy document created
4. Strategy ready → StrategyProposalReadyEvent
5. Request review → StrategyReviewRequestedEvent
6. Client meeting → ClientCommunicationRecordedEvent
7. Feedback received → StrategyModifiedEvent (if changes needed)
8. Repeat 6-7 until approved
9. Client approves → StrategyApprovedEvent
10. Ready for execution → ProjectStatusChangedEvent (status=active)
```

---


### 3.5 Phase 2+: Active Work (Sprint Execution)

**Goal:** Execute marketing strategy through sprint-based workflow with continuous client feedback.

**Structure:** Each sprint has 4 sub-phases:
- 2.1 Sprint Planning
- 2.2 Task Execution
- 2.3 Sprint Review
- 2.4 Sprint Retrospective

---

#### 3.5.1 Sprint Planning (Phase 2.1)

**SprintPlanningStartedEvent**
```python
class SprintPlanningStartedEvent(BaseEvent):
    """Operator started sprint planning"""
    type: Literal["project.sprint.planning_started"]
    priority: int = 1  # P1 - High
    data: SprintPlanningStartedData

class SprintPlanningStartedData(BaseModel):
    project_id: str
    sprint_number: int
    sprint_duration_weeks: int
    planning_deadline: datetime
    strategy_version: str  # Which strategy version to use
```

**SprintPlanCreatedEvent**
```python
class SprintPlanCreatedEvent(BaseEvent):
    """Sprint plan created"""
    type: Literal["project.sprint.plan_created"]
    priority: int = 1  # P1 - High
    data: SprintPlanCreatedData

class SprintPlanCreatedData(BaseModel):
    project_id: str
    sprint_id: str
    sprint_number: int
    tasks: List[SprintTask]
    dependencies: List[TaskDependency]
    estimated_hours: float
    start_date: datetime
    end_date: datetime

class SprintTask(BaseModel):
    task_id: str
    magister: str  # Which Magister is responsible
    capability: str  # Which capability to use
    description: str
    estimated_hours: float
    priority: int
    dependencies: List[str]  # task_ids that must complete first

class TaskDependency(BaseModel):
    task_id: str
    depends_on: List[str]  # task_ids
    dependency_type: Literal["blocking", "soft"]
    # blocking = cannot start until dependencies complete
    # soft = preferable to wait but not required
```

**SprintApprovedEvent**
```python
class SprintApprovedEvent(BaseEvent):
    """Client approved sprint plan"""
    type: Literal["project.sprint.approved"]
    priority: int = 1  # P1 - High
    data: SprintApprovedData

class SprintApprovedData(BaseModel):
    project_id: str
    sprint_id: str
    approved_by: str
    approved_at: datetime
    modifications: Optional[List[str]] = None  # Changes before approval
```

---

#### 3.5.2 Task Execution (Phase 2.2)

**TaskAssignedEvent**
```python
class TaskAssignedEvent(BaseEvent):
    """Operator assigned task to Magister"""
    type: Literal["task.assigned"]
    priority: int = 2  # P2 - Normal
    data: TaskAssignedData

class TaskAssignedData(BaseModel):
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    capability: str
    parameters: Dict[str, Any]
    deadline: datetime
    dependencies: List[str]  # task_ids that must complete first
```

**TaskStartedEvent**
```python
class TaskStartedEvent(BaseEvent):
    """Magister started task execution"""
    type: Literal["task.started"]
    priority: int = 2  # P2 - Normal
    data: TaskStartedData

class TaskStartedData(BaseModel):
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    started_at: datetime
    estimated_completion: datetime
```

**TaskProgressEvent**
```python
class TaskProgressEvent(BaseEvent):
    """Magister reports task progress"""
    type: Literal["task.progress"]
    priority: int = 2  # P2 - Normal
    data: TaskProgressData

class TaskProgressData(BaseModel):
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    progress_percent: int  # 0-100
    current_step: str
    estimated_completion: datetime
    notes: Optional[str] = None
```

**TaskCompletedEvent**
```python
class TaskCompletedEvent(BaseEvent):
    """Magister completed task"""
    type: Literal["task.completed"]
    priority: int = 2  # P2 - Normal
    data: TaskCompletedData

class TaskCompletedData(BaseModel):
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    completed_at: datetime
    result: Dict[str, Any]
    deliverables: List[Deliverable]
    next_actions: Optional[List[str]] = None

class Deliverable(BaseModel):
    type: str  # "report", "content", "campaign", "analysis"
    title: str
    description: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    requires_approval: bool = True
```

**TaskFailedEvent**
```python
class TaskFailedEvent(BaseEvent):
    """Magister failed to complete task"""
    type: Literal["task.failed"]
    priority: int = 1  # P1 - High (needs attention)
    data: TaskFailedData

class TaskFailedData(BaseModel):
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    failed_at: datetime
    error_type: str
    error_message: str
    retry_possible: bool
    escalation_required: bool
```

**TaskBlockedEvent**
```python
class TaskBlockedEvent(BaseEvent):
    """Task blocked by dependency"""
    type: Literal["task.blocked"]
    priority: int = 2  # P2 - Normal
    data: TaskBlockedData

class TaskBlockedData(BaseModel):
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    blocked_by: List[str]  # task_ids blocking this task
    blocked_at: datetime
    estimated_unblock: Optional[datetime] = None
```

---

#### 3.5.3 Sprint Review (Phase 2.3)

**SprintReviewStartedEvent**
```python
class SprintReviewStartedEvent(BaseEvent):
    """Operator started sprint review"""
    type: Literal["project.sprint.review_started"]
    priority: int = 1  # P1 - High
    data: SprintReviewStartedData

class SprintReviewStartedData(BaseModel):
    project_id: str
    sprint_id: str
    sprint_number: int
    review_date: datetime
    completed_tasks: int
    total_tasks: int
```

**SprintReportGeneratedEvent**
```python
class SprintReportGeneratedEvent(BaseEvent):
    """Sprint report generated"""
    type: Literal["project.sprint.report_generated"]
    priority: int = 1  # P1 - High
    data: SprintReportGeneratedData

class SprintReportGeneratedData(BaseModel):
    project_id: str
    sprint_id: str
    report_path: str
    summary: SprintSummary
    deliverables: List[Deliverable]
    metrics: SprintMetrics

class SprintSummary(BaseModel):
    completed_tasks: int
    total_tasks: int
    completion_rate: float
    total_hours_spent: float
    estimated_hours: float
    key_achievements: List[str]
    challenges: List[str]

class SprintMetrics(BaseModel):
    velocity: float  # tasks per week
    quality_score: float  # 0-100
    client_satisfaction: Optional[float] = None  # 0-100
    magister_performance: Dict[str, float]  # magister -> score
```

**ClientReviewRequestedEvent**
```python
class ClientReviewRequestedEvent(BaseEvent):
    """Client review requested for sprint"""
    type: Literal["client.review.requested"]
    priority: int = 1  # P1 - High
    data: ClientReviewRequestedData

class ClientReviewRequestedData(BaseModel):
    project_id: str
    sprint_id: str
    deliverables: List[Deliverable]
    review_deadline: datetime
    meeting_scheduled: Optional[datetime] = None
```

**ClientFeedbackReceivedEvent**
```python
class ClientFeedbackReceivedEvent(BaseEvent):
    """Client provided feedback on sprint"""
    type: Literal["client.feedback.received"]
    priority: int = 1  # P1 - High
    data: ClientFeedbackReceivedData

class ClientFeedbackReceivedData(BaseModel):
    project_id: str
    sprint_id: str
    received_at: datetime
    satisfaction_score: int  # 1-10
    approved_deliverables: List[str]  # deliverable ids
    revision_requested: List[DeliverableRevision]
    comments: str

class DeliverableRevision(BaseModel):
    deliverable_id: str
    revision_type: Literal["minor", "major"]
    requested_changes: str
    deadline: datetime
```

---

#### 3.5.4 Sprint Retrospective (Phase 2.4)

**SprintRetrospectiveStartedEvent**
```python
class SprintRetrospectiveStartedEvent(BaseEvent):
    """Sprint retrospective started"""
    type: Literal["project.sprint.retrospective_started"]
    priority: int = 2  # P2 - Normal
    data: SprintRetrospectiveStartedData

class SprintRetrospectiveStartedData(BaseModel):
    project_id: str
    sprint_id: str
    sprint_number: int
    retrospective_date: datetime
```

**SprintLessonsLearnedEvent**
```python
class SprintLessonsLearnedEvent(BaseEvent):
    """Sprint lessons learned recorded"""
    type: Literal["project.sprint.lessons_learned"]
    priority: int = 2  # P2 - Normal
    data: SprintLessonsLearnedData

class SprintLessonsLearnedData(BaseModel):
    project_id: str
    sprint_id: str
    what_went_well: List[str]
    what_went_wrong: List[str]
    action_items: List[ActionItem]
    process_improvements: List[str]

class ActionItem(BaseModel):
    description: str
    assignee: str  # magister or operator
    deadline: datetime
    priority: int
```

**SprintCompletedEvent**
```python
class SprintCompletedEvent(BaseEvent):
    """Sprint fully completed"""
    type: Literal["project.sprint.completed"]
    priority: int = 1  # P1 - High
    data: SprintCompletedData

class SprintCompletedData(BaseModel):
    project_id: str
    sprint_id: str
    sprint_number: int
    completed_at: datetime
    next_sprint_planned: bool
    next_sprint_start: Optional[datetime] = None
```

---


## 4. Cross-Cutting Concerns

### 4.1 Inter-Magister Communication

**Goal:** Enable Magisters to request data from each other and handle dependencies.

**Pattern:** Request/Response with correlation_id linking.

#### 4.1.1 Events

**MagisterDataRequestEvent**
```python
class MagisterDataRequestEvent(BaseEvent):
    """Magister requests data from another Magister"""
    type: Literal["magister.request.data"]
    priority: int = 2  # P2 - Normal
    data: MagisterDataRequestData

class MagisterDataRequestData(BaseModel):
    project_id: str
    requesting_magister: str
    target_magister: str
    data_type: str  # "tone_of_voice", "keywords", "analytics", etc.
    parameters: Dict[str, Any]
    urgency: Literal["low", "medium", "high"]
    deadline: Optional[datetime] = None
```

**MagisterDataResponseEvent**
```python
class MagisterDataResponseEvent(BaseEvent):
    """Magister responds to data request"""
    type: Literal["magister.response.data"]
    priority: int = 2  # P2 - Normal
    data: MagisterDataResponseData

class MagisterDataResponseData(BaseModel):
    project_id: str
    request_id: str  # correlation_id from request
    responding_magister: str
    requesting_magister: str
    data: Dict[str, Any]
    status: Literal["success", "partial", "failed"]
    notes: Optional[str] = None
```

**MagisterDependencyBlockedEvent**
```python
class MagisterDependencyBlockedEvent(BaseEvent):
    """Magister blocked by dependency on another Magister"""
    type: Literal["magister.dependency.blocked"]
    priority: int = 2  # P2 - Normal
    data: MagisterDependencyBlockedData

class MagisterDependencyBlockedData(BaseModel):
    project_id: str
    task_id: str
    blocked_magister: str
    blocking_magister: str
    reason: str
    estimated_unblock: Optional[datetime] = None
```

**MagisterDependencyResolvedEvent**
```python
class MagisterDependencyResolvedEvent(BaseEvent):
    """Dependency between Magisters resolved"""
    type: Literal["magister.dependency.resolved"]
    priority: int = 2  # P2 - Normal
    data: MagisterDependencyResolvedData

class MagisterDependencyResolvedData(BaseModel):
    project_id: str
    task_id: str
    blocked_magister: str
    blocking_magister: str
    resolved_at: datetime
```

#### 4.1.2 Flow Example: Content Magister needs Tone of Voice

```
1. Content Magister starts task → needs ToV from Brand Magister
2. Content emits → MagisterDataRequestEvent
   - requesting_magister: "content_magister"
   - target_magister: "brand_magister"
   - data_type: "tone_of_voice"
   - correlation_id: "req-123"
3. Brand Magister receives request → processes
4. Brand emits → MagisterDataResponseEvent
   - reply_to: "req-123"
   - data: {tone_of_voice: {...}}
5. Content Magister receives response → continues task
```

---

### 4.2 Client Approval Flow

**Goal:** Structured workflow for client approval of deliverables.

#### 4.2.1 Events

**ClientApprovalRequestedEvent**
```python
class ClientApprovalRequestedEvent(BaseEvent):
    """Approval requested from client"""
    type: Literal["client.approval.requested"]
    priority: int = 1  # P1 - High
    data: ClientApprovalRequestedData

class ClientApprovalRequestedData(BaseModel):
    project_id: str
    approval_id: str
    deliverable_id: str
    deliverable_type: str
    deliverable_title: str
    deliverable_path: Optional[str] = None
    deliverable_url: Optional[str] = None
    requested_at: datetime
    deadline: datetime
    description: str
```

**ClientApprovalApprovedEvent**
```python
class ClientApprovalApprovedEvent(BaseEvent):
    """Client approved deliverable"""
    type: Literal["client.approval.approved"]
    priority: int = 1  # P1 - High
    data: ClientApprovalApprovedData

class ClientApprovalApprovedData(BaseModel):
    project_id: str
    approval_id: str
    deliverable_id: str
    approved_by: str
    approved_at: datetime
    comments: Optional[str] = None
```

**ClientApprovalRejectedEvent**
```python
class ClientApprovalRejectedEvent(BaseEvent):
    """Client rejected deliverable"""
    type: Literal["client.approval.rejected"]
    priority: int = 1  # P1 - High
    data: ClientApprovalRejectedData

class ClientApprovalRejectedData(BaseModel):
    project_id: str
    approval_id: str
    deliverable_id: str
    rejected_by: str
    rejected_at: datetime
    reason: str
    severity: Literal["minor", "major", "critical"]
```

**ClientRevisionRequestedEvent**
```python
class ClientRevisionRequestedEvent(BaseEvent):
    """Client requested revisions"""
    type: Literal["client.approval.revision_requested"]
    priority: int = 1  # P1 - High
    data: ClientRevisionRequestedData

class ClientRevisionRequestedData(BaseModel):
    project_id: str
    approval_id: str
    deliverable_id: str
    requested_by: str
    requested_at: datetime
    revision_type: Literal["minor", "major"]
    requested_changes: str
    deadline: datetime
    priority: int
```

#### 4.2.2 Flow

```
1. Deliverable ready → ClientApprovalRequestedEvent
2. Client reviews → One of:
   a) ClientApprovalApprovedEvent → Continue
   b) ClientApprovalRejectedEvent → Escalate
   c) ClientRevisionRequestedEvent → Revise and re-submit
3. If revision → Magister updates → New ClientApprovalRequestedEvent
4. Repeat until approved
```

---


### 4.3 Error Handling & Recovery

**Goal:** Comprehensive error handling with retry, escalation, and rollback mechanisms.

#### 4.3.1 Error Types and Severity

```python
class ErrorType(str, Enum):
    VALIDATION = "validation"  # Invalid data
    TIMEOUT = "timeout"  # Operation timed out
    API_FAILURE = "api_failure"  # External API failed
    DATA_MISSING = "data_missing"  # Required data not found
    PERMISSION_DENIED = "permission_denied"  # Access denied
    RATE_LIMIT = "rate_limit"  # API rate limit hit
    NETWORK = "network"  # Network connectivity issue
    UNKNOWN = "unknown"  # Unknown error

class ErrorSeverity(str, Enum):
    LOW = "low"  # Can be ignored
    MEDIUM = "medium"  # Should be logged
    HIGH = "high"  # Requires retry
    CRITICAL = "critical"  # Requires escalation
```

#### 4.3.2 Events

**ErrorOccurredEvent**
```python
class ErrorOccurredEvent(BaseEvent):
    """Error occurred in system"""
    type: Literal["error.occurred"]
    priority: int = 0  # P0 - Critical (if severity=critical)
    data: ErrorOccurredData

class ErrorOccurredData(BaseModel):
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    component: str  # "operator", "seo_magister", "event_bus", etc.
    error_type: ErrorType
    severity: ErrorSeverity
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any]
    retry_possible: bool
    retry_count: int = 0
    max_retries: int = 3
```

**ErrorRetryAttemptedEvent**
```python
class ErrorRetryAttemptedEvent(BaseEvent):
    """Retry attempted after error"""
    type: Literal["error.retry_attempted"]
    priority: int = 1  # P1 - High
    data: ErrorRetryAttemptedData

class ErrorRetryAttemptedData(BaseModel):
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    original_error_id: str
    component: str
    retry_number: int
    max_retries: int
    attempted_at: datetime
```

**ErrorResolvedEvent**
```python
class ErrorResolvedEvent(BaseEvent):
    """Error resolved"""
    type: Literal["error.resolved"]
    priority: int = 2  # P2 - Normal
    data: ErrorResolvedData

class ErrorResolvedData(BaseModel):
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    original_error_id: str
    component: str
    resolved_at: datetime
    resolution_method: Literal["retry", "manual", "automatic", "workaround"]
    notes: Optional[str] = None
```

**ErrorEscalatedEvent**
```python
class ErrorEscalatedEvent(BaseEvent):
    """Error escalated to Operator or YOU"""
    type: Literal["error.escalated"]
    priority: int = 0  # P0 - Critical
    data: ErrorEscalatedData

class ErrorEscalatedData(BaseModel):
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    original_error_id: str
    component: str
    escalated_to: Literal["operator", "user"]
    escalated_at: datetime
    reason: str
    suggested_actions: List[str]
```

**RollbackInitiatedEvent**
```python
class RollbackInitiatedEvent(BaseEvent):
    """Rollback initiated"""
    type: Literal["system.rollback.initiated"]
    priority: int = 0  # P0 - Critical
    data: RollbackInitiatedData

class RollbackInitiatedData(BaseModel):
    project_id: str
    rollback_id: str
    reason: str
    target_state: str  # snapshot_id or timestamp
    initiated_by: str
    initiated_at: datetime
```

**RollbackCompletedEvent**
```python
class RollbackCompletedEvent(BaseEvent):
    """Rollback completed"""
    type: Literal["system.rollback.completed"]
    priority: int = 0  # P0 - Critical
    data: RollbackCompletedData

class RollbackCompletedData(BaseModel):
    project_id: str
    rollback_id: str
    completed_at: datetime
    restored_state: str
    affected_components: List[str]
```

#### 4.3.3 Retry Strategy

```python
# Retry logic based on error type
RETRY_STRATEGIES = {
    ErrorType.TIMEOUT: {
        "max_retries": 3,
        "backoff": "exponential",  # 1s, 2s, 4s
        "escalate_after": 3
    },
    ErrorType.API_FAILURE: {
        "max_retries": 5,
        "backoff": "exponential",
        "escalate_after": 5
    },
    ErrorType.RATE_LIMIT: {
        "max_retries": 3,
        "backoff": "linear",  # Wait for rate limit reset
        "escalate_after": 3
    },
    ErrorType.NETWORK: {
        "max_retries": 5,
        "backoff": "exponential",
        "escalate_after": 5
    },
    ErrorType.VALIDATION: {
        "max_retries": 0,  # No retry for validation errors
        "escalate_after": 0
    },
    ErrorType.PERMISSION_DENIED: {
        "max_retries": 0,  # No retry for permission errors
        "escalate_after": 0
    }
}
```

#### 4.3.4 Flow

```
1. Error occurs → ErrorOccurredEvent
2. Check retry_possible and error_type
3. If retryable:
   a) ErrorRetryAttemptedEvent
   b) Retry operation
   c) If success → ErrorResolvedEvent
   d) If fail → Increment retry_count, goto 3a
4. If max_retries exceeded or not retryable:
   a) ErrorEscalatedEvent (to Operator or YOU)
5. If critical error affecting project state:
   a) RollbackInitiatedEvent
   b) Restore from snapshot
   c) RollbackCompletedEvent
```

---


### 4.4 System Monitoring & Health Checks

**Goal:** Monitor system health, performance, and resource usage.

#### 4.4.1 Events

**SystemHealthCheckEvent**
```python
class SystemHealthCheckEvent(BaseEvent):
    """Periodic system health check"""
    type: Literal["system.health.check"]
    priority: int = 3  # P3 - Low
    data: SystemHealthCheckData

class SystemHealthCheckData(BaseModel):
    check_id: str
    checked_at: datetime
    components: Dict[str, ComponentHealth]
    overall_status: Literal["healthy", "degraded", "critical"]

class ComponentHealth(BaseModel):
    component: str
    status: Literal["healthy", "degraded", "critical", "offline"]
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    last_activity: Optional[datetime] = None
```

**SystemPerformanceDegradedEvent**
```python
class SystemPerformanceDegradedEvent(BaseEvent):
    """System performance degraded"""
    type: Literal["system.performance.degraded"]
    priority: int = 1  # P1 - High
    data: SystemPerformanceDegradedData

class SystemPerformanceDegradedData(BaseModel):
    component: str
    metric: str  # "response_time", "error_rate", "throughput"
    current_value: float
    threshold_value: float
    degradation_percent: float
    detected_at: datetime
```

**SystemResourceLowEvent**
```python
class SystemResourceLowEvent(BaseEvent):
    """System resource running low"""
    type: Literal["system.resource.low"]
    priority: int = 1  # P1 - High
    data: SystemResourceLowData

class SystemResourceLowData(BaseModel):
    resource_type: Literal["memory", "disk", "api_quota", "database_connections"]
    current_usage: float
    max_capacity: float
    usage_percent: float
    threshold_percent: float
    detected_at: datetime
```

**AgentUnresponsiveEvent**
```python
class AgentUnresponsiveEvent(BaseEvent):
    """Agent not responding"""
    type: Literal["system.agent.unresponsive"]
    priority: int = 0  # P0 - Critical
    data: AgentUnresponsiveData

class AgentUnresponsiveData(BaseModel):
    agent_type: str  # "operator", "seo_magister", etc.
    agent_id: str
    last_activity: datetime
    timeout_seconds: int
    detected_at: datetime
    action_taken: Literal["restart", "escalate", "wait"]
```

#### 4.4.2 Monitoring Schedule

```python
MONITORING_SCHEDULE = {
    "health_check": "every 5 minutes",
    "performance_check": "every 1 minute",
    "resource_check": "every 10 minutes",
    "agent_heartbeat": "every 30 seconds"
}

THRESHOLDS = {
    "response_time_ms": 5000,  # Alert if > 5s
    "error_rate": 0.05,  # Alert if > 5%
    "memory_usage": 0.85,  # Alert if > 85%
    "disk_usage": 0.90,  # Alert if > 90%
    "api_quota": 0.80,  # Alert if > 80%
    "agent_timeout_seconds": 300  # Alert if no activity for 5 min
}
```

---

### 4.5 Data Versioning & Baseline Management

**Goal:** Track data versions and enable comparison over time.

#### 4.5.1 Events

**DataVersionCreatedEvent**
```python
class DataVersionCreatedEvent(BaseEvent):
    """New data version created"""
    type: Literal["data.version.created"]
    priority: int = 2  # P2 - Normal
    data: DataVersionCreatedData

class DataVersionCreatedData(BaseModel):
    project_id: str
    version_id: str
    version_number: int
    data_type: str  # "baseline", "analytics", "content", etc.
    created_at: datetime
    created_by: str  # magister
    changes_summary: str
    file_path: Optional[str] = None
```

**DataVersionComparedEvent**
```python
class DataVersionComparedEvent(BaseEvent):
    """Data versions compared"""
    type: Literal["data.version.compared"]
    priority: int = 2  # P2 - Normal
    data: DataVersionComparedData

class DataVersionComparedData(BaseModel):
    project_id: str
    comparison_id: str
    version_a: str
    version_b: str
    compared_at: datetime
    differences: List[DataDifference]
    summary: str

class DataDifference(BaseModel):
    field: str
    old_value: Any
    new_value: Any
    change_type: Literal["added", "removed", "modified"]
    significance: Literal["minor", "major", "critical"]
```

**DataVersionArchivedEvent**
```python
class DataVersionArchivedEvent(BaseEvent):
    """Data version archived"""
    type: Literal["data.version.archived"]
    priority: int = 3  # P3 - Low
    data: DataVersionArchivedData

class DataVersionArchivedData(BaseModel):
    project_id: str
    version_id: str
    archived_at: datetime
    archive_path: str
    retention_days: int
```

#### 4.5.2 Versioning Strategy

```python
# Baseline versioning
BASELINE_VERSIONS = {
    "initial": "1.0.0",  # First baseline
    "monthly": "1.1.0, 1.2.0, ...",  # Monthly increments
    "quarterly": "2.0.0, 3.0.0, ...",  # Quarterly major versions
}

# Retention policy
RETENTION_POLICY = {
    "initial_baseline": "forever",
    "monthly_baseline": "12 months",
    "quarterly_baseline": "36 months",
    "daily_snapshots": "30 days"
}
```

---

## 5. Event Routing & Priority

### 5.1 Priority Queue Implementation

```python
class PriorityQueue:
    """Priority-based event queue"""
    
    def __init__(self):
        self.queues = {
            0: [],  # P0 - Critical
            1: [],  # P1 - High
            2: [],  # P2 - Normal
            3: []   # P3 - Low
        }
    
    def enqueue(self, event: BaseEvent):
        """Add event to appropriate priority queue"""
        priority = event.priority
        self.queues[priority].append(event)
    
    def dequeue(self) -> Optional[BaseEvent]:
        """Get highest priority event"""
        for priority in [0, 1, 2, 3]:
            if self.queues[priority]:
                return self.queues[priority].pop(0)
        return None
```

### 5.2 Routing Rules

**Direct Routing:**
```python
# Event with single target
event = TaskAssignedEvent(
    source="operator",
    target="seo_magister",  # Direct to SEO Magister
    ...
)
```

**Broadcast Routing:**
```python
# Event with multiple targets
event = BaselineCollectionStartedEvent(
    source="operator",
    target=["seo_magister", "content_magister", "analytics_magister"],
    ...
)
```

**Subscription-Based Routing:**
```python
# Components subscribe to event types
subscriptions = {
    "operator": [
        "task.completed",
        "task.failed",
        "error.escalated",
        "client.feedback.received"
    ],
    "analytics_magister": [
        "data.baseline.collected",
        "task.completed"
    ]
}
```

### 5.3 Correlation Chains

**Request/Response Pattern:**
```python
# Request
request = MagisterDataRequestEvent(
    id="req-123",
    correlation_id="chain-456",
    source="content_magister",
    target="brand_magister",
    ...
)

# Response
response = MagisterDataResponseEvent(
    id="resp-789",
    correlation_id="chain-456",  # Same chain
    reply_to="req-123",  # Links to request
    source="brand_magister",
    target="content_magister",
    ...
)
```

---


## 6. Implementation Considerations

### 6.1 Event Store

**Purpose:** Immutable audit log of all events for replay and debugging.

**Implementation:**
```python
class EventStore:
    """Persistent event storage"""
    
    async def append(self, event: BaseEvent) -> None:
        """Append event to store (immutable)"""
        await self.db.execute(
            "INSERT INTO events (id, type, source, target, priority, "
            "timestamp, correlation_id, reply_to, data, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event.id, event.type, event.source, event.target, 
             event.priority, event.timestamp, event.correlation_id,
             event.reply_to, json.dumps(event.data), 
             json.dumps(event.metadata))
        )
    
    async def get_by_id(self, event_id: str) -> Optional[BaseEvent]:
        """Retrieve event by ID"""
        ...
    
    async def get_by_correlation(self, correlation_id: str) -> List[BaseEvent]:
        """Get all events in correlation chain"""
        ...
    
    async def get_by_project(self, project_id: str) -> List[BaseEvent]:
        """Get all events for project"""
        ...
    
    async def replay(self, from_timestamp: datetime) -> AsyncIterator[BaseEvent]:
        """Replay events from timestamp"""
        ...
```

**Schema:**
```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    priority INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    correlation_id TEXT,
    reply_to TEXT,
    data TEXT NOT NULL,  -- JSON
    metadata TEXT,  -- JSON
    INDEX idx_type (type),
    INDEX idx_correlation (correlation_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_project (json_extract(data, '$.project_id'))
);
```

---

### 6.2 Event Bus

**Purpose:** Async message routing with priority queue.

**Implementation:**
```python
class EventBus:
    """Asynchronous event bus with priority queue"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.priority_queue = PriorityQueue()
        self.subscriptions: Dict[str, List[str]] = {}
        self.handlers: Dict[str, Callable] = {}
    
    async def publish(self, event: BaseEvent) -> None:
        """Publish event to bus"""
        # 1. Store event
        await self.event_store.append(event)
        
        # 2. Add to priority queue
        self.priority_queue.enqueue(event)
        
        # 3. Notify subscribers
        await self._notify_subscribers(event)
    
    def subscribe(self, component: str, event_types: List[str]) -> None:
        """Subscribe component to event types"""
        self.subscriptions[component] = event_types
    
    def register_handler(self, component: str, handler: Callable) -> None:
        """Register event handler for component"""
        self.handlers[component] = handler
    
    async def _notify_subscribers(self, event: BaseEvent) -> None:
        """Notify all subscribers of event"""
        for component, event_types in self.subscriptions.items():
            if event.type in event_types or event.target == component:
                handler = self.handlers.get(component)
                if handler:
                    await handler(event)
    
    async def process_queue(self) -> None:
        """Process events from priority queue"""
        while True:
            event = self.priority_queue.dequeue()
            if event:
                await self._route_event(event)
            else:
                await asyncio.sleep(0.1)
    
    async def _route_event(self, event: BaseEvent) -> None:
        """Route event to target(s)"""
        targets = event.target if isinstance(event.target, list) else [event.target]
        for target in targets:
            handler = self.handlers.get(target)
            if handler:
                await handler(event)
```

---

### 6.3 Pydantic Models

**Validation Rules:**
```python
from pydantic import BaseModel, Field, validator

class ProjectCreatedData(BaseModel):
    project_id: str = Field(..., regex=r'^proj-[a-z0-9]{8}$')
    client_name: str = Field(..., min_length=1, max_length=200)
    client_domain: str = Field(..., regex=r'^[a-z0-9.-]+\.[a-z]{2,}$')
    client_contact: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    industry: str = Field(..., min_length=1)
    
    @validator('client_domain')
    def validate_domain(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v
```

**Serialization:**
```python
# To JSON
event_json = event.model_dump_json()

# From JSON
event = ProjectCreatedEvent.model_validate_json(event_json)

# To dict
event_dict = event.model_dump()

# From dict
event = ProjectCreatedEvent.model_validate(event_dict)
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Test Event Schemas:**
```python
def test_project_created_event_validation():
    """Test ProjectCreatedEvent validation"""
    # Valid event
    event = ProjectCreatedEvent(
        source="operator",
        target="operator",
        data=ProjectCreatedData(
            project_id="proj-abc12345",
            client_name="Test Client",
            client_domain="example.com",
            client_contact="test@example.com",
            industry="Healthcare"
        )
    )
    assert event.type == "project.created"
    assert event.priority == 1
    
    # Invalid event (bad email)
    with pytest.raises(ValidationError):
        ProjectCreatedEvent(
            source="operator",
            target="operator",
            data=ProjectCreatedData(
                project_id="proj-abc12345",
                client_name="Test Client",
                client_domain="example.com",
                client_contact="invalid-email",
                industry="Healthcare"
            )
        )
```

**Test Priority Queue:**
```python
def test_priority_queue_ordering():
    """Test events processed by priority"""
    queue = PriorityQueue()
    
    # Add events with different priorities
    queue.enqueue(BaseEvent(priority=2, type="normal"))
    queue.enqueue(BaseEvent(priority=0, type="critical"))
    queue.enqueue(BaseEvent(priority=1, type="high"))
    
    # Should dequeue in priority order
    assert queue.dequeue().type == "critical"
    assert queue.dequeue().type == "high"
    assert queue.dequeue().type == "normal"
```

---

### 7.2 Integration Tests

**Test Event Flow:**
```python
@pytest.mark.asyncio
async def test_pre_sale_flow():
    """Test complete Pre-Sale phase flow"""
    event_bus = EventBus(event_store)
    operator = Operator(event_bus)
    
    # 1. Create project
    await operator.create_project(
        client_name="Test Client",
        client_domain="example.com",
        client_contact="test@example.com",
        industry="Healthcare"
    )
    
    # 2. Verify ProjectCreatedEvent emitted
    events = await event_store.get_by_type("project.created")
    assert len(events) == 1
    assert events[0].data.client_name == "Test Client"
    
    # 3. Verify TaskCreatedEvents for Magisters
    task_events = await event_store.get_by_type("task.created")
    assert len(task_events) > 0
    
    # 4. Simulate Magister completions
    for task_event in task_events:
        await event_bus.publish(TaskCompletedEvent(
            source=task_event.data.magister,
            target="operator",
            data=TaskCompletedData(
                project_id=task_event.data.project_id,
                task_id=task_event.data.task_id,
                magister=task_event.data.magister,
                result={"status": "success"}
            )
        ))
    
    # 5. Verify ProposalGenerationStartedEvent
    proposal_events = await event_store.get_by_type("project.proposal.generation_started")
    assert len(proposal_events) == 1
```

**Test Inter-Magister Communication:**
```python
@pytest.mark.asyncio
async def test_magister_data_request():
    """Test Magister requesting data from another Magister"""
    event_bus = EventBus(event_store)
    content_magister = ContentMagister(event_bus)
    brand_magister = BrandMagister(event_bus)
    
    # 1. Content Magister requests ToV
    request = await content_magister.request_tone_of_voice(
        project_id="proj-test123"
    )
    
    # 2. Verify request event
    request_events = await event_store.get_by_type("magister.request.data")
    assert len(request_events) == 1
    assert request_events[0].data.data_type == "tone_of_voice"
    
    # 3. Brand Magister responds
    await brand_magister.handle_data_request(request_events[0])
    
    # 4. Verify response event
    response_events = await event_store.get_by_type("magister.response.data")
    assert len(response_events) == 1
    assert response_events[0].reply_to == request_events[0].id
```

---

### 7.3 End-to-End Tests

**Test Complete Project Lifecycle:**
```python
@pytest.mark.asyncio
async def test_complete_project_lifecycle():
    """Test project from Pre-Sale to Active Work"""
    system = System()
    
    # Phase -1: Pre-Sale
    project = await system.create_project(...)
    await system.run_pre_sale_analysis(project.id)
    await system.generate_proposal(project.id)
    await system.send_proposal(project.id)
    
    # Phase 0: Setup
    await system.sign_contract(project.id)
    await system.setup_infrastructure(project.id)
    
    # Phase 1: Baseline
    await system.collect_baseline(project.id)
    
    # Phase 1.5: Strategy Planning
    await system.plan_strategy(project.id)
    await system.approve_strategy(project.id)
    
    # Phase 2: Active Work
    sprint = await system.plan_sprint(project.id, sprint_number=1)
    await system.execute_sprint(sprint.id)
    await system.review_sprint(sprint.id)
    
    # Verify all phases completed
    events = await system.event_store.get_by_project(project.id)
    assert any(e.type == "project.created" for e in events)
    assert any(e.type == "project.setup.completed" for e in events)
    assert any(e.type == "project.baseline.aggregation_completed" for e in events)
    assert any(e.type == "project.strategy.approved" for e in events)
    assert any(e.type == "project.sprint.completed" for e in events)
```

---


## 8. Future Enhancements

### 8.1 Financial Intelligence Agent Events

**Note:** Financial Intelligence Agent specification to be created separately.

**Proposed Events:**
```python
class FinancialAnalysisStartedEvent(BaseEvent):
    """Financial analysis started"""
    type: Literal["financial.analysis.started"]
    data: FinancialAnalysisStartedData

class FinancialAnalysisStartedData(BaseModel):
    project_id: str
    company_name: str
    inn: str  # Russian tax ID
    data_sources: List[str]  # ["spark", "kontour", "public"]

class FinancialDataCollectedEvent(BaseEvent):
    """Financial data collected"""
    type: Literal["financial.data.collected"]
    data: FinancialDataCollectedData

class FinancialDataCollectedData(BaseModel):
    project_id: str
    source: str
    metrics: Dict[str, Any]
    financial_health_score: float  # 0-100
    market_position: str
```

---

### 8.2 Advanced Analytics Events

**Proposed Events:**
```python
class AnalyticsInsightGeneratedEvent(BaseEvent):
    """Analytics insight generated"""
    type: Literal["analytics.insight.generated"]
    data: AnalyticsInsightData

class AnalyticsInsightData(BaseModel):
    project_id: str
    insight_type: str  # "correlation", "anomaly", "trend"
    description: str
    confidence: float  # 0-1
    recommended_actions: List[str]

class AnalyticsAnomalyDetectedEvent(BaseEvent):
    """Anomaly detected in metrics"""
    type: Literal["analytics.anomaly.detected"]
    data: AnalyticsAnomalyData

class AnalyticsAnomalyData(BaseModel):
    project_id: str
    metric: str
    expected_value: float
    actual_value: float
    deviation_percent: float
    severity: Literal["low", "medium", "high"]
```

---

### 8.3 Multi-Project Coordination

**Proposed Events:**
```python
class CrossProjectInsightEvent(BaseEvent):
    """Insight from multiple projects"""
    type: Literal["system.cross_project.insight"]
    data: CrossProjectInsightData

class CrossProjectInsightData(BaseModel):
    insight_type: str
    affected_projects: List[str]
    description: str
    recommended_actions: Dict[str, List[str]]  # project_id -> actions

class ResourceAllocationEvent(BaseEvent):
    """Resource allocation across projects"""
    type: Literal["system.resource.allocation"]
    data: ResourceAllocationData

class ResourceAllocationData(BaseModel):
    resource_type: str  # "magister", "api_quota", "budget"
    allocations: Dict[str, float]  # project_id -> amount
    reason: str
```

---

## Appendix A: Complete Event Catalog

### Project Lifecycle Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| project.created | P1 | Pre-Sale | New project created |
| project.status.changed | P1 | All | Project status changed |
| project.proposal.generation_started | P1 | Pre-Sale | Proposal generation started |
| project.setup.started | P1 | Setup | Infrastructure setup started |
| project.setup.completed | P1 | Setup | Infrastructure setup completed |
| project.baseline.started | P1 | Baseline | Baseline collection started |
| project.baseline.aggregation_completed | P1 | Baseline | Baseline aggregation completed |
| project.strategy.planning_started | P1 | Strategy | Strategy planning started |
| project.strategy.proposal_ready | P1 | Strategy | Strategy proposal ready |
| project.strategy.review_requested | P1 | Strategy | Strategy review requested |
| project.strategy.modified | P1 | Strategy | Strategy modified |
| project.strategy.approved | P1 | Strategy | Strategy approved |
| project.communication.recorded | P2 | All | Client communication recorded |

### Sprint Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| project.sprint.planning_started | P1 | Active | Sprint planning started |
| project.sprint.plan_created | P1 | Active | Sprint plan created |
| project.sprint.approved | P1 | Active | Sprint approved by client |
| project.sprint.review_started | P1 | Active | Sprint review started |
| project.sprint.report_generated | P1 | Active | Sprint report generated |
| project.sprint.retrospective_started | P2 | Active | Sprint retrospective started |
| project.sprint.lessons_learned | P2 | Active | Sprint lessons learned |
| project.sprint.completed | P1 | Active | Sprint completed |

### Task Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| task.created | P2 | All | Task created |
| task.assigned | P2 | Active | Task assigned to Magister |
| task.started | P2 | Active | Task execution started |
| task.progress | P2 | Active | Task progress update |
| task.completed | P2 | Active | Task completed |
| task.failed | P1 | Active | Task failed |
| task.blocked | P2 | Active | Task blocked by dependency |

### Data Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| data.baseline.collected | P2 | Baseline | Baseline data collected |
| data.version.created | P2 | All | Data version created |
| data.version.compared | P2 | All | Data versions compared |
| data.version.archived | P3 | All | Data version archived |

### Magister Communication Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| magister.request.data | P2 | Active | Magister requests data |
| magister.response.data | P2 | Active | Magister responds with data |
| magister.dependency.blocked | P2 | Active | Magister blocked by dependency |
| magister.dependency.resolved | P2 | Active | Dependency resolved |

### Client Interaction Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| client.approval.requested | P1 | All | Approval requested from client |
| client.approval.approved | P1 | All | Client approved deliverable |
| client.approval.rejected | P1 | All | Client rejected deliverable |
| client.approval.revision_requested | P1 | All | Client requested revisions |
| client.review.requested | P1 | Active | Client review requested |
| client.feedback.received | P1 | Active | Client feedback received |

### Error Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| error.occurred | P0/P1 | All | Error occurred |
| error.retry_attempted | P1 | All | Retry attempted |
| error.resolved | P2 | All | Error resolved |
| error.escalated | P0 | All | Error escalated |

### System Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| system.health.check | P3 | All | System health check |
| system.performance.degraded | P1 | All | Performance degraded |
| system.resource.low | P1 | All | Resource running low |
| system.agent.unresponsive | P0 | All | Agent not responding |
| system.rollback.initiated | P0 | All | Rollback initiated |
| system.rollback.completed | P0 | All | Rollback completed |

### Reminder Events

| Event Type | Priority | Phase | Description |
|------------|----------|-------|-------------|
| reminder.scheduled | P3 | Pre-Sale | Reminder scheduled |

---

## Appendix B: Flow Diagrams

### B.1 Pre-Sale Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase -1: Pre-Sale                                          │
└─────────────────────────────────────────────────────────────┘

YOU
 │
 ├─> ProjectCreatedEvent (status=lead)
 │
 v
Operator
 │
 ├─> Multiple TaskCreatedEvents
 │   ├─> SEO Magister (competitor analysis)
 │   ├─> Content Magister (content audit)
 │   ├─> Brand Magister (CustDev)
 │   ├─> Intelligence Magister (market research)
 │   └─> Analytics Magister (public data)
 │
 v
Magisters execute tasks
 │
 ├─> Multiple TaskCompletedEvents
 │
 v
Operator aggregates results
 │
 ├─> ProposalGenerationStartedEvent
 │
 v
Proposal ready
 │
 ├─> ProjectStatusChangedEvent (status=proposal_sent)
 │
 v
Wait for client response
 │
 ├─> If no response after 1 month: ReminderEvent
 ├─> If no response after 2 months: ReminderEvent
 └─> If no response after 3 months: ReminderEvent
 │
 v
Client responds
 │
 ├─> If accepted: ProjectStatusChangedEvent (status=contract_signed)
 └─> If rejected: ProjectStatusChangedEvent (status=closed_lost)
```

### B.2 Setup Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 0: Setup                                              │
└─────────────────────────────────────────────────────────────┘

Contract signed
 │
 ├─> ProjectStatusChangedEvent (status=setup)
 │
 v
Operator
 │
 ├─> InfrastructureSetupStartedEvent
 │
 v
Create infrastructure
 │
 ├─> Create Obsidian vaults for each Magister
 ├─> Create project folders
 ├─> Connect APIs (Analytics, Ads, etc.)
 └─> Setup database tables
 │
 v
Setup complete
 │
 ├─> InfrastructureSetupCompletedEvent
 │
 v
Ready for Baseline
 │
 └─> ProjectStatusChangedEvent (status=baseline)
```

### B.3 Baseline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Baseline                                           │
└─────────────────────────────────────────────────────────────┘

Setup complete
 │
 ├─> ProjectStatusChangedEvent (status=baseline)
 │
 v
Operator
 │
 ├─> BaselineCollectionStartedEvent
 │
 v
Magisters collect data
 │
 ├─> SEO Magister: BaselineDataCollectedEvent (rankings, keywords)
 ├─> Content Magister: BaselineDataCollectedEvent (content audit)
 ├─> Ads Magister: BaselineDataCollectedEvent (campaigns, spend)
 └─> Analytics Magister: BaselineDataCollectedEvent (traffic, conversions)
 │
 v
Analytics Magister aggregates
 │
 ├─> BaselineAggregationCompletedEvent
 │
 v
Baseline stored in vaults
 │
 v
Ready for Strategy
 │
 └─> ProjectStatusChangedEvent (status=strategy_planning)
```

### B.4 Strategy Planning Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1.5: Strategy Planning                                │
└─────────────────────────────────────────────────────────────┘

Baseline complete
 │
 ├─> ProjectStatusChangedEvent (status=strategy_planning)
 │
 v
Operator
 │
 ├─> StrategyPlanningStartedEvent
 │
 v
Magisters contribute to strategy
 │
 v
Strategy document created
 │
 ├─> StrategyProposalReadyEvent (version 1.0)
 │
 v
Request client review
 │
 ├─> StrategyReviewRequestedEvent
 │
 v
Client meeting
 │
 ├─> ClientCommunicationRecordedEvent
 │
 v
Client feedback
 │
 ├─> If changes needed: StrategyModifiedEvent (version 1.1)
 │   └─> Loop back to review
 │
 └─> If approved: StrategyApprovedEvent
     │
     v
     Ready for execution
     │
     └─> ProjectStatusChangedEvent (status=active)
```

### B.5 Sprint Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Active Work (Sprint)                               │
└─────────────────────────────────────────────────────────────┘

Strategy approved
 │
 ├─> ProjectStatusChangedEvent (status=active)
 │
 v
┌─────────────────────────────────────────────────────────────┐
│ 2.1 Sprint Planning                                         │
└─────────────────────────────────────────────────────────────┘
Operator
 │
 ├─> SprintPlanningStartedEvent
 │
 v
Create sprint plan
 │
 ├─> SprintPlanCreatedEvent
 │
 v
Client approves
 │
 ├─> SprintApprovedEvent
 │
 v
┌─────────────────────────────────────────────────────────────┐
│ 2.2 Task Execution                                          │
└─────────────────────────────────────────────────────────────┘
Operator assigns tasks
 │
 ├─> Multiple TaskAssignedEvents
 │
 v
Magisters execute
 │
 ├─> TaskStartedEvent
 ├─> TaskProgressEvent (periodic updates)
 ├─> TaskCompletedEvent (with deliverables)
 │   OR
 ├─> TaskFailedEvent (if error)
 │   OR
 └─> TaskBlockedEvent (if dependency)
 │
 v
┌─────────────────────────────────────────────────────────────┐
│ 2.3 Sprint Review                                           │
└─────────────────────────────────────────────────────────────┘
Operator
 │
 ├─> SprintReviewStartedEvent
 │
 v
Generate report
 │
 ├─> SprintReportGeneratedEvent
 │
 v
Request client review
 │
 ├─> ClientReviewRequestedEvent
 │
 v
Client provides feedback
 │
 ├─> ClientFeedbackReceivedEvent
 │
 v
┌─────────────────────────────────────────────────────────────┐
│ 2.4 Sprint Retrospective                                    │
└─────────────────────────────────────────────────────────────┘
Operator
 │
 ├─> SprintRetrospectiveStartedEvent
 │
 v
Record lessons learned
 │
 ├─> SprintLessonsLearnedEvent
 │
 v
Sprint complete
 │
 ├─> SprintCompletedEvent
 │
 v
Plan next sprint or close project
```

### B.6 Inter-Magister Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Inter-Magister Communication                                │
└─────────────────────────────────────────────────────────────┘

Content Magister needs Tone of Voice
 │
 ├─> MagisterDataRequestEvent
 │   - requesting_magister: "content_magister"
 │   - target_magister: "brand_magister"
 │   - data_type: "tone_of_voice"
 │   - correlation_id: "chain-123"
 │
 v
Brand Magister receives request
 │
 ├─> Processes request
 │
 v
Brand Magister responds
 │
 ├─> MagisterDataResponseEvent
 │   - reply_to: request event ID
 │   - correlation_id: "chain-123"
 │   - data: {tone_of_voice: {...}}
 │
 v
Content Magister receives response
 │
 └─> Continues task execution
```

### B.7 Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Error Handling & Recovery                                   │
└─────────────────────────────────────────────────────────────┘

Error occurs
 │
 ├─> ErrorOccurredEvent
 │   - error_type: "api_failure"
 │   - severity: "high"
 │   - retry_possible: true
 │
 v
Check retry strategy
 │
 ├─> If retryable:
 │   │
 │   ├─> ErrorRetryAttemptedEvent (attempt 1)
 │   │
 │   v
 │   Retry operation
 │   │
 │   ├─> If success: ErrorResolvedEvent
 │   │
 │   └─> If fail: ErrorRetryAttemptedEvent (attempt 2)
 │       │
 │       └─> Repeat up to max_retries
 │
 └─> If max retries exceeded or not retryable:
     │
     ├─> ErrorEscalatedEvent
     │   - escalated_to: "operator" or "user"
     │
     v
     If critical error affecting project state:
     │
     ├─> RollbackInitiatedEvent
     │
     v
     Restore from snapshot
     │
     └─> RollbackCompletedEvent
```

---

## Appendix C: Data Model Reference

### Core Enums

```python
class ProjectStatus(str, Enum):
    LEAD = "lead"
    PRE_SALE = "pre-sale"
    PROPOSAL_SENT = "proposal_sent"
    PROPOSAL_FOLLOW_UP = "proposal_follow_up"
    CONTRACT_SIGNED = "contract_signed"
    SETUP = "setup"
    BASELINE = "baseline"
    STRATEGY_PLANNING = "strategy_planning"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class ErrorType(str, Enum):
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    API_FAILURE = "api_failure"
    DATA_MISSING = "data_missing"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    UNKNOWN = "unknown"

class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### Common Data Models

```python
class SprintTask(BaseModel):
    task_id: str
    magister: str
    capability: str
    description: str
    estimated_hours: float
    priority: int
    dependencies: List[str]

class Deliverable(BaseModel):
    type: str
    title: str
    description: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    requires_approval: bool = True

class ComponentHealth(BaseModel):
    component: str
    status: Literal["healthy", "degraded", "critical", "offline"]
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    last_activity: Optional[datetime] = None

class DataDifference(BaseModel):
    field: str
    old_value: Any
    new_value: Any
    change_type: Literal["added", "removed", "modified"]
    significance: Literal["minor", "major", "critical"]
```

---

## Conclusion

This specification defines a comprehensive Event Bus architecture for the meAI system, covering all project lifecycle phases from Pre-Sale to Active Work. The architecture provides:

✅ **Strict typing** with Pydantic for data validation  
✅ **Priority-based routing** for critical event handling  
✅ **Comprehensive error handling** with retry and rollback  
✅ **Inter-Magister communication** for data dependencies  
✅ **Client approval workflow** for deliverables  
✅ **System monitoring** for health and performance  
✅ **Data versioning** for baseline management  
✅ **Audit trail** through immutable Event Store  
✅ **Testability** at unit, integration, and E2E levels

**Next Steps:**
1. Implement Event Store (SQLite + async)
2. Implement Event Bus (priority queue + subscriptions)
3. Implement Pydantic event models
4. Write unit tests for event schemas
5. Write integration tests for event flows
6. Implement Magisters with event handlers
7. Write E2E tests for complete lifecycle

---

**Document Version:** 1.0  
**Date:** 2026-05-08  
**Status:** Design Complete, Ready for Implementation  
**Author:** meAI Architect

