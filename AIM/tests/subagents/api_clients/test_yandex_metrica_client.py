"""Tests for Yandex Metrica API Client."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aim.subagents.api_clients.yandex_metrica_client import (
    YandexMetricaClient,
    YandexMetricaCredentials,
    YandexMetricaTrafficData,
)


@pytest.fixture
def yandex_credentials():
    """Yandex Metrica credentials fixture."""
    return YandexMetricaCredentials(
        counter_id="12345678",
        access_token="test_oauth_token",
    )


@pytest.fixture
def mock_yandex_response():
    """Mock Yandex Metrica API response."""
    return {
        "data": [
            {
                "dimensions": [{"name": "Яндекс"}],
                "metrics": [3000, 2500, 9000, 50.2, 150.0],
            },
            {
                "dimensions": [{"name": "Google"}],
                "metrics": [5000, 4200, 15000, 45.5, 180.0],
            },
        ],
    }


@pytest.mark.asyncio
async def test_yandex_client_initialization(yandex_credentials):
    """Test Yandex Metrica client initialization."""
    client = YandexMetricaClient(credentials=yandex_credentials)

    assert client.counter_id == "12345678"
    assert client.access_token == "test_oauth_token"
    assert client.credentials == yandex_credentials
    assert client.client is not None

    await client.close()


@pytest.mark.asyncio
async def test_get_traffic_sources(yandex_credentials, mock_yandex_response):
    """Test fetching traffic sources."""
    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_yandex_response

        client = YandexMetricaClient(credentials=yandex_credentials)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        traffic_sources = await client.get_traffic_sources(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=10,
        )

        assert len(traffic_sources) == 2
        assert isinstance(traffic_sources[0], YandexMetricaTrafficData)
        assert traffic_sources[0].source == "Яндекс"
        assert traffic_sources[0].visits == 3000
        assert traffic_sources[0].users == 2500
        assert traffic_sources[0].pageviews == 9000
        assert traffic_sources[0].bounce_rate == 50.2
        assert traffic_sources[0].avg_visit_duration == 150.0

        assert traffic_sources[1].source == "Google"
        assert traffic_sources[1].visits == 5000

        await client.close()


@pytest.mark.asyncio
async def test_get_traffic_sources_caching(yandex_credentials, mock_yandex_response):
    """Test traffic sources caching."""
    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_yandex_response

        client = YandexMetricaClient(credentials=yandex_credentials)

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
        assert mock_request.call_count == 1

        # Results should be identical
        assert len(traffic_sources_1) == len(traffic_sources_2)
        assert traffic_sources_1[0].visits == traffic_sources_2[0].visits

        await client.close()


@pytest.mark.asyncio
async def test_get_user_behavior(yandex_credentials):
    """Test fetching user behavior metrics."""
    mock_response = {
        "totals": [10000, 7000, 3.2, 165.0],
    }

    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        client = YandexMetricaClient(credentials=yandex_credentials)

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

        await client.close()


@pytest.mark.asyncio
async def test_get_bounce_rate_by_page(yandex_credentials):
    """Test fetching bounce rate by page."""
    mock_response = {
        "data": [
            {
                "dimensions": [{"name": "/products"}],
                "metrics": [1000, 25.5],
            },
            {
                "dimensions": [{"name": "/services"}],
                "metrics": [800, 30.0],
            },
        ],
    }

    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        client = YandexMetricaClient(credentials=yandex_credentials)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        pages = await client.get_bounce_rate_by_page(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=20,
        )

        assert len(pages) == 2
        assert pages[0]["page"] == "/products"
        assert pages[0]["sessions"] == 1000
        assert pages[0]["bounce_rate"] == 25.5

        assert pages[1]["page"] == "/services"
        assert pages[1]["sessions"] == 800
        assert pages[1]["bounce_rate"] == 30.0

        await client.close()


@pytest.mark.asyncio
async def test_rate_limiting(yandex_credentials, mock_yandex_response):
    """Test rate limiting."""
    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_yandex_response

        # Create client with strict rate limit
        client = YandexMetricaClient(
            credentials=yandex_credentials,
            rate_limit_capacity=2,
            rate_limit_refill=1.0,
        )

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        # Make 3 requests with different limits to bypass cache
        await client.get_traffic_sources(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=10,
        )

        await client.get_traffic_sources(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=20,
        )

        await client.get_traffic_sources(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=30,
        )

        # Verify all 3 requests hit the API (not cached)
        assert mock_request.call_count == 3

        await client.close()


@pytest.mark.asyncio
async def test_error_handling(yandex_credentials):
    """Test error handling."""
    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        client = YandexMetricaClient(credentials=yandex_credentials)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        with pytest.raises(Exception) as exc_info:
            await client.get_traffic_sources(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=10,
            )

        assert "API Error" in str(exc_info.value)

        await client.close()


@pytest.mark.asyncio
async def test_empty_response(yandex_credentials):
    """Test handling empty API response."""
    mock_response = {"data": []}

    with patch.object(YandexMetricaClient, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        client = YandexMetricaClient(credentials=yandex_credentials)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        traffic_sources = await client.get_traffic_sources(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=10,
        )

        assert len(traffic_sources) == 0

        await client.close()


@pytest.mark.asyncio
async def test_close(yandex_credentials):
    """Test client cleanup."""
    client = YandexMetricaClient(credentials=yandex_credentials)

    # Should not raise
    await client.close()
