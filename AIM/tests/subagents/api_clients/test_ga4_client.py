"""Tests for GA4 API Client."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aim.subagents.api_clients.ga4_client import (
    GA4Client,
    GA4Credentials,
    GA4TrafficData,
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
def mock_credentials():
    """Mock Google credentials."""
    with patch("AIM.src.aim.subagents.api_clients.ga4_client.service_account.Credentials.from_service_account_info") as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_ga4_client():
    """Mock GA4 BetaAnalyticsDataClient."""
    with patch("AIM.src.aim.subagents.api_clients.ga4_client.BetaAnalyticsDataClient") as mock:
        yield mock


@pytest.fixture
def mock_ga4_response():
    """Mock GA4 API response."""
    mock_row = MagicMock()
    mock_row.dimension_values = [
        MagicMock(value="google"),
        MagicMock(value="organic"),
    ]
    mock_row.metric_values = [
        MagicMock(value="5000"),  # sessions
        MagicMock(value="4200"),  # users
        MagicMock(value="3500"),  # new_users
        MagicMock(value="15000"),  # pageviews
        MagicMock(value="45.5"),  # bounce_rate
        MagicMock(value="180.0"),  # avg_session_duration
    ]

    mock_response = MagicMock()
    mock_response.rows = [mock_row]

    return mock_response


@pytest.mark.asyncio
async def test_ga4_client_initialization(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test GA4 client initialization."""
    client = GA4Client(credentials=ga4_credentials)

    assert client.property_id == "123456789"
    assert client.credentials == ga4_credentials
    assert client.client is not None
    mock_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_get_traffic_sources(ga4_credentials, mock_credentials, mock_ga4_client, mock_ga4_response):
    """Test fetching traffic sources."""
    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_ga4_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    traffic_sources = await client.get_traffic_sources(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=10,
    )

    assert len(traffic_sources) == 1
    assert isinstance(traffic_sources[0], GA4TrafficData)
    assert traffic_sources[0].source == "google"
    assert traffic_sources[0].medium == "organic"
    assert traffic_sources[0].sessions == 5000
    assert traffic_sources[0].users == 4200
    assert traffic_sources[0].new_users == 3500
    assert traffic_sources[0].pageviews == 15000
    assert traffic_sources[0].bounce_rate == 45.5
    assert traffic_sources[0].avg_session_duration == 180.0


@pytest.mark.asyncio
async def test_get_traffic_sources_caching(ga4_credentials, mock_credentials, mock_ga4_client, mock_ga4_response):
    """Test traffic sources caching."""
    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_ga4_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    # First call - should hit API
    traffic_sources_1 = await client.get_traffic_sources(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=10,
    )

    # Second call - should hit cache
    traffic_sources_2 = await client.get_traffic_sources(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=10,
    )

    # API should be called only once
    assert mock_client.run_report.call_count == 1

    # Results should be identical
    assert len(traffic_sources_1) == len(traffic_sources_2)
    assert traffic_sources_1[0].sessions == traffic_sources_2[0].sessions


