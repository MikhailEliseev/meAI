# tests/unit/test_intelligence_magister.py
"""Tests for Intelligence Magister"""

import pytest
from unittest.mock import AsyncMock

from meai.agents.magisters.intelligence_magister import IntelligenceMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_intelligence_magister_initialization():
    """Test Intelligence Magister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    intelligence_magister = IntelligenceMagister(
        agent_id="intelligence-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/intelligence-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await intelligence_magister.initialize()

    assert intelligence_magister.agent_id == "intelligence-magister-1"
    assert intelligence_magister.get_domain() == "intelligence"
    assert "gather_intelligence" in intelligence_magister.get_capabilities()
    assert "analyze_trends" in intelligence_magister.get_capabilities()
    assert "monitor_competitors" in intelligence_magister.get_capabilities()

    await intelligence_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_intelligence_magister_gather_intelligence():
    """Test Intelligence Magister can gather intelligence"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    intelligence_magister = IntelligenceMagister(
        agent_id="intelligence-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/intelligence-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await intelligence_magister.initialize()

    # Mock hybrid search
    intelligence_magister.hybrid_search = AsyncMock(return_value={
        "source": "local",
        "results": [
            {"content": "Market intelligence data", "score": 0.9}
        ]
    })

    result = await intelligence_magister.gather_intelligence(
        topic="medical marketing trends",
        sources=["industry_reports", "competitor_analysis"]
    )

    assert result["status"] == "success"
    assert "intelligence" in result
    assert result["topic"] == "medical marketing trends"

    await intelligence_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_intelligence_magister_analyze_trends():
    """Test Intelligence Magister can analyze trends"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    intelligence_magister = IntelligenceMagister(
        agent_id="intelligence-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/intelligence-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await intelligence_magister.initialize()

    result = await intelligence_magister.analyze_trends(
        industry="medical_marketing",
        timeframe="quarterly",
        data_points=[
            {"period": "Q1", "value": 100},
            {"period": "Q2", "value": 120},
            {"period": "Q3", "value": 150}
        ]
    )

    assert result["status"] == "success"
    assert "trends" in result
    assert "growth_rate" in result

    await intelligence_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_intelligence_magister_monitor_competitors():
    """Test Intelligence Magister can monitor competitors"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    intelligence_magister = IntelligenceMagister(
        agent_id="intelligence-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/intelligence-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await intelligence_magister.initialize()

    # Mock hybrid search
    intelligence_magister.hybrid_search = AsyncMock(return_value={
        "source": "teacher",
        "results": [
            {"content": "Competitor monitoring insights", "score": 0.85}
        ]
    })

    result = await intelligence_magister.monitor_competitors(
        competitors=["competitor1.com", "competitor2.com"],
        metrics=["traffic", "content", "social_media"]
    )

    assert result["status"] == "success"
    assert "monitoring_report" in result
    assert len(result["competitors"]) == 2

    await intelligence_magister.shutdown()
    await event_bus.close()
