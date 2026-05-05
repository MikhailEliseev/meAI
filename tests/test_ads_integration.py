"""Integration test for Ads Magister + Ads Campaign Creator Agent

Tests the complete Ads domain workflow:
- Ads Magister coordinates campaign creation
- Campaign Creator Agent executes
- Magister aggregates results
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.magisters.ads_magister import AdsMagister
from AIM.src.aim.subagents.ads_campaign_creator_agent import AdsCampaignCreatorAgent
from meai.agents.base_agent import Task, TaskStatus
from datetime import datetime, timezone


class TestAdsIntegration:
    """Integration tests for Ads domain"""

    @pytest.mark.asyncio
    async def test_ads_magister_campaign_creator_flow(self):
        """Test complete Ads workflow: Magister → Campaign Creator → Aggregation"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_ads_integration.db"

        # Initialize components
        magister = AdsMagister(magister_id="test-ads-magister", database_url=database_url)
        agent = AdsCampaignCreatorAgent(agent_id="ads-campaign-creator-agent", database_url=database_url)

        await magister.initialize()
        await agent.initialize()

        try:
            print("\n🎯 INTEGRATION TEST: Ads Domain\n")
            print("Scenario: Dental clinic needs advertising campaign\n")

            # Step 1: Magister identifies which subagents to use
            print("1️⃣ Ads Magister identifies subagents:")
            subagents = await magister.identify_subagents("create_campaign")
            print(f"   → Identified: {subagents}")
            assert "ads-campaign-creator-agent" in subagents

            # Step 2: Subagent executes task
            print("\n2️⃣ Campaign Creator Agent creates campaign:")
            task = Task(
                task_id="ads-integration-1",
                subtask_id="ads-integration-sub-1",
                parent_task_id="parent-1",
                action="create_campaign",
                description="dental implants Moscow budget 10000",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await agent.execute_task(task)
            print(f"   ✅ Campaign created: {result.result['campaign_name']}")
            print(f"   ✅ Ad Groups: {len(result.result['ad_groups'])}")
            print(f"   ✅ Budget: {result.result['budget']['total_daily']} RUB")

            # Step 3: Magister aggregates results
            print("\n3️⃣ Ads Magister aggregates results:")
            aggregated = await magister.aggregate_results([result.result])

            print(f"\n📊 Aggregated Results:")
            print(f"   Summary: {aggregated['summary']}")
            print(f"\n   Metrics:")
            for key, value in aggregated['metrics'].items():
                print(f"      {key}: {value}")

            print(f"\n   💡 Insights: {len(aggregated['insights'])}")
            for i, insight in enumerate(aggregated['insights'], 1):
                print(f"      {i}. {insight}")

            print(f"\n   🎯 Recommendations: {len(aggregated['recommendations'])}")
            for i, rec in enumerate(aggregated['recommendations'], 1):
                print(f"      {i}. {rec}")

            # Validate aggregation
            assert "summary" in aggregated
            assert "metrics" in aggregated
            assert "insights" in aggregated
            assert "recommendations" in aggregated

            # Validate metrics
            metrics = aggregated['metrics']
            assert metrics['total_campaigns'] == 1
            assert metrics['total_ad_groups'] == 3
            assert metrics['total_budget'] == 10000

            print("\n✅ COMPLETE ADS WORKFLOW VALIDATED!\n")

        finally:
            await magister.shutdown()
            await agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
