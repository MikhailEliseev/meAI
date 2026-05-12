"""Integration tests for Content Gap Analysis Agent

Tests the complete workflow:
1. Web scraping (client + competitors)
2. E-E-A-T scoring
3. Topic clustering
4. Gap detection
5. Opportunity scoring
6. Report generation
7. Obsidian integration
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from meai.agents.base_agent import Task, TaskStatus
from meai.events.event_bus import EventBus

from src.aim.subagents.content_gap_analysis_agent import ContentGapAnalysisAgent
from src.aim.subagents.schemas.content_gap_analysis import ScrapedPageData, EEATScores


@pytest.fixture
def mock_scraped_pages():
    """Mock scraped pages with E-E-A-T scores"""
    # Client pages (2 pages)
    client_pages = [
        ScrapedPageData(
            url="https://client.com/dental-implants",
            title="Dental Implants - Complete Guide",
            body_text="Dental implants are artificial tooth roots. " * 50,
            headings=["What are dental implants?", "Benefits", "Procedure"],
            author_name="Dr. John Smith",
            author_credentials="DDS, 15 years experience",
            is_doctor_authored=True,
            citations=["https://pubmed.ncbi.nlm.nih.gov/12345"],
            word_count=500,
            readability_score=8.5,
            content_type="service_page",
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            eeat_scores=EEATScores(
                experience_score=0.8,
                expertise_score=0.7,
                authoritativeness_score=0.6,
                trustworthiness_score=0.9,
                overall_score=0.75,
                quality_tier="good",
            ),
            is_client_content=True,
            scraped_at=datetime.now(timezone.utc),
        ),
        ScrapedPageData(
            url="https://client.com/implant-cost",
            title="Dental Implant Cost Guide",
            body_text="The cost of dental implants varies. " * 40,
            headings=["Cost factors", "Insurance coverage"],
            author_name="Dr. John Smith",
            author_credentials="DDS, 15 years experience",
            is_doctor_authored=True,
            citations=[],
            word_count=400,
            readability_score=9.0,
            content_type="blog_post",
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            eeat_scores=EEATScores(
                experience_score=0.7,
                expertise_score=0.6,
                authoritativeness_score=0.6,
                trustworthiness_score=0.9,
                overall_score=0.70,
                quality_tier="good",
            ),
            is_client_content=True,
            scraped_at=datetime.now(timezone.utc),
        ),
    ]

    # Competitor pages (4 pages, 2 per competitor)
    competitor_pages = [
        # Competitor 1
        ScrapedPageData(
            url="https://competitor1.com/all-on-4-implants",
            title="All-on-4 Dental Implants - Complete Solution",
            body_text="All-on-4 is a revolutionary technique. " * 60,
            headings=["What is All-on-4?", "Benefits", "Recovery time"],
            author_name="Dr. Jane Doe",
            author_credentials="DMD, Board Certified",
            is_doctor_authored=True,
            citations=["https://pubmed.ncbi.nlm.nih.gov/67890", "https://pubmed.ncbi.nlm.nih.gov/11111"],
            word_count=600,
            readability_score=8.0,
            content_type="service_page",
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            eeat_scores=EEATScores(
                experience_score=0.9,
                expertise_score=0.8,
                authoritativeness_score=0.7,
                trustworthiness_score=0.9,
                overall_score=0.83,
                quality_tier="excellent",
            ),
            is_client_content=False,
            scraped_at=datetime.now(timezone.utc),
        ),
        ScrapedPageData(
            url="https://competitor1.com/implant-recovery",
            title="Dental Implant Recovery Guide",
            body_text="Recovery from dental implants takes time. " * 50,
            headings=["Recovery timeline", "Pain management", "Diet"],
            author_name="Dr. Jane Doe",
            author_credentials="DMD, Board Certified",
            is_doctor_authored=True,
            citations=["https://pubmed.ncbi.nlm.nih.gov/22222"],
            word_count=500,
            readability_score=8.5,
            content_type="blog_post",
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            eeat_scores=EEATScores(
                experience_score=0.8,
                expertise_score=0.7,
                authoritativeness_score=0.7,
                trustworthiness_score=0.9,
                overall_score=0.78,
                quality_tier="good",
            ),
            is_client_content=False,
            scraped_at=datetime.now(timezone.utc),
        ),
        # Competitor 2
        ScrapedPageData(
            url="https://competitor2.com/implant-vs-bridge",
            title="Dental Implants vs Bridges - Which is Better?",
            body_text="Comparing dental implants and bridges. " * 55,
            headings=["Implants overview", "Bridges overview", "Comparison"],
            author_name="Dr. Bob Johnson",
            author_credentials="DDS, PhD",
            is_doctor_authored=True,
            citations=["https://pubmed.ncbi.nlm.nih.gov/33333"],
            word_count=550,
            readability_score=8.2,
            content_type="blog_post",
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            eeat_scores=EEATScores(
                experience_score=0.8,
                expertise_score=0.8,
                authoritativeness_score=0.7,
                trustworthiness_score=0.9,
                overall_score=0.80,
                quality_tier="excellent",
            ),
            is_client_content=False,
            scraped_at=datetime.now(timezone.utc),
        ),
        ScrapedPageData(
            url="https://competitor2.com/bone-grafting",
            title="Bone Grafting for Dental Implants",
            body_text="Bone grafting is sometimes necessary. " * 45,
            headings=["What is bone grafting?", "When needed", "Procedure"],
            author_name="Dr. Bob Johnson",
            author_credentials="DDS, PhD",
            is_doctor_authored=True,
            citations=["https://pubmed.ncbi.nlm.nih.gov/44444"],
            word_count=450,
            readability_score=8.8,
            content_type="service_page",
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            eeat_scores=EEATScores(
                experience_score=0.7,
                expertise_score=0.7,
                authoritativeness_score=0.7,
                trustworthiness_score=0.9,
                overall_score=0.75,
                quality_tier="good",
            ),
            is_client_content=False,
            scraped_at=datetime.now(timezone.utc),
        ),
    ]

    return client_pages, competitor_pages


@pytest.mark.asyncio
async def test_content_gap_analysis_end_to_end(mock_scraped_pages, tmp_path):
    """Test complete content gap analysis workflow"""
    client_pages, competitor_pages = mock_scraped_pages

    # Create agent with temp vault
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    agent = ContentGapAnalysisAgent(
        agent_id="test-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path=str(vault_path),
    )

    # Mock _scrape_site to return our test data
    async def mock_scrape_site(url: str, max_pages: int, is_client: bool):
        if is_client:
            return client_pages
        elif "competitor1" in url:
            return [competitor_pages[0], competitor_pages[1]]
        elif "competitor2" in url:
            return [competitor_pages[2], competitor_pages[3]]
        return []

    agent._scrape_site = mock_scrape_site

    # Create task
    from meai.agents.base_agent import TaskStatus
    task = Task(
        task_id="test-task-1",
        subtask_id="test-subtask-1",
        parent_task_id="test-parent-1",
        action="content_gap_analysis",
        description="Analyze content gaps for dental implants",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "competitor_urls": ["https://competitor1.com", "https://competitor2.com"],
            "niche": "dental implants",
            "max_pages_per_site": 10,
            "max_cost_usd": 1.0,
            "min_content_quality": 0.6,
        },
    )

    # Execute task
    result = await agent.execute_task(task)

    # Assertions
    assert result.status == "completed"
    assert "gaps" in result.result
    assert result.result["client_pages_analyzed"] == 2
    assert result.result["competitor_pages_analyzed"] == 4
    assert result.result["topics_discovered"] > 0

    # Check gaps were detected
    gaps = result.result["gaps"]
    assert len(gaps) > 0

    # Check gap structure
    gap = gaps[0]
    assert "topic" in gap
    assert "gap_type" in gap
    assert "opportunity_score" in gap
    assert "priority" in gap
    assert "severity" in gap

    # Check report was saved to vault
    reports_dir = vault_path / "wiki" / "reports" / "content-gap-analysis"
    assert reports_dir.exists()
    report_files = list(reports_dir.glob("*.md"))
    assert len(report_files) == 1

    # Check report content
    report_content = report_files[0].read_text()
    assert "Content Gap Analysis Report: dental implants" in report_content
    assert "Client pages analyzed: 2" in report_content
    assert "Competitor pages analyzed: 4" in report_content

    await agent.close()


@pytest.mark.asyncio
async def test_content_gap_analysis_quality_filtering(mock_scraped_pages, tmp_path):
    """Test that low-quality competitor pages are filtered out"""
    client_pages, competitor_pages = mock_scraped_pages

    # Add low-quality competitor page
    low_quality_page = ScrapedPageData(
        url="https://competitor3.com/spam",
        title="Buy cheap implants now!!!",
        body_text="Spam content. " * 20,
        headings=["Buy now"],
        author_name=None,
        author_credentials=None,
        is_doctor_authored=False,
        citations=[],
        word_count=100,
        readability_score=5.0,
        content_type="unknown",
        has_https=False,
        has_contact_info=False,
        has_privacy_policy=False,
        eeat_scores=EEATScores(
            experience_score=0.2,
            expertise_score=0.1,
            authoritativeness_score=0.1,
            trustworthiness_score=0.3,
            overall_score=0.18,  # Below 0.6 threshold
            quality_tier="poor",
        ),
        is_client_content=False,
        scraped_at=datetime.now(timezone.utc),
    )

    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    agent = ContentGapAnalysisAgent(
        agent_id="test-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path=str(vault_path),
    )

    # Mock _scrape_site
    async def mock_scrape_site(url: str, max_pages: int, is_client: bool):
        if is_client:
            return client_pages
        elif "competitor1" in url:
            return [competitor_pages[0], competitor_pages[1]]
        elif "competitor2" in url:
            return [competitor_pages[2], competitor_pages[3]]
        elif "competitor3" in url:
            return [low_quality_page]
        return []

    agent._scrape_site = mock_scrape_site

    # Create task with quality threshold
    task = Task(
        task_id="test-task-2",
        subtask_id="test-subtask-2",
        parent_task_id="test-parent-2",
        action="content_gap_analysis",
        description="Analyze content gaps with quality filtering",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "competitor_urls": [
                "https://competitor1.com",
                "https://competitor2.com",
                "https://competitor3.com",
            ],
            "niche": "dental implants",
            "max_pages_per_site": 10,
            "max_cost_usd": 1.0,
            "min_content_quality": 0.6,  # Filter out low-quality page
        },
    )

    # Execute task
    result = await agent.execute_task(task)

    # Assertions
    assert result.status == "completed"
    # Should only analyze 4 quality competitor pages (not the spam page)
    assert result.result["competitor_pages_analyzed"] == 4

    await agent.close()


@pytest.mark.asyncio
async def test_content_gap_analysis_missing_parameters(tmp_path):
    """Test that missing required parameters raise errors"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    agent = ContentGapAnalysisAgent(
        agent_id="test-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path=str(vault_path),
    )

    # Test missing client_url
    task = Task(
        task_id="test-task-3",
        subtask_id="test-subtask-3",
        parent_task_id="test-parent-3",
        action="content_gap_analysis",
        description="Test missing client_url",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "competitor_urls": ["https://competitor1.com"],
            "niche": "dental implants",
        },
    )

    result = await agent.execute_task(task)
    assert result.status == "failed"
    assert "client_url is required" in result.error

    # Test missing competitor_urls
    task = Task(
        task_id="test-task-4",
        subtask_id="test-subtask-4",
        parent_task_id="test-parent-4",
        action="content_gap_analysis",
        description="Test missing competitor_urls",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "niche": "dental implants",
        },
    )

    result = await agent.execute_task(task)
    assert result.status == "failed"
    assert "competitor_urls is required" in result.error

    # Test missing niche
    task = Task(
        task_id="test-task-5",
        subtask_id="test-subtask-5",
        parent_task_id="test-parent-5",
        action="content_gap_analysis",
        description="Test missing niche",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "competitor_urls": ["https://competitor1.com"],
        },
    )

    result = await agent.execute_task(task)
    assert result.status == "failed"
    assert "niche is required" in result.error

    await agent.close()


