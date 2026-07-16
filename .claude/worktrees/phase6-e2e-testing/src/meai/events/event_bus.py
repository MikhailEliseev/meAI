"""Event Bus implementation for meAI"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


@dataclass
class Message:
    """Message for async communication between agents"""

    from_agent: str
    to_agent: str
    message_type: str
    priority: int  # 0 (critical) to 3 (low)
    payload: dict[str, Any]
    timestamp: str
    id: int | None = None
    processed: bool = False
    processed_at: str | None = None
    error: str | None = None


class EventBus:
    """Event Bus for async message queue with priority routing"""

    def __init__(self, database_url: str):
        """Initialize Event Bus

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self._engine: AsyncEngine | None = None
        self._subscribers: dict[str, asyncio.Queue[Message]] = {}
        self._processing = False
        self._processing_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize database and create messages table"""
        self._engine = create_async_engine(self.database_url, echo=False)

        async with self._engine.begin() as conn:
            # Create messages table
            await conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    processed_at TEXT,
                    error TEXT
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_messages_to "
                    "ON messages(to_agent, processed)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_messages_priority "
                    "ON messages(priority, timestamp)"
                )
            )

    async def close(self) -> None:
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None

    async def publish(self, message: Message) -> int:
        """Publish message to bus (persist to SQLite first)

        Args:
            message: Message to publish

        Returns:
            Message ID
        """
        if not self._engine:
            raise RuntimeError("EventBus not initialized")

        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                INSERT INTO messages (
                    from_agent, to_agent, message_type, priority,
                    payload, timestamp, processed
                ) VALUES (
                    :from_agent, :to_agent, :message_type, :priority,
                    :payload, :timestamp, :processed
                )
            """
                ),
                {
                    "from_agent": message.from_agent,
                    "to_agent": message.to_agent,
                    "message_type": message.message_type,
                    "priority": message.priority,
                    "payload": json.dumps(message.payload),
                    "timestamp": message.timestamp,
                    "processed": False,
                },
            )
            return result.lastrowid

    async def subscribe(self, agent_id: str) -> asyncio.Queue[Message]:
        """Subscribe to messages for agent

        Args:
            agent_id: Agent identifier

        Returns:
            Queue for receiving messages
        """
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = asyncio.Queue()
        return self._subscribers[agent_id]

    async def start_processing(self) -> None:
        """Start processing messages from database"""
        if self._processing:
            return

        self._processing = True

        while self._processing:
            try:
                await self._process_batch()
                await asyncio.sleep(0.1)  # Small delay between batches
            except Exception as e:
                print(f"Error processing messages: {e}")
                await asyncio.sleep(1)  # Longer delay on error

    async def stop_processing(self) -> None:
        """Stop processing messages"""
        self._processing = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def _process_batch(self) -> None:
        """Process batch of unprocessed messages"""
        if not self._engine:
            return

        # Get unprocessed messages ordered by priority, then timestamp
        async with self._engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                SELECT * FROM messages
                WHERE processed = FALSE
                ORDER BY priority ASC, timestamp ASC
                LIMIT 100
            """
                )
            )
            rows = result.fetchall()

        # Route messages to subscribers
        for row in rows:
            message = Message(
                id=row[0],
                from_agent=row[1],
                to_agent=row[2],
                message_type=row[3],
                priority=row[4],
                payload=json.loads(row[5]),
                timestamp=row[6],
                processed=row[7],
                processed_at=row[8],
                error=row[9],
            )

            # Route to specific agent or broadcast
            if message.to_agent == "*":
                # Broadcast to all subscribers
                for queue in self._subscribers.values():
                    await queue.put(message)
            elif message.to_agent in self._subscribers:
                # Route to specific agent
                await self._subscribers[message.to_agent].put(message)

            # Mark as processed
            await self.mark_processed(message.id)

    async def mark_processed(
        self, message_id: int, error: str | None = None
    ) -> None:
        """Mark message as processed

        Args:
            message_id: Message ID
            error: Optional error message if processing failed
        """
        if not self._engine:
            raise RuntimeError("EventBus not initialized")

        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                UPDATE messages
                SET processed = TRUE,
                    processed_at = :processed_at,
                    error = :error
                WHERE id = :id
            """
                ),
                {
                    "id": message_id,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "error": error,
                },
            )

    async def is_processed(self, message_id: int) -> bool:
        """Check if message is processed

        Args:
            message_id: Message ID

        Returns:
            True if processed
        """
        if not self._engine:
            raise RuntimeError("EventBus not initialized")

        async with self._engine.connect() as conn:
            result = await conn.execute(
                text("SELECT processed FROM messages WHERE id = :id"),
                {"id": message_id},
            )
            row = result.fetchone()
            return bool(row[0]) if row else False
