"""Payment Schemas

Pydantic models for payment processing API.

Part of: Phase 11 Sprint 3 - Task 3.1
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class PaymentStatus(str, Enum):
    """Payment transaction status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method type."""

    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    YOOKASSA = "yookassa"  # For future ЮKassa integration


class CardBrand(str, Enum):
    """Card brand/network."""

    VISA = "visa"
    MASTERCARD = "mastercard"
    MIR = "mir"
    UNKNOWN = "unknown"


class PaymentRequest(BaseModel):
    """Payment initiation request."""

    amount: float = Field(..., gt=0, description="Payment amount in RUB")
    currency: str = Field(default="RUB", description="Currency code (ISO 4217)")
    payment_method: PaymentMethod = Field(..., description="Payment method")

    # Customer info
    customer_name: str = Field(..., min_length=2, max_length=200)
    customer_email: EmailStr
    customer_phone: Optional[str] = Field(None, pattern=r"^\+7\d{10}$")

    # Card info (for card payments)
    card_number: Optional[str] = Field(None, min_length=13, max_length=19)
    card_expiry: Optional[str] = Field(None, pattern=r"^\d{2}/\d{2}$")  # MM/YY
    card_cvv: Optional[str] = Field(None, pattern=r"^\d{3,4}$")

    # Optional references
    lead_id: Optional[str] = None
    metadata: Optional[dict] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if v != "RUB":
            raise ValueError("Only RUB currency is supported")
        return v

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate card number (Luhn algorithm)."""
        if v is None:
            return v

        # Remove spaces and dashes
        digits = "".join(c for c in v if c.isdigit())

        # Check length
        if len(digits) < 13 or len(digits) > 19:
            raise ValueError("Invalid card number length")

        # Luhn algorithm
        total = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        if total % 10 != 0:
            raise ValueError("Invalid card number (Luhn check failed)")

        return digits


class PaymentResponse(BaseModel):
    """Payment initiation response."""

    payment_id: str
    status: PaymentStatus
    amount: float
    currency: str
    external_transaction_id: Optional[str] = None
    created_at: datetime
    message: str = "Payment initiated successfully"


class PaymentStatusResponse(BaseModel):
    """Payment status check response."""

    payment_id: str
    status: PaymentStatus
    amount: float
    currency: str
    payment_method: str
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    external_transaction_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class RefundRequest(BaseModel):
    """Payment refund request."""

    payment_id: str
    amount: Optional[float] = Field(
        None,
        gt=0,
        description="Refund amount (partial refund if less than original)",
    )
    reason: str = Field(..., min_length=10, max_length=500)


class RefundResponse(BaseModel):
    """Payment refund response."""

    payment_id: str
    refunded_amount: float
    status: PaymentStatus
    refunded_at: datetime
    message: str = "Refund processed successfully"


class PaymentRecord(BaseModel):
    """Internal payment record (with decrypted data)."""

    id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str

    # Decrypted customer info
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None

    # Card info
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None

    # References
    external_transaction_id: Optional[str] = None
    lead_id: Optional[str] = None

    # Metadata
    metadata: Optional[dict] = None

    # Error tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Refund tracking
    refunded_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    # Audit
    created_by: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True
