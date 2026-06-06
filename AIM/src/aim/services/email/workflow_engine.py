"""Email Workflow Engine

Manages multi-step email sequences for leads based on their tier.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.models import EmailWorkflow, Lead, ScheduledEmail
from src.aim.services.email.template_renderer import TemplateRenderer


class WorkflowEngine:
    """Manages email workflow lifecycle and scheduling.

    Responsibilities:
    - Start workflows for leads based on tier
    - Schedule emails in multi-step sequences
    - Process scheduled emails (cron job)
    - Update workflow state

    Example:
        engine = WorkflowEngine(db_session)
        workflow = await engine.trigger_workflow(
            lead_id=lead.id,
            tier="warm"
        )
    """

    # Workflow definitions per tier
    WORKFLOW_DEFINITIONS = {
        "hot": [
            {
                "template_id": "hot_instant",
                "delay_minutes": 0,  # Instant
            }
        ],
        "warm": [
            {
                "template_id": "warm_day0",
                "delay_minutes": 0,  # Instant
            },
            {
                "template_id": "warm_day3",
                "delay_minutes": 3 * 24 * 60,  # 3 days
            },
            {
                "template_id": "warm_day7",
                "delay_minutes": 7 * 24 * 60,  # 7 days
            },
        ],
        "cold": [
            {
                "template_id": "cold_weekly",
                "delay_minutes": 0,  # First digest instant
            }
            # Weekly digest continues via cron (not workflow-based)
        ],
    }

    def __init__(self, db: AsyncSession):
        """Initialize workflow engine.

        Args:
            db: Database session
        """
        self.db = db
        self.renderer = TemplateRenderer()

    async def trigger_workflow(
        self, lead_id: UUID, tier: str, start_immediately: bool = True
    ) -> EmailWorkflow:
        """Start email workflow for a lead.

        Args:
            lead_id: Lead UUID
            tier: Lead tier (hot/warm/cold)
            start_immediately: Whether to schedule first email now

        Returns:
            Created EmailWorkflow

        Raises:
            ValueError: If tier is invalid or lead not found
        """
        # Validate tier
        if tier not in self.WORKFLOW_DEFINITIONS:
            raise ValueError(f"Invalid tier: {tier}. Must be hot/warm/cold")

        # Load lead
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        # Check if workflow already exists
        result = await self.db.execute(
            select(EmailWorkflow).where(
                EmailWorkflow.lead_id == lead_id,
                EmailWorkflow.status == "active",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(
                f"Active workflow already exists for lead {lead_id}"
            )

        # Create workflow
        workflow = EmailWorkflow(
            id=uuid4(),
            lead_id=lead_id,
            tier=tier,
            status="active",
            current_step=0,
            started_at=datetime.now(timezone.utc) if start_immediately else None,
        )
        self.db.add(workflow)
        await self.db.flush()

        # Schedule emails
        if start_immediately:
            await self._schedule_workflow_emails(workflow, lead)

        await self.db.commit()
        return workflow

    async def _schedule_workflow_emails(
        self, workflow: EmailWorkflow, lead: Lead
    ) -> None:
        """Schedule all emails in workflow sequence.

        Args:
            workflow: EmailWorkflow to schedule
            lead: Lead receiving emails
        """
        workflow_def = self.WORKFLOW_DEFINITIONS[workflow.tier]
        base_time = datetime.now(timezone.utc)

        for step_idx, step_def in enumerate(workflow_def):
            # Calculate send time
            delay_minutes = step_def["delay_minutes"]
            scheduled_at = base_time + timedelta(minutes=delay_minutes)

            # Render email content
            context = {
                "name": lead.name or "Коллега",
                "email": lead.email,
                "specialty": lead.specialty or "медицинская клиника",
                "service": "маркетинговые услуги",  # Default service
            }

            html_content, text_content = await self.renderer.render(
                template_id=step_def["template_id"],
                context=context,
                generate_ai_content=True,
            )

            subject = self.renderer.render_subject(
                template_id=step_def["template_id"], context=context
            )

            # Create scheduled email
            scheduled_email = ScheduledEmail(
                id=uuid4(),
                workflow_id=workflow.id,
                template_id=step_def["template_id"],
                recipient_email=lead.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                scheduled_at=scheduled_at,
                status="pending",
            )
            self.db.add(scheduled_email)

    async def schedule_email(
        self,
        workflow_id: UUID,
        template_id: str,
        recipient_email: str,
        context: dict,
        send_at: datetime,
    ) -> ScheduledEmail:
        """Schedule a single email (for manual/ad-hoc sends).

        Args:
            workflow_id: Parent workflow UUID
            template_id: Template identifier
            recipient_email: Recipient email address
            context: Template variables
            send_at: When to send

        Returns:
            Created ScheduledEmail

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

        # Render email
        html_content, text_content = await self.renderer.render(
            template_id=template_id,
            context=context,
            generate_ai_content=True,
        )

        subject = self.renderer.render_subject(
            template_id=template_id, context=context
        )

        # Create scheduled email
        scheduled_email = ScheduledEmail(
            id=uuid4(),
            workflow_id=workflow_id,
            template_id=template_id,
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            scheduled_at=send_at,
            status="pending",
        )
        self.db.add(scheduled_email)
        await self.db.commit()

        return scheduled_email

    async def process_scheduled_emails(
        self, batch_size: int = 100
    ) -> list[ScheduledEmail]:
        """Process emails scheduled for sending (cron job).

        Finds emails with scheduled_at <= now and status=pending,
        marks them as ready for sending.

        Args:
            batch_size: Max emails to process per run

        Returns:
            List of emails ready to send
        """
        now = datetime.now(timezone.utc)

        # Find due emails
        result = await self.db.execute(
            select(ScheduledEmail)
            .where(
                ScheduledEmail.scheduled_at <= now,
                ScheduledEmail.status == "pending",
            )
            .limit(batch_size)
        )
        due_emails = result.scalars().all()

        # Mark as ready (actual sending happens in EmailSender)
        ready_emails = []
        for email in due_emails:
            # Check if workflow is still active
            result = await self.db.execute(
                select(EmailWorkflow).where(
                    EmailWorkflow.id == email.workflow_id
                )
            )
            workflow = result.scalar_one_or_none()

            if workflow and workflow.status == "active":
                ready_emails.append(email)
            else:
                # Workflow cancelled/completed, cancel email
                email.status = "cancelled"

        await self.db.commit()
        return ready_emails

    async def pause_workflow(self, workflow_id: UUID) -> None:
        """Pause workflow (stop sending emails).

        Args:
            workflow_id: Workflow UUID

        Raises:
            ValueError: If workflow not found
        """
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow.status = "paused"
        await self.db.commit()

    async def resume_workflow(self, workflow_id: UUID) -> None:
        """Resume paused workflow.

        Args:
            workflow_id: Workflow UUID

        Raises:
            ValueError: If workflow not found or not paused
        """
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if workflow.status != "paused":
            raise ValueError(
                f"Workflow {workflow_id} is not paused (status: {workflow.status})"
            )

        workflow.status = "active"
        await self.db.commit()

    async def complete_workflow(self, workflow_id: UUID) -> None:
        """Mark workflow as completed.

        Args:
            workflow_id: Workflow UUID

        Raises:
            ValueError: If workflow not found
        """
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow.status = "completed"
        workflow.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def cancel_workflow(self, workflow_id: UUID) -> None:
        """Cancel workflow and all pending emails.

        Args:
            workflow_id: Workflow UUID

        Raises:
            ValueError: If workflow not found
        """
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Cancel workflow
        workflow.status = "cancelled"
        workflow.completed_at = datetime.now(timezone.utc)

        # Cancel pending emails
        result = await self.db.execute(
            select(ScheduledEmail).where(
                ScheduledEmail.workflow_id == workflow_id,
                ScheduledEmail.status == "pending",
            )
        )
        pending_emails = result.scalars().all()
        for email in pending_emails:
            email.status = "cancelled"

        await self.db.commit()

    async def get_workflow_status(
        self, workflow_id: UUID
    ) -> Optional[dict]:
        """Get workflow status and progress.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Dict with workflow status, or None if not found
        """
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            return None

        # Count emails by status
        result = await self.db.execute(
            select(ScheduledEmail).where(
                ScheduledEmail.workflow_id == workflow_id
            )
        )
        emails = result.scalars().all()

        email_stats = {
            "total": len(emails),
            "pending": sum(1 for e in emails if e.status == "pending"),
            "sent": sum(1 for e in emails if e.status == "sent"),
            "failed": sum(1 for e in emails if e.status == "failed"),
            "cancelled": sum(1 for e in emails if e.status == "cancelled"),
        }

        return {
            "workflow_id": str(workflow.id),
            "lead_id": str(workflow.lead_id),
            "tier": workflow.tier,
            "status": workflow.status,
            "current_step": workflow.current_step,
            "started_at": workflow.started_at.isoformat()
            if workflow.started_at
            else None,
            "completed_at": workflow.completed_at.isoformat()
            if workflow.completed_at
            else None,
            "emails": email_stats,
        }
