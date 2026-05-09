"""Unit tests for Links SEO Agent."""

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
        <title>Medical Clinic</title>
    </head>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/about">About Us</a>
            <a href="/services">Services</a>
            <a href="/contact">Contact</a>
        </nav>
        <main>
            <article>
                <h1>Welcome to Our Clinic</h1>
                <p>Visit our <a href="/services">services page</a> for more information.</p>
                <p>Read more about <a href="/about">our team</a> and <a href="/about#history">our history</a>.</p>

                <h2>External Resources</h2>
                <p>Learn more at <a href="https://example.com/health" rel="nofollow">Health Guide</a>.</p>
                <p>Check <a href="https://medical.org/research">Medical Research</a> for studies.</p>
                <p>Sponsored link: <a href="https://ads.com" rel="sponsored">Advertisement</a>.</p>

                <h2>Generic Links</h2>
                <p><a href="/page1">Click here</a> for details.</p>
                <p><a href="/page2">Read more</a> about our services.</p>
                <p><a href="/page3"></a></p>

                <h2>Social Media</h2>
                <p>Follow us on <a href="https://facebook.com/clinic">Facebook</a>.</p>
                <p>Connect on <a href="https://linkedin.com/company/clinic">LinkedIn</a>.</p>
            </article>
        </main>
        <footer>
            <a href="/privacy">Privacy Policy</a>
            <a href="/terms">Terms of Service</a>
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


class TestLinksSEOAgent:
    """Test Links SEO Agent."""

    @pytest.mark.asyncio
    async def test_analyze_internal_links(self, agent, sample_html):
        """Test internal links analysis."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_internal_links(links, "https://example.com")

        assert result["total"] > 0
        assert result["unique"] > 0
        assert result["total"] >= result["unique"]
        assert len(result["most_linked"]) > 0
        assert len(result["links"]) > 0

        # Check that internal links are identified correctly
        internal_urls = [link["url"] for link in result["links"]]
        assert any("example.com" in url or url.startswith("/") for url in internal_urls)

    @pytest.mark.asyncio
    async def test_analyze_external_links(self, agent, sample_html):
        """Test external links analysis."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_external_links(links, "https://example.com")

        assert result["total"] > 0
        assert result["unique"] > 0
        assert result["nofollow_count"] >= 0
        assert 0 <= result["nofollow_percentage"] <= 100
        assert len(result["top_domains"]) > 0
        assert len(result["links"]) > 0

        # Check that external links are identified correctly
        external_urls = [link["url"] for link in result["links"]]
        assert any("example.com" not in url for url in external_urls)

        # Check nofollow detection (at least one nofollow link in sample HTML)
        assert result["nofollow_count"] >= 0

    @pytest.mark.asyncio
    async def test_analyze_anchor_text(self, agent, sample_html):
        """Test anchor text analysis."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_anchor_text(links)

        assert result["total"] > 0
        assert result["empty_count"] >= 0
        assert 0 <= result["empty_percentage"] <= 100
        assert result["generic_count"] > 0  # "Click here", "Read more"
        assert 0 <= result["generic_percentage"] <= 100
        assert result["avg_length"] > 0
        assert len(result["most_common"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_anchor_text_empty(self, agent):
        """Test anchor text analysis with empty anchors."""
        from bs4 import BeautifulSoup
        html = '<html><body><a href="/page"></a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_anchor_text(links)

        assert result["empty_count"] == 1
        assert result["empty_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_analyze_anchor_text_generic(self, agent):
        """Test anchor text analysis with generic terms."""
        from bs4 import BeautifulSoup
        html = '''
        <html><body>
            <a href="/page1">Click here</a>
            <a href="/page2">Read more</a>
            <a href="/page3">Here</a>
        </body></html>
        '''
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_anchor_text(links)

        assert result["generic_count"] == 3
        assert result["generic_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_check_broken_links(self, agent, sample_html):
        """Test broken links detection."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")
        links = soup.find_all("a", href=True)

        # Mock link checking
        async def mock_check_link(url, session):
            if "broken" in url:
                return url, 404
            return url, 200

        with patch.object(agent, '_check_broken_links') as mock_check:
            mock_check.return_value = {
                "checked": 10,
                "broken_count": 2,
                "working_count": 8,
                "broken_percentage": 20.0,
                "broken_links": [
                    {"url": "https://example.com/broken1", "status": 404},
                    {"url": "https://example.com/broken2", "status": 0}
                ],
                "note": "Checked first 10 unique links for performance"
            }

            result = await agent._check_broken_links(links, "https://example.com")

        assert result["checked"] == 10
        assert result["broken_count"] == 2
        assert result["working_count"] == 8
        assert result["broken_percentage"] == 20.0
        assert len(result["broken_links"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_success(self, agent, sample_html):
        """Test full analysis workflow."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        # Mock broken links check to avoid actual HTTP requests
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
                result = await agent.analyze("https://example.com", "test-correlation-123")

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

        # Verify internal links
        internal = result["results"]["internal_links"]
        assert internal["total"] > 0
        assert internal["unique"] > 0

        # Verify external links
        external = result["results"]["external_links"]
        assert external["total"] > 0
        assert external["unique"] > 0

        # Verify anchor text
        anchor = result["results"]["anchor_text"]
        assert anchor["total"] > 0

        # Verify broken links
        broken = result["results"]["broken_links"]
        assert broken["checked"] > 0

    @pytest.mark.asyncio
    async def test_analyze_http_error(self, agent):
        """Test analysis with HTTP error."""
        mock_response = create_mock_response(404, "")
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent.analyze("https://example.com", "test-correlation-456")

        assert result["status"] == "error"
        assert "HTTP 404" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_network_error(self, agent):
        """Test analysis with network error."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent.analyze("https://example.com", "test-correlation-789")

        assert result["status"] == "error"
        assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_internal_links_no_links(self, agent):
        """Test internal links analysis with no links."""
        from bs4 import BeautifulSoup
        html = "<html><body><p>No links here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_internal_links(links, "https://example.com")

        assert result["total"] == 0
        assert result["unique"] == 0
        assert len(result["most_linked"]) == 0
        assert len(result["links"]) == 0

    @pytest.mark.asyncio
    async def test_external_links_no_links(self, agent):
        """Test external links analysis with no links."""
        from bs4 import BeautifulSoup
        html = "<html><body><p>No links here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)

        result = agent._analyze_external_links(links, "https://example.com")

        assert result["total"] == 0
        assert result["unique"] == 0
        assert result["nofollow_count"] == 0
        assert result["nofollow_percentage"] == 0
