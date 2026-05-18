"""Workflow Service — unified email workflow management.

Wraps WorkflowEngine and EmailSender into a single service for E2E testing.
Part of: Phase 11 Sprint 4 - Task 4.1
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.email_workflow import EmailWorkflow
from aim.models.scheduled_email import ScheduledEmail
from aim.services.email.workflow_engine import WorkflowEngine
from aim.services.email.email_sender import EmailSender


class WorkflowService:
    """Unified email workflow service for E2E testing."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = WorkflowEngine(db)

    async def get_workflows_by_lead(self, lead_id: str) -> list[EmailWorkflow]:
        result = await self.db.execute(
            select(EmailWorkflow).where(EmailWorkflow.lead_id == lead_id)
        )
        return list(result.scalars().all())

    async def send_scheduled_emails(self):
        """Process and send due scheduled emails."""
        due_emails = await self.engine.process_scheduled_emails()
        sender = EmailSender(api_key="test_key", db=self.db)
        for email in due_emails:
            await sender.send_email(email.id)
        await self.db.commit()
