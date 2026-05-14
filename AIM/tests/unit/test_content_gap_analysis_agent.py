"""Unit tests for Content Gap Analysis Agent

Tests gap detection, competitor analysis, and brief generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from meai.agents.base_agent import Task, TaskStatus
from src.aim.subagents.content_gap_analysis_agent import ContentGapAnalysisAgent
from src.aim.subagents.schemas.content_gap_analysis import ScrapedPageData, EEATScores
from src.aim.subagents.schemas.content_gap import ContentGap, GapType, GapSeverity


@pytest.fixture
def content_gap_agent(tmp_path):
    """Create Content Gap Analysis Agent with mocked components"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    agent = ContentGapAnalysisAgent(
        agent_id="test-content-gap-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path=str(vault_path),
    )

    return agent


@pytest.fixture
def mock_client_pages():
    """Mock client pages with E-E-A-T scores"""
    return [
        {
            "url": "https://oursite.com/dental-implants",
            "title": "Dental Implants Guide",
            "topic": 0,  # Topic cluster 0
            "eeat_score": 0.75,
        },
        {
            "url": "https://oursite.com/implant-cost",
            "title": "Implant Cost",
            "topic": 1,  # Topic cluster 1
            "eeat_score": 0.70,
        },
    ]


@pytest.fixture
def mock_competitor_pages():
    """Mock competitor pages with E-E-A-T scores"""
    return [
        {
            "url": "https://competitor.com/dental-implants",
            "title": "Dental Implants Complete Guide",
            "topic": 0,  # Same topic as client
            "eeat_score": 0.80,
        },
        {
            "url": "https://competitor.com/implant-cost",
            "title": "Implant Cost Breakdown",
            "topic": 1,  # Same topic as client
            "eeat_score": 0.78,
        },
        {
            "url": "https://competitor.com/recovery-time",
            "title": "Recovery Time After Implants",
            "topic": 2,  # Missing topic (gap!)
            "eeat_score": 0.82,
        },
        {
            "url": "https://competitor.com/aftercare",
            "title": "Dental Implant Aftercare",
            "topic": 3,  # Missing topic (gap!)
            "eeat_score": 0.85,
        },
    ]


@pytest.fixture
def mock_topic_clusters():
    """Mock topic clusters"""
    return [
        {"cluster_id": 0, "name": "Dental Implants Basics", "count": 2},
        {"cluster_id": 1, "name": "Cost and Pricing", "count": 2},
        {"cluster_id": 2, "name": "Recovery and Healing", "count": 1},
        {"cluster_id": 3, "name": "Aftercare and Maintenance", "count": 1},
    ]


