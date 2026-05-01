"""Database layer for meAI - SQLite with async support"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self, database_url: str):
        """Initialize database manager

        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite+aiosqlite:///./data/meai.db)
        """
        self.database_url = database_url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Connect to database and configure WAL mode"""
        if self._engine is not None:
            return

        # Create async engine
        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
        )

        # Configure WAL mode for SQLite (better concurrency)
        if "sqlite" in self.database_url:
            @event.listens_for(self._engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._engine is not None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager

        Usage:
            async with db.session() as session:
                result = await session.execute(...)
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def health_check(self) -> bool:
        """Check database health

        Returns:
            True if database is healthy, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
