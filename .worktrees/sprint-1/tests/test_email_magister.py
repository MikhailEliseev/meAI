"""Tests for Email Magister"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone

from meai.agents.magisters.email_magister import EmailMagister
from meai.agents.base_agent import Task
from meai.events.event_bus import EventBus


@pytest_asyncio.fixture
async def email_magister():
    """Create Email Magister for testing"""
    event_bus = EventBus("sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    magister = EmailMagister(
        agent_id="email-magister-test",
        event_bus=event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await magister.initialize()

    yield magister

    await event_bus.close()


@pytest.mark.asyncio
async def test_execute_task_routing_campaign_creation(email_magister):
    """Test task routing to campaign creation handler"""
    task = Task(
        task_id="test-email-001",
        agent_id="operator",
        action="create_campaign",
        description="Create email campaign",
        data={
            "action": "create_campaign",
            "campaign_name": "Summer Sale",
            "target_audience": "active_users",
            "subject_line": "Don't miss our summer sale!",
        },
        priority=1,
        created_at=datetime.now(timezone.utc),
    )

    result = await email_magister.execute_task(task)

    assert result.status == "success"
    assert result.task_id == "test-email-001"
    assert "campaign_id" in result.data
    assert result.data["campaign_name"] == "Summer Sale"
    assert result.data["target_audience"] == "active_users"
    assert len(result.data["insights"]) > 0


@pytest.mark.asyncio
async def test_handle_campaign_creation_success(email_magister):
    """Test successful campaign creation"""
    task = Task(
        task_id="test-email-002",
        agent_id="operator",
        action="create_campaign",
        description="Create campaign",
        data={
            "action": "create_campaign",
            "campaign_name": "Newsletter Q2",
            "target_audience": "subscribers",
            "subject_line": "Q2 Updates",
        },
        priority=1,
        created_at=datetime.now(timezone.utc),
    )

    result = await email_magister._handle_campaign_creation(task)

    assert result.status == "success"
    assert result.data["campaign_name"] == "Newsletter Q2"
    assert result.data["estimated_reach"] == 1000
    assert "insights" in result.data
    assert "summary" in result.data


@pytest.mark.asyncio
async def test_store_email_result(email_magister):
    """Test storing email result in database"""
    result_data = {
        "status": "success",
        "campaign_id": "camp-12345678",
        "campaign_name": "Test Campaign",
    }

    # Should not raise exception
    await email_magister._store_email_result("test-task-001", result_data)


@pytest.mark.asyncio
async def test_validate_email_result_success(email_magister):
    """Test validation of successful email result"""
    result = {
        "status": "success",
        "campaign_id": "camp-12345678",
        "campaign_name": "Test",
    }

    validation = await email_magister._validate_email_result(result)

    assert validation["valid"] is True
    assert len(validation["issues"]) == 0


@pytest.mark.asyncio
async def test_validate_email_result_missing_status(email_magister):
    """Test validation fails when status is missing"""
    result = {
        "campaign_id": "camp-12345678",
    }

    validation = await email_magister._validate_email_result(result)

    assert validation["valid"] is False
    assert "Missing 'status' field" in validation["issues"]


@pytest.mark.asyncio
async def test_get_capabilities(email_magister):
    """Test Email Magister capabilities"""
    capabilities = email_magister.get_capabilities()

    assert "create_campaign" in capabilities
    assert "design_template" in capabilities
    assert "segment_audience" in capabilities
    assert "track_metrics" in capabilities
    assert "optimize_delivery" in capabilities


@pytest.mark.asyncio
async def test_handle_template_design(email_magister):
    """Test email template design"""
    task = Task(
        task_id="test-email-003",
        agent_id="operator",
        action="design_template",
        description="Design template",
        data={
            "action": "design_template",
            "template_type": "newsletter",
            "brand_colors": ["#FF0000", "#00FF00"],
        },
        priority=1,
        created_at=datetime.now(timezone.utc),
    )

    result = await email_magister._handle_template_design(task)

    assert result.status == "success"
    assert "template_id" in result.data
    assert result.data["template_type"] == "newsletter"
    assert result.data["responsive"] is True


@pytest.mark.asyncio
async def test_handle_audience_segmentation(email_magister):
    """Test audience segmentation"""
    task = Task(
        task_id="test-email-004",
        agent_id="operator",
        action="segment_audience",
        description="Segment audience",
        data={
            "action": "segment_audience",
            "criteria": {"engagement": "high"},
            "list_size": 5000,
        },
        priority=1,
        created_at=datetime.now(timezone.utc),
    )

    result = await email_magister._handle_audience_segmentation(task)

    assert result.status == "success"
    assert "segments" in result.data
    assert len(result.data["segments"]) == 3
    assert result.data["total_contacts"] == 5000


@pytest.mark.asyncio
async def test_handle_generic_email(email_magister):
    """Test generic email task handling"""
    task = Task(
        task_id="test-email-005",
        agent_id="operator",
        action="custom_action",
        description="Custom email task",
        data={"action": "custom_action"},
        priority=1,
        created_at=datetime.now(timezone.utc),
    )

    result = await email_magister._handle_generic_email(task)

    assert result.status == "success"
    assert result.data["action"] == "custom_action"
    assert "insights" in result.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
