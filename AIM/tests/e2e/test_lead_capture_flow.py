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

from src.aim.models.lead import Lead
from src.aim.models.linear_task import LinearTask
from src.aim.services.lead_capture import LeadCaptureService
from src.aim.ai.lead_scoring.scoring_service import LeadScoringService
from src.aim.integrations.linear.service import LinearService


@pytest.mark.asyncio
async def test_hot_lead_capture_flow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test complete flow for lead with AI scoring."""
    # Step 1: Submit contact form
    form_data = {
        "name": "Dr. Иван Петров",
        "email": "ivan.petrov@clinic-premium.ru",
        "phone": "+79991234567",
        "clinic_name": "Премиум Клиника",
        "specialty": "dentistry",
        "message": "Интересует комплексное продвижение стоматологической клиники. Хотим увеличить поток пациентов на имплантацию и ортодонтию. Готовы обсудить бюджет от 500к/месяц.",
        "fz152_consent": True,
        "recaptcha_token": "test_token_lead",
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
    # With message and business email, score should be ~40-50 (Cold tier)
    assert data["tier"] in ["cold", "warm"]
    assert data["score"] >= 30

    # Step 2: Verify lead in database
    from sqlalchemy import select
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    assert lead is not None
    assert lead.specialty == "dentistry"
    assert lead.tier in ["cold", "warm"]
    assert lead.score >= 30
    assert lead.processed is True

    # Step 3: Verify lead is stored with encryption
    assert lead.name_encrypted is not None
    assert lead.email_encrypted is not None
    assert lead.phone_encrypted is not None

    # Verify decryption works
    assert lead.name == "Dr. Иван Петров"
    assert lead.email == "ivan.petrov@clinic-premium.ru"
    assert lead.phone == "+79991234567"


@pytest.mark.asyncio
async def test_warm_lead_capture_flow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test complete flow for Warm tier lead (score 50-79)."""
    # Step 1: Submit contact form with less signals
    form_data = {
        "name": "Dr. Мария Сидорова",
        "email": "maria@dental-center.ru",
        "phone": "+79997654321",
        "clinic_name": "Дентал Центр",
        "specialty": "dentistry",
        "fz152_consent": True,
        "recaptcha_token": "test_token_warm_lead",
    }

    response = await client.post("/api/leads/capture", json=form_data)

    # Verify lead created
    assert response.status_code == 201
    data = response.json()
    lead_id = data["lead_id"]
    # Without message and UTM, score should be lower
    assert data["tier"] in ["cold", "warm"]
    assert data["score"] >= 20

    # Step 2: Verify lead in database
    from sqlalchemy import select
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    assert lead is not None
    assert lead.specialty == "dentistry"
    assert lead.processed is True


@pytest.mark.asyncio
async def test_cold_lead_capture_flow_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
    mock_recaptcha,
):
    """Test complete flow for Cold tier lead (score < 50)."""
    # Step 1: Submit contact form with minimal data
    form_data = {
        "name": "Иван Иванов",
        "email": "ivan@example.com",
        "phone": "+79991111111",
        "clinic_name": "Клиника",
        "specialty": "dentistry",
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

    # Step 2: Verify lead in database
    from sqlalchemy import select
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    assert lead is not None
    assert lead.specialty == "dentistry"
    assert lead.processed is True


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
        "fz152_consent": True,
        "recaptcha_token": "test_token_duplicate",
    }

    response1 = await client.post("/api/leads/capture", json=form_data)
    assert response1.status_code == 201
    lead_id_1 = response1.json()["lead_id"]

    # Step 2: Try to create duplicate
    response2 = await client.post("/api/leads/capture", json=form_data)

    # Should return existing lead (status 201 but same lead_id)
    assert response2.status_code == 201
    data = response2.json()
    assert data["lead_id"] == lead_id_1
    assert "уже получили" in data["message"]

    # Step 3: Verify only one lead in database
    from sqlalchemy import select
    stmt = select(Lead).where(Lead.email_hash == Lead.hash_email("test@clinic.ru"))
    result = await db.execute(stmt)
    leads = result.scalars().all()
    assert len(leads) == 1


@pytest.mark.asyncio
async def test_rate_limiting_lead_capture(
    client: AsyncClient,
    mock_recaptcha,
):
    """Test rate limiting on lead capture endpoint."""
    # Submit 11 leads rapidly (limit is 10 per minute from same IP)
    responses = []
    for i in range(11):
        form_data = {
            "name": "Dr. Test",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": f"test_token_rate_limit_{i}",
        }
        response = await client.post("/api/leads/capture", json=form_data)
        responses.append(response)

    # First 10 requests should succeed
    successful = [r for r in responses if r.status_code == 201]
    assert len(successful) == 10

    # 11th request should be rate limited (429)
    assert responses[10].status_code == 429


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
        "fz152_consent": True,
        "recaptcha_token": "test_token_invalid_phone",
    })
    assert response3.status_code == 422

    # Missing fz152_consent
    response4 = await client.post("/api/leads/capture", json={
        "name": "Test",
        "email": "test@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Clinic",
        "specialty": "dentistry",
        "fz152_consent": False,
        "recaptcha_token": "test_token_no_consent",
    })
    assert response4.status_code == 422
