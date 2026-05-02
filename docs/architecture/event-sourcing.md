# Event Sourcing Architecture

> Immutable audit log with replay capability

## Core Concept

**Event Sourcing** — все изменения сохраняются как последовательность immutable событий.

```
State = replay(Events)
```

## Event Structure

```python
Event {
    aggregate_id: "agent-123",      # Кто/что
    aggregate_type: "agent",         # Тип
    event_type: "task_completed",    # Что произошло
    event_version: 1,                # Версия схемы
    payload: {...},                  # Данные
    timestamp: "2026-05-02T...",     # Когда
    idempotency_key: "unique-key"    # Защита от дубликатов
}
```

## Benefits

1. **Complete Audit Trail** — все действия залогированы
2. **Time Travel** — можно восстановить состояние на любой момент
3. **Debugging** — легко понять что произошло
4. **Replay** — восстановление после сбоев
5. **Analytics** — анализ поведения системы

## Event Types

### Agent Events
- `agent_created`
- `task_started`
- `task_completed`
- `agent_deleted`

### System Events
- `checkpoint_created`
- `system_started`
- `system_shutdown`

## Idempotency

Каждое событие имеет `idempotency_key`:

```python
# First append - creates event
event_id_1 = await event_store.append_event(event)

# Second append - returns existing ID
event_id_2 = await event_store.append_event(event)

assert event_id_1 == event_id_2  # No duplicate
```

## Event Replay

```python
# Get all events
events = await event_store.replay_events(
    aggregate_id="agent-123"
)

# Rebuild state
state = {}
for event in events:
    apply_event(state, event)
```

## Storage

События хранятся в SQLite:

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    aggregate_id TEXT,
    event_type TEXT,
    payload TEXT,  -- JSON
    timestamp TEXT,
    idempotency_key TEXT UNIQUE
);
```

## Performance

- Append: ~5-10ms
- Query: ~10-50ms
- Replay: ~50-200ms (depends on event count)

## See Also

- [Event Store API](../api/event-store.md)
- [Tutorial: Event Sourcing](../tutorials/03-event-sourcing.md)
- [ADR-002: Event Sourcing](../adr/002-event-sourcing.md)
