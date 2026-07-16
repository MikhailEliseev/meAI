# tests/unit/test_event_bus.py
import pytest
import asyncio
from meai.events.event_bus import EventBus, Event


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
