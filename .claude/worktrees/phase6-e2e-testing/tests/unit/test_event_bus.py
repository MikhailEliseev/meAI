"""Tests for Event Bus"""

import pytest
import asyncio
from datetime import datetime, timezone
from meai.events.event_bus import EventBus, Message


@pytest.mark.asyncio
async def test_publish_message(tmp_path):
    """Test publishing message to bus"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    bus = EventBus(db_url)
    await bus.initialize()

    message = Message(
        from_agent="architect",
        to_agent="monitoring",
        message_type="AgentCreated",
        priority=1,
        payload={"agent_id": "test-agent"},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    message_id = await bus.publish(message)
    assert message_id is not None
    assert message_id > 0

    await bus.close()


@pytest.mark.asyncio
async def test_subscribe_and_receive(tmp_path):
    """Test subscribing and receiving messages"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    bus = EventBus(db_url)
    await bus.initialize()

    # Subscribe to messages
    queue = await bus.subscribe("monitoring")

    # Publish message
    message = Message(
        from_agent="architect",
        to_agent="monitoring",
        message_type="AgentCreated",
        priority=1,
        payload={"agent_id": "test-agent"},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await bus.publish(message)

    # Start processing
    asyncio.create_task(bus.start_processing())

    # Receive message from queue
    received = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert received is not None
    assert received.message_type == "AgentCreated"
    assert received.to_agent == "monitoring"

    await bus.stop_processing()
    await bus.close()


@pytest.mark.asyncio
async def test_priority_ordering(tmp_path):
    """Test messages processed by priority"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    bus = EventBus(db_url)
    await bus.initialize()

    queue = await bus.subscribe("test-agent")

    # Publish messages with different priorities
    messages = [
        Message(
            from_agent="sender",
            to_agent="test-agent",
            message_type="LowPriority",
            priority=3,  # Low
            payload={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        Message(
            from_agent="sender",
            to_agent="test-agent",
            message_type="HighPriority",
            priority=0,  # Critical
            payload={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        Message(
            from_agent="sender",
            to_agent="test-agent",
            message_type="MediumPriority",
            priority=2,  # Normal
            payload={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    ]

    for msg in messages:
        await bus.publish(msg)

    # Start processing
    asyncio.create_task(bus.start_processing())

    # Receive messages - should be in priority order
    received = []
    for _ in range(3):
        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        received.append(msg.message_type)

    # Should receive in priority order: P0 (High), P2 (Medium), P3 (Low)
    assert received[0] == "HighPriority"
    assert received[1] == "MediumPriority"
    assert received[2] == "LowPriority"

    await bus.stop_processing()
    await bus.close()


@pytest.mark.asyncio
async def test_mark_processed(tmp_path):
    """Test marking message as processed"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    bus = EventBus(db_url)
    await bus.initialize()

    message = Message(
        from_agent="sender",
        to_agent="receiver",
        message_type="TestMessage",
        priority=1,
        payload={},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    message_id = await bus.publish(message)

    # Mark as processed
    await bus.mark_processed(message_id)

    # Verify message is marked
    is_processed = await bus.is_processed(message_id)
    assert is_processed is True

    await bus.close()


@pytest.mark.asyncio
async def test_crash_recovery(tmp_path):
    """Test unprocessed messages are recovered after crash"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    # First session - publish messages
    bus1 = EventBus(db_url)
    await bus1.initialize()

    for i in range(3):
        message = Message(
            from_agent="sender",
            to_agent="receiver",
            message_type=f"Message{i}",
            priority=1,
            payload={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await bus1.publish(message)

    await bus1.close()

    # Second session - recover unprocessed messages
    bus2 = EventBus(db_url)
    await bus2.initialize()

    queue = await bus2.subscribe("receiver")
    asyncio.create_task(bus2.start_processing())

    # Should receive all 3 unprocessed messages
    received = []
    for _ in range(3):
        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        received.append(msg.message_type)

    assert len(received) == 3
    assert "Message0" in received
    assert "Message1" in received
    assert "Message2" in received

    await bus2.stop_processing()
    await bus2.close()


@pytest.mark.asyncio
async def test_broadcast_messages(tmp_path):
    """Test broadcast messages to all subscribers"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    bus = EventBus(db_url)
    await bus.initialize()

    # Subscribe multiple agents
    queue1 = await bus.subscribe("agent1")
    queue2 = await bus.subscribe("agent2")

    # Publish broadcast message
    message = Message(
        from_agent="sender",
        to_agent="*",  # Broadcast
        message_type="BroadcastMessage",
        priority=1,
        payload={},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await bus.publish(message)

    asyncio.create_task(bus.start_processing())

    # Both agents should receive the message
    msg1 = await asyncio.wait_for(queue1.get(), timeout=2.0)
    msg2 = await asyncio.wait_for(queue2.get(), timeout=2.0)

    assert msg1.message_type == "BroadcastMessage"
    assert msg2.message_type == "BroadcastMessage"

    await bus.stop_processing()
    await bus.close()
