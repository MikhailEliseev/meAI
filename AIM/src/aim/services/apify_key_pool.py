"""Apify API key pool with round-robin rotation and 31-day auto-recovery.

Stores keys in JSON, rotates active keys via round-robin, marks exhausted
keys and auto-recovers them after 31 days (Apify free tier reset).
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_RECOVERY_DAYS = 31
_TMP_STALE_SECONDS = 60


class ApifyKeyPool:
    """Round-robin key pool with automatic exhaustion tracking and recovery."""

    def __init__(self, keys_file: str):
        if not os.path.exists(keys_file):
            raise FileNotFoundError(f"Apify keys file not found: {keys_file}")
        self._keys_file = keys_file
        self._lock = asyncio.Lock()
        self._keys: list[dict] = []
        self._active_indices: list[int] = []
        self._cursor = 0
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_next_key(self) -> str:
        """Return the next active token (round-robin). Raises RuntimeError if pool dry."""
        async with self._lock:
            if not self._active_indices:
                raise RuntimeError("All Apify keys exhausted — no active keys remaining")
            idx = self._active_indices[self._cursor % len(self._active_indices)]
            self._cursor = (self._cursor + 1) % len(self._active_indices)
            return self._keys[idx]["token"]

    async def mark_exhausted(self, token: str):
        """Record a key as exhausted (called on quota error). Persists to file."""
        async with self._lock:
            self._mark_exhausted_locked(token)

    def get_stats(self) -> dict:
        total = len(self._keys)
        active = sum(1 for k in self._keys if k["status"] == "active")
        return {"total": total, "active": active, "exhausted": total - active}

    @property
    def active_count(self) -> int:
        return len(self._active_indices)

    # ------------------------------------------------------------------
    # Internal — load / save
    # ------------------------------------------------------------------

    def _load(self):
        with open(self._keys_file, "r") as f:
            data = json.load(f)

        self._cleanup_stale_tmp()
        self._keys = data["keys"]
        self._auto_recover()
        self._rebuild_indices()

        logger.info(
            "ApifyKeyPool loaded: %d total, %d active, %d exhausted",
            len(self._keys), len(self._active_indices),
            len(self._keys) - len(self._active_indices),
        )

    def _save(self):
        """Atomic write: tmp → replace. Keeps .bak for safety."""
        tmp_path = self._keys_file + ".tmp"
        bak_path = self._keys_file + ".bak"

        with open(tmp_path, "w") as f:
            json.dump({"keys": self._keys}, f, indent=2, ensure_ascii=False)

        if os.path.exists(self._keys_file):
            os.replace(self._keys_file, bak_path)
        os.replace(tmp_path, self._keys_file)

    def _cleanup_stale_tmp(self):
        tmp_path = self._keys_file + ".tmp"
        if os.path.exists(tmp_path):
            try:
                if time.time() - os.path.getmtime(tmp_path) > _TMP_STALE_SECONDS:
                    os.remove(tmp_path)
                    logger.warning("Removed stale tmp file: %s", tmp_path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Internal — recovery
    # ------------------------------------------------------------------

    def _auto_recover(self):
        """Reactivate keys exhausted >= 31 days ago."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=_RECOVERY_DAYS)
        recovered = 0

        for key in self._keys:
            if key["status"] != "exhausted":
                continue
            exhausted_at = key.get("exhausted_at")
            if exhausted_at:
                try:
                    if datetime.fromisoformat(exhausted_at) <= cutoff:
                        key["status"] = "active"
                        key["exhausted_at"] = None
                        recovered += 1
                except (ValueError, TypeError):
                    key["status"] = "active"
                    key["exhausted_at"] = None
                    recovered += 1
            else:
                key["status"] = "active"
                recovered += 1

        if recovered:
            logger.info("Auto-recovered %d keys (>= %d days)", recovered, _RECOVERY_DAYS)
            self._save()

    # ------------------------------------------------------------------
    # Internal — indices + exhaustion
    # ------------------------------------------------------------------

    def _rebuild_indices(self):
        self._active_indices = [
            i for i, k in enumerate(self._keys) if k["status"] == "active"
        ]
        self._cursor = 0

    def _mark_exhausted_locked(self, token: str):
        """Mark key exhausted and persist. Caller must hold self._lock."""
        for key in self._keys:
            if key["token"] == token and key["status"] == "active":
                key["status"] = "exhausted"
                key["exhausted_at"] = datetime.now(timezone.utc).isoformat()
                label = key.get("label", token[:20] + "...")
                self._save()
                self._rebuild_indices()
                logger.warning(
                    "Apify key exhausted: %s (remaining active: %d)",
                    label, len(self._active_indices),
                )
                return

        logger.debug("Token not found or already exhausted: %s...", token[:20])
