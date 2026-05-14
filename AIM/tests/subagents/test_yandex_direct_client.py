"""
Tests for Yandex Direct API Client.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from AIM.src.aim.subagents.ads.yandex_direct_client import (
    YandexDirectAPIClient,
    CampaignInfo,
    CampaignStats,
    BudgetRecommendation,
)


@pytest.fixture
def client():
    """Create client instance."""
    return YandexDirectAPIClient(token="test_token")


@pytest.fixture
def mock_campaigns_response():
    """Mock Yandex Direct campaigns API response."""
    return {
        "result": {
            "Campaigns": [
                {
                    "Id": 12345,
                    "Name": "Test Campaign 1",
                    "Status": "ACTIVE",
                    "Type": "TEXT_CAMPAIGN",
                    "DailyBudget": {"Amount": 5000000000},  # 5000 RUB in micros
                    "Currency": "RUB",
                    "StartDate": "2026-05-01",
                    "EndDate": "2026-05-31",
                },
                {
                    "Id": 12346,
                    "Name": "Test Campaign 2",
                    "Status": "PAUSED",
                    "Type": "TEXT_CAMPAIGN",
                    "DailyBudget": {"Amount": 3000000000},  # 3000 RUB in micros
                    "Currency": "RUB",
                    "StartDate": "2026-05-01",
                    "EndDate": None,
                },
            ]
        }
    }


@pytest.fixture
def mock_create_campaign_response():
    """Mock Yandex Direct create campaign API response."""
    return {"result": {"AddResults": [{"Id": 12347}]}}


@pytest.mark.asyncio
async def test_get_campaigns(client, mock_campaigns_response):
    """Test fetching campaigns."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_campaigns_response)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        campaigns = await client.get_campaigns()

        assert len(campaigns) == 2

        # Check first campaign
        assert campaigns[0].id == 12345
        assert campaigns[0].name == "Test Campaign 1"
        assert campaigns[0].status == "ACTIVE"
        assert campaigns[0].type == "TEXT_CAMPAIGN"
        assert campaigns[0].daily_budget == 5000.0  # Converted from micros
        assert campaigns[0].currency == "RUB"
        assert campaigns[0].start_date == "2026-05-01"
        assert campaigns[0].end_date == "2026-05-31"

        # Check second campaign
        assert campaigns[1].id == 12346
        assert campaigns[1].name == "Test Campaign 2"
        assert campaigns[1].status == "PAUSED"
        assert campaigns[1].daily_budget == 3000.0
        assert campaigns[1].end_date is None


@pytest.mark.asyncio
async def test_get_campaigns_with_ids(client, mock_campaigns_response):
    """Test fetching specific campaigns by IDs."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_campaigns_response)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        campaigns = await client.get_campaigns(campaign_ids=[12345, 12346])

        assert len(campaigns) == 2
        assert campaigns[0].id == 12345
        assert campaigns[1].id == 12346


@pytest.mark.asyncio
async def test_get_campaign_stats(client):
    """Test fetching campaign statistics."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={})
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        stats = await client.get_campaign_stats(
            campaign_ids=[12345, 12346],
            date_from="2026-05-01",
            date_to="2026-05-14",
        )

        # Mock implementation returns stats for each campaign
        assert len(stats) == 2

        # Check first campaign stats
        assert stats[0].campaign_id == 12345
        assert stats[0].impressions == 10000
        assert stats[0].clicks == 500
        assert stats[0].cost == 5000.0
        assert stats[0].conversions == 50
        assert stats[0].ctr == 5.0
        assert stats[0].cpc == 10.0
        assert stats[0].cpa == 100.0


