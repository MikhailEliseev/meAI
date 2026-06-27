"""_file_cache — File-based TTL cache surviving container restarts.

Stores cached responses in /opt/data/cache/ as JSON files.
Safe for single-process FastAPI (no race conditions).

TTL: 3600s (1 hour) — doctors/content don't change hourly.

Usage:
    from app.tools._file_cache import file_cache
    result = await file_cache.get(key)
    await file_cache.set(key, result)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("HERMES_CACHE_DIR", "/opt/data/cache")
DEFAULT_TTL = int(os.getenv("HERMES_CACHE_TTL", "3600"))


class FileCache:
    """Simple file-based TTL cache."""

    def __init__(self, cache_dir: str = CACHE_DIR, ttl: int = DEFAULT_TTL):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self._ensured = False

    def _ensure_dir(self):
        if not self._ensured:
            os.makedirs(self.cache_dir, exist_ok=True)
            self._ensured = True

    def _key_path(self, key: str) -> str:
        """Derive a safe filename from the cache key."""
        hashed = hashlib.sha256(key.encode()).hexdigest()[:32]
        return os.path.join(self.cache_dir, f"{hashed}.json")

    async def get(self, key: str) -> str | None:
        """Get cached value. Returns None if missing or expired."""
        self._ensure_dir()
        path = self._key_path(key)
        try:
            with open(path) as f:
                data = json.load(f)
            ts = data.get("_ts", 0)
            if time.time() - ts > self.ttl:
                # Expired — delete and return None
                os.remove(path)
                logger.debug("FileCache: EXPIRED %s", key[:60])
                return None
            logger.debug("FileCache: HIT %s", key[:60])
            return data.get("value")
        except FileNotFoundError:
            logger.debug("FileCache: MISS %s", key[:60])
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("FileCache: corrupt cache file %s — %s", path, str(e)[:80])
            try:
                os.remove(path)
            except OSError:
                pass
            return None

    async def set(self, key: str, value: str):
        """Store value in cache."""
        self._ensure_dir()
        path = self._key_path(key)
        try:
            with open(path, "w") as f:
                json.dump({"_ts": time.time(), "value": value}, f)
            logger.debug("FileCache: SET %s (%d chars)", key[:60], len(value))
        except OSError as e:
            logger.warning("FileCache: write error %s — %s", path, str(e)[:80])

    def cleanup_expired(self) -> int:
        """Delete all expired cache files. Returns count of deleted files.

        Called periodically (e.g. once per tool invocation) to prevent
        unlimited cache directory growth.
        """
        self._ensure_dir()
        deleted = 0
        now = time.time()
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith(".json"):
                    continue
                path = os.path.join(self.cache_dir, filename)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if now - data.get("_ts", 0) > self.ttl:
                        os.remove(path)
                        deleted += 1
                except (json.JSONDecodeError, OSError):
                    try:
                        os.remove(path)
                        deleted += 1
                    except OSError:
                        pass
        except OSError:
            pass
        if deleted:
            logger.info("FileCache: cleaned up %d expired files", deleted)
        return deleted


# Singleton
file_cache = FileCache()
