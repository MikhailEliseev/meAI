# Event Store API Reference

> Immutable event log with idempotency and replay

## Overview

**Event Store** — компонент для event sourcing. Хранит immutable audit log всех событий в системе с поддержкой idempotency и event replay.

## Class: `EventStore`

### Constructor

```python
from meai.events.event_store import EventStore

event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
await event_store.initialize()
```

**Parameters:**
- `database_url` (str) — SQLAlchemy database URL

---

## Methods

### `initialize() -> None`

Initialize database and create events table.

**Parameters:**
- None

**Returns:**
- None

**Example:**

```python
event_store = EventStore("sqlite+aiosqlite:///:memory:")
await event_store.initialize()

print("✅ Event Store initialized")
```

**What happens:**
1. Creates async engine
2. Creates `events` table
3. Creates indexes for performance

---

### `append_event(event: Event, side_effect_handler: Callable = None) -> int`

Append event to store with idempotency.

**Parameters:**
- `event` (Event) — Event to append
- `side_effect_handler` (Callable, optional) — Handler for side effects (not called during replay)

**Returns:**
- `int` — Event ID

**Raises:**
- `ConcurrentWriteError` — If concurrent write detected

**Example:**

```python
from meai.events.event_store import Event
from datetime import datetime, timezone

event = Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={
        "task_id": "task-456",
        "result": "success",
        "duration_ms": 1234
    },
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-456-completed"
)

event_id = await event_store.append_event(event)
print(f"Event stored with ID: {event_id}")
```

**Idempotency:**

```python
# First call - creates event
event_id_1 = await event_store.append_event(event)

# Second call with same idempotency_key - returns existing ID
event_id_2 = await event_store.append_event(event)

assert event_id_1 == event_id_2  # Same ID, no duplicate
```

---

### `get_events(...) -> list[Event]`

Get events with filters.

**Parameters:**
- `aggregate_id` (str, optional) — Filter by aggregate ID
- `aggregate_type` (str, optional) — Filter by aggregate type
- `event_type` (str, optional) — Filter by event type
- `from_timestamp` (str, optional) — Filter events after this timestamp
- `to_timestamp` (str, optional) — Filter events before this timestamp

**Returns:**
- `list[Event]` — List of events matching filters

**Example:**

```python
# Get all events for an agent
events = await event_store.get_events(
    aggregate_id="agent-123"
)

# Get specific event type
events = await event_store.get_events(
    aggregate_id="agent-123",
    event_type="task_completed"
)

# Get events in time range
events = await event_store.get_events(
    aggregate_id="agent-123",
    from_timestamp="2026-05-01T00:00:00Z",
    to_timestamp="2026-05-02T00:00:00Z"
)

# Get all events of a type
events = await event_store.get_events(
    event_type="checkpoint_created"
)
```

---

### `replay_events(...) -> list[Event]`

Replay events for aggregate.

**Parameters:**
- `aggregate_id` (str) — Aggregate to replay
- `from_timestamp` (str, optional) — Start timestamp
- `to_timestamp` (str, optional) — End timestamp
- `side_effect_handler` (Callable, optional) — Handler (NOT called if replaying=True)
- `replaying` (bool) — If True, skip side effects (default: True)

**Returns:**
- `list[Event]` — List of replayed events

**Example:**

```python
# Replay all events for agent
events = await event_store.replay_events(
    aggregate_id="agent-123"
)

print(f"Replayed {len(events)} events")

# Replay with time range
events = await event_store.replay_events(
    aggregate_id="agent-123",
    from_timestamp="2026-05-01T00:00:00Z"
)

# Replay with side effects (dangerous!)
def handle_side_effect(event: Event):
    print(f"Side effect: {event.event_type}")

events = await event_store.replay_events(
    aggregate_id="agent-123",
    side_effect_handler=handle_side_effect,
    replaying=False  # Enable side effects
)
```

---

### `close() -> None`

Close database connection.

**Parameters:**
- None

**Returns:**
- None

**Example:**

```python
await event_store.close()
print("✅ Event Store closed")
```

---

## Data Classes

### `Event`

Immutable event representing a fact that happened.

**Fields:**
- `aggregate_id` (str) — ID of the aggregate (e.g., "agent-123")
- `aggregate_type` (str) — Type of aggregate (e.g., "agent")
- `event_type` (str) — Type of event (e.g., "task_completed")
- `event_version` (int) — Event schema version
- `payload` (dict) — Event data
- `timestamp` (str) — ISO 8601 timestamp
- `idempotency_key` (str, optional) — Unique key for idempotency
- `id` (int, optional) — Event ID (set after storage)

**Example:**

```python
from meai.events.event_store import Event
from datetime import datetime, timezone

event = Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="agent_created",
    event_version=1,
    payload={
        "agent_id": "agent-123",
        "department": "seo",
        "role": "SEO specialist"
    },
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="agent-123-created"
)
```

---

## Event Types

Common event types in meAI:

### Agent Events

