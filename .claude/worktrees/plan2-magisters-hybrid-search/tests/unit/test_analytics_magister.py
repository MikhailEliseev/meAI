# tests/unit/test_analytics_magister.py
"""Tests for Analytics Magister"""

import pytest
from unittest.mock import AsyncMock

from meai.agents.magisters.analytics_magister import AnalyticsMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_analytics_magister_initialization():
    """Test Analytics Magister can be initialized"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    analytics_magister = AnalyticsMagister(
        agent_id="analytics-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/analytics-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await analytics_magister.initialize()

    assert analytics_magister.agent_id == "analytics-magister-1"
    assert analytics_magister.get_domain() == "analytics"
    assert "analyze_traffic" in analytics_magister.get_capabilities()
    assert "generate_report" in analytics_magister.get_capabilities()
    assert "track_conversions" in analytics_magister.get_capabilities()

    await analytics_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_analytics_magister_analyze_traffic():
    """Test Analytics Magister can analyze traffic"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    analytics_magister = AnalyticsMagister(
        agent_id="analytics-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/analytics-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await analytics_magister.initialize()

    # Mock hybrid search
    analytics_magister.hybrid_search = AsyncMock(return_value={
        "source": "local",
        "results": [
            {"content": "Traffic analysis best practices", "score": 0.9}
        ]
    })

    result = await analytics_magister.analyze_traffic(
        data={
            "sessions": 1000,
            "users": 800,
            "pageviews": 3000,
            "bounce_rate": 45.5,
            "avg_session_duration": 180
        }
    )

    assert result["status"] == "success"
    assert "analysis" in result
    assert "metrics" in result

    await analytics_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_analytics_magister_generate_report():
    """Test Analytics Magister can generate report"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    analytics_magister = AnalyticsMagister(
        agent_id="analytics-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/analytics-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await analytics_magister.initialize()

    result = await analytics_magister.generate_report(
        report_type="monthly",
        data={
            "traffic": {"sessions": 1000, "users": 800},
            "conversions": {"total": 50, "rate": 5.0}
        }
    )

    assert result["status"] == "success"
    assert "report" in result
    assert result["report_type"] == "monthly"

    await analytics_magister.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_analytics_magister_track_conversions():
    """Test Analytics Magister can track conversions"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    analytics_magister = AnalyticsMagister(
        agent_id="analytics-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="obsidian/analytics-magister",
        event_bus=event_bus,
        teacher=teacher,
    )

    await analytics_magister.initialize()

    # Mock hybrid search
    analytics_magister.hybrid_search = AsyncMock(return_value={
        "source": "teacher",
        "results": [
            {"content": "Conversion tracking metrics", "score": 0.85}
        ]
    })

    result = await analytics_magister.track_conversions(
        goal="form_submission",
        data={
            "total_visitors": 1000,
            "conversions": 50,
            "value": 5000
        }
    )

    assert result["status"] == "success"
    assert "conversion_rate" in result
    assert "value_per_conversion" in result

    await analytics_magister.shutdown()
    await event_bus.close()
