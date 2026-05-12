"""
Embeddings Generator

Generates semantic embeddings using Sentence-BERT for content clustering.
Uses all-MiniLM-L6-v2 model for fast, high-quality embeddings.
"""

import hashlib
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingsGenerator:
    """Generate and cache semantic embeddings for text content

    Uses Sentence-BERT (all-MiniLM-L6-v2) for generating embeddings.
    Supports batch processing and caching for performance.

    Model: all-MiniLM-L6-v2
    - Embedding size: 384 dimensions
    - Speed: ~14,000 sentences/sec on CPU
    - Quality: Good balance of speed and accuracy
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        cache_dir: Optional[Path] = None,
        device: str = "cpu",
    ):
        """Initialize embeddings generator

        Args:
            model_name: Sentence-BERT model name
            batch_size: Batch size for encoding
            cache_dir: Directory for caching embeddings
            device: Device to use ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device

        # Load model
        self.model = SentenceTransformer(model_name, device=device)

        # Cache setup
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache in memory for current session
        self._memory_cache: Dict[str, np.ndarray] = {}

    def generate_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Generate embeddings for list of texts

        Args:
            texts: List of text strings
            use_cache: Use cached embeddings if available
            show_progress: Show progress bar

        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        # Check cache
        if use_cache:
            cached_embeddings = self._get_cached_embeddings(texts)
            if cached_embeddings is not None:
                return cached_embeddings

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        # Cache embeddings
        if use_cache:
            self._cache_embeddings(texts, embeddings)

        return embeddings

    def generate_single_embedding(
        self,
        text: str,
        use_cache: bool = True,
    ) -> np.ndarray:
        """Generate embedding for single text

        Args:
            text: Text string
            use_cache: Use cached embedding if available

        Returns:
            Numpy array of shape (embedding_dim,)
        """
        embeddings = self.generate_embeddings([text], use_cache=use_cache)
        return embeddings[0]

    def calculate_similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
    ) -> np.ndarray:
        """Calculate cosine similarity between embeddings

        Args:
            embeddings1: Array of shape (n, embedding_dim)
            embeddings2: Array of shape (m, embedding_dim)

        Returns:
            Similarity matrix of shape (n, m)
        """
        return cosine_similarity(embeddings1, embeddings2)

    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 5,
    ) -> List[tuple[int, float]]:
        """Find most similar embeddings to query

        Args:
            query_embedding: Query embedding of shape (embedding_dim,)
            candidate_embeddings: Candidate embeddings of shape (n, embedding_dim)
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples
        """
        # Calculate similarities
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            candidate_embeddings
        )[0]

        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Return (index, score) tuples
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    def _get_cache_key(self, texts: List[str]) -> str:
        """Generate cache key for list of texts"""
        # Hash concatenated texts
        text_hash = hashlib.md5(
            "".join(texts).encode("utf-8")
        ).hexdigest()
        return f"{self.model_name}_{text_hash}"

    def _get_cached_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Get cached embeddings if available"""
        cache_key = self._get_cache_key(texts)

        # Check memory cache
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Check disk cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    embeddings = pickle.load(f)
                # Store in memory cache
                self._memory_cache[cache_key] = embeddings
                return embeddings

        return None

    def _cache_embeddings(self, texts: List[str], embeddings: np.ndarray) -> None:
        """Cache embeddings to memory and disk"""
        cache_key = self._get_cache_key(texts)

        # Store in memory cache
        self._memory_cache[cache_key] = embeddings

        # Store in disk cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, "wb") as f:
                pickle.dump(embeddings, f)

    def clear_cache(self) -> None:
        """Clear all cached embeddings"""
        # Clear memory cache
        self._memory_cache.clear()

        # Clear disk cache
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()

    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "embedding_dim": self.get_embedding_dim(),
            "batch_size": self.batch_size,
            "device": self.device,
            "max_seq_length": self.model.max_seq_length,
        }
