"""E2E Test: Lead Capture Flow

Tests complete lead capture journey from form submission to Linear task creation.

Flow:
1. User fills contact form
2. Lead created in database
3. AI scoring executed
4. Linear task created based on tier
5. Email workflow triggered

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.lead import Lead
from aim.models.linear_task import LinearTask
from aim.services.lead_capture import LeadCaptureService
from aim.ai.lead_scoring.scoring_service import LeadScoringService
from aim.integrations.linear.service import LinearService


@pytest.mark.asyncio
async def test_hot_lead_capture_flow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test complete flow for Hot tier lead (score >= 80)."""
    # Step 1: Submit contact form
    form_data = {
        "name": "Dr. Иван Петров",
        "email": "ivan.petrov@clinic-premium.ru",
        "phone": "+79991234567",
        "clinic_name": "Премиум Клиника",
        "specialty": "dentistry",
        "city": "Москва",
        "services": ["implants", "orthodontics", "surgery"],
        "monthly_budget": 500000,
        "current_marketing": ["yandex_direct", "instagram", "seo"],
        "pain_points": ["low_conversion", "high_cpc", "no_analytics"],
        "fz152_consent": True,
        "recaptcha_token": "test_token_hot_lead",
        "utm_source": "yandex",
        "utm_medium": "cpc",
        "utm_campaign": "dental_implants_moscow",
    }

    response = await client.post("/api/leads/capture", json=form_data)

    # Verify lead created
    if response.status_code != 201:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    lead_id = data["lead_id"]
    assert data["tier"] == "hot"
    assert data["score"] >= 80

    # Step 2: Verify lead in database
    lead_service = LeadCaptureService(db)
    lead = await lead_service.get_lead(lead_id)

    assert lead is not None
    assert lead.name == "Dr. Иван Петров"
    assert lead.email == "ivan.petrov@clinic-premium.ru"
    assert lead.tier == "hot"
    assert lead.score >= 80

    # Step 3: Verify AI scoring factors
    assert lead.scoring_factors is not None
    factors = lead.scoring_factors

    # High-value signals
    assert factors["budget_score"] > 0  # 500k budget
    assert factors["services_score"] > 0  # Multiple services
    assert factors["pain_points_score"] > 0  # Clear pain points
    assert factors["marketing_maturity_score"] > 0  # Active marketing

    # Step 4: Verify Linear task created
    from aim.integrations.linear.client import LinearClient
    linear_client = LinearClient(api_key="test_key")

    # Mock Linear API call
    with patch.object(linear_client, 'create_issue', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            "id": "linear_123",
            "identifier": "AIM-123",
            "url": "https://linear.app/aim/issue/AIM-123",
        }

        linear_service = LinearService(db, linear_client)
        task = await linear_service.get_task_by_lead(lead_id)

        assert task is not None
        assert task.priority == "urgent"  # Hot leads = urgent
        assert task.title == f"🔥 Hot Lead: Dr. Иван Петров (Премиум Клиника)"
        assert "500000" in task.description  # Budget mentioned
        assert "implants" in task.description  # Services mentioned

    # Step 5: Verify email workflow triggered
    # Hot tier = 1 instant email
    from aim.services.email.workflow_service import WorkflowService
    workflow_service = WorkflowService(db)

    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert len(workflows) == 1

    workflow = workflows[0]
    assert workflow.tier == "hot"
    assert workflow.total_emails == 1
    assert workflow.emails_sent == 0  # Not sent yet (async)
    assert workflow.status == "active"


