"""End-to-end test for SEO Analysis Workflow.

Tests the complete workflow from SEO Magister to three subagents.
Uses direct agent mocking for reliability.
"""

import pytest
from unittest.mock import AsyncMock, patch

from aim.magisters.seo_magister import SEOMagister


@pytest.fixture
def sample_technical_result():
    """Sample technical agent result."""
    return {
        "agent": "technical-agent",
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-09T13:00:00Z",
        "duration_seconds": 5.2,
        "results": {
            "robots_txt": {
                "exists": True,
                "allows_crawling": True
            },
            "sitemap_xml": {
                "exists": True,
                "valid": True
            },
            "meta_tags": {
                "title": "Medical Clinic - Best Healthcare Services",
                "description": "Professional medical services with experienced doctors."
            },
            "performance": {
                "score": 85
            },
            "schema_org": {
                "count": 3
            }
        }
    }


@pytest.fixture
def sample_content_result():
    """Sample content agent result."""
    return {
        "agent": "content-agent",
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-09T13:00:00Z",
        "duration_seconds": 3.8,
        "results": {
            "headers": {
                "h1_count": 1,
                "broken_hierarchy": False
            },
            "keywords": {
                "total": 150
            },
            "readability": {
                "flesch_reading_ease": 65.5
            },
            "content_quality": {
                "word_count": 850,
                "image_count": 5,
                "alt_text_coverage": 100.0
            },
            "structure": {
                "semantic_score": 85
            }
        }
    }


@pytest.fixture
def sample_links_result():
    """Sample links agent result."""
    return {
        "agent": "links-agent",
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-09T13:00:00Z",
        "duration_seconds": 4.5,
        "results": {
            "internal_links": {
                "total": 25,
                "unique": 18
            },
            "external_links": {
                "total": 8,
                "nofollow_percentage": 37.5
            },
            "anchor_text": {
                "empty_percentage": 0.0,
                "generic_percentage": 6.1
            },
            "broken_links": {
                "broken_percentage": 0.0
            }
        }
    }


@pytest.mark.asyncio
async def test_seo_workflow_end_to_end(
    sample_technical_result, sample_content_result, sample_links_result
):
    """Test complete SEO analysis workflow.

    Workflow:
    1. SEO Magister receives analysis request
    2. Dispatches three agents in parallel
    3. Aggregates results with weighted scoring
    4. Generates recommendations and summary
    5. Returns comprehensive report
    """
    magister = SEOMagister(timeout=60)

    # Mock all three agents
    with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
         patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
         patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

        mock_tech.return_value = sample_technical_result
        mock_content.return_value = sample_content_result
        mock_links.return_value = sample_links_result

        result = await magister.coordinate_analysis(
            url="https://example.com",
            correlation_id="e2e-test-123"
        )

    # Verify result structure
    assert result["status"] == "success"
    assert result["url"] == "https://example.com"
    assert result["correlation_id"] == "e2e-test-123"
    assert "timestamp" in result
    assert result["duration_seconds"] >= 0

    # Verify scores
    scores = result["scores"]
    assert "overall" in scores
    assert "technical" in scores
    assert "content" in scores
    assert "links" in scores

    # All scores should be between 0 and 100
    assert 0 <= scores["overall"] <= 100
    assert 0 <= scores["technical"] <= 100
    assert 0 <= scores["content"] <= 100
    assert 0 <= scores["links"] <= 100

    # Verify weighted scoring (40% tech, 30% content, 30% links)
    expected_overall = (
        scores["technical"] * 0.4 +
        scores["content"] * 0.3 +
        scores["links"] * 0.3
    )
    assert abs(scores["overall"] - expected_overall) < 0.1

    # Verify summary
    assert "summary" in result
    assert len(result["summary"]) > 0
    assert "SEO health" in result["summary"]

    # Verify recommendations
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)

    # Each recommendation should have required fields
    for rec in result["recommendations"]:
        assert "priority" in rec
        assert "category" in rec
        assert "issue" in rec
        assert "action" in rec
        assert rec["priority"] in ["high", "medium", "low"]
        assert rec["category"] in ["technical", "content", "links"]

    # Verify details from all three agents
    details = result["details"]
    assert "technical" in details
    assert "content" in details
    assert "links" in details

    assert details["technical"]["status"] == "success"
    assert details["content"]["status"] == "success"
    assert details["links"]["status"] == "success"

    # Verify all agents were called
    mock_tech.assert_called_once_with("https://example.com", "e2e-test-123")
    mock_content.assert_called_once_with("https://example.com", "e2e-test-123")
    mock_links.assert_called_once_with("https://example.com", "e2e-test-123")


