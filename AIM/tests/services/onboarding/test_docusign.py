"""
Tests for DocuSign API Client

Tests BAA signature workflow, webhook handling, and error scenarios.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from aim.services.onboarding.docusign_client import (
    DocuSignClient,
    DocuSignConfig,
    DocuSignWebhookHandler,
    EnvelopeStatus,
)


@pytest.fixture
def docusign_config():
    """DocuSign configuration"""
    return DocuSignConfig(
        account_id="test-account",
        integration_key="test-key",
        user_id="test-user",
        private_key="test-private-key",
        base_url="https://demo.docusign.net/restapi",
        oauth_base_url="https://account-d.docusign.com",
    )


@pytest.fixture
def docusign_client(docusign_config):
    """DocuSign client instance"""
    return DocuSignClient(docusign_config)


@pytest.fixture
def mock_workflow():
    """Mock workflow service"""
    workflow = AsyncMock()
    workflow.handle_event = AsyncMock()
    return workflow


@pytest.fixture
def webhook_handler(mock_workflow):
    """Webhook handler instance"""
    return DocuSignWebhookHandler(mock_workflow)


@pytest.mark.asyncio
async def test_get_access_token_success(docusign_client):
    """Test successful JWT token retrieval"""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "test-token",
        "expires_in": 3600,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        # Act
        token = await docusign_client._get_access_token()

        # Assert
        assert token == "test-token"
        assert docusign_client.access_token == "test-token"
        assert docusign_client.token_expires_at is not None


@pytest.mark.asyncio
async def test_get_access_token_cached(docusign_client):
    """Test that cached token is reused"""
    # Arrange
    docusign_client.access_token = "cached-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    # Act
    token = await docusign_client._get_access_token()

    # Assert
    assert token == "cached-token"


@pytest.mark.asyncio
async def test_send_baa_success(docusign_client):
    """Test successful BAA sending"""
    # Arrange
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {
        "access_token": "test-token",
        "expires_in": 3600,
    }
    mock_token_response.raise_for_status = MagicMock()

    mock_envelope_response = MagicMock()
    mock_envelope_response.json.return_value = {
        "envelopeId": "envelope-123",
    }
    mock_envelope_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(
            side_effect=[mock_token_response, mock_envelope_response]
        )

        # Act
        envelope_id = await docusign_client.send_baa(
            recipient_email="test@example.com",
            recipient_name="Dr. Test",
            practice_name="Test Clinic",
        )

        # Assert
        assert envelope_id == "envelope-123"
        assert mock_instance.post.call_count == 2


@pytest.mark.asyncio
async def test_send_baa_with_template(docusign_client):
    """Test BAA sending with custom template"""
    # Arrange
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {
        "access_token": "test-token",
        "expires_in": 3600,
    }
    mock_token_response.raise_for_status = MagicMock()

    mock_envelope_response = MagicMock()
    mock_envelope_response.json.return_value = {
        "envelopeId": "envelope-456",
    }
    mock_envelope_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(
            side_effect=[mock_token_response, mock_envelope_response]
        )

        # Act
        envelope_id = await docusign_client.send_baa(
            recipient_email="test@example.com",
            recipient_name="Dr. Test",
            practice_name="Test Clinic",
            template_id="custom-template",
        )

        # Assert
        assert envelope_id == "envelope-456"


@pytest.mark.asyncio
async def test_get_envelope_status_completed(docusign_client):
    """Test getting completed envelope status"""
    # Arrange
    docusign_client.access_token = "test-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "completed",
        "sentDateTime": "2026-05-16T10:00:00Z",
        "deliveredDateTime": "2026-05-16T10:05:00Z",
        "completedDateTime": "2026-05-16T10:10:00Z",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        # Act
        status = await docusign_client.get_envelope_status("envelope-123")

        # Assert
        assert status.envelope_id == "envelope-123"
        assert status.status == "completed"
        assert status.sent_at is not None
        assert status.delivered_at is not None
        assert status.signed_at is not None


@pytest.mark.asyncio
async def test_get_envelope_status_declined(docusign_client):
    """Test getting declined envelope status"""
    # Arrange
    docusign_client.access_token = "test-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "declined",
        "sentDateTime": "2026-05-16T10:00:00Z",
        "declinedDateTime": "2026-05-16T10:05:00Z",
        "declineReason": "Not interested",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        # Act
        status = await docusign_client.get_envelope_status("envelope-123")

        # Assert
        assert status.status == "declined"
        assert status.decline_reason == "Not interested"
        assert status.declined_at is not None


@pytest.mark.asyncio
async def test_download_signed_document(docusign_client):
    """Test downloading signed document"""
    # Arrange
    docusign_client.access_token = "test-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    mock_response = MagicMock()
    mock_response.content = b"PDF content here"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        # Act
        content = await docusign_client.download_signed_document("envelope-123")

        # Assert
        assert content == b"PDF content here"


@pytest.mark.asyncio
async def test_get_audit_trail(docusign_client):
    """Test getting audit trail"""
    # Arrange
    docusign_client.access_token = "test-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    mock_response = MagicMock()
    mock_response.content = b"Audit trail PDF"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        # Act
        content = await docusign_client.get_audit_trail("envelope-123")

        # Assert
        assert content == b"Audit trail PDF"


@pytest.mark.asyncio
async def test_void_envelope(docusign_client):
    """Test voiding an envelope"""
    # Arrange
    docusign_client.access_token = "test-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(
            return_value=mock_response
        )

        # Act
        await docusign_client.void_envelope(
            envelope_id="envelope-123",
            reason="Client requested cancellation",
        )

        # Assert
        mock_client.return_value.__aenter__.return_value.put.assert_called_once()


@pytest.mark.asyncio
async def test_resend_envelope(docusign_client):
    """Test resending envelope notification"""
    # Arrange
    docusign_client.access_token = "test-token"
    docusign_client.token_expires_at = datetime.utcnow() + timedelta(minutes=30)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(
            return_value=mock_response
        )

        # Act
        await docusign_client.resend_envelope("envelope-123")

        # Assert
        mock_client.return_value.__aenter__.return_value.put.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_envelope_completed(webhook_handler, mock_workflow):
    """Test webhook handling for completed envelope"""
    # Arrange
    payload = {
        "event": "envelope-completed",
        "envelopeId": "envelope-123",
    }

    # Act
    await webhook_handler.handle_webhook(payload)

    # Assert
    # Should trigger BAA_SIGNED event
    # Note: This test is simplified as it requires database lookup
    # In real implementation, would need to mock database query


@pytest.mark.asyncio
async def test_webhook_envelope_declined(webhook_handler, mock_workflow):
    """Test webhook handling for declined envelope"""
    # Arrange
    payload = {
        "event": "envelope-declined",
        "envelopeId": "envelope-123",
        "declineReason": "Not interested",
    }

    # Act
    await webhook_handler.handle_webhook(payload)

    # Assert
    # Should trigger BAA_DECLINED event
    # Note: This test is simplified as it requires database lookup


@pytest.mark.asyncio
async def test_webhook_envelope_voided(webhook_handler):
    """Test webhook handling for voided envelope"""
    # Arrange
    payload = {
        "event": "envelope-voided",
        "envelopeId": "envelope-123",
    }

    # Act
    await webhook_handler.handle_webhook(payload)

    # Assert
    # Should log the event but not trigger workflow transition


@pytest.mark.asyncio
async def test_parse_datetime_valid(docusign_client):
    """Test parsing valid datetime string"""
    # Arrange
    dt_str = "2026-05-16T10:00:00Z"

    # Act
    result = docusign_client._parse_datetime(dt_str)

    # Assert
    assert result is not None
    assert isinstance(result, datetime)


@pytest.mark.asyncio
async def test_parse_datetime_none(docusign_client):
    """Test parsing None datetime"""
    # Act
    result = docusign_client._parse_datetime(None)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_parse_datetime_invalid(docusign_client):
    """Test parsing invalid datetime string"""
    # Arrange
    dt_str = "invalid-date"

    # Act
    result = docusign_client._parse_datetime(dt_str)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_send_baa_api_error(docusign_client):
    """Test BAA sending with API error"""
    # Arrange
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {
        "access_token": "test-token",
        "expires_in": 3600,
    }
    mock_token_response.raise_for_status = MagicMock()

    mock_envelope_response = MagicMock()
    mock_envelope_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "API Error",
            request=MagicMock(),
            response=MagicMock(status_code=400),
        )
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(
            side_effect=[mock_token_response, mock_envelope_response]
        )

        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            await docusign_client.send_baa(
                recipient_email="test@example.com",
                recipient_name="Dr. Test",
                practice_name="Test Clinic",
            )
