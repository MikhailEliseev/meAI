"""Firecrawl key bank через UnifiedKeyPool (замена ломаной версии).

Единый пул: atomic save, asyncio.Lock, auto-recovery.
Ключи: /opt/keys/firecrawl.json (через env FIRECRAWL_KEYS_FILE).

Обратная совместимость: сохранён интерфейс FirecrawlKeyBank + classify_exhaustion + key_bank singleton.
"""
import asyncio
import logging
import os
import threading as _threading

from app.lib.key_pool import UnifiedKeyPool

logger = logging.getLogger(__name__)

# Хранилище для background tasks (предотвращает GC)
_bg_tasks: set = set()

FIRECRAWL_KEYS_PATH = os.getenv(
    "FIRECRAWL_KEYS_FILE",
    os.getenv("HERMES_DATA_DIR", "/opt/data") + "/firecrawl_keys.json",
)


def classify_exhaustion(status_code: int, body: str) -> bool:
    """True если ответ указывает на исчерпание ключа (402/429/quota/limit)."""
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
    """Thin wrapper над UnifiedKeyPool для обратной совместимости.

    Сохраняет sync интерфейс get_key()/mark_exhausted() для существующих тулов,
    но внутри использует UnifiedKeyPool с блокировками и auto-recovery.
    """

    def __init__(self):
        self._pool: UnifiedKeyPool | None = None
        self._sync_lock = _threading.Lock()
        self._sync_cursor = 0
        self._init_pool()

    def _init_pool(self):
        """Инициализирует пул. Если JSON не найден — fallback на env ключи."""
        global FIRECRAWL_KEYS_PATH
        try:
            self._pool = UnifiedKeyPool("firecrawl", FIRECRAWL_KEYS_PATH)
        except FileNotFoundError:
            # Fallback: нет JSON, пробуем создать из env ключей
            keys = self._collect_env_keys()
            if keys:
                self._create_pool_from_env(keys)
            else:
                logger.warning("FirecrawlKeyBank: no keys found (no JSON, no env)")
                self._pool = None

    def _collect_env_keys(self) -> list[str]:
        """Собирает Firecrawl ключи из env (fallback если нет JSON)."""
        seen = set()
        keys = []
        for prefix in ("FIRECRAWL_API_KEY_", "FIRECRAWL_KEY_"):
            for i in range(1, 21):
                k = os.getenv(f"{prefix}{i:02d}", "") or os.getenv(f"{prefix}{i}", "")
                if k and k not in seen:
                    keys.append(k)
                    seen.add(k)
        single = os.getenv("FIRECRAWL_API_KEY", "")
        if single and single not in seen:
            keys.append(single)
        return keys

    def _create_pool_from_env(self, keys: list[str]):
        """Создаёт JSON-файл из env ключей и инициализирует пул."""
        import json
        global FIRECRAWL_KEYS_PATH
        os.makedirs(os.path.dirname(FIRECRAWL_KEYS_PATH) or ".", exist_ok=True)
        data = {
            "provider": "firecrawl",
            "updated_at": "2026-07-15T00:00:00+00:00",
            "keys": [
                {"token": k, "label": f"env-{i+1}", "status": "active",
                 "exhausted_at": None, "exhaust_reason": None, "last_checked": None}
                for i, k in enumerate(keys)
            ],
        }
        with open(FIRECRAWL_KEYS_PATH, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("FirecrawlKeyBank: created %s from %d env keys", FIRECRAWL_KEYS_PATH, len(keys))
        self._pool = UnifiedKeyPool("firecrawl", FIRECRAWL_KEYS_PATH)

    def get_key(self) -> str | None:
        """Возвращает следующий активный ключ.

        Потокобезопасно через threading.Lock (не обходит asyncio.Lock пула).
        Если в event loop — делает snapshot активных ключей и round-robin по ним.
        """
        if self._pool is None:
            return None
        # Потокобезопасный snapshot активных ключей
        with self._sync_lock:
            active_tokens = [
                k["token"] for k in self._pool._keys if k.get("status") == "active"
            ]
            if not active_tokens:
                return None
            key = active_tokens[self._sync_cursor % len(active_tokens)]
            self._sync_cursor += 1
            return key

    async def mark_exhausted_async(self, key: str, reason: str = "insufficient_credits"):
        """Помечает ключ исчерпанным (async — правильный путь)."""
        if self._pool is None:
            return
        await self._pool.mark_exhausted(key, reason)

    def mark_exhausted(self, key: str, reason: str = "insufficient_credits"):
        """Помечает ключ исчерпанным (sync wrapper — fire-and-forget safe)."""
        if self._pool is None:
            return
        try:
            loop = asyncio.get_running_loop()
            # Сохраняем reference чтобы task не был GC'd
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
