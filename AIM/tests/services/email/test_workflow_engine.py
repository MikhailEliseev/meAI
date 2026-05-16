"""Tests for WorkflowEngine

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from aim.models import EmailWorkflow, Lead, ScheduledEmail
from aim.services.email.workflow_engine import WorkflowEngine


@pytest.fixture
async def lead(db_session):
    """Create test lead."""
    from datetime import datetime, timezone
    from aim.utils.encryption import FieldEncryption

    email = "ivan@example.com"
    encryptor = FieldEncryption()

    lead = Lead(
        id="lead_20260516_test123",
        name_encrypted=encryptor.encrypt("Иван Петров"),
        phone_encrypted=encryptor.encrypt("+79991234567"),
        email_encrypted=encryptor.encrypt(email),
        email_hash=Lead.hash_email(email),
        clinic_name_encrypted=encryptor.encrypt("Стоматология Улыбка"),
        specialty="стоматология",
        fz152_consent=True,
        fz152_consent_timestamp=datetime.now(timezone.utc),
        fz152_consent_ip="127.0.0.1",
        source="test",
        tier="warm",
        score=75,
    )
    db_session.add(lead)
    await db_session.commit()
    return lead


@pytest.fixture
def workflow_engine(db_session):
    """Create WorkflowEngine instance."""
    return WorkflowEngine(db_session)


@pytest.mark.asyncio
async def test_trigger_workflow_hot(workflow_engine, lead, db_session):
    """Test triggering hot lead workflow."""
    # Update lead tier
    lead.tier = "hot"
    await db_session.commit()

    # Trigger workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="hot", start_immediately=True
    )

    assert workflow.lead_id == lead.id
    assert workflow.tier == "hot"
    assert workflow.status == "active"
    assert workflow.current_step == 0
    assert workflow.started_at is not None

    # Check scheduled emails
    result = await db_session.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.workflow_id == workflow.id
        )
    )
    emails = result.scalars().all()

    # Hot workflow has 1 email (instant)
    assert len(emails) == 1
    assert emails[0].template_id == "hot_instant"
    assert emails[0].status == "pending"
    assert emails[0].recipient_email == lead.email


@pytest.mark.asyncio
async def test_trigger_workflow_warm(workflow_engine, lead, db_session):
    """Test triggering warm lead workflow."""
    # Trigger workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="warm", start_immediately=True
    )

    assert workflow.tier == "warm"
    assert workflow.status == "active"

    # Check scheduled emails
    result = await db_session.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.workflow_id == workflow.id
        )
    )
    emails = result.scalars().all()

    # Warm workflow has 3 emails (day 0, 3, 7)
    assert len(emails) == 3

    # Check template IDs
    template_ids = [e.template_id for e in emails]
    assert "warm_day0" in template_ids
    assert "warm_day3" in template_ids
    assert "warm_day7" in template_ids

    # Check scheduling
    emails_sorted = sorted(emails, key=lambda e: e.scheduled_at)
    assert emails_sorted[0].template_id == "warm_day0"  # Instant
    assert emails_sorted[1].template_id == "warm_day3"  # +3 days
    assert emails_sorted[2].template_id == "warm_day7"  # +7 days


@pytest.mark.asyncio
async def test_trigger_workflow_cold(workflow_engine, lead, db_session):
    """Test triggering cold lead workflow."""
    # Update lead tier
    lead.tier = "cold"
    await db_session.commit()

    # Trigger workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="cold", start_immediately=True
    )

    assert workflow.tier == "cold"

    # Check scheduled emails
    result = await db_session.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.workflow_id == workflow.id
        )
    )
    emails = result.scalars().all()

    # Cold workflow has 1 email (weekly digest)
    assert len(emails) == 1
    assert emails[0].template_id == "cold_weekly"


@pytest.mark.asyncio
async def test_trigger_workflow_invalid_tier(workflow_engine, lead):
    """Test triggering workflow with invalid tier."""
    with pytest.raises(ValueError, match="Invalid tier"):
        await workflow_engine.trigger_workflow(
            lead_id=lead.id, tier="invalid"
        )


@pytest.mark.asyncio
async def test_trigger_workflow_lead_not_found(workflow_engine):
    """Test triggering workflow for non-existent lead."""
    fake_id = uuid4()
    with pytest.raises(ValueError, match="Lead not found"):
        await workflow_engine.trigger_workflow(lead_id=fake_id, tier="hot")


@pytest.mark.asyncio
async def test_trigger_workflow_duplicate(workflow_engine, lead):
    """Test triggering workflow when one already exists."""
    # Create first workflow
    await workflow_engine.trigger_workflow(lead_id=lead.id, tier="warm")

    # Try to create second workflow
    with pytest.raises(ValueError, match="Active workflow already exists"):
        await workflow_engine.trigger_workflow(lead_id=lead.id, tier="warm")


@pytest.mark.asyncio
async def test_schedule_email(workflow_engine, lead, db_session):
    """Test scheduling a single email."""
    # Create workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="hot", start_immediately=False
    )

    # Schedule email
    send_at = datetime.utcnow() + timedelta(hours=1)
    context = {
        "name": lead.name,
        "email": lead.email,
        "specialty": lead.specialty,
    }

    email = await workflow_engine.schedule_email(
        workflow_id=workflow.id,
        template_id="hot_instant",
        recipient_email=lead.email,
        context=context,
        send_at=send_at,
    )

    assert email.workflow_id == workflow.id
    assert email.template_id == "hot_instant"
    assert email.recipient_email == lead.email
    assert email.status == "pending"
    assert email.scheduled_at == send_at


@pytest.mark.asyncio
async def test_process_scheduled_emails(workflow_engine, lead, db_session):
    """Test processing scheduled emails."""
    # Create workflow with emails
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="hot", start_immediately=True
    )

    # Get scheduled email
    result = await db_session.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.workflow_id == workflow.id
        )
    )
    email = result.scalar_one()

    # Set scheduled_at to past
    email.scheduled_at = datetime.utcnow() - timedelta(minutes=5)
    await db_session.commit()

    # Process scheduled emails
    ready_emails = await workflow_engine.process_scheduled_emails()

    assert len(ready_emails) == 1
    assert ready_emails[0].id == email.id


@pytest.mark.asyncio
async def test_pause_workflow(workflow_engine, lead, db_session):
    """Test pausing workflow."""
    # Create workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="warm"
    )

    # Pause workflow
    await workflow_engine.pause_workflow(workflow.id)

    # Verify status
    await db_session.refresh(workflow)
    assert workflow.status == "paused"


@pytest.mark.asyncio
async def test_resume_workflow(workflow_engine, lead, db_session):
    """Test resuming paused workflow."""
    # Create and pause workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="warm"
    )
    await workflow_engine.pause_workflow(workflow.id)

    # Resume workflow
    await workflow_engine.resume_workflow(workflow.id)

    # Verify status
    await db_session.refresh(workflow)
    assert workflow.status == "active"


@pytest.mark.asyncio
async def test_complete_workflow(workflow_engine, lead, db_session):
    """Test completing workflow."""
    # Create workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="hot"
    )

    # Complete workflow
    await workflow_engine.complete_workflow(workflow.id)

    # Verify status
    await db_session.refresh(workflow)
    assert workflow.status == "completed"
    assert workflow.completed_at is not None


@pytest.mark.asyncio
async def test_cancel_workflow(workflow_engine, lead, db_session):
    """Test cancelling workflow."""
    # Create workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="warm", start_immediately=True
    )

    # Cancel workflow
    await workflow_engine.cancel_workflow(workflow.id)

    # Verify workflow status
    await db_session.refresh(workflow)
    assert workflow.status == "cancelled"
    assert workflow.completed_at is not None

    # Verify pending emails cancelled
    result = await db_session.execute(
        select(ScheduledEmail).where(
            ScheduledEmail.workflow_id == workflow.id
        )
    )
    emails = result.scalars().all()
    assert all(e.status == "cancelled" for e in emails)


@pytest.mark.asyncio
async def test_get_workflow_status(workflow_engine, lead, db_session):
    """Test getting workflow status."""
    # Create workflow
    workflow = await workflow_engine.trigger_workflow(
        lead_id=lead.id, tier="warm", start_immediately=True
    )

    # Get status
    status = await workflow_engine.get_workflow_status(workflow.id)

    assert status is not None
    assert status["workflow_id"] == str(workflow.id)
    assert status["lead_id"] == str(lead.id)
    assert status["tier"] == "warm"
    assert status["status"] == "active"
    assert status["emails"]["total"] == 3
    assert status["emails"]["pending"] == 3
