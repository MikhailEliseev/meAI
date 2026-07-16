# tests/unit/test_content_magister.py
"""Tests for Content Magister"""

import pytest
from unittest.mock import AsyncMock

from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_content_magister_initialization():
    """Test Content Magister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    content_magister = ContentMagister(
        agent_id="content-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/content-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await content_magister.initialize()

    assert content_magister.agent_id == "content-magister-1"
    assert content_magister.get_domain() == "content"
    assert "generate_content" in content_magister.get_capabilities()
    assert "edit_content" in content_magister.get_capabilities()
    assert "plan_content" in content_magister.get_capabilities()

    await content_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_content_magister_generate_content():
    """Test Content Magister can generate content"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    content_magister = ContentMagister(
        agent_id="content-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/content-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await content_magister.initialize()

    # Mock hybrid search
    content_magister.hybrid_search = AsyncMock(return_value={
        "source": "local",
        "results": [
            {"content": "Content generation guidelines", "score": 0.9}
        ]
    })

    result = await content_magister.generate_content(
        topic="medical marketing",
        content_type="article",
        target_length=500
    )

    assert result["status"] == "success"
    assert "content" in result
    assert result["content_type"] == "article"

    await content_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_content_magister_edit_content():
    """Test Content Magister can edit content"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    content_magister = ContentMagister(
        agent_id="content-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/content-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await content_magister.initialize()

    result = await content_magister.edit_content(
        content="Original content with some errors.",
        edit_instructions="Fix grammar and improve clarity"
    )

    assert result["status"] == "success"
    assert "edited_content" in result
    assert "changes_made" in result

    await content_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_content_magister_plan_content():
    """Test Content Magister can plan content"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    content_magister = ContentMagister(
        agent_id="content-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/content-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await content_magister.initialize()

    # Mock hybrid search
    content_magister.hybrid_search = AsyncMock(return_value={
        "source": "teacher",
        "results": [
            {"content": "Content planning best practices", "score": 0.85}
        ]
    })

    result = await content_magister.plan_content(
        topic="medical marketing strategy",
        timeframe="monthly",
        content_types=["article", "social_post"]
    )

    assert result["status"] == "success"
    assert "plan" in result
    assert result["timeframe"] == "monthly"

    await content_magister.shutdown()
    await event_bus.close()
