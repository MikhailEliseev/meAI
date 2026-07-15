"""UnifiedKeyPool — единый пул API-ключей для всех провайдеров.

Один модуль, одна логика recovery, атомарная запись.
Заменяет 6 разрозненных систем управления ключами.

Принципы:
- asyncio.Lock на все мутации (защита от гонки записи)
- Atomic save: tmp → os.replace(old→bak) → os.replace(tmp→old)
- _auto_recover() при КАЖДОМ get_next_key() (не только при старте)
- Recovery: insufficient_credits → 1-е число месяца; rate_limited → 30 мин
- Чистый модуль: только stdlib, никаких внешних зависимостей
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_RECOVERY_RULES = {
    # Причина → стратегия восстановления
    "rate_limited": timedelta(minutes=30),     # временный 429 → 30 мин
    "insufficient_credits": "next_billing_month",  # ежемесячный reset → 1-е число
    "invalid": None,                            # мёртвый ключ → не восстанавливаем
}

_TMP_STALE_SECONDS = 60


def _utc_now_iso() -> str:
    """Текущее время в UTC ISO формате."""
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str | None) -> datetime | None:
    """Парсит ISO timestamp с timezone. None если невалидный."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _should_recover(key: dict) -> bool:
    """Проверяет, должен ли ключ быть восстановлен по recovery rules."""
    if key.get("status") != "exhausted":
        return False

    reason = key.get("exhaust_reason")
    exhausted_at = _parse_iso(key.get("exhausted_at"))
    now = datetime.now(timezone.utc)

    rule = _RECOVERY_RULES.get(reason)

    if rule is None:
        # invalid → не восстанавливаем
        return False

    if reason == "next_billing_month" or rule == "next_billing_month":
        # insufficient_credits → восстанавливаем 1-го числа следующего месяца
        if exhausted_at is None:
            return True  # нет timestamp — восстанавливаем (защита от старых данных)
        if exhausted_at.year < now.year or \
           (exhausted_at.year == now.year and exhausted_at.month < now.month):
            return True
        return False

    if isinstance(rule, timedelta):
        # rate_limited → восстанавливаем через rule (30 мин)
        if exhausted_at is None:
            return True
        return now >= exhausted_at + rule

    return False


