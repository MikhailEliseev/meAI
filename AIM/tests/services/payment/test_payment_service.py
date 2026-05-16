"""Tests for Payment Service

Part of: Phase 11 Sprint 3 - Task 3.1
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.payment import Payment
from aim.schemas.payment import (
    PaymentMethod,
    PaymentRequest,
    PaymentStatus,
    RefundRequest,
)
from aim.services.payment.helcim_client import HelcimClient
from aim.services.payment.payment_service import PaymentService
from aim.utils.encryption import FieldEncryption


@pytest.fixture
def encryption():
    """Encryption utility fixture."""
    return FieldEncryption()


@pytest.fixture
def helcim_client():
    """Helcim client stub fixture."""
    return HelcimClient(api_key="test_key", test_mode=True)


@pytest.fixture
def payment_service(db_session: AsyncSession, helcim_client: HelcimClient, encryption: FieldEncryption):
    """Payment service fixture."""
    return PaymentService(
        db_session=db_session,
        helcim_client=helcim_client,
        encryption=encryption,
    )


@pytest.mark.asyncio
class TestPaymentService:
    """Test suite for Payment Service."""

    async def test_create_payment_success(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test successful payment creation."""
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            customer_phone="+79991234567",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        response = await payment_service.create_payment(
            request=request,
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert response.status == PaymentStatus.COMPLETED
        assert response.amount == 1000.0
        assert response.currency == "RUB"
        assert response.payment_id.startswith("pay_")
        assert response.external_transaction_id.startswith("STUB-")

        # Verify payment stored in database
        payment = await db_session.get(Payment, response.payment_id)
        assert payment is not None
        assert payment.amount == 1000.0
        assert payment.status == PaymentStatus.COMPLETED.value
        assert payment.card_last4 == "1111"
        assert payment.card_brand == "visa"
        assert payment.ip_address == "192.168.1.1"

    async def test_create_payment_with_lead_id(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test payment creation with lead reference."""
        request = PaymentRequest(
            amount=500.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Мария Петрова",
            customer_email="maria@example.com",
            card_number="5555555555554444",
            card_expiry="06/26",
            card_cvv="456",
            lead_id="lead_123",
        )

        response = await payment_service.create_payment(request=request)

        assert response.status == PaymentStatus.COMPLETED

        # Verify lead_id stored
        payment = await db_session.get(Payment, response.payment_id)
        assert payment.lead_id == "lead_123"

    async def test_create_payment_with_metadata(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test payment creation with metadata."""
        metadata = {"campaign": "summer_promo", "source": "landing_page"}

        request = PaymentRequest(
            amount=750.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Петр Сидоров",
            customer_email="petr@example.com",
            card_number="4111111111111111",
            card_expiry="03/27",
            card_cvv="789",
            metadata=metadata,
        )

        response = await payment_service.create_payment(request=request)

        # Verify metadata stored
        payment = await db_session.get(Payment, response.payment_id)
        assert payment.payment_metadata == metadata

    async def test_get_payment_status(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test payment status retrieval."""
        # Create payment first
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        create_response = await payment_service.create_payment(request=request)

        # Get status
        status_response = await payment_service.get_payment_status(
            create_response.payment_id
        )

        assert status_response.payment_id == create_response.payment_id
        assert status_response.status == PaymentStatus.COMPLETED
        assert status_response.amount == 1000.0
        assert status_response.currency == "RUB"
        assert status_response.card_last4 == "1111"
        assert status_response.card_brand == "visa"

    async def test_get_payment_status_not_found(
        self,
        payment_service: PaymentService,
    ):
        """Test payment status for non-existent payment."""
        with pytest.raises(ValueError, match="Payment not found"):
            await payment_service.get_payment_status("pay_nonexistent")

    async def test_refund_payment_full(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test full payment refund."""
        # Create payment first
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        create_response = await payment_service.create_payment(request=request)

        # Refund payment
        refund_request = RefundRequest(
            payment_id=create_response.payment_id,
            reason="Customer request",
        )

        refund_response = await payment_service.refund_payment(refund_request)

        assert refund_response.payment_id == create_response.payment_id
        assert refund_response.status == PaymentStatus.REFUNDED
        assert refund_response.refunded_amount == 1000.0

        # Verify payment updated in database
        payment = await db_session.get(Payment, create_response.payment_id)
        assert payment.status == PaymentStatus.REFUNDED.value
        assert payment.refunded_amount == 1000.0
        assert payment.refund_reason == "Customer request"
        assert payment.refunded_at is not None

    async def test_refund_payment_partial(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test partial payment refund."""
        # Create payment first
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        create_response = await payment_service.create_payment(request=request)

        # Partial refund
        refund_request = RefundRequest(
            payment_id=create_response.payment_id,
            amount=500.0,
            reason="Partial refund",
        )

        refund_response = await payment_service.refund_payment(refund_request)

        assert refund_response.refunded_amount == 500.0

        # Verify payment updated
        payment = await db_session.get(Payment, create_response.payment_id)
        assert payment.refunded_amount == 500.0

    async def test_refund_payment_not_found(
        self,
        payment_service: PaymentService,
    ):
        """Test refund for non-existent payment."""
        refund_request = RefundRequest(
            payment_id="pay_nonexistent",
            reason="Test refund for non-existent payment",
        )

        with pytest.raises(ValueError, match="Payment not found"):
            await payment_service.refund_payment(refund_request)

    async def test_refund_payment_invalid_status(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
    ):
        """Test refund for payment with invalid status."""
        # Create failed payment
        payment = Payment(
            id="pay_failed",
            amount=1000.0,
            currency="RUB",
            status=PaymentStatus.FAILED.value,
            payment_method="card",
            customer_name_encrypted="encrypted",
            customer_email_encrypted="encrypted",
        )
        db_session.add(payment)
        await db_session.commit()

        # Try to refund
        refund_request = RefundRequest(
            payment_id="pay_failed",
            reason="Test refund for invalid status",
        )

        with pytest.raises(ValueError, match="Cannot refund payment with status"):
            await payment_service.refund_payment(refund_request)

    async def test_refund_amount_exceeds_payment(
        self,
        payment_service: PaymentService,
    ):
        """Test refund amount exceeding payment amount."""
        # Create payment first
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        create_response = await payment_service.create_payment(request=request)

        # Try to refund more than payment amount
        refund_request = RefundRequest(
            payment_id=create_response.payment_id,
            amount=2000.0,
            reason="Test refund exceeding payment amount",
        )

        with pytest.raises(ValueError, match="Refund amount .* exceeds payment amount"):
            await payment_service.refund_payment(refund_request)

    async def test_get_payment_record(
        self,
        payment_service: PaymentService,
        encryption: FieldEncryption,
    ):
        """Test payment record retrieval with decrypted data."""
        # Create payment first
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            customer_phone="+79991234567",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        create_response = await payment_service.create_payment(request=request)

        # Get payment record
        record = await payment_service.get_payment_record(create_response.payment_id)

        assert record.id == create_response.payment_id
        assert record.customer_name == "Иван Иванов"
        assert record.customer_email == "ivan@example.com"
        assert record.customer_phone == "+79991234567"
        assert record.amount == 1000.0
        assert record.status == PaymentStatus.COMPLETED

    async def test_get_payment_record_not_found(
        self,
        payment_service: PaymentService,
    ):
        """Test payment record retrieval for non-existent payment."""
        with pytest.raises(ValueError, match="Payment not found"):
            await payment_service.get_payment_record("pay_nonexistent")

    async def test_payment_id_generation(
        self,
        payment_service: PaymentService,
    ):
        """Test payment ID generation format."""
        payment_id = payment_service._generate_payment_id()

        assert payment_id.startswith("pay_")
        assert len(payment_id) == 25  # pay_ + 14 digits + _ + 6 hex chars

    async def test_encryption_of_customer_data(
        self,
        payment_service: PaymentService,
        db_session: AsyncSession,
        encryption: FieldEncryption,
    ):
        """Test customer data is encrypted in database."""
        request = PaymentRequest(
            amount=1000.0,
            currency="RUB",
            payment_method=PaymentMethod.CARD,
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            customer_phone="+79991234567",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
        )

        response = await payment_service.create_payment(request=request)

        # Get payment from database
        payment = await db_session.get(Payment, response.payment_id)

        # Verify data is encrypted
        assert payment.customer_name_encrypted != "Иван Иванов"
        assert payment.customer_email_encrypted != "ivan@example.com"
        assert payment.customer_phone_encrypted != "+79991234567"

        # Verify decryption works
        assert encryption.decrypt(payment.customer_name_encrypted) == "Иван Иванов"
        assert encryption.decrypt(payment.customer_email_encrypted) == "ivan@example.com"
        assert encryption.decrypt(payment.customer_phone_encrypted) == "+79991234567"
