"""E2E Test: Analytics Flow

Tests complete analytics journey from data collection to reporting.

Flow:
1. Lead metrics aggregation
2. Email metrics calculation
3. Conversion funnel tracking
4. Real-time stats
5. Export reports (CSV, JSON, PDF)

Part of: Phase 11 Sprint 4 - Task 4.1
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_lead_metrics_aggregation_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test lead metrics aggregation across tiers."""
    # Step 1: Create leads across all tiers
    leads_data = [
        # Hot leads (3)
        {"name": "Dr. Hot 1", "email": "hot1@clinic.ru", "monthly_budget": 500000, "services": ["implants", "orthodontics"]},
        {"name": "Dr. Hot 2", "email": "hot2@clinic.ru", "monthly_budget": 600000, "services": ["implants", "surgery"]},
        {"name": "Dr. Hot 3", "email": "hot3@clinic.ru", "monthly_budget": 550000, "services": ["orthodontics", "surgery"]},
        # Warm leads (5)
        {"name": "Dr. Warm 1", "email": "warm1@clinic.ru", "monthly_budget": 150000, "services": ["therapy"]},
        {"name": "Dr. Warm 2", "email": "warm2@clinic.ru", "monthly_budget": 180000, "services": ["hygiene"]},
        {"name": "Dr. Warm 3", "email": "warm3@clinic.ru", "monthly_budget": 160000, "services": ["therapy"]},
        {"name": "Dr. Warm 4", "email": "warm4@clinic.ru", "monthly_budget": 170000, "services": ["hygiene"]},
        {"name": "Dr. Warm 5", "email": "warm5@clinic.ru", "monthly_budget": 155000, "services": ["therapy"]},
        # Cold leads (7)
        {"name": "Dr. Cold 1", "email": "cold1@clinic.ru", "monthly_budget": 30000, "services": ["consultation"]},
        {"name": "Dr. Cold 2", "email": "cold2@clinic.ru", "monthly_budget": 40000, "services": ["consultation"]},
        {"name": "Dr. Cold 3", "email": "cold3@clinic.ru", "monthly_budget": 35000, "services": ["consultation"]},
        {"name": "Dr. Cold 4", "email": "cold4@clinic.ru", "monthly_budget": 45000, "services": ["consultation"]},
        {"name": "Dr. Cold 5", "email": "cold5@clinic.ru", "monthly_budget": 32000, "services": ["consultation"]},
        {"name": "Dr. Cold 6", "email": "cold6@clinic.ru", "monthly_budget": 38000, "services": ["consultation"]},
        {"name": "Dr. Cold 7", "email": "cold7@clinic.ru", "monthly_budget": 42000, "services": ["consultation"]},
    ]

    for lead_data in leads_data:
        await client.post("/api/leads/capture", json={
            **lead_data,
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
        })

    # Step 2: Get lead metrics
    metrics_response = await client.get("/api/analytics/leads/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()

    # Verify counts
    assert metrics["total_leads"] == 15
    assert metrics["hot_leads"] == 3
    assert metrics["warm_leads"] == 5
    assert metrics["cold_leads"] == 7

    # Verify percentages
    assert metrics["hot_percentage"] == pytest.approx(20.0, rel=0.1)  # 3/15
    assert metrics["warm_percentage"] == pytest.approx(33.3, rel=0.1)  # 5/15
    assert metrics["cold_percentage"] == pytest.approx(46.7, rel=0.1)  # 7/15

    # Verify average scores
    assert metrics["avg_score_hot"] >= 80
    assert 50 <= metrics["avg_score_warm"] < 80
    assert metrics["avg_score_cold"] < 50


@pytest.mark.asyncio
async def test_email_metrics_calculation_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test email metrics calculation."""
    # Step 1: Create leads and send emails
    for i in range(10):
        lead_response = await client.post("/api/leads/capture", json={
            "name": f"Dr. Test {i}",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            "services": ["therapy"],
            "monthly_budget": 100000,
        })

    # Step 2: Simulate email sending
    from aim.services.email.workflow_service import WorkflowService
    workflow_service = WorkflowService(db)

    from aim.services.email.sendgrid_client import SendGridClient
    with patch.object(SendGridClient, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": "msg", "status": "sent"}
        await workflow_service.send_scheduled_emails()

    # Step 3: Simulate email events
    # 8 delivered, 6 opened, 3 clicked
    for i in range(8):
        await client.post("/api/email/webhook/sendgrid", json={
            "event": "delivered",
            "email": f"test{i}@clinic.ru",
            "timestamp": int(datetime.utcnow().timestamp()),
            "sg_message_id": f"msg_{i}",
        })

    for i in range(6):
        await client.post("/api/email/webhook/sendgrid", json={
            "event": "open",
            "email": f"test{i}@clinic.ru",
            "timestamp": int(datetime.utcnow().timestamp()),
            "sg_message_id": f"msg_{i}",
        })

    for i in range(3):
        await client.post("/api/email/webhook/sendgrid", json={
            "event": "click",
            "email": f"test{i}@clinic.ru",
            "timestamp": int(datetime.utcnow().timestamp()),
            "sg_message_id": f"msg_{i}",
            "url": "https://iamaim.ru",
        })

    # Step 4: Get email metrics
    metrics_response = await client.get("/api/analytics/email/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()

    # Verify counts
    assert metrics["total_sent"] >= 10
    assert metrics["total_delivered"] >= 8
    assert metrics["total_opened"] >= 6
    assert metrics["total_clicked"] >= 3

    # Verify rates
    assert metrics["delivery_rate"] >= 80.0  # 8/10
    assert metrics["open_rate"] >= 60.0  # 6/10
    assert metrics["click_rate"] >= 30.0  # 3/10
    assert metrics["click_to_open_rate"] >= 50.0  # 3/6


@pytest.mark.asyncio
async def test_conversion_funnel_tracking_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test conversion funnel tracking."""
    # Step 1: Create 20 leads
    lead_ids = []
    for i in range(20):
        lead_response = await client.post("/api/leads/capture", json={
            "name": f"Dr. Test {i}",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            "services": ["therapy"],
            "monthly_budget": 100000,
        })
        lead_ids.append(lead_response.json()["lead_id"])

    # Step 2: Start onboarding for 10 leads
    onboarding_ids = []
    for i in range(10):
        onboarding_response = await client.post("/api/onboarding/start", json={
            "lead_id": lead_ids[i],
        })
        onboarding_ids.append(onboarding_response.json()["onboarding_id"])

    # Step 3: Complete onboarding for 5 leads
    for i in range(5):
        # Upload documents
        for doc_type in ["license", "inn", "ogrn", "contract"]:
            file = BytesIO(b"%PDF-1.4 fake content")
            await client.post(
                f"/api/onboarding/{onboarding_ids[i]}/documents",
                params={"document_type": doc_type},
                files={"file": (f"{doc_type}.pdf", file, "application/pdf")},
            )

        # Process payment
        await client.post(
            f"/api/onboarding/{onboarding_ids[i]}/payment",
            json={
                "amount": 50000.0,
                "currency": "RUB",
                "payment_method": "CARD",
                "customer_name": f"Dr. Test {i}",
                "customer_email": f"test{i}@clinic.ru",
            },
        )

        # Complete onboarding
        await client.post(f"/api/onboarding/{onboarding_ids[i]}/complete")

    # Step 4: Get funnel metrics
    funnel_response = await client.get("/api/analytics/funnel")
    assert funnel_response.status_code == 200
    funnel = funnel_response.json()

    # Verify funnel stages
    assert funnel["leads_captured"] == 20
    assert funnel["onboarding_started"] == 10
    assert funnel["onboarding_completed"] == 5

    # Verify conversion rates
    assert funnel["lead_to_onboarding_rate"] == 50.0  # 10/20
    assert funnel["onboarding_completion_rate"] == 50.0  # 5/10
    assert funnel["overall_conversion_rate"] == 25.0  # 5/20


@pytest.mark.asyncio
async def test_real_time_stats_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test real-time stats updates."""
    # Step 1: Get initial stats
    stats_response_1 = await client.get("/api/analytics/stats/realtime")
    assert stats_response_1.status_code == 200
    stats_1 = stats_response_1.json()
    initial_leads = stats_1["leads_today"]

    # Step 2: Create new lead
    await client.post("/api/leads/capture", json={
        "name": "Dr. New Lead",
        "email": "newlead@clinic.ru",
        "phone": "+79991234567",
        "clinic_name": "Test Clinic",
        "city": "Москва",
        "services": ["therapy"],
        "monthly_budget": 100000,
    })

    # Step 3: Get updated stats
    stats_response_2 = await client.get("/api/analytics/stats/realtime")
    assert stats_response_2.status_code == 200
    stats_2 = stats_response_2.json()

    # Verify stats updated
    assert stats_2["leads_today"] == initial_leads + 1
    assert stats_2["last_updated"] > stats_1["last_updated"]


@pytest.mark.asyncio
async def test_export_report_csv_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test CSV report export."""
    # Step 1: Create test data
    for i in range(5):
        await client.post("/api/leads/capture", json={
            "name": f"Dr. Test {i}",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            "services": ["therapy"],
            "monthly_budget": 100000,
        })

    # Step 2: Export CSV report
    export_response = await client.get("/api/analytics/export/leads", params={
        "format": "csv",
        "date_from": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "date_to": datetime.utcnow().isoformat(),
    })

    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "text/csv"
    assert "attachment" in export_response.headers["content-disposition"]

    # Step 3: Verify CSV content
    csv_content = export_response.text
    lines = csv_content.split("\n")
    assert len(lines) >= 6  # Header + 5 leads

    # Verify header
    header = lines[0]
    assert "name" in header.lower()
    assert "email" in header.lower()
    assert "tier" in header.lower()
    assert "score" in header.lower()


@pytest.mark.asyncio
async def test_export_report_json_end_to_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test JSON report export."""
    # Step 1: Create test data
    for i in range(3):
        await client.post("/api/leads/capture", json={
            "name": f"Dr. Test {i}",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            "services": ["therapy"],
            "monthly_budget": 100000,
        })

    # Step 2: Export JSON report
    export_response = await client.get("/api/analytics/export/leads", params={
        "format": "json",
        "date_from": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "date_to": datetime.utcnow().isoformat(),
    })

    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "application/json"

    # Step 3: Verify JSON structure
    data = export_response.json()
    assert "leads" in data
    assert "metadata" in data
    assert len(data["leads"]) >= 3

    # Verify lead structure
    lead = data["leads"][0]
    assert "name" in lead
    assert "email" in lead
    assert "tier" in lead
    assert "score" in lead
    assert "created_at" in lead


@pytest.mark.asyncio
async def test_analytics_date_range_filtering(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test analytics date range filtering."""
    # Step 1: Create leads with different dates
    # Today's leads
    for i in range(3):
        await client.post("/api/leads/capture", json={
            "name": f"Dr. Today {i}",
            "email": f"today{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            "services": ["therapy"],
            "monthly_budget": 100000,
        })

    # Step 2: Get today's metrics
    today_response = await client.get("/api/analytics/leads/metrics", params={
        "date_from": datetime.utcnow().date().isoformat(),
        "date_to": datetime.utcnow().date().isoformat(),
    })
    assert today_response.status_code == 200
    today_metrics = today_response.json()
    assert today_metrics["total_leads"] >= 3

    # Step 3: Get last 7 days metrics
    week_response = await client.get("/api/analytics/leads/metrics", params={
        "date_from": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
        "date_to": datetime.utcnow().date().isoformat(),
    })
    assert week_response.status_code == 200
    week_metrics = week_response.json()
    assert week_metrics["total_leads"] >= today_metrics["total_leads"]


@pytest.mark.asyncio
async def test_analytics_tier_breakdown(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test analytics tier breakdown."""
    # Step 1: Create leads across tiers
    # 2 Hot, 3 Warm, 5 Cold
    hot_leads = [
        {"monthly_budget": 500000, "services": ["implants", "orthodontics"]},
        {"monthly_budget": 600000, "services": ["implants", "surgery"]},
    ]
    warm_leads = [
        {"monthly_budget": 150000, "services": ["therapy"]},
        {"monthly_budget": 180000, "services": ["hygiene"]},
        {"monthly_budget": 160000, "services": ["therapy"]},
    ]
    cold_leads = [
        {"monthly_budget": 30000, "services": ["consultation"]},
        {"monthly_budget": 40000, "services": ["consultation"]},
        {"monthly_budget": 35000, "services": ["consultation"]},
        {"monthly_budget": 45000, "services": ["consultation"]},
        {"monthly_budget": 32000, "services": ["consultation"]},
    ]

    for i, lead_data in enumerate(hot_leads + warm_leads + cold_leads):
        await client.post("/api/leads/capture", json={
            "name": f"Dr. Test {i}",
            "email": f"test{i}@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "city": "Москва",
            **lead_data,
        })

    # Step 2: Get tier breakdown
    breakdown_response = await client.get("/api/analytics/leads/tier-breakdown")
    assert breakdown_response.status_code == 200
    breakdown = breakdown_response.json()

    # Verify breakdown
    assert breakdown["hot"]["count"] == 2
    assert breakdown["warm"]["count"] == 3
    assert breakdown["cold"]["count"] == 5

    # Verify average budgets
    assert breakdown["hot"]["avg_budget"] > breakdown["warm"]["avg_budget"]
    assert breakdown["warm"]["avg_budget"] > breakdown["cold"]["avg_budget"]
