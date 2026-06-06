"""
Tests for Kontour.Diadok Client

Tests e-signature integration (STUB implementation).
"""

import pytest
from datetime import datetime

from src.aim.services.contracts.kontour_client import (
    KontourClient,
    KontourWebhookHandler,
    DocumentStatus,
    SignatureType,
    get_signature_type_for_amount,
    verify_webhook_signature,
)


@pytest.fixture
def kontour_client():
    """Create Kontour client"""
    return KontourClient(
        api_key="test_api_key",
        organization_id="test_org_id",
    )


@pytest.mark.asyncio
async def test_send_for_signature(kontour_client):
    """Test sending document for signature"""
    # Send document
    document_id = await kontour_client.send_for_signature(
        document_path="/path/to/contract.pdf",
        recipient_email="test@clinic.ru",
        recipient_name="Иван Петров",
        recipient_inn="7701234567",
        signature_type=SignatureType.ENHANCED,
        message="Пожалуйста, подпишите договор",
    )

    # Verify document ID returned
    assert document_id is not None
    assert document_id.startswith("STUB-DOC-")


@pytest.mark.asyncio
async def test_get_document_status(kontour_client):
    """Test getting document status"""
    # Get status
    status = await kontour_client.get_document_status("STUB-DOC-123")

    # Verify status structure
    assert "document_id" in status
    assert "status" in status
    assert status["status"] in [s.value for s in DocumentStatus]
    assert "sent_at" in status
    assert "stub" in status
    assert status["stub"] is True


@pytest.mark.asyncio
async def test_get_document_status_signed(kontour_client):
    """Test getting status for signed document"""
    # Get status for signed document
    status = await kontour_client.get_document_status("STUB-DOC-SIGNED-123")

    # Verify signed status
    assert status["status"] == DocumentStatus.SIGNED
    assert status["signed_at"] is not None


@pytest.mark.asyncio
async def test_get_document_status_declined(kontour_client):
    """Test getting status for declined document"""
    # Get status for declined document
    status = await kontour_client.get_document_status("STUB-DOC-DECLINED-123")

    # Verify declined status
    assert status["status"] == DocumentStatus.DECLINED


@pytest.mark.asyncio
async def test_download_signed_document(kontour_client):
    """Test downloading signed document"""
    # Download document
    document_bytes = await kontour_client.download_signed_document("STUB-DOC-123")

    # Verify bytes returned
    assert document_bytes is not None
    assert len(document_bytes) > 0
    assert document_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_get_signature_certificate(kontour_client):
    """Test getting signature certificate"""
    # Get certificate
    certificate_bytes = await kontour_client.get_signature_certificate("STUB-DOC-123")

    # Verify bytes returned
    assert certificate_bytes is not None
    assert len(certificate_bytes) > 0
    assert certificate_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_cancel_signature_request(kontour_client):
    """Test cancelling signature request"""
    # Cancel request (should not raise)
    await kontour_client.cancel_signature_request(
        document_id="STUB-DOC-123",
        reason="Ошибка в договоре",
    )


@pytest.mark.asyncio
async def test_resend_notification(kontour_client):
    """Test resending notification"""
    # Resend notification (should not raise)
    await kontour_client.resend_notification("STUB-DOC-123")


@pytest.mark.asyncio
async def test_get_organization_info(kontour_client):
    """Test getting organization info"""
    # Get organization info
    org_info = await kontour_client.get_organization_info()

    # Verify structure
    assert "organization_id" in org_info
    assert "name" in org_info
    assert "inn" in org_info
    assert "stub" in org_info
    assert org_info["stub"] is True


def test_signature_type_for_amount_simple():
    """Test signature type for small amount"""
    signature_type = get_signature_type_for_amount(50_000)
    assert signature_type == SignatureType.SIMPLE


def test_signature_type_for_amount_enhanced():
    """Test signature type for medium amount"""
    signature_type = get_signature_type_for_amount(250_000)
    assert signature_type == SignatureType.ENHANCED


def test_signature_type_for_amount_qualified():
    """Test signature type for large amount"""
    signature_type = get_signature_type_for_amount(700_000)
    assert signature_type == SignatureType.QUALIFIED


