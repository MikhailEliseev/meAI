"""Document Model

Tracks uploaded documents for clinic onboarding with OCR and AI extraction.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Float, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.aim.storage.models import Base


class Document(Base):
    """Document model for clinic onboarding.

    Stores uploaded documents (license, INN, OGRN, contracts) with:
    - File metadata (path, size, type)
    - OCR extracted text
    - AI extracted structured data
    - Validation results
    - Processing status
    """

    __tablename__ = "documents"

    # Primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Relationships
    lead_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Document metadata
    document_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # license, inn, ogrn, contract
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, default="pending"
    )  # pending, processing, completed, failed

    # OCR results
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI extraction results
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Validation results
    validation_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # valid, invalid, needs_review
    validation_errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Audit trail
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, type={self.document_type}, "
            f"status={self.status}, lead_id={self.lead_id})>"
        )

    @staticmethod
    def generate_id() -> str:
        """Generate unique document ID.

        Format: doc_YYYYMMDDHHMMSS_random

        Returns:
            Document ID
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6]
        return f"doc_{timestamp}_{random_suffix}"
