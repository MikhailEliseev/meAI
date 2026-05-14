"""Unit tests for Technical SEO Agent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from AIM.src.aim.subagents.seo.technical_agent import TechnicalSEOAgent


@pytest.fixture
def agent():
    """Create Technical SEO Agent instance."""
    return TechnicalSEOAgent()


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Example Medical Clinic</title>
        <meta name="description" content="Best medical clinic in town">
        <meta name="keywords" content="medical, clinic, healthcare">
        <meta property="og:title" content="Example Clinic">
        <meta property="og:description" content="Medical services">
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "MedicalClinic",
            "name": "Example Clinic"
        }
        </script>
    </head>
    <body>
        <h1>Welcome</h1>
    </body>
    </html>
    """


@pytest.fixture
def sample_robots_txt():
    """Sample robots.txt content."""
    return """
User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
"""


@pytest.fixture
def sample_sitemap_xml():
    """Sample sitemap.xml content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2026-05-01</lastmod>
    </url>
    <url>
        <loc>https://example.com/about</loc>
        <lastmod>2026-05-01</lastmod>
    </url>
</urlset>
"""


@pytest.fixture
def sample_pagespeed_response():
    """Sample PageSpeed API response."""
    return {
        "lighthouseResult": {
            "categories": {
                "performance": {
                    "score": 0.85
                }
            },
            "audits": {
                "first-contentful-paint": {
                    "numericValue": 1200
                },
                "largest-contentful-paint": {
                    "numericValue": 2500
                },
                "cumulative-layout-shift": {
                    "numericValue": 0.1
                }
            }
        }
    }


def create_mock_response(status, content):
    """Helper to create mock aiohttp response."""
    mock_response = AsyncMock()
    mock_response.status = status
    if isinstance(content, str):
        mock_response.text = AsyncMock(return_value=content)
    else:
        mock_response.json = AsyncMock(return_value=content)
    return mock_response


def create_mock_session(mock_response):
    """Helper to create mock aiohttp session."""
    mock_get = MagicMock()
    mock_get.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_get)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


class TestTechnicalSEOAgent:
    """Test Technical SEO Agent."""

    @pytest.mark.asyncio
    async def test_analyze_robots_txt_exists(self, agent, sample_robots_txt):
        """Test robots.txt analysis when file exists."""
        mock_response = create_mock_response(200, sample_robots_txt)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._analyze_robots_txt("https://example.com")

        assert result["exists"] is True
        assert result["allows_crawling"] is True
        assert "https://example.com/sitemap.xml" in result["sitemap_urls"]

    @pytest.mark.asyncio
    async def test_analyze_robots_txt_not_exists(self, agent):
        """Test robots.txt analysis when file doesn't exist."""
        mock_response = create_mock_response(404, "")
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._analyze_robots_txt("https://example.com")

        assert result["exists"] is False
        assert result["allows_crawling"] is True  # Default
        assert result["sitemap_urls"] == []

    @pytest.mark.asyncio
    async def test_analyze_robots_txt_disallows_crawling(self, agent):
        """Test robots.txt that disallows crawling."""
        disallow_robots = "User-agent: *\nDisallow: /"
        mock_response = create_mock_response(200, disallow_robots)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._analyze_robots_txt("https://example.com")

        assert result["exists"] is True
        assert result["allows_crawling"] is False

    @pytest.mark.asyncio
    async def test_analyze_sitemap_exists(self, agent, sample_sitemap_xml):
        """Test sitemap.xml analysis when file exists."""
        mock_response = create_mock_response(200, sample_sitemap_xml)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._analyze_sitemap("https://example.com")

        assert result["exists"] is True
        assert result["url_count"] == 2
        assert result["last_modified"] == "2026-05-01"

    @pytest.mark.asyncio
    async def test_analyze_sitemap_not_exists(self, agent):
        """Test sitemap.xml analysis when file doesn't exist."""
        mock_response = create_mock_response(404, "")
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._analyze_sitemap("https://example.com")

        assert result["exists"] is False
        assert result["url_count"] == 0

    @pytest.mark.asyncio
    async def test_extract_meta_tags(self, agent, sample_html):
        """Test meta tags extraction."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._extract_meta_tags("https://example.com")

        assert result["title"] == "Example Medical Clinic"
        assert result["description"] == "Best medical clinic in town"
        assert "medical" in result["keywords"]
        assert "og:title" in result["og_tags"]
        assert result["og_tags"]["og:title"] == "Example Clinic"

    @pytest.mark.asyncio
    async def test_extract_meta_tags_missing(self, agent):
        """Test meta tags extraction when tags are missing."""
        minimal_html = "<html><head></head><body></body></html>"
        mock_response = create_mock_response(200, minimal_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._extract_meta_tags("https://example.com")

        assert result["title"] is None
        assert result["description"] is None
        assert result["keywords"] == []
        assert result["og_tags"] == {}

    @pytest.mark.asyncio
    async def test_get_page_speed_api(self, agent, sample_pagespeed_response):
        """Test PageSpeed API call."""
        agent.pagespeed_api_key = "test_key"
        mock_response = create_mock_response(200, sample_pagespeed_response)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._get_page_speed_api("https://example.com")

        assert result["page_speed_score"] == 85.0
        assert result["first_contentful_paint"] == 1.2
        assert result["largest_contentful_paint"] == 2.5
        assert result["cumulative_layout_shift"] == 0.1
        assert result["source"] == "pagespeed_api"

    @pytest.mark.asyncio
    async def test_get_page_speed_no_api_key(self, agent):
        """Test PageSpeed fallback when no API key."""
        agent.pagespeed_api_key = None

        with patch.object(agent, "_get_page_speed_lighthouse", return_value={"source": "lighthouse_cli"}):
            result = await agent._get_page_speed("https://example.com")

        assert result["source"] == "lighthouse_cli"

    @pytest.mark.asyncio
    async def test_validate_schema_exists(self, agent, sample_html):
        """Test Schema.org validation when schema exists."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._validate_schema("https://example.com")

        assert result["has_schema"] is True
        assert "MedicalClinic" in result["types"]
        assert result["valid"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_validate_schema_not_exists(self, agent):
        """Test Schema.org validation when no schema."""
        html_no_schema = "<html><head></head><body></body></html>"
        mock_response = create_mock_response(200, html_no_schema)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent._validate_schema("https://example.com")

        assert result["has_schema"] is False
        assert result["types"] == []
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_analyze_handles_errors(self, agent):
        """Test that analyze handles errors gracefully."""
        # Mock all methods to raise exceptions
        with patch.object(agent, "_analyze_robots_txt", side_effect=Exception("Network error")):
            with patch.object(agent, "_analyze_sitemap", side_effect=Exception("Network error")):
                with patch.object(agent, "_extract_meta_tags", side_effect=Exception("Network error")):
                    with patch.object(agent, "_get_page_speed", side_effect=Exception("Network error")):
                        with patch.object(agent, "_validate_schema", side_effect=Exception("Network error")):
                            result = await agent.analyze("https://example.com", "test-correlation-123")

        # Should still return a result with errors
        assert result["agent"] == "technical-agent"
        assert result["status"] == "success"  # Partial success
        assert "error" in str(result["results"]["robots_txt"])