def test_signature_type_boundary_100k():
    """Test signature type at 100k boundary"""
    # Just below 100k
    assert get_signature_type_for_amount(99_999) == SignatureType.SIMPLE
    # At 100k
    assert get_signature_type_for_amount(100_000) == SignatureType.ENHANCED


def test_signature_type_boundary_600k():
    """Test signature type at 600k boundary"""
    # Just below 600k
    assert get_signature_type_for_amount(599_999) == SignatureType.ENHANCED
    # At 600k
    assert get_signature_type_for_amount(600_000) == SignatureType.QUALIFIED


def test_verify_webhook_signature():
    """Test webhook signature verification (STUB)"""
    # STUB always returns True
    result = verify_webhook_signature(
        payload=b"test payload",
        signature="test_signature",
        secret="test_secret",
    )
    assert result is True


@pytest.mark.asyncio
async def test_webhook_handler_document_signed():
    """Test webhook handler for signed document"""
    # Create mock workflow service
    class MockWorkflow:
        def __init__(self):
            self.events = []

        async def handle_event(self, *args, **kwargs):
            self.events.append(("handle_event", args, kwargs))

    workflow = MockWorkflow()
    handler = KontourWebhookHandler(workflow)

    # Handle signed event
    await handler.handle_webhook({
        "event_type": "document.signed",
        "document_id": "STUB-DOC-123",
    })

    # Verify event was processed (no exception)


@pytest.mark.asyncio
async def test_webhook_handler_document_declined():
    """Test webhook handler for declined document"""
    class MockWorkflow:
        def __init__(self):
            self.events = []

        async def handle_event(self, *args, **kwargs):
            self.events.append(("handle_event", args, kwargs))

    workflow = MockWorkflow()
    handler = KontourWebhookHandler(workflow)

    # Handle declined event
    await handler.handle_webhook({
        "event_type": "document.declined",
        "document_id": "STUB-DOC-123",
        "decline_reason": "Не согласен с условиями",
    })

    # Verify event was processed (no exception)


@pytest.mark.asyncio
async def test_webhook_handler_document_expired():
    """Test webhook handler for expired document"""
    class MockWorkflow:
        def __init__(self):
            self.events = []

        async def handle_event(self, *args, **kwargs):
            self.events.append(("handle_event", args, kwargs))

    workflow = MockWorkflow()
    handler = KontourWebhookHandler(workflow)

    # Handle expired event
    await handler.handle_webhook({
        "event_type": "document.expired",
        "document_id": "STUB-DOC-123",
    })

    # Verify event was processed (no exception)


@pytest.mark.asyncio
async def test_send_for_signature_all_signature_types(kontour_client):
    """Test sending with all signature types"""
    for signature_type in SignatureType:
        document_id = await kontour_client.send_for_signature(
            document_path="/path/to/contract.pdf",
            recipient_email="test@clinic.ru",
            recipient_name="Иван Петров",
            recipient_inn="7701234567",
            signature_type=signature_type,
        )
        assert document_id is not None


@pytest.mark.asyncio
async def test_send_for_signature_with_message(kontour_client):
    """Test sending with custom message"""
    document_id = await kontour_client.send_for_signature(
        document_path="/path/to/contract.pdf",
        recipient_email="test@clinic.ru",
        recipient_name="Иван Петров",
        recipient_inn="7701234567",
        message="Срочно! Пожалуйста, подпишите договор до конца дня.",
    )
    assert document_id is not None


@pytest.mark.asyncio
async def test_multiple_documents_same_session(kontour_client):
    """Test sending multiple documents in same session"""
    document_ids = []

    for i in range(3):
        document_id = await kontour_client.send_for_signature(
            document_path=f"/path/to/contract_{i}.pdf",
            recipient_email=f"test{i}@clinic.ru",
            recipient_name=f"Клиент {i}",
            recipient_inn="7701234567",
        )
        document_ids.append(document_id)

    # Verify all unique
    assert len(document_ids) == 3
    assert len(set(document_ids)) == 3
