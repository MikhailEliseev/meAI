"""Tests for SEO Magister V2 with Content Gap Analysis integration.

Tests cover:
- Initialization with gap analyzer parameters
- Parallel dispatch of 4 agents (technical, content, links, gap)
- Gap score calculation (deductive scoring with P0/P1/P2 gaps)
- Weighted overall score calculation (30/25/20/25)
- Recommendations generation including content gap recommendations
- Error handling for gap analyzer failures
- Client cleanup (close method)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from AIM.src.aim.magisters.seo_magister_v2 import SEOMagisterV2
from AIM.src.aim.subagents.schemas.content_gap import (
    ContentGap,
    GapAnalysisResult,
    GapType,
)


@pytest.fixture
def mock_gap_analyzer():
    """Create mock Content Gap Analyzer."""
    analyzer = AsyncMock()
    analyzer.analyze = AsyncMock()
    analyzer.close = AsyncMock()
    return analyzer


@pytest.fixture
def mock_technical_agent():
    """Create mock Technical SEO Agent."""
    agent = AsyncMock()
    agent.analyze = AsyncMock(
        return_value={
            "score": 85.0,
            "issues": [
                {"type": "mobile", "severity": "high", "description": "Mobile optimization needed"}
            ],
            "recommendations": ["Improve mobile responsiveness"],
        }
    )
    return agent


@pytest.fixture
def mock_content_agent():
    """Create mock Content SEO Agent."""
    agent = AsyncMock()
    agent.analyze = AsyncMock(
        return_value={
            "score": 75.0,
            "issues": [
                {"type": "quality", "severity": "medium", "description": "Content quality issues"}
            ],
            "recommendations": ["Improve content depth"],
        }
    )
    return agent


@pytest.fixture
def mock_links_agent():
    """Create mock Links SEO Agent."""
    agent = AsyncMock()
    agent.analyze = AsyncMock(
        return_value={
            "score": 65.0,
            "issues": [
                {"type": "backlinks", "severity": "high", "description": "Low backlink count"}
            ],
            "recommendations": ["Build more backlinks"],
        }
    )
    return agent


@pytest.fixture
def sample_gap_result():
    """Create sample gap analysis result."""
    from AIM.src.aim.subagents.schemas.content_gap import GapSeverity

    gaps = [
        ContentGap(
            missing_keyword="dental implants cost",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.CRITICAL,
            search_volume=1000,
            opportunity_score=0.85,
            competitor_coverage={"https://competitor1.com": True},
            target_keywords=["dental implants cost", "implant cost"],
            estimated_traffic_potential=1000,
        ),
        ContentGap(
            missing_keyword="implant procedure",
            gap_type=GapType.MISSING_KEYWORD,
            severity=GapSeverity.HIGH,
            search_volume=500,
            opportunity_score=0.75,
            competitor_coverage={"https://competitor1.com": True},
            target_keywords=["implant procedure"],
            estimated_traffic_potential=500,
        ),
        ContentGap(
            missing_keyword="dental implants guide",
            gap_type=GapType.MISSING_URL,
            severity=GapSeverity.MEDIUM,
            search_volume=200,
            opportunity_score=0.65,
            competitor_coverage={"https://competitor1.com": True},
            target_keywords=["dental implants guide"],
            estimated_traffic_potential=200,
        ),
    ]

    return GapAnalysisResult(
        client_url="https://client.com",
        competitor_urls=["https://competitor1.com"],
        niche="dental implants",
        gaps=gaps,
        clusters=[],
        architecture={},
        briefs=[],
        summary={
            "total_gaps": 3,
            "p0_gaps": 1,
            "p1_gaps": 1,
            "p2_gaps": 1,
            "total_clusters": 0,
            "total_briefs": 0,
            "execution_time_ms": 1000,
            "pages_analyzed": 10,
            "keywords_used": 5,
        },
    )


class TestSEOMagisterV2Initialization:
    """Test SEO Magister V2 initialization."""

    def test_init_without_gap_analyzer_params(self):
        """Test initialization without gap analyzer parameters."""
        magister = SEOMagisterV2()

        # Gap analyzer is always created (with mock provider by default)
        assert magister.gap_analyzer is not None
        assert magister.technical_agent is not None
        assert magister.content_agent is not None
        assert magister.links_agent is not None

    def test_init_with_gap_analyzer_params(self):
        """Test initialization with gap analyzer parameters."""
        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )

        assert magister.gap_analyzer is not None
        assert magister.technical_agent is not None
        assert magister.content_agent is not None
        assert magister.links_agent is not None


class TestSEOMagisterV2Analysis:
    """Test SEO Magister V2 analysis coordination."""

    @pytest.mark.asyncio
    async def test_coordinate_analysis_without_gap_analyzer(
        self,
        mock_technical_agent,
        mock_content_agent,
        mock_links_agent,
    ):
        """Test analysis coordination without gap analyzer (3 agents only)."""
        magister = SEOMagisterV2()
        magister.technical_agent = mock_technical_agent
        magister.content_agent = mock_content_agent
        magister.links_agent = mock_links_agent

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        # Verify 3 agents were called
        mock_technical_agent.analyze.assert_called_once()
        mock_content_agent.analyze.assert_called_once()
        mock_links_agent.analyze.assert_called_once()

        # Verify result structure (SEO Magister v2 format)
        assert "scores" in result
        assert "details" in result
        assert "technical" in result["details"]
        assert "content" in result["details"]
        assert "links" in result["details"]
        assert "content_gaps" in result["details"]  # Always present

        # Verify score is calculated
        assert result["scores"]["overall"] > 0

    @pytest.mark.asyncio
    async def test_coordinate_analysis_with_gap_analyzer(
        self,
        mock_technical_agent,
        mock_content_agent,
        mock_links_agent,
        mock_gap_analyzer,
        sample_gap_result,
    ):
        """Test analysis coordination with gap analyzer (4 agents)."""
        mock_gap_analyzer.analyze.return_value = sample_gap_result

        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )
        magister.gap_analyzer = mock_gap_analyzer
        magister.technical_agent = mock_technical_agent
        magister.content_agent = mock_content_agent
        magister.links_agent = mock_links_agent

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        # Verify 4 agents were called
        mock_technical_agent.analyze.assert_called_once()
        mock_content_agent.analyze.assert_called_once()
        mock_links_agent.analyze.assert_called_once()
        mock_gap_analyzer.analyze.assert_called_once()

        # Verify result structure
        assert "scores" in result
        assert "details" in result
        assert "technical" in result["details"]
        assert "content" in result["details"]
        assert "links" in result["details"]
        assert "content_gaps" in result["details"]

        # Verify gap analyzer was called with correct params
        call_kwargs = mock_gap_analyzer.analyze.call_args.kwargs
        assert call_kwargs["client_url"] == "https://client.com"
        assert call_kwargs["competitor_urls"] == ["https://competitor1.com"]
        assert call_kwargs["niche"] == "dental implants"

        # Verify weighted score calculation (4 agents: 30/25/20/25)
        assert "overall" in result["scores"]
        assert result["scores"]["overall"] > 0

    @pytest.mark.asyncio
    async def test_coordinate_analysis_with_keyword_expansion(
        self,
        mock_technical_agent,
        mock_content_agent,
        mock_links_agent,
        mock_gap_analyzer,
        sample_gap_result,
    ):
        """Test analysis with keyword expansion enabled."""
        mock_gap_analyzer.analyze.return_value = sample_gap_result

        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )
        magister.gap_analyzer = mock_gap_analyzer
        magister.technical_agent = mock_technical_agent
        magister.content_agent = mock_content_agent
        magister.links_agent = mock_links_agent

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
            expand_keywords=True,
            seed_keyword="dental implants",
            max_keywords=100,
            min_volume=10,
        )

        # Verify gap analyzer was called with expansion params
        call_kwargs = mock_gap_analyzer.analyze.call_args.kwargs
        assert call_kwargs["expand_keywords"] is True
        assert call_kwargs["seed_keyword"] == "dental implants"
        assert call_kwargs["max_keywords"] == 100
        assert call_kwargs["min_volume"] == 10


class TestSEOMagisterV2GapScoring:
    """Test gap score calculation."""

    def test_calculate_gap_score_no_gaps(self):
        """Test gap score with no gaps (perfect score)."""
        magister = SEOMagisterV2()

        gap_result = GapAnalysisResult(
            client_url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
            gaps=[],
            clusters=[],
            architecture={},
            briefs=[],
            summary={
                "total_gaps": 0,
                "p0_gaps": 0,
                "p1_gaps": 0,
                "p2_gaps": 0,
            },
        )

        score = magister._calculate_gap_score(gap_result)
        assert score == 100.0

    def test_calculate_gap_score_with_p0_gaps(self):
        """Test gap score with P0 gaps (critical)."""
        magister = SEOMagisterV2()

        gap_result = GapAnalysisResult(
            client_url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
            gaps=[],
            clusters=[],
            architecture={},
            briefs=[],
            summary={
                "total_gaps": 2,
                "p0_gaps": 2,
                "p1_gaps": 0,
                "p2_gaps": 0,
            },
        )

        score = magister._calculate_gap_score(gap_result)
        # 100 - (2 * 20) = 60
        assert score == 60.0

    def test_calculate_gap_score_with_mixed_gaps(self, sample_gap_result):
        """Test gap score with mixed P0/P1/P2 gaps."""
        magister = SEOMagisterV2()

        score = magister._calculate_gap_score(sample_gap_result)
        # 100 - (1*20 + 1*10 + 1*5) = 65
        assert score == 65.0

    def test_calculate_gap_score_floor_at_zero(self):
        """Test gap score never goes below 0."""
        magister = SEOMagisterV2()

        gap_result = GapAnalysisResult(
            client_url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
            gaps=[],
            clusters=[],
            architecture={},
            briefs=[],
            summary={
                "total_gaps": 10,
                "p0_gaps": 10,  # 10 * 20 = 200 points deduction
                "p1_gaps": 0,
                "p2_gaps": 0,
            },
        )

        score = magister._calculate_gap_score(gap_result)
        assert score == 0.0  # Floor at 0, not negative


class TestSEOMagisterV2Recommendations:
    """Test recommendations generation."""

    @pytest.mark.asyncio
    async def test_recommendations_include_content_gaps(
        self,
        mock_technical_agent,
        mock_content_agent,
        mock_links_agent,
        mock_gap_analyzer,
        sample_gap_result,
    ):
        """Test that recommendations include content gap recommendations."""
        mock_gap_analyzer.analyze.return_value = sample_gap_result

        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )
        magister.gap_analyzer = mock_gap_analyzer
        magister.technical_agent = mock_technical_agent
        magister.content_agent = mock_content_agent
        magister.links_agent = mock_links_agent

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        # Verify recommendations structure
        assert "recommendations" in result
        recommendations = result["recommendations"]

        # Should have recommendations from all 4 agents
        assert len(recommendations) >= 4

        # Check for content gap recommendations (dict format)
        gap_recommendations = [
            r for r in recommendations
            if isinstance(r, dict) and ("gap" in r.get("issue", "").lower() or "missing" in r.get("issue", "").lower())
        ]
        assert len(gap_recommendations) > 0

        # Check for critical priority (P0 gaps)
        critical_recommendations = [
            r for r in recommendations
            if isinstance(r, dict) and r.get("priority") == "critical"
        ]
        assert len(critical_recommendations) > 0

    @pytest.mark.asyncio
    async def test_recommendations_priority_order(
        self,
        mock_technical_agent,
        mock_content_agent,
        mock_links_agent,
        mock_gap_analyzer,
        sample_gap_result,
    ):
        """Test that recommendations are ordered by priority."""
        mock_gap_analyzer.analyze.return_value = sample_gap_result

        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )
        magister.gap_analyzer = mock_gap_analyzer
        magister.technical_agent = mock_technical_agent
        magister.content_agent = mock_content_agent
        magister.links_agent = mock_links_agent

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        recommendations = result["recommendations"]

        # Find indices of different priority levels (dict format)
        critical_idx = next(
            (i for i, r in enumerate(recommendations) if isinstance(r, dict) and r.get("priority") == "critical"),
            None
        )
        high_idx = next(
            (i for i, r in enumerate(recommendations) if isinstance(r, dict) and r.get("priority") == "high"),
            None
        )
        medium_idx = next(
            (i for i, r in enumerate(recommendations) if isinstance(r, dict) and r.get("priority") == "medium"),
            None
        )

        # Verify order: critical < high < medium (if they exist)
        if critical_idx is not None and high_idx is not None:
            assert critical_idx < high_idx
        if high_idx is not None and medium_idx is not None:
            assert high_idx < medium_idx


class TestSEOMagisterV2ErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_gap_analyzer_failure_does_not_crash(
        self,
        mock_technical_agent,
        mock_content_agent,
        mock_links_agent,
        mock_gap_analyzer,
    ):
        """Test that gap analyzer failure doesn't crash entire analysis."""
        mock_gap_analyzer.analyze.side_effect = Exception("API error")

        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )
        magister.gap_analyzer = mock_gap_analyzer
        magister.technical_agent = mock_technical_agent
        magister.content_agent = mock_content_agent
        magister.links_agent = mock_links_agent

        # Should not raise exception
        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        # Should still have results from other 3 agents
        assert "scores" in result
        assert "details" in result
        assert "technical" in result["details"]
        assert "content" in result["details"]
        assert "links" in result["details"]

        # Gap analysis should have error status
        assert "content_gaps" in result["details"]
        assert result["details"]["content_gaps"]["status"] == "error"


class TestSEOMagisterV2Cleanup:
    """Test cleanup and resource management."""

    @pytest.mark.asyncio
    async def test_close_without_gap_analyzer(self):
        """Test close method without gap analyzer."""
        magister = SEOMagisterV2()

        # Should not raise exception
        await magister.close()

    @pytest.mark.asyncio
    async def test_close_with_gap_analyzer(self, mock_gap_analyzer):
        """Test close method with gap analyzer."""
        magister = SEOMagisterV2(
            semrush_api_key="test_semrush_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )
        magister.gap_analyzer = mock_gap_analyzer

        await magister.close()

        # Verify gap analyzer was closed
        mock_gap_analyzer.close.assert_called_once()
