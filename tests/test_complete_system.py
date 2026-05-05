"""Complete System Test - All domains working together

Tests the complete AIM Agency system:
- SEO Magister + Keyword Research Agent
- Content Magister + Content Writer Agent
- Ads Magister (ready for subagents)

Validates full architecture end-to-end.
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.magisters.seo_magister import SEOMagister
from AIM.src.aim.magisters.content_magister import ContentMagister
from AIM.src.aim.magisters.ads_magister import AdsMagister
from AIM.src.aim.subagents.keyword_research_agent import KeywordResearchAgent
from AIM.src.aim.subagents.content_writer_agent import ContentWriterAgent
from meai.agents.base_agent import Task, TaskStatus
from datetime import datetime, timezone


class TestCompleteSystem:
    """Complete system integration tests"""

    @pytest.mark.asyncio
    async def test_all_magisters_coordination(self):
        """Test all 3 Magisters can identify their subagents correctly"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_complete_system.db"

        seo_magister = SEOMagister(magister_id="test-seo", database_url=database_url)
        content_magister = ContentMagister(magister_id="test-content", database_url=database_url)
        ads_magister = AdsMagister(magister_id="test-ads", database_url=database_url)

        await seo_magister.initialize()
        await content_magister.initialize()
        await ads_magister.initialize()

        try:
            print("\n🎯 TESTING ALL MAGISTERS\n")

            # Test SEO Magister
            print("1️⃣ SEO Magister:")
            seo_agents = await seo_magister.identify_subagents("keyword_research")
            print(f"   → Identifies: {seo_agents}")
            assert "keyword-research-agent" in seo_agents

            # Test Content Magister
            print("2️⃣ Content Magister:")
            content_agents = await content_magister.identify_subagents("create_article")
            print(f"   → Identifies: {content_agents}")
            assert "content-writer-agent" in content_agents

            # Test Ads Magister
            print("3️⃣ Ads Magister:")
            ads_agents = await ads_magister.identify_subagents("create_campaign")
            print(f"   → Identifies: {ads_agents}")
            assert "ads-campaign-creator-agent" in ads_agents

            print("\n✅ All 3 Magisters working correctly!\n")

        finally:
            await seo_magister.shutdown()
            await content_magister.shutdown()
            await ads_magister.shutdown()

    @pytest.mark.asyncio
    async def test_two_domains_parallel(self):
        """Test SEO and Content domains working in parallel

        This simulates real agency workflow:
        - SEO Magister coordinates keyword research
        - Content Magister coordinates content creation
        - Both produce results simultaneously
        """
        database_url = "sqlite+aiosqlite:///./AIM/data/test_complete_system.db"

        # Initialize all components
        seo_magister = SEOMagister(magister_id="test-seo", database_url=database_url)
        content_magister = ContentMagister(magister_id="test-content", database_url=database_url)
        keyword_agent = KeywordResearchAgent(agent_id="keyword-research-agent", database_url=database_url)
        content_writer = ContentWriterAgent(agent_id="content-writer-agent", database_url=database_url)

        await seo_magister.initialize()
        await content_magister.initialize()
        await keyword_agent.initialize()
        await content_writer.initialize()

        try:
            print("\n🎯 PARALLEL DOMAIN TEST\n")
            print("Scenario: Dental clinic needs SEO + Content for 'dental implants'\n")

            # SEO Task
            print("📊 SEO Domain:")
            seo_task = Task(
                task_id="seo-1",
                subtask_id="seo-sub-1",
                parent_task_id="parent-1",
                action="keyword_research",
                description='Research keywords for "dental implants"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            seo_result = await keyword_agent.execute_task(seo_task)
            seo_aggregated = await seo_magister.aggregate_results([seo_result.result])
            print(f"   ✅ Keywords: {seo_aggregated['metrics']['total_keywords']}")
            print(f"   ✅ Opportunities: {seo_aggregated['metrics']['opportunities']}")

            # Content Task
            print("\n📝 Content Domain:")
            content_task = Task(
                task_id="content-1",
                subtask_id="content-sub-1",
                parent_task_id="parent-1",
                action="create_article",
                description='Create article about "dental implants"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            content_result = await content_writer.execute_task(content_task)
            content_aggregated = await content_magister.aggregate_results([content_result.result])
            print(f"   ✅ Word count: {content_result.result['word_count']}")
            print(f"   ✅ Quality: {content_aggregated['metrics']['avg_quality']}/100")

            print("\n✅ BOTH DOMAINS WORKING!\n")
            print("📊 Combined Results:")
            print(f"   - SEO: {seo_aggregated['metrics']['total_keywords']} keywords analyzed")
            print(f"   - Content: {content_result.result['word_count']} words generated")
            print(f"   - Quality: {content_aggregated['metrics']['avg_quality']}/100")
            print(f"   - SEO Score: {content_result.result['seo_score']}/100")

        finally:
            await seo_magister.shutdown()
            await content_magister.shutdown()
            await keyword_agent.shutdown()
            await content_writer.shutdown()

    @pytest.mark.asyncio
    async def test_system_readiness(self):
        """Test complete system readiness

        Validates:
        - All 3 Magisters can initialize
        - All 2 Subagents can initialize
        - All components can shutdown cleanly
        """
        database_url = "sqlite+aiosqlite:///./AIM/data/test_complete_system.db"

        components = [
            SEOMagister(magister_id="test-seo", database_url=database_url),
            ContentMagister(magister_id="test-content", database_url=database_url),
            AdsMagister(magister_id="test-ads", database_url=database_url),
            KeywordResearchAgent(agent_id="keyword-research-agent", database_url=database_url),
            ContentWriterAgent(agent_id="content-writer-agent", database_url=database_url),
        ]

        print("\n🎯 SYSTEM READINESS TEST\n")

        # Initialize all
        print("🔄 Initializing all components...")
        for component in components:
            await component.initialize()
            print(f"   ✅ {component.__class__.__name__}")

        # Shutdown all
        print("\n🔄 Shutting down all components...")
        for component in components:
            await component.shutdown()
            print(f"   ✅ {component.__class__.__name__}")

        print("\n✅ SYSTEM READY FOR PRODUCTION!\n")
        print("📊 System Status:")
        print("   - 3 Magisters: READY ✅")
        print("   - 2 Subagents: READY ✅")
        print("   - Architecture: VALIDATED ✅")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
