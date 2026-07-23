"""Apify-клиент через UnifiedKeyPool.

Единый пул ключей с атомарной записью, блокировками и auto-recovery.

Ключи: /opt/keys/apify.json (через env APIFY_KEYS_FILE).
"""
import logging
import os

from app.lib.key_pool import UnifiedKeyPool

logger = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"
ACTOR_ID = "apify~instagram-profile-scraper"
APIFY_KEYS_PATH = os.getenv("APIFY_KEYS_FILE", os.getenv("APIFY_KEYS_PATH", "/opt/data/apify_keys.json"))
REQUEST_TIMEOUT = 180.0

# Singleton pool — создаётся при первом обращении (lazy, для тестов)
_pool: UnifiedKeyPool | None = None


def get_apify_pool() -> UnifiedKeyPool:
    """Возвращает singleton UnifiedKeyPool для Apify."""
    global _pool
    if _pool is None:
        _pool = UnifiedKeyPool("apify", APIFY_KEYS_PATH)
    return _pool
