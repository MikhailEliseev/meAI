"""Apify-клиент через UnifiedKeyPool (замена ломаной версии).

Единый пул ключей с атомарной записью, блокировками и auto-recovery.
Больше никакого load_apify_keys() без блокировки и mark_exhausted без persist.

Ключи: /opt/keys/apify.json (через env APIFY_KEYS_FILE).
Actor: apify~instagram-profile-scraper.
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


# ── Обратная совместимость: старые функции делегируют в пул ──────────────

def load_apify_keys() -> list[str]:
    """Возвращает токены активных ключей (через UnifiedKeyPool).

    Deprecated: используйте get_apify_pool().get_next_key() для ротации.
    Оставлен для обратной совместимости с run_instagram_content.py.
    """
    try:
        pool = get_apify_pool()
        return [k["token"] for k in pool._keys if k.get("status") == "active"]
    except Exception:
        logger.warning("apify: cannot load keys from %s", APIFY_KEYS_PATH)
        return []


_bg_tasks: set = set()


def mark_apify_key_exhausted(token: str, reason: str = "insufficient_credits") -> None:
    """Помечает ключ exhausted через UnifiedKeyPool (с persist + lock)."""
    try:
        import asyncio
        pool = get_apify_pool()
        try:
            loop = asyncio.get_running_loop()
            # Сохраняем reference чтобы task не был GC'd
            task = loop.create_task(pool.mark_exhausted(token, reason))
            _bg_tasks.add(task)
            task.add_done_callback(_bg_tasks.discard)
        except RuntimeError:
            asyncio.run(pool.mark_exhausted(token, reason))
    except Exception:
        logger.exception("apify: failed to mark key exhausted")
