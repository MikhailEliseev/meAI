"""
Unit tests for EmbeddingsGenerator

Tests embedding generation, caching, and similarity calculations.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

from src.aim.subagents.content_gap_analysis.clustering.embeddings_generator import (
    EmbeddingsGenerator,
)


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory"""
    cache_dir = Path(tempfile.mkdtemp())
    yield cache_dir
    shutil.rmtree(cache_dir)


@pytest.fixture
def generator(temp_cache_dir):
    """Create EmbeddingsGenerator instance"""
    return EmbeddingsGenerator(
        model_name="all-MiniLM-L6-v2",
        batch_size=32,
        cache_dir=temp_cache_dir,
        device="cpu",
    )


@pytest.fixture
def sample_texts():
    """Sample texts for testing"""
    return [
        "Dental implants are artificial tooth roots.",
        "Teeth whitening improves smile appearance.",
        "Root canal treatment saves infected teeth.",
        "Orthodontics corrects misaligned teeth.",
        "Dental crowns restore damaged teeth.",
    ]


class TestEmbeddingsGenerator:
    """Test EmbeddingsGenerator functionality"""

    def test_initialization(self, generator):
        """Test generator initialization"""
        assert generator.model_name == "all-MiniLM-L6-v2"
        assert generator.batch_size == 32
        assert generator.device == "cpu"
        assert generator.model is not None

    def test_get_embedding_dim(self, generator):
        """Test getting embedding dimension"""
        dim = generator.get_embedding_dim()
        assert dim == 384  # all-MiniLM-L6-v2 has 384 dimensions

    def test_generate_embeddings(self, generator, sample_texts):
        """Test generating embeddings for multiple texts"""
        embeddings = generator.generate_embeddings(sample_texts, use_cache=False)

        assert embeddings.shape == (len(sample_texts), 384)
        assert embeddings.dtype == np.float32 or embeddings.dtype == np.float64

    def test_generate_single_embedding(self, generator):
        """Test generating embedding for single text"""
        text = "Dental implants are artificial tooth roots."
        embedding = generator.generate_single_embedding(text, use_cache=False)

        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32 or embedding.dtype == np.float64

    def test_embeddings_are_normalized(self, generator, sample_texts):
        """Test that embeddings are unit vectors (normalized)"""
        embeddings = generator.generate_embeddings(sample_texts, use_cache=False)

        # Check if embeddings are approximately normalized
        norms = np.linalg.norm(embeddings, axis=1)
        assert np.allclose(norms, 1.0, atol=0.1)

    def test_similar_texts_have_similar_embeddings(self, generator):
        """Test that similar texts have high cosine similarity"""
        text1 = "Dental implants replace missing teeth."
        text2 = "Dental implants are artificial tooth roots."
        text3 = "Teeth whitening makes teeth brighter."

        emb1 = generator.generate_single_embedding(text1, use_cache=False)
        emb2 = generator.generate_single_embedding(text2, use_cache=False)
        emb3 = generator.generate_single_embedding(text3, use_cache=False)

        # Calculate similarities
        sim_12 = np.dot(emb1, emb2)
        sim_13 = np.dot(emb1, emb3)

        # Similar texts (1 and 2) should have higher similarity than dissimilar (1 and 3)
        assert sim_12 > sim_13

    def test_calculate_similarity(self, generator, sample_texts):
        """Test calculating similarity between embeddings"""
        embeddings = generator.generate_embeddings(sample_texts, use_cache=False)

        # Calculate similarity matrix
        similarity_matrix = generator.calculate_similarity(embeddings, embeddings)

        # Check shape
        assert similarity_matrix.shape == (len(sample_texts), len(sample_texts))

        # Diagonal should be ~1.0 (self-similarity)
        diagonal = np.diag(similarity_matrix)
        assert np.allclose(diagonal, 1.0, atol=0.1)

        # Matrix should be symmetric
        assert np.allclose(similarity_matrix, similarity_matrix.T, atol=1e-5)

    def test_find_most_similar(self, generator, sample_texts):
        """Test finding most similar embeddings"""
        embeddings = generator.generate_embeddings(sample_texts, use_cache=False)

        # Query with first text
        query_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]

        # Find top 3 most similar
        results = generator.find_most_similar(
            query_embedding, candidate_embeddings, top_k=3
        )

        # Check results
        assert len(results) == 3
        assert all(isinstance(idx, int) for idx, _ in results)
        assert all(isinstance(score, float) for _, score in results)

        # Scores should be in descending order
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_caching_memory(self, generator, sample_texts):
        """Test in-memory caching"""
        # First call - no cache
        embeddings1 = generator.generate_embeddings(sample_texts, use_cache=True)

        # Second call - should use memory cache
        embeddings2 = generator.generate_embeddings(sample_texts, use_cache=True)

        # Should be identical
        assert np.array_equal(embeddings1, embeddings2)

    def test_caching_disk(self, generator, sample_texts, temp_cache_dir):
        """Test disk caching"""
        # Generate embeddings with caching
        embeddings1 = generator.generate_embeddings(sample_texts, use_cache=True)

        # Check cache file exists
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) > 0

        # Clear memory cache
        generator._memory_cache.clear()

        # Generate again - should load from disk
        embeddings2 = generator.generate_embeddings(sample_texts, use_cache=True)

        # Should be identical
        assert np.array_equal(embeddings1, embeddings2)

    def test_cache_disabled(self, generator, sample_texts):
        """Test that caching can be disabled"""
        # Generate without cache
        embeddings1 = generator.generate_embeddings(sample_texts, use_cache=False)
        embeddings2 = generator.generate_embeddings(sample_texts, use_cache=False)

        # Should be equal but not from cache
        assert np.allclose(embeddings1, embeddings2, atol=1e-5)
        assert len(generator._memory_cache) == 0

    def test_clear_cache(self, generator, sample_texts, temp_cache_dir):
        """Test clearing cache"""
        # Generate embeddings with caching
        generator.generate_embeddings(sample_texts, use_cache=True)

        # Check cache exists
        assert len(generator._memory_cache) > 0
        assert len(list(temp_cache_dir.glob("*.pkl"))) > 0

        # Clear cache
        generator.clear_cache()

        # Check cache is empty
        assert len(generator._memory_cache) == 0
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 0

    def test_empty_texts(self, generator):
        """Test handling empty text list"""
        embeddings = generator.generate_embeddings([], use_cache=False)
        assert embeddings.shape == (0,)

    def test_get_model_info(self, generator):
        """Test getting model information"""
        info = generator.get_model_info()

        assert info["model_name"] == "all-MiniLM-L6-v2"
        assert info["embedding_dim"] == 384
        assert info["batch_size"] == 32
        assert info["device"] == "cpu"
        assert "max_seq_length" in info

    def test_batch_processing(self, generator):
        """Test batch processing with large number of texts"""
        # Create 100 texts
        texts = [f"Sample text number {i}" for i in range(100)]

        # Generate embeddings
        embeddings = generator.generate_embeddings(texts, use_cache=False)

        # Check shape
        assert embeddings.shape == (100, 384)

    def test_long_text_handling(self, generator):
        """Test handling of long texts (truncation)"""
        # Create very long text (> max_seq_length)
        long_text = " ".join(["word"] * 1000)

        # Should not raise error (model truncates)
        embedding = generator.generate_single_embedding(long_text, use_cache=False)
        assert embedding.shape == (384,)
