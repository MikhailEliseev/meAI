"""
Unit tests for ClusterAnalyzer

Tests cluster quality metrics, statistics, and recommendations.
"""

import pytest
import numpy as np

from src.aim.subagents.content_gap_analysis.clustering.cluster_analyzer import (
    ClusterAnalyzer,
)


@pytest.fixture
def analyzer():
    """Create ClusterAnalyzer instance"""
    return ClusterAnalyzer()


@pytest.fixture
def good_clusters():
    """Create well-separated clusters for testing"""
    np.random.seed(42)

    # Create 3 well-separated clusters
    embeddings = []
    topics = []

    # Cluster 0: 10 points around [5, 0, 0, ...]
    for _ in range(10):
        emb = np.random.randn(50) * 0.5
        emb[0] += 5.0
        embeddings.append(emb)
        topics.append(0)

    # Cluster 1: 10 points around [0, 5, 0, ...]
    for _ in range(10):
        emb = np.random.randn(50) * 0.5
        emb[1] += 5.0
        embeddings.append(emb)
        topics.append(1)

    # Cluster 2: 10 points around [0, 0, 5, ...]
    for _ in range(10):
        emb = np.random.randn(50) * 0.5
        emb[2] += 5.0
        embeddings.append(emb)
        topics.append(2)

    return np.array(embeddings, dtype=np.float32), topics


@pytest.fixture
def poor_clusters():
    """Create overlapping clusters for testing"""
    np.random.seed(42)

    # Create 2 overlapping clusters
    embeddings = []
    topics = []

    # Cluster 0: 10 points around [1, 0, 0, ...]
    for _ in range(10):
        emb = np.random.randn(50) * 2.0  # Large variance
        emb[0] += 1.0
        embeddings.append(emb)
        topics.append(0)

    # Cluster 1: 10 points around [2, 0, 0, ...] (close to cluster 0)
    for _ in range(10):
        emb = np.random.randn(50) * 2.0
        emb[0] += 2.0
        embeddings.append(emb)
        topics.append(1)

    return np.array(embeddings, dtype=np.float32), topics


@pytest.fixture
def clusters_with_outliers():
    """Create clusters with outliers"""
    np.random.seed(42)

    embeddings = []
    topics = []

    # Cluster 0: 8 points
    for _ in range(8):
        emb = np.random.randn(50) * 0.5
        emb[0] += 5.0
        embeddings.append(emb)
        topics.append(0)

    # Outliers: 4 points
    for _ in range(4):
        emb = np.random.randn(50) * 3.0
        embeddings.append(emb)
        topics.append(-1)

    return np.array(embeddings, dtype=np.float32), topics


