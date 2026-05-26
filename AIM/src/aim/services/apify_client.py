"""Shared Apify client with key-pool-based resilience.

Uses ApifyKeyPool for automatic key rotation on quota exhaustion.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Optional

from apify_client import ApifyClientAsync
from apify_client.errors import ApifyApiError

from .apify_key_pool import ApifyKeyPool

logger = logging.getLogger(__name__)

_DEFAULT_RUN_TIMEOUT = timedelta(minutes=3)
_DEFAULT_MEMORY_MB = 2048
_RETRY_MAX = 3
_RETRY_BASE_DELAY = 2.0

_QUOTA_KEYWORDS = ("quota", "exceeded", "insufficient", "balance", "limit")


class ApifyClient:
    """Async Apify client that auto-rotates Apify keys on quota errors."""

    def __init__(self, key_pool: ApifyKeyPool):
        self._key_pool = key_pool
        self._current_token: Optional[str] = None
        self._client: Optional[ApifyClientAsync] = None

    async def _ensure_client(self):
        if self._client is None:
            self._current_token = await self._key_pool.get_next_key()
            self._client = ApifyClientAsync(token=self._current_token)

    async def call_actor(
        self,
        actor_id: str,
        run_input: dict,
        run_timeout: timedelta = _DEFAULT_RUN_TIMEOUT,
        memory_mbytes: int = _DEFAULT_MEMORY_MB,
        max_retries: int = _RETRY_MAX,
    ):
        """Call an Apify actor with automatic key rotation on quota errors."""
        await self._ensure_client()
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                run = await self._client.actor(actor_id).call(
                    run_input=run_input,
                    run_timeout=run_timeout,
                    memory_mbytes=memory_mbytes,
                )
                return run

            except ApifyApiError as e:
                if self._is_quota_error(e):
                    logger.warning("Apify quota error, rotating key (attempt %d)", attempt + 1)
                    last_error = e
                    if await self._rotate_key():
                        continue
                    raise RuntimeError("All Apify keys exhausted")

                if e.status_code == 429:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Apify 429, attempt %d/%d, waiting %.1fs",
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
                if any(kw in msg for kw in ("timeout", "connection", "reset", "503", "502")):
                    if attempt < max_retries:
                        delay = _RETRY_BASE_DELAY * (2 ** attempt)
                        logger.warning(
                            "Apify transient '%s', attempt %d/%d, waiting %.1fs",
                            e, attempt + 1, max_retries + 1, delay,
                        )
                        last_error = e
                        await asyncio.sleep(delay)
                        continue
                raise

        raise last_error or RuntimeError("Apify actor call failed after retries")

    async def get_dataset_items(self, dataset_id: str) -> list[dict]:
        """Fetch all items from a dataset."""
        await self._ensure_client()
        dataset = self._client.dataset(dataset_id)
        return [item async for item in dataset.iterate_items()]

    async def close(self):
        pass

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_quota_error(self, error: ApifyApiError) -> bool:
        """Check if error indicates quota/balance exhaustion."""
        if error.status_code in (402, 403):
            return True
        return any(kw in str(error).lower() for kw in _QUOTA_KEYWORDS)

    async def _rotate_key(self) -> bool:
        """Mark current key exhausted, switch to next. Returns False if pool dry."""
        try:
            await self._key_pool.mark_exhausted(self._current_token)
            self._current_token = await self._key_pool.get_next_key()
            self._client = ApifyClientAsync(token=self._current_token)
            logger.info("Rotated Apify key (active: %d)", self._key_pool.active_count)
            return True
        except RuntimeError:
            logger.error("ApifyKeyPool dry — no active keys left")
            return False
