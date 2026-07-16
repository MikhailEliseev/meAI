"""Deprecate outdated or low-performing knowledge"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.learning.experience_tracker import ExperienceTracker
from meai.storage.database import Database


class DeprecationManager:
    """Manage knowledge deprecation based on performance

    Deprecation criteria:
    1. Low quality score (< threshold after sufficient usage)
    2. Low success rate (< threshold with sufficient data)
    3. Consistently poor outcomes
    4. Manual deprecation by admin

    Deprecated knowledge:
    - Marked as deprecated in database
    - Excluded from search results (optional)
    - Can be undeprecated if quality improves
    """

    def __init__(
        self,
        experience_tracker: ExperienceTracker,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        quality_threshold: float = 3.0,
        success_rate_threshold: float = 0.3,
        min_usage_for_deprecation: int = 20,
    ):
        """Initialize Deprecation Manager

        Args:
            experience_tracker: Experience tracker instance
            database_url: Database URL
            quality_threshold: Quality score below which to deprecate
            success_rate_threshold: Success rate below which to deprecate
            min_usage_for_deprecation: Minimum usage before considering deprecation
        """
        self.tracker = experience_tracker
        self.db = Database(database_url)
        self.quality_threshold = quality_threshold
        self.success_rate_threshold = success_rate_threshold
        self.min_usage_for_deprecation = min_usage_for_deprecation

    async def initialize(self) -> None:
        """Initialize manager"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown manager"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create deprecation tracking tables"""
        async with self.db.session() as session:
            # Deprecations table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS deprecations (
                    id TEXT PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    quality_at_deprecation REAL,
                    success_rate_at_deprecation REAL,
                    usage_count_at_deprecation INTEGER,
                    deprecated_at TIMESTAMP NOT NULL,
                    deprecated_by TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    undeprecated_at TIMESTAMP,
                    undeprecation_reason TEXT
                )
                """)
            )

            await session.commit()

    async def should_deprecate(
        self,
        knowledge_id: str,
        current_quality: float,
    ) -> tuple[bool, str]:
        """Check if knowledge should be deprecated

        Args:
            knowledge_id: Knowledge ID
            current_quality: Current quality score

        Returns:
            Tuple of (should_deprecate, reason)
        """
        # Get experience stats
        stats = await self.tracker.get_knowledge_stats(knowledge_id)

        # Not enough data yet
        if stats["total_uses"] < self.min_usage_for_deprecation:
            return False, "Insufficient usage data"

        # Check quality threshold
        if current_quality < self.quality_threshold:
            return True, f"Low quality score: {current_quality:.1f} < {self.quality_threshold}"

        # Check success rate threshold
        if stats["success_rate"] < self.success_rate_threshold:
            return True, f"Low success rate: {stats['success_rate']:.1%} < {self.success_rate_threshold:.1%}"

        # Check average score
        if stats["average_score"] < 0.4:
            return True, f"Consistently poor outcomes: avg score {stats['average_score']:.2f}"

        return False, "Performance acceptable"

    async def deprecate_knowledge(
        self,
        knowledge_id: str,
        reason: str,
        current_quality: float | None = None,
        deprecated_by: str = "system",
    ) -> dict[str, Any]:
        """Deprecate knowledge

        Args:
            knowledge_id: Knowledge ID
            reason: Deprecation reason
            current_quality: Current quality score
            deprecated_by: Who deprecated it (system/admin/user)

        Returns:
            Deprecation result
        """
        # Get current stats
        stats = await self.tracker.get_knowledge_stats(knowledge_id)

        # Create deprecation record
        deprecation_id = f"deprecation-{uuid4().hex[:8]}"
        deprecated_at = datetime.now(timezone.utc)

        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO deprecations
                (id, knowledge_id, reason, quality_at_deprecation,
                 success_rate_at_deprecation, usage_count_at_deprecation,
                 deprecated_at, deprecated_by, active)
                VALUES (:id, :knowledge_id, :reason, :quality,
                        :success_rate, :usage_count, :deprecated_at,
                        :deprecated_by, TRUE)
                """),
                {
                    "id": deprecation_id,
                    "knowledge_id": knowledge_id,
                    "reason": reason,
                    "quality": current_quality,
                    "success_rate": stats["success_rate"],
                    "usage_count": stats["total_uses"],
                    "deprecated_at": deprecated_at,
                    "deprecated_by": deprecated_by,
                },
            )
            await session.commit()

        # TODO: Update Teacher's Qdrant metadata to mark as deprecated

        return {
            "deprecated": True,
            "deprecation_id": deprecation_id,
            "knowledge_id": knowledge_id,
            "reason": reason,
            "deprecated_at": deprecated_at,
            "stats": stats,
        }

    async def undeprecate_knowledge(
        self,
        knowledge_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Undeprecate knowledge (restore it)

        Args:
            knowledge_id: Knowledge ID
            reason: Undeprecation reason

        Returns:
            Undeprecation result
        """
        undeprecated_at = datetime.now(timezone.utc)

        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE deprecations
                SET active = FALSE,
                    undeprecated_at = :undeprecated_at,
                    undeprecation_reason = :reason
                WHERE knowledge_id = :knowledge_id
                  AND active = TRUE
                """),
                {
                    "knowledge_id": knowledge_id,
                    "undeprecated_at": undeprecated_at,
                    "reason": reason,
                },
            )
            await session.commit()

        # TODO: Update Teacher's Qdrant metadata to unmark as deprecated

        return {
            "undeprecated": True,
            "knowledge_id": knowledge_id,
            "reason": reason,
            "undeprecated_at": undeprecated_at,
        }

    async def scan_for_deprecation_candidates(
        self,
        min_usage_count: int | None = None,
    ) -> list[dict[str, Any]]:
        """Scan for knowledge that should be deprecated

        Args:
            min_usage_count: Minimum usage count (overrides default)

        Returns:
            List of deprecation candidates
        """
        min_usage = min_usage_count or self.min_usage_for_deprecation

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
                {"min_usage": min_usage},
            )
            rows = result.fetchall()

        candidates = []

        for row in rows:
            knowledge_id = row[0]
            total_uses = row[1]
            successful_uses = row[2]
            failed_uses = row[3]
            total_score = row[4]

            success_rate = successful_uses / total_uses
            average_score = total_score / total_uses

            # Estimate quality (assume 7.0 baseline, adjust by performance)
            estimated_quality = 7.0 * (success_rate + average_score) / 2

            # Check if should deprecate
            should_deprecate, reason = await self.should_deprecate(
                knowledge_id,
                estimated_quality,
            )

            if should_deprecate:
                candidates.append({
                    "knowledge_id": knowledge_id,
                    "estimated_quality": estimated_quality,
                    "success_rate": success_rate,
                    "average_score": average_score,
                    "usage_count": total_uses,
                    "reason": reason,
                    "should_deprecate": True,
                    "priority": "high" if estimated_quality < 2.0 else "medium",
                })

        # Sort by priority (lowest quality first)
        candidates.sort(key=lambda x: x["estimated_quality"])

        return candidates

    async def auto_deprecate_low_performers(
        self,
        min_usage_count: int | None = None,
        dry_run: bool = True,
    ) -> list[dict[str, Any]]:
        """Automatically deprecate low-performing knowledge

        Args:
            min_usage_count: Minimum usage count
            dry_run: If True, only return candidates without deprecating

        Returns:
            List of deprecation results
        """
        candidates = await self.scan_for_deprecation_candidates(min_usage_count)

        results = []

        for candidate in candidates:
            if dry_run:
                results.append({
                    "knowledge_id": candidate["knowledge_id"],
                    "would_deprecate": True,
                    "reason": candidate["reason"],
                    "estimated_quality": candidate["estimated_quality"],
                })
            else:
                result = await self.deprecate_knowledge(
                    knowledge_id=candidate["knowledge_id"],
                    reason=candidate["reason"],
                    current_quality=candidate["estimated_quality"],
                    deprecated_by="auto_system",
                )
                results.append(result)

        return results

    async def get_deprecated_knowledge(
        self,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Get deprecated knowledge

        Args:
            active_only: Only return currently deprecated (not undeprecated)

        Returns:
            List of deprecated knowledge
        """
        async with self.db.session() as session:
            if active_only:
                result = await session.execute(
                    text("""
                    SELECT id, knowledge_id, reason, quality_at_deprecation,
                           success_rate_at_deprecation, usage_count_at_deprecation,
                           deprecated_at, deprecated_by, active
                    FROM deprecations
                    WHERE active = TRUE
                    ORDER BY deprecated_at DESC
                    """)
                )
            else:
                result = await session.execute(
                    text("""
                    SELECT id, knowledge_id, reason, quality_at_deprecation,
                           success_rate_at_deprecation, usage_count_at_deprecation,
                           deprecated_at, deprecated_by, active,
                           undeprecated_at, undeprecation_reason
                    FROM deprecations
                    ORDER BY deprecated_at DESC
                    """)
                )

            rows = result.fetchall()

        deprecated = []
        for row in rows:
            item = {
                "id": row[0],
                "knowledge_id": row[1],
                "reason": row[2],
                "quality_at_deprecation": row[3],
                "success_rate_at_deprecation": row[4],
                "usage_count_at_deprecation": row[5],
                "deprecated_at": row[6],
                "deprecated_by": row[7],
                "active": row[8],
            }

            if not active_only and len(row) > 9:
                item["undeprecated_at"] = row[9]
                item["undeprecation_reason"] = row[10]

            deprecated.append(item)

        return deprecated

    async def get_deprecation_stats(self) -> dict[str, Any]:
        """Get deprecation statistics

        Returns:
            Stats dictionary
        """
        async with self.db.session() as session:
            # Total deprecated
            result = await session.execute(
                text("SELECT COUNT(*) FROM deprecations")
            )
            total_deprecated = result.scalar()

            # Active deprecated
            result = await session.execute(
                text("SELECT COUNT(*) FROM deprecations WHERE active = TRUE")
            )
            active_deprecated = result.scalar()

            # Undeprecated
            result = await session.execute(
                text("SELECT COUNT(*) FROM deprecations WHERE active = FALSE")
            )
            undeprecated = result.scalar()

        return {
            "total_deprecated": total_deprecated,
            "active_deprecated": active_deprecated,
            "undeprecated": undeprecated,
            "deprecation_rate": active_deprecated / total_deprecated if total_deprecated > 0 else 0.0,
        }
