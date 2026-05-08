"""Event Bus for async agent communication"""

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Callable, Awaitable
from uuid import uuid4

from typing import TYPE_CHECKING

from sqlalchemy import text
from meai.storage.database import Database
from meai.events.base import BaseEvent

if TYPE_CHECKING:
    from meai.events.event_store import EventStore


class EventPriority(IntEnum):
    """Event priority levels

    P0 = Critical (system failures, security alerts)
    P1 = High (important business events, reports)
    P2 = Normal (regular operations, analytics)
    P3 = Low (background tasks, cleanup)
    """
    P0 = 0  # Critical
    P1 = 1  # High
    P2 = 2  # Normal
    P3 = 3  # Low


@dataclass
class Event:
    """Event for pub/sub pattern"""

    event_type: str
    payload: dict[str, Any]
    event_id: str | None = None
    timestamp: str | None = None

    def __post_init__(self):
        if self.event_id is None:
            self.event_id = f"evt-{uuid4().hex[:8]}"
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    """Message sent between agents"""

    from_agent: str
    to_agent: str
    message_type: str
    priority: int  # 0-3 (P0 = highest)
    payload: dict[str, Any]
    timestamp: str
    message_id: str | None = None


class EventBus:
    """Async event bus for agent communication

    Features:
    - Priority-based message queue (P0-P3)
    - Persistent message storage
    - Pub/sub pattern
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///:memory:"):
        """Initialize Event Bus

        Args:
            database_url: Database connection URL
        """
        self.db = Database(database_url)
        self._initialized = False
        self._subscribers: dict[str, list[Callable[[Event], Awaitable[None]]]] = {}
        self._event_store: "EventStore | None" = None

    async def initialize(self) -> None:
        """Initialize Event Bus"""
        await self.db.connect()
        await self._create_tables()
        self._initialized = True

    async def close(self) -> None:
        """Close Event Bus"""
        await self.db.disconnect()

    def set_event_store(self, event_store: "EventStore") -> None:
        """Set Event Store for automatic event persistence

        Args:
            event_store: EventStore instance
        """
        self._event_store = event_store

    async def _create_tables(self) -> None:
        """Create Event Bus tables"""
        async with self.db.session() as session:
            # Legacy table for Message objects (backward compatibility)
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

            # New table for BaseEvent objects
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS event_bus_events (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    reply_to TEXT,
                    metadata TEXT NOT NULL,
                    data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )

            # Indexes for efficient querying
            await session.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_events_correlation
                ON event_bus_events(correlation_id)
                """)
            )

            await session.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_events_reply_to
                ON event_bus_events(reply_to)
                """)
            )

            await session.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_status_priority
                ON event_bus_events(status, priority)
                """)
            )

            await session.commit()

    async def _get_event_by_id(self, event_id: str) -> dict[str, Any]:
        """Get event by ID from event_bus_events table

        Args:
            event_id: Event ID to retrieve

        Returns:
            Dictionary with event data

        Raises:
            RuntimeError: If EventBus not initialized
            ValueError: If event not found
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
                {"event_id": event_id},
            )

            row = result.fetchone()
            if not row:
                raise ValueError(f"Event not found: {event_id}")

            return {
                "id": row[0],
                "type": row[1],
                "source": row[2],
                "target": row[3],
                "priority": row[4],
                "timestamp": row[5],
                "correlation_id": row[6],
                "reply_to": row[7],
                "metadata": json.loads(row[8]),
                "data": json.loads(row[9]),
                "status": row[10],
            }

    async def get_messages(
        self, agent_id: str, status: str = "pending", limit: int = 100
    ) -> list[Message]:
        """Get messages for agent

        Args:
            agent_id: Agent ID
            status: Message status (pending, processed, failed)
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT message_id, from_agent, to_agent, message_type, priority, payload, timestamp
                FROM event_bus_messages
                WHERE to_agent = :agent_id AND status = :status
                ORDER BY priority ASC, created_at ASC
                LIMIT :limit
                """),
                {"agent_id": agent_id, "status": status, "limit": limit},
            )

            messages = []
            for row in result.fetchall():
                messages.append(
                    Message(
                        message_id=row[0],
                        from_agent=row[1],
                        to_agent=row[2],
                        message_type=row[3],
                        priority=row[4],
                        payload=json.loads(row[5]),
                        timestamp=row[6],
                    )
                )

            return messages

    async def mark_processed(self, message_id: str) -> None:
        """Mark message or event as processed

        Supports both new event_bus_events table and legacy event_bus_messages table.
        Tries new table first, falls back to legacy if not found.

        Args:
            message_id: Message ID or Event ID
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        async with self.db.session() as session:
            # Try event_bus_events table first (new BaseEvent system)
            result = await session.execute(
                text("""
                UPDATE event_bus_events
                SET status = 'processed'
                WHERE id = :message_id
                """),
                {"message_id": message_id},
            )

            # If no rows updated, try legacy event_bus_messages table
            if result.rowcount == 0:
                await session.execute(
                    text("""
                    UPDATE event_bus_messages
                    SET status = 'processed'
                    WHERE message_id = :message_id
                    """),
                    {"message_id": message_id},
                )

            await session.commit()

    async def mark_failed(self, message_id: str, error: str) -> None:
        """Mark message or event as failed

        Supports both new event_bus_events table and legacy event_bus_messages table.
        Tries new table first, falls back to legacy if not found.

        Args:
            message_id: Message ID or Event ID
            error: Error message
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        async with self.db.session() as session:
            # Try event_bus_events table first (new BaseEvent system)
            result = await session.execute(
                text("""
                UPDATE event_bus_events
                SET status = 'failed'
                WHERE id = :message_id
                """),
                {"message_id": message_id},
            )

            # If no rows updated, try legacy event_bus_messages table
            if result.rowcount == 0:
                await session.execute(
                    text("""
                    UPDATE event_bus_messages
                    SET status = 'failed'
                    WHERE message_id = :message_id
                    """),
                    {"message_id": message_id},
                )

            await session.commit()

    async def get_events(
        self,
        target: str | None = None,
        event_type: str | None = None,
        correlation_id: str | None = None,
        status: str = "pending",
        limit: int = 100,
    ) -> list[BaseEvent]:
        """Get events from queue with filtering

        Args:
            target: Filter by target agent
            event_type: Filter by event type
            correlation_id: Filter by correlation ID
            status: Event status (pending, processed, failed)
            limit: Maximum number of events

        Returns:
            List of BaseEvent instances
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        # Build dynamic WHERE clause
        where_conditions = ["status = :status"]
        params = {"status": status, "limit": limit}

        if target:
            where_conditions.append("target = :target")
            params["target"] = target

        if event_type:
            where_conditions.append("type = :event_type")
            params["event_type"] = event_type

        if correlation_id:
            where_conditions.append("correlation_id = :correlation_id")
            params["correlation_id"] = correlation_id

        where_clause = " AND ".join(where_conditions)

        async with self.db.session() as session:
            # Safe to use f-string here: where_clause is built from hardcoded SQL fragments only
            result = await session.execute(
                text(f"""
                SELECT id, type, source, target, priority, timestamp,
                       correlation_id, reply_to, metadata, data, status
                FROM event_bus_events
                WHERE {where_clause}
                ORDER BY priority ASC, created_at ASC
                LIMIT :limit
                """),
                params,
            )

            events = []
            for row in result.fetchall():
                event_data = {
                    "id": row[0],
                    "type": row[1],
                    "source": row[2],
                    "target": row[3],
                    "priority": row[4],
                    "timestamp": row[5],
                    "correlation_id": row[6],
                    "reply_to": row[7],
                    "metadata": json.loads(row[8]),
                }

                # Parse the full event data JSON
                full_data = json.loads(row[9])

                # Dynamically import event class based on type
                event_type_str = row[1]  # e.g., "project.created"

                # Convert type to class name: "project.created" -> "ProjectCreatedEvent"
                class_name = "".join(
                    word.capitalize() for word in event_type_str.split(".")
                ) + "Event"

                try:
                    # Import from meai.events module
                    from meai import events as events_module

                    # Try to get specific event class
                    event_class = getattr(events_module, class_name, None)

                    if event_class and issubclass(event_class, BaseEvent):
                        # Reconstruct event using Pydantic validation
                        event = event_class.model_validate(full_data)
                    else:
                        # Fallback to BaseEvent if specific class not found
                        event = BaseEvent.model_validate(full_data)

                    events.append(event)
                except (AttributeError, ImportError) as e:
                    # Log fallback for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Could not load event class {class_name}, using BaseEvent: {e}")
                    event = BaseEvent.model_validate(full_data)
                    events.append(event)

            return events

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Subscribe to events of a specific type

        Args:
            event_type: Event type to subscribe to
            handler: Async handler function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Unsubscribe from events

        Args:
            event_type: Event type
            handler: Handler function to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event | Message | BaseEvent) -> str:
        """Publish event or message

        Args:
            event: Event, Message, or BaseEvent to publish

        Returns:
            Event/Message ID
        """
        # Handle BaseEvent (Pydantic models)
        if isinstance(event, BaseEvent):
            if not self._initialized:
                raise RuntimeError("EventBus not initialized. Call initialize() first.")

            # Store event in event_bus_events table
            async with self.db.session() as session:
                # Convert target to JSON if it's a list
                target_str = json.dumps(event.target) if isinstance(event.target, list) else event.target

                await session.execute(
                    text("""
                    INSERT INTO event_bus_events
                    (id, type, source, target, priority, timestamp,
                     correlation_id, reply_to, metadata, data, status)
                    VALUES (:id, :type, :source, :target, :priority, :timestamp,
                            :correlation_id, :reply_to, :metadata, :data, :status)
                    """),
                    {
                        "id": str(event.id),
                        "type": event.type,
                        "source": event.source,
                        "target": target_str,
                        "priority": event.priority,
                        "timestamp": event.timestamp.isoformat(),
                        "correlation_id": event.correlation_id,
                        "reply_to": event.reply_to,
                        "metadata": json.dumps(event.metadata),
                        "data": event.model_dump_json(),
                        "status": "pending",
                    },
                )
                await session.commit()

            # Append to Event Store if configured
            if self._event_store:
                await self._event_store.append(event)

            # Notify subscribers for event.type
            if event.type in self._subscribers:
                tasks = [handler(event) for handler in self._subscribers[event.type]]
                await asyncio.gather(*tasks, return_exceptions=True)

            return str(event.id)

        # Handle Event (pub/sub pattern - legacy dataclass)
        if isinstance(event, Event):
            # Notify subscribers
            if event.event_type in self._subscribers:
                tasks = [
                    handler(event)
                    for handler in self._subscribers[event.event_type]
                ]
                # Run handlers concurrently
                await asyncio.gather(*tasks, return_exceptions=True)
            return event.event_id

        # Handle Message (existing logic)
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        # Generate message ID if not provided
        if not event.message_id:
            event.message_id = f"msg-{uuid4().hex[:8]}"

        # Store message
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
                    "status": "pending",
                },
            )
            await session.commit()

        return event.message_id


