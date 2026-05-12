"""
Tests for Architecture Planner.
"""

import pytest

from AIM.src.aim.subagents.gap_detection.architecture_planner import (
    ArchitecturePlanner,
    ContentPage,
    PageType,
    PlanningConfig,
)
from AIM.src.aim.subagents.schemas.content_gap import (
    ContentCluster,
    ContentGap,
    GapSeverity,
    GapType,
    IntentType,
)


@pytest.fixture
def planner():
    """Create planner with default config."""
    return ArchitecturePlanner()


@pytest.fixture
def sample_gaps():
    """Create sample content gaps."""
    return [
        ContentGap(
            missing_keyword="dental implants cost",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.CRITICAL,
            search_volume=1000,
            opportunity_score=0.9,
            competitor_coverage={"comp1.com": True, "comp2.com": True},
        ),
        ContentGap(
            missing_keyword="how much are dental implants",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.HIGH,
            search_volume=800,
            opportunity_score=0.85,
            competitor_coverage={"comp1.com": True},
        ),
        ContentGap(
            missing_keyword="dental implant procedure",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.HIGH,
            search_volume=500,
            opportunity_score=0.8,
            competitor_coverage={"comp2.com": True},
        ),
        ContentGap(
            missing_keyword="dental implant recovery",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.MEDIUM,
            search_volume=300,
            opportunity_score=0.7,
            competitor_coverage={"comp1.com": True},
        ),
    ]


@pytest.fixture
def sample_clusters():
    """Create sample content clusters."""
    return [
        ContentCluster(
            hub_keyword="dental implants cost",
            spoke_keywords=["how much are dental implants", "dental implant pricing"],
            total_search_volume=2000,
            primary_intent=IntentType.COMMERCIAL,
            keywords=["dental implants cost", "how much are dental implants", "dental implant pricing"],
        ),
        ContentCluster(
            hub_keyword="dental implant procedure",
            spoke_keywords=["dental implant recovery", "dental implant steps"],
            total_search_volume=1000,
            primary_intent=IntentType.INFORMATIONAL,
            keywords=["dental implant procedure", "dental implant recovery", "dental implant steps"],
        ),
    ]


@pytest.mark.asyncio
async def test_plan_architecture_basic(planner, sample_gaps, sample_clusters):
    """Test basic architecture planning."""
    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)

    assert architecture.total_pages > 0
    assert len(architecture.hub_pages) >= 1
    assert len(architecture.creation_order) == architecture.total_pages
    assert architecture.total_estimated_traffic > 0


@pytest.mark.asyncio
async def test_plan_architecture_empty_gaps(planner, sample_clusters):
    """Test planning with empty gaps."""
    with pytest.raises(ValueError, match="gaps cannot be empty"):
        await planner.plan_architecture([], sample_clusters)


@pytest.mark.asyncio
async def test_plan_architecture_empty_clusters(planner, sample_gaps):
    """Test planning with empty clusters."""
    with pytest.raises(ValueError, match="clusters cannot be empty"):
        await planner.plan_architecture(sample_gaps, [])


@pytest.mark.asyncio
async def test_hub_pages_creation(planner, sample_gaps, sample_clusters):
    """Test hub pages are created correctly."""
    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)

    hub_pages = architecture.hub_pages
    assert len(hub_pages) >= 1

    for hub in hub_pages:
        assert hub.page_type == PageType.HUB
        assert hub.hub_page_slug is None
        assert hub.search_volume >= planner.config.min_hub_volume
        assert len(hub.spoke_page_slugs) >= 0


@pytest.mark.asyncio
async def test_spoke_pages_creation(planner, sample_gaps, sample_clusters):
    """Test spoke pages are created and linked to hubs."""
    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)

    spoke_pages = architecture.spoke_pages

    for spoke in spoke_pages:
        assert spoke.page_type == PageType.SPOKE
        assert spoke.hub_page_slug is not None
        assert spoke.hub_page_slug.startswith("/")
        assert len(spoke.spoke_page_slugs) == 0


