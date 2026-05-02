"""Embeddings model wrapper for sentence-transformers"""

import asyncio
from typing import Any
from sentence_transformers import SentenceTransformer


class EmbeddingsModel:
    """Wrapper for sentence-transformers embeddings model"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """Initialize embeddings model

        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        self.model: SentenceTransformer | None = None
        self.dimension: int = 0

    async def load(self) -> None:
        """Load the embeddings model"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None, SentenceTransformer, self.model_name
        )

        # Get embedding dimension
        test_embedding = self.model.encode("test")
        self.dimension = len(test_embedding)

    async def encode(self, text: str) -> list[float]:
        """Encode text to embedding vector

        Args:
            text: Text to encode

        Returns:
            Embedding vector as list of floats
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.model.encode, text
        )

        return embedding.tolist()

    async def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to embeddings

        Args:
            texts: List of texts to encode

        Returns:
            List of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.model.encode, texts
        )

        return [emb.tolist() for emb in embeddings]
