"""
Topic Clusterer

Clusters content into semantic topics using BERTopic.
Combines UMAP dimensionality reduction, HDBSCAN clustering, and c-TF-IDF for topic extraction.
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer


class TopicClusterer:
    """Cluster content into semantic topics using BERTopic

    Uses BERTopic pipeline:
    1. UMAP for dimensionality reduction
    2. HDBSCAN for clustering
    3. c-TF-IDF for topic representation

    Supports hierarchical topic structure and dynamic topic modeling.
    """

    def __init__(
        self,
        min_cluster_size: int = 5,
        min_samples: int = 3,
        n_neighbors: int = 15,
        n_components: int = 5,
        random_state: int = 42,
        language: str = "english",
    ):
        """Initialize topic clusterer

        Args:
            min_cluster_size: Minimum cluster size for HDBSCAN
            min_samples: Minimum samples for HDBSCAN core points
            n_neighbors: Number of neighbors for UMAP
            n_components: Number of UMAP dimensions
            random_state: Random seed for reproducibility
            language: Language for stop words
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.n_neighbors = n_neighbors
        self.n_components = n_components
        self.random_state = random_state
        self.language = language

        # Initialize components
        self.umap_model = UMAP(
            n_neighbors=n_neighbors,
            n_components=n_components,
            min_dist=0.0,
            metric="cosine",
            random_state=random_state,
        )

        self.hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        self.vectorizer_model = CountVectorizer(
            stop_words=language,
            ngram_range=(1, 2),
            min_df=1,  # Changed from 2 to handle small datasets
        )

        # Initialize BERTopic
        self.topic_model = BERTopic(
            umap_model=self.umap_model,
            hdbscan_model=self.hdbscan_model,
            vectorizer_model=self.vectorizer_model,
            calculate_probabilities=True,
            verbose=False,
        )

        # Store results
        self.topics: Optional[List[int]] = None
        self.probabilities: Optional[np.ndarray] = None
        self.topic_info: Optional[Dict[int, Dict[str, Any]]] = None
        self.texts: Optional[List[str]] = None  # Store original texts for reduce_topics

    def fit_transform(
        self,
        texts: List[str],
        embeddings: np.ndarray,
    ) -> Tuple[List[int], np.ndarray]:
        """Fit topic model and transform texts to topics

        Args:
            texts: List of text documents
            embeddings: Pre-computed embeddings of shape (len(texts), embedding_dim)

        Returns:
            Tuple of (topics, probabilities)
            - topics: List of topic IDs for each document (-1 = outlier)
            - probabilities: Topic probability matrix of shape (len(texts), n_topics)
        """
        # Handle edge cases
        if len(texts) == 0:
            raise ValueError("Cannot fit on empty text list")

        # For very small datasets (< 10 texts), skip clustering
        # All texts will be in one cluster (topic 0)
        if len(texts) < 10:
            topics = [0] * len(texts)
            probabilities = np.ones((len(texts), 1))
            self.topics = topics
            self.probabilities = probabilities
            self.topic_info = {
                0: {
                    "topic_id": 0,
                    "name": "General Topic",
                    "count": len(texts),
                    "words": ["general"],
                }
            }
            self.texts = texts
            return topics, probabilities

        # Adjust n_neighbors for small datasets
        original_n_neighbors = self.umap_model.n_neighbors
        if len(texts) < self.n_neighbors:
            self.umap_model.n_neighbors = max(2, min(len(texts) - 1, 5))

        # Adjust n_components for small datasets
        original_n_components = self.umap_model.n_components
        if len(texts) <= self.n_components:
            self.umap_model.n_components = max(2, min(len(texts) - 1, 3))

        try:
            # Fit and transform
            topics, probabilities = self.topic_model.fit_transform(texts, embeddings)
        finally:
            # Restore original parameters
            self.umap_model.n_neighbors = original_n_neighbors
            self.umap_model.n_components = original_n_components

        # Store results
        self.topics = topics
        self.probabilities = probabilities
        self.texts = texts  # Store for reduce_topics

        # Extract topic info
        self._extract_topic_info()

        return topics, probabilities

    def transform(
        self,
        texts: List[str],
        embeddings: np.ndarray,
    ) -> Tuple[List[int], np.ndarray]:
        """Transform new texts to topics using fitted model

        Args:
            texts: List of text documents
            embeddings: Pre-computed embeddings

        Returns:
            Tuple of (topics, probabilities)
        """
        if self.topic_model is None:
            raise ValueError("Model not fitted. Call fit_transform first.")

        topics, probabilities = self.topic_model.transform(texts, embeddings)
        return topics, probabilities

    def get_topic_info(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific topic

        Args:
            topic_id: Topic ID

        Returns:
            Dictionary with topic information:
            - topic_id: Topic ID
            - count: Number of documents in topic
            - name: Topic name (top words)
            - words: List of (word, score) tuples
            - representative_docs: Sample documents from topic
        """
        if self.topic_info is None:
            return None

        return self.topic_info.get(topic_id)

    def get_all_topics(self) -> Dict[int, Dict[str, Any]]:
        """Get information about all topics

        Returns:
            Dictionary mapping topic_id -> topic_info
        """
        if self.topic_info is None:
            return {}

        return self.topic_info

    def get_topic_hierarchy(self) -> Optional[Dict[str, Any]]:
        """Get hierarchical topic structure

        Returns:
            Dictionary with hierarchical topic tree
        """
        if self.topic_model is None:
            return None

        # Get hierarchical topics
        hierarchical_topics = self.topic_model.hierarchical_topics(self.topics)

        return {
            "hierarchy": hierarchical_topics.to_dict(orient="records"),
            "n_levels": len(hierarchical_topics["Distance"].unique()),
        }

    def reduce_topics(self, n_topics: int) -> List[int]:
        """Reduce number of topics by merging similar ones

        Args:
            n_topics: Target number of topics

        Returns:
            New topic assignments
        """
        if self.topic_model is None or self.texts is None:
            raise ValueError("Model not fitted. Call fit_transform first.")

        # Reduce topics (needs original texts, not topic IDs)
        self.topic_model.reduce_topics(self.texts, n_topics)

        # Update topics
        self.topics = self.topic_model.topics_

        # Re-extract topic info
        self._extract_topic_info()

        return self.topics

    def get_representative_docs(
        self,
        topic_id: int,
        n_docs: int = 5,
    ) -> List[str]:
        """Get representative documents for a topic

        Args:
            topic_id: Topic ID
            n_docs: Number of documents to return

        Returns:
            List of representative document texts
        """
        if self.topic_model is None:
            return []

        # Get representative docs
        repr_docs = self.topic_model.get_representative_docs(topic_id)

        return repr_docs[:n_docs] if repr_docs else []

    def visualize_topics(self) -> Any:
        """Visualize topics in 2D space

        Returns:
            Plotly figure object
        """
        if self.topic_model is None:
            return None

        return self.topic_model.visualize_topics()

    def visualize_hierarchy(self) -> Any:
        """Visualize hierarchical topic structure

        Returns:
            Plotly figure object
        """
        if self.topic_model is None:
            return None

        return self.topic_model.visualize_hierarchy()

    def _extract_topic_info(self) -> None:
        """Extract and store topic information"""
        if self.topic_model is None:
            return

        self.topic_info = {}

        # Get topic info from BERTopic
        topic_info_df = self.topic_model.get_topic_info()

        for _, row in topic_info_df.iterrows():
            topic_id = row["Topic"]

            # Get topic words
            topic_words = self.topic_model.get_topic(topic_id)

            # Get representative docs
            repr_docs = self.get_representative_docs(topic_id, n_docs=3)

            self.topic_info[topic_id] = {
                "topic_id": topic_id,
                "count": row["Count"],
                "name": row["Name"],
                "words": topic_words if topic_words else [],
                "representative_docs": repr_docs,
            }

    def get_outliers(self) -> List[int]:
        """Get indices of outlier documents (topic = -1)

        Returns:
            List of document indices that are outliers
        """
        if self.topics is None:
            return []

        return [i for i, topic in enumerate(self.topics) if topic == -1]

    def get_topic_sizes(self) -> Dict[int, int]:
        """Get size of each topic

        Returns:
            Dictionary mapping topic_id -> count
        """
        if self.topics is None:
            return {}

        topic_sizes = {}
        for topic_id in set(self.topics):
            topic_sizes[topic_id] = self.topics.count(topic_id)

        return topic_sizes

    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration information

        Returns:
            Dictionary with model parameters
        """
        return {
            "min_cluster_size": self.min_cluster_size,
            "min_samples": self.min_samples,
            "n_neighbors": self.n_neighbors,
            "n_components": self.n_components,
            "random_state": self.random_state,
            "language": self.language,
            "n_topics": len(self.topic_info) if self.topic_info else 0,
            "n_outliers": len(self.get_outliers()),
        }
