"""Integration tests for Links SEO Agent with Event Bus."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aim.subagents.seo.links_agent import LinksSEOAgent


@pytest.fixture
def agent():
    """Create Links SEO Agent instance."""
    return LinksSEOAgent()


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Clinic - Healthcare Services</title>
    </head>
    <body>
        <header>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About Us</a>
                <a href="/services">Our Services</a>
                <a href="/services/primary-care">Primary Care</a>
                <a href="/services/specialists">Specialists</a>
                <a href="/contact">Contact Us</a>
                <a href="/appointments">Book Appointment</a>
            </nav>
        </header>
        <main>
            <article>
                <h1>Welcome to Our Medical Clinic</h1>
                <p>Learn more about <a href="/about">our experienced team</a> and <a href="/services">comprehensive services</a>.</p>
                <p>Visit our <a href="/services/primary-care">primary care department</a> for routine checkups.</p>
                <p>Schedule an <a href="/appointments">appointment online</a> or call us today.</p>

                <h2>Health Resources</h2>
                <p>Read the latest <a href="https://healthnews.com/articles" rel="nofollow">health news</a>.</p>
                <p>Check <a href="https://medical-research.org/studies">medical research studies</a>.</p>
                <p>Visit <a href="https://who.int/health-topics">WHO health topics</a> for global health information.</p>

                <h2>Patient Resources</h2>
                <p><a href="/patient-portal">Patient Portal</a> - Access your medical records.</p>
                <p><a href="/insurance">Insurance Information</a> - Learn about accepted plans.</p>
                <p><a href="/faq">Frequently Asked Questions</a> - Find answers to common questions.</p>

                <h2>Connect With Us</h2>
                <p>Follow us on <a href="https://facebook.com/medicalclinic" rel="nofollow">Facebook</a>.</p>
                <p>Connect on <a href="https://linkedin.com/company/medicalclinic" rel="nofollow">LinkedIn</a>.</p>
                <p>Watch our videos on <a href="https://youtube.com/medicalclinic" rel="nofollow">YouTube</a>.</p>

                <h2>Generic Links (Poor SEO)</h2>
                <p><a href="/page1">Click here</a> for more information.</p>
                <p><a href="/page2">Read more</a> about our services.</p>
                <p><a href="/page3">Here</a> you can find details.</p>
            </article>
        </main>
        <footer>
            <nav>
                <a href="/privacy">Privacy Policy</a>
                <a href="/terms">Terms of Service</a>
                <a href="/sitemap">Sitemap</a>
                <a href="/accessibility">Accessibility</a>
            </nav>
        </footer>
    </body>
    </html>
    """


def create_mock_response(status, content):
    """Helper to create mock aiohttp response."""
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.text = AsyncMock(return_value=content)
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


class TestLinksAgentEventBusIntegration:
    """Test Links SEO Agent integration with Event Bus."""

    @pytest.mark.asyncio
    async def test_agent_analyzes_and_returns_result(self, agent, sample_html):
        """Test that agent can analyze a URL and return structured result."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        # Mock broken links check to avoid actual HTTP requests
        async def mock_check_broken(links, base_url):
            return {
                "checked": 10,
                "broken_count": 1,
                "working_count": 9,
                "broken_percentage": 10.0,
                "broken_links": [{"url": "https://example.com/broken", "status": 404}],
                "note": "Checked first 10 unique links for performance"
            }

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch.object(agent, '_check_broken_links', side_effect=mock_check_broken):
                result = await agent.analyze("https://example.com", "test-correlation-123")

        # Verify result structure
        assert result["agent"] == "links-agent"
        assert result["url"] == "https://example.com"
        assert result["correlation_id"] == "test-correlation-123"
        assert result["status"] == "success"
        assert "timestamp" in result
        assert result["duration_seconds"] >= 0

        # Verify all components analyzed
        assert "internal_links" in result["results"]
        assert "external_links" in result["results"]
        assert "anchor_text" in result["results"]
        assert "broken_links" in result["results"]

        # Verify internal links analysis
        internal = result["results"]["internal_links"]
        assert internal["total"] > 0
        assert internal["unique"] > 0
        assert len(internal["most_linked"]) > 0
        assert len(internal["links"]) > 0

        # Verify external links analysis
        external = result["results"]["external_links"]
        assert external["total"] > 0
        assert external["unique"] > 0
        assert external["nofollow_count"] > 0  # Social media links have nofollow
        assert len(external["top_domains"]) > 0

        # Verify anchor text analysis
        anchor = result["results"]["anchor_text"]
        assert anchor["total"] > 0
        assert anchor["generic_count"] > 0  # "Click here", "Read more", "Here"
        assert anchor["generic_percentage"] > 0

        # Verify broken links check
        broken = result["results"]["broken_links"]
        assert broken["checked"] == 10
        assert broken["broken_count"] == 1
        assert broken["working_count"] == 9

    @pytest.mark.asyncio
    async def test_agent_handles_poor_link_structure(self, agent):
        """Test that agent identifies poor link structure."""
        poor_html = """
        <html>
        <body>
            <a href="/page1">Click here</a>
            <a href="/page2">Read more</a>
            <a href="/page3">Here</a>
            <a href="/page4"></a>
            <a href="/page5"></a>
        </body>
        </html>
        """

        mock_response = create_mock_response(200, poor_html)
        mock_session = create_mock_session(mock_response)

        # Mock broken links check
        async def mock_check_broken(links, base_url):
            return {
                "checked": 5,
                "broken_count": 0,
                "working_count": 5,
                "broken_percentage": 0.0,
                "broken_links": [],
                "note": "Checked first 5 unique links for performance"
            }

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch.object(agent, '_check_broken_links', side_effect=mock_check_broken):
                result = await agent.analyze("https://example.com", "test-correlation-456")

        # Should still return success with issues identified
        assert result["status"] == "success"

        # Verify poor anchor text detected
        anchor = result["results"]["anchor_text"]
        assert anchor["generic_count"] == 3  # "Click here", "Read more", "Here"
        assert anchor["generic_percentage"] == 60.0  # 3 out of 5
        assert anchor["empty_count"] == 2
        assert anchor["empty_percentage"] == 40.0  # 2 out of 5

    @pytest.mark.asyncio
    async def test_agent_execution_time_reasonable(self, agent, sample_html):
        """Test that agent completes analysis in reasonable time."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        # Mock broken links check
        async def mock_check_broken(links, base_url):
            return {
                "checked": 10,
                "broken_count": 0,
                "working_count": 10,
                "broken_percentage": 0.0,
                "broken_links": [],
                "note": "Checked first 10 unique links for performance"
            }

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch.object(agent, '_check_broken_links', side_effect=mock_check_broken):
                result = await agent.analyze("https://example.com", "test-correlation-789")

        # Should complete in under 5 seconds (mocked, so should be instant)
        assert result["duration_seconds"] < 5.0
        assert result["status"] == "success"
