"""Database configuration for AIM agency

SQLAlchemy async setup with SQLite backend.

Part of: Phase 11 - Client Acquisition (Task 2.1)
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import Base from storage.models (single source of truth)
from aim.storage.models import Base

# Database URL (SQLite for development, PostgreSQL for production)
DATABASE_URL = "sqlite+aiosqlite:///./AIM/data/aim.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Import all models to register them with Base.metadata
# This must happen after Base is imported
def _import_models():
    """Import all models to register them with Base.metadata"""
    from aim.models.lead import Lead  # noqa: F401
    from aim.models.linear_task import LinearTask  # noqa: F401
    from aim.models.email_workflow import EmailWorkflow  # noqa: F401
    from aim.models.scheduled_email import ScheduledEmail  # noqa: F401
    from aim.models.email_event import EmailEvent  # noqa: F401
    from aim.models.email_template import EmailTemplate  # noqa: F401
    from aim.models.payment import Payment  # noqa: F401
    from aim.models.document import Document  # noqa: F401
    from aim.models.onboarding import Onboarding  # noqa: F401


_import_models()


async def get_db() -> AsyncSession:
    """Get database session

    Usage:
        async with get_db() as db:
            # Use db session
            pass
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables)

    Usage:
        await init_db()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
