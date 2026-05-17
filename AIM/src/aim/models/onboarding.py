"""Onboarding Model

Tracks clinic onboarding workflow state and progress.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Float, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from aim.database import Base


class Onboarding(Base):
    """Onboarding model for clinic onboarding workflow.

    Tracks complete onboarding process:
    - Lead association
    - State machine state
    - Document upload progress
    - Payment processing
    - Completion status
    """

    __tablename__ = "onboardings"

    # Primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Relationships
    lead_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # State tracking
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # LEAD_CREATED, DOCUMENTS_PENDING, etc.
    progress: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 0-100

    # Document tracking
    documents_uploaded: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # List of document IDs
    documents_validated: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )

    # Payment tracking
    onboarding_fee: Mapped[float] = mapped_column(
        Float, nullable=False, default=50000.0
    )  # RUB

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Failure tracking
    failure_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Onboarding(id={self.id}, lead_id={self.lead_id}, "
            f"state={self.state}, progress={self.progress}%)>"
        )

    @staticmethod
    def generate_id() -> str:
        """Generate unique onboarding ID.

        Format: onb_YYYYMMDDHHMMSS_random

        Returns:
            Onboarding ID
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6]
        return f"onb_{timestamp}_{random_suffix}"

    def add_document(self, document_id: str) -> None:
        """Add document to uploaded list.

        Args:
            document_id: Document ID to add
        """
        if document_id not in self.documents_uploaded:
            self.documents_uploaded.append(document_id)

    def get_uploaded_document_types(self) -> list[str]:
        """Get list of uploaded document types.

        Returns:
            List of document types (from extra_data)
        """
        if not self.extra_data:
            return []
        return self.extra_data.get("document_types", [])

    def is_documents_complete(self) -> bool:
        """Check if all required documents uploaded.

        Required: license, inn, ogrn, contract

        Returns:
            True if all required documents uploaded
        """
        required = {"license", "inn", "ogrn", "contract"}
        uploaded = set(self.get_uploaded_document_types())
        return required.issubset(uploaded)

    def calculate_progress(self) -> int:
        """Calculate onboarding progress percentage.

        Steps:
        - Lead created: 10%
        - Documents uploaded: 40%
        - Documents validated: 60%
        - Payment completed: 90%
        - Onboarding complete: 100%

        Returns:
            Progress percentage (0-100)
        """
        if self.state == "ONBOARDING_COMPLETE":
            return 100
        elif self.state == "ONBOARDING_FAILED":
            return self.progress  # Keep last progress
        elif self.state in ("PAYMENT_COMPLETED", "PAYMENT_PROCESSING"):
            return 90
        elif self.state == "DOCUMENTS_VALIDATED":
            return 60
        elif self.state == "DOCUMENTS_UPLOADED":
            return 40
        elif self.state == "DOCUMENTS_PENDING":
            # Partial progress based on uploaded documents
            if self.is_documents_complete():
                return 40
            else:
                uploaded_count = len(self.get_uploaded_document_types())
                return 10 + (uploaded_count * 7)  # 10% + up to 28% (4 docs * 7%)
        elif self.state == "LEAD_CREATED":
            return 10
        else:
            return 0
