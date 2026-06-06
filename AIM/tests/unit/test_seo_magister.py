"""Unit tests for SEO Magister orchestration

Tests SEO Magister coordination logic in isolation using mocked subagents.
Covers: success, timeout, partial failure, full failure scenarios.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock

from AIM.tests.fixtures.magister_fixtures import mock_seo_subagents, seo_magister


@pytest.mark.asyncio
async def test_seo_magister_success(seo_magister, mock_seo_subagents):
    """Should coordinate 3 subagents successfully and aggregate results

    Scenario: All 3 subagents return success
    Expected: overall_score calculated, status="success", all results aggregated
    """
    # Arrange: Mock successful responses from all 3 subagents
    mock_seo_subagents["technical"].analyze.return_value = {
        "agent": "technical-agent",
        "status": "success",
        "results": {
            "robots_txt": {"exists": True, "allows_crawling": True},
            "sitemap_xml": {"exists": True, "valid": True},
            "meta_tags": {"title": "Great Title (50 chars)", "description": "A" * 140},
            "performance": {"score": 85},
            "schema_org": {"count": 3},
        }
    }

    mock_seo_subagents["content"].analyze.return_value = {
        "agent": "content-agent",
        "status": "success",
        "results": {
            "headers": {"h1_count": 1, "broken_hierarchy": False},
            "readability": {"flesch_reading_ease": 70},
            "content_quality": {"word_count": 1200, "image_count": 5, "alt_text_coverage": 95},
            "structure": {"semantic_score": 80},
        }
    }

    mock_seo_subagents["links"].analyze.return_value = {
        "agent": "links-agent",
        "status": "success",
        "results": {
            "internal_links": {"total": 25, "unique": 15},
            "external_links": {"total": 8, "nofollow_percentage": 30},
            "anchor_text": {"empty_percentage": 0, "generic_percentage": 5},
            "broken_links": {"broken_percentage": 0, "broken_count": 0},
        }
    }

    # Act: Coordinate analysis
    result = await seo_magister.coordinate_analysis("https://example.com", "test-123")

    # Assert: Verify successful coordination
    assert result["status"] == "success"
    assert result["url"] == "https://example.com"
    assert result["correlation_id"] == "test-123"
    assert "scores" in result
    assert result["scores"]["overall"] > 0
    assert result["scores"]["technical"] > 0
    assert result["scores"]["content"] > 0
    assert result["scores"]["links"] > 0
    assert "summary" in result
    assert "recommendations" in result
    assert "details" in result

    # Verify all 3 subagents were called
    mock_seo_subagents["technical"].analyze.assert_called_once_with("https://example.com", "test-123")
    mock_seo_subagents["content"].analyze.assert_called_once_with("https://example.com", "test-123")
    mock_seo_subagents["links"].analyze.assert_called_once_with("https://example.com", "test-123")


@pytest.mark.asyncio
async def test_seo_magister_timeout(mock_seo_subagents):
    """Should timeout after 600 seconds if subagent hangs

    Scenario: One subagent delays 700s (exceeds 600s timeout)
    Expected: asyncio.TimeoutError raised, error status returned
    """
    # Create magister with short timeout for testing (1 second)
    from src.aim.magisters.seo_magister import SEOMagister
    seo_magister = SEOMagister(
        timeout=1,
        technical_agent=mock_seo_subagents["technical"],
        content_agent=mock_seo_subagents["content"],
        links_agent=mock_seo_subagents["links"],
    )

    # Arrange: Mock one slow subagent (2s delay, exceeds 1s timeout)
    async def slow_mock(url, correlation_id):
        await asyncio.sleep(2)
        return {"status": "success"}

    mock_seo_subagents["technical"].analyze.side_effect = slow_mock
    mock_seo_subagents["content"].analyze.return_value = {"status": "success", "results": {}}
    mock_seo_subagents["links"].analyze.return_value = {"status": "success", "results": {}}

    # Act: Coordinate analysis
    result = await seo_magister.coordinate_analysis("https://example.com", "test-123")

    # Assert: Should return error status (not raise exception)
    assert result["status"] == "error"
    assert "timeout" in result["error"].lower()
    assert result["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_seo_magister_partial_failure(seo_magister, mock_seo_subagents):
    """Should handle partial failure gracefully (1 of 3 subagents fails)

    Scenario: Technical agent fails, Content and Links succeed
    Expected: status="success", technical error logged, other results aggregated
    """
    # Arrange: Mock 1 failure, 2 successes
    mock_seo_subagents["technical"].analyze.side_effect = ValueError("API error")

    mock_seo_subagents["content"].analyze.return_value = {
        "agent": "content-agent",
        "status": "success",
        "results": {
            "headers": {"h1_count": 1, "broken_hierarchy": False},
            "readability": {"flesch_reading_ease": 70},
            "content_quality": {"word_count": 800, "image_count": 3, "alt_text_coverage": 80},
            "structure": {"semantic_score": 75},
        }
    }

    mock_seo_subagents["links"].analyze.return_value = {
        "agent": "links-agent",
        "status": "success",
        "results": {
            "internal_links": {"total": 15, "unique": 10},
            "external_links": {"total": 5, "nofollow_percentage": 25},
            "anchor_text": {"empty_percentage": 2, "generic_percentage": 10},
            "broken_links": {"broken_percentage": 0, "broken_count": 0},
        }
    }

    # Act: Coordinate analysis
    result = await seo_magister.coordinate_analysis("https://example.com", "test-123")

    # Assert: Graceful degradation
    assert result["status"] == "success"
    assert "details" in result
    assert result["details"]["technical"]["status"] == "error"
    assert "API error" in result["details"]["technical"]["error"]
    assert result["details"]["content"]["status"] == "success"
    assert result["details"]["links"]["status"] == "success"

    # Technical score should be 0, others should be > 0
    assert result["scores"]["technical"] == 0.0
    assert result["scores"]["content"] > 0
    assert result["scores"]["links"] > 0


@pytest.mark.asyncio
async def test_seo_magister_full_failure(seo_magister, mock_seo_subagents):
    """Should handle full failure (all 3 subagents fail)

    Scenario: All 3 subagents raise exceptions
    Expected: status="success" (per current implementation), all errors logged, scores=0
    """
    # Arrange: Mock all failures with different error types
    mock_seo_subagents["technical"].analyze.side_effect = ValueError("Invalid URL")
    mock_seo_subagents["content"].analyze.side_effect = ConnectionError("Network timeout")
    mock_seo_subagents["links"].analyze.side_effect = KeyError("Missing API key")

    # Act: Coordinate analysis
    result = await seo_magister.coordinate_analysis("https://example.com", "test-123")

    # Assert: All errors logged
    assert result["status"] == "success"  # Current implementation returns success even on full failure
    assert result["details"]["technical"]["status"] == "error"
    assert result["details"]["content"]["status"] == "error"
    assert result["details"]["links"]["status"] == "error"

    # All scores should be 0
    assert result["scores"]["technical"] == 0.0
    assert result["scores"]["content"] == 0.0
    assert result["scores"]["links"] == 0.0
    assert result["scores"]["overall"] == 0.0
