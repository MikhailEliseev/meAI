"""Tests for Content Magister V2."""

import pytest
from datetime import datetime

from AIM.src.aim.magisters.content_magister_v2 import (
    ContentMagisterV2,
    ContentWorkflowReport,
)
from AIM.src.aim.subagents.content.content_brief_generator import (
    ContentBrief,
    HeaderStructure,
    TopicCoverage,
    QuestionToAnswer,
)
from AIM.src.aim.subagents.content.content_quality_checker import (
    ReadabilityAnalysis,
    GrammarAnalysis,
    UniquenessAnalysis,
    EEATAnalysis,
    ContentDepthAnalysis,
    EngagementAnalysis,
    ContentQualityReport,
)
from AIM.src.aim.subagents.content.content_calendar_manager import (
    ContentItem,
    ContentGap,
    ContentCalendarReport,
    ChannelSchedule,
    DeadlineAlert,
    CalendarMetrics,
)


@pytest.fixture
def magister():
    """Create Content Magister V2 instance."""
    return ContentMagisterV2()


@pytest.fixture
def sample_brief():
    """Sample content brief."""
    return ContentBrief(
        target_keyword="dental implants",
        timestamp=datetime.now().isoformat(),
        search_volume=5000,
        keyword_difficulty=65.0,
        search_intent="commercial",
        recommended_word_count=2000,
        word_count_range=(1800, 2200),
        tone="professional",
        header_structure=[
            HeaderStructure(
                level=1,
                text="Complete Guide to Dental Implants",
                keywords=["dental implants", "guide"],
            ),
            HeaderStructure(
                level=2,
                text="What Are Dental Implants",
                keywords=["dental implants", "definition"],
            ),
        ],
        topics_to_cover=[
            TopicCoverage(
                topic="Types of dental implants",
                priority="high",
                reason="Covered by 8/10 competitors",
                competitor_coverage=8,
            ),
            TopicCoverage(
                topic="Cost and insurance",
                priority="high",
                reason="High search volume",
                competitor_coverage=7,
            ),
        ],
        total_topics=2,
        questions_to_answer=[
            QuestionToAnswer(
                question="How long do dental implants last?",
                priority="high",
                source="user intent",
            ),
        ],
        total_questions=1,
        competitor_avg_word_count=1850,
        competitor_urls=["competitor1.com", "competitor2.com"],
        top_performing_competitor="competitor1.com",
        title_suggestions=[
            "Complete Guide to Dental Implants in 2026",
            "Dental Implants: Everything You Need to Know",
        ],
        meta_description_suggestion="Learn everything about dental implants: types, costs, procedure, and recovery. Expert guide for 2026.",
    )


@pytest.fixture
def sample_quality_report():
    """Sample quality report."""
    return ContentQualityReport(
        url="https://example.com",
        timestamp=datetime.now().isoformat(),
        readability=ReadabilityAnalysis(
            flesch_reading_ease=65.0,
            flesch_kincaid_grade=8.0,
            avg_sentence_length=15.0,
            avg_word_length=5.0,
            complex_words_percent=10.0,
            readability_level="medium",
            issues=["Some long sentences"],
            recommendations=["Break up long sentences"],
        ),
        grammar=GrammarAnalysis(
            total_errors=2,
            spelling_errors=1,
            grammar_errors=1,
            punctuation_errors=0,
            style_issues=0,
            error_rate=0.5,
            issues=[
                {"type": "spelling", "text": "Typo in line 5"},
                {"type": "grammar", "text": "Missing comma in line 10"},
            ],
            recommendations=["Fix typo", "Add comma"],
        ),
        uniqueness=UniquenessAnalysis(
            uniqueness_score=95.0,
            duplicate_phrases=[],
            plagiarism_detected=False,
            ai_generated_probability=10.0,
            issues=[],
            recommendations=[],
        ),
        eeat=EEATAnalysis(
            experience_score=80.0,
            expertise_score=85.0,
            authoritativeness_score=75.0,
            trustworthiness_score=90.0,
            overall_eeat_score=82.5,
            signals_found=["author bio", "citations"],
            missing_signals=["credentials"],
            recommendations=["Include expert quotes"],
        ),
        depth=ContentDepthAnalysis(
            word_count=2000,
            topic_coverage_score=85.0,
            subtopics_covered=5,
            subtopics_missing=["case studies"],
            has_examples=True,
            has_data=True,
            has_visuals=True,
            depth_level="comprehensive",
            recommendations=["Add patient testimonials"],
        ),
        engagement=EngagementAnalysis(
            hook_strength=75.0,
            storytelling_score=70.0,
            emotional_appeal=65.0,
            call_to_action_present=True,
            multimedia_usage=60.0,
            engagement_score=72.5,
            recommendations=["Start with compelling question"],
        ),
        overall_quality_score=80.0,
        quality_grade="B+",
        priority_issues=[
            "Fix 2 grammar errors",
            "Add more author credentials",
            "Strengthen opening hook",
        ],
        quick_wins=[
            "Fix typos",
            "Add expert quote",
        ],
    )