@pytest.mark.asyncio
async def test_gap_detection_success(content_gap_agent, mock_client_pages, mock_competitor_pages, mock_topic_clusters):
    """Test content gap detection through SERP overlap"""
    # Mock gap detector
    mock_gap_detector = AsyncMock()

    # Mock topic gaps (topics 2 and 3 are missing from client)
    topic_gaps = [
        ContentGap(
            missing_keyword="recovery time",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.HIGH,
            search_volume=3000,
            opportunity_score=0.85,
            competitor_coverage={"competitor.com": True},
            target_keywords=["recovery time", "healing time"],
            recommended_content_type="blog_post",
            estimated_traffic_potential=3000,
        ),
        ContentGap(
            missing_keyword="aftercare",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.HIGH,
            search_volume=2500,
            opportunity_score=0.82,
            competitor_coverage={"competitor.com": True},
            target_keywords=["aftercare", "post-surgery care"],
            recommended_content_type="blog_post",
            estimated_traffic_potential=2500,
        ),
    ]

    mock_gap_detector.detect_topic_gaps.return_value = topic_gaps
    mock_gap_detector.detect_url_gaps.return_value = []
    mock_gap_detector.detect_keyword_gaps.return_value = []

    # Inject mock
    content_gap_agent.gap_detector = mock_gap_detector

    # Mock other components to avoid initialization
    content_gap_agent.web_scraper = AsyncMock()
    content_gap_agent.eeat_scorer = MagicMock()
    content_gap_agent.embeddings_generator = MagicMock()
    content_gap_agent.topic_clusterer = MagicMock()
    content_gap_agent.cluster_analyzer = MagicMock()
    content_gap_agent.opportunity_scorer = AsyncMock()

    # Mock _scrape_site to return test data
    async def mock_scrape_site(url: str, max_pages: int, is_client: bool):
        if is_client:
            # Return client pages as ScrapedPageData
            return [
                ScrapedPageData(
                    url=p["url"],
                    title=p["title"],
                    body_text="Test content " * 50,
                    headings=["Test heading"],
                    word_count=500,
                    readability_score=8.0,
                    content_type="blog_post",
                    has_https=True,
                    has_contact_info=True,
                    has_privacy_policy=True,
                    eeat_scores=EEATScores(
                        experience_score=0.7,
                        expertise_score=0.7,
                        authoritativeness_score=0.7,
                        trustworthiness_score=0.8,
                        overall_score=p["eeat_score"],
                        quality_tier="good",
                        recommendations=[],
                    ),
                    is_client_content=True,
                    scraped_at=datetime.now(timezone.utc),
                )
                for p in mock_client_pages
            ]
        else:
            # Return competitor pages as ScrapedPageData
            return [
                ScrapedPageData(
                    url=p["url"],
                    title=p["title"],
                    body_text="Test content " * 50,
                    headings=["Test heading"],
                    word_count=500,
                    readability_score=8.0,
                    content_type="blog_post",
                    has_https=True,
                    has_contact_info=True,
                    has_privacy_policy=True,
                    eeat_scores=EEATScores(
                        experience_score=0.8,
                        expertise_score=0.8,
                        authoritativeness_score=0.8,
                        trustworthiness_score=0.9,
                        overall_score=p["eeat_score"],
                        quality_tier="excellent",
                        recommendations=[],
                    ),
                    is_client_content=False,
                    scraped_at=datetime.now(timezone.utc),
                )
                for p in mock_competitor_pages
            ]

    content_gap_agent._scrape_site = mock_scrape_site

    # Mock embeddings and clustering
    content_gap_agent.embeddings_generator.generate_embeddings.return_value = [[0.1] * 384] * 6
    content_gap_agent.topic_clusterer.fit_transform.return_value = ([0, 1, 0, 1, 2, 3], [0.9] * 6)
    content_gap_agent.topic_clusterer.get_all_topics.return_value = {
        0: {"topic_id": 0, "name": "Dental Implants Basics", "count": 2},
        1: {"topic_id": 1, "name": "Cost and Pricing", "count": 2},
        2: {"topic_id": 2, "name": "Recovery and Healing", "count": 1},
        3: {"topic_id": 3, "name": "Aftercare and Maintenance", "count": 1},
    }
    content_gap_agent.cluster_analyzer.analyze_clusters.return_value = {
        "quality_classification": "good",
        "silhouette_score": 0.65,
    }

    # Mock opportunity scorer
    content_gap_agent.opportunity_scorer.score_gaps.return_value = topic_gaps

    # Create task
    task = Task(
        task_id="test-gap-001",
        subtask_id="test-gap-001-sub",
        parent_task_id="test-gap-001-parent",
        action="content_gap_analysis",
        description="Test gap detection",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://oursite.com",
            "competitor_urls": ["https://competitor.com"],
            "niche": "dental implants",
            "max_pages_per_site": 10,
            "min_content_quality": 0.5,
        },
    )

    # Execute
    result = await content_gap_agent.execute_task(task)

    # Verify success
    assert result.status == "completed"
    assert "gaps" in result.result

    # Verify gap detection
    gaps = result.result["gaps"]
    assert len(gaps) >= 2

    # Verify missing keywords identified
    missing_keywords = [g["missing_keyword"] for g in gaps]
    assert "recovery time" in missing_keywords
    assert "aftercare" in missing_keywords

    # Verify gap types
    gap_types = [g["gap_type"] for g in gaps]
    assert "missing_topic" in gap_types

    # Verify opportunity scores
    for gap in gaps:
        assert "opportunity_score" in gap
        assert 0.0 <= gap["opportunity_score"] <= 1.0

    await content_gap_agent.close()


