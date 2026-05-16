"""Tests for Analytics API Endpoints

Part of: Phase 11 Sprint 2 - Task 2.5
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from aim.api.analytics import router
from aim.models.email_event import EmailEvent
from aim.models.email_workflow import EmailWorkflow
from aim.models.lead import Lead
from aim.models.linear_task import LinearTask
from aim.models.scheduled_email import ScheduledEmail
from aim.utils.encryption import FieldEncryption


@pytest.fixture
def app(db_session: AsyncSession):
    """FastAPI app with analytics router and test database."""
    from aim.database import get_db

    app = FastAPI()
    app.include_router(router, prefix="/api")

    # Override database dependency to use test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest.fixture
def encryption():
    """Encryption utility fixture."""
    return FieldEncryption()


@pytest.fixture
async def sample_data(db_session: AsyncSession, encryption: FieldEncryption):
    """Create sample data for API tests."""
    now = datetime.utcnow()

    # Create leads
    leads = []
    for i in range(3):
        lead = Lead(
            id=f"lead_20260516_00{i+1}",
            name_encrypted=encryption.encrypt(f"Dr. Test {i}"),
            email_encrypted=encryption.encrypt(f"test{i}@example.com"),
            email_hash=Lead.hash_email(f"test{i}@example.com"),
            phone_encrypted=encryption.encrypt(f"+7900000000{i}"),
            clinic_name_encrypted=encryption.encrypt(f"Clinic {i}"),
            specialty="dentist",
            source="landing_page",
            fz152_consent=True,
            fz152_consent_timestamp=now,
            fz152_consent_ip="127.0.0.1",
            score=70 + i * 10,
            tier=["hot", "warm", "cold"][i],
            created_at=now - timedelta(days=i),
        )
        db_session.add(lead)
        leads.append(lead)

    await db_session.commit()
    for lead in leads:
        await db_session.refresh(lead)

    # Create workflows
    workflows = []
    for lead in leads:
        workflow = EmailWorkflow(
            lead_id=lead.id,
            tier=lead.tier,
            status="active",
        )
        db_session.add(workflow)
        workflows.append(workflow)

    await db_session.commit()
    for workflow in workflows:
        await db_session.refresh(workflow)

    # Create emails
    emails = []
    for workflow in workflows:
        email = ScheduledEmail(
            workflow_id=workflow.id,
            template_id="welcome",
            recipient_email="test@example.com",
            subject="Welcome",
            html_content="<p>Welcome</p>",
            text_content="Welcome",
            scheduled_at=now - timedelta(hours=2),
            sent_at=now - timedelta(hours=1),
            status="sent",
        )
        db_session.add(email)
        emails.append(email)

    await db_session.commit()
    for email in emails:
        await db_session.refresh(email)

    # Create events
    for email in emails:
        event = EmailEvent(
            email_id=email.id,
            event_type="delivered",
            occurred_at=now - timedelta(minutes=55),
        )
        db_session.add(event)

    await db_session.commit()

    # Create task
    task = LinearTask(
        id="task_001",
        lead_id=leads[0].id,
        linear_issue_id="LEAD-123",
        linear_url="https://linear.app/issue/LEAD-123",
        status="todo",
        created_at=now,
        updated_at=now,
    )
    db_session.add(task)
    await db_session.commit()

    return {"leads": leads, "workflows": workflows, "emails": emails}


@pytest.mark.asyncio
class TestAnalyticsAPI:
    """Test suite for Analytics API endpoints."""

    async def test_get_lead_analytics(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/leads endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/leads",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_leads"] == 3
            assert "leads_by_tier" in data
            assert "average_score" in data

    async def test_get_lead_analytics_filtered_by_tier(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/leads with tier filter."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/leads",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "tier": "hot",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_leads"] == 1

    async def test_get_lead_analytics_invalid_date_range(
        self,
        app: FastAPI,
        db_session: AsyncSession,
    ):
        """Test GET /api/analytics/leads with invalid date range."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow()
            end_date = datetime.utcnow() - timedelta(days=7)

            response = await client.get(
                "/api/analytics/leads",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

            assert response.status_code == 422
            assert "end_date must be after start_date" in response.json()["detail"]

    async def test_get_lead_analytics_invalid_tier(
        self,
        app: FastAPI,
        db_session: AsyncSession,
    ):
        """Test GET /api/analytics/leads with invalid tier."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/leads",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "tier": "invalid",
                },
            )

            assert response.status_code == 422

    async def test_get_email_analytics(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/emails endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/emails",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

            if response.status_code != 200:
                print(f"Error response: {response.json()}")

            assert response.status_code == 200
            data = response.json()
            assert data["total_sent"] == 3
            assert "delivery_rate" in data
            assert "open_rate" in data

    async def test_get_email_analytics_filtered_by_tier(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/emails with tier filter."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/emails",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "tier": "warm",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_sent"] == 1

    async def test_get_conversion_funnel(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/funnel endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/funnel",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["leads_captured"] == 3
            assert data["tasks_created"] == 1
            assert "conversion_rates" in data

    async def test_get_realtime_stats(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/realtime endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/realtime")

            assert response.status_code == 200
            data = response.json()
            assert "leads_today" in data
            assert "emails_sent_today" in data
            assert "active_workflows" in data
            assert "hot_leads_count" in data

    async def test_export_report_csv(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/export with CSV format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/export",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "format": "csv",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "file_path" in data
            assert "file_size" in data
            assert data["format"] == "csv"

    async def test_export_report_json(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/export with JSON format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/export",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "format": "json",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["format"] == "json"

    async def test_export_report_pdf(
        self,
        app: FastAPI,
        db_session: AsyncSession,
        sample_data: dict,
    ):
        """Test GET /api/analytics/export with PDF format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/export",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "format": "pdf",
                    "include_charts": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["format"] == "pdf"

    async def test_export_report_invalid_format(
        self,
        app: FastAPI,
        db_session: AsyncSession,
    ):
        """Test GET /api/analytics/export with invalid format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()

            response = await client.get(
                "/api/analytics/export",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "format": "xml",
                },
            )

            assert response.status_code == 422

    async def test_missing_required_params(
        self,
        app: FastAPI,
        db_session: AsyncSession,
    ):
        """Test endpoints with missing required parameters."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Missing start_date
            response = await client.get(
                "/api/analytics/leads",
                params={"end_date": datetime.utcnow().isoformat()},
            )
            assert response.status_code == 422

            # Missing end_date
            response = await client.get(
                "/api/analytics/leads",
                params={"start_date": datetime.utcnow().isoformat()},
            )
            assert response.status_code == 422
