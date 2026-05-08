# Event Schemas & Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all Pydantic event models and data schemas for the Event Bus architecture

**Architecture:** Strict typing with Pydantic v2, organized by event categories (project, task, data, magister, client, system, error), with base models and enums for reusability

**Tech Stack:** Python 3.11+, Pydantic v2, typing module

---

## File Structure

**New files to create:**
```
src/meai/events/
├── __init__.py                    # Export all events
├── base.py                        # BaseEvent, enums
├── project_events.py              # Project lifecycle events
├── task_events.py                 # Task execution events
├── data_events.py                 # Data collection events
├── magister_events.py             # Inter-magister communication
├── client_events.py               # Client interaction events
├── system_events.py               # System monitoring events
└── error_events.py                # Error handling events
```

**Existing files to modify:**
- None (all new files)

---

## Task 1: Base Event Model & Enums

**Files:**
- Create: `src/meai/events/base.py`

- [ ] **Step 1: Write test for BaseEvent model**

Create: `tests/events/test_base.py`

```python
import pytest
from datetime import datetime
from pydantic import ValidationError
from meai.events.base import BaseEvent, ProjectStatus, ErrorType, ErrorSeverity


def test_base_event_creation():
    """Test BaseEvent can be created with required fields"""
    event = BaseEvent(
        type="test.event",
        source="test_source",
        target="test_target"
    )
    
    assert event.type == "test.event"
    assert event.source == "test_source"
    assert event.target == "test_target"
    assert event.priority == 2  # Default P2
    assert isinstance(event.id, str)
    assert isinstance(event.timestamp, datetime)


def test_base_event_with_correlation():
    """Test BaseEvent with correlation_id and reply_to"""
    event = BaseEvent(
        type="test.event",
        source="source",
        target="target",
        correlation_id="chain-123",
        reply_to="req-456"
    )
    
    assert event.correlation_id == "chain-123"
    assert event.reply_to == "req-456"


def test_base_event_priority_levels():
    """Test all priority levels"""
    for priority in [0, 1, 2, 3]:
        event = BaseEvent(
            type="test",
            source="src",
            target="tgt",
            priority=priority
        )
        assert event.priority == priority


def test_base_event_multiple_targets():
    """Test BaseEvent with list of targets"""
    event = BaseEvent(
        type="test",
        source="src",
        target=["target1", "target2", "target3"]
    )
    
    assert isinstance(event.target, list)
    assert len(event.target) == 3


def test_project_status_enum():
    """Test ProjectStatus enum values"""
    assert ProjectStatus.LEAD == "lead"
    assert ProjectStatus.PRE_SALE == "pre-sale"
    assert ProjectStatus.PROPOSAL_SENT == "proposal_sent"
    assert ProjectStatus.CONTRACT_SIGNED == "contract_signed"
    assert ProjectStatus.ACTIVE == "active"
    assert ProjectStatus.CLOSED_WON == "closed_won"
    assert ProjectStatus.CLOSED_LOST == "closed_lost"


def test_error_type_enum():
    """Test ErrorType enum values"""
    assert ErrorType.VALIDATION == "validation"
    assert ErrorType.TIMEOUT == "timeout"
    assert ErrorType.API_FAILURE == "api_failure"
    assert ErrorType.NETWORK == "network"


def test_error_severity_enum():
    """Test ErrorSeverity enum values"""
    assert ErrorSeverity.LOW == "low"
    assert ErrorSeverity.MEDIUM == "medium"
    assert ErrorSeverity.HIGH == "high"
    assert ErrorSeverity.CRITICAL == "critical"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_base.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'meai.events.base'"

- [ ] **Step 3: Create base.py with BaseEvent and enums**

Create: `src/meai/events/base.py`

```python
"""Base event model and enums for Event Bus"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from uuid import uuid4
from enum import Enum


class BaseEvent(BaseModel):
    """Base event model for all events in the system
    
    All events inherit from this base class and add their specific data.
    
    Attributes:
        id: Unique event identifier (auto-generated UUID)
        type: Event type in format "category.action.status"
        source: Component that emitted the event
        target: Target component(s) - single string or list
        priority: Priority level (0=P0 critical, 1=P1 high, 2=P2 normal, 3=P3 low)
        timestamp: Event creation timestamp (auto-generated)
        correlation_id: Links related events in a chain
        reply_to: For request/response pattern, ID of request event
        metadata: Optional additional metadata
    """
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str  # Format: "category.action.status"
    
    # Routing
    source: str  # Component that emitted the event
    target: Union[str, List[str]]  # Target component(s)
    priority: int = 2  # 0=P0 (critical), 1=P1 (high), 2=P2 (normal), 3=P3 (low)
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Correlation
    correlation_id: Optional[str] = None  # Links related events
    reply_to: Optional[str] = None  # For request/response pattern
    
    # Extensibility
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectStatus(str, Enum):
    """Project status enum"""
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
    """Error type enum"""
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    API_FAILURE = "api_failure"
    DATA_MISSING = "data_missing"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity enum"""
    LOW = "low"  # Can be ignored
    MEDIUM = "medium"  # Should be logged
    HIGH = "high"  # Requires retry
    CRITICAL = "critical"  # Requires escalation
```

- [ ] **Step 4: Create tests directory structure**

```bash
mkdir -p tests/events
touch tests/events/__init__.py
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/events/test_base.py -v
```

Expected: PASS (all tests green)

- [ ] **Step 6: Commit**

```bash
git add src/meai/events/base.py tests/events/test_base.py tests/events/__init__.py
git commit -m "feat(events): add BaseEvent model and core enums

- Add BaseEvent with id, type, source, target, priority
- Add correlation_id and reply_to for request/response pattern
- Add ProjectStatus enum (12 statuses)
- Add ErrorType enum (8 types)
- Add ErrorSeverity enum (4 levels)
- Add comprehensive tests for base models"
```

---

## Task 2: Project Lifecycle Events

**Files:**
- Create: `src/meai/events/project_events.py`
- Create: `tests/events/test_project_events.py`

- [ ] **Step 1: Write tests for project events**

Create: `tests/events/test_project_events.py`

```python
import pytest
from datetime import datetime
from pydantic import ValidationError
from meai.events.project_events import (
    ProjectCreatedEvent,
    ProjectCreatedData,
    InfrastructureSetupStartedEvent,
    InfrastructureSetupStartedData,
    SetupTask,
    InfrastructureSetupCompletedEvent,
    InfrastructureSetupCompletedData,
    BaselineCollectionStartedEvent,
    BaselineCollectionStartedData,
    BaselineTask,
    BaselineDataCollectedEvent,
    BaselineDataCollectedData,
    BaselineAggregationCompletedEvent,
    BaselineAggregationCompletedData,
    StrategyPlanningStartedEvent,
    StrategyPlanningStartedData,
    StrategyProposalReadyEvent,
    StrategyProposalReadyData,
    StrategyReviewRequestedEvent,
    StrategyReviewRequestedData,
    StrategyModifiedEvent,
    StrategyModifiedData,
    StrategyModification,
    StrategyApprovedEvent,
    StrategyApprovedData,
)
from meai.events.base import ProjectStatus


def test_project_created_event():
    """Test ProjectCreatedEvent creation"""
    data = ProjectCreatedData(
        project_id="proj-abc12345",
        client_name="Test Client",
        client_domain="example.com",
        client_contact="test@example.com",
        industry="Healthcare",
        source="inbound",
        created_at=datetime.utcnow()
    )
    
    event = ProjectCreatedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.created"
    assert event.priority == 1  # P1 - High
    assert event.data.client_name == "Test Client"
    assert event.data.initial_status == ProjectStatus.LEAD


def test_project_created_data_validation():
    """Test ProjectCreatedData validation"""
    # Valid data
    data = ProjectCreatedData(
        project_id="proj-test123",
        client_name="Client",
        client_domain="test.com",
        client_contact="email@test.com",
        industry="Tech",
        source="outbound",
        created_at=datetime.utcnow()
    )
    assert data.client_name == "Client"
    
    # Invalid email should fail
    with pytest.raises(ValidationError):
        ProjectCreatedData(
            project_id="proj-test",
            client_name="Client",
            client_domain="test.com",
            client_contact="invalid-email",
            industry="Tech",
            source="inbound",
            created_at=datetime.utcnow()
        )


def test_infrastructure_setup_started_event():
    """Test InfrastructureSetupStartedEvent"""
    tasks = [
        SetupTask(
            task_type="vault",
            description="Create SEO Magister vault",
            magister="seo_magister"
        ),
        SetupTask(
            task_type="api_connection",
            description="Connect Google Analytics API"
        )
    ]
    
    data = InfrastructureSetupStartedData(
        project_id="proj-test",
        setup_tasks=tasks,
        estimated_completion=datetime.utcnow()
    )
    
    event = InfrastructureSetupStartedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.setup.started"
    assert event.priority == 1
    assert len(event.data.setup_tasks) == 2


def test_infrastructure_setup_completed_event():
    """Test InfrastructureSetupCompletedEvent"""
    data = InfrastructureSetupCompletedData(
        project_id="proj-test",
        completed_at=datetime.utcnow(),
        created_vaults=["seo_magister", "content_magister"],
        created_folders=["data", "reports"],
        connected_apis=["google_analytics", "yandex_metrika"],
        ready_for_baseline=True
    )
    
    event = InfrastructureSetupCompletedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.setup.completed"
    assert event.data.ready_for_baseline is True


def test_baseline_collection_started_event():
    """Test BaselineCollectionStartedEvent"""
    tasks = [
        BaselineTask(
            magister="seo_magister",
            data_source="google_search_console",
            metrics=["rankings", "clicks", "impressions"],
            time_range="last_90_days"
        )
    ]
    
    data = BaselineCollectionStartedData(
        project_id="proj-test",
        baseline_type="initial",
        collection_tasks=tasks,
        estimated_completion=datetime.utcnow()
    )
    
    event = BaselineCollectionStartedEvent(
        source="operator",
        target=["seo_magister", "content_magister"],
        data=data
    )
    
    assert event.type == "project.baseline.started"
    assert event.data.baseline_type == "initial"


def test_baseline_data_collected_event():
    """Test BaselineDataCollectedEvent"""
    data = BaselineDataCollectedData(
        project_id="proj-test",
        magister="seo_magister",
        data_source="google_analytics",
        metrics={"traffic": 10000, "bounce_rate": 0.45},
        time_range="last_30_days",
        collected_at=datetime.utcnow(),
        data_quality="complete"
    )
    
    event = BaselineDataCollectedEvent(
        source="seo_magister",
        target="analytics_magister",
        data=data
    )
    
    assert event.type == "data.baseline.collected"
    assert event.data.data_quality == "complete"


