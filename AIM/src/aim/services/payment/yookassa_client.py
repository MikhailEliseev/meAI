"""YooKassa Payment Client

Real payment processing via YooKassa for Russian market.
Uses async_yookassa library for API communication.

YooKassa uses a REDIRECT payment flow:
1. create_payment → returns confirmation_url
2. User redirected to YooKassa page to enter card details
3. YooKassa sends webhook notification with payment result

This client does NOT handle raw card data — YooKassa handles card data on their page.

Part of: Phase 12 - Production Deployment
"""

import logging
import os
from typing import Optional

from async_yookassa import YooKassaClient as AsyncYooKassaClient

logger = logging.getLogger(__name__)


class YooKassaClient:
    """Async YooKassa payment client.

    Thin wrapper around async_yookassa.YooKassaClient providing
    a simplified interface for our redirect payment flow.

    Usage:
        client = YooKassaClient(
            account_id="your_shop_id",
            secret_key="your_secret_key",
        )
        async with client:
            payment = await client.create_payment(
                amount=50000.00,
                currency="RUB",
                description="Clinic onboarding payment",
                customer_email="client@clinic.ru",
            )
            # Redirect user to payment["confirmation_url"]
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        return_url: Optional[str] = None,
        test_mode: bool = False,
    ):
        self.account_id = account_id or os.getenv("YOOKASSA_SHOP_ID", "")
        self.secret_key = secret_key or os.getenv("YOOKASSA_SECRET_KEY", "")
        self.return_url = return_url or os.getenv(
            "YOOKASSA_RETURN_URL", "https://iamaim.ru/payment/callback"
        )
        self.test_mode = test_mode

        if not self.account_id or not self.secret_key:
            raise ValueError(
                "YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY are required. "
                "Set them in .env or pass as constructor arguments."
            )

        api_url = "https://api.yookassa.ru/v3"
        self._client: Optional[AsyncYooKassaClient] = None
        self._api_url = api_url

        logger.info(
            "[YOOKASSA] Client initialized",
            extra={
                "account_id": self.account_id[:4] + "****" if self.account_id else "N/A",
                "return_url": self.return_url,
                "test_mode": self.test_mode,
            },
        )

    async def __aenter__(self):
        self._client = AsyncYooKassaClient(
            account_id=self.account_id,
            secret_key=self.secret_key,
            api_url=self._api_url,
        )
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.close()
            self._client = None

    def _ensure_client(self) -> AsyncYooKassaClient:
        if self._client is None:
            self._client = AsyncYooKassaClient(
                account_id=self.account_id,
                secret_key=self.secret_key,
                api_url=self._api_url,
            )
        return self._client

    async def create_payment(
        self,
        amount: float,
        currency: str = "RUB",
        description: str = "",
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a payment and get redirect URL.

        The user must be redirected to confirmation_url to enter card details.
        Our system never sees the card data.

        Returns:
            {
                "id": "2ab123...",          # YooKassa payment ID
                "status": "pending",
                "paid": False,
                "amount": {"value": "50000.00", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "confirmation_url": "https://yoomoney.ru/checkout/..."
                },
                "created_at": "2024-01-01T00:00:00.000Z",
                "description": "...",
                "metadata": {...},
                "test": True/False,
            }
        """
        client = self._ensure_client()

        amount_value = f"{amount:.2f}"

        payment_params = {
            "amount": {
                "value": amount_value,
                "currency": currency,
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": self.return_url,
            },
            "description": description[:128] if description else "",
        }

        if metadata:
            payment_params["metadata"] = metadata

        logger.info(
            "[YOOKASSA] Creating payment",
            extra={
                "amount": amount_value,
                "currency": currency,
                "description": description[:50],
            },
        )

        try:
            response = await client.payment.create(payment_params)

            result = {
                "id": response.id,
                "status": response.status.value,
                "paid": response.paid,
                "amount": {
                    "value": response.amount.value,
                    "currency": response.amount.currency,
                },
                "confirmation": {
                    "type": response.confirmation.type.value
                    if response.confirmation
                    else None,
                    "confirmation_url": response.confirmation.confirmation_url
                    if response.confirmation
                    else None,
                },
                "created_at": response.created_at.isoformat()
                if response.created_at
                else None,
                "description": response.description,
                "metadata": response.metadata,
                "test": response.test,
            }

            logger.info(
                "[YOOKASSA] Payment created",
                extra={
                    "payment_id": result["id"],
                    "status": result["status"],
                },
            )
            return result

        except Exception as e:
            logger.error(
                "[YOOKASSA] Payment creation failed",
                extra={"error": str(e), "amount": amount_value},
            )
            raise ValueError(f"YooKassa payment creation failed: {e}")

    async def check_payment_status(self, payment_id: str) -> dict:
        """Check payment status by YooKassa payment ID.

        Returns:
            {
                "id": "2ab123...",
                "status": "succeeded",
                "paid": True,
                "amount": {"value": "50000.00", "currency": "RUB"},
                "created_at": "2024-01-01T00:00:00.000Z",
                "captured_at": "2024-01-01T00:05:00.000Z",
                ...
            }
        """
        client = self._ensure_client()

        logger.info("[YOOKASSA] Checking payment status", extra={"payment_id": payment_id})

        try:
            response = await client.payment.find_one(payment_id)

            result = {
                "id": response.id,
                "status": response.status.value,
                "paid": response.paid,
                "amount": {
                    "value": response.amount.value,
                    "currency": response.amount.currency,
                },
                "created_at": response.created_at.isoformat()
                if response.created_at
                else None,
                "captured_at": response.captured_at.isoformat()
                if response.captured_at
                else None,
                "description": response.description,
                "metadata": response.metadata,
                "test": response.test,
                "cancellation_details": (
                    {
                        "party": response.cancellation_details.party,
                        "reason": response.cancellation_details.reason,
                    }
                    if response.cancellation_details
                    else None
                ),
            }

            logger.info(
                "[YOOKASSA] Payment status checked",
                extra={
                    "payment_id": payment_id,
                    "status": result["status"],
                },
            )
            return result

        except Exception as e:
            logger.error(
                "[YOOKASSA] Payment status check failed",
                extra={"payment_id": payment_id, "error": str(e)},
            )
            raise ValueError(f"YooKassa payment status check failed: {e}")

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> dict:
        """Create a refund for a payment.

        Returns:
            {
                "id": "refund_id",
                "payment_id": "...",
                "status": "succeeded",
                "amount": {"value": "50000.00", "currency": "RUB"},
                "created_at": "2024-01-01T00:00:00.000Z",
            }
        """
        client = self._ensure_client()

        amount_value = f"{amount:.2f}" if amount else None

        refund_params = {
            "payment_id": payment_id,
            "amount": {
                "value": amount_value or "0.00",
                "currency": "RUB",
            },
        }

        if reason:
            refund_params["description"] = reason[:250]

        logger.info(
            "[YOOKASSA] Creating refund",
            extra={
                "payment_id": payment_id,
                "amount": amount_value,
                "reason": reason[:50],
            },
        )

        try:
            response = await client.refund.create(refund_params)

            result = {
                "id": response.id,
                "payment_id": response.payment_id,
                "status": response.status.value,
                "amount": {
                    "value": response.amount.value,
                    "currency": response.amount.currency,
                },
                "created_at": response.created_at.isoformat()
                if response.created_at
                else None,
                "description": response.description,
            }

            logger.info(
                "[YOOKASSA] Refund created",
                extra={
                    "refund_id": result["id"],
                    "payment_id": payment_id,
                    "status": result["status"],
                },
            )
            return result

        except Exception as e:
            logger.error(
                "[YOOKASSA] Refund creation failed",
                extra={"payment_id": payment_id, "error": str(e)},
            )
            raise ValueError(f"YooKassa refund failed: {e}")

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("[YOOKASSA] Client closed")
