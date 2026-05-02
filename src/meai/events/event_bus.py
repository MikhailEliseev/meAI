"""Event Bus for async agent communication"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from meai.storage.database import Database


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

    def __init__(self, database_url: str):
        """Initialize Event Bus

        Args:
            database_url: Database connection URL
        """
        self.db = Database(database_url)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Event Bus"""
        await self.db.connect()
        await self._create_tables()
        self._initialized = True

    async def close(self) -> None:
        """Close Event Bus"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create Event Bus tables"""
        async with self.db.session() as session:
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
            await session.commit()

    async def publish(self, message: Message) -> str:
        """Publish message to Event Bus

        Args:
            message: Message to publish

        Returns:
            Message ID
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        # Generate message ID if not provided
        if not message.message_id:
            message.message_id = f"msg-{uuid4().hex[:8]}"

        # Store message
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO event_bus_messages
                (message_id, from_agent, to_agent, message_type, priority, payload, timestamp, status)
                VALUES (:message_id, :from_agent, :to_agent, :message_type, :priority, :payload, :timestamp, :status)
                """),
                {
                    "message_id": message.message_id,
                    "from_agent": message.from_agent,
                    "to_agent": message.to_agent,
                    "message_type": message.message_type,
                    "priority": message.priority,
                    "payload": json.dumps(message.payload),
                    "timestamp": message.timestamp,
                    "status": "pending",
                },
            )
            await session.commit()

        return message.message_id

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
            for row in await result.fetchall():
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
        """Mark message as processed

        Args:
            message_id: Message ID
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        async with self.db.session() as session:
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
        """Mark message as failed

        Args:
            message_id: Message ID
            error: Error message
        """
        if not self._initialized:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE event_bus_messages
                SET status = 'failed'
                WHERE message_id = :message_id
                """),
                {"message_id": message_id},
            )
            await session.commit()
