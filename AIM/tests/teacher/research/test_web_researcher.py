"""
Tests for WebResearcher.
"""

import pytest

from AIM.src.aim.teacher.research.web_researcher import (
    WebResearcher,
    ResearchDepth,
    WebResearchResult,
)


@pytest.fixture
def web_researcher():
    """Create WebResearcher instance."""
    return WebResearcher()


@pytest.mark.asyncio
async def test_quick_research(web_researcher):
    """Test quick research (5-10 min, ~$0.50)."""
    result = await web_researcher.research(
        topic="SEO analysis Python",
        depth=ResearchDepth.QUICK,
        focus=["tools", "libraries"],
    )

    assert isinstance(result, WebResearchResult)
    assert len(result.best_practices) > 0
    assert len(result.tools) > 0
    assert result.cost == 0.50


@pytest.mark.asyncio
async def test_standard_research(web_researcher):
    """Test standard research (10-20 min, ~$1.50)."""
    result = await web_researcher.research(
        topic="SEO analysis Python",
        depth=ResearchDepth.STANDARD,
        focus=["best practices", "tools", "patterns"],
    )

    assert isinstance(result, WebResearchResult)
    assert len(result.best_practices) >= 5
    assert len(result.tools) >= 4
    assert len(result.insights) >= 3
    assert result.cost == 1.50


@pytest.mark.asyncio
async def test_deep_research(web_researcher):
    """Test deep research (20-40 min, ~$3.00)."""
    result = await web_researcher.research(
        topic="SEO analysis Python",
        depth=ResearchDepth.DEEP,
        focus=["best practices", "tools", "patterns", "security"],
    )

    assert isinstance(result, WebResearchResult)
    assert len(result.best_practices) >= 8
    assert len(result.tools) >= 6
    assert len(result.insights) >= 5
    assert result.cost == 3.00


@pytest.mark.asyncio
async def test_research_with_default_focus(web_researcher):
    """Test research with default focus areas."""
    result = await web_researcher.research(
        topic="keyword research",
        depth=ResearchDepth.QUICK,
    )

    # Should use default focus: ["best practices", "tools", "libraries", "patterns"]
    assert isinstance(result, WebResearchResult)
    assert len(result.best_practices) > 0


@pytest.mark.asyncio
async def test_research_result_structure(web_researcher):
    """Test that research result has correct structure."""
    result = await web_researcher.research(
        topic="content gap analysis",
        depth=ResearchDepth.STANDARD,
    )

    assert hasattr(result, "best_practices")
    assert hasattr(result, "tools")
    assert hasattr(result, "insights")
    assert hasattr(result, "sources")
    assert hasattr(result, "cost")

    assert isinstance(result.best_practices, list)
    assert isinstance(result.tools, list)
    assert isinstance(result.insights, list)
    assert isinstance(result.sources, list)
    assert isinstance(result.cost, float)


@pytest.mark.asyncio
async def test_quick_research_cheaper_than_standard(web_researcher):
    """Test that quick research is cheaper than standard."""
    quick = await web_researcher.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    standard = await web_researcher.research(
        topic="test",
        depth=ResearchDepth.STANDARD,
    )

    assert quick.cost < standard.cost


@pytest.mark.asyncio
async def test_standard_research_cheaper_than_deep(web_researcher):
    """Test that standard research is cheaper than deep."""
    standard = await web_researcher.research(
        topic="test",
        depth=ResearchDepth.STANDARD,
    )

    deep = await web_researcher.research(
        topic="test",
        depth=ResearchDepth.DEEP,
    )

    assert standard.cost < deep.cost


@pytest.mark.asyncio
async def test_deep_research_more_comprehensive(web_researcher):
    """Test that deep research returns more comprehensive results."""
    quick = await web_researcher.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    deep = await web_researcher.research(
        topic="test",
        depth=ResearchDepth.DEEP,
    )

    assert len(deep.best_practices) > len(quick.best_practices)
    assert len(deep.tools) > len(quick.tools)
    assert len(deep.insights) > len(quick.insights)


@pytest.mark.asyncio
async def test_research_sources_included(web_researcher):
    """Test that research includes source URLs."""
    result = await web_researcher.research(
        topic="technical SEO",
        depth=ResearchDepth.STANDARD,
    )

    assert len(result.sources) > 0
    # Mock sources should be URLs
    for source in result.sources:
        assert source.startswith("https://")


@pytest.mark.asyncio
async def test_multiple_research_calls(web_researcher):
    """Test multiple research calls work correctly."""
    result1 = await web_researcher.research(
        topic="topic1",
        depth=ResearchDepth.QUICK,
    )

    result2 = await web_researcher.research(
        topic="topic2",
        depth=ResearchDepth.STANDARD,
    )

    # Both should succeed
    assert isinstance(result1, WebResearchResult)
    assert isinstance(result2, WebResearchResult)

    # Should have different costs
    assert result1.cost != result2.cost


@pytest.mark.asyncio
async def test_research_with_custom_focus(web_researcher):
    """Test research with custom focus areas."""
    result = await web_researcher.research(
        topic="performance optimization",
        depth=ResearchDepth.STANDARD,
        focus=["caching", "database", "async"],
    )

    assert isinstance(result, WebResearchResult)
    assert len(result.best_practices) > 0
