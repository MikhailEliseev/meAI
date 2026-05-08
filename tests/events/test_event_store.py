"""Tests for Event Store - immutable audit log for event replay and debugging.

This module tests the Event Store implementation:
- Append-only storage (no updates/deletes)
- Event retrieval by ID
- Dynamic event class reconstruction
- Schema and indexes
"""

import pytest
from datetime import datetime, UTC

from meai.events.event_store import EventStore
from meai.events.project_events import ProjectCreatedEvent, ProjectCreatedData
from meai.events.base import ProjectStatus


@pytest.mark.asyncio
async def test_append_and_get_event():
    """Test appending event to store and retrieving it by ID."""
    # Arrange
    store = EventStore()
    await store.initialize()

    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="test-project-001",
            client_name="Test Client",
            client_domain="testclient.com",
            client_contact="contact@testclient.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC),
            notes="Test project for event store"
        )
    )

    # Act
    await store.append(event)
    retrieved = await store.get_by_id(str(event.id))

    # Assert
    assert retrieved is not None
    assert retrieved.id == event.id
    assert retrieved.type == "project.created"
    assert retrieved.source == "operator"
    assert retrieved.target == "brand-magister"
    assert retrieved.priority == 1  # ProjectCreatedEvent has priority=1
    assert isinstance(retrieved, ProjectCreatedEvent)
    assert retrieved.data.project_id == "test-project-001"
    assert retrieved.data.client_name == "Test Client"

    await store.close()


@pytest.mark.asyncio
async def test_get_nonexistent_event():
    """Test retrieving non-existent event returns None."""
    # Arrange
    store = EventStore()
    await store.initialize()

    # Act
    retrieved = await store.get_by_id("nonexistent-id")

    # Assert
    assert retrieved is None

    await store.close()


@pytest.mark.asyncio
async def test_append_without_initialize_raises_error():
    """Test that appending without initialization raises RuntimeError."""
    # Arrange
    store = EventStore()
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="test-project-002",
            client_name="Test Client 2",
            client_domain="testclient2.com",
            client_contact="contact@testclient2.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Referral",
            created_at=datetime.now(UTC)
        )
    )

    # Act & Assert
    with pytest.raises(RuntimeError, match="not initialized"):
        await store.append(event)


@pytest.mark.asyncio
async def test_multiple_events_stored_independently():
    """Test that multiple events are stored independently."""
    # Arrange
    store = EventStore()
    await store.initialize()

    event1 = ProjectCreatedEvent(
        source="operator",
        target="seo-magister",
        data=ProjectCreatedData(
            project_id="project-001",
            client_name="Client 1",
            client_domain="client1.com",
            client_contact="contact@client1.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )

    event2 = ProjectCreatedEvent(
        source="operator",
        target="content-magister",
        data=ProjectCreatedData(
            project_id="project-002",
            client_name="Client 2",
            client_domain="client2.com",
            client_contact="contact@client2.com",
            industry="Finance",
            initial_status=ProjectStatus.PRE_SALE,
            source="Referral",
            created_at=datetime.now(UTC)
        )
    )

    # Act
    await store.append(event1)
    await store.append(event2)

    retrieved1 = await store.get_by_id(str(event1.id))
    retrieved2 = await store.get_by_id(str(event2.id))

    # Assert
    assert retrieved1 is not None
    assert retrieved2 is not None
    assert retrieved1.id == event1.id
    assert retrieved2.id == event2.id
    assert retrieved1.data.client_name == "Client 1"
    assert retrieved2.data.client_name == "Client 2"

    await store.close()


@pytest.mark.asyncio
async def test_get_by_correlation():
    """Test retrieving events by correlation_id."""
    # Arrange
    store = EventStore()
    await store.initialize()

    # Import TaskCreatedEvent
    from meai.events.task_events import TaskCreatedEvent, TaskCreatedData

    # Create correlation chain
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-123",
        data=ProjectCreatedData(
            project_id="project-001",
            client_name="Client 1",
            client_domain="client1.com",
            client_contact="contact@client1.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )

    event2 = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-123",  # Same correlation
        data=TaskCreatedData(
            project_id="project-001",
            task_id="task-001",
            magister="brand-magister",
            capability="brand_analysis",
            parameters={"depth": "full"}
        )
    )

    event3 = ProjectCreatedEvent(
        source="operator",
        target="content-magister",
        correlation_id="corr-456",  # Different correlation
        data=ProjectCreatedData(
            project_id="project-002",
            client_name="Client 2",
            client_domain="client2.com",
            client_contact="contact@client2.com",
            industry="Finance",
            initial_status=ProjectStatus.PRE_SALE,
            source="Referral",
            created_at=datetime.now(UTC)
        )
    )

    # Act
    await store.append(event1)
    await store.append(event2)
    await store.append(event3)

    # Get correlation chain
    chain = await store.get_by_correlation("corr-123")

    # Assert
    assert len(chain) == 2
    assert all(e.correlation_id == "corr-123" for e in chain)
    assert chain[0].type == "project.created"
    assert chain[1].type == "task.created"

    await store.close()


@pytest.mark.asyncio
async def test_get_by_correlation_empty():
    """Test retrieving events by non-existent correlation_id returns empty list."""
    # Arrange
    store = EventStore()
    await store.initialize()

    # Act
    chain = await store.get_by_correlation("nonexistent-correlation")

    # Assert
    assert chain == []

    await store.close()


@pytest.mark.asyncio
async def test_get_by_time_range():
    """Test retrieving events by time range."""
    # Arrange
    import asyncio
    from meai.events.task_events import TaskCreatedEvent, TaskCreatedData

    store = EventStore()
    await store.initialize()

    now = datetime.now(UTC)

    # Create events with different timestamps
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="project-001",
            client_name="Client 1",
            client_domain="client1.com",
            client_contact="contact@client1.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )
    await store.append(event1)

    # Wait a bit
    await asyncio.sleep(0.1)

    event2 = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        data=TaskCreatedData(
            project_id="project-001",
            task_id="task-001",
            magister="brand-magister",
            capability="brand_analysis",
            parameters={"depth": "full"}
        )
    )
    await store.append(event2)

    # Get events from start time
    events = await store.get_by_time_range(from_time=now)

    # Assert
    assert len(events) == 2
    assert events[0].id == event1.id
    assert events[1].id == event2.id

    await store.close()


@pytest.mark.asyncio
async def test_get_by_time_range_with_to_time():
    """Test retrieving events with both from_time and to_time."""
    # Arrange
    import asyncio
    from meai.events.task_events import TaskCreatedEvent, TaskCreatedData

    store = EventStore()
    await store.initialize()

    # Create first event
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="project-001",
            client_name="Client 1",
            client_domain="client1.com",
            client_contact="contact@client1.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )
    await store.append(event1)

    # Wait and capture middle time
    await asyncio.sleep(0.1)
    middle_time = datetime.now(UTC)
    await asyncio.sleep(0.1)

    # Create second event
    event2 = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        data=TaskCreatedData(
            project_id="project-001",
            task_id="task-001",
            magister="brand-magister",
            capability="brand_analysis",
            parameters={"depth": "full"}
        )
    )
    await store.append(event2)

    # Get events before middle_time (should only get event1)
    events = await store.get_by_time_range(to_time=middle_time)

    # Assert
    assert len(events) == 1
    assert events[0].id == event1.id

    await store.close()