@pytest.mark.asyncio
async def test_get_user_behavior(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test fetching user behavior metrics."""
    mock_row = MagicMock()
    mock_row.metric_values = [
        MagicMock(value="10000"),  # total_users
        MagicMock(value="7000"),   # new_users
        MagicMock(value="3.2"),    # pages_per_session
        MagicMock(value="165.0"),  # avg_session_duration
    ]

    mock_response = MagicMock()
    mock_response.rows = [mock_row]

    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    behavior = await client.get_user_behavior(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    assert behavior["total_users"] == 10000
    assert behavior["new_users"] == 7000
    assert behavior["returning_users"] == 3000
    assert behavior["new_user_rate"] == 70.0
    assert behavior["pages_per_session"] == 3.2
    assert behavior["avg_session_duration"] == 165.0


@pytest.mark.asyncio
async def test_get_conversions(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test fetching conversion events."""
    mock_row = MagicMock()
    mock_row.dimension_values = [
        MagicMock(value="purchase"),
    ]
    mock_row.metric_values = [
        MagicMock(value="500"),    # event_count
        MagicMock(value="450"),    # total_users
        MagicMock(value="25000.0"), # event_value
    ]

    mock_response = MagicMock()
    mock_response.rows = [mock_row]

    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    conversions = await client.get_conversions(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        event_names=["purchase"],
    )

    assert len(conversions) == 1
    assert isinstance(conversions[0], GA4ConversionData)
    assert conversions[0].event_name == "purchase"
    assert conversions[0].event_count == 500
    assert conversions[0].total_users == 450
    assert conversions[0].event_value == 25000.0
    assert conversions[0].conversion_rate == 111.11  # 500/450 * 100


@pytest.mark.asyncio
async def test_get_bounce_rate_by_page(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test fetching bounce rate by page."""
    mock_row = MagicMock()
    mock_row.dimension_values = [
        MagicMock(value="/products"),
    ]
    mock_row.metric_values = [
        MagicMock(value="1000"),  # sessions
        MagicMock(value="25.5"),  # bounce_rate
    ]

    mock_response = MagicMock()
    mock_response.rows = [mock_row]

    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    pages = await client.get_bounce_rate_by_page(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=20,
    )

    assert len(pages) == 1
    assert pages[0]["page"] == "/products"
    assert pages[0]["sessions"] == 1000
    assert pages[0]["bounce_rate"] == 25.5


@pytest.mark.asyncio
async def test_rate_limiting(ga4_credentials, mock_credentials, mock_ga4_client, mock_ga4_response):
    """Test rate limiting."""
    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_ga4_response)
    mock_ga4_client.return_value = mock_client

    # Create client with strict rate limit
    client = GA4Client(
        credentials=ga4_credentials,
        rate_limit_capacity=2,
        rate_limit_refill=1.0,
    )

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    # Make 3 requests (should be rate limited)
    start_time = asyncio.get_event_loop().time()

    await client.get_traffic_sources(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=10,
    )

    await client.get_traffic_sources(
        start_date=(start_date - timedelta(days=1)).isoformat(),
        end_date=(end_date - timedelta(days=1)).isoformat(),
        limit=10,
    )

    await client.get_traffic_sources(
        start_date=(start_date - timedelta(days=2)).isoformat(),
        end_date=(end_date - timedelta(days=2)).isoformat(),
        limit=10,
    )

    elapsed = asyncio.get_event_loop().time() - start_time

    # Third request should be delayed by rate limiter
    assert elapsed >= 1.0  # At least 1 second delay


@pytest.mark.asyncio
async def test_error_handling(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test error handling."""
    mock_client = MagicMock()
    mock_client.run_report = MagicMock(side_effect=Exception("API Error"))
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    with pytest.raises(Exception) as exc_info:
        await client.get_traffic_sources(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=10,
        )

    assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_attribution_data(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test fetching attribution data."""
    mock_row = MagicMock()
    mock_row.dimension_values = [
        MagicMock(value="google"),
        MagicMock(value="cpc"),
        MagicMock(value="brand_campaign"),
    ]
    mock_row.metric_values = [
        MagicMock(value="150"),    # conversions
        MagicMock(value="7500.0"), # revenue
    ]

    mock_response = MagicMock()
    mock_response.rows = [mock_row]

    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    attributions = await client.get_attribution_data(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    assert len(attributions) == 1
    assert attributions[0]["source"] == "google"
    assert attributions[0]["medium"] == "cpc"
    assert attributions[0]["campaign"] == "brand_campaign"
    assert attributions[0]["conversions"] == 150
    assert attributions[0]["revenue"] == 7500.0


@pytest.mark.asyncio
async def test_get_revenue_data(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test fetching revenue data."""
    mock_row = MagicMock()
    mock_row.metric_values = [
        MagicMock(value="50000.0"),  # total_revenue
        MagicMock(value="1000"),     # transactions
        MagicMock(value="50.0"),     # avg_order_value
        MagicMock(value="10000"),    # sessions
        MagicMock(value="8000"),     # users
    ]

    mock_response = MagicMock()
    mock_response.rows = [mock_row]

    mock_client = MagicMock()
    mock_client.run_report = MagicMock(return_value=mock_response)
    mock_ga4_client.return_value = mock_client

    client = GA4Client(credentials=ga4_credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    revenue = await client.get_revenue_data(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    assert revenue["total_revenue"] == 50000.0
    assert revenue["transactions"] == 1000
    assert revenue["avg_order_value"] == 50.0
    assert revenue["revenue_per_session"] == 5.0  # 50000 / 10000
    assert revenue["revenue_per_user"] == 6.25    # 50000 / 8000


@pytest.mark.asyncio
async def test_close(ga4_credentials, mock_credentials, mock_ga4_client):
    """Test client cleanup."""
    client = GA4Client(credentials=ga4_credentials)

    # Should not raise
    await client.close()
