"""Tests for EmailSender

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.aim.models import EmailWorkflow, Lead, ScheduledEmail
from src.aim.services.email.email_sender import EmailSender


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
        subject="Ваш запрос получен",
        html_content="<p>Здравствуйте, Иван!</p>",
        text_content="Здравствуйте, Иван!",
        scheduled_at=datetime.utcnow(),
        status="pending",
    )
    db_session.add(email)
    await db_session.commit()
    return email


@pytest.fixture
def email_sender(db_session):
    """Create EmailSender instance with mocked SendGrid client."""
    with patch("src.aim.services.email.email_sender.SendGridAPIClient") as mock_sg:
        # Mock the client structure
        mock_client = MagicMock()
        mock_sg.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            db=db_session,
            from_email="test@iamaim.ru",
            from_name="Test Sender",
        )
        return sender


@pytest.mark.asyncio
async def test_send_email_success(email_sender, scheduled_email, db_session):
    """Test successful email sending."""
    # Mock SendGrid response
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {"X-Message-Id": "test-message-id-123"}

    with patch.object(
        email_sender.client, "send", return_value=mock_response
    ):
        # Send email
        success = await email_sender.send_email(scheduled_email.id)

        assert success is True

        # Verify email updated
        await db_session.refresh(scheduled_email)
        assert scheduled_email.status == "sent"
        assert scheduled_email.sent_at is not None
        assert scheduled_email.sendgrid_message_id == "test-message-id-123"


@pytest.mark.asyncio
async def test_send_email_already_sent(
    email_sender, scheduled_email, db_session
):
    """Test sending email that was already sent."""
    # Mark as sent
    scheduled_email.status = "sent"
    await db_session.commit()

    # Try to send again
    success = await email_sender.send_email(scheduled_email.id)

    assert success is True  # Returns True but doesn't send


@pytest.mark.asyncio
async def test_send_email_not_found(email_sender):
    """Test sending non-existent email."""
    fake_id = uuid4()
    with pytest.raises(ValueError, match="Email not found"):
        await email_sender.send_email(fake_id)


@pytest.mark.asyncio
async def test_send_email_sendgrid_error(
    email_sender, scheduled_email, db_session
):
    """Test SendGrid API error."""
    # Mock SendGrid error response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.body = "Bad Request"

    with patch.object(
        email_sender.client, "send", return_value=mock_response
    ):
        # Send email
        success = await email_sender.send_email(scheduled_email.id)

        assert success is False

        # Verify email marked as failed
        await db_session.refresh(scheduled_email)
        assert scheduled_email.status == "failed"
        assert scheduled_email.retry_count == 1


@pytest.mark.asyncio
async def test_send_email_network_error(
    email_sender, scheduled_email, db_session
):
    """Test network error during sending."""
    with patch.object(
        email_sender.client,
        "send",
        side_effect=Exception("Network error"),
    ):
        # Send email
        success = await email_sender.send_email(scheduled_email.id)

        assert success is False

        # Verify email marked as failed
        await db_session.refresh(scheduled_email)
        assert scheduled_email.status == "failed"
        assert scheduled_email.retry_count == 1


@pytest.mark.asyncio
async def test_send_email_max_retries(email_sender, scheduled_email, db_session):
    """Test email exceeding max retries."""
    # Set retry count to max
    scheduled_email.retry_count = 3
    await db_session.commit()

    # Try to send
    success = await email_sender.send_email(scheduled_email.id)

    assert success is False


@pytest.mark.asyncio
async def test_send_batch(email_sender, workflow, db_session):
    """Test sending batch of emails."""
    # Create multiple emails
    emails = []
    for i in range(3):
        email = ScheduledEmail(
            id=uuid4(),
            workflow_id=workflow.id,
            template_id="hot_instant",
            recipient_email=f"test{i}@example.com",
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test",
            scheduled_at=datetime.utcnow(),
            status="pending",
        )
        db_session.add(email)
        emails.append(email)
    await db_session.commit()

    # Mock SendGrid success
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {"X-Message-Id": "test-id"}

    with patch.object(
        email_sender.client, "send", return_value=mock_response
    ):
        # Send batch
        results = await email_sender.send_batch(
            [e.id for e in emails]
        )

        assert results["sent"] == 3
        assert results["failed"] == 0


@pytest.mark.asyncio
async def test_send_test_email(email_sender):
    """Test sending test email."""
    # Mock SendGrid success
    mock_response = MagicMock()
    mock_response.status_code = 202

    with patch.object(
        email_sender.client, "send", return_value=mock_response
    ):
        # Send test email
        success = await email_sender.send_test_email(
            to_email="test@example.com",
            subject="Test Email",
            html_content="<p>Test</p>",
            text_content="Test",
        )

        assert success is True


@pytest.mark.asyncio
async def test_get_send_statistics(
    email_sender, workflow, db_session
):
    """Test getting send statistics."""
    # Create emails with different statuses
    statuses = ["pending", "sent", "sent", "failed", "cancelled"]
    for status in statuses:
        email = ScheduledEmail(
            id=uuid4(),
            workflow_id=workflow.id,
            template_id="hot_instant",
            recipient_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test",
            scheduled_at=datetime.utcnow(),
            status=status,
            retry_count=1 if status == "failed" else 0,
        )
        db_session.add(email)
    await db_session.commit()

    # Get statistics
    stats = await email_sender.get_send_statistics()

    assert stats["total"] == 5
    assert stats["pending"] == 1
    assert stats["sent"] == 2
    assert stats["failed"] == 1
    assert stats["cancelled"] == 1
    assert stats["retried"] == 1


@pytest.mark.asyncio
async def test_validate_api_key_success(email_sender):
    """Test API key validation success."""
    # Mock successful validation at the right level
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(
        email_sender.client.client.api_keys,
        "get"
    ) as mock_get:
        mock_get.return_value = mock_response
        valid = email_sender.validate_api_key()
        assert valid is True
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_validate_api_key_failure(email_sender):
    """Test API key validation failure."""
    # Mock failed validation
    with patch.object(
        email_sender.client.client.api_keys,
        "get",
        side_effect=Exception("Invalid API key"),
    ):
        valid = email_sender.validate_api_key()
        assert valid is False
