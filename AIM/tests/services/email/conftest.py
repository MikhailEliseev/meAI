"""Pytest configuration and fixtures for email services tests

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import os
import base64
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import all models to register them with Base.metadata
from aim.storage.models import Base
from aim.models.lead import Lead
from aim.models.linear_task import LinearTask
from aim.models.email_workflow import EmailWorkflow
from aim.models.scheduled_email import ScheduledEmail
from aim.models.email_event import EmailEvent
from aim.models.email_template import EmailTemplate


@pytest.fixture(scope="session", autouse=True)
def setup_encryption_key():
    """Set up encryption key for tests."""
    # Generate a test encryption key
    test_key = base64.b64encode(os.urandom(32)).decode()
    os.environ["AIM_ENCRYPTION_KEY"] = test_key
    yield
    # Cleanup
    if "AIM_ENCRYPTION_KEY" in os.environ:
        del os.environ["AIM_ENCRYPTION_KEY"]


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()
