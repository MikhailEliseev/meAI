"""E2E Test: Email Automation Flow

Tests complete email automation journey from trigger to delivery.

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.models.email_workflow import EmailWorkflow
from src.aim.models.email_event import EmailEvent
from src.aim.models.scheduled_email import ScheduledEmail
from src.aim.services.email.workflow_service import WorkflowService
from src.aim.services.email.email_sender import EmailSender


def _make_lead_data(name, email, phone, clinic, **extra):
    """Build valid lead capture payload."""
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "clinic_name": clinic,
        "specialty": "dentistry",
        "fz152_consent": True,
        "recaptcha_token": f"test_token_{email.split('@')[0]}",
        **extra,
    }


@pytest.mark.asyncio
async def test_email_workflow_created_on_lead_capture(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test that capturing a lead creates an email workflow."""
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Иван Петров", "ivan.petrov@clinic.ru", "+79991234567", "Премиум Клиника",
        message="Клиника в Москве, имплантация, бюджет 500000",
        utm_source="yandex", utm_medium="cpc",
    ))
    assert resp.status_code == 201
    lead_id = resp.json()["lead_id"]

    # Verify workflow exists for lead
    result = await db.execute(
        select(EmailWorkflow).where(EmailWorkflow.lead_id == lead_id)
    )
    workflows = result.scalars().all()
    assert len(workflows) == 1
    assert workflows[0].tier in ("hot", "warm", "cold")
    assert workflows[0].status == "active"


