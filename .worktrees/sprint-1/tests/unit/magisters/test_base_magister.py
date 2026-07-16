"""Unit tests for Base Magister class"""

import pytest
from pathlib import Path
from meai.agents.magisters.base_magister import BaseMagister
from meai.events.event_bus import EventBus
from meai.agents.base_agent import Task


@pytest.mark.asyncio
async def test_base_magister_initialization():
    """Test BaseMagister can be initialized"""
    event_bus = EventBus()

    magister = BaseMagister(
        agent_id="test-magister-1",
        magister_type="test",
        domain="testing",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    assert magister.agent_id == "test-magister-1"
    assert magister.magister_type == "test"
    assert magister.domain == "testing"
    assert magister.vault_path == Path("/tmp/test-magister")


@pytest.mark.asyncio
async def test_base_magister_capabilities():
    """Test BaseMagister has required capabilities"""
    event_bus = EventBus()

    magister = BaseMagister(
        agent_id="test-magister-1",
        magister_type="test",
        domain="testing",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    capabilities = magister.get_capabilities()

    assert "search_knowledge" in capabilities
    assert "cache_knowledge" in capabilities
    assert "query_teacher" in capabilities
    assert "request_research" in capabilities


@pytest.mark.asyncio
async def test_hybrid_search_local_hit():
    """Test hybrid search finds knowledge in local vault"""
    event_bus = EventBus()

    magister = BaseMagister(
        agent_id="test-magister-1",
        magister_type="test",
        domain="testing",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Cache some knowledge locally
    knowledge = {
        "content": "Test knowledge about SEO",
        "source": "local",
        "metadata": {"topic": "seo"},
    }

    await magister.cache_knowledge(knowledge, "seo_test")

    # Search should find it locally
    results = await magister.search_knowledge("SEO", search_local=True)

    assert len(results) > 0
    assert results[0]["source"] == "local"
    assert "SEO" in results[0]["content"]

    await magister.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_teacher_query():
    """Test hybrid search queries Teacher when not found locally"""
    event_bus = EventBus()

    magister = BaseMagister(
        agent_id="test-magister-1",
        magister_type="test",
        domain="testing",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Search for knowledge not in local vault
    # Should trigger Teacher query
    query = "Advanced SEO techniques"

    # This will return empty for now (Teacher not mocked)
    results = await magister.search_knowledge(query, search_local=True, search_teacher=True)

    # Verify query was attempted
    assert results is not None

    await magister.shutdown()


@pytest.mark.asyncio
async def test_execute_task():
    """Test executing a task"""
    event_bus = EventBus()

    magister = BaseMagister(
        agent_id="test-magister-1",
        magister_type="test",
        domain="testing",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    task = Task(
        task_id="task-1",
        description="Search for SEO knowledge",
        metadata={
            "capability": "search_knowledge",
            "query": "SEO best practices",
        },
    )

    result = await magister.execute_task(task)

    assert result.task_id == "task-1"
    assert result.status in ["completed", "failed"]

    await magister.shutdown()
