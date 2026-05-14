"""Tests for Conversion Tracker."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from AIM.src.aim.subagents.analytics.conversion_tracker import (
    ConversionTracker,
    Goal,
    Attribution,
    RevenueMetrics,
)
from AIM.src.aim.subagents.api_clients.ga4_client import (
    GA4Credentials,
    GA4ConversionData,
)


@pytest.fixture
def ga4_credentials():
    """GA4 credentials fixture."""
    return GA4Credentials(
        property_id="123456789",
        credentials_json={
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        },
    )


@pytest.fixture
def mock_ga4_client():
    """Mock GA4 client."""
    with patch("AIM.src.aim.subagents.analytics.conversion_tracker.GA4Client") as mock:
        yield mock


@pytest.mark.asyncio
async def test_tracker_initialization_without_ga4():
    """Test tracker initialization without GA4."""
    tracker = ConversionTracker()

    assert tracker.ga4_client is None
    assert tracker.yandex_counter_id is None


@pytest.mark.asyncio
async def test_tracker_initialization_with_ga4(ga4_credentials, mock_ga4_client):
    """Test tracker initialization with GA4."""
    tracker = ConversionTracker(ga4_credentials=ga4_credentials)

    assert tracker.ga4_client is not None
    mock_ga4_client.assert_called_once()


@pytest.mark.asyncio
async def test_track_goals_from_ga4(ga4_credentials, mock_ga4_client):
    """Test tracking goals from GA4 API."""
    # Mock GA4 conversions
    mock_conversions = [
        GA4ConversionData(
            event_name="purchase",
            event_count=500,
            total_users=450,
            event_value=25000.0,
            conversion_rate=111.11,
        ),
        GA4ConversionData(
            event_name="sign_up",
            event_count=1000,
            total_users=900,
            event_value=5000.0,
            conversion_rate=111.11,
        ),
    ]

    mock_client = MagicMock()
    mock_client.get_conversions = AsyncMock(return_value=mock_conversions)
    mock_client.get_attribution_data = AsyncMock(return_value=[])
    mock_client.get_revenue_data = AsyncMock(return_value={
        "total_revenue": 30000.0,
        "transactions": 500,
        "avg_order_value": 60.0,
        "revenue_per_session": 3.0,
        "revenue_per_user": 3.75,
    })
    mock_client.close = AsyncMock()
    mock_ga4_client.return_value = mock_client

    tracker = ConversionTracker(ga4_credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    report = await tracker.track(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        source="ga4",
    )

    # Verify goals from GA4
    assert len(report.goals) == 2
    assert report.goals[0].goal_name == "purchase"
    assert report.goals[0].completions == 500
    assert report.goals[0].value == 25000.0

    assert report.goals[1].goal_name == "sign_up"
    assert report.goals[1].completions == 1000

    await tracker.close()


@pytest.mark.asyncio
async def test_track_attribution_from_ga4(ga4_credentials, mock_ga4_client):
    """Test tracking attribution from GA4 API."""
    # Mock GA4 attribution
    mock_attribution = [
        {
            "source": "google",
            "medium": "cpc",
            "campaign": "brand",
            "conversions": 300,
            "revenue": 15000.0,
        },
        {
            "source": "facebook",
            "medium": "social",
            "campaign": "retargeting",
            "conversions": 200,
            "revenue": 10000.0,
        },
    ]

    mock_client = MagicMock()
    mock_client.get_conversions = AsyncMock(return_value=[])
    mock_client.get_attribution_data = AsyncMock(return_value=mock_attribution)
    mock_client.get_revenue_data = AsyncMock(return_value={
        "total_revenue": 25000.0,
        "transactions": 500,
        "avg_order_value": 50.0,
        "revenue_per_session": 2.5,
        "revenue_per_user": 3.125,
    })
    mock_client.close = AsyncMock()
    mock_ga4_client.return_value = mock_client

    tracker = ConversionTracker(ga4_credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    report = await tracker.track(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        source="ga4",
    )

    # Verify attribution from GA4
    assert len(report.attributions) == 2
    assert report.attributions[0].source == "google"
    assert report.attributions[0].medium == "cpc"
    assert report.attributions[0].conversions == 300
    assert report.attributions[0].revenue == 15000.0

    assert report.attributions[1].source == "facebook"
    assert report.attributions[1].conversions == 200

    await tracker.close()


@pytest.mark.asyncio
async def test_track_revenue_from_ga4(ga4_credentials, mock_ga4_client):
    """Test tracking revenue from GA4 API."""
    # Mock GA4 revenue
    mock_revenue = {
        "total_revenue": 100000.0,
        "transactions": 2000,
        "avg_order_value": 50.0,
        "revenue_per_session": 10.0,
        "revenue_per_user": 12.5,
    }

    mock_client = MagicMock()
    mock_client.get_conversions = AsyncMock(return_value=[])
    mock_client.get_attribution_data = AsyncMock(return_value=[])
    mock_client.get_revenue_data = AsyncMock(return_value=mock_revenue)
    mock_client.close = AsyncMock()
    mock_ga4_client.return_value = mock_client

    tracker = ConversionTracker(ga4_credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    report = await tracker.track(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        source="ga4",
    )

    # Verify revenue from GA4
    assert report.revenue_metrics.total_revenue == 100000.0
    assert report.revenue_metrics.transactions == 2000
    assert report.revenue_metrics.avg_order_value == 50.0
    assert report.revenue_metrics.revenue_per_session == 10.0
    assert report.revenue_metrics.revenue_per_user == 12.5

    await tracker.close()


@pytest.mark.asyncio
async def test_fallback_to_mock_data():
    """Test fallback to mock data when GA4 unavailable."""
    tracker = ConversionTracker()  # No GA4 credentials

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    report = await tracker.track(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        source="ga4",
    )

    # Should use mock data
    assert len(report.goals) == 4  # Mock has 4 goals
    assert len(report.attributions) == 4  # Mock has 4 attributions
    assert report.revenue_metrics.total_revenue == 50000.0  # Mock revenue


@pytest.mark.asyncio
async def test_ga4_error_fallback(ga4_credentials, mock_ga4_client):
    """Test fallback to mock when GA4 API fails."""
    mock_client = MagicMock()
    mock_client.get_conversions = AsyncMock(side_effect=Exception("API Error"))
    mock_client.get_attribution_data = AsyncMock(side_effect=Exception("API Error"))
    mock_client.get_revenue_data = AsyncMock(side_effect=Exception("API Error"))
    mock_client.close = AsyncMock()
    mock_ga4_client.return_value = mock_client

    tracker = ConversionTracker(ga4_credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    report = await tracker.track(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        source="ga4",
    )

    # Should fallback to mock data
    assert len(report.goals) == 4
    assert len(report.attributions) == 4
    assert report.revenue_metrics.total_revenue == 50000.0

    await tracker.close()


@pytest.mark.asyncio
async def test_close():
    """Test tracker cleanup."""
    tracker = ConversionTracker()

    # Should not raise
    await tracker.close()
