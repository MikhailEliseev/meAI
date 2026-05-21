"""Tests for VK Ads API client."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from aim.subagents.ads.vk_ads_client import VKAdsClient, VKCampaignInfo, VKAPIError


def make_mock_vk_response(data, error=None):
    """Build mock VK API response (sync methods like httpx.Response)."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    if error:
        mock_response.json = Mock(return_value={"error": {"error_msg": error}})
    else:
        mock_response.json = Mock(return_value={"response": data})
    return mock_response


@pytest.mark.asyncio
async def test_get_campaigns():
    """get_campaigns returns correctly parsed VKCampaignInfo list."""
    client = VKAdsClient(access_token="test_token")

    mock_vk_data = [
        {"id": 100, "name": "Test Campaign", "status": "active",
         "day_limit": 50000, "start_time": 1716249600, "platform": "vk"},
        {"id": 200, "name": "Stopped", "status": "paused",
         "day_limit": 0, "start_time": 1716336000, "platform": "vk_ads"},
    ]

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_vk_response(mock_vk_data)
        )
        campaigns = await client.get_campaigns(account_id=12345)

    assert len(campaigns) == 2
    assert campaigns[0].id == 100
    assert campaigns[0].name == "Test Campaign"
    assert campaigns[0].status == "active"
    assert campaigns[0].daily_budget == 500.0  # 50000 kopecks / 100
    assert campaigns[0].platform == "vk"
    assert campaigns[1].daily_budget == 0.0


@pytest.mark.asyncio
async def test_get_campaigns_empty():
    """Empty response returns empty list."""
    client = VKAdsClient(access_token="test_token")

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_vk_response([])
        )
        campaigns = await client.get_campaigns(account_id=99999)

    assert campaigns == []


@pytest.mark.asyncio
async def test_vk_api_error():
    """VK error response raises VKAPIError."""
    client = VKAdsClient(access_token="bad_token")

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_vk_response(None, error="Access denied")
        )
        with pytest.raises(VKAPIError, match="Access denied"):
            await client.get_campaigns(account_id=12345)


@pytest.mark.asyncio
async def test_get_campaign_stats():
    """get_campaign_stats returns CampaignStats list."""
    client = VKAdsClient(access_token="test_token")

    mock_stats = [
        {"id": 100, "stats": [
            {"impressions": 5000, "clicks": 150, "spent": "1500.50",
             "reach": 3, "ctr": 3.0, "cpc": 10.0, "cpa": 500.17, "day": "2026-05-20"}
        ]}
    ]

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_vk_response(mock_stats)
        )
        stats = await client.get_campaign_stats(
            account_id=12345,
            campaign_ids=[100],
            date_from="2026-05-01",
            date_to="2026-05-20",
        )

    assert len(stats) == 1
    assert stats[0].campaign_id == 100
    assert stats[0].impressions == 5000
    assert stats[0].clicks == 150
    assert stats[0].cost == 1500.50
    assert stats[0].date == "2026-05-20"
