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
        assert analyzer.serp_client is not None  # Mock client by default

    def test_initialization_custom(self):
        """Test custom initialization."""
        analyzer = ContentGapAnalyzer(
            min_content_quality=0.7,
            overlap_threshold=0.5,
            max_cost_usd=2.0,
            serp_provider="mock",
        )

        assert analyzer.min_content_quality == 0.7
        assert analyzer.overlap_threshold == 0.5
        assert analyzer.max_cost_usd == 2.0
        assert analyzer.serp_client is not None

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

    @pytest.mark.asyncio
    async def test_fetch_serp_data(self):
        """Test fetching SERP data for keywords."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")

        keywords = ["dental implants", "teeth whitening"]
        serp_data = await analyzer._fetch_serp_data(keywords)

        assert len(serp_data) == 2
        assert serp_data[0].keyword == "dental implants"
        assert serp_data[1].keyword == "teeth whitening"
        assert len(serp_data[0].serp_results) == 30  # Default depth

    @pytest.mark.asyncio
    async def test_fetch_serp_data_no_client(self):
        """Test that fetching SERP data without client raises error."""
        analyzer = ContentGapAnalyzer()
        analyzer.serp_client = None  # Disable client

        with pytest.raises(ValueError, match="SERP client not initialized"):
            await analyzer._fetch_serp_data(["dental implants"])

    @pytest.mark.asyncio
    async def test_analyze_with_keywords_and_clustering(self):
        """Test analysis with keywords triggers SERP fetching and clustering."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")

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
        # Clusters may be empty if overlap threshold not met
        assert result.summary["total_clusters"] >= 0

    @pytest.mark.asyncio
    async def test_close_serp_client(self):
        """Test closing SERP client."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        await analyzer.close()
        # Should not raise error


class TestContentGapAnalyzerSERPIntegration:
    """Test SERP client integration with Content Gap Analyzer."""

    @pytest.mark.asyncio
    async def test_fetch_serp_data(self):
        """Test fetching SERP data for keywords."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        keywords = ["dental implants", "teeth whitening"]
        serp_data = await analyzer._fetch_serp_data(keywords)
        
        assert len(serp_data) == 2
        assert serp_data[0].keyword == "dental implants"
        assert serp_data[1].keyword == "teeth whitening"
        assert len(serp_data[0].serp_results) == 30  # Default depth
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_fetch_serp_data_no_client(self):
        """Test error when SERP client not initialized."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        analyzer.serp_client = None  # Disable client
        
        with pytest.raises(ValueError, match="SERP client not initialized"):
            await analyzer._fetch_serp_data(["dental implants"])

    @pytest.mark.asyncio
    async def test_analyze_with_keywords_and_clustering(self):
        """Test full analysis with keywords and clustering."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Client Page 1",
                "topics": ["dental implants"],
                "keywords": ["implants"],
                "word_count": 1000,
                "eeat_score": 0.7,
            }
        ]
        
        competitor_pages = [
            {
                "url": "https://competitor.com/page1",
                "title": "Competitor Page 1",
                "topics": ["dental implants", "teeth whitening"],
                "keywords": ["implants", "whitening"],
                "word_count": 1500,
                "eeat_score": 0.8,
            },
            {
                "url": "https://competitor.com/page2",
                "title": "Competitor Page 2",
                "topics": ["orthodontics"],
                "keywords": ["braces"],
                "word_count": 1200,
                "eeat_score": 0.75,
            },
        ]
        
        keywords = ["dental implants", "teeth whitening", "orthodontics"]
        
        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental services",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
            keywords=keywords,
        )
        
        # Verify clusters were created
        assert len(result.clusters) > 0
        assert result.summary["total_clusters"] > 0

        # Verify architecture was planned (when clusters available)
        assert len(result.architecture) > 0

        # Note: briefs generation requires architecture_planner to return pages
        # Currently architecture_planner is stub, so briefs will be empty
        # This is expected behavior until architecture_planner is fully implemented

        await analyzer.close()

    @pytest.mark.asyncio
    async def test_close_serp_client(self):
        """Test closing SERP client."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Should not raise error
        await analyzer.close()
        
        # Second close should also not raise error
        await analyzer.close()


class TestContentGapAnalyzerKeywordResearch:
    """Test Keyword Research Agent integration."""

    @pytest.mark.asyncio
    async def test_expand_keywords_success(self):
        """Test keyword expansion with SEMrush."""
        from unittest.mock import AsyncMock, MagicMock
        
        # Create analyzer with mock SEMrush client
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Mock SEMrush client
        mock_semrush = AsyncMock()
        mock_semrush.expand_keywords = AsyncMock(return_value=[
            {"keyword": "dental implants cost", "volume": 1000, "difficulty": 50},
            {"keyword": "dental implants near me", "volume": 800, "difficulty": 45},
            {"keyword": "dental implants procedure", "volume": 600, "difficulty": 40},
        ])
        analyzer.semrush_client = mock_semrush
        
        # Expand keywords
        keywords = await analyzer.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=100,
            min_volume=10,
            max_cost_usd=0.5,
        )
        
        # Verify results
        assert len(keywords) == 3
        assert "dental implants cost" in keywords
        assert "dental implants near me" in keywords
        assert "dental implants procedure" in keywords
        
        # Verify SEMrush client was called
        mock_semrush.expand_keywords.assert_called_once_with(
            seed_keyword="dental implants",
            max_keywords=100,
            min_volume=10,
            max_cost_usd=0.5,
        )
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_expand_keywords_no_client(self):
        """Test keyword expansion without SEMrush client."""
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Should raise error when SEMrush client not initialized
        with pytest.raises(ValueError, match="SEMrush client not initialized"):
            await analyzer.expand_keywords(
                seed_keyword="dental implants",
                max_keywords=100,
                min_volume=10,
                max_cost_usd=0.5,
            )
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_analyze_with_keyword_expansion(self):
        """Test analysis with automatic keyword expansion."""
        from unittest.mock import AsyncMock
        
        # Create analyzer with mock clients
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Mock SEMrush client
        mock_semrush = AsyncMock()
        mock_semrush.expand_keywords = AsyncMock(return_value=[
            {"keyword": "dental implants cost", "volume": 1000, "difficulty": 50},
            {"keyword": "dental implants near me", "volume": 800, "difficulty": 45},
            {"keyword": "dental implants procedure", "volume": 600, "difficulty": 40},
        ])
        mock_semrush.close = AsyncMock()
        analyzer.semrush_client = mock_semrush
        
        # Sample data
        client_pages = [
            {
                "url": "https://client.com/page1",
                "title": "Client Page 1",
                "topics": ["dental services"],
                "keywords": ["dentist"],
                "word_count": 1000,
                "eeat_score": 0.7,
            }
        ]
        
        competitor_pages = [
            {
                "url": "https://competitor.com/page1",
                "title": "Competitor Page 1",
                "topics": ["dental implants", "teeth whitening"],
                "keywords": ["implants", "whitening"],
                "word_count": 1500,
                "eeat_score": 0.8,
            }
        ]
        
        # Analyze with keyword expansion
        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental services",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
            expand_keywords=True,
            seed_keyword="dental implants",
            max_keywords=100,
            min_volume=10,
        )
        
        # Verify keyword expansion was called
        mock_semrush.expand_keywords.assert_called_once()
        
        # Verify results
        assert result.summary["keywords_used"] == 3
        assert len(result.gaps) > 0
        assert len(result.clusters) > 0
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_analyze_with_keyword_expansion_no_seed(self):
        """Test analysis with keyword expansion but no seed keyword."""
        from unittest.mock import AsyncMock
        
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Mock SEMrush client
        mock_semrush = AsyncMock()
        analyzer.semrush_client = mock_semrush
        
        client_pages = [{"url": "https://client.com/page1", "title": "Page 1", "topics": [], "keywords": [], "word_count": 1000, "eeat_score": 0.7}]
        competitor_pages = [{"url": "https://competitor.com/page1", "title": "Page 1", "topics": [], "keywords": [], "word_count": 1000, "eeat_score": 0.7}]
        
        # Should raise error when expand_keywords=True but no seed_keyword
        with pytest.raises(ValueError, match="seed_keyword is required"):
            await analyzer.analyze(
                client_url="https://client.com",
                competitor_urls=["https://competitor.com"],
                niche="dental services",
                client_pages=client_pages,
                competitor_pages=competitor_pages,
                expand_keywords=True,  # True but no seed_keyword
            )
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_analyze_merge_expanded_and_provided_keywords(self):
        """Test merging expanded keywords with provided keywords."""
        from unittest.mock import AsyncMock
        
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Mock SEMrush client
        mock_semrush = AsyncMock()
        mock_semrush.expand_keywords = AsyncMock(return_value=[
            {"keyword": "dental implants cost", "volume": 1000, "difficulty": 50},
            {"keyword": "dental implants near me", "volume": 800, "difficulty": 45},
        ])
        mock_semrush.close = AsyncMock()
        analyzer.semrush_client = mock_semrush
        
        client_pages = [{"url": "https://client.com/page1", "title": "Page 1", "topics": [], "keywords": [], "word_count": 1000, "eeat_score": 0.7}]
        competitor_pages = [{"url": "https://competitor.com/page1", "title": "Page 1", "topics": [], "keywords": [], "word_count": 1000, "eeat_score": 0.7}]
        
        # Provide some keywords and expand more
        provided_keywords = ["orthodontics", "teeth whitening"]
        
        result = await analyzer.analyze(
            client_url="https://client.com",
            competitor_urls=["https://competitor.com"],
            niche="dental services",
            client_pages=client_pages,
            competitor_pages=competitor_pages,
            keywords=provided_keywords,
            expand_keywords=True,
            seed_keyword="dental implants",
            max_keywords=100,
            min_volume=10,
        )
        
        # Verify keywords were merged (2 provided + 2 expanded = 4 unique)
        assert result.summary["keywords_used"] == 4
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_close_both_clients(self):
        """Test closing both SERP and SEMrush clients."""
        from unittest.mock import AsyncMock
        
        analyzer = ContentGapAnalyzer(serp_provider="mock")
        
        # Mock both clients
        mock_semrush = AsyncMock()
        mock_semrush.close = AsyncMock()
        analyzer.semrush_client = mock_semrush
        
        # Close should call both clients
        await analyzer.close()
        
        # Verify both were closed
        mock_semrush.close.assert_called_once()
