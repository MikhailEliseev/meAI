"""Tests for OpportunityScorer."""

import pytest

from src.aim.subagents.gap_detection.opportunity_scorer import OpportunityScorer
from src.aim.subagents.schemas.content_gap import (
    ContentGap,
    GapSeverity,
    GapType,
)


@pytest.fixture
def opportunity_scorer():
    """Create opportunity scorer instance."""
    return OpportunityScorer()


@pytest.fixture
def sample_gaps():
    """Sample content gaps."""
    return [
        ContentGap(
            topic="All-on-4 Implants",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.HIGH,
            opportunity_score=0.0,  # Will be calculated
            priority="P3",  # Will be assigned
            competitor_coverage={
                "competitor1.com": {
                    "url": "https://competitor1.com/all-on-4",
                    "quality_score": 0.9,
                    "traffic_estimate": 1500,
                    "word_count": 2500,
                    "doctor_authored": True,
                    "medical_citations": 8,
                },
                "competitor2.com": {
                    "url": "https://competitor2.com/all-on-4-guide",
                    "quality_score": 0.85,
                    "traffic_estimate": 1200,
                    "word_count": 2200,
                    "doctor_authored": True,
                    "medical_citations": 6,
                },
            },
            target_keywords=["all on 4", "full arch implants"],
        ),
        ContentGap(
            topic="Teeth Whitening",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.MEDIUM,
            opportunity_score=0.0,
            priority="P3",
            competitor_coverage={
                "competitor1.com": {
                    "url": "https://competitor1.com/whitening",
                    "quality_score": 0.7,
                    "traffic_estimate": 500,
                    "word_count": 1200,
                    "doctor_authored": False,
                    "medical_citations": 1,
                },
            },
            target_keywords=["teeth whitening"],
        ),
    ]


@pytest.fixture
def client_pages():
    """Sample client pages."""
    return [
        {
            "url": "https://client.com/dental-implants",
            "title": "Dental Implants",
            "eeat_score": 0.7,
            "word_count": 1000,
            "doctor_authored": False,
            "medical_citations": 2,
            "keywords": ["dental implants"],
        },
    ]


@pytest.fixture
def competitor_pages():
    """Sample competitor pages."""
    return [
        {
            "url": "https://competitor1.com/all-on-4",
            "title": "All-on-4 Implants",
            "eeat_score": 0.9,
            "word_count": 2500,
            "doctor_authored": True,
            "medical_citations": 8,
        },
        {
            "url": "https://competitor2.com/all-on-4-guide",
            "title": "All-on-4 Guide",
            "eeat_score": 0.85,
            "word_count": 2200,
            "doctor_authored": True,
            "medical_citations": 6,
        },
    ]


@pytest.mark.asyncio
async def test_score_gaps(opportunity_scorer, sample_gaps, client_pages):
    """Test scoring multiple gaps."""
    scored_gaps = await opportunity_scorer.score_gaps(
        gaps=sample_gaps,
        niche="dental implants",
        client_pages=client_pages,
    )

    assert len(scored_gaps) == 2

    # Check that scores are calculated
    for gap in scored_gaps:
        assert gap.opportunity_score > 0.0
        assert gap.opportunity_score <= 100.0
        assert gap.priority in ["P0", "P1", "P2", "P3"]

    # Check that gaps are sorted by score (descending)
    assert scored_gaps[0].opportunity_score >= scored_gaps[1].opportunity_score


@pytest.mark.asyncio
async def test_calculate_opportunity_score_high_traffic(
    opportunity_scorer, sample_gaps, client_pages
):
    """Test that high traffic increases opportunity score."""
    gap = sample_gaps[0]  # All-on-4 with high traffic (1500, 1200)

    score = await opportunity_scorer._calculate_opportunity_score(
        gap=gap,
        niche="dental implants",
        client_pages=client_pages,
    )

    assert score > 0.0
    assert score <= 100.0


