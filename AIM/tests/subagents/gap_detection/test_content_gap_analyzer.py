"""
Unit tests for Content Gap Analyzer - Main Orchestrator.

Tests integration of all gap detection components.
"""

from datetime import datetime

import pytest

from AIM.src.aim.subagents.gap_detection.content_gap_analyzer import (
    ContentGapAnalyzer,
)
from AIM.src.aim.subagents.schemas.content_gap import GapType


class TestContentGapAnalyzer:
    """Test Content Gap Analyzer main orchestrator."""

    def test_initialization_default(self):
        """Test default initialization."""
        analyzer = ContentGapAnalyzer()

        assert analyzer.min_content_quality == 0.6
        assert analyzer.overlap_threshold == 0.4
        assert analyzer.max_cost_usd == 1.0
        assert analyzer.gap_detector is not None
        assert analyzer.opportunity_scorer is not None
        assert analyzer.serp_clusterer is not None
        assert analyzer.architecture_planner is not None
        assert analyzer.brief_generator is not None

    def test_initialization_custom(self):
        """Test custom initialization."""
        analyzer = ContentGapAnalyzer(
            min_content_quality=0.7,
            overlap_threshold=0.5,
            max_cost_usd=2.0,
        )

        assert analyzer.min_content_quality == 0.7
        assert analyzer.overlap_threshold == 0.5
        assert analyzer.max_cost_usd == 2.0

    @pytest.mark.asyncio
    async def test_analyze_basic_structure(self):
        """Test basic analysis structure."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/page1",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            },
            {
                "url": "https://competitor.com/page2",
                "title": "Dental Implant Recovery",
                "word_count": 1500,
                "eeat_score": 0.75,
                "doctor_authored": True,
                "keywords": ["recovery", "dental implants"],
            },
        ]

        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        assert result.client_url == "https://client.com"
        assert result.competitor_urls == ["https://competitor.com"]
        assert result.niche == "dental implants"
        assert isinstance(result.gaps, list)
        assert isinstance(result.clusters, list)
        assert isinstance(result.architecture, dict)
        assert isinstance(result.briefs, list)
        assert isinstance(result.summary, dict)
        assert isinstance(result.analyzed_at, datetime)

    @pytest.mark.asyncio
    async def test_analyze_detects_gaps(self):
        """Test that analysis detects gaps."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/all-on-4",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            },
            {
                "url": "https://competitor.com/recovery",
                "title": "Dental Implant Recovery",
                "word_count": 1500,
                "eeat_score": 0.75,
                "doctor_authored": True,
                "keywords": ["recovery", "dental implants"],
            },
        ]

        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # Should detect keyword gaps (all-on-4, recovery)
        assert len(result.gaps) > 0
        assert result.summary["total_gaps"] > 0

    @pytest.mark.asyncio
    async def test_analyze_scores_and_prioritizes(self):
        """Test that gaps are scored and prioritized."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/all-on-4",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            }
        ]

        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # All gaps should have scores and priorities
        for gap in result.gaps:
            assert gap.opportunity_score >= 0
            assert gap.opportunity_score <= 100
            assert gap.priority in ["P0", "P1", "P2", "P3"]

    @pytest.mark.asyncio
    async def test_analyze_with_keywords_clusters(self):
        """Test analysis with keyword clustering."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/page1",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            }
        ]

        keywords = ["dental implants", "all-on-4", "implant cost"]

        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
            keywords=keywords,
        )

        # Should have clusters when keywords provided
        assert isinstance(result.clusters, list)

    @pytest.mark.asyncio
    async def test_analyze_generates_briefs(self):
        """Test that briefs are generated for top gaps."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/all-on-4",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            }
        ]

        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # Should generate briefs for top gaps
        assert isinstance(result.briefs, list)

    @pytest.mark.asyncio
    async def test_analyze_summary_metrics(self):
        """Test summary metrics calculation."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/page1",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            }
        ]

        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        summary = result.summary
        assert "total_gaps" in summary
        assert "p0_gaps" in summary
        assert "p1_gaps" in summary
        assert "p2_gaps" in summary
        assert "total_clusters" in summary
        assert "total_briefs" in summary
        assert "execution_time_ms" in summary
        assert "pages_analyzed" in summary
        assert summary["pages_analyzed"] == 2  # 1 client + 1 competitor

    @pytest.mark.asyncio
    async def test_validate_inputs_invalid_client_url(self):
        """Test validation fails for invalid client URL."""
        analyzer = ContentGapAnalyzer()

        with pytest.raises(ValueError, match="Invalid client_url"):
            await analyzer.analyze(
                client_url="invalid-url",
                competitor_urls=["https://competitor.com"],
                niche="dental implants",
                client_pages=[{"url": "https://client.com/page1"}],
                competitor_pages=[{"url": "https://competitor.com/page1"}],
            )

    @pytest.mark.asyncio
    async def test_validate_inputs_empty_competitor_urls(self):
        """Test validation fails for empty competitor URLs."""
        analyzer = ContentGapAnalyzer()

        with pytest.raises(ValueError, match="competitor_urls must contain at least 1 URL"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=[],
                niche="dental implants",
                client_pages=[{"url": "https://client.com/page1"}],
                competitor_pages=[{"url": "https://competitor.com/page1"}],
            )

    @pytest.mark.asyncio
    async def test_validate_inputs_too_many_competitors(self):
        """Test validation fails for too many competitor URLs."""
        analyzer = ContentGapAnalyzer()

        competitor_urls = [f"https://competitor{i}.com" for i in range(11)]

        with pytest.raises(ValueError, match="competitor_urls must contain at most 10 URLs"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=competitor_urls,
                niche="dental implants",
                client_pages=[{"url": "https://client.com/page1"}],
                competitor_pages=[{"url": "https://competitor.com/page1"}],
            )

    @pytest.mark.asyncio
    async def test_validate_inputs_invalid_competitor_url(self):
        """Test validation fails for invalid competitor URL."""
        analyzer = ContentGapAnalyzer()

        with pytest.raises(ValueError, match="Invalid competitor URL"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=["invalid-url"],
                niche="dental implants",
                client_pages=[{"url": "https://client.com/page1"}],
                competitor_pages=[{"url": "https://competitor.com/page1"}],
            )

    @pytest.mark.asyncio
    async def test_validate_inputs_empty_niche(self):
        """Test validation fails for empty niche."""
        analyzer = ContentGapAnalyzer()

        with pytest.raises(ValueError, match="niche cannot be empty"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=["https://competitor.com"],
                niche="",
                client_pages=[{"url": "https://client.com/page1"}],
                competitor_pages=[{"url": "https://competitor.com/page1"}],
            )

    @pytest.mark.asyncio
    async def test_validate_inputs_empty_client_pages(self):
        """Test validation fails for empty client pages."""
        analyzer = ContentGapAnalyzer()

        with pytest.raises(ValueError, match="client_pages cannot be empty"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=["https://competitor.com"],
                niche="dental implants",
                client_pages=[],
                competitor_pages=[{"url": "https://competitor.com/page1"}],
            )

    @pytest.mark.asyncio
    async def test_validate_inputs_empty_competitor_pages(self):
        """Test validation fails for empty competitor pages."""
        analyzer = ContentGapAnalyzer()

        with pytest.raises(ValueError, match="competitor_pages cannot be empty"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=["https://competitor.com"],
                niche="dental implants",
                client_pages=[{"url": "https://client.com/page1"}],
                competitor_pages=[],
            )

    @pytest.mark.asyncio
    async def test_compare_quality_basic(self):
        """Test quality comparison calculation."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
            },
            {
                "word_count": 1200,
                "eeat_score": 0.75,
                "doctor_authored": False,
            },
        ]

        competitor_pages = [
            {
                "word_count": 2000,
                "eeat_score": 0.85,
                "doctor_authored": True,
            },
            {
                "word_count": 1800,
                "eeat_score": 0.8,
                "doctor_authored": True,
            },
        ]

        comparison = await analyzer.compare_quality(
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        assert "client" in comparison
        assert "competitor" in comparison
        assert "gaps" in comparison

        # Client metrics
        assert comparison["client"]["avg_word_count"] == 1100  # (1000 + 1200) / 2
        assert comparison["client"]["avg_eeat_score"] == 0.72  # (0.7 + 0.75) / 2
        assert comparison["client"]["doctor_authored_pct"] == 50.0  # 1/2 * 100

        # Competitor metrics
        assert comparison["competitor"]["avg_word_count"] == 1900  # (2000 + 1800) / 2
        assert comparison["competitor"]["avg_eeat_score"] == 0.82  # (0.85 + 0.8) / 2
        assert comparison["competitor"]["doctor_authored_pct"] == 100.0  # 2/2 * 100

        # Gaps
        assert comparison["gaps"]["word_count_gap"] == 800  # 1900 - 1100
        assert comparison["gaps"]["eeat_gap"] == 0.1  # 0.82 - 0.72
        assert comparison["gaps"]["doctor_authorship_gap"] == 50.0  # 100 - 50

    @pytest.mark.asyncio
    async def test_compare_quality_empty_pages(self):
        """Test quality comparison with empty pages."""
        analyzer = ContentGapAnalyzer()

        comparison = await analyzer.compare_quality(
            client_pages=[],
            competitor_pages=[],
        )

        assert comparison["client"]["avg_word_count"] == 0
        assert comparison["client"]["avg_eeat_score"] == 0
        assert comparison["client"]["doctor_authored_pct"] == 0

    @pytest.mark.asyncio
    async def test_parallel_gap_detection(self):
        """Test that gap detection runs in parallel."""
        analyzer = ContentGapAnalyzer()

        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Dental Implants",
                "word_count": 1000,
                "eeat_score": 0.7,
                "doctor_authored": True,
                "keywords": ["dental implants"],
            }
        ]

        competitor_pages = [
            {
                "url": "https://competitor.com/all-on-4",
                "title": "All-on-4 Dental Implants",
                "word_count": 2000,
                "eeat_score": 0.8,
                "doctor_authored": True,
                "keywords": ["all-on-4", "dental implants"],
            }
        ]

        # This should complete quickly due to parallel execution
        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental implants",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # Verify execution time is reasonable (< 5 seconds for small dataset)
        assert result.summary["execution_time_ms"] < 5000
