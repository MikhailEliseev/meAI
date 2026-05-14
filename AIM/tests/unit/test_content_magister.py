"""Unit tests for Content Magister orchestration

Tests Content Magister coordination logic in isolation using mocked methods.
Covers: subagent identification, result aggregation, error handling.
"""

import pytest
from unittest.mock import AsyncMock

from AIM.tests.fixtures.magister_fixtures import mock_content_subagents, content_magister


@pytest.mark.asyncio
async def test_content_magister_identify_subagents_success():
    """Should route actions to correct subagents

    Scenario: Various action types (create, optimize, plan, distribute)
    Expected: Correct subagent IDs returned for each action
    """
    # Arrange: Create real ContentMagister (not using fixture for this test)
    from AIM.src.aim.magisters.content_magister import ContentMagister
    magister = ContentMagister()

    # Act & Assert: Test action routing

    # Content creation
    result = await magister.identify_subagents("create_article")
    assert result == ["content-writer-agent"]

    result = await magister.identify_subagents("write blog post")
    assert result == ["content-writer-agent"]

    # Content optimization
    result = await magister.identify_subagents("optimize_content")
    assert result == ["content-editor-agent"]

    result = await magister.identify_subagents("edit article")
    assert result == ["content-editor-agent"]

    # Editorial calendar
    result = await magister.identify_subagents("plan_calendar")
    assert result == ["editorial-calendar-agent"]

    # Content distribution
    result = await magister.identify_subagents("distribute_content")
    assert result == ["content-distribution-agent"]

    # Full audit
    result = await magister.identify_subagents("full_content_audit")
    assert len(result) == 4
    assert "content-writer-agent" in result
    assert "content-editor-agent" in result
    assert "editorial-calendar-agent" in result
    assert "content-distribution-agent" in result


@pytest.mark.asyncio
async def test_content_magister_aggregate_results_success():
    """Should aggregate results from multiple subagents correctly

    Scenario: 3 subagents return results with quality metrics
    Expected: Average scores calculated, insights generated, recommendations provided
    """
    # Arrange: Create real ContentMagister
    from AIM.src.aim.magisters.content_magister import ContentMagister
    magister = ContentMagister()

    subagent_results = [
        {
            "content_pieces": 5,
            "content_type": "blog_post",
            "quality_score": 85,
            "readability_score": 75,
            "seo_score": 80,
        },
        {
            "content_pieces": 3,
            "content_type": "article",
            "quality_score": 90,
            "readability_score": 80,
            "seo_score": 85,
        },
        {
            "content_pieces": 2,
            "content_type": "blog_post",
            "quality_score": 75,
            "readability_score": 70,
            "seo_score": 75,
        },
    ]

    # Act: Aggregate results
    result = await magister.aggregate_results(subagent_results)

    # Assert: Correct aggregation
    assert result["metrics"]["total_content_pieces"] == 10
    assert result["metrics"]["avg_quality"] == pytest.approx(83.3, abs=0.1)
    assert result["metrics"]["avg_readability"] == pytest.approx(75.0, abs=0.1)
    assert result["metrics"]["avg_seo"] == pytest.approx(80.0, abs=0.1)
    assert "blog_post" in result["metrics"]["content_types"]
    assert result["metrics"]["content_types"]["blog_post"] == 2
    assert len(result["insights"]) > 0
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_content_magister_aggregate_results_partial_failure():
    """Should handle partial failure gracefully (missing metrics)

    Scenario: Some subagents return incomplete results (missing quality_score)
    Expected: Aggregation continues with available data, no crashes
    """
    # Arrange: Create real ContentMagister
    from AIM.src.aim.magisters.content_magister import ContentMagister
    magister = ContentMagister()

    subagent_results = [
        {
            "content_pieces": 5,
            "content_type": "blog_post",
            "quality_score": 85,
            # Missing readability_score and seo_score
        },
        {
            "content_pieces": 3,
            "content_type": "article",
            # Missing all scores
        },
        {
            "content_pieces": 2,
            "content_type": "blog_post",
            "quality_score": 75,
            "readability_score": 70,
            "seo_score": 75,
        },
    ]

    # Act: Aggregate results
    result = await magister.aggregate_results(subagent_results)

    # Assert: Graceful handling
    assert result["metrics"]["total_content_pieces"] == 10
    assert result["metrics"]["avg_quality"] == pytest.approx(80.0, abs=0.1)  # (85 + 75) / 2
    assert result["metrics"]["avg_readability"] == pytest.approx(70.0, abs=0.1)  # Only 1 value
    assert result["metrics"]["avg_seo"] == pytest.approx(75.0, abs=0.1)  # Only 1 value
    assert "summary" in result
    assert "insights" in result
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_content_magister_aggregate_results_full_failure():
    """Should handle full failure (empty results list)

    Scenario: No subagent results provided
    Expected: Returns empty aggregation with default values
    """
    # Arrange: Create real ContentMagister
    from AIM.src.aim.magisters.content_magister import ContentMagister
    magister = ContentMagister()

    subagent_results = []

    # Act: Aggregate results
    result = await magister.aggregate_results(subagent_results)

    # Assert: Default values returned
    assert result["summary"] == "No results to aggregate"
    assert result["insights"] == []
    assert result["recommendations"] == []
