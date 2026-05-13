"""
Tests for ResearchOrchestrator.
"""

import pytest
from datetime import datetime

from AIM.src.aim.teacher.research.research_orchestrator import (
    ResearchOrchestrator,
    ResearchFindings,
)
from AIM.src.aim.teacher.research.web_researcher import ResearchDepth


@pytest.fixture
def orchestrator():
    """Create ResearchOrchestrator instance."""
    return ResearchOrchestrator()


@pytest.mark.asyncio
async def test_research_returns_findings(orchestrator):
    """Test that research returns complete findings."""
    findings = await orchestrator.research(
        topic="SEO analysis Python",
        depth=ResearchDepth.QUICK,
    )

    assert isinstance(findings, ResearchFindings)
    assert len(findings.best_practices) > 0
    assert len(findings.tools) > 0
    assert len(findings.insights) > 0
    assert len(findings.web_sources) > 0
    assert len(findings.top_repos) > 0


@pytest.mark.asyncio
async def test_research_with_standard_depth(orchestrator):
    """Test research with standard depth."""
    findings = await orchestrator.research(
        topic="keyword research",
        depth=ResearchDepth.STANDARD,
    )

    assert findings.research_depth == "standard"
    assert findings.total_cost == 1.50  # Standard research cost
    assert len(findings.best_practices) >= 5
    assert len(findings.tools) >= 4


@pytest.mark.asyncio
async def test_research_with_deep_depth(orchestrator):
    """Test research with deep depth."""
    findings = await orchestrator.research(
        topic="content gap analysis",
        depth=ResearchDepth.DEEP,
    )

    assert findings.research_depth == "deep"
    assert findings.total_cost == 3.00  # Deep research cost
    assert len(findings.best_practices) >= 8
    assert len(findings.tools) >= 6


@pytest.mark.asyncio
async def test_research_with_custom_focus(orchestrator):
    """Test research with custom focus areas."""
    findings = await orchestrator.research(
        topic="technical SEO",
        depth=ResearchDepth.STANDARD,
        focus=["crawling", "indexing", "performance"],
    )

    assert isinstance(findings, ResearchFindings)
    assert len(findings.best_practices) > 0


@pytest.mark.asyncio
async def test_research_with_github_filters(orchestrator):
    """Test research with GitHub filters."""
    findings = await orchestrator.research(
        topic="SEO tools",
        depth=ResearchDepth.QUICK,
        github_language="JavaScript",
        github_min_stars=500,
        github_max_results=5,
    )

    assert len(findings.top_repos) <= 5
    # All repos should be JavaScript
    for repo_score in findings.top_repos:
        assert repo_score.repo.language == "JavaScript"
        assert repo_score.repo.stars >= 500


@pytest.mark.asyncio
async def test_research_findings_structure(orchestrator):
    """Test that ResearchFindings has correct structure."""
    findings = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    assert hasattr(findings, "best_practices")
    assert hasattr(findings, "tools")
    assert hasattr(findings, "insights")
    assert hasattr(findings, "web_sources")
    assert hasattr(findings, "top_repos")
    assert hasattr(findings, "research_depth")
    assert hasattr(findings, "total_cost")
    assert hasattr(findings, "duration_seconds")
    assert hasattr(findings, "timestamp")

    assert isinstance(findings.best_practices, list)
    assert isinstance(findings.tools, list)
    assert isinstance(findings.insights, list)
    assert isinstance(findings.web_sources, list)
    assert isinstance(findings.top_repos, list)
    assert isinstance(findings.research_depth, str)
    assert isinstance(findings.total_cost, float)
    assert isinstance(findings.duration_seconds, float)
    assert isinstance(findings.timestamp, datetime)


@pytest.mark.asyncio
async def test_research_duration_tracked(orchestrator):
    """Test that research duration is tracked."""
    findings = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    # Duration should be > 0 (research takes time)
    assert findings.duration_seconds > 0


@pytest.mark.asyncio
async def test_research_timestamp_set(orchestrator):
    """Test that research timestamp is set."""
    before = datetime.now()
    findings = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )
    after = datetime.now()

    # Timestamp should be between before and after
    assert before <= findings.timestamp <= after


@pytest.mark.asyncio
async def test_repos_ranked_by_quality(orchestrator):
    """Test that GitHub repos are ranked by quality."""
    findings = await orchestrator.research(
        topic="SEO analysis",
        depth=ResearchDepth.QUICK,
        github_max_results=10,
    )

    # Repos should be sorted by total_score (descending)
    for i in range(len(findings.top_repos) - 1):
        assert findings.top_repos[i].total_score >= findings.top_repos[i + 1].total_score


@pytest.mark.asyncio
async def test_format_findings(orchestrator):
    """Test formatting findings as markdown."""
    findings = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    markdown = orchestrator.format_findings(findings)

    assert isinstance(markdown, str)
    assert "# Research Findings" in markdown
    assert "## Best Practices" in markdown
    assert "## Tools & Libraries" in markdown
    assert "## Industry Insights" in markdown
    assert "## Top GitHub Repositories" in markdown
    assert "## Web Sources" in markdown
    assert f"**Cost:** ${findings.total_cost:.2f}" in markdown


@pytest.mark.asyncio
async def test_quick_cheaper_than_standard(orchestrator):
    """Test that quick research is cheaper than standard."""
    quick = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    standard = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.STANDARD,
    )

    assert quick.total_cost < standard.total_cost


@pytest.mark.asyncio
async def test_standard_cheaper_than_deep(orchestrator):
    """Test that standard research is cheaper than deep."""
    standard = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.STANDARD,
    )

    deep = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.DEEP,
    )

    assert standard.total_cost < deep.total_cost


@pytest.mark.asyncio
async def test_deep_more_comprehensive(orchestrator):
    """Test that deep research returns more comprehensive results."""
    quick = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.QUICK,
    )

    deep = await orchestrator.research(
        topic="test",
        depth=ResearchDepth.DEEP,
    )

    assert len(deep.best_practices) > len(quick.best_practices)
    assert len(deep.tools) > len(quick.tools)
    assert len(deep.insights) > len(quick.insights)


@pytest.mark.asyncio
async def test_multiple_research_calls(orchestrator):
    """Test multiple research calls work correctly."""
    findings1 = await orchestrator.research(
        topic="topic1",
        depth=ResearchDepth.QUICK,
    )

    findings2 = await orchestrator.research(
        topic="topic2",
        depth=ResearchDepth.STANDARD,
    )

    # Both should succeed
    assert isinstance(findings1, ResearchFindings)
    assert isinstance(findings2, ResearchFindings)

    # Should have different costs
    assert findings1.total_cost != findings2.total_cost
