# tests/integration/test_event_bus_e2e.py
"""End-to-end integration tests for EventBus with BaseEvent system"""
import pytest
import asyncio
from datetime import datetime, UTC
from meai.events.event_bus import EventBus
from meai.events.project_events import (
    ProjectCreatedEvent,
    ProjectCreatedData,
    StrategyApprovedEvent,
)
from meai.events.task_events import (
    TaskCreatedEvent,
    TaskCreatedData,
    TaskAssignedEvent,
    TaskAssignedData,
    TaskCompletedEvent,
    TaskCompletedData,
)
from meai.events.error_events import (
    ErrorOccurredEvent,
    ErrorOccurredData,
)
from meai.events.base import ProjectStatus, ErrorType, ErrorSeverity


@pytest.mark.asyncio
async def test_full_project_lifecycle_with_correlation():
    """Test complete project lifecycle with correlation chains

    Simulates:
    1. Operator creates project (correlation_id: proj-lifecycle-001)
    2. Brand Magister receives project.created
    3. Brand Magister creates tasks (same correlation_id)
    4. SEO Magister receives tasks
    5. SEO Magister completes tasks
    6. Brand Magister receives task.completed
    7. Brand Magister approves strategy
    """
    bus = EventBus()
    await bus.initialize()

    correlation_id = "proj-lifecycle-001"
    received_events = {
        "brand-magister": [],
        "seo-magister": [],
        "operator": [],
    }

    # Subscribe handlers
    async def brand_handler(event):
        received_events["brand-magister"].append(event)

    async def seo_handler(event):
        received_events["seo-magister"].append(event)

    async def operator_handler(event):
        received_events["operator"].append(event)

    bus.subscribe("project.created", brand_handler)
    bus.subscribe("task.created", seo_handler)
    bus.subscribe("task.completed", brand_handler)
    bus.subscribe("strategy.approved", operator_handler)

    # Step 1: Operator creates project
    project_event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id=correlation_id,
        data=ProjectCreatedData(
            project_id="proj-001",
            client_name="Medical Clinic",
            client_domain="medclinic.com",
            client_contact="contact@medclinic.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )
    project_event_id = await bus.publish(project_event)
    await asyncio.sleep(0.1)

    # Verify Brand Magister received project.created
    assert len(received_events["brand-magister"]) == 1
    assert received_events["brand-magister"][0].type == "project.created"

    # Step 2: Brand Magister creates tasks
    task1_event = TaskCreatedEvent(
        source="brand-magister",
        target="seo-magister",
        correlation_id=correlation_id,
        data=TaskCreatedData(
            project_id="proj-001",
            task_id="task-001",
            magister="seo-magister",
            capability="seo_audit",
            parameters={"depth": "comprehensive"}
        )
    )
    task1_event_id = await bus.publish(task1_event)
    await asyncio.sleep(0.1)

    # Verify SEO Magister received task.created
    assert len(received_events["seo-magister"]) == 1
    assert received_events["seo-magister"][0].type == "task.created"

    # Step 3: SEO Magister completes task
    task_completed_event = TaskCompletedEvent(
        source="seo-magister",
        target="brand-magister",
        correlation_id=correlation_id,
        data=TaskCompletedData(
            project_id="proj-001",
            task_id="task-001",
            magister="seo-magister",
            completed_at=datetime.now(UTC),
            deliverables=[],
            summary="SEO audit completed successfully"
        )
    )
    task_completed_event_id = await bus.publish(task_completed_event)
    await asyncio.sleep(0.1)

    # Verify Brand Magister received task.completed
    assert len(received_events["brand-magister"]) == 2
    assert received_events["brand-magister"][1].type == "task.completed"

    # Step 4: Brand Magister approves strategy
    strategy_event = StrategyApprovedEvent(
        source="brand-magister",
        target="operator",
        correlation_id=correlation_id,
        project_id="proj-001",
        final_strategy={"seo": "comprehensive", "content": "blog_focused"},
        approval_timestamp=datetime.now(UTC)
    )
    strategy_event_id = await bus.publish(strategy_event)
    await asyncio.sleep(0.1)

    # Verify all events have same correlation_id
    events = await bus.get_events(correlation_id=correlation_id, status="pending", limit=10)
    assert len(events) == 4
    for event in events:
        assert event.correlation_id == correlation_id

    # Mark all as processed
    await bus.mark_processed(project_event_id)
    await bus.mark_processed(task1_event_id)
    await bus.mark_processed(task_completed_event_id)
    await bus.mark_processed(strategy_event_id)

    # Verify no pending events
    pending = await bus.get_events(correlation_id=correlation_id, status="pending", limit=10)
    assert len(pending) == 0

    await bus.close()


@pytest.mark.asyncio
async def test_error_handling_with_priority_ordering():
    """Test error handling with priority-based event ordering

    Simulates:
    1. Multiple events with different priorities (P0, P1, P2, P3)
    2. One event fails with error
    3. Verify priority ordering is maintained
    4. Verify failed event is marked correctly
    """
    bus = EventBus()
    await bus.initialize()

    # Create events with different priorities
    # P0 - Critical system event
    error_event = ErrorOccurredEvent(
        source="seo-magister",
        target="operator",
        data=ErrorOccurredData(
            error_type=ErrorType.API_FAILURE,
            error_severity=ErrorSeverity.CRITICAL,
            error_message="Database connection failed",
            context={"operation": "save_audit_results"}
        )
    )
    error_event_id = await bus.publish(error_event)

    # P1 - Project event
    project_event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="proj-002",
            client_name="Dental Practice",
            client_domain="dentalpractice.com",
            client_contact="contact@dentalpractice.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Referral",
            created_at=datetime.now(UTC)
        )
    )
    project_event_id = await bus.publish(project_event)

    # P2 - Task event
    task_event = TaskCreatedEvent(
        source="brand-magister",
        target="content-magister",
        data=TaskCreatedData(
            project_id="proj-002",
            task_id="task-002",
            magister="content-magister",
            capability="content_strategy",
            parameters={"focus": "blog"}
        )
    )
    task_event_id = await bus.publish(task_event)

    # Get events for operator (should get error first - P0)
    operator_events = await bus.get_events(target="operator", status="pending", limit=10)
    assert len(operator_events) == 1
    assert operator_events[0].type == "error.occurred"
    assert operator_events[0].priority == 0  # P0

    # Get events for brand-magister (should get project - P1)
    brand_events = await bus.get_events(target="brand-magister", status="pending", limit=10)
    assert len(brand_events) == 1
    assert brand_events[0].type == "project.created"
    assert brand_events[0].priority == 1  # P1

    # Get events for content-magister (should get task - P2)
    content_events = await bus.get_events(target="content-magister", status="pending", limit=10)
    assert len(content_events) == 1
    assert content_events[0].type == "task.created"
    assert content_events[0].priority == 2  # P2

    # Mark error event as failed
    await bus.mark_failed(error_event_id, "Failed to process critical error")

    # Verify error event is marked as failed
    stored_error = await bus._get_event_by_id(error_event_id)
    assert stored_error["status"] == "failed"

    # Verify failed event doesn't appear in pending queue
    operator_pending = await bus.get_events(target="operator", status="pending", limit=10)
    assert len(operator_pending) == 0

    await bus.close()


