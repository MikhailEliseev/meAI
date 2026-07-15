"""Тесты UnifiedKeyPool — единого пула API-ключей.

Проверяет:
- Round-robin ротацию
- Atomic save (corruption resistance)
- mark_exhausted → persist → reload
- _auto_recover (rate_limited 30м, insufficient_credits monthly, invalid never)
- Concurrent get_next_key (asyncio.Lock)
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from app.lib.key_pool import UnifiedKeyPool


@pytest.fixture
def tmp_keys_file():
    """Создаёт временный JSON-файл с тестовыми ключами."""
    data = {
        "provider": "test",
        "updated_at": "2026-07-15T00:00:00+00:00",
        "keys": [
            {"token": "key-001", "label": "test-1", "status": "active",
             "exhausted_at": None, "exhaust_reason": None, "last_checked": None},
            {"token": "key-002", "label": "test-2", "status": "active",
             "exhausted_at": None, "exhaust_reason": None, "last_checked": None},
            {"token": "key-003", "label": "test-3", "status": "active",
             "exhausted_at": None, "exhaust_reason": None, "last_checked": None},
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    yield path
    # Cleanup
    for suffix in ("", ".bak", ".tmp"):
        p = path + suffix
        if os.path.exists(p):
            os.unlink(p)


# ═══════════════════════════════════════════════════════════════════════════
# Round-robin
# ═══════════════════════════════════════════════════════════════════════════

class TestRoundRobin:
    """Проверка round-robin ротации."""

    @pytest.mark.asyncio
    async def test_cycles_through_keys(self, tmp_keys_file):
        """get_next_key() возвращает ключи по кругу."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        results = [await pool.get_next_key() for _ in range(7)]
        # 3 ключа → цикл 001, 002, 003, 001, 002, 003, 001
        assert results[0] != results[1] != results[2]
        assert results[0] == results[3]  # цикл повторился
        assert results[1] == results[4]

    @pytest.mark.asyncio
    async def test_skips_exhausted(self, tmp_keys_file):
        """Exhausted ключи пропускаются."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-002", "insufficient_credits")
        results = [await pool.get_next_key() for _ in range(4)]
        # key-002 не должен появиться
        assert "key-002" not in results
        assert set(results) == {"key-001", "key-003"}


# ═══════════════════════════════════════════════════════════════════════════
# Atomic save + persist
# ═══════════════════════════════════════════════════════════════════════════

class TestAtomicSave:
    """Проверка персистенции и атомарной записи."""

    @pytest.mark.asyncio
    async def test_mark_exhausted_persists(self, tmp_keys_file):
        """mark_exhausted сохраняет статус в JSON-файл."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "insufficient_credits")

        # Reload из файла и проверяем
        pool2 = UnifiedKeyPool("test", tmp_keys_file)
        key1 = [k for k in pool2._keys if k["token"] == "key-001"][0]
        assert key1["status"] == "exhausted"
        assert key1["exhaust_reason"] == "insufficient_credits"
        assert key1["exhausted_at"] is not None

    @pytest.mark.asyncio
    async def test_bak_file_created(self, tmp_keys_file):
        """При save создаётся .bak файл (предыдущая версия)."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "insufficient_credits")
        assert os.path.exists(tmp_keys_file + ".bak")

    @pytest.mark.asyncio
    async def test_no_tmp_left_after_save(self, tmp_keys_file):
        """После успешного save .tmp файл удаляется."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "insufficient_credits")
        assert not os.path.exists(tmp_keys_file + ".tmp")


# ═══════════════════════════════════════════════════════════════════════════
# Auto-recovery
# ═══════════════════════════════════════════════════════════════════════════

