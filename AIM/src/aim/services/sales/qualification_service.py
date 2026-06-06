"""Sales qualification service — evaluates lead quality from conversations.

Analyzes chat messages for buying signals, matches against per-client
qualification criteria, and produces a qualification result with tier,
score, and recommended action.

The form-based LeadScoringService (lead_scoring/) handles static lead records.
This service handles the dynamic conversation context — intent signals,
budget indicators, urgency, and specialty fit.

Part of Phase 13: AI Sales Admin Agent — Sub-Phase 2.
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

from src.aim.magisters.sales_admin_base import ProjectSalesConfig

logger = logging.getLogger(__name__)


@dataclass
class QualificationResult:
    """Output of the qualification analysis."""

    score: int  # 0–100
    tier: str  # hot / warm / cold
    recommended_action: str  # create_lead, nurture, escalate, ignore
    signals: list[str]  # detected buying signals
    concerns: list[str]  # detected risk factors
    specialty_match: bool
    budget_indicated: bool
    urgency: str  # high / medium / low / none
    reasoning: str  # human-readable summary
    qualified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Signal detection ─────────────────────────────────────────────────────────

BUDGET_KEYWORDS: list[str] = [
    "стоимость", "цена", "сколько стоит", "бюджет", "недорого",
    "дешево", "акция", "скидка", "рассрочка", "прайс",
    "цены", "дорого", "премиум",
]

URGENCY_HIGH: list[str] = [
    "срочно", "сегодня", "завтра", "как можно быстрее", "горит",
    "экстренно", "немедленно", "прямо сейчас",
]

URGENCY_MEDIUM: list[str] = [
    "на этой неделе", "в ближайшее время", "планирую", "думаю",
    "на следующей неделе", "в течение месяца",
]

SERVICE_INQUIRY: list[str] = [
    "прием", "консультация", "запись", "записаться", "врач",
    "доктор", "клиника", "лечение", "операция", "процедура",
    "диагностика", "анализ", "осмотр",
]

HIGH_INTENT: list[str] = [
    "готов", "хочу записаться", "давайте", "согласен",
    "когда можно", "приму", "оформляйте",
]

CONCERN_KEYWORDS: list[str] = [
    "боюсь", "страшно", "больно", "осложнения", "реабилитация",
    "побочные", "риск", "гарантия", "результат",
    "отзывы", "рекомендации",
]


def _match_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _count_matches(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


class QualificationService:
    """Analyzes sales conversations for lead qualification.

    Unlike LeadScoringService (which scores static form submissions),
    this service evaluates the dynamic conversation — buying signals,
    budget indicators, urgency, specialty fit, and risk factors.
    """

    def __init__(self) -> None:
        pass

    async def qualify(
        self,
        messages: list[str],
        config: ProjectSalesConfig | None = None,
        specialty: str | None = None,
    ) -> QualificationResult:
        """Evaluate lead quality from conversation messages.

        Args:
            messages: List of message texts from the conversation (most recent last).
            config: Per-project sales configuration.
            specialty: Detected or declared medical specialty.

        Returns:
            QualificationResult with score, tier, signals, and recommendation.
        """
        all_text = " ".join(messages).lower()
        last_msg = messages[-1].lower() if messages else ""

        # 1. Detect signals
        signals: list[str] = []
        concerns: list[str] = []

        if _match_any(all_text, BUDGET_KEYWORDS):
            signals.append("budget_discussion")
        if _match_any(all_text, HIGH_INTENT):
            signals.append("high_intent")
        if _match_any(all_text, SERVICE_INQUIRY):
            signals.append("service_inquiry")
        if len(messages) >= 3:
            signals.append("sustained_conversation")

        if _match_any(all_text, CONCERN_KEYWORDS):
            concerns.append("patient_anxiety")
        if len(all_text) < 30:
            concerns.append("low_engagement")

        # 2. Urgency
        if _match_any(all_text, URGENCY_HIGH):
            urgency = "high"
        elif _match_any(all_text, URGENCY_MEDIUM):
            urgency = "medium"
        else:
            urgency = "low"

        # 3. Budget
        budget_indicated = bool(signals and "budget_discussion" in signals)

        # 4. Specialty match
        specialty_match = False
        if config and config.high_value_specialties and specialty:
            specialty_match = specialty in config.high_value_specialties

        # 5. Score calculation
        score = self._calculate_score(
            signals=signals,
            concerns=concerns,
            urgency=urgency,
            specialty_match=specialty_match,
            message_count=len(messages),
        )

        # 6. Tier assignment
        tier = self._assign_tier(score)

        # 7. Recommended action
        action = self._recommend_action(
            tier=tier,
            urgency=urgency,
            signals=signals,
            concerns=concerns,
        )

        # 8. Reasoning
        reasoning = self._build_reasoning(
            score=score,
            tier=tier,
            signals=signals,
            concerns=concerns,
            urgency=urgency,
            specialty_match=specialty_match,
            budget_indicated=budget_indicated,
        )

        return QualificationResult(
            score=score,
            tier=tier,
            recommended_action=action,
            signals=signals,
            concerns=concerns,
            specialty_match=specialty_match,
            budget_indicated=budget_indicated,
            urgency=urgency,
            reasoning=reasoning,
        )

    # ── Scoring ──────────────────────────────────────────────────────────

    def _calculate_score(
        self,
        signals: list[str],
        concerns: list[str],
        urgency: str,
        specialty_match: bool,
        message_count: int,
    ) -> int:
        """Calculate qualification score (0–100) from detected signals."""
        score = 20  # base — any conversation starts with some potential

        # Signal bonuses
        signal_bonuses = {
            "budget_discussion": 20,
            "high_intent": 25,
            "service_inquiry": 15,
            "sustained_conversation": 10,
        }
        for signal in signals:
            score += signal_bonuses.get(signal, 0)

        # Urgency boost
        urgency_boost = {"high": 20, "medium": 10, "low": 0, "none": 0}
        score += urgency_boost.get(urgency, 0)

        # Specialty match
        if specialty_match:
            score += 15

        # Concern penalties
        concern_penalties = {
            "patient_anxiety": -5,
            "low_engagement": -10,
        }
        for concern in concerns:
            score += concern_penalties.get(concern, 0)

        # Conversational depth
        if message_count >= 5:
            score += 5

        return max(0, min(100, score))

    def _assign_tier(self, score: int) -> str:
        if score >= 70:
            return "hot"
        elif score >= 40:
            return "warm"
        return "cold"

    def _recommend_action(
        self,
        tier: str,
        urgency: str,
        signals: list[str],
        concerns: list[str],
    ) -> str:
        """Decide what to do with this conversation."""
        # High urgency always gets priority treatment
        if urgency == "high" and tier in ("hot", "warm"):
            return "create_lead"

        if tier == "hot":
            return "create_lead"

        if tier == "warm":
            if "budget_discussion" in signals or "service_inquiry" in signals:
                return "create_lead"
            return "nurture"

        if tier == "cold":
            if "sustained_conversation" in signals:
                return "nurture"
            if "low_engagement" in concerns and len(signals) == 0:
                return "ignore"
            return "nurture"

        return "nurture"

    def _build_reasoning(
        self,
        score: int,
        tier: str,
        signals: list[str],
        concerns: list[str],
        urgency: str,
        specialty_match: bool,
        budget_indicated: bool,
    ) -> str:
        parts: list[str] = []

        if signals:
            parts.append(f"Сигналы: {', '.join(signals)}")
        if concerns:
            parts.append(f"Риски: {', '.join(concerns)}")
        if urgency != "low":
            parts.append(f"Срочность: {urgency}")
        if specialty_match:
            parts.append("Специальность совпадает с высокоценными")
        if budget_indicated:
            parts.append("Бюджет обсуждается")

        if not parts:
            return "Недостаточно данных для квалификации"

        return f"Счёт {score} ({tier}). " + ". ".join(parts) + "."
