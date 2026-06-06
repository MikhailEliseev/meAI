"""Integration tests for Technical SEO Agent with Event Bus."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aim.subagents.seo.technical_agent import TechnicalSEOAgent


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
        <meta name="description" content="Best medical clinic">
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "MedicalClinic"}
        </script>
    </head>
    <body><h1>Welcome</h1></body>
    </html>
    """


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


class TestTechnicalAgentEventBusIntegration:
    """Test Technical SEO Agent integration with Event Bus."""

    @pytest.mark.asyncio
    async def test_agent_analyzes_and_returns_result(self, agent, sample_html):
        """Test that agent can analyze a URL and return structured result."""
        # Mock HTTP responses
        robots_txt = "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml"
        sitemap_xml = '<?xml version="1.0"?><urlset><url><loc>https://example.com/</loc></url></urlset>'

        def mock_get_side_effect(url, **kwargs):
            """Return different responses based on URL."""
            mock_response = AsyncMock()
            mock_response.status = 200

            if "robots.txt" in url:
                mock_response.text = AsyncMock(return_value=robots_txt)
            elif "sitemap.xml" in url:
                mock_response.text = AsyncMock(return_value=sitemap_xml)
            elif "pagespeedonline" in url:
                mock_response.json = AsyncMock(return_value={
                    "lighthouseResult": {
                        "categories": {"performance": {"score": 0.85}},
                        "audits": {
                            "first-contentful-paint": {"numericValue": 1200},
                            "largest-contentful-paint": {"numericValue": 2500},
                            "cumulative-layout-shift": {"numericValue": 0.1}
                        }
                    }
                })
            else:
                mock_response.text = AsyncMock(return_value=sample_html)

            mock_get = MagicMock()
            mock_get.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.__aexit__ = AsyncMock(return_value=None)
            return mock_get

        agent.pagespeed_api_key = "test_key"

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=mock_get_side_effect)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session

            # Execute analysis
            result = await agent.analyze("https://example.com", "test-correlation-123")

        # Verify result structure
        assert result["agent"] == "technical-agent"
        assert result["url"] == "https://example.com"
        assert result["correlation_id"] == "test-correlation-123"
        assert result["status"] == "success"
        assert "timestamp" in result
        assert result["duration_seconds"] > 0

        # Verify all components analyzed
        assert "robots_txt" in result["results"]
        assert "sitemap" in result["results"]
        assert "meta_tags" in result["results"]
        assert "performance" in result["results"]
        assert "schema" in result["results"]

        # Verify robots.txt analysis
        assert result["results"]["robots_txt"]["exists"] is True
        assert result["results"]["robots_txt"]["allows_crawling"] is True

        # Verify sitemap analysis
        assert result["results"]["sitemap"]["exists"] is True
        assert result["results"]["sitemap"]["url_count"] == 1

        # Verify meta tags
        assert result["results"]["meta_tags"]["title"] == "Example Medical Clinic"

        # Verify performance
        assert result["results"]["performance"]["page_speed_score"] == 85.0

        # Verify schema
        assert result["results"]["schema"]["has_schema"] is True
        assert "MedicalClinic" in result["results"]["schema"]["types"]

    @pytest.mark.asyncio
    async def test_agent_handles_partial_failures(self, agent):
        """Test that agent handles partial failures gracefully."""
        def mock_get_side_effect(url, **kwargs):
            """Return 404 for some URLs."""
            mock_response = AsyncMock()

            if "robots.txt" in url or "sitemap.xml" in url:
                mock_response.status = 404
            else:
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html><head><title>Test</title></head></html>")

            mock_get = MagicMock()
            mock_get.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.__aexit__ = AsyncMock(return_value=None)
            return mock_get

        agent.pagespeed_api_key = None  # Use Lighthouse fallback

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=mock_get_side_effect)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session

            # Mock Lighthouse CLI to return error
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.returncode = 1
                mock_process.communicate = AsyncMock(return_value=(b"", b"Lighthouse failed"))
                mock_subprocess.return_value = mock_process

                result = await agent.analyze("https://example.com", "test-correlation-456")

        # Should still return success with partial results
        assert result["status"] == "success"
        assert result["results"]["robots_txt"]["exists"] is False
        assert result["results"]["sitemap"]["exists"] is False
        assert result["results"]["meta_tags"]["title"] == "Test"
        assert "error" in result["results"]["performance"]

    @pytest.mark.asyncio
    async def test_agent_execution_time_reasonable(self, agent, sample_html):
        """Test that agent completes analysis in reasonable time."""
        # Mock fast responses
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        agent.pagespeed_api_key = None  # Skip PageSpeed API

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.returncode = 1
                mock_process.communicate = AsyncMock(return_value=(b"", b"Skip"))
                mock_subprocess.return_value = mock_process

                result = await agent.analyze("https://example.com", "test-correlation-789")

        # Should complete in under 5 seconds (mocked, so should be instant)
        assert result["duration_seconds"] < 5.0
        assert result["status"] == "success"