@pytest.mark.asyncio
async def test_pub_sub_with_multiple_event_types():
    """Test pub/sub with multiple event types and subscribers

    Simulates:
    1. Multiple subscribers for different event types
    2. Publishing various event types
    3. Verify each subscriber receives correct events
    4. Verify event isolation (subscribers only get their events)
    """
    bus = EventBus()
    await bus.initialize()

    received = {
        "project_events": [],
        "task_events": [],
        "error_events": [],
    }

    # Subscribe handlers
    async def project_handler(event):
        received["project_events"].append(event)

    async def task_handler(event):
        received["task_events"].append(event)

    async def error_handler(event):
        received["error_events"].append(event)

    bus.subscribe("project.created", project_handler)
    bus.subscribe("strategy.approved", project_handler)
    bus.subscribe("task.created", task_handler)
    bus.subscribe("task.assigned", task_handler)
    bus.subscribe("task.completed", task_handler)
    bus.subscribe("error.occurred", error_handler)

    # Publish project events
    await bus.publish(ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="proj-003",
            client_name="Hospital",
            client_domain="hospital.com",
            client_contact="contact@hospital.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Cold Outreach",
            created_at=datetime.now(UTC)
        )
    ))

    await bus.publish(StrategyApprovedEvent(
        source="brand-magister",
        target="operator",
        project_id="proj-003",
        final_strategy={"approach": "comprehensive"},
        approval_timestamp=datetime.now(UTC)
    ))

    # Publish task events
    await bus.publish(TaskCreatedEvent(
        source="brand-magister",
        target="seo-magister",
        data=TaskCreatedData(
            project_id="proj-003",
            task_id="task-003",
            magister="seo-magister",
            capability="keyword_research",
            parameters={"target": "medical"}
        )
    ))

    await bus.publish(TaskAssignedEvent(
        source="brand-magister",
        target="seo-magister",
        data=TaskAssignedData(
            project_id="proj-003",
            sprint_id="sprint-001",
            task_id="task-003",
            magister="seo-magister",
            capability="keyword_research",
            parameters={"target": "medical"}
        )
    ))

    await bus.publish(TaskCompletedEvent(
        source="seo-magister",
        target="brand-magister",
        data=TaskCompletedData(
            project_id="proj-003",
            task_id="task-003",
            magister="seo-magister",
            completed_at=datetime.now(UTC),
            deliverables=[],
            summary="Keyword research completed"
        )
    ))

    # Publish error event
    await bus.publish(ErrorOccurredEvent(
        source="seo-magister",
        target="operator",
        data=ErrorOccurredData(
            error_type=ErrorType.VALIDATION,
            error_severity=ErrorSeverity.MEDIUM,
            error_message="Invalid keyword format",
            context={"keyword": "test@#$"}
        )
    ))

    await asyncio.sleep(0.2)

    # Verify subscribers received correct events
    assert len(received["project_events"]) == 2
    assert received["project_events"][0].type == "project.created"
    assert received["project_events"][1].type == "strategy.approved"

    assert len(received["task_events"]) == 3
    assert received["task_events"][0].type == "task.created"
    assert received["task_events"][1].type == "task.assigned"
    assert received["task_events"][2].type == "task.completed"

    assert len(received["error_events"]) == 1
    assert received["error_events"][0].type == "error.occurred"

    await bus.close()