@pytest.mark.asyncio
async def test_seo_workflow_with_poor_site():
    """Test workflow with a poorly optimized site."""
    magister = SEOMagister(timeout=60)

    # Poor results from all agents
    poor_technical = {
        "agent": "technical-agent",
        "status": "success",
        "results": {
            "robots_txt": {"exists": False},
            "sitemap_xml": {"exists": False},
            "meta_tags": {"title": "", "description": ""},
            "performance": {"score": 20},
            "schema_org": {"count": 0}
        }
    }

    poor_content = {
        "agent": "content-agent",
        "status": "success",
        "results": {
            "headers": {"h1_count": 0, "broken_hierarchy": True},
            "readability": {"flesch_reading_ease": 20},
            "content_quality": {
                "word_count": 50,
                "image_count": 0,
                "alt_text_coverage": 0
            },
            "structure": {"semantic_score": 20}
        }
    }

    poor_links = {
        "agent": "links-agent",
        "status": "success",
        "results": {
            "internal_links": {"total": 2, "unique": 2},
            "external_links": {"total": 1, "nofollow_percentage": 100},
            "anchor_text": {
                "empty_percentage": 50,
                "generic_percentage": 80
            },
            "broken_links": {"broken_percentage": 30}
        }
    }

    with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
         patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
         patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

        mock_tech.return_value = poor_technical
        mock_content.return_value = poor_content
        mock_links.return_value = poor_links

        result = await magister.coordinate_analysis("https://example.com")

    # Should succeed
    assert result["status"] == "success"

    # Should have low scores
    assert result["scores"]["overall"] < 50
    assert result["scores"]["technical"] < 50
    assert result["scores"]["content"] < 50
    assert result["scores"]["links"] < 50

    # Should have many recommendations
    assert len(result["recommendations"]) >= 5

    # Should have high priority recommendations
    high_priority = [r for r in result["recommendations"] if r["priority"] == "high"]
    assert len(high_priority) > 0


@pytest.mark.asyncio
async def test_seo_workflow_parallel_execution():
    """Test that three agents execute in parallel, not sequentially."""
    import asyncio
    import time

    magister = SEOMagister(timeout=60)

    # Mock agents with different execution times
    async def slow_technical(*args, **kwargs):
        await asyncio.sleep(0.3)
        return {"agent": "technical-agent", "status": "success", "results": {}}

    async def slow_content(*args, **kwargs):
        await asyncio.sleep(0.2)
        return {"agent": "content-agent", "status": "success", "results": {}}

    async def slow_links(*args, **kwargs):
        await asyncio.sleep(0.1)
        return {"agent": "links-agent", "status": "success", "results": {}}

    with patch.object(magister.technical_agent, 'analyze', side_effect=slow_technical), \
         patch.object(magister.content_agent, 'analyze', side_effect=slow_content), \
         patch.object(magister.links_agent, 'analyze', side_effect=slow_links):

        start = time.time()
        result = await magister.coordinate_analysis("https://example.com")
        duration = time.time() - start

    # If sequential: 0.3 + 0.2 + 0.1 = 0.6 seconds
    # If parallel: max(0.3, 0.2, 0.1) = 0.3 seconds
    # Allow some overhead, but should be much closer to 0.3 than 0.6
    assert duration < 0.5  # Parallel execution
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_seo_workflow_with_agent_failure(sample_content_result, sample_links_result):
    """Test workflow when one agent fails."""
    magister = SEOMagister(timeout=60)

    # Technical agent fails, others succeed
    with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
         patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
         patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

        mock_tech.side_effect = Exception("Network error")
        mock_content.return_value = sample_content_result
        mock_links.return_value = sample_links_result

        result = await magister.coordinate_analysis("https://example.com")

    # Should still succeed with partial results
    assert result["status"] == "success"
    assert result["details"]["technical"]["status"] == "error"
    assert result["details"]["content"]["status"] == "success"
    assert result["details"]["links"]["status"] == "success"

    # Technical score should be 0
    assert result["scores"]["technical"] == 0.0
    assert result["scores"]["content"] > 0
    assert result["scores"]["links"] > 0


@pytest.mark.asyncio
async def test_seo_workflow_correlation_id_generation(
    sample_technical_result, sample_content_result, sample_links_result
):
    """Test that correlation ID is auto-generated if not provided."""
    magister = SEOMagister(timeout=60)

    with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
         patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
         patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

        mock_tech.return_value = sample_technical_result
        mock_content.return_value = sample_content_result
        mock_links.return_value = sample_links_result

        result = await magister.coordinate_analysis("https://example.com")

    # Should have auto-generated correlation ID
    assert "correlation_id" in result
    assert result["correlation_id"].startswith("seo-analysis-")
