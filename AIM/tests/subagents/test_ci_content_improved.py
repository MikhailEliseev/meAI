"""
Tests for CI Content Agent (Improved with trafilatura)
"""

import pytest
from pathlib import Path
from datetime import datetime

from AIM.src.aim.subagents.competitive_intel.agents.ci_content_improved import (
    CIContentAgentImproved,
    PageAnalyzer,
)
from meai.agents.base_agent import Task, TaskStatus


@pytest.mark.asyncio
async def test_page_analyzer_with_real_url():
    """Test PageAnalyzer with a real URL."""
    # Use a simple, stable URL for testing
    url = "https://example.com"

    analyzer = PageAnalyzer(url)
    success = await analyzer.analyze()

    assert success is True
    assert analyzer.url == url
    assert analyzer.content_hash != ""
    assert analyzer.total_word_count > 0

    # Check extracted data
    result = analyzer.as_dict()
    assert "url" in result
    assert "word_count" in result
    assert result["word_count"] > 0


@pytest.mark.asyncio
async def test_page_analyzer_quality_score():
    """Test quality score calculation."""
    url = "https://example.com"

    analyzer = PageAnalyzer(url)
    await analyzer.analyze()

    # Create agent to access scoring methods
    agent = CIContentAgentImproved(
        agent_id="test-ci-content",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    quality_score = agent._calculate_quality_score(analyzer)
    seo_score = agent._calculate_seo_score(analyzer)

    assert 0 <= quality_score <= 100
    assert 0 <= seo_score <= 100

    print(f"\nQuality score: {quality_score}")
    print(f"SEO score: {seo_score}")
    print(f"Word count: {analyzer.total_word_count}")
    print(f"Title: {analyzer.title}")
    print(f"Description: {analyzer.description}")


@pytest.mark.asyncio
async def test_ci_content_agent_improved():
    """Test CI Content Agent Improved with real analysis."""
    agent = CIContentAgentImproved(
        agent_id="test-ci-content",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    # Create task with competitors
    task = Task(
        task_id="test-task-1",
        subtask_id="test-subtask-1",
        parent_task_id="test-parent-1",
        action="analyze_content",
        description="Analyze competitor content",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
        data={
            "competitors": [
                {
                    "name": "Example Site",
                    "url": "https://example.com"
                }
            ],
            "niche": "test"
        }
    )

    # Execute task
    result = await agent.execute_task(task)

    assert result.status == "success"
    assert "content_profiles" in result.result
    assert len(result.result["content_profiles"]) == 1

    # Check profile
    profile = result.result["content_profiles"][0]
    assert profile["name"] == "Example Site"
    assert profile["url"] == "https://example.com"
    assert profile["word_count"] > 0
    assert 0 <= profile["quality_score"] <= 100
    assert 0 <= profile["seo_score"] <= 100

    print(f"\n=== Content Profile ===")
    print(f"Name: {profile['name']}")
    print(f"Word count: {profile['word_count']}")
    print(f"Quality score: {profile['quality_score']}")
    print(f"SEO score: {profile['seo_score']}")
    print(f"Content maturity: {profile['content_maturity']}")

    # Check market analysis
    assert "market_analysis" in result.result
    market = result.result["market_analysis"]
    print(f"\n=== Market Analysis ===")
    print(f"Avg word count: {market['avg_word_count']}")
    print(f"Avg quality: {market['avg_quality_score']}")
    print(f"Avg SEO: {market['avg_seo_score']}")


@pytest.mark.asyncio
async def test_ci_content_agent_multiple_competitors():
    """Test with multiple competitors."""
    agent = CIContentAgentImproved(
        agent_id="test-ci-content",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    task = Task(
        task_id="test-task-2",
        subtask_id="test-subtask-2",
        parent_task_id="test-parent-2",
        action="analyze_content",
        description="Analyze multiple competitors",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
        data={
            "competitors": [
                {"name": "Example 1", "url": "https://example.com"},
                {"name": "Example 2", "url": "https://example.org"},
            ],
            "niche": "test"
        }
    )

    result = await agent.execute_task(task)

    assert result.status == "success"
    assert len(result.result["content_profiles"]) == 2

    # Check leaders
    assert "content_leaders" in result.result
    leaders = result.result["content_leaders"]
    assert "quality_leaders" in leaders
    assert "seo_leaders" in leaders

    print(f"\n=== Content Leaders ===")
    print(f"Quality leaders: {len(leaders['quality_leaders'])}")
    print(f"SEO leaders: {len(leaders['seo_leaders'])}")


@pytest.mark.asyncio
async def test_ci_content_agent_no_url():
    """Test handling of competitor without URL."""
    agent = CIContentAgentImproved(
        agent_id="test-ci-content",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    task = Task(
        task_id="test-task-3",
        subtask_id="test-subtask-3",
        parent_task_id="test-parent-3",
        action="analyze_content",
        description="Analyze competitor without URL",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
        data={
            "competitors": [
                {"name": "No URL Competitor"}  # No URL provided
            ],
            "niche": "test"
        }
    )

    result = await agent.execute_task(task)

    assert result.status == "success"
    profile = result.result["content_profiles"][0]

    # Should have empty profile
    assert profile["name"] == "No URL Competitor"
    assert profile["url"] == ""
    assert profile["word_count"] == 0
    assert profile["quality_score"] == 0
    assert profile["content_maturity"] == "minimal"
    assert "No URL provided" in profile["warnings"]


def test_agent_capabilities():
    """Test agent capabilities."""
    agent = CIContentAgentImproved(
        agent_id="test-ci-content",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    capabilities = agent.get_capabilities()

    assert "real_content_extraction" in capabilities
    assert "trafilatura_analysis" in capabilities
    assert "content_quality_assessment" in capabilities
    assert "seo_content_analysis" in capabilities
    assert "metadata_extraction" in capabilities
    assert "heading_structure_analysis" in capabilities
