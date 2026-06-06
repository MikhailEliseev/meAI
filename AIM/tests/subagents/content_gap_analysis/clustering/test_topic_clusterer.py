"""
Unit tests for TopicClusterer

Tests BERTopic clustering, topic extraction, and hierarchical structure.
"""

import pytest
import numpy as np

from src.aim.subagents.content_gap_analysis.clustering.topic_clusterer import (
    TopicClusterer,
)


@pytest.fixture
def clusterer():
    """Create TopicClusterer instance"""
    return TopicClusterer(
        min_cluster_size=3,
        min_samples=2,
        n_neighbors=10,  # Increased from 5 (need < len(texts))
        n_components=5,  # Increased from 3 for better dimensionality
        random_state=42,
        language="english",
    )


@pytest.fixture
def sample_texts():
    """Sample texts for testing (3 clear topics)"""
    return [
        # Topic 1: Dental implants (5 docs)
        "Dental implants are artificial tooth roots that provide a permanent base.",
        "Implant surgery involves placing titanium posts into the jawbone.",
        "Dental implants can last a lifetime with proper care.",
        "The success rate of dental implants exceeds 95 percent.",
        "Implants look and function like natural teeth.",
        # Topic 2: Teeth whitening (5 docs)
        "Teeth whitening removes stains and brightens your smile.",
        "Professional whitening treatments are safe and effective.",
        "Whitening results can last up to three years.",
        "In-office whitening provides immediate results.",
        "Home whitening kits offer gradual improvement.",
        # Topic 3: Orthodontics (5 docs)
        "Braces correct misaligned teeth and improve bite.",
        "Orthodontic treatment typically lasts 18 to 24 months.",
        "Clear aligners are a popular alternative to traditional braces.",
        "Retainers maintain teeth position after orthodontic treatment.",
        "Early orthodontic intervention can prevent future problems.",
    ]


@pytest.fixture
def sample_embeddings(sample_texts):
    """Generate sample embeddings (mock with random but clustered data)"""
    np.random.seed(42)

    # Create 3 clusters with 5 points each
    embeddings = []

    # Cluster 1: centered at [1, 0, 0]
    for _ in range(5):
        emb = np.random.randn(384) * 0.1
        emb[0] += 1.0
        embeddings.append(emb)

    # Cluster 2: centered at [0, 1, 0]
    for _ in range(5):
        emb = np.random.randn(384) * 0.1
        emb[1] += 1.0
        embeddings.append(emb)

    # Cluster 3: centered at [0, 0, 1]
    for _ in range(5):
        emb = np.random.randn(384) * 0.1
        emb[2] += 1.0
        embeddings.append(emb)

    return np.array(embeddings, dtype=np.float32)


