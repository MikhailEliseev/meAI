"""Integration tests for SEO Magister E2E flow

Tests SEO Magister with real subagents (only API clients mocked).
Verifies end-to-end coordination from Magister → Subagents → API clients.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from AIM.src.aim.magisters.seo_magister import SEOMagister


@pytest.mark.asyncio
async def test_seo_magister_e2e_success():
    """Should complete E2E flow with real subagents (mocked aiohttp)

    Scenario: Real TechnicalSEOAgent, ContentSEOAgent, LinksSEOAgent with mocked aiohttp
    Expected: Full coordination works, results aggregated, scores calculated
    """
    # Arrange: Create real SEO Magister (uses real subagents by default)
    magister = SEOMagister(timeout=600)

    # Mock aiohttp response (used by all 3 subagents)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = """
    <html>
        <head>
            <title>Test Page Title (45 chars)</title>
            <meta name="description" content="Test page description for SEO testing purposes with enough length to pass validation checks">
            <meta name="robots" content="index, follow">
        </head>
        <body>
            <h1>Main Heading</h1>
            <h2>Subheading</h2>
            <p>Content paragraph with some text for readability testing. This needs to be long enough to calculate proper readability scores.</p>
            <p>Another paragraph to increase word count and improve content quality metrics.</p>
            <img src="/image1.jpg" alt="Image description">
            <img src="/image2.jpg" alt="Another image">
            <a href="/internal">Internal Link</a>
            <a href="/page2">Another Internal Link</a>
            <a href="https://external.com">External Link</a>
        </body>
    </html>
    """

    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    mock_session.close = AsyncMock()

    # Patch aiohttp.ClientSession
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Act: Coordinate analysis with real subagents
        result = await magister.coordinate_analysis("https://example.com", "e2e-test-123")

    # Assert: E2E flow completed successfully
    assert result["status"] == "success"
    assert result["url"] == "https://example.com"
    assert result["correlation_id"] == "e2e-test-123"
    assert "scores" in result
    assert result["scores"]["overall"] >= 0
    assert "details" in result
    assert "technical" in result["details"]
    assert "content" in result["details"]
    assert "links" in result["details"]


@pytest.mark.asyncio
async def test_seo_magister_e2e_error():
    """Should handle E2E error when API client fails

    Scenario: Real subagents, aiohttp raises ConnectionError
    Expected: Error propagates, graceful degradation with all scores=0
    """
    # Arrange: Create real SEO Magister
    magister = SEOMagister(timeout=600)

    # Mock aiohttp to raise error
    mock_session = AsyncMock()
    mock_session.get.side_effect = ConnectionError("Network error")
    mock_session.close = AsyncMock()

    # Patch aiohttp.ClientSession
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Act: Coordinate analysis (should handle error)
        result = await magister.coordinate_analysis("https://example.com", "e2e-error-123")

    # Assert: Error handled gracefully
    assert result["status"] == "success"  # Graceful degradation
    assert result["url"] == "https://example.com"
    assert result["correlation_id"] == "e2e-error-123"

    # All scores should be 0 (all subagents failed)
    assert result["scores"]["overall"] == 0.0
    assert result["scores"]["technical"] == 0.0
    assert result["scores"]["content"] == 0.0
    assert result["scores"]["links"] == 0.0
