"""Tests for WebhookHandler

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from src.aim.models import EmailEvent, EmailWorkflow, Lead, ScheduledEmail
from src.aim.services.email.webhook_handler import WebhookHandler


@pytest.fixture
async def lead(db_session):
    """Create test lead."""
    from datetime import datetime, timezone
    from src.aim.utils.encryption import FieldEncryption

    email = "ivan@example.com"
    encryptor = FieldEncryption()

    lead = Lead(
        id="lead_20260516_test123",
        name_encrypted=encryptor.encrypt("Иван Петров"),
        phone_encrypted=encryptor.encrypt("+79991234567"),
        email_encrypted=encryptor.encrypt(email),
        email_hash=Lead.hash_email(email),
        clinic_name_encrypted=encryptor.encrypt("Стоматология Улыбка"),
        specialty="стоматология",
        fz152_consent=True,
        fz152_consent_timestamp=datetime.now(timezone.utc),
        fz152_consent_ip="127.0.0.1",
        source="test",
        tier="hot",
        score=85,
    )
    db_session.add(lead)
    await db_session.commit()
    return lead


@pytest.fixture
async def workflow(db_session, lead):
    """Create test workflow."""
    workflow = EmailWorkflow(
        id=uuid4(),
        lead_id=lead.id,
        tier="hot",
        status="active",
        current_step=0,
        started_at=datetime.utcnow(),
    )
    db_session.add(workflow)
    await db_session.commit()
    return workflow


@pytest.fixture
async def scheduled_email(db_session, workflow):
    """Create test scheduled email."""
    email = ScheduledEmail(
        id=uuid4(),
        workflow_id=workflow.id,
        template_id="hot_instant",
        recipient_email="ivan@example.com",
        subject="Test",
        html_content="<p>Test</p>",
        text_content="Test",
        scheduled_at=datetime.utcnow(),
        status="sent",
        sent_at=datetime.utcnow(),
    )
    db_session.add(email)
    await db_session.commit()
    return email


@pytest.fixture
def webhook_handler(db_session):
    """Create WebhookHandler instance."""
    return WebhookHandler(db=db_session, webhook_secret="test_secret")


@pytest.mark.asyncio
async def test_verify_signature_valid(webhook_handler):
    """Test valid webhook signature verification."""
    import hmac
    import hashlib

    payload = b'{"event": "delivered"}'
    timestamp = "1234567890"

    # Generate valid signature
    signed_payload = timestamp.encode() + payload
    signature = hmac.new(
        b"test_secret",
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    # Verify
    valid = webhook_handler.verify_signature(payload, signature, timestamp)
    assert valid is True


@pytest.mark.asyncio
async def test_verify_signature_invalid(webhook_handler):
    """Test invalid webhook signature verification."""
    payload = b'{"event": "delivered"}'
    timestamp = "1234567890"
    signature = "invalid_signature"

    # Verify
    valid = webhook_handler.verify_signature(payload, signature, timestamp)
    assert valid is False


@pytest.mark.asyncio
async def test_verify_signature_no_secret(db_session):
    """Test signature verification without secret."""
    handler = WebhookHandler(db=db_session, webhook_secret=None)

    payload = b'{"event": "delivered"}'
    timestamp = "1234567890"
    signature = "any_signature"

    # Should pass without secret
    valid = handler.verify_signature(payload, signature, timestamp)
    assert valid is True


@pytest.mark.asyncio
async def test_process_delivered_event(
    webhook_handler, scheduled_email, db_session
):
    """Test processing delivered event."""
    events = [
        {
            "event": "delivered",
            "email_id": str(scheduled_email.id),
            "email": "ivan@example.com",
            "timestamp": 1234567890,
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 1
    assert stats["failed"] == 0

    # Check event recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    event = result.scalar_one()

    assert event.event_type == "delivered"
    assert event.event_data["email"] == "ivan@example.com"


@pytest.mark.asyncio
async def test_process_opened_event(
    webhook_handler, scheduled_email, db_session
):
    """Test processing opened event."""
    events = [
        {
            "event": "open",
            "email_id": str(scheduled_email.id),
            "email": "ivan@example.com",
            "timestamp": 1234567890,
            "useragent": "Mozilla/5.0",
            "ip": "192.168.1.1",
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 1

    # Check event recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    event = result.scalar_one()

    assert event.event_type == "opened"
    assert event.event_data["useragent"] == "Mozilla/5.0"
    assert event.event_data["ip"] == "192.168.1.1"


@pytest.mark.asyncio
async def test_process_clicked_event(
    webhook_handler, scheduled_email, db_session
):
    """Test processing clicked event."""
    events = [
        {
            "event": "click",
            "email_id": str(scheduled_email.id),
            "email": "ivan@example.com",
            "timestamp": 1234567890,
            "url": "https://iamaim.ru/consultation",
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 1

    # Check event recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    event = result.scalar_one()

    assert event.event_type == "clicked"
    assert event.event_data["url"] == "https://iamaim.ru/consultation"


@pytest.mark.asyncio
async def test_process_bounced_event(
    webhook_handler, scheduled_email, db_session
):
    """Test processing bounced event."""
    events = [
        {
            "event": "bounce",
            "email_id": str(scheduled_email.id),
            "email": "ivan@example.com",
            "timestamp": 1234567890,
            "reason": "550 5.1.1 User unknown",
            "response": "User not found",
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 1

    # Check event recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    event = result.scalar_one()

    assert event.event_type == "bounced"
    assert event.event_data["reason"] == "550 5.1.1 User unknown"


@pytest.mark.asyncio
async def test_process_spam_report_event(
    webhook_handler, scheduled_email, db_session
):
    """Test processing spam report event."""
    events = [
        {
            "event": "spam_report",
            "email_id": str(scheduled_email.id),
            "email": "ivan@example.com",
            "timestamp": 1234567890,
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 1

    # Check event recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    event = result.scalar_one()

    assert event.event_type == "complained"


@pytest.mark.asyncio
async def test_process_unsubscribe_event(
    webhook_handler, scheduled_email, db_session
):
    """Test processing unsubscribe event."""
    events = [
        {
            "event": "unsubscribe",
            "email_id": str(scheduled_email.id),
            "email": "ivan@example.com",
            "timestamp": 1234567890,
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 1

    # Check event recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    event = result.scalar_one()

    assert event.event_type == "unsubscribed"


@pytest.mark.asyncio
async def test_process_multiple_events(
    webhook_handler, scheduled_email, db_session
):
    """Test processing multiple events in batch."""
    events = [
        {
            "event": "delivered",
            "email_id": str(scheduled_email.id),
            "timestamp": 1234567890,
        },
        {
            "event": "open",
            "email_id": str(scheduled_email.id),
            "timestamp": 1234567891,
        },
        {
            "event": "click",
            "email_id": str(scheduled_email.id),
            "timestamp": 1234567892,
            "url": "https://iamaim.ru",
        },
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 3
    assert stats["failed"] == 0

    # Check all events recorded
    result = await db_session.execute(
        select(EmailEvent).where(EmailEvent.email_id == scheduled_email.id)
    )
    recorded_events = result.scalars().all()

    assert len(recorded_events) == 3
    event_types = {e.event_type for e in recorded_events}
    assert event_types == {"delivered", "opened", "clicked"}


@pytest.mark.asyncio
async def test_process_event_missing_email_id(webhook_handler):
    """Test processing event without email_id."""
    events = [
        {
            "event": "delivered",
            "email": "test@example.com",
            "timestamp": 1234567890,
        }
    ]

    stats = await webhook_handler.process_events(events)

    # Should not fail, just skip
    assert stats["processed"] == 0
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_process_event_invalid_email_id(webhook_handler):
    """Test processing event with invalid email_id."""
    events = [
        {
            "event": "delivered",
            "email_id": "not-a-uuid",
            "timestamp": 1234567890,
        }
    ]

    stats = await webhook_handler.process_events(events)

    assert stats["processed"] == 0
    assert stats["failed"] == 1


@pytest.mark.asyncio
async def test_process_event_unknown_type(
    webhook_handler, scheduled_email
):
    """Test processing event with unknown type."""
    events = [
        {
            "event": "unknown_event",
            "email_id": str(scheduled_email.id),
            "timestamp": 1234567890,
        }
    ]

    stats = await webhook_handler.process_events(events)

    # Should not fail, just skip
    assert stats["processed"] == 0
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_get_webhook_statistics(
    webhook_handler, scheduled_email, db_session
):
    """Test getting webhook statistics."""
    # Create events
    event_types = ["delivered", "opened", "clicked", "bounced"]
    for event_type in event_types:
        event = EmailEvent(
            email_id=scheduled_email.id,
            event_type=event_type,
            event_data={},
            occurred_at=datetime.utcnow(),
        )
        db_session.add(event)
    await db_session.commit()

    # Get statistics
    stats = await webhook_handler.get_webhook_statistics()

    assert stats["total"] == 4
    assert stats["delivered"] == 1
    assert stats["opened"] == 1
    assert stats["clicked"] == 1
    assert stats["bounced"] == 1


@pytest.mark.asyncio
async def test_get_webhook_url(webhook_handler):
    """Test getting webhook URL."""
    url = webhook_handler.get_webhook_url("https://iamaim.ru")
    assert url == "https://iamaim.ru/api/webhooks/sendgrid"


@pytest.mark.asyncio
async def test_get_webhook_setup_instructions(webhook_handler):
    """Test getting webhook setup instructions."""
    instructions = webhook_handler.get_webhook_setup_instructions(
        "https://iamaim.ru"
    )

    assert "SendGrid" in instructions
    assert "https://iamaim.ru/api/webhooks/sendgrid" in instructions
    assert "Event Webhook" in instructions
    assert "Delivered" in instructions
    assert "Opened" in instructions
