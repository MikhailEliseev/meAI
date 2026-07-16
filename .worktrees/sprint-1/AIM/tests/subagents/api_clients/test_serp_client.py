"""Tests for SERP API Client."""

import pytest
from unittest.mock import AsyncMock, patch

from AIM.src.aim.subagents.api_clients.serp_client import (
    SERPAPIClient,
    SERPClientConfig,
)
from AIM.src.aim.subagents.gap_detection.serp_overlap_clusterer import (
    KeywordSERPData,
    SERPResult,
)
from AIM.src.aim.subagents.schemas.content_gap import IntentType


@pytest.fixture
def serp_config():
    """Create SERP client config."""
    return SERPClientConfig(
        provider="mock",
        api_key="test_key",
        serp_depth=30,
        max_cost_per_keyword=0.02,
    )


@pytest.fixture
def serp_client(serp_config):
    """Create SERP API client."""
    return SERPAPIClient(config=serp_config)


@pytest.fixture
def mock_dataforseo_response():
    """Mock DataForSEO API response."""
    return {
        "tasks": [
            {
                "status_code": 20000,
                "data": {"keyword": "dental implants"},
                "result": [
                    {
                        "items": [
                            {
                                "type": "organic",
                                "url": "https://example1.com/dental-implants",
                                "rank_absolute": 1,
                                "title": "Dental Implants Guide",
                            },
                            {
                                "type": "organic",
                                "url": "https://example2.com/implants",
                                "rank_absolute": 2,
                                "title": "Best Dental Implants",
                            },
                        ]
                    }
                ],
            }
        ]
    }


@pytest.fixture
def mock_semrush_response():
    """Mock SEMrush API response."""
    return """Ph;Po;Ur;Tt
dental implants;1;https://example1.com/dental-implants;Dental Implants Guide
dental implants;2;https://example2.com/implants;Best Dental Implants"""


@pytest.mark.asyncio
async def test_fetch_serp_data_mock(serp_client):
    """Test fetching SERP data with mock provider."""
    keywords = ["dental implants", "teeth whitening"]

    results = await serp_client.fetch_serp_data(
        keywords=keywords,
        max_cost_usd=1.0,
    )

    assert len(results) == 2
    assert all(isinstance(r, KeywordSERPData) for r in results)
    assert results[0].keyword == "dental implants"
    assert results[1].keyword == "teeth whitening"
    assert len(results[0].serp_results) == 30  # Default serp_depth
    assert all(isinstance(r, SERPResult) for r in results[0].serp_results)


@pytest.mark.asyncio
async def test_fetch_serp_data_empty_keywords(serp_client):
    """Test that empty keywords list raises error."""
    with pytest.raises(ValueError, match="keywords list cannot be empty"):
        await serp_client.fetch_serp_data(keywords=[])


@pytest.mark.asyncio
async def test_fetch_serp_data_budget_exceeded(serp_client):
    """Test that budget exceeded raises error."""
    keywords = ["keyword"] * 100  # 100 keywords * $0.02 = $2.00

    with pytest.raises(ValueError, match="exceeds budget"):
        await serp_client.fetch_serp_data(
            keywords=keywords,
            max_cost_usd=1.0,  # Budget too low
        )


