"""Tests for SEO Magister V2."""

import pytest
from datetime import datetime

from src.aim.magisters.seo_magister_v2 import (
    SEOMagisterV2,
    SEOWorkflowReport,
)
from src.aim.subagents.seo.keyword_research_agent import (
    KeywordCluster,
    KeywordIntent,
    KeywordPriority,
    KeywordResearchResult,
)
from src.aim.subagents.schemas.api_responses import KeywordDataUnified
from src.aim.subagents.seo.onpage_optimizer import (
    TitleTagAnalysis,
    MetaDescriptionAnalysis,
    HeaderStructure,
    ContentAnalysis,
    InternalLinking,
    ImageOptimization,
    URLAnalysis,
    OnPageReport,
)
from src.aim.subagents.seo.schema_generator import (
    SchemaValidation,
    SchemaReport,
)


@pytest.fixture
def magister():
    """Create SEO Magister V2 instance."""
    return SEOMagisterV2()


@pytest.fixture
def sample_keyword_report():
    """Sample keyword research report."""
    kw1 = KeywordDataUnified(
        keyword="dental implants",
        volume=5000,
        difficulty=65.0,
        cpc=12.50,
        intent="commercial",
        source="semrush",
        priority_score=75.5,
    )
    kw2 = KeywordDataUnified(
        keyword="dental implants cost",
        volume=3000,
        difficulty=55.0,
        cpc=10.00,
        intent="commercial",
        source="semrush",
        priority_score=70.0,
    )

    return KeywordResearchResult(
        seed_keyword="dental implants",
        timestamp=datetime.now().isoformat(),
        keywords=[kw1, kw2],
        total_keywords=2,
        intents=[
            KeywordIntent(
                keyword="dental implants",
                intent="commercial",
                confidence=0.9,
                signals=["cost", "price"],
            )
        ],
        clusters=[
            KeywordCluster(
                main_keyword="dental implants",
                keywords=[kw1, kw2],
                total_volume=8000,
                avg_difficulty=60.0,
                avg_cpc=11.25,
                cluster_size=2,
            )
        ],
        total_clusters=1,
        priorities=[
            KeywordPriority(
                keyword="dental implants",
                priority_score=75.5,
                volume=5000,
                difficulty=65.0,
                cpc=12.50,
                intent="commercial",
                reason="High volume, commercial intent",
            )
        ],
        total_volume=8000,
        avg_difficulty=60.0,
        avg_cpc=11.25,
        top_opportunities=[kw1],
    )


@pytest.fixture
def sample_onpage_report():
    """Sample on-page optimization report."""
    return OnPageReport(
        url="https://example.com",
        timestamp=datetime.now().isoformat(),
        title_tag=TitleTagAnalysis(
            title="Dental Implants - Best Clinic",
            length=30,
            has_keyword=True,
            keyword_position=1,
            is_optimal_length=False,
            issues=["Title too short"],
            recommendations=["Expand to 50-60 characters"],
        ),
        meta_description=MetaDescriptionAnalysis(
            description="Professional dental implants service",
            length=40,
            has_keyword=True,
            has_cta=False,
            is_optimal_length=False,
            issues=["Too short", "Missing CTA"],
            recommendations=["Expand to 150-160 characters", "Add call-to-action"],
        ),
        headers=HeaderStructure(
            h1_count=1,
            h1_text=["Dental Implants"],
            h2_count=3,
            h3_count=5,
            has_keyword_in_h1=True,
            hierarchy_valid=True,
            issues=[],
            recommendations=[],
        ),
        content=ContentAnalysis(
            word_count=800,
            keyword_density=2.5,
            keyword_count=20,
            readability_score=65.0,
            paragraph_count=10,
            avg_paragraph_length=80.0,
            has_lists=True,
            has_images=True,
            issues=["Keyword density slightly high"],
            recommendations=["Reduce keyword density to 1-2%"],
        ),
        internal_linking=InternalLinking(
            total_links=10,
            internal_links=5,
            external_links=5,
            broken_links=0,
            anchor_text_optimized=True,
            link_depth=2,
            issues=["Few internal links"],
            recommendations=["Add more internal links (target: 10-15)"],
        ),
        images=ImageOptimization(
            total_images=3,
            images_with_alt=2,
            images_without_alt=1,
            alt_text_quality=66.67,
            large_images=1,
            webp_usage=33.33,
            issues=["1 image missing alt text"],
            recommendations=["Add alt text to all images"],
        ),
        url_analysis=URLAnalysis(
            url="https://example.com/dental-implants",
            length=40,
            has_keyword=True,
            is_readable=True,
            has_special_chars=False,
            depth=1,
            issues=[],
            recommendations=[],
        ),
        overall_score=75.0,
        priority_issues=[
            "Meta description too short (40 chars)",
            "Missing CTA in meta description",
            "Few internal links (5)",
        ],
        quick_wins=[
            "Add alt text to 1 image",
            "Add call-to-action to meta description",
        ],
    )


@pytest.fixture
def sample_schema_report():
    """Sample schema markup report."""
    return SchemaReport(
        url="https://example.com",
        timestamp=datetime.now().isoformat(),
        schemas=[
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Example Clinic",
                "url": "https://example.com",
            }
        ],
        validation_results=[
            SchemaValidation(
                is_valid=True,
                schema_type="Organization",
                errors=[],
                warnings=[],
                recommendations=[],
            )
        ],
        missing_schemas=["LocalBusiness", "MedicalBusiness"],
        rich_results_eligible=True,
        overall_score=50.0,
    )


