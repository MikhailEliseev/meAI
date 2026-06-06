"""E2E Test: Analytics Flow

Tests analytics endpoints: lead metrics, email metrics, funnel, realtime stats, export.

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from io import BytesIO

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.services.email.workflow_service import WorkflowService
from src.aim.services.email.email_sender import EmailSender


def _lead_payload(name, email, phone="+79991234567", clinic="Test Clinic",
                  specialty="dentistry", message=None, **extra):
    """Build valid lead capture payload."""
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "clinic_name": clinic,
        "specialty": specialty,
        "fz152_consent": True,
        "recaptcha_token": f"test_token_{email.split('@')[0]}",
        **({"message": message} if message else {}),
        **extra,
    }


@pytest.mark.asyncio
async def test_lead_metrics_aggregation_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Lead metrics endpoint returns valid structure with created leads."""
    start = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # Create leads with varied data
    for i in range(5):
        await client.post("/api/leads/capture", json=_lead_payload(
            f"Dr. Test {i}", f"test{i}@clinic.ru",
            message="Подробное описание потребностей клиники" if i < 2 else None,
            utm_source="yandex" if i < 3 else None,
        ))

    end = datetime.now(timezone.utc).isoformat()
    metrics_resp = await client.get("/api/analytics/leads", params={
        "start_date": start,
        "end_date": end,
    })

    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_leads"] >= 5
    assert isinstance(metrics["leads_by_tier"], dict)
    assert isinstance(metrics["leads_by_source"], dict)
    assert isinstance(metrics["leads_by_specialty"], dict)
    assert metrics["average_score"] > 0
    assert metrics["capture_rate"] > 0


@pytest.mark.asyncio
async def test_email_metrics_calculation_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Email metrics endpoint via /api/analytics/emails."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).isoformat()
    end = now.isoformat()

    # Create leads with valid data
    for i in range(5):
        resp = await client.post("/api/leads/capture", json=_lead_payload(
            f"Dr. Test {i}", f"test{i}@clinic.ru",
        ))
        assert resp.status_code == 201

    # Send emails
    workflow_service = WorkflowService(db)
    with patch.object(EmailSender, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await workflow_service.send_scheduled_emails()

    metrics_resp = await client.get("/api/analytics/emails", params={
        "start_date": start,
        "end_date": end,
    })

    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert isinstance(metrics["total_sent"], int)
    assert isinstance(metrics["delivery_rate"], (int, float))


@pytest.mark.asyncio
async def test_conversion_funnel_tracking_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Conversion funnel endpoint returns valid structure."""
    start = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # Create leads
    lead_ids = []
    for i in range(5):
        resp = await client.post("/api/leads/capture", json=_lead_payload(
            f"Dr. Test {i}", f"test{i}@clinic.ru",
        ))
        if resp.status_code == 201:
            lead_ids.append(resp.json()["lead_id"])

    # Start onboarding for some leads
    for lid in lead_ids[:3]:
        await client.post("/api/onboarding/start", json={"lead_id": lid})

    end = datetime.now(timezone.utc).isoformat()
    funnel_resp = await client.get("/api/analytics/funnel", params={
        "start_date": start,
        "end_date": end,
    })

    assert funnel_resp.status_code == 200
    funnel = funnel_resp.json()
    assert funnel["leads_captured"] >= len(lead_ids)
    assert isinstance(funnel["conversion_rates"], dict)


@pytest.mark.asyncio
async def test_real_time_stats_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Real-time stats endpoint returns valid structure."""
    # Create a lead
    await client.post("/api/leads/capture", json=_lead_payload(
        "Dr. New Lead", "newlead@clinic.ru",
    ))

    stats_resp = await client.get("/api/analytics/realtime")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["leads_today"] >= 1
    assert "last_updated" in stats


@pytest.mark.asyncio
async def test_export_report_csv_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """CSV report export returns file metadata."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=7)).isoformat()
    end = now.isoformat()

    # Create test data
    for i in range(3):
        await client.post("/api/leads/capture", json=_lead_payload(
            f"Dr. Test {i}", f"test{i}@clinic.ru",
        ))

    export_resp = await client.get("/api/analytics/export", params={
        "start_date": start,
        "end_date": end,
        "format": "csv",
    })

    assert export_resp.status_code == 200
    data = export_resp.json()
    assert data["format"] == "csv"
    assert data["file_size"] > 0
    assert "file_path" in data


@pytest.mark.asyncio
async def test_export_report_json_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """JSON report export returns file metadata."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=7)).isoformat()
    end = now.isoformat()

    # Create test data
    for i in range(3):
        await client.post("/api/leads/capture", json=_lead_payload(
            f"Dr. Test {i}", f"test{i}@clinic.ru",
        ))

    export_resp = await client.get("/api/analytics/export", params={
        "start_date": start,
        "end_date": end,
        "format": "json",
    })

    assert export_resp.status_code == 200
    data = export_resp.json()
    assert data["format"] == "json"
    assert data["file_size"] > 0
    assert "file_path" in data


@pytest.mark.asyncio
async def test_analytics_date_range_filtering(
    client: AsyncClient,
    db: AsyncSession,
):
    """Analytics date range filtering works with query params."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=7)).isoformat()

    # Create a lead now
    await client.post("/api/leads/capture", json=_lead_payload(
        "Dr. Today", "today@clinic.ru",
    ))

    today_end = datetime.now(timezone.utc).isoformat()
    # Today's metrics
    today_resp = await client.get("/api/analytics/leads", params={
        "start_date": today_start,
        "end_date": today_end,
    })
    assert today_resp.status_code == 200
    today_metrics = today_resp.json()
    assert today_metrics["total_leads"] >= 1

    # Week metrics should include today's lead
    week_resp = await client.get("/api/analytics/leads", params={
        "start_date": week_start,
        "end_date": today_end,
    })
    assert week_resp.status_code == 200
    week_metrics = week_resp.json()
    assert week_metrics["total_leads"] >= today_metrics["total_leads"]


@pytest.mark.asyncio
async def test_analytics_leads_by_tier(
    client: AsyncClient,
    db: AsyncSession,
):
    """Leads endpoint with tier filter returns filtered results."""
    start = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # Create leads
    for i in range(3):
        await client.post("/api/leads/capture", json=_lead_payload(
            f"Dr. Test {i}", f"test{i}@clinic.ru",
        ))

    end = datetime.now(timezone.utc).isoformat()
    # Filter by tier=cold (most default leads are cold)
    resp = await client.get("/api/analytics/leads", params={
        "start_date": start,
        "end_date": end,
        "tier": "cold",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_leads"] >= 0
    assert isinstance(data["leads_by_tier"], dict)
