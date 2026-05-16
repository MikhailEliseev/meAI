"""
DocuSign API Client

Handles electronic signature workflows for HIPAA BAA (Business Associate Agreement).

Features:
- Send BAA for signature
- Track signature status
- Download signed documents
- Webhook handling for status updates
- Audit trail
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class DocuSignConfig(BaseModel):
    """DocuSign configuration"""
    account_id: str
    integration_key: str
    user_id: str
    private_key: str
    base_url: str = "https://demo.docusign.net/restapi"  # Use demo for testing
    oauth_base_url: str = "https://account-d.docusign.com"


class EnvelopeStatus(BaseModel):
    """Envelope status"""
    envelope_id: str
    status: str  # sent, delivered, completed, declined, voided
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None


class DocuSignClient:
    """
    DocuSign API client for BAA signature workflow

    Handles sending BAA documents for electronic signature and tracking status.
    """

    def __init__(self, config: DocuSignConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """Get JWT access token"""
        if self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token

        # Request JWT token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.oauth_base_url}/oauth/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": self._create_jwt_assertion(),
                },
            )
            response.raise_for_status()
            data = response.json()

            self.access_token = data["access_token"]
            # Token expires in 1 hour, refresh 5 minutes early
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 300)

            logger.info("docusign_token_refreshed")

            return self.access_token

    def _create_jwt_assertion(self) -> str:
        """Create JWT assertion for authentication"""
        # TODO: Implement JWT creation with private key
        # For now, return placeholder
        return "jwt_assertion_placeholder"

    async def send_baa(
        self,
        recipient_email: str,
        recipient_name: str,
        practice_name: str,
        template_id: Optional[str] = None,
    ) -> str:
        """
        Send BAA document for signature

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient full name
            practice_name: Practice/clinic name
            template_id: DocuSign template ID (optional)

        Returns:
            Envelope ID
        """
        token = await self._get_access_token()

        # Create envelope definition
        envelope_definition = {
            "emailSubject": f"HIPAA Business Associate Agreement - {practice_name}",
            "status": "sent",
            "templateId": template_id or "default-baa-template",
            "templateRoles": [
                {
                    "email": recipient_email,
                    "name": recipient_name,
                    "roleName": "Client",
                    "tabs": {
                        "textTabs": [
                            {
                                "tabLabel": "practice_name",
                                "value": practice_name,
                            },
                            {
                                "tabLabel": "date",
                                "value": datetime.utcnow().strftime("%Y-%m-%d"),
                            },
                        ],
                    },
                }
            ],
        }

        # Send envelope
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.base_url}/v2.1/accounts/{self.config.account_id}/envelopes",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=envelope_definition,
            )
            response.raise_for_status()
            data = response.json()

            envelope_id = data["envelopeId"]

            logger.info(
                "baa_sent",
                envelope_id=envelope_id,
                recipient_email=recipient_email,
                practice_name=practice_name,
            )

            return envelope_id

    async def get_envelope_status(self, envelope_id: str) -> EnvelopeStatus:
        """Get envelope status"""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.base_url}/v2.1/accounts/{self.config.account_id}/envelopes/{envelope_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()

            return EnvelopeStatus(
                envelope_id=envelope_id,
                status=data["status"],
                sent_at=self._parse_datetime(data.get("sentDateTime")),
                delivered_at=self._parse_datetime(data.get("deliveredDateTime")),
                signed_at=self._parse_datetime(data.get("completedDateTime")),
                declined_at=self._parse_datetime(data.get("declinedDateTime")),
                decline_reason=data.get("declineReason"),
            )

    async def download_signed_document(
        self,
        envelope_id: str,
        document_id: str = "combined",
    ) -> bytes:
        """Download signed document"""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.base_url}/v2.1/accounts/{self.config.account_id}/envelopes/{envelope_id}/documents/{document_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

            logger.info(
                "document_downloaded",
                envelope_id=envelope_id,
                document_id=document_id,
            )

            return response.content

    async def get_audit_trail(self, envelope_id: str) -> bytes:
        """Get audit trail (certificate of completion)"""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.base_url}/v2.1/accounts/{self.config.account_id}/envelopes/{envelope_id}/documents/certificate",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

            return response.content

    async def void_envelope(
        self,
        envelope_id: str,
        reason: str,
    ) -> None:
        """Void an envelope"""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.config.base_url}/v2.1/accounts/{self.config.account_id}/envelopes/{envelope_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "status": "voided",
                    "voidedReason": reason,
                },
            )
            response.raise_for_status()

            logger.info(
                "envelope_voided",
                envelope_id=envelope_id,
                reason=reason,
            )

    async def resend_envelope(self, envelope_id: str) -> None:
        """Resend envelope notification"""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.config.base_url}/v2.1/accounts/{self.config.account_id}/envelopes/{envelope_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"resendEnvelope": "true"},
            )
            response.raise_for_status()

            logger.info("envelope_resent", envelope_id=envelope_id)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse DocuSign datetime string"""
        if not dt_str:
            return None

        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None


class DocuSignWebhookHandler:
    """
    Handle DocuSign webhook events

    Processes status updates from DocuSign Connect.
    """

    def __init__(self, workflow_service):
        self.workflow = workflow_service

    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """Handle DocuSign webhook event"""
        event_type = payload.get("event")
        envelope_id = payload.get("envelopeId")

        logger.info(
            "docusign_webhook_received",
            event_type=event_type,
            envelope_id=envelope_id,
        )

        # Map DocuSign events to onboarding events
        if event_type == "envelope-completed":
            # BAA signed
            await self._handle_baa_signed(envelope_id, payload)

        elif event_type == "envelope-declined":
            # BAA declined
            await self._handle_baa_declined(envelope_id, payload)

        elif event_type == "envelope-voided":
            # BAA voided
            logger.info("baa_voided", envelope_id=envelope_id)

    async def _handle_baa_signed(
        self,
        envelope_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """Handle BAA signed event"""
        # Find onboarding session by envelope ID
        # TODO: Query database for session with this envelope_id
        session_id = "placeholder"  # Get from database

        # Trigger BAA signed event
        from aim.services.onboarding.workflow import OnboardingEvent

        await self.workflow.handle_event(
            session_id,
            OnboardingEvent.BAA_SIGNED,
            {
                "baa_signed_at": datetime.utcnow().isoformat(),
                "baa_envelope_id": envelope_id,
            },
        )

    async def _handle_baa_declined(
        self,
        envelope_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """Handle BAA declined event"""
        decline_reason = payload.get("declineReason", "No reason provided")

        # Find onboarding session
        session_id = "placeholder"

        # Trigger BAA declined event
        from aim.services.onboarding.workflow import OnboardingEvent

        await self.workflow.handle_event(
            session_id,
            OnboardingEvent.BAA_DECLINED,
            {
                "baa_declined_at": datetime.utcnow().isoformat(),
                "decline_reason": decline_reason,
            },
        )
