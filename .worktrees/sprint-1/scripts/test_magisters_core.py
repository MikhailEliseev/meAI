"""Complete end-to-end test of Magisters system"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.agents.researcher import ResearcherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


def print_header(title: str):
    """Print section header"""
    print()
    print("=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"📋 {message}")


async def test_1_initialize_magisters():
    """Test 1: Initialize all Magisters"""
    print_header("Initialize Magisters")

    try:
        event_bus = EventBus()

        magisters = []

        # Initialize SEO Magister
        seo_magister = SEOMagister(
            agent_id="seo-magister-1",
            event_bus=event_bus,
            vault_path=Path("/tmp/test-magisters/seo-magister"),
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await seo_magister.initialize()
        magisters.append(("SEO Magister", seo_magister))
        print_success("SEO Magister initialized")

        # Verify capabilities
        capabilities = seo_magister.get_capabilities()
        print_info(f"   Capabilities: {len(capabilities)}")
        print_info(f"   Domain: {seo_magister.domain}")

        return {
            "event_bus": event_bus,
            "magisters": magisters,
        }

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        raise


async def test_2_hybrid_search_local_cache():
    """Test 2: Hybrid search - local cache hit"""
    print_header("Hybrid Search - Local Cache")

    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magisters/seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Cache knowledge locally
    knowledge = {
        "content": "SEO best practices for 2026: Focus on Core Web Vitals, E-E-A-T content, and AI-powered search optimization",
        "source": "local_cache",
        "quality_score": 9.0,
        "metadata": {"topic": "seo", "year": "2026"},
    }

    print_info("Caching knowledge locally...")
    await magister.cache_knowledge(knowledge, "SEO best practices 2026")
    print_success("Knowledge cached")

    # Search should find it locally
    print_info("Searching local cache...")
    results = await magister.search_knowledge(
        query="SEO best practices 2026",
        search_local=True,
        search_teacher=False,
        search_researcher=False,
    )

    if len(results) > 0:
        print_success(f"Found {len(results)} results in local cache")
        print_info(f"   Source: {results[0]['source']}")
        print_info(f"   Quality: {results[0]['quality_score']}")
        await magister.shutdown()
        return True
    else:
        print_error("No results found in local cache")
        await magister.shutdown()
        return False


async def test_3_hybrid_search_teacher_query():
    """Test 3: Hybrid search - Teacher query"""
    print_header("Hybrid Search - Teacher Query")

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
    print_success("Teacher initialized")

    # Store knowledge in Teacher
    knowledge = {
        "content": "Advanced SEO techniques: Schema markup, internal linking strategies, and content clustering",
        "source": "teacher_qdrant",
        "sources": ["source1", "source2"],
        "metadata": {"topic": "advanced_seo"},
    }

    print_info("Storing knowledge in Teacher (Qdrant)...")
    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")
    print_success(f"Knowledge stored (ID: {knowledge_id})")

    # Initialize Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magisters/seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Mock Teacher query
    print_info("Magister querying Teacher...")
    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{
            "id": knowledge_id,
            "content": knowledge["content"],
            "source": knowledge["source"],
            "quality_score": 9.0,
            "similarity_score": 0.95,
            "metadata": knowledge["metadata"],
        }]

        results = await magister.search_knowledge(
            query="Advanced SEO techniques",
            search_local=True,
            search_teacher=True,
            search_researcher=False,
        )

        if len(results) > 0:
            print_success(f"Found {len(results)} results from Teacher")
            print_info(f"   Similarity: {results[0]['similarity_score']:.2f}")
            print_info(f"   Quality: {results[0]['quality_score']}")

            # Cleanup
            await qdrant.client.delete_collection("seo_knowledge")
            await teacher.shutdown()
            await magister.shutdown()
            return True
        else:
            print_error("No results from Teacher")
            await qdrant.client.delete_collection("seo_knowledge")
            await teacher.shutdown()
            await magister.shutdown()
            return False


async def test_4_hybrid_search_researcher_request():
    """Test 4: Hybrid search - Researcher request"""
    print_header("Hybrid Search - Researcher Request")

    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magisters/seo-magister"),
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

    # Mock Teacher to return empty
    print_info("Searching for unknown knowledge...")
    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = []

        results = await magister.search_knowledge(
            query="Emerging SEO trends 2027",
            search_local=True,
            search_teacher=True,
            search_researcher=True,
        )

        # Wait for research request
        try:
            await asyncio.wait_for(research_requested.wait(), timeout=1.0)
            print_success("Researcher request sent")
            print_info(f"   Topic: {requested_topic}")
            await magister.shutdown()
            return True
        except asyncio.TimeoutError:
            print_error("Researcher request not sent")
            await magister.shutdown()
            return False


async def test_5_knowledge_caching():
    """Test 5: Knowledge caching after Teacher query"""
    print_header("Knowledge Caching")

    event_bus = EventBus()

    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magisters/seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()

    # Mock Teacher response
    teacher_result = [{
        "id": "knowledge-1",
        "content": "Link building strategies for medical websites",
        "source": "teacher",
        "quality_score": 8.5,
        "similarity_score": 0.9,
        "metadata": {"topic": "link_building"},
    }]

    print_info("First query - Teacher returns results...")
    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = teacher_result

        # First search
        results1 = await magister.search_knowledge(
            query="link building strategies",
            search_local=True,
            search_teacher=True,
        )

        print_success(f"Results received: {len(results1)}")
        print_info("   Caching results locally...")

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

        if count > 0:
            print_success(f"Knowledge cached in database ({count} items)")

            # Verify vault file
            vault_path = Path("/tmp/test-magisters/seo-magister/knowledge")
            if vault_path.exists():
                cached_files = list(vault_path.glob("*.md"))
                print_success(f"Knowledge cached in Obsidian ({len(cached_files)} files)")
            else:
                print_info("Obsidian vault not created yet")

            await magister.shutdown()
            return True
        else:
            print_error("Knowledge not cached")
            await magister.shutdown()
            return False


async def test_6_end_to_end_flow():
    """Test 6: Complete end-to-end flow"""
    print_header("End-to-End Flow")

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
    print_success("Teacher initialized")

    # Initialize Researcher (mocked)
    researcher = ResearcherAgent(
        agent_id="researcher-1",
        event_bus=event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await researcher.initialize()
    print_success("Researcher initialized")

    # Initialize Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        vault_path=Path("/tmp/test-magisters/seo-magister"),
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await magister.initialize()
    print_success("SEO Magister initialized")

    print()
    print_info("Scenario: Magister queries → Teacher → Researcher → Cache")
    print()

    # Step 1: First query - not in cache, not in Teacher
    print_info("Step 1: First query (not in cache)")
    results1 = await magister.search_knowledge(
        query="SEO for medical websites 2026",
        search_local=True,
        search_teacher=False,
        search_researcher=False,
    )
    print_info(f"   Results: {len(results1)} (expected: 0)")

    # Step 2: Store knowledge in Teacher
    print_info("Step 2: Researcher finds knowledge, Teacher stores it")
    knowledge = {
        "content": "Medical SEO best practices: HIPAA compliance, medical schema markup, and patient-focused content",
        "source": "researcher_perplexity",
        "sources": ["source1", "source2"],
        "metadata": {"industry": "medical", "topic": "seo"},
    }

    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")
    print_success(f"   Knowledge stored (ID: {knowledge_id})")

    # Step 3: Second query - should find in Teacher
    print_info("Step 3: Second query (should find in Teacher)")
    with patch.object(magister, 'query_teacher', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{
            "id": knowledge_id,
            "content": knowledge["content"],
            "source": knowledge["source"],
            "quality_score": 9.0,
            "similarity_score": 0.95,
            "metadata": knowledge["metadata"],
        }]

        results2 = await magister.search_knowledge(
            query="SEO for medical websites 2026",
            search_local=True,
            search_teacher=True,
        )

        if len(results2) > 0:
            print_success(f"   Results: {len(results2)} from Teacher")
            print_info("   Caching locally...")
            await asyncio.sleep(0.2)

            # Step 4: Third query - should find in local cache
            print_info("Step 4: Third query (should find in local cache)")
            results3 = await magister.search_knowledge(
                query="SEO for medical websites 2026",
                search_local=True,
                search_teacher=False,
            )

            if len(results3) > 0:
                print_success(f"   Results: {len(results3)} from local cache")
                print_success("End-to-end flow completed successfully!")

                # Cleanup
                await qdrant.client.delete_collection("seo_knowledge")
                await teacher.shutdown()
                await researcher.shutdown()
                await magister.shutdown()
                return True
            else:
                print_error("   Not found in local cache")

    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()
    await researcher.shutdown()
    await magister.shutdown()
    return False


async def main():
    """Run all tests"""
    print()
    print("🧪 Testing Magisters Core System")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_passed = True

    try:
        # Test 1: Initialize
        await test_1_initialize_magisters()

        # Test 2: Local cache
        if not await test_2_hybrid_search_local_cache():
            all_passed = False

        # Test 3: Teacher query
        if not await test_3_hybrid_search_teacher_query():
            all_passed = False

        # Test 4: Researcher request
        if not await test_4_hybrid_search_researcher_request():
            all_passed = False

        # Test 5: Caching
        if not await test_5_knowledge_caching():
            all_passed = False

        # Test 6: End-to-end
        if not await test_6_end_to_end_flow():
            all_passed = False

    except Exception as e:
        print_error(f"Test suite failed: {e}")
        all_passed = False

    # Final result
    print()
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
