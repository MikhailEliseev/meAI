"""Tests for database layer"""

import pytest
from pathlib import Path
from sqlalchemy import text
from meai.storage.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_connects(tmp_path):
    """Test database connection"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    db = DatabaseManager(db_url)
    await db.connect()
    
    assert db.is_connected()
    
    await db.disconnect()
    assert not db.is_connected()


@pytest.mark.asyncio
async def test_database_session_factory(tmp_path):
    """Test session factory creates sessions"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    db = DatabaseManager(db_url)
    await db.connect()
    
    async with db.session() as session:
        assert session is not None
        # Session should be usable
        result = await session.execute(text("SELECT 1"))
        assert result is not None
    
    await db.disconnect()


@pytest.mark.asyncio
async def test_database_health_check(tmp_path):
    """Test database health check"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    db = DatabaseManager(db_url)
    await db.connect()
    
    is_healthy = await db.health_check()
    assert is_healthy is True
    
    await db.disconnect()
    
    # After disconnect, health check should fail
    is_healthy = await db.health_check()
    assert is_healthy is False


@pytest.mark.asyncio
async def test_database_wal_mode(tmp_path):
    """Test database uses WAL mode for concurrency"""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    db = DatabaseManager(db_url)
    await db.connect()
    
    # Check WAL mode is enabled
    async with db.session() as session:
        result = await session.execute(text("PRAGMA journal_mode"))
        mode = result.scalar()
        assert mode.lower() == "wal"
    
    await db.disconnect()
