# tests/unit/test_event_bus.py
import pytest
import asyncio
from meai.events.event_bus import EventBus, Event
from meai.events.project_events import ProjectCreatedEvent, ProjectCreatedData
from meai.events.base import ProjectStatus
from datetime import datetime, UTC


@pytest.mark.asyncio
async def test_event_bus_initialization():
    """Test EventBus can be initialized"""
    event_bus = EventBus()
    assert event_bus is not None


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    """Test publishing and subscribing to events"""
    event_bus = EventBus()
    received_events = []

    # Subscribe to events
    async def handler(event: Event):
        received_events.append(event)

    event_bus.subscribe("test.event", handler)

    # Publish event
    await event_bus.publish(Event(
        event_type="test.event",
        payload={"message": "Hello"},
    ))

    # Give event bus time to process
    await asyncio.sleep(0.1)

    assert len(received_events) == 1
    assert received_events[0].event_type == "test.event"
    assert received_events[0].payload["message"] == "Hello"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    """Test multiple subscribers receive the same event"""
    event_bus = EventBus()
    received_1 = []
    received_2 = []

    async def handler_1(event: Event):
        received_1.append(event)

    async def handler_2(event: Event):
        received_2.append(event)

    event_bus.subscribe("test.event", handler_1)
    event_bus.subscribe("test.event", handler_2)

    await event_bus.publish(Event(
        event_type="test.event",
        payload={"data": "test"},
    ))

    await asyncio.sleep(0.1)

    assert len(received_1) == 1
    assert len(received_2) == 1


@pytest.mark.asyncio
async def test_store_event_with_correlation():
    """Test storing event with correlation_id"""
    bus = EventBus()
    await bus.initialize()

    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-123",
        data=ProjectCreatedData(
            project_id="proj-001",
            client_name="Test Client",
            client_domain="testclient.com",
            client_contact="contact@testclient.com",
            industry="Healthcare",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )

    event_id = await bus.publish(event)

    # Verify stored with correlation_id
    stored = await bus._get_event_by_id(str(event.id))
    assert stored["correlation_id"] == "corr-123"

    await bus.close()


@pytest.mark.asyncio
async def test_publish_base_event():
    """Test publishing BaseEvent instance"""
    bus = EventBus()
    await bus.initialize()

    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="proj-002",
            client_name="Test Client",
            client_domain="testclient.com",
            client_contact="contact@testclient.com",
            industry="Medical Marketing",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(UTC)
        )
    )

    event_id = await bus.publish(event)

    assert event_id == str(event.id)

    # Verify stored correctly
    stored = await bus._get_event_by_id(event_id)
    assert stored["type"] == "project.created"
    assert stored["source"] == "operator"
    assert stored["target"] == "brand-magister"
    assert stored["priority"] == 1  # P1 for project events

    await bus.close()
