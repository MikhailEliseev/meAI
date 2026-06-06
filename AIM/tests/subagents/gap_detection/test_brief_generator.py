"""
Tests for Brief Generator.
"""

import pytest

from src.aim.subagents.gap_detection.architecture_planner import (
    ContentPage,
    PageType,
)
from src.aim.subagents.gap_detection.brief_generator import (
    BriefConfig,
    BriefGenerator,
    ReadabilityLevel,
)
from src.aim.subagents.schemas.content_gap import (
    ContentGap,
    GapSeverity,
    GapType,
    IntentType,
)


@pytest.fixture
def generator():
    """Create generator with default config."""
    return BriefGenerator()


@pytest.fixture
def sample_page():
    """Create sample content page."""
    return ContentPage(
        title="Dental Implants Cost",
        url_slug="/dental-implants-cost",
        page_type=PageType.HUB,
        target_keyword="dental implants cost",
        related_keywords=["how much are dental implants", "dental implant pricing"],
        search_volume=1000,
        intent=IntentType.COMMERCIAL,
        priority=90,
        estimated_traffic=300,
    )


@pytest.fixture
def sample_gap():
    """Create sample content gap."""
    return ContentGap(
        missing_keyword="dental implants cost",
        gap_type=GapType.MISSING_TOPIC,
        severity=GapSeverity.CRITICAL,
        search_volume=1000,
        opportunity_score=0.9,
        competitor_coverage={"comp1.com": True, "comp2.com": True},
    )


@pytest.fixture
def competitor_urls():
    """Create sample competitor URLs."""
    return [
        "https://competitor1.com/dental-implants-cost",
        "https://competitor2.com/implant-pricing",
        "https://competitor3.com/dental-costs",
    ]


@pytest.mark.asyncio
async def test_generate_brief_basic(generator, sample_page, sample_gap, competitor_urls):
    """Test basic brief generation."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    assert brief.title == sample_page.title
    assert brief.target_keyword == sample_page.target_keyword
    assert brief.search_intent == sample_page.intent
    assert brief.target_word_count >= generator.config.min_word_count
    assert len(brief.eeat_requirements) > 0
    assert len(brief.content_outline) > 0


@pytest.mark.asyncio
async def test_generate_brief_empty_keyword(generator, sample_gap, competitor_urls):
    """Test brief generation with empty keyword."""
    page = ContentPage(
        title="Test",
        url_slug="/test",
        page_type=PageType.HUB,
        target_keyword="",  # Empty
        search_volume=1000,
        intent=IntentType.INFORMATIONAL,
        priority=50,
        estimated_traffic=300,
    )

    with pytest.raises(ValueError, match="target_keyword cannot be empty"):
        await generator.generate_brief(page, sample_gap, competitor_urls)


@pytest.mark.asyncio
async def test_generate_brief_empty_competitors(generator, sample_page, sample_gap):
    """Test brief generation with empty competitors."""
    with pytest.raises(ValueError, match="competitor_urls cannot be empty"):
        await generator.generate_brief(sample_page, sample_gap, [])


@pytest.mark.asyncio
async def test_eeat_requirements_medical(generator, sample_page, sample_gap, competitor_urls):
    """Test E-E-A-T requirements for medical content."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    eeat_categories = {req.category for req in brief.eeat_requirements}
    assert "Experience" in eeat_categories
    assert "Expertise" in eeat_categories
    assert "Authoritativeness" in eeat_categories
    assert "Trustworthiness" in eeat_categories


@pytest.mark.asyncio
async def test_eeat_requirements_commercial(generator, sample_gap, competitor_urls):
    """Test E-E-A-T requirements for commercial intent."""
    page = ContentPage(
        title="Test",
        url_slug="/test",
        page_type=PageType.HUB,
        target_keyword="dental implants cost",
        search_volume=1000,
        intent=IntentType.COMMERCIAL,
        priority=50,
        estimated_traffic=300,
    )

    brief = await generator.generate_brief(page, sample_gap, competitor_urls)

    # Commercial intent should have Transparency requirement
    categories = [req.category for req in brief.eeat_requirements]
    assert "Transparency" in categories


@pytest.mark.asyncio
async def test_content_outline_structure(generator, sample_page, sample_gap, competitor_urls):
    """Test content outline structure."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    outline = brief.content_outline
    assert len(outline) >= generator.config.min_sections

    # Check first section is Introduction
    assert outline[0].heading == "Introduction"
    assert outline[0].heading_level == 2

    # Check all sections have required fields
    for section in outline:
        assert section.heading
        assert 2 <= section.heading_level <= 4
        assert section.target_word_count >= 50
        assert len(section.key_points) > 0


@pytest.mark.asyncio
async def test_content_outline_commercial_intent(generator, sample_page, sample_gap, competitor_urls):
    """Test content outline for commercial intent."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    headings = [section.heading for section in brief.content_outline]
    # Commercial intent should have cost-related sections
    assert any("Cost" in h or "Financing" in h for h in headings)


