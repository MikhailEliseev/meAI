"""Track task outcomes and knowledge usage"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.storage.database import Database


class ExperienceTracker:
    """Track task experiences and knowledge usage

    Records:
    - Task outcomes (success/failure)
    - Knowledge used in tasks
    - Outcome scores (0.0 - 1.0)
    - Feedback from task execution

    Provides analytics:
    - Knowledge success rate
    - Average outcome score
    - Usage frequency
    - Recent experiences
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/meai.db"):
        """Initialize Experience Tracker

        Args:
            database_url: Database URL
        """
        self.db = Database(database_url)

    async def initialize(self) -> None:
        """Initialize tracker"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown tracker"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create experience tracking tables"""
        async with self.db.session() as session:
            # Experiences table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    knowledge_ids TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    outcome_score REAL,
                    feedback TEXT,
                    created_at TIMESTAMP NOT NULL
                )
                """)
            )

            # Knowledge usage stats (denormalized for performance)
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS knowledge_stats (
                    knowledge_id TEXT PRIMARY KEY,
                    total_uses INTEGER DEFAULT 0,
                    successful_uses INTEGER DEFAULT 0,
                    failed_uses INTEGER DEFAULT 0,
                    total_score REAL DEFAULT 0.0,
                    last_used_at TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.commit()

    async def record_experience(
        self,
        magister_id: str,
        task_id: str,
        knowledge_ids: list[str],
        outcome: str,
        outcome_score: float | None = None,
        feedback: str | None = None,
    ) -> str:
        """Record a task experience

        Args:
            magister_id: Magister that executed the task
            task_id: Task identifier
            knowledge_ids: Knowledge used in the task
            outcome: Task outcome (success, failure, partial)
            outcome_score: Outcome quality score (0.0 - 1.0)
            feedback: Optional feedback text

        Returns:
            Experience ID
        """
        experience_id = f"exp-{uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc)

        async with self.db.session() as session:
            # Record experience
            await session.execute(
                text("""
                INSERT INTO experiences
                (id, magister_id, task_id, knowledge_ids, outcome,
                 outcome_score, feedback, created_at)
                VALUES (:id, :magister_id, :task_id, :knowledge_ids,
                        :outcome, :outcome_score, :feedback, :created_at)
                """),
                {
                    "id": experience_id,
                    "magister_id": magister_id,
                    "task_id": task_id,
                    "knowledge_ids": json.dumps(knowledge_ids),
                    "outcome": outcome,
                    "outcome_score": outcome_score,
                    "feedback": feedback,
                    "created_at": created_at,
                },
            )

            # Update knowledge stats
            for knowledge_id in knowledge_ids:
                await self._update_knowledge_stats(
                    session,
                    knowledge_id,
                    outcome,
                    outcome_score or 0.0,
                    created_at,
                )

            await session.commit()

        return experience_id

    async def _update_knowledge_stats(
        self,
        session,
        knowledge_id: str,
        outcome: str,
        outcome_score: float,
        timestamp: datetime,
    ) -> None:
        """Update knowledge usage statistics

        Args:
            session: Database session
            knowledge_id: Knowledge ID
            outcome: Task outcome
            outcome_score: Outcome score
            timestamp: Timestamp
        """
        # Check if stats exist
        result = await session.execute(
            text("""
            SELECT total_uses FROM knowledge_stats
            WHERE knowledge_id = :knowledge_id
            """),
            {"knowledge_id": knowledge_id},
        )
        exists = result.fetchone() is not None

        if exists:
            # Update existing stats
            await session.execute(
                text("""
                UPDATE knowledge_stats
                SET total_uses = total_uses + 1,
                    successful_uses = successful_uses + CASE WHEN :outcome = 'success' THEN 1 ELSE 0 END,
                    failed_uses = failed_uses + CASE WHEN :outcome = 'failure' THEN 1 ELSE 0 END,
                    total_score = total_score + :outcome_score,
                    last_used_at = :timestamp,
                    updated_at = :timestamp
                WHERE knowledge_id = :knowledge_id
                """),
                {
                    "knowledge_id": knowledge_id,
                    "outcome": outcome,
                    "outcome_score": outcome_score,
                    "timestamp": timestamp,
                },
            )
        else:
            # Create new stats
            await session.execute(
                text("""
                INSERT INTO knowledge_stats
                (knowledge_id, total_uses, successful_uses, failed_uses,
                 total_score, last_used_at, updated_at)
                VALUES (:knowledge_id, 1,
                        CASE WHEN :outcome = 'success' THEN 1 ELSE 0 END,
                        CASE WHEN :outcome = 'failure' THEN 1 ELSE 0 END,
                        :outcome_score, :timestamp, :timestamp)
                """),
                {
                    "knowledge_id": knowledge_id,
                    "outcome": outcome,
                    "outcome_score": outcome_score,
                    "timestamp": timestamp,
                },
            )

    async def get_knowledge_success_rate(self, knowledge_id: str) -> float:
        """Get success rate for knowledge

        Args:
            knowledge_id: Knowledge ID

        Returns:
            Success rate (0.0 - 1.0)
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT total_uses, successful_uses
                FROM knowledge_stats
                WHERE knowledge_id = :knowledge_id
                """),
                {"knowledge_id": knowledge_id},
            )
            row = result.fetchone()

        if not row or row[0] == 0:
            return 0.0

        total_uses, successful_uses = row
        return successful_uses / total_uses

    async def get_knowledge_average_score(self, knowledge_id: str) -> float:
        """Get average outcome score for knowledge

        Args:
            knowledge_id: Knowledge ID

        Returns:
            Average score (0.0 - 1.0)
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT total_uses, total_score
                FROM knowledge_stats
                WHERE knowledge_id = :knowledge_id
                """),
                {"knowledge_id": knowledge_id},
            )
            row = result.fetchone()

        if not row or row[0] == 0:
            return 0.0

        total_uses, total_score = row
        return total_score / total_uses

    async def get_knowledge_usage_count(self, knowledge_id: str) -> int:
        """Get usage count for knowledge

        Args:
            knowledge_id: Knowledge ID

        Returns:
            Usage count
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT total_uses
                FROM knowledge_stats
                WHERE knowledge_id = :knowledge_id
                """),
                {"knowledge_id": knowledge_id},
            )
            row = result.fetchone()

        return row[0] if row else 0

    async def get_magister_experiences(
        self,
        magister_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get experiences for a Magister

        Args:
            magister_id: Magister ID
            limit: Maximum number of experiences

        Returns:
            List of experiences
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, magister_id, task_id, knowledge_ids, outcome,
                       outcome_score, feedback, created_at
                FROM experiences
                WHERE magister_id = :magister_id
                ORDER BY created_at DESC
                LIMIT :limit
                """),
                {"magister_id": magister_id, "limit": limit},
            )
            rows = result.fetchall()

        experiences = []
        for row in rows:
            experiences.append({
                "id": row[0],
                "magister_id": row[1],
                "task_id": row[2],
                "knowledge_ids": json.loads(row[3]),
                "outcome": row[4],
                "outcome_score": row[5],
                "feedback": row[6],
                "created_at": row[7],
            })

        return experiences

    async def get_recent_experiences(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent experiences across all Magisters

        Args:
            limit: Maximum number of experiences

        Returns:
            List of experiences
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, magister_id, task_id, knowledge_ids, outcome,
                       outcome_score, feedback, created_at
                FROM experiences
                ORDER BY created_at DESC
                LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = result.fetchall()

        experiences = []
        for row in rows:
            experiences.append({
                "id": row[0],
                "magister_id": row[1],
                "task_id": row[2],
                "knowledge_ids": json.loads(row[3]),
                "outcome": row[4],
                "outcome_score": row[5],
                "feedback": row[6],
                "created_at": row[7],
            })

        return experiences

    async def get_knowledge_stats(self, knowledge_id: str) -> dict[str, Any]:
        """Get comprehensive stats for knowledge

        Args:
            knowledge_id: Knowledge ID

        Returns:
            Stats dictionary
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT total_uses, successful_uses, failed_uses,
                       total_score, last_used_at, updated_at
                FROM knowledge_stats
                WHERE knowledge_id = :knowledge_id
                """),
                {"knowledge_id": knowledge_id},
            )
            row = result.fetchone()

        if not row:
            return {
                "knowledge_id": knowledge_id,
                "total_uses": 0,
                "successful_uses": 0,
                "failed_uses": 0,
                "success_rate": 0.0,
                "average_score": 0.0,
                "last_used_at": None,
            }

        total_uses, successful_uses, failed_uses, total_score, last_used_at, updated_at = row

        return {
            "knowledge_id": knowledge_id,
            "total_uses": total_uses,
            "successful_uses": successful_uses,
            "failed_uses": failed_uses,
            "success_rate": successful_uses / total_uses if total_uses > 0 else 0.0,
            "average_score": total_score / total_uses if total_uses > 0 else 0.0,
            "last_used_at": last_used_at,
            "updated_at": updated_at,
        }
