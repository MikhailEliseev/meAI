"""Qdrant vector database client"""

from typing import Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class QdrantClient:
    """Async Qdrant client wrapper"""

    def __init__(self, url: str = "http://localhost:6333"):
        """Initialize Qdrant client

        Args:
            url: Qdrant server URL
        """
        self.url = url
        self.client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        """Connect to Qdrant server"""
        self.client = AsyncQdrantClient(url=self.url)

    async def disconnect(self) -> None:
        """Disconnect from Qdrant server"""
        if self.client:
            await self.client.close()
            self.client = None

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: Distance = Distance.COSINE,
    ) -> None:
        """Create a collection

        Args:
            collection_name: Name of the collection
            vector_size: Size of vectors (default: 768 for bge-m3)
            distance: Distance metric (default: COSINE)
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        collections = await self.client.get_collections()
        return any(c.name == collection_name for c in collections.collections)

    async def upsert_points(
        self,
        collection_name: str,
        points: list[PointStruct],
    ) -> None:
        """Upsert points into collection

        Args:
            collection_name: Name of the collection
            points: List of points to upsert
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        await self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors

        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of search results with id, score, and payload
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            }
            for result in results
        ]