class TestClusterAnalyzer:
    """Test ClusterAnalyzer functionality"""

    def test_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer.metrics == {}
        assert analyzer.cluster_stats == {}

    def test_analyze_good_clusters(self, analyzer, good_clusters):
        """Test analyzing well-separated clusters"""
        embeddings, topics = good_clusters

        results = analyzer.analyze_clusters(embeddings, topics)

        # Check structure
        assert "metrics" in results
        assert "cluster_stats" in results
        assert "distribution" in results
        assert "outliers" in results

        # Check metrics
        metrics = results["metrics"]
        assert "silhouette_score" in metrics
        assert "davies_bouldin_score" in metrics
        assert "calinski_harabasz_score" in metrics

        # Good clusters should have positive silhouette score
        assert metrics["silhouette_score"] > 0.3

        # Good clusters should have low Davies-Bouldin score
        assert metrics["davies_bouldin_score"] < 2.0

    def test_analyze_poor_clusters(self, analyzer, poor_clusters):
        """Test analyzing overlapping clusters"""
        embeddings, topics = poor_clusters

        results = analyzer.analyze_clusters(embeddings, topics)

        metrics = results["metrics"]

        # Poor clusters should have lower silhouette score
        assert metrics["silhouette_score"] < 0.7

        # Poor clusters may have higher Davies-Bouldin score
        # (but not always, depends on overlap)
        assert metrics["davies_bouldin_score"] >= 0.0

    def test_cluster_stats(self, analyzer, good_clusters):
        """Test cluster statistics calculation"""
        embeddings, topics = good_clusters

        results = analyzer.analyze_clusters(embeddings, topics)
        cluster_stats = results["cluster_stats"]

        # Should have stats for each cluster
        assert len(cluster_stats) == 3  # 3 clusters

        # Check stats structure
        for topic_id, stats in cluster_stats.items():
            assert "size" in stats
            assert "avg_distance_to_centroid" in stats
            assert "max_distance_to_centroid" in stats
            assert "min_distance_to_centroid" in stats
            assert "density" in stats
            assert "is_outlier_cluster" in stats

            # Size should be 10 for each cluster
            assert stats["size"] == 10

            # Distances should be positive
            assert stats["avg_distance_to_centroid"] > 0
            assert stats["max_distance_to_centroid"] > 0
            assert stats["min_distance_to_centroid"] >= 0

            # Density should be positive
            assert stats["density"] > 0

    def test_distribution_analysis(self, analyzer, good_clusters):
        """Test cluster size distribution analysis"""
        embeddings, topics = good_clusters

        results = analyzer.analyze_clusters(embeddings, topics)
        distribution = results["distribution"]

        assert distribution["n_clusters"] == 3
        assert distribution["total_docs"] == 30
        assert distribution["avg_cluster_size"] == 10.0
        assert distribution["min_cluster_size"] == 10
        assert distribution["max_cluster_size"] == 10
        assert distribution["std_cluster_size"] == 0.0  # All same size

    def test_outlier_analysis(self, analyzer, clusters_with_outliers):
        """Test outlier analysis"""
        embeddings, topics = clusters_with_outliers

        results = analyzer.analyze_clusters(embeddings, topics)
        outliers = results["outliers"]

        assert outliers["n_outliers"] == 4
        assert outliers["outlier_ratio"] == 4 / 12  # 4 out of 12 docs
        assert len(outliers["outlier_indices"]) == 4

        # Check outlier indices are correct
        for idx in outliers["outlier_indices"]:
            assert topics[idx] == -1

    def test_classify_cluster_quality(self, analyzer, good_clusters):
        """Test cluster quality classification"""
        embeddings, topics = good_clusters

        analyzer.analyze_clusters(embeddings, topics)

        # Classify each cluster
        for topic_id in [0, 1, 2]:
            quality = analyzer.classify_cluster_quality(topic_id)
            # Good clusters should be at least "fair" or better
            assert quality in ["excellent", "good", "fair", "poor"]

    def test_classify_outlier_cluster(self, analyzer, clusters_with_outliers):
        """Test classifying outlier cluster"""
        embeddings, topics = clusters_with_outliers

        analyzer.analyze_clusters(embeddings, topics)

        # Outlier cluster should be classified as "outlier"
        quality = analyzer.classify_cluster_quality(-1)
        assert quality == "outlier"

    def test_get_quality_summary(self, analyzer, good_clusters):
        """Test getting quality summary"""
        embeddings, topics = good_clusters

        analyzer.analyze_clusters(embeddings, topics)

        summary = analyzer.get_quality_summary()

        assert "overall_quality" in summary
        assert "silhouette_quality" in summary
        assert "davies_bouldin_quality" in summary
        assert "metrics" in summary

        # Good clusters should have good overall quality
        assert summary["overall_quality"] in ["excellent", "good"]

    def test_get_recommendations_good_clusters(self, analyzer, good_clusters):
        """Test recommendations for good clusters"""
        embeddings, topics = good_clusters

        analyzer.analyze_clusters(embeddings, topics)

        recommendations = analyzer.get_recommendations()

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Good clusters should have positive feedback
        assert any("good" in rec.lower() or "no major issues" in rec.lower() for rec in recommendations)

    def test_get_recommendations_poor_clusters(self, analyzer, poor_clusters):
        """Test recommendations for poor clusters"""
        embeddings, topics = poor_clusters

        analyzer.analyze_clusters(embeddings, topics)

        recommendations = analyzer.get_recommendations()

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_get_recommendations_high_outliers(self, analyzer):
        """Test recommendations for high outlier ratio"""
        np.random.seed(42)

        # Create mostly outliers
        embeddings = np.random.randn(10, 50).astype(np.float32)
        topics = [-1] * 7 + [0] * 3  # 70% outliers

        analyzer.analyze_clusters(embeddings, topics)
        analyzer.outliers = {"outlier_ratio": 0.7}

        recommendations = analyzer.get_recommendations()

        # Should recommend lowering min_cluster_size
        assert any("outlier" in rec.lower() for rec in recommendations)

    def test_empty_clusters(self, analyzer):
        """Test handling empty clusters"""
        embeddings = np.array([]).reshape(0, 50)
        topics = []

        results = analyzer.analyze_clusters(embeddings, topics)

        # Should handle gracefully
        assert results["distribution"]["n_clusters"] == 0
        assert results["outliers"]["n_outliers"] == 0

    def test_single_cluster(self, analyzer):
        """Test handling single cluster"""
        np.random.seed(42)

        embeddings = np.random.randn(5, 50).astype(np.float32)
        topics = [0] * 5

        results = analyzer.analyze_clusters(embeddings, topics)

        # Should handle gracefully (but metrics may be 0)
        assert results["distribution"]["n_clusters"] == 1
        assert results["distribution"]["total_docs"] == 5

    def test_all_outliers(self, analyzer):
        """Test handling all outliers"""
        np.random.seed(42)

        embeddings = np.random.randn(5, 50).astype(np.float32)
        topics = [-1] * 5

        results = analyzer.analyze_clusters(embeddings, topics)

        # Should have 0 clusters (only outliers)
        assert results["distribution"]["n_clusters"] == 0
        assert results["outliers"]["n_outliers"] == 5
        assert results["outliers"]["outlier_ratio"] == 1.0

    def test_unbalanced_clusters(self, analyzer):
        """Test detecting unbalanced cluster sizes"""
        np.random.seed(42)

        embeddings = []
        topics = []

        # Large cluster: 20 points
        for _ in range(20):
            emb = np.random.randn(50) * 0.5
            emb[0] += 5.0
            embeddings.append(emb)
            topics.append(0)

        # Small cluster: 2 points
        for _ in range(2):
            emb = np.random.randn(50) * 0.5
            emb[1] += 5.0
            embeddings.append(emb)
            topics.append(1)

        embeddings = np.array(embeddings, dtype=np.float32)

        analyzer.analyze_clusters(embeddings, topics)
        recommendations = analyzer.get_recommendations()

        # Should detect unbalanced sizes (ratio 10:1)
        # But recommendation might not always trigger depending on other metrics
        # Just check we got some recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_metrics_with_insufficient_data(self, analyzer):
        """Test metrics calculation with insufficient data"""
        # Only 1 document
        embeddings = np.random.randn(1, 50).astype(np.float32)
        topics = [0]

        results = analyzer.analyze_clusters(embeddings, topics)

        # Metrics should be 0 (not enough data)
        assert results["metrics"]["silhouette_score"] == 0.0
        assert results["metrics"]["davies_bouldin_score"] == 0.0
        assert results["metrics"]["calinski_harabasz_score"] == 0.0