@pytest.fixture
def sample_calendar_report():
    """Sample calendar report."""
    return ContentCalendarReport(
        period="month",
        generated_at=datetime.now().isoformat(),
        calendar_items=[
            ContentItem(
                content_id="content-001",
                title="Dental Implants Guide",
                content_type="blog",
                status="scheduled",
                author="John Doe",
                target_keyword="dental implants",
                scheduled_date="2026-05-20",
                publish_channel="blog",
                priority="high",
                word_count=2000,
                estimated_hours=4.0,
            )
        ],
        channel_schedules=[
            ChannelSchedule(
                channel="blog",
                frequency="weekly",
                optimal_times=["09:00", "14:00"],
                next_slot="2026-05-21T09:00:00",
                capacity=4,
                current_load=1,
            )
        ],
        content_gaps=[
            ContentGap(
                topic="Dental care",
                keyword="dental implants cost",
                priority="medium",
                reason="High search volume, no content",
                suggested_type="blog",
                estimated_traffic=1000,
            )
        ],
        deadline_alerts=[],
        metrics=CalendarMetrics(
            total_items=1,
            published_count=0,
            scheduled_count=1,
            draft_count=0,
            overdue_count=0,
            completion_rate=100.0,
            avg_production_time=4.0,
            channel_distribution={"blog": 1},
        ),
        recommendations=["Schedule content for gap period"],
    )


@pytest.mark.asyncio
async def test_calculate_overall_score_with_quality(magister, sample_brief, sample_quality_report, sample_calendar_report):
    """Test overall score calculation with quality report."""
    score = magister._calculate_overall_score(
        sample_brief,
        sample_quality_report,
        sample_calendar_report,
    )

    # Brief: 2 headers * 10 + 2 topics * 5 + 1 question * 5 = 35 (40% weight = 14.0)
    # Quality: 80.0 (40% weight = 32.0)
    # Calendar: 100 - 1 gap * 10 = 90 (20% weight = 18.0)
    # Total: 14.0 + 32.0 + 18.0 = 64.0
    assert 60.0 <= score <= 70.0


@pytest.mark.asyncio
async def test_calculate_overall_score_without_quality(magister, sample_brief, sample_calendar_report):
    """Test overall score calculation without quality report."""
    score = magister._calculate_overall_score(
        sample_brief,
        None,
        sample_calendar_report,
    )

    # Brief: 35 (60% weight = 21.0)
    # Calendar: 90 (40% weight = 36.0)
    # Total: 21.0 + 36.0 = 57.0
    assert 50.0 <= score <= 65.0


@pytest.mark.asyncio
async def test_generate_priority_actions(magister, sample_brief, sample_quality_report, sample_calendar_report):
    """Test priority actions generation."""
    actions = magister._generate_priority_actions(
        sample_brief,
        sample_quality_report,
        sample_calendar_report,
    )

    assert isinstance(actions, list)
    assert len(actions) <= 5
    # Should include word count target
    assert any("2000 words" in action for action in actions)
    # Should include quality issues
    assert any("grammar" in action.lower() for action in actions)
    # Should include gap
    assert any("gap" in action.lower() for action in actions)


@pytest.mark.asyncio
async def test_estimate_effort_low(magister):
    """Test effort estimation for short content."""
    brief = ContentBrief(
        target_keyword="test",
        timestamp=datetime.now().isoformat(),
        search_volume=0,
        keyword_difficulty=0.0,
        search_intent="unknown",
        recommended_word_count=300,
        word_count_range=(250, 350),
        tone="",
        header_structure=[],
        topics_to_cover=[],
        total_topics=0,
        questions_to_answer=[],
        total_questions=0,
        competitor_avg_word_count=0,
        competitor_urls=[],
        top_performing_competitor=None,
        title_suggestions=[],
        meta_description_suggestion="",
    )

    effort = magister._estimate_effort(brief, None)
    assert effort == "low"


