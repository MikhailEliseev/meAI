# tests/unit/test_qdrant_client.py
import pytest
from meai.knowledge.qdrant_client import QdrantClient


@pytest.mark.asyncio
async def test_qdrant_client_initialization():
    """Test QdrantClient can be initialized"""
    client = QdrantClient(url="http://localhost:6333")

    assert client.url == "http://localhost:6333"
    assert client.client is None  # Not connected yet


@pytest.mark.asyncio
async def test_qdrant_client_connect():
    """Test connecting to Qdrant server"""
    client = QdrantClient(url="http://localhost:6333")

    await client.connect()

    assert client.client is not None

    await client.disconnect()
