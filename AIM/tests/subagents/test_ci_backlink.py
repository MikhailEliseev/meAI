"""
Tests for CI Backlink Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from AIM.src.aim.subagents.competitive_intel.agents.ci_backlink import (
    CIBacklinkAgent,
    BacklinkStats,
    DomainMetrics,
    BacklinkOpportunity,
)


@pytest.fixture
def agent():
    """Create agent instance."""
    return CIBacklinkAgent(api_key="test_key")


@pytest.fixture
def mock_backlinks_stats():
    """Mock backlinks stats response."""
    return {
        "live": 5000,
        "live_refdomains": 500,
        "dofollow": 4000,
        "nofollow": 1000,
        "gov": 10,
        "edu": 5,
        "text": 4500,
        "image": 500,
        "redirect": 100,
        "canonical": 50,
    }


@pytest.fixture
def mock_metrics():
    """Mock domain metrics response."""
    return {
        "domain_rating": 75.0,
        "ahrefs_rank": 1000,
        "org_keywords": 10000,
        "org_traffic": 50000,
        "refdomains": 500,
    }


@pytest.fixture
def mock_linkeddomains():
    """Mock linked domains response."""
    return {
        "linkeddomains": [
            {
                "domain": "authority-site.com",
                "domain_rating": 85.0,
                "backlinks": 50,
            },
            {
                "domain": "medium-site.com",
                "domain_rating": 60.0,
                "backlinks": 20,
            },
            {
                "domain": "low-site.com",
                "domain_rating": 30.0,
                "backlinks": 5,
            },
        ]
    }


@pytest.mark.asyncio
async def test_fetch_backlinks_stats(agent, mock_backlinks_stats):
    """Test fetching backlink statistics."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_backlinks_stats)
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        import httpx
        async with httpx.AsyncClient() as client:
            stats = await agent._fetch_backlinks_stats(
                client, "example.com", "2026-05-14"
            )

        assert stats.live == 5000
        assert stats.live_refdomains == 500
        assert stats.dofollow == 4000
        assert stats.nofollow == 1000
        assert stats.gov == 10
        assert stats.edu == 5


