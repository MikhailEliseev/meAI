"""Onboarding Schemas

Pydantic models for onboarding workflow API.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OnboardingStartRequest(BaseModel):
    """Request to start onboarding."""

    lead_id: str = Field(..., min_length=1, max_length=50)


class OnboardingStartResponse(BaseModel):
    """Response after starting onboarding."""

    onboarding_id: str
    lead_id: str
    state: str
    progress: int
    message: str


class OnboardingStatusResponse(BaseModel):
    """Response with onboarding status."""

    onboarding_id: str
    lead_id: str
    state: str
    progress: int
    documents_uploaded: list[str]
    documents_validated: bool
    payment_id: Optional[str] = None
    onboarding_fee: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    next_steps: list[str]


class OnboardingDocumentUploadRequest(BaseModel):
    """Request to upload document during onboarding."""

    document_type: Literal["license", "inn", "ogrn", "contract"] = Field(...)


class OnboardingDocumentUploadResponse(BaseModel):
    """Response after document upload."""

    onboarding_id: str
    document_id: str
    document_type: str
    state: str
    progress: int
    message: str


class OnboardingPaymentRequest(BaseModel):
    """Request to process onboarding payment."""

    amount: float = Field(..., gt=0)
    currency: str = Field(default="RUB", pattern="^[A-Z]{3}$")
    payment_method: Literal["CARD", "BANK_TRANSFER", "YOOKASSA"] = Field(...)

    # Card details (if payment_method == CARD)
    card_number: Optional[str] = Field(None, min_length=13, max_length=19)
    card_holder: Optional[str] = Field(None, min_length=1, max_length=100)
    card_expiry: Optional[str] = Field(None, pattern=r"^\d{2}/\d{2}$")
    card_cvv: Optional[str] = Field(None, min_length=3, max_length=4)

    # Customer details
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_email: str = Field(..., min_length=1, max_length=200)
    customer_phone: Optional[str] = Field(None, min_length=1, max_length=20)


class OnboardingPaymentResponse(BaseModel):
    """Response after payment processing."""

    onboarding_id: str
    payment_id: str
    payment_status: str
    state: str
    progress: int
    message: str


class OnboardingCompleteResponse(BaseModel):
    """Response after onboarding completion."""

    onboarding_id: str
    lead_id: str
    state: str
    progress: int
    completed_at: datetime
    message: str


class OnboardingRetryRequest(BaseModel):
    """Request to retry failed step."""

    step: Literal[
        "documents_validation",
        "payment_processing",
        "onboarding_completion"
    ] = Field(...)


class OnboardingRetryResponse(BaseModel):
    """Response after retry attempt."""

    onboarding_id: str
    step: str
    state: str
    progress: int
    message: str


class OnboardingNextStep(BaseModel):
    """Next step in onboarding workflow."""

    step: str
    description: str
    required: bool
    completed: bool


class OnboardingProgressResponse(BaseModel):
    """Detailed progress response."""

    onboarding_id: str
    state: str
    progress: int
    steps: list[OnboardingNextStep]
    current_step: Optional[str] = None
    estimated_completion: Optional[str] = None
