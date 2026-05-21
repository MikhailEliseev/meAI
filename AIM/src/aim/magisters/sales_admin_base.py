"""Sales Admin Agent — shared constants, enums, and configuration schemas.

Part of Phase 13: AI Sales Admin Agent.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Channels ────────────────────────────────────────────────────────────────

class Channel(str, Enum):
    """Communication channel for incoming messages."""
    telegram = "telegram"
    instagram = "instagram"
    vk = "vk"
    whatsapp = "whatsapp"
    web_chat = "web_chat"


# ── Lead Pipeline ───────────────────────────────────────────────────────────

class LeadPipelineStage(str, Enum):
    """Lead lifecycle stages in the sales pipeline."""
    new = "new"
    qualified = "qualified"
    contacted = "contacted"
    active = "active"
    completed = "completed"
    closed = "closed"


# ── Escalation ──────────────────────────────────────────────────────────────

class EscalationReason(str, Enum):
    """Why a conversation was escalated to a human manager."""
    medical_data_request = "medical_data_request"    # 152-ФЗ
    complex_question = "complex_question"
    inappropriate_behavior = "inappropriate_behavior"
    human_request = "human_request"
    technical_failure = "technical_failure"


class EscalationSeverity(str, Enum):
    immediate = "immediate"  # Stop responding, escalate NOW
    urgent = "urgent"        # Escalate within 5 min
    routine = "routine"      # Flag for review, keep talking


# ── Conversation Status ─────────────────────────────────────────────────────

class ConversationStatus(str, Enum):
    active = "active"
    waiting_human = "waiting_human"
    escalated = "escalated"
    closed = "closed"


# ── Per-Client Configuration ────────────────────────────────────────────────

class EscalationRule(BaseModel):
    """Single escalation rule — trigger + action."""
    trigger_keywords: list[str] = Field(default_factory=list)
    reason: EscalationReason
    severity: EscalationSeverity = EscalationSeverity.urgent
    auto_escalate: bool = True
    response_template: Optional[str] = None


class ProjectSalesConfig(BaseModel):
    """Per-project configuration for the Sales Admin Agent.

    Set during client onboarding / setup phase.
    """

    project_id: str
    client_id: str = ""

    # Channels to monitor
    enabled_channels: list[Channel] = Field(default_factory=lambda: [Channel.telegram])

    # Response SLA
    response_time_target_seconds: int = 30

    # Qualification
    high_value_specialties: list[str] = Field(default_factory=list)
    min_budget_threshold_rub: int = 0
    auto_qualify_enabled: bool = True

    # Escalation
    escalation_rules: list[EscalationRule] = Field(default_factory=list)
    escalation_on_medical_data: bool = True
    escalation_on_complex_question: bool = True

    # Working hours (for human manager notifications)
    working_hours_start: str = "09:00"
    working_hours_end: str = "21:00"
    timezone: str = "Europe/Moscow"

    # Tone of Voice
    tone_formality: str = "professional"
    tone_language: str = "ru"
    tone_medical_terms: str = "patient_friendly"

    # Knowledge
    website_url: str = ""
    knowledge_vault_path: str = ""

    # Notification targets
    manager_telegram_chat_id: Optional[int] = None
    manager_email: Optional[str] = None

    class Config:
        use_enum_values = True


# ── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_ESCALATION_RULES: list[EscalationRule] = [
    EscalationRule(
        trigger_keywords=[
            "я у вас был", "я уже был", "я был у вас",
            "посмотрите историю", "посмотрите мою историю", "моя история",
            "мои анализы", "что мне назначали", "мои результаты",
            "моя карта", "мои записи", "мои данные",
            "узнайте меня", "я у вас лечился", "я ваш пациент",
        ],
        reason=EscalationReason.medical_data_request,
        severity=EscalationSeverity.immediate,
        auto_escalate=True,
        response_template=(
            "Сейчас соединю вас с администратором, "
            "который сможет посмотреть вашу историю."
        ),
    ),
    EscalationRule(
        trigger_keywords=[
            "позовите человека", "соедините с администратором",
            "дайте телефон", "хочу поговорить с врачом",
            "менеджера", "перезвоните мне",
        ],
        reason=EscalationReason.human_request,
        severity=EscalationSeverity.urgent,
        auto_escalate=True,
        response_template="Сейчас соединю вас с администратором. Одну минуту.",
    ),
    EscalationRule(
        trigger_keywords=[
            "сука", "блядь", "иди нахуй", "пидор",
        ],
        reason=EscalationReason.inappropriate_behavior,
        severity=EscalationSeverity.routine,
        auto_escalate=False,
        response_template="Пожалуйста, давайте общаться уважительно.",
    ),
]
