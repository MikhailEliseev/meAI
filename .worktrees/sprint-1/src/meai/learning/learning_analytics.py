"""Learning analytics and metrics"""

from datetime import datetime, timezone, timedelta
from typing import Any

from meai.learning.experience_tracker import ExperienceTracker
from meai.learning.quality_updater import QualityUpdater
from meai.learning.deprecation_manager import DeprecationManager


class LearningAnalytics:
    """Analytics for experience-based learning system

    Provides insights into:
    - Learning progress over time
    - Knowledge quality trends
    - Deprecation patterns
    - Magister performance
    - System health metrics
    """

    def __init__(
        self,
        experience_tracker: ExperienceTracker,
        quality_updater: QualityUpdater,
        deprecation_manager: DeprecationManager,
    ):
        """Initialize Learning Analytics

        Args:
            experience_tracker: Experience tracker instance
            quality_updater: Quality updater instance
            deprecation_manager: Deprecation manager instance
        """
        self.tracker = experience_tracker
        self.updater = quality_updater
        self.deprecation = deprecation_manager

    async def get_system_health(self) -> dict[str, Any]:
        """Get overall system health metrics

        Returns:
            Health metrics dictionary
        """
        # Get deprecation stats
        deprecation_stats = await self.deprecation.get_deprecation_stats()

        # Get recent experiences
        recent_experiences = await self.tracker.get_recent_experiences(limit=100)

        # Calculate success rate
        if recent_experiences:
            successful = sum(1 for exp in recent_experiences if exp["outcome"] == "success")
            success_rate = successful / len(recent_experiences)
        else:
            success_rate = 0.0

        # Calculate average outcome score
        if recent_experiences:
            scores = [exp["outcome_score"] for exp in recent_experiences if exp["outcome_score"] is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.0
        else:
            avg_score = 0.0

        return {
            "overall_success_rate": success_rate,
            "average_outcome_score": avg_score,
            "total_experiences": len(recent_experiences),
            "active_deprecated": deprecation_stats["active_deprecated"],
            "deprecation_rate": deprecation_stats["deprecation_rate"],
            "health_score": self._calculate_health_score(
                success_rate,
                avg_score,
                deprecation_stats["deprecation_rate"],
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_health_score(
        self,
        success_rate: float,
        avg_score: float,
        deprecation_rate: float,
    ) -> float:
        """Calculate overall health score (0.0 - 10.0)

        Args:
            success_rate: Overall success rate
            avg_score: Average outcome score
            deprecation_rate: Rate of deprecated knowledge

        Returns:
            Health score
        """
        # Success rate: 0.0 - 1.0 → 0 - 4 points
        success_points = success_rate * 4.0

        # Average score: 0.0 - 1.0 → 0 - 4 points
        score_points = avg_score * 4.0

        # Deprecation rate: lower is better
        # 0.0 - 0.2 → 2 points, 0.2 - 0.5 → 1 point, > 0.5 → 0 points
        if deprecation_rate < 0.2:
            deprecation_points = 2.0
        elif deprecation_rate < 0.5:
            deprecation_points = 1.0
        else:
            deprecation_points = 0.0

        health_score = success_points + score_points + deprecation_points

        return round(health_score, 1)

    async def get_knowledge_performance_report(
        self,
        knowledge_id: str,
    ) -> dict[str, Any]:
        """Get detailed performance report for knowledge

        Args:
            knowledge_id: Knowledge ID

        Returns:
            Performance report
        """
        # Get stats
        stats = await self.tracker.get_knowledge_stats(knowledge_id)

        # Get quality update history
        quality_history = await self.updater.get_quality_update_history(
            knowledge_id=knowledge_id,
            limit=10,
        )

        # Check if deprecated
        deprecated_list = await self.deprecation.get_deprecated_knowledge(active_only=False)
        deprecation_info = next(
            (d for d in deprecated_list if d["knowledge_id"] == knowledge_id),
            None,
        )

        return {
            "knowledge_id": knowledge_id,
            "usage_stats": stats,
            "quality_history": quality_history,
            "deprecation_info": deprecation_info,
            "performance_grade": self._calculate_performance_grade(stats),
            "recommendations": self._generate_recommendations(stats, deprecation_info),
        }

    def _calculate_performance_grade(self, stats: dict[str, Any]) -> str:
        """Calculate performance grade (A-F)

        Args:
            stats: Knowledge stats

        Returns:
            Grade letter
        """
        if stats["total_uses"] < 5:
            return "N/A"

        success_rate = stats["success_rate"]
        avg_score = stats["average_score"]

        # Combined score
        combined = (success_rate + avg_score) / 2

        if combined >= 0.9:
            return "A"
        elif combined >= 0.8:
            return "B"
        elif combined >= 0.7:
            return "C"
        elif combined >= 0.6:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
        self,
        stats: dict[str, Any],
        deprecation_info: dict[str, Any] | None,
    ) -> list[str]:
        """Generate recommendations based on performance

        Args:
            stats: Knowledge stats
            deprecation_info: Deprecation info if deprecated

        Returns:
            List of recommendations
        """
        recommendations = []

        if stats["total_uses"] < 10:
            recommendations.append("Needs more usage data for reliable assessment")

        if stats["success_rate"] < 0.5:
            recommendations.append("Low success rate - consider updating or deprecating")

        if stats["average_score"] < 0.5:
            recommendations.append("Poor outcome scores - review knowledge quality")

        if deprecation_info and deprecation_info["active"]:
            recommendations.append("Currently deprecated - consider removal or update")

        if stats["success_rate"] > 0.8 and stats["average_score"] > 0.8:
            recommendations.append("High performance - good candidate for promotion")

        if not recommendations:
            recommendations.append("Performance is acceptable")

        return recommendations

    async def get_magister_performance_report(
        self,
        magister_id: str,
    ) -> dict[str, Any]:
        """Get performance report for a Magister

        Args:
            magister_id: Magister ID

        Returns:
            Performance report
        """
        # Get Magister experiences
        experiences = await self.tracker.get_magister_experiences(
            magister_id=magister_id,
            limit=100,
        )

        if not experiences:
            return {
                "magister_id": magister_id,
                "total_tasks": 0,
                "success_rate": 0.0,
                "average_score": 0.0,
                "performance_grade": "N/A",
            }

        # Calculate metrics
        successful = sum(1 for exp in experiences if exp["outcome"] == "success")
        success_rate = successful / len(experiences)

        scores = [exp["outcome_score"] for exp in experiences if exp["outcome_score"] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Performance grade
        combined = (success_rate + avg_score) / 2
        if combined >= 0.9:
            grade = "A"
        elif combined >= 0.8:
            grade = "B"
        elif combined >= 0.7:
            grade = "C"
        elif combined >= 0.6:
            grade = "D"
        else:
            grade = "F"

        return {
            "magister_id": magister_id,
            "total_tasks": len(experiences),
            "successful_tasks": successful,
            "failed_tasks": len(experiences) - successful,
            "success_rate": success_rate,
            "average_score": avg_score,
            "performance_grade": grade,
            "recent_experiences": experiences[:10],
        }

    async def get_learning_trends(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get learning trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Trends data
        """
        # Get recent experiences
        all_experiences = await self.tracker.get_recent_experiences(limit=1000)

        # Filter by date range
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_experiences = [
            exp for exp in all_experiences
            if exp["created_at"] >= cutoff_date
        ]

        if not recent_experiences:
            return {
                "days": days,
                "total_experiences": 0,
                "trend": "insufficient_data",
            }

        # Group by day
        daily_stats = {}
        for exp in recent_experiences:
            date_key = exp["created_at"].date().isoformat()

            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "total": 0,
                    "successful": 0,
                    "scores": [],
                }

            daily_stats[date_key]["total"] += 1
            if exp["outcome"] == "success":
                daily_stats[date_key]["successful"] += 1
            if exp["outcome_score"] is not None:
                daily_stats[date_key]["scores"].append(exp["outcome_score"])

        # Calculate daily metrics
        daily_metrics = []
        for date_key, stats in sorted(daily_stats.items()):
            success_rate = stats["successful"] / stats["total"] if stats["total"] > 0 else 0.0
            avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0.0

            daily_metrics.append({
                "date": date_key,
                "total_tasks": stats["total"],
                "success_rate": success_rate,
                "average_score": avg_score,
            })

        # Determine trend
        if len(daily_metrics) >= 2:
            first_half = daily_metrics[:len(daily_metrics)//2]
            second_half = daily_metrics[len(daily_metrics)//2:]

            first_avg = sum(d["success_rate"] for d in first_half) / len(first_half)
            second_avg = sum(d["success_rate"] for d in second_half) / len(second_half)

            if second_avg > first_avg + 0.1:
                trend = "improving"
            elif second_avg < first_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "days": days,
            "total_experiences": len(recent_experiences),
            "daily_metrics": daily_metrics,
            "trend": trend,
            "overall_success_rate": sum(d["success_rate"] for d in daily_metrics) / len(daily_metrics) if daily_metrics else 0.0,
        }

    async def get_top_performing_knowledge(
        self,
        limit: int = 10,
        min_usage: int = 10,
    ) -> list[dict[str, Any]]:
        """Get top performing knowledge items

        Args:
            limit: Maximum number of items
            min_usage: Minimum usage count

        Returns:
            List of top performers
        """
        # Get all knowledge stats
        from sqlalchemy import text

        async with self.tracker.db.session() as session:
            result = await session.execute(
                text("""
                SELECT knowledge_id, total_uses, successful_uses, total_score
                FROM knowledge_stats
                WHERE total_uses >= :min_usage
                ORDER BY (CAST(successful_uses AS REAL) / total_uses) DESC,
                         (total_score / total_uses) DESC
                LIMIT :limit
                """),
                {"min_usage": min_usage, "limit": limit},
            )
            rows = result.fetchall()

        top_performers = []
        for row in rows:
            knowledge_id = row[0]
            total_uses = row[1]
            successful_uses = row[2]
            total_score = row[3]

            success_rate = successful_uses / total_uses
            avg_score = total_score / total_uses

            top_performers.append({
                "knowledge_id": knowledge_id,
                "usage_count": total_uses,
                "success_rate": success_rate,
                "average_score": avg_score,
                "performance_score": (success_rate + avg_score) / 2,
            })

        return top_performers
