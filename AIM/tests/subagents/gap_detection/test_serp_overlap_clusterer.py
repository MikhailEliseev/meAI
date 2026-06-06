"""
Tests for SERP Overlap Clusterer.
"""

import pytest

from src.aim.subagents.gap_detection.serp_overlap_clusterer import (
    ClusteringConfig,
    KeywordSERPData,
    SERPOverlapClusterer,
    SERPResult,
)
from src.aim.subagents.schemas.content_gap import IntentType


@pytest.fixture
def clusterer():
    """Create clusterer with default config."""
    return SERPOverlapClusterer()


@pytest.fixture
def sample_serp_data():
    """Create sample SERP data for testing."""
    return [
        KeywordSERPData(
            keyword="dental implants cost",
            search_volume=1000,
            intent=IntentType.COMMERCIAL,
            serp_results=[
                SERPResult(keyword="dental implants cost", url="https://example.com/cost", position=1, title="Cost Guide"),
                SERPResult(keyword="dental implants cost", url="https://example.com/pricing", position=2, title="Pricing"),
                SERPResult(keyword="dental implants cost", url="https://example.com/fees", position=3, title="Fees"),
            ],
        ),
        KeywordSERPData(
            keyword="how much are dental implants",
            search_volume=800,
            intent=IntentType.COMMERCIAL,
            serp_results=[
                SERPResult(keyword="how much are dental implants", url="https://example.com/cost", position=1, title="Cost Guide"),
                SERPResult(keyword="how much are dental implants", url="https://example.com/pricing", position=2, title="Pricing"),
                SERPResult(keyword="how much are dental implants", url="https://example.com/guide", position=3, title="Guide"),
            ],
        ),
        KeywordSERPData(
            keyword="dental implant procedure",
            search_volume=500,
            intent=IntentType.INFORMATIONAL,
            serp_results=[
                SERPResult(keyword="dental implant procedure", url="https://example.com/procedure", position=1, title="Procedure"),
                SERPResult(keyword="dental implant procedure", url="https://example.com/steps", position=2, title="Steps"),
                SERPResult(keyword="dental implant procedure", url="https://example.com/process", position=3, title="Process"),
            ],
        ),
    ]


@pytest.mark.asyncio
async def test_cluster_keywords_basic(clusterer, sample_serp_data):
    """Test basic keyword clustering."""
    clusters = await clusterer.cluster_keywords(sample_serp_data)

    assert len(clusters) >= 1
    assert all(len(c.keywords) >= 2 for c in clusters)
    assert all(c.hub_keyword in c.keywords for c in clusters)


@pytest.mark.asyncio
async def test_cluster_keywords_empty_input(clusterer):
    """Test clustering with empty input."""
    with pytest.raises(ValueError, match="serp_data cannot be empty"):
        await clusterer.cluster_keywords([])


@pytest.mark.asyncio
async def test_cluster_keywords_high_overlap(clusterer):
    """Test clustering with high SERP overlap."""
    serp_data = [
        KeywordSERPData(
            keyword="kw1",
            search_volume=1000,
            serp_results=[
                SERPResult(keyword="kw1", url=f"https://example.com/{i}", position=i, title=f"Title {i}")
                for i in range(1, 11)
            ],
        ),
        KeywordSERPData(
            keyword="kw2",
            search_volume=800,
            serp_results=[
                SERPResult(keyword="kw2", url=f"https://example.com/{i}", position=i, title=f"Title {i}")
                for i in range(1, 11)  # Same URLs = 100% overlap
            ],
        ),
    ]

    clusters = await clusterer.cluster_keywords(serp_data)

    # Should form single cluster due to 100% overlap
    assert len(clusters) == 1
    assert set(clusters[0].keywords) == {"kw1", "kw2"}
    assert clusters[0].hub_keyword == "kw1"  # Higher volume


