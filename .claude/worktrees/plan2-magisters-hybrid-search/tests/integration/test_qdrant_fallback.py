# tests/integration/test_qdrant_fallback.py
"""Integration test: Qdrant fallback to SQLite"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from meai.agents.teacher import TeacherAgent
from meai.agents.base_agent import Task, TaskStatus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_qdrant_unavailable_fallback_to_sqlite():
    """Test automatic fallback to SQLite when Qdrant is unavailable"""

    # Initialize Teacher with Qdrant that will fail
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

    await fallback.initialize()

    # Mock embeddings
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        # Mock Qdrant to fail (simulate unavailable)
        with patch.object(teacher.qdrant, 'upsert_points', new_callable=AsyncMock) as mock_upsert:
            mock_upsert.side_effect = Exception("Qdrant unavailable")

            # Mock fallback storage
            with patch.object(teacher.fallback, 'store_knowledge', new_callable=AsyncMock) as mock_store:
                mock_store.return_value = "fallback-12345678"

                # Try to store knowledge - should fallback to SQLite
                store_task = Task(
                    task_id="task-001",
                    subtask_id="subtask-001",
                    parent_task_id="task-001",
                    action="store_knowledge",
                    description="SEO best practices include keyword research and quality content",
                    priority=1,
                    status=TaskStatus.RECEIVED,
                    created_at=datetime.now(timezone.utc),
                    received_at=datetime.now(timezone.utc),
                )

                result = await teacher.execute_task(store_task)

                # Should succeed with fallback
                assert result.status == "success"
                assert result.result["stored"] == True
                assert result.result["stored_in"] == "fallback"
                assert "fallback-" in result.result["knowledge_id"]

                # Verify fallback was called
                mock_store.assert_called_once()

    await fallback.shutdown()


@pytest.mark.asyncio
async def test_search_fallback_when_qdrant_fails():
    """Test search falls back to SQLite when Qdrant fails"""

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

    await fallback.initialize()

    # Mock embeddings
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        # Mock Qdrant collection_exists to fail
        with patch.object(teacher.qdrant, 'collection_exists', new_callable=AsyncMock) as mock_exists:
            mock_exists.side_effect = Exception("Qdrant unavailable")

            # Mock fallback search
            with patch.object(teacher.fallback, 'search_knowledge', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = [
                    {
                        "content": "SEO best practices",
                        "metadata": {"collection": "seo_knowledge", "source": "test"},
                    }
                ]

                # Search should fallback to SQLite
                search_task = Task(
                    task_id="task-002",
                    subtask_id="subtask-002",
                    parent_task_id="task-002",
                    action="search_knowledge",
                    description="SEO best practices",
                    priority=1,
                    status=TaskStatus.RECEIVED,
                    created_at=datetime.now(timezone.utc),
                    received_at=datetime.now(timezone.utc),
                )

                result = await teacher.execute_task(search_task)

                # Should succeed with fallback results
                assert result.status == "success"
                assert len(result.result["results"]) > 0
                assert "SEO" in result.result["results"][0]["content"]

                # Verify fallback was called
                mock_search.assert_called_once()

    await fallback.shutdown()


@pytest.mark.asyncio
async def test_qdrant_success_no_fallback():
    """Test that fallback is NOT used when Qdrant works"""

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

    # Mock embeddings
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        # Mock Qdrant to succeed
        with patch.object(teacher.qdrant, 'upsert_points', new_callable=AsyncMock) as mock_upsert:
            mock_upsert.return_value = None  # Success

            # Mock fallback storage (should NOT be called)
            with patch.object(teacher.fallback, 'store_knowledge', new_callable=AsyncMock) as mock_store:

                store_task = Task(
                    task_id="task-003",
                    subtask_id="subtask-003",
                    parent_task_id="task-003",
                    action="store_knowledge",
                    description="SEO best practices include keyword research and quality content",
                    priority=1,
                    status=TaskStatus.RECEIVED,
                    created_at=datetime.now(timezone.utc),
                    received_at=datetime.now(timezone.utc),
                )

                result = await teacher.execute_task(store_task)

                # Should succeed with Qdrant
                assert result.status == "success"
                assert result.result["stored"] == True
                assert result.result["stored_in"] == "qdrant"

                # Verify fallback was NOT called
                mock_store.assert_not_called()
