"""Tests for GapDetector."""

import pytest

from AIM.src.aim.subagents.gap_detection.gap_detector import GapDetector
from AIM.src.aim.subagents.schemas.content_gap import GapSeverity, GapType


@pytest.fixture
def gap_detector():
    """Create gap detector instance."""
    return GapDetector(min_content_quality=0.6)


@pytest.fixture
def client_pages():
    """Sample client pages."""
    return [
        {
            "url": "https://client.com/dental-implants",
            "title": "Dental Implants",
            "cluster_id": 0,
            "eeat_score": 0.7,
            "word_count": 1000,
            "keywords": ["dental implants", "tooth replacement"],
        },
        {
            "url": "https://client.com/teeth-whitening",
            "title": "Teeth Whitening",
            "cluster_id": 1,
            "eeat_score": 0.65,
            "word_count": 800,
            "keywords": ["teeth whitening", "white teeth"],
        },
    ]


@pytest.fixture
def competitor_pages():
    """Sample competitor pages."""
    return [
        # Cluster 0: Dental Implants (3 pages)
        {
            "url": "https://competitor1.com/dental-implants",
            "title": "Dental Implants Guide",
            "cluster_id": 0,
            "eeat_score": 0.85,
            "word_count": 2000,
            "traffic_estimate": 1000,
            "doctor_authored": True,
            "medical_citations": 5,
            "keywords": ["dental implants", "tooth replacement"],
        },
        {
            "url": "https://competitor2.com/implants",
            "title": "Implant Surgery",
            "cluster_id": 0,
            "eeat_score": 0.8,
            "word_count": 1800,
            "traffic_estimate": 800,
            "doctor_authored": True,
            "medical_citations": 4,
            "keywords": ["dental implants", "implant surgery"],
        },
        {
            "url": "https://competitor3.com/dental-implants",
            "title": "All About Implants",
            "cluster_id": 0,
            "eeat_score": 0.75,
            "word_count": 1500,
            "traffic_estimate": 600,
            "doctor_authored": False,
            "medical_citations": 2,
            "keywords": ["dental implants"],
        },
        # Cluster 1: Teeth Whitening (2 pages)
        {
            "url": "https://competitor1.com/whitening",
            "title": "Teeth Whitening",
            "cluster_id": 1,
            "eeat_score": 0.7,
            "word_count": 1200,
            "traffic_estimate": 500,
            "doctor_authored": False,
            "medical_citations": 1,
            "keywords": ["teeth whitening"],
        },
        {
            "url": "https://competitor2.com/white-teeth",
            "title": "Get White Teeth",
            "cluster_id": 1,
            "eeat_score": 0.65,
            "word_count": 1000,
            "traffic_estimate": 400,
            "doctor_authored": False,
            "medical_citations": 0,
            "keywords": ["white teeth"],
        },
        # Cluster 2: All-on-4 (missing from client)
        {
            "url": "https://competitor1.com/all-on-4",
            "title": "All-on-4 Implants",
            "cluster_id": 2,
            "eeat_score": 0.9,
            "word_count": 2500,
            "traffic_estimate": 1500,
            "doctor_authored": True,
            "medical_citations": 8,
            "keywords": ["all on 4", "full arch implants"],
        },
        {
            "url": "https://competitor2.com/all-on-4-guide",
            "title": "All-on-4 Guide",
            "cluster_id": 2,
            "eeat_score": 0.85,
            "word_count": 2200,
            "traffic_estimate": 1200,
            "doctor_authored": True,
            "medical_citations": 6,
            "keywords": ["all on 4", "dental implants"],
        },
    ]


@pytest.fixture
def topic_clusters():
    """Sample topic clusters."""
    return [
        {"cluster_id": 0, "name": "Dental Implants"},
        {"cluster_id": 1, "name": "Teeth Whitening"},
        {"cluster_id": 2, "name": "All-on-4 Implants"},
    ]


@pytest.mark.asyncio
async def test_detect_topic_gaps_missing_topic(
    gap_detector, client_pages, competitor_pages, topic_clusters
):
    """Test detection of missing topic (cluster 2)."""
    gaps = await gap_detector.detect_topic_gaps(
        client_pages=client_pages,
        competitor_pages=competitor_pages,
        topic_clusters=topic_clusters,
    )

    # Should detect cluster 2 as gap (0 client pages vs 2 competitor pages)
    cluster_2_gaps = [g for g in gaps if "All-on-4" in g.topic]
    assert len(cluster_2_gaps) == 1

    gap = cluster_2_gaps[0]
    assert gap.gap_type == GapType.MISSING_TOPIC
    assert gap.severity == GapSeverity.HIGH
    assert len(gap.competitor_coverage) == 2  # 2 competitors