@pytest.mark.asyncio
async def test_concurrent_event_processing():
    """Test concurrent event processing with multiple agents

    Simulates:
    1. Multiple agents publishing events concurrently
    2. Multiple agents consuming events concurrently
    3. Verify all events are processed correctly
    4. Verify no race conditions or data loss
    """
    bus = EventBus()
    await bus.initialize()

    num_events = 20
    correlation_id = "concurrent-test"

    # Publish events concurrently
    tasks = []
    for i in range(num_events):
        event = TaskCreatedEvent(
            source="brand-magister",
            target=f"magister-{i % 3}",  # Distribute across 3 magisters
            correlation_id=correlation_id,
            data=TaskCreatedData(
                project_id="proj-concurrent",
                task_id=f"task-{i}",
                magister=f"magister-{i % 3}",
                capability="concurrent_task",
                parameters={"index": i}
            )
        )
        tasks.append(bus.publish(event))

    event_ids = await asyncio.gather(*tasks)
    assert len(event_ids) == num_events

    # Verify all events stored
    all_events = await bus.get_events(correlation_id=correlation_id, status="pending", limit=50)
    assert len(all_events) == num_events

    # Verify distribution across targets
    magister_0_events = await bus.get_events(target="magister-0", status="pending", limit=50)
    magister_1_events = await bus.get_events(target="magister-1", status="pending", limit=50)
    magister_2_events = await bus.get_events(target="magister-2", status="pending", limit=50)

    assert len(magister_0_events) + len(magister_1_events) + len(magister_2_events) == num_events

    # Mark all as processed concurrently
    mark_tasks = [bus.mark_processed(event_id) for event_id in event_ids]
    await asyncio.gather(*mark_tasks)

    # Verify all processed
    pending = await bus.get_events(correlation_id=correlation_id, status="pending", limit=50)
    assert len(pending) == 0

    await bus.close()


