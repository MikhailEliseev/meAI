"""
AI Ad Copy Generator Schemas

Pydantic models for ad copy generation results.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AdCopyVariant(BaseModel):
    """Single ad copy variant."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "headline": "Имплантация зубов за 1 день",
                "description": "Без боли и осложнений. Гарантия 10 лет. Запись на бесплатную консультацию.",
                "cta": "Записаться на консультацию",
                "emotional_trigger": "urgency",
                "compliance_score": 95.0,
                "predicted_ctr": 3.2,
            }
        }
    )

    headline: str = Field(..., description="Ad headline (max 30 chars)")
    description: str = Field(..., description="Ad description (max 90 chars)")
    cta: str = Field(..., description="Call-to-action text")
    emotional_trigger: str = Field(..., description="Emotional trigger used (urgency, trust, fear, etc.)")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Compliance score (0-100)")
    predicted_ctr: float = Field(..., ge=0.0, le=100.0, description="Predicted CTR (%)")


class ComplianceCheck(BaseModel):
    """Compliance check result."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "passed": True,
                "score": 95.0,
                "violations": [],
                "warnings": ["Избегайте слова 'лучший' без подтверждения"],
                "recommendations": ["Добавьте номер лицензии клиники"],
            }
        }
    )

    passed: bool = Field(..., description="Whether compliance check passed")
    score: float = Field(..., ge=0.0, le=100.0, description="Compliance score (0-100)")
    violations: List[str] = Field(default_factory=list, description="List of violations found")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")


class AdCopyResult(BaseModel):
    """Complete ad copy generation result."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "specialty": "Стоматология",
                "service": "Имплантация зубов",
                "platform": "yandex_direct",
                "variants": [],
                "compliance": {},
                "template_used": "dental_implants_urgency",
                "generation_cost": 0.14,
            }
        }
    )

    specialty: str = Field(..., description="Medical specialty")
    service: str = Field(..., description="Specific service")
    platform: str = Field(..., description="Ad platform (yandex_direct, google_ads)")
    variants: List[AdCopyVariant] = Field(..., description="Generated ad copy variants")
    compliance: ComplianceCheck = Field(..., description="Compliance check result")
    template_used: str = Field(..., description="Template ID used")
    generation_cost: float = Field(..., description="Generation cost in USD")


class AdTemplate(BaseModel):
    """Ad copy template."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "template_id": "dental_implants_urgency",
                "specialty": "Стоматология",
                "service": "Имплантация зубов",
                "emotional_trigger": "urgency",
                "headline_template": "{service} за {timeframe}",
                "description_template": "{benefit}. {guarantee}. {cta_text}.",
                "cta_options": ["Записаться", "Узнать цену", "Получить консультацию"],
                "compliance_notes": ["Указать номер лицензии", "Не использовать 'лучший'"],
            }
        }
    )

    template_id: str = Field(..., description="Unique template ID")
    specialty: str = Field(..., description="Medical specialty")
    service: str = Field(..., description="Specific service")
    emotional_trigger: str = Field(..., description="Emotional trigger (urgency, trust, fear, etc.)")
    headline_template: str = Field(..., description="Headline template with placeholders")
    description_template: str = Field(..., description="Description template with placeholders")
    cta_options: List[str] = Field(..., description="CTA options")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance notes")
