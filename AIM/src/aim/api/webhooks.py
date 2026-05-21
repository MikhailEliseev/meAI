"""YooKassa Webhook Handler

Receives payment notifications from YooKassa.
YooKassa retries for 24h if no HTTP 200 response.

Webhook security:
- Validates source IP against YooKassa IP ranges (production only)
- Looks up payment by external_transaction_id (YooKassa payment ID)
- Only updates status, cannot create new payments

Part of: Phase 12 - Production Deployment
"""

import ipaddress
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from aim.database import async_session_maker
from aim.models.payment import Payment
from aim.schemas.payment import PaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

YOOKASSA_IP_RANGES = [
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.154.128/25",
    "77.75.156.0/25",
    "77.75.156.128/25",
    "2a02:5180::/32",
]


def _is_yookassa_ip(client_ip: str) -> bool:
    """Check if client IP belongs to YooKassa IP ranges."""
    try:
        ip = ipaddress.ip_address(client_ip)
        for cidr in YOOKASSA_IP_RANGES:
            if ip in ipaddress.ip_network(cidr):
                return True
        return False
    except ValueError:
        return False


@router.post("/yookassa/payment", status_code=status.HTTP_200_OK)
async def yookassa_payment_webhook(request: Request):
    """Handle YooKassa payment webhook.

    Events: payment.succeeded, payment.waiting_for_capture,
            payment.canceled, refund.succeeded

    YooKassa resends every 10 minutes for 24 hours if no HTTP 200.
    """
    client_ip = request.client.host if request.client else "unknown"

    if os.getenv("ENVIRONMENT") == "production":
        if not _is_yookassa_ip(client_ip):
            logger.warning(f"Webhook rejected from non-YooKassa IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Forbidden IP")

    payload = await request.json()
    event = payload.get("event", "")
    payment_object = payload.get("object", {})
    payment_id = payment_object.get("id", "")
    payment_status = payment_object.get("status", "")

    logger.info(
        f"YooKassa webhook: event={event}, payment_id={payment_id}, "
        f"status={payment_status}"
    )

    async with async_session_maker() as db:
        result = await db.execute(
            select(Payment).where(Payment.external_transaction_id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            logger.warning(f"Payment not found for YooKassa ID: {payment_id}")
            raise HTTPException(status_code=404, detail="Payment not found")

        if event == "payment.succeeded":
            payment.status = PaymentStatus.COMPLETED.value
            payment.completed_at = datetime.now(timezone.utc)
        elif event == "payment.canceled":
            payment.status = PaymentStatus.FAILED.value
            payment.error_message = "Payment canceled by user"
        elif event == "payment.waiting_for_capture":
            payment.status = PaymentStatus.PROCESSING.value
        elif event == "refund.succeeded":
            payment.status = PaymentStatus.REFUNDED.value
            payment.refunded_at = datetime.now(timezone.utc)

        await db.commit()

    return {"status": "ok"}