# ============================================================================
# Analytics Events Documentation
# ============================================================================

"""
Analytics Events for Domain Analytics Architecture

Domain Analytics subagents publish events to Analytics Magister for
cross-domain analysis and strategic insights.

Event Types:

1. analytics.domain_metrics_ready
   - Published by: Domain Analytics subagents (SEO/Content/Ads/AI Analytics)
   - Consumed by: Analytics Magister
   - Priority: P2 (Normal)
   - Payload:
     {
       "domain": "seo",
       "metrics": AggregatedMetrics.dict(),
       "timestamp": "2026-05-05T10:00:00Z"
     }
   - Description: Domain Analytics subagent has aggregated metrics ready

2. analytics.daily_report_ready
   - Published by: Analytics Magister
   - Consumed by: Operator, Magisters
   - Priority: P1 (High)
   - Payload:
     {
       "report_type": "daily",
       "cross_domain_metrics": CrossDomainMetrics.dict(),
       "strategic_insights": [StrategicInsight.dict()],
       "timestamp": "2026-05-05T10:00:00Z"
     }
   - Description: Analytics Magister has generated daily report

3. analytics.alert
   - Published by: Analytics Magister
   - Consumed by: Operator, affected Magisters
   - Priority: P0 (Critical) or P1 (High)
   - Payload:
     {
       "severity": "high",
       "message": "SEO traffic dropped 25%",
       "affected_domains": ["seo", "content"],
       "metric": "organic_sessions",
       "current_value": 11250.0,
       "threshold_value": 15000.0,
       "change_percent": -25.0,
       "recommendation": "Investigate Google algorithm update",
       "timestamp": "2026-05-05T14:30:00Z"
     }
   - Description: Critical metric change detected

4. analytics.correlation_found
   - Published by: Analytics Magister
   - Consumed by: Operator, affected Magisters
   - Priority: P2 (Normal)
   - Payload:
     {
       "correlation": Correlation.dict(),
       "strategic_insight": StrategicInsight.dict(),
       "timestamp": "2026-05-05T10:30:00Z"
     }
   - Description: Cross-domain correlation discovered

Usage Example:

    from meai.events.event_bus import EventBus, Event, EventPriority
    from aim.models.analytics_models import AggregatedMetrics

    # Domain Analytics publishes metrics
    await event_bus.publish(Event(
        event_type="analytics.domain_metrics_ready",
        payload={
            "domain": "seo",
            "metrics": aggregated_metrics.dict(),
            "timestamp": datetime.now().isoformat()
        },
        priority=EventPriority.P2
    ))

    # Analytics Magister publishes alert
    await event_bus.publish(Event(
        event_type="analytics.alert",
        payload={
            "severity": "high",
            "message": "SEO traffic dropped 25%",
            "affected_domains": ["seo", "content"],
            "timestamp": datetime.now().isoformat()
        },
        priority=EventPriority.P0
    ))
"""