@pytest.mark.asyncio
async def test_get_by_time_range_no_bounds():
    """Test retrieving events with no time bounds (all events)."""
    # Arrange
    store = EventStore()
    await store.initialize()

    # Create multiple events
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="project-001",
            client_name="Client 1",
            client_domain="client1.com",
            client_contact="contact@client1.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )
    await store.append(event1)

    event2 = ProjectCreatedEvent(
        source="operator",
        target="content-magister",
        data=ProjectCreatedData(
            project_id="project-002",
            client_name="Client 2",
            client_domain="client2.com",
            client_contact="contact@client2.com",
            industry="Finance",
            initial_status=ProjectStatus.PRE_SALE,
            source="Referral",
            created_at=datetime.now(UTC)
        )
    )
    await store.append(event2)

    # Get all events (no time bounds)
    events = await store.get_by_time_range()

    # Assert
    assert len(events) == 2
    assert events[0].id == event1.id
    assert events[1].id == event2.id

    await store.close()


@pytest.mark.asyncio
async def test_get_by_time_range_with_limit():
    """Test retrieving events with limit."""
    # Arrange
    store = EventStore()
    await store.initialize()

    # Create 3 events
    for i in range(3):
        event = ProjectCreatedEvent(
            source="operator",
            target="brand-magister",
            data=ProjectCreatedData(
                project_id=f"project-{i:03d}",
                client_name=f"Client {i}",
                client_domain=f"client{i}.com",
                client_contact=f"contact@client{i}.com",
                industry="Healthcare",
                initial_status=ProjectStatus.LEAD,
                source="Website Form",
                created_at=datetime.now(UTC)
            )
        )
        await store.append(event)

    # Get events with limit=2
    events = await store.get_by_time_range(limit=2)

    # Assert
    assert len(events) == 2

    await store.close()


@pytest.mark.asyncio
async def test_get_by_time_range_empty():
    """Test retrieving events with time range that has no events."""
    # Arrange
    from datetime import timedelta

    store = EventStore()
    await store.initialize()

    # Create event
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="project-001",
            client_name="Client 1",
            client_domain="client1.com",
            client_contact="contact@client1.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )
    await store.append(event)

    # Query for events in the future
    future_time = datetime.now(UTC) + timedelta(days=1)
    events = await store.get_by_time_range(from_time=future_time)

    # Assert
    assert events == []

    await store.close()
