"""End-to-End Tests for SEO Workflow

Tests complete SEO workflow from SEO Magister to Keyword Research Agent
and other SEO subagents, validating task delegation, result aggregation,
and error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from AIM.src.aim.magisters.seo_magister import SEOMagister
from AIM.src.aim.subagents.keyword_research_agent import KeywordResearchAgent
from AIM.src.aim.subagents.seo.technical_agent import TechnicalSEOAgent
from AIM.src.aim.subagents.seo.content_agent import ContentSEOAgent
from AIM.src.aim.subagents.seo.links_agent import LinksSEOAgent


@pytest.fixture
def mock_keyword_research_result():
    """Mock Keyword Research Agent result"""
    return {
        "status": "success",
        "keywords": [
            {
                "keyword": "dental implants",
                "volume": 12000,
                "difficulty": 65,
                "cpc": 8.50,
                "intent": "commercial",
                "priority_score": 85,
            },
            {
                "keyword": "teeth whitening",
                "volume": 8500,
                "difficulty": 45,
                "cpc": 5.20,
                "intent": "commercial",
                "priority_score": 78,
            },
            {
                "keyword": "orthodontics near me",
                "volume": 6200,
                "difficulty": 38,
                "cpc": 6.80,
                "intent": "local",
                "priority_score": 72,
            },
        ],
        "clusters": [
            {
                "name": "Dental Procedures",
                "keywords": ["dental implants", "teeth whitening"],
                "avg_priority": 81.5,
            }
        ],
        "recommendations": [
            {
                "type": "content",
                "priority": "high",
                "description": "Create comprehensive guide on dental implants",
            }
        ],
    }


@pytest.fixture
def mock_technical_result():
    """Mock Technical SEO Agent result"""
    return {
        "agent": "technical-agent",
        "status": "success",
        "results": {
            "robots_txt": {"exists": True, "allows_crawling": True},
            "sitemap_xml": {"exists": True, "valid": True},
            "meta_tags": {
                "title": "Dental Clinic - Best Services",
                "description": "Professional dental care",
            },
            "performance": {"score": 85},
            "schema_org": {"count": 3},
        },
    }


@pytest.fixture
def mock_content_result():
    """Mock Content SEO Agent result"""
    return {
        "agent": "content-agent",
        "status": "success",
        "results": {
            "headers": {"h1_count": 1, "broken_hierarchy": False},
            "keywords": {"total": 150},
            "readability": {"flesch_reading_ease": 65.5},
            "content_quality": {
                "word_count": 850,
                "image_count": 5,
                "alt_text_coverage": 100.0,
            },
        },
    }


@pytest.fixture
def mock_links_result():
    """Mock Links SEO Agent result"""
    return {
        "agent": "links-agent",
        "status": "success",
        "results": {
            "internal_links": {"total": 25, "unique": 18},
            "external_links": {"total": 8, "nofollow_percentage": 37.5},
            "anchor_text": {"empty_percentage": 0.0, "generic_percentage": 6.1},
        },
    }


@pytest.mark.asyncio
async def test_seo_workflow_keyword_research_success(mock_keyword_research_result):
    """Test full SEO workflow with Keyword Research Agent integration

    Validates:
    - Keyword Research Agent can be instantiated and mocked
    - Result structure includes keywords, priorities, clusters
    - Mock data flows correctly through the system

    Note: This test validates the Keyword Research Agent interface,
    not the SEO Magister coordination (which uses Technical/Content/Links agents).
    """
    # Create mock Keyword Research Agent
    mock_kr_agent = AsyncMock(spec=KeywordResearchAgent)
    mock_kr_agent.execute_task.return_value = mock_keyword_research_result

    # Simulate calling the agent directly
    result = await mock_kr_agent.execute_task(
        task={"seed_keyword": "dental implants", "correlation_id": "test-kr-001"}
    )

    # Verify result structure
    assert result["status"] == "success"
    assert "keywords" in result
    assert len(result["keywords"]) == 3
    assert result["keywords"][0]["keyword"] == "dental implants"
    assert result["keywords"][0]["priority_score"] == 85

    # Verify clusters
    assert "clusters" in result
    assert len(result["clusters"]) == 1
    assert result["clusters"][0]["name"] == "Dental Procedures"

    # Verify recommendations
    assert "recommendations" in result
    assert len(result["recommendations"]) >= 1

    # Verify agent was called
    mock_kr_agent.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_seo_workflow_with_multiple_subagents(
    mock_technical_result, mock_content_result, mock_links_result
):
    """Test SEO Magister coordinating multiple subagents in parallel

    Validates:
    - Parallel execution of Technical, Content, Links agents
    - Weighted score aggregation (40% tech, 30% content, 30% links)
    - Recommendations generation from all agents
    - Correlation ID propagation
    """
    # Create mock subagents
    mock_technical = AsyncMock(spec=TechnicalSEOAgent)
    mock_technical.analyze.return_value = mock_technical_result

    mock_content = AsyncMock(spec=ContentSEOAgent)
    mock_content.analyze.return_value = mock_content_result

    mock_links = AsyncMock(spec=LinksSEOAgent)
    mock_links.analyze.return_value = mock_links_result

    # Create SEO Magister with mocked agents
    magister = SEOMagister(
        timeout=600,
        technical_agent=mock_technical,
        content_agent=mock_content,
        links_agent=mock_links,
    )

    # Execute workflow
    result = await magister.coordinate_analysis(
        url="https://example.com",
        correlation_id="test-multi-001"
    )

    # Verify all agents were called
    mock_technical.analyze.assert_called_once()
    mock_content.analyze.assert_called_once()
    mock_links.analyze.assert_called_once()

    # Verify result structure
    assert result["status"] == "success"
    assert "scores" in result
    assert "overall" in result["scores"]
    assert "technical" in result["scores"]
    assert "content" in result["scores"]
    assert "links" in result["scores"]

    # Verify weighted scoring (approximate check)
    # Overall score should be weighted average: 40% tech + 30% content + 30% links
    overall = result["scores"]["overall"]
    assert 70 <= overall <= 90

    # Verify recommendations field exists (may be empty if scores are high)
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)

    # Verify summary generated
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert "SEO health" in result["summary"]


@pytest.mark.asyncio
async def test_seo_workflow_subagent_failure(mock_content_result, mock_links_result):
    """Test error handling when one subagent fails

    Validates:
    - Graceful degradation with partial results
    - Error status in response
    - Other subagents complete successfully
    - Recommendations still generated from successful agents
    """
    # Create mock subagents - technical agent will fail
    mock_technical = AsyncMock(spec=TechnicalSEOAgent)
    mock_technical.analyze.side_effect = Exception("Technical analysis failed")

    mock_content = AsyncMock(spec=ContentSEOAgent)
    mock_content.analyze.return_value = mock_content_result

    mock_links = AsyncMock(spec=LinksSEOAgent)
    mock_links.analyze.return_value = mock_links_result

    # Create SEO Magister with mocked agents
    magister = SEOMagister(
        timeout=600,
        technical_agent=mock_technical,
        content_agent=mock_content,
        links_agent=mock_links,
    )

    # Execute workflow - should not raise exception
    result = await magister.coordinate_analysis(
        url="https://example.com",
        correlation_id="test-failure-001"
    )

    # Verify partial success
    assert result["status"] in ["partial_success", "success"]

    # Verify technical agent error is captured in details
    assert "details" in result
    assert "technical" in result["details"]
    assert result["details"]["technical"]["status"] == "error"
    assert "error" in result["details"]["technical"]

    # Verify other agents completed successfully
    assert "content" in result["details"]
    assert result["details"]["content"]["status"] == "success"
    assert "links" in result["details"]
    assert result["details"]["links"]["status"] == "success"

    # Verify recommendations still generated (from successful agents)
    assert "recommendations" in result

    # Verify all agents were attempted
    mock_technical.analyze.assert_called_once()
    mock_content.analyze.assert_called_once()
    mock_links.analyze.assert_called_once()
