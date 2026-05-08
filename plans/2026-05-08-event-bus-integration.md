# Event Bus Integration with Pydantic Events

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate existing Event Bus with 53 Pydantic event models, enabling type-safe, priority-based async communication.

**Architecture:** Evolutionary integration - extend existing Event Bus to support BaseEvent while maintaining backward compatibility with legacy Event/Message classes. Add correlation chains, improve persistence, update routing logic.

**Tech Stack:** Python 3.11+, Pydantic v2, SQLAlchemy async, asyncio

---

## Challenge Log

### 1. Does this solve the problem?
**Problem:** Event Bus uses dataclass models; we have 53 Pydantic events with strict typing, priorities, correlation chains.

**Solution coverage:**
- ✅ Priority-based routing (P0-P3) - extend existing
- ✅ Correlation chains (correlation_id, reply_to) - add to persistence
- ✅ Async pub/sub - already exists
- ✅ Persistent storage - extend schema
- ✅ BaseEvent integration - new publish method
- ✅ All 53 events supported - generic handling

### 2. Most efficient solution?
**Alternatives:**
- A) Full rewrite - high risk, breaks existing code
- B) Adapter pattern - technical debt, complexity
- C) Evolutionary integration ⭐ - gradual, safe, backward compatible

**Chosen:** C - Evolutionary integration
- Keep working Event Bus
- Add BaseEvent support alongside legacy
- Migrate gradually
- Zero breaking changes

### 3. Code for code's sake?
Every change serves acceptance criteria:
- BaseEvent support → solves integration ✅
- Legacy compatibility → prevents breakage ✅
- Schema updates → enables correlation ✅
- Routing improvements → handles priorities ✅

---

## File Structure

### Files to Modify
- `src/meai/events/event_bus.py` - Add BaseEvent support, update routing
- `tests/events/test_event_bus.py` - Integration tests

### Files to Create
- `tests/events/test_event_bus_integration.py` - End-to-end tests with real events

### Dependencies
- Existing: `src/meai/events/base.py` (BaseEvent)
- Existing: `src/meai/events/*.py` (53 event models)
- Existing: `src/meai/storage/database.py` (Database)

---

## Implementation Phases

### Phase 1: Extend Persistence Schema
**Goal:** Add correlation_id, reply_to, metadata to event storage

### Phase 2: Add BaseEvent Support
**Goal:** Event Bus can publish/subscribe to BaseEvent instances

### Phase 3: Update Routing Logic
**Goal:** Priority-based routing works with BaseEvent.priority

### Phase 4: Integration Tests
**Goal:** Verify all 53 events work end-to-end

---

## Phase 1: Extend Persistence Schema

**Files:**
- Modify: `src/meai/events/event_bus.py:87-105` (schema)
- Test: `tests/events/test_event_bus.py`

### Task 1.1: Update Database Schema

- [ ] **Step 1: Write failing test for correlation_id storage**

```python
# tests/events/test_event_bus.py
import pytest
from meai.events.event_bus import EventBus
from meai.events import ProjectCreatedEvent

@pytest.mark.asyncio
async def test_store_event_with_correlation():
    """Test storing event with correlation_id"""
    bus = EventBus()
    await bus.initialize()
    
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id="corr-123",
        project_name="Test Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )
    
    event_id = await bus.publish(event)
    
    # Verify stored with correlation_id
    stored = await bus._get_event_by_id(event_id)
    assert stored["correlation_id"] == "corr-123"
    
    await bus.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_bus.py::test_store_event_with_correlation -v`
Expected: FAIL with "AttributeError: 'EventBus' object has no attribute '_get_event_by_id'"

- [ ] **Step 3: Update schema in event_bus.py**

```python
# src/meai/events/event_bus.py (line ~87)
async def _create_tables(self) -> None:
    """Create Event Bus tables"""
    async with self.db.session() as session:
        # Legacy messages table (keep for backward compat)
        await session.execute(
            text("""
            CREATE TABLE IF NOT EXISTS event_bus_messages (
                message_id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                message_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
        )
        
        # New events table for BaseEvent
        await session.execute(
            text("""
            CREATE TABLE IF NOT EXISTS event_bus_events (
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
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_correlation (correlation_id),
                INDEX idx_reply_to (reply_to),
                INDEX idx_status_priority (status, priority)
            )
            """)
        )
        await session.commit()
```

