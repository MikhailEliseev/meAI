"""Workflow State Manager

Tracks workflow progress and updates state based on email events.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models import EmailEvent, EmailWorkflow, ScheduledEmail


class WorkflowStateManager:
    """Manages workflow state transitions and progress tracking.

    Responsibilities:
    - Update workflow current_step when emails are sent
    - Auto-complete workflows when all emails sent
    - Track email engagement metrics
    - Handle workflow state transitions

    Example:
        manager = WorkflowStateManager(db_session)
        await manager.update_on_email_sent(email_id)
    """

    def __init__(self, db: AsyncSession):
        """Initialize state manager.

        Args:
            db: Database session
        """
        self.db = db

    async def update_on_email_sent(self, email_id: UUID) -> None:
        """Update workflow state when email is sent.

        Args:
            email_id: ScheduledEmail UUID

        Raises:
            ValueError: If email not found
        """
        # Load email with workflow
        result = await self.db.execute(
            select(ScheduledEmail).where(ScheduledEmail.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email not found: {email_id}")

        # Load workflow
        result = await self.db.execute(
            select(EmailWorkflow).where(
                EmailWorkflow.id == email.workflow_id
            )
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow not found: {email.workflow_id}")

        # Update email status
        email.status = "sent"
        email.sent_at = datetime.utcnow()

        # Increment workflow step
        workflow.current_step += 1

        # Check if workflow is complete
        result = await self.db.execute(
            select(ScheduledEmail).where(
                ScheduledEmail.workflow_id == workflow.id
            )
        )
        all_emails = result.scalars().all()

        # If all emails sent or cancelled, complete workflow
        all_done = all(
            e.status in ("sent", "failed", "cancelled") for e in all_emails
        )
        if all_done:
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()

        await self.db.commit()

    async def update_on_email_failed(
        self, email_id: UUID, error_message: str
    ) -> None:
        """Update workflow state when email fails.

        Args:
            email_id: ScheduledEmail UUID
            error_message: Error description

        Raises:
            ValueError: If email not found
        """
        # Load email
        result = await self.db.execute(
            select(ScheduledEmail).where(ScheduledEmail.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email not found: {email_id}")

        # Update email status
        email.status = "failed"
        email.retry_count += 1

        # Create failure event
        event = EmailEvent(
            email_id=email_id,
            event_type="failed",
            event_data={"error": error_message},
            occurred_at=datetime.utcnow(),
        )
        self.db.add(event)

        await self.db.commit()

    async def record_email_event(
        self,
        email_id: UUID,
        event_type: str,
        event_data: Optional[dict] = None,
    ) -> EmailEvent:
        """Record email event from SendGrid webhook.

        Args:
            email_id: ScheduledEmail UUID
            event_type: Event type (delivered, opened, clicked, etc.)
            event_data: Additional event data

        Returns:
            Created EmailEvent

        Raises:
            ValueError: If email not found or invalid event type
        """
        # Validate event type
        valid_events = {
            "sent",
            "delivered",
            "opened",
            "clicked",
            "bounced",
            "complained",
            "unsubscribed",
        }
        if event_type not in valid_events:
            raise ValueError(
                f"Invalid event type: {event_type}. Must be one of {valid_events}"
            )

        # Verify email exists
        result = await self.db.execute(
            select(ScheduledEmail).where(ScheduledEmail.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email not found: {email_id}")

        # Create event
        event = EmailEvent(
            email_id=email_id,
            event_type=event_type,
            event_data=event_data or {},
            occurred_at=datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.commit()

        return event

    async def get_workflow_metrics(self, workflow_id: UUID) -> dict:
        """Get engagement metrics for workflow.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Dict with metrics (sent, delivered, opened, clicked, etc.)

        Raises:
            ValueError: If workflow not found
        """
        # Verify workflow exists
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Get all emails in workflow
        result = await self.db.execute(
            select(ScheduledEmail).where(
                ScheduledEmail.workflow_id == workflow_id
            )
        )
        emails = result.scalars().all()

        # Count email statuses
        email_stats = {
            "total": len(emails),
            "pending": sum(1 for e in emails if e.status == "pending"),
            "sent": sum(1 for e in emails if e.status == "sent"),
            "failed": sum(1 for e in emails if e.status == "failed"),
            "cancelled": sum(1 for e in emails if e.status == "cancelled"),
        }

        # Get events for all emails
        email_ids = [e.id for e in emails]
        if email_ids:
            result = await self.db.execute(
                select(EmailEvent).where(EmailEvent.email_id.in_(email_ids))
            )
            events = result.scalars().all()

            # Count event types
            event_stats = {
                "delivered": sum(
                    1 for e in events if e.event_type == "delivered"
                ),
                "opened": sum(1 for e in events if e.event_type == "opened"),
                "clicked": sum(1 for e in events if e.event_type == "clicked"),
                "bounced": sum(1 for e in events if e.event_type == "bounced"),
                "complained": sum(
                    1 for e in events if e.event_type == "complained"
                ),
                "unsubscribed": sum(
                    1 for e in events if e.event_type == "unsubscribed"
                ),
            }

            # Calculate rates
            sent_count = email_stats["sent"]
            if sent_count > 0:
                event_stats["delivery_rate"] = (
                    event_stats["delivered"] / sent_count
                )
                event_stats["open_rate"] = (
                    event_stats["opened"] / sent_count
                )
                event_stats["click_rate"] = (
                    event_stats["clicked"] / sent_count
                )
                event_stats["bounce_rate"] = (
                    event_stats["bounced"] / sent_count
                )
            else:
                event_stats["delivery_rate"] = 0.0
                event_stats["open_rate"] = 0.0
                event_stats["click_rate"] = 0.0
                event_stats["bounce_rate"] = 0.0
        else:
            event_stats = {
                "delivered": 0,
                "opened": 0,
                "clicked": 0,
                "bounced": 0,
                "complained": 0,
                "unsubscribed": 0,
                "delivery_rate": 0.0,
                "open_rate": 0.0,
                "click_rate": 0.0,
                "bounce_rate": 0.0,
            }

        return {
            "workflow_id": str(workflow_id),
            "tier": workflow.tier,
            "status": workflow.status,
            "emails": email_stats,
            "engagement": event_stats,
        }

    async def get_email_history(self, email_id: UUID) -> dict:
        """Get complete event history for an email.

        Args:
            email_id: ScheduledEmail UUID

        Returns:
            Dict with email details and event timeline

        Raises:
            ValueError: If email not found
        """
        # Load email
        result = await self.db.execute(
            select(ScheduledEmail).where(ScheduledEmail.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email not found: {email_id}")

        # Load events
        result = await self.db.execute(
            select(EmailEvent)
            .where(EmailEvent.email_id == email_id)
            .order_by(EmailEvent.occurred_at)
        )
        events = result.scalars().all()

        return {
            "email_id": str(email.id),
            "workflow_id": str(email.workflow_id),
            "template_id": email.template_id,
            "recipient": email.recipient_email,
            "subject": email.subject,
            "scheduled_at": email.scheduled_at.isoformat(),
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "status": email.status,
            "retry_count": email.retry_count,
            "sendgrid_message_id": email.sendgrid_message_id,
            "events": [
                {
                    "type": e.event_type,
                    "occurred_at": e.occurred_at.isoformat(),
                    "data": e.event_data,
                }
                for e in events
            ],
        }

    async def retry_failed_email(self, email_id: UUID) -> None:
        """Retry sending a failed email.

        Args:
            email_id: ScheduledEmail UUID

        Raises:
            ValueError: If email not found or not failed
        """
        # Load email
        result = await self.db.execute(
            select(ScheduledEmail).where(ScheduledEmail.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email not found: {email_id}")

        if email.status != "failed":
            raise ValueError(
                f"Email {email_id} is not failed (status: {email.status})"
            )

        # Reset to pending for retry
        email.status = "pending"
        email.scheduled_at = datetime.utcnow()  # Send immediately

        await self.db.commit()

    async def get_lead_email_history(self, lead_id: UUID) -> list[dict]:
        """Get all email workflows and emails for a lead.

        Args:
            lead_id: Lead UUID

        Returns:
            List of workflow summaries with emails
        """
        # Get all workflows for lead
        result = await self.db.execute(
            select(EmailWorkflow)
            .where(EmailWorkflow.lead_id == lead_id)
            .order_by(EmailWorkflow.created_at.desc())
        )
        workflows = result.scalars().all()

        history = []
        for workflow in workflows:
            # Get emails for workflow
            result = await self.db.execute(
                select(ScheduledEmail)
                .where(ScheduledEmail.workflow_id == workflow.id)
                .order_by(ScheduledEmail.scheduled_at)
            )
            emails = result.scalars().all()

            history.append(
                {
                    "workflow_id": str(workflow.id),
                    "tier": workflow.tier,
                    "status": workflow.status,
                    "started_at": workflow.started_at.isoformat()
                    if workflow.started_at
                    else None,
                    "completed_at": workflow.completed_at.isoformat()
                    if workflow.completed_at
                    else None,
                    "emails": [
                        {
                            "email_id": str(e.id),
                            "template_id": e.template_id,
                            "subject": e.subject,
                            "scheduled_at": e.scheduled_at.isoformat(),
                            "sent_at": e.sent_at.isoformat()
                            if e.sent_at
                            else None,
                            "status": e.status,
                        }
                        for e in emails
                    ],
                }
            )

        return history
