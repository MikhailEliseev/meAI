"""Pytest fixtures for Magister testing

Provides mock subagents and configured Magister instances for unit tests.
"""

import pytest
from unittest.mock import AsyncMock

from AIM.src.aim.subagents.seo.technical_agent import TechnicalSEOAgent
from AIM.src.aim.subagents.seo.content_agent import ContentSEOAgent
from AIM.src.aim.subagents.seo.links_agent import LinksSEOAgent
from AIM.src.aim.magisters.seo_magister import SEOMagister


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
