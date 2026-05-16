"""Payment Transaction Model

Tracks payment transactions with encryption for sensitive data.

Part of: Phase 11 Sprint 3 - Task 3.1
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from aim.database import Base


class Payment(Base):
    """Payment transaction record.

    Tracks payment lifecycle from initiation to completion/failure.
    Stores encrypted customer data for ФЗ-152 compliance.
    """

    __tablename__ = "payments"

    # Primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Transaction details
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, processing, completed, failed, refunded

    # Payment method
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # card, bank_transfer, etc.

    # Customer info (encrypted)
    customer_name_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    customer_email_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    customer_phone_encrypted: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Card info (last 4 digits only, not encrypted)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    card_brand: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )  # visa, mastercard, mir

    # External references
    external_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )  # Payment processor transaction ID
    lead_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )  # Associated lead

    # Metadata (renamed to avoid SQLAlchemy reserved name conflict)
    payment_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Error tracking
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Refund tracking
    refunded_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    refund_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit trail
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, amount={self.amount} {self.currency}, "
            f"status={self.status})>"
        )
