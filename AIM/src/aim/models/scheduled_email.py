"""Scheduled Email model for email automation.

Represents a single email scheduled to be sent as part of a workflow.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from aim.storage.models import Base


class ScheduledEmail(Base):
    """Scheduled email in a workflow.

    Represents a single email to be sent at a specific time.
    Tracks send status, retries, and SendGrid message ID.

    Attributes:
        id: Unique email identifier
        workflow_id: Reference to workflow
        template_id: Template identifier (e.g., 'hot_instant', 'warm_day0')
        recipient_email: Email address to send to
        subject: Email subject line
        html_content: HTML version of email
        text_content: Plain text version of email
        scheduled_at: When to send this email
        sent_at: When email was actually sent
        status: Email status (pending, sent, failed, cancelled)
        retry_count: Number of send attempts
        sendgrid_message_id: SendGrid message ID for tracking
        created_at: When email was created

    Relationships:
        workflow: Workflow this email belongs to
        events: Tracking events for this email
    """

    __tablename__ = "scheduled_emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("email_workflows.id"), nullable=False)
    template_id = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed, cancelled
    retry_count = Column(Integer, nullable=False, default=0)
    sendgrid_message_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    workflow = relationship("EmailWorkflow", back_populates="scheduled_emails")
    events = relationship("EmailEvent", back_populates="email", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ScheduledEmail(id={self.id}, workflow_id={self.workflow_id}, template={self.template_id}, status={self.status})>"