@pytest.mark.asyncio
async def test_competitor_content_analysis(content_gap_agent):
    """Test competitor content quality analysis"""
    # Mock web scraper
    mock_web_scraper = AsyncMock()
    mock_web_scraper.scrape_page.return_value = {
        "url": "https://competitor.com/dental-implants-guide",
        "title": "Complete Guide to Dental Implants",
        "body_text": "Dental implants are artificial tooth roots. " * 50,
        "headings": ["What are dental implants?", "Cost breakdown", "Procedure steps"],
        "author_name": "Dr. Jane Smith",
        "author_credentials": "DDS, Board Certified",
        "is_doctor_authored": True,
        "citations": ["https://pubmed.ncbi.nlm.nih.gov/12345"],
        "word_count": 2500,
        "readability_score": 8.5,
        "content_type": "service_page",
        "has_https": True,
        "has_contact_info": True,
        "has_privacy_policy": True,
    }

    # Mock E-E-A-T scorer
    mock_eeat_scorer = MagicMock()
    mock_eeat_scorer.score_content.return_value = EEATScores(
        experience_score=0.85,
        expertise_score=0.90,
        authoritativeness_score=0.80,
        trustworthiness_score=0.95,
        overall_score=0.88,
        quality_tier="excellent",
        recommendations=["Add more patient testimonials", "Include more citations"],
    )

    # Inject mocks
    content_gap_agent.web_scraper = mock_web_scraper
    content_gap_agent.eeat_scorer = mock_eeat_scorer

    # Mock other components
    content_gap_agent.embeddings_generator = MagicMock()
    content_gap_agent.topic_clusterer = MagicMock()
    content_gap_agent.cluster_analyzer = MagicMock()
    content_gap_agent.gap_detector = AsyncMock()
    content_gap_agent.opportunity_scorer = AsyncMock()

    # Mock _scrape_site to use our mocked scraper
    async def mock_scrape_site(url: str, max_pages: int, is_client: bool):
        scraped = await content_gap_agent.web_scraper.scrape_page(url)
        eeat_scores = content_gap_agent.eeat_scorer.score_content(
            title=scraped["title"],
            body_text=scraped["body_text"],
            author_name=scraped["author_name"],
            author_credentials=scraped["author_credentials"],
            is_doctor_authored=scraped["is_doctor_authored"],
            citations=scraped["citations"],
            word_count=scraped["word_count"],
            has_https=scraped["has_https"],
            has_contact_info=scraped["has_contact_info"],
            has_privacy_policy=scraped["has_privacy_policy"],
        )

        return [
            ScrapedPageData(
                url=scraped["url"],
                title=scraped["title"],
                body_text=scraped["body_text"],
                headings=scraped["headings"],
                author_name=scraped["author_name"],
                author_credentials=scraped["author_credentials"],
                is_doctor_authored=scraped["is_doctor_authored"],
                citations=scraped["citations"],
                word_count=scraped["word_count"],
                readability_score=scraped["readability_score"],
                content_type=scraped["content_type"],
                has_https=scraped["has_https"],
                has_contact_info=scraped["has_contact_info"],
                has_privacy_policy=scraped["has_privacy_policy"],
                eeat_scores=eeat_scores,
                is_client_content=is_client,
                scraped_at=datetime.now(timezone.utc),
            )
        ]

    content_gap_agent._scrape_site = mock_scrape_site

    # Mock remaining components
    # Need 2 embeddings: 1 for client, 1 for competitor
    content_gap_agent.embeddings_generator.generate_embeddings.return_value = [[0.1] * 384, [0.2] * 384]
    content_gap_agent.topic_clusterer.fit_transform.return_value = ([0, 0], [0.9, 0.9])
    content_gap_agent.topic_clusterer.get_all_topics.return_value = {
        0: {"topic_id": 0, "name": "Dental Implants", "count": 2}
    }
    content_gap_agent.cluster_analyzer.analyze_clusters.return_value = {
        "quality_classification": "excellent",
        "silhouette_score": 0.85,
    }
    content_gap_agent.gap_detector.detect_topic_gaps.return_value = []
    content_gap_agent.gap_detector.detect_url_gaps.return_value = []
    content_gap_agent.gap_detector.detect_keyword_gaps.return_value = []
    content_gap_agent.opportunity_scorer.score_gaps.return_value = []

    # Create task
    task = Task(
        task_id="test-gap-002",
        subtask_id="test-gap-002-sub",
        parent_task_id="test-gap-002-parent",
        action="competitor_analysis",
        description="Test competitor analysis",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "competitor_urls": ["https://competitor.com/dental-implants-guide"],
            "niche": "dental implants",
            "max_pages_per_site": 1,
        },
    )

    # Execute
    result = await content_gap_agent.execute_task(task)

    # Verify success
    assert result.status == "completed"

    # Verify scraper was called
    assert mock_web_scraper.scrape_page.called

    # Verify E-E-A-T scorer was called
    assert mock_eeat_scorer.score_content.called

    # Verify quality metrics in result
    assert "competitor_pages_analyzed" in result.result
    assert result.result["competitor_pages_analyzed"] >= 1
    assert "cluster_quality" in result.result
    assert result.result["cluster_quality"] == "excellent"

    await content_gap_agent.close()


