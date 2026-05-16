"""
DocuSign API Client

Handles BAA (Business Associate Agreement) signature workflow.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
import structlog
import httpx

logger = structlog.get_logger()


class EnvelopeStatus(str, Enum):
    """DocuSign envelope status"""
    CREATED = "created"
    SENT = "sent"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    DECLINED = "declined"
    VOIDED = "voided"


class DocuSignConfig(BaseModel):
    """DocuSign configuration"""
    account_id: str
    integration_key: str
    user_id: str
    private_key: str
    base_url: str = "https://demo.docusign.net/restapi"
    oauth_base_url: str = "https://account-d.docusign.com"


class DocuSignClient:
    """
    DocuSign API client for BAA signatures

    Features:
    - Send BAA for e-signature
    - Track signature status
    - Download signed documents
    - Webhook notifications
    """

    def __init__(self, config: DocuSignConfig):
        """
        Initialize DocuSign client

        Args:
            config: DocuSign configuration
        """
        self.config = config
        self.account_id = config.account_id
        self.integration_key = config.integration_key
        self.user_id = config.user_id
        self.private_key = config.private_key
        self.base_url = config.base_url
        self.oauth_base_url = config.oauth_base_url
        self.logger = logger.bind(service="docusign_client")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    @property
    def access_token(self) -> Optional[str]:
        """Get access token"""
        return self._access_token

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set access token"""
        self._access_token = value

    @property
    def token_expires_at(self) -> Optional[datetime]:
        """Get token expiration time"""
        return self._token_expires_at

    @token_expires_at.setter
    def token_expires_at(self, value: Optional[datetime]) -> None:
        """Set token expiration time"""
        self._token_expires_at = value

    async def _get_access_token(self) -> str:
        """Get JWT access token"""
        # Check if token is still valid
        if (
            self._access_token
            and self._token_expires_at
            and datetime.utcnow() < self._token_expires_at
        ):
            return self._access_token

        # Request new token via JWT
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.oauth_base_url}/oauth/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": self._create_jwt_assertion(),
                },
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access_token"]
            # Token expires in 1 hour, refresh 5 minutes early
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 300)

            self.logger.info("access_token_refreshed")
            return self._access_token

    def _create_jwt_assertion(self) -> str:
        """Create JWT assertion for authentication"""
        import jwt
        from datetime import timedelta

        now = datetime.utcnow()
        payload = {
            "iss": self.integration_key,
            "sub": self.user_id,
            "aud": "account-d.docusign.com",
            "iat": now,
            "exp": now + timedelta(hours=1),
            "scope": "signature impersonation",
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def send_baa(
        self,
        client_email: str,
        client_name: str,
        practice_name: str,
    ) -> Dict[str, Any]:
        """
        Send BAA for signature
        
        Args:
            client_email: Client email address
            client_name: Client full name
            practice_name: Practice/clinic name
        
        Returns:
            Envelope data with envelope_id and status_url
        """
        token = await self._get_access_token()

        # Create envelope with BAA template
        envelope_definition = {
            "emailSubject": f"Business Associate Agreement - {practice_name}",
            "templateId": "baa_template_id",  # Pre-configured BAA template
            "templateRoles": [
                {
                    "email": client_email,
                    "name": client_name,
                    "roleName": "Client",
                    "tabs": {
                        "textTabs": [
                            {
                                "tabLabel": "practice_name",
                                "value": practice_name,
                            },
                            {
                                "tabLabel": "client_name",
                                "value": client_name,
                            },
                            {
                                "tabLabel": "date",
                                "value": datetime.utcnow().strftime("%Y-%m-%d"),
                            },
                        ],
                    },
                },
            ],
            "status": "sent",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=envelope_definition,
            )
            response.raise_for_status()
            data = response.json()

            self.logger.info(
                "baa_sent",
                envelope_id=data["envelopeId"],
                client_email=client_email,
            )

            return {
                "envelope_id": data["envelopeId"],
                "status": data["status"],
                "status_url": f"https://iamaim.ru/api/docusign/status/{data['envelopeId']}",
            }

    async def get_envelope_status(
        self,
        envelope_id: str,
    ) -> Dict[str, Any]:
        """
        Get envelope signature status
        
        Args:
            envelope_id: DocuSign envelope ID
        
        Returns:
            Status data with signed status and recipients
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()

            return {
                "envelope_id": envelope_id,
                "status": data["status"],
                "completed": data["status"] == "completed",
                "sent_at": data.get("sentDateTime"),
                "completed_at": data.get("completedDateTime"),
            }

    async def download_signed_document(
        self,
        envelope_id: str,
        output_path: str,
    ) -> str:
        """
        Download signed BAA document
        
        Args:
            envelope_id: DocuSign envelope ID
            output_path: Local file path to save PDF
        
        Returns:
            Path to downloaded file
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}/documents/combined",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

            # Save PDF
            with open(output_path, "wb") as f:
                f.write(response.content)

            self.logger.info(
                "document_downloaded",
                envelope_id=envelope_id,
                output_path=output_path,
            )

            return output_path

    async def send_baa(
        self,
        recipient_email: str,
        recipient_name: str,
        practice_name: str,
        template_id: Optional[str] = None,
    ) -> str:
        """
        Send BAA for signature

        Args:
            recipient_email: Recipient email
            recipient_name: Recipient name
            practice_name: Practice name
            template_id: Optional custom template ID

        Returns:
            Envelope ID
        """
        token = await self._get_access_token()

        envelope_definition = {
            "emailSubject": f"Business Associate Agreement - {practice_name}",
            "templateId": template_id or "baa_template_id",
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
                                "tabLabel": "client_name",
                                "value": recipient_name,
                            },
                            {
                                "tabLabel": "date",
                                "value": datetime.utcnow().strftime("%Y-%m-%d"),
                            },
                        ],
                    },
                },
            ],
            "status": "sent",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=envelope_definition,
            )
            response.raise_for_status()
            data = response.json()

            self.logger.info(
                "baa_sent",
                envelope_id=data["envelopeId"],
                recipient_email=recipient_email,
            )

            return data["envelopeId"]

    async def get_envelope_status(self, envelope_id: str) -> "EnvelopeStatusResponse":
        """
        Get envelope status

        Args:
            envelope_id: Envelope ID

        Returns:
            Envelope status response
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()

            return EnvelopeStatusResponse(
                envelope_id=envelope_id,
                status=data["status"],
                sent_at=self._parse_datetime(data.get("sentDateTime")),
                delivered_at=self._parse_datetime(data.get("deliveredDateTime")),
                signed_at=self._parse_datetime(data.get("completedDateTime")),
                declined_at=self._parse_datetime(data.get("declinedDateTime")),
                decline_reason=data.get("declineReason"),
            )

    async def download_signed_document(self, envelope_id: str) -> bytes:
        """
        Download signed document

        Args:
            envelope_id: Envelope ID

        Returns:
            PDF content
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}/documents/combined",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

            self.logger.info(
                "document_downloaded",
                envelope_id=envelope_id,
            )

            return response.content

    async def get_audit_trail(self, envelope_id: str) -> bytes:
        """
        Get audit trail

        Args:
            envelope_id: Envelope ID

        Returns:
            Audit trail PDF content
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}/documents/certificate",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

            return response.content

    async def void_envelope(self, envelope_id: str, reason: str) -> None:
        """
        Void envelope

        Args:
            envelope_id: Envelope ID
            reason: Void reason
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}",
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

            self.logger.info(
                "envelope_voided",
                envelope_id=envelope_id,
                reason=reason,
            )

    async def resend_envelope(self, envelope_id: str) -> None:
        """
        Resend envelope notification

        Args:
            envelope_id: Envelope ID
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}/notification",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"resendEnvelope": True},
            )
            response.raise_for_status()

            self.logger.info(
                "envelope_resent",
                envelope_id=envelope_id,
            )

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string

        Args:
            dt_str: Datetime string

        Returns:
            Parsed datetime or None
        """
        if not dt_str:
            return None

        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


