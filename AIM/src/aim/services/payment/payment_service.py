"""Payment Service

Orchestrates payment processing with encryption and audit logging.
Uses YooKassa for real payment processing (redirect flow).

Part of: Phase 12 - Production Deployment
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.models.payment import Payment
from src.aim.schemas.payment import (
    PaymentRecord,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentStatusResponse,
    RefundRequest,
    RefundResponse,
)
from src.aim.services.payment.yookassa_client import YooKassaClient
from src.aim.utils.encryption import FieldEncryption

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment processing service.

    Handles payment lifecycle:
    1. Encrypt customer data (ФЗ-152 compliance)
    2. Create payment via YooKassa → get redirect URL
    3. User pays on YooKassa page → webhook updates status
    4. Track status and refunds
    """

    def __init__(
        self,
        db_session: AsyncSession,
        yookassa_client: YooKassaClient,
        encryption: Optional[FieldEncryption] = None,
    ):
        """Initialize payment service.

        Args:
            db_session: Database session
            yookassa_client: YooKassa payment client
            encryption: Field encryption utility
        """
        self.db = db_session
        self.yookassa = yookassa_client
        self.encryption = encryption or FieldEncryption()

    async def create_payment(
        self,
        request: PaymentRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PaymentResponse:
        """Create a payment via YooKassa redirect flow.

        YooKassa handles card data on its own page.
        We create the payment, get a confirmation_url, and redirect the user.
        Webhook updates the status when payment completes.

        Args:
            request: Payment request data
            client_ip: Client IP address (for audit)
            user_agent: Client user agent (for audit)

        Returns:
            PaymentResponse with confirmation_url for redirect

        Raises:
            ValueError: If payment creation fails
        """
        payment_id = self._generate_payment_id()

        logger.info(
            f"Creating payment - id={payment_id}, amount={request.amount} {request.currency}"
        )

        try:
            yookassa_response = await self.yookassa.create_payment(
                amount=request.amount,
                currency=request.currency,
                description=f"Clinic onboarding payment",
                customer_email=request.customer_email,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone,
                metadata=request.metadata,
            )

            confirmation_url = (
                yookassa_response.get("confirmation", {}).get("confirmation_url")
                if yookassa_response.get("confirmation")
                else None
            )

            payment = Payment(
                id=payment_id,
                amount=request.amount,
                currency=request.currency,
                status=PaymentStatus.PENDING.value,
                payment_method=request.payment_method.value,
                customer_name_encrypted=self.encryption.encrypt(request.customer_name),
                customer_email_encrypted=self.encryption.encrypt(request.customer_email),
                customer_phone_encrypted=(
                    self.encryption.encrypt(request.customer_phone)
                    if request.customer_phone
                    else None
                ),
                external_transaction_id=yookassa_response.get("id"),
                lead_id=request.lead_id,
                payment_metadata=request.metadata,
                ip_address=client_ip,
                user_agent=user_agent,
            )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)

            logger.info(
                f"Payment created - id={payment_id}, "
                f"yookassa_id={payment.external_transaction_id}, "
                f"status=pending"
            )

            return PaymentResponse(
                payment_id=payment.id,
                status=PaymentStatus.PENDING,
                amount=payment.amount,
                currency=payment.currency,
                external_transaction_id=payment.external_transaction_id,
                confirmation_url=confirmation_url,
                created_at=payment.created_at,
                message="Payment created. Redirect user to confirmation_url.",
            )

        except Exception as e:
            logger.error(f"Payment creation failed - id={payment_id}: {e}")

            payment = Payment(
                id=payment_id,
                amount=request.amount,
                currency=request.currency,
                status=PaymentStatus.FAILED.value,
                payment_method=request.payment_method.value,
                customer_name_encrypted=self.encryption.encrypt(request.customer_name),
                customer_email_encrypted=self.encryption.encrypt(request.customer_email),
                customer_phone_encrypted=(
                    self.encryption.encrypt(request.customer_phone)
                    if request.customer_phone
                    else None
                ),
                error_code="PROCESSING_ERROR",
                error_message=str(e)[:500],
                ip_address=client_ip,
                user_agent=user_agent,
            )

            self.db.add(payment)
            await self.db.commit()

            raise ValueError(f"Payment creation failed: {e}")

    async def get_payment_status(self, payment_id: str) -> PaymentStatusResponse:
        """Get payment status.

        For PENDING payments, checks YooKassa for the latest status
        and updates the DB record.

        Args:
            payment_id: Payment ID

        Returns:
            Payment status response

        Raises:
            ValueError: If payment not found
        """
        logger.info(f"Getting payment status - id={payment_id}")

        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        # For PENDING payments, sync with YooKassa
        if payment.status == PaymentStatus.PENDING.value and payment.external_transaction_id:
            try:
                yookassa_status = await self.yookassa.check_payment_status(
                    payment.external_transaction_id
                )
                yk_status = yookassa_status.get("status", "")

                if yk_status == "succeeded":
                    payment.status = PaymentStatus.COMPLETED.value
                    payment.completed_at = datetime.now(timezone.utc)
                elif yk_status == "canceled":
                    payment.status = PaymentStatus.FAILED.value
                    payment.error_message = "Payment canceled on YooKassa side"
                elif yk_status == "waiting_for_capture":
                    payment.status = PaymentStatus.PROCESSING.value

                await self.db.commit()
            except Exception as e:
                logger.warning(f"Failed to sync YooKassa status: {e}")

        return PaymentStatusResponse(
            payment_id=payment.id,
            status=PaymentStatus(payment.status),
            amount=payment.amount,
            currency=payment.currency,
            payment_method=payment.payment_method,
            card_last4=payment.card_last4,
            card_brand=payment.card_brand,
            external_transaction_id=payment.external_transaction_id,
            error_code=payment.error_code,
            error_message=payment.error_message,
            created_at=payment.created_at,
            completed_at=payment.completed_at,
        )

    async def refund_payment(self, request: RefundRequest) -> RefundResponse:
        """Refund a payment.

        Args:
            request: Refund request

        Returns:
            Refund response

        Raises:
            ValueError: If payment not found or refund fails
        """
        logger.info(
            f"Processing refund - payment_id={request.payment_id}, "
            f"amount={request.amount}"
        )

        # Get payment from database
        result = await self.db.execute(
            select(Payment).where(Payment.id == request.payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError(f"Payment not found: {request.payment_id}")

        if payment.status != PaymentStatus.COMPLETED.value:
            raise ValueError(f"Cannot refund payment with status: {payment.status}")

        # Determine refund amount
        refund_amount = request.amount or payment.amount

        if refund_amount > payment.amount:
            raise ValueError(
                f"Refund amount ({refund_amount}) exceeds payment amount ({payment.amount})"
            )

        # Process refund via YooKassa
        try:
            await self.yookassa.refund_payment(
                payment_id=payment.external_transaction_id or "",
                amount=refund_amount,
                reason=request.reason,
            )

            payment.status = PaymentStatus.REFUNDED.value
            payment.refunded_amount = refund_amount
            payment.refund_reason = request.reason
            payment.refunded_at = datetime.now(timezone.utc)

            await self.db.commit()

            logger.info(
                f"Refund processed - payment_id={request.payment_id}, "
                f"amount={refund_amount}"
            )

            return RefundResponse(
                payment_id=payment.id,
                refunded_amount=refund_amount,
                status=PaymentStatus.REFUNDED,
                refunded_at=payment.refunded_at,
                message="Refund processed successfully",
            )

        except Exception as e:
            logger.error(f"Refund failed - payment_id={request.payment_id}: {e}")
            raise ValueError(f"Refund processing failed: {e}")

    async def get_payment_record(self, payment_id: str) -> PaymentRecord:
        """Get payment record with decrypted data.

        Args:
            payment_id: Payment ID

        Returns:
            Payment record with decrypted customer data

        Raises:
            ValueError: If payment not found
        """
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        return PaymentRecord(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            status=PaymentStatus(payment.status),
            payment_method=payment.payment_method,
            customer_name=self.encryption.decrypt(payment.customer_name_encrypted),
            customer_email=self.encryption.decrypt(payment.customer_email_encrypted),
            customer_phone=(
                self.encryption.decrypt(payment.customer_phone_encrypted)
                if payment.customer_phone_encrypted
                else None
            ),
            card_last4=payment.card_last4,
            card_brand=payment.card_brand,
            external_transaction_id=payment.external_transaction_id,
            lead_id=payment.lead_id,
            metadata=payment.payment_metadata,
            error_code=payment.error_code,
            error_message=payment.error_message,
            refunded_amount=payment.refunded_amount,
            refund_reason=payment.refund_reason,
            refunded_at=payment.refunded_at,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            completed_at=payment.completed_at,
            created_by=payment.created_by,
            ip_address=payment.ip_address,
        )

    def _generate_payment_id(self) -> str:
        """Generate unique payment ID.

        Returns:
            Payment ID in format: pay_YYYYMMDDHHMMSS_random
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6]
        return f"pay_{timestamp}_{random_suffix}"
