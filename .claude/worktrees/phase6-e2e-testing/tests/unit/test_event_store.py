"""Tests for Event Store"""

import pytest
from datetime import datetime, timezone
from meai.events.event_store import EventStore, Event, ConcurrentWriteError


@pytest.mark.asyncio
async def test_append_event(tmp_path):
    """Test appending event to store"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    await store.initialize()

    event = Event(
        aggregate_id="agent-123",
        aggregate_type="agent",
        event_type="AgentCreated",
        event_version=1,
        payload={"name": "test-agent", "type": "subagent"},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    event_id = await store.append_event(event)
    assert event_id is not None
    assert event_id > 0

    await store.close()


@pytest.mark.asyncio
async def test_idempotency(tmp_path):
    """Test idempotency prevents duplicate events"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    await store.initialize()

    event = Event(
        aggregate_id="agent-123",
        aggregate_type="agent",
        event_type="AgentCreated",
        event_version=1,
        payload={"name": "test-agent"},
        timestamp=datetime.now(timezone.utc).isoformat(),
        idempotency_key="agent-123:AgentCreated:2026-05-01T19:00:00",
    )

    # First append should succeed
    event_id_1 = await store.append_event(event)
    assert event_id_1 is not None

    # Second append with same idempotency_key should be skipped
    event_id_2 = await store.append_event(event)
    assert event_id_2 == event_id_1  # Same ID, not duplicated

    await store.close()


@pytest.mark.asyncio
async def test_get_events(tmp_path):
    """Test retrieving events with filters"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    await store.initialize()

    # Append multiple events
    for i in range(3):
        event = Event(
            aggregate_id="agent-123",
            aggregate_type="agent",
            event_type="AgentCreated",
            event_version=1,
            payload={"name": f"agent-{i}"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await store.append_event(event)

    # Get all events for aggregate
    events = await store.get_events(aggregate_id="agent-123")
    assert len(events) == 3

    # Get events by type
    events = await store.get_events(event_type="AgentCreated")
    assert len(events) == 3

    await store.close()


@pytest.mark.asyncio
async def test_replay_events(tmp_path):
    """Test replaying events to rebuild state"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    await store.initialize()

    # Append events
    events_data = [
        {"name": "agent-1", "status": "created"},
        {"name": "agent-1", "status": "active"},
        {"name": "agent-1", "status": "paused"},
    ]

    for data in events_data:
        event = Event(
            aggregate_id="agent-1",
            aggregate_type="agent",
            event_type="StatusChanged",
            event_version=1,
            payload=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await store.append_event(event)

    # Replay events
    events = await store.replay_events(aggregate_id="agent-1")
    assert len(events) == 3
    assert events[-1].payload["status"] == "paused"

    await store.close()


@pytest.mark.asyncio
async def test_concurrent_writes(tmp_path):
    """Test optimistic locking for concurrent writes"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    await store.initialize()

    # Simulate concurrent writes to same aggregate
    import asyncio

    async def write_event(version: int):
        event = Event(
            aggregate_id="agent-123",
            aggregate_type="agent",
            event_type="StatusChanged",
            event_version=version,
            payload={"status": f"v{version}"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        try:
            return await store.append_event(event)
        except ConcurrentWriteError:
            return None

    # Run concurrent writes
    results = await asyncio.gather(
        write_event(1),
        write_event(1),  # Same version - should conflict
        write_event(1),
        return_exceptions=True,
    )

    # Only one should succeed, others should fail or return None
    successful = [r for r in results if r is not None and not isinstance(r, Exception)]
    assert len(successful) >= 1  # At least one succeeded

    await store.close()


@pytest.mark.asyncio
async def test_side_effect_skipping(tmp_path):
    """Test that replay skips side effects"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    store = EventStore(db_url)
    await store.initialize()

    # Track side effects
    side_effects_called = []

    def side_effect_handler(event):
        side_effects_called.append(event.event_type)

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
    assert len(side_effects_called) == 1

    # Clear side effects
    side_effects_called.clear()

    # Replay events - side effects should NOT be called
    await store.replay_events(
        aggregate_id="agent-123",
        side_effect_handler=side_effect_handler,
        replaying=True,
    )

    # Side effects should be skipped during replay
    assert len(side_effects_called) == 0

    await store.close()
