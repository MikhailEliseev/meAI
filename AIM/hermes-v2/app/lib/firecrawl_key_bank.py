"""Firecrawl key bank через UnifiedKeyPool.

Единый пул: atomic save, asyncio.Lock, auto-recovery.
Ключи: /opt/keys/firecrawl.json (через env FIRECRAWL_KEYS_FILE).

Единый источник истины — JSON файл. Env vars НЕ используются.
"""
import asyncio
import logging
import os

from app.lib.key_pool import UnifiedKeyPool

logger = logging.getLogger(__name__)

# Хранилище для background tasks (предотвращает GC)
_bg_tasks: set = set()

FIRECRAWL_KEYS_PATH = os.getenv(
    "FIRECRAWL_KEYS_FILE",
    os.getenv("HERMES_DATA_DIR", "/opt/data") + "/firecrawl_keys.json",
)


def classify_exhaustion(status_code: int, body: str) -> bool:
    """True если ответ указывает на исчерпания ключа (402/429/quota/limit)."""
    if status_code == 402 or status_code == 429:
        return True
    body_lower = body.lower() if body else ""
    return "quota" in body_lower or "limit" in body_lower or "payment required" in body_lower


def classify_exhaustion_reason(status_code: int, body: str) -> str:
    """Возвращает причину исчерпания для recovery rules."""
    if status_code == 429:
        return "rate_limited"
    if status_code == 402:
        return "insufficient_credits"
    body_lower = body.lower() if body else ""
    if "quota" in body_lower or "limit" in body_lower or "payment required" in body_lower:
        return "insufficient_credits"
    return "invalid"


class FirecrawlKeyBank:
    """Thin wrapper над UnifiedKeyPool.

    Единый источник ключей — JSON файл. Никаких env fallback.
    Async-only интерфейс — нет sync get_key() (был race condition).
    """

    def __init__(self):
        self._pool: UnifiedKeyPool | None = None
        self._init_pool()

    def _init_pool(self):
        """Инициализирует пул из JSON файла."""
        try:
            self._pool = UnifiedKeyPool("firecrawl", FIRECRAWL_KEYS_PATH)
        except FileNotFoundError:
            logger.error(
                "FirecrawlKeyBank: JSON file not found: %s — "
                "no env fallback (keys must be in JSON pool)",
                FIRECRAWL_KEYS_PATH,
            )
            self._pool = None

    async def get_key_async(self) -> str | None:
        """Возвращает следующий активный ключ (async — правильный путь).

        Использует asyncio.Lock из UnifiedKeyPool — безопасно.
        """
        if self._pool is None:
            return None
        try:
            return await self._pool.get_next_key()
        except RuntimeError:
            logger.warning("FirecrawlKeyBank: all keys exhausted")
            return None

    async def mark_exhausted_async(self, key: str, reason: str = "insufficient_credits"):
        """Помечает ключ исчерпанным (async — правильный путь)."""
        if self._pool is None:
            return
        await self._pool.mark_exhausted(key, reason)

    def mark_exhausted(self, key: str, reason: str = "insufficient_credits"):
        """Sync wrapper для mark_exhausted (fire-and-forget safe)."""
        if self._pool is None:
            return
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._pool.mark_exhausted(key, reason))
            _bg_tasks.add(task)
            task.add_done_callback(_bg_tasks.discard)
        except RuntimeError:
            try:
                asyncio.run(self._pool.mark_exhausted(key, reason))
            except Exception as e:
                logger.warning("mark_exhausted failed: %s", e)


# Singleton (lazy — инициализируется при первом обращении, не при импорте)
key_bank: FirecrawlKeyBank | None = None


def get_key_bank() -> FirecrawlKeyBank:
    """Возвращает singleton FirecrawlKeyBank."""
    global key_bank
    if key_bank is None:
        key_bank = FirecrawlKeyBank()
    return key_bank
