"""Unit-тесты SQLite session-слоя (Phase 2).

Используют tmp_path для изолированной БД — реальная prod БД не трогается.
"""
import pytest

from app import session


@pytest.mark.asyncio
async def test_session_creates_db_if_missing(tmp_path, monkeypatch):
    """init_db() создаёт файл БД с таблицей messages."""
    db = tmp_path / "test.db"
    session.init_db(str(db))
    assert db.exists()

    import sqlite3
    conn = sqlite3.connect(str(db))
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    assert ("messages",) in tables


@pytest.mark.asyncio
async def test_session_save_load_roundtrip(tmp_path, monkeypatch):
    """save_message → load_history round-trip возвращает то же."""
    db = str(tmp_path / "test.db")
    monkeypatch.setattr(session, "DB_PATH", db)
    session.init_db(db)

    await session.async_save_message("s1", "user", "привет")
    history = await session.async_load_history("s1")

    assert history == [{"role": "user", "content": "привет"}]


@pytest.mark.asyncio
async def test_session_isolation(tmp_path, monkeypatch):
    """save_message в s1 НЕ виден в load_history s2 — изоляция session_id."""
    db = str(tmp_path / "test.db")
    monkeypatch.setattr(session, "DB_PATH", db)
    session.init_db(db)

    await session.async_save_message("s1", "user", "секрет сессии 1")
    await session.async_save_message("s2", "user", "другая сессия")

    h1 = await session.async_load_history("s1")
    h2 = await session.async_load_history("s2")

    assert len(h1) == 1 and h1[0]["content"] == "секрет сессии 1"
    assert len(h2) == 1 and h2[0]["content"] == "другая сессия"
    # s2 не видит s1
    assert "секрет сессии 1" not in str(h2)


def test_get_session_lock_returns_per_session_lock():
    """get_session_lock возвращает разные lock'и для разных session_id."""
    lock_a = session.get_session_lock("aaa")
    lock_b = session.get_session_lock("bbb")
    assert lock_a is not lock_b
    # тот же session_id → тот же lock
    assert session.get_session_lock("aaa") is lock_a
