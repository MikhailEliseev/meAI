"""Simple in-memory response cache with TTL.

Used for analytics endpoints that don't need real-time data.
"""

import hashlib
import json
import time
from typing import Any


class ResponseCache:
    """TTL-based in-memory cache for API responses."""

    def __init__(self, default_ttl: int = 30):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl  # seconds

    def _make_key(self, prefix: str, params: dict) -> str:
        raw = json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.md5(raw.encode()).hexdigest()
        return f"{prefix}:{digest}"

    def get(self, prefix: str, params: dict) -> Any | None:
        key = self._make_key(prefix, params)
        entry = self._cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._cache[key]
            return None
        return value

    def set(self, prefix: str, params: dict, value: Any, ttl: int | None = None) -> None:
        key = self._make_key(prefix, params)
        ttl = ttl or self._default_ttl
        self._cache[key] = (time.monotonic() + ttl, value)

    def invalidate(self, prefix: str) -> int:
        """Invalidate all entries with given prefix. Returns count removed."""
        count = 0
        for key in list(self._cache):
            if key.startswith(f"{prefix}:"):
                del self._cache[key]
                count += 1
        return count

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# Global cache instance
cache = ResponseCache(default_ttl=30)
