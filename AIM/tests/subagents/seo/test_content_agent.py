"""Unit tests for Content SEO Agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aim.subagents.seo.content_agent import ContentSEOAgent


@pytest.fixture
def agent():
    """Create Content SEO Agent instance."""
    return ContentSEOAgent()


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Clinic Services</title>
    </head>
    <body>
        <header>
            <h1>Best Medical Clinic</h1>
        </header>
        <main>
            <article>
                <h2>Our Services</h2>
                <p>We provide comprehensive medical services for all patients. Our experienced doctors offer quality healthcare with modern equipment and facilities.</p>

                <h3>Primary Care</h3>
                <p>Regular checkups and preventive care for maintaining good health. We focus on early detection and treatment of common conditions.</p>

                <h3>Specialist Consultations</h3>
                <p>Expert consultations with certified specialists in various medical fields. Our team includes cardiologists, neurologists, and other specialists.</p>

                <section>
                    <h2>Why Choose Us</h2>
                    <ul>
                        <li>Experienced medical professionals</li>
                        <li>Modern diagnostic equipment</li>
                        <li>Patient-centered approach</li>
                    </ul>
                </section>

                <img src="clinic.jpg" alt="Modern medical clinic">
                <img src="doctor.jpg" alt="Professional doctor">
                <img src="equipment.jpg">
            </article>
        </main>
        <footer>
            <nav>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def minimal_html():
    """Minimal HTML for testing edge cases."""
    return "<html><head><title>Test</title></head><body></body></html>"


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


class TestContentSEOAgent:
    """Test Content SEO Agent."""

    @pytest.mark.asyncio
    async def test_analyze_headers_proper_structure(self, agent, sample_html):
        """Test header analysis with proper structure."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")

        result = agent._analyze_headers(soup)

        assert result["counts"]["h1"] == 1
        assert result["counts"]["h2"] == 2
        assert result["counts"]["h3"] == 2
        assert result["total"] == 5
        assert result["has_proper_hierarchy"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_headers_missing_h1(self, agent):
        """Test header analysis when H1 is missing."""
        from bs4 import BeautifulSoup
        html = "<html><body><h2>Title</h2></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        result = agent._analyze_headers(soup)

        assert result["counts"]["h1"] == 0
        assert "Missing H1 tag" in result["issues"]
        assert result["has_proper_hierarchy"] is False

    @pytest.mark.asyncio
    async def test_analyze_headers_multiple_h1(self, agent):
        """Test header analysis with multiple H1 tags."""
        from bs4 import BeautifulSoup
        html = "<html><body><h1>Title 1</h1><h1>Title 2</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        result = agent._analyze_headers(soup)

        assert result["counts"]["h1"] == 2
        assert any("Multiple H1 tags" in issue for issue in result["issues"])
        assert result["has_proper_hierarchy"] is False

    @pytest.mark.asyncio
    async def test_analyze_headers_broken_hierarchy(self, agent):
        """Test header analysis with broken hierarchy."""
        from bs4 import BeautifulSoup
        html = "<html><body><h1>Title</h1><h3>Subtitle</h3></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        result = agent._analyze_headers(soup)

        assert "broken hierarchy" in str(result["issues"]).lower()
        assert result["has_proper_hierarchy"] is False

    @pytest.mark.asyncio
    async def test_analyze_keywords(self, agent, sample_html):
        """Test keyword density analysis."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")

        result = agent._analyze_keywords(soup)

        assert result["total_words"] > 0
        assert result["unique_words"] > 0
        assert len(result["top_keywords"]) > 0
        assert "medical" in [kw["word"] for kw in result["top_keywords"]]

        # Check density calculation
        for word, data in result["keyword_density"].items():
            assert "count" in data
            assert "density" in data
            assert 0 <= data["density"] <= 100

    @pytest.mark.asyncio
    async def test_analyze_keywords_empty_content(self, agent, minimal_html):
        """Test keyword analysis with minimal content."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(minimal_html, "html.parser")

        result = agent._analyze_keywords(soup)

        # "Test" from title is 1 word
        assert result["total_words"] >= 0
        assert result["unique_words"] >= 0
        # May have "test" keyword from title
        assert isinstance(result["top_keywords"], list)

    @pytest.mark.asyncio
    async def test_analyze_readability(self, agent, sample_html):
        """Test readability scoring."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")

        result = agent._analyze_readability(soup)

        assert result["flesch_reading_ease"] is not None
        assert result["flesch_kincaid_grade"] is not None
        assert result["gunning_fog"] is not None
        assert result["automated_readability_index"] is not None
        assert "interpretation" in result
        assert result["interpretation"] in [
            "Very Easy", "Easy", "Fairly Easy", "Standard",
            "Fairly Difficult", "Difficult", "Very Difficult"
        ]

    @pytest.mark.asyncio
    async def test_analyze_readability_insufficient_text(self, agent, minimal_html):
        """Test readability with insufficient text."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(minimal_html, "html.parser")

        result = agent._analyze_readability(soup)

        assert result["flesch_reading_ease"] is None
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_content_quality(self, agent, sample_html):
        """Test content quality metrics."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")

        result = agent._analyze_content_quality(soup)

        assert result["total_characters"] > 0
        assert result["total_words"] > 0
        assert result["avg_word_length"] > 0
        assert result["paragraph_count"] > 0
        assert result["avg_paragraph_length"] > 0
        assert result["image_count"] == 3
        assert result["images_with_alt"] == 2
        assert result["alt_text_coverage"] == 66.7
        assert result["list_count"] == 1
        assert result["link_count"] == 2
        assert result["content_to_code_ratio"] > 0

    @pytest.mark.asyncio
    async def test_analyze_structure(self, agent, sample_html):
        """Test content structure analysis."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, "html.parser")

        result = agent._analyze_structure(soup)

        assert result["has_main_tag"] is True
        assert result["has_article_tag"] is True
        assert result["has_semantic_structure"] is True
        assert result["section_count"] == 1
        assert result["nav_count"] == 1
        assert result["has_footer"] is True
        assert result["has_header"] is True

    @pytest.mark.asyncio
    async def test_analyze_structure_no_semantic_tags(self, agent, minimal_html):
        """Test structure analysis without semantic tags."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(minimal_html, "html.parser")

        result = agent._analyze_structure(soup)

        assert result["has_main_tag"] is False
        assert result["has_article_tag"] is False
        assert result["has_semantic_structure"] is False

    @pytest.mark.asyncio
    async def test_analyze_success(self, agent, sample_html):
        """Test full analysis workflow."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent.analyze("https://example.com", "test-correlation-123")

        assert result["agent"] == "content-agent"
        assert result["url"] == "https://example.com"
        assert result["correlation_id"] == "test-correlation-123"
        assert result["status"] == "success"
        assert "timestamp" in result
        assert result["duration_seconds"] >= 0

        # Verify all components analyzed
        assert "headers" in result["results"]
        assert "keywords" in result["results"]
        assert "readability" in result["results"]
        assert "content_quality" in result["results"]
        assert "structure" in result["results"]

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
