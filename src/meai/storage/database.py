"""Database connection and session management"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


class Database:
    """Async database connection manager"""

    def __init__(self, database_url: str):
        """Initialize database connection

        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite+aiosqlite:///./data/meai.db)
        """
        self.database_url = database_url
        self.engine = None
        self._session_maker = None

    async def connect(self) -> None:
        """Connect to database"""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
        )
        self._session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self.engine:
            await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session

        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        if not self._session_maker:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
