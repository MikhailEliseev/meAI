"""Database configuration for AIM agency

SQLAlchemy async setup with SQLite development fallback and PostgreSQL production.
Alembic manages schema migrations.

Part of: Phase 12-02 — PostgreSQL migration
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import Base from storage.models (single source of truth)
from aim.storage.models import Base

# Database URL — PostgreSQL for production, SQLite fallback for local dev
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./AIM/data/aim.db",
)

# Create async engine with production pool config
_is_pg = "postgresql" in DATABASE_URL or "asyncpg" in DATABASE_URL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20 if _is_pg else 1,
    max_overflow=10 if _is_pg else 0,
    pool_pre_ping=True if _is_pg else False,
    pool_recycle=3600 if _is_pg else -1,
)

# Attach query profiler to engine
from aim.middleware.profiling import get_profiler
get_profiler().attach(engine.sync_engine)

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
    from aim.models.fz152_audit import FZ152AuditLog  # noqa: F401
    from aim.models.company_profile import CompanyProfileModel  # noqa: F401


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
