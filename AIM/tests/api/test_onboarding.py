"""Tests for Onboarding API Endpoints

Tests for onboarding workflow API.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from httpx import AsyncClient

from aim.models.onboarding import Onboarding
from aim.services.onboarding.state_machine import OnboardingState


@pytest.fixture
def mock_onboarding_service():
    """Mock OnboardingService."""
    service = MagicMock()
    service.start_onboarding = AsyncMock()
    service.get_onboarding_status = AsyncMock()
    service.upload_document = AsyncMock()
    service.process_payment = AsyncMock()
    service.complete_onboarding = AsyncMock()
    service.retry_failed_step = AsyncMock()
    service.get_onboarding_by_lead = AsyncMock()
    return service


# Test: POST /api/onboarding/start
@pytest.mark.asyncio
async def test_start_onboarding_success(client: AsyncClient, mock_onboarding_service):
    """Test starting onboarding successfully."""
    # Mock service response
    mock_onboarding = Onboarding(
        id="onb_20260517014000_abc123",
        lead_id="lead_123",
        state=OnboardingState.DOCUMENTS_PENDING,
        progress=10,
        documents_uploaded=[],
        documents_validated=False,
        onboarding_fee=50000.0,
        started_at=datetime.utcnow(),
        metadata={},
    )
    mock_onboarding_service.start_onboarding.return_value = mock_onboarding

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/start",
            json={"lead_id": "lead_123"},
        )

    # Verify
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["onboarding_id"] == "onb_20260517014000_abc123"
    assert data["lead_id"] == "lead_123"
    assert data["state"] == OnboardingState.DOCUMENTS_PENDING
    assert data["progress"] == 10


@pytest.mark.asyncio
async def test_start_onboarding_lead_not_found(client: AsyncClient, mock_onboarding_service):
    """Test starting onboarding with non-existent lead."""
    # Mock service error
    mock_onboarding_service.start_onboarding.side_effect = ValueError("Lead lead_999 not found")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/start",
            json={"lead_id": "lead_999"},
        )

    # Verify
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_onboarding_already_exists(client: AsyncClient, mock_onboarding_service):
    """Test starting onboarding when already exists."""
    # Mock service error
    mock_onboarding_service.start_onboarding.side_effect = ValueError("Onboarding already exists for lead")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/start",
            json={"lead_id": "lead_123"},
        )

    # Verify
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


# Test: GET /api/onboarding/{onboarding_id}/status
@pytest.mark.asyncio
async def test_get_onboarding_status_success(client: AsyncClient, mock_onboarding_service):
    """Test getting onboarding status successfully."""
    # Mock service response
    mock_status = {
        "onboarding_id": "onb_20260517014000_abc123",
        "lead_id": "lead_123",
        "state": OnboardingState.DOCUMENTS_PENDING,
        "progress": 10,
        "documents_uploaded": [],
        "documents_validated": False,
        "payment_id": None,
        "onboarding_fee": 50000.0,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "failed_at": None,
        "failure_reason": None,
        "next_steps": ["upload_license", "upload_inn", "upload_ogrn", "upload_contract"],
    }
    mock_onboarding_service.get_onboarding_status.return_value = mock_status

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.get("/api/onboarding/onb_20260517014000_abc123/status")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["onboarding_id"] == "onb_20260517014000_abc123"
    assert data["state"] == OnboardingState.DOCUMENTS_PENDING
    assert data["progress"] == 10
    assert len(data["next_steps"]) == 4


@pytest.mark.asyncio
async def test_get_onboarding_status_not_found(client: AsyncClient, mock_onboarding_service):
    """Test getting status for non-existent onboarding."""
    # Mock service error
    mock_onboarding_service.get_onboarding_status.side_effect = ValueError("Onboarding onb_999 not found")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.get("/api/onboarding/onb_999/status")

    # Verify
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Test: POST /api/onboarding/{onboarding_id}/documents
@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, mock_onboarding_service):
    """Test uploading document successfully."""
    # Mock service response
    from aim.models.document import Document
    mock_document = Document(
        id="doc_123",
        lead_id="lead_123",
        document_type="license",
        file_path="/uploads/license.pdf",
        status="processing",
        uploaded_at=datetime.utcnow(),
    )
    mock_onboarding_service.upload_document.return_value = mock_document

    mock_status = {
        "onboarding_id": "onb_20260517014000_abc123",
        "lead_id": "lead_123",
        "state": OnboardingState.DOCUMENTS_PENDING,
        "progress": 17,
        "documents_uploaded": ["doc_123"],
        "documents_validated": False,
        "payment_id": None,
        "onboarding_fee": 50000.0,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "failed_at": None,
        "failure_reason": None,
        "next_steps": ["upload_inn", "upload_ogrn", "upload_contract"],
    }
    mock_onboarding_service.get_onboarding_status.return_value = mock_status

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/documents",
            params={"document_type": "license"},
            files={"file": ("license.pdf", b"fake pdf content", "application/pdf")},
        )

    # Verify
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["document_id"] == "doc_123"
    assert data["document_type"] == "license"
    assert data["progress"] == 17


@pytest.mark.asyncio
async def test_upload_document_invalid_type(client: AsyncClient, mock_onboarding_service):
    """Test uploading document with invalid type."""
    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/documents",
            params={"document_type": "invalid_type"},
            files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        )

    # Verify
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid document type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_document_invalid_file_type(client: AsyncClient, mock_onboarding_service):
    """Test uploading document with invalid file type."""
    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/documents",
            params={"document_type": "license"},
            files={"file": ("doc.txt", b"fake text content", "text/plain")},
        )

    # Verify
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file type" in response.json()["detail"]


# Test: POST /api/onboarding/{onboarding_id}/payment
@pytest.mark.asyncio
async def test_process_payment_success(client: AsyncClient, mock_onboarding_service):
    """Test processing payment successfully."""
    # Mock service response
    from aim.models.payment import Payment
    mock_payment = Payment(
        id="pay_123",
        lead_id="lead_123",
        amount=50000.0,
        currency="RUB",
        status="completed",
        payment_method="CARD",
        created_at=datetime.utcnow(),
    )
    mock_onboarding_service.process_payment.return_value = mock_payment

    mock_status = {
        "onboarding_id": "onb_20260517014000_abc123",
        "lead_id": "lead_123",
        "state": OnboardingState.PAYMENT_COMPLETED,
        "progress": 90,
        "documents_uploaded": ["doc_1", "doc_2", "doc_3", "doc_4"],
        "documents_validated": True,
        "payment_id": "pay_123",
        "onboarding_fee": 50000.0,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "failed_at": None,
        "failure_reason": None,
        "next_steps": ["complete_onboarding"],
    }
    mock_onboarding_service.get_onboarding_status.return_value = mock_status

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/payment",
            json={
                "amount": 50000.0,
                "currency": "RUB",
                "payment_method": "CARD",
                "customer_name": "Dr. Test",
                "customer_email": "test@example.com",
            },
        )

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["payment_id"] == "pay_123"
    assert data["payment_status"] == "completed"
    assert data["progress"] == 90


@pytest.mark.asyncio
async def test_process_payment_documents_not_validated(client: AsyncClient, mock_onboarding_service):
    """Test processing payment when documents not validated."""
    # Mock service error
    mock_onboarding_service.process_payment.side_effect = ValueError("Documents not validated")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/payment",
            json={
                "amount": 50000.0,
                "currency": "RUB",
                "payment_method": "CARD",
                "customer_name": "Dr. Test",
                "customer_email": "test@example.com",
            },
        )

    # Verify
    assert response.status_code == status.HTTP_409_CONFLICT


# Test: POST /api/onboarding/{onboarding_id}/complete
@pytest.mark.asyncio
async def test_complete_onboarding_success(client: AsyncClient, mock_onboarding_service):
    """Test completing onboarding successfully."""
    # Mock service response
    mock_onboarding = Onboarding(
        id="onb_20260517014000_abc123",
        lead_id="lead_123",
        state=OnboardingState.ONBOARDING_COMPLETE,
        progress=100,
        documents_uploaded=["doc_1", "doc_2", "doc_3", "doc_4"],
        documents_validated=True,
        onboarding_fee=50000.0,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        metadata={},
    )
    mock_onboarding_service.complete_onboarding.return_value = mock_onboarding

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post("/api/onboarding/onb_20260517014000_abc123/complete")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["onboarding_id"] == "onb_20260517014000_abc123"
    assert data["state"] == OnboardingState.ONBOARDING_COMPLETE
    assert data["progress"] == 100
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_complete_onboarding_payment_not_completed(client: AsyncClient, mock_onboarding_service):
    """Test completing onboarding when payment not completed."""
    # Mock service error
    mock_onboarding_service.complete_onboarding.side_effect = ValueError("Payment not completed")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post("/api/onboarding/onb_20260517014000_abc123/complete")

    # Verify
    assert response.status_code == status.HTTP_409_CONFLICT


# Test: POST /api/onboarding/{onboarding_id}/retry
@pytest.mark.asyncio
async def test_retry_step_success(client: AsyncClient, mock_onboarding_service):
    """Test retrying failed step successfully."""
    # Mock service response
    mock_onboarding = Onboarding(
        id="onb_20260517014000_abc123",
        lead_id="lead_123",
        state=OnboardingState.DOCUMENTS_PENDING,
        progress=10,
        documents_uploaded=[],
        documents_validated=False,
        onboarding_fee=50000.0,
        started_at=datetime.utcnow(),
        metadata={},
    )
    mock_onboarding_service.retry_failed_step.return_value = mock_onboarding

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/retry",
            json={"step": "documents_validation"},
        )

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["onboarding_id"] == "onb_20260517014000_abc123"
    assert data["step"] == "documents_validation"
    assert data["state"] == OnboardingState.DOCUMENTS_PENDING


@pytest.mark.asyncio
async def test_retry_step_not_failed(client: AsyncClient, mock_onboarding_service):
    """Test retrying step when onboarding not failed."""
    # Mock service error
    mock_onboarding_service.retry_failed_step.side_effect = ValueError("Onboarding is not in failed state")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.post(
            "/api/onboarding/onb_20260517014000_abc123/retry",
            json={"step": "documents_validation"},
        )

    # Verify
    assert response.status_code == status.HTTP_409_CONFLICT


# Test: GET /api/onboarding/lead/{lead_id}
@pytest.mark.asyncio
async def test_get_onboarding_by_lead_success(client: AsyncClient, mock_onboarding_service):
    """Test getting onboarding by lead successfully."""
    # Mock service response
    mock_onboarding = Onboarding(
        id="onb_20260517014000_abc123",
        lead_id="lead_123",
        state=OnboardingState.DOCUMENTS_PENDING,
        progress=10,
        documents_uploaded=[],
        documents_validated=False,
        onboarding_fee=50000.0,
        started_at=datetime.utcnow(),
        metadata={},
    )
    mock_onboarding_service.get_onboarding_by_lead.return_value = mock_onboarding

    mock_status = {
        "onboarding_id": "onb_20260517014000_abc123",
        "lead_id": "lead_123",
        "state": OnboardingState.DOCUMENTS_PENDING,
        "progress": 10,
        "documents_uploaded": [],
        "documents_validated": False,
        "payment_id": None,
        "onboarding_fee": 50000.0,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "failed_at": None,
        "failure_reason": None,
        "next_steps": ["upload_license", "upload_inn", "upload_ogrn", "upload_contract"],
    }
    mock_onboarding_service.get_onboarding_status.return_value = mock_status

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.get("/api/onboarding/lead/lead_123")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["onboarding_id"] == "onb_20260517014000_abc123"
    assert data["lead_id"] == "lead_123"


@pytest.mark.asyncio
async def test_get_onboarding_by_lead_not_found(client: AsyncClient, mock_onboarding_service):
    """Test getting onboarding by lead when not found."""
    # Mock service error
    mock_onboarding_service.get_onboarding_by_lead.side_effect = ValueError("No onboarding found for lead")

    # Make request
    with patch("aim.api.onboarding.get_onboarding_service", return_value=mock_onboarding_service):
        response = await client.get("/api/onboarding/lead/lead_999")

    # Verify
    assert response.status_code == status.HTTP_404_NOT_FOUND
