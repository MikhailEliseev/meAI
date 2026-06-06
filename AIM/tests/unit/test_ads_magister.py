"""Unit tests for Ads Magister orchestration

Tests Ads Magister coordination logic in isolation using mocked methods.
Covers: subagent identification, result aggregation, campaign metrics, error handling.
"""

import pytest
from unittest.mock import AsyncMock

from AIM.tests.fixtures.magister_fixtures import mock_ads_subagents, ads_magister


@pytest.mark.asyncio
async def test_ads_magister_identify_subagents_success():
    """Should route actions to correct subagents

    Scenario: Various action types (campaign, budget, test, conversion)
    Expected: Correct subagent IDs returned for each action
    """
    # Arrange: Create real AdsMagister (not using fixture for this test)
    from src.aim.magisters.ads_magister import AdsMagister
    magister = AdsMagister()

    # Act & Assert: Test action routing

    # Campaign creation
    result = await magister.identify_subagents("create_campaign")
    assert result == ["ads-campaign-creator-agent"]

    result = await magister.identify_subagents("campaign setup")
    assert result == ["ads-campaign-creator-agent"]

    # Budget optimization
    result = await magister.identify_subagents("optimize_budget")
    assert result == ["ads-budget-optimizer-agent"]

    result = await magister.identify_subagents("budget allocation")
    assert result == ["ads-budget-optimizer-agent"]

    # A/B testing
    result = await magister.identify_subagents("ab_test")
    assert result == ["ads-ab-testing-agent"]

    result = await magister.identify_subagents("ab testing")
    assert result == ["ads-ab-testing-agent"]

    # Conversion tracking
    result = await magister.identify_subagents("track_conversions")
    assert result == ["ads-conversion-tracker-agent"]

    result = await magister.identify_subagents("conversion analysis")
    assert result == ["ads-conversion-tracker-agent"]

    # Full audit
    result = await magister.identify_subagents("full_ads_audit")
    assert len(result) == 4
    assert "ads-campaign-creator-agent" in result
    assert "ads-budget-optimizer-agent" in result
    assert "ads-ab-testing-agent" in result
    assert "ads-conversion-tracker-agent" in result


@pytest.mark.asyncio
async def test_ads_magister_aggregate_results_success():
    """Should aggregate results from multiple subagents correctly

    Scenario: 3 subagents return campaign results with metrics
    Expected: Total budget calculated, CTR/conversion_rate computed, insights generated
    """
    # Arrange: Create real AdsMagister
    from src.aim.magisters.ads_magister import AdsMagister
    magister = AdsMagister()

    subagent_results = [
        {
            "campaign_name": "Campaign 1",
            "ad_groups": ["group1", "group2"],
            "budget": {"total_daily": 5000},
            "predictions": {
                "estimated_impressions": 100000,
                "estimated_clicks": 2500,
                "estimated_conversions": 125,
            },
            "platform": "yandex_direct",
            "specialty": "dentistry",
        },
        {
            "campaign_name": "Campaign 2",
            "ad_groups": ["group3"],
            "budget": {"total_daily": 3000},
            "predictions": {
                "estimated_impressions": 60000,
                "estimated_clicks": 1500,
                "estimated_conversions": 75,
            },
            "platform": "google_ads",
            "specialty": "dentistry",
        },
        {
            "campaign_name": "Campaign 3",
            "ad_groups": ["group4", "group5"],
            "budget": {"total_daily": 2000},
            "predictions": {
                "estimated_impressions": 40000,
                "estimated_clicks": 1000,
                "estimated_conversions": 50,
            },
            "platform": "yandex_direct",
            "specialty": "cardiology",
        },
    ]

    # Act: Aggregate results
    result = await magister.aggregate_results(subagent_results)

    # Assert: Correct aggregation
    assert result["metrics"]["total_campaigns"] == 3
    assert result["metrics"]["total_ad_groups"] == 5
    assert result["metrics"]["total_budget"] == 10000.0
    assert result["metrics"]["total_impressions"] == 200000
    assert result["metrics"]["total_clicks"] == 5000
    assert result["metrics"]["total_conversions"] == 250
    assert result["metrics"]["ctr"] == pytest.approx(2.5, abs=0.1)  # 5000/200000 * 100
    assert result["metrics"]["conversion_rate"] == pytest.approx(5.0, abs=0.1)  # 250/5000 * 100
    assert "yandex_direct" in result["metrics"]["platforms"]
    assert "google_ads" in result["metrics"]["platforms"]
    assert len(result["insights"]) > 0
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_ads_magister_aggregate_results_partial_failure():
    """Should handle partial failure gracefully (missing metrics)

    Scenario: Some subagents return incomplete results (missing predictions)
    Expected: Aggregation continues with available data, no crashes
    """
    # Arrange: Create real AdsMagister
    from src.aim.magisters.ads_magister import AdsMagister
    magister = AdsMagister()

    subagent_results = [
        {
            "campaign_name": "Campaign 1",
            "ad_groups": ["group1"],
            "budget": {"total_daily": 5000},
            "predictions": {
                "estimated_impressions": 100000,
                "estimated_clicks": 2500,
                "estimated_conversions": 125,
            },
        },
        {
            "campaign_name": "Campaign 2",
            "ad_groups": ["group2"],
            "budget": {"total_daily": 3000},
            # Missing predictions
        },
        {
            "campaign_name": "Campaign 3",
            # Missing ad_groups, budget, predictions
        },
    ]

    # Act: Aggregate results
    result = await magister.aggregate_results(subagent_results)

    # Assert: Graceful handling
    assert result["metrics"]["total_campaigns"] == 3
    assert result["metrics"]["total_ad_groups"] == 2
    assert result["metrics"]["total_budget"] == 8000.0
    assert result["metrics"]["total_impressions"] == 100000
    assert result["metrics"]["total_clicks"] == 2500
    assert result["metrics"]["total_conversions"] == 125
    assert "summary" in result
    assert "insights" in result
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_ads_magister_aggregate_results_full_failure():
    """Should handle full failure (empty results list)

    Scenario: No subagent results provided
    Expected: Returns empty aggregation with default values
    """
    # Arrange: Create real AdsMagister
    from src.aim.magisters.ads_magister import AdsMagister
    magister = AdsMagister()

    subagent_results = []

    # Act: Aggregate results
    result = await magister.aggregate_results(subagent_results)

    # Assert: Default values returned
    assert result["summary"] == "No results to aggregate"
    assert result["insights"] == []
    assert result["recommendations"] == []
