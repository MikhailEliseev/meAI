"""Email API Endpoints — webhook handler and metrics.

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.database import get_db
from aim.models.email_event import EmailEvent
from aim.models.scheduled_email import ScheduledEmail
from aim.services.email.webhook_handler import WebhookHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


class SendGridEvent(BaseModel):
    event: str
    email: str
    timestamp: int
    sg_message_id: str
    url: Optional[str] = None
    reason: Optional[str] = None
    type: Optional[str] = None


@router.post("/webhook/sendgrid")
async def sendgrid_webhook(
    events: list[dict],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle SendGrid webhook events."""
    handler = WebhookHandler(db)
    await handler.process_events(events)
    return {"status": "ok"}


@router.get("/metrics")
async def email_metrics(db: AsyncSession = Depends(get_db)):
    """Get email metrics."""
    total_sent_result = await db.execute(select(func.count(ScheduledEmail.id)))
    total_sent = total_sent_result.scalar() or 0

    total_delivered_result = await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.event_type == "delivered")
    )
    total_delivered = total_delivered_result.scalar() or 0

    total_opened_result = await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.event_type == "opened")
    )
    total_opened = total_opened_result.scalar() or 0

    total_clicked_result = await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.event_type == "clicked")
    )
    total_clicked = total_clicked_result.scalar() or 0

    return {
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
        "open_rate": (total_opened / total_sent * 100) if total_sent > 0 else 0,
        "click_rate": (total_clicked / total_sent * 100) if total_sent > 0 else 0,
    }
