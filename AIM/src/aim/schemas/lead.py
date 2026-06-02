"""Lead Capture Schemas with ФЗ-152 Compliance

Russian Market Adaptation:
- ФЗ-152 consent validation (not HIPAA)
- Russian phone number format (+7)
- Cyrillic name support
- Russian medical specialties

Part of: Phase 11 - Client Acquisition (Task 2.1)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class MedicalSpecialty(str, Enum):
    """Russian medical specialties"""

    DENTISTRY = "dentistry"  # Стоматология
    COSMETOLOGY = "cosmetology"  # Косметология
    PLASTIC_SURGERY = "plastic_surgery"  # Пластическая хирургия
    OPHTHALMOLOGY = "ophthalmology"  # Офтальмология
    CARDIOLOGY = "cardiology"  # Кардиология
    NEUROLOGY = "neurology"  # Неврология
    ORTHOPEDICS = "orthopedics"  # Ортопедия
    GYNECOLOGY = "gynecology"  # Гинекология
    PEDIATRICS = "pediatrics"  # Педиатрия
    DERMATOLOGY = "dermatology"  # Дерматология
    OTHER = "other"  # Другое


class LeadSource(str, Enum):
    """Lead acquisition source"""

    LANDING_PAGE = "landing_page"
    ORGANIC_SEARCH = "organic_search"
    PAID_ADS = "paid_ads"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    DIRECT = "direct"
    OTHER = "other"


class LeadCaptureRequest(BaseModel):
    """Lead capture form data with ФЗ-152 compliance

    Russian Market Adaptation:
    - fz152_consent: Required consent for personal data processing (ФЗ-152)
    - phone: Russian format validation (+7XXXXXXXXXX)
    - name/clinic_name: Cyrillic support
    """

    # Contact Information
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name (supports Cyrillic)",
    )
    phone: str = Field(
        ...,
        pattern=r"^\+7\d{10}$",
        description="Russian phone number (+7XXXXXXXXXX)",
    )
    email: EmailStr = Field(..., description="Email address")

    # Clinic Information
    clinic_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Clinic name (supports Cyrillic)",
    )
    specialty: MedicalSpecialty = Field(
        ...,
        description="Medical specialty",
    )

    # Message
    message: Optional[str] = Field(
        None,
        max_length=2000,
        description="Additional message or questions",
    )

    # ФЗ-152 Compliance (Russian Market Adaptation)
    fz152_consent: bool = Field(
        ...,
        description="Consent for personal data processing (ФЗ-152 required)",
    )

    # Metadata
    source: LeadSource = Field(
        default=LeadSource.LANDING_PAGE,
        description="Lead acquisition source",
    )
    utm_source: Optional[str] = Field(None, max_length=100)
    utm_medium: Optional[str] = Field(None, max_length=100)
    utm_campaign: Optional[str] = Field(None, max_length=100)
    utm_content: Optional[str] = Field(None, max_length=100)
    utm_term: Optional[str] = Field(None, max_length=100)

    # reCAPTCHA
    recaptcha_token: str = Field(
        ...,
        min_length=1,
        description="reCAPTCHA v3 token",
    )

    @field_validator("fz152_consent")
    @classmethod
    def validate_fz152_consent(cls, v: bool) -> bool:
        """Validate ФЗ-152 consent is explicitly given"""
        if not v:
            raise ValueError(
                "ФЗ-152 consent is required for personal data processing"
            )
        return v

    @field_validator("name", "clinic_name")
    @classmethod
    def validate_no_html(cls, v: str) -> str:
        """Prevent HTML injection"""
        if "<" in v or ">" in v:
            raise ValueError("HTML tags are not allowed")
        return v.strip()

    @field_validator("message")
    @classmethod
    def validate_message_no_html(cls, v: Optional[str]) -> Optional[str]:
        """Prevent HTML injection in message"""
        if v and ("<" in v or ">" in v):
            raise ValueError("HTML tags are not allowed")
        return v.strip() if v else None


class ChatLeadRequest(BaseModel):
    """Lightweight lead capture from Hermes chat — no form validation.

    Hermes collects contact via two-step conversation flow and calls
    collect_contact tool, which POSTs here. No reCAPTCHA, no rate limiting,
    no ФЗ-152 consent checkbox (obtained verbally in chat).
    """

    contact_type: str = Field(
        default="",
        description="Contact type: telegram, email, or phone. Empty for website-only leads.",
    )
    contact_value: str = Field(
        default="",
        max_length=200,
        description="Contact value: @username, email@domain.com, +7...",
    )
    website: str = Field(
        default="",
        max_length=500,
        description="Client website URL (optional)",
    )
    name: str = Field(
        default="",
        max_length=100,
        description="Client name (optional, supports Cyrillic)",
    )
    source: str = Field(
        default="web_chat",
        max_length=50,
        description="Lead source",
    )


class LeadCaptureResponse(BaseModel):
    """Lead capture response"""

    success: bool = Field(..., description="Capture success status")
    lead_id: str = Field(..., description="Unique lead identifier")
    message: str = Field(..., description="Response message")
    estimated_response_time: str = Field(
        default="15 минут",
        description="Estimated response time",
    )
    tier: Optional[str] = Field(None, description="Lead tier (Hot/Warm/Cold)")
    score: Optional[float] = Field(None, description="Lead score (0-100)")


class LeadRecord(BaseModel):
    """Internal lead record (encrypted storage)

    Fields are encrypted at rest using AES-256.
    Audit log tracks all access.
    """

    # Identifiers
    id: str = Field(..., description="Unique lead ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Contact Information (encrypted)
    name_encrypted: str = Field(..., description="Encrypted name")
    phone_encrypted: str = Field(..., description="Encrypted phone")
    email_encrypted: str = Field(..., description="Encrypted email")

    # Clinic Information (encrypted)
    clinic_name_encrypted: str = Field(..., description="Encrypted clinic name")
    specialty: MedicalSpecialty = Field(..., description="Medical specialty")

    # Message (encrypted if present)
    message_encrypted: Optional[str] = Field(
        None, description="Encrypted message"
    )

    # Compliance
    fz152_consent: bool = Field(..., description="ФЗ-152 consent given")
    fz152_consent_timestamp: datetime = Field(
        ..., description="Consent timestamp"
    )
    fz152_consent_ip: str = Field(..., description="Consent IP address")

    # Metadata
    source: LeadSource = Field(..., description="Lead source")
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None

    # Processing Status
    processed: bool = Field(default=False, description="Processing status")
    linear_task_id: Optional[str] = Field(None, description="Linear task ID")
    score: Optional[float] = Field(None, description="Lead score (0-100)")
    tier: Optional[str] = Field(None, description="Lead tier (Hot/Warm/Cold)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "lead_2026051620180001",
                "created_at": "2026-05-16T20:18:00Z",
                "updated_at": "2026-05-16T20:18:00Z",
                "name_encrypted": "encrypted_base64_string",
                "phone_encrypted": "encrypted_base64_string",
                "email_encrypted": "encrypted_base64_string",
                "clinic_name_encrypted": "encrypted_base64_string",
                "specialty": "dentistry",
                "message_encrypted": None,
                "fz152_consent": True,
                "fz152_consent_timestamp": "2026-05-16T20:18:00Z",
                "fz152_consent_ip": "192.168.1.1",
                "source": "landing_page",
                "processed": False,
            }
        }
