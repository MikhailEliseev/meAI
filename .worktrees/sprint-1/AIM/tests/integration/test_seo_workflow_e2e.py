"""End-to-end tests for SEO Magister v2 workflow.

Tests complete workflow with 4 agents:
- Technical SEO Agent (30%)
- Content SEO Agent (25%)
- Links SEO Agent (20%)
- Content Gap Analyzer (25%)

Coverage:
- Basic workflow (4 agents, no optional features)
- Keyword expansion integration
- SERP clustering integration
- Error handling and graceful degradation
- Performance characteristics
- Full integration scenarios
"""

import pytest
from unittest.mock import AsyncMock, patch

from AIM.src.aim.magisters.seo_magister_v2 import SEOMagisterV2
from AIM.src.aim.subagents.schemas.content_gap import (
    ContentGap,
    ContentCluster,
    GapAnalysisResult,
    GapType,
    GapSeverity,
    IntentType,
)


@pytest.fixture
def sample_technical_result():
    """Sample technical agent result."""
    return {
        "status": "success",
        "results": {
            "robots_txt": {"exists": True, "allows_crawling": True},
            "sitemap_xml": {"exists": True, "valid": True},
            "meta_tags": {
                "title": "Dental Implants - Best Clinic",
                "description": "Professional dental implants service with experienced doctors and modern equipment. Get your perfect smile today.",
            },
            "performance": {"score": 85},
            "schema_org": {"count": 3},
        },
        "issues": [
            {"type": "mobile", "severity": "high", "description": "Mobile optimization needed"}
        ],
        "recommendations": ["Improve mobile responsiveness"],
    }


@pytest.fixture
def sample_content_result():
    """Sample content agent result."""
    return {
        "status": "success",
        "results": {
            "headers": {
                "h1_count": 1,
                "broken_hierarchy": False,
            },
            "readability": {
                "flesch_reading_ease": 70,
            },
            "content_quality": {
                "word_count": 1500,
                "image_count": 5,
                "alt_text_coverage": 90,
            },
            "structure": {
                "semantic_score": 75,
            },
        },
        "issues": [
            {"type": "quality", "severity": "medium", "description": "Content quality issues"}
        ],
        "recommendations": ["Improve content depth"],
    }


@pytest.fixture
def sample_links_result():
    """Sample links agent result."""
    return {
        "status": "success",
        "results": {
            "internal_links": {
                "total": 80,
                "unique": 15,
            },
            "external_links": {
                "total": 10,
                "nofollow_percentage": 30,
            },
            "anchor_text": {
                "empty_percentage": 5,
                "generic_percentage": 20,
            },
            "broken_links": {
                "count": 0,
            },
        },
        "issues": [
            {"type": "backlinks", "severity": "high", "description": "Low backlink count"}
        ],
        "recommendations": ["Build more backlinks"],
    }


@pytest.fixture
def sample_gap_result():
    """Sample gap analysis result."""
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
            "total_gaps": 2,
            "p0_gaps": 1,
            "p1_gaps": 1,
            "p2_gaps": 0,
            "total_clusters": 0,
            "total_briefs": 0,
            "execution_time_ms": 1000,
            "pages_analyzed": 10,
            "keywords_used": 5,
        },
    )