class TestAutoRecovery:
    """Проверка автоматического восстановления ключей."""

    @pytest.mark.asyncio
    async def test_rate_limited_recovers_after_30min(self, tmp_keys_file):
        """rate_limited ключ восстанавливается через 30 минут."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "rate_limited")

        # Меняем exhausted_at на 31 минуту назад
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
        for k in pool._keys:
            if k["token"] == "key-001":
                k["exhausted_at"] = old_time
        pool._save()

        # При следующем get_next_key → auto_recover должен восстановить
        pool2 = UnifiedKeyPool("test", tmp_keys_file)
        key = await pool2.get_next_key()
        # key-001 должен снова быть доступен
        stats = pool2.get_stats()
        assert stats["active"] == 3  # все 3 восстановлены

    @pytest.mark.asyncio
    async def test_rate_limited_not_recovered_before_30min(self, tmp_keys_file):
        """rate_limited ключ НЕ восстанавливается раньше 30 минут."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "rate_limited")
        # Не меняем exhausted_at — он только что

        pool2 = UnifiedKeyPool("test", tmp_keys_file)
        stats = pool2.get_stats()
        assert stats["active"] == 2  # key-001 всё ещё exhausted

    @pytest.mark.asyncio
    async def test_invalid_never_recovers(self, tmp_keys_file):
        """invalid ключ НЕ восстанавливается никогда."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "invalid")

        # Даже через 100 дней
        old_time = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        for k in pool._keys:
            if k["token"] == "key-001":
                k["exhausted_at"] = old_time
        pool._save()

        pool2 = UnifiedKeyPool("test", tmp_keys_file)
        stats = pool2.get_stats()
        assert stats["active"] == 2  # key-001 всё ещё exhausted

    @pytest.mark.asyncio
    async def test_insufficient_credits_recovers_next_month(self, tmp_keys_file):
        """insufficient_credits восстанавливается в следующем месяце."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "insufficient_credits")

        # Меняем exhausted_at на прошлый месяц
        now = datetime.now(timezone.utc)
        last_month = now.replace(month=max(1, now.month - 1)) if now.month > 1 else now.replace(year=now.year - 1, month=12)
        for k in pool._keys:
            if k["token"] == "key-001":
                k["exhausted_at"] = last_month.isoformat()
        pool._save()

        pool2 = UnifiedKeyPool("test", tmp_keys_file)
        stats = pool2.get_stats()
        assert stats["active"] == 3  # key-001 восстановлен


# ═══════════════════════════════════════════════════════════════════════════
# Concurrency
# ═══════════════════════════════════════════════════════════════════════════

class TestConcurrency:
    """Проверка конкурентного доступа (asyncio.Lock)."""

    @pytest.mark.asyncio
    async def test_concurrent_get_next_key(self, tmp_keys_file):
        """10 конкурентных get_next_key() не ломают пул."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        results = await asyncio.gather(*[pool.get_next_key() for _ in range(10)])
        # Все 10 результатов — валидные ключи
        assert len(results) == 10
        assert all(r.startswith("key-") for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_mark_exhausted(self, tmp_keys_file):
        """Конкурентная mark_exhausted не ломает JSON."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await asyncio.gather(
            pool.mark_exhausted("key-001", "rate_limited"),
            pool.mark_exhausted("key-002", "rate_limited"),
        )
        stats = pool.get_stats()
        assert stats["exhausted"] == 2

        # JSON валиден после конкурентной записи
        with open(tmp_keys_file) as f:
            data = json.load(f)
        assert len(data["keys"]) == 3


# ═══════════════════════════════════════════════════════════════════════════
# Stats + error handling
# ═══════════════════════════════════════════════════════════════════════════

class TestStatsAndErrors:
    """Проверка статистики и обработки ошибок."""

    def test_get_stats(self, tmp_keys_file):
        """get_stats возвращает корректную статистику."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        stats = pool.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 3
        assert stats["exhausted"] == 0

    @pytest.mark.asyncio
    async def test_all_exhausted_raises(self, tmp_keys_file):
        """Все ключи exhausted → RuntimeError."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        await pool.mark_exhausted("key-001", "invalid")
        await pool.mark_exhausted("key-002", "invalid")
        await pool.mark_exhausted("key-003", "invalid")

        with pytest.raises(RuntimeError, match="All test keys exhausted"):
            await pool.get_next_key()

    def test_file_not_found(self):
        """Несуществующий файл → FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            UnifiedKeyPool("test", "/nonexistent/path/keys.json")

    @pytest.mark.asyncio
    async def test_mark_unknown_key_ignored(self, tmp_keys_file):
        """Пометка несуществующего ключа — без ошибки."""
        pool = UnifiedKeyPool("test", tmp_keys_file)
        # Не должно бросить исключение
        await pool.mark_exhausted("nonexistent-key", "invalid")
        assert pool.get_stats()["active"] == 3  # ничего не изменилось