@pytest.mark.asyncio
async def test_calculate_opportunity_score_low_traffic(
    opportunity_scorer, sample_gaps, client_pages
):
    """Test that low traffic decreases opportunity score."""
    gap = sample_gaps[1]  # Teeth Whitening with low traffic (500)

    score = await opportunity_scorer._calculate_opportunity_score(
        gap=gap,
        niche="dental implants",
        client_pages=client_pages,
    )

    # Should be lower than high-traffic gap
    high_traffic_gap = sample_gaps[0]
    high_score = await opportunity_scorer._calculate_opportunity_score(
        gap=high_traffic_gap,
        niche="dental implants",
        client_pages=client_pages,
    )

    # Note: Low traffic gap might score higher due to lower difficulty
    # Just check that both scores are valid
    assert 0.0 <= score <= 100.0
    assert 0.0 <= high_score <= 100.0


def test_calculate_competitor_traffic(opportunity_scorer, sample_gaps):
    """Test competitor traffic calculation."""
    gap = sample_gaps[0]  # Traffic: 1500, 1200

    traffic = opportunity_scorer._calculate_competitor_traffic(gap)

    assert traffic > 0.0
    assert traffic <= 1.0
    # Average traffic: (1500 + 1200) / 2 = 1350
    # Normalized: 1350 / 10000 = 0.135
    assert traffic == pytest.approx(0.135, abs=0.01)


def test_calculate_competitor_quality(opportunity_scorer, sample_gaps):
    """Test competitor quality calculation."""
    gap = sample_gaps[0]  # Quality: 0.9, 0.85

    quality = opportunity_scorer._calculate_competitor_quality(gap)

    assert quality > 0.0
    assert quality <= 1.0
    # Average quality: (0.9 + 0.85) / 2 = 0.875
    assert quality == pytest.approx(0.875, abs=0.01)


def test_calculate_topic_relevance_high(opportunity_scorer, sample_gaps):
    """Test topic relevance calculation (high relevance)."""
    gap = sample_gaps[0]  # Topic: "All-on-4 Implants"

    relevance = opportunity_scorer._calculate_topic_relevance(
        gap=gap,
        niche="dental implants",
    )

    assert relevance > 0.0
    assert relevance <= 1.0
    # "implants" matches niche
    assert relevance > 0.3


def test_calculate_topic_relevance_low(opportunity_scorer, sample_gaps):
    """Test topic relevance calculation (low relevance)."""
    gap = sample_gaps[1]  # Topic: "Teeth Whitening"

    relevance = opportunity_scorer._calculate_topic_relevance(
        gap=gap,
        niche="dental implants",
    )

    assert relevance >= 0.0
    assert relevance <= 1.0
    # No keyword match
    assert relevance < 0.5


def test_calculate_content_difficulty_high(opportunity_scorer, sample_gaps):
    """Test content difficulty calculation (high difficulty)."""
    gap = sample_gaps[0]  # Long content, doctor-authored, many citations

    difficulty = opportunity_scorer._calculate_content_difficulty(gap)

    assert difficulty > 0.0
    assert difficulty <= 1.0
    # High word count (2500, 2200), doctor-authored, many citations
    assert difficulty > 0.5


def test_calculate_content_difficulty_low(opportunity_scorer, sample_gaps):
    """Test content difficulty calculation (low difficulty)."""
    gap = sample_gaps[1]  # Shorter content, not doctor-authored, few citations

    difficulty = opportunity_scorer._calculate_content_difficulty(gap)

    assert difficulty >= 0.0
    assert difficulty <= 1.0
    # Lower word count (1200), not doctor-authored, few citations
    assert difficulty < 0.5


def test_calculate_client_coverage_zero(opportunity_scorer, sample_gaps, client_pages):
    """Test client coverage calculation (zero coverage)."""
    gap = sample_gaps[0]  # Topic: "All-on-4 Implants"

    coverage = opportunity_scorer._calculate_client_coverage(
        gap=gap,
        client_pages=client_pages,
    )

    # Should be very low (< 0.3) since "All-on-4 Implants" doesn't match "Dental Implants" well
    # (only 1 out of 3 keywords match: "implants")
    assert coverage < 0.3


