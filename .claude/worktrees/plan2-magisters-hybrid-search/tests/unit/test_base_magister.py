# tests/unit/test_base_magister.py
"""Tests for BaseMagister class"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskStatus
from meai.events.event_bus import EventBus
from meai.agents.teacher import TeacherAgent
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


class TestMagister(BaseMagister):
    """Concrete implementation for testing"""

    def get_domain(self) -> str:
        return "test"

    def get_capabilities(self) -> list[str]:
        return ["test_action"]


@pytest.mark.asyncio
async def test_base_magister_initialization():
    """Test BaseMagister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    magister = TestMagister(
        agent_id="test-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/test-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await magister.initialize()

    assert magister.agent_id == "test-magister"
    assert str(magister.vault.vault_path) == "obsidian/test-magister"
    assert magister.get_domain() == "test"
    assert "test_action" in magister.get_capabilities()

    await magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_base_magister_local_search():
    """Test BaseMagister can search local vault"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    magister = TestMagister(
        agent_id="test-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/test-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await magister.initialize()

    # Mock local search
    magister.vault.search = AsyncMock(return_value=[
        {"content": "Test knowledge", "path": "knowledge/test.md"}
    ])

    results = await magister.search_local("test query")

    assert len(results) > 0
    assert results[0]["content"] == "Test knowledge"

    await magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_base_magister_hybrid_search():
    """Test BaseMagister hybrid search: local → Teacher → Researcher"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    magister = TestMagister(
        agent_id="test-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/test-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await magister.initialize()

    # Mock local search (empty)
    magister.vault.search = AsyncMock(return_value=[])

    # Mock Teacher search
    magister.teacher.execute_task = AsyncMock(return_value=MagicMock(
        status="success",
        result={
            "status": "success",
            "results": [{"content": "Teacher knowledge", "score": 0.9}]
        }
    ))

    results = await magister.hybrid_search("test query")

    assert results["source"] == "teacher"
    assert len(results["results"]) > 0
    assert results["results"][0]["content"] == "Teacher knowledge"

    await magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_base_magister_request_research():
    """Test BaseMagister can request new research from Researcher"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    magister = TestMagister(
        agent_id="test-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/test-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await magister.initialize()

    # Mock event bus publish
    event_bus.publish = AsyncMock()

    await magister.request_research("test topic")

    # Verify event was published
    event_bus.publish.assert_called_once()
    call_args = event_bus.publish.call_args[1]
    assert call_args["event_type"] == "research_request"
    assert call_args["priority"] == 2

    await magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_base_magister_store_knowledge():
    """Test BaseMagister can store knowledge in local vault"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    magister = TestMagister(
        agent_id="test-magister",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/test-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await magister.initialize()

    # Mock vault write
    magister.vault.write_note = AsyncMock(return_value="knowledge/test-123.md")

    path = await magister.store_knowledge(
        content="Test knowledge content",
        topic="test",
        metadata={"source": "test"}
    )

    assert path == "knowledge/test-123.md"
    magister.vault.write_note.assert_called_once()

    await magister.shutdown()
    await event_bus.close()
