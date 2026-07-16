# tests/unit/test_fallback_storage.py
import pytest
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_fallback_storage_initialization():
    """Test FallbackStorage can be initialized"""
    storage = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")

    assert storage.database_url == "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_fallback_storage_store_and_retrieve():
    """Test storing and retrieving knowledge"""
    storage = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    await storage.initialize()

    # Store knowledge
    knowledge_id = await storage.store_knowledge(
        content="SEO best practices",
        embedding=[0.1, 0.2, 0.3],
        metadata={"source": "test"},
    )

    assert knowledge_id is not None

    # Retrieve knowledge
    result = await storage.get_knowledge(knowledge_id)

    assert result is not None
    assert result["content"] == "SEO best practices"
    assert result["metadata"]["source"] == "test"

    await storage.shutdown()


@pytest.mark.asyncio
async def test_fallback_storage_search():
    """Test searching knowledge"""
    storage = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    await storage.initialize()

    # Store multiple items
    await storage.store_knowledge(
        content="SEO optimization",
        embedding=[0.1, 0.2, 0.3],
        metadata={"topic": "seo"},
    )
    await storage.store_knowledge(
        content="Content marketing",
        embedding=[0.4, 0.5, 0.6],
        metadata={"topic": "content"},
    )

    # Search
    results = await storage.search_knowledge(query="SEO", limit=5)

    assert len(results) > 0
    assert any("SEO" in r["content"] for r in results)

    await storage.shutdown()
