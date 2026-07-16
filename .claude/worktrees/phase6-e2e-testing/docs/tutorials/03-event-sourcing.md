# Tutorial: Event Sourcing

> Logging and replaying events for audit and recovery

## Overview

Event Sourcing — это паттерн, где все изменения сохраняются как immutable события. В этом туториале мы научимся логировать события и восстанавливать состояние через replay.

**Time:** ~10 minutes  
**Level:** Intermediate

---

## Step 1: Understanding Events

Каждое событие — это факт, который произошёл:

```python
from meai.events.event_store import Event
from datetime import datetime, timezone

event = Event(
    aggregate_id="agent-123",      # Кто/что
    aggregate_type="agent",         # Тип сущности
    event_type="task_completed",    # Что произошло
    event_version=1,                # Версия схемы
    payload={                       # Данные события
        "task_id": "task-456",
        "result": "success",
        "duration_ms": 1234
    },
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-456-completed"  # Защита от дубликатов
)
```

---

## Step 2: Logging Events

```python
from meai.events.event_store import EventStore

# Initialize
event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
await event_store.initialize()

# Log agent creation
event = Event(
    aggregate_id="seo-agent",
    aggregate_type="agent",
    event_type="agent_created",
    event_version=1,
    payload={
        "agent_id": "seo-agent",
        "department": "seo",
        "role": "SEO specialist"
    },
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="seo-agent-created"
)

event_id = await event_store.append_event(event)
print(f"✅ Event logged: {event_id}")
```

---

## Step 3: Logging Agent Activity

```python
# Task started
await event_store.append_event(Event(
    aggregate_id="seo-agent",
    aggregate_type="agent",
    event_type="task_started",
    event_version=1,
    payload={"task_id": "task-123", "action": "analyze_competitors"},
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-123-started"
))

# Task completed
await event_store.append_event(Event(
    aggregate_id="seo-agent",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={
        "task_id": "task-123",
        "result": "success",
        "duration_ms": 5400000  # 90 minutes
    },
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-123-completed"
))
```

---

## Step 4: Querying Events

```python
# Get all events for agent
events = await event_store.get_events(
    aggregate_id="seo-agent"
)

print(f"Total events: {len(events)}")
for event in events:
    print(f"  {event.event_type}: {event.payload}")

# Get specific event type
completed_tasks = await event_store.get_events(
    aggregate_id="seo-agent",
    event_type="task_completed"
)

print(f"Completed tasks: {len(completed_tasks)}")

# Get events in time range
today_events = await event_store.get_events(
    aggregate_id="seo-agent",
    from_timestamp="2026-05-02T00:00:00Z",
    to_timestamp="2026-05-02T23:59:59Z"
)

print(f"Today's events: {len(today_events)}")
```

---

## Step 5: Event Replay

Восстановление состояния из событий:

```python
# Get all events
events = await event_store.replay_events(
    aggregate_id="seo-agent"
)

# Rebuild agent state
agent_state = {
    "agent_id": None,
    "department": None,
    "tasks_completed": 0,
    "total_duration_ms": 0
}

for event in events:
    if event.event_type == "agent_created":
        agent_state["agent_id"] = event.payload["agent_id"]
        agent_state["department"] = event.payload["department"]
    
    elif event.event_type == "task_completed":
        agent_state["tasks_completed"] += 1
        agent_state["total_duration_ms"] += event.payload["duration_ms"]

print(f"Agent state: {agent_state}")
# Output: {
#   "agent_id": "seo-agent",
#   "department": "seo",
#   "tasks_completed": 5,
#   "total_duration_ms": 27000000
# }
```

---

## Step 6: Idempotency

Защита от дубликатов:

```python
# First append
event_id_1 = await event_store.append_event(Event(
    aggregate_id="seo-agent",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={"task_id": "task-789"},
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-789-completed"
))

# Second append with same key - returns existing ID
event_id_2 = await event_store.append_event(Event(
    aggregate_id="seo-agent",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={"task_id": "task-789"},
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-789-completed"  # Same key!
))

assert event_id_1 == event_id_2  # No duplicate created
```

---

## Step 7: Complete Example

```python
import asyncio
from datetime import datetime, timezone
from meai.events.event_store import EventStore, Event

async def main():
    # Initialize
    event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
    await event_store.initialize()
    
    # Log agent lifecycle
    events_to_log = [
        ("agent_created", {"agent_id": "seo-agent", "department": "seo"}),
        ("task_started", {"task_id": "task-1", "action": "research"}),
        ("task_completed", {"task_id": "task-1", "result": "success"}),
        ("task_started", {"task_id": "task-2", "action": "analysis"}),
        ("task_completed", {"task_id": "task-2", "result": "success"}),
    ]
    
    for event_type, payload in events_to_log:
        event = Event(
            aggregate_id="seo-agent",
            aggregate_type="agent",
            event_type=event_type,
            event_version=1,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
            idempotency_key=f"seo-agent-{event_type}-{payload.get('task_id', 'init')}"
        )
        await event_store.append_event(event)
    
    # Replay and rebuild state
    events = await event_store.replay_events(aggregate_id="seo-agent")
    
    state = {"tasks_completed": 0}
    for event in events:
        if event.event_type == "task_completed":
            state["tasks_completed"] += 1
    
    print(f"✅ Agent completed {state['tasks_completed']} tasks")
    
    await event_store.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

1. **Always use idempotency keys** для важных событий
2. **Version your events** для будущих изменений схемы
3. **Include timestamps** для временного анализа
4. **Keep payloads focused** — только релевантные данные
5. **Never delete events** — они immutable

---

## See Also

- [Event Store API](../api/event-store.md)
- [Tutorial #4: Rollback & Recovery](04-rollback.md)
- [Architecture: Event Sourcing](../architecture/event-sourcing.md)
