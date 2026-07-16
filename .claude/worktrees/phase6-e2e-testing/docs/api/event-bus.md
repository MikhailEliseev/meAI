# Event Bus API Reference

> Async message queue with priority support

## Overview

**Event Bus** — компонент для асинхронной передачи сообщений между агентами. Поддерживает приоритеты (P0-P3), pub/sub паттерн и crash recovery.

## Class: `EventBus`

### Constructor

```python
from meai.events.event_bus import EventBus
from meai.storage.database import Database

db = Database("sqlite+aiosqlite:///./data/meai.db")
await db.connect()

event_bus = EventBus(db)
```

**Parameters:**
- `db` (Database) — Database instance for message persistence

---

## Methods

### `publish(message: Message) -> str`

Publish message to the bus.

**Parameters:**
- `message` (Message) — Message to publish

**Returns:**
- `str` — Message ID

**Example:**

```python
from meai.events.event_bus import Message

message = Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="task_assignment",
    priority=1,  # P1 - High priority
    payload={
        "task_id": "task-123",
        "action": "analyze_competitors",
        "deadline": "2026-05-03T00:00:00Z"
    }
)

message_id = await event_bus.publish(message)
print(f"Message published: {message_id}")
```

---

### `subscribe(agent_id: str) -> AsyncIterator[Message]`

Subscribe to messages for an agent.

**Parameters:**
- `agent_id` (str) — Agent identifier

**Returns:**
- `AsyncIterator[Message]` — Stream of messages

**Example:**

```python
# Subscribe to messages
async for message in event_bus.subscribe("seo-agent"):
    print(f"Received: {message.message_type}")
    print(f"From: {message.from_agent}")
    print(f"Payload: {message.payload}")
    
    # Process message
    await process_message(message)
    
    # Mark as processed
    await event_bus.mark_processed(message.message_id)
```

---

### `get_pending_messages(agent_id: str) -> list[Message]`

Get pending messages for an agent.

**Parameters:**
- `agent_id` (str) — Agent identifier

**Returns:**
- `list[Message]` — List of pending messages (ordered by priority)

**Example:**

```python
# Get all pending messages
messages = await event_bus.get_pending_messages("seo-agent")

print(f"Pending messages: {len(messages)}")
for msg in messages:
    print(f"  P{msg.priority}: {msg.message_type}")
```

**Output:**
```
Pending messages: 3
  P0: critical_alert
  P1: task_assignment
  P2: status_update
```

---

### `mark_processed(message_id: str) -> None`

Mark message as processed.

**Parameters:**
- `message_id` (str) — Message identifier

**Returns:**
- None

**Example:**

```python
# Get message
messages = await event_bus.get_pending_messages("seo-agent")
message = messages[0]

# Process it
result = await process_message(message)

# Mark as processed
await event_bus.mark_processed(message.message_id)

print("✅ Message processed")
```

---

### `broadcast(message: Message) -> list[str]`

Broadcast message to all agents.

**Parameters:**
- `message` (Message) — Message to broadcast (to_agent is ignored)

**Returns:**
- `list[str]` — List of message IDs (one per agent)

**Example:**

```python
# Broadcast system announcement
message = Message(
    from_agent="system",
    to_agent="*",  # Broadcast
    message_type="system_announcement",
    priority=0,  # P0 - Critical
    payload={
        "announcement": "System maintenance in 10 minutes",
        "action_required": "Save your work"
    }
)

message_ids = await event_bus.broadcast(message)
print(f"Broadcasted to {len(message_ids)} agents")
```

---

## Data Classes

### `Message`

Message for inter-agent communication.

**Fields:**
- `from_agent` (str) — Sender agent ID
- `to_agent` (str) — Recipient agent ID
- `message_type` (str) — Type of message
- `priority` (int) — Priority: 0 (P0/critical) to 3 (P3/low)
- `payload` (dict) — Message data
- `message_id` (str, optional) — Message ID (set after publish)
- `status` (str, optional) — Status: "pending", "processed"
- `created_at` (datetime, optional) — Creation timestamp
- `processed_at` (datetime, optional) — Processing timestamp

