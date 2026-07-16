"""SQLite fallback storage for knowledge"""

import json
import aiosqlite
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class FallbackStorage:
    """SQLite fallback storage for when Qdrant is unavailable"""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/fallback.db"):
        """Initialize fallback storage

        Args:
            database_url: SQLAlchemy database URL (will extract path)
        """
        self.database_url = database_url
        # Extract path from SQLAlchemy URL
        if ":///" in database_url:
            self.db_path = database_url.split("///")[1]
        else:
            self.db_path = ":memory:"
        self.db = None

    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        self.db = await aiosqlite.connect(self.db_path)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        await self.db.commit()

    async def shutdown(self) -> None:
        """Shutdown database connection"""
        if self.db:
            await self.db.close()

    async def store_knowledge(
        self,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> str:
        """Store knowledge in fallback storage

        Args:
            content: Knowledge content
            embedding: Embedding vector
            metadata: Metadata dictionary

        Returns:
            Knowledge ID
        """
        knowledge_id = f"fallback-{uuid4().hex[:8]}"

        await self.db.execute(
            """
            INSERT INTO knowledge (id, content, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                knowledge_id,
                content,
                json.dumps(embedding),
                json.dumps(metadata),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        await self.db.commit()

        return knowledge_id

    async def get_knowledge(self, knowledge_id: str) -> dict[str, Any] | None:
        """Get knowledge by ID

        Args:
            knowledge_id: Knowledge ID

        Returns:
            Knowledge dict or None if not found
        """
        async with self.db.execute(
            """
            SELECT id, content, embedding, metadata, created_at
            FROM knowledge
            WHERE id = ?
            """,
            (knowledge_id,),
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "content": row[1],
                "embedding": json.loads(row[2]),
                "metadata": json.loads(row[3]),
                "created_at": row[4],
            }

    async def search_knowledge(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search knowledge by text query

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of knowledge items
        """
        async with self.db.execute(
            """
            SELECT id, content, embedding, metadata, created_at
            FROM knowledge
            WHERE content LIKE ?
            LIMIT ?
            """,
            (f"%{query}%", limit),
        ) as cursor:
            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "content": row[1],
                    "embedding": json.loads(row[2]),
                    "metadata": json.loads(row[3]),
                    "created_at": row[4],
                }
                for row in rows
            ]
