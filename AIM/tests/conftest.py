"""Pytest configuration for AIM tests."""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from aim.database import Base

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def encryption_key():
    """Set encryption key for tests."""
    import base64
    # Generate proper 32-byte random key and encode to base64
    key = base64.b64encode(os.urandom(32)).decode()
    os.environ["AIM_ENCRYPTION_KEY"] = key
    yield key
    del os.environ["AIM_ENCRYPTION_KEY"]


@pytest.fixture
async def db_session(encryption_key):
    """Create async database session for tests."""
    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create session
    async with async_session_factory() as session:
        yield session

    # Cleanup
    await engine.dispose()
