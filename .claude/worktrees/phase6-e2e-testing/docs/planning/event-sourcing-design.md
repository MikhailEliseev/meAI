# Event Sourcing Design - meAI Core Foundation

**Date:** 2026-05-01  
**Status:** Design Document  
**Purpose:** Clarify Event Store vs Event Bus architecture

---

## Problem Statement

The spec uses "events" and "messages" interchangeably, causing confusion about:
- Are Event Store and Event Bus the same thing?
- How does event replay work?
- What's the difference between events and messages?

---

## Solution: Separate Concerns

### Events vs Messages

**Events** = Immutable facts about what happened (past tense)
- "AgentCreated", "StructureBuilt", "DecisionMade"
- Stored in Event Store (SQLite `events` table)
- Used for audit trail and replay
- Never deleted, only appended

**Messages** = Commands or queries between agents (imperative)
- "CreateAgent", "SendNotification", "CheckHealth"
- Stored in Event Bus (SQLite `messages` table)
- Used for async communication
- Marked as processed, can be deleted

---

## Architecture

```
Command Flow:
┌─────────────┐
│   Command   │ (e.g., "Create Agent")
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────┐
│  Handler (e.g., Architect)              │
│  1. Execute business logic              │
│  2. Append event to Event Store         │
│  3. Publish message to Event Bus        │
└─────────────────────────────────────────┘
       │                    │
       v                    v
┌─────────────┐      ┌─────────────┐
│ Event Store │      │  Event Bus  │
│ (Audit Log) │      │ (Messaging) │
└─────────────┘      └─────────────┘
```

---

## Event Store Design

### Purpose
- Immutable audit log
- Event replay for rollback
- Time-travel debugging
- Compliance and audit

### Schema

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_id TEXT NOT NULL,        -- e.g., "agent-123"
    aggregate_type TEXT NOT NULL,      -- e.g., "agent", "agency"
    event_type TEXT NOT NULL,          -- e.g., "AgentCreated"
    event_version INTEGER NOT NULL,    -- Schema version (for evolution)
    payload JSON NOT NULL,             -- Event data
    timestamp TEXT NOT NULL,           -- ISO 8601
    idempotency_key TEXT UNIQUE,       -- Prevent duplicates
    created_at TEXT NOT NULL           -- When written to store
);

CREATE INDEX idx_events_aggregate ON events(aggregate_id, aggregate_type);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_idempotency ON events(idempotency_key);
```

### Event Versioning

Events evolve over time. Use `event_version` to handle schema changes:

```python
# Version 1
{
    "event_type": "AgentCreated",
    "event_version": 1,
    "payload": {
        "name": "seo-agent",
        "type": "subagent"
    }
}

# Version 2 (added department)
{
    "event_type": "AgentCreated",
    "event_version": 2,
    "payload": {
        "name": "seo-agent",
        "type": "subagent",
        "department": "seo"  # NEW
    }
}
```

**Replay Strategy:** Upcasters convert old events to new schema during replay.

### Idempotency

Use `idempotency_key` to prevent duplicate events:

```python
idempotency_key = f"{aggregate_id}:{event_type}:{timestamp}"
```

If same key exists, skip append (idempotent).

### Snapshot Strategy

Event log grows forever. Use snapshots to optimize replay:

**Snapshot Every N Events:**
- After 1000 events for an aggregate, create snapshot
- Store snapshot in Obsidian: `snapshots/{aggregate_id}/{timestamp}.json`
- Replay = load snapshot + replay events after snapshot

**Not in MVP:** Implement in post-MVP when event log > 10K events.

---

## Event Bus Design

### Purpose
- Async message queue between agents
- Priority-based routing (P0-P3)
- Pub/sub pattern
- Durability (persist before processing)

### Schema

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,          -- Sender
    to_agent TEXT NOT NULL,            -- Receiver (or "*" for broadcast)
    message_type TEXT NOT NULL,        -- e.g., "CreateAgent", "Notify"
    priority INTEGER NOT NULL,         -- 0 (highest) to 3 (lowest)
    payload JSON NOT NULL,             -- Message data
    timestamp TEXT NOT NULL,           -- ISO 8601
    processed BOOLEAN DEFAULT FALSE,   -- Processed flag
    processed_at TEXT,                 -- When processed
    error TEXT                         -- Error if processing failed
);

CREATE INDEX idx_messages_to ON messages(to_agent, processed);
CREATE INDEX idx_messages_priority ON messages(priority, timestamp);
```

### Message Flow

1. **Publish:** Write message to `messages` table
2. **Route:** asyncio.Queue pulls unprocessed messages by priority
3. **Process:** Handler processes message
4. **Mark:** Update `processed = TRUE`
5. **Cleanup:** Delete processed messages after 7 days (optional)

### Priority Queue

Messages processed in order:
1. P0 (critical) - immediate
2. P1 (high) - within 1 minute
3. P2 (normal) - within 5 minutes
4. P3 (low) - best effort

**Implementation:**
```python
# Pull messages ordered by priority, then timestamp
SELECT * FROM messages 
WHERE to_agent = ? AND processed = FALSE
ORDER BY priority ASC, timestamp ASC
LIMIT 100
```

### Durability

Messages persisted to SQLite BEFORE processing:
- Crash recovery: restart processing from unprocessed messages
- No message loss

---

## Event Replay

### Purpose
- Rollback to checkpoint
- Rebuild state from events
- Time-travel debugging

### Replay Process

