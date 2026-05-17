"""E2E Test: Onboarding Flow

Tests complete onboarding journey from start to completion.

Flow:
1. Lead → Start onboarding
2. Upload documents (license, inn, ogrn, contract)
3. AI extraction and validation
4. Payment processing
5. Onboarding completion

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.onboarding import Onboarding
from aim.models.document import Document
from aim.models.payment import Payment
from aim.services.onboarding.state_machine import OnboardingState


@pytest.mark.asyncio
async def test_complete_onboarding_flow_success(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test complete onboarding flow from start to completion."""
    # Step 1: Create lead first
    lead_response = await client.post("/api/leads/capture", json={
        "name": "Dr. Иван Петров",
        "email": "ivan.petrov@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Премиум Клиника",
        "city": "Москва",
        "services": ["implants"],
        "monthly_budget": 300000,
    })
    assert lead_response.status_code == 201
    lead_id = lead_response.json()["lead_id"]

    # Step 2: Start onboarding
    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    assert start_response.status_code == 201
    data = start_response.json()
    onboarding_id = data["onboarding_id"]
    assert data["state"] == OnboardingState.DOCUMENTS_PENDING
    assert data["progress"] == 10

    # Step 3: Upload license document
    license_file = BytesIO(b"%PDF-1.4 fake license content")
    license_response = await client.post(
        f"/api/onboarding/{onboarding_id}/documents",
        params={"document_type": "license"},
        files={"file": ("license.pdf", license_file, "application/pdf")},
    )
    assert license_response.status_code == 201
    assert license_response.json()["document_type"] == "license"
    assert license_response.json()["progress"] == 17  # 10 + 7

    # Step 4: Upload INN document
    inn_file = BytesIO(b"%PDF-1.4 fake inn content")
    inn_response = await client.post(
        f"/api/onboarding/{onboarding_id}/documents",
        params={"document_type": "inn"},
        files={"file": ("inn.pdf", inn_file, "application/pdf")},
    )
    assert inn_response.status_code == 201
    assert inn_response.json()["progress"] == 24  # 17 + 7

    # Step 5: Upload OGRN document
    ogrn_file = BytesIO(b"%PDF-1.4 fake ogrn content")
    ogrn_response = await client.post(
        f"/api/onboarding/{onboarding_id}/documents",
        params={"document_type": "ogrn"},
        files={"file": ("ogrn.pdf", ogrn_file, "application/pdf")},
    )
    assert ogrn_response.status_code == 201
    assert ogrn_response.json()["progress"] == 31  # 24 + 7

    # Step 6: Upload contract document
    contract_file = BytesIO(b"%PDF-1.4 fake contract content")
    contract_response = await client.post(
        f"/api/onboarding/{onboarding_id}/documents",
        params={"document_type": "contract"},
        files={"file": ("contract.pdf", contract_file, "application/pdf")},
    )
    assert contract_response.status_code == 201
    assert contract_response.json()["progress"] == 38  # 31 + 7

    # Step 7: Check status after all documents uploaded
    status_response = await client.get(f"/api/onboarding/{onboarding_id}/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["state"] == OnboardingState.DOCUMENTS_VALIDATED
    assert status_data["progress"] == 60
    assert status_data["documents_validated"] is True
    assert len(status_data["documents_uploaded"]) == 4

    # Step 8: Process payment
    payment_response = await client.post(
        f"/api/onboarding/{onboarding_id}/payment",
        json={
            "amount": 50000.0,
            "currency": "RUB",
            "payment_method": "CARD",
            "customer_name": "Dr. Иван Петров",
            "customer_email": "ivan.petrov@clinic.ru",
            "card_number": "4111111111111111",
            "card_expiry": "12/25",
            "card_cvv": "123",
        },
    )
    assert payment_response.status_code == 200
    payment_data = payment_response.json()
    assert payment_data["payment_status"] == "completed"
    assert payment_data["progress"] == 90

    # Step 9: Complete onboarding
    complete_response = await client.post(
        f"/api/onboarding/{onboarding_id}/complete"
    )
    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data["state"] == OnboardingState.ONBOARDING_COMPLETE
    assert complete_data["progress"] == 100
    assert complete_data["completed_at"] is not None

    # Step 10: Verify final status
    final_status = await client.get(f"/api/onboarding/{onboarding_id}/status")
    assert final_status.status_code == 200
    final_data = final_status.json()
    assert final_data["state"] == OnboardingState.ONBOARDING_COMPLETE
    assert final_data["progress"] == 100
    assert len(final_data["next_steps"]) == 0  # No more steps


@pytest.mark.asyncio
async def test_onboarding_flow_with_document_validation_failure(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test onboarding flow when document validation fails."""
    # Step 1: Create lead and start onboarding
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

    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    onboarding_id = start_response.json()["onboarding_id"]

    # Step 2: Upload invalid license (wrong format)
    with patch("aim.services.document.processor.DocumentProcessor.extract_license_data") as mock_extract:
        mock_extract.side_effect = ValueError("Invalid license format")

        invalid_file = BytesIO(b"invalid content")
        response = await client.post(
            f"/api/onboarding/{onboarding_id}/documents",
            params={"document_type": "license"},
            files={"file": ("license.pdf", invalid_file, "application/pdf")},
        )

        # Should fail validation
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    # Step 3: Verify onboarding still in DOCUMENTS_PENDING
    status_response = await client.get(f"/api/onboarding/{onboarding_id}/status")
    assert status_response.json()["state"] == OnboardingState.DOCUMENTS_PENDING


@pytest.mark.asyncio
async def test_onboarding_flow_with_payment_failure(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test onboarding flow when payment fails."""
    # Step 1: Create lead, start onboarding, upload all documents
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

    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    onboarding_id = start_response.json()["onboarding_id"]

    # Upload all 4 documents
    for doc_type in ["license", "inn", "ogrn", "contract"]:
        file = BytesIO(b"%PDF-1.4 fake content")
        await client.post(
            f"/api/onboarding/{onboarding_id}/documents",
            params={"document_type": doc_type},
            files={"file": (f"{doc_type}.pdf", file, "application/pdf")},
        )

    # Step 2: Try payment with insufficient funds
    with patch("aim.services.payment.payment_service.PaymentService.process_payment") as mock_payment:
        mock_payment.side_effect = ValueError("Insufficient funds")

        payment_response = await client.post(
            f"/api/onboarding/{onboarding_id}/payment",
            json={
                "amount": 50000.0,
                "currency": "RUB",
                "payment_method": "CARD",
                "customer_name": "Dr. Test",
                "customer_email": "test@clinic.ru",
                "card_number": "4111111111111111",
                "card_expiry": "12/25",
                "card_cvv": "123",
            },
        )

        # Should fail
        assert payment_response.status_code == 400

    # Step 3: Verify onboarding in PAYMENT_FAILED state
    status_response = await client.get(f"/api/onboarding/{onboarding_id}/status")
    status_data = status_response.json()
    assert status_data["state"] == OnboardingState.ONBOARDING_FAILED
    assert "payment" in status_data["failure_reason"].lower()


@pytest.mark.asyncio
async def test_onboarding_flow_retry_after_failure(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test retry mechanism after onboarding failure."""
    # Step 1: Create failed onboarding (payment failure)
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

    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    onboarding_id = start_response.json()["onboarding_id"]

    # Upload documents and fail payment
    for doc_type in ["license", "inn", "ogrn", "contract"]:
        file = BytesIO(b"%PDF-1.4 fake content")
        await client.post(
            f"/api/onboarding/{onboarding_id}/documents",
            params={"document_type": doc_type},
            files={"file": (f"{doc_type}.pdf", file, "application/pdf")},
        )

    with patch("aim.services.payment.payment_service.PaymentService.process_payment") as mock_payment:
        mock_payment.side_effect = ValueError("Payment failed")
        await client.post(
            f"/api/onboarding/{onboarding_id}/payment",
            json={
                "amount": 50000.0,
                "currency": "RUB",
                "payment_method": "CARD",
                "customer_name": "Dr. Test",
                "customer_email": "test@clinic.ru",
            },
        )

    # Step 2: Retry payment step
    retry_response = await client.post(
        f"/api/onboarding/{onboarding_id}/retry",
        json={"step": "payment"},
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["state"] == OnboardingState.DOCUMENTS_VALIDATED

    # Step 3: Try payment again (should succeed)
    payment_response = await client.post(
        f"/api/onboarding/{onboarding_id}/payment",
        json={
            "amount": 50000.0,
            "currency": "RUB",
            "payment_method": "CARD",
            "customer_name": "Dr. Test",
            "customer_email": "test@clinic.ru",
        },
    )
    assert payment_response.status_code == 200
    assert payment_response.json()["payment_status"] == "completed"


@pytest.mark.asyncio
async def test_onboarding_flow_document_types_validation(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test validation of document types during upload."""
    # Step 1: Create lead and start onboarding
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

    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    onboarding_id = start_response.json()["onboarding_id"]

    # Step 2: Try invalid document type
    file = BytesIO(b"%PDF-1.4 fake content")
    response = await client.post(
        f"/api/onboarding/{onboarding_id}/documents",
        params={"document_type": "invalid_type"},
        files={"file": ("doc.pdf", file, "application/pdf")},
    )
    assert response.status_code == 400
    assert "Invalid document type" in response.json()["detail"]

    # Step 3: Try invalid file type (not PDF/image)
    text_file = BytesIO(b"plain text content")
    response = await client.post(
        f"/api/onboarding/{onboarding_id}/documents",
        params={"document_type": "license"},
        files={"file": ("doc.txt", text_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_onboarding_flow_state_transitions(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test state machine transitions during onboarding."""
    # Step 1: Create lead and start onboarding
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

    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    onboarding_id = start_response.json()["onboarding_id"]

    # Step 2: Try to complete without documents (should fail)
    complete_response = await client.post(
        f"/api/onboarding/{onboarding_id}/complete"
    )
    assert complete_response.status_code == 409  # Invalid state transition

    # Step 3: Try to pay without documents (should fail)
    payment_response = await client.post(
        f"/api/onboarding/{onboarding_id}/payment",
        json={
            "amount": 50000.0,
            "currency": "RUB",
            "payment_method": "CARD",
            "customer_name": "Dr. Test",
            "customer_email": "test@clinic.ru",
        },
    )
    assert payment_response.status_code == 409  # Documents not validated

    # Step 4: Upload documents
    for doc_type in ["license", "inn", "ogrn", "contract"]:
        file = BytesIO(b"%PDF-1.4 fake content")
        await client.post(
            f"/api/onboarding/{onboarding_id}/documents",
            params={"document_type": doc_type},
            files={"file": (f"{doc_type}.pdf", file, "application/pdf")},
        )

    # Step 5: Try to complete without payment (should fail)
    complete_response = await client.post(
        f"/api/onboarding/{onboarding_id}/complete"
    )
    assert complete_response.status_code == 409  # Payment not completed

    # Step 6: Process payment
    payment_response = await client.post(
        f"/api/onboarding/{onboarding_id}/payment",
        json={
            "amount": 50000.0,
            "currency": "RUB",
            "payment_method": "CARD",
            "customer_name": "Dr. Test",
            "customer_email": "test@clinic.ru",
        },
    )
    assert payment_response.status_code == 200

    # Step 7: Now complete should succeed
    complete_response = await client.post(
        f"/api/onboarding/{onboarding_id}/complete"
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["state"] == OnboardingState.ONBOARDING_COMPLETE


@pytest.mark.asyncio
async def test_onboarding_flow_get_by_lead(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test getting onboarding by lead ID."""
    # Step 1: Create lead and start onboarding
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

    start_response = await client.post("/api/onboarding/start", json={
        "lead_id": lead_id,
    })
    onboarding_id = start_response.json()["onboarding_id"]

    # Step 2: Get onboarding by lead ID
    get_response = await client.get(f"/api/onboarding/lead/{lead_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["onboarding_id"] == onboarding_id
    assert data["lead_id"] == lead_id

    # Step 3: Try to get non-existent onboarding
    get_response = await client.get("/api/onboarding/lead/lead_999")
    assert get_response.status_code == 404
