"""Lead Scoring Schemas

Pydantic models for lead scoring results and features.

Part of: Phase 11 Sprint 2 - Task 2.2
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class LeadScore(BaseModel):
    """Lead scoring result with tier and explanation"""

    score: int = Field(..., ge=0, le=100, description="Lead score (0-100)")
    tier: str = Field(..., description="Lead tier (Hot/Warm/Cold)")
    explanation: list[str] = Field(..., description="Top 5 factors influencing score")
    factors: dict[str, Any] = Field(..., description="All extracted features")
    scored_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when lead was scored",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "score": 85,
                "tier": "Hot",
                "explanation": [
                    "High-value specialty: Plastic Surgery (+15 points)",
                    "Detailed inquiry message (+12 points)",
                    "Business hours submission (+8 points)",
                    "Organic search traffic (+10 points)",
                    "First-time submission (+5 points)",
                ],
                "factors": {
                    "specialty": "plastic_surgery",
                    "message_length": 150,
                    "hour_of_day": 14,
                    "traffic_source": "organic_search",
                    "previous_submissions": 0,
                },
                "scored_at": "2026-05-16T20:30:00Z",
            }
        }


class LeadFeatures(BaseModel):
    """Extracted features for lead scoring"""

    # Demographic factors (10 points)
    specialty: str = Field(..., description="Medical specialty")
    clinic_size: str = Field(..., description="Inferred clinic size (chain/single)")
    location: str = Field(..., description="Location tier (moscow/spb/regional/small)")

    # Behavioral factors (20 points)
    message_quality: int = Field(..., ge=0, le=10, description="Message quality score")
    response_time: str = Field(..., description="Response time category")
    utm_campaign: str | None = Field(None, description="UTM campaign")

    # Engagement factors (15 points)
    form_completion: float = Field(..., ge=0, le=1, description="Form completion rate")
    message_length: int = Field(..., ge=0, description="Message length in characters")
    has_phone_and_email: bool = Field(..., description="Both phone and email provided")

    # Technical factors (10 points)
    device_type: str = Field(..., description="Device type (desktop/mobile/tablet)")
    browser: str = Field(..., description="Browser type")
    session_duration: int = Field(..., ge=0, description="Session duration in seconds")

    # Timing factors (10 points)
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday)")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")

    # Source factors (15 points)
    traffic_source: str = Field(..., description="Traffic source")
    is_referral: bool = Field(..., description="Is referral traffic")

    # Historical factors (10 points)
    previous_submissions: int = Field(..., ge=0, description="Previous submission count")
    email_domain_type: str = Field(..., description="Email domain type (business/free)")

    # Compliance factors (10 points)
    fz152_consent: bool = Field(..., description="ФЗ-152 consent given")
    data_completeness: float = Field(..., ge=0, le=1, description="Data completeness")

    class Config:
        json_schema_extra = {
            "example": {
                "specialty": "plastic_surgery",
                "clinic_size": "single",
                "location": "moscow",
                "message_quality": 8,
                "response_time": "business_hours",
                "utm_campaign": "plastic_surgery_promo",
                "form_completion": 1.0,
                "message_length": 150,
                "has_phone_and_email": True,
                "device_type": "desktop",
                "browser": "chrome",
                "session_duration": 180,
                "day_of_week": 2,
                "hour_of_day": 14,
                "traffic_source": "organic_search",
                "is_referral": False,
                "previous_submissions": 0,
                "email_domain_type": "business",
                "fz152_consent": True,
                "data_completeness": 1.0,
            }
        }
