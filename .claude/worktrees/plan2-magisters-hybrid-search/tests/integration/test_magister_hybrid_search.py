# tests/integration/test_magister_hybrid_search.py
"""Integration test: Hybrid search across all layers"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_hybrid_search_local_hit():
    """Test Level 1: Local vault hit"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    # Initialize components
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

    # Mock Qdrant to avoid connection
    teacher.qdrant.collection_exists = AsyncMock(return_value=True)

    await teacher.initialize()

    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_hybrid_vault",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    # Create local knowledge
    knowledge_dir = Path("./test_hybrid_vault/knowledge")
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    (knowledge_dir / "seo-2026.md").write_text("""---
id: seo-2026
source: local
quality_score: 9.0
---

SEO best practices for 2026 include Core Web Vitals optimization.
""")

    # Search (should hit local)
    result = await seo_magister.hybrid_search("SEO best practices 2026")

    assert result["source"] == "local"
    assert len(result["results"]) > 0

    # Cleanup
    import shutil
    shutil.rmtree("./test_hybrid_vault")
    await seo_magister.shutdown()
    await teacher.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_hybrid_search_teacher_hit():
    """Test Level 2: Teacher Qdrant hit"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    # Initialize components
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

    # Mock Qdrant to avoid connection
    teacher.qdrant.collection_exists = AsyncMock(return_value=True)

    await teacher.initialize()

    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_hybrid_vault_2",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    # Mock Teacher to return results
    teacher.execute_task = AsyncMock(return_value=MagicMock(
        status="success",
        result={
            "status": "success",
            "results": [
                {"content": "Teacher knowledge about SEO", "score": 0.9}
            ]
        }
    ))

    # Search (should hit Teacher)
    result = await seo_magister.hybrid_search("advanced SEO techniques")

    assert result["source"] == "teacher"
    assert len(result["results"]) > 0

    # Cleanup
    import shutil
    if Path("./test_hybrid_vault_2").exists():
        shutil.rmtree("./test_hybrid_vault_2")
    await seo_magister.shutdown()
    await teacher.shutdown()
    await event_bus.close()


@pytest.mark.asyncio
async def test_hybrid_search_researcher_request():
    """Test Level 3: Researcher request"""
    event_bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await event_bus.initialize()

    # Initialize components
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

    # Mock Qdrant to avoid connection
    teacher.qdrant.collection_exists = AsyncMock(return_value=True)

    await teacher.initialize()

    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_hybrid_vault_3",
        event_bus=event_bus,
        teacher=teacher,
    )

    await seo_magister.initialize()

    # Mock Teacher to return no results
    teacher.execute_task = AsyncMock(return_value=MagicMock(
        status="success",
        result={
            "status": "success",
            "results": []
        }
    ))

    # Mock event bus publish
    event_bus.publish = AsyncMock()

    # Search (should request Researcher)
    result = await seo_magister.hybrid_search("brand new SEO topic 2026")

    assert result["source"] == "researcher_requested"
    assert result["results"] == []
    assert "message" in result

    # Verify research was requested
    event_bus.publish.assert_called_once()
    call_args = event_bus.publish.call_args[1]
    assert call_args["event_type"] == "research_request"

    # Cleanup
    import shutil
    if Path("./test_hybrid_vault_3").exists():
        shutil.rmtree("./test_hybrid_vault_3")
    await seo_magister.shutdown()
    await teacher.shutdown()
    await event_bus.close()
