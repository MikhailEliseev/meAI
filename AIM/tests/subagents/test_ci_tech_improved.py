"""
Tests for CI Tech Agent Improved - Real Technical SEO Audit
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from AIM.src.aim.subagents.competitive_intel.agents.ci_tech_improved import (
    CITechAgentImproved,
    PageSpeedResult,
    RobotsResult,
    SitemapResult,
    fetch_pagespeed,
    fetch_robots,
    fetch_sitemap,
    rate_metric,
)
from meai.agents.base_agent import Task


@pytest.fixture
def ci_tech_agent():
    """Create CI Tech Agent instance."""
    return CITechAgentImproved(
        agent_id="ci-tech-test",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_obsidian",
        pagespeed_api_key=None,
    )


@pytest.fixture
def sample_competitors():
    """Sample competitor data."""
    return [
        {"name": "Competitor A", "url": "https://example.com"},
        {"name": "Competitor B", "url": "https://example.org"},
    ]


# ============================================================================
# PageSpeed Tests
# ============================================================================


def test_rate_metric_lcp():
    """Test LCP metric rating."""
    assert rate_metric("lcp", 2000) == "good"  # < 2.5s
    assert rate_metric("lcp", 3000) == "needs-improvement"  # 2.5s - 4s
    assert rate_metric("lcp", 5000) == "poor"  # > 4s


def test_rate_metric_cls():
    """Test CLS metric rating."""
    assert rate_metric("cls", 0.05) == "good"  # < 0.1
    assert rate_metric("cls", 0.15) == "needs-improvement"  # 0.1 - 0.25
    assert rate_metric("cls", 0.3) == "poor"  # > 0.25


def test_rate_metric_inp():
    """Test INP metric rating."""
    assert rate_metric("inp", 150) == "good"  # < 200ms
    assert rate_metric("inp", 300) == "needs-improvement"  # 200ms - 500ms
    assert rate_metric("inp", 600) == "poor"  # > 500ms


@pytest.mark.asyncio
async def test_fetch_pagespeed_success():
    """Test successful PageSpeed fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.85},
                "seo": {"score": 0.92},
                "accessibility": {"score": 0.88},
                "best-practices": {"score": 0.90},
            },
            "audits": {
                "largest-contentful-paint": {"numericValue": 2300},
                "cumulative-layout-shift": {"numericValue": 0.08},
                "first-contentful-paint": {"numericValue": 1500},
            },
        },
        "loadingExperience": {
            "metrics": {
                "LARGEST_CONTENTFUL_PAINT_MS": {
                    "percentile": 2400,
                    "category": "FAST",
                },
                "CUMULATIVE_LAYOUT_SHIFT_SCORE": {
                    "percentile": 9,
                    "category": "FAST",
                },
                "INTERACTION_TO_NEXT_PAINT": {
                    "percentile": 180,
                    "category": "FAST",
                },
            }
        },
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_pagespeed("https://example.com")

        assert result.performance_score == 85
        assert result.seo_score == 92
        assert result.accessibility_score == 88
        assert result.best_practices_score == 90
        assert result.lcp_ms == 2300
        assert result.cls == 0.08
        assert result.fcp_ms == 1500
        assert result.has_field_data is True
        assert result.crux_lcp_ms == 2400
        assert result.crux_lcp_rating == "good"
        assert result.crux_cls == 0.09
        assert result.crux_cls_rating == "good"
        assert result.crux_inp_ms == 180
        assert result.crux_inp_rating == "good"


@pytest.mark.asyncio
async def test_fetch_pagespeed_rate_limited():
    """Test PageSpeed rate limit handling."""
    mock_response = MagicMock()
    mock_response.status_code = 429

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_pagespeed("https://example.com")

        assert result.error == "Rate limited (429). Set PAGESPEED_API_KEY for higher quota."


# ============================================================================
# Robots.txt Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_robots_success():
    """Test successful robots.txt fetch."""
    robots_content = """User-agent: *
Disallow: /admin/
Disallow: /private/

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = robots_content

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_robots("https://example.com")

        assert result.exists is True
        assert result.status_code == 200
        assert len(result.sitemap_directives) == 2
        assert "https://example.com/sitemap.xml" in result.sitemap_directives
        assert "GPTBot" in result.blocked_ai_crawlers
        assert "ClaudeBot" in result.blocked_ai_crawlers


@pytest.mark.asyncio
async def test_fetch_robots_blocks_css_js():
    """Test detection of CSS/JS blocking."""
    robots_content = """User-agent: *
