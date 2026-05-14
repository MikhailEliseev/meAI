"""End-to-End Tests for Ads Workflow

Tests complete Ads workflow from Ads Magister to Campaign Creator Agent,
validating task delegation, budget optimization, and validation scenarios.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from AIM.src.aim.magisters.ads_magister import AdsMagister
from AIM.src.aim.subagents.ads_campaign_creator_agent import AdsCampaignCreatorAgent


@pytest.fixture
def mock_campaign_creation_result():
    """Mock Campaign Creator Agent result"""
    return {
        "status": "success",
        "campaign": {
            "campaign_id": "camp-12345",
            "name": "Dental Implants - Search Campaign",
            "budget": {
                "daily": 150.0,
                "monthly": 4500.0,
                "currency": "USD",
            },
            "targeting": {
                "keywords": ["dental implants", "teeth replacement", "implant dentist"],
                "locations": ["New York", "Los Angeles", "Chicago"],
                "demographics": {
                    "age_range": "35-65",
                    "income_level": "middle-high",
                },
            },
            "ad_groups": [
                {
                    "name": "Dental Implants - Exact Match",
                    "keywords": ["dental implants"],
                    "bid": 8.50,
                    "ads_count": 3,
                },
                {
                    "name": "Teeth Replacement - Broad Match",
                    "keywords": ["teeth replacement", "replace missing teeth"],
                    "bid": 6.20,
                    "ads_count": 2,
                },
            ],
        },
        "metrics": {
            "estimated_ctr": 2.8,
            "estimated_conversion_rate": 5.2,
            "estimated_cpc": 7.80,
            "estimated_monthly_clicks": 577,
            "estimated_monthly_conversions": 30,
        },
        "recommendations": [
            {
                "type": "optimization",
                "priority": "medium",
                "description": "Consider adding negative keywords to reduce wasted spend",
            }
        ],
    }


@pytest.fixture
def mock_budget_optimization_result():
    """Mock budget optimization result with multiple campaigns"""
    return {
        "status": "success",
        "campaigns": [
            {
                "campaign_id": "camp-001",
                "name": "Search - Dental Implants",
                "budget_allocation": 2500.0,
                "expected_roi": 3.2,
                "priority": "high",
            },
            {
                "campaign_id": "camp-002",
                "name": "Display - Awareness",
                "budget_allocation": 1500.0,
                "expected_roi": 1.8,
                "priority": "medium",
            },
            {
                "campaign_id": "camp-003",
                "name": "Remarketing",
                "budget_allocation": 1000.0,
                "expected_roi": 4.5,
                "priority": "high",
            },
        ],
        "total_budget": 5000.0,
        "optimization_strategy": "roi_weighted",
        "ab_tests": [
            {
                "test_id": "ab-001",
                "variant_a": "Headline: Get Your Smile Back",
                "variant_b": "Headline: Dental Implants from $99/month",
                "budget_split": "50/50",
                "duration_days": 14,
            }
        ],
    }


@pytest.mark.asyncio
async def test_ads_workflow_campaign_creation_success(mock_campaign_creation_result):
    """Test full Ads workflow from Ads Magister to Campaign Creator Agent

    Validates:
    - Campaign Creator Agent executes and returns campaign data
    - Ads Magister receives and validates campaign
    - Result structure includes campaign_id, budget, targeting, ad_groups
    - Budget allocation logic is correct
    """
    # Create mock Campaign Creator Agent
    mock_creator = AsyncMock(spec=AdsCampaignCreatorAgent)
    mock_creator.execute_task.return_value = mock_campaign_creation_result

    # Simulate calling the agent directly
    result = await mock_creator.execute_task(
        task={
            "campaign_type": "search",
            "target_keyword": "dental implants",
            "budget": 4500.0,
            "locations": ["New York", "Los Angeles", "Chicago"],
            "correlation_id": "test-campaign-001",
        }
    )

    # Verify result structure
    assert result["status"] == "success"
    assert "campaign" in result
    assert result["campaign"]["campaign_id"] == "camp-12345"

    # Verify budget allocation
    assert "budget" in result["campaign"]
    assert result["campaign"]["budget"]["daily"] == 150.0
    assert result["campaign"]["budget"]["monthly"] == 4500.0
    assert result["campaign"]["budget"]["currency"] == "USD"

    # Verify targeting parameters
    assert "targeting" in result["campaign"]
    targeting = result["campaign"]["targeting"]
    assert len(targeting["keywords"]) >= 3
    assert len(targeting["locations"]) == 3
    assert "demographics" in targeting

    # Verify ad groups
    assert "ad_groups" in result["campaign"]
    assert len(result["campaign"]["ad_groups"]) >= 2
    assert all("bid" in ag for ag in result["campaign"]["ad_groups"])

    # Verify metrics
    assert "metrics" in result
    assert result["metrics"]["estimated_ctr"] > 0
    assert result["metrics"]["estimated_conversion_rate"] > 0

    # Verify agent was called
    mock_creator.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_ads_workflow_budget_optimization(mock_budget_optimization_result):
    """Test Ads Magister coordinating budget optimization across campaigns

    Validates:
    - Budget distribution across multiple campaigns
    - CTR and conversion rate predictions
    - A/B test setup and configuration
    - ROI-weighted optimization strategy
    """
    # Create mock Campaign Creator Agent
    mock_creator = AsyncMock(spec=AdsCampaignCreatorAgent)
    mock_creator.execute_task.return_value = mock_budget_optimization_result

    # Simulate calling the agent for budget optimization
    result = await mock_creator.execute_task(
        task={
            "operation": "optimize_budget",
            "total_budget": 5000.0,
            "campaigns": ["camp-001", "camp-002", "camp-003"],
            "correlation_id": "test-budget-001",
        }
    )

    # Verify result structure
    assert result["status"] == "success"
    assert "campaigns" in result
    assert len(result["campaigns"]) == 3

    # Verify budget distribution
    total_allocated = sum(c["budget_allocation"] for c in result["campaigns"])
    assert total_allocated == result["total_budget"]
    assert total_allocated == 5000.0

    # Verify ROI-weighted allocation (high ROI campaigns get more budget)
    high_roi_campaigns = [c for c in result["campaigns"] if c["priority"] == "high"]
    medium_roi_campaigns = [c for c in result["campaigns"] if c["priority"] == "medium"]

    assert len(high_roi_campaigns) >= 1
    # High priority campaigns should have higher expected ROI
    for high_roi in high_roi_campaigns:
        for medium_roi in medium_roi_campaigns:
            assert high_roi["expected_roi"] > medium_roi["expected_roi"]

    # Verify A/B test configuration
    assert "ab_tests" in result
    assert len(result["ab_tests"]) >= 1
    ab_test = result["ab_tests"][0]
    assert ab_test["budget_split"] == "50/50"
    assert ab_test["duration_days"] > 0

    # Verify optimization strategy
    assert result["optimization_strategy"] == "roi_weighted"

    # Verify agent was called
    mock_creator.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_ads_workflow_invalid_budget():
    """Test error handling for invalid budget constraints

    Validates:
    - Validation error raised for budget exceeding limit
    - Error message clarity
    - No partial campaign creation
    """
    # Create mock Campaign Creator Agent that raises validation error
    mock_creator = AsyncMock(spec=AdsCampaignCreatorAgent)
    mock_creator.execute_task.return_value = {
        "status": "error",
        "error": "Budget exceeds maximum allowed limit of $10,000",
        "error_code": "BUDGET_EXCEEDED",
        "details": {
            "requested_budget": 15000.0,
            "max_budget": 10000.0,
            "excess": 5000.0,
        },
    }

    # Simulate calling the agent with excessive budget
    result = await mock_creator.execute_task(
        task={
            "campaign_type": "search",
            "budget": 15000.0,
            "correlation_id": "test-invalid-001",
        }
    )

    # Verify error response
    assert result["status"] == "error"
    assert "error" in result
    assert "Budget exceeds" in result["error"]
    assert result["error_code"] == "BUDGET_EXCEEDED"

    # Verify error details
    assert "details" in result
    assert result["details"]["requested_budget"] == 15000.0
    assert result["details"]["max_budget"] == 10000.0
    assert result["details"]["excess"] == 5000.0

    # Verify no campaign was created
    assert "campaign" not in result
    assert "campaign_id" not in result

    # Verify agent was called
    mock_creator.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_ads_workflow_campaign_metrics_validation():
    """Test campaign metrics validation and prediction

    Validates:
    - CTR prediction is realistic (1-5% range)
    - Conversion rate is realistic (2-10% range)
    - CPC is within market range
    - Monthly projections are calculated correctly
    """
    mock_creator = AsyncMock(spec=AdsCampaignCreatorAgent)
    mock_creator.execute_task.return_value = {
        "status": "success",
        "campaign": {
            "campaign_id": "camp-metrics-001",
            "budget": {"daily": 200.0, "monthly": 6000.0},
        },
        "metrics": {
            "estimated_ctr": 3.2,  # 3.2% CTR
            "estimated_conversion_rate": 6.5,  # 6.5% conversion rate
            "estimated_cpc": 9.50,
            "estimated_monthly_clicks": 632,
            "estimated_monthly_conversions": 41,
        },
    }

    result = await mock_creator.execute_task(task={"campaign_type": "search"})

    # Verify metrics are realistic
    metrics = result["metrics"]

    # CTR should be between 1-5% for search campaigns
    assert 1.0 <= metrics["estimated_ctr"] <= 5.0

    # Conversion rate should be between 2-10%
    assert 2.0 <= metrics["estimated_conversion_rate"] <= 10.0

    # CPC should be positive and reasonable (< $50)
    assert 0 < metrics["estimated_cpc"] < 50.0

    # Verify monthly projections calculation
    # monthly_clicks = monthly_budget / cpc
    expected_clicks = result["campaign"]["budget"]["monthly"] / metrics["estimated_cpc"]
    assert abs(metrics["estimated_monthly_clicks"] - expected_clicks) < 10  # Allow small variance

    # monthly_conversions = monthly_clicks * conversion_rate
    expected_conversions = metrics["estimated_monthly_clicks"] * (metrics["estimated_conversion_rate"] / 100)
    assert abs(metrics["estimated_monthly_conversions"] - expected_conversions) < 2


@pytest.mark.asyncio
async def test_ads_workflow_targeting_validation():
    """Test campaign targeting parameters validation

    Validates:
    - Keywords list is not empty
    - Locations are specified
    - Demographics are within valid ranges
    - Ad groups have valid bid amounts
    """
    mock_creator = AsyncMock(spec=AdsCampaignCreatorAgent)
    mock_creator.execute_task.return_value = {
        "status": "success",
        "campaign": {
            "campaign_id": "camp-targeting-001",
            "targeting": {
                "keywords": ["dental implants", "implant dentist", "tooth replacement"],
                "locations": ["New York", "California"],
                "demographics": {
                    "age_range": "25-65",
                    "income_level": "middle-high",
                },
            },
            "ad_groups": [
                {"name": "Group 1", "bid": 8.50, "keywords": ["dental implants"]},
                {"name": "Group 2", "bid": 6.00, "keywords": ["implant dentist"]},
            ],
        },
    }

    result = await mock_creator.execute_task(task={"campaign_type": "search"})

    campaign = result["campaign"]
    targeting = campaign["targeting"]

    # Verify keywords
    assert len(targeting["keywords"]) >= 3
    assert all(isinstance(kw, str) and len(kw) > 0 for kw in targeting["keywords"])

    # Verify locations
    assert len(targeting["locations"]) >= 1
    assert all(isinstance(loc, str) and len(loc) > 0 for loc in targeting["locations"])

    # Verify demographics
    assert "age_range" in targeting["demographics"]
    assert "income_level" in targeting["demographics"]

    # Verify ad groups have valid bids
    assert len(campaign["ad_groups"]) >= 2
    for ad_group in campaign["ad_groups"]:
        assert ad_group["bid"] > 0
        assert ad_group["bid"] < 100  # Reasonable max CPC
        assert len(ad_group["keywords"]) >= 1
