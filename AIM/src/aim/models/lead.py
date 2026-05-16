"""Lead Database Model with ФЗ-152 Compliance

SQLAlchemy model for storing encrypted lead data.
All PII fields are encrypted at rest using AES-256-GCM.

Russian Market Adaptation:
- ФЗ-152 consent tracking (timestamp, IP)
- Russian phone format (+7XXXXXXXXXX)
- Cyrillic name support
- Email hash for duplicate detection

Part of: Phase 11 - Client Acquisition (Task 2.1)
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from AIM.src.aim.database import Base


class Lead(Base):
    """Lead model with encrypted PII fields

    All sensitive fields (name, phone, email, clinic_name, message) are encrypted
    using AES-256-GCM before storage. Only encrypted versions are stored in DB.

    ФЗ-152 Compliance:
    - Consent timestamp and IP tracked
    - Audit log for all access (via service layer)
    - Encrypted storage for all PII
    - Email hash for duplicate detection (can't query encrypted fields directly)

    Fields:
    - id: Unique lead identifier (lead_YYYYMMDDHHMMSS_UUID)
    - created_at: Lead creation timestamp
    - updated_at: Last update timestamp
    - name_encrypted: Encrypted full name (base64)
    - phone_encrypted: Encrypted phone number (base64)
    - email_encrypted: Encrypted email address (base64)
    - email_hash: SHA-256 hash of email (for duplicate detection)
    - clinic_name_encrypted: Encrypted clinic name (base64)
    - specialty: Medical specialty (not encrypted - used for filtering)
    - message_encrypted: Encrypted message (base64, optional)
    - fz152_consent: ФЗ-152 consent given (boolean)
    - fz152_consent_timestamp: When consent was given
    - fz152_consent_ip: IP address when consent was given
    - source: Lead acquisition source
    - utm_source: UTM source parameter
    - utm_medium: UTM medium parameter
    - utm_campaign: UTM campaign parameter
    - utm_content: UTM content parameter
    - utm_term: UTM term parameter
    - user_agent: Client user agent string
    - processed: Whether lead has been processed (scoring, Linear, email)
    - linear_task_id: Linear task ID (if created)
    - score: AI lead score (0-100)
    - tier: Lead tier (Hot/Warm/Cold)
    """

    __tablename__ = "leads"

    # Primary Key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Encrypted PII Fields (base64-encoded AES-256-GCM ciphertext)
    name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    phone_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    email_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    email_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # SHA-256 hash for duplicate detection
    clinic_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    message_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Non-encrypted Fields
    specialty: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Used for filtering

    # ФЗ-152 Compliance
    fz152_consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fz152_consent_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fz152_consent_ip: Mapped[str] = mapped_column(String(45), nullable=False)

    # Metadata
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_content: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_term: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing Status
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linear_task_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tier: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # Hot/Warm/Cold

    def __repr__(self) -> str:
        return (
            f"<Lead(id={self.id}, specialty={self.specialty}, "
            f"source={self.source}, processed={self.processed})>"
        )

    @staticmethod
    def hash_email(email: str) -> str:
        """Generate SHA-256 hash of email for duplicate detection

        Args:
            email: Email address to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(email.encode()).hexdigest()
