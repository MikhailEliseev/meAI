"""Event Store implementation for meAI"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class ConcurrentWriteError(Exception):
    """Raised when concurrent write is detected"""

    pass


@dataclass
class Event:
    """Immutable event representing a fact that happened"""

    aggregate_id: str
    aggregate_type: str
    event_type: str
    event_version: int
    payload: dict[str, Any]
    timestamp: str
    idempotency_key: str | None = None
    id: int | None = None


class EventStore:
    """Event Store for immutable audit log and event replay"""

    def __init__(self, database_url: str):
        """Initialize Event Store

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self._engine: AsyncEngine | None = None

    async def initialize(self) -> None:
        """Initialize database and create events table"""
        self._engine = create_async_engine(self.database_url, echo=False)

        async with self._engine.begin() as conn:
            # Create events table
            await conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregate_id TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_version INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE,
                    created_at TEXT NOT NULL
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_events_aggregate "
                    "ON events(aggregate_id, aggregate_type)"
                )
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_events_idempotency "
                    "ON events(idempotency_key)"
                )
            )

    async def close(self) -> None:
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None

    async def append_event(
        self,
        event: Event,
        side_effect_handler: Callable[[Event], None] | None = None,
    ) -> int:
        """Append event to store with idempotency

        Args:
            event: Event to append
            side_effect_handler: Optional handler for side effects (not called during replay)

        Returns:
            Event ID

        Raises:
            ConcurrentWriteError: If concurrent write detected
        """
        if not self._engine:
            raise RuntimeError("EventStore not initialized")

        # Check if event already exists (idempotency)
        if event.idempotency_key:
            async with self._engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT id FROM events WHERE idempotency_key = :key"),
                    {"key": event.idempotency_key},
                )
                existing = result.fetchone()
                if existing:
                    return existing[0]  # Return existing event ID

        # Append event
        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(
                    text(
                        """
                    INSERT INTO events (
                        aggregate_id, aggregate_type, event_type, event_version,
                        payload, timestamp, idempotency_key, created_at
                    ) VALUES (
                        :aggregate_id, :aggregate_type, :event_type, :event_version,
                        :payload, :timestamp, :idempotency_key, :created_at
                    )
                """
                    ),
                    {
                        "aggregate_id": event.aggregate_id,
                        "aggregate_type": event.aggregate_type,
                        "event_type": event.event_type,
                        "event_version": event.event_version,
                        "payload": json.dumps(event.payload),
                        "timestamp": event.timestamp,
                        "idempotency_key": event.idempotency_key,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                event_id = result.lastrowid

            # Execute side effects (only during normal append, not replay)
            if side_effect_handler:
                side_effect_handler(event)

            return event_id

        except IntegrityError as e:
            # Concurrent write or duplicate idempotency key
            if "idempotency_key" in str(e):
                # Idempotency key conflict - return existing event
                async with self._engine.connect() as conn:
                    result = await conn.execute(
                        text("SELECT id FROM events WHERE idempotency_key = :key"),
                        {"key": event.idempotency_key},
                    )
                    existing = result.fetchone()
                    if existing:
                        return existing[0]
            raise ConcurrentWriteError("Concurrent write detected") from e

    async def get_events(
        self,
        aggregate_id: str | None = None,
        aggregate_type: str | None = None,
        event_type: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> list[Event]:
        """Get events with filters

        Args:
            aggregate_id: Filter by aggregate ID
            aggregate_type: Filter by aggregate type
            event_type: Filter by event type
            from_timestamp: Filter events after this timestamp
            to_timestamp: Filter events before this timestamp

        Returns:
            List of events
        """
        if not self._engine:
            raise RuntimeError("EventStore not initialized")

        # Build query
        query = "SELECT * FROM events WHERE 1=1"
        params: dict[str, Any] = {}

        if aggregate_id:
            query += " AND aggregate_id = :aggregate_id"
            params["aggregate_id"] = aggregate_id

        if aggregate_type:
            query += " AND aggregate_type = :aggregate_type"
            params["aggregate_type"] = aggregate_type

        if event_type:
            query += " AND event_type = :event_type"
            params["event_type"] = event_type

        if from_timestamp:
            query += " AND timestamp >= :from_timestamp"
            params["from_timestamp"] = from_timestamp

        if to_timestamp:
            query += " AND timestamp <= :to_timestamp"
            params["to_timestamp"] = to_timestamp

        query += " ORDER BY timestamp ASC"

        # Execute query
        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params)
            rows = result.fetchall()

        # Convert to Event objects
        events = []
        for row in rows:
            events.append(
                Event(
                    id=row[0],
                    aggregate_id=row[1],
                    aggregate_type=row[2],
                    event_type=row[3],
                    event_version=row[4],
                    payload=json.loads(row[5]),
                    timestamp=row[6],
                    idempotency_key=row[7],
                )
            )

        return events

    async def replay_events(
        self,
        aggregate_id: str,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        side_effect_handler: Callable[[Event], None] | None = None,
        replaying: bool = True,
    ) -> list[Event]:
        """Replay events for aggregate

        Args:
            aggregate_id: Aggregate to replay
            from_timestamp: Start timestamp
            to_timestamp: End timestamp
            side_effect_handler: Optional handler (NOT called if replaying=True)
            replaying: If True, skip side effects

        Returns:
            List of replayed events
        """
        events = await self.get_events(
            aggregate_id=aggregate_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
        )

        # Execute side effects only if not replaying
        if side_effect_handler and not replaying:
            for event in events:
                side_effect_handler(event)

        return events
