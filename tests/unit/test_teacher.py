# tests/unit/test_teacher.py
import pytest
from unittest.mock import AsyncMock, patch
from meai.agents.teacher import TeacherAgent
from meai.agents.base_agent import Task, TaskStatus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_teacher_initialization():
    """Test TeacherAgent can be initialized"""
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    teacher = TeacherAgent(
        agent_id="teacher-1",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
    )

    assert teacher.agent_id == "teacher-1"
    assert teacher.agent_type == "teacher"
    capabilities = teacher.get_capabilities()
    assert "evaluate_knowledge" in capabilities
    assert "store_knowledge" in capabilities
    assert "search_knowledge" in capabilities


@pytest.mark.asyncio
async def test_teacher_store_knowledge():
    """Test storing knowledge in fallback (without Qdrant)"""
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    teacher = TeacherAgent(
        agent_id="teacher-1",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
    )

    # Mock embeddings encode
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        # Mock fallback store_knowledge
        with patch.object(teacher.fallback, 'store_knowledge', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = "fallback-12345678"

            task = Task(
                task_id="task-001",
                subtask_id="subtask-001",
                parent_task_id="task-001",
                action="store_knowledge",
                description="SEO best practices include keyword research",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await teacher.execute_task(task)

            # Should succeed with fallback storage
            assert result.status == "success"
            assert "stored" in result.result


@pytest.mark.asyncio
async def test_teacher_evaluate_knowledge():
    """Test evaluating knowledge quality"""
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    teacher = TeacherAgent(
        agent_id="teacher-1",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
    )

    task = Task(
        task_id="task-002",
        subtask_id="subtask-002",
        parent_task_id="task-002",
        action="evaluate_knowledge",
        description="SEO best practices from https://moz.com",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    result = await teacher.execute_task(task)

    assert result.status == "success"
    assert "quality_score" in result.result
    assert "evaluation" in result.result
    assert result.result["quality_score"] >= 0
    assert result.result["quality_score"] <= 100


@pytest.mark.asyncio
async def test_teacher_search_knowledge():
    """Test searching knowledge in fallback"""
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    teacher = TeacherAgent(
        agent_id="teacher-1",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
    )

    # Mock embeddings encode
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        # Mock fallback search
        with patch.object(teacher.fallback, 'search_knowledge', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            task = Task(
                task_id="task-003",
                subtask_id="subtask-003",
                parent_task_id="task-003",
                action="search_knowledge",
                description="keyword research",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await teacher.execute_task(task)

            assert result.status == "success"
            assert "results" in result.result
            assert isinstance(result.result["results"], list)


@pytest.mark.asyncio
async def test_handle_magister_query():
    """Test handling Magister queries"""
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    teacher = TeacherAgent(
        agent_id="teacher-1",
        database_url="sqlite+aiosqlite:///:memory:",
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
    )

    # Mock embeddings encode
    with patch.object(teacher.embeddings, 'encode', new_callable=AsyncMock) as mock_encode:
        mock_encode.return_value = [0.1] * 1024

        # Mock fallback search
        with patch.object(teacher.fallback, 'search_knowledge', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "content": "SEO best practices include keyword research",
                    "metadata": {"collection": "seo_knowledge", "source": "test"},
                }
            ]

            task = Task(
                task_id="task-004",
                subtask_id="subtask-004",
                parent_task_id="task-004",
                action="handle_magister_query",
                description="query: What are SEO best practices? | collection: seo_knowledge | magister_id: seo-magister-1",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await teacher.execute_task(task)

            assert result.status == "success"
            assert result.result["status"] == "success"
            assert "results" in result.result
            assert len(result.result["results"]) > 0
            assert result.result["magister_id"] == "seo-magister-1"
