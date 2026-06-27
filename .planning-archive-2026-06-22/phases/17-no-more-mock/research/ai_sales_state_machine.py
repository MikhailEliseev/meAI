"""
AI Sales Agent — Conversation State Machine
============================================
Based on:
- ai-lead-qualifier conversation state pattern
- ai-crm-agents event-driven orchestrator
- ROADMAP.md Phase 13 flow

State transitions for the chat dialog.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


class ConversationStage(Enum):
    """Stages of the sales conversation."""
    WELCOME = auto()             # First message, collect clinic_type
    QUALIFICATION = auto()        # Asking mandatory questions
    QUALIFICATION_IMPORTANT = auto()  # Asking important questions
    TIER1_RUNNING = auto()        # Background audit running
    TIER1_PRESENTING = auto()     # Showing basic audit results
    TIER2_CONSENT = auto()        # Asking permission for deep audit
    TIER2_RUNNING = auto()        # Deep audit in background
    TIER2_PRESENTING = auto()     # Showing full results
    PROPOSAL = auto()             # Making offer with ROI
    OBJECTION_HANDLING = auto()   # Processing objections
    CLOSING = auto()              # Payment / next step
    FOLLOW_UP = auto()            # Post-conversation follow-up
    HUMAN_HANDOFF = auto()        # Escalated to human manager


@dataclass
class LeadData:
    """Structured lead data (populated during qualification)."""
    # Mandatory
    clinic_type: Optional[str] = None       # Стоматология, Косметология, ...
    location: Optional[str] = None          # Город, регион
    monthly_patients: Optional[str] = None  # До 100 / 100-300 / ...
    current_channels: list[str] = field(default_factory=list)  # SEO, Ads, Social, Referral, None

    # Important
    avg_check: Optional[str] = None         # 3-7 тыс / 7-15 тыс / ...
    website_url: Optional[str] = None       # https://clinic.ru
    marketing_history: Optional[str] = None  # Что пробовали, результаты
    competitors: list[str] = field(default_factory=list)  # Названия или URL конкурентов

    # Optional
    budget_range: Optional[str] = None      # До 30 тыс / 30-60 тыс / ...
    urgency: Optional[str] = None           # Вчера / В этом месяце / ...
    decision_authority: Optional[str] = None  # Собственник / Главврач / ...
    email: Optional[str] = None             # Для отправки аудита
    phone: Optional[str] = None             # Для созвона

    # Computed
    lead_score: int = 0
    lead_tier: str = "cold"                 # hot / warm / cold


@dataclass
class AuditResults:
    """Results from background Magister runs."""
    # TIER 1 (free)
    pagespeed_score: Optional[int] = None
    pagespeed_impact: Optional[str] = None
    load_time_seconds: Optional[float] = None
    technical_errors_count: Optional[int] = None
    content_pages_count: Optional[int] = None
    questions_unanswered: Optional[int] = None
    example_question: Optional[str] = None
    visibility_queries: Optional[int] = None
    competitor_visibility_queries: Optional[int] = None

    # TIER 2 (paid APIs)
    keyword_gap_count: Optional[int] = None
    competitor_revenue: Optional[dict] = None   # {name: revenue}
    ad_cost_per_click: Optional[float] = None
    ad_cost_per_patient: Optional[float] = None
    social_competitor_stats: Optional[dict] = None  # {name: {platform: followers}}

    # Computed
    lost_patients_monthly: Optional[int] = None
    lost_revenue_monthly: Optional[int] = None
    predicted_patients: Optional[int] = None
    predicted_revenue: Optional[int] = None
    recommended_plan: Optional[str] = None     # start / growth / scale
    roi_multiplier: Optional[float] = None
    cost_per_patient: Optional[float] = None
    payback_months: Optional[int] = None


@dataclass
class ConversationState:
    """Full conversation state (one per chat session)."""
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    stage: ConversationStage = ConversationStage.WELCOME
    lead: LeadData = field(default_factory=LeadData)
    audit: AuditResults = field(default_factory=AuditResults)

    # Question tracking
    current_question_index: int = 0
    questions_asked: int = 0
    mandatory_questions: list[str] = field(default_factory=lambda: [
        "clinic_type",
        "location",
        "monthly_patients",
        "current_channels",
    ])
    important_questions: list[str] = field(default_factory=lambda: [
        "avg_check",
        "website_url",
        "marketing_history",
        "competitors",
    ])
    optional_questions: list[str] = field(default_factory=lambda: [
        "budget_range",
        "urgency",
        "decision_authority",
        "email",
        "phone",
    ])

    # Message history
    messages: list[dict] = field(default_factory=list)

    # Timestamps
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # TIER tracking
    tier1_completed: bool = False
    tier2_completed: bool = False
    proposal_shown: bool = False

    def missing_mandatory(self) -> list[str]:
        """Return list of mandatory attributes not yet collected."""
        missing = []
        for attr in self.mandatory_questions:
            value = getattr(self.lead, attr, None)
            if value is None or value == "" or value == []:
                missing.append(attr)
        return missing

    def missing_important(self) -> list[str]:
        """Return list of important attributes not yet collected."""
        missing = []
        for attr in self.important_questions:
            value = getattr(self.lead, attr, None)
            if value is None or value == "" or value == []:
                missing.append(attr)
        return missing

    def next_question(self) -> Optional[str]:
        """Determine next question based on priority: mandatory → important → optional."""
        mandatory = self.missing_mandatory()
        if mandatory:
            return mandatory[0]

        important = self.missing_important()
        if important:
            return important[0]

        # Only ask optional if lead is warm+
        if self.lead.lead_tier in ("warm", "hot"):
            for attr in self.optional_questions:
                value = getattr(self.lead, attr, None)
                if value is None or value == "":
                    return attr

        return None  # All questions asked

    def is_mandatory_complete(self) -> bool:
        return len(self.missing_mandatory()) == 0

    def is_important_complete(self) -> bool:
        return len(self.missing_important()) == 0

    def is_ready_for_tier1(self) -> bool:
        """Tier1 requires: mandatory complete + website_url."""
        return self.is_mandatory_complete() and self.lead.website_url is not None

    def is_ready_for_tier2(self) -> bool:
        """Tier2 requires: important complete + tier1 done + lead is hot."""
        return (
            self.is_important_complete()
            and self.tier1_completed
            and self.lead.lead_tier == "hot"
        )

    def is_ready_for_proposal(self) -> bool:
        """Proposal requires: tier1 done + tier2 consent (or skipped) + basic scoring."""
        return self.tier1_completed and self.lead.lead_tier in ("warm", "hot")

    def compute_lead_score(self) -> int:
        """Rule-based lead scoring (same pattern as ai-lead-qualification-agent)."""
        score = 0

        # Mandatory signals (40 points max)
        if self.lead.clinic_type:
            score += 5
        if self.lead.location:
            score += 5
        if self.lead.monthly_patients:
            # Higher patient volume = more potential
            pts = self.lead.monthly_patients
            if "500" in pts:
                score += 15
            elif "300" in pts:
                score += 10
            elif "100" in pts:
                score += 5
        if self.lead.current_channels:
            score += 5
        if self.lead.website_url:
            score += 15  # URL = strongest signal (can run audit)

        # Important signals (35 points max)
        if self.lead.avg_check:
            if "15" in self.lead.avg_check or "30" in self.lead.avg_check:
                score += 10  # High check = can afford our service
            else:
                score += 5
        if self.lead.competitors:
            score += 5
        if self.lead.marketing_history:
            score += 10  # Tried marketing = has budget + need
        if len(self.lead.current_channels) > 1:
            score += 5  # Multiple channels = serious approach

        # Optional signals (25 points max)
        if self.lead.budget_range:
            score += 10
        if self.lead.urgency:
            urgent_keywords = ["вчера", "срочно", "этот месяц", "asap"]
            if any(kw in self.lead.urgency.lower() for kw in urgent_keywords):
                score += 10
            else:
                score += 5
        if self.lead.decision_authority:
            authority_keywords = ["собственник", "главврач", "владелец", "owner"]
            if any(kw in (self.lead.decision_authority or "").lower() for kw in authority_keywords):
                score += 5

        # Determine tier
        if score >= 70:
            self.lead.lead_tier = "hot"
        elif score >= 40:
            self.lead.lead_tier = "warm"
        else:
            self.lead.lead_tier = "cold"

        self.lead.lead_score = min(100, score)
        return self.lead.lead_score


# ============================================================================
# CONVERSATION FLOW (State Transition Map)
# ============================================================================
"""
State transitions:

WELCOME
  ├── [has clinic_type] → QUALIFICATION
  └── [no clinic_type] → WELCOME (re-ask)

QUALIFICATION
  ├── [mandatory complete + has URL] → TIER1_RUNNING
  ├── [mandatory complete + no URL] → QUALIFICATION_IMPORTANT (ask URL)
  └── [mandatory not complete] → QUALIFICATION (next mandatory question)

QUALIFICATION_IMPORTANT
  ├── [got URL] → TIER1_RUNNING
  ├── [important complete + warm/hot + no URL] → TIER1_PRESENTING (general info, no site audit)
  └── [important not complete] → QUALIFICATION_IMPORTANT (next important question)

TIER1_RUNNING
  ├── [audit success] → TIER1_PRESENTING
  ├── [audit error] → TIER1_PRESENTING (graceful degradation)
  └── [user asked unrelated question] → QUALIFICATION (answer + resume)

TIER1_PRESENTING
  ├── [hot + wants more] → TIER2_CONSENT
  ├── [warm + wants more] → TIER2_CONSENT
  ├── [warm + not sure] → PROPOSAL (show TIER1-only proposal)
  └── [cold] → QUALIFICATION_IMPORTANT (more qualifying questions)

TIER2_CONSENT
  ├── [yes] → TIER2_RUNNING
  └── [no / not now] → PROPOSAL (TIER1-only)

TIER2_RUNNING
  ├── [audit success] → TIER2_PRESENTING
  └── [audit error] → PROPOSAL (TIER1-only with note)

TIER2_PRESENTING
  └── [user ready] → PROPOSAL

PROPOSAL
  ├── [yes, pay] → CLOSING
  ├── [objection] → OBJECTION_HANDLING
  ├── [question] → PROPOSAL (answer + re-present)
  └── [need to think] → FOLLOW_UP

OBJECTION_HANDLING
  ├── [resolved + ready] → PROPOSAL
  ├── [resolved + not ready] → FOLLOW_UP
  └── [escalation needed] → HUMAN_HANDOFF

CLOSING
  ├── [payment initiated] → FOLLOW_UP (confirmation + next steps)
  └── [payment deferred] → FOLLOW_UP

FOLLOW_UP
  └── [conversation dormant] → (wait for user return or scheduled nudge)

HUMAN_HANDOFF
  └── [transferred] → FOLLOW_UP (manager will contact)
"""