def test_baseline_aggregation_completed_event():
    """Test BaselineAggregationCompletedEvent"""
    data = BaselineAggregationCompletedData(
        project_id="proj-test",
        baseline_id="baseline-001",
        baseline_type="initial",
        aggregated_metrics={"total_traffic": 50000},
        completed_at=datetime.utcnow(),
        vault_path="AIM/obsidian/analytics-magister/baselines/baseline-001.md",
        ready_for_strategy=True
    )
    
    event = BaselineAggregationCompletedEvent(
        source="analytics_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "project.baseline.aggregation_completed"
    assert event.data.ready_for_strategy is True


def test_strategy_planning_started_event():
    """Test StrategyPlanningStartedEvent"""
    data = StrategyPlanningStartedData(
        project_id="proj-test",
        baseline_id="baseline-001",
        planning_deadline=datetime.utcnow(),
        assigned_magisters=["seo_magister", "content_magister"]
    )
    
    event = StrategyPlanningStartedEvent(
        source="operator",
        target=["seo_magister", "content_magister"],
        data=data
    )
    
    assert event.type == "project.strategy.planning_started"
    assert len(event.data.assigned_magisters) == 2


def test_strategy_proposal_ready_event():
    """Test StrategyProposalReadyEvent"""
    data = StrategyProposalReadyData(
        project_id="proj-test",
        strategy_id="strategy-001",
        version="1.0",
        strategy_document_path="strategies/strategy-001-v1.0.md",
        key_recommendations=["Improve SEO", "Create content calendar"],
        estimated_budget=50000.0,
        estimated_timeline_months=6,
        created_at=datetime.utcnow()
    )
    
    event = StrategyProposalReadyEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.strategy.proposal_ready"
    assert event.data.version == "1.0"


def test_strategy_review_requested_event():
    """Test StrategyReviewRequestedEvent"""
    data = StrategyReviewRequestedData(
        project_id="proj-test",
        strategy_id="strategy-001",
        version="1.0",
        review_deadline=datetime.utcnow()
    )
    
    event = StrategyReviewRequestedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.strategy.review_requested"


def test_strategy_modified_event():
    """Test StrategyModifiedEvent"""
    modifications = [
        StrategyModification(
            section="SEO Strategy",
            change_type="modified",
            description="Updated keyword targets",
            impact="minor"
        )
    ]
    
    data = StrategyModifiedData(
        project_id="proj-test",
        strategy_id="strategy-001",
        previous_version="1.0",
        new_version="1.1",
        modifications=modifications,
        modified_by="operator",
        modified_at=datetime.utcnow(),
        reason="Client feedback"
    )
    
    event = StrategyModifiedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.strategy.modified"
    assert event.data.new_version == "1.1"


def test_strategy_approved_event():
    """Test StrategyApprovedEvent"""
    data = StrategyApprovedData(
        project_id="proj-test",
        strategy_id="strategy-001",
        version="1.1",
        approved_by="client@example.com",
        approved_at=datetime.utcnow(),
        ready_for_execution=True
    )
    
    event = StrategyApprovedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.strategy.approved"
    assert event.data.ready_for_execution is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_project_events.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'meai.events.project_events'"

- [ ] **Step 3: Implement project_events.py (Part 1 - Pre-Sale & Setup)**

Create: `src/meai/events/project_events.py`

```python
"""Project lifecycle events"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from meai.events.base import BaseEvent, ProjectStatus


# ============================================================================
# Phase -1: Pre-Sale Events
# ============================================================================

class ProjectCreatedData(BaseModel):
    """Data for ProjectCreatedEvent"""
    project_id: str
    client_name: str
    client_domain: str
    client_contact: str  # Email
    industry: str
    initial_status: ProjectStatus = ProjectStatus.LEAD
    source: Literal["inbound", "outbound", "referral"]
    created_at: datetime
    notes: Optional[str] = None


class ProjectCreatedEvent(BaseEvent):
    """New project created in Pre-Sale phase"""
    type: Literal["project.created"] = "project.created"
    priority: int = 1  # P1 - High priority
    data: ProjectCreatedData


# ============================================================================
# Phase 0: Setup Events
# ============================================================================

class SetupTask(BaseModel):
    """Setup task definition"""
    task_type: Literal["vault", "folder", "api_connection", "database"]
    description: str
    magister: Optional[str] = None  # Which magister needs this


class InfrastructureSetupStartedData(BaseModel):
    """Data for InfrastructureSetupStartedEvent"""
    project_id: str
    setup_tasks: List[SetupTask]
    estimated_completion: datetime


class InfrastructureSetupStartedEvent(BaseEvent):
    """Operator started infrastructure setup"""
    type: Literal["project.setup.started"] = "project.setup.started"
    priority: int = 1  # P1 - High
    data: InfrastructureSetupStartedData


class InfrastructureSetupCompletedData(BaseModel):
    """Data for InfrastructureSetupCompletedEvent"""
    project_id: str
    completed_at: datetime
    created_vaults: List[str]
    created_folders: List[str]
    connected_apis: List[str]
    ready_for_baseline: bool


class InfrastructureSetupCompletedEvent(BaseEvent):
    """Infrastructure setup completed"""
    type: Literal["project.setup.completed"] = "project.setup.completed"
    priority: int = 1  # P1 - High
    data: InfrastructureSetupCompletedData


# ============================================================================
# Phase 1: Baseline Events
# ============================================================================

class BaselineTask(BaseModel):
    """Baseline collection task"""
    magister: str
    data_source: str  # "google_analytics", "yandex_metrika", etc.
    metrics: List[str]
    time_range: str  # "last_30_days", "last_90_days", etc.


class BaselineCollectionStartedData(BaseModel):
    """Data for BaselineCollectionStartedEvent"""
    project_id: str
    baseline_type: Literal["initial", "monthly", "quarterly"]
    collection_tasks: List[BaselineTask]
    estimated_completion: datetime


class BaselineCollectionStartedEvent(BaseEvent):
    """Baseline data collection started"""
    type: Literal["project.baseline.started"] = "project.baseline.started"
    priority: int = 1  # P1 - High
    data: BaselineCollectionStartedData


class BaselineDataCollectedData(BaseModel):
    """Data for BaselineDataCollectedEvent"""
    project_id: str
    magister: str
    data_source: str
    metrics: Dict[str, Any]
    time_range: str
    collected_at: datetime
    data_quality: Literal["complete", "partial", "failed"]
    notes: Optional[str] = None


class BaselineDataCollectedEvent(BaseEvent):
    """Magister collected baseline data"""
    type: Literal["data.baseline.collected"] = "data.baseline.collected"
    priority: int = 2  # P2 - Normal
    data: BaselineDataCollectedData


class BaselineAggregationCompletedData(BaseModel):
    """Data for BaselineAggregationCompletedEvent"""
    project_id: str
    baseline_id: str
    baseline_type: Literal["initial", "monthly", "quarterly"]
    aggregated_metrics: Dict[str, Any]
    completed_at: datetime
    vault_path: str  # Where baseline is stored
    ready_for_strategy: bool


class BaselineAggregationCompletedEvent(BaseEvent):
    """All baseline data aggregated"""
    type: Literal["project.baseline.aggregation_completed"] = "project.baseline.aggregation_completed"
    priority: int = 1  # P1 - High
    data: BaselineAggregationCompletedData


# ============================================================================
# Phase 1.5: Strategy Planning Events
# ============================================================================

class StrategyPlanningStartedData(BaseModel):
    """Data for StrategyPlanningStartedEvent"""
    project_id: str
    baseline_id: str  # Which baseline to use
    planning_deadline: datetime
    assigned_magisters: List[str]


class StrategyPlanningStartedEvent(BaseEvent):
    """Strategy planning phase started"""
    type: Literal["project.strategy.planning_started"] = "project.strategy.planning_started"
    priority: int = 1  # P1 - High
    data: StrategyPlanningStartedData


class StrategyProposalReadyData(BaseModel):
    """Data for StrategyProposalReadyEvent"""
    project_id: str
    strategy_id: str
    version: str  # "1.0"
    strategy_document_path: str
    key_recommendations: List[str]
    estimated_budget: float
    estimated_timeline_months: int
    created_at: datetime


class StrategyProposalReadyEvent(BaseEvent):
    """Strategy proposal ready for review"""
    type: Literal["project.strategy.proposal_ready"] = "project.strategy.proposal_ready"
    priority: int = 1  # P1 - High
    data: StrategyProposalReadyData


class StrategyReviewRequestedData(BaseModel):
    """Data for StrategyReviewRequestedEvent"""
    project_id: str
    strategy_id: str
    version: str
    review_deadline: datetime
    meeting_scheduled: Optional[datetime] = None


class StrategyReviewRequestedEvent(BaseEvent):
    """Strategy review requested from client"""
    type: Literal["project.strategy.review_requested"] = "project.strategy.review_requested"
    priority: int = 1  # P1 - High
    data: StrategyReviewRequestedData


class StrategyModification(BaseModel):
    """Strategy modification detail"""
    section: str
    change_type: Literal["added", "removed", "modified"]
    description: str
    impact: Literal["minor", "major"]


class StrategyModifiedData(BaseModel):
    """Data for StrategyModifiedEvent"""
    project_id: str
    strategy_id: str
    previous_version: str
    new_version: str
    modifications: List[StrategyModification]
    modified_by: str
    modified_at: datetime
    reason: str


class StrategyModifiedEvent(BaseEvent):
    """Strategy modified based on feedback"""
    type: Literal["project.strategy.modified"] = "project.strategy.modified"
    priority: int = 1  # P1 - High
    data: StrategyModifiedData


class StrategyApprovedData(BaseModel):
    """Data for StrategyApprovedEvent"""
    project_id: str
    strategy_id: str
    version: str
    approved_by: str
    approved_at: datetime
    comments: Optional[str] = None
    ready_for_execution: bool


class StrategyApprovedEvent(BaseEvent):
    """Strategy approved by client"""
    type: Literal["project.strategy.approved"] = "project.strategy.approved"
    priority: int = 1  # P1 - High
    data: StrategyApprovedData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_project_events.py -v
```

Expected: PASS (all tests green)

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/project_events.py tests/events/test_project_events.py
git commit -m "feat(events): add project lifecycle events

Phase -1 (Pre-Sale):
- ProjectCreatedEvent with client data

Phase 0 (Setup):
- InfrastructureSetupStartedEvent
- InfrastructureSetupCompletedEvent

Phase 1 (Baseline):
- BaselineCollectionStartedEvent
- BaselineDataCollectedEvent
- BaselineAggregationCompletedEvent

Phase 1.5 (Strategy Planning):
- StrategyPlanningStartedEvent
- StrategyProposalReadyEvent
- StrategyReviewRequestedEvent
- StrategyModifiedEvent
- StrategyApprovedEvent

All events with comprehensive tests"
```

---


## Task 3: Task Execution Events

**Files:**
- Create: `src/meai/events/task_events.py`
- Create: `tests/events/test_task_events.py`

- [ ] **Step 1: Write tests for task events**

Create: `tests/events/test_task_events.py`

```python
import pytest
from datetime import datetime
from meai.events.task_events import (
    TaskCreatedEvent,
    TaskCreatedData,
    TaskAssignedEvent,
    TaskAssignedData,
    TaskStartedEvent,
    TaskStartedData,
    TaskProgressEvent,
    TaskProgressData,
    TaskCompletedEvent,
    TaskCompletedData,
    Deliverable,
    TaskFailedEvent,
    TaskFailedData,
    TaskBlockedEvent,
    TaskBlockedData,
)


def test_task_created_event():
    """Test TaskCreatedEvent"""
    data = TaskCreatedData(
        project_id="proj-test",
        task_id="task-001",
        magister="seo_magister",
        capability="analyze_competitors",
        parameters={"domain": "example.com"},
        dependencies=[]
    )
    
    event = TaskCreatedEvent(
        source="operator",
        target="seo_magister",
        data=data
    )
    
    assert event.type == "task.created"
    assert event.priority == 2  # P2 - Normal
    assert event.data.magister == "seo_magister"


def test_task_assigned_event():
    """Test TaskAssignedEvent"""
    data = TaskAssignedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        task_id="task-001",
        magister="content_magister",
        capability="generate_content",
        parameters={"topic": "SEO Guide"},
        deadline=datetime.utcnow(),
        dependencies=[]
    )
    
    event = TaskAssignedEvent(
        source="operator",
        target="content_magister",
        data=data
    )
    
    assert event.type == "task.assigned"
    assert event.data.capability == "generate_content"


