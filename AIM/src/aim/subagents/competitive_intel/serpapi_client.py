"""Rotating SerpAPI client with automatic key failover on 429 errors.

SerpAPI free tier has 100 searches/month per key. When one key exhausts
its quota (429 Too Many Requests), we rotate to the next key. Old keys
recover after ~1 month of inactivity.

Usage:
    client = RotatingSerpAPIClient(keys=["key1", "key2"])
    results = await client.search("query text")
"""

import asyncio
import time
from typing import Optional

import httpx


class RotatingSerpAPIClient:
    """SerpAPI client with automatic key rotation."""

    def __init__(self, keys: list[str], cooldown_seconds: float = 60.0):
        if not keys:
            raise ValueError("At least one SerpAPI key required")
        self._keys = keys
        self._active_index = 0
        self._cooldown = cooldown_seconds
        self._exhausted_until: dict[str, float] = {}  # key → timestamp
        self._lock = asyncio.Lock()

    @property
    def active_key(self) -> str:
        return self._keys[self._active_index]

    async def search(
        self,
        query: str,
        engine: str = "google",
        hl: str = "ru",
        gl: str = "ru",
        num: int = 10,
        timeout: float = 15.0,
    ) -> list[dict]:
        """Execute a SerpAPI search with automatic key rotation on 429."""
        async with self._lock:
            return await self._search_internal(query, engine, hl, gl, num, timeout)

    async def _search_internal(
        self, query: str, engine: str, hl: str, gl: str, num: int, timeout: float
    ) -> list[dict]:
        """Try all available keys, rotating on failure."""
        now = time.monotonic()
        attempts = 0

        for _ in range(len(self._keys)):
            attempts += 1
            key = self._keys[self._active_index]

            # Skip keys that are still in cooldown
            if key in self._exhausted_until:
                if now < self._exhausted_until[key]:
                    self._active_index = (self._active_index + 1) % len(self._keys)
                    continue
                del self._exhausted_until[key]

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get("https://serpapi.com/search", params={
                        "api_key": key,
                        "engine": engine,
                        "q": query,
                        "hl": hl,
                        "gl": gl,
                        "num": num,
                    })

                    if resp.status_code == 429:
                        self._exhausted_until[key] = now + self._cooldown
                        self._active_index = (self._active_index + 1) % len(self._keys)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("organic_results", [])

            except (httpx.HTTPError, httpx.TimeoutException):
                self._active_index = (self._active_index + 1) % len(self._keys)
                continue

        return []


def get_serpapi_client() -> Optional[RotatingSerpAPIClient]:
    """Factory: creates a rotating SerpAPI client from configured keys.

    Reads env vars directly to avoid triggering full APISettings validation
    which requires SEMrush key (not needed for SerpAPI).
    """
    import os
    keys = []
    primary = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
    if primary and len(primary) >= 10:
        keys.append(primary)
    secondary = os.getenv("SERPAPI_KEY_SECONDARY")
    if secondary and len(secondary) >= 10:
        keys.append(secondary)
    if keys:
        return RotatingSerpAPIClient(keys)
    return None
