"""Integration tests for Event Store + Event Bus"""

import pytest
import asyncio
from datetime import datetime, timezone
from meai.events.event_store import EventStore, Event
from meai.events.event_bus import EventBus, Message


@pytest.mark.asyncio
async def test_event_store_and_bus_integration(tmp_path):
    """Test Event Store and Event Bus work together"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    # Initialize both
    store = EventStore(db_url)
    bus = EventBus(db_url)
    await store.initialize()
    await bus.initialize()

    # Scenario: Create agent workflow
    # 1. Append event to Event Store (audit log)
    event = Event(
        aggregate_id="agent-123",
        aggregate_type="agent",
        event_type="AgentCreated",
        event_version=1,
        payload={"name": "seo-agent", "type": "subagent"},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    event_id = await store.append_event(event)
    assert event_id is not None

    # 2. Publish message to Event Bus (notify monitoring)
    message = Message(
        from_agent="architect",
        to_agent="monitoring",
        message_type="AgentCreated",
        priority=1,
        payload={"agent_id": "agent-123"},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    message_id = await bus.publish(message)
    assert message_id is not None

    # 3. Subscribe and receive message
    queue = await bus.subscribe("monitoring")
    asyncio.create_task(bus.start_processing())

    received = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert received.message_type == "AgentCreated"
    assert received.payload["agent_id"] == "agent-123"

    # 4. Verify event in store
    events = await store.get_events(aggregate_id="agent-123")
    assert len(events) == 1
    assert events[0].event_type == "AgentCreated"

    await bus.stop_processing()
    await store.close()
    await bus.close()


@pytest.mark.asyncio
async def test_event_replay_with_messages(tmp_path):
    """Test event replay doesn't trigger messages"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    bus = EventBus(db_url)
    await store.initialize()
    await bus.initialize()

    # Track side effects (messages published)
    messages_published = []

    def side_effect_handler(event):
        # Simulate publishing message as side effect
        messages_published.append(event.event_type)

    # Append event with side effect
    event = Event(
        aggregate_id="agent-123",
        aggregate_type="agent",
        event_type="AgentCreated",
        event_version=1,
        payload={"name": "test-agent"},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await store.append_event(event, side_effect_handler=side_effect_handler)

    # Side effect should be called during append
    assert len(messages_published) == 1

    # Clear side effects
    messages_published.clear()

    # Replay events - side effects should NOT be called
    await store.replay_events(
        aggregate_id="agent-123",
        side_effect_handler=side_effect_handler,
        replaying=True,
    )

    # Side effects should be skipped during replay
    assert len(messages_published) == 0

    await store.close()
    await bus.close()


@pytest.mark.asyncio
async def test_concurrent_event_and_message_writes(tmp_path):
    """Test concurrent writes to Event Store and Event Bus"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    bus = EventBus(db_url)
    await store.initialize()
    await bus.initialize()

    # Simulate concurrent agent creation
    async def create_agent(agent_id: str):
        # Append event
        event = Event(
            aggregate_id=agent_id,
            aggregate_type="agent",
            event_type="AgentCreated",
            event_version=1,
            payload={"name": agent_id},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await store.append_event(event)

        # Publish message
        message = Message(
            from_agent="architect",
            to_agent="monitoring",
            message_type="AgentCreated",
            priority=1,
            payload={"agent_id": agent_id},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await bus.publish(message)

    # Create 5 agents concurrently
    await asyncio.gather(
        create_agent("agent-1"),
        create_agent("agent-2"),
        create_agent("agent-3"),
        create_agent("agent-4"),
        create_agent("agent-5"),
    )

    # Verify all events stored
    events = await store.get_events(event_type="AgentCreated")
    assert len(events) == 5

    # Verify all messages published
    queue = await bus.subscribe("monitoring")
    asyncio.create_task(bus.start_processing())

    received = []
    for _ in range(5):
        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        received.append(msg.payload["agent_id"])

    assert len(received) == 5
    assert "agent-1" in received
    assert "agent-5" in received

    await bus.stop_processing()
    await store.close()
    await bus.close()


@pytest.mark.asyncio
async def test_priority_messages_with_events(tmp_path):
    """Test priority messages are processed in order with events"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    bus = EventBus(db_url)
    await store.initialize()
    await bus.initialize()

    queue = await bus.subscribe("monitoring")

    # Create events and messages with different priorities
    scenarios = [
        ("agent-1", 3, "LowPriority"),  # P3 - Low
        ("agent-2", 0, "HighPriority"),  # P0 - Critical
        ("agent-3", 2, "MediumPriority"),  # P2 - Normal
    ]

    for agent_id, priority, label in scenarios:
        # Append event
        event = Event(
            aggregate_id=agent_id,
            aggregate_type="agent",
            event_type="AgentCreated",
            event_version=1,
            payload={"name": agent_id, "priority": priority},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await store.append_event(event)

        # Publish message
        message = Message(
            from_agent="architect",
            to_agent="monitoring",
            message_type=label,
            priority=priority,
            payload={"agent_id": agent_id},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await bus.publish(message)

    # Start processing
    asyncio.create_task(bus.start_processing())

    # Receive messages - should be in priority order
    received = []
    for _ in range(3):
        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        received.append(msg.message_type)

    # Should receive in priority order: P0, P2, P3
    assert received[0] == "HighPriority"
    assert received[1] == "MediumPriority"
    assert received[2] == "LowPriority"

    # Verify all events stored
    events = await store.get_events(event_type="AgentCreated")
    assert len(events) == 3

    await bus.stop_processing()
    await store.close()
    await bus.close()