def test_task_started_event():
    """Test TaskStartedEvent"""
    data = TaskStartedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        task_id="task-001",
        magister="seo_magister",
        started_at=datetime.utcnow(),
        estimated_completion=datetime.utcnow()
    )
    
    event = TaskStartedEvent(
        source="seo_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "task.started"


def test_task_progress_event():
    """Test TaskProgressEvent"""
    data = TaskProgressData(
        project_id="proj-test",
        sprint_id="sprint-001",
        task_id="task-001",
        magister="content_magister",
        progress_percent=50,
        current_step="Writing content",
        estimated_completion=datetime.utcnow()
    )
    
    event = TaskProgressEvent(
        source="content_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "task.progress"
    assert event.data.progress_percent == 50


def test_task_completed_event():
    """Test TaskCompletedEvent"""
    deliverables = [
        Deliverable(
            type="report",
            title="SEO Analysis Report",
            description="Competitor analysis",
            file_path="reports/seo-analysis.pdf",
            requires_approval=True
        )
    ]
    
    data = TaskCompletedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        task_id="task-001",
        magister="seo_magister",
        completed_at=datetime.utcnow(),
        result={"status": "success"},
        deliverables=deliverables
    )
    
    event = TaskCompletedEvent(
        source="seo_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "task.completed"
    assert len(event.data.deliverables) == 1


def test_task_failed_event():
    """Test TaskFailedEvent"""
    data = TaskFailedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        task_id="task-001",
        magister="ads_magister",
        failed_at=datetime.utcnow(),
        error_type="api_failure",
        error_message="Google Ads API timeout",
        retry_possible=True,
        escalation_required=False
    )
    
    event = TaskFailedEvent(
        source="ads_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "task.failed"
    assert event.priority == 1  # P1 - High
    assert event.data.retry_possible is True


def test_task_blocked_event():
    """Test TaskBlockedEvent"""
    data = TaskBlockedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        task_id="task-002",
        magister="content_magister",
        blocked_by=["task-001"],
        blocked_at=datetime.utcnow()
    )
    
    event = TaskBlockedEvent(
        source="content_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "task.blocked"
    assert len(event.data.blocked_by) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_task_events.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement task_events.py**

Create: `src/meai/events/task_events.py`

```python
"""Task execution events"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from meai.events.base import BaseEvent


class Deliverable(BaseModel):
    """Task deliverable"""
    type: str  # "report", "content", "campaign", "analysis"
    title: str
    description: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    requires_approval: bool = True


# ============================================================================
# Pre-Sale & General Task Events
# ============================================================================

class TaskCreatedData(BaseModel):
    """Data for TaskCreatedEvent"""
    project_id: str
    task_id: str
    magister: str  # Target magister
    capability: str  # Capability to execute
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    dependencies: List[str] = []  # Other task_ids


class TaskCreatedEvent(BaseEvent):
    """Task created for Magister execution"""
    type: Literal["task.created"] = "task.created"
    priority: int = 2  # P2 - Normal
    data: TaskCreatedData


# ============================================================================
# Active Work (Sprint) Task Events
# ============================================================================

class TaskAssignedData(BaseModel):
    """Data for TaskAssignedEvent"""
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    capability: str
    parameters: Dict[str, Any]
    deadline: datetime
    dependencies: List[str]  # task_ids that must complete first


class TaskAssignedEvent(BaseEvent):
    """Operator assigned task to Magister"""
    type: Literal["task.assigned"] = "task.assigned"
    priority: int = 2  # P2 - Normal
    data: TaskAssignedData


class TaskStartedData(BaseModel):
    """Data for TaskStartedEvent"""
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    started_at: datetime
    estimated_completion: datetime


class TaskStartedEvent(BaseEvent):
    """Magister started task execution"""
    type: Literal["task.started"] = "task.started"
    priority: int = 2  # P2 - Normal
    data: TaskStartedData


class TaskProgressData(BaseModel):
    """Data for TaskProgressEvent"""
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    progress_percent: int  # 0-100
    current_step: str
    estimated_completion: datetime
    notes: Optional[str] = None


class TaskProgressEvent(BaseEvent):
    """Magister reports task progress"""
    type: Literal["task.progress"] = "task.progress"
    priority: int = 2  # P2 - Normal
    data: TaskProgressData


class TaskCompletedData(BaseModel):
    """Data for TaskCompletedEvent"""
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    completed_at: datetime
    result: Dict[str, Any]
    deliverables: List[Deliverable]
    next_actions: Optional[List[str]] = None


class TaskCompletedEvent(BaseEvent):
    """Magister completed task"""
    type: Literal["task.completed"] = "task.completed"
    priority: int = 2  # P2 - Normal
    data: TaskCompletedData


class TaskFailedData(BaseModel):
    """Data for TaskFailedEvent"""
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    failed_at: datetime
    error_type: str
    error_message: str
    retry_possible: bool
    escalation_required: bool


class TaskFailedEvent(BaseEvent):
    """Magister failed to complete task"""
    type: Literal["task.failed"] = "task.failed"
    priority: int = 1  # P1 - High (needs attention)
    data: TaskFailedData


class TaskBlockedData(BaseModel):
    """Data for TaskBlockedEvent"""
    project_id: str
    sprint_id: str
    task_id: str
    magister: str
    blocked_by: List[str]  # task_ids blocking this task
    blocked_at: datetime
    estimated_unblock: Optional[datetime] = None


class TaskBlockedEvent(BaseEvent):
    """Task blocked by dependency"""
    type: Literal["task.blocked"] = "task.blocked"
    priority: int = 2  # P2 - Normal
    data: TaskBlockedData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_task_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/task_events.py tests/events/test_task_events.py
git commit -m "feat(events): add task execution events

- TaskCreatedEvent (Pre-Sale phase)
- TaskAssignedEvent (Sprint phase)
- TaskStartedEvent
- TaskProgressEvent
- TaskCompletedEvent with Deliverable model
- TaskFailedEvent (P1 priority)
- TaskBlockedEvent

All events with comprehensive tests"
```

---

## Task 4: Sprint Events

**Files:**
- Create: `src/meai/events/sprint_events.py`
- Create: `tests/events/test_sprint_events.py`

- [ ] **Step 1: Write tests for sprint events**

Create: `tests/events/test_sprint_events.py`

```python
import pytest
from datetime import datetime
from meai.events.sprint_events import (
    SprintPlanningStartedEvent,
    SprintPlanningStartedData,
    SprintPlanCreatedEvent,
    SprintPlanCreatedData,
    SprintTask,
    TaskDependency,
    SprintApprovedEvent,
    SprintApprovedData,
    SprintReviewStartedEvent,
    SprintReviewStartedData,
    SprintReportGeneratedEvent,
    SprintReportGeneratedData,
    SprintSummary,
    SprintMetrics,
    SprintRetrospectiveStartedEvent,
    SprintRetrospectiveStartedData,
    SprintLessonsLearnedEvent,
    SprintLessonsLearnedData,
    ActionItem,
    SprintCompletedEvent,
    SprintCompletedData,
)
from meai.events.task_events import Deliverable


def test_sprint_planning_started_event():
    """Test SprintPlanningStartedEvent"""
    data = SprintPlanningStartedData(
        project_id="proj-test",
        sprint_number=1,
        sprint_duration_weeks=2,
        planning_deadline=datetime.utcnow(),
        strategy_version="1.0"
    )
    
    event = SprintPlanningStartedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.planning_started"
    assert event.priority == 1  # P1
    assert event.data.sprint_number == 1


def test_sprint_plan_created_event():
    """Test SprintPlanCreatedEvent"""
    tasks = [
        SprintTask(
            task_id="task-001",
            magister="seo_magister",
            capability="analyze_competitors",
            description="Analyze top 10 competitors",
            estimated_hours=8.0,
            priority=1,
            dependencies=[]
        )
    ]
    
    dependencies = [
        TaskDependency(
            task_id="task-002",
            depends_on=["task-001"],
            dependency_type="blocking"
        )
    ]
    
    data = SprintPlanCreatedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        sprint_number=1,
        tasks=tasks,
        dependencies=dependencies,
        estimated_hours=40.0,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow()
    )
    
    event = SprintPlanCreatedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.plan_created"
    assert len(event.data.tasks) == 1
    assert len(event.data.dependencies) == 1


def test_sprint_approved_event():
    """Test SprintApprovedEvent"""
    data = SprintApprovedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        approved_by="client@example.com",
        approved_at=datetime.utcnow()
    )
    
    event = SprintApprovedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.approved"


def test_sprint_review_started_event():
    """Test SprintReviewStartedEvent"""
    data = SprintReviewStartedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        sprint_number=1,
        review_date=datetime.utcnow(),
        completed_tasks=8,
        total_tasks=10
    )
    
    event = SprintReviewStartedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.review_started"
    assert event.data.completed_tasks == 8


def test_sprint_report_generated_event():
    """Test SprintReportGeneratedEvent"""
    summary = SprintSummary(
        completed_tasks=8,
        total_tasks=10,
        completion_rate=0.8,
        total_hours_spent=35.0,
        estimated_hours=40.0,
        key_achievements=["Completed competitor analysis"],
        challenges=["API rate limits"]
    )
    
    metrics = SprintMetrics(
        velocity=4.0,
        quality_score=85.0,
        magister_performance={"seo_magister": 90.0}
    )
    
    data = SprintReportGeneratedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        report_path="reports/sprint-001.md",
        summary=summary,
        deliverables=[],
        metrics=metrics
    )
    
    event = SprintReportGeneratedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.report_generated"
    assert event.data.summary.completion_rate == 0.8


def test_sprint_retrospective_started_event():
    """Test SprintRetrospectiveStartedEvent"""
    data = SprintRetrospectiveStartedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        sprint_number=1,
        retrospective_date=datetime.utcnow()
    )
    
    event = SprintRetrospectiveStartedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.retrospective_started"


def test_sprint_lessons_learned_event():
    """Test SprintLessonsLearnedEvent"""
    action_items = [
        ActionItem(
            description="Improve API error handling",
            assignee="seo_magister",
            deadline=datetime.utcnow(),
            priority=1
        )
    ]
    
    data = SprintLessonsLearnedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        what_went_well=["Good collaboration"],
        what_went_wrong=["API timeouts"],
        action_items=action_items,
        process_improvements=["Add retry logic"]
    )
    
    event = SprintLessonsLearnedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.lessons_learned"
    assert len(event.data.action_items) == 1


def test_sprint_completed_event():
    """Test SprintCompletedEvent"""
    data = SprintCompletedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        sprint_number=1,
        completed_at=datetime.utcnow(),
        next_sprint_planned=True,
        next_sprint_start=datetime.utcnow()
    )
    
    event = SprintCompletedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.sprint.completed"
    assert event.data.next_sprint_planned is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_sprint_events.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement sprint_events.py**

Create: `src/meai/events/sprint_events.py`

```python
"""Sprint execution events (Phase 2: Active Work)"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Literal
from meai.events.base import BaseEvent
from meai.events.task_events import Deliverable


# ============================================================================
# Sprint Planning (Phase 2.1)
# ============================================================================

class SprintPlanningStartedData(BaseModel):
    """Data for SprintPlanningStartedEvent"""
    project_id: str
    sprint_number: int
    sprint_duration_weeks: int
    planning_deadline: datetime
    strategy_version: str  # Which strategy version to use


class SprintPlanningStartedEvent(BaseEvent):
    """Operator started sprint planning"""
    type: Literal["project.sprint.planning_started"] = "project.sprint.planning_started"
    priority: int = 1  # P1 - High
    data: SprintPlanningStartedData


class SprintTask(BaseModel):
    """Sprint task definition"""
    task_id: str
    magister: str  # Which Magister is responsible
    capability: str  # Which capability to use
    description: str
    estimated_hours: float
    priority: int
    dependencies: List[str]  # task_ids that must complete first


class TaskDependency(BaseModel):
    """Task dependency definition"""
    task_id: str
    depends_on: List[str]  # task_ids
    dependency_type: Literal["blocking", "soft"]
    # blocking = cannot start until dependencies complete
    # soft = preferable to wait but not required


class SprintPlanCreatedData(BaseModel):
    """Data for SprintPlanCreatedEvent"""
    project_id: str
    sprint_id: str
    sprint_number: int
    tasks: List[SprintTask]
    dependencies: List[TaskDependency]
    estimated_hours: float
    start_date: datetime
    end_date: datetime


class SprintPlanCreatedEvent(BaseEvent):
    """Sprint plan created"""
    type: Literal["project.sprint.plan_created"] = "project.sprint.plan_created"
    priority: int = 1  # P1 - High
    data: SprintPlanCreatedData


class SprintApprovedData(BaseModel):
    """Data for SprintApprovedEvent"""
    project_id: str
    sprint_id: str
    approved_by: str
    approved_at: datetime
    modifications: Optional[List[str]] = None  # Changes before approval


class SprintApprovedEvent(BaseEvent):
    """Client approved sprint plan"""
    type: Literal["project.sprint.approved"] = "project.sprint.approved"
    priority: int = 1  # P1 - High
    data: SprintApprovedData


# ============================================================================
# Sprint Review (Phase 2.3)
# ============================================================================

class SprintReviewStartedData(BaseModel):
    """Data for SprintReviewStartedEvent"""
    project_id: str
    sprint_id: str
    sprint_number: int
    review_date: datetime
    completed_tasks: int
    total_tasks: int


class SprintReviewStartedEvent(BaseEvent):
    """Operator started sprint review"""
    type: Literal["project.sprint.review_started"] = "project.sprint.review_started"
    priority: int = 1  # P1 - High
    data: SprintReviewStartedData


class SprintSummary(BaseModel):
    """Sprint summary metrics"""
    completed_tasks: int
    total_tasks: int
    completion_rate: float
    total_hours_spent: float
    estimated_hours: float
    key_achievements: List[str]
    challenges: List[str]


class SprintMetrics(BaseModel):
    """Sprint performance metrics"""
    velocity: float  # tasks per week
    quality_score: float  # 0-100
    client_satisfaction: Optional[float] = None  # 0-100
    magister_performance: Dict[str, float]  # magister -> score


class SprintReportGeneratedData(BaseModel):
    """Data for SprintReportGeneratedEvent"""
    project_id: str
    sprint_id: str
    report_path: str
    summary: SprintSummary
    deliverables: List[Deliverable]
    metrics: SprintMetrics


class SprintReportGeneratedEvent(BaseEvent):
    """Sprint report generated"""
    type: Literal["project.sprint.report_generated"] = "project.sprint.report_generated"
    priority: int = 1  # P1 - High
    data: SprintReportGeneratedData


# ============================================================================
# Sprint Retrospective (Phase 2.4)
# ============================================================================

class SprintRetrospectiveStartedData(BaseModel):
    """Data for SprintRetrospectiveStartedEvent"""
    project_id: str
    sprint_id: str
    sprint_number: int
    retrospective_date: datetime


class SprintRetrospectiveStartedEvent(BaseEvent):
    """Sprint retrospective started"""
    type: Literal["project.sprint.retrospective_started"] = "project.sprint.retrospective_started"
    priority: int = 2  # P2 - Normal
    data: SprintRetrospectiveStartedData


class ActionItem(BaseModel):
    """Retrospective action item"""
    description: str
    assignee: str  # magister or operator
    deadline: datetime
    priority: int


class SprintLessonsLearnedData(BaseModel):
    """Data for SprintLessonsLearnedEvent"""
    project_id: str
    sprint_id: str
    what_went_well: List[str]
    what_went_wrong: List[str]
    action_items: List[ActionItem]
    process_improvements: List[str]


class SprintLessonsLearnedEvent(BaseEvent):
    """Sprint lessons learned recorded"""
    type: Literal["project.sprint.lessons_learned"] = "project.sprint.lessons_learned"
    priority: int = 2  # P2 - Normal
    data: SprintLessonsLearnedData


class SprintCompletedData(BaseModel):
    """Data for SprintCompletedEvent"""
    project_id: str
    sprint_id: str
    sprint_number: int
    completed_at: datetime
    next_sprint_planned: bool
    next_sprint_start: Optional[datetime] = None


class SprintCompletedEvent(BaseEvent):
    """Sprint fully completed"""
    type: Literal["project.sprint.completed"] = "project.sprint.completed"
    priority: int = 1  # P1 - High
    data: SprintCompletedData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_sprint_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/sprint_events.py tests/events/test_sprint_events.py
git commit -m "feat(events): add sprint execution events

Phase 2.1 (Sprint Planning):
- SprintPlanningStartedEvent
- SprintPlanCreatedEvent with SprintTask and TaskDependency
- SprintApprovedEvent

Phase 2.3 (Sprint Review):
- SprintReviewStartedEvent
- SprintReportGeneratedEvent with SprintSummary and SprintMetrics

Phase 2.4 (Sprint Retrospective):
- SprintRetrospectiveStartedEvent
- SprintLessonsLearnedEvent with ActionItem
- SprintCompletedEvent

All events with comprehensive tests"
```

---


## Task 5: Client Interaction Events

**Files:**
- Create: `src/meai/events/client_events.py`
- Create: `tests/events/test_client_events.py`

- [ ] **Step 1: Write tests for client events**

Create: `tests/events/test_client_events.py`

```python
import pytest
from datetime import datetime
from meai.events.client_events import (
    ClientCommunicationRecordedEvent,
    ClientCommunicationData,
    ClientApprovalRequestedEvent,
    ClientApprovalRequestedData,
    ClientApprovalApprovedEvent,
    ClientApprovalApprovedData,
    ClientApprovalRejectedEvent,
    ClientApprovalRejectedData,
    ClientRevisionRequestedEvent,
    ClientRevisionRequestedData,
    ClientReviewRequestedEvent,
    ClientReviewRequestedData,
    ClientFeedbackReceivedEvent,
    ClientFeedbackReceivedData,
    DeliverableRevision,
)
from meai.events.task_events import Deliverable


def test_client_communication_recorded_event():
    """Test ClientCommunicationRecordedEvent"""
    data = ClientCommunicationData(
        project_id="proj-test",
        communication_id="comm-001",
        communication_type="meeting",
        direction="inbound",
        participants=["client@example.com", "operator"],
        summary="Discussed strategy proposal",
        action_items=["Review section 3", "Provide budget approval"],
        recorded_at=datetime.utcnow(),
        related_to="strategy-001"
    )
    
    event = ClientCommunicationRecordedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "project.communication.recorded"
    assert event.priority == 2  # P2
    assert len(event.data.action_items) == 2


def test_client_approval_requested_event():
    """Test ClientApprovalRequestedEvent"""
    data = ClientApprovalRequestedData(
        project_id="proj-test",
        approval_id="approval-001",
        deliverable_id="deliv-001",
        deliverable_type="report",
        deliverable_title="SEO Analysis Report",
        deliverable_path="reports/seo-analysis.pdf",
        requested_at=datetime.utcnow(),
        deadline=datetime.utcnow(),
        description="Comprehensive SEO analysis"
    )
    
    event = ClientApprovalRequestedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "client.approval.requested"
    assert event.priority == 1  # P1


def test_client_approval_approved_event():
    """Test ClientApprovalApprovedEvent"""
    data = ClientApprovalApprovedData(
        project_id="proj-test",
        approval_id="approval-001",
        deliverable_id="deliv-001",
        approved_by="client@example.com",
        approved_at=datetime.utcnow(),
        comments="Looks great!"
    )
    
    event = ClientApprovalApprovedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "client.approval.approved"


def test_client_approval_rejected_event():
    """Test ClientApprovalRejectedEvent"""
    data = ClientApprovalRejectedData(
        project_id="proj-test",
        approval_id="approval-001",
        deliverable_id="deliv-001",
        rejected_by="client@example.com",
        rejected_at=datetime.utcnow(),
        reason="Missing competitor analysis",
        severity="major"
    )
    
    event = ClientApprovalRejectedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "client.approval.rejected"
    assert event.data.severity == "major"


def test_client_revision_requested_event():
    """Test ClientRevisionRequestedEvent"""
    data = ClientRevisionRequestedData(
        project_id="proj-test",
        approval_id="approval-001",
        deliverable_id="deliv-001",
        requested_by="client@example.com",
        requested_at=datetime.utcnow(),
        revision_type="minor",
        requested_changes="Update chart colors",
        deadline=datetime.utcnow(),
        priority=2
    )
    
    event = ClientRevisionRequestedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "client.approval.revision_requested"
    assert event.data.revision_type == "minor"


def test_client_review_requested_event():
    """Test ClientReviewRequestedEvent"""
    deliverables = [
        Deliverable(
            type="report",
            title="Sprint 1 Report",
            description="Sprint results",
            file_path="reports/sprint-1.pdf",
            requires_approval=True
        )
    ]
    
    data = ClientReviewRequestedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        deliverables=deliverables,
        review_deadline=datetime.utcnow()
    )
    
    event = ClientReviewRequestedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "client.review.requested"
    assert len(event.data.deliverables) == 1


def test_client_feedback_received_event():
    """Test ClientFeedbackReceivedEvent"""
    revisions = [
        DeliverableRevision(
            deliverable_id="deliv-001",
            revision_type="minor",
            requested_changes="Fix typos",
            deadline=datetime.utcnow()
        )
    ]
    
    data = ClientFeedbackReceivedData(
        project_id="proj-test",
        sprint_id="sprint-001",
        received_at=datetime.utcnow(),
        satisfaction_score=8,
        approved_deliverables=["deliv-002"],
        revision_requested=revisions,
        comments="Good work overall"
    )
    
    event = ClientFeedbackReceivedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "client.feedback.received"
    assert event.data.satisfaction_score == 8
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_client_events.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement client_events.py**

Create: `src/meai/events/client_events.py`

```python
"""Client interaction events"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal
from meai.events.base import BaseEvent
from meai.events.task_events import Deliverable


# ============================================================================
# Client Communication Events
# ============================================================================

class ClientCommunicationData(BaseModel):
    """Data for ClientCommunicationRecordedEvent"""
    project_id: str
    communication_id: str
    communication_type: Literal["email", "call", "meeting", "chat"]
    direction: Literal["inbound", "outbound"]
    participants: List[str]
    summary: str
    action_items: List[str]
    recorded_at: datetime
    related_to: Optional[str] = None  # strategy_id, sprint_id, etc.


class ClientCommunicationRecordedEvent(BaseEvent):
    """Client communication recorded"""
    type: Literal["project.communication.recorded"] = "project.communication.recorded"
    priority: int = 2  # P2 - Normal
    data: ClientCommunicationData


# ============================================================================
# Client Approval Flow Events
# ============================================================================

class ClientApprovalRequestedData(BaseModel):
    """Data for ClientApprovalRequestedEvent"""
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


class ClientApprovalRequestedEvent(BaseEvent):
    """Approval requested from client"""
    type: Literal["client.approval.requested"] = "client.approval.requested"
    priority: int = 1  # P1 - High
    data: ClientApprovalRequestedData


class ClientApprovalApprovedData(BaseModel):
    """Data for ClientApprovalApprovedEvent"""
    project_id: str
    approval_id: str
    deliverable_id: str
    approved_by: str
    approved_at: datetime
    comments: Optional[str] = None


class ClientApprovalApprovedEvent(BaseEvent):
    """Client approved deliverable"""
    type: Literal["client.approval.approved"] = "client.approval.approved"
    priority: int = 1  # P1 - High
    data: ClientApprovalApprovedData


class ClientApprovalRejectedData(BaseModel):
    """Data for ClientApprovalRejectedEvent"""
    project_id: str
    approval_id: str
    deliverable_id: str
    rejected_by: str
    rejected_at: datetime
    reason: str
    severity: Literal["minor", "major", "critical"]


class ClientApprovalRejectedEvent(BaseEvent):
    """Client rejected deliverable"""
    type: Literal["client.approval.rejected"] = "client.approval.rejected"
    priority: int = 1  # P1 - High
    data: ClientApprovalRejectedData


class ClientRevisionRequestedData(BaseModel):
    """Data for ClientRevisionRequestedEvent"""
    project_id: str
    approval_id: str
    deliverable_id: str
    requested_by: str
    requested_at: datetime
    revision_type: Literal["minor", "major"]
    requested_changes: str
    deadline: datetime
    priority: int


class ClientRevisionRequestedEvent(BaseEvent):
    """Client requested revisions"""
    type: Literal["client.approval.revision_requested"] = "client.approval.revision_requested"
    priority: int = 1  # P1 - High
    data: ClientRevisionRequestedData


# ============================================================================
# Sprint Review Client Events
# ============================================================================

class ClientReviewRequestedData(BaseModel):
    """Data for ClientReviewRequestedEvent"""
    project_id: str
    sprint_id: str
    deliverables: List[Deliverable]
    review_deadline: datetime
    meeting_scheduled: Optional[datetime] = None


class ClientReviewRequestedEvent(BaseEvent):
    """Client review requested for sprint"""
    type: Literal["client.review.requested"] = "client.review.requested"
    priority: int = 1  # P1 - High
    data: ClientReviewRequestedData


class DeliverableRevision(BaseModel):
    """Deliverable revision request"""
    deliverable_id: str
    revision_type: Literal["minor", "major"]
    requested_changes: str
    deadline: datetime


class ClientFeedbackReceivedData(BaseModel):
    """Data for ClientFeedbackReceivedEvent"""
    project_id: str
    sprint_id: str
    received_at: datetime
    satisfaction_score: int  # 1-10
    approved_deliverables: List[str]  # deliverable ids
    revision_requested: List[DeliverableRevision]
    comments: str


class ClientFeedbackReceivedEvent(BaseEvent):
    """Client provided feedback on sprint"""
    type: Literal["client.feedback.received"] = "client.feedback.received"
    priority: int = 1  # P1 - High
    data: ClientFeedbackReceivedData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_client_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/client_events.py tests/events/test_client_events.py
git commit -m "feat(events): add client interaction events

Communication:
- ClientCommunicationRecordedEvent

Approval Flow:
- ClientApprovalRequestedEvent
- ClientApprovalApprovedEvent
- ClientApprovalRejectedEvent
- ClientRevisionRequestedEvent

Sprint Review:
- ClientReviewRequestedEvent
- ClientFeedbackReceivedEvent with DeliverableRevision

All events with comprehensive tests"
```

---

## Task 6: Inter-Magister Communication Events

**Files:**
- Create: `src/meai/events/magister_events.py`
- Create: `tests/events/test_magister_events.py`

- [ ] **Step 1: Write tests for magister events**

Create: `tests/events/test_magister_events.py`

```python
import pytest
from datetime import datetime
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


def test_magister_data_request_event():
    """Test MagisterDataRequestEvent"""
    data = MagisterDataRequestData(
        project_id="proj-test",
        requesting_magister="content_magister",
        target_magister="brand_magister",
        data_type="tone_of_voice",
        parameters={"segment": "healthcare"},
        urgency="high"
    )
    
    event = MagisterDataRequestEvent(
        source="content_magister",
        target="brand_magister",
        data=data
    )
    
    assert event.type == "magister.request.data"
    assert event.priority == 2  # P2
    assert event.data.data_type == "tone_of_voice"


def test_magister_data_response_event():
    """Test MagisterDataResponseEvent"""
    data = MagisterDataResponseData(
        project_id="proj-test",
        request_id="req-123",
        responding_magister="brand_magister",
        requesting_magister="content_magister",
        data={"tone": "professional", "style": "informative"},
        status="success"
    )
    
    event = MagisterDataResponseEvent(
        source="brand_magister",
        target="content_magister",
        data=data,
        reply_to="req-123"
    )
    
    assert event.type == "magister.response.data"
    assert event.data.status == "success"
    assert event.reply_to == "req-123"


def test_magister_dependency_blocked_event():
    """Test MagisterDependencyBlockedEvent"""
    data = MagisterDependencyBlockedData(
        project_id="proj-test",
        task_id="task-002",
        blocked_magister="content_magister",
        blocking_magister="brand_magister",
        reason="Waiting for tone of voice"
    )
    
    event = MagisterDependencyBlockedEvent(
        source="content_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "magister.dependency.blocked"
    assert event.data.blocked_magister == "content_magister"


def test_magister_dependency_resolved_event():
    """Test MagisterDependencyResolvedEvent"""
    data = MagisterDependencyResolvedData(
        project_id="proj-test",
        task_id="task-002",
        blocked_magister="content_magister",
        blocking_magister="brand_magister",
        resolved_at=datetime.utcnow()
    )
    
    event = MagisterDependencyResolvedEvent(
        source="content_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "magister.dependency.resolved"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_magister_events.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement magister_events.py**

Create: `src/meai/events/magister_events.py`

```python
"""Inter-magister communication events"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from meai.events.base import BaseEvent


class MagisterDataRequestData(BaseModel):
    """Data for MagisterDataRequestEvent"""
    project_id: str
    requesting_magister: str
    target_magister: str
    data_type: str  # "tone_of_voice", "keywords", "analytics", etc.
    parameters: Dict[str, Any]
    urgency: Literal["low", "medium", "high"]
    deadline: Optional[datetime] = None


class MagisterDataRequestEvent(BaseEvent):
    """Magister requests data from another Magister"""
    type: Literal["magister.request.data"] = "magister.request.data"
    priority: int = 2  # P2 - Normal
    data: MagisterDataRequestData


class MagisterDataResponseData(BaseModel):
    """Data for MagisterDataResponseEvent"""
    project_id: str
    request_id: str  # correlation_id from request
    responding_magister: str
    requesting_magister: str
    data: Dict[str, Any]
    status: Literal["success", "partial", "failed"]
    notes: Optional[str] = None


class MagisterDataResponseEvent(BaseEvent):
    """Magister responds to data request"""
    type: Literal["magister.response.data"] = "magister.response.data"
    priority: int = 2  # P2 - Normal
    data: MagisterDataResponseData


class MagisterDependencyBlockedData(BaseModel):
    """Data for MagisterDependencyBlockedEvent"""
    project_id: str
    task_id: str
    blocked_magister: str
    blocking_magister: str
    reason: str
    estimated_unblock: Optional[datetime] = None


class MagisterDependencyBlockedEvent(BaseEvent):
    """Magister blocked by dependency on another Magister"""
    type: Literal["magister.dependency.blocked"] = "magister.dependency.blocked"
    priority: int = 2  # P2 - Normal
    data: MagisterDependencyBlockedData


class MagisterDependencyResolvedData(BaseModel):
    """Data for MagisterDependencyResolvedEvent"""
    project_id: str
    task_id: str
    blocked_magister: str
    blocking_magister: str
    resolved_at: datetime


class MagisterDependencyResolvedEvent(BaseEvent):
    """Dependency between Magisters resolved"""
    type: Literal["magister.dependency.resolved"] = "magister.dependency.resolved"
    priority: int = 2  # P2 - Normal
    data: MagisterDependencyResolvedData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_magister_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/magister_events.py tests/events/test_magister_events.py
git commit -m "feat(events): add inter-magister communication events

- MagisterDataRequestEvent (request/response pattern)
- MagisterDataResponseEvent (with reply_to)
- MagisterDependencyBlockedEvent
- MagisterDependencyResolvedEvent

All events with comprehensive tests"
```

---


## Task 7: Error Handling Events

**Files:**
- Create: `src/meai/events/error_events.py`
- Create: `tests/events/test_error_events.py`

- [ ] **Step 1: Write tests for error events**

Create: `tests/events/test_error_events.py`

```python
import pytest
from datetime import datetime
from meai.events.error_events import (
    ErrorOccurredEvent,
    ErrorOccurredData,
    ErrorRetryAttemptedEvent,
    ErrorRetryAttemptedData,
    ErrorResolvedEvent,
    ErrorResolvedData,
    ErrorEscalatedEvent,
    ErrorEscalatedData,
    RollbackInitiatedEvent,
    RollbackInitiatedData,
    RollbackCompletedEvent,
    RollbackCompletedData,
)
from meai.events.base import ErrorType, ErrorSeverity


def test_error_occurred_event():
    """Test ErrorOccurredEvent"""
    data = ErrorOccurredData(
        project_id="proj-test",
        task_id="task-001",
        component="seo_magister",
        error_type=ErrorType.API_FAILURE,
        severity=ErrorSeverity.HIGH,
        error_message="Google Search Console API timeout",
        context={"url": "https://api.google.com"},
        retry_possible=True,
        retry_count=0,
        max_retries=3
    )
    
    event = ErrorOccurredEvent(
        source="seo_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "error.occurred"
    assert event.priority == 0  # P0 for critical errors
    assert event.data.retry_possible is True


def test_error_retry_attempted_event():
    """Test ErrorRetryAttemptedEvent"""
    data = ErrorRetryAttemptedData(
        project_id="proj-test",
        task_id="task-001",
        original_error_id="error-123",
        component="seo_magister",
        retry_number=1,
        max_retries=3,
        attempted_at=datetime.utcnow()
    )
    
    event = ErrorRetryAttemptedEvent(
        source="seo_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "error.retry_attempted"
    assert event.priority == 1  # P1
    assert event.data.retry_number == 1


def test_error_resolved_event():
    """Test ErrorResolvedEvent"""
    data = ErrorResolvedData(
        project_id="proj-test",
        task_id="task-001",
        original_error_id="error-123",
        component="seo_magister",
        resolved_at=datetime.utcnow(),
        resolution_method="retry",
        notes="Succeeded on retry 2"
    )
    
    event = ErrorResolvedEvent(
        source="seo_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "error.resolved"
    assert event.data.resolution_method == "retry"


def test_error_escalated_event():
    """Test ErrorEscalatedEvent"""
    data = ErrorEscalatedData(
        project_id="proj-test",
        task_id="task-001",
        original_error_id="error-123",
        component="seo_magister",
        escalated_to="user",
        escalated_at=datetime.utcnow(),
        reason="Max retries exceeded",
        suggested_actions=["Check API credentials", "Contact support"]
    )
    
    event = ErrorEscalatedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "error.escalated"
    assert event.priority == 0  # P0 - Critical
    assert event.data.escalated_to == "user"


def test_rollback_initiated_event():
    """Test RollbackInitiatedEvent"""
    data = RollbackInitiatedData(
        project_id="proj-test",
        rollback_id="rollback-001",
        reason="Critical error in baseline collection",
        target_state="snapshot-123",
        initiated_by="operator",
        initiated_at=datetime.utcnow()
    )
    
    event = RollbackInitiatedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "system.rollback.initiated"
    assert event.priority == 0  # P0


def test_rollback_completed_event():
    """Test RollbackCompletedEvent"""
    data = RollbackCompletedData(
        project_id="proj-test",
        rollback_id="rollback-001",
        completed_at=datetime.utcnow(),
        restored_state="snapshot-123",
        affected_components=["seo_magister", "analytics_magister"]
    )
    
    event = RollbackCompletedEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "system.rollback.completed"
    assert len(event.data.affected_components) == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_error_events.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement error_events.py**

Create: `src/meai/events/error_events.py`

```python
"""Error handling and recovery events"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from meai.events.base import BaseEvent, ErrorType, ErrorSeverity


class ErrorOccurredData(BaseModel):
    """Data for ErrorOccurredEvent"""
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


class ErrorOccurredEvent(BaseEvent):
    """Error occurred in system"""
    type: Literal["error.occurred"] = "error.occurred"
    priority: int = 0  # P0 - Critical (if severity=critical)
    data: ErrorOccurredData


class ErrorRetryAttemptedData(BaseModel):
    """Data for ErrorRetryAttemptedEvent"""
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    original_error_id: str
    component: str
    retry_number: int
    max_retries: int
    attempted_at: datetime


class ErrorRetryAttemptedEvent(BaseEvent):
    """Retry attempted after error"""
    type: Literal["error.retry_attempted"] = "error.retry_attempted"
    priority: int = 1  # P1 - High
    data: ErrorRetryAttemptedData


class ErrorResolvedData(BaseModel):
    """Data for ErrorResolvedEvent"""
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    original_error_id: str
    component: str
    resolved_at: datetime
    resolution_method: Literal["retry", "manual", "automatic", "workaround"]
    notes: Optional[str] = None


class ErrorResolvedEvent(BaseEvent):
    """Error resolved"""
    type: Literal["error.resolved"] = "error.resolved"
    priority: int = 2  # P2 - Normal
    data: ErrorResolvedData


class ErrorEscalatedData(BaseModel):
    """Data for ErrorEscalatedEvent"""
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    original_error_id: str
    component: str
    escalated_to: Literal["operator", "user"]
    escalated_at: datetime
    reason: str
    suggested_actions: List[str]


class ErrorEscalatedEvent(BaseEvent):
    """Error escalated to Operator or YOU"""
    type: Literal["error.escalated"] = "error.escalated"
    priority: int = 0  # P0 - Critical
    data: ErrorEscalatedData


class RollbackInitiatedData(BaseModel):
    """Data for RollbackInitiatedEvent"""
    project_id: str
    rollback_id: str
    reason: str
    target_state: str  # snapshot_id or timestamp
    initiated_by: str
    initiated_at: datetime


class RollbackInitiatedEvent(BaseEvent):
    """Rollback initiated"""
    type: Literal["system.rollback.initiated"] = "system.rollback.initiated"
    priority: int = 0  # P0 - Critical
    data: RollbackInitiatedData


class RollbackCompletedData(BaseModel):
    """Data for RollbackCompletedEvent"""
    project_id: str
    rollback_id: str
    completed_at: datetime
    restored_state: str
    affected_components: List[str]


class RollbackCompletedEvent(BaseEvent):
    """Rollback completed"""
    type: Literal["system.rollback.completed"] = "system.rollback.completed"
    priority: int = 0  # P0 - Critical
    data: RollbackCompletedData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_error_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/error_events.py tests/events/test_error_events.py
git commit -m "feat(events): add error handling and recovery events

- ErrorOccurredEvent with ErrorType and ErrorSeverity
- ErrorRetryAttemptedEvent
- ErrorResolvedEvent
- ErrorEscalatedEvent (P0 priority)
- RollbackInitiatedEvent
- RollbackCompletedEvent

All events with comprehensive tests"
```

---

## Task 8: System Monitoring & Data Events

**Files:**
- Create: `src/meai/events/system_events.py`
- Create: `tests/events/test_system_events.py`

- [ ] **Step 1: Write tests for system events**

Create: `tests/events/test_system_events.py`

```python
import pytest
from datetime import datetime
from meai.events.system_events import (
    SystemHealthCheckEvent,
    SystemHealthCheckData,
    ComponentHealth,
    SystemPerformanceDegradedEvent,
    SystemPerformanceDegradedData,
    SystemResourceLowEvent,
    SystemResourceLowData,
    AgentUnresponsiveEvent,
    AgentUnresponsiveData,
    DataVersionCreatedEvent,
    DataVersionCreatedData,
    DataVersionComparedEvent,
    DataVersionComparedData,
    DataDifference,
    DataVersionArchivedEvent,
    DataVersionArchivedData,
    ReminderEvent,
    ReminderData,
)


def test_system_health_check_event():
    """Test SystemHealthCheckEvent"""
    components = {
        "operator": ComponentHealth(
            component="operator",
            status="healthy",
            response_time_ms=50.0,
            error_rate=0.01,
            last_activity=datetime.utcnow()
        ),
        "seo_magister": ComponentHealth(
            component="seo_magister",
            status="degraded",
            response_time_ms=5500.0,
            error_rate=0.03
        )
    }
    
    data = SystemHealthCheckData(
        check_id="check-001",
        checked_at=datetime.utcnow(),
        components=components,
        overall_status="degraded"
    )
    
    event = SystemHealthCheckEvent(
        source="system",
        target="operator",
        data=data
    )
    
    assert event.type == "system.health.check"
    assert event.priority == 3  # P3 - Low
    assert event.data.overall_status == "degraded"


def test_system_performance_degraded_event():
    """Test SystemPerformanceDegradedEvent"""
    data = SystemPerformanceDegradedData(
        component="event_bus",
        metric="response_time",
        current_value=6000.0,
        threshold_value=5000.0,
        degradation_percent=20.0,
        detected_at=datetime.utcnow()
    )
    
    event = SystemPerformanceDegradedEvent(
        source="system",
        target="operator",
        data=data
    )
    
    assert event.type == "system.performance.degraded"
    assert event.priority == 1  # P1


def test_system_resource_low_event():
    """Test SystemResourceLowEvent"""
    data = SystemResourceLowData(
        resource_type="api_quota",
        current_usage=8500.0,
        max_capacity=10000.0,
        usage_percent=85.0,
        threshold_percent=80.0,
        detected_at=datetime.utcnow()
    )
    
    event = SystemResourceLowEvent(
        source="system",
        target="operator",
        data=data
    )
    
    assert event.type == "system.resource.low"
    assert event.data.usage_percent == 85.0


def test_agent_unresponsive_event():
    """Test AgentUnresponsiveEvent"""
    data = AgentUnresponsiveData(
        agent_type="seo_magister",
        agent_id="seo-001",
        last_activity=datetime.utcnow(),
        timeout_seconds=300,
        detected_at=datetime.utcnow(),
        action_taken="restart"
    )
    
    event = AgentUnresponsiveEvent(
        source="system",
        target="operator",
        data=data
    )
    
    assert event.type == "system.agent.unresponsive"
    assert event.priority == 0  # P0 - Critical


def test_data_version_created_event():
    """Test DataVersionCreatedEvent"""
    data = DataVersionCreatedData(
        project_id="proj-test",
        version_id="version-001",
        version_number=1,
        data_type="baseline",
        created_at=datetime.utcnow(),
        created_by="analytics_magister",
        changes_summary="Initial baseline",
        file_path="baselines/baseline-001.json"
    )
    
    event = DataVersionCreatedEvent(
        source="analytics_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "data.version.created"
    assert event.data.version_number == 1


def test_data_version_compared_event():
    """Test DataVersionComparedEvent"""
    differences = [
        DataDifference(
            field="traffic",
            old_value=10000,
            new_value=12000,
            change_type="modified",
            significance="major"
        )
    ]
    
    data = DataVersionComparedData(
        project_id="proj-test",
        comparison_id="comp-001",
        version_a="version-001",
        version_b="version-002",
        compared_at=datetime.utcnow(),
        differences=differences,
        summary="Traffic increased by 20%"
    )
    
    event = DataVersionComparedEvent(
        source="analytics_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "data.version.compared"
    assert len(event.data.differences) == 1


def test_data_version_archived_event():
    """Test DataVersionArchivedEvent"""
    data = DataVersionArchivedData(
        project_id="proj-test",
        version_id="version-001",
        archived_at=datetime.utcnow(),
        archive_path="archive/version-001.json",
        retention_days=365
    )
    
    event = DataVersionArchivedEvent(
        source="analytics_magister",
        target="operator",
        data=data
    )
    
    assert event.type == "data.version.archived"
    assert event.data.retention_days == 365


def test_reminder_event():
    """Test ReminderEvent"""
    data = ReminderData(
        project_id="proj-test",
        reminder_type="1_month",
        scheduled_for=datetime.utcnow(),
        action="Follow up on proposal",
        context={"proposal_id": "prop-001"}
    )
    
    event = ReminderEvent(
        source="operator",
        target="operator",
        data=data
    )
    
    assert event.type == "reminder.scheduled"
    assert event.priority == 3  # P3
    assert event.data.reminder_type == "1_month"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_system_events.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement system_events.py**

Create: `src/meai/events/system_events.py`

```python
"""System monitoring and data versioning events"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from meai.events.base import BaseEvent


# ============================================================================
# System Monitoring Events
# ============================================================================

class ComponentHealth(BaseModel):
    """Component health status"""
    component: str
    status: Literal["healthy", "degraded", "critical", "offline"]
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    last_activity: Optional[datetime] = None


class SystemHealthCheckData(BaseModel):
    """Data for SystemHealthCheckEvent"""
    check_id: str
    checked_at: datetime
    components: Dict[str, ComponentHealth]
    overall_status: Literal["healthy", "degraded", "critical"]


class SystemHealthCheckEvent(BaseEvent):
    """Periodic system health check"""
    type: Literal["system.health.check"] = "system.health.check"
    priority: int = 3  # P3 - Low
    data: SystemHealthCheckData


class SystemPerformanceDegradedData(BaseModel):
    """Data for SystemPerformanceDegradedEvent"""
    component: str
    metric: str  # "response_time", "error_rate", "throughput"
    current_value: float
    threshold_value: float
    degradation_percent: float
    detected_at: datetime


class SystemPerformanceDegradedEvent(BaseEvent):
    """System performance degraded"""
    type: Literal["system.performance.degraded"] = "system.performance.degraded"
    priority: int = 1  # P1 - High
    data: SystemPerformanceDegradedData


class SystemResourceLowData(BaseModel):
    """Data for SystemResourceLowEvent"""
    resource_type: Literal["memory", "disk", "api_quota", "database_connections"]
    current_usage: float
    max_capacity: float
    usage_percent: float
    threshold_percent: float
    detected_at: datetime


class SystemResourceLowEvent(BaseEvent):
    """System resource running low"""
    type: Literal["system.resource.low"] = "system.resource.low"
    priority: int = 1  # P1 - High
    data: SystemResourceLowData


class AgentUnresponsiveData(BaseModel):
    """Data for AgentUnresponsiveEvent"""
    agent_type: str  # "operator", "seo_magister", etc.
    agent_id: str
    last_activity: datetime
    timeout_seconds: int
    detected_at: datetime
    action_taken: Literal["restart", "escalate", "wait"]


class AgentUnresponsiveEvent(BaseEvent):
    """Agent not responding"""
    type: Literal["system.agent.unresponsive"] = "system.agent.unresponsive"
    priority: int = 0  # P0 - Critical
    data: AgentUnresponsiveData


# ============================================================================
# Data Versioning Events
# ============================================================================

class DataVersionCreatedData(BaseModel):
    """Data for DataVersionCreatedEvent"""
    project_id: str
    version_id: str
    version_number: int
    data_type: str  # "baseline", "analytics", "content", etc.
    created_at: datetime
    created_by: str  # magister
    changes_summary: str
    file_path: Optional[str] = None


class DataVersionCreatedEvent(BaseEvent):
    """New data version created"""
    type: Literal["data.version.created"] = "data.version.created"
    priority: int = 2  # P2 - Normal
    data: DataVersionCreatedData


class DataDifference(BaseModel):
    """Data difference between versions"""
    field: str
    old_value: Any
    new_value: Any
    change_type: Literal["added", "removed", "modified"]
    significance: Literal["minor", "major", "critical"]


class DataVersionComparedData(BaseModel):
    """Data for DataVersionComparedEvent"""
    project_id: str
    comparison_id: str
    version_a: str
    version_b: str
    compared_at: datetime
    differences: List[DataDifference]
    summary: str


class DataVersionComparedEvent(BaseEvent):
    """Data versions compared"""
    type: Literal["data.version.compared"] = "data.version.compared"
    priority: int = 2  # P2 - Normal
    data: DataVersionComparedData


class DataVersionArchivedData(BaseModel):
    """Data for DataVersionArchivedEvent"""
    project_id: str
    version_id: str
    archived_at: datetime
    archive_path: str
    retention_days: int


class DataVersionArchivedEvent(BaseEvent):
    """Data version archived"""
    type: Literal["data.version.archived"] = "data.version.archived"
    priority: int = 3  # P3 - Low
    data: DataVersionArchivedData


# ============================================================================
# Reminder Events
# ============================================================================

class ReminderData(BaseModel):
    """Data for ReminderEvent"""
    project_id: str
    reminder_type: Literal["1_month", "2_months", "3_months"]
    scheduled_for: datetime
    action: str  # What to do when reminder fires
    context: Dict[str, Any]


class ReminderEvent(BaseEvent):
    """Scheduled reminder for follow-up"""
    type: Literal["reminder.scheduled"] = "reminder.scheduled"
    priority: int = 3  # P3 - Low
    data: ReminderData
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_system_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/system_events.py tests/events/test_system_events.py
git commit -m "feat(events): add system monitoring and data versioning events

System Monitoring:
- SystemHealthCheckEvent with ComponentHealth
- SystemPerformanceDegradedEvent
- SystemResourceLowEvent
- AgentUnresponsiveEvent (P0 priority)

Data Versioning:
- DataVersionCreatedEvent
- DataVersionComparedEvent with DataDifference
- DataVersionArchivedEvent

Other:
- ReminderEvent (Pre-Sale follow-up)

All events with comprehensive tests"
```

---


## Task 9: Export All Events

**Files:**
- Modify: `src/meai/events/__init__.py`
- Create: `tests/events/test_imports.py`

- [ ] **Step 1: Write test for imports**

Create: `tests/events/test_imports.py`

```python
"""Test that all events can be imported from meai.events"""

def test_import_base_events():
    """Test importing base events"""
    from meai.events import BaseEvent, ProjectStatus, ErrorType, ErrorSeverity
    
    assert BaseEvent is not None
    assert ProjectStatus is not None
    assert ErrorType is not None
    assert ErrorSeverity is not None


def test_import_project_events():
    """Test importing project events"""
    from meai.events import (
        ProjectCreatedEvent,
        InfrastructureSetupStartedEvent,
        InfrastructureSetupCompletedEvent,
        BaselineCollectionStartedEvent,
        BaselineDataCollectedEvent,
        BaselineAggregationCompletedEvent,
        StrategyPlanningStartedEvent,
        StrategyProposalReadyEvent,
        StrategyReviewRequestedEvent,
        StrategyModifiedEvent,
        StrategyApprovedEvent,
    )
    
    assert ProjectCreatedEvent is not None
    assert BaselineCollectionStartedEvent is not None
    assert StrategyApprovedEvent is not None


def test_import_task_events():
    """Test importing task events"""
    from meai.events import (
        TaskCreatedEvent,
        TaskAssignedEvent,
        TaskStartedEvent,
        TaskProgressEvent,
        TaskCompletedEvent,
        TaskFailedEvent,
        TaskBlockedEvent,
        Deliverable,
    )
    
    assert TaskCreatedEvent is not None
    assert TaskCompletedEvent is not None
    assert Deliverable is not None


def test_import_sprint_events():
    """Test importing sprint events"""
    from meai.events import (
        SprintPlanningStartedEvent,
        SprintPlanCreatedEvent,
        SprintApprovedEvent,
        SprintReviewStartedEvent,
        SprintReportGeneratedEvent,
        SprintRetrospectiveStartedEvent,
        SprintLessonsLearnedEvent,
        SprintCompletedEvent,
    )
    
    assert SprintPlanningStartedEvent is not None
    assert SprintCompletedEvent is not None


def test_import_client_events():
    """Test importing client events"""
    from meai.events import (
        ClientCommunicationRecordedEvent,
        ClientApprovalRequestedEvent,
        ClientApprovalApprovedEvent,
        ClientApprovalRejectedEvent,
        ClientRevisionRequestedEvent,
        ClientReviewRequestedEvent,
        ClientFeedbackReceivedEvent,
    )
    
    assert ClientCommunicationRecordedEvent is not None
    assert ClientApprovalRequestedEvent is not None


def test_import_magister_events():
    """Test importing magister events"""
    from meai.events import (
        MagisterDataRequestEvent,
        MagisterDataResponseEvent,
        MagisterDependencyBlockedEvent,
        MagisterDependencyResolvedEvent,
    )
    
    assert MagisterDataRequestEvent is not None
    assert MagisterDataResponseEvent is not None


def test_import_error_events():
    """Test importing error events"""
    from meai.events import (
        ErrorOccurredEvent,
        ErrorRetryAttemptedEvent,
        ErrorResolvedEvent,
        ErrorEscalatedEvent,
        RollbackInitiatedEvent,
        RollbackCompletedEvent,
    )
    
    assert ErrorOccurredEvent is not None
    assert RollbackInitiatedEvent is not None


def test_import_system_events():
    """Test importing system events"""
    from meai.events import (
        SystemHealthCheckEvent,
        SystemPerformanceDegradedEvent,
        SystemResourceLowEvent,
        AgentUnresponsiveEvent,
        DataVersionCreatedEvent,
        DataVersionComparedEvent,
        DataVersionArchivedEvent,
        ReminderEvent,
    )
    
    assert SystemHealthCheckEvent is not None
    assert DataVersionCreatedEvent is not None
    assert ReminderEvent is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_imports.py -v
```

Expected: FAIL with "ImportError: cannot import name..."

- [ ] **Step 3: Create __init__.py with all exports**

Create: `src/meai/events/__init__.py`

```python
"""Event Bus events package

This package contains all Pydantic event models for the Event Bus architecture.
Events are organized by category:
- base: BaseEvent and core enums
- project_events: Project lifecycle events
- task_events: Task execution events
- sprint_events: Sprint execution events
- client_events: Client interaction events
- magister_events: Inter-magister communication events
- error_events: Error handling and recovery events
- system_events: System monitoring and data versioning events
"""

# Base events and enums
from meai.events.base import (
    BaseEvent,
    ProjectStatus,
    ErrorType,
    ErrorSeverity,
)

# Project lifecycle events
from meai.events.project_events import (
    # Pre-Sale
    ProjectCreatedEvent,
    ProjectCreatedData,
    # Setup
    InfrastructureSetupStartedEvent,
    InfrastructureSetupStartedData,
    SetupTask,
    InfrastructureSetupCompletedEvent,
    InfrastructureSetupCompletedData,
    # Baseline
    BaselineCollectionStartedEvent,
    BaselineCollectionStartedData,
    BaselineTask,
    BaselineDataCollectedEvent,
    BaselineDataCollectedData,
    BaselineAggregationCompletedEvent,
    BaselineAggregationCompletedData,
    # Strategy Planning
    StrategyPlanningStartedEvent,
    StrategyPlanningStartedData,
    StrategyProposalReadyEvent,
    StrategyProposalReadyData,
    StrategyReviewRequestedEvent,
    StrategyReviewRequestedData,
    StrategyModifiedEvent,
    StrategyModifiedData,
    StrategyModification,
    StrategyApprovedEvent,
    StrategyApprovedData,
)

# Task execution events
from meai.events.task_events import (
    TaskCreatedEvent,
    TaskCreatedData,
    TaskAssignedEvent,
    TaskAssignedData,
    TaskStartedEvent,
    TaskStartedData,
    TaskProgressEvent,
    TaskProgressData,
    TaskCompletedEvent,
    TaskCompletedData,
    Deliverable,
    TaskFailedEvent,
    TaskFailedData,
    TaskBlockedEvent,
    TaskBlockedData,
)

# Sprint execution events
from meai.events.sprint_events import (
    SprintPlanningStartedEvent,
    SprintPlanningStartedData,
    SprintPlanCreatedEvent,
    SprintPlanCreatedData,
    SprintTask,
    TaskDependency,
    SprintApprovedEvent,
    SprintApprovedData,
    SprintReviewStartedEvent,
    SprintReviewStartedData,
    SprintReportGeneratedEvent,
    SprintReportGeneratedData,
    SprintSummary,
    SprintMetrics,
    SprintRetrospectiveStartedEvent,
    SprintRetrospectiveStartedData,
    SprintLessonsLearnedEvent,
    SprintLessonsLearnedData,
    ActionItem,
    SprintCompletedEvent,
    SprintCompletedData,
)

# Client interaction events
from meai.events.client_events import (
    ClientCommunicationRecordedEvent,
    ClientCommunicationData,
    ClientApprovalRequestedEvent,
    ClientApprovalRequestedData,
    ClientApprovalApprovedEvent,
    ClientApprovalApprovedData,
    ClientApprovalRejectedEvent,
    ClientApprovalRejectedData,
    ClientRevisionRequestedEvent,
    ClientRevisionRequestedData,
    ClientReviewRequestedEvent,
    ClientReviewRequestedData,
    ClientFeedbackReceivedEvent,
    ClientFeedbackReceivedData,
    DeliverableRevision,
)

# Inter-magister communication events
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

# Error handling and recovery events
from meai.events.error_events import (
    ErrorOccurredEvent,
    ErrorOccurredData,
    ErrorRetryAttemptedEvent,
    ErrorRetryAttemptedData,
    ErrorResolvedEvent,
    ErrorResolvedData,
    ErrorEscalatedEvent,
    ErrorEscalatedData,
    RollbackInitiatedEvent,
    RollbackInitiatedData,
    RollbackCompletedEvent,
    RollbackCompletedData,
)

# System monitoring and data versioning events
from meai.events.system_events import (
    SystemHealthCheckEvent,
    SystemHealthCheckData,
    ComponentHealth,
    SystemPerformanceDegradedEvent,
    SystemPerformanceDegradedData,
    SystemResourceLowEvent,
    SystemResourceLowData,
    AgentUnresponsiveEvent,
    AgentUnresponsiveData,
    DataVersionCreatedEvent,
    DataVersionCreatedData,
    DataVersionComparedEvent,
    DataVersionComparedData,
    DataDifference,
    DataVersionArchivedEvent,
    DataVersionArchivedData,
    ReminderEvent,
    ReminderData,
)

__all__ = [
    # Base
    "BaseEvent",
    "ProjectStatus",
    "ErrorType",
    "ErrorSeverity",
    # Project events
    "ProjectCreatedEvent",
    "ProjectCreatedData",
    "InfrastructureSetupStartedEvent",
    "InfrastructureSetupStartedData",
    "SetupTask",
    "InfrastructureSetupCompletedEvent",
    "InfrastructureSetupCompletedData",
    "BaselineCollectionStartedEvent",
    "BaselineCollectionStartedData",
    "BaselineTask",
    "BaselineDataCollectedEvent",
    "BaselineDataCollectedData",
    "BaselineAggregationCompletedEvent",
    "BaselineAggregationCompletedData",
    "StrategyPlanningStartedEvent",
    "StrategyPlanningStartedData",
    "StrategyProposalReadyEvent",
    "StrategyProposalReadyData",
    "StrategyReviewRequestedEvent",
    "StrategyReviewRequestedData",
    "StrategyModifiedEvent",
    "StrategyModifiedData",
    "StrategyModification",
    "StrategyApprovedEvent",
    "StrategyApprovedData",
    # Task events
    "TaskCreatedEvent",
    "TaskCreatedData",
    "TaskAssignedEvent",
    "TaskAssignedData",
    "TaskStartedEvent",
    "TaskStartedData",
    "TaskProgressEvent",
    "TaskProgressData",
    "TaskCompletedEvent",
    "TaskCompletedData",
    "Deliverable",
    "TaskFailedEvent",
    "TaskFailedData",
    "TaskBlockedEvent",
    "TaskBlockedData",
    # Sprint events
    "SprintPlanningStartedEvent",
    "SprintPlanningStartedData",
    "SprintPlanCreatedEvent",
    "SprintPlanCreatedData",
    "SprintTask",
    "TaskDependency",
    "SprintApprovedEvent",
    "SprintApprovedData",
    "SprintReviewStartedEvent",
    "SprintReviewStartedData",
    "SprintReportGeneratedEvent",
    "SprintReportGeneratedData",
    "SprintSummary",
    "SprintMetrics",
    "SprintRetrospectiveStartedEvent",
    "SprintRetrospectiveStartedData",
    "SprintLessonsLearnedEvent",
    "SprintLessonsLearnedData",
    "ActionItem",
    "SprintCompletedEvent",
    "SprintCompletedData",
    # Client events
    "ClientCommunicationRecordedEvent",
    "ClientCommunicationData",
    "ClientApprovalRequestedEvent",
    "ClientApprovalRequestedData",
    "ClientApprovalApprovedEvent",
    "ClientApprovalApprovedData",
    "ClientApprovalRejectedEvent",
    "ClientApprovalRejectedData",
    "ClientRevisionRequestedEvent",
    "ClientRevisionRequestedData",
    "ClientReviewRequestedEvent",
    "ClientReviewRequestedData",
    "ClientFeedbackReceivedEvent",
    "ClientFeedbackReceivedData",
    "DeliverableRevision",
    # Magister events
    "MagisterDataRequestEvent",
    "MagisterDataRequestData",
    "MagisterDataResponseEvent",
    "MagisterDataResponseData",
    "MagisterDependencyBlockedEvent",
    "MagisterDependencyBlockedData",
    "MagisterDependencyResolvedEvent",
    "MagisterDependencyResolvedData",
    # Error events
    "ErrorOccurredEvent",
    "ErrorOccurredData",
    "ErrorRetryAttemptedEvent",
    "ErrorRetryAttemptedData",
    "ErrorResolvedEvent",
    "ErrorResolvedData",
    "ErrorEscalatedEvent",
    "ErrorEscalatedData",
    "RollbackInitiatedEvent",
    "RollbackInitiatedData",
    "RollbackCompletedEvent",
    "RollbackCompletedData",
    # System events
    "SystemHealthCheckEvent",
    "SystemHealthCheckData",
    "ComponentHealth",
    "SystemPerformanceDegradedEvent",
    "SystemPerformanceDegradedData",
    "SystemResourceLowEvent",
    "SystemResourceLowData",
    "AgentUnresponsiveEvent",
    "AgentUnresponsiveData",
    "DataVersionCreatedEvent",
    "DataVersionCreatedData",
    "DataVersionComparedEvent",
    "DataVersionComparedData",
    "DataDifference",
    "DataVersionArchivedEvent",
    "DataVersionArchivedData",
    "ReminderEvent",
    "ReminderData",
]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/events/test_imports.py -v
```

Expected: PASS (all imports work)

- [ ] **Step 5: Run all event tests**

```bash
pytest tests/events/ -v
```

Expected: PASS (all tests green)

- [ ] **Step 6: Commit**

```bash
git add src/meai/events/__init__.py tests/events/test_imports.py
git commit -m "feat(events): export all events from meai.events package

- Add __init__.py with all event exports
- Add comprehensive import tests
- 60+ event types exported
- All events accessible via 'from meai.events import ...'

All tests passing"
```

---

## Self-Review Checklist

- [ ] **Placeholder scan:** No TBD, TODO, or incomplete sections
- [ ] **Type consistency:** All event types use Literal for type field
- [ ] **Priority consistency:** All events have appropriate priority (P0-P3)
- [ ] **Test coverage:** Every event has at least one test
- [ ] **Import verification:** All events can be imported from meai.events
- [ ] **Pydantic validation:** All data models use proper Pydantic types
- [ ] **Spec coverage:** All events from spec are implemented

---

## Summary

**Created:**
- 8 event module files (base, project, task, sprint, client, magister, error, system)
- 60+ event types with Pydantic models
- Comprehensive test suite (8 test files)
- Package exports (__init__.py)

**Event Categories:**
- Project lifecycle: 13 events
- Task execution: 7 events
- Sprint execution: 8 events
- Client interaction: 7 events
- Inter-magister: 4 events
- Error handling: 6 events
- System monitoring: 8 events
- Data versioning: 3 events
- Other: 4 events

**Total:** 60+ events, all with strict Pydantic typing

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-08-event-schemas-models.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

