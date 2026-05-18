"""Pytest configuration for AIM tests."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from aim.database import Base
from aim.main import app

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all models to register them with Base.metadata
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


@pytest.fixture
async def db(db_session):
    """Alias for db_session to match test expectations."""
    return db_session


@pytest.fixture
async def client(db, encryption_key):
    """Create async HTTP client for API testing."""
    from aim.database import get_db

    # Override get_db dependency to use test database
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_recaptcha():
    """Mock reCAPTCHA verification for all tests automatically."""
    with patch("aim.services.lead_capture.LeadCaptureService._verify_recaptcha") as mock:
        mock.return_value = AsyncMock(return_value=None)
        yield mock


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit cache between tests to prevent cross-test contamination."""
    from aim.services.lead_capture import LeadCaptureService
    LeadCaptureService._rate_limit_cache.clear()
    yield
    LeadCaptureService._rate_limit_cache.clear()


@pytest.fixture(autouse=True)
def mock_document_processing():
    """Mock document processing pipeline for all tests.

    Replaces OCR + AI extraction + validation with a fast pass-through
    that marks documents as completed/valid without real processing.
    Individual tests can override this mock for failure cases.
    """
    from datetime import datetime as dt

    async def mock_process_document(self, document, file_path, db):
        document.status = "completed"
        document.validation_status = "valid"
        document.ocr_text = "Mock OCR text for testing"
        document.extracted_data = {
            "clinic_name": "Test Clinic",
            "inn": "1234567890",
            "ogrn": "1234567890123",
            "license_number": "LO-77-01-123456",
        }
        document.confidence_score = 0.95
        document.processed_at = dt.utcnow()
        await db.commit()
        return document

    with patch(
        "aim.services.documents.processor.DocumentProcessor.process_document",
        mock_process_document,
    ):
        yield
