"""Pytest fixtures for Magister testing

Provides mock subagents and configured Magister instances for unit tests.
"""

import pytest
from unittest.mock import AsyncMock

from AIM.src.aim.subagents.seo.technical_agent import TechnicalSEOAgent
from AIM.src.aim.subagents.seo.content_agent import ContentSEOAgent
from AIM.src.aim.subagents.seo.links_agent import LinksSEOAgent
from AIM.src.aim.magisters.seo_magister import SEOMagister
from AIM.src.aim.magisters.content_magister import ContentMagister


@pytest.fixture
def mock_seo_subagents():
    """Mock SEO subagents for unit testing

    Returns dict with AsyncMock instances for all 3 SEO agents.
    Each mock has spec set to prevent typos in test code.
    """
    return {
        "technical": AsyncMock(spec=TechnicalSEOAgent),
        "content": AsyncMock(spec=ContentSEOAgent),
        "links": AsyncMock(spec=LinksSEOAgent),
    }


@pytest.fixture
def seo_magister(mock_seo_subagents):
    """SEO Magister with mocked subagents for unit testing

    Uses dependency injection to inject AsyncMock subagents.
    """
    return SEOMagister(
        timeout=600,
        technical_agent=mock_seo_subagents["technical"],
        content_agent=mock_seo_subagents["content"],
        links_agent=mock_seo_subagents["links"],
    )


@pytest.fixture
def mock_content_subagents():
    """Mock Content subagents for unit testing

    Returns dict with AsyncMock instances for Content subagent methods.
    Mocks identify_subagents and aggregate_results methods.
    """
    return {
        "identify_subagents": AsyncMock(return_value=["content-writer-agent"]),
        "aggregate_results": AsyncMock(return_value={
            "summary": "Test summary",
            "insights": ["Test insight"],
            "recommendations": ["Test recommendation"],
        }),
    }


@pytest.fixture
def content_magister(mock_content_subagents):
    """Content Magister with mocked dependencies for unit testing

    Uses dependency injection to inject AsyncMock event_bus and vault.
    """
    mock_event_bus = AsyncMock()
    mock_vault = AsyncMock()
    mock_vault.vault_path = AsyncMock()
    mock_vault.vault_path.exists.return_value = True

    magister = ContentMagister(
        magister_id="test-content-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
        event_bus=mock_event_bus,
        vault=mock_vault,
    )

    # Inject mocked methods
    magister.identify_subagents = mock_content_subagents["identify_subagents"]
    magister.aggregate_results = mock_content_subagents["aggregate_results"]

    return magister