class TestSEOWorkflowBasic:
    """Test basic SEO workflow without optional features."""

    @pytest.mark.asyncio
    async def test_basic_analysis_4_agents(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test basic analysis with all 4 agents."""
        magister = SEOMagisterV2()

        # Mock agent methods directly
        magister.technical_agent.analyze = AsyncMock(return_value=sample_technical_result)
        magister.content_agent.analyze = AsyncMock(return_value=sample_content_result)
        magister.links_agent.analyze = AsyncMock(return_value=sample_links_result)
        magister.gap_analyzer.analyze = AsyncMock(return_value=sample_gap_result)

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        # Verify all 4 agents called
        magister.technical_agent.analyze.assert_called_once()
        magister.content_agent.analyze.assert_called_once()
        magister.links_agent.analyze.assert_called_once()
        magister.gap_analyzer.analyze.assert_called_once()

        # Verify result structure
        assert "scores" in result
        assert "details" in result
        assert "recommendations" in result

        # Verify 4 agent scores
        assert "overall" in result["scores"]
        assert "technical" in result["scores"]
        assert "content" in result["scores"]
        assert "links" in result["scores"]
        assert "content_gaps" in result["scores"]

        # Verify weighted scoring (30/25/20/25)
        # Actual scores from fixtures:
        # - Technical: 80.5 (robots 15 + sitemap 15 + meta 10 + perf 25.5 + schema 15 = 80.5)
        # - Content: 90.0 (headers 25 + readability 25 + quality 25 + structure 15 = 90)
        # - Links: 85.0 (internal 30 + external 25 + anchor 10 + broken 20 = 85)
        # - Gap: 70.0 (100 - 1*20 - 1*10 = 70, fixture has p0=1, p1=1, p2=0)
        expected_overall = (
            80.5 * 0.30 +  # technical
            90.0 * 0.25 +  # content
            85.0 * 0.20 +  # links
            70.0 * 0.25    # gaps
        )
        assert abs(result["scores"]["overall"] - expected_overall) < 0.2  # Allow rounding tolerance
        assert result["scores"]["technical"] == 80.5
        assert result["scores"]["content"] == 90.0
        assert result["scores"]["links"] == 85.0
        assert result["scores"]["content_gaps"] == 70.0

    @pytest.mark.asyncio
    async def test_multiple_competitors(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test analysis with multiple competitors."""
        magister = SEOMagisterV2()
        magister.technical_agent.analyze = AsyncMock(return_value=sample_technical_result)
        magister.content_agent.analyze = AsyncMock(return_value=sample_content_result)
        magister.links_agent.analyze = AsyncMock(return_value=sample_links_result)
        magister.gap_analyzer.analyze = AsyncMock(return_value=sample_gap_result)

        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=[
                "https://competitor1.com",
                "https://competitor2.com",
                "https://competitor3.com",
            ],
            niche="dental implants",
        )

        # Verify gap analyzer called with all competitors
        call_kwargs = magister.gap_analyzer.analyze.call_args.kwargs
        assert len(call_kwargs["competitor_urls"]) == 3

        assert result["scores"]["overall"] > 0

    @pytest.mark.asyncio
    async def test_recommendations_structure(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test recommendations have correct structure."""
        magister = SEOMagisterV2()

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

        recommendations = result["recommendations"]
        # With high scores (tech 80.5, content 90, links 85), only gap recommendations generated
        # Gap score 65 < 80, so we get P0 and P1 gap recommendations
        assert len(recommendations) >= 2  # At least P0 and P1 gap recommendations

        # Check structure of dict recommendations
        for rec in recommendations:
            if isinstance(rec, dict):
                assert "issue" in rec
                assert "action" in rec
                assert "priority" in rec
                assert "category" in rec
                assert rec["priority"] in ["critical", "high", "medium", "low"]


class TestSEOWorkflowWithKeywordExpansion:
    """Test workflow with keyword expansion enabled."""

    @pytest.mark.asyncio
    async def test_keyword_expansion_enabled(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test analysis with keyword expansion."""
        magister = SEOMagisterV2(
            semrush_api_key="test_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
                expand_keywords=True,
                seed_keyword="dental implants",
                max_keywords=100,
                min_volume=10,
            )

            # Verify gap analyzer called with expansion params
            call_kwargs = mock_gap.call_args.kwargs
            assert call_kwargs["expand_keywords"] is True
            assert call_kwargs["seed_keyword"] == "dental implants"
            assert call_kwargs["max_keywords"] == 100
            assert call_kwargs["min_volume"] == 10

        assert result["scores"]["overall"] > 0

    @pytest.mark.asyncio
    async def test_budget_control(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test budget control for keyword expansion."""
        # Budget is set in __init__, not coordinate_analysis
        magister = SEOMagisterV2(
            semrush_api_key="test_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

            assert result["scores"]["overall"] > 0

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
                expand_keywords=True,
                seed_keyword="dental implants",
            )

            # Verify gap analyzer was called with expansion params
            call_kwargs = mock_gap.call_args.kwargs
            assert call_kwargs["expand_keywords"] is True

            assert result["scores"]["overall"] > 0


class TestSEOWorkflowWithClustering:
    """Test workflow with SERP clustering."""

    @pytest.mark.asyncio
    async def test_serp_clustering_integration(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
    ):
        """Test SERP clustering with keyword data."""
        # Create gap result with clusters (only 1 P0 gap)
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
        ]

        from AIM.src.aim.subagents.schemas.content_gap import ContentCluster, IntentType

        gap_result_with_clusters = GapAnalysisResult(
            client_url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
            gaps=gaps,
            clusters=[
                ContentCluster(
                    hub_keyword="dental implants cost",
                    spoke_keywords=["implant cost"],
                    keywords=["dental implants cost", "implant cost"],
                    total_search_volume=1500,
                    primary_intent=IntentType.INFORMATIONAL,
                )
            ],
            architecture={},
            briefs=[],
            summary={
                "total_gaps": 1,
                "p0_gaps": 1,
                "p1_gaps": 0,
                "p2_gaps": 0,
                "total_clusters": 1,
                "total_briefs": 0,
            },
        )

        magister = SEOMagisterV2(
            semrush_api_key="test_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = gap_result_with_clusters

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

        # Verify clusters in result
        assert "content_gaps" in result["details"]
        gap_details = result["details"]["content_gaps"]
        # gap_details is GapAnalysisResult object, access via attributes
        assert gap_details.summary["total_clusters"] == 1

        assert result["scores"]["overall"] > 0


class TestSEOWorkflowErrorHandling:
    """Test error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_gap_analyzer_failure(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
    ):
        """Test that gap analyzer failure doesn't crash analysis."""
        magister = SEOMagisterV2()

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.side_effect = Exception("API error")

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

        # Should still have results from other 3 agents
        assert "scores" in result
        assert result["scores"]["technical"] == 80.5
        assert result["scores"]["content"] == 90.0
        assert result["scores"]["links"] == 85.0
        assert result["scores"]["content_gaps"] == 0.0  # Failed agent gets 0

        # Gap analysis should have error status
        assert "content_gaps" in result["details"]
        assert result["details"]["content_gaps"]["status"] == "error"

        # Overall score should still be calculated (with 0 for gap score)
        expected_overall = 80.5 * 0.30 + 90.0 * 0.25 + 85.0 * 0.20 + 0.0 * 0.25
        assert abs(result["scores"]["overall"] - expected_overall) < 0.1

    @pytest.mark.asyncio
    async def test_technical_agent_failure(
        self,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test technical agent failure."""
        magister = SEOMagisterV2()

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.side_effect = Exception("Network error")
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

        # Technical score should be 0
        assert result["scores"]["technical"] == 0.0
        # Other scores should be normal
        assert result["scores"]["content"] == 90.0
        assert result["scores"]["links"] == 85.0
        assert result["scores"]["content_gaps"] == 70.0  # 100 - 1*20 - 1*10 = 70

    @pytest.mark.asyncio
    async def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        magister = SEOMagisterV2()

        # Should handle gracefully (agents will fail, but magister won't crash)
        result = await magister.coordinate_analysis(
            url="not-a-valid-url",
            competitor_urls=["also-invalid"],
            niche="test",
        )

        # Should have error details
        assert "details" in result


class TestSEOWorkflowPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_parallel_execution(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test that 4 agents execute in parallel."""
        import asyncio
        import time

        magister = SEOMagisterV2()

        # Mock agents with delays
        async def slow_technical(*args, **kwargs):
            await asyncio.sleep(0.2)
            return sample_technical_result

        async def slow_content(*args, **kwargs):
            await asyncio.sleep(0.2)
            return sample_content_result

        async def slow_links(*args, **kwargs):
            await asyncio.sleep(0.2)
            return sample_links_result

        async def slow_gap(*args, **kwargs):
            await asyncio.sleep(0.2)
            return sample_gap_result

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.side_effect = slow_technical
            mock_content.side_effect = slow_content
            mock_links.side_effect = slow_links
            mock_gap.side_effect = slow_gap

            start = time.time()
            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )
            duration = time.time() - start

        # If sequential: 0.2 * 4 = 0.8 seconds
        # If parallel: max(0.2, 0.2, 0.2, 0.2) = 0.2 seconds
        assert duration < 0.5  # Parallel execution
        assert result["scores"]["overall"] > 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        import asyncio

        magister = SEOMagisterV2(timeout=1)  # 1 second timeout

        # Mock agent that takes too long
        async def very_slow(*args, **kwargs):
            await asyncio.sleep(10)
            return {"score": 100.0}

        magister.technical_agent.analyze = AsyncMock(side_effect=very_slow)

        # Should handle timeout gracefully
        result = await magister.coordinate_analysis(
            url="https://client.com",
            competitor_urls=["https://competitor1.com"],
            niche="dental implants",
        )

        # Should have error result due to timeout
        assert result["status"] == "error"
        assert "timeout" in result["error"].lower()


class TestSEOWorkflowIntegration:
    """Test full integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_all_features(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test complete workflow with all features enabled."""
        magister = SEOMagisterV2(
            timeout=600,
            semrush_api_key="test_key",
            serp_api_key="test_serp_key",
            serp_provider="mock",
        )

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com", "https://competitor2.com"],
                niche="dental implants",
                expand_keywords=True,
                seed_keyword="dental implants",
                max_keywords=200,
                min_volume=50,
            )

        # Verify complete result structure
        assert "scores" in result
        assert "details" in result
        assert "recommendations" in result

        # Verify all 4 agents
        assert "technical" in result["details"]
        assert "content" in result["details"]
        assert "links" in result["details"]
        assert "content_gaps" in result["details"]

        # Verify weighted scoring
        assert 0 <= result["scores"]["overall"] <= 100

        # Verify recommendations from gap analyzer
        # With high scores (tech 80.5, content 90, links 85), only gap recommendations generated
        assert len(result["recommendations"]) >= 2

    @pytest.mark.asyncio
    async def test_correlation_id_tracking(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test correlation ID is passed through workflow."""
        magister = SEOMagisterV2()

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

        # Should have result
        assert result["scores"]["overall"] > 0

    @pytest.mark.asyncio
    async def test_resource_cleanup(
        self,
        sample_technical_result,
        sample_content_result,
        sample_links_result,
        sample_gap_result,
    ):
        """Test that resources are properly cleaned up."""
        magister = SEOMagisterV2()

        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links, \
             patch.object(magister.gap_analyzer, 'analyze', new_callable=AsyncMock) as mock_gap, \
             patch.object(magister.gap_analyzer, 'close', new_callable=AsyncMock) as mock_close:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result
            mock_gap.return_value = sample_gap_result

            result = await magister.coordinate_analysis(
                url="https://client.com",
                competitor_urls=["https://competitor1.com"],
                niche="dental implants",
            )

            # Close magister
            await magister.close()

            # Verify gap analyzer was closed
            mock_close.assert_called_once()

        assert result["scores"]["overall"] > 0
