"""Update knowledge quality scores based on real-world experience"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.learning.experience_tracker import ExperienceTracker
from meai.storage.database import Database


class QualityUpdater:
    """Update knowledge quality scores based on experience

    Algorithm:
    1. Get knowledge usage stats from ExperienceTracker
    2. Calculate adjustment based on:
       - Success rate (higher = increase quality)
       - Average outcome score (higher = increase quality)
       - Usage frequency (more data = more confidence)
    3. Apply weighted adjustment to current quality score
    4. Update Teacher's Qdrant metadata

    Quality score range: 1.0 - 10.0
    """

    def __init__(
        self,
        experience_tracker: ExperienceTracker,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        learning_rate: float = 0.3,
        min_usage_for_update: int = 5,
    ):
        """Initialize Quality Updater

        Args:
            experience_tracker: Experience tracker instance
            database_url: Database URL
            learning_rate: How quickly to adjust quality (0.0 - 1.0)
            min_usage_for_update: Minimum usage count before updating
        """
        self.tracker = experience_tracker
        self.db = Database(database_url)
        self.learning_rate = learning_rate
        self.min_usage_for_update = min_usage_for_update

    async def initialize(self) -> None:
        """Initialize updater"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown updater"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create quality update tracking tables"""
        async with self.db.session() as session:
            # Quality updates history
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS quality_updates (
                    id TEXT PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    old_score REAL NOT NULL,
                    new_score REAL NOT NULL,
                    adjustment REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    average_score REAL NOT NULL,
                    usage_count INTEGER NOT NULL,
                    reason TEXT,
                    updated_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.commit()

    async def calculate_new_quality_score(
        self,
        knowledge_id: str,
        current_score: float,
    ) -> float:
        """Calculate new quality score based on experience

        Args:
            knowledge_id: Knowledge ID
            current_score: Current quality score

        Returns:
            New quality score (1.0 - 10.0)
        """
        # Get experience stats
        stats = await self.tracker.get_knowledge_stats(knowledge_id)

        if stats["total_uses"] < self.min_usage_for_update:
            # Not enough data yet
            return current_score

        success_rate = stats["success_rate"]
        average_score = stats["average_score"]

        # Calculate target score based on performance
        # Success rate: 0.0 - 1.0 → 1.0 - 10.0
        # Average score: 0.0 - 1.0 → 1.0 - 10.0
        target_from_success = 1.0 + (success_rate * 9.0)
        target_from_score = 1.0 + (average_score * 9.0)

        # Weighted average (success rate is more important)
        target_score = (target_from_success * 0.6) + (target_from_score * 0.4)

        # Apply learning rate (gradual adjustment)
        adjustment = (target_score - current_score) * self.learning_rate
        new_score = current_score + adjustment

        # Clamp to valid range
        new_score = max(1.0, min(10.0, new_score))

        return new_score

    async def update_knowledge_quality(
        self,
        knowledge_id: str,
        current_score: float,
    ) -> dict[str, Any]:
        """Update knowledge quality score

        Args:
            knowledge_id: Knowledge ID
            current_score: Current quality score

        Returns:
            Update result with new score
        """
        # Calculate new score
        new_score = await self.calculate_new_quality_score(
            knowledge_id,
            current_score,
        )

        # Get stats for logging
        stats = await self.tracker.get_knowledge_stats(knowledge_id)

        # Determine reason
        adjustment = new_score - current_score
        if adjustment > 0.5:
            reason = "Strong positive performance"
        elif adjustment > 0:
            reason = "Positive performance"
        elif adjustment < -0.5:
            reason = "Strong negative performance"
        elif adjustment < 0:
            reason = "Negative performance"
        else:
            reason = "No significant change"

        # Log update
        update_id = f"qupdate-{uuid4().hex[:8]}"
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO quality_updates
                (id, knowledge_id, old_score, new_score, adjustment,
                 success_rate, average_score, usage_count, reason, updated_at)
                VALUES (:id, :knowledge_id, :old_score, :new_score, :adjustment,
                        :success_rate, :average_score, :usage_count, :reason, :updated_at)
                """),
                {
                    "id": update_id,
                    "knowledge_id": knowledge_id,
                    "old_score": current_score,
                    "new_score": new_score,
                    "adjustment": adjustment,
                    "success_rate": stats["success_rate"],
                    "average_score": stats["average_score"],
                    "usage_count": stats["total_uses"],
                    "reason": reason,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()

        # Update Teacher's Qdrant metadata
        updated = await self._update_teacher_quality(knowledge_id, new_score)

        return {
            "knowledge_id": knowledge_id,
            "old_score": current_score,
            "new_score": new_score,
            "adjustment": adjustment,
            "reason": reason,
            "updated": updated,
            "stats": stats,
        }

    async def _update_teacher_quality(
        self,
        knowledge_id: str,
        new_score: float,
    ) -> bool:
        """Update quality score in Teacher's Qdrant

        Args:
            knowledge_id: Knowledge ID
            new_score: New quality score

        Returns:
            True if updated successfully
        """
        # TODO: Implement Qdrant metadata update
        # This will be implemented when integrating with Teacher
        # For now, just return True
        return True

    async def batch_update_qualities(
        self,
        knowledge_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Update quality scores for multiple knowledge items

        Args:
            knowledge_items: List of dicts with 'id' and 'current_score'

        Returns:
            List of update results
        """
        results = []

        for item in knowledge_items:
            result = await self.update_knowledge_quality(
                knowledge_id=item["id"],
                current_score=item["current_score"],
            )
            results.append(result)

        return results

    async def get_quality_update_recommendations(
        self,
        min_usage_count: int = 10,
        min_adjustment_threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Get recommendations for quality updates

        Args:
            min_usage_count: Minimum usage count to consider
            min_adjustment_threshold: Minimum adjustment to recommend

        Returns:
            List of recommendations
        """
        # Get all knowledge with sufficient usage
        async with self.tracker.db.session() as session:
            result = await session.execute(
                text("""
                SELECT knowledge_id, total_uses, successful_uses,
                       failed_uses, total_score
                FROM knowledge_stats
                WHERE total_uses >= :min_usage
                ORDER BY total_uses DESC
                """),
                {"min_usage": min_usage_count},
            )
            rows = result.fetchall()

        recommendations = []

        for row in rows:
            knowledge_id = row[0]
            total_uses = row[1]
            successful_uses = row[2]
            failed_uses = row[3]
            total_score = row[4]

            success_rate = successful_uses / total_uses
            average_score = total_score / total_uses

            # Estimate current score (assume 7.0 as baseline)
            current_score = 7.0

            # Calculate potential new score
            new_score = await self.calculate_new_quality_score(
                knowledge_id,
                current_score,
            )

            adjustment = new_score - current_score

            # Only recommend if adjustment is significant
            if abs(adjustment) >= min_adjustment_threshold:
                recommendations.append({
                    "knowledge_id": knowledge_id,
                    "current_score": current_score,
                    "recommended_score": new_score,
                    "adjustment": adjustment,
                    "success_rate": success_rate,
                    "average_score": average_score,
                    "usage_count": total_uses,
                    "priority": "high" if abs(adjustment) > 1.0 else "medium",
                })

        # Sort by absolute adjustment (highest priority first)
        recommendations.sort(key=lambda x: abs(x["adjustment"]), reverse=True)

        return recommendations

    async def get_quality_update_history(
        self,
        knowledge_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get quality update history

        Args:
            knowledge_id: Optional knowledge ID to filter
            limit: Maximum number of records

        Returns:
            List of quality updates
        """
        async with self.db.session() as session:
            if knowledge_id:
                result = await session.execute(
                    text("""
                    SELECT id, knowledge_id, old_score, new_score, adjustment,
                           success_rate, average_score, usage_count, reason, updated_at
                    FROM quality_updates
                    WHERE knowledge_id = :knowledge_id
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """),
                    {"knowledge_id": knowledge_id, "limit": limit},
                )
            else:
                result = await session.execute(
                    text("""
                    SELECT id, knowledge_id, old_score, new_score, adjustment,
                           success_rate, average_score, usage_count, reason, updated_at
                    FROM quality_updates
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """),
                    {"limit": limit},
                )

            rows = result.fetchall()

        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "knowledge_id": row[1],
                "old_score": row[2],
                "new_score": row[3],
                "adjustment": row[4],
                "success_rate": row[5],
                "average_score": row[6],
                "usage_count": row[7],
                "reason": row[8],
                "updated_at": row[9],
            })

        return history
