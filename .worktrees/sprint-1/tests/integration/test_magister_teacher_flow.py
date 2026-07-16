"""Integration test: Magister → Teacher communication flow"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus, Event
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_magister_queries_teacher():
    """Test Magister querying Teacher for knowledge

    Scenario:
    1. Magister sends query to Teacher via Event Bus
    2. Teacher searches Qdrant
    3. Teacher returns results to Magister
    """
    event_bus = EventBus()
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    # Initialize Teacher
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await teacher.initialize()

    # Store knowledge in Teacher
    knowledge = {
        "content": "SEO best practices for medical websites in 2026",
        "source": "https://perplexity.ai/search/medical-seo",
        "sources": ["source1", "source2"],
        "metadata": {"industry": "medical", "topic": "seo"},
    }

    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")

    # Initialize Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Magister queries Teacher
    query_event = Event(
        event_type="magister.query",
        source_agent_id="seo-magister-1",
        target_agent_id="teacher-1",
        priority=2,
        payload={
            "query": "medical SEO best practices",
            "collection": "seo_knowledge",
            "magister_id": "seo-magister-1",
        },
    )

    await event_bus.publish(query_event)

    # Simulate Teacher handling query
    query_result = await teacher.handle_magister_query({
        "query": "medical SEO best practices",
        "collection": "seo_knowledge",
        "magister_id": "seo-magister-1",
    })

    # Verify Teacher found knowledge
    assert query_result["status"] == "success"
    assert len(query_result["results"]) > 0
    assert "medical" in query_result["results"][0]["content"]

    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()
    await magister.shutdown()


@pytest.mark.asyncio
async def test_teacher_distributes_to_magister():
    """Test Teacher distributing new knowledge to Magister

    Scenario:
    1. Teacher stores new knowledge
    2. Teacher distributes to relevant Magister via Event Bus
    3. Magister receives notification
    """
    event_bus = EventBus()
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    # Initialize Teacher
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await teacher.initialize()

    # Initialize Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Track distribution events
    distribution_received = asyncio.Event()
    received_knowledge_id = None

    async def on_distribution(event: Event):
        nonlocal received_knowledge_id
        if event.event_type == "knowledge.distributed":
            received_knowledge_id = event.payload.get("knowledge_id")
            distribution_received.set()

    await event_bus.subscribe("knowledge.distributed", on_distribution)

    # Teacher stores and distributes knowledge
    knowledge = {
        "content": "New SEO algorithm update for 2026",
        "source": "https://perplexity.ai/search/seo-update",
        "sources": ["source1"],
        "metadata": {"topic": "seo"},
    }

    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")
    await teacher.distribute_to_magisters(knowledge_id, "seo_knowledge")

    # Wait for distribution
    await asyncio.wait_for(distribution_received.wait(), timeout=2.0)

    # Verify Magister received notification
    assert received_knowledge_id == knowledge_id

    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()
    await magister.shutdown()


@pytest.mark.asyncio
async def test_magister_caches_teacher_results():
    """Test Magister caching results from Teacher

    Scenario:
    1. Magister queries Teacher
    2. Teacher returns results
    3. Magister caches results locally
    4. Verify cached in database and Obsidian vault
    """
    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Mock Teacher response
    teacher_results = [{
        "id": "knowledge-1",
        "content": "Technical SEO checklist for 2026",
        "source": "teacher",
        "quality_score": 9.0,
        "similarity_score": 0.95,
        "metadata": {"topic": "technical_seo"},
    }]

    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = teacher_results

        # Search triggers Teacher query and caching
        results = await magister.search_knowledge(
            query="technical SEO checklist",
            search_local=True,
            search_teacher=True,
        )

        assert len(results) > 0

        # Wait for caching
        await asyncio.sleep(0.2)

        # Verify cached in database
        from sqlalchemy import text
        async with magister.db.session() as session:
            result = await session.execute(
                text("""
                SELECT COUNT(*) FROM magister_knowledge_cache
                WHERE magister_id = :magister_id
                """),
                {"magister_id": "seo-magister-1"},
            )
            count = result.scalar()

        assert count > 0

        # Verify cached in Obsidian vault
        knowledge_dir = Path("/tmp/test-seo-magister/knowledge")
        assert knowledge_dir.exists()
        cached_files = list(knowledge_dir.glob("*.md"))
        assert len(cached_files) > 0

    await magister.shutdown()


@pytest.mark.asyncio
async def test_magister_teacher_not_found_flow():
    """Test flow when Teacher doesn't have knowledge

    Scenario:
    1. Magister queries Teacher
    2. Teacher doesn't have knowledge
    3. Teacher requests Researcher
    4. Magister receives "not found" response
    """
    event_bus = EventBus()
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    # Initialize Teacher
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await teacher.initialize()

    # Initialize Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Track research requests
    research_requested = asyncio.Event()

    async def on_research_request(event: Event):
        if event.event_type == "research.requested":
            research_requested.set()

    await event_bus.subscribe("research.requested", on_research_request)

    # Magister queries Teacher for unknown topic
    query_result = await teacher.handle_magister_query({
        "query": "Quantum computing SEO strategies",
        "collection": "seo_knowledge",
        "magister_id": "seo-magister-1",
    })

    # Wait for research request
    await asyncio.wait_for(research_requested.wait(), timeout=2.0)

    # Verify Teacher requested Researcher
    assert query_result["status"] == "not_found"
    assert query_result["action"] == "research_requested"

    await teacher.shutdown()
    await magister.shutdown()


@pytest.mark.asyncio
async def test_multiple_magisters_teacher_interaction():
    """Test multiple Magisters interacting with Teacher

    Scenario:
    1. SEO Magister queries Teacher for SEO knowledge
    2. Content Magister queries Teacher for content knowledge
    3. Teacher returns domain-specific results to each
    """
    from meai.agents.magisters.content_magister import ContentMagister

    event_bus = EventBus()
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    # Initialize Teacher
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await teacher.initialize()

    # Store domain-specific knowledge
    seo_knowledge = {
        "content": "SEO optimization techniques",
        "source": "test",
        "sources": [],
        "metadata": {"domain": "seo"},
    }

    content_knowledge = {
        "content": "Content marketing strategies",
        "source": "test",
        "sources": [],
        "metadata": {"domain": "content"},
    }

    await teacher.store_knowledge(seo_knowledge, "seo_knowledge")
    await teacher.store_knowledge(content_knowledge, "content_knowledge")

    # Initialize Magisters
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-content-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await seo_magister.initialize()
    await content_magister.initialize()

    # Each Magister queries Teacher
    seo_result = await teacher.handle_magister_query({
        "query": "SEO optimization",
        "collection": "seo_knowledge",
        "magister_id": "seo-magister-1",
    })

    content_result = await teacher.handle_magister_query({
        "query": "content marketing",
        "collection": "content_knowledge",
        "magister_id": "content-magister-1",
    })

    # Verify domain-specific results
    assert seo_result["status"] == "success"
    assert len(seo_result["results"]) > 0
    assert "SEO" in seo_result["results"][0]["content"]

    assert content_result["status"] == "success"
    assert len(content_result["results"]) > 0
    assert "Content" in content_result["results"][0]["content"]

    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await qdrant.client.delete_collection("content_knowledge")
    await teacher.shutdown()
    await seo_magister.shutdown()
    await content_magister.shutdown()