**Example:**

```python
from meai.events.event_bus import Message

message = Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="task_assignment",
    priority=1,
    payload={
        "task_id": "task-123",
        "action": "analyze_competitors"
    }
)
```

---

## Priority Levels

Event Bus поддерживает 4 уровня приоритета:

| Priority | Level | Use Case | Example |
|----------|-------|----------|---------|
| **P0** | Critical | System alerts, emergencies | System shutdown, critical errors |
| **P1** | High | Urgent tasks, deadlines | Task assignments, urgent requests |
| **P2** | Normal | Regular tasks | Status updates, routine tasks |
| **P3** | Low | Background tasks | Cleanup, maintenance |

**Example:**

```python
# P0 - Critical
critical = Message(
    from_agent="system",
    to_agent="operator",
    message_type="critical_alert",
    priority=0,
    payload={"error": "Database connection lost"}
)

# P1 - High
high = Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="urgent_task",
    priority=1,
    payload={"task": "Fix broken links"}
)

# P2 - Normal
normal = Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="task_assignment",
    priority=2,
    payload={"task": "Weekly report"}
)

# P3 - Low
low = Message(
    from_agent="system",
    to_agent="seo-agent",
    message_type="cleanup",
    priority=3,
    payload={"action": "Archive old logs"}
)
```

---

## Message Types

Common message types:

### Task Messages

```python
# Task assignment
Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="task_assignment",
    priority=1,
    payload={
        "task_id": "task-123",
        "action": "analyze_competitors",
        "deadline": "2026-05-03T00:00:00Z"
    }
)

# Task completed
Message(
    from_agent="seo-agent",
    to_agent="operator",
    message_type="task_completed",
    priority=2,
    payload={
        "task_id": "task-123",
        "result": "success",
        "report_path": "/vault/reports/competitors.md"
    }
)
```

### Status Messages

```python
# Status update
Message(
    from_agent="seo-agent",
    to_agent="operator",
    message_type="status_update",
    priority=2,
    payload={
        "status": "working",
        "progress": 50,
        "eta": "2026-05-02T12:00:00Z"
    }
)

# Health check
Message(
    from_agent="system",
    to_agent="seo-agent",
    message_type="health_check",
    priority=2,
    payload={"check_type": "ping"}
)
```

### System Messages

```python
# System announcement
Message(
    from_agent="system",
    to_agent="*",
    message_type="system_announcement",
    priority=0,
    payload={
        "announcement": "System maintenance",
        "scheduled_at": "2026-05-02T22:00:00Z"
    }
)

# Critical alert
Message(
    from_agent="system",
    to_agent="operator",
    message_type="critical_alert",
    priority=0,
    payload={
        "alert": "High memory usage",
        "value": "95%"
    }
)
```

---

## Message Processing

### Basic Processing

```python
# Get pending messages
messages = await event_bus.get_pending_messages("seo-agent")

for message in messages:
    # Process based on type
    if message.message_type == "task_assignment":
        await handle_task(message.payload)
    
    elif message.message_type == "status_request":
        await send_status(message.from_agent)
    
    # Mark as processed
    await event_bus.mark_processed(message.message_id)
```

### Priority Processing

```python
# Messages are already sorted by priority
messages = await event_bus.get_pending_messages("seo-agent")

# Process P0 first, then P1, P2, P3
for message in messages:
    print(f"Processing P{message.priority}: {message.message_type}")
    
    if message.priority == 0:
        # Critical - process immediately
        await handle_critical(message)
    else:
        # Normal processing
        await handle_normal(message)
    
    await event_bus.mark_processed(message.message_id)
```

---

## Crash Recovery

Event Bus сохраняет сообщения в базу для crash recovery:

```python
# Publish message
message_id = await event_bus.publish(message)

# System crashes...

# After restart: messages still in database
messages = await event_bus.get_pending_messages("seo-agent")

# Unprocessed messages are recovered
print(f"Recovered {len(messages)} messages")
```

