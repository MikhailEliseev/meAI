"""ApifyKeyPool — thin wrapper над UnifiedKeyPool.

Сохраняет публичный API для существующих потребителей AIM
(get_next_key, mark_exhausted, get_stats, active_count),
но внутри использует UnifiedKeyPool с единой логикой recovery.

Это обеспечивает единую систему управления ключами во всём проекте.
"""
import logging
import os

from .key_pool import UnifiedKeyPool

logger = logging.getLogger(__name__)


class ApifyKeyPool:
    """Round-robin key pool для Apify — делегирует в UnifiedKeyPool.

    Backward-compatible с предыдущей версией (asyncio.Lock, atomic save, recovery).
    """

    def __init__(self, keys_file: str | None = None):
        """Создаёт пул.

        Args:
            keys_file: Путь к JSON с ключами. Если None — берёт из env
                       APIFY_KEYS_FILE или дефолт AIM/data/apify_keys.json.
        """
        if keys_file is None:
            keys_file = os.getenv(
                "APIFY_KEYS_FILE",
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "..", "data", "apify_keys.json"
                ),
            )
        self._pool = UnifiedKeyPool("apify", keys_file)
        # Алиасы для обратной совместимости
        self._keys = self._pool._keys
        self._active_indices = self._pool._active_indices
        self._cursor = self._pool._cursor
        self._keys_file = keys_file

    # ── Делегирование в UnifiedKeyPool ──────────────────────────────────

    async def get_next_key(self) -> str:
        return await self._pool.get_next_key()

    async def mark_exhausted(self, token: str):
        """Backward-compatible: cause по умолчанию insufficient_credits."""
        await self._pool.mark_exhausted(token, "insufficient_credits")

    async def mark_exhausted_reason(self, token: str, reason: str):
        """Явное указание причины для recovery rules."""
        await self._pool.mark_exhausted(token, reason)

    def get_stats(self) -> dict:
        return self._pool.get_stats()

    @property
    def active_count(self) -> int:
        return self._pool.active_count

    # ── Синхронизация алиасов (для кода, читающего _keys напрямую) ───────

    def _sync_aliases(self):
        """Обновляет алиасы после мутаций в UnifiedKeyPool."""
        self._keys = self._pool._keys
        self._active_indices = self._pool._active_indices
        self._cursor = self._pool._cursor