@pytest.mark.asyncio
async def test_warm_lead_capture_flow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test complete flow for Warm tier lead (score 50-79)."""
    # Step 1: Submit contact form
    form_data = {
        "name": "Dr. Мария Сидорова",
        "email": "maria@dental-center.ru",
        "phone": "+79997654321",
        "clinic_name": "Дентал Центр",
        "specialty": "dentistry",
        "city": "Санкт-Петербург",
        "services": ["therapy", "hygiene"],
        "monthly_budget": 150000,
        "current_marketing": ["instagram"],
        "pain_points": ["low_traffic"],
        "fz152_consent": True,
        "recaptcha_token": "test_token_warm_lead",
    }

    response = await client.post("/api/leads/capture", json=form_data)

    # Verify lead created
    assert response.status_code == 201
    data = response.json()
    lead_id = data["lead_id"]
    assert data["tier"] == "warm"
    assert 50 <= data["score"] < 80

    # Step 2: Verify Linear task priority
    from aim.integrations.linear.service import LinearService
    linear_service = LinearService(db, MagicMock())

    task = await linear_service.get_task_by_lead(lead_id)
    assert task.priority == "high"  # Warm leads = high priority

    # Step 3: Verify email workflow (3 emails: day 0, 3, 7)
    from aim.services.email.workflow_service import WorkflowService
    workflow_service = WorkflowService(db)

    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert len(workflows) == 1

    workflow = workflows[0]
    assert workflow.tier == "warm"
    assert workflow.total_emails == 3
    assert workflow.status == "active"


@pytest.mark.asyncio
async def test_cold_lead_capture_flow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test complete flow for Cold tier lead (score < 50)."""
    # Step 1: Submit contact form
    form_data = {
        "name": "Иван Иванов",
        "email": "ivan@example.com",
        "phone": "+79991111111",
        "clinic_name": "Клиника",
        "specialty": "dentistry",
        "city": "Воронеж",
        "services": ["consultation"],
        "monthly_budget": 30000,
        "fz152_consent": True,
        "recaptcha_token": "test_token_cold_lead",
    }

    response = await client.post("/api/leads/capture", json=form_data)

    # Verify lead created
    assert response.status_code == 201
    data = response.json()
    lead_id = data["lead_id"]
    assert data["tier"] == "cold"
    assert data["score"] < 50

    # Step 2: Verify Linear task priority
    from aim.integrations.linear.service import LinearService
    linear_service = LinearService(db, MagicMock())

    task = await linear_service.get_task_by_lead(lead_id)
    assert task.priority == "medium"  # Cold leads = medium priority

    # Step 3: Verify email workflow (weekly digest)
    from aim.services.email.workflow_service import WorkflowService
    workflow_service = WorkflowService(db)

    workflows = await workflow_service.get_workflows_by_lead(lead_id)
    assert len(workflows) == 1

    workflow = workflows[0]
    assert workflow.tier == "cold"
    assert workflow.schedule_type == "weekly_digest"
    assert workflow.status == "active"


@pytest.mark.asyncio
async def test_duplicate_lead_detection(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test duplicate lead detection by email."""
    # Step 1: Create first lead
    form_data = {
        "name": "Dr. Test",
        "email": "test@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Test Clinic",
        "specialty": "dentistry",
        "city": "Москва",
        "services": ["implants"],
        "monthly_budget": 200000,
        "fz152_consent": True,
        "recaptcha_token": "test_token_duplicate",
    }

    response1 = await client.post("/api/leads/capture", json=form_data)
    assert response1.status_code == 201
    lead_id_1 = response1.json()["lead_id"]

    # Step 2: Try to create duplicate
    response2 = await client.post("/api/leads/capture", json=form_data)

    # Should return existing lead
    assert response2.status_code == 200
    data = response2.json()
    assert data["lead_id"] == lead_id_1
    assert data["message"] == "Lead already exists"

    # Step 3: Verify only one lead in database
    lead_service = LeadCaptureService(db)
    leads = await lead_service.get_leads_by_email("test@clinic.ru")
    assert len(leads) == 1


@pytest.mark.asyncio
async def test_rate_limiting_lead_capture(
    client: AsyncClient,
    mock_recaptcha,
):
    """Test rate limiting on lead capture endpoint."""
    form_data = {
        "name": "Dr. Test",
        "email": f"test{i}@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Test Clinic",
        "specialty": "dentistry",
        "city": "Москва",
        "services": ["implants"],
        "monthly_budget": 200000,
        "fz152_consent": True,
        "recaptcha_token": f"test_token_rate_limit_{i}",
    }

    # Submit 10 leads rapidly
    responses = []
    for i in range(10):
        form_data["email"] = f"test{i}@clinic.ru"
        response = await client.post("/api/leads/capture", json=form_data)
        responses.append(response)

    # First requests should succeed
    assert responses[0].status_code == 201
    assert responses[1].status_code == 201

    # Later requests should be rate limited (429)
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0


@pytest.mark.asyncio
async def test_invalid_lead_data_validation(
    client: AsyncClient,
    mock_recaptcha,
):
    """Test validation of invalid lead data."""
    # Missing required fields
    response1 = await client.post("/api/leads/capture", json={})
    assert response1.status_code == 422

    # Invalid email
    response2 = await client.post("/api/leads/capture", json={
        "name": "Test",
        "email": "invalid-email",
        "phone": "+79991234567",
        "clinic_name": "Clinic",
        "specialty": "dentistry",
        "city": "Москва",
        "fz152_consent": True,
        "recaptcha_token": "test_token_invalid_email",
    })
    assert response2.status_code == 422

    # Invalid phone
    response3 = await client.post("/api/leads/capture", json={
        "name": "Test",
        "email": "test@clinic.ru",
        "phone": "invalid",
        "clinic_name": "Clinic",
        "specialty": "dentistry",
        "city": "Москва",
        "fz152_consent": True,
        "recaptcha_token": "test_token_invalid_phone",
    })
    assert response3.status_code == 422

    # Negative budget
    response4 = await client.post("/api/leads/capture", json={
        "name": "Test",
        "email": "test@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Clinic",
        "specialty": "dentistry",
        "city": "Москва",
        "monthly_budget": -1000,
        "fz152_consent": True,
        "recaptcha_token": "test_token_negative_budget",
    })
    assert response4.status_code == 422
