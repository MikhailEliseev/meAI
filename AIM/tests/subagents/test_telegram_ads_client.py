"""Tests for Telegram Ads API client."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.aim.subagents.ads.telegram_ads_client import (
    TelegramAdsClient, TelegramCampaignInfo, TelegramAPIError
)


def make_mock_tg_response(ok=True, result=None, description=None):
    """Build mock Telegram API response (sync methods like httpx.Response)."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    data = {"ok": ok, "result": result}
    if description:
        data["description"] = description
    mock_response.json = Mock(return_value=data)
    return mock_response


@pytest.mark.asyncio
async def test_create_campaign():
    """create_campaign returns campaign ID."""
    client = TelegramAdsClient(bot_token="test_token")

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_tg_response(ok=True, result={"campaign_id": 42})
        )
        campaign_id = await client.create_campaign(
            channel_username="@testchannel",
            title="Test Ad",
            daily_budget=500.0,
            message_text="Buy our product!",
        )

    assert campaign_id == 42


@pytest.mark.asyncio
async def test_get_campaigns():
    """get_campaigns returns TelegramCampaignInfo list."""
    client = TelegramAdsClient(bot_token="test_token")

    mock_data = [
        {"id": 1, "title": "Promo 1", "channel_username": "@chan1",
         "status": "active", "daily_budget": 1000.0, "total_spent": 500.0,
         "impressions": 10000, "clicks": 500, "ctr": 5.0,
         "start_date": "2026-05-01", "end_date": None},
    ]

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_tg_response(ok=True, result=mock_data)
        )
        campaigns = await client.get_campaigns()

    assert len(campaigns) == 1
    assert campaigns[0].id == 1
    assert campaigns[0].title == "Promo 1"
    assert campaigns[0].daily_budget == 1000.0
    assert campaigns[0].ctr == 5.0


@pytest.mark.asyncio
async def test_get_campaign_stats():
    """get_campaign_stats returns CampaignStats list."""
    client = TelegramAdsClient(bot_token="test_token")

    mock_stats = {
        "impressions": 8000, "clicks": 400, "spent": 2000.0,
        "conversions": 20, "ctr": 5.0, "cpc": 5.0, "cpa": 100.0,
    }

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_tg_response(ok=True, result=mock_stats)
        )
        stats = await client.get_campaign_stats(
            campaign_ids=[1],
            date_from="2026-05-01",
            date_to="2026-05-20",
        )

    assert len(stats) == 1
    assert stats[0].impressions == 8000
    assert stats[0].cost == 2000.0


@pytest.mark.asyncio
async def test_telegram_api_error():
    """Telegram error response raises TelegramAPIError."""
    client = TelegramAdsClient(bot_token="bad_token")

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=make_mock_tg_response(ok=False, description="Unauthorized")
        )
        with pytest.raises(TelegramAPIError, match="Unauthorized"):
            await client.get_campaigns()