@pytest.mark.asyncio
async def test_brief_generation(content_gap_agent):
    """Test content brief generation from gaps"""
    # Mock gap data
    gaps = [
        ContentGap(
            missing_keyword="recovery time",
            gap_type=GapType.MISSING_KEYWORD,
            severity=GapSeverity.HIGH,
            search_volume=3000,
            opportunity_score=0.85,
            competitor_coverage={"competitor1.com": True, "competitor2.com": True},
            target_keywords=["recovery time", "healing time", "post-surgery recovery"],
            recommended_content_type="blog_post",
            estimated_traffic_potential=3000,
            recommended_actions=[
                "Create comprehensive recovery guide",
                "Include timeline infographic",
                "Add patient testimonials",
            ],
        ),
        ContentGap(
            missing_keyword="aftercare",
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.MEDIUM,
            search_volume=2000,
            opportunity_score=0.75,
            competitor_coverage={"competitor1.com": True},
            target_keywords=["aftercare", "post-surgery care", "maintenance"],
            recommended_content_type="blog_post",
            estimated_traffic_potential=2000,
            recommended_actions=[
                "Create aftercare checklist",
                "Include dos and don'ts",
                "Add care product recommendations",
            ],
        ),
    ]

    # Mock all components
    content_gap_agent.web_scraper = AsyncMock()
    content_gap_agent.eeat_scorer = MagicMock()
    content_gap_agent.embeddings_generator = MagicMock()
    content_gap_agent.topic_clusterer = MagicMock()
    content_gap_agent.cluster_analyzer = MagicMock()
    content_gap_agent.gap_detector = AsyncMock()
    content_gap_agent.opportunity_scorer = AsyncMock()

    # Mock _scrape_site
    async def mock_scrape_site(url: str, max_pages: int, is_client: bool):
        return [
            ScrapedPageData(
                url=url,
                title="Test Page",
                body_text="Test content " * 50,
                headings=["Test"],
                word_count=500,
                readability_score=8.0,
                content_type="blog_post",
                has_https=True,
                has_contact_info=True,
                has_privacy_policy=True,
                eeat_scores=EEATScores(
                    experience_score=0.7,
                    expertise_score=0.7,
                    authoritativeness_score=0.7,
                    trustworthiness_score=0.8,
                    overall_score=0.75,
                    quality_tier="good",
                    recommendations=[],
                ),
                is_client_content=is_client,
                scraped_at=datetime.now(timezone.utc),
            )
        ]

    content_gap_agent._scrape_site = mock_scrape_site

    # Mock components
    content_gap_agent.embeddings_generator.generate_embeddings.return_value = [[0.1] * 384] * 2
    content_gap_agent.topic_clusterer.fit_transform.return_value = ([0, 1], [0.9, 0.9])
    content_gap_agent.topic_clusterer.get_all_topics.return_value = {
        0: {"topic_id": 0, "name": "Recovery", "count": 1},
        1: {"topic_id": 1, "name": "Aftercare", "count": 1},
    }
    content_gap_agent.cluster_analyzer.analyze_clusters.return_value = {
        "quality_classification": "good",
        "silhouette_score": 0.70,
    }
    content_gap_agent.gap_detector.detect_topic_gaps.return_value = gaps
    content_gap_agent.gap_detector.detect_url_gaps.return_value = []
    content_gap_agent.gap_detector.detect_keyword_gaps.return_value = []
    content_gap_agent.opportunity_scorer.score_gaps.return_value = gaps

    # Create task
    task = Task(
        task_id="test-gap-003",
        subtask_id="test-gap-003-sub",
        parent_task_id="test-gap-003-parent",
        action="brief_generation",
        description="Test brief generation",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "competitor_urls": ["https://competitor.com"],
            "niche": "dental implants",
            "target_word_count": 2000,
        },
    )

    # Execute
    result = await content_gap_agent.execute_task(task)

    # Verify success
    assert result.status == "completed"
    assert "gaps" in result.result

    # Verify brief structure (gaps contain recommended actions)
    gaps_result = result.result["gaps"]
    assert len(gaps_result) >= 2

    # Verify gap keywords integrated
    gap_keywords = [g["missing_keyword"] for g in gaps_result]
    assert "recovery time" in gap_keywords
    assert "aftercare" in gap_keywords

    # Verify recommended actions (brief guidelines)
    for gap in gaps_result:
        assert "recommended_actions" in gap
        assert len(gap["recommended_actions"]) > 0
        assert "target_keywords" in gap
        assert len(gap["target_keywords"]) > 0
        assert "recommended_content_type" in gap
        assert "estimated_traffic_potential" in gap

    # Verify severity (quality guidelines)
    # Note: priority is a @property, not serialized in model_dump()
    severities = [g["severity"] for g in gaps_result]
    assert "high" in severities or "medium" in severities

    # Verify gap types
    gap_types = [g["gap_type"] for g in gaps_result]
    assert "missing_keyword" in gap_types or "missing_topic" in gap_types

    await content_gap_agent.close()