@pytest.mark.asyncio
async def test_cluster_keywords_no_overlap(clusterer):
    """Test clustering with no SERP overlap."""
    serp_data = [
        KeywordSERPData(
            keyword="kw1",
            search_volume=1000,
            serp_results=[
                SERPResult(keyword="kw1", url=f"https://site1.com/{i}", position=i, title=f"Title {i}")
                for i in range(1, 11)
            ],
        ),
        KeywordSERPData(
            keyword="kw2",
            search_volume=800,
            serp_results=[
                SERPResult(keyword="kw2", url=f"https://site2.com/{i}", position=i, title=f"Title {i}")
                for i in range(1, 11)  # Different URLs = 0% overlap
            ],
        ),
    ]

    clusters = await clusterer.cluster_keywords(serp_data)

    # Should form separate clusters (or no clusters if min_size=2)
    # With min_size=2, no clusters should be returned
    assert len(clusters) == 0


def test_calculate_jaccard_similarity(clusterer):
    """Test Jaccard similarity calculation."""
    set1 = {"a", "b", "c"}
    set2 = {"b", "c", "d"}

    similarity = clusterer._calculate_jaccard_similarity(set1, set2)

    # Intersection: {b, c} = 2
    # Union: {a, b, c, d} = 4
    # Jaccard: 2/4 = 0.5
    assert similarity == 0.5


def test_calculate_jaccard_similarity_empty(clusterer):
    """Test Jaccard similarity with empty sets."""
    assert clusterer._calculate_jaccard_similarity(set(), {"a"}) == 0.0
    assert clusterer._calculate_jaccard_similarity({"a"}, set()) == 0.0
    assert clusterer._calculate_jaccard_similarity(set(), set()) == 0.0


def test_calculate_jaccard_similarity_identical(clusterer):
    """Test Jaccard similarity with identical sets."""
    set1 = {"a", "b", "c"}
    similarity = clusterer._calculate_jaccard_similarity(set1, set1)
    assert similarity == 1.0


@pytest.mark.asyncio
async def test_cluster_quality_analysis(clusterer, sample_serp_data):
    """Test cluster quality analysis."""
    clusters = await clusterer.cluster_keywords(sample_serp_data)

    if clusters:
        quality = await clusterer.analyze_cluster_quality(clusters[0], sample_serp_data)

        assert "avg_serp_overlap" in quality
        assert "intent_consistency" in quality
        assert "hub_volume" in quality
        assert "cohesion_score" in quality
        assert 0.0 <= quality["avg_serp_overlap"] <= 1.0
        assert 0.0 <= quality["intent_consistency"] <= 1.0
        assert 0.0 <= quality["cohesion_score"] <= 1.0


@pytest.mark.asyncio
async def test_clustering_config_custom(sample_serp_data):
    """Test clustering with custom config."""
    config = ClusteringConfig(
        overlap_threshold=0.6,  # Higher threshold
        min_cluster_size=3,
        max_clusters=10,
    )
    clusterer = SERPOverlapClusterer(config)

    clusters = await clusterer.cluster_keywords(sample_serp_data)

    # With higher threshold, fewer clusters expected
    assert all(len(c.keywords) >= 3 for c in clusters)
    assert len(clusters) <= 10


@pytest.mark.asyncio
async def test_hub_keyword_selection(clusterer):
    """Test that hub keyword is highest volume in cluster."""
    serp_data = [
        KeywordSERPData(
            keyword="low volume",
            search_volume=100,
            serp_results=[
                SERPResult(keyword="low volume", url=f"https://example.com/{i}", position=i, title=f"Title {i}")
                for i in range(1, 11)
            ],
        ),
        KeywordSERPData(
            keyword="high volume",
            search_volume=1000,
            serp_results=[
                SERPResult(keyword="high volume", url=f"https://example.com/{i}", position=i, title=f"Title {i}")
                for i in range(1, 11)
            ],
        ),
    ]

    clusters = await clusterer.cluster_keywords(serp_data)

    if clusters:
        assert clusters[0].hub_keyword == "high volume"
        assert "low volume" in clusters[0].spoke_keywords
