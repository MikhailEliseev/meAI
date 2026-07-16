# tests/e2e/test_full_workflow.py
"""End-to-end test: Full University Infrastructure workflow"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from meai.agents.researcher import ResearcherAgent
from meai.agents.teacher import TeacherAgent
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage
from meai.knowledge.wiki_synthesizer import WikiSynthesizer
from meai.agents.base_agent import Task, TaskStatus


@pytest.mark.asyncio
async def test_full_workflow_research_to_storage():
    """
    End-to-end test: Complete workflow from research request to knowledge storage

    Flow:
    1. Researcher receives research request
    2. Researcher collects knowledge from Perplexity
    3. Teacher evaluates knowledge quality
    4. Teacher stores high-quality knowledge
    5. Teacher can search and retrieve stored knowledge
    6. WikiSynthesizer extracts wikilinks
    """

    print("\n🚀 Starting end-to-end workflow test...")

    # ========== Setup ==========
    print("\n1️⃣ Initializing components...")

    # Initialize Researcher
    researcher = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
        perplexity_api_key="test-key",
    )

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

    # Initialize WikiSynthesizer
    synthesizer = WikiSynthesizer()

    await researcher.initialize()
    await fallback.initialize()

    print("  ✓ All components initialized")

    # ========== Step 1: Research ==========
    print("\n2️⃣ Researcher collecting knowledge...")

    mock_research_result = {
        "content": "SEO best practices include [[keyword research]], [[on-page optimization]], and [[link building]]. Quality content is essential for [[search engine rankings]].",
        "sources": ["https://moz.com/seo", "https://google.com/seo"],
    }

    with patch.object(researcher.perplexity, 'research', new_callable=AsyncMock) as mock_research:
        mock_research.return_value = mock_research_result

        research_task = Task(
            task_id="task-001",
            subtask_id="subtask-001",
            parent_task_id="task-001",
            action="research_topic",
            description="Research SEO best practices",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
        )

        research_result = await researcher.execute_task(research_task)

        assert research_result.status == "success"
        assert "content" in research_result.result
        assert "sources" in research_result.result

        print(f"  ✓ Research completed: {len(research_result.result['content'])} chars")
        print(f"  ✓ Sources: {len(research_result.result['sources'])} URLs")

    # ========== Step 2: Evaluate Quality ==========
    print("\n3️⃣ Teacher evaluating knowledge quality...")

    eval_task = Task(
        task_id="task-002",
        subtask_id="subtask-002",
        parent_task_id="task-002",
        action="evaluate_knowledge",
        description=f"{research_result.result['content']} from {research_result.result['sources'][0]}",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    eval_result = await teacher.execute_task(eval_task)

    assert eval_result.status == "success"
    assert "quality_score" in eval_result.result
    assert eval_result.result["quality_score"] >= 60  # Should be high quality

    print(f"  ✓ Quality score: {eval_result.result['quality_score']}/100")
    print(f"  ✓ Evaluation: {eval_result.result['evaluation']}")

    # ========== Step 3: Extract Wikilinks ==========
    print("\n4️⃣ WikiSynthesizer extracting wikilinks...")

    wikilinks = synthesizer.extract_wikilinks(research_result.result['content'])

    assert len(wikilinks) > 0
    assert "keyword research" in wikilinks
    assert "on-page optimization" in wikilinks

    print(f"  ✓ Extracted {len(wikilinks)} wikilinks:")
    for link in wikilinks:
        print(f"    - [[{link}]]")

    # ========== Step 4: Store Knowledge ==========
    print("\n5️⃣ Teacher storing knowledge...")

    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        with patch.object(teacher.fallback, 'store_knowledge', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = "knowledge-12345678"

            store_task = Task(
                task_id="task-003",
                subtask_id="subtask-003",
                parent_task_id="task-003",
                action="store_knowledge",
                description=research_result.result['content'],
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            store_result = await teacher.execute_task(store_task)

            assert store_result.status == "success"
            assert store_result.result["stored"] == True

            print(f"  ✓ Knowledge stored: {store_result.result['knowledge_id']}")
            print(f"  ✓ Collection: {store_result.result['collection']}")
            print(f"  ✓ Storage: {store_result.result['stored_in']}")

    # ========== Step 5: Search Knowledge ==========
    print("\n6️⃣ Teacher searching stored knowledge...")

    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        with patch.object(teacher.fallback, 'search_knowledge', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "content": research_result.result['content'],
                    "metadata": {
                        "collection": "seo_knowledge",
                        "source": research_result.result['sources'][0],
                    },
                }
            ]

            search_task = Task(
                task_id="task-004",
                subtask_id="subtask-004",
                parent_task_id="task-004",
                action="search_knowledge",
                description="keyword research",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            search_result = await teacher.execute_task(search_task)

            assert search_result.status == "success"
            assert len(search_result.result["results"]) > 0
            assert "keyword research" in search_result.result["results"][0]["content"]

            print(f"  ✓ Found {len(search_result.result['results'])} results")
            print(f"  ✓ Top result score: {search_result.result['results'][0].get('score', 'N/A')}")

    # ========== Step 6: Synthesize Knowledge ==========
    print("\n7️⃣ WikiSynthesizer synthesizing knowledge...")

    knowledge_items = [
        {
            "id": "k1",
            "content": research_result.result['content'],
            "topic": "seo",
        }
    ]

    synthesized = await synthesizer.synthesize(knowledge_items)

    assert synthesized["topic"] == "seo"
    assert len(synthesized["wikilinks"]) > 0
    assert "keyword research" in synthesized["wikilinks"]

    print(f"  ✓ Synthesized topic: {synthesized['topic']}")
    print(f"  ✓ Wikilinks: {len(synthesized['wikilinks'])}")
    print(f"  ✓ Cross-references: {len(synthesized['cross_references'])}")

    # ========== Cleanup ==========
    await researcher.shutdown()
    await fallback.shutdown()

    print("\n" + "=" * 60)
    print("✅ End-to-end workflow completed successfully!")
    print("=" * 60)
    print("\nWorkflow summary:")
    print("  1. ✓ Researcher collected knowledge from Perplexity")
    print("  2. ✓ Teacher evaluated quality (score: {}/100)".format(eval_result.result['quality_score']))
    print("  3. ✓ WikiSynthesizer extracted {} wikilinks".format(len(wikilinks)))
    print("  4. ✓ Teacher stored knowledge in {}".format(store_result.result['stored_in']))
    print("  5. ✓ Teacher searched and retrieved knowledge")
    print("  6. ✓ WikiSynthesizer synthesized knowledge graph")
    print("\n🎉 All systems operational!")


@pytest.mark.asyncio
async def test_workflow_with_low_quality_rejection():
    """Test that low quality knowledge is rejected in the workflow"""

    print("\n🧪 Testing low quality rejection workflow...")

    teacher = TeacherAgent(
        agent_id="teacher",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=QdrantClient(url="http://localhost:6333"),
        embeddings_model=EmbeddingsModel(model_name="BAAI/bge-m3"),
        fallback_storage=FallbackStorage(database_url="sqlite+aiosqlite:///:memory:"),
    )

    # Low quality content
    eval_task = Task(
        task_id="task-001",
        subtask_id="subtask-001",
        parent_task_id="task-001",
        action="evaluate_knowledge",
        description="SEO is good from unknown",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    eval_result = await teacher.execute_task(eval_task)

    assert eval_result.result["quality_score"] < 60
    print(f"  ✓ Low quality detected: {eval_result.result['quality_score']}/100")

    # Try to store - should be rejected
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        store_task = Task(
            task_id="task-002",
            subtask_id="subtask-002",
            parent_task_id="task-002",
            action="store_knowledge",
            description="SEO is good",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
        )

        store_result = await teacher.execute_task(store_task)

        assert store_result.result["stored"] == False
        print(f"  ✓ Storage rejected: {store_result.result['reason']}")

    print("  ✅ Quality control working correctly!")