@pytest.mark.asyncio
async def test_standalone_pages_creation(planner, sample_gaps, sample_clusters):
    """Test standalone pages are created for unclustered gaps."""
    # Add gap not in any cluster
    unclustered_gap = ContentGap(
        missing_keyword="unique topic",
        gap_type=GapType.MISSING_TOPIC,
        severity=GapSeverity.CRITICAL,
        search_volume=500,
        opportunity_score=0.9,
        competitor_coverage={"comp1.com": True},
    )
    gaps = sample_gaps + [unclustered_gap]

    architecture = await planner.plan_architecture(gaps, sample_clusters)

    standalone_pages = architecture.standalone_pages
    assert len(standalone_pages) >= 1

    for standalone in standalone_pages:
        assert standalone.page_type == PageType.STANDALONE
        assert standalone.hub_page_slug is None
        assert len(standalone.spoke_page_slugs) == 0


def test_generate_title(planner):
    """Test title generation from keyword."""
    title = planner._generate_title("dental implants cost")
    assert title == "Dental Implants Cost"


def test_generate_slug(planner):
    """Test URL slug generation from keyword."""
    slug = planner._generate_slug("dental implants cost")
    assert slug == "/dental-implants-cost"


def test_calculate_priority(planner, sample_gaps):
    """Test priority calculation."""
    gap = sample_gaps[0]  # CRITICAL severity, 1000 volume, 0.9 score

    priority = planner._calculate_priority(gap, gap.search_volume)

    assert 0 <= priority <= 100
    assert priority >= 90  # Should be high due to CRITICAL severity


@pytest.mark.asyncio
async def test_creation_order_hubs_first(planner, sample_gaps, sample_clusters):
    """Test that hub pages come first in creation order."""
    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)

    # Get page types in creation order
    page_map = {
        page.url_slug: page
        for page in architecture.hub_pages + architecture.spoke_pages + architecture.standalone_pages
    }
    ordered_types = [page_map[slug].page_type for slug in architecture.creation_order]

    # Find first hub and first spoke
    first_hub_idx = next((i for i, t in enumerate(ordered_types) if t == PageType.HUB), None)
    first_spoke_idx = next((i for i, t in enumerate(ordered_types) if t == PageType.SPOKE), None)

    # Hubs should come before spokes
    if first_hub_idx is not None and first_spoke_idx is not None:
        assert first_hub_idx < first_spoke_idx


@pytest.mark.asyncio
async def test_custom_config(sample_gaps, sample_clusters):
    """Test planning with custom config."""
    config = PlanningConfig(
        min_hub_volume=1500,  # Higher threshold
        min_spoke_volume=100,
        max_spokes_per_hub=5,
        traffic_multiplier=0.5,
    )
    planner = ArchitecturePlanner(config)

    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)

    # With higher min_hub_volume, fewer hubs expected
    assert all(hub.search_volume >= 1500 for hub in architecture.hub_pages)


@pytest.mark.asyncio
async def test_export_architecture_summary(planner, sample_gaps, sample_clusters):
    """Test architecture summary export."""
    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)
    summary = await planner.export_architecture_summary(architecture)

    assert "total_pages" in summary
    assert "hub_pages" in summary
    assert "spoke_pages" in summary
    assert "total_estimated_traffic" in summary
    assert "creation_order_preview" in summary
    assert "top_priority_pages" in summary
    assert len(summary["top_priority_pages"]) <= 5


@pytest.mark.asyncio
async def test_traffic_estimation(planner, sample_gaps, sample_clusters):
    """Test traffic estimation for pages."""
    architecture = await planner.plan_architecture(sample_gaps, sample_clusters)

    for page in architecture.hub_pages + architecture.spoke_pages:
        # Traffic should be volume * multiplier
        expected_traffic = int(page.search_volume * planner.config.traffic_multiplier)
        assert page.estimated_traffic == expected_traffic