class EnvelopeStatusResponse(BaseModel):
    """Envelope status response"""
    envelope_id: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None


class DocuSignWebhookHandler:
    """
    DocuSign webhook handler

    Processes webhook events and triggers workflow transitions
    """

    def __init__(self, workflow_service):
        """
        Initialize webhook handler

        Args:
            workflow_service: Workflow service instance
        """
        self.workflow_service = workflow_service
        self.logger = logger.bind(service="docusign_webhook_handler")

    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Handle webhook payload

        Args:
            payload: Webhook payload from DocuSign
        """
        event_type = payload.get("event")
        envelope_id = payload.get("envelopeId")

        self.logger.info(
            "webhook_received",
            event_type=event_type,
            envelope_id=envelope_id,
        )

        # Map DocuSign events to workflow events
        event_mapping = {
            "envelope-completed": "BAA_SIGNED",
            "envelope-declined": "BAA_DECLINED",
            "envelope-voided": None,  # Log only, no workflow transition
        }

        workflow_event = event_mapping.get(event_type)

        if workflow_event:
            # Trigger workflow event
            # Note: In real implementation, would need to look up client_id from envelope_id
            self.logger.info(
                "triggering_workflow_event",
                workflow_event=workflow_event,
                envelope_id=envelope_id,
            )