---

## Database Schema

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    message_type TEXT NOT NULL,
    priority INTEGER NOT NULL,
    payload TEXT NOT NULL,  -- JSON
    status TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    processed_at DATETIME
);

CREATE INDEX idx_messages_queue 
    ON messages(status, priority, created_at);

CREATE INDEX idx_messages_to 
    ON messages(to_agent, status);

CREATE INDEX idx_messages_from 
    ON messages(from_agent);
```

---

## Use Cases

### 1. Task Assignment

```python
# Operator assigns task to agent
message = Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="task_assignment",
    priority=1,
    payload={
        "task_id": "task-123",
        "action": "analyze_competitors",
        "params": {"competitors": ["site1.com", "site2.com"]}
    }
)

await event_bus.publish(message)
```

### 2. Agent Communication

```python
# Agent requests help from another agent
message = Message(
    from_agent="seo-agent",
    to_agent="content-agent",
    message_type="collaboration_request",
    priority=2,
    payload={
        "request": "Need content for SEO keywords",
        "keywords": ["medical marketing", "healthcare SEO"]
    }
)

await event_bus.publish(message)
```

### 3. System Alerts

```python
# System sends critical alert
message = Message(
    from_agent="system",
    to_agent="operator",
    message_type="critical_alert",
    priority=0,
    payload={
        "alert": "API rate limit exceeded",
        "current_rate": 1000,
        "limit": 900
    }
)

await event_bus.publish(message)
```

### 4. Broadcast Announcements

```python
# Broadcast to all agents
message = Message(
    from_agent="system",
    to_agent="*",
    message_type="system_announcement",
    priority=0,
    payload={
        "announcement": "New feature deployed",
        "feature": "Rollback Manager",
        "docs": "/docs/api/rollback.md"
    }
)

await event_bus.broadcast(message)
```

---

## Best Practices

### 1. Use Appropriate Priorities

```python
# ✅ Good: Correct priorities
P0: "critical_alert", "system_shutdown"
P1: "urgent_task", "deadline_approaching"
P2: "task_assignment", "status_update"
P3: "cleanup", "maintenance"

# ❌ Bad: Everything is P0
P0: "task_assignment"  # Not critical!
P0: "status_update"    # Not critical!
```

### 2. Always Mark as Processed

```python
# ✅ Good: Mark as processed
messages = await event_bus.get_pending_messages("seo-agent")
for msg in messages:
    await process_message(msg)
    await event_bus.mark_processed(msg.message_id)

# ❌ Bad: Forget to mark
messages = await event_bus.get_pending_messages("seo-agent")
for msg in messages:
    await process_message(msg)
    # Message stays in queue forever!
```

### 3. Handle Errors Gracefully

```python
# ✅ Good: Error handling
messages = await event_bus.get_pending_messages("seo-agent")
for msg in messages:
    try:
        await process_message(msg)
        await event_bus.mark_processed(msg.message_id)
    except Exception as e:
        print(f"Failed to process {msg.message_id}: {e}")
        # Message stays in queue for retry
```

### 4. Use Descriptive Message Types

```python
# ✅ Good: Clear message types
"task_assignment"
"task_completed"
"status_update"
"collaboration_request"

# ❌ Bad: Vague types
"message"
"data"
"info"
```

---

## Error Handling

```python
try:
    message_id = await event_bus.publish(message)
except Exception as e:
    print(f"Failed to publish message: {e}")

try:
    messages = await event_bus.get_pending_messages("seo-agent")
except Exception as e:
    print(f"Failed to get messages: {e}")
```

---

## Performance

- **Publish:** ~5-10ms per message
- **Get pending:** ~10-50ms (depends on queue size)
- **Mark processed:** ~5ms
- **Broadcast:** ~10ms × number of agents

---

## See Also

- [Event Store API](event-store.md) — Event sourcing
- [Orchestrator API](orchestrator.md) — Workflow coordination
- [Agent Factory API](agent-factory.md) — Agent creation
