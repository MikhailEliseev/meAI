"""Architect - autonomous decision making"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import select
import structlog

from ..storage.database import Database
from ..storage.models import Base
from sqlalchemy import String, Float, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

logger = structlog.get_logger()


@dataclass
class DecisionContext:
    """Context for decision making"""

    goal: str
    constraints: list[str]
    available_resources: dict[str, Any]


@dataclass
class Decision:
    """Decision result"""

    action: str
    rationale: str
    confidence: float
    alternatives: list[str]
    timestamp: datetime


class DecisionRecord(Base):
    """Decision history record"""

    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    rationale: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    context: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)


class Architect:
    """Autonomous decision maker"""

    def __init__(self, db: Database):
        """Initialize Architect

        Args:
            db: Database instance
        """
        self.db = db

    async def make_decision(self, context: DecisionContext) -> Decision:
        """Make autonomous decision

        Args:
            context: Decision context

        Returns:
            Decision with action and rationale
        """
        logger.info("architect.decision_start", goal=context.goal)

        # Analyze context
        analysis = await self.analyze_context(context)

        # Generate options
        options = self._generate_options(context, analysis)

        # Evaluate and select best option
        best_option = await self.evaluate_options(options, context)

        # Calculate confidence
        confidence = self._calculate_confidence(best_option, analysis)

        # Create decision
        decision = Decision(
            action=best_option.get("action", "proceed"),
            rationale=best_option.get("rationale", "Best option based on analysis"),
            confidence=confidence,
            alternatives=[opt.get("action", "") for opt in options if opt != best_option],
            timestamp=datetime.now(timezone.utc),
        )

        # Store decision
        await self._store_decision(context, decision)

        logger.info(
            "architect.decision_made",
            action=decision.action,
            confidence=decision.confidence,
        )

        return decision

    async def analyze_context(self, context: DecisionContext) -> dict[str, Any]:
        """Analyze decision context

        Args:
            context: Decision context

        Returns:
            Analysis results
        """
        # Check feasibility
        feasibility = self._check_feasibility(context)

        # Identify risks
        risks = self._identify_risks(context)

        # Generate recommendations
        recommendations = self._generate_recommendations(context, feasibility, risks)

        return {
            "feasibility": feasibility,
            "risks": risks,
            "recommendations": recommendations,
        }

    async def evaluate_options(
        self,
        options: list[dict[str, Any]],
        context: DecisionContext,
    ) -> dict[str, Any]:
        """Evaluate and select best option

        Args:
            options: List of options to evaluate
            context: Decision context

        Returns:
            Best option
        """
        if not options:
            return {"action": "no_action", "rationale": "No viable options"}

        # Score each option
        scored_options = []
        for option in options:
            score = self._score_option(option, context)
            scored_options.append((score, option))

        # Sort by score (highest first)
        scored_options.sort(reverse=True, key=lambda x: x[0])

        return scored_options[0][1]

    async def get_decision_history(self, limit: int = 10) -> list[Decision]:
        """Get decision history

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of past decisions
        """
        async with self.db.session() as session:
            query = (
                select(DecisionRecord)
                .order_by(DecisionRecord.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            records = list(result.scalars().all())

        decisions = []
        for record in records:
            decisions.append(
                Decision(
                    action=record.action,
                    rationale=record.rationale,
                    confidence=record.confidence,
                    alternatives=[],
                    timestamp=record.timestamp,
                )
            )

        return decisions

    def _generate_options(
        self,
        context: DecisionContext,
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate possible options"""
        options = []

        # Option 1: Direct approach
        options.append(
            {
                "action": f"execute_{context.goal.lower().replace(' ', '_')}",
                "rationale": "Direct execution of goal",
                "cost": 50,
                "quality": 8,
            }
        )

        # Option 2: Cautious approach
        if analysis["risks"]:
            options.append(
                {
                    "action": f"cautious_{context.goal.lower().replace(' ', '_')}",
                    "rationale": "Mitigate risks first",
                    "cost": 75,
                    "quality": 9,
                }
            )

        # Option 3: Minimal approach
        options.append(
            {
                "action": f"minimal_{context.goal.lower().replace(' ', '_')}",
                "rationale": "Minimal viable approach",
                "cost": 25,
                "quality": 6,
            }
        )

        return options

    def _check_feasibility(self, context: DecisionContext) -> str:
        """Check if goal is feasible"""
        if not context.available_resources:
            return "low"

        if context.constraints and len(context.constraints) > 5:
            return "medium"

        return "high"

    def _identify_risks(self, context: DecisionContext) -> list[str]:
        """Identify potential risks"""
        risks = []

        if "budget" in str(context.constraints).lower():
            risks.append("budget_constraint")

        if not context.available_resources:
            risks.append("resource_shortage")

        return risks

    def _generate_recommendations(
        self,
        context: DecisionContext,
        feasibility: str,
        risks: list[str],
    ) -> list[str]:
        """Generate recommendations"""
        recommendations = []

        if feasibility == "low":
            recommendations.append("Gather more resources before proceeding")

        if risks:
            recommendations.append(f"Mitigate {len(risks)} identified risks")

        if not recommendations:
            recommendations.append("Proceed with execution")

        return recommendations

    def _score_option(self, option: dict[str, Any], context: DecisionContext) -> float:
        """Score an option"""
        score = 0.0

        # Quality score
        quality = option.get("quality", 5)
        score += quality * 10

        # Cost efficiency
        cost = option.get("cost", 50)
        if cost < 50:
            score += 20
        elif cost > 100:
            score -= 20

        # Check constraints
        for constraint in context.constraints:
            if "budget" in constraint.lower():
                budget_limit = int("".join(filter(str.isdigit, constraint)))
                if cost <= budget_limit:
                    score += 30

        return score

    def _calculate_confidence(
        self,
        option: dict[str, Any],
        analysis: dict[str, Any],
    ) -> float:
        """Calculate decision confidence"""
        confidence = 0.5  # Base confidence

        # Increase for high feasibility
        if analysis["feasibility"] == "high":
            confidence += 0.3
        elif analysis["feasibility"] == "medium":
            confidence += 0.1

        # Decrease for risks
        confidence -= len(analysis["risks"]) * 0.1

        # Increase for high quality option
        if option.get("quality", 0) >= 8:
            confidence += 0.2

        return max(0.0, min(1.0, confidence))

    async def _store_decision(
        self,
        context: DecisionContext,
        decision: Decision,
    ) -> None:
        """Store decision in database"""
        async with self.db.session() as session:
            record = DecisionRecord(
                goal=context.goal,
                action=decision.action,
                rationale=decision.rationale,
                confidence=decision.confidence,
                context={
                    "constraints": context.constraints,
                    "resources": context.available_resources,
                },
                timestamp=decision.timestamp,
            )
            session.add(record)
