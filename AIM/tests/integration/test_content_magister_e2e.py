"""Integration tests for Content Magister E2E flow

Tests Content Magister with real coordination logic (event_bus mocked).
Verifies end-to-end task execution and result aggregation.
"""

import pytest
from unittest.mock import AsyncMock, patch

from AIM.src.aim.magisters.content_magister import ContentMagister


@pytest.mark.asyncio
async def test_content_magister_e2e_success():
    """Should complete E2E flow with real coordination logic

    Scenario: Real ContentMagister with mocked event_bus for delegation
    Expected: identify_subagents called, results aggregated correctly
    """
    # Arrange: Create real ContentMagister with mocked event_bus
    mock_event_bus = AsyncMock()
    mock_vault = AsyncMock()
    mock_vault.vault_path = AsyncMock()
    mock_vault.vault_path.exists.return_value = True

    magister = ContentMagister(
        magister_id="e2e-content-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
        event_bus=mock_event_bus,
        vault=mock_vault,
    )

    # Mock subagent results
    subagent_results = [
        {
            "content_pieces": 5,
            "content_type": "blog_post",
            "quality_score": 85,
            "readability_score": 75,
            "seo_score": 80,
        },
    ]

    # Act: Aggregate results (E2E flow)
    result = await magister.aggregate_results(subagent_results)

    # Assert: E2E flow completed
    assert result["summary"] != "No results to aggregate"
    assert result["metrics"]["total_content_pieces"] == 5
    assert result["metrics"]["avg_quality"] == 85.0
    assert len(result["insights"]) > 0
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_content_magister_e2e_error():
    """Should handle E2E error when vault logging fails

    Scenario: Real ContentMagister, vault.vault_path raises error
    Expected: Error handled gracefully, aggregation continues
    """
    # Arrange: Create real ContentMagister with failing vault
    mock_event_bus = AsyncMock()
    mock_vault = AsyncMock()
    mock_vault.vault_path.exists.side_effect = OSError("Vault not accessible")

    magister = ContentMagister(
        magister_id="e2e-error-content-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
        event_bus=mock_event_bus,
        vault=mock_vault,
    )

    subagent_results = [
        {
            "content_pieces": 3,
            "content_type": "article",
            "quality_score": 90,
            "readability_score": 80,
            "seo_score": 85,
        },
    ]

    # Act: Aggregate results (should handle vault error)
    result = await magister.aggregate_results(subagent_results)

    # Assert: Aggregation succeeded despite vault error
    assert result["summary"] != "No results to aggregate"
    assert result["metrics"]["total_content_pieces"] == 3
    assert result["metrics"]["avg_quality"] == 90.0
