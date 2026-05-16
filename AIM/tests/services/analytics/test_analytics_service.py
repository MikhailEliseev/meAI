"""Tests for AnalyticsService

Part of: Phase 11 Sprint 2 - Task 2.5
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.email_event import EmailEvent
from aim.models.email_workflow import EmailWorkflow
from aim.models.lead import Lead
from aim.models.linear_task import LinearTask
from aim.models.scheduled_email import ScheduledEmail
from aim.services.analytics.analytics_service import AnalyticsService
from aim.utils.encryption import FieldEncryption


@pytest.fixture
def encryption():
    """Encryption utility fixture."""
    return FieldEncryption()


@pytest.fixture
async def sample_leads(db_session: AsyncSession, encryption: FieldEncryption):
    """Create sample leads for testing."""
    now = datetime.utcnow()
    leads = []

    # Hot lead
    lead1 = Lead(
        id="lead_20260516_001",
        name_encrypted=encryption.encrypt("Dr. Ivan Petrov"),
        email_encrypted=encryption.encrypt("ivan@example.com"),
        email_hash=Lead.hash_email("ivan@example.com"),
        phone_encrypted=encryption.encrypt("+79001234567"),
        clinic_name_encrypted=encryption.encrypt("Dental Clinic Moscow"),
        specialty="dentist",
        source="landing_page",
        fz152_consent=True,
        fz152_consent_timestamp=now,
        fz152_consent_ip="127.0.0.1",
        score=85,
        tier="hot",
        created_at=now - timedelta(days=2),
    )
    db_session.add(lead1)
    leads.append(lead1)

    # Warm lead
    lead2 = Lead(
        id="lead_20260516_002",
        name_encrypted=encryption.encrypt("Dr. Maria Ivanova"),
        email_encrypted=encryption.encrypt("maria@example.com"),
        email_hash=Lead.hash_email("maria@example.com"),
        phone_encrypted=encryption.encrypt("+79009876543"),
        clinic_name_encrypted=encryption.encrypt("Medical Center SPb"),
        specialty="therapist",
        source="referral",
        fz152_consent=True,
        fz152_consent_timestamp=now,
        fz152_consent_ip="127.0.0.1",
        score=65,
        tier="warm",
        created_at=now - timedelta(days=1),
    )
    db_session.add(lead2)
    leads.append(lead2)

    # Cold lead
    lead3 = Lead(
        id="lead_20260516_003",
        name_encrypted=encryption.encrypt("Dr. Alexey Smirnov"),
        email_encrypted=encryption.encrypt("alexey@example.com"),
        email_hash=Lead.hash_email("alexey@example.com"),
        phone_encrypted=encryption.encrypt("+79005555555"),
        clinic_name_encrypted=encryption.encrypt("Surgery Center"),
        specialty="surgeon",
        source="organic",
        fz152_consent=True,
        fz152_consent_timestamp=now,
        fz152_consent_ip="127.0.0.1",
        score=45,
        tier="cold",
        created_at=now - timedelta(days=3),
    )
    db_session.add(lead3)
    leads.append(lead3)

    await db_session.commit()
    for lead in leads:
        await db_session.refresh(lead)

    return leads


@pytest.fixture
async def sample_workflows(
    db_session: AsyncSession, sample_leads: list[Lead]
):
    """Create sample email workflows."""
    workflows = []

    for lead in sample_leads:
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

    return workflows


@pytest.fixture
async def sample_emails(
    db_session: AsyncSession, sample_workflows: list[EmailWorkflow]
):
    """Create sample scheduled emails."""
    now = datetime.utcnow()
    emails = []

    for workflow in sample_workflows:
        # Sent email
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

    return emails


@pytest.fixture
async def sample_events(
    db_session: AsyncSession, sample_emails: list[ScheduledEmail]
):
    """Create sample email events."""
    now = datetime.utcnow()
    events = []

    # First email: delivered + opened + clicked
    email1 = sample_emails[0]
    events.extend([
        EmailEvent(
            email_id=email1.id,
            event_type="delivered",
            occurred_at=now - timedelta(minutes=55),
        ),
        EmailEvent(
            email_id=email1.id,
            event_type="opened",
            occurred_at=now - timedelta(minutes=50),
        ),
        EmailEvent(
            email_id=email1.id,
            event_type="clicked",
            occurred_at=now - timedelta(minutes=45),
        ),
    ])

    # Second email: delivered + opened
    email2 = sample_emails[1]
    events.extend([
        EmailEvent(
            email_id=email2.id,
            event_type="delivered",
            occurred_at=now - timedelta(minutes=55),
        ),
        EmailEvent(
            email_id=email2.id,
            event_type="opened",
            occurred_at=now - timedelta(minutes=50),
        ),
    ])

    # Third email: delivered only
    email3 = sample_emails[2]
    events.append(
        EmailEvent(
            email_id=email3.id,
            event_type="delivered",
            occurred_at=now - timedelta(minutes=55),
        )
    )

    for event in events:
        db_session.add(event)

    await db_session.commit()
    for event in events:
        await db_session.refresh(event)

    return events


@pytest.fixture
async def sample_tasks(
    db_session: AsyncSession, sample_leads: list[Lead]
):
    """Create sample Linear tasks."""
    now = datetime.utcnow()
    tasks = []

    # Task for hot lead
    task = LinearTask(
        id="task_001",
        lead_id=sample_leads[0].id,
        linear_issue_id="LEAD-123",
        linear_url="https://linear.app/issue/LEAD-123",
        status="todo",
        created_at=now,
        updated_at=now,
    )
    db_session.add(task)
    tasks.append(task)

    await db_session.commit()
    for task in tasks:
        await db_session.refresh(task)

    return tasks


@pytest.mark.asyncio
class TestAnalyticsService:
    """Test suite for AnalyticsService."""

    async def test_get_lead_metrics_all(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
    ):
        """Test getting lead metrics for all tiers."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.total_leads == 3
        assert metrics.leads_by_tier["hot"] == 1
        assert metrics.leads_by_tier["warm"] == 1
        assert metrics.leads_by_tier["cold"] == 1
        assert metrics.average_score == pytest.approx(65.0, rel=0.1)
        assert metrics.capture_rate > 0

    async def test_get_lead_metrics_filtered_by_tier(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
    ):
        """Test getting lead metrics filtered by tier."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
            tier="hot",
        )

        assert metrics.total_leads == 1
        assert metrics.leads_by_tier["hot"] == 1
        assert metrics.average_score == 85.0

    async def test_get_lead_metrics_by_source(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
    ):
        """Test lead metrics grouped by source."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.leads_by_source["landing_page"] == 1
        assert metrics.leads_by_source["referral"] == 1
        assert metrics.leads_by_source["organic"] == 1

    async def test_get_lead_metrics_by_specialty(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
    ):
        """Test lead metrics grouped by specialty."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.leads_by_specialty["dentist"] == 1
        assert metrics.leads_by_specialty["therapist"] == 1
        assert metrics.leads_by_specialty["surgeon"] == 1

    async def test_get_lead_metrics_empty(
        self,
        db_session: AsyncSession,
    ):
        """Test getting lead metrics with no data."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=365)
        end_date = datetime.utcnow() - timedelta(days=364)

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.total_leads == 0
        assert metrics.average_score == 0.0
        assert metrics.capture_rate == 0.0

    async def test_get_email_metrics_all(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
        sample_events: list[EmailEvent],
    ):
        """Test getting email metrics for all tiers."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.total_sent == 3
        assert metrics.total_delivered == 3
        assert metrics.total_opened == 2
        assert metrics.total_clicked == 1
        assert metrics.delivery_rate == 100.0
        assert metrics.open_rate == pytest.approx(66.67, rel=0.1)
        assert metrics.click_rate == 50.0

    async def test_get_email_metrics_filtered_by_tier(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
        sample_events: list[EmailEvent],
    ):
        """Test getting email metrics filtered by tier."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
            tier="hot",
        )

        assert metrics.total_sent == 1
        assert metrics.total_delivered == 1
        assert metrics.total_opened == 1
        assert metrics.total_clicked == 1

    async def test_get_email_metrics_by_tier(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
        sample_events: list[EmailEvent],
    ):
        """Test email metrics grouped by tier."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.emails_by_tier["hot"] == 1
        assert metrics.emails_by_tier["warm"] == 1
        assert metrics.emails_by_tier["cold"] == 1

    async def test_get_email_metrics_empty(
        self,
        db_session: AsyncSession,
    ):
        """Test getting email metrics with no data."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=365)
        end_date = datetime.utcnow() - timedelta(days=364)

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert metrics.total_sent == 0
        assert metrics.delivery_rate == 0.0
        assert metrics.open_rate == 0.0

    async def test_get_conversion_funnel(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
        sample_events: list[EmailEvent],
        sample_tasks: list[LinearTask],
    ):
        """Test getting conversion funnel metrics."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        funnel = await service.get_conversion_funnel(
            start_date=start_date,
            end_date=end_date,
        )

        assert funnel.leads_captured == 3
        assert funnel.leads_scored == 3
        assert funnel.tasks_created == 1
        assert funnel.workflows_triggered == 3
        assert funnel.emails_sent == 3
        assert funnel.emails_delivered == 3
        assert funnel.emails_opened == 2
        assert funnel.emails_clicked == 1

        # Check conversion rates
        assert funnel.conversion_rates["capture_to_score"] == 100.0
        assert funnel.conversion_rates["score_to_task"] == pytest.approx(33.33, rel=0.1)
        # task_to_workflow: 1 task -> 3 workflows = 300%
        assert funnel.conversion_rates["task_to_workflow"] == 300.0

    async def test_get_conversion_funnel_empty(
        self,
        db_session: AsyncSession,
    ):
        """Test getting conversion funnel with no data."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=365)
        end_date = datetime.utcnow() - timedelta(days=364)

        funnel = await service.get_conversion_funnel(
            start_date=start_date,
            end_date=end_date,
        )

        assert funnel.leads_captured == 0
        assert funnel.conversion_rates["capture_to_score"] == 0.0

    async def test_get_real_time_stats(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
    ):
        """Test getting real-time statistics."""
        service = AnalyticsService(db_session)

        stats = await service.get_real_time_stats()

        assert stats.leads_today >= 0
        assert stats.emails_sent_today >= 0
        assert stats.active_workflows == 3
        assert stats.pending_emails >= 0
        assert stats.hot_leads_count == 1

    async def test_lead_time_series(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
    ):
        """Test lead time series generation."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert len(metrics.time_series) > 0
        for point in metrics.time_series:
            assert point.timestamp is not None
            assert point.value >= 0
            assert point.label != ""

    async def test_email_time_series(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
    ):
        """Test email time series generation."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        assert len(metrics.time_series) > 0
        for point in metrics.time_series:
            assert point.timestamp is not None
            assert point.value >= 0
            assert point.label != ""

    async def test_avg_time_to_open(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
        sample_events: list[EmailEvent],
    ):
        """Test average time to open calculation."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        # Should have avg_time_to_open since we have opened events
        assert metrics.avg_time_to_open is not None
        assert metrics.avg_time_to_open > 0

    async def test_avg_time_to_click(
        self,
        db_session: AsyncSession,
        sample_leads: list[Lead],
        sample_workflows: list[EmailWorkflow],
        sample_emails: list[ScheduledEmail],
        sample_events: list[EmailEvent],
    ):
        """Test average time to click calculation."""
        service = AnalyticsService(db_session)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        # Should have avg_time_to_click since we have clicked events
        assert metrics.avg_time_to_click is not None
        assert metrics.avg_time_to_click > 0
