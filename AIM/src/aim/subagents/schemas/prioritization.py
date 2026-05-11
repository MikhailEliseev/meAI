"""Prioritization Schemas

Models for keyword prioritization, user feedback, and adaptive learning.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PriorityTier(str, Enum):
    """Priority tier classification

    P0: 80-100 - Critical opportunities (high volume, low difficulty, transactional)
    P1: 60-79 - High priority (good balance of metrics)
    P2: 40-59 - Medium priority (worth pursuing but not urgent)
    P3: 0-39 - Low priority (low volume, high difficulty, or informational)
    """

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class KeywordPriority(BaseModel):
    """Keyword priority calculation result

    Priority Score = (Volume × Intent × Position) / (Difficulty × Competition)

    Components:
    - Volume: Search volume (normalized 0-100)
    - Intent: Commercial intent multiplier (1.0-1.4)
    - Position: Current ranking bonus (0.5-1.0)
    - Difficulty: SEO difficulty (0-100)
    - Competition: Paid competition (0-1)

    Adjustments:
    - Medical intent boost: +40% for transactional, +30% for informational
    - SERP penalty: -20% to -50% based on AI Overview/Featured Snippet presence
    - Compliance penalty: -50% for HIGH risk, -100% (blocked) for CRITICAL risk
    """

    keyword: str = Field(..., description="Keyword text")
    base_score: float = Field(..., ge=0, le=100, description="Base priority score (0-100)")
    adjusted_score: float = Field(..., ge=0, le=100, description="Score after adjustments")
    tier: PriorityTier = Field(..., description="Priority tier (P0-P3)")

    # Score components
    volume_score: float = Field(..., ge=0, le=100, description="Volume component")
    intent_score: float = Field(..., ge=1.0, le=1.4, description="Intent multiplier")
    position_score: float = Field(..., ge=0.5, le=1.0, description="Position bonus")
    difficulty_score: float = Field(..., ge=0, le=100, description="Difficulty penalty")
    competition_score: float = Field(..., ge=0, le=1, description="Competition penalty")

    # Adjustments applied
    medical_boost: float = Field(default=0.0, ge=0, le=0.4, description="Medical intent boost")
    serp_penalty: float = Field(default=0.0, ge=0, le=0.5, description="SERP feature penalty")
    compliance_penalty: float = Field(default=0.0, ge=0, le=1.0, description="Compliance penalty")

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence in calculation")

    @field_validator("tier", mode="before")
    @classmethod
    def classify_tier(cls, v: Optional[PriorityTier], info) -> PriorityTier:
        """Auto-classify tier based on adjusted_score if not provided"""
        if v is not None:
            return v

        score = info.data.get("adjusted_score", 0)
        if score >= 80:
            return PriorityTier.P0
        elif score >= 60:
            return PriorityTier.P1
        elif score >= 40:
            return PriorityTier.P2
        else:
            return PriorityTier.P3


class FeedbackType(str, Enum):
    """User feedback type"""

    ACCURACY = "accuracy"  # Keyword relevance/accuracy
    PRIORITY = "priority"  # Priority tier correctness
    COMPLIANCE = "compliance"  # Compliance decision correctness
    GENERAL = "general"  # General feedback


class UserFeedback(BaseModel):
    """User feedback on keyword research results

    Used for adaptive learning and priority adjustment.
    """

    keyword: str = Field(..., description="Keyword that feedback is about")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 (1=poor, 5=excellent)")
    comment: Optional[str] = Field(None, description="Optional comment")

    # Context
    original_priority: Optional[PriorityTier] = Field(None, description="Original priority tier")
    suggested_priority: Optional[PriorityTier] = Field(None, description="User-suggested priority")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = Field(None, description="User identifier")


class FeedbackSummary(BaseModel):
    """Aggregated feedback summary for learning

    Used to adjust prioritization weights and formulas.
    """

    total_feedback: int = Field(..., ge=0, description="Total feedback count")
    average_rating: float = Field(..., ge=1, le=5, description="Average rating")

    # By type
    accuracy_avg: float = Field(..., ge=1, le=5, description="Average accuracy rating")
    priority_avg: float = Field(..., ge=1, le=5, description="Average priority rating")
    compliance_avg: float = Field(..., ge=1, le=5, description="Average compliance rating")

    # Priority tier accuracy
    p0_accuracy: float = Field(..., ge=0, le=1, description="P0 tier accuracy (0-1)")
    p1_accuracy: float = Field(..., ge=0, le=1, description="P1 tier accuracy (0-1)")
    p2_accuracy: float = Field(..., ge=0, le=1, description="P2 tier accuracy (0-1)")
    p3_accuracy: float = Field(..., ge=0, le=1, description="P3 tier accuracy (0-1)")

    # Recommendations
    needs_adjustment: bool = Field(..., description="Whether weights need adjustment")
    adjustment_reason: Optional[str] = Field(None, description="Why adjustment is needed")

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    feedback_period_days: int = Field(..., ge=1, description="Period covered by summary")
