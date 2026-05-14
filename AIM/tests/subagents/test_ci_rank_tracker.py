"""
Tests for CI Rank Tracker Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from AIM.src.aim.subagents.competitive_intel.agents.ci_rank_tracker import (
    CIRankTrackerAgent,
    KeywordPosition,
    PositionChange,
    CompetitorPosition,
)


@pytest.fixture
def agent():
    """Create agent instance."""
    return CIRankTrackerAgent(serpapi_key="test_key")


@pytest.fixture
def mock_current_positions():
    """Mock current period positions."""
    return [
        KeywordPosition(
            keyword="seo tools",
            position=5.0,
            url="https://example.com/seo-tools",
            impressions=1000,
            clicks=50,
            ctr=0.05,
            date="2026-05-14",
        ),
        KeywordPosition(
            keyword="keyword research",
            position=12.0,
            url="https://example.com/keyword-research",
            impressions=500,
            clicks=20,
            ctr=0.04,
            date="2026-05-14",
        ),
        KeywordPosition(
            keyword="backlink analysis",
            position=8.0,
            url="https://example.com/backlinks",
            impressions=300,
            clicks=15,
            ctr=0.05,
            date="2026-05-14",
        ),
    ]


@pytest.fixture
def mock_previous_positions():
    """Mock previous period positions."""
    return [
        KeywordPosition(
            keyword="seo tools",
            position=8.0,  # Was worse
            url="https://example.com/seo-tools",
            impressions=800,
            clicks=40,
            ctr=0.05,
            date="2026-05-07",
        ),
        KeywordPosition(
            keyword="keyword research",
            position=10.0,  # Was better
            url="https://example.com/keyword-research",
            impressions=600,
            clicks=25,
            ctr=0.042,
            date="2026-05-07",
        ),
        KeywordPosition(
            keyword="backlink analysis",
            position=8.0,  # Same
            url="https://example.com/backlinks",
            impressions=300,
            clicks=15,
            ctr=0.05,
            date="2026-05-07",
        ),
    ]


@pytest.fixture
def mock_serpapi_response():
    """Mock SerpAPI response."""
    return {
        "organic_results": [
            {
                "position": 1,
                "link": "https://competitor1.com/page",
                "title": "Best SEO Tools 2026",
                "snippet": "Comprehensive guide to SEO tools...",
            },
            {
                "position": 2,
                "link": "https://competitor2.com/page",
                "title": "Top 10 SEO Tools",
                "snippet": "Our favorite SEO tools for 2026...",
            },
            {
                "position": 3,
                "link": "https://example.com/seo-tools",
                "title": "SEO Tools Guide",
                "snippet": "Everything you need to know...",
            },
        ]
    }


def test_calculate_changes(agent, mock_current_positions, mock_previous_positions):
    """Test position change calculation."""
    changes = agent._calculate_changes(
        mock_current_positions, mock_previous_positions
    )

    assert len(changes) == 3

    # Check "seo tools" - improved from 8 to 5
    seo_change = next(c for c in changes if c.keyword == "seo tools")
    assert seo_change.current_position == 5.0
    assert seo_change.previous_position == 8.0
    assert seo_change.change == -3.0  # Negative = improvement
    assert seo_change.trend == "up"

    # Check "keyword research" - declined from 10 to 12
    keyword_change = next(c for c in changes if c.keyword == "keyword research")
    assert keyword_change.current_position == 12.0
    assert keyword_change.previous_position == 10.0
    assert keyword_change.change == 2.0  # Positive = decline
    assert keyword_change.trend == "down"

    # Check "backlink analysis" - stable at 8
    backlink_change = next(c for c in changes if c.keyword == "backlink analysis")
    assert backlink_change.current_position == 8.0
    assert backlink_change.previous_position == 8.0
    assert backlink_change.change == 0.0
    assert backlink_change.trend == "stable"


@pytest.mark.asyncio
async def test_fetch_competitor_positions(agent, mock_serpapi_response):
    """Test fetching competitor positions from SerpAPI."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_serpapi_response)
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        import httpx
        async with httpx.AsyncClient() as client:
            positions = await agent._fetch_competitor_positions(
                client, ["seo tools"]
            )

        assert len(positions) == 3

        # Check first competitor
        assert positions[0].keyword == "seo tools"
        assert positions[0].competitor_url == "https://competitor1.com/page"
        assert positions[0].position == 1
        assert positions[0].title == "Best SEO Tools 2026"

        # Check our position
        our_position = next(
            p for p in positions if "example.com" in p.competitor_url
        )
        assert our_position.position == 3


