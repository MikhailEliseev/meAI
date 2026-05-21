"""Email Event model for tracking email interactions.

Tracks SendGrid webhook events (sent, delivered, opened, clicked, bounced, etc.).

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from aim.storage.models import Base


class EmailEvent(Base):
    """Email tracking event from SendGrid.

    Represents a single event in the email lifecycle.
    Events are received via SendGrid webhooks.

    Attributes:
        id: Unique event identifier
        email_id: Reference to scheduled email
        event_type: Type of event (sent, delivered, opened, clicked, bounced, complained, unsubscribed)
        event_data: Additional event data from SendGrid (JSON)
        occurred_at: When event occurred (from SendGrid)
        created_at: When event was recorded in our system

    Relationships:
        email: Scheduled email this event belongs to

    Event Types:
        - sent: Email sent to SendGrid
        - delivered: Email delivered to recipient's server
        - opened: Recipient opened email
        - clicked: Recipient clicked link in email
        - bounced: Email bounced (hard or soft)
        - complained: Recipient marked as spam
        - unsubscribed: Recipient unsubscribed
    """

    __tablename__ = "email_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_emails.id"), nullable=False)
    event_type = Column(String(20), nullable=False)
    event_data = Column(JSON, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    email = relationship("ScheduledEmail", back_populates="events")

    def __repr__(self) -> str:
        return f"<EmailEvent(id={self.id}, email_id={self.email_id}, type={self.event_type}, occurred_at={self.occurred_at})>"
