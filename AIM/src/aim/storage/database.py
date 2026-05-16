"""
Database configuration for AIM

SQLAlchemy async setup with PostgreSQL/SQLite support.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import os

# Base class for all models
Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv(
    "AIM_DATABASE_URL",
    "sqlite+aiosqlite:///./data/aim.db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session

    Usage:
        async with get_db() as db:
            # Use db session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables

    Creates all tables defined in Base metadata.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all database tables

    WARNING: This will delete all data!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
