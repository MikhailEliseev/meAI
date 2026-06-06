"""Tests for Onboarding Service

Tests for onboarding workflow orchestration.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.models.onboarding import Onboarding
from src.aim.models.lead import Lead
from src.aim.models.document import Document
from src.aim.models.payment import Payment
from src.aim.services.onboarding.onboarding_service import OnboardingService
from src.aim.services.onboarding.state_machine import OnboardingState, OnboardingEvent


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_lead():
    """Mock lead."""
    lead = Lead(
        id="lead_123",
        clinic_name="Test Clinic",
        contact_name="Dr. Test",
        email="test@example.com",
        phone="+79001234567",
        city="Moscow",
        score=85.0,
    )
    return lead


@pytest.fixture
def mock_onboarding():
    """Mock onboarding."""
    onboarding = Onboarding(
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
    return onboarding


@pytest.fixture
def mock_document():
    """Mock document."""
    document = Document(
        id="doc_123",
        lead_id="lead_123",
        document_type="license",
        file_path="/uploads/license.pdf",
        status="completed",
        validation_status="valid",
        uploaded_at=datetime.utcnow(),
    )
    return document


@pytest.fixture
def mock_payment():
    """Mock payment."""
    payment = Payment(
        id="pay_123",
        lead_id="lead_123",
        amount=50000.0,
        currency="RUB",
        status="completed",
        payment_method="CARD",
        created_at=datetime.utcnow(),
    )
    return payment


@pytest.fixture
def onboarding_service(mock_db):
    """Create OnboardingService instance."""
    return OnboardingService(mock_db)


# Test: start_onboarding
@pytest.mark.asyncio
async def test_start_onboarding_success(onboarding_service, mock_db, mock_lead):
    """Test starting onboarding successfully."""
    # Mock lead query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_lead
    mock_db.execute.return_value = mock_result

    # Start onboarding
    onboarding = await onboarding_service.start_onboarding("lead_123")

    # Verify
    assert onboarding.lead_id == "lead_123"
    assert onboarding.state == OnboardingState.DOCUMENTS_PENDING
    assert onboarding.progress == 10
    assert onboarding.onboarding_fee == 50000.0
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_start_onboarding_lead_not_found(onboarding_service, mock_db):
    """Test starting onboarding with non-existent lead."""
    # Mock lead not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Lead .* not found"):
        await onboarding_service.start_onboarding("lead_999")


@pytest.mark.asyncio
async def test_start_onboarding_already_exists(onboarding_service, mock_db, mock_lead, mock_onboarding):
    """Test starting onboarding when already exists."""
    # Mock lead and existing onboarding
    mock_result_lead = MagicMock()
    mock_result_lead.scalar_one_or_none.return_value = mock_lead

    mock_result_onboarding = MagicMock()
    mock_result_onboarding.scalar_one_or_none.return_value = mock_onboarding

    mock_db.execute.side_effect = [mock_result_lead, mock_result_onboarding]

    # Verify error
    with pytest.raises(ValueError, match="Onboarding already exists"):
        await onboarding_service.start_onboarding("lead_123")


# Test: upload_document
@pytest.mark.asyncio
async def test_upload_document_success(onboarding_service, mock_db, mock_onboarding, mock_document):
    """Test uploading document successfully."""
    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Mock document processor
    with patch.object(onboarding_service, 'document_processor') as mock_processor:
        mock_processor.process_document = AsyncMock(return_value=mock_document)

        # Upload document
        document = await onboarding_service.upload_document(
            onboarding_id="onb_20260517014000_abc123",
            document_type="license",
            file_content=b"fake pdf content",
            filename="license.pdf",
        )

        # Verify
        assert document.id == "doc_123"
        assert document.document_type == "license"
        assert "doc_123" in mock_onboarding.documents_uploaded
        mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_upload_document_onboarding_not_found(onboarding_service, mock_db):
    """Test uploading document with non-existent onboarding."""
    # Mock onboarding not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Onboarding .* not found"):
        await onboarding_service.upload_document(
            onboarding_id="onb_999",
            document_type="license",
            file_content=b"fake pdf content",
            filename="license.pdf",
        )


@pytest.mark.asyncio
async def test_upload_document_invalid_state(onboarding_service, mock_db, mock_onboarding):
    """Test uploading document in invalid state."""
    # Set onboarding to completed state
    mock_onboarding.state = OnboardingState.ONBOARDING_COMPLETE

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Cannot upload document"):
        await onboarding_service.upload_document(
            onboarding_id="onb_20260517014000_abc123",
            document_type="license",
            file_content=b"fake pdf content",
            filename="license.pdf",
        )


# Test: check_documents_complete
@pytest.mark.asyncio
async def test_check_documents_complete_all_uploaded(onboarding_service, mock_db, mock_onboarding):
    """Test checking documents when all are uploaded."""
    # Set all documents uploaded
    mock_onboarding.metadata = {
        "document_types": ["license", "inn", "ogrn", "contract"]
    }

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Check documents
    is_complete = await onboarding_service.check_documents_complete("onb_20260517014000_abc123")

    # Verify
    assert is_complete is True


@pytest.mark.asyncio
async def test_check_documents_complete_missing_documents(onboarding_service, mock_db, mock_onboarding):
    """Test checking documents when some are missing."""
    # Set only 2 documents uploaded
    mock_onboarding.metadata = {
        "document_types": ["license", "inn"]
    }

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Check documents
    is_complete = await onboarding_service.check_documents_complete("onb_20260517014000_abc123")

    # Verify
    assert is_complete is False


# Test: validate_documents
@pytest.mark.asyncio
async def test_validate_documents_success(onboarding_service, mock_db, mock_onboarding):
    """Test validating documents successfully."""
    # Set all documents uploaded and valid
    mock_onboarding.metadata = {
        "document_types": ["license", "inn", "ogrn", "contract"]
    }
    mock_onboarding.state = OnboardingState.DOCUMENTS_UPLOADED

    # Mock onboarding query
    mock_result_onboarding = MagicMock()
    mock_result_onboarding.scalar_one_or_none.return_value = mock_onboarding

    # Mock documents query (all valid)
    mock_doc1 = MagicMock(status="completed", validation_status="valid")
    mock_doc2 = MagicMock(status="completed", validation_status="valid")
    mock_doc3 = MagicMock(status="completed", validation_status="valid")
    mock_doc4 = MagicMock(status="completed", validation_status="valid")

    mock_result_docs = MagicMock()
    mock_result_docs.scalars.return_value.all.return_value = [mock_doc1, mock_doc2, mock_doc3, mock_doc4]

    mock_db.execute.side_effect = [mock_result_onboarding, mock_result_docs]

    # Validate documents
    onboarding = await onboarding_service.validate_documents("onb_20260517014000_abc123")

    # Verify
    assert onboarding.state == OnboardingState.DOCUMENTS_VALIDATED
    assert onboarding.documents_validated is True
    assert onboarding.progress == 60
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_validate_documents_not_all_uploaded(onboarding_service, mock_db, mock_onboarding):
    """Test validating documents when not all uploaded."""
    # Set only 2 documents uploaded
    mock_onboarding.metadata = {
        "document_types": ["license", "inn"]
    }

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Not all required documents uploaded"):
        await onboarding_service.validate_documents("onb_20260517014000_abc123")


@pytest.mark.asyncio
async def test_validate_documents_some_invalid(onboarding_service, mock_db, mock_onboarding):
    """Test validating documents when some are invalid."""
    # Set all documents uploaded
    mock_onboarding.metadata = {
        "document_types": ["license", "inn", "ogrn", "contract"]
    }
    mock_onboarding.state = OnboardingState.DOCUMENTS_UPLOADED

    # Mock onboarding query
    mock_result_onboarding = MagicMock()
    mock_result_onboarding.scalar_one_or_none.return_value = mock_onboarding

    # Mock documents query (one invalid)
    mock_doc1 = MagicMock(status="completed", validation_status="valid")
    mock_doc2 = MagicMock(status="completed", validation_status="invalid")
    mock_doc3 = MagicMock(status="completed", validation_status="valid")
    mock_doc4 = MagicMock(status="completed", validation_status="valid")

    mock_result_docs = MagicMock()
    mock_result_docs.scalars.return_value.all.return_value = [mock_doc1, mock_doc2, mock_doc3, mock_doc4]

    mock_db.execute.side_effect = [mock_result_onboarding, mock_result_docs]

    # Verify error
    with pytest.raises(ValueError, match="Some documents are invalid"):
        await onboarding_service.validate_documents("onb_20260517014000_abc123")


# Test: calculate_onboarding_fee
@pytest.mark.asyncio
async def test_calculate_onboarding_fee(onboarding_service, mock_db, mock_onboarding):
    """Test calculating onboarding fee."""
    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Calculate fee
    fee = await onboarding_service.calculate_onboarding_fee("onb_20260517014000_abc123")

    # Verify
    assert fee == 50000.0


# Test: process_payment
@pytest.mark.asyncio
async def test_process_payment_success(onboarding_service, mock_db, mock_onboarding, mock_payment):
    """Test processing payment successfully."""
    # Set documents validated
    mock_onboarding.state = OnboardingState.DOCUMENTS_VALIDATED
    mock_onboarding.documents_validated = True

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Mock payment service
    with patch.object(onboarding_service, 'payment_service') as mock_payment_service:
        mock_payment_service.process_payment = AsyncMock(return_value=mock_payment)

        # Process payment
        payment = await onboarding_service.process_payment(
            onboarding_id="onb_20260517014000_abc123",
            payment_data={
                "amount": 50000.0,
                "currency": "RUB",
                "payment_method": "CARD",
                "customer_name": "Dr. Test",
                "customer_email": "test@example.com",
            },
        )

        # Verify
        assert payment.id == "pay_123"
        assert payment.status == "completed"
        assert mock_onboarding.payment_id == "pay_123"
        assert mock_onboarding.state == OnboardingState.PAYMENT_COMPLETED
        mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_payment_documents_not_validated(onboarding_service, mock_db, mock_onboarding):
    """Test processing payment when documents not validated."""
    # Set documents not validated
    mock_onboarding.state = OnboardingState.DOCUMENTS_UPLOADED
    mock_onboarding.documents_validated = False

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Documents not validated"):
        await onboarding_service.process_payment(
            onboarding_id="onb_20260517014000_abc123",
            payment_data={},
        )


# Test: complete_onboarding
@pytest.mark.asyncio
async def test_complete_onboarding_success(onboarding_service, mock_db, mock_onboarding):
    """Test completing onboarding successfully."""
    # Set payment completed
    mock_onboarding.state = OnboardingState.PAYMENT_COMPLETED
    mock_onboarding.payment_id = "pay_123"

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Complete onboarding
    onboarding = await onboarding_service.complete_onboarding("onb_20260517014000_abc123")

    # Verify
    assert onboarding.state == OnboardingState.ONBOARDING_COMPLETE
    assert onboarding.progress == 100
    assert onboarding.completed_at is not None
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_complete_onboarding_payment_not_completed(onboarding_service, mock_db, mock_onboarding):
    """Test completing onboarding when payment not completed."""
    # Set payment not completed
    mock_onboarding.state = OnboardingState.PAYMENT_PROCESSING
    mock_onboarding.payment_id = "pay_123"

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Transition not allowed"):
        await onboarding_service.complete_onboarding("onb_20260517014000_abc123")


# Test: get_onboarding_status
@pytest.mark.asyncio
async def test_get_onboarding_status_success(onboarding_service, mock_db, mock_onboarding):
    """Test getting onboarding status successfully."""
    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Get status
    status = await onboarding_service.get_onboarding_status("onb_20260517014000_abc123")

    # Verify
    assert status["onboarding_id"] == "onb_20260517014000_abc123"
    assert status["lead_id"] == "lead_123"
    assert status["state"] == OnboardingState.DOCUMENTS_PENDING
    assert status["progress"] == 10
    assert "next_steps" in status
    assert len(status["next_steps"]) > 0


@pytest.mark.asyncio
async def test_get_onboarding_status_not_found(onboarding_service, mock_db):
    """Test getting status for non-existent onboarding."""
    # Mock onboarding not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Onboarding .* not found"):
        await onboarding_service.get_onboarding_status("onb_999")


# Test: retry_failed_step
@pytest.mark.asyncio
async def test_retry_failed_step_documents_validation(onboarding_service, mock_db, mock_onboarding):
    """Test retrying failed documents validation."""
    # Set failed state
    mock_onboarding.state = OnboardingState.ONBOARDING_FAILED
    mock_onboarding.failure_reason = "Document validation failed"

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Retry step
    onboarding = await onboarding_service.retry_failed_step(
        onboarding_id="onb_20260517014000_abc123",
        step="documents_validation",
    )

    # Verify
    assert onboarding.state == OnboardingState.DOCUMENTS_PENDING
    assert onboarding.failed_at is None
    assert onboarding.failure_reason is None
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_retry_failed_step_payment_processing(onboarding_service, mock_db, mock_onboarding):
    """Test retrying failed payment processing."""
    # Set failed state
    mock_onboarding.state = OnboardingState.ONBOARDING_FAILED
    mock_onboarding.failure_reason = "Payment processing failed"
    mock_onboarding.documents_validated = True

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Retry step
    onboarding = await onboarding_service.retry_failed_step(
        onboarding_id="onb_20260517014000_abc123",
        step="payment_processing",
    )

    # Verify
    assert onboarding.state == OnboardingState.DOCUMENTS_VALIDATED
    assert onboarding.failed_at is None
    assert onboarding.failure_reason is None
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_retry_failed_step_not_failed(onboarding_service, mock_db, mock_onboarding):
    """Test retrying step when onboarding not failed."""
    # Set non-failed state
    mock_onboarding.state = OnboardingState.DOCUMENTS_PENDING

    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="Onboarding is not in failed state"):
        await onboarding_service.retry_failed_step(
            onboarding_id="onb_20260517014000_abc123",
            step="documents_validation",
        )


# Test: get_onboarding_by_lead
@pytest.mark.asyncio
async def test_get_onboarding_by_lead_success(onboarding_service, mock_db, mock_onboarding):
    """Test getting onboarding by lead successfully."""
    # Mock onboarding query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_onboarding
    mock_db.execute.return_value = mock_result

    # Get onboarding
    onboarding = await onboarding_service.get_onboarding_by_lead("lead_123")

    # Verify
    assert onboarding.id == "onb_20260517014000_abc123"
    assert onboarding.lead_id == "lead_123"


@pytest.mark.asyncio
async def test_get_onboarding_by_lead_not_found(onboarding_service, mock_db):
    """Test getting onboarding by lead when not found."""
    # Mock onboarding not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Verify error
    with pytest.raises(ValueError, match="No onboarding found for lead"):
        await onboarding_service.get_onboarding_by_lead("lead_999")
