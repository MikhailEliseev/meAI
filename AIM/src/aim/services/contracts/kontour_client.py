"""Контур.Диадок API Client

Real REST API client for Russian e-signature service.
Uses KontourAuth for OIDC token management and httpx for API calls.

Part of: Phase 12-02 — Контур.Диадок integration
"""

import base64
import os
from enum import Enum
from typing import Any, Optional

import httpx
import structlog

from src.aim.services.contracts.kontour_auth import KontourAuth

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
    """Signature type per Russian law"""
    SIMPLE = "simple"
    ENHANCED = "enhanced"
    QUALIFIED = "qualified"


STATUS_MAP = {
    "Draft": DocumentStatus.DRAFT,
    "Sent": DocumentStatus.SENT,
    "Delivered": DocumentStatus.DELIVERED,
    "Signed": DocumentStatus.SIGNED,
    "Declined": DocumentStatus.DECLINED,
}


class KontourClient:
    """Контур.Диадок API client for e-signatures.

    Uses KontourAuth for OIDC token lifecycle.
    All methods perform real httpx API calls.
    """

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        organization_inn: str = "",
        base_url: str = "https://diadoc-api.kontur.ru",
        test_mode: bool = False,
    ):
        self.client_id = client_id or os.getenv("KONTOUR_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("KONTOUR_CLIENT_SECRET", "")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "KONTOUR_CLIENT_ID and KONTOUR_CLIENT_SECRET are required. "
                "Set them in .env or pass directly."
            )
        self.auth = KontourAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self.organization_inn = organization_inn or os.getenv(
            "KONTOUR_ORGANIZATION_INN", ""
        )
        self.base_url = base_url
        self.test_mode = test_mode
        self._box_id: str | None = None
        self._client = httpx.AsyncClient(timeout=60.0)
        logger.info("kontour_client_initialized", test_mode=test_mode)

    async def _get_headers(self) -> dict:
        token = await self.auth.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _get_box_id(self) -> str:
        """Lazy init — fetch box ID from GetMyOrganizations."""
        if not self._box_id:
            headers = await self._get_headers()
            resp = await self._client.get(
                f"{self.base_url}/GetMyOrganizations", headers=headers
            )
            resp.raise_for_status()
            orgs = resp.json()
            if self.organization_inn:
                for org in orgs:
                    if org.get("Inn") == self.organization_inn:
                        self._box_id = org["BoxId"]
                        break
                if not self._box_id:
                    raise ValueError(
                        f"Organization with INN {self.organization_inn} not found"
                    )
            else:
                self._box_id = orgs[0]["BoxId"]
                logger.warning(
                    "kontour_no_inn_using_first_org",
                    org_name=orgs[0].get("Name", "unknown"),
                )
        return self._box_id

    async def send_for_signature(
        self,
        document_path: str,
        recipient_email: str,
        recipient_name: str,
        recipient_inn: str,
        signature_type: SignatureType = SignatureType.ENHANCED,
        message: Optional[str] = None,
    ) -> str:
        """Send document for e-signature via PostMessage."""
        box_id = await self._get_box_id()

        # Find recipient by INN
        headers = await self._get_headers()
        recipient_resp = await self._client.get(
            f"{self.base_url}/GetOrganizationsByInnKpp",
            params={"inn": recipient_inn},
            headers=headers,
        )
        recipient_resp.raise_for_status()
        recipients = recipient_resp.json()
        if not recipients:
            raise ValueError(f"Recipient not found for INN: {recipient_inn}")
        recipient_box_id = recipients[0]["BoxId"]

        # Read and encode document
        with open(document_path, "rb") as f:
            document_content = f.read()

        payload = {
            "BoxId": box_id,
            "Recipients": [{"BoxId": recipient_box_id}],
            "Documents": [
                {
                    "FileName": os.path.basename(document_path),
                    "Content": base64.b64encode(document_content).decode(),
                    "TypeNamedId": "Nonformalized",
                }
            ],
            "MessageText": message
            or f"Договор на подписание для {recipient_name}",
        }
        resp = await self._client.post(
            f"{self.base_url}/V3/PostMessage",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        result = resp.json()
        document_id = result["EntityId"]

        logger.info(
            "document_sent_for_signature",
            document_id=document_id,
            recipient_inn=recipient_inn,
            signature_type=signature_type,
        )
        return document_id

    async def get_document_status(self, document_id: str) -> dict[str, Any]:
        """Get document status via GetDocument."""
        box_id = await self._get_box_id()
        headers = await self._get_headers()
        resp = await self._client.get(
            f"{self.base_url}/V3/GetDocument",
            params={
                "boxId": box_id,
                "messageId": document_id,
                "entityId": document_id,
            },
            headers=headers,
        )
        resp.raise_for_status()
        doc = resp.json()
        diadoc_status = doc.get("Status", "Draft")
        return {
            "document_id": document_id,
            "status": STATUS_MAP.get(diadoc_status, DocumentStatus.DRAFT),
            "diadoc_status": diadoc_status,
            "sent_at": doc.get("SentAt"),
            "delivered_at": doc.get("DeliveredAt"),
            "signed_at": doc.get("SignedAt"),
            "expires_at": doc.get("ExpiresAt"),
        }

    async def download_signed_document(self, document_id: str) -> bytes:
        """Download signed document via GetEntityContent."""
        box_id = await self._get_box_id()
        headers = await self._get_headers()
        resp = await self._client.get(
            f"{self.base_url}/V4/GetEntityContent",
            params={
                "boxId": box_id,
                "messageId": document_id,
                "entityId": document_id,
            },
            headers=headers,
        )
        resp.raise_for_status()
        return resp.content

    async def get_signature_certificate(self, document_id: str) -> bytes:
        """Get signature certificate (proof of signing) via GetSignatureInfo."""
        box_id = await self._get_box_id()
        headers = await self._get_headers()
        resp = await self._client.get(
            f"{self.base_url}/GetSignatureInfo",
            params={
                "boxId": box_id,
                "messageId": document_id,
                "entityId": document_id,
            },
            headers=headers,
        )
        resp.raise_for_status()
        return resp.content

    async def cancel_signature_request(
        self, document_id: str, reason: str
    ) -> None:
        """Cancel a signature request."""
        box_id = await self._get_box_id()
        headers = await self._get_headers()
        resp = await self._client.post(
            f"{self.base_url}/CancelSignatureRequest",
            json={
                "BoxId": box_id,
                "MessageId": document_id,
                "Reason": reason,
            },
            headers=headers,
        )
        resp.raise_for_status()
        logger.info(
            "signature_request_cancelled",
            document_id=document_id,
            reason=reason,
        )

    async def resend_notification(self, document_id: str) -> None:
        """Resend notification to recipient."""
        box_id = await self._get_box_id()
        headers = await self._get_headers()
        resp = await self._client.post(
            f"{self.base_url}/ResendNotification",
            json={"BoxId": box_id, "MessageId": document_id},
            headers=headers,
        )
        resp.raise_for_status()
        logger.info("notification_resent", document_id=document_id)

    async def get_organization_info(self) -> dict[str, Any]:
        """Get organization information from GetMyOrganizations."""
        headers = await self._get_headers()
        resp = await self._client.get(
            f"{self.base_url}/GetMyOrganizations", headers=headers
        )
        resp.raise_for_status()
        orgs = resp.json()
        if not orgs:
            raise ValueError("No organizations found")
        target_inn = self.organization_inn
        target = None
        if target_inn:
            for org in orgs:
                if org.get("Inn") == target_inn:
                    target = org
                    break
        if not target:
            target = orgs[0]
        return {
            "organization_id": target.get("BoxId", ""),
            "name": target.get("Name", ""),
            "inn": target.get("Inn", ""),
            "kpp": target.get("Kpp", ""),
            "ogrn": target.get("Ogrn", ""),
            "address": target.get("Address", ""),
            "certificate_valid_until": target.get("CertificateValidUntil"),
        }

    async def close(self) -> None:
        """Close HTTP client and auth."""
        await self._client.aclose()
        await self.auth.close()


# ── Webhook utilities (DEPRECATED) ──────────────────────────────────────────
# Контур.Диадок uses POLLING (GetNewEvents V8), not webhooks.
# KontourWebhookHandler is replaced by KontourPoller.
# verify_webhook_signature is kept for backward compatibility with
# the __init__.py export but is not used in new code.


class KontourWebhookHandler:
    """DEPRECATED. Replaced by KontourPoller (kontour_poller.py).

    Контур.Диадок does NOT support webhooks — polling-based only.
    This class is kept for backward compatibility but does nothing.
    """

    def __init__(self, workflow_service=None):
        self.workflow = workflow_service
        logger.warning(
            "KontourWebhookHandler is deprecated. Use KontourPoller instead."
        )

    async def handle_webhook(self, payload: dict[str, Any]) -> None:
        """No-op. Контур.Диадок has no webhooks."""
        logger.warning(
            "kontour_webhook_deprecated",
            message="Контур.Диадок uses polling, not webhooks. "
            "This handler is a no-op.",
        )


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """DEPRECATED. Контур.Диадок has no webhooks (polling-based).

    Kept for backward compatibility. Always returns True.
    """
    return True


def get_signature_type_for_amount(amount: float) -> SignatureType:
    """Get required signature type based on contract amount.

    Russian law requirements:
    - < 100,000 RUB: Simple signature
    - 100,000 - 600,000 RUB: Enhanced unqualified
    - > 600,000 RUB: Qualified signature
    """
    if amount < 100_000:
        return SignatureType.SIMPLE
    elif amount < 600_000:
        return SignatureType.ENHANCED
    else:
        return SignatureType.QUALIFIED
