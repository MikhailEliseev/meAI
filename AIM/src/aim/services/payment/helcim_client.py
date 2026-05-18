"""Helcim Payment Processor Client

DEPRECATED: Replaced by YooKassaClient (yookassa_client.py).
Helcim is a US payment processor that does not operate in Russia.
Kept for reference only. Use YooKassaClient for all payment processing.
Will be removed in a future cleanup.

Part of: Phase 11 Sprint 3 - Task 3.1 (DEPRECATED in Phase 12)
"""

import logging
import warnings

warnings.warn(
    "HelcimClient is deprecated. Use YooKassaClient instead.",
    DeprecationWarning,
    stacklevel=2,
)
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class HelcimClient:
    """Helcim payment processor client (STUB).

    IMPORTANT: This is a STUB implementation for development only.
    Real payment processing will be implemented with ЮKassa in Phase 12.

    All methods return mock success responses.
    No actual payment processing occurs.
    """

    def __init__(self, api_key: str, test_mode: bool = True):
        """Initialize Helcim client stub.

        Args:
            api_key: API key (not used in stub)
            test_mode: Test mode flag (always True in stub)
        """
        self.api_key = api_key
        self.test_mode = True  # Always test mode in stub
        logger.info("HelcimClient initialized (STUB MODE)")
        logger.warning(
            "STUB: Using mock Helcim client. "
            "Replace with ЮKassa in Phase 12 for production."
        )

    async def process_payment(
        self,
        amount: float,
        currency: str,
        card_number: str,
        card_expiry: str,
        card_cvv: str,
        customer_name: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Process a payment (STUB).

        STUB: Always returns success with mock transaction ID.
        No actual payment processing occurs.

        Args:
            amount: Payment amount
            currency: Currency code (RUB)
            card_number: Card number
            card_expiry: Card expiry (MM/YY)
            card_cvv: Card CVV
            customer_name: Customer name
            customer_email: Customer email
            customer_phone: Customer phone (optional)
            metadata: Additional metadata (optional)

        Returns:
            Mock payment response with success status
        """
        logger.info(
            f"STUB: Processing payment - amount={amount} {currency}, "
            f"customer={customer_email}"
        )

        # Generate mock transaction ID
        transaction_id = f"STUB-{uuid.uuid4().hex[:16].upper()}"

        # Extract card info
        card_last4 = card_number[-4:]
        card_brand = self._detect_card_brand(card_number)

        # Mock response
        response = {
            "success": True,
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": amount,
            "currency": currency,
            "card_last4": card_last4,
            "card_brand": card_brand,
            "processed_at": datetime.utcnow().isoformat(),
            "message": "Payment processed successfully (STUB)",
        }

        logger.info(f"STUB: Payment successful - transaction_id={transaction_id}")
        return response

    async def check_payment_status(self, transaction_id: str) -> dict:
        """Check payment status (STUB).

        STUB: Always returns completed status for any transaction ID.

        Args:
            transaction_id: Transaction ID to check

        Returns:
            Mock status response
        """
        logger.info(f"STUB: Checking payment status - transaction_id={transaction_id}")

        response = {
            "success": True,
            "transaction_id": transaction_id,
            "status": "completed",
            "message": "Payment completed (STUB)",
        }

        return response

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> dict:
        """Refund a payment (STUB).

        STUB: Always returns success for refund requests.

        Args:
            transaction_id: Original transaction ID
            amount: Refund amount (None for full refund)
            reason: Refund reason

        Returns:
            Mock refund response
        """
        logger.info(
            f"STUB: Processing refund - transaction_id={transaction_id}, "
            f"amount={amount}, reason={reason}"
        )

        refund_id = f"REFUND-{uuid.uuid4().hex[:16].upper()}"

        response = {
            "success": True,
            "refund_id": refund_id,
            "transaction_id": transaction_id,
            "status": "refunded",
            "refunded_amount": amount,
            "refunded_at": datetime.utcnow().isoformat(),
            "message": "Refund processed successfully (STUB)",
        }

        logger.info(f"STUB: Refund successful - refund_id={refund_id}")
        return response

    def _detect_card_brand(self, card_number: str) -> str:
        """Detect card brand from card number.

        Args:
            card_number: Card number

        Returns:
            Card brand (visa, mastercard, mir, unknown)
        """
        # Remove spaces and dashes
        digits = "".join(c for c in card_number if c.isdigit())

        # Visa: starts with 4
        if digits.startswith("4"):
            return "visa"

        # Mastercard: starts with 51-55 or 2221-2720
        if digits.startswith(("51", "52", "53", "54", "55")):
            return "mastercard"
        if digits.startswith("22") and 2221 <= int(digits[:4]) <= 2720:
            return "mastercard"

        # Mir: starts with 2200-2204
        if digits.startswith("220") and 2200 <= int(digits[:4]) <= 2204:
            return "mir"

        return "unknown"

    async def close(self) -> None:
        """Close client connection (STUB).

        STUB: No-op, no actual connection to close.
        """
        logger.info("STUB: Closing HelcimClient (no-op)")