@pytest.mark.asyncio
async def test_fetch_dataforseo(serp_client, mock_dataforseo_response):
    """Test fetching SERP data from DataForSEO."""
    serp_client.provider = "dataforseo"

    with patch.object(
        serp_client, "_make_request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_dataforseo_response

        results = await serp_client.fetch_serp_data(
            keywords=["dental implants"],
            max_cost_usd=1.0,
        )

        assert len(results) == 1
        assert results[0].keyword == "dental implants"
        assert len(results[0].serp_results) == 2
        assert results[0].serp_results[0].url == "https://example1.com/dental-implants"
        assert results[0].serp_results[0].position == 1
        assert results[0].serp_results[0].title == "Dental Implants Guide"


@pytest.mark.asyncio
async def test_fetch_semrush(serp_client, mock_semrush_response):
    """Test fetching SERP data from SEMrush."""
    serp_client.provider = "semrush"

    with patch.object(
        serp_client, "_make_request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_semrush_response

        results = await serp_client.fetch_serp_data(
            keywords=["dental implants"],
            max_cost_usd=1.0,
        )

        assert len(results) == 1
        assert results[0].keyword == "dental implants"
        assert len(results[0].serp_results) == 2
        assert results[0].serp_results[0].url == "https://example1.com/dental-implants"
        assert results[0].serp_results[0].position == 1


def test_detect_intent_transactional(serp_client):
    """Test intent detection for transactional queries."""
    serp_item = {
        "url": "https://example.com/buy-dental-implants",
        "title": "Buy Dental Implants Online",
    }

    intent = serp_client._detect_intent(serp_item)
    assert intent == IntentType.TRANSACTIONAL


def test_detect_intent_commercial(serp_client):
    """Test intent detection for commercial queries."""
    serp_item = {
        "url": "https://example.com/best-dental-implants-review",
        "title": "Best Dental Implants 2024",
    }

    intent = serp_client._detect_intent(serp_item)
    assert intent == IntentType.COMMERCIAL


def test_detect_intent_navigational(serp_client):
    """Test intent detection for navigational queries."""
    serp_item = {
        "url": "https://example.com/about",
        "title": "About Us - Dental Clinic",
    }

    intent = serp_client._detect_intent(serp_item)
    assert intent == IntentType.NAVIGATIONAL


def test_detect_intent_informational(serp_client):
    """Test intent detection for informational queries."""
    serp_item = {
        "url": "https://example.com/what-are-dental-implants",
        "title": "What Are Dental Implants?",
    }

    intent = serp_client._detect_intent(serp_item)
    assert intent == IntentType.INFORMATIONAL


def test_determine_primary_intent(serp_client):
    """Test determining primary intent from SERP results."""
    serp_results = [
        SERPResult(
            keyword="dental implants",
            url="https://example1.com",
            position=1,
            title="Title 1",
            intent=IntentType.INFORMATIONAL,
        ),
        SERPResult(
            keyword="dental implants",
            url="https://example2.com",
            position=2,
            title="Title 2",
            intent=IntentType.INFORMATIONAL,
        ),
        SERPResult(
            keyword="dental implants",
            url="https://example3.com",
            position=3,
            title="Title 3",
            intent=IntentType.COMMERCIAL,
        ),
    ]

    primary_intent = serp_client._determine_primary_intent(serp_results)
    assert primary_intent == IntentType.INFORMATIONAL  # Majority


def test_determine_primary_intent_empty(serp_client):
    """Test determining primary intent with empty results."""
    primary_intent = serp_client._determine_primary_intent([])
    assert primary_intent == IntentType.INFORMATIONAL  # Default


def test_get_semrush_database(serp_client):
    """Test mapping location to SEMrush database code."""
    assert serp_client._get_semrush_database("United States") == "us"
    assert serp_client._get_semrush_database("United Kingdom") == "uk"
    assert serp_client._get_semrush_database("Russia") == "ru"
    assert serp_client._get_semrush_database("Unknown") == "us"  # Default


@pytest.mark.asyncio
async def test_fetch_mock_serp_depth(serp_client):
    """Test that mock provider respects serp_depth config."""
    serp_client.config.serp_depth = 10

    results = await serp_client.fetch_serp_data(
        keywords=["dental implants"],
        max_cost_usd=1.0,
    )

    assert len(results[0].serp_results) == 10


@pytest.mark.asyncio
async def test_fetch_serp_data_multiple_keywords(serp_client):
    """Test fetching SERP data for multiple keywords."""
    keywords = ["dental implants", "teeth whitening", "orthodontics"]

    results = await serp_client.fetch_serp_data(
        keywords=keywords,
        max_cost_usd=1.0,
    )

    assert len(results) == 3
    assert {r.keyword for r in results} == set(keywords)


@pytest.mark.asyncio
async def test_close_client(serp_client):
    """Test closing SERP client."""
    await serp_client.close()
    # Should not raise error