@pytest.mark.asyncio
async def test_content_outline_informational_intent(generator, sample_gap, competitor_urls):
    """Test content outline for informational intent."""
    page = ContentPage(
        title="Dental Implant Procedure",
        url_slug="/dental-implant-procedure",
        page_type=PageType.HUB,
        target_keyword="dental implant procedure",
        search_volume=500,
        intent=IntentType.INFORMATIONAL,
        priority=80,
        estimated_traffic=150,
    )

    brief = await generator.generate_brief(page, sample_gap, competitor_urls)

    headings = [section.heading for section in brief.content_outline]
    # Informational intent should have how-to sections
    assert any("How" in h or "Benefits" in h for h in headings)


@pytest.mark.asyncio
async def test_word_count_calculation(generator, sample_page, sample_gap, competitor_urls):
    """Test target word count calculation."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    # Word count should be within config limits
    assert generator.config.min_word_count <= brief.target_word_count <= generator.config.max_word_count


@pytest.mark.asyncio
async def test_internal_links_hub_page(generator, sample_gap, competitor_urls):
    """Test internal links for hub page."""
    page = ContentPage(
        title="Test Hub",
        url_slug="/test-hub",
        page_type=PageType.HUB,
        target_keyword="test keyword",
        search_volume=1000,
        intent=IntentType.INFORMATIONAL,
        spoke_page_slugs=["/spoke1", "/spoke2", "/spoke3"],
        priority=50,
        estimated_traffic=300,
    )

    brief = await generator.generate_brief(page, sample_gap, competitor_urls)

    # Hub should link to spokes
    assert len(brief.internal_links) > 0
    assert "/spoke1" in brief.internal_links


@pytest.mark.asyncio
async def test_internal_links_spoke_page(generator, sample_gap, competitor_urls):
    """Test internal links for spoke page."""
    page = ContentPage(
        title="Test Spoke",
        url_slug="/test-spoke",
        page_type=PageType.SPOKE,
        target_keyword="test keyword",
        search_volume=500,
        intent=IntentType.INFORMATIONAL,
        hub_page_slug="/test-hub",
        priority=50,
        estimated_traffic=150,
    )

    brief = await generator.generate_brief(page, sample_gap, competitor_urls)

    # Spoke should link to hub
    assert "/test-hub" in brief.internal_links


@pytest.mark.asyncio
async def test_external_sources(generator, sample_page, sample_gap, competitor_urls):
    """Test external sources recommendations."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    # Should have authoritative medical sources
    assert len(brief.external_sources) > 0
    assert any("pubmed" in src.lower() for src in brief.external_sources)
    assert any("ada.org" in src.lower() for src in brief.external_sources)


@pytest.mark.asyncio
async def test_meta_description_length(generator, sample_page, sample_gap, competitor_urls):
    """Test meta description length."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    assert len(brief.meta_description) <= 160
    assert len(brief.meta_description) > 0


@pytest.mark.asyncio
async def test_meta_description_commercial(generator, sample_page, sample_gap, competitor_urls):
    """Test meta description for commercial intent."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    # Commercial meta should mention costs/pricing
    assert any(word in brief.meta_description.lower() for word in ["cost", "price", "financing"])


@pytest.mark.asyncio
async def test_notes_generation(generator, sample_page, sample_gap, competitor_urls):
    """Test notes generation."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    # Should have notes
    assert len(brief.notes) > 0

    # Critical gap should have priority note
    if sample_gap.severity == GapSeverity.CRITICAL:
        assert "HIGH PRIORITY" in brief.notes or "CRITICAL" in brief.notes


@pytest.mark.asyncio
async def test_custom_config(sample_page, sample_gap, competitor_urls):
    """Test brief generation with custom config."""
    config = BriefConfig(
        min_word_count=1500,
        max_word_count=2500,
        target_readability=ReadabilityLevel.COLLEGE,
        min_sections=8,
        include_faq=False,
    )
    generator = BriefGenerator(config)

    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)

    assert brief.target_word_count >= 1500
    assert brief.readability_level == ReadabilityLevel.COLLEGE


@pytest.mark.asyncio
async def test_export_brief_markdown(generator, sample_page, sample_gap, competitor_urls):
    """Test markdown export."""
    brief = await generator.generate_brief(sample_page, sample_gap, competitor_urls)
    markdown = await generator.export_brief_markdown(brief)

    assert isinstance(markdown, str)
    assert len(markdown) > 0
    assert brief.title in markdown
    assert brief.target_keyword in markdown
    assert "## Overview" in markdown
    assert "## E-E-A-T Requirements" in markdown
    assert "## Content Outline" in markdown