@pytest.mark.asyncio
async def test_calculate_overall_score(magister, sample_keyword_report, sample_onpage_report, sample_schema_report):
    """Test overall score calculation."""
    score = magister._calculate_overall_score(
        sample_keyword_report,
        sample_onpage_report,
        sample_schema_report,
    )

    # Keyword: 1 opportunity * 10 = 10 (30% weight = 3.0)
    # On-page: 75.0 (50% weight = 37.5)
    # Schema: 50.0 (20% weight = 10.0)
    # Total: 3.0 + 37.5 + 10.0 = 50.5
    assert 50.0 <= score <= 51.0


@pytest.mark.asyncio
async def test_generate_priority_actions(magister, sample_keyword_report, sample_onpage_report, sample_schema_report):
    """Test priority actions generation."""
    actions = magister._generate_priority_actions(
        sample_keyword_report,
        sample_onpage_report,
        sample_schema_report,
    )

    assert isinstance(actions, list)
    assert len(actions) <= 5
    # Should include top keyword
    assert any("dental implants" in action.lower() for action in actions)
    # Should include on-page issues
    assert any("meta description" in action.lower() for action in actions)
    # Should include schema recommendation
    assert any("localbusiness" in action.lower() for action in actions)


@pytest.mark.asyncio
async def test_estimate_impact_high(magister):
    """Test impact estimation for low score."""
    impact = magister._estimate_impact(30.0, ["action1", "action2"])
    assert impact == "high"


@pytest.mark.asyncio
async def test_estimate_impact_medium(magister):
    """Test impact estimation for medium score."""
    impact = magister._estimate_impact(55.0, ["action1", "action2"])
    assert impact == "medium"


@pytest.mark.asyncio
async def test_estimate_impact_low(magister):
    """Test impact estimation for high score."""
    impact = magister._estimate_impact(85.0, ["action1", "action2"])
    assert impact == "low"


@pytest.mark.asyncio
async def test_execute_workflow_structure(magister):
    """Test workflow execution returns correct structure."""
    # Mock data to avoid real API calls
    report = await magister.execute_workflow(
        url="https://example.com",
        seed_keyword="dental implants",
        html_content="<html><head><title>Test</title></head><body><h1>Test</h1></body></html>",
    )

    assert isinstance(report, SEOWorkflowReport)
    assert report.url == "https://example.com"
    assert isinstance(report.generated_at, str)
    assert isinstance(report.duration_seconds, float)
    assert isinstance(report.keyword_research, KeywordResearchResult)
    assert isinstance(report.on_page_optimization, OnPageReport)
    assert isinstance(report.schema_markup, SchemaReport)
    assert 0 <= report.overall_score <= 100
    assert isinstance(report.priority_actions, list)
    assert report.estimated_impact in ["high", "medium", "low"]
    assert report.workflow_status in ["success", "partial", "failed"]
    assert isinstance(report.errors, list)


@pytest.mark.asyncio
async def test_execute_keyword_research_only(magister):
    """Test executing only keyword research phase."""
    report = await magister.execute_keyword_research_only(
        seed_keyword="dental implants",
        max_keywords=10,
    )

    assert isinstance(report, KeywordResearchResult)
    assert report.seed_keyword == "dental implants"


@pytest.mark.asyncio
async def test_execute_onpage_optimization_only(magister):
    """Test executing only on-page optimization phase."""
    report = await magister.execute_onpage_optimization_only(
        url="https://example.com",
        target_keyword="dental implants",
        html_content="<html><head><title>Test</title></head><body><h1>Test</h1></body></html>",
    )

    assert isinstance(report, OnPageReport)
    assert report.url == "https://example.com"


@pytest.mark.asyncio
async def test_execute_schema_generation_only(magister):
    """Test executing only schema markup phase."""
    report = await magister.execute_schema_generation_only(
        url="https://example.com",
        html_content="<html><head><title>Test</title></head><body><h1>Test</h1></body></html>",
    )

    assert isinstance(report, SchemaReport)
    assert report.url == "https://example.com"


@pytest.mark.asyncio
async def test_workflow_with_errors_partial_status(magister, monkeypatch):
    """Test workflow continues with partial status when one phase fails."""
    # Mock keyword agent to raise exception
    async def mock_research(*args, **kwargs):
        raise Exception("API error")

    monkeypatch.setattr(magister.keyword_agent, "research", mock_research)

    report = await magister.execute_workflow(
        url="https://example.com",
        seed_keyword="dental implants",
        html_content="<html><head><title>Test</title></head><body><h1>Test</h1></body></html>",
    )

    assert report.workflow_status == "partial"
    assert len(report.errors) > 0
    assert any("Keyword Research failed" in error for error in report.errors)


@pytest.mark.asyncio
async def test_workflow_priority_actions_limit(magister, sample_keyword_report, sample_onpage_report, sample_schema_report):
    """Test priority actions are limited to top 5."""
    # Create on-page report with many issues
    onpage_with_many_issues = OnPageReport(
        url="https://example.com",
        timestamp=datetime.now().isoformat(),
        title_tag=sample_onpage_report.title_tag,
        meta_description=sample_onpage_report.meta_description,
        headers=sample_onpage_report.headers,
        content=sample_onpage_report.content,
        internal_linking=sample_onpage_report.internal_linking,
        images=sample_onpage_report.images,
        url_analysis=sample_onpage_report.url_analysis,
        overall_score=50.0,
        priority_issues=[f"Issue {i}" for i in range(10)],  # 10 issues
        quick_wins=[],
    )

    actions = magister._generate_priority_actions(
        sample_keyword_report,
        onpage_with_many_issues,
        sample_schema_report,
    )

    assert len(actions) <= 5