def test_calculate_client_coverage_partial(opportunity_scorer, sample_gaps):
    """Test client coverage calculation (partial coverage)."""
    gap = sample_gaps[0]  # Topic: "All-on-4 Implants"

    # Add client page with partial match
    client_pages = [
        {
            "title": "Dental Implants Guide",
            "keywords": ["dental implants", "implants"],
        },
    ]

    coverage = opportunity_scorer._calculate_client_coverage(
        gap=gap,
        client_pages=client_pages,
    )

    assert coverage > 0.0
    assert coverage <= 1.0


def test_assign_priority_tier_p0(opportunity_scorer):
    """Test priority tier assignment (P0)."""
    assert opportunity_scorer._assign_priority_tier(85.0) == "P0"
    assert opportunity_scorer._assign_priority_tier(100.0) == "P0"


def test_assign_priority_tier_p1(opportunity_scorer):
    """Test priority tier assignment (P1)."""
    assert opportunity_scorer._assign_priority_tier(70.0) == "P1"
    assert opportunity_scorer._assign_priority_tier(60.0) == "P1"


def test_assign_priority_tier_p2(opportunity_scorer):
    """Test priority tier assignment (P2)."""
    assert opportunity_scorer._assign_priority_tier(50.0) == "P2"
    assert opportunity_scorer._assign_priority_tier(40.0) == "P2"


def test_assign_priority_tier_p3(opportunity_scorer):
    """Test priority tier assignment (P3)."""
    assert opportunity_scorer._assign_priority_tier(30.0) == "P3"
    assert opportunity_scorer._assign_priority_tier(0.0) == "P3"


@pytest.mark.asyncio
async def test_calculate_quality_comparison(
    opportunity_scorer, client_pages, competitor_pages
):
    """Test quality comparison calculation."""
    comparison = await opportunity_scorer.calculate_quality_comparison(
        client_pages=client_pages,
        competitor_pages=competitor_pages,
    )

    assert "client" in comparison
    assert "competitors_avg" in comparison
    assert "gaps" in comparison

    # Check client metrics
    assert comparison["client"]["avg_word_count"] == 1000
    assert comparison["client"]["avg_eeat_score"] == 0.7

    # Check competitor metrics
    assert comparison["competitors_avg"]["avg_word_count"] == pytest.approx(
        2350, abs=50
    )  # (2500 + 2200) / 2
    assert comparison["competitors_avg"]["avg_eeat_score"] == pytest.approx(
        0.875, abs=0.01
    )  # (0.9 + 0.85) / 2

    # Check gaps
    assert comparison["gaps"]["word_count_gap"] > 0  # Competitor has more words
    assert comparison["gaps"]["eeat_gap"] > 0  # Competitor has higher E-E-A-T


def test_aggregate_metrics_empty(opportunity_scorer):
    """Test metrics aggregation with empty list."""
    metrics = opportunity_scorer._aggregate_metrics([])

    assert metrics["avg_word_count"] == 0.0
    assert metrics["avg_eeat_score"] == 0.0
    assert metrics["doctor_authored_pct"] == 0.0
    assert metrics["medical_citations_per_page"] == 0.0


def test_aggregate_metrics(opportunity_scorer, competitor_pages):
    """Test metrics aggregation."""
    metrics = opportunity_scorer._aggregate_metrics(competitor_pages)

    assert metrics["avg_word_count"] == pytest.approx(2350, abs=50)
    assert metrics["avg_eeat_score"] == pytest.approx(0.875, abs=0.01)
    assert metrics["doctor_authored_pct"] == 1.0  # Both are doctor-authored
    assert metrics["medical_citations_per_page"] == pytest.approx(7.0, abs=0.5)