@pytest.mark.asyncio
async def test_event_filtering_combinations():
    """Test various combinations of event filtering

    Tests:
    1. Filter by target only
    2. Filter by event_type only
    3. Filter by correlation_id only
    4. Filter by target + event_type
    5. Filter by target + correlation_id
    6. Filter by event_type + correlation_id
    7. Filter by all three
    """
    bus = EventBus()
    await bus.initialize()

    # Publish diverse events
    await bus.publish(ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-A",
        data=ProjectCreatedData(
            project_id="proj-filter-1",
            client_name="Client A",
            client_domain="clienta.com",
            client_contact="contact@clienta.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website",
            created_at=datetime.now(UTC)
        )
    ))

    await bus.publish(ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-B",
        data=ProjectCreatedData(
            project_id="proj-filter-2",
            client_name="Client B",
            client_domain="clientb.com",
            client_contact="contact@clientb.com",
            industry="Medical",
            initial_status=ProjectStatus.LEAD,
            source="Referral",
            created_at=datetime.now(UTC)
        )
    ))

    await bus.publish(TaskCreatedEvent(
        source="brand-magister",
        target="seo-magister",
        correlation_id="corr-A",
        data=TaskCreatedData(
            project_id="proj-filter-1",
            task_id="task-filter-1",
            magister="seo-magister",
            capability="seo_task",
            parameters={}
        )
    ))

    await bus.publish(TaskCreatedEvent(
        source="brand-magister",
        target="content-magister",
        correlation_id="corr-B",
        data=TaskCreatedData(
            project_id="proj-filter-2",
            task_id="task-filter-2",
            magister="content-magister",
            capability="content_task",
            parameters={}
        )
    ))

    # Test 1: Filter by target only
    brand_events = await bus.get_events(target="brand-magister", limit=10)
    assert len(brand_events) == 2
    assert all(e.target == "brand-magister" for e in brand_events)

    # Test 2: Filter by event_type only
    project_events = await bus.get_events(event_type="project.created", limit=10)
    assert len(project_events) == 2
    assert all(e.type == "project.created" for e in project_events)

    # Test 3: Filter by correlation_id only
    corr_a_events = await bus.get_events(correlation_id="corr-A", limit=10)
    assert len(corr_a_events) == 2
    assert all(e.correlation_id == "corr-A" for e in corr_a_events)

    # Test 4: Filter by target + event_type
    brand_projects = await bus.get_events(
        target="brand-magister",
        event_type="project.created",
        limit=10
    )
    assert len(brand_projects) == 2
    assert all(e.target == "brand-magister" and e.type == "project.created" for e in brand_projects)

    # Test 5: Filter by target + correlation_id
    brand_corr_a = await bus.get_events(
        target="brand-magister",
        correlation_id="corr-A",
        limit=10
    )
    assert len(brand_corr_a) == 1
    assert brand_corr_a[0].target == "brand-magister"
    assert brand_corr_a[0].correlation_id == "corr-A"

    # Test 6: Filter by event_type + correlation_id
    task_corr_b = await bus.get_events(
        event_type="task.created",
        correlation_id="corr-B",
        limit=10
    )
    assert len(task_corr_b) == 1
    assert task_corr_b[0].type == "task.created"
    assert task_corr_b[0].correlation_id == "corr-B"

    # Test 7: Filter by all three
    specific_event = await bus.get_events(
        target="seo-magister",
        event_type="task.created",
        correlation_id="corr-A",
        limit=10
    )
    assert len(specific_event) == 1
    assert specific_event[0].target == "seo-magister"
    assert specific_event[0].type == "task.created"
    assert specific_event[0].correlation_id == "corr-A"

    await bus.close()
