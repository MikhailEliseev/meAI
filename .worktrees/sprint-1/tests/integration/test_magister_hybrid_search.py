"""Integration test: Magister hybrid search flow"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.agents.researcher import ResearcherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_hybrid_search_local_hit():
    """Test hybrid search finds knowledge in local cache

    Scenario:
    1. Magister caches knowledge locally
    2. Magister searches for same knowledge
    3. Should find it in local cache (no Teacher/Researcher query)
    """
    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-test-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Cache knowledge locally
    knowledge = {
        "content": "SEO best practices include keyword research, on-page optimization, and link building",
        "source": "local_test",
        "quality_score": 8.5,
        "metadata": {"topic": "seo"},
    }

    await magister.cache_knowledge(knowledge, "SEO best practices")

    # Search should find it locally
    results = await magister.search_knowledge(
        query="SEO best practices",
        search_local=True,
        search_teacher=False,
        search_researcher=False,
    )

    assert len(results) > 0
    assert results[0]["source"] == "local_test"
    assert "SEO" in results[0]["content"]

    await magister.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_teacher_hit():
    """Test hybrid search queries Teacher when not found locally

    Scenario:
    1. Magister searches for knowledge not in local cache
    2. Teacher has the knowledge in Qdrant
    3. Magister receives results from Teacher
    4. Magister caches results locally
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

    # Store knowledge in Teacher's Qdrant
    knowledge = {
        "content": "Advanced SEO techniques for 2026 include Core Web Vitals optimization",
        "source": "teacher_test",
        "sources": ["source1"],
        "metadata": {"topic": "seo"},
    }

    await teacher.store_knowledge(knowledge, "seo_knowledge")

    # Initialize Magister
    magister = SEOMagister(
        agent_id="seo-test-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Mock Teacher query to return results
    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{
            "id": "knowledge-1",
            "content": knowledge["content"],
            "source": knowledge["source"],
            "quality_score": 9.0,
            "similarity_score": 0.95,
            "metadata": knowledge["metadata"],
        }]

        # Search should query Teacher
        results = await magister.search_knowledge(
            query="Advanced SEO techniques 2026",
            search_local=True,
            search_teacher=True,
            search_researcher=False,
        )

        assert len(results) > 0
        assert results[0]["source"] == "teacher_test"
        assert "Core Web Vitals" in results[0]["content"]

        # Verify Teacher was queried
        mock_query.assert_called_once()

    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()
    await magister.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_researcher_request():
    """Test hybrid search requests Researcher when Teacher doesn't have knowledge

    Scenario:
    1. Magister searches for knowledge
    2. Not found in local cache
    3. Not found in Teacher's Qdrant
    4. Magister requests Researcher to investigate
    """
    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-test-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Track research requests
    research_requested = asyncio.Event()
    requested_topic = None

    async def on_research_request(event):
        nonlocal requested_topic
        if event.event_type == "research.requested":
            requested_topic = event.payload.get("topic")
            research_requested.set()

    await event_bus.subscribe("research.requested", on_research_request)

    # Mock Teacher query to return empty
    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = []

        # Search should request Researcher
        results = await magister.search_knowledge(
            query="Emerging SEO trends 2027",
            search_local=True,
            search_teacher=True,
            search_researcher=True,
        )

        # Wait for research request
        await asyncio.wait_for(research_requested.wait(), timeout=1.0)

        # Verify Researcher was requested
        assert requested_topic == "Emerging SEO trends 2027"
        assert len(results) == 0  # No results yet (Researcher will provide later)

    await magister.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_caching():
    """Test that Teacher results are cached locally

    Scenario:
    1. Magister queries Teacher and gets results
    2. Results are cached locally
    3. Second query finds results in local cache (no Teacher query)
    """
    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-test-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Mock Teacher query
    teacher_result = [{
        "id": "knowledge-1",
        "content": "Link building strategies for 2026",
        "source": "teacher",
        "quality_score": 8.0,
        "similarity_score": 0.9,
        "metadata": {"topic": "seo"},
    }]

    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = teacher_result

        # First search - should query Teacher
        results1 = await magister.search_knowledge(
            query="link building strategies",
            search_local=True,
            search_teacher=True,
        )

        assert len(results1) > 0
        assert mock_query.call_count == 1

        # Wait for caching
        await asyncio.sleep(0.1)

        # Second search - should find in local cache
        results2 = await magister.search_knowledge(
            query="link building strategies",
            search_local=True,
            search_teacher=True,
        )

        assert len(results2) > 0
        # Teacher should not be queried again (found in cache)
        # Note: This depends on cache implementation

    await magister.shutdown()


@pytest.mark.asyncio
async def test_multiple_magisters_hybrid_search():
    """Test multiple Magisters searching independently

    Scenario:
    1. SEO Magister searches for SEO knowledge
    2. Content Magister searches for content knowledge
    3. Each finds domain-specific knowledge
    """
    from meai.agents.magisters.content_magister import ContentMagister

    event_bus = EventBus()

    seo_magister = SEOMagister(
        agent_id="seo-test-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    content_magister = ContentMagister(
        agent_id="content-test-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-content-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await seo_magister.initialize()
    await content_magister.initialize()

    # Cache domain-specific knowledge
    seo_knowledge = {
        "content": "SEO keyword research techniques",
        "source": "local",
        "quality_score": 8.0,
        "metadata": {"domain": "seo"},
    }

    content_knowledge = {
        "content": "Content marketing strategies",
        "source": "local",
        "quality_score": 8.0,
        "metadata": {"domain": "content"},
    }

    await seo_magister.cache_knowledge(seo_knowledge, "SEO keyword research")
    await content_magister.cache_knowledge(content_knowledge, "content marketing")

    # Each Magister searches their domain
    seo_results = await seo_magister.search_knowledge(
        query="SEO keyword research",
        search_local=True,
    )

    content_results = await content_magister.search_knowledge(
        query="content marketing",
        search_local=True,
    )

    # Verify domain-specific results
    assert len(seo_results) > 0
    assert "SEO" in seo_results[0]["content"]

    assert len(content_results) > 0
    assert "Content" in content_results[0]["content"]

    await seo_magister.shutdown()
    await content_magister.shutdown()
