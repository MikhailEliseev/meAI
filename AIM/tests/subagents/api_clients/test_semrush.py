"""Tests for SEMrush API client"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aim.subagents.api_clients.semrush import SEMrushClient
from AIM.tests.fixtures.keyword_data import (
    SEMRUSH_MOCK_RESPONSE,
    ZERO_VOLUME_RESPONSE,
    SUGGESTIONS_RESPONSE,
)


@pytest.fixture
def semrush_client():
    """Create SEMrush client for testing"""
    client = SEMrushClient(
        api_key="test_semrush_key",
        rate_limit_capacity=10,
        rate_limit_refill=2.0,
    )
    yield client
    import asyncio
    asyncio.run(client.close())


@pytest.mark.asyncio
async def test_keyword_expansion_success(semrush_client):
    """Test successful keyword expansion"""
    with patch.object(semrush_client, "_make_request") as mock_request:
        mock_request.return_value = SEMRUSH_MOCK_RESPONSE

        keywords = await semrush_client.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=5,
            min_volume=10,
            max_cost_usd=1.0,
        )

        assert len(keywords) == 5
        assert all("keyword" in kw for kw in keywords)
        assert all("volume" in kw for kw in keywords)
        assert all("difficulty" in kw for kw in keywords)
        assert all("cpc" in kw for kw in keywords)
        assert all("intent" in kw for kw in keywords)
        assert all("priority_score" in kw for kw in keywords)


@pytest.mark.asyncio
async def test_budget_guard_stops_at_max_cost(semrush_client):
    """Test budget guard stops at max_cost_usd"""
    with patch.object(semrush_client, "_make_request") as mock_request:
        mock_request.return_value = SEMRUSH_MOCK_RESPONSE

        # Request 500 keywords but only allow $0.05 budget (5 requests max)
        keywords = await semrush_client.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=500,
            min_volume=10,
            max_cost_usd=0.05,
        )

        # Should stop after 5 requests (5 * $0.01 = $0.05)
        assert mock_request.call_count <= 5
        assert len(keywords) <= 500


@pytest.mark.asyncio
async def test_zero_volume_handling_with_retry(semrush_client):
    """Test zero-volume handling retries with min_volume=0"""
    with patch.object(semrush_client, "_make_request") as mock_request:
        # First call returns zero results, second call returns data
        mock_request.side_effect = [
            ZERO_VOLUME_RESPONSE,
            SEMRUSH_MOCK_RESPONSE,
        ]

        keywords = await semrush_client.expand_keywords(
            seed_keyword="rare medical term",
            max_keywords=5,
            min_volume=100,  # High threshold
            max_cost_usd=1.0,
        )

        # Should have retried with min_volume=0
        assert mock_request.call_count == 2
        assert len(keywords) > 0


@pytest.mark.asyncio
async def test_zero_volume_handling_with_suggestions(semrush_client):
    """Test zero-volume handling provides suggestions"""
    with patch.object(semrush_client, "_make_request") as mock_request:
        # Both calls return zero results
        mock_request.side_effect = [
            ZERO_VOLUME_RESPONSE,
            ZERO_VOLUME_RESPONSE,
            SUGGESTIONS_RESPONSE,  # For suggestions
        ]

        with pytest.raises(ValueError) as exc_info:
            await semrush_client.expand_keywords(
                seed_keyword="nonexistent keyword",
                max_keywords=5,
                min_volume=10,
                max_cost_usd=1.0,
            )

        # Should include suggestions in error message
        assert "Suggestions:" in str(exc_info.value)


@pytest.mark.asyncio
async def test_intent_detection(semrush_client):
    """Test intent detection for different keyword types"""
    # Local intent
    assert semrush_client._detect_intent("dentist near me") == "local"
    assert semrush_client._detect_intent("dental clinic in boston") == "local"

    # Informational intent
    assert semrush_client._detect_intent("what are dental implants") == "informational"
    assert semrush_client._detect_intent("how to brush teeth") == "informational"

    # Commercial intent
    assert semrush_client._detect_intent("dental implants cost") == "commercial"
    assert semrush_client._detect_intent("book dentist appointment") == "commercial"

    # Navigational intent
    assert semrush_client._detect_intent("best dentist") == "navigational"
    assert semrush_client._detect_intent("top dental clinics") == "navigational"


@pytest.mark.asyncio
async def test_pagination_support(semrush_client):
    """Test pagination fetches multiple pages"""
    with patch.object(semrush_client, "_fetch_keyword_page") as mock_fetch:
        # Create full page of 100 keywords to trigger pagination
        full_page = []
        for i in range(100):
            full_page.append({
                "keyword": f"dental implants {i}",
                "volume": 1000 + i,
                "difficulty": 50,
                "cpc": 10.0,
                "intent": "commercial",
                "trend": "",
                "competition": 0.5,
            })

        # Return full page twice
        mock_fetch.side_effect = [full_page, full_page[:50]]

        keywords = await semrush_client.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=150,  # More than one page
            min_volume=10,
            max_cost_usd=5.0,
        )

        # Should have made multiple requests for pagination
        assert mock_fetch.call_count == 2
        assert len(keywords) == 150


@pytest.mark.asyncio
async def test_min_volume_filtering(semrush_client):
    """Test min_volume filtering is applied"""
    with patch.object(semrush_client, "_fetch_keyword_page") as mock_fetch:
        mock_fetch.return_value = [
            {
                "keyword": "high volume",
                "volume": 5000,
                "difficulty": 50,
                "cpc": 10.0,
                "intent": "commercial",
                "trend": "",
                "competition": 0.5,
            }
        ]

        await semrush_client.expand_keywords(
            seed_keyword="test",
            max_keywords=10,
            min_volume=100,
            max_cost_usd=1.0,
        )

        # Check that min_volume was passed to fetch
        call_args = mock_fetch.call_args
        assert call_args[1]["min_volume"] == 100


@pytest.mark.asyncio
async def test_cost_tracking(semrush_client):
    """Test API cost is tracked in metrics"""
    from src.aim.subagents.api_clients.base import api_cost_total

    with patch.object(semrush_client, "_make_request") as mock_request:
        mock_request.return_value = SEMRUSH_MOCK_RESPONSE

        # Get initial cost
        initial_cost = api_cost_total.labels(
            client="SEMrushClient",
            endpoint="keyword_magic",
        )._value.get()

        await semrush_client.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=5,
            min_volume=10,
            max_cost_usd=1.0,
        )

        # Check cost incremented
        final_cost = api_cost_total.labels(
            client="SEMrushClient",
            endpoint="keyword_magic",
        )._value.get()

        assert final_cost > initial_cost


@pytest.mark.asyncio
async def test_parse_semrush_row(semrush_client):
    """Test parsing SEMrush API row format"""
    row = {
        "Ph": "dental implants",
        "Nq": 5000,
        "Cp": 12.50,
        "Co": 0.85,
        "Nr": 1500000,
        "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
    }

    result = semrush_client._parse_semrush_row(row)

    assert result is not None
    assert result["keyword"] == "dental implants"
    assert result["volume"] == 5000
    assert result["cpc"] == 12.50
    assert result["difficulty"] == 85  # 0.85 * 100
    assert result["intent"] in ["informational", "commercial", "navigational", "local"]
