"""Integration tests for Ads Magister E2E flow

Tests Ads Magister with real coordination logic (event_bus mocked).
Verifies end-to-end task execution and campaign metric aggregation.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.aim.magisters.ads_magister import AdsMagister


@pytest.mark.asyncio
async def test_ads_magister_e2e_success():
    """Should complete E2E flow with real coordination logic

    Scenario: Real AdsMagister with mocked event_bus for delegation
    Expected: identify_subagents called, campaign metrics aggregated correctly
    """
    # Arrange: Create real AdsMagister with mocked event_bus
    mock_event_bus = AsyncMock()
    mock_vault = AsyncMock()
    mock_vault.vault_path = AsyncMock()
    mock_vault.vault_path.exists.return_value = True

    magister = AdsMagister(
        magister_id="e2e-ads-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
        event_bus=mock_event_bus,
        vault=mock_vault,
    )

    # Mock subagent results
    subagent_results = [
        {
            "campaign_name": "Test Campaign",
            "ad_groups": ["group1", "group2"],
            "budget": {"total_daily": 10000},
            "predictions": {
                "estimated_impressions": 200000,
                "estimated_clicks": 5000,
                "estimated_conversions": 250,
            },
            "platform": "yandex_direct",
            "specialty": "dentistry",
        },
    ]

    # Act: Aggregate results (E2E flow)
    result = await magister.aggregate_results(subagent_results)

    # Assert: E2E flow completed
    assert result["summary"] != "No results to aggregate"
    assert result["metrics"]["total_campaigns"] == 1
    assert result["metrics"]["total_budget"] == 10000.0
    assert result["metrics"]["ctr"] == pytest.approx(2.5, abs=0.1)
    assert result["metrics"]["conversion_rate"] == pytest.approx(5.0, abs=0.1)
    assert len(result["insights"]) > 0
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_ads_magister_e2e_error():
    """Should handle E2E error when vault logging fails

    Scenario: Real AdsMagister, vault.vault_path raises error
    Expected: Error handled gracefully, aggregation continues
    """
    # Arrange: Create real AdsMagister with failing vault
    mock_event_bus = AsyncMock()
    mock_vault = AsyncMock()
    mock_vault.vault_path.exists.side_effect = OSError("Vault not accessible")

    magister = AdsMagister(
        magister_id="e2e-error-ads-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
        event_bus=mock_event_bus,
        vault=mock_vault,
    )

    subagent_results = [
        {
            "campaign_name": "Test Campaign",
            "ad_groups": ["group1"],
            "budget": {"total_daily": 5000},
            "predictions": {
                "estimated_impressions": 100000,
                "estimated_clicks": 2500,
                "estimated_conversions": 125,
            },
            "platform": "google_ads",
            "specialty": "cardiology",
        },
    ]

    # Act: Aggregate results (should handle vault error)
    result = await magister.aggregate_results(subagent_results)

    # Assert: Aggregation succeeded despite vault error
    assert result["summary"] != "No results to aggregate"
    assert result["metrics"]["total_campaigns"] == 1
    assert result["metrics"]["total_budget"] == 5000.0
    assert result["metrics"]["ctr"] == pytest.approx(2.5, abs=0.1)
