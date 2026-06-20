"""firecrawl_key_bank — Firecrawl API key rotation.

Engine.py использует этот модуль для ротации Firecrawl-ключей при
exhaustion (402/401/Insufficient credits).

Ключи берутся из переменных окружения FIRECRAWL_KEY_1, FIRECRAWL_KEY_2, ...
или из FIRECRAWL_API_KEY (один ключ).
"""

import logging
import os
import threading

logger = logging.getLogger(__name__)


class FirecrawlKeyBank:
    """Пул Firecrawl API-ключей с ротацией."""

    def __init__(self):
        self._keys: list[str] = []
        self._exhausted: set[str] = set()
        self._index: int = 0
        self._lock = threading.Lock()
        self._load_keys()

    def _load_keys(self):
        """Загрузить ключи из переменных окружения."""
        # Множественные ключи: FIRECRAWL_KEY_1, FIRECRAWL_KEY_2, ...
        for i in range(1, 11):
            key = os.getenv(f"FIRECRAWL_KEY_{i}", "")
            if key and key not in self._keys:
                self._keys.append(key)

        # Один ключ: FIRECRAWL_API_KEY
        single_key = os.getenv("FIRECRAWL_API_KEY", "")
        if single_key and single_key not in self._keys:
            self._keys.append(single_key)

        if self._keys:
            logger.info("FirecrawlKeyBank: loaded %d keys", len(self._keys))
        else:
            logger.warning("FirecrawlKeyBank: NO keys found in environment")

    def get_key(self) -> str | None:
        """Получить текущий не-exhausted ключ."""
        with self._lock:
            available = [k for k in self._keys if k not in self._exhausted]
            if not available:
                return None

            if self._index >= len(self._keys):
                self._index = 0

            # Найти следующий доступный
            for _ in range(len(self._keys)):
                candidate = self._keys[self._index % len(self._keys)]
                self._index = (self._index + 1) % len(self._keys)
                if candidate not in self._exhausted:
                    return candidate

            return None

    def mark_exhausted(self, key: str) -> None:
        """Пометить ключ как exhausted."""
        with self._lock:
            self._exhausted.add(key)
            logger.warning("FirecrawlKeyBank: marked key as exhausted (%d/%d available)",
                           len(self._keys) - len(self._exhausted), len(self._keys))

    def rotate(self) -> str | None:
        """Взять следующий ключ (пометив текущий exhausted)."""
        with self._lock:
            available = [k for k in self._keys if k not in self._exhausted]
            if not available:
                logger.error("FirecrawlKeyBank: ALL keys exhausted")
                return None
            return available[0]

    def reset(self) -> None:
        """Сбросить exhausted-метки (для нового пайплайна)."""
        with self._lock:
            self._exhausted.clear()
            self._index = 0
            logger.info("FirecrawlKeyBank: reset — all keys available")


# Глобальный экземпляр
_bank: FirecrawlKeyBank | None = None
_bank_lock = threading.Lock()


def _get_bank() -> FirecrawlKeyBank:
    """Ленивая инициализация глобального банка ключей."""
    global _bank
    with _bank_lock:
        if _bank is None:
            _bank = FirecrawlKeyBank()
    return _bank


def get_key_with_fallback() -> str | None:
    """Получить ключ с fallback-логикой.

    Используется engine.py при ротации ключей.
    """
    return _get_bank().get_key()


def mark_exhausted(key: str | None = None) -> None:
    """Пометить текущий ключ как exhausted.

    Если key не указан — используется текущий ключ из банка.
    """
    bank = _get_bank()
    if key:
        bank.mark_exhausted(key)
    else:
        current = bank.get_key()
        if current:
            bank.mark_exhausted(current)


def rotate_key() -> str | None:
    """Ротировать на следующий ключ."""
    return _get_bank().rotate()
