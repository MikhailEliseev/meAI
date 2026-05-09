"""Integration tests for Content SEO Agent with Event Bus."""

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
        <title>Medical Clinic - Healthcare Services</title>
    </head>
    <body>
        <header>
            <h1>Professional Medical Clinic</h1>
        </header>
        <main>
            <article>
                <h2>Comprehensive Healthcare Services</h2>
                <p>Our medical clinic provides comprehensive healthcare services for patients of all ages. We specialize in preventive care, diagnosis, and treatment of various medical conditions. Our experienced team of doctors and nurses is dedicated to providing quality healthcare with compassion and professionalism.</p>

                <h3>Primary Care Services</h3>
                <p>We offer regular checkups, health screenings, and preventive care to help you maintain optimal health. Our primary care physicians work closely with patients to develop personalized treatment plans that address their unique healthcare needs.</p>

                <h3>Specialist Consultations</h3>
                <p>Our clinic features board-certified specialists in cardiology, neurology, orthopedics, and other medical fields. We provide expert consultations and advanced diagnostic services to ensure accurate diagnosis and effective treatment.</p>

                <h3>Emergency Care</h3>
                <p>We provide urgent care services for non-life-threatening emergencies. Our emergency department is staffed with experienced physicians who can quickly assess and treat acute medical conditions.</p>

                <section>
                    <h2>Why Choose Our Clinic</h2>
                    <ul>
                        <li>Experienced medical professionals with advanced training</li>
                        <li>State-of-the-art diagnostic equipment and facilities</li>
                        <li>Patient-centered approach to healthcare delivery</li>
                        <li>Convenient appointment scheduling and extended hours</li>
                        <li>Comprehensive insurance coverage and payment options</li>
                    </ul>
                </section>

                <img src="clinic-exterior.jpg" alt="Modern medical clinic building">
                <img src="doctor-consultation.jpg" alt="Doctor consulting with patient">
                <img src="medical-equipment.jpg" alt="Advanced medical equipment">
            </article>
        </main>
        <footer>
            <nav>
                <a href="/about">About Us</a>
                <a href="/services">Services</a>
                <a href="/contact">Contact</a>
                <a href="/appointments">Appointments</a>
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


class TestContentAgentEventBusIntegration:
    """Test Content SEO Agent integration with Event Bus."""

    @pytest.mark.asyncio
    async def test_agent_analyzes_and_returns_result(self, agent, sample_html):
        """Test that agent can analyze a URL and return structured result."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent.analyze("https://example.com", "test-correlation-123")

        # Verify result structure
        assert result["agent"] == "content-agent"
        assert result["url"] == "https://example.com"
        assert result["correlation_id"] == "test-correlation-123"
        assert result["status"] == "success"
        assert "timestamp" in result
        assert result["duration_seconds"] > 0

        # Verify all components analyzed
        assert "headers" in result["results"]
        assert "keywords" in result["results"]
        assert "readability" in result["results"]
        assert "content_quality" in result["results"]
        assert "structure" in result["results"]

        # Verify headers analysis
        headers = result["results"]["headers"]
        assert headers["counts"]["h1"] == 1
        assert headers["counts"]["h2"] == 2
        assert headers["counts"]["h3"] == 3
        assert headers["has_proper_hierarchy"] is True

        # Verify keywords analysis
        keywords = result["results"]["keywords"]
        assert keywords["total_words"] > 100
        assert keywords["unique_words"] > 0
        assert len(keywords["top_keywords"]) > 0
        assert any("medical" in kw["word"] for kw in keywords["top_keywords"])

        # Verify readability analysis
        readability = result["results"]["readability"]
        assert readability["flesch_reading_ease"] is not None
        assert readability["flesch_kincaid_grade"] is not None
        assert "interpretation" in readability

        # Verify content quality
        quality = result["results"]["content_quality"]
        assert quality["total_words"] > 100
        assert quality["paragraph_count"] > 0
        assert quality["image_count"] == 3
        assert quality["images_with_alt"] == 3
        assert quality["alt_text_coverage"] == 100.0

        # Verify structure
        structure = result["results"]["structure"]
        assert structure["has_main_tag"] is True
        assert structure["has_article_tag"] is True
        assert structure["has_semantic_structure"] is True

    @pytest.mark.asyncio
    async def test_agent_handles_poor_content(self, agent):
        """Test that agent handles poorly structured content."""
        poor_html = """
        <html>
        <body>
            <h1>Title 1</h1>
            <h1>Title 2</h1>
            <h3>Subtitle without H2</h3>
            <p>Short text.</p>
            <img src="image.jpg">
        </body>
        </html>
        """

        mock_response = create_mock_response(200, poor_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent.analyze("https://example.com", "test-correlation-456")

        # Should still return success with issues identified
        assert result["status"] == "success"

        # Verify issues detected
        headers = result["results"]["headers"]
        assert headers["has_proper_hierarchy"] is False
        assert len(headers["issues"]) > 0
        assert any("Multiple H1" in issue for issue in headers["issues"])

        # Verify poor alt text coverage
        quality = result["results"]["content_quality"]
        assert quality["images_with_alt"] == 0
        assert quality["alt_text_coverage"] == 0.0

        # Verify lack of semantic structure
        structure = result["results"]["structure"]
        assert structure["has_semantic_structure"] is False

    @pytest.mark.asyncio
    async def test_agent_execution_time_reasonable(self, agent, sample_html):
        """Test that agent completes analysis in reasonable time."""
        mock_response = create_mock_response(200, sample_html)
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await agent.analyze("https://example.com", "test-correlation-789")

        # Should complete in under 5 seconds (mocked, so should be instant)
        assert result["duration_seconds"] < 5.0
        assert result["status"] == "success"
