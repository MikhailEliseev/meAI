"""Payment Service

Orchestrates payment processing with encryption and audit logging.

Part of: Phase 11 Sprint 3 - Task 3.1
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.payment import Payment
from aim.schemas.payment import (
    PaymentRecord,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentStatusResponse,
    RefundRequest,
    RefundResponse,
)
from aim.services.payment.helcim_client import HelcimClient
from aim.utils.encryption import FieldEncryption

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment processing service.

    Handles payment lifecycle:
    1. Encrypt customer data (ФЗ-152 compliance)
    2. Process payment via Helcim (stub)
    3. Store transaction record
    4. Track status and refunds
    """

    def __init__(
        self,
        db_session: AsyncSession,
        helcim_client: HelcimClient,
        encryption: Optional[FieldEncryption] = None,
    ):
        """Initialize payment service.

        Args:
            db_session: Database session
            helcim_client: Helcim payment client (stub)
            encryption: Field encryption utility
        """
        self.db = db_session
        self.helcim = helcim_client
        self.encryption = encryption or FieldEncryption()

    async def create_payment(
        self,
        request: PaymentRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PaymentResponse:
        """Create and process a payment.

        Args:
            request: Payment request data
            client_ip: Client IP address (for audit)
            user_agent: Client user agent (for audit)

        Returns:
            Payment response with transaction ID

        Raises:
            ValueError: If payment processing fails
        """
        # Generate payment ID
        payment_id = self._generate_payment_id()

        logger.info(
            f"Creating payment - id={payment_id}, amount={request.amount} {request.currency}"
        )

        try:
            # Process payment via Helcim (stub)
            helcim_response = await self.helcim.process_payment(
                amount=request.amount,
                currency=request.currency,
                card_number=request.card_number or "",
                card_expiry=request.card_expiry or "",
                card_cvv=request.card_cvv or "",
                customer_name=request.customer_name,
                customer_email=request.customer_email,
                customer_phone=request.customer_phone,
                metadata=request.metadata,
            )

            # Create payment record
            payment = Payment(
                id=payment_id,
                amount=request.amount,
                currency=request.currency,
                status=PaymentStatus.COMPLETED.value,  # Stub always succeeds
                payment_method=request.payment_method.value,
                customer_name_encrypted=self.encryption.encrypt(request.customer_name),
                customer_email_encrypted=self.encryption.encrypt(request.customer_email),
                customer_phone_encrypted=(
                    self.encryption.encrypt(request.customer_phone)
                    if request.customer_phone
                    else None
                ),
                card_last4=helcim_response.get("card_last4"),
                card_brand=helcim_response.get("card_brand"),
                external_transaction_id=helcim_response.get("transaction_id"),
                lead_id=request.lead_id,
                payment_metadata=request.metadata,
                completed_at=datetime.utcnow(),
                ip_address=client_ip,
                user_agent=user_agent,
            )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)

            logger.info(
                f"Payment created successfully - id={payment_id}, "
                f"external_id={payment.external_transaction_id}"
            )

            return PaymentResponse(
                payment_id=payment.id,
                status=PaymentStatus.COMPLETED,
                amount=payment.amount,
                currency=payment.currency,
                external_transaction_id=payment.external_transaction_id,
                created_at=payment.created_at,
                message="Payment processed successfully",
            )

        except Exception as e:
            logger.error(f"Payment processing failed - id={payment_id}: {e}")

            # Create failed payment record
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

            raise ValueError(f"Payment processing failed: {e}")

    async def get_payment_status(self, payment_id: str) -> PaymentStatusResponse:
        """Get payment status.

        Args:
            payment_id: Payment ID

        Returns:
            Payment status response

        Raises:
            ValueError: If payment not found
        """
        logger.info(f"Getting payment status - id={payment_id}")

        # Get payment from database
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

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

        # Process refund via Helcim (stub)
        try:
            helcim_response = await self.helcim.refund_payment(
                transaction_id=payment.external_transaction_id or "",
                amount=refund_amount,
                reason=request.reason,
            )

            # Update payment record
            payment.status = PaymentStatus.REFUNDED.value
            payment.refunded_amount = refund_amount
            payment.refund_reason = request.reason
            payment.refunded_at = datetime.utcnow()

            await self.db.commit()

            logger.info(
                f"Refund processed successfully - payment_id={request.payment_id}, "
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
            logger.error(f"Refund processing failed - payment_id={request.payment_id}: {e}")
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
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6]
        return f"pay_{timestamp}_{random_suffix}"
