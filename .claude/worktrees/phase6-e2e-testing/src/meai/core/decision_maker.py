"""Decision Maker - strategy selection and learning"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import select, func
import structlog

from ..storage.database import Database
from ..storage.models import Base
from sqlalchemy import String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

logger = structlog.get_logger()


@dataclass
class Strategy:
    """Strategy definition"""

    name: str
    description: str
    expected_cost: float
    expected_quality: float
    risk_level: str  # low, medium, high


@dataclass
class StrategyOutcome:
    """Strategy execution outcome"""

    strategy_name: str
    actual_cost: float
    actual_quality: float
    success: bool
    notes: str


class StrategyRecord(Base):
    """Strategy outcome record"""

    __tablename__ = "strategy_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_name: Mapped[str] = mapped_column(String, index=True)
    expected_cost: Mapped[float] = mapped_column(Float)
    expected_quality: Mapped[float] = mapped_column(Float)
    actual_cost: Mapped[float] = mapped_column(Float)
    actual_quality: Mapped[float] = mapped_column(Float)
    success: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)


class DecisionMaker:
    """Strategy selection and learning"""

    def __init__(self, db: Database):
        """Initialize Decision Maker

        Args:
            db: Database instance
        """
        self.db = db

    async def select_strategy(
        self,
        strategies: list[Strategy],
        criteria: dict[str, Any],
    ) -> Optional[Strategy]:
        """Select optimal strategy

        Args:
            strategies: Available strategies
            criteria: Selection criteria

        Returns:
            Selected strategy or None
        """
        if not strategies:
            return None

        logger.info("decision_maker.selecting", count=len(strategies))

        # Score each strategy
        scored = []
        for strategy in strategies:
            score = self.score_strategy(strategy, criteria)
            scored.append((score, strategy))

        # Sort by score (highest first)
        scored.sort(reverse=True, key=lambda x: x[0])

        selected = scored[0][1]

        logger.info(
            "decision_maker.selected",
            strategy=selected.name,
            score=scored[0][0],
        )

        return selected

    def score_strategy(
        self,
        strategy: Strategy,
        criteria: dict[str, Any],
    ) -> float:
        """Score a strategy

        Args:
            strategy: Strategy to score
            criteria: Scoring criteria

        Returns:
            Strategy score
        """
        score = 0.0

        # Quality score
        score += strategy.expected_quality * 10

        # Cost efficiency
        max_cost = criteria.get("max_cost", 100)
        if strategy.expected_cost <= max_cost:
            score += 20
            # Bonus for being under budget
            savings = max_cost - strategy.expected_cost
            score += (savings / max_cost) * 10

        # Quality requirement
        min_quality = criteria.get("min_quality", 0)
        if strategy.expected_quality >= min_quality:
            score += 15

        # Risk penalty
        risk_penalties = {"low": 0, "medium": -5, "high": -15}
        score += risk_penalties.get(strategy.risk_level, 0)

        return max(0.0, score)

    async def track_outcome(
        self,
        strategy: Strategy,
        outcome: StrategyOutcome,
    ) -> None:
        """Track strategy outcome

        Args:
            strategy: Strategy that was executed
            outcome: Execution outcome
        """
        async with self.db.session() as session:
            record = StrategyRecord(
                strategy_name=strategy.name,
                expected_cost=strategy.expected_cost,
                expected_quality=strategy.expected_quality,
                actual_cost=outcome.actual_cost,
                actual_quality=outcome.actual_quality,
                success=outcome.success,
                notes=outcome.notes,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(record)

        logger.info(
            "decision_maker.outcome_tracked",
            strategy=strategy.name,
            success=outcome.success,
        )

    async def get_strategy_history(
        self,
        strategy_name: str,
    ) -> list[StrategyRecord]:
        """Get strategy execution history

        Args:
            strategy_name: Strategy name

        Returns:
            List of outcome records
        """
        async with self.db.session() as session:
            query = (
                select(StrategyRecord)
                .where(StrategyRecord.strategy_name == strategy_name)
                .order_by(StrategyRecord.timestamp.desc())
            )
            result = await session.execute(query)
            records = list(result.scalars().all())

        return records

    async def get_strategy_insights(
        self,
        strategy_name: str,
    ) -> dict[str, Any]:
        """Get insights from strategy history

        Args:
            strategy_name: Strategy name

        Returns:
            Insights dictionary
        """
        async with self.db.session() as session:
            query = select(
                func.count(StrategyRecord.id).label("total"),
                func.sum(
                    func.cast(StrategyRecord.success, Float)
                ).label("successes"),
                func.avg(StrategyRecord.actual_cost).label("avg_cost"),
                func.avg(StrategyRecord.actual_quality).label("avg_quality"),
            ).where(StrategyRecord.strategy_name == strategy_name)

            result = await session.execute(query)
            row = result.one()

        total = row.total or 0
        successes = row.successes or 0
        success_rate = (successes / total) if total > 0 else 0.0

        return {
            "strategy_name": strategy_name,
            "total_executions": total,
            "success_rate": success_rate,
            "avg_cost": float(row.avg_cost) if row.avg_cost else 0.0,
            "avg_quality": float(row.avg_quality) if row.avg_quality else 0.0,
        }

    async def compare_strategies(
        self,
        strategies: list[Strategy],
    ) -> list[dict[str, Any]]:
        """Compare strategies with historical data

        Args:
            strategies: Strategies to compare

        Returns:
            Comparison results
        """
        comparisons = []

        for strategy in strategies:
            insights = await self.get_strategy_insights(strategy.name)

            # Calculate adjusted score based on history
            base_score = self.score_strategy(strategy, {})

            # Adjust for historical performance
            if insights["total_executions"] > 0:
                success_bonus = insights["success_rate"] * 20
                base_score += success_bonus

            comparisons.append(
                {
                    "strategy": strategy.name,
                    "score": base_score,
                    "expected_cost": strategy.expected_cost,
                    "expected_quality": strategy.expected_quality,
                    "risk_level": strategy.risk_level,
                    "historical_success_rate": insights["success_rate"],
                    "historical_executions": insights["total_executions"],
                }
            )

        # Sort by score
        comparisons.sort(reverse=True, key=lambda x: x["score"])

        return comparisons