```python
# Agent created
Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="agent_created",
    payload={"agent_id": "agent-123", "department": "seo"}
)

# Task completed
Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="task_completed",
    payload={"task_id": "task-456", "result": "success"}
)

# Agent deleted
Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="agent_deleted",
    payload={"agent_id": "agent-123", "reason": "cleanup"}
)
```

### System Events

```python
# Checkpoint created
Event(
    aggregate_id="system",
    aggregate_type="checkpoint",
    event_type="checkpoint_created",
    payload={"name": "before-migration", "snapshot_path": "/path"}
)

# System started
Event(
    aggregate_id="system",
    aggregate_type="system",
    event_type="system_started",
    payload={"version": "0.1.0", "timestamp": "..."}
)
```

---

## Idempotency

Event Store гарантирует idempotency через `idempotency_key`:

```python
# Create event with idempotency key
event = Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={"task_id": "task-456"},
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-456-completed"  # Unique key
)

# First append - creates event
id1 = await event_store.append_event(event)

# Second append - returns existing ID
id2 = await event_store.append_event(event)

assert id1 == id2  # No duplicate created
```

**Best practices:**
- Always use idempotency_key for important events
- Format: `{aggregate_id}-{event_type}-{unique_id}`
- Examples:
  - `agent-123-created`
  - `task-456-completed`
  - `checkpoint-before-migration-created`

---

## Event Replay

Event replay восстанавливает состояние из событий:

```python
# Get all events for agent
events = await event_store.replay_events(
    aggregate_id="agent-123"
)

# Rebuild state
agent_state = {}
for event in events:
    if event.event_type == "agent_created":
        agent_state["id"] = event.payload["agent_id"]
        agent_state["department"] = event.payload["department"]
    
    elif event.event_type == "task_completed":
        if "tasks" not in agent_state:
            agent_state["tasks"] = []
        agent_state["tasks"].append(event.payload["task_id"])

print(f"Agent state: {agent_state}")
```

---

## Side Effects

Side effects выполняются только при append, не при replay:

```python
def send_notification(event: Event):
    """Side effect: send notification"""
    print(f"📧 Notification: {event.event_type}")

# Append with side effect
await event_store.append_event(
    event,
    side_effect_handler=send_notification
)
# Output: 📧 Notification: task_completed

# Replay WITHOUT side effects
events = await event_store.replay_events(
    aggregate_id="agent-123",
    replaying=True  # Default
)
# No notifications sent during replay
```

---

## Database Schema

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL,
    payload TEXT NOT NULL,  -- JSON
    timestamp TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_events_aggregate 
    ON events(aggregate_id, aggregate_type);

CREATE INDEX idx_events_type 
    ON events(event_type);

CREATE INDEX idx_events_timestamp 
    ON events(timestamp);

CREATE INDEX idx_events_idempotency 
    ON events(idempotency_key);
```

---

## Best Practices

### 1. Always Use Idempotency Keys

```python
# ✅ Good: With idempotency key
event = Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={"task_id": "task-456"},
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-456-completed"
)

# ❌ Bad: Without idempotency key
event = Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={"task_id": "task-456"},
    timestamp=datetime.now(timezone.utc).isoformat()
    # No idempotency_key - duplicates possible!
)
```

### 2. Use Descriptive Event Types

```python
# ✅ Good: Clear event types
"agent_created"
"task_completed"
"checkpoint_created"
"system_started"

# ❌ Bad: Vague event types
"created"
"done"
"event"
```

### 3. Include Relevant Data in Payload

```python
# ✅ Good: Complete payload
payload = {
    "task_id": "task-456",
    "result": "success",
    "duration_ms": 1234,
    "agent_id": "agent-123",
    "timestamp": "2026-05-02T10:00:00Z"
}

# ❌ Bad: Minimal payload
payload = {
    "result": "success"
}
```

### 4. Version Your Events

```python
# Version 1
Event(
    event_type="task_completed",
    event_version=1,
    payload={"task_id": "task-456", "result": "success"}
)

# Version 2 (added duration)
Event(
    event_type="task_completed",
    event_version=2,
    payload={
        "task_id": "task-456",
        "result": "success",
        "duration_ms": 1234
    }
)
```

---

## Error Handling

```python
from meai.events.event_store import ConcurrentWriteError

try:
    event_id = await event_store.append_event(event)
except ConcurrentWriteError as e:
    print(f"Concurrent write detected: {e}")
except Exception as e:
    print(f"Failed to append event: {e}")
```

---

## Performance

- **Append:** ~5-10ms per event
- **Get events:** ~10-50ms (depends on filters)
- **Replay:** ~50-200ms (depends on event count)
- **Idempotency check:** ~5ms

**Optimization tips:**
- Use specific filters (aggregate_id, event_type)
- Limit time ranges
- Use indexes (already created)
- Batch operations when possible

---

## See Also

- [Event Bus API](event-bus.md) — Async message queue
- [Rollback API](rollback.md) — Event replay for recovery
- [Architecture: Event Sourcing](../architecture/event-sourcing.md)
