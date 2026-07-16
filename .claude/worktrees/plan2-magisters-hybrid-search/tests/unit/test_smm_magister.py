# tests/unit/test_smm_magister.py
"""Tests for SMM Magister"""

import pytest
from unittest.mock import AsyncMock

from meai.agents.magisters.smm_magister import SMMMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_smm_magister_initialization():
    """Test SMM Magister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    smm_magister = SMMMagister(
        agent_id="smm-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/smm-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await smm_magister.initialize()

    assert smm_magister.agent_id == "smm-magister-1"
    assert smm_magister.get_domain() == "smm"
    assert "create_post" in smm_magister.get_capabilities()
    assert "schedule_posts" in smm_magister.get_capabilities()
    assert "analyze_engagement" in smm_magister.get_capabilities()

    await smm_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_smm_magister_create_post():
    """Test SMM Magister can create social media post"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    smm_magister = SMMMagister(
        agent_id="smm-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/smm-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await smm_magister.initialize()

    # Mock hybrid search
    smm_magister.hybrid_search = AsyncMock(return_value={
        "source": "local",
        "results": [
            {"content": "Social media best practices", "score": 0.9}
        ]
    })

    result = await smm_magister.create_post(
        topic="medical marketing tips",
        platform="linkedin",
        tone="professional"
    )

    assert result["status"] == "success"
    assert "post" in result
    assert result["platform"] == "linkedin"

    await smm_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_smm_magister_schedule_posts():
    """Test SMM Magister can schedule posts"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    smm_magister = SMMMagister(
        agent_id="smm-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/smm-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await smm_magister.initialize()

    result = await smm_magister.schedule_posts(
        posts=[
            {"content": "Post 1", "platform": "linkedin"},
            {"content": "Post 2", "platform": "twitter"}
        ],
        frequency="daily"
    )

    assert result["status"] == "success"
    assert "schedule" in result
    assert len(result["schedule"]) == 2

    await smm_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_smm_magister_analyze_engagement():
    """Test SMM Magister can analyze engagement"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    smm_magister = SMMMagister(
        agent_id="smm-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/smm-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await smm_magister.initialize()

    # Mock hybrid search
    smm_magister.hybrid_search = AsyncMock(return_value={
        "source": "teacher",
        "results": [
            {"content": "Engagement analysis metrics", "score": 0.85}
        ]
    })

    result = await smm_magister.analyze_engagement(
        post_id="post-123",
        metrics={"likes": 100, "comments": 20, "shares": 10, "views": 1000}
    )

    assert result["status"] == "success"
    assert "analysis" in result
    assert "engagement_rate" in result

    await smm_magister.shutdown()
    await event_bus.close()
