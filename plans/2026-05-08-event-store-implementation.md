# Event Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement immutable Event Store for audit logging, event replay, and debugging support.

**Architecture:** Append-only event log with SQLite persistence. Provides query API for retrieving events by ID, correlation chain, project, and time range. Supports event replay from any timestamp.

**Tech Stack:** Python 3.11+, SQLAlchemy async, SQLite, Pydantic v2

---

## File Structure

### Files to Create
- `src/meai/events/event_store.py` - Event Store implementation
- `tests/events/test_event_store.py` - Unit tests

### Files to Modify
- `src/meai/events/__init__.py` - Export EventStore

### Dependencies
- Existing: `src/meai/events/base.py` (BaseEvent)
- Existing: `src/meai/storage/database.py` (Database)

---

## Implementation Phases

### Phase 1: Core Event Store
**Goal:** Basic append-only event storage with retrieval

### Phase 2: Query API
**Goal:** Query events by correlation, project, time range

### Phase 3: Replay Capability
**Goal:** Event replay from timestamp

---

## Phase 1: Core Event Store

### Task 1.1: Create Event Store Schema

**Files:**
- Create: `src/meai/events/event_store.py`
- Test: `tests/events/test_event_store.py`

- [ ] **Step 1: Write failing test for event storage**

```python
# tests/events/test_event_store.py
import pytest
from meai.events.event_store import EventStore
from meai.events import ProjectCreatedEvent

@pytest.mark.asyncio
async def test_append_event():
    """Test appending event to store"""
    store = EventStore()
    await store.initialize()
    
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Test Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )
    
    await store.append(event)
    
    # Verify event stored
    retrieved = await store.get_by_id(event.id)
    assert retrieved is not None
    assert retrieved.id == event.id
    assert retrieved.type == "project.created"
    
    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_store.py::test_append_event -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'meai.events.event_store'"

- [ ] **Step 3: Create EventStore class with schema**

```python
# src/meai/events/event_store.py
"""Immutable Event Store for audit logging and replay"""

import json
from datetime import datetime
from typing import Optional, List, AsyncIterator
from sqlalchemy import text

from meai.storage.database import Database
from meai.events.base import BaseEvent


