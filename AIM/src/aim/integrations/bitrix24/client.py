"""Bitrix24 REST API Client.

Wraps fast_bitrix24 with additional resilience patterns:
- Circuit breaker (pybreaker) for connection failures
- Exponential backoff retry (tenacity) for transient errors
- Structured logging with operation context
- Webhook verification

Auth modes:
- Webhook: https://{domain}/rest/{user_id}/{webhook_code}/ — no token management
- OAuth 2.0: token_func callback for auto-refresh — for multi-user apps

Usage:
    client = Bitrix24Client(webhook_url="https://...")
    leads = await client.list_leads()
    lead_id = await client.create_lead(Bitrix24Lead(title="..."))
"""

import logging
from typing import Optional

import pybreaker
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# fast_bitrix24 is optional — only required when Bitrix24Client is actually used
try:
    from fast_bitrix24 import BitrixAsync
    _FAST_BITRIX24_AVAILABLE = True
except ImportError:
    BitrixAsync = None
    _FAST_BITRIX24_AVAILABLE = False

from src.aim.integrations.bitrix24.schemas import (
    Bitrix24Contact,
    Bitrix24Deal,
    Bitrix24Lead,
    Bitrix24Webhook,
    CrmSyncResult,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
CIRCUIT_BREAKER_FAIL_MAX = 5
CIRCUIT_BREAKER_RESET = 60


class Bitrix24ClientError(Exception):
    """Base exception for Bitrix24 client errors."""


class Bitrix24AuthError(Bitrix24ClientError):
    """Authentication or webhook configuration error."""


class Bitrix24APIError(Bitrix24ClientError):
    """Bitrix24 REST API returned an error."""


class Bitrix24Client:
    """Async Bitrix24 REST API client with resilience patterns.

    Wraps fast_bitrix24.BitrixAsync with circuit breaker and exponential
    backoff retry for production reliability.

    Args:
        webhook_url: Bitrix24 inbound webhook URL
            Format: https://{domain}/rest/{user_id}/{webhook_code}/
        token_func: Async callable that returns a fresh OAuth access_token
            for OAuth 2.0 apps. None for webhook-based auth.
        ssl: Verify SSL certificate (default True)
    """

    def __init__(
        self,
        webhook_url: str,
        token_func=None,
        ssl: bool = True,
    ) -> None:
        if not _FAST_BITRIX24_AVAILABLE:
            raise ImportError(
                "fast-bitrix24 is required for Bitrix24Client. "
                "Install it with: pip install fast-bitrix24"
            )
        self._webhook_url = webhook_url
        self._token_func = token_func
        self._bx: Optional[BitrixAsync] = None

        self._circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=CIRCUIT_BREAKER_FAIL_MAX,
            reset_timeout=CIRCUIT_BREAKER_RESET,
            name="bitrix24",
        )

        self._retry = lambda: AsyncRetrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min_wait=1, max_wait=10),
            retry=retry_if_exception_type((
                Bitrix24APIError,
                ConnectionError,
                TimeoutError,
            )),
            reraise=True,
        )

    @property
    def client(self) -> BitrixAsync:
        """Lazy-init fast_bitrix24 client."""
        if self._bx is None:
            webhook = self._webhook_url.rstrip("/") + "/" if self._webhook_url else ""
            self._bx = BitrixAsync(
                webhook=webhook,
                token_func=self._token_func,
                verbose=False,
                respect_velocity_policy=True,
                requests_per_second=2.0,
                ssl=True,
            )
        return self._bx

    def _parse_error(self, response: dict | list) -> str | None:
        """Extract error message from Bitrix24 response."""
        if isinstance(response, dict):
            if "error" in response:
                return response.get("error_description", response["error"])
        return None

    # ── Lead operations ──────────────────────────────────────────────────

    async def create_lead(self, lead: Bitrix24Lead) -> CrmSyncResult:
        """Create a lead in Bitrix24 CRM.

        Args:
            lead: Bitrix24Lead schema with contact info and custom fields.
        """
        op = "lead_add"
        logger.info("Bitrix24: creating lead title=%s", lead.title)
        try:
            async for attempt in self._retry():
                async with attempt:
                    result = await self._circuit_breaker.call(
                        self.client.call, "crm.lead.add", lead.to_bitrix24()
                    )
                    error = self._parse_error(result)
                    if error:
                        raise Bitrix24APIError(error)
                    lead_id = result.get("result") if isinstance(result, dict) else None
                    logger.info("Bitrix24: lead created id=%s", lead_id)
                    return CrmSyncResult(
                        success=True,
                        action=op,
                        bitrix24_id=lead_id,
                        aim_lead_id=lead.uf_crm_lead_aim_id,
                    )
        except pybreaker.CircuitBreakerError:
            logger.error("Bitrix24: circuit breaker open for %s", op)
            return CrmSyncResult(success=False, action=op, error="Circuit breaker open")
        except Exception as e:
            logger.error("Bitrix24: %s failed: %s", op, e)
            return CrmSyncResult(success=False, action=op, error=str(e))

    async def update_lead(self, bitrix24_id: int, lead: Bitrix24Lead) -> CrmSyncResult:
        """Update an existing lead in Bitrix24."""
        op = "lead_update"
        logger.info("Bitrix24: updating lead id=%s", bitrix24_id)
        try:
            async for attempt in self._retry():
                async with attempt:
                    params = {"ID": bitrix24_id, **lead.to_bitrix24()}
                    result = await self._circuit_breaker.call(
                        self.client.call, "crm.lead.update", params
                    )
                    error = self._parse_error(result)
                    if error:
                        raise Bitrix24APIError(error)
                    logger.info("Bitrix24: lead updated id=%s", bitrix24_id)
                    return CrmSyncResult(
                        success=True,
                        action=op,
                        bitrix24_id=bitrix24_id,
                        aim_lead_id=lead.uf_crm_lead_aim_id,
                    )
        except pybreaker.CircuitBreakerError:
            return CrmSyncResult(success=False, action=op, error="Circuit breaker open")
        except Exception as e:
            logger.error("Bitrix24: %s failed: %s", op, e)
            return CrmSyncResult(success=False, action=op, error=str(e))

    async def list_leads(self, filter_params: dict | None = None) -> list[dict]:
        """Get all leads, optionally filtered.

        Args:
            filter_params: Bitrix24 filter dict, e.g. {"SOURCE_ID": "WEB"}
        """
        params = {}
        if filter_params:
            params["filter"] = filter_params
        try:
            return await self._circuit_breaker.call(
                self.client.get_all, "crm.lead.list", params
            )
        except pybreaker.CircuitBreakerError:
            logger.error("Bitrix24: circuit breaker open for lead_list")
            return []
        except Exception as e:
            logger.error("Bitrix24: list_leads failed: %s", e)
            return []

    async def find_lead_by_phone(self, phone: str) -> Optional[dict]:
        """Find a lead by phone number. Used for deduplication."""
        cleaned = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        results = await self.list_leads({"PHONE": cleaned})
        return results[0] if results else None

    async def find_lead_by_email(self, email: str) -> Optional[dict]:
        """Find a lead by email. Used for deduplication."""
        results = await self.list_leads({"EMAIL": email.strip().lower()})
        return results[0] if results else None

    # ── Contact operations ────────────────────────────────────────────────

    async def create_contact(self, contact: Bitrix24Contact) -> CrmSyncResult:
        """Create a contact in Bitrix24."""
        op = "contact_add"
        logger.info("Bitrix24: creating contact name=%s", contact.name)
        try:
            async for attempt in self._retry():
                async with attempt:
                    result = await self._circuit_breaker.call(
                        self.client.call, "crm.contact.add", contact.to_bitrix24()
                    )
                    error = self._parse_error(result)
                    if error:
                        raise Bitrix24APIError(error)
                    contact_id = result.get("result") if isinstance(result, dict) else None
                    return CrmSyncResult(
                        success=True,
                        action=op,
                        bitrix24_id=contact_id,
                        aim_lead_id=contact.uf_crm_contact_aim_id,
                    )
        except pybreaker.CircuitBreakerError:
            return CrmSyncResult(success=False, action=op, error="Circuit breaker open")
        except Exception as e:
            logger.error("Bitrix24: %s failed: %s", e, op)
            return CrmSyncResult(success=False, action=op, error=str(e))

    # ── Deal operations ───────────────────────────────────────────────────

    async def create_deal(self, deal: Bitrix24Deal) -> CrmSyncResult:
        """Create a deal in Bitrix24."""
        op = "deal_add"
        logger.info("Bitrix24: creating deal title=%s", deal.title)
        try:
            async for attempt in self._retry():
                async with attempt:
                    result = await self._circuit_breaker.call(
                        self.client.call, "crm.deal.add", deal.to_bitrix24()
                    )
                    error = self._parse_error(result)
                    if error:
                        raise Bitrix24APIError(error)
                    deal_id = result.get("result") if isinstance(result, dict) else None
                    return CrmSyncResult(
                        success=True,
                        action=op,
                        bitrix24_id=deal_id,
                        aim_lead_id=deal.uf_crm_deal_aim_id,
                    )
        except pybreaker.CircuitBreakerError:
            return CrmSyncResult(success=False, action=op, error="Circuit breaker open")
        except Exception as e:
            logger.error("Bitrix24: %s failed: %s", e, op)
            return CrmSyncResult(success=False, action=op, error=str(e))

    # ── Webhook ───────────────────────────────────────────────────────────

    def verify_webhook(self, webhook: Bitrix24Webhook, expected_domain: str | None = None) -> bool:
        """Verify incoming Bitrix24 webhook authenticity.

        Args:
            webhook: Parsed Bitrix24Webhook payload
            expected_domain: Optional expected Bitrix24 domain for extra verification
        """
        if not webhook.event:
            logger.warning("Bitrix24 webhook: missing event type")
            return False
        if not webhook.data:
            logger.warning("Bitrix24 webhook: missing data")
            return False

        auth = webhook.auth
        if auth:
            domain = auth.get("domain", "")
            if expected_domain and domain != expected_domain:
                logger.warning("Bitrix24 webhook: domain mismatch expected=%s got=%s", expected_domain, domain)
                return False

        logger.info("Bitrix24 webhook: verified event=%s", webhook.event)
        return True

    # ── Health check ──────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Verify connection to Bitrix24 CRM."""
        try:
            result = await self._circuit_breaker.call(
                self.client.call, "app.info", {}
            )
            return isinstance(result, dict) and "result" in result
        except Exception as e:
            logger.error("Bitrix24 health check failed: %s", e)
            return False

    async def close(self) -> None:
        """Clean up resources."""
        self._bx = None
        logger.info("Bitrix24 client closed")


def create_bitrix24_client(
    webhook_url: str | None = None,
    oauth_token_func=None,
) -> Bitrix24Client | None:
    """Factory: create Bitrix24Client from environment or explicit config.

    Returns None if neither webhook nor OAuth config is available.
    """
    import os

    webhook = webhook_url or os.getenv("BITRIX24_WEBHOOK_URL", "")
    if webhook:
        return Bitrix24Client(webhook_url=webhook)

    if oauth_token_func:
        return Bitrix24Client(webhook_url="", token_func=oauth_token_func)

    logger.warning("Bitrix24: no webhook URL or OAuth config — client not created")
    return None
