"""Pytest fixtures for subagent tests

Provides mocked API clients and configured subagent instances.
"""

import pytest
from unittest.mock import AsyncMock

from src.aim.subagents.api_clients.semrush import SEMrushClient
from src.aim.subagents.api_clients.ahrefs import AhrefsClient
from src.aim.subagents.keyword_research_agent import KeywordResearchAgent
from src.aim.subagents.content_writer_agent import ContentWriterAgent


@pytest.fixture
def mock_api_clients():
    """Mock all external API clients"""
    return {
        "semrush": AsyncMock(spec=SEMrushClient),
        "ahrefs": AsyncMock(spec=AhrefsClient),
        "openai": AsyncMock(),
        "anthropic": AsyncMock(),
        "yandex_direct": AsyncMock(),
        "ga4": AsyncMock(),
        "yandex_metrica": AsyncMock(),
    }


@pytest.fixture
def keyword_research_agent(mock_api_clients):
    """Keyword Research Agent with mocked API clients"""
    agent = KeywordResearchAgent(
        agent_id="test-keyword-research",
        skip_api_validation=True,
    )
    # Inject mocked clients
    agent.semrush_client = mock_api_clients["semrush"]
    agent.ahrefs_client = mock_api_clients["ahrefs"]
    return agent


@pytest.fixture
def content_writer_agent(mock_api_clients):
    """Content Writer Agent with mocked LLM client"""
    agent = ContentWriterAgent(
        agent_id="test-content-writer",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
    )
    # Inject mocked OpenAI client
    if hasattr(agent, 'openai_client'):
        agent.openai_client = mock_api_clients["openai"]
    if hasattr(agent, 'anthropic_client'):
        agent.anthropic_client = mock_api_clients["anthropic"]
    return agent