class UnifiedKeyPool:
    """Единый пул ключей с атомарной записью и авто-recovery.

    Args:
        provider: Имя провайдера ("apify", "firecrawl", ...).
        file_path: Путь к JSON файлу с ключами.

    JSON schema:
        {
            "provider": "apify",
            "updated_at": "2026-07-15T...",
            "keys": [
                {
                    "token": "apify_api_...",
                    "label": "key-01",
                    "status": "active",
                    "exhausted_at": null,
                    "exhaust_reason": null,
                    "last_checked": null
                }
            ]
        }
    """

    def __init__(self, provider: str, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Key pool file not found: {file_path}")
        self._provider = provider
        self._file_path = file_path
        self._lock = asyncio.Lock()
        self._keys: list[dict] = []
        self._active_indices: list[int] = []
        self._cursor = 0
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_next_key(self) -> str:
        """Возвращает следующий активный ключ (round-robin).

        Перед возвutom вызывает _auto_recover() — ключи восстанавливаются
        не только при старте, но и при каждом обращении.

        Raises:
            RuntimeError: если все ключи исчерпаны.
        """
        async with self._lock:
            self._auto_recover()
            if not self._active_indices:
                raise RuntimeError(
                    f"All {self._provider} keys exhausted — no active keys remaining"
                )
            idx = self._active_indices[self._cursor % len(self._active_indices)]
            self._cursor = (self._cursor + 1) % len(self._active_indices)
            return self._keys[idx]["token"]

    async def mark_exhausted(self, token: str, reason: str = "insufficient_credits"):
        """Помечает ключ исчерпанным и персистит в файл.

        Args:
            token: Ключ для пометки.
            reason: "rate_limited" | "insufficient_credits" | "invalid".
        """
        async with self._lock:
            self._mark_exhausted_locked(token, reason)

    def get_stats(self) -> dict:
        """Возвращает статистику пула (без блокировки, только чтение)."""
        total = len(self._keys)
        active = sum(1 for k in self._keys if k.get("status") == "active")
        return {
            "provider": self._provider,
            "total": total,
            "active": active,
            "exhausted": total - active,
        }

    @property
    def active_count(self) -> int:
        return len(self._active_indices)

    # ------------------------------------------------------------------
    # Internal — load / save
    # ------------------------------------------------------------------

    def _load(self):
        """Загружает JSON, чистит stale tmp, запускает auto_recover."""
        self._cleanup_stale_tmp()
        with open(self._file_path, "r") as f:
            data = json.load(f)

        # Поддерживаем оба формата: {"keys": [...]} и прямой список
        if isinstance(data, dict):
            self._keys = data.get("keys", [])
            self._provider = data.get("provider", self._provider)
        elif isinstance(data, list):
            # Legacy формат: [{"token": "...", ...}, ...]
            self._keys = data
        else:
            self._keys = []

        # Нормализуем ключи: обеспечиваем все поля
        for k in self._keys:
            if "status" not in k:
                k["status"] = "active"
            if "exhausted_at" not in k:
                k["exhausted_at"] = None
            if "exhaust_reason" not in k:
                k["exhaust_reason"] = None
            if "label" not in k:
                k["label"] = k.get("token", "")[:20] + "..."

        self._auto_recover()
        self._rebuild_indices()

        logger.info(
            "UnifiedKeyPool[%s] loaded: %d total, %d active, %d exhausted — %s",
            self._provider, len(self._keys), len(self._active_indices),
            len(self._keys) - len(self._active_indices), self._file_path,
        )

    def _save(self):
        """Атомарная запись: tmp → os.replace(old→bak) → os.replace(tmp→old).

        Предотвращает corruption при конкурентной записи и сбоях питания.
        """
        tmp_path = self._file_path + ".tmp"
        bak_path = self._file_path + ".bak"

        payload = {
            "provider": self._provider,
            "updated_at": _utc_now_iso(),
            "keys": self._keys,
        }

        with open(tmp_path, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        # Backup текущего → bak, затем tmp → текущий
        if os.path.exists(self._file_path):
            os.replace(self._file_path, bak_path)
        os.replace(tmp_path, self._file_path)

    def _cleanup_stale_tmp(self):
        """Удаляет stale .tmp файл (если процесс упал mid-write)."""
        tmp_path = self._file_path + ".tmp"
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
        """Восстанавливает ключи по recovery rules. ВСЕГДА вызывает _save().

        Фикс корневого бага: recovery-логика раньше не персистила изменения.
        """
        recovered = 0
        for key in self._keys:
            if _should_recover(key):
                key["status"] = "active"
                key["exhausted_at"] = None
                key["exhaust_reason"] = None
                recovered += 1

        if recovered:
            logger.info(
                "UnifiedKeyPool[%s] auto-recovered %d keys", self._provider, recovered
            )
            self._save()
            self._rebuild_indices()

    # ------------------------------------------------------------------
    # Internal — indices + exhaustion
    # ------------------------------------------------------------------

    def _rebuild_indices(self):
        """Перестраивает список индексов активных ключей."""
        self._active_indices = [
            i for i, k in enumerate(self._keys) if k.get("status") == "active"
        ]
        # Сброс курсора если он вне диапазона
        if self._active_indices:
            self._cursor = self._cursor % len(self._active_indices)
        else:
            self._cursor = 0

    def _mark_exhausted_locked(self, token: str, reason: str):
        """Помечает ключ исчерпанным. Вызывающий должен держать self._lock."""
        for key in self._keys:
            stored_token = key.get("token", "")
            if stored_token == token and key.get("status") == "active":
                key["status"] = "exhausted"
                key["exhausted_at"] = _utc_now_iso()
                key["exhaust_reason"] = reason
                label = key.get("label", token[:20] + "...")
                self._save()
                self._rebuild_indices()
                logger.warning(
                    "UnifiedKeyPool[%s] key exhausted: %s (reason=%s, remaining=%d)",
                    self._provider, label, reason, len(self._active_indices),
                )
                return

        logger.debug(
            "UnifiedKeyPool[%s] token not found or already exhausted: %s...",
            self._provider, token[:20],
        )