@pytest.mark.asyncio
async def test_fetch_metrics(agent, mock_metrics):
    """Test fetching domain metrics."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_metrics)
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        import httpx
        async with httpx.AsyncClient() as client:
            metrics = await agent._fetch_metrics(
                client, "example.com", "2026-05-14"
            )

        assert metrics.domain_rating == 75.0
        assert metrics.ahrefs_rank == 1000
        assert metrics.org_keywords == 10000
        assert metrics.org_traffic == 50000
        assert metrics.refdomains == 500


@pytest.mark.asyncio
async def test_find_opportunities(agent, mock_linkeddomains):
    """Test finding link building opportunities."""
    with patch("httpx.AsyncClient.get") as mock_get:
        # First call: competitor domains
        competitor_response = AsyncMock()
        competitor_response.json = AsyncMock(return_value=mock_linkeddomains)
        competitor_response.raise_for_status = AsyncMock()

        # Second call: our domains (empty)
        our_response = AsyncMock()
        our_response.json = AsyncMock(return_value={"linkeddomains": []})
        our_response.raise_for_status = AsyncMock()

        mock_get.side_effect = [competitor_response, our_response]

        import httpx
        async with httpx.AsyncClient() as client:
            opportunities = await agent._find_opportunities(
                client,
                "competitor.com",
                "oursite.com",
                "2026-05-14",
            )

        # Should find all 3 domains as opportunities
        assert len(opportunities) == 3

        # Check first opportunity (highest DR)
        top_opp = opportunities[0]
        assert top_opp.domain == "authority-site.com"
        assert top_opp.domain_rating == 85.0
        assert top_opp.backlinks_to_competitor == 50
        assert top_opp.backlinks_to_us == 0
        assert top_opp.opportunity_score > 0


@pytest.mark.asyncio
async def test_analyze_complete_workflow(
    agent,
    mock_backlinks_stats,
    mock_metrics,
    mock_linkeddomains,
):
    """Test complete analysis workflow."""
    with patch("httpx.AsyncClient.get") as mock_get:
        # Setup mock responses for all API calls
        stats_response = AsyncMock()
        stats_response.json = AsyncMock(return_value=mock_backlinks_stats)
        stats_response.raise_for_status = AsyncMock()

        metrics_response = AsyncMock()
        metrics_response.json = AsyncMock(return_value=mock_metrics)
        metrics_response.raise_for_status = AsyncMock()

        competitor_domains_response = AsyncMock()
        competitor_domains_response.json = AsyncMock(return_value=mock_linkeddomains)
        competitor_domains_response.raise_for_status = AsyncMock()

        our_domains_response = AsyncMock()
        our_domains_response.json = AsyncMock(return_value={"linkeddomains": []})
        our_domains_response.raise_for_status = AsyncMock()

        # Order: competitor stats, competitor metrics, our stats, our metrics,
        #        competitor domains, our domains
        mock_get.side_effect = [
            stats_response,  # competitor stats
            metrics_response,  # competitor metrics
            stats_response,  # our stats
            metrics_response,  # our metrics
            competitor_domains_response,  # competitor domains
            our_domains_response,  # our domains
        ]

        result = await agent.analyze(
            target_url="competitor.com",
            our_url="oursite.com",
            date="2026-05-14",
        )

        # Check result structure
        assert result.target_url == "competitor.com"
        assert result.our_url == "oursite.com"
        assert result.timestamp is not None

        # Check stats
        assert result.competitor_stats.live == 5000
        assert result.our_stats.live == 5000

        # Check metrics
        assert result.competitor_metrics.domain_rating == 75.0
        assert result.our_metrics.domain_rating == 75.0

        # Check gaps (should be 0 since we used same mock data)
        assert result.backlink_gap == 0
        assert result.refdomains_gap == 0
        assert result.dr_gap == 0.0

        # Check opportunities
        assert len(result.opportunities) == 3

        # Check summary and recommendations
        assert result.summary is not None
        assert len(result.recommendations) > 0


def test_generate_summary(agent):
    """Test summary generation."""
    competitor_stats = BacklinkStats(
        live=10000,
        live_refdomains=1000,
        dofollow=8000,
        nofollow=2000,
        gov=20,
        edu=10,
        text=9000,
        image=1000,
        redirect=200,
        canonical=100,
    )

    our_stats = BacklinkStats(
        live=5000,
        live_refdomains=500,
        dofollow=4000,
        nofollow=1000,
        gov=10,
        edu=5,
        text=4500,
        image=500,
        redirect=100,
        canonical=50,
    )

    summary = agent._generate_summary(
        competitor_stats=competitor_stats,
        our_stats=our_stats,
        backlink_gap=5000,
        refdomains_gap=500,
        dr_gap=10.0,
    )

    assert "5,000 more backlinks" in summary
    assert "500 more referring domains" in summary
    assert "10.0 higher Domain Rating" in summary
    assert "10,000 live backlinks" in summary
    assert "5,000 live backlinks" in summary


def test_generate_recommendations(agent):
    """Test recommendations generation."""
    opportunities = [
        BacklinkOpportunity(
            domain="high-authority.com",
            domain_rating=90.0,
            backlinks_to_competitor=100,
            backlinks_to_us=0,
            gap=100,
            opportunity_score=0.85,
        ),
        BacklinkOpportunity(
            domain="medium-authority.com",
            domain_rating=70.0,
            backlinks_to_competitor=50,
            backlinks_to_us=0,
            gap=50,
            opportunity_score=0.65,
        ),
    ]

    # Test large gap
    recommendations = agent._generate_recommendations(
        backlink_gap=2000,
        refdomains_gap=100,
        dr_gap=15.0,
        opportunities=opportunities,
    )

    assert len(recommendations) > 0
    assert any("CRITICAL" in rec for rec in recommendations)
    assert any("Domain Rating gap" in rec for rec in recommendations)
    assert any("high-authority.com" in rec for rec in recommendations)

    # Test small gap
    recommendations = agent._generate_recommendations(
        backlink_gap=50,
        refdomains_gap=10,
        dr_gap=2.0,
        opportunities=[],
    )

    assert len(recommendations) > 0


def test_agent_capabilities():
    """Test agent capabilities reporting."""
    agent = CIBacklinkAgent(api_key="test_key")

    # Agent should have these capabilities
    assert hasattr(agent, "analyze")
    assert hasattr(agent, "_fetch_backlinks_stats")
    assert hasattr(agent, "_fetch_metrics")
    assert hasattr(agent, "_find_opportunities")
    assert hasattr(agent, "_generate_summary")
    assert hasattr(agent, "_generate_recommendations")


@pytest.mark.asyncio
async def test_opportunity_scoring():
    """Test opportunity scoring algorithm."""
    agent = CIBacklinkAgent(api_key="test_key")

    # High DR, many backlinks = high score
    high_dr_domain = {
        "domain": "authority.com",
        "domain_rating": 90.0,
        "backlinks": 100,
    }

    # Low DR, few backlinks = low score
    low_dr_domain = {
        "domain": "weak.com",
        "domain_rating": 20.0,
        "backlinks": 5,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        competitor_response = AsyncMock()
        competitor_response.json = AsyncMock(return_value={
            "linkeddomains": [high_dr_domain, low_dr_domain]
        })
        competitor_response.raise_for_status = AsyncMock()

        our_response = AsyncMock()
        our_response.json = AsyncMock(return_value={"linkeddomains": []})
        our_response.raise_for_status = AsyncMock()

        mock_get.side_effect = [competitor_response, our_response]

        import httpx
        async with httpx.AsyncClient() as client:
            opportunities = await agent._find_opportunities(
                client,
                "competitor.com",
                "oursite.com",
                "2026-05-14",
            )

        # High DR domain should have higher score
        assert opportunities[0].domain == "authority.com"
        assert opportunities[0].opportunity_score > opportunities[1].opportunity_score
