"""SQLite-хранилище истории диалога, per-session.

Сырой sqlite3 (без SQLAlchemy) — меньше зависимостей. WAL mode для
конкурентных чтений. Синхронные вызовы обёрнуты в asyncio.to_thread.
Per-session asyncio.Lock предотвращает race condition на историю (DIALOG-05).
"""
import asyncio
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("SESSIONS_DB_PATH", "/opt/data/sessions.db")

_session_locks: dict[str, asyncio.Lock] = {}


def get_session_lock(session_id: str) -> asyncio.Lock:
    """Возвращает (или создаёт) asyncio.Lock для session_id.

    Per-session изоляция — разные session_id не блокируют друг друга.
    Исправление бага глобальной очереди старого main.py:47 (DIALOG-05).
    """
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


def init_db(db_path: str | None = None) -> None:
    """Создаёт таблицу messages если её нет. Идемпотентна."""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)"
        )
        conn.commit()
        logger.info("SQLite init OK: %s", path)
    finally:
        conn.close()


def load_history(session_id: str, db_path: str | None = None) -> list[dict]:
    """Загружает историю диалога для session_id (синхронно)."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]
    finally:
        conn.close()


def save_message(session_id: str, role: str, content: str, db_path: str | None = None) -> None:
    """Сохраняет сообщение в историю session_id (синхронно)."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()
    finally:
        conn.close()


# --- async-обёртки ---------------------------------------------------------

async def async_load_history(session_id: str, db_path: str | None = None) -> list[dict]:
    return await asyncio.to_thread(load_history, session_id, db_path)


async def async_save_message(
    session_id: str, role: str, content: str, db_path: str | None = None
) -> None:
    await asyncio.to_thread(save_message, session_id, role, content, db_path)


async def async_init_db(db_path: str | None = None) -> None:
    await asyncio.to_thread(init_db, db_path)
