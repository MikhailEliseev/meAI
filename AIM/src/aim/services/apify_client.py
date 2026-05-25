"""Shared Apify client with resilience patterns — retry, circuit breaker, rate limiting.

API token is read from APIFY_API_TOKEN env var. Raises RuntimeError if not set.
"""

import logging
import os
import asyncio
from datetime import timedelta
from typing import Optional

from apify_client import ApifyClientAsync
from apify_client.errors import ApifyApiError

logger = logging.getLogger(__name__)

_DEFAULT_RUN_TIMEOUT = timedelta(minutes=3)
_DEFAULT_MEMORY_MB = 2048
_RETRY_MAX = 3
_RETRY_BASE_DELAY = 2.0  # seconds


class ApifyClient:
    """Async Apify client with built-in retry, circuit breaker, and timeout guard."""

    def __init__(self, token: Optional[str] = None):
        token = token or os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise RuntimeError("APIFY_API_TOKEN not set in environment")
        self._client = ApifyClientAsync(token=token)
        self._circuit_open = False
        self._failure_count = 0
        self._failure_reset_at = 0.0

    async def call_actor(
        self,
        actor_id: str,
        run_input: dict,
        run_timeout: timedelta = _DEFAULT_RUN_TIMEOUT,
        memory_mbytes: int = _DEFAULT_MEMORY_MB,
        max_retries: int = _RETRY_MAX,
    ):
        """Call an Apify actor with automatic retry on transient failures.

        Returns the Run object (Pydantic model with snake_case attrs).
        """
        if self._circuit_open:
            now = asyncio.get_event_loop().time()
            if now < self._failure_reset_at:
                raise RuntimeError(
                    f"Apify circuit breaker open — too many failures, "
                    f"retry after {self._failure_reset_at - now:.0f}s"
                )
            self._circuit_open = False
            self._failure_count = 0

        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                run = await self._client.actor(actor_id).call(
                    run_input=run_input,
                    run_timeout=run_timeout,
                    memory_mbytes=memory_mbytes,
                )
                self._failure_count = 0  # reset on success
                return run

            except ApifyApiError as e:
                if e.status_code == 429:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Apify rate limited (429), attempt %d/%d, waiting %.1fs",
                        attempt + 1, max_retries + 1, delay,
                    )
                    last_error = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        continue
                else:
                    logger.error("Apify API error (status=%s): %s", e.status_code, e)
                    raise

            except Exception as e:
                msg = str(e).lower()
                is_transient = any(
                    kw in msg for kw in ("timeout", "connection", "reset", "503", "502")
                )
                if is_transient and attempt < max_retries:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Apify transient error '%s', attempt %d/%d, waiting %.1fs",
                        e, attempt + 1, max_retries + 1, delay,
                    )
                    last_error = e
                    await asyncio.sleep(delay)
                    continue
                raise

        # All retries exhausted
        self._failure_count += 1
        if self._failure_count >= 5:
            logger.error("Apify circuit breaker OPEN — %d consecutive failures", self._failure_count)
            self._circuit_open = True
            self._failure_reset_at = asyncio.get_event_loop().time() + 60.0

        raise last_error or RuntimeError("Apify actor call failed after retries")

    async def get_dataset_items(self, dataset_id: str) -> list[dict]:
        """Fetch all items from a dataset."""
        dataset = self._client.dataset(dataset_id)
        return [item async for item in dataset.iterate_items()]

    async def close(self):
        """No-op — ApifyClientAsync doesn't need explicit close."""
        pass


# Module-level singleton
_client: Optional[ApifyClient] = None


def get_apify_client() -> ApifyClient:
    global _client
    if _client is None:
        _client = ApifyClient()
    return _client
