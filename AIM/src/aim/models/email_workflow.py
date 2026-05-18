"""Email Workflow model for automated email campaigns.

Tracks multi-step email sequences for leads based on their tier (Hot/Warm/Cold).

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from aim.storage.models import Base


class EmailWorkflow(Base):
    """Email workflow for automated campaigns.

    Represents a multi-step email sequence for a lead.
    Each workflow has a tier (hot/warm/cold) and tracks progress through steps.

    Attributes:
        id: Unique workflow identifier
        lead_id: Reference to lead
        tier: Lead tier (hot, warm, cold)
        status: Workflow status (active, paused, completed, cancelled)
        current_step: Current step in sequence (0-indexed)
        started_at: When workflow started
        completed_at: When workflow completed
        created_at: When workflow was created

    Relationships:
        lead: Lead this workflow belongs to
        scheduled_emails: Emails scheduled for this workflow
    """

    __tablename__ = "email_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(String(50), ForeignKey("leads.id"), nullable=False, index=True)
    tier = Column(String(10), nullable=False, index=True)  # hot, warm, cold
    status = Column(String(20), nullable=False, default="active", index=True)
    current_step = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_workflow_lead_tier", "lead_id", "tier"),
        Index("idx_workflow_status_created", "status", "created_at"),
    )

    # Relationships
    lead = relationship("Lead", back_populates="email_workflows")
    scheduled_emails = relationship("ScheduledEmail", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EmailWorkflow(id={self.id}, lead_id={self.lead_id}, tier={self.tier}, status={self.status}, step={self.current_step})>"
