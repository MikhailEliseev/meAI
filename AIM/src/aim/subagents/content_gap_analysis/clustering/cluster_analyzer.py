"""
Cluster Analyzer

Analyzes quality and characteristics of topic clusters.
Provides metrics for cluster evaluation and optimization.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
from collections import Counter


class ClusterAnalyzer:
    """Analyze quality and characteristics of topic clusters

    Provides metrics:
    - Silhouette score (cluster cohesion and separation)
    - Davies-Bouldin index (cluster similarity)
    - Calinski-Harabasz score (cluster variance ratio)
    - Cluster size distribution
    - Outlier detection
    - Topic coherence
    """

    def __init__(self):
        """Initialize cluster analyzer"""
        self.metrics: Dict[str, float] = {}
        self.cluster_stats: Dict[int, Dict[str, Any]] = {}

    def analyze_clusters(
        self,
        embeddings: np.ndarray,
        topics: List[int],
        texts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze cluster quality and characteristics

        Args:
            embeddings: Document embeddings of shape (n_docs, embedding_dim)
            topics: Topic assignments for each document
            texts: Optional document texts for coherence analysis

        Returns:
            Dictionary with analysis results:
            - metrics: Quality metrics (silhouette, davies_bouldin, etc.)
            - cluster_stats: Per-cluster statistics
            - distribution: Cluster size distribution
            - outliers: Outlier analysis
        """
        # Calculate quality metrics
        self.metrics = self._calculate_quality_metrics(embeddings, topics)

        # Calculate cluster statistics
        self.cluster_stats = self._calculate_cluster_stats(
            embeddings, topics, texts
        )

        # Analyze distribution
        distribution = self._analyze_distribution(topics)

        # Analyze outliers
        outliers = self._analyze_outliers(topics)

        return {
            "metrics": self.metrics,
            "cluster_stats": self.cluster_stats,
            "distribution": distribution,
            "outliers": outliers,
        }

    def _calculate_quality_metrics(
        self,
        embeddings: np.ndarray,
        topics: List[int],
    ) -> Dict[str, float]:
        """Calculate cluster quality metrics

        Args:
            embeddings: Document embeddings
            topics: Topic assignments

        Returns:
            Dictionary with quality metrics
        """
        metrics = {}

        # Filter out outliers (topic = -1) for metrics
        valid_mask = np.array(topics) != -1
        valid_embeddings = embeddings[valid_mask]
        valid_topics = np.array(topics)[valid_mask]

        if len(valid_topics) < 2 or len(set(valid_topics)) < 2:
            # Not enough data for metrics
            return {
                "silhouette_score": 0.0,
                "davies_bouldin_score": 0.0,
                "calinski_harabasz_score": 0.0,
            }

        # Silhouette score (higher is better, range: -1 to 1)
        # Measures how similar documents are to their own cluster vs other clusters
        try:
            metrics["silhouette_score"] = float(
                silhouette_score(valid_embeddings, valid_topics)
            )
        except Exception:
            metrics["silhouette_score"] = 0.0

        # Davies-Bouldin index (lower is better, range: 0 to inf)
        # Measures average similarity between each cluster and its most similar cluster
        try:
            metrics["davies_bouldin_score"] = float(
                davies_bouldin_score(valid_embeddings, valid_topics)
            )
        except Exception:
            metrics["davies_bouldin_score"] = 0.0

        # Calinski-Harabasz score (higher is better, range: 0 to inf)
        # Ratio of between-cluster to within-cluster variance
        try:
            metrics["calinski_harabasz_score"] = float(
                calinski_harabasz_score(valid_embeddings, valid_topics)
            )
        except Exception:
            metrics["calinski_harabasz_score"] = 0.0

        return metrics

    def _calculate_cluster_stats(
        self,
        embeddings: np.ndarray,
        topics: List[int],
        texts: Optional[List[str]] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """Calculate per-cluster statistics

        Args:
            embeddings: Document embeddings
            topics: Topic assignments
            texts: Optional document texts

        Returns:
            Dictionary mapping topic_id -> statistics
        """
        cluster_stats = {}

        unique_topics = set(topics)

        for topic_id in unique_topics:
            # Get documents in this cluster
            mask = np.array(topics) == topic_id
            cluster_embeddings = embeddings[mask]
            cluster_size = int(mask.sum())

            # Calculate centroid
            centroid = cluster_embeddings.mean(axis=0)

            # Calculate intra-cluster distances
            distances = np.linalg.norm(
                cluster_embeddings - centroid, axis=1
            )
            avg_distance = float(distances.mean())
            max_distance = float(distances.max())
            min_distance = float(distances.min())

            # Calculate density (inverse of average distance)
            density = 1.0 / (avg_distance + 1e-10)

            cluster_stats[topic_id] = {
                "size": cluster_size,
                "avg_distance_to_centroid": avg_distance,
                "max_distance_to_centroid": max_distance,
                "min_distance_to_centroid": min_distance,
                "density": density,
                "is_outlier_cluster": topic_id == -1,
            }

        return cluster_stats

    def _analyze_distribution(self, topics: List[int]) -> Dict[str, Any]:
        """Analyze cluster size distribution

        Args:
            topics: Topic assignments

        Returns:
            Dictionary with distribution statistics
        """
        # Count topics
        topic_counts = Counter(topics)

        # Remove outliers from distribution analysis
        topic_counts_no_outliers = {
            k: v for k, v in topic_counts.items() if k != -1
        }

        if not topic_counts_no_outliers:
            return {
                "n_clusters": 0,
                "total_docs": len(topics),
                "avg_cluster_size": 0.0,
                "min_cluster_size": 0,
                "max_cluster_size": 0,
                "std_cluster_size": 0.0,
            }

        sizes = list(topic_counts_no_outliers.values())

        return {
            "n_clusters": len(topic_counts_no_outliers),
            "total_docs": len(topics),
            "avg_cluster_size": float(np.mean(sizes)),
            "min_cluster_size": int(np.min(sizes)),
            "max_cluster_size": int(np.max(sizes)),
            "std_cluster_size": float(np.std(sizes)),
            "cluster_sizes": dict(topic_counts_no_outliers),
        }

    def _analyze_outliers(self, topics: List[int]) -> Dict[str, Any]:
        """Analyze outlier documents (topic = -1)

        Args:
            topics: Topic assignments

        Returns:
            Dictionary with outlier statistics
        """
        n_outliers = topics.count(-1)
        n_total = len(topics)
        outlier_ratio = n_outliers / n_total if n_total > 0 else 0.0

        outlier_indices = [i for i, t in enumerate(topics) if t == -1]

        return {
            "n_outliers": n_outliers,
            "outlier_ratio": outlier_ratio,
            "outlier_indices": outlier_indices,
        }

    def classify_cluster_quality(
        self,
        topic_id: int,
    ) -> str:
        """Classify cluster quality based on statistics

        Args:
            topic_id: Topic ID to classify

        Returns:
            Quality tier: "excellent", "good", "fair", "poor"
        """
        if topic_id not in self.cluster_stats:
            return "unknown"

        stats = self.cluster_stats[topic_id]

        # Outlier cluster
        if stats["is_outlier_cluster"]:
            return "outlier"

        # Quality based on density and size
        density = stats["density"]
        size = stats["size"]

        if density > 2.0 and size >= 10:
            return "excellent"
        elif density > 1.0 and size >= 5:
            return "good"
        elif density > 0.5 and size >= 3:
            return "fair"
        else:
            return "poor"

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get overall quality summary

        Returns:
            Dictionary with quality assessment
        """
        if not self.metrics:
            return {"overall_quality": "unknown"}

        # Interpret silhouette score
        silhouette = self.metrics.get("silhouette_score", 0.0)

        if silhouette > 0.7:
            silhouette_quality = "excellent"
        elif silhouette > 0.5:
            silhouette_quality = "good"
        elif silhouette > 0.25:
            silhouette_quality = "fair"
        else:
            silhouette_quality = "poor"

        # Interpret Davies-Bouldin score (lower is better)
        davies_bouldin = self.metrics.get("davies_bouldin_score", float("inf"))

        if davies_bouldin < 0.5:
            db_quality = "excellent"
        elif davies_bouldin < 1.0:
            db_quality = "good"
        elif davies_bouldin < 2.0:
            db_quality = "fair"
        else:
            db_quality = "poor"

        # Overall quality (average of interpretations)
        quality_scores = {
            "excellent": 4,
            "good": 3,
            "fair": 2,
            "poor": 1,
        }

        avg_score = (
            quality_scores[silhouette_quality] + quality_scores[db_quality]
        ) / 2

        if avg_score >= 3.5:
            overall_quality = "excellent"
        elif avg_score >= 2.5:
            overall_quality = "good"
        elif avg_score >= 1.5:
            overall_quality = "fair"
        else:
            overall_quality = "poor"

        return {
            "overall_quality": overall_quality,
            "silhouette_quality": silhouette_quality,
            "davies_bouldin_quality": db_quality,
            "metrics": self.metrics,
        }

    def get_recommendations(self) -> List[str]:
        """Get recommendations for improving clustering

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not self.metrics:
            return ["Run analyze_clusters first"]

        # Check silhouette score
        silhouette = self.metrics.get("silhouette_score", 0.0)
        if silhouette < 0.25:
            recommendations.append(
                "Low silhouette score: Consider increasing min_cluster_size or adjusting UMAP parameters"
            )

        # Check Davies-Bouldin score
        davies_bouldin = self.metrics.get("davies_bouldin_score", 0.0)
        if davies_bouldin > 2.0:
            recommendations.append(
                "High Davies-Bouldin score: Clusters may be too similar. Consider reducing number of topics."
            )

        # Check outlier ratio
        if hasattr(self, "outliers"):
            outlier_ratio = self.outliers.get("outlier_ratio", 0.0)
            if outlier_ratio > 0.3:
                recommendations.append(
                    f"High outlier ratio ({outlier_ratio:.1%}): Consider lowering min_cluster_size"
                )

        # Check cluster size distribution
        if self.cluster_stats:
            sizes = [s["size"] for s in self.cluster_stats.values() if not s["is_outlier_cluster"]]
            if sizes and max(sizes) / min(sizes) > 10:
                recommendations.append(
                    "Unbalanced cluster sizes: Some clusters are much larger than others"
                )

        if not recommendations:
            recommendations.append("Clustering quality is good. No major issues detected.")

        return recommendations