```python
async def replay_events(
    aggregate_id: str,
    from_timestamp: str,
    to_timestamp: str | None = None
) -> list[Event]:
    """Replay events for aggregate in time range"""
    
    # 1. Load snapshot (if exists)
    snapshot = await load_snapshot(aggregate_id, from_timestamp)
    state = snapshot.state if snapshot else {}
    
    # 2. Query events after snapshot
    events = await event_store.get_events(
        aggregate_id=aggregate_id,
        from_timestamp=snapshot.timestamp if snapshot else from_timestamp,
        to_timestamp=to_timestamp
    )
    
    # 3. Replay events (skip side effects)
    for event in events:
        state = apply_event(state, event, replaying=True)
    
    return state
```

### Side Effect Handling

During replay, skip side effects:
- Don't send Telegram notifications
- Don't call external APIs
- Don't write to filesystem (except state)

**Implementation:**
```python
def apply_event(state, event, replaying=False):
    if event.type == "AgentCreated":
        state["agents"][event.payload["name"]] = event.payload
        
        if not replaying:
            # Side effects only during normal processing
            send_telegram_notification(...)
    
    return state
```

---

## Concurrent Writes

### Problem
Multiple agents writing events simultaneously → race conditions

### Solution: Optimistic Locking

Use `event_version` as optimistic lock:

```python
async def append_event(aggregate_id, event_type, payload):
    # 1. Get current version
    current_version = await get_latest_version(aggregate_id)
    
    # 2. Append with next version
    try:
        await db.execute(
            """
            INSERT INTO events (aggregate_id, event_type, event_version, payload, ...)
            VALUES (?, ?, ?, ?, ...)
            """,
            (aggregate_id, event_type, current_version + 1, payload, ...)
        )
    except IntegrityError:
        # Concurrent write detected, retry
        raise ConcurrentWriteError("Retry append")
```

**Retry Strategy:** Exponential backoff, max 3 retries.

---

## Data Flow Examples

### Example 1: Create Agent

```
1. User → Architect.create_agent("seo-agent")

2. Architect:
   - Execute: Create vault, generate prompt
   - Append Event: AgentCreated(name="seo-agent", ...)
   - Publish Message: NotifyAgentCreated(to="monitoring")

3. Event Store:
   - Write to events table
   - Return event_id

4. Event Bus:
   - Write to messages table
   - Notify subscribers via asyncio.Queue

5. Monitoring:
   - Receive message from queue
   - Update metrics
   - Mark message as processed
```

### Example 2: Rollback

```
1. User → RollbackManager.rollback_to_checkpoint("checkpoint-1")

2. RollbackManager:
   - Load snapshot from Obsidian
   - Query events after snapshot
   - Replay events (skip side effects)
   - Restore state

3. Event Store:
   - Read events (no writes during replay)

4. Event Bus:
   - Not involved in replay
```

---

## Implementation Checklist

### Event Store (Task 5)
- [ ] Create `events` table with versioning
- [ ] Implement `append_event()` with idempotency
- [ ] Implement `get_events()` with filters
- [ ] Implement `replay_events()` with side effect skipping
- [ ] Add optimistic locking for concurrent writes
- [ ] Add event upcasters for schema evolution

### Event Bus (Task 6)
- [ ] Create `messages` table
- [ ] Implement `publish_message()` with persistence
- [ ] Implement priority queue (asyncio.Queue + SQLite)
- [ ] Implement `subscribe()` for pub/sub
- [ ] Implement `mark_processed()`
- [ ] Add cleanup job for old messages

### Rollback (Task 25)
- [ ] Integrate Event Store replay
- [ ] Integrate Obsidian snapshots
- [ ] Implement checkpoint creation
- [ ] Implement rollback workflow
- [ ] Add dry-run mode
- [ ] Add rollback validation

---

## Testing Strategy

### Event Store Tests
- Append event → verify in database
- Append duplicate (same idempotency_key) → verify skipped
- Concurrent writes → verify optimistic locking
- Replay events → verify state rebuilt correctly
- Replay with side effects → verify side effects skipped

### Event Bus Tests
- Publish message → verify in database
- Subscribe → verify message received
- Priority ordering → verify P0 before P3
- Mark processed → verify flag updated
- Crash recovery → verify unprocessed messages replayed

### Integration Tests
- Create agent → verify event + message
- Rollback → verify state restored
- Concurrent agent creation → verify no race conditions

---

## Performance Considerations

### Event Store
- **Writes:** ~1000/sec (SQLite limit)
- **Reads:** Fast with indexes
- **Replay:** O(n) where n = events after snapshot

### Event Bus
- **Throughput:** ~1000 messages/sec
- **Latency:** < 100ms per message
- **Queue size:** Max 10,000 messages (backpressure)

### Bottlenecks
- SQLite write lock (single writer)
- Filesystem I/O for snapshots

### Mitigations
- Batch writes where possible
- Use WAL mode for SQLite
- Async I/O for Obsidian

---

## MVP Limits

- **Max agents:** 20
- **Max events/min:** 1000
- **Max messages/min:** 1000
- **Event log size:** 100K events (then snapshot)
- **Message retention:** 7 days

---

## Post-MVP Enhancements

- Snapshot compaction (automatic)
- Event log archival (move old events to cold storage)
- Distributed event bus (Redis/RabbitMQ)
- CQRS (separate read/write models)
- Event streaming (Kafka)

---

## References

- Martin Fowler: Event Sourcing (https://martinfowler.com/eaaDev/EventSourcing.html)
- Greg Young: CQRS Documents (https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)
- Vaughn Vernon: Implementing Domain-Driven Design

---

**Approved:** Ready for implementation  
**Next:** Update spec.md with this design