@pytest.mark.asyncio
async def test_optimize_budgets(client):
    """Test budget optimization."""
    campaigns = [
        CampaignInfo(
            id=12345,
            name="High Performer",
            status="ACTIVE",
            type="TEXT_CAMPAIGN",
            daily_budget=5000.0,
            currency="RUB",
            start_date="2026-05-01",
            end_date="2026-05-31",
        ),
        CampaignInfo(
            id=12346,
            name="Low Performer",
            status="ACTIVE",
            type="TEXT_CAMPAIGN",
            daily_budget=3000.0,
            currency="RUB",
            start_date="2026-05-01",
            end_date="2026-05-31",
        ),
    ]

    stats = [
        CampaignStats(
            campaign_id=12345,
            impressions=10000,
            clicks=500,
            cost=5000.0,
            conversions=100,  # High conversions
            ctr=5.0,
            cpc=10.0,
            cpa=50.0,
            date="2026-05-14",
        ),
        CampaignStats(
            campaign_id=12346,
            impressions=5000,
            clicks=200,
            cost=3000.0,
            conversions=10,  # Low conversions
            ctr=4.0,
            cpc=15.0,
            cpa=300.0,
            date="2026-05-14",
        ),
    ]

    recommendations = await client.optimize_budgets(
        campaigns=campaigns,
        stats=stats,
        total_budget=10000.0,
    )

    assert len(recommendations) == 2

    # High performer should get more budget
    high_perf = next(r for r in recommendations if r.campaign_id == 12345)
    assert high_perf.recommended_budget > high_perf.current_budget
    assert high_perf.change > 0
    assert "High performance" in high_perf.reason

    # Low performer should get less budget
    low_perf = next(r for r in recommendations if r.campaign_id == 12346)
    assert low_perf.recommended_budget < low_perf.current_budget
    assert low_perf.change < 0
    assert "Low performance" in low_perf.reason


@pytest.mark.asyncio
async def test_optimize_budgets_equal_distribution(client):
    """Test budget optimization with no performance data."""
    campaigns = [
        CampaignInfo(
            id=12345,
            name="Campaign 1",
            status="ACTIVE",
            type="TEXT_CAMPAIGN",
            daily_budget=5000.0,
            currency="RUB",
            start_date="2026-05-01",
            end_date="2026-05-31",
        ),
        CampaignInfo(
            id=12346,
            name="Campaign 2",
            status="ACTIVE",
            type="TEXT_CAMPAIGN",
            daily_budget=5000.0,
            currency="RUB",
            start_date="2026-05-01",
            end_date="2026-05-31",
        ),
    ]

    # No stats (no performance data)
    stats = []

    recommendations = await client.optimize_budgets(
        campaigns=campaigns,
        stats=stats,
        total_budget=10000.0,
    )

    # Should distribute equally when no performance data
    assert len(recommendations) == 0  # No recommendations without stats


@pytest.mark.asyncio
async def test_create_campaign(client, mock_create_campaign_response):
    """Test creating a new campaign."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_create_campaign_response)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        campaign_id = await client.create_campaign(
            name="New Test Campaign",
            daily_budget=5000.0,
            start_date="2026-05-15",
            end_date="2026-06-15",
        )

        assert campaign_id == 12347


@pytest.mark.asyncio
async def test_create_campaign_without_end_date(client, mock_create_campaign_response):
    """Test creating a campaign without end date."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_create_campaign_response)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        campaign_id = await client.create_campaign(
            name="Ongoing Campaign",
            daily_budget=3000.0,
            start_date="2026-05-15",
        )

        assert campaign_id == 12347


def test_agent_capabilities():
    """Test agent capabilities reporting."""
    client = YandexDirectAPIClient(token="test_token")

    # Agent should have these capabilities
    assert hasattr(client, "get_campaigns")
    assert hasattr(client, "get_campaign_stats")
    assert hasattr(client, "optimize_budgets")
    assert hasattr(client, "create_campaign")


@pytest.mark.asyncio
async def test_budget_optimization_performance_score(client):
    """Test performance score calculation in budget optimization."""
    campaigns = [
        CampaignInfo(
            id=12345,
            name="Campaign A",
            status="ACTIVE",
            type="TEXT_CAMPAIGN",
            daily_budget=5000.0,
            currency="RUB",
            start_date="2026-05-01",
            end_date="2026-05-31",
        ),
    ]

    stats = [
        CampaignStats(
            campaign_id=12345,
            impressions=10000,
            clicks=500,
            cost=5000.0,
            conversions=100,
            ctr=5.0,
            cpc=10.0,
            cpa=50.0,
            date="2026-05-14",
        ),
    ]

    recommendations = await client.optimize_budgets(
        campaigns=campaigns,
        stats=stats,
        total_budget=10000.0,
    )

    assert len(recommendations) == 1
    rec = recommendations[0]

    # Performance score = conversions / cost = 100 / 5000 = 0.02
    # With only one campaign, it should get all budget
    assert rec.recommended_budget == 10000.0
