# tests/unit/test_ads_magister.py
"""Tests for Ads Magister"""

import pytest
from unittest.mock import AsyncMock

from meai.agents.magisters.ads_magister import AdsMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_ads_magister_initialization():
    """Test Ads Magister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    ads_magister = AdsMagister(
        agent_id="ads-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/ads-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await ads_magister.initialize()

    assert ads_magister.agent_id == "ads-magister-1"
    assert ads_magister.get_domain() == "ads"
    assert "create_campaign" in ads_magister.get_capabilities()
    assert "optimize_budget" in ads_magister.get_capabilities()
    assert "analyze_performance" in ads_magister.get_capabilities()

    await ads_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_ads_magister_create_campaign():
    """Test Ads Magister can create ad campaign"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    ads_magister = AdsMagister(
        agent_id="ads-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/ads-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await ads_magister.initialize()

    # Mock hybrid search
    ads_magister.hybrid_search = AsyncMock(return_value={
        "source": "local",
        "results": [
            {"content": "Campaign creation best practices", "score": 0.9}
        ]
    })

    result = await ads_magister.create_campaign(
        name="Medical Marketing Campaign",
        platform="google_ads",
        budget=1000,
        target_audience="medical professionals"
    )

    assert result["status"] == "success"
    assert "campaign" in result
    assert result["platform"] == "google_ads"

    await ads_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_ads_magister_optimize_budget():
    """Test Ads Magister can optimize budget"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    ads_magister = AdsMagister(
        agent_id="ads-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/ads-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await ads_magister.initialize()

    result = await ads_magister.optimize_budget(
        campaign_id="camp-123",
        current_budget=1000,
        performance_data={"clicks": 100, "conversions": 5}
    )

    assert result["status"] == "success"
    assert "optimized_budget" in result
    assert "recommendations" in result

    await ads_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_ads_magister_analyze_performance():
    """Test Ads Magister can analyze campaign performance"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    ads_magister = AdsMagister(
        agent_id="ads-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/ads-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await ads_magister.initialize()

    # Mock hybrid search
    ads_magister.hybrid_search = AsyncMock(return_value={
        "source": "teacher",
        "results": [
            {"content": "Performance analysis metrics", "score": 0.85}
        ]
    })

    result = await ads_magister.analyze_performance(
        campaign_id="camp-123",
        metrics={"impressions": 1000, "clicks": 100, "conversions": 5, "spend": 500}
    )

    assert result["status"] == "success"
    assert "analysis" in result
    assert "ctr" in result
    assert "conversion_rate" in result

    await ads_magister.shutdown()
    await event_bus.close()
