"""Escalation service — detects when a conversation must be handed to a human.

Five escalation categories:
1. medical_data_request — ФЗ-152: patient asks for their medical history (IMMEDIATE)
2. complex_question — agent cannot answer confidently (URGENT)
3. inappropriate_behavior — profanity, threats, spam (ROUTINE)
4. human_request — explicit "call a human" (URGENT)
5. technical_failure — agent errors, timeouts (ROUTINE)

Each category has configurable severity, auto-escalate flag, and response template.

Part of Phase 13: AI Sales Admin Agent — Sub-Phase 2.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from aim.magisters.sales_admin_base import (
    DEFAULT_ESCALATION_RULES,
    EscalationReason,
    EscalationSeverity,
    ProjectSalesConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class EscalationCheck:
    """Result of an escalation check."""

    should_escalate: bool
    reason: str  # EscalationReason value
    severity: str  # EscalationSeverity value
    auto_escalate: bool
    response_template: str | None
    matched_trigger: str
    context: dict[str, Any] = field(default_factory=dict)


# ── Category 1: ФЗ-152 Medical Data Request ─────────────────────────────────

MEDICAL_DATA_PATTERNS: list[str] = [
    # Existing patient signals (from DEFAULT_ESCALATION_RULES)
    r"я\s+(у\s+вас\s+)?(был|лечился|наблюдался)",
    r"посмотрите\s+(мою\s+)?(историю|карту|записи|данные|анализы)",
    r"мо[ейи]\s+(истори[ия]|карт[ае]|запис[иь]|данные|результаты|анализы)",
    r"(узнайте|найдите|посмотрите)\s+меня",
    r"я\s+(ваш\s+)?пациент",
    r"что\s+мне\s+(назначали|прописывали|выписывали)",
    # Additional patterns
    r"(мо[ейи]|сво[ейи])\s+(диагноз|лечени[еи]|назначени[яи])",
    r"(когда|во\s+сколько)\s+(я|у\s+меня|мне)\s+(при[её]м|запис[ьи])",
    r"перенести|отменить|перезаписать",
    r"результаты\s+(мо[ейи]|анализов|обследования)",
]


def _check_medical_data(text: str) -> EscalationCheck | None:
    """Detect requests for existing patient medical data (152-ФЗ)."""
    text_lower = text.lower()
    for pattern in MEDICAL_DATA_PATTERNS:
        if re.search(pattern, text_lower):
            return EscalationCheck(
                should_escalate=True,
                reason=EscalationReason.medical_data_request.value,
                severity=EscalationSeverity.immediate.value,
                auto_escalate=True,
                response_template=(
                    "Сейчас соединю вас с администратором, "
                    "который сможет посмотреть вашу историю."
                ),
                matched_trigger=pattern,
            )
    return None


# ── Category 2: Complex Question ────────────────────────────────────────────

COMPLEX_QUESTION_INDICATORS: list[str] = [
    r"почему\s+(не\s+|так\s+|это\s+)",
    r"(объясните|разъясните)\s+(почему|как|что)",
    r"как\s+(вы|мне|это)\s+(определили|решили|узнали)",
    r"а\s+(если|вдруг|что\s+если)",
    r"(гаранти[юи]|безопасно|осложнения|противопоказания)",
    r"какой\s+(врач|специалист|метод|препарат)\s+(лучше|нужен|подойд[её]т)",
    r"(отличие|разница|сравни)\s+(между|от|с)",
    r"(сколько|как)\s+(долго|длится|продолжается)\s+(лечение|реабилитация|восстановление)",
]


def _check_complex_question(text: str) -> EscalationCheck | None:
    """Detect questions that are too complex for automated response."""
    text_lower = text.lower()

    # Long message with multiple question marks = complex
    question_count = text.count("?")
    if question_count >= 3 and len(text) > 100:
        return EscalationCheck(
            should_escalate=True,
            reason=EscalationReason.complex_question.value,
            severity=EscalationSeverity.urgent.value,
            auto_escalate=True,
            response_template=(
                "Это сложный вопрос, дайте мне минуту — "
                "сейчас подключу администратора."
            ),
            matched_trigger="multiple_questions",
            context={"question_count": question_count, "text_length": len(text)},
        )

    # Regex patterns for complex medical/legal questions
    for pattern in COMPLEX_QUESTION_INDICATORS:
        if re.search(pattern, text_lower):
            return EscalationCheck(
                should_escalate=True,
                reason=EscalationReason.complex_question.value,
                severity=EscalationSeverity.urgent.value,
                auto_escalate=True,
                response_template=(
                    "Хороший вопрос! Дайте мне минуту — "
                    "сейчас подключу администратора, он ответит точнее."
                ),
                matched_trigger=pattern,
            )

    return None


# ── Category 3: Inappropriate Behavior ──────────────────────────────────────

PROFANITY_PATTERNS: list[str] = [
    r"\b(сука|блядь|блять|иди\s+нахуй|пидор|пидорас|мудак|гандон)\b",
    r"\b(ху[йе]|пизд|еб[аои]|заеб|уеб|охуе|ахуе)\w*\b",
]

THREAT_PATTERNS: list[str] = [
    r"(подам\s+в\s+суд|жалобу\s+(напишу|подам)|роспотребнадзор|прокуратур)",
    r"(вы\s+(мне\s+)?(ответите|заплатите)|я\s+(вас|тебя)\s+(найду|заставлю|засужу))",
    r"(обманули|кинули|развод|мошенники|лохотрон)",
]


def _check_inappropriate(text: str) -> EscalationCheck | None:
    """Detect profanity, threats, and abusive behavior."""
    text_lower = text.lower()

    for pattern in PROFANITY_PATTERNS:
        if re.search(pattern, text_lower):
            return EscalationCheck(
                should_escalate=True,
                reason=EscalationReason.inappropriate_behavior.value,
                severity=EscalationSeverity.routine.value,
                auto_escalate=False,
                response_template="Пожалуйста, давайте общаться уважительно.",
                matched_trigger=pattern,
                context={"category": "profanity"},
            )

    for pattern in THREAT_PATTERNS:
        if re.search(pattern, text_lower):
            return EscalationCheck(
                should_escalate=True,
                reason=EscalationReason.inappropriate_behavior.value,
                severity=EscalationSeverity.urgent.value,
                auto_escalate=True,
                response_template="Сейчас соединю вас с руководителем.",
                matched_trigger=pattern,
                context={"category": "threat"},
            )

    return None


# ── Category 4: Explicit Human Request ──────────────────────────────────────

HUMAN_REQUEST_PATTERNS: list[str] = [
    r"(позовите|позвать|соедините|дайте|нужен|хочу)\s+(человека|администратора|менеджера|оператора|врача|доктора)",
    r"(человек|живой\s+человек|реальный\s+человек)",
    r"(не\s+робот|не\s+бот|это\s+бот|автоответчик)",
    r"(перезвоните|позвоните|наберите|дайте\s+телефон|номер\s+телефона)",
    r"(хочу\s+поговорить|хочу\s+общаться)\s+(с\s+)?(человеком|врачом|доктором|администратором)",
    r"(свяжитесь|свяжись)\s+(со\s+мной|с\s+руководителем)",
]


def _check_human_request(text: str) -> EscalationCheck | None:
    """Detect explicit requests to speak with a human."""
    text_lower = text.lower()

    for pattern in HUMAN_REQUEST_PATTERNS:
        if re.search(pattern, text_lower):
            return EscalationCheck(
                should_escalate=True,
                reason=EscalationReason.human_request.value,
                severity=EscalationSeverity.urgent.value,
                auto_escalate=True,
                response_template="Сейчас соединю вас с администратором. Одну минуту.",
                matched_trigger=pattern,
            )

    return None


# ── Category 5: Technical Failure ───────────────────────────────────────────

REPETITIVE_RESPONSES_THRESHOLD = 3  # Same response 3+ times = failure


def _check_technical_failure(
    last_messages: list[str],
    conversation_errors: int = 0,
) -> EscalationCheck | None:
    """Detect agent malfunctions — repetitive responses, error loops."""
    if conversation_errors >= 3:
        return EscalationCheck(
            should_escalate=True,
            reason=EscalationReason.technical_failure.value,
            severity=EscalationSeverity.routine.value,
            auto_escalate=True,
            response_template=(
                "Извините за техническую задержку. "
                "Администратор уже подключается к диалогу."
            ),
            matched_trigger=f"error_count_{conversation_errors}",
            context={"conversation_errors": conversation_errors},
        )

    # Detect repetitive agent responses
    agent_messages = [
        m for m in last_messages if len(m) > 20
    ]
    if len(agent_messages) >= REPETITIVE_RESPONSES_THRESHOLD:
        unique = set(agent_messages)
        if len(unique) <= 1:
            return EscalationCheck(
                should_escalate=True,
                reason=EscalationReason.technical_failure.value,
                severity=EscalationSeverity.routine.value,
                auto_escalate=True,
                response_template=(
                    "Извините, кажется произошёл технический сбой. "
                    "Сейчас подключу администратора."
                ),
                matched_trigger="repetitive_responses",
                context={"unique_responses": len(unique)},
            )

    return None


# ── Main Service ────────────────────────────────────────────────────────────


class EscalationService:
    """Multi-layered escalation detection for sales conversations.

    Checks are ordered by severity — medical data requests (IMMEDIATE)
    are checked first. Returns the first match.
    """

    def __init__(self) -> None:
        pass

    async def check(
        self,
        text: str,
        conversation_messages: list[str] | None = None,
        config: ProjectSalesConfig | None = None,
        conversation_errors: int = 0,
    ) -> EscalationCheck | None:
        """Run all escalation checks and return the first match.

        Args:
            text: Latest user message.
            conversation_messages: Recent message history (last N messages).
            config: Per-project escalation configuration.
            conversation_errors: Count of technical errors in this conversation.

        Returns:
            EscalationCheck if escalation is needed, None if safe to auto-reply.
        """
        # Layer 1: 152-ФЗ (IMMEDIATE — stop everything)
        result = _check_medical_data(text)
        if result:
            logger.info("escalation: medical_data_request")
            return result

        # Layer 2: Human request (URGENT)
        result = _check_human_request(text)
        if result:
            logger.info("escalation: human_request")
            return result

        # Layer 3: Threats (URGENT)
        result = _check_inappropriate(text)
        if result and result.context.get("category") == "threat":
            logger.info("escalation: threat")
            return result

        # Layer 4: Complex question (URGENT)
        result = _check_complex_question(text)
        if result:
            logger.info("escalation: complex_question")
            return result

        # Layer 5: Technical failure (ROUTINE)
        result = _check_technical_failure(
            last_messages=conversation_messages or [],
            conversation_errors=conversation_errors,
        )
        if result:
            logger.info("escalation: technical_failure")
            return result

        # Layer 6: Profanity (ROUTINE — auto-escalate=false, warn first)
        result = _check_inappropriate(text)
        if result:
            logger.info("escalation: inappropriate_behavior")
            return result

        # Layer 7: Config-based keyword rules (per-client overrides)
        if config and config.escalation_rules:
            text_lower = text.lower()
            for rule in config.escalation_rules:
                for keyword in rule.trigger_keywords:
                    if keyword.lower() in text_lower:
                        return EscalationCheck(
                            should_escalate=True,
                            reason=rule.reason.value if hasattr(rule.reason, "value") else rule.reason,
                            severity=rule.severity.value if hasattr(rule.severity, "value") else rule.severity,
                            auto_escalate=rule.auto_escalate,
                            response_template=rule.response_template,
                            matched_trigger=keyword,
                        )

        # Layer 8: Default keyword rules (from sales_admin_base)
        for rule in DEFAULT_ESCALATION_RULES:
            for keyword in rule.trigger_keywords:
                if keyword.lower() in text.lower():
                    return EscalationCheck(
                        should_escalate=True,
                        reason=rule.reason.value,
                        severity=rule.severity.value,
                        auto_escalate=rule.auto_escalate,
                        response_template=rule.response_template,
                        matched_trigger=keyword,
                    )

        return None
