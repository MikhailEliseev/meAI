"""
SERP Overlap Clusterer - Semantic topic clustering using SERP overlap methodology.

Implements the SERP overlap clustering approach:
1. Expand seed keywords via Keyword Research Agent
2. Fetch SERP results for each keyword (top 30 URLs)
3. Calculate pairwise SERP overlap (Jaccard similarity)
4. Cluster keywords by overlap threshold (>= 40% = same topic)
5. Build hub-and-spoke architecture from clusters

Based on: https://ahrefs.com/blog/topic-clusters/
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.aim.subagents.schemas.content_gap import (
    ContentCluster,
    IntentType,
)


class SERPResult(BaseModel):
    """Single SERP result for a keyword."""

    keyword: str = Field(..., description="Search keyword")
    url: str = Field(..., description="Ranking URL")
    position: int = Field(..., ge=1, le=100, description="SERP position (1-100)")
    title: str = Field(..., description="Page title")
    intent: IntentType = Field(default=IntentType.INFORMATIONAL, description="Search intent")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {v}")
        return v


class KeywordSERPData(BaseModel):
    """SERP data for a single keyword."""

    keyword: str = Field(..., description="Search keyword")
    serp_results: list[SERPResult] = Field(
        default_factory=list, description="Top 30 SERP results"
    )
    search_volume: int = Field(default=0, ge=0, description="Monthly search volume")
    intent: IntentType = Field(default=IntentType.INFORMATIONAL, description="Primary intent")

    @field_validator("serp_results")
    @classmethod
    def validate_serp_results(cls, v: list[SERPResult]) -> list[SERPResult]:
        """Validate SERP results count."""
        if len(v) > 100:
            raise ValueError(f"Too many SERP results: {len(v)} (max 100)")
        return v


@dataclass
class ClusteringConfig:
    """Configuration for SERP overlap clustering."""

    overlap_threshold: float = 0.4  # 40% overlap = same topic
    min_cluster_size: int = 2  # Min keywords per cluster
    max_clusters: int = 50  # Max clusters to return
    serp_depth: int = 30  # Top N URLs to compare


class SERPOverlapClusterer:
    """
    Clusters keywords by SERP overlap using Jaccard similarity.

    Methodology:
    1. For each keyword pair, calculate SERP overlap (Jaccard index)
    2. If overlap >= threshold (40%), keywords belong to same topic
    3. Build clusters using connected components algorithm
    4. Identify hub keywords (highest search volume in cluster)
    5. Return hub-and-spoke structure
    """

    def __init__(self, config: ClusteringConfig | None = None):
        """Initialize clusterer with config."""
        self.config = config or ClusteringConfig()

    async def cluster_keywords(
        self,
        serp_data: list[KeywordSERPData],
    ) -> list[ContentCluster]:
        """
        Cluster keywords by SERP overlap.

        Args:
            serp_data: SERP data for each keyword

        Returns:
            List of content clusters with hub-and-spoke structure

        Raises:
            ValueError: If serp_data is empty or invalid
        """
        if not serp_data:
            raise ValueError("serp_data cannot be empty")

        # Build overlap matrix
        overlap_matrix = self._build_overlap_matrix(serp_data)

        # Find connected components (clusters)
        clusters = self._find_clusters(overlap_matrix, serp_data)

        # Filter by min cluster size
        clusters = [c for c in clusters if len(c.keywords) >= self.config.min_cluster_size]

        # Limit to max clusters
        if len(clusters) > self.config.max_clusters:
            # Sort by total search volume, keep top N
            clusters.sort(key=lambda c: c.total_search_volume, reverse=True)
            clusters = clusters[: self.config.max_clusters]

        return clusters

    def _build_overlap_matrix(
        self, serp_data: list[KeywordSERPData]
    ) -> dict[tuple[str, str], float]:
        """
        Build pairwise SERP overlap matrix.

        Returns:
            Dict mapping (keyword1, keyword2) -> overlap_score (0.0-1.0)
        """
        overlap_matrix: dict[tuple[str, str], float] = {}

        # Build URL sets for each keyword
        keyword_urls: dict[str, set[str]] = {}
        for kw_data in serp_data:
            urls = {
                result.url
                for result in kw_data.serp_results[: self.config.serp_depth]
            }
            keyword_urls[kw_data.keyword] = urls

        # Calculate pairwise overlap
        keywords = list(keyword_urls.keys())
        for i, kw1 in enumerate(keywords):
            for kw2 in keywords[i + 1 :]:
                overlap = self._calculate_jaccard_similarity(
                    keyword_urls[kw1], keyword_urls[kw2]
                )
                overlap_matrix[(kw1, kw2)] = overlap
                overlap_matrix[(kw2, kw1)] = overlap  # Symmetric

        return overlap_matrix

    def _calculate_jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """
        Calculate Jaccard similarity between two URL sets.

        Jaccard = |intersection| / |union|

        Returns:
            Similarity score (0.0-1.0)
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _find_clusters(
        self,
        overlap_matrix: dict[tuple[str, str], float],
        serp_data: list[KeywordSERPData],
    ) -> list[ContentCluster]:
        """
        Find clusters using connected components algorithm.

        Algorithm:
        1. Build adjacency list (edges = overlap >= threshold)
        2. Find connected components via DFS
        3. For each component, identify hub keyword (highest volume)
        4. Build ContentCluster with hub and spokes

        Returns:
            List of ContentCluster objects
        """
        # Build adjacency list
        adjacency: dict[str, set[str]] = defaultdict(set)
        for (kw1, kw2), overlap in overlap_matrix.items():
            if overlap >= self.config.overlap_threshold:
                adjacency[kw1].add(kw2)

        # Find connected components via DFS
        visited: set[str] = set()
        components: list[set[str]] = []

        def dfs(keyword: str, component: set[str]) -> None:
            """Depth-first search to find connected component."""
            visited.add(keyword)
            component.add(keyword)
            for neighbor in adjacency.get(keyword, set()):
                if neighbor not in visited:
                    dfs(neighbor, component)

        # Run DFS from each unvisited keyword
        for kw_data in serp_data:
            if kw_data.keyword not in visited:
                component: set[str] = set()
                dfs(kw_data.keyword, component)
                if component:
                    components.append(component)

        # Build ContentCluster for each component
        clusters: list[ContentCluster] = []
        kw_data_map = {kw.keyword: kw for kw in serp_data}

        for component in components:
            # Find hub keyword (highest search volume)
            component_data = [kw_data_map[kw] for kw in component if kw in kw_data_map]
            if not component_data:
                continue

            hub_data = max(component_data, key=lambda x: x.search_volume)
            spoke_keywords = [kw for kw in component if kw != hub_data.keyword]

            # Calculate total search volume
            total_volume = sum(kw.search_volume for kw in component_data)

            # Determine primary intent (most common in cluster)
            intent_counts: dict[IntentType, int] = defaultdict(int)
            for kw in component_data:
                intent_counts[kw.intent] += 1
            primary_intent = max(intent_counts.items(), key=lambda x: x[1])[0]

            cluster = ContentCluster(
                hub_keyword=hub_data.keyword,
                spoke_keywords=spoke_keywords,
                total_search_volume=total_volume,
                primary_intent=primary_intent,
                keywords=list(component),
            )
            clusters.append(cluster)

        return clusters

    async def analyze_cluster_quality(
        self, cluster: ContentCluster, serp_data: list[KeywordSERPData]
    ) -> dict[str, Any]:
        """
        Analyze cluster quality metrics.

        Metrics:
        - Avg SERP overlap within cluster
        - Intent consistency (% keywords with same intent)
        - Volume distribution (hub vs spokes)
        - Cluster cohesion score (0.0-1.0)

        Returns:
            Dict with quality metrics
        """
        kw_data_map = {kw.keyword: kw for kw in serp_data}

        # Calculate avg SERP overlap
        overlaps: list[float] = []
        for i, kw1 in enumerate(cluster.keywords):
            for kw2 in cluster.keywords[i + 1 :]:
                if kw1 in kw_data_map and kw2 in kw_data_map:
                    urls1 = {r.url for r in kw_data_map[kw1].serp_results}
                    urls2 = {r.url for r in kw_data_map[kw2].serp_results}
                    overlap = self._calculate_jaccard_similarity(urls1, urls2)
                    overlaps.append(overlap)

        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0

        # Calculate intent consistency
        cluster_data = [kw_data_map[kw] for kw in cluster.keywords if kw in kw_data_map]
        if cluster_data:
            primary_intent_count = sum(
                1 for kw in cluster_data if kw.intent == cluster.primary_intent
            )
            intent_consistency = primary_intent_count / len(cluster_data)
        else:
            intent_consistency = 0.0

        # Calculate volume distribution
        hub_volume = kw_data_map.get(cluster.hub_keyword, KeywordSERPData(keyword="", search_volume=0)).search_volume
        spoke_volumes = [
            kw_data_map[kw].search_volume
            for kw in cluster.spoke_keywords
            if kw in kw_data_map
        ]
        avg_spoke_volume = sum(spoke_volumes) / len(spoke_volumes) if spoke_volumes else 0

        # Calculate cohesion score (weighted avg of metrics)
        cohesion_score = (
            avg_overlap * 0.5 + intent_consistency * 0.3 + min(1.0, avg_overlap / 0.4) * 0.2
        )

        return {
            "avg_serp_overlap": round(avg_overlap, 3),
            "intent_consistency": round(intent_consistency, 3),
            "hub_volume": hub_volume,
            "avg_spoke_volume": round(avg_spoke_volume, 1),
            "cohesion_score": round(cohesion_score, 3),
            "cluster_size": len(cluster.keywords),
        }
