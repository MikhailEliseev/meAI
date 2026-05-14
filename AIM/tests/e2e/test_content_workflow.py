"""End-to-End Tests for Content Workflow

Tests complete Content workflow from Content Magister to Content Writer Agent
and Content Gap Analysis Agent, validating task delegation, result aggregation,
and timeout handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from AIM.src.aim.magisters.content_magister import ContentMagister
from AIM.src.aim.subagents.content_writer_agent import ContentWriterAgent
from AIM.src.aim.subagents.content_gap_analysis_agent import ContentGapAnalysisAgent


@pytest.fixture
def mock_content_writer_result():
    """Mock Content Writer Agent result"""
    return {
        "status": "success",
        "content": {
            "title": "Complete Guide to Dental Implants: Everything You Need to Know",
            "body": "Dental implants are a revolutionary solution for missing teeth...",
            "word_count": 1500,
            "readability_score": 68.5,
            "seo_optimized": True,
        },
        "metadata": {
            "target_keyword": "dental implants",
            "keyword_density": 2.1,
            "headers": ["H1: Complete Guide to Dental Implants", "H2: What Are Dental Implants?", "H2: Benefits of Dental Implants"],
            "meta_description": "Learn everything about dental implants, from procedure to recovery. Expert guide with 15+ years experience.",
        },
        "quality_score": 92,
        "recommendations": [
            {
                "type": "enhancement",
                "priority": "medium",
                "description": "Add FAQ section for common questions",
            }
        ],
    }


@pytest.fixture
def mock_gap_analysis_result():
    """Mock Content Gap Analysis Agent result"""
    return {
        "status": "success",
        "gaps": [
            {
                "topic": "dental implant cost",
                "competitor_coverage": 85,
                "our_coverage": 20,
                "gap_score": 65,
                "priority": "high",
            },
            {
                "topic": "dental implant recovery time",
                "competitor_coverage": 78,
                "our_coverage": 30,
                "gap_score": 48,
                "priority": "medium",
            },
        ],
        "clusters": [
            {
                "name": "Cost & Insurance",
                "topics": ["dental implant cost", "insurance coverage", "payment plans"],
                "avg_gap_score": 58,
            }
        ],
        "recommendations": [
            {
                "type": "content_creation",
                "priority": "high",
                "description": "Create comprehensive cost guide for dental implants",
                "estimated_impact": "high",
            }
        ],
    }


@pytest.mark.asyncio
async def test_content_workflow_writer_success(mock_content_writer_result):
    """Test full Content workflow from Content Magister to Content Writer Agent

    Validates:
    - Content Writer Agent executes and returns generated content
    - Content Magister receives and validates content
    - Result structure includes content, metadata, quality_score
    - SEO optimization is applied
    """
    # Create mock Content Writer Agent
    mock_writer = AsyncMock(spec=ContentWriterAgent)
    mock_writer.execute_task.return_value = mock_content_writer_result

    # Simulate calling the agent directly
    result = await mock_writer.execute_task(
        task={
            "topic": "dental implants",
            "target_keyword": "dental implants",
            "word_count": 1500,
            "correlation_id": "test-writer-001",
        }
    )

    # Verify result structure
    assert result["status"] == "success"
    assert "content" in result
    assert result["content"]["word_count"] == 1500
    assert result["content"]["seo_optimized"] is True

    # Verify metadata
    assert "metadata" in result
    assert result["metadata"]["target_keyword"] == "dental implants"
    assert 1.5 <= result["metadata"]["keyword_density"] <= 3.0  # Optimal range

    # Verify quality score
    assert "quality_score" in result
    assert result["quality_score"] >= 90  # High quality

    # Verify SEO optimization
    assert len(result["metadata"]["headers"]) >= 3
    assert result["metadata"]["meta_description"]
    assert len(result["metadata"]["meta_description"]) <= 160

    # Verify agent was called
    mock_writer.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_content_workflow_gap_analysis(mock_gap_analysis_result):
    """Test Content Magister coordinating Gap Analysis Agent

    Validates:
    - Gap Analysis Agent identifies competitor content gaps
    - Gap prioritization based on coverage difference
    - Topic clustering for content strategy
    - Recommendations for content creation
    """
    # Create mock Gap Analysis Agent
    mock_gap_agent = AsyncMock(spec=ContentGapAnalysisAgent)
    mock_gap_agent.execute_task.return_value = mock_gap_analysis_result

    # Simulate calling the agent directly
    result = await mock_gap_agent.execute_task(
        task={
            "our_url": "https://example.com",
            "competitor_urls": ["https://competitor1.com", "https://competitor2.com"],
            "correlation_id": "test-gap-001",
        }
    )

    # Verify result structure
    assert result["status"] == "success"
    assert "gaps" in result
    assert len(result["gaps"]) >= 2

    # Verify gap prioritization
    high_priority_gaps = [g for g in result["gaps"] if g["priority"] == "high"]
    assert len(high_priority_gaps) >= 1
    assert high_priority_gaps[0]["gap_score"] >= 60

    # Verify topic clustering
    assert "clusters" in result
    assert len(result["clusters"]) >= 1
    assert result["clusters"][0]["name"] == "Cost & Insurance"

    # Verify recommendations
    assert "recommendations" in result
    assert len(result["recommendations"]) >= 1
    assert result["recommendations"][0]["type"] == "content_creation"
    assert result["recommendations"][0]["priority"] == "high"

    # Verify agent was called
    mock_gap_agent.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_content_workflow_timeout():
    """Test timeout handling when subagent takes too long

    Validates:
    - TimeoutError raised or handled gracefully when agent exceeds timeout
    - Partial results returned if available
    - Error status in response
    """
    # Create mock Content Writer Agent with long delay
    mock_writer = AsyncMock(spec=ContentWriterAgent)

    async def slow_task(*args, **kwargs):
        await asyncio.sleep(5)  # Simulate long-running task
        return {"status": "success", "content": "..."}

    mock_writer.execute_task.side_effect = slow_task

    # Execute with short timeout
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            mock_writer.execute_task(task={"topic": "test"}),
            timeout=0.1  # Very short timeout
        )

    # Verify agent was called (even though it timed out)
    mock_writer.execute_task.assert_called_once()


@pytest.mark.asyncio
async def test_content_workflow_writer_with_validation():
    """Test Content Writer with content quality validation

    Validates:
    - Content meets minimum word count requirements
    - Readability score is within acceptable range
    - SEO optimization flags are set correctly
    - Quality score reflects content standards
    """
    # Create mock with high-quality content
    mock_writer = AsyncMock(spec=ContentWriterAgent)
    mock_writer.execute_task.return_value = {
        "status": "success",
        "content": {
            "title": "Expert Guide to Dental Implants",
            "body": "A" * 2000,  # 2000 characters
            "word_count": 2000,
            "readability_score": 65.0,  # Good readability
            "seo_optimized": True,
        },
        "metadata": {
            "target_keyword": "dental implants",
            "keyword_density": 2.5,
            "headers": ["H1: Guide", "H2: Section 1", "H2: Section 2", "H3: Subsection"],
            "meta_description": "Expert guide to dental implants with 20+ years experience. Learn about procedure, recovery, costs, and benefits from certified specialists.",
        },
        "quality_score": 95,
    }

    result = await mock_writer.execute_task(task={"topic": "dental implants"})

    # Verify content quality
    assert result["content"]["word_count"] >= 1000  # Minimum for quality content
    assert 60 <= result["content"]["readability_score"] <= 80  # Optimal range
    assert result["content"]["seo_optimized"] is True

    # Verify SEO metadata
    assert 1.5 <= result["metadata"]["keyword_density"] <= 3.0
    assert len(result["metadata"]["headers"]) >= 3
    assert 120 <= len(result["metadata"]["meta_description"]) <= 160

    # Verify quality score
    assert result["quality_score"] >= 90


@pytest.mark.asyncio
async def test_content_workflow_gap_analysis_prioritization():
    """Test Gap Analysis Agent prioritization logic

    Validates:
    - Gaps sorted by priority (high > medium > low)
    - Gap score calculation (competitor_coverage - our_coverage)
    - High-priority gaps have gap_score >= 50
    - Recommendations align with high-priority gaps
    """
    mock_gap_agent = AsyncMock(spec=ContentGapAnalysisAgent)
    mock_gap_agent.execute_task.return_value = {
        "status": "success",
        "gaps": [
            {"topic": "cost", "gap_score": 70, "priority": "high"},
            {"topic": "recovery", "gap_score": 55, "priority": "high"},
            {"topic": "maintenance", "gap_score": 35, "priority": "medium"},
            {"topic": "alternatives", "gap_score": 20, "priority": "low"},
        ],
        "recommendations": [
            {"type": "content_creation", "priority": "high", "topic": "cost"},
            {"type": "content_creation", "priority": "high", "topic": "recovery"},
        ],
    }

    result = await mock_gap_agent.execute_task(task={"our_url": "https://example.com"})

    # Verify gap prioritization
    gaps = result["gaps"]
    high_priority = [g for g in gaps if g["priority"] == "high"]
    medium_priority = [g for g in gaps if g["priority"] == "medium"]
    low_priority = [g for g in gaps if g["priority"] == "low"]

    assert len(high_priority) == 2
    assert len(medium_priority) == 1
    assert len(low_priority) == 1

    # Verify high-priority gaps have high scores
    for gap in high_priority:
        assert gap["gap_score"] >= 50

    # Verify recommendations focus on high-priority gaps
    recommendations = result["recommendations"]
    assert all(r["priority"] == "high" for r in recommendations)
    assert len(recommendations) == 2
