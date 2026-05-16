"""
Контур.Диадок API Client (STUB for Phase 12)

Russian e-signature service for contract signing.
This is a STUB implementation for development. Real integration in Phase 12.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()


class DocumentStatus(str, Enum):
    """Document status in Контур.Диадок"""
    DRAFT = "draft"
    SENT = "sent"
    DELIVERED = "delivered"
    SIGNED = "signed"
    DECLINED = "declined"
    EXPIRED = "expired"


class SignatureType(str, Enum):
    """Signature type"""
    SIMPLE = "simple"  # Простая электронная подпись
    ENHANCED = "enhanced"  # Усиленная неквалифицированная
    QUALIFIED = "qualified"  # Усиленная квалифицированная


class KontourClient:
    """
    Контур.Диадок API client for e-signatures

    STUB IMPLEMENTATION - Real integration in Phase 12
    """

    def __init__(
        self,
        api_key: str,
        organization_id: str,
        base_url: str = "https://diadoc-api.kontur.ru",
    ):
        self.api_key = api_key
        self.organization_id = organization_id
        self.base_url = base_url

        logger.warning(
            "kontour_client_stub",
            message="Using STUB implementation. Real integration in Phase 12.",
        )

    async def send_for_signature(
        self,
        document_path: str,
        recipient_email: str,
        recipient_name: str,
        recipient_inn: str,
        signature_type: SignatureType = SignatureType.ENHANCED,
        message: Optional[str] = None,
    ) -> str:
        """
        Send document for e-signature

        STUB: Returns mock document ID with 500ms delay

        Args:
            document_path: Path to PDF document
            recipient_email: Recipient email
            recipient_name: Recipient name
            recipient_inn: Recipient INN
            signature_type: Type of signature required
            message: Optional message to recipient

        Returns:
            Document ID in Контур.Диадок
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.5)

        # STUB: Generate mock document ID with microseconds for uniqueness
        document_id = f"STUB-DOC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        logger.info(
            "document_sent_for_signature_stub",
            document_id=document_id,
            recipient_email=recipient_email,
            signature_type=signature_type,
            stub=True,
        )

        # STUB: In real implementation, this would:
        # 1. Upload document to Контур.Диадок
        # 2. Create signature request
        # 3. Send notification to recipient
        # 4. Return real document ID

        return document_id

    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get document status

        STUB: Returns mock status data

        Args:
            document_id: Document ID

        Returns:
            Document status information
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.3)

        # STUB: Mock status based on document age
        # In real implementation, this would query Контур.Диадок API
        status = DocumentStatus.SENT

        if "SIGNED" in document_id:
            status = DocumentStatus.SIGNED
        elif "DECLINED" in document_id:
            status = DocumentStatus.DECLINED

        return {
            "document_id": document_id,
            "status": status,
            "sent_at": datetime.now().isoformat(),
            "delivered_at": (datetime.now() + timedelta(minutes=5)).isoformat() if status != DocumentStatus.DRAFT else None,
            "signed_at": (datetime.now() + timedelta(hours=2)).isoformat() if status == DocumentStatus.SIGNED else None,
            "declined_at": None,
            "decline_reason": None,
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            "stub": True,
        }

    async def download_signed_document(
        self,
        document_id: str,
    ) -> bytes:
        """
        Download signed document with signatures

        STUB: Returns mock PDF bytes

        Args:
            document_id: Document ID

        Returns:
            Signed document bytes
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.5)

        logger.info(
            "signed_document_downloaded_stub",
            document_id=document_id,
            stub=True,
        )

        # STUB: Return mock PDF bytes
        # In real implementation, this would download from Контур.Диадок
        return b"%PDF-1.4 STUB SIGNED DOCUMENT"

    async def get_signature_certificate(
        self,
        document_id: str,
    ) -> bytes:
        """
        Get signature certificate (proof of signing)

        STUB: Returns mock certificate bytes

        Args:
            document_id: Document ID

        Returns:
            Certificate bytes (PDF)
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.3)

        logger.info(
            "signature_certificate_downloaded_stub",
            document_id=document_id,
            stub=True,
        )

        # STUB: Return mock certificate
        return b"%PDF-1.4 STUB SIGNATURE CERTIFICATE"

    async def cancel_signature_request(
        self,
        document_id: str,
        reason: str,
    ) -> None:
        """
        Cancel signature request

        STUB: Logs cancellation

        Args:
            document_id: Document ID
            reason: Cancellation reason
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.3)

        logger.info(
            "signature_request_cancelled_stub",
            document_id=document_id,
            reason=reason,
            stub=True,
        )

    async def resend_notification(
        self,
        document_id: str,
    ) -> None:
        """
        Resend notification to recipient

        STUB: Logs resend

        Args:
            document_id: Document ID
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.3)

        logger.info(
            "notification_resent_stub",
            document_id=document_id,
            stub=True,
        )

    async def get_organization_info(self) -> Dict[str, Any]:
        """
        Get organization information from Контур.Диадок

        STUB: Returns mock organization data

        Returns:
            Organization information
        """
        # STUB: Simulate API delay
        import asyncio
        await asyncio.sleep(0.3)

        return {
            "organization_id": self.organization_id,
            "name": "ООО \"АИМ Маркетинг\"",
            "inn": "7701234567",
            "kpp": "770101001",
            "ogrn": "1234567890123",
            "address": "123456, г. Москва, ул. Примерная, д. 1, офис 100",
            "certificate_valid_until": (datetime.now() + timedelta(days=365)).isoformat(),
            "stub": True,
        }


