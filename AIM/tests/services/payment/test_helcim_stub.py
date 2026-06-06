"""Tests for Helcim Client Stub

Part of: Phase 11 Sprint 3 - Task 3.1
"""

import pytest

from src.aim.services.payment.helcim_client import HelcimClient


@pytest.mark.asyncio
class TestHelcimClientStub:
    """Test suite for Helcim client stub."""

    async def test_initialization(self):
        """Test client initialization."""
        client = HelcimClient(api_key="test_key", test_mode=True)
        assert client.api_key == "test_key"
        assert client.test_mode is True

    async def test_process_payment_success(self):
        """Test successful payment processing (stub)."""
        client = HelcimClient(api_key="test_key")

        response = await client.process_payment(
            amount=1000.0,
            currency="RUB",
            card_number="4111111111111111",
            card_expiry="12/25",
            card_cvv="123",
            customer_name="Иван Иванов",
            customer_email="ivan@example.com",
            customer_phone="+79991234567",
        )

        assert response["success"] is True
        assert response["status"] == "completed"
        assert response["amount"] == 1000.0
        assert response["currency"] == "RUB"
        assert response["card_last4"] == "1111"
        assert response["card_brand"] == "visa"
        assert "transaction_id" in response
        assert response["transaction_id"].startswith("STUB-")

    async def test_process_payment_with_metadata(self):
        """Test payment processing with metadata."""
        client = HelcimClient(api_key="test_key")

        metadata = {"lead_id": "lead_123", "campaign": "summer_promo"}

        response = await client.process_payment(
            amount=500.0,
            currency="RUB",
            card_number="5555555555554444",
            card_expiry="06/26",
            card_cvv="456",
            customer_name="Мария Петрова",
            customer_email="maria@example.com",
            metadata=metadata,
        )

        assert response["success"] is True
        assert response["card_brand"] == "mastercard"

    async def test_check_payment_status(self):
        """Test payment status check (stub)."""
        client = HelcimClient(api_key="test_key")

        response = await client.check_payment_status(
            transaction_id="STUB-ABC123"
        )

        assert response["success"] is True
        assert response["status"] == "completed"
        assert response["transaction_id"] == "STUB-ABC123"

    async def test_refund_payment_full(self):
        """Test full payment refund (stub)."""
        client = HelcimClient(api_key="test_key")

        response = await client.refund_payment(
            transaction_id="STUB-ABC123",
            amount=1000.0,
            reason="Customer request",
        )

        assert response["success"] is True
        assert response["status"] == "refunded"
        assert response["transaction_id"] == "STUB-ABC123"
        assert response["refunded_amount"] == 1000.0
        assert "refund_id" in response
        assert response["refund_id"].startswith("REFUND-")

    async def test_refund_payment_partial(self):
        """Test partial payment refund (stub)."""
        client = HelcimClient(api_key="test_key")

        response = await client.refund_payment(
            transaction_id="STUB-ABC123",
            amount=500.0,
            reason="Partial refund",
        )

        assert response["success"] is True
        assert response["refunded_amount"] == 500.0

    async def test_detect_card_brand_visa(self):
        """Test Visa card detection."""
        client = HelcimClient(api_key="test_key")

        brand = client._detect_card_brand("4111111111111111")
        assert brand == "visa"

    async def test_detect_card_brand_mastercard(self):
        """Test Mastercard detection."""
        client = HelcimClient(api_key="test_key")

        # 51-55 range
        brand = client._detect_card_brand("5555555555554444")
        assert brand == "mastercard"

        # 2221-2720 range
        brand = client._detect_card_brand("2221000000000000")
        assert brand == "mastercard"

    async def test_detect_card_brand_mir(self):
        """Test Mir card detection."""
        client = HelcimClient(api_key="test_key")

        brand = client._detect_card_brand("2200000000000000")
        assert brand == "mir"

    async def test_detect_card_brand_unknown(self):
        """Test unknown card brand."""
        client = HelcimClient(api_key="test_key")

        brand = client._detect_card_brand("9999999999999999")
        assert brand == "unknown"

    async def test_close_client(self):
        """Test client close (no-op in stub)."""
        client = HelcimClient(api_key="test_key")
        await client.close()  # Should not raise
