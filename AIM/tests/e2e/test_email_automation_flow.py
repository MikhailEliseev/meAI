"""E2E Test: Email Automation Flow

Tests complete email automation journey from trigger to delivery.

Flow:
1. Lead captured → Workflow triggered
2. Emails scheduled based on tier
3. Emails sent via SendGrid
4. Events tracked (open, click, bounce)
5. Workflow completion

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.email_workflow import EmailWorkflow
from aim.models.email_event import EmailEvent
from aim.services.email.workflow_service import WorkflowService
from aim.services.email.sendgrid_client import SendGridClient


@pytest.mark.asyncio
async def test_hot_tier_email_workflow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test Hot tier email workflow (1 instant email)."""
    # Step 1: Create Hot lead
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Иван Петров",
        "email": "ivan.petrov@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Премиум Клиника",
        "city": "Москва",
        "services": ["implants", "orthodontics"],
        "monthly_budget": 500000,
        "current_marketing": ["yandex_direct", "instagram"],
        "pain_points": ["low_conversion", "high_cpc"],
    })
    assert lead_response.status_code == 201
    lead_id = lead_response.json()["lead_id"]
    assert lead_response.json()["tier"] == "hot"

    # Step 2: Verify workflow created
    workflow_service = WorkflowService(db)
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert len(workflows) == 1

    workflow = workflows[0]
    assert workflow.tier == "hot"
    assert workflow.total_emails == 1
    assert workflow.emails_sent == 0
    assert workflow.status == "active"

    # Step 3: Trigger email send (async task)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {
            "message_id": "sendgrid_123",
            "status": "sent",
        }

        # Simulate async task execution
        await workflow_service.send_scheduled_emails()

        # Verify email sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["to_email"] == "ivan.petrov@clinic.ru"
        assert "Премиум Клиника" in call_args["subject"]

    # Step 4: Verify workflow updated
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    workflow = workflows[0]
    assert workflow.emails_sent == 1
    assert workflow.status == "completed"

    # Step 5: Simulate webhook events (open, click)
    # Open event
    open_event_response = await client.post("/api/email/webhook/sendgrid", json={
        "event": "open",
        "email": "ivan.petrov@clinic.ru",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "sendgrid_123",
    })
    assert open_event_response.status_code == 200

    # Click event
    click_event_response = await client.post("/api/email/webhook/sendgrid", json={
        "event": "click",
        "email": "ivan.petrov@clinic.ru",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "sendgrid_123",
        "url": "https://iamaim.ru/onboarding",
    })
    assert click_event_response.status_code == 200

    # Step 6: Verify events tracked
    from aim.services.email.event_service import EventService
    event_service = EventService(db)
    events = await event_service.get_events_by_workflow(workflow.id)

    assert len(events) >= 2
    event_types = [e.event_type for e in events]
    assert "open" in event_types
    assert "click" in event_types


@pytest.mark.asyncio
async def test_warm_tier_email_workflow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test Warm tier email workflow (3 emails: day 0, 3, 7)."""
    # Step 1: Create Warm lead
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Мария Сидорова",
        "email": "maria@dental-center.ru",
        "phone": "+79997654321",
        "clinic_name": "Дентал Центр",
        "city": "Санкт-Петербург",
        "services": ["therapy", "hygiene"],
        "monthly_budget": 150000,
        "current_marketing": ["instagram"],
    })
    assert lead_response.status_code == 201
    lead_id = lead_response.json()["lead_id"]
    assert lead_response.json()["tier"] == "warm"

    # Step 2: Verify workflow created
    workflow_service = WorkflowService(db)
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert len(workflows) == 1

    workflow = workflows[0]
    assert workflow.tier == "warm"
    assert workflow.total_emails == 3
    assert workflow.emails_sent == 0
    assert workflow.status == "active"

    # Step 3: Send first email (day 0)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg_1", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert workflows[0].emails_sent == 1

    # Step 4: Simulate day 3 (send second email)
    workflow.next_email_at = datetime.utcnow() - timedelta(hours=1)
    await db.commit()

    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg_2", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert workflows[0].emails_sent == 2

    # Step 5: Simulate day 7 (send third email)
    workflow.next_email_at = datetime.utcnow() - timedelta(hours=1)
    await db.commit()

    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg_3", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    # Step 6: Verify workflow completed
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    workflow = workflows[0]
    assert workflow.emails_sent == 3
    assert workflow.status == "completed"


@pytest.mark.asyncio
async def test_cold_tier_email_workflow_weekly_digest(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test Cold tier email workflow (weekly digest)."""
    # Step 1: Create Cold lead
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Иван Иванов",
        "email": "ivan@example.com",
        "phone": "+79991111111",
        "clinic_name": "Клиника",
        "city": "Воронеж",
        "services": ["consultation"],
        "monthly_budget": 30000,
    })
    assert lead_response.status_code == 201
    lead_id = lead_response.json()["lead_id"]
    assert lead_response.json()["tier"] == "cold"

    # Step 2: Verify workflow created
    workflow_service = WorkflowService(db)
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert len(workflows) == 1

    workflow = workflows[0]
    assert workflow.tier == "cold"
    assert workflow.schedule_type == "weekly_digest"
    assert workflow.status == "active"

    # Step 3: Verify no immediate email sent
    assert workflow.emails_sent == 0

    # Step 4: Simulate weekly digest trigger
    workflow.next_email_at = datetime.utcnow() - timedelta(hours=1)
    await db.commit()

    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "digest_1", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    # Step 5: Verify digest sent
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    workflow = workflows[0]
    assert workflow.emails_sent == 1
    assert workflow.next_email_at > datetime.utcnow()  # Next week scheduled