@pytest.mark.asyncio
async def test_content_gap_analysis_event_bus_integration(mock_scraped_pages, tmp_path):
    """Test Event Bus integration"""
    client_pages, competitor_pages = mock_scraped_pages

    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    # Create Event Bus
    event_bus = EventBus()

    # Create agent with Event Bus
    agent = ContentGapAnalysisAgent(
        agent_id="test-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path=str(vault_path),
        event_bus=event_bus,
    )

    # Mock _scrape_site
    async def mock_scrape_site(url: str, max_pages: int, is_client: bool):
        if is_client:
            return client_pages
        else:
            return competitor_pages

    agent._scrape_site = mock_scrape_site

    # Subscribe to events
    events_received = []

    async def event_handler(event):
        events_received.append(event)

    event_bus.subscribe("subagent.task.completed", event_handler)

    # Create task
    task = Task(
        task_id="test-task-6",
        subtask_id="test-subtask-6",
        parent_task_id="test-parent-6",
        action="content_gap_analysis",
        description="Test Event Bus integration",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "client_url": "https://client.com",
            "competitor_urls": ["https://competitor1.com"],
            "niche": "dental implants",
        },
    )

    # Execute task
    result = await agent.execute_task(task)

    # Assertions
    assert result.status == "completed"
    assert agent.event_bus is not None

    await agent.close()


