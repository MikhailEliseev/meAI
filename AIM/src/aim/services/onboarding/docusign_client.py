"""
DocuSign API Client

Handles BAA (Business Associate Agreement) signature workflow.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import structlog
import httpx

logger = structlog.get_logger()


class DocuSignClient:
    """
    DocuSign API client for BAA signatures
    
    Features:
    - Send BAA for e-signature
    - Track signature status
    - Download signed documents
    - Webhook notifications
    """

    def __init__(
        self,
        account_id: str,
        integration_key: str,
        user_id: str,
        private_key: str,
        base_url: str = "https://demo.docusign.net/restapi",
    ):
        """
        Initialize DocuSign client
        
        Args:
            account_id: DocuSign account ID
            integration_key: OAuth integration key
            user_id: DocuSign user ID
            private_key: RSA private key for JWT
            base_url: API base URL (demo or production)
        """
        self.account_id = account_id
        self.integration_key = integration_key
        self.user_id = user_id
        self.private_key = private_key
        self.base_url = base_url
        self.logger = logger.bind(service="docusign_client")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

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
                "https://account-d.docusign.com/oauth/token",
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

    async def handle_webhook(
        self,
        webhook_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle DocuSign webhook notification
        
        Args:
            webhook_data: Webhook payload from DocuSign
        
        Returns:
            Processed event data
        """
        event = webhook_data.get("event")
        envelope_id = webhook_data.get("data", {}).get("envelopeId")

        self.logger.info(
            "webhook_received",
            event=event,
            envelope_id=envelope_id,
        )

        # Map DocuSign events to our workflow events
        event_mapping = {
            "envelope-sent": "baa_sent",
            "envelope-delivered": "baa_delivered",
            "envelope-completed": "baa_signed",
            "envelope-declined": "baa_declined",
            "envelope-voided": "baa_voided",
        }

        workflow_event = event_mapping.get(event)

        return {
            "envelope_id": envelope_id,
            "docusign_event": event,
            "workflow_event": workflow_event,
            "timestamp": webhook_data.get("generatedDateTime"),
        }

from datetime import timedelta