class KontourWebhookHandler:
    """
    Handle Контур.Диадок webhook events

    STUB: Processes mock webhook events
    """

    def __init__(self, workflow_service):
        self.workflow = workflow_service

    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Handle Контур.Диадок webhook event

        STUB: Processes mock events

        Args:
            payload: Webhook payload
        """
        event_type = payload.get("event_type")
        document_id = payload.get("document_id")

        logger.info(
            "kontour_webhook_received_stub",
            event_type=event_type,
            document_id=document_id,
            stub=True,
        )

        # Map Контур.Диадок events to onboarding events
        if event_type == "document.signed":
            # Contract signed
            await self._handle_contract_signed(document_id, payload)

        elif event_type == "document.declined":
            # Contract declined
            await self._handle_contract_declined(document_id, payload)

        elif event_type == "document.expired":
            # Contract expired (not signed in time)
            logger.warning(
                "contract_expired_stub",
                document_id=document_id,
                stub=True,
            )

    async def _handle_contract_signed(
        self,
        document_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """Handle contract signed event"""
        # STUB: In real implementation, this would:
        # 1. Find onboarding session by document_id
        # 2. Trigger CONTRACT_SIGNED event
        # 3. Update session with signed document URL

        logger.info(
            "contract_signed_stub",
            document_id=document_id,
            stub=True,
        )

    async def _handle_contract_declined(
        self,
        document_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """Handle contract declined event"""
        decline_reason = payload.get("decline_reason", "No reason provided")

        logger.warning(
            "contract_declined_stub",
            document_id=document_id,
            reason=decline_reason,
            stub=True,
        )


# STUB: Helper functions for Phase 12 integration

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify Контур.Диадок webhook signature

    STUB: Always returns True

    Args:
        payload: Webhook payload bytes
        signature: Signature from header
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    # STUB: In real implementation, this would:
    # 1. Calculate HMAC-SHA256 of payload with secret
    # 2. Compare with provided signature
    # 3. Return True if match

    logger.warning(
        "webhook_signature_verification_stub",
        message="Signature verification skipped (STUB)",
        stub=True,
    )

    return True


def get_signature_type_for_amount(amount: float) -> SignatureType:
    """
    Get required signature type based on contract amount

    Russian law requirements:
    - < 100,000 RUB: Simple signature
    - 100,000 - 600,000 RUB: Enhanced unqualified
    - > 600,000 RUB: Qualified signature

    Args:
        amount: Contract amount in RUB

    Returns:
        Required signature type
    """
    if amount < 100_000:
        return SignatureType.SIMPLE
    elif amount < 600_000:
        return SignatureType.ENHANCED
    else:
        return SignatureType.QUALIFIED
