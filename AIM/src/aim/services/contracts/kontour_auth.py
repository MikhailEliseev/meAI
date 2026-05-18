"""Контур.Диадок OIDC Authentication

Device Authorization Flow for server-to-server token management.

Part of: Phase 12-02 — Контур.Диадок integration
"""

import asyncio
import time
import httpx
import structlog

logger = structlog.get_logger()


class KontourAuth:
    """Manages OIDC tokens for Контур.Диадок API.

    Uses Device Authorization Flow:
    1. POST /connect/deviceauthorization → device_code + verification_uri
    2. User authenticates in browser (one-time)
    3. POST /connect/token → access_token (1h) + refresh_token (24h)
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        identity_url: str = "https://identity.kontur.ru",
        scopes: str = "openid profile email offline_access Diadoc.PublicAPI",
    ):
        if not client_id or not client_secret:
            raise ValueError("KONTOUR_CLIENT_ID and KONTOUR_CLIENT_SECRET are required")
        self.client_id = client_id
        self.client_secret = client_secret
        self.identity_url = identity_url
        self.scopes = scopes
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._client = httpx.AsyncClient(timeout=30.0)

    async def get_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token
        if self._refresh_token:
            return await self._refresh_access_token()
        return await self._request_new_token()

    async def _request_new_token(self) -> str:
        """Device Authorization Flow — initial token request."""
        device_resp = await self._client.post(
            f"{self.identity_url}/connect/deviceauthorization",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scopes,
            },
        )
        device_resp.raise_for_status()
        device_data = device_resp.json()
        device_code = device_data["device_code"]
        verification_uri = device_data["verification_uri"]
        user_code = device_data.get("user_code", "")
        interval = device_data.get("interval", 5)

        logger.info(
            "kontour_device_auth",
            verification_uri=verification_uri,
            user_code=user_code,
        )

        max_attempts = 60
        for attempt in range(max_attempts):
            await asyncio.sleep(interval)
            token_resp = await self._client.post(
                f"{self.identity_url}/connect/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                },
            )
            if token_resp.status_code == 200:
                token_data = token_resp.json()
                self._access_token = token_data["access_token"]
                self._refresh_token = token_data.get("refresh_token")
                self._expires_at = time.time() + token_data.get("expires_in", 3600)
                logger.info("kontour_token_obtained")
                return self._access_token
            if token_resp.status_code == 400:
                error = token_resp.json().get("error", "")
                if error == "authorization_pending":
                    continue
                if error == "slow_down":
                    interval += 5
                    continue

        raise RuntimeError("Device authorization timed out after 5 minutes")

    async def _refresh_access_token(self) -> str:
        """Refresh access token using refresh_token."""
        resp = await self._client.post(
            f"{self.identity_url}/connect/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        self._expires_at = time.time() + data.get("expires_in", 86400)
        logger.debug("kontour_token_refreshed")
        return self._access_token

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