@pytest.mark.asyncio
async def test_email_scheduled_on_lead_capture(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test that capturing a lead schedules emails via workflow."""
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Иван Петров", "ivan.petrov@clinic.ru", "+79991234567", "Премиум Клиника",
        message="Клиника в Москве, имплантация, бюджет 500000",
        utm_source="yandex", utm_medium="cpc",
    ))
    assert resp.status_code == 201
    lead_id = resp.json()["lead_id"]

    # Get workflow
    result = await db.execute(
        select(EmailWorkflow).where(EmailWorkflow.lead_id == lead_id)
    )
    workflow = result.scalar_one()

    # Verify scheduled emails exist
    result = await db.execute(
        select(ScheduledEmail).where(ScheduledEmail.workflow_id == workflow.id)
    )
    emails = result.scalars().all()
    assert len(emails) >= 1
    assert emails[0].status in ("pending", "sent")
    assert emails[0].recipient_email == "ivan.petrov@clinic.ru"


@pytest.mark.asyncio
async def test_email_sending_mocked(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email sending with SendGrid mocked."""
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Test", "test@clinic.ru", "+79991234567", "Test Clinic",
    ))
    assert resp.status_code == 201
    lead_id = resp.json()["lead_id"]

    workflow_service = WorkflowService(db)
    with patch.object(EmailSender, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await workflow_service.send_scheduled_emails()
        assert mock_send.called
        # Each call passes an email_id UUID
        call_arg = mock_send.call_args[0][0]
        assert isinstance(call_arg, type(uuid4()))


@pytest.mark.asyncio
async def test_webhook_open_and_click_events(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test SendGrid webhook processing for open and click events."""
    # Create lead
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Иван Петров", "ivan.petrov@clinic.ru", "+79991234567", "Премиум Клиника",
    ))
    assert resp.status_code == 201
    lead_id = resp.json()["lead_id"]

    # Send emails to get a valid sendgrid_message_id
    workflow_service = WorkflowService(db)
    with patch.object(EmailSender, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await workflow_service.send_scheduled_emails()

    # Get scheduled email
    result = await db.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.recipient_email == "ivan.petrov@clinic.ru"
        )
    )
    email = result.scalar_one()
    email_id = str(email.id)

    # Simulate open event
    open_resp = await client.post("/api/email/webhook/sendgrid", json=[{
        "event": "open",
        "email": "ivan.petrov@clinic.ru",
        "email_id": email_id,
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
    }])
    assert open_resp.status_code == 200

    # Simulate click event
    click_resp = await client.post("/api/email/webhook/sendgrid", json=[{
        "event": "click",
        "email": "ivan.petrov@clinic.ru",
        "email_id": email_id,
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "url": "https://iamaim.ru",
    }])
    assert click_resp.status_code == 200


@pytest.mark.asyncio
async def test_webhook_bounce_handling(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test SendGrid bounce event handling."""
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Test", "invalid@bounced.com", "+79991234567", "Test Clinic",
    ))
    assert resp.status_code == 201

    workflow_service = WorkflowService(db)
    with patch.object(EmailSender, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await workflow_service.send_scheduled_emails()

    result = await db.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.recipient_email == "invalid@bounced.com"
        )
    )
    email = result.scalar_one()

    bounce_resp = await client.post("/api/email/webhook/sendgrid", json=[{
        "event": "bounce",
        "email": "invalid@bounced.com",
        "email_id": str(email.id),
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "reason": "550 5.1.1 User unknown",
    }])
    assert bounce_resp.status_code == 200

    # Verify bounce event recorded
    result = await db.execute(
        select(EmailEvent).where(
            EmailEvent.email_id == email.id,
            EmailEvent.event_type == "bounced",
        )
    )
    events = result.scalars().all()
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_webhook_unsubscribe_handling(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test SendGrid unsubscribe event handling."""
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Test", "unsub@clinic.ru", "+79991234567", "Test Clinic",
    ))
    assert resp.status_code == 201

    workflow_service = WorkflowService(db)
    with patch.object(EmailSender, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await workflow_service.send_scheduled_emails()

    result = await db.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.recipient_email == "unsub@clinic.ru"
        )
    )
    email = result.scalar_one()

    unsub_resp = await client.post("/api/email/webhook/sendgrid", json=[{
        "event": "unsubscribe",
        "email": "unsub@clinic.ru",
        "email_id": str(email.id),
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
    }])
    assert unsub_resp.status_code == 200

    result = await db.execute(
        select(EmailEvent).where(
            EmailEvent.email_id == email.id,
            EmailEvent.event_type == "unsubscribed",
        )
    )
    events = result.scalars().all()
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_email_metrics_endpoint(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email metrics aggregation endpoint."""
    resp = await client.post("/api/leads/capture", json=_make_lead_data(
        "Dr. Test", "metrics@clinic.ru", "+79991234567", "Test Clinic",
    ))
    assert resp.status_code == 201

    workflow_service = WorkflowService(db)
    with patch.object(EmailSender, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await workflow_service.send_scheduled_emails()

    # Send webhook events
    result = await db.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.recipient_email == "metrics@clinic.ru"
        )
    )
    email = result.scalar_one()
    eid = str(email.id)
    ts = int(datetime.now(timezone.utc).timestamp())

    await client.post("/api/email/webhook/sendgrid", json=[
        {"event": "delivered", "email": "metrics@clinic.ru", "email_id": eid, "timestamp": ts},
    ])
    await client.post("/api/email/webhook/sendgrid", json=[
        {"event": "open", "email": "metrics@clinic.ru", "email_id": eid, "timestamp": ts},
    ])
    await client.post("/api/email/webhook/sendgrid", json=[
        {"event": "click", "email": "metrics@clinic.ru", "email_id": eid, "timestamp": ts, "url": "https://iamaim.ru"},
    ])

    metrics_resp = await client.get("/api/email/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_sent"] >= 1
    assert metrics["total_delivered"] >= 1
    assert metrics["total_opened"] >= 1
    assert metrics["total_clicked"] >= 1


@pytest.mark.asyncio
async def test_email_rate_limiting_lead_capture(
    client: AsyncClient,
):
    """Test rate limiting on lead capture prevents excessive email creation."""
    responses = []
    for i in range(11):
        resp = await client.post("/api/leads/capture", json=_make_lead_data(
            f"Dr. Test {i}", f"test{i}@clinic.ru", "+79991234567", "Test Clinic",
        ))
        responses.append(resp)

    successful = [r for r in responses if r.status_code == 201]
    assert len(successful) == 10
    assert responses[10].status_code == 429