@pytest.mark.asyncio
async def test_track_rankings_summary_metrics(
    agent, mock_current_positions, mock_previous_positions
):
    """Test summary metrics calculation."""
    with patch.object(
        agent, "_fetch_gsc_data", side_effect=[mock_current_positions, mock_previous_positions]
    ):
        with patch.object(agent, "_fetch_competitor_positions", return_value=[]):
            result = await agent.track_rankings(
                target_url="https://example.com",
                keywords=["seo tools", "keyword research", "backlink analysis"],
                days=7,
                compare_days=7,
            )

    # Check summary metrics
    assert result.total_keywords == 3
    assert result.avg_position == 8.3  # (5 + 12 + 8) / 3
    assert result.top_3_count == 0
    assert result.top_10_count == 2  # positions 5 and 8
    assert result.top_100_count == 3  # all positions


@pytest.mark.asyncio
async def test_track_rankings_insights(
    agent, mock_current_positions, mock_previous_positions
):
    """Test insights generation (gains, losses, new, lost)."""
    with patch.object(
        agent, "_fetch_gsc_data", side_effect=[mock_current_positions, mock_previous_positions]
    ):
        with patch.object(agent, "_fetch_competitor_positions", return_value=[]):
            result = await agent.track_rankings(
                target_url="https://example.com",
                keywords=["seo tools", "keyword research", "backlink analysis"],
                days=7,
                compare_days=7,
            )

    # Check biggest gains (improved positions)
    assert len(result.biggest_gains) > 0
    top_gain = result.biggest_gains[0]
    assert top_gain.keyword == "seo tools"
    assert top_gain.change == -3.0  # Improved by 3 positions

    # Check biggest losses (declined positions)
    assert len(result.biggest_losses) > 0
    top_loss = result.biggest_losses[0]
    assert top_loss.keyword == "keyword research"
    assert top_loss.change == 2.0  # Declined by 2 positions


@pytest.mark.asyncio
async def test_track_rankings_new_and_lost(agent):
    """Test detection of new and lost rankings."""
    current = [
        KeywordPosition(
            keyword="new keyword",
            position=15.0,
            url="https://example.com/new",
            impressions=100,
            clicks=5,
            ctr=0.05,
            date="2026-05-14",
        ),
        KeywordPosition(
            keyword="existing keyword",
            position=10.0,
            url="https://example.com/existing",
            impressions=200,
            clicks=10,
            ctr=0.05,
            date="2026-05-14",
        ),
    ]

    previous = [
        KeywordPosition(
            keyword="existing keyword",
            position=12.0,
            url="https://example.com/existing",
            impressions=150,
            clicks=8,
            ctr=0.053,
            date="2026-05-07",
        ),
        KeywordPosition(
            keyword="lost keyword",
            position=20.0,
            url="https://example.com/lost",
            impressions=50,
            clicks=2,
            ctr=0.04,
            date="2026-05-07",
        ),
    ]

    with patch.object(agent, "_fetch_gsc_data", side_effect=[current, previous]):
        with patch.object(agent, "_fetch_competitor_positions", return_value=[]):
            result = await agent.track_rankings(
                target_url="https://example.com",
                keywords=["new keyword", "existing keyword"],
                days=7,
                compare_days=7,
            )

    # Check new rankings
    assert len(result.new_rankings) == 1
    assert result.new_rankings[0].keyword == "new keyword"

    # Check lost rankings
    assert len(result.lost_rankings) == 1
    assert "lost keyword" in result.lost_rankings


def test_agent_capabilities():
    """Test agent capabilities reporting."""
    agent = CIRankTrackerAgent(serpapi_key="test_key")

    # Agent should have these capabilities
    assert hasattr(agent, "track_rankings")
    assert hasattr(agent, "_fetch_gsc_data")
    assert hasattr(agent, "_fetch_competitor_positions")
    assert hasattr(agent, "_calculate_changes")


@pytest.mark.asyncio
async def test_fetch_gsc_data_with_keywords(agent):
    """Test GSC data fetching with specific keywords."""
    import httpx

    async with httpx.AsyncClient() as client:
        positions = await agent._fetch_gsc_data(
            client,
            "https://example.com",
            "2026-05-07",
            "2026-05-14",
            keywords=["test keyword 1", "test keyword 2"],
        )

    # Should return positions for specified keywords
    assert len(positions) == 2
    assert positions[0].keyword == "test keyword 1"
    assert positions[1].keyword == "test keyword 2"


def test_position_change_percent_calculation(agent):
    """Test position change percentage calculation."""
    current = [
        KeywordPosition(
            keyword="test",
            position=5.0,
            url="https://example.com",
            impressions=100,
            clicks=5,
            ctr=0.05,
            date="2026-05-14",
        )
    ]

    previous = [
        KeywordPosition(
            keyword="test",
            position=10.0,
            url="https://example.com",
            impressions=100,
            clicks=5,
            ctr=0.05,
            date="2026-05-07",
        )
    ]

    changes = agent._calculate_changes(current, previous)

    assert len(changes) == 1
    change = changes[0]

    # Position improved from 10 to 5 = -5 change
    assert change.change == -5.0

    # Percent change: (-5 / 10) * 100 = -50%
    assert change.change_percent == -50.0
