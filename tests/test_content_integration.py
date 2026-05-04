"""Content Domain Integration Test - Full coordination

Tests complete flow:
Content Magister → Content Writer Agent → Aggregated Results
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.magisters.content_magister import ContentMagister
from AIM.src.aim.subagents.content_writer_agent import ContentWriterAgent
from meai.agents.base_agent import Task, TaskStatus
from datetime import datetime, timezone


class TestContentIntegration:
    """Content domain integration tests"""

    @pytest.mark.asyncio
    async def test_full_content_workflow(self):
        """Test complete flow: Content Magister → Content Writer Agent → Results

        This validates:
        1. Content Magister identifies Content Writer Agent
        2. Content Writer Agent generates content structure
        3. Content Magister aggregates results with analysis
        4. Full workflow produces actionable insights
        """
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content_integration.db"

        content_magister = ContentMagister(
            magister_id="test-content-magister",
            database_url=database_url,
        )

        content_writer = ContentWriterAgent(
            agent_id="content-writer-agent",
            database_url=database_url,
        )

        await content_magister.initialize()
        await content_writer.initialize()

        try:
            print("\n🎯 CONTENT WORKFLOW TEST\n")

            # Step 1: Content Magister identifies subagents
            print("📥 Step 1: Content Magister receives task")
            action = "create_article"
            subagents = await content_magister.identify_subagents(action)
            print(f"   → Identified: {subagents}")
            assert "content-writer-agent" in subagents

            # Step 2: Content Writer Agent executes
            print("⚙️  Step 2: Content Writer Agent generates content")
            task = Task(
                task_id="test-task-1",
                subtask_id="test-subtask-1",
                parent_task_id="test-parent-1",
                action="create_article",
                description='Create article about "cosmetic dentistry services"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await content_writer.execute_task(task)
            assert result.status == "success"
            print(f"   → Generated: {result.result['word_count']} words")
            print(f"   → Quality: {result.result['quality_score']}/100")

            # Step 3: Content Magister aggregates
            print("📊 Step 3: Content Magister aggregates results")
            aggregated = await content_magister.aggregate_results([result.result])

            # Validate aggregation
            assert "summary" in aggregated
            assert "insights" in aggregated
            assert "recommendations" in aggregated
            assert "metrics" in aggregated

            print("\n✅ FULL WORKFLOW COMPLETED!\n")
            print("📋 AGGREGATED RESULTS:\n")
            print(f"Summary: {aggregated['summary']}\n")
            print("💡 Insights:")
            for i, insight in enumerate(aggregated['insights'], 1):
                print(f"   {i}. {insight}")
            print("\n🎯 Recommendations:")
            for i, rec in enumerate(aggregated['recommendations'], 1):
                print(f"   {i}. {rec}")
            print(f"\n📈 Metrics:")
            print(f"   - Content pieces: {aggregated['metrics']['total_content_pieces']}")
            print(f"   - Avg quality: {aggregated['metrics']['avg_quality']}")
            print(f"   - Avg readability: {aggregated['metrics']['avg_readability']}")
            print(f"   - Avg SEO: {aggregated['metrics']['avg_seo']}")

        finally:
            await content_magister.shutdown()
            await content_writer.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
