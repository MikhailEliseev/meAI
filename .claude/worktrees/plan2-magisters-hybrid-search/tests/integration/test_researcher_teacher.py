# tests/integration/test_researcher_teacher.py
"""Integration test: Researcher → Teacher workflow"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from meai.agents.researcher import ResearcherAgent
from meai.agents.teacher import TeacherAgent
from meai.agents.base_agent import Task, TaskStatus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_researcher_to_teacher_workflow():
    """Test full workflow: Researcher collects → Teacher stores"""

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

    await researcher.initialize()

    # Step 1: Researcher collects knowledge
    mock_research_result = {
        "content": "SEO best practices include keyword research, on-page optimization, and quality content creation.",
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

        # Step 2: Teacher evaluates the knowledge
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
        assert eval_result.result["quality_score"] > 0

        # Step 3: Teacher stores the knowledge (if quality is good)
        if eval_result.result["quality_score"] >= 60:
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

    await researcher.shutdown()


@pytest.mark.asyncio
async def test_low_quality_knowledge_rejected():
    """Test that low quality knowledge is rejected by Teacher"""

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

    # Low quality content (short, no keywords, unknown source)
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

    assert eval_result.status == "success"
    assert eval_result.result["quality_score"] < 60
    assert eval_result.result["evaluation"] == "low"

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

        assert store_result.status == "success"
        assert store_result.result["stored"] == False
        assert "below threshold" in store_result.result["reason"]