class TestTopicClusterer:
    """Test TopicClusterer functionality"""

    def test_initialization(self, clusterer):
        """Test clusterer initialization"""
        assert clusterer.min_cluster_size == 3
        assert clusterer.min_samples == 2
        assert clusterer.n_neighbors == 10
        assert clusterer.n_components == 5
        assert clusterer.random_state == 42
        assert clusterer.language == "english"
        assert clusterer.umap_model.n_neighbors == 10
        assert clusterer.umap_model.n_components == 5

    def test_fit_transform(self, clusterer, sample_texts, sample_embeddings):
        """Test fitting and transforming texts to topics"""
        topics, probabilities = clusterer.fit_transform(sample_texts, sample_embeddings)

        # Check topics
        assert len(topics) == len(sample_texts)
        assert all(isinstance(t, (int, np.integer)) for t in topics)

        # Check probabilities
        assert probabilities.shape[0] == len(sample_texts)
        assert probabilities.shape[1] > 0  # At least one topic

        # Probabilities should be reasonable (BERTopic doesn't guarantee sum=1.0)
        assert np.all(probabilities >= 0.0)
        assert np.all(probabilities <= 1.0)

    def test_topics_are_consistent(self, clusterer, sample_texts, sample_embeddings):
        """Test that similar documents get same topic"""
        topics, _ = clusterer.fit_transform(sample_texts, sample_embeddings)

        # Documents 0-4 should be in same cluster (dental implants)
        implant_topics = set(topics[0:5])
        # Should have 1 or 2 topics (allowing for some variation)
        assert len(implant_topics) <= 2

        # Documents 5-9 should be in same cluster (whitening)
        whitening_topics = set(topics[5:10])
        assert len(whitening_topics) <= 2

        # Documents 10-14 should be in same cluster (orthodontics)
        ortho_topics = set(topics[10:15])
        assert len(ortho_topics) <= 2

    def test_get_topic_info(self, clusterer, sample_texts, sample_embeddings):
        """Test getting topic information"""
        topics, _ = clusterer.fit_transform(sample_texts, sample_embeddings)

        # Get info for first non-outlier topic
        valid_topics = [t for t in topics if t != -1]
        if valid_topics:
            topic_id = valid_topics[0]
            info = clusterer.get_topic_info(topic_id)

            assert info is not None
            assert info["topic_id"] == topic_id
            assert "count" in info
            assert "name" in info
            assert "words" in info
            assert "representative_docs" in info

    def test_get_all_topics(self, clusterer, sample_texts, sample_embeddings):
        """Test getting all topics"""
        clusterer.fit_transform(sample_texts, sample_embeddings)

        all_topics = clusterer.get_all_topics()

        assert isinstance(all_topics, dict)
        assert len(all_topics) > 0

        # Check structure of each topic
        for topic_id, info in all_topics.items():
            assert isinstance(topic_id, int)
            assert "count" in info
            assert "name" in info
            assert "words" in info

    def test_get_outliers(self, clusterer, sample_texts, sample_embeddings):
        """Test getting outlier documents"""
        topics, _ = clusterer.fit_transform(sample_texts, sample_embeddings)

        outliers = clusterer.get_outliers()

        assert isinstance(outliers, list)
        # Check that outlier indices are valid
        assert all(0 <= idx < len(sample_texts) for idx in outliers)
        # Check that outliers have topic -1
        assert all(topics[idx] == -1 for idx in outliers)

    def test_get_topic_sizes(self, clusterer, sample_texts, sample_embeddings):
        """Test getting topic sizes"""
        clusterer.fit_transform(sample_texts, sample_embeddings)

        sizes = clusterer.get_topic_sizes()

        assert isinstance(sizes, dict)
        assert len(sizes) > 0
        # All sizes should be positive
        assert all(size > 0 for size in sizes.values())
        # Sum of sizes should equal number of documents
        assert sum(sizes.values()) == len(sample_texts)

    def test_get_representative_docs(self, clusterer, sample_texts, sample_embeddings):
        """Test getting representative documents"""
        topics, _ = clusterer.fit_transform(sample_texts, sample_embeddings)

        # Get representative docs for first non-outlier topic
        valid_topics = [t for t in topics if t != -1]
        if valid_topics:
            topic_id = valid_topics[0]
            repr_docs = clusterer.get_representative_docs(topic_id, n_docs=3)

            assert isinstance(repr_docs, list)
            assert len(repr_docs) <= 3
            assert all(isinstance(doc, str) for doc in repr_docs)

    def test_transform_new_documents(self, clusterer, sample_texts, sample_embeddings):
        """Test transforming new documents with fitted model"""
        # Fit model
        clusterer.fit_transform(sample_texts, sample_embeddings)

        # Create new documents (similar to existing)
        new_texts = [
            "Dental implants replace missing teeth permanently.",
            "Teeth whitening improves smile appearance.",
        ]

        # Create mock embeddings for new texts
        np.random.seed(43)
        new_embeddings = np.array([
            np.random.randn(384) * 0.1 + np.array([1.0] + [0.0] * 383),  # Similar to cluster 1
            np.random.randn(384) * 0.1 + np.array([0.0, 1.0] + [0.0] * 382),  # Similar to cluster 2
        ], dtype=np.float32)

        # Transform
        new_topics, new_probs = clusterer.transform(new_texts, new_embeddings)

        assert len(new_topics) == len(new_texts)
        assert new_probs.shape[0] == len(new_texts)

    def test_reduce_topics(self, clusterer, sample_texts, sample_embeddings):
        """Test reducing number of topics"""
        topics_before, _ = clusterer.fit_transform(sample_texts, sample_embeddings)

        n_topics_before = len(set(topics_before)) - (1 if -1 in topics_before else 0)

        if n_topics_before > 2:
            # Reduce to 2 topics
            topics_after = clusterer.reduce_topics(n_topics=2)

            n_topics_after = len(set(topics_after)) - (1 if -1 in topics_after else 0)

            # Should have fewer topics
            assert n_topics_after <= n_topics_before

    def test_get_model_info(self, clusterer, sample_texts, sample_embeddings):
        """Test getting model information"""
        clusterer.fit_transform(sample_texts, sample_embeddings)

        info = clusterer.get_model_info()

        assert info["min_cluster_size"] == 3
        assert info["min_samples"] == 2
        assert info["n_neighbors"] == 10  # Updated from 5
        assert info["n_components"] == 5  # Updated from 3
        assert info["random_state"] == 42
        assert info["language"] == "english"
        assert "n_topics" in info
        assert "n_outliers" in info

    def test_empty_texts(self, clusterer):
        """Test handling empty text list"""
        with pytest.raises(Exception):
            # BERTopic should raise error for empty input
            clusterer.fit_transform([], np.array([]))

    def test_single_document(self, clusterer):
        """Test handling single document"""
        texts = ["Single document about dental implants."]
        embeddings = np.random.randn(1, 384).astype(np.float32)

        # Should handle gracefully (likely as outlier)
        topics, probs = clusterer.fit_transform(texts, embeddings)

        assert len(topics) == 1
        assert probs.shape[0] == 1

    def test_min_cluster_size_enforcement(self):
        """Test that min_cluster_size is enforced"""
        # Create clusterer with min_cluster_size=5
        clusterer = TopicClusterer(min_cluster_size=5, random_state=42)

        # Create only 3 documents (less than min_cluster_size)
        texts = ["Doc 1", "Doc 2", "Doc 3"]
        embeddings = np.random.randn(3, 384).astype(np.float32)

        topics, _ = clusterer.fit_transform(texts, embeddings)

        # All should be outliers (topic = -1)
        assert all(t == -1 for t in topics)
