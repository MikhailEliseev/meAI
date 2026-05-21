"""Tests for Yandex Direct real stats (TSV parsing)."""
import pytest
from unittest.mock import AsyncMock, patch

from aim.subagents.ads.yandex_direct_client import YandexDirectAPIClient, CampaignStats


SAMPLE_TSV = (
    "CampaignId\tDate\tImpressions\tClicks\tCost\tConversions\tCtr\tAvgCpc\tAvgCpa\r\n"
    "123\t2026-05-20\t5678\t234\t12345670\t12\t4.12\t52760000\t1028810000\r\n"
    "456\t2026-05-20\t3200\t89\t8900000\t3\t2.78\t100000000\t2966666667\r\n"
)

EMPTY_TSV = ""


class MockResponse:
    """Helper to build mock httpx response."""

    def __init__(self, status_code, text_body):
        self.status_code = status_code
        self.text = text_body
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.mark.asyncio
async def test_real_tsv_parsing():
    """TSV response with real data parses into correct CampaignStats."""
    client = YandexDirectAPIClient(token="test_token")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = MockResponse(200, SAMPLE_TSV)

        stats = await client.get_campaign_stats(
            campaign_ids=[123, 456],
            date_from="2026-05-01",
            date_to="2026-05-20",
        )

    assert len(stats) == 2

    # Campaign 123
    assert stats[0].campaign_id == 123
    assert stats[0].impressions == 5678
    assert stats[0].clicks == 234
    assert stats[0].cost == pytest.approx(12.35, rel=0.01)  # 12345670 / 1e6
    assert stats[0].conversions == 12
    assert stats[0].ctr == pytest.approx(4.12, rel=0.01)
    assert stats[0].cpc == pytest.approx(52.76, rel=0.01)
    assert stats[0].cpa == pytest.approx(1028.81, rel=0.01)
    assert stats[0].date == "2026-05-20"

    # Campaign 456
    assert stats[1].campaign_id == 456
    assert stats[1].impressions == 3200
    assert stats[1].clicks == 89


@pytest.mark.asyncio
async def test_empty_tsv_returns_empty_list():
    """Empty TSV response returns empty stats list."""
    client = YandexDirectAPIClient(token="test_token")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = MockResponse(200, EMPTY_TSV)

        stats = await client.get_campaign_stats(
            campaign_ids=[999],
            date_from="2026-01-01",
            date_to="2026-01-31",
        )

    assert stats == []


@pytest.mark.asyncio
async def test_async_report_polling():
    """HTTP 202 then 200 response — polls correctly and parses final TSV."""
    client = YandexDirectAPIClient(token="test_token")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # First response: 202 (still generating)
        resp_202 = MockResponse(202, "")
        resp_202.headers = {"retryIn": "1"}

        # Second response: 200 with data
        resp_200 = MockResponse(200, SAMPLE_TSV)

        mock_client.post.return_value = resp_202
        mock_client.get.return_value = resp_200

        stats = await client.get_campaign_stats(
            campaign_ids=[123],
            date_from="2026-05-01",
            date_to="2026-05-20",
        )

    assert len(stats) == 2  # SAMPLE_TSV has 2 rows
    mock_client.get.assert_called_once()  # Polled once