Disallow: /*.css$
Disallow: /*.js$
Disallow: /static/
"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = robots_content

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_robots("https://example.com")

        assert result.blocks_css_js is True


@pytest.mark.asyncio
async def test_fetch_robots_not_found():
    """Test robots.txt not found."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_robots("https://example.com")

        assert result.exists is False
        assert result.status_code == 404


# ============================================================================
# Sitemap Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_sitemap_regular():
    """Test regular sitemap fetch."""
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page1</loc>
    <lastmod>2026-05-01</lastmod>
  </url>
  <url>
    <loc>https://example.com/page2</loc>
    <lastmod>2026-05-02</lastmod>
  </url>
</urlset>
"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = sitemap_xml.encode()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_sitemap("https://example.com/sitemap.xml")

        assert result.exists is True
        assert result.status_code == 200
        assert result.is_index is False
        assert result.url_count == 2


@pytest.mark.asyncio
async def test_fetch_sitemap_index():
    """Test sitemap index fetch."""
    sitemap_index_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap-1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap-2.xml</loc>
  </sitemap>
</sitemapindex>
"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = sitemap_index_xml.encode()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_sitemap("https://example.com/sitemap.xml")

        assert result.exists is True
        assert result.is_index is True
        assert len(result.child_sitemaps) == 2


# ============================================================================
# CI Tech Agent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ci_tech_agent_capabilities(ci_tech_agent):
    """Test agent capabilities."""
    capabilities = ci_tech_agent.get_capabilities()

    assert "core_web_vitals_analysis" in capabilities
    assert "pagespeed_insights_audit" in capabilities
    assert "playwright_spa_rendering" in capabilities
    assert "robots_txt_audit" in capabilities
    assert "sitemap_xml_audit" in capabilities
    assert "ai_crawler_detection" in capabilities
    assert "tech_maturity_scoring" in capabilities


@pytest.mark.asyncio
async def test_ci_tech_agent_execute_task(ci_tech_agent, sample_competitors):
    """Test agent task execution."""
    from meai.agents.base_agent import TaskStatus

    task = Task(
        task_id="test-task",
        subtask_id="test-subtask",
        parent_task_id="test-parent",
        action="analyze_tech",
        description="Test tech analysis",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
    )

    # Add payload to task (not in constructor)
    task.payload = {"competitors": sample_competitors}

    # Mock the audit methods
    with patch.object(
        ci_tech_agent, "_audit_competitor", new_callable=AsyncMock
    ) as mock_audit:
        mock_audit.return_value = {
            "name": "Test Competitor",
            "url": "https://example.com",
            "pagespeed": {
                "performance_score": 85,
                "seo_score": 92,
            },
            "robots": {
                "exists": True,
                "has_sitemap": True,
                "blocked_ai_crawlers": [],
                "blocks_css_js": False,
            },
            "sitemap": {
                "exists": True,
                "url_count": 100,
                "is_index": False,
            },
            "tech_score": {"total": 78.5, "rating": "high"},
        }

        result = await ci_tech_agent.execute_task(task)

        assert result.status == "success"
        assert result.result["total_analyzed"] == 2
        assert "audits" in result.result
        assert "insights" in result.result


def test_calculate_tech_score(ci_tech_agent):
    """Test tech score calculation."""
    pagespeed = PageSpeedResult(
        url="https://example.com",
        performance_score=85,
        seo_score=92,
        accessibility_score=88,
        best_practices_score=90,
    )

    robots = RobotsResult(
        exists=True,
        sitemap_directives=["https://example.com/sitemap.xml"],
        blocked_ai_crawlers=[],
        blocks_css_js=False,
    )

    sitemap = SitemapResult(
        url="https://example.com/sitemap.xml",
        exists=True,
        url_count=100,
    )

    score = ci_tech_agent._calculate_tech_score(pagespeed, robots, sitemap)

    assert score["total"] > 0
    assert score["rating"] in ["low", "medium", "high"]
    assert score["total"] >= 70  # Should be high with these good scores
    assert score["rating"] == "high"


def test_calculate_tech_score_with_penalties(ci_tech_agent):
    """Test tech score with penalties."""
    pagespeed = PageSpeedResult(
        url="https://example.com",
        performance_score=85,
        seo_score=92,
    )

    robots = RobotsResult(
        exists=True,
        blocked_ai_crawlers=["GPTBot", "ClaudeBot"],  # -10 penalty
        blocks_css_js=True,  # -5 penalty
    )

    sitemap = SitemapResult(exists=True, url_count=100)

    score = ci_tech_agent._calculate_tech_score(pagespeed, robots, sitemap)

    # Score should be reduced by penalties
    assert score["total"] < 100


def test_generate_insights(ci_tech_agent):
    """Test insights generation."""
    audits = [
        {
            "name": "Competitor A",
            "pagespeed": {"performance_score": 85},
            "robots": {"blocked_ai_crawlers": []},
            "sitemap": {"exists": True},
            "tech_score": {"total": 78.5},
        },
        {
            "name": "Competitor B",
            "pagespeed": {"performance_score": 72},
            "robots": {"blocked_ai_crawlers": ["GPTBot"]},
            "sitemap": {"exists": False},
            "tech_score": {"total": 65.0},
        },
    ]

    insights = ci_tech_agent._generate_insights(audits)

    assert "avg_performance_score" in insights
    assert "avg_tech_score" in insights
    assert "ai_crawler_blocking_rate" in insights
    assert "sitemap_adoption_rate" in insights
    assert "key_findings" in insights
    assert insights["avg_performance_score"] == 78.5  # (85 + 72) / 2
    assert insights["ai_crawler_blocking_rate"] == 50.0  # 1/2 * 100
    assert insights["sitemap_adoption_rate"] == 50.0  # 1/2 * 100
