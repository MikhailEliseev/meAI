"""Content Magister Test - Coordination logic validation

Tests Content Magister coordination with mock subagent results.
Validates identify_subagents() and aggregate_results() logic.
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.magisters.content_magister import ContentMagister
from datetime import datetime, timezone


class TestContentMagister:
    """Content Magister coordination tests"""

    @pytest.mark.asyncio
    async def test_identify_subagents_create_article(self):
        """Test Content Magister identifies correct agent for article creation"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content.db"

        content_magister = ContentMagister(
            magister_id="test-content-magister",
            database_url=database_url,
        )

        await content_magister.initialize()

        try:
            # Test article creation
            subagents = await content_magister.identify_subagents("create_article")
            assert subagents == ["content-writer-agent"]

            # Test with "write" in action
            subagents = await content_magister.identify_subagents("write blog post about dental implants")
            assert subagents == ["content-writer-agent"]

            print("\n✅ identify_subagents() works correctly!")

        finally:
            await content_magister.shutdown()

    @pytest.mark.asyncio
    async def test_aggregate_results_mock_content(self):
        """Test Content Magister aggregates mock content results"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content.db"

        content_magister = ContentMagister(
            magister_id="test-content-magister",
            database_url=database_url,
        )

        await content_magister.initialize()

        try:
            # Mock content results
            mock_results = [
                {
                    "content_pieces": 3,
                    "content_type": "blog_post",
                    "quality_score": 85,
                    "readability_score": 75,
                    "seo_score": 80,
                },
                {
                    "content_pieces": 2,
                    "content_type": "article",
                    "quality_score": 90,
                    "readability_score": 80,
                    "seo_score": 85,
                },
            ]

            # Aggregate results
            aggregated = await content_magister.aggregate_results(mock_results)

            # Validate aggregation
            assert "summary" in aggregated
            assert "insights" in aggregated
            assert "recommendations" in aggregated
            assert "metrics" in aggregated

            # Check metrics
            metrics = aggregated["metrics"]
            assert metrics["total_content_pieces"] == 5
            assert metrics["avg_quality"] == 87.5
            assert metrics["avg_readability"] == 77.5
            assert metrics["avg_seo"] == 82.5

            # Check insights are real (not mocks)
            assert len(aggregated["insights"]) > 0
            assert "Mock" not in aggregated["summary"]

            print("\n✅ aggregate_results() works with mock data!")
            print(f"\n📊 Aggregated Results:")
            print(f"   Summary: {aggregated['summary']}")
            print(f"   Insights: {len(aggregated['insights'])} insights")
            print(f"   Recommendations: {len(aggregated['recommendations'])} recommendations")
            print(f"   Metrics: {metrics}")

        finally:
            await content_magister.shutdown()

    @pytest.mark.asyncio
    async def test_full_coordination_flow(self):
        """Test complete flow: Content Magister coordination logic

        This validates:
        1. Content Magister identifies correct subagents
        2. Aggregates results with real analysis
        3. Generates actionable insights
        """
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content.db"

        content_magister = ContentMagister(
            magister_id="test-content-magister",
            database_url=database_url,
        )

        await content_magister.initialize()

        try:
            # Step 1: Identify subagents
            action = "create_article"
            subagents = await content_magister.identify_subagents(action)
            assert "content-writer-agent" in subagents

            # Step 2: Mock content creation results
            mock_results = [
                {
                    "content_pieces": 5,
                    "content_type": "medical_article",
                    "quality_score": 88,
                    "readability_score": 72,
                    "seo_score": 78,
                }
            ]

            # Step 3: Aggregate results
            aggregated = await content_magister.aggregate_results(mock_results)

            # Validate full flow
            assert aggregated["metrics"]["total_content_pieces"] == 5
            assert len(aggregated["insights"]) > 0
            assert len(aggregated["recommendations"]) > 0

            print("\n✅ FULL COORDINATION FLOW PASSED!")
            print(f"\n🎯 Content Task: Create medical articles")
            print(f"\n📊 Results:")
            print(f"   - Identified subagents: {subagents}")
            print(f"   - Content pieces: {aggregated['metrics']['total_content_pieces']}")
            print(f"   - Avg quality: {aggregated['metrics']['avg_quality']}")
            print(f"   - Insights generated: {len(aggregated['insights'])}")
            print(f"   - Recommendations: {len(aggregated['recommendations'])}")

        finally:
            await content_magister.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
