# tests/unit/test_seo_magister.py
"""Tests for SEO Magister"""

import pytest
from unittest.mock import AsyncMock

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_seo_magister_initialization():
    """Test SEO Magister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
    )

    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/seo-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    assert seo_magister.agent_id == "seo-magister-1"
    assert seo_magister.get_domain() == "seo"
    assert "analyze_keywords" in seo_magister.get_capabilities()
    assert "optimize_content" in seo_magister.get_capabilities()
    assert "analyze_competitors" in seo_magister.get_capabilities()

    await seo_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_seo_magister_analyze_keywords():
    """Test SEO Magister can analyze keywords"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/seo-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    # Mock hybrid search
    seo_magister.hybrid_search = AsyncMock(return_value={
        "source": "local",
        "results": [
            {"content": "SEO keywords analysis", "score": 0.9}
        ]
    })

    result = await seo_magister.analyze_keywords("medical marketing")

    assert result["status"] == "success"
    assert "keywords" in result

    await seo_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_seo_magister_optimize_content():
    """Test SEO Magister can optimize content"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/seo-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    result = await seo_magister.optimize_content(
        content="Test content",
        target_keywords=["medical", "marketing"]
    )

    assert result["status"] == "success"
    assert "optimized_content" in result

    await seo_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_seo_magister_analyze_competitors():
    """Test SEO Magister can analyze competitors"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/seo-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    # Mock hybrid search
    seo_magister.hybrid_search = AsyncMock(return_value={
        "source": "teacher",
        "results": [
            {"content": "Competitor analysis data", "score": 0.85}
        ]
    })

    result = await seo_magister.analyze_competitors(
        domain="medical-marketing.com",
        keywords=["medical", "marketing"]
    )

    assert result["status"] == "success"
    assert "analysis" in result

    await seo_magister.shutdown()
    await event_bus.close()