class EventStore:
    """Immutable append-only event store
    
    Features:
    - Append-only (no updates or deletes)
    - Full audit trail
    - Event replay capability
    - Query by ID, correlation, project, time range
    """
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///:memory:"):
        """Initialize Event Store
        
        Args:
            database_url: Database connection URL
        """
        self.db = Database(database_url)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Event Store and create schema"""
        if self._initialized:
            return
        
        await self.db.initialize()
        await self._create_schema()
        self._initialized = True
    
    async def _create_schema(self) -> None:
        """Create Event Store schema"""
        async with self.db.session() as session:
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS event_store (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT,
                    priority INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    reply_to TEXT,
                    metadata TEXT,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )
            
            # Indexes for efficient querying
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS idx_store_type ON event_store(type)")
            )
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS idx_store_correlation ON event_store(correlation_id)")
            )
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS idx_store_timestamp ON event_store(timestamp)")
            )
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS idx_store_created_at ON event_store(created_at)")
            )
            
            await session.commit()
    
    async def append(self, event: BaseEvent) -> None:
        """Append event to store (immutable)
        
        Args:
            event: Event to append
            
        Raises:
            RuntimeError: If store not initialized
        """
        if not self._initialized:
            raise RuntimeError("EventStore not initialized. Call initialize() first.")
        
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO event_store
                (id, type, source, target, priority, timestamp, 
                 correlation_id, reply_to, metadata, data)
                VALUES (:id, :type, :source, :target, :priority, :timestamp,
                        :correlation_id, :reply_to, :metadata, :data)
                """),
                {
                    "id": event.id,
                    "type": event.type,
                    "source": event.source,
                    "target": event.target,
                    "priority": event.priority,
                    "timestamp": event.timestamp.isoformat(),
                    "correlation_id": event.correlation_id,
                    "reply_to": event.reply_to,
                    "metadata": json.dumps(event.metadata),
                    "data": event.model_dump_json()
                }
            )
            await session.commit()
    
    async def get_by_id(self, event_id: str) -> Optional[BaseEvent]:
        """Retrieve event by ID
        
        Args:
            event_id: Event ID
            
        Returns:
            Event or None if not found
        """
        if not self._initialized:
            raise RuntimeError("EventStore not initialized. Call initialize() first.")
        
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT data
                FROM event_store
                WHERE id = :event_id
                """),
                {"event_id": event_id}
            )
            
            row = result.fetchone()
            if not row:
                return None
            
            # Reconstruct event from JSON
            event_data = json.loads(row[0])
            
            # Import event class dynamically
            from meai import events as events_module
            event_type_str = event_data.get("type", "")
            class_name = "".join(
                word.capitalize() for word in event_type_str.split(".")
            ) + "Event"
            
            try:
                event_class = getattr(events_module, class_name, None)
                if event_class and issubclass(event_class, BaseEvent):
                    return event_class.model_validate(event_data)
                else:
                    return BaseEvent.model_validate(event_data)
            except (AttributeError, ImportError):
                return BaseEvent.model_validate(event_data)
    
    async def close(self) -> None:
        """Close Event Store"""
        await self.db.close()
        self._initialized = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_store.py::test_append_event -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_store.py tests/events/test_event_store.py
git commit -m "feat(event-store): add core EventStore with append and get_by_id

- Create event_store table (append-only)
- Implement append() for immutable event storage
- Implement get_by_id() for event retrieval
- Add indexes for efficient querying
- Dynamic event class reconstruction

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: Query API

### Task 2.1: Add get_by_correlation() method

**Files:**
- Modify: `src/meai/events/event_store.py`
- Test: `tests/events/test_event_store.py`

- [ ] **Step 1: Write failing test**

```python
# tests/events/test_event_store.py
@pytest.mark.asyncio
async def test_get_by_correlation():
    """Test retrieving events by correlation_id"""
    store = EventStore()
    await store.initialize()
    
    # Create correlation chain
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-123",
        project_name="Project 1",
        project_type="medical_marketing",
        client_name="Client 1"
    )
    event2 = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-123",  # Same correlation
        task_title="Task 1",
        task_description="Description 1",
        assigned_to="brand-magister"
    )
    event3 = ProjectCreatedEvent(
        source="operator",
        target="content-magister",
        correlation_id="corr-456",  # Different correlation
        project_name="Project 2",
        project_type="medical_marketing",
        client_name="Client 2"
    )
    
    await store.append(event1)
    await store.append(event2)
    await store.append(event3)
    
    # Get correlation chain
    chain = await store.get_by_correlation("corr-123")
    
    assert len(chain) == 2
    assert all(e.correlation_id == "corr-123" for e in chain)
    assert chain[0].type == "project.created"
    assert chain[1].type == "task.created"
    
    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_store.py::test_get_by_correlation -v`
Expected: FAIL with "AttributeError: 'EventStore' object has no attribute 'get_by_correlation'"

- [ ] **Step 3: Implement get_by_correlation() method**

```python
# src/meai/events/event_store.py (add after get_by_id method)
async def get_by_correlation(self, correlation_id: str) -> List[BaseEvent]:
    """Get all events in correlation chain
    
    Args:
        correlation_id: Correlation ID
        
    Returns:
        List of events in chronological order
    """
    if not self._initialized:
        raise RuntimeError("EventStore not initialized. Call initialize() first.")
    
    async with self.db.session() as session:
        result = await session.execute(
            text("""
            SELECT data
            FROM event_store
            WHERE correlation_id = :correlation_id
            ORDER BY timestamp ASC
            """),
            {"correlation_id": correlation_id}
        )
        
        events = []
        for row in result.fetchall():
            event_data = json.loads(row[0])
            
            # Import event class dynamically
            from meai import events as events_module
            event_type_str = event_data.get("type", "")
            class_name = "".join(
                word.capitalize() for word in event_type_str.split(".")
            ) + "Event"
            
            try:
                event_class = getattr(events_module, class_name, None)
                if event_class and issubclass(event_class, BaseEvent):
                    event = event_class.model_validate(event_data)
                else:
                    event = BaseEvent.model_validate(event_data)
                events.append(event)
            except (AttributeError, ImportError):
                event = BaseEvent.model_validate(event_data)
                events.append(event)
        
        return events
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_store.py::test_get_by_correlation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_store.py tests/events/test_event_store.py
git commit -m "feat(event-store): add get_by_correlation() for correlation chains

- Query events by correlation_id
- Return events in chronological order
- Support for tracing request/response chains

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Task 2.2: Add get_by_time_range() method

**Files:**
- Modify: `src/meai/events/event_store.py`
- Test: `tests/events/test_event_store.py`

- [ ] **Step 1: Write failing test**

```python
# tests/events/test_event_store.py
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_by_time_range():
    """Test retrieving events by time range"""
    store = EventStore()
    await store.initialize()
    
    now = datetime.now()
    
    # Create events with different timestamps
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Project 1",
        project_type="medical_marketing",
        client_name="Client 1"
    )
    await store.append(event1)
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    event2 = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        task_title="Task 1",
        task_description="Description 1",
        assigned_to="brand-magister"
    )
    await store.append(event2)
    
    # Get events from start time
    events = await store.get_by_time_range(from_time=now)
    
    assert len(events) == 2
    assert events[0].id == event1.id
    assert events[1].id == event2.id
    
    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_store.py::test_get_by_time_range -v`
Expected: FAIL

- [ ] **Step 3: Implement get_by_time_range() method**

```python
# src/meai/events/event_store.py (add after get_by_correlation method)
async def get_by_time_range(
    self,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 1000
) -> List[BaseEvent]:
    """Get events within time range
    
    Args:
        from_time: Start time (inclusive)
        to_time: End time (inclusive)
        limit: Maximum number of events
        
    Returns:
        List of events in chronological order
    """
    if not self._initialized:
        raise RuntimeError("EventStore not initialized. Call initialize() first.")
    
    # Build WHERE clause
    conditions = []
    params = {"limit": limit}
    
    if from_time:
        conditions.append("timestamp >= :from_time")
        params["from_time"] = from_time.isoformat()
    
    if to_time:
        conditions.append("timestamp <= :to_time")
        params["to_time"] = to_time.isoformat()
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    async with self.db.session() as session:
        # Safe to use f-string: where_clause built from hardcoded SQL fragments only
        result = await session.execute(
            text(f"""
            SELECT data
            FROM event_store
            WHERE {where_clause}
            ORDER BY timestamp ASC
            LIMIT :limit
            """),
            params
        )
        
        events = []
        for row in result.fetchall():
            event_data = json.loads(row[0])
            
            # Import event class dynamically
            from meai import events as events_module
            event_type_str = event_data.get("type", "")
            class_name = "".join(
                word.capitalize() for word in event_type_str.split(".")
            ) + "Event"
            
            try:
                event_class = getattr(events_module, class_name, None)
                if event_class and issubclass(event_class, BaseEvent):
                    event = event_class.model_validate(event_data)
                else:
                    event = BaseEvent.model_validate(event_data)
                events.append(event)
            except (AttributeError, ImportError):
                event = BaseEvent.model_validate(event_data)
                events.append(event)
        
        return events
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_store.py::test_get_by_time_range -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_store.py tests/events/test_event_store.py
git commit -m "feat(event-store): add get_by_time_range() for time-based queries

- Query events by time range (from/to)
- Support for debugging and analysis
- Chronological ordering

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: Replay Capability

### Task 3.1: Add replay() method

**Files:**
- Modify: `src/meai/events/event_store.py`
- Test: `tests/events/test_event_store.py`

- [ ] **Step 1: Write failing test**

```python
# tests/events/test_event_store.py
@pytest.mark.asyncio
async def test_replay_events():
    """Test replaying events from timestamp"""
    store = EventStore()
    await store.initialize()
    
    # Create events
    event1 = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Project 1",
        project_type="medical_marketing",
        client_name="Client 1"
    )
    event2 = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        task_title="Task 1",
        task_description="Description 1",
        assigned_to="brand-magister"
    )
    
    await store.append(event1)
    await store.append(event2)
    
    # Replay all events
    replayed = []
    async for event in store.replay(from_time=datetime.min):
        replayed.append(event)
    
    assert len(replayed) == 2
    assert replayed[0].id == event1.id
    assert replayed[1].id == event2.id
    
    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_store.py::test_replay_events -v`
Expected: FAIL

- [ ] **Step 3: Implement replay() method**

```python
# src/meai/events/event_store.py (add after get_by_time_range method)
async def replay(
    self,
    from_time: datetime,
    to_time: Optional[datetime] = None,
    batch_size: int = 100
) -> AsyncIterator[BaseEvent]:
    """Replay events from timestamp
    
    Args:
        from_time: Start time for replay
        to_time: End time for replay (None = all events)
        batch_size: Number of events to fetch per batch
        
    Yields:
        Events in chronological order
    """
    if not self._initialized:
        raise RuntimeError("EventStore not initialized. Call initialize() first.")
    
    offset = 0
    
    while True:
        # Build WHERE clause
        conditions = ["timestamp >= :from_time"]
        params = {
            "from_time": from_time.isoformat(),
            "limit": batch_size,
            "offset": offset
        }
        
        if to_time:
            conditions.append("timestamp <= :to_time")
            params["to_time"] = to_time.isoformat()
        
        where_clause = " AND ".join(conditions)
        
        async with self.db.session() as session:
            # Safe to use f-string: where_clause built from hardcoded SQL fragments only
            result = await session.execute(
                text(f"""
                SELECT data
                FROM event_store
                WHERE {where_clause}
                ORDER BY timestamp ASC
                LIMIT :limit OFFSET :offset
                """),
                params
            )
            
            rows = result.fetchall()
            
            if not rows:
                break
            
            for row in rows:
                event_data = json.loads(row[0])
                
                # Import event class dynamically
                from meai import events as events_module
                event_type_str = event_data.get("type", "")
                class_name = "".join(
                    word.capitalize() for word in event_type_str.split(".")
                ) + "Event"
                
                try:
                    event_class = getattr(events_module, class_name, None)
                    if event_class and issubclass(event_class, BaseEvent):
                        event = event_class.model_validate(event_data)
                    else:
                        event = BaseEvent.model_validate(event_data)
                    yield event
                except (AttributeError, ImportError):
                    event = BaseEvent.model_validate(event_data)
                    yield event
            
            offset += batch_size
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_store.py::test_replay_events -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_store.py tests/events/test_event_store.py
git commit -m "feat(event-store): add replay() for event replay capability

- Async iterator for memory-efficient replay
- Batch processing for large event sets
- Support for debugging and system recovery

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 4: Integration with Event Bus

### Task 4.1: Auto-append events to Event Store

**Files:**
- Modify: `src/meai/events/event_bus.py`
- Modify: `src/meai/events/event_store.py`
- Test: `tests/events/test_event_bus_integration.py`

- [ ] **Step 1: Write failing test**

```python
# tests/events/test_event_bus_integration.py (add new test)
@pytest.mark.asyncio
async def test_event_bus_auto_appends_to_store():
    """Test Event Bus automatically appends to Event Store"""
    from meai.events.event_bus import EventBus
    from meai.events.event_store import EventStore
    
    bus = EventBus()
    store = EventStore()
    
    await bus.initialize()
    await store.initialize()
    
    # Connect store to bus
    bus.set_event_store(store)
    
    # Publish event
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Test Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )
    
    await bus.publish(event)
    
    # Verify event in store
    stored = await store.get_by_id(event.id)
    assert stored is not None
    assert stored.id == event.id
    
    await bus.close()
    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_bus_integration.py::test_event_bus_auto_appends_to_store -v`
Expected: FAIL

- [ ] **Step 3: Add Event Store integration to Event Bus**

```python
# src/meai/events/event_bus.py (add to __init__ method)
def __init__(self, database_url: str = "sqlite+aiosqlite:///:memory:"):
    """Initialize Event Bus"""
    self.db = Database(database_url)
    self._initialized = False
    self._subscribers: dict[str, list[Callable]] = {}
    self._event_store: Optional["EventStore"] = None  # Add this line

# Add new method after __init__
def set_event_store(self, event_store: "EventStore") -> None:
    """Set Event Store for automatic event persistence
    
    Args:
        event_store: EventStore instance
    """
    self._event_store = event_store

# Modify publish() method to append to store
# Find the BaseEvent handling section and add after database commit:
if isinstance(event, BaseEvent):
    # ... existing storage code ...
    await session.commit()
    
    # Append to Event Store if configured
    if self._event_store:
        await self._event_store.append(event)
    
    # ... rest of code ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_bus_integration.py::test_event_bus_auto_appends_to_store -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_bus.py tests/events/test_event_bus_integration.py
git commit -m "feat(event-bus): integrate Event Store for automatic audit logging

- Add set_event_store() to Event Bus
- Auto-append events to Event Store on publish
- Complete audit trail for all events

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 5: Export and Documentation

### Task 5.1: Export EventStore and update __init__.py

**Files:**
- Modify: `src/meai/events/__init__.py`

- [ ] **Step 1: Add EventStore to exports**

```python
# src/meai/events/__init__.py (add to imports)
from meai.events.event_store import EventStore

# Add to __all__ list
__all__ = [
    # ... existing exports ...
    "EventStore",  # Add this
]
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from meai.events import EventStore; print('✅ EventStore import works')"`
Expected: "✅ EventStore import works"

- [ ] **Step 3: Commit**

```bash
git add src/meai/events/__init__.py
git commit -m "feat(events): export EventStore

- Add EventStore to public API
- Enable easy importing: from meai.events import EventStore

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Self-Review Checklist

After completing all phases, verify:

### 1. Spec Compliance
- [ ] Immutable append-only storage
- [ ] get_by_id() works
- [ ] get_by_correlation() works
- [ ] get_by_time_range() works
- [ ] replay() works
- [ ] Integration with Event Bus

### 2. No Placeholders
- [ ] No TBD, TODO, or incomplete code
- [ ] All test cases have actual assertions
- [ ] All methods implemented

### 3. Type Consistency
- [ ] BaseEvent used consistently
- [ ] Method signatures match across tasks
- [ ] Return types correct

---

## Verification Gates

### Tier 1: Required (block completion)
```bash
# Type checking
python -m mypy src/meai/events/event_store.py --strict

# Tests
python -m pytest tests/events/test_event_store.py -v
python -m pytest tests/events/test_event_bus_integration.py -v

# Linting
ruff check src/meai/events/event_store.py
```

### Tier 2: Recommended
```bash
# Test coverage
python -m pytest tests/events/ --cov=src/meai/events/event_store --cov-report=term-missing

# Should be >90% coverage
```

---

## Execution Handoff

Plan complete and saved to `plans/2026-05-08-event-store-implementation.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - Fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
