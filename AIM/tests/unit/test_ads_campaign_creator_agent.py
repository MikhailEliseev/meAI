"""Unit tests for Ads Campaign Creator Agent

Tests campaign creation, ad copy generation, and bid optimization.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from meai.agents.base_agent import Task, TaskStatus
from AIM.src.aim.subagents.ads_campaign_creator_agent import AdsCampaignCreatorAgent
from tests.fixtures.subagent_data import YANDEX_CAMPAIGN


@pytest.fixture
def mock_api_clients():
    """Mock API clients for Ads Campaign Creator testing"""
    return {
        "yandex_direct": AsyncMock(),
        "openai": AsyncMock(),
    }


@pytest.fixture
def ads_campaign_agent(mock_api_clients):
    """Ads Campaign Creator Agent with mocked API clients"""
    agent = AdsCampaignCreatorAgent(
        agent_id="test-ads-campaign-creator",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
    )

    # Inject mocked API clients if agent has them
    if hasattr(agent, 'yandex_client'):
        agent.yandex_client = mock_api_clients["yandex_direct"]
    if hasattr(agent, 'openai_client'):
        agent.openai_client = mock_api_clients["openai"]

    return agent


@pytest.mark.asyncio
async def test_campaign_creation_success(ads_campaign_agent, mock_api_clients):
    """Test campaign creation in Yandex Direct

    Verifies:
    - Campaign structure generation (ad groups, ads, keywords)
    - Budget allocation logic
    - Platform-specific optimizations
    - Performance predictions
    """
    # Create task
    task = Task(
        task_id="test-ads-001",
        subtask_id="test-ads-001-sub",
        parent_task_id="test-ads-001-parent",
        action="create_campaign",
        description="dental implants Moscow 5000",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    # Execute
    result = await ads_campaign_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert result.result is not None

    # Verify campaign structure
    campaign = result.result
    assert "campaign_name" in campaign
    assert "Dental Implants" in campaign["campaign_name"]
    assert "Москва" in campaign["campaign_name"]

    # Verify platform
    assert campaign["platform"] == "google_ads"  # Default

    # Verify specialty detection
    assert campaign["specialty"] == "dentistry"

    # Verify ad groups created (by intent)
    assert "ad_groups" in campaign
    ad_groups = campaign["ad_groups"]
    assert len(ad_groups) == 3  # informational, commercial, transactional

    # Verify ad group structure
    for ad_group in ad_groups:
        assert "name" in ad_group
        assert "intent" in ad_group
        assert "keywords" in ad_group
        assert "max_cpc" in ad_group
        assert "ads" in ad_group

        # Verify ads generated for each ad group
        assert len(ad_group["ads"]) == 3  # A/B testing

        for ad in ad_group["ads"]:
            assert "ad_id" in ad
            assert "headlines" in ad
            assert "descriptions" in ad
            assert "final_url" in ad
            assert "display_url" in ad

            # Verify character limits (Google Ads)
            for headline in ad["headlines"]:
                assert len(headline) <= 30
            for description in ad["descriptions"]:
                assert len(description) <= 90

    # Verify budget allocation
    assert "budget" in campaign
    budget = campaign["budget"]
    assert budget["total_daily"] == 5000
    assert "allocation" in budget

    # Verify budget allocation by intent
    allocation = budget["allocation"]
    assert len(allocation) == 3

    # Transactional should get most budget (50%)
    transactional_budget = allocation.get("dental implants moscow - Транзакционные", 0)
    assert transactional_budget == 2500  # 50% of 5000

    # Commercial should get medium budget (30%)
    commercial_budget = allocation.get("dental implants moscow - Коммерческие", 0)
    assert commercial_budget == 1500  # 30% of 5000

    # Informational should get least budget (20%)
    informational_budget = allocation.get("dental implants moscow - Информационные", 0)
    assert informational_budget == 1000  # 20% of 5000

    # Verify performance predictions
    assert "predictions" in campaign
    predictions = campaign["predictions"]
    assert "estimated_impressions" in predictions
    assert "estimated_clicks" in predictions
    assert "estimated_conversions" in predictions
    assert "estimated_ctr" in predictions
    assert "estimated_conversion_rate" in predictions
    assert "estimated_cpa" in predictions
    assert "estimated_roas" in predictions

    # Verify predictions are realistic
    assert predictions["estimated_clicks"] > 0
    assert predictions["estimated_conversions"] > 0
    assert predictions["estimated_ctr"] > 0
    assert predictions["estimated_conversion_rate"] > 0

    # Verify recommendations
    assert "recommendations" in campaign
    recommendations = campaign["recommendations"]
    assert len(recommendations) > 0
    assert any("бюджет" in rec.lower() or "расширен" in rec.lower() or "ретаргетинг" in rec.lower() for rec in recommendations)

    # Verify compliance level
    assert "compliance_level" in campaign
    assert campaign["compliance_level"] == "medium"  # Dentistry


@pytest.mark.asyncio
async def test_ad_copy_generation(ads_campaign_agent, mock_api_clients):
    """Test ad copy generation with compliance

    Verifies:
    - Ad copy structure (headlines, descriptions)
    - Character limits enforcement
    - Medical compliance rules
    - Forbidden words detection
    """
    # Create task for plastic surgery (high compliance)
    task = Task(
        task_id="test-ads-002",
        subtask_id="test-ads-002-sub",
        parent_task_id="test-ads-002-parent",
        action="create_campaign",
        description="plastic surgery rhinoplasty Moscow 10000",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    # Execute
    result = await ads_campaign_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    campaign = result.result

    # Verify specialty detection
    assert campaign["specialty"] == "plastic_surgery"

    # Verify high compliance level
    assert campaign["compliance_level"] == "high"

    # Verify ad groups
    ad_groups = campaign["ad_groups"]
    assert len(ad_groups) == 3

    # Check ad copy in each ad group
    for ad_group in ad_groups:
        for ad in ad_group["ads"]:
            # Verify headlines
            assert len(ad["headlines"]) > 0
            for headline in ad["headlines"]:
                # Verify character limit (Google Ads)
                assert len(headline) <= 30

                # Verify no forbidden words
                forbidden_words = [
                    "лучший", "самый", "гарантируем", "100%", "навсегда",
                    "чудо", "уникальный", "единственный", "быстро вылечим"
                ]
                headline_lower = headline.lower()
                for forbidden in forbidden_words:
                    assert forbidden not in headline_lower, f"Forbidden word '{forbidden}' found in headline"

            # Verify descriptions
            assert len(ad["descriptions"]) > 0
            for description in ad["descriptions"]:
                # Verify character limit (Google Ads)
                assert len(description) <= 90

            # Verify compliance disclaimer for high compliance specialty
            descriptions_text = " ".join(ad["descriptions"])
            assert "противопоказания" in descriptions_text.lower() or "консультация специалиста" in descriptions_text.lower()


@pytest.mark.asyncio
async def test_bid_strategy_optimization(ads_campaign_agent, mock_api_clients):
    """Test bid strategy optimization

    Verifies:
    - Budget allocation by intent priority
    - CPC recommendations by ad group
    - Performance predictions
    - ROI calculations
    """
    # Create task with higher budget
    task = Task(
        task_id="test-ads-003",
        subtask_id="test-ads-003-sub",
        parent_task_id="test-ads-003-parent",
        action="create_campaign",
        description="dental implants Moscow 20000",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    # Execute
    result = await ads_campaign_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    campaign = result.result

    # Verify budget
    assert campaign["budget"]["total_daily"] == 20000

    # Verify budget allocation strategy
    allocation = campaign["budget"]["allocation"]

    # Calculate total allocated
    total_allocated = sum(allocation.values())
    assert total_allocated == 20000

    # Verify intent-based allocation percentages
    transactional_budget = allocation.get("dental implants moscow - Транзакционные", 0)
    commercial_budget = allocation.get("dental implants moscow - Коммерческие", 0)
    informational_budget = allocation.get("dental implants moscow - Информационные", 0)

    # Transactional should get 50%
    assert transactional_budget == 10000

    # Commercial should get 30%
    assert commercial_budget == 6000

    # Informational should get 20%
    assert informational_budget == 4000

    # Verify CPC recommendations by intent
    ad_groups = campaign["ad_groups"]

    for ad_group in ad_groups:
        intent = ad_group["intent"]
        max_cpc = ad_group["max_cpc"]

        if intent == "transactional":
            # Highest CPC for transactional
            assert max_cpc == 350
        elif intent == "commercial":
            # Medium CPC for commercial
            assert max_cpc == 250
        elif intent == "informational":
            # Lowest CPC for informational
            assert max_cpc == 150

    # Verify performance predictions scale with budget
    predictions = campaign["predictions"]

    # With 20000 budget and avg CPC 250 (dentistry)
    expected_clicks = int(20000 / 250)
    assert predictions["estimated_clicks"] == expected_clicks

    # Verify CTR prediction (dentistry avg: 3.5%)
    assert predictions["estimated_ctr"] == 3.5

    # Verify conversion rate prediction (dentistry avg: 8.0%)
    assert predictions["estimated_conversion_rate"] == 8.0

    # Verify conversions calculation
    expected_conversions = int(expected_clicks * 0.08)
    assert predictions["estimated_conversions"] == expected_conversions

    # Verify CPA calculation
    if expected_conversions > 0:
        expected_cpa = int(20000 / expected_conversions)
        assert predictions["estimated_cpa"] == expected_cpa

    # Verify ROAS prediction
    assert predictions["estimated_roas"] == 3.5  # Typical for medical

    # Verify recommendations include budget optimization
    recommendations = campaign["recommendations"]
    assert len(recommendations) > 0
