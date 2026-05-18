"""ФЗ-152 Audit Log Model

Immutable audit trail for personal data processing operations.
Required by ФЗ-152 for regulatory compliance.

Part of: Phase 11 Sprint 4 - Task 4.2 (Security Audit)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from aim.storage.models import Base


class FZ152AuditLog(Base):
    """Immutable audit trail for ФЗ-152 personal data operations.

    Every personal data access, modification, or consent change is recorded.
    This table serves as legal evidence of compliance.
    """

    __tablename__ = "fz152_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    lead_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    agent: Mapped[str] = mapped_column(String(100), nullable=False, default="lead_capture")

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        Index("idx_fz152_lead_action", "lead_id", "action"),
        Index("idx_fz152_action_timestamp", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<FZ152AuditLog(id={self.id}, lead_id='{self.lead_id}', "
            f"action='{self.action}', timestamp={self.timestamp.isoformat()})>"
        )