@pytest.mark.asyncio
async def test_content_gap_analysis_capabilities():
    """Test agent capabilities"""
    agent = ContentGapAnalysisAgent(
        agent_id="test-agent",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    capabilities = agent.get_capabilities()

    assert "content_gap_analysis" in capabilities
    assert "web_scraping" in capabilities
    assert "eeat_scoring" in capabilities
    assert "topic_clustering" in capabilities
    assert "gap_detection" in capabilities
    assert "opportunity_scoring" in capabilities

    await agent.close()


@pytest.mark.asyncio
async def test_markdown_report_generation(mock_scraped_pages, tmp_path):
    """Test markdown report generation"""
    from src.aim.subagents.schemas.content_gap import ContentGap, GapAnalysisResult

    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    agent = ContentGapAnalysisAgent(
        agent_id="test-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path=str(vault_path),
    )

    # Create mock result
    gaps = [
        ContentGap(
            topic="All-on-4 dental implants",
            gap_type="missing_topic",
            severity="high",
            opportunity_score=85.5,
            priority="P0",
            competitor_coverage=[
                {"url": "https://competitor1.com/all-on-4", "traffic": 5000, "quality": 0.85}
            ],
            target_keywords=["all on 4 implants", "all on four"],
            recommended_content_type="service_page",
            estimated_traffic_potential=5000,
        ),
        ContentGap(
            topic="Dental implant recovery",
            gap_type="missing_topic",
            severity="medium",
            opportunity_score=72.3,
            priority="P1",
            competitor_coverage=[
                {"url": "https://competitor1.com/recovery", "traffic": 3000, "quality": 0.78}
            ],
            target_keywords=["implant recovery", "recovery time"],
            recommended_content_type="blog_post",
            estimated_traffic_potential=3000,
        ),
    ]

    result = GapAnalysisResult(
        gaps=gaps,
        client_pages_analyzed=2,
        competitor_pages_analyzed=4,
        topics_discovered=5,
        cluster_quality="good",
        analysis_time_seconds=45.2,
        cost_usd=0.0,
    )

    # Generate report
    await agent._save_to_vault(result, "dental implants")

    # Check report was created
    reports_dir = vault_path / "wiki" / "reports" / "content-gap-analysis"
    assert reports_dir.exists()

    report_files = list(reports_dir.glob("*.md"))
    assert len(report_files) == 1

    # Check report content
    report_content = report_files[0].read_text()
    assert "Content Gap Analysis Report: dental implants" in report_content
    assert "Client pages analyzed: 2" in report_content
    assert "Competitor pages analyzed: 4" in report_content
    assert "Topics discovered: 5" in report_content
    assert "P0 (High Priority): 1 gaps" in report_content
    assert "P1 (Medium Priority): 1 gaps" in report_content
    assert "All-on-4 dental implants" in report_content
    assert "Dental implant recovery" in report_content

    await agent.close()