@pytest.mark.asyncio
async def test_detect_topic_gaps_underrepresented(
    gap_detector, client_pages, competitor_pages, topic_clusters
):
    """Test detection of underrepresented topic (cluster 0)."""
    gaps = await gap_detector.detect_topic_gaps(
        client_pages=client_pages,
        competitor_pages=competitor_pages,
        topic_clusters=topic_clusters,
    )

    # Should detect cluster 0 as gap (1 client page vs 3 competitor pages)
    cluster_0_gaps = [g for g in gaps if "Dental Implants" in g.topic]
    assert len(cluster_0_gaps) == 1

    gap = cluster_0_gaps[0]
    assert gap.gap_type == GapType.MISSING_TOPIC
    assert gap.severity == GapSeverity.MEDIUM  # Underrepresented


@pytest.mark.asyncio
async def test_detect_topic_gaps_quality_filter(
    gap_detector, client_pages, competitor_pages, topic_clusters
):
    """Test that low-quality competitor pages are filtered out."""
    # Add low-quality competitor page
    low_quality_page = {
        "url": "https://competitor3.com/bad-content",
        "title": "Bad Content",
        "cluster_id": 3,
        "eeat_score": 0.3,  # Below min_content_quality (0.6)
        "word_count": 500,
        "traffic_estimate": 100,
        "doctor_authored": False,
        "medical_citations": 0,
        "keywords": ["bad content"],
    }
    competitor_pages.append(low_quality_page)
    topic_clusters.append({"cluster_id": 3, "name": "Bad Content"})

    gaps = await gap_detector.detect_topic_gaps(
        client_pages=client_pages,
        competitor_pages=competitor_pages,
        topic_clusters=topic_clusters,
    )

    # Should NOT detect cluster 3 as gap (low quality)
    cluster_3_gaps = [g for g in gaps if "Bad Content" in g.topic]
    assert len(cluster_3_gaps) == 0


@pytest.mark.asyncio
async def test_detect_url_gaps(gap_detector, client_pages, competitor_pages):
    """Test detection of missing URLs."""
    gaps = await gap_detector.detect_url_gaps(
        client_pages=client_pages,
        competitor_pages=competitor_pages,
    )

    # Should detect some URL gaps
    assert len(gaps) >= 1

    # Check that gaps have correct type and severity
    for gap in gaps:
        assert gap.gap_type == GapType.MISSING_URL
        assert gap.severity == GapSeverity.HIGH


@pytest.mark.asyncio
async def test_detect_keyword_gaps(gap_detector, client_pages, competitor_pages):
    """Test detection of missing keywords."""
    gaps = await gap_detector.detect_keyword_gaps(
        client_pages=client_pages,
        competitor_pages=competitor_pages,
    )

    # Should detect "all on 4" keyword as missing
    all_on_4_gaps = [g for g in gaps if "all on 4" in g.topic.lower()]
    assert len(all_on_4_gaps) >= 1

    gap = all_on_4_gaps[0]
    assert gap.gap_type == GapType.MISSING_KEYWORD
    assert gap.severity == GapSeverity.MEDIUM


@pytest.mark.asyncio
async def test_group_by_topic(gap_detector, competitor_pages):
    """Test grouping pages by topic cluster."""
    grouped = gap_detector._group_by_topic(competitor_pages)

    assert 0 in grouped
    assert 1 in grouped
    assert 2 in grouped
    assert len(grouped[0]) == 3  # 3 pages in cluster 0
    assert len(grouped[1]) == 2  # 2 pages in cluster 1
    assert len(grouped[2]) == 2  # 2 pages in cluster 2


def test_normalize_url(gap_detector):
    """Test URL normalization."""
    assert (
        gap_detector._normalize_url("https://www.example.com/page/")
        == "example.com/page"
    )
    assert (
        gap_detector._normalize_url("http://example.com/page") == "example.com/page"
    )
    assert gap_detector._normalize_url("https://example.com") == "example.com"


def test_extract_url_pattern(gap_detector):
    """Test URL pattern extraction."""
    assert (
        gap_detector._extract_url_pattern("https://example.com/blog/post-1")
        == "/blog/post-1"
    )
    assert (
        gap_detector._extract_url_pattern("https://example.com/services/dental")
        == "/services/dental"
    )
    assert gap_detector._extract_url_pattern("https://example.com") == "/"


def test_urls_similar(gap_detector):
    """Test URL similarity check."""
    # Same structure, different IDs - should be similar (both have "blog")
    assert gap_detector._urls_similar("/blog/post", "/blog/article")
    # Same structure, same first part - should be similar
    assert gap_detector._urls_similar("/services/dental", "/services/medical")
    # Different structure - should not be similar
    assert not gap_detector._urls_similar("/blog/post", "/services/page")
    # Different depth - should not be similar
    assert not gap_detector._urls_similar("/blog", "/blog/post")


def test_extract_domain(gap_detector):
    """Test domain extraction."""
    assert gap_detector._extract_domain("https://www.example.com/page") == "example.com"
    assert gap_detector._extract_domain("http://example.com") == "example.com"
    assert gap_detector._extract_domain("https://sub.example.com") == "sub.example.com"