@pytest.mark.asyncio
async def test_email_bounce_handling(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email bounce event handling."""
    # Step 1: Create lead and workflow
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Test",
        "email": "invalid@bounced.com",
        "phone": "+79991234567",
        "clinic_name": "Test Clinic",
        "city": "Москва",
        "services": ["therapy"],
        "monthly_budget": 100000,
    })
    lead_id = lead_response.json()["lead_id"]

    # Step 2: Send email (simulate bounce)
    workflow_service = WorkflowService(db)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg_bounce", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    # Step 3: Receive bounce webhook
    bounce_response = await client.post("/api/email/webhook/sendgrid", json={
        "event": "bounce",
        "email": "invalid@bounced.com",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "msg_bounce",
        "reason": "550 5.1.1 User unknown",
        "type": "hard",
    })
    assert bounce_response.status_code == 200

    # Step 4: Verify workflow paused
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    workflow = workflows[0]
    assert workflow.status == "paused"  # Hard bounce pauses workflow

    # Step 5: Verify bounce event tracked
    from aim.services.email.event_service import EventService
    event_service = EventService(db)
    events = await event_service.get_events_by_workflow(workflow.id)

    bounce_events = [e for e in events if e.event_type == "bounce"]
    assert len(bounce_events) == 1
    assert bounce_events[0].metadata["bounce_type"] == "hard"


@pytest.mark.asyncio
async def test_email_unsubscribe_handling(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email unsubscribe event handling."""
    # Step 1: Create lead and workflow
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Test",
        "email": "test@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Test Clinic",
        "city": "Москва",
        "services": ["therapy"],
        "monthly_budget": 100000,
    })
    lead_id = lead_response.json()["lead_id"]

    # Step 2: Send email
    workflow_service = WorkflowService(db)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg_unsub", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    # Step 3: Receive unsubscribe webhook
    unsub_response = await client.post("/api/email/webhook/sendgrid", json={
        "event": "unsubscribe",
        "email": "test@clinic.ru",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "msg_unsub",
    })
    assert unsub_response.status_code == 200

    # Step 4: Verify workflow stopped
    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    workflow = workflows[0]
    assert workflow.status == "stopped"  # Unsubscribe stops workflow

    # Step 5: Verify no more emails sent
    workflow.next_email_at = datetime.utcnow() - timedelta(hours=1)
    await db.commit()

    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        await workflow_service.send_scheduled_emails()
        mock_send.assert_not_called()  # No email sent


@pytest.mark.asyncio
async def test_email_rate_limiting(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email rate limiting."""
    # Step 1: Create multiple leads
    lead_ids = []
    for i in range(20):
        lead_response = await client.post("/api/leads/capture", json={
            "name": f"Dr. Test {i}",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            "services": ["therapy"],
            "monthly_budget": 100000,
        })
        lead_ids.append(lead_response.json()["lead_id"])

    # Step 2: Try to send all emails at once
    workflow_service = WorkflowService(db)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg", "status": "sent"}
        await workflow_service.send_scheduled_emails()

        # Verify rate limiting applied (max 10 emails per batch)
        assert mock_send.call_count <= 10


@pytest.mark.asyncio
async def test_email_template_personalization(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email template personalization."""
    # Step 1: Create lead with specific data
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Иван Петров",
        "email": "ivan@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Премиум Клиника",
        "city": "Москва",
        "services": ["implants"],
        "monthly_budget": 300000,
        "pain_points": ["low_conversion"],
    })
    lead_id = lead_response.json()["lead_id"]

    # Step 2: Send email and verify personalization
    workflow_service = WorkflowService(db)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg", "status": "sent"}
        await workflow_service.send_scheduled_emails()

        # Verify personalization in email content
        call_args = mock_send.call_args[1]
        assert "Иван" in call_args["html_content"]  # Name
        assert "Премиум Клиника" in call_args["html_content"]  # Clinic
        assert "Москва" in call_args["html_content"]  # City
        assert "имплант" in call_args["html_content"].lower()  # Service
        assert "конверси" in call_args["html_content"].lower()  # Pain point


@pytest.mark.asyncio
async def test_email_metrics_aggregation(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email metrics aggregation."""
    # Step 1: Create lead and send email
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Test",
        "email": "test@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Test Clinic",
        "city": "Москва",
        "services": ["therapy"],
        "monthly_budget": 100000,
    })
    lead_id = lead_response.json()["lead_id"]

    workflow_service = WorkflowService(db)
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    # Step 2: Simulate events
    await client.post("/api/email/webhook/sendgrid", json={
        "event": "delivered",
        "email": "test@clinic.ru",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "msg",
    })

    await client.post("/api/email/webhook/sendgrid", json={
        "event": "open",
        "email": "test@clinic.ru",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "msg",
    })

    await client.post("/api/email/webhook/sendgrid", json={
        "event": "click",
        "email": "test@clinic.ru",
        "timestamp": int(datetime.utcnow().timestamp()),
        "sg_message_id": "msg",
        "url": "https://iamaim.ru",
    })

    # Step 3: Get metrics
    metrics_response = await client.get("/api/email/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()

    assert metrics["total_sent"] >= 1
    assert metrics["total_delivered"] >= 1
    assert metrics["total_opened"] >= 1
    assert metrics["total_clicked"] >= 1
    assert metrics["open_rate"] > 0
    assert metrics["click_rate"] > 0
