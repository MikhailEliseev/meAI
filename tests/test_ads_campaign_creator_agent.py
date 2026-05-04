"""Tests for Ads Campaign Creator Agent

Tests real advertising campaign creation logic:
- Campaign structure generation
- Ad copy generation
- Budget allocation
- Performance predictions
- Compliance checks
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.subagents.ads_campaign_creator_agent import AdsCampaignCreatorAgent
from meai.agents.base_agent import Task, TaskStatus
from datetime import datetime, timezone


class TestAdsCampaignCreatorAgent:
    """Test suite for Ads Campaign Creator Agent"""

    @pytest.mark.asyncio
    async def test_campaign_creation(self):
        """Test complete campaign creation with real logic"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_ads_agent.db"
        agent = AdsCampaignCreatorAgent(
            agent_id="ads-campaign-creator-agent",
            database_url=database_url
        )

        await agent.initialize()

        try:
            print("\n🎯 TEST: Campaign Creation\n")

            # Create task
            task = Task(
                task_id="ads-1",
                subtask_id="ads-sub-1",
                parent_task_id="parent-1",
                action="create_campaign",
                description="dental implants Moscow budget 5000",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            # Execute
            result = await agent.execute_task(task)

            # Validate result
            assert result.status == "success"
            assert "campaign_name" in result.result
            assert "ad_groups" in result.result
            assert "budget" in result.result
            assert "predictions" in result.result

            campaign = result.result

            print(f"📊 Campaign: {campaign['campaign_name']}")
            print(f"   Platform: {campaign['platform']}")
            print(f"   Specialty: {campaign['specialty']}")
            print(f"   Location: {campaign['location']}")
            print(f"   Daily Budget: {campaign['budget']['total_daily']} RUB")
            print(f"   Ad Groups: {len(campaign['ad_groups'])}")

            # Validate ad groups
            assert len(campaign['ad_groups']) == 3  # informational, commercial, transactional
            for ad_group in campaign['ad_groups']:
                assert "name" in ad_group
                assert "intent" in ad_group
                assert "keywords" in ad_group
                assert "ads" in ad_group
                assert len(ad_group['ads']) == 3  # 3 ads per group for A/B testing

            # Validate predictions
            predictions = campaign['predictions']
            assert predictions['estimated_clicks'] > 0
            assert predictions['estimated_impressions'] > 0
            assert predictions['estimated_conversions'] > 0
            assert predictions['estimated_cpa'] > 0

            print(f"\n📈 Predictions:")
            print(f"   Impressions: {predictions['estimated_impressions']:,}")
            print(f"   Clicks: {predictions['estimated_clicks']:,}")
            print(f"   Conversions: {predictions['estimated_conversions']}")
            print(f"   CTR: {predictions['estimated_ctr']}%")
            print(f"   Conversion Rate: {predictions['estimated_conversion_rate']}%")
            print(f"   CPA: {predictions['estimated_cpa']} RUB")
            print(f"   ROAS: {predictions['estimated_roas']}")

            print("\n✅ Campaign creation working!\n")

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_ad_structure_details(self):
        """Test ad structure generation details"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_ads_agent.db"
        agent = AdsCampaignCreatorAgent(
            agent_id="ads-campaign-creator-agent",
            database_url=database_url
        )

        await agent.initialize()

        try:
            print("\n🎯 TEST: Ad Structure Details\n")

            task = Task(
                task_id="ads-2",
                subtask_id="ads-sub-2",
                parent_task_id="parent-1",
                action="create_campaign",
                description="plastic surgery rhinoplasty Moscow budget 10000",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await agent.execute_task(task)
            campaign = result.result

            print(f"📊 Campaign: {campaign['campaign_name']}")
            print(f"   Specialty: {campaign['specialty']}")
            print(f"   Compliance Level: {campaign['compliance_level']}")

            # Check first ad group
            ad_group = campaign['ad_groups'][0]
            print(f"\n📝 Ad Group: {ad_group['name']}")
            print(f"   Intent: {ad_group['intent']}")
            print(f"   Keywords: {len(ad_group['keywords'])}")
            print(f"   Max CPC: {ad_group['max_cpc']} RUB")

            # Check first ad
            ad = ad_group['ads'][0]
            print(f"\n📢 Ad #{ad['ad_id']}:")
            print(f"   Headlines: {len(ad['headlines'])}")
            for i, headline in enumerate(ad['headlines'][:3], 1):
                print(f"      {i}. {headline}")
            print(f"   Descriptions: {len(ad['descriptions'])}")
            for i, desc in enumerate(ad['descriptions'][:2], 1):
                print(f"      {i}. {desc}")

            # Validate ad structure
            assert len(ad['headlines']) > 0
            assert len(ad['descriptions']) > 0
            assert 'final_url' in ad
            assert 'display_url' in ad

            # Check compliance for plastic surgery (high compliance level)
            assert campaign['compliance_level'] == "high"
            # Should have disclaimer in descriptions
            has_disclaimer = any(
                "противопоказания" in desc.lower() or "консультация" in desc.lower()
                for desc in ad['descriptions']
            )
            assert has_disclaimer, "High compliance specialty should have disclaimer"

            print("\n✅ Ad structure details validated!\n")

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_budget_allocation(self):
        """Test budget allocation across ad groups"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_ads_agent.db"
        agent = AdsCampaignCreatorAgent(
            agent_id="ads-campaign-creator-agent",
            database_url=database_url
        )

        await agent.initialize()

        try:
            print("\n🎯 TEST: Budget Allocation\n")

            task = Task(
                task_id="ads-3",
                subtask_id="ads-sub-3",
                parent_task_id="parent-1",
                action="create_campaign",
                description="dermatology skin treatment Moscow budget 8000",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await agent.execute_task(task)
            campaign = result.result

            print(f"📊 Campaign: {campaign['campaign_name']}")
            print(f"   Total Daily Budget: {campaign['budget']['total_daily']} RUB")

            allocation = campaign['budget']['allocation']
            print(f"\n💰 Budget Allocation:")

            total_allocated = 0
            for ad_group_name, budget in allocation.items():
                print(f"   {ad_group_name}: {budget} RUB")
                total_allocated += budget

            # Validate allocation
            assert total_allocated == campaign['budget']['total_daily']
            assert len(allocation) == 3  # 3 ad groups

            # Check allocation percentages (transactional should get most)
            transactional_budget = next(
                (budget for name, budget in allocation.items() if "Транзакционные" in name),
                0
            )
            commercial_budget = next(
                (budget for name, budget in allocation.items() if "Коммерческие" in name),
                0
            )
            informational_budget = next(
                (budget for name, budget in allocation.items() if "Информационные" in name),
                0
            )

            assert transactional_budget > commercial_budget > informational_budget
            print(f"\n✅ Budget allocation correct:")
            print(f"   Transactional: {transactional_budget} RUB (highest)")
            print(f"   Commercial: {commercial_budget} RUB (medium)")
            print(f"   Informational: {informational_budget} RUB (lowest)")

            # Check recommendations
            recommendations = campaign['recommendations']
            print(f"\n💡 Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

            assert len(recommendations) > 0

            print("\n✅ Budget allocation working!\n")

        finally:
            await agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
