"""Real SEO Magister Test - Full coordination with business logic

Tests the complete flow with REAL logic:
SEO Magister → Keyword Research Agent → Aggregated Results

This validates that SEO Magister can:
1. Identify correct subagents based on action
2. Coordinate with Keyword Research Agent
3. Aggregate results with real analysis
4. Generate actionable insights
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.magisters.seo_magister import SEOMagister
from AIM.src.aim.subagents.keyword_research_agent import KeywordResearchAgent
from meai.agents.base_agent import Task, TaskStatus
from datetime import datetime, timezone


class TestSEOMagisterReal:
    """Real SEO Magister coordination tests"""

    @pytest.mark.asyncio
    async def test_identify_subagents_keyword_research(self):
        """Test SEO Magister identifies correct agent for keyword research"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_seo_real.db"

        seo_magister = SEOMagister(
            magister_id="test-seo-magister",
            database_url=database_url,
        )

        await seo_magister.initialize()

        try:
            # Test keyword research action
            subagents = await seo_magister.identify_subagents("keyword_research")
            assert subagents == ["keyword-research-agent"]

            # Test with "keyword" in action
            subagents = await seo_magister.identify_subagents("analyze keywords for dental clinic")
            assert subagents == ["keyword-research-agent"]

            print("\n✅ identify_subagents() works correctly!")

        finally:
            await seo_magister.shutdown()

    @pytest.mark.asyncio
    async def test_aggregate_results_real_keywords(self):
        """Test SEO Magister aggregates real keyword research results"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_seo_real.db"

        seo_magister = SEOMagister(
            magister_id="test-seo-magister",
            database_url=database_url,
        )

        keyword_agent = KeywordResearchAgent(
            agent_id="test-keyword-agent",
            database_url=database_url,
        )

        await seo_magister.initialize()
        await keyword_agent.initialize()

        try:
            # Step 1: Get real keyword research results
            task = Task(
                task_id="test-task-1",
                subtask_id="test-subtask-1",
                parent_task_id="test-parent-1",
                action="keyword_research",
                description='Research keywords for "dental implants"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await keyword_agent.execute_task(task)
            assert result.status == "success"

            # Step 2: Aggregate results through SEO Magister
            aggregated = await seo_magister.aggregate_results([result.result])

            # Validate aggregation
            assert "summary" in aggregated
            assert "insights" in aggregated
            assert "recommendations" in aggregated
            assert "metrics" in aggregated
            assert "top_opportunities" in aggregated

            # Check metrics
            metrics = aggregated["metrics"]
            assert metrics["total_keywords"] > 0
            assert metrics["opportunities"] >= 0
            assert "intent_distribution" in metrics

            # Check insights are real (not mocks)
            assert len(aggregated["insights"]) > 0
            assert "Mock" not in aggregated["summary"]

            print("\n✅ aggregate_results() works with real data!")
            print(f"\n📊 Aggregated Results:")
            print(f"   Summary: {aggregated['summary']}")
            print(f"   Insights: {len(aggregated['insights'])} insights")
            print(f"   Recommendations: {len(aggregated['recommendations'])} recommendations")
            print(f"   Top Opportunities: {len(aggregated['top_opportunities'])} keywords")

        finally:
            await seo_magister.shutdown()
            await keyword_agent.shutdown()

    @pytest.mark.asyncio
    async def test_full_coordination_flow(self):
        """Test complete flow: SEO Magister coordinates Keyword Research Agent

        This is the REAL end-to-end test with business logic:
        1. SEO Magister receives SEO task
        2. Identifies Keyword Research Agent
        3. Agent executes with real SEO logic
        4. Magister aggregates with real analysis
        5. Returns actionable insights
        """
        database_url = "sqlite+aiosqlite:///./AIM/data/test_seo_real.db"

        seo_magister = SEOMagister(
            magister_id="test-seo-magister",
            database_url=database_url,
        )

        keyword_agent = KeywordResearchAgent(
            agent_id="keyword-research-agent",  # Real agent ID
            database_url=database_url,
        )

        await seo_magister.initialize()
        await keyword_agent.initialize()

        try:
            # Step 1: SEO Magister identifies subagents
            action = "keyword_research"
            subagents = await seo_magister.identify_subagents(action)
            assert "keyword-research-agent" in subagents

            # Step 2: Execute keyword research
            task = Task(
                task_id="test-task-full",
                subtask_id="test-subtask-full",
                parent_task_id="test-parent-full",
                action="keyword_research",
                description='Research keywords for "cosmetic dentistry"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await keyword_agent.execute_task(task)
            assert result.status == "success"

            # Step 3: Aggregate results
            aggregated = await seo_magister.aggregate_results([result.result])

            # Validate full flow
            assert aggregated["metrics"]["total_keywords"] > 0
            assert len(aggregated["insights"]) > 0
            assert len(aggregated["recommendations"]) > 0
            assert len(aggregated["top_opportunities"]) > 0

            print("\n✅ FULL COORDINATION FLOW PASSED!")
            print(f"\n🎯 SEO Task: Research keywords for 'cosmetic dentistry'")
            print(f"\n📊 Results:")
            print(f"   - Identified subagents: {subagents}")
            print(f"   - Keywords analyzed: {aggregated['metrics']['total_keywords']}")
            print(f"   - Opportunities found: {aggregated['metrics']['opportunities']}")
            print(f"   - Insights generated: {len(aggregated['insights'])}")
            print(f"   - Recommendations: {len(aggregated['recommendations'])}")
            print(f"\n💡 Top Recommendation:")
            if aggregated["recommendations"]:
                print(f"   {aggregated['recommendations'][0]}")

        finally:
            await seo_magister.shutdown()
            await keyword_agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