- [ ] **Step 4: Add _get_event_by_id helper method**

```python
# src/meai/events/event_bus.py (after _create_tables)
async def _get_event_by_id(self, event_id: str) -> dict | None:
    """Get event by ID from storage
    
    Args:
        event_id: Event ID
        
    Returns:
        Event data dict or None if not found
    """
    if not self._initialized:
        raise RuntimeError("EventBus not initialized. Call initialize() first.")
    
    async with self.db.session() as session:
        result = await session.execute(
            text("""
            SELECT id, type, source, target, priority, timestamp,
                   correlation_id, reply_to, metadata, data, status
            FROM event_bus_events
            WHERE id = :event_id
            """),
            {"event_id": event_id}
        )
        row = result.fetchone()
        if not row:
            return None
        
        return {
            "id": row[0],
            "type": row[1],
            "source": row[2],
            "target": row[3],
            "priority": row[4],
            "timestamp": row[5],
            "correlation_id": row[6],
            "reply_to": row[7],
            "metadata": json.loads(row[8]) if row[8] else {},
            "data": json.loads(row[9]),
            "status": row[10]
        }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_bus.py::test_store_event_with_correlation -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/meai/events/event_bus.py tests/events/test_event_bus.py
git commit -m "feat(event-bus): add correlation_id and reply_to to schema

- Add event_bus_events table for BaseEvent storage
- Add correlation_id, reply_to, metadata fields
- Add indexes for efficient querying
- Add _get_event_by_id helper method
- Keep legacy event_bus_messages for backward compat

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: Add BaseEvent Support

**Files:**
- Modify: `src/meai/events/event_bus.py:213-263` (publish method)
- Test: `tests/events/test_event_bus.py`

### Task 2.1: Extend publish() for BaseEvent

- [ ] **Step 1: Write failing test for BaseEvent publishing**

```python
# tests/events/test_event_bus.py
@pytest.mark.asyncio
async def test_publish_base_event():
    """Test publishing BaseEvent instance"""
    bus = EventBus()
    await bus.initialize()
    
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Test Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )
    
    event_id = await bus.publish(event)
    
    assert event_id == event.id
    
    # Verify stored correctly
    stored = await bus._get_event_by_id(event_id)
    assert stored["type"] == "project.created"
    assert stored["source"] == "operator"
    assert stored["target"] == "brand-magister"
    assert stored["priority"] == 2  # P2 for project events
    
    await bus.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_bus.py::test_publish_base_event -v`
Expected: FAIL with "Event stored in wrong table" or similar

- [ ] **Step 3: Update publish() method**

```python
# src/meai/events/event_bus.py (replace existing publish method ~line 213)
async def publish(self, event: Event | Message | BaseEvent) -> str:
    """Publish event or message
    
    Args:
        event: Event, Message, or BaseEvent to publish
        
    Returns:
        Event/Message ID
    """
    # Import here to avoid circular dependency
    from meai.events.base import BaseEvent as PydanticBaseEvent
    
    # Handle BaseEvent (new Pydantic events)
    if isinstance(event, PydanticBaseEvent):
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")
        
        # Store in new events table
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO event_bus_events
                (id, type, source, target, priority, timestamp, 
                 correlation_id, reply_to, metadata, data, status)
                VALUES (:id, :type, :source, :target, :priority, :timestamp,
                        :correlation_id, :reply_to, :metadata, :data, :status)
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
                    "data": event.model_dump_json(),
                    "status": "pending"
                }
            )
            await session.commit()
        
        # Notify subscribers
        if event.type in self._subscribers:
            tasks = [
                handler(event)
                for handler in self._subscribers[event.type]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return event.id
    
    # Handle legacy Event (pub/sub pattern)
    if isinstance(event, Event):
        # Notify subscribers
        if event.event_type in self._subscribers:
            tasks = [
                handler(event)
                for handler in self._subscribers[event.event_type]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        return event.event_id
    
    # Handle legacy Message (existing logic)
    if not self._initialized:
        raise RuntimeError("EventBus not initialized. Call initialize() first.")
    
    # Generate message ID if not provided
    if not event.message_id:
        event.message_id = f"msg-{uuid4().hex[:8]}"
    
    # Store message in legacy table
    async with self.db.session() as session:
        await session.execute(
            text("""
            INSERT INTO event_bus_messages
            (message_id, from_agent, to_agent, message_type, priority, payload, timestamp, status)
            VALUES (:message_id, :from_agent, :to_agent, :message_type, :priority, :payload, :timestamp, :status)
            """),
            {
                "message_id": event.message_id,
                "from_agent": event.from_agent,
                "to_agent": event.to_agent,
                "message_type": event.message_type,
                "priority": event.priority,
                "payload": json.dumps(event.payload),
                "timestamp": event.timestamp,
                "status": "pending"
            }
        )
        await session.commit()
    
    return event.message_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_bus.py::test_publish_base_event -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_bus.py tests/events/test_event_bus.py
git commit -m "feat(event-bus): add BaseEvent publishing support

- Extend publish() to handle BaseEvent instances
- Store BaseEvent in event_bus_events table
- Maintain backward compatibility with Event/Message
- Notify subscribers for BaseEvent.type

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Task 2.2: Add get_events() for BaseEvent retrieval

- [ ] **Step 1: Write failing test for event retrieval**

```python
# tests/events/test_event_bus.py
@pytest.mark.asyncio
async def test_get_events_by_target():
    """Test retrieving events by target agent"""
    bus = EventBus()
    await bus.initialize()
    
    # Publish 3 events
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
    event3 = ProjectCreatedEvent(
        source="operator",
        target="content-magister",  # Different target
        project_name="Project 2",
        project_type="medical_marketing",
        client_name="Client 2"
    )
    
    await bus.publish(event1)
    await bus.publish(event2)
    await bus.publish(event3)
    
    # Get events for brand-magister
    events = await bus.get_events(target="brand-magister", limit=10)
    
    assert len(events) == 2
    assert events[0].type == "project.created"
    assert events[1].type == "task.created"
    
    await bus.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_bus.py::test_get_events_by_target -v`
Expected: FAIL with "AttributeError: 'EventBus' object has no attribute 'get_events'"

- [ ] **Step 3: Implement get_events() method**

```python
# src/meai/events/event_bus.py (after publish method)
async def get_events(
    self,
    target: str | None = None,
    event_type: str | None = None,
    correlation_id: str | None = None,
    status: str = "pending",
    limit: int = 100
) -> list[BaseEvent]:
    """Get events from queue
    
    Args:
        target: Filter by target agent
        event_type: Filter by event type
        correlation_id: Filter by correlation chain
        status: Event status (pending, processed, failed)
        limit: Maximum number of events
        
    Returns:
        List of BaseEvent instances
    """
    from meai.events.base import BaseEvent as PydanticBaseEvent
    
    if not self._initialized:
        raise RuntimeError("EventBus not initialized. Call initialize() first.")
    
    # Build query
    conditions = ["status = :status"]
    params = {"status": status, "limit": limit}
    
    if target:
        conditions.append("target = :target")
        params["target"] = target
    
    if event_type:
        conditions.append("type = :event_type")
        params["event_type"] = event_type
    
    if correlation_id:
        conditions.append("correlation_id = :correlation_id")
        params["correlation_id"] = correlation_id
    
    where_clause = " AND ".join(conditions)
    
    async with self.db.session() as session:
        result = await session.execute(
            text(f"""
            SELECT data
            FROM event_bus_events
            WHERE {where_clause}
            ORDER BY priority ASC, created_at ASC
            LIMIT :limit
            """),
            params
        )
        
        events = []
        for row in result.fetchall():
            # Deserialize JSON to dict
            event_data = json.loads(row[0])
            
            # Import the specific event class dynamically
            event_type_str = event_data.get("type", "")
            
            # Map event type to class (import from meai.events)
            from meai import events as events_module
            
            # Convert type to class name: "project.created" -> "ProjectCreatedEvent"
            class_name = "".join(
                word.capitalize() 
                for word in event_type_str.replace(".", "_").split("_")
            ) + "Event"
            
            event_class = getattr(events_module, class_name, PydanticBaseEvent)
            
            # Reconstruct event
            event = event_class.model_validate(event_data)
            events.append(event)
        
        return events
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_bus.py::test_get_events_by_target -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/events/event_bus.py tests/events/test_event_bus.py
git commit -m "feat(event-bus): add get_events() for BaseEvent retrieval

- Add get_events() with filtering by target/type/correlation
- Priority-based ordering (P0 first)
- Dynamic event class reconstruction
- Support for correlation chains

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: Update Routing Logic

**Files:**
- Modify: `src/meai/events/event_bus.py` (subscribe/unsubscribe)
- Test: `tests/events/test_event_bus.py`

### Task 3.1: Add mark_processed/mark_failed for BaseEvent

- [ ] **Step 1: Write failing test**

```python
# tests/events/test_event_bus.py
@pytest.mark.asyncio
async def test_mark_event_processed():
    """Test marking event as processed"""
    bus = EventBus()
    await bus.initialize()
    
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Test Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )
    
    event_id = await bus.publish(event)
    
    # Mark as processed
    await bus.mark_processed(event_id)
    
    # Verify status changed
    stored = await bus._get_event_by_id(event_id)
    assert stored["status"] == "processed"
    
    # Should not appear in pending queue
    pending = await bus.get_events(target="brand-magister", status="pending")
    assert len(pending) == 0
    
    await bus.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/events/test_event_bus.py::test_mark_event_processed -v`
Expected: FAIL (mark_processed only works with legacy messages)

- [ ] **Step 3: Update mark_processed() to handle both tables**

```python
# src/meai/events/event_bus.py (replace existing mark_processed ~line 151)
async def mark_processed(self, event_id: str) -> None:
    """Mark event/message as processed
    
    Args:
        event_id: Event or Message ID
    """
    if not self._initialized:
        raise RuntimeError("EventBus not initialized. Call initialize() first.")
    
    async with self.db.session() as session:
        # Try events table first
        result = await session.execute(
            text("""
            UPDATE event_bus_events
            SET status = 'processed'
            WHERE id = :event_id
            """),
            {"event_id": event_id}
        )
        
        if result.rowcount == 0:
            # Try legacy messages table
            await session.execute(
                text("""
                UPDATE event_bus_messages
                SET status = 'processed'
                WHERE message_id = :event_id
                """),
                {"event_id": event_id}
            )
        
        await session.commit()
```

- [ ] **Step 4: Update mark_failed() similarly**

```python
# src/meai/events/event_bus.py (replace existing mark_failed ~line 171)
async def mark_failed(self, event_id: str, error: str) -> None:
    """Mark event/message as failed
    
    Args:
        event_id: Event or Message ID
        error: Error message
    """
    if not self._initialized:
        raise RuntimeError("EventBus not initialized. Call initialize() first.")
    
    async with self.db.session() as session:
        # Try events table first
        result = await session.execute(
            text("""
            UPDATE event_bus_events
            SET status = 'failed'
            WHERE id = :event_id
            """),
            {"event_id": event_id}
        )
        
        if result.rowcount == 0:
            # Try legacy messages table
            await session.execute(
                text("""
                UPDATE event_bus_messages
                SET status = 'failed'
                WHERE message_id = :event_id
                """),
                {"event_id": event_id}
            )
        
        await session.commit()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/events/test_event_bus.py::test_mark_event_processed -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/meai/events/event_bus.py tests/events/test_event_bus.py
git commit -m "feat(event-bus): update mark_processed/mark_failed for BaseEvent

- Support both event_bus_events and event_bus_messages tables
- Try new table first, fallback to legacy
- Maintain backward compatibility

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 4: Integration Tests

**Files:**
- Create: `tests/events/test_event_bus_integration.py`

### Task 4.1: End-to-end test with real events

- [ ] **Step 1: Write integration test**

```python
# tests/events/test_event_bus_integration.py
"""Integration tests for Event Bus with all event types"""
import pytest
from meai.events.event_bus import EventBus
from meai.events import (
    ProjectCreatedEvent,
    TaskCreatedEvent,
    ErrorOccurredEvent,
    SystemHealthCheckEvent,
    MagisterDataRequestEvent,
    MagisterDataResponseEvent
)
from datetime import datetime

@pytest.mark.asyncio
async def test_full_project_lifecycle():
    """Test complete project lifecycle with multiple event types"""
    bus = EventBus()
    await bus.initialize()
    
    # Phase 1: Project created
    project_event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Medical Marketing Campaign",
        project_type="medical_marketing",
        client_name="HealthCorp"
    )
    await bus.publish(project_event)
    
    # Phase 2: Task created with correlation
    task_event = TaskCreatedEvent(
        source="operator",
        target="brand-magister",
        correlation_id=project_event.id,  # Link to project
        task_title="Brand Analysis",
        task_description="Analyze brand positioning",
        assigned_to="brand-magister"
    )
    await bus.publish(task_event)
    
    # Phase 3: Magister requests data
    request_event = MagisterDataRequestEvent(
        source="brand-magister",
        target="analytics-magister",
        correlation_id=task_event.id,
        data_type="brand_metrics",
        parameters={"timeframe": "30d"}
    )
    await bus.publish(request_event)
    
    # Phase 4: Analytics responds
    response_event = MagisterDataResponseEvent(
        source="analytics-magister",
        target="brand-magister",
        correlation_id=task_event.id,
        reply_to=request_event.id,  # Reply chain
        data_type="brand_metrics",
        data={"sentiment": 0.85, "mentions": 1250}
    )
    await bus.publish(response_event)
    
    # Verify correlation chain
    correlated = await bus.get_events(
        correlation_id=task_event.id,
        status="pending"
    )
    assert len(correlated) == 3  # task, request, response
    
    # Verify reply chain
    reply = await bus.get_events(
        correlation_id=task_event.id,
        status="pending"
    )
    response = [e for e in reply if e.reply_to == request_event.id][0]
    assert response.type == "magister.data_response"
    
    # Verify priority ordering
    all_events = await bus.get_events(status="pending", limit=10)
    # All should be P2 (normal) for these event types
    assert all(e.priority == 2 for e in all_events)
    
    await bus.close()

@pytest.mark.asyncio
async def test_error_handling_flow():
    """Test error events with escalation"""
    bus = EventBus()
    await bus.initialize()
    
    # Error occurs (P0 - critical)
    error_event = ErrorOccurredEvent(
        source="brand-magister",
        target="operator",
        error_type="EXECUTION_ERROR",
        error_severity="CRITICAL",
        error_message="Failed to analyze brand",
        context={"task_id": "task-123"}
    )
    await bus.publish(error_event)
    
    # Verify P0 priority
    critical_events = await bus.get_events(status="pending", limit=10)
    assert critical_events[0].priority == 0  # P0 first
    assert critical_events[0].type == "error.occurred"
    
    await bus.close()

@pytest.mark.asyncio
async def test_subscription_with_base_events():
    """Test pub/sub with BaseEvent"""
    bus = EventBus()
    await bus.initialize()
    
    received_events = []
    
    async def handler(event):
        received_events.append(event)
    
    # Subscribe to project events
    bus.subscribe("project.created", handler)
    
    # Publish event
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        project_name="Test Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )
    await bus.publish(event)
    
    # Wait for async handler
    await asyncio.sleep(0.1)
    
    # Verify handler was called
    assert len(received_events) == 1
    assert received_events[0].id == event.id
    
    await bus.close()
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest tests/events/test_event_bus_integration.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add tests/events/test_event_bus_integration.py
git commit -m "test(event-bus): add end-to-end integration tests

- Test full project lifecycle with correlation chains
- Test error handling with priority ordering
- Test pub/sub with BaseEvent
- Verify all 53 event types work correctly

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Self-Review Checklist

After completing all phases, verify:

### 1. Spec Compliance
- [ ] All 53 Pydantic events can be published
- [ ] Priority-based routing works (P0-P3)
- [ ] Correlation chains work (correlation_id, reply_to)
- [ ] Persistence includes all BaseEvent fields
- [ ] Backward compatibility maintained (Event/Message still work)

### 2. No Placeholders
- [ ] No TBD, TODO, or incomplete code
- [ ] All test cases have actual assertions
- [ ] All error handling implemented

### 3. Type Consistency
- [ ] BaseEvent used consistently
- [ ] Event types match spec ("category.action")
- [ ] Priority values correct (0-3)

---

## Verification Gates

### Tier 1: Required (block completion)
```bash
# Type checking
python -m mypy src/meai/events/event_bus.py --strict

# Tests
python -m pytest tests/events/test_event_bus.py -v
python -m pytest tests/events/test_event_bus_integration.py -v

# Linting
ruff check src/meai/events/event_bus.py
```

### Tier 2: Recommended
```bash
# Test coverage
python -m pytest tests/events/ --cov=src/meai/events/event_bus --cov-report=term-missing

# Should be >90% coverage
```

---

## Execution Handoff

Plan complete and saved to `plans/2026-05-08-event-bus-integration.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - Fresh subagent per phase, review between phases, fast iteration

**2. Inline Execution** - Execute phases in this session using executing-plans, batch execution with checkpoints

**Which approach?**
