"""Linear Task Database Model

Stores Linear task metadata in AIM database for tracking and synchronization.

Part of: Phase 11 Sprint 2 - Task 2.3
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aim.storage.models import Base


class LinearTask(Base):
    """Linear task metadata

    Stores information about Linear issues created for leads.
    Used for status synchronization and tracking.
    """

    __tablename__ = "linear_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    lead_id: Mapped[str] = mapped_column(
        String, ForeignKey("leads.id"), nullable=False, index=True
    )
    linear_issue_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    linear_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # backlog, in_progress, completed, canceled
    assignee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationship
    lead: Mapped["Lead"] = relationship("Lead", back_populates="linear_tasks")

    def __repr__(self) -> str:
        return f"<LinearTask(id={self.id}, lead_id={self.lead_id}, status={self.status})>"