@pytest.mark.asyncio
async def test_estimate_effort_medium(magister):
    """Test effort estimation for medium content."""
    brief = ContentBrief(
        target_keyword="test",
        timestamp=datetime.now().isoformat(),
        search_volume=0,
        keyword_difficulty=0.0,
        search_intent="unknown",
        recommended_word_count=1000,
        word_count_range=(900, 1100),
        tone="",
        header_structure=[],
        topics_to_cover=[],
        total_topics=0,
        questions_to_answer=[],
        total_questions=0,
        competitor_avg_word_count=0,
        competitor_urls=[],
        top_performing_competitor=None,
        title_suggestions=[],
        meta_description_suggestion="",
    )

    effort = magister._estimate_effort(brief, None)
    assert effort == "medium"


@pytest.mark.asyncio
async def test_estimate_effort_high(magister):
    """Test effort estimation for long content."""
    brief = ContentBrief(
        target_keyword="test",
        timestamp=datetime.now().isoformat(),
        search_volume=0,
        keyword_difficulty=0.0,
        search_intent="unknown",
        recommended_word_count=3000,
        word_count_range=(2800, 3200),
        tone="",
        header_structure=[],
        topics_to_cover=[],
        total_topics=0,
        questions_to_answer=[],
        total_questions=0,
        competitor_avg_word_count=0,
        competitor_urls=[],
        top_performing_competitor=None,
        title_suggestions=[],
        meta_description_suggestion="",
    )

    effort = magister._estimate_effort(brief, None)
    assert effort == "high"


@pytest.mark.asyncio
async def test_execute_workflow_structure(magister):
    """Test workflow execution returns correct structure."""
    report = await magister.execute_workflow(
        topic="Dental Implants",
        target_keyword="dental implants",
    )

    assert isinstance(report, ContentWorkflowReport)
    assert report.topic == "Dental Implants"
    assert isinstance(report.generated_at, str)
    assert isinstance(report.duration_seconds, float)
    assert isinstance(report.content_brief, ContentBrief)
    assert report.quality_check is None  # No content provided
    assert isinstance(report.calendar_planning, ContentCalendarReport)
    assert 0 <= report.overall_score <= 100
    assert isinstance(report.priority_actions, list)
    assert report.estimated_effort in ["low", "medium", "high"]
    assert report.workflow_status in ["success", "partial", "failed"]
    assert isinstance(report.errors, list)


@pytest.mark.asyncio
async def test_execute_brief_generation_only(magister):
    """Test executing only brief generation phase."""
    brief = await magister.execute_brief_generation_only(
        target_keyword="dental implants",
        competitor_urls=[],
    )

    assert isinstance(brief, ContentBrief)
    assert brief.target_keyword == "dental implants"


@pytest.mark.asyncio
async def test_execute_quality_check_only(magister):
    """Test executing only quality check phase."""
    report = await magister.execute_quality_check_only(
        content="This is a test content about dental implants. " * 50,
        target_keyword="dental implants",
    )

    assert isinstance(report, ContentQualityReport)
    assert 0 <= report.overall_quality_score <= 100


@pytest.mark.asyncio
async def test_execute_calendar_planning_only(magister):
    """Test executing only calendar planning phase."""
    report = await magister.execute_calendar_planning_only(
        period="month",
    )

    assert isinstance(report, ContentCalendarReport)


@pytest.mark.asyncio
async def test_workflow_with_errors_partial_status(magister, monkeypatch):
    """Test workflow continues with partial status when one phase fails."""
    # Mock brief generator to raise exception
    async def mock_generate(*args, **kwargs):
        raise Exception("API error")

    monkeypatch.setattr(magister.brief_generator, "generate", mock_generate)

    report = await magister.execute_workflow(
        topic="Dental Implants",
        target_keyword="dental implants",
    )

    assert report.workflow_status == "partial"
    assert len(report.errors) > 0
    assert any("Content Brief Generation failed" in error for error in report.errors)


@pytest.mark.asyncio
async def test_workflow_priority_actions_limit(magister, sample_brief, sample_quality_report, sample_calendar_report):
    """Test priority actions are limited to top 5."""
    # Create quality report with many issues
    quality_with_many_issues = ContentQualityReport(
        url="https://example.com",
        timestamp=datetime.now().isoformat(),
        readability=sample_quality_report.readability,
        grammar=sample_quality_report.grammar,
        uniqueness=sample_quality_report.uniqueness,
        eeat=sample_quality_report.eeat,
        depth=sample_quality_report.depth,
        engagement=sample_quality_report.engagement,
        overall_quality_score=50.0,
        quality_grade="C",
        priority_issues=[f"Issue {i}" for i in range(10)],  # 10 issues
        quick_wins=[],
    )

    actions = magister._generate_priority_actions(
        sample_brief,
        quality_with_many_issues,
        sample_calendar_report,
    )

    assert len(actions) <= 5
