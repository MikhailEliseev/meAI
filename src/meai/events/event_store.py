"""Event Store - Immutable audit log for event replay and debugging.

This module provides append-only event storage with:
- Immutable storage (no updates/deletes)
- Event retrieval by ID
- Dynamic event class reconstruction from JSON
- Efficient querying with indexes
- Full audit trail capability
"""

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from meai.events.base import BaseEvent
from meai.storage.database import Database


class EventStore:
    """Append-only event store for immutable audit log.

    Features:
    - Immutable storage (no updates/deletes)
    - Dynamic event class reconstruction
    - Efficient querying with indexes
    - Full audit trail

    Usage:
        store = EventStore()
        await store.initialize()

        # Append event
        await store.append(event)

        # Retrieve event
        event = await store.get_by_id(event_id)

        await store.close()
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///:memory:"):
        """Initialize Event Store.

        Args:
            database_url: SQLAlchemy database URL (default: in-memory SQLite)
        """
        self.database_url = database_url
        self.db = Database(database_url)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database connection and create schema."""
        await self.db.connect()
        await self._create_schema()
        self._initialized = True

    async def _create_schema(self) -> None:
        """Create event_store table and indexes."""
        async with self.db.session() as session:
            # Create table
            await session.execute(text("""
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
            """))

            # Create indexes
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_store_type
                ON event_store(type)
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_store_correlation
                ON event_store(correlation_id)
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_store_timestamp
                ON event_store(timestamp)
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_store_created_at
                ON event_store(created_at)
            """))

            await session.commit()

    async def append(self, event: BaseEvent) -> None:
        """Append event to store (immutable).

        Args:
            event: Event to store

        Raises:
            RuntimeError: If store not initialized
        """
        if not self._initialized:
            raise RuntimeError("EventStore not initialized. Call initialize() first.")

        # Serialize event to JSON
        event_json = event.model_dump_json()
        event_dict = event.model_dump()

        # Handle target (can be string or list)
        target = event_dict["target"]
        if isinstance(target, list):
            target = json.dumps(target)

        async with self.db.session() as session:
            await session.execute(
                text("""
                    INSERT INTO event_store (
                        id, type, source, target, priority, timestamp,
                        correlation_id, reply_to, metadata, data
                    ) VALUES (
                        :id, :type, :source, :target, :priority, :timestamp,
                        :correlation_id, :reply_to, :metadata, :data
                    )
                """),
                {
                    "id": str(event.id),
                    "type": event.type,
                    "source": event.source,
                    "target": target,
                    "priority": event.priority,
                    "timestamp": event.timestamp.isoformat(),
                    "correlation_id": event.correlation_id,
                    "reply_to": event.reply_to,
                    "metadata": json.dumps(event.metadata) if event.metadata else None,
                    "data": event_json,
                }
            )
            await session.commit()

    async def get_by_id(self, event_id: str) -> BaseEvent | None:
        """Retrieve event by ID.

        Args:
            event_id: Event ID to retrieve

        Returns:
            Event instance or None if not found

        Raises:
            RuntimeError: If store not initialized
        """
        if not self._initialized:
            raise RuntimeError("EventStore not initialized. Call initialize() first.")

        async with self.db.session() as session:
            result = await session.execute(
                text("SELECT data FROM event_store WHERE id = :id"),
                {"id": event_id}
            )
            row = result.fetchone()

            if row is None:
                return None

            # Reconstruct event from JSON
            event_data = json.loads(row[0])
            return self._reconstruct_event(event_data)

    async def get_by_correlation(self, correlation_id: str) -> list[BaseEvent]:
        """Get all events in correlation chain.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of events in chronological order

        Raises:
            RuntimeError: If store not initialized
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
            rows = result.fetchall()

            # Reconstruct events from JSON
            events = []
            for row in rows:
                event_data = json.loads(row[0])
                events.append(self._reconstruct_event(event_data))

            return events

    def _reconstruct_event(self, event_data: dict[str, Any]) -> BaseEvent:
        """Reconstruct event instance from JSON data.

        Args:
            event_data: Event data dictionary

        Returns:
            Event instance (specific class or BaseEvent fallback)
        """
        event_type = event_data.get("type")

        # Try to find specific event class
        event_class = self._get_event_class(event_type)

        if event_class:
            # Reconstruct with specific class
            return event_class.model_validate(event_data)
        else:
            # Fallback to BaseEvent
            return BaseEvent.model_validate(event_data)

    def _get_event_class(self, event_type: str) -> type[BaseEvent] | None:
        """Get event class by type string.

        Args:
            event_type: Event type (e.g., "project.created")

        Returns:
            Event class or None if not found
        """
        # Convert type to class name: "project.created" -> "ProjectCreatedEvent"
        parts = event_type.split(".")
        class_name = "".join(word.capitalize() for word in parts) + "Event"

        # Try to import from meai.events modules
        try:
            # Import all event modules
            from meai import events as events_module

            # Try to get class from events module
            if hasattr(events_module, class_name):
                return getattr(events_module, class_name)

            # Try specific modules
            module_names = [
                "project_events",
                "task_events",
                "error_events",
                "system_events",
                "client_events",
                "sprint_events",
                "magister_events",
            ]

            for module_name in module_names:
                try:
                    module = __import__(
                        f"meai.events.{module_name}",
                        fromlist=[class_name]
                    )
                    if hasattr(module, class_name):
                        return getattr(module, class_name)
                except (ImportError, AttributeError):
                    continue

            return None
        except Exception:
            return None

    async def close(self) -> None:
        """Close database connection."""
        await self.db.disconnect()
        self._initialized = False
