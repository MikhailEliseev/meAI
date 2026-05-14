"""Unit tests for Content Writer Agent

Tests content generation, quality validation, and revision.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from meai.agents.base_agent import Task, TaskStatus
from AIM.src.aim.subagents.content_writer_agent import ContentWriterAgent
from tests.fixtures.subagent_fixtures import mock_api_clients, content_writer_agent


@pytest.mark.asyncio
async def test_content_generation_success(content_writer_agent, mock_api_clients):
    """Test content generation with SEO optimization"""
    # Mock OpenAI response
    mock_api_clients["openai"].generate.return_value = {
        "content": "Dental implants are a popular solution for missing teeth. The cost varies from $1,000 to $3,000 per implant...",
        "word_count": 500,
        "tokens_used": 650,
    }

    # Create task
    task = Task(
        task_id="test-writer-001",
        subtask_id="test-writer-001",
        parent_task_id="test-parent-001",
        action="create_content",
        description="Create article about dental implants cost",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "content_type": "article",
            "topic": "dental implants cost",
            "niche": "dentistry",
            "target_word_count": 1500,
            "tone": "professional",
        },
    )

    # Execute
    result = await content_writer_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert "structure" in result.result

    # Verify content structure generated
    structure = result.result["structure"]
    assert len(structure) > 0
    assert all("section" in s for s in structure)
    assert all("title" in s for s in structure)
    assert all("estimated_words" in s for s in structure)

    # Verify specialty detected
    assert result.result["specialty"] == "dentistry"

    # Verify metrics calculated
    assert "quality_score" in result.result
    assert "readability_score" in result.result
    assert "seo_score" in result.result
    assert result.result["quality_score"] > 0
    assert result.result["readability_score"] > 0
    assert result.result["seo_score"] > 0

    # Verify recommendations generated
    assert "recommendations" in result.result
    assert len(result.result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_content_quality_validation(content_writer_agent, mock_api_clients):
    """Test content quality validation"""
    # Create task for blog post
    task = Task(
        task_id="test-writer-002",
        subtask_id="test-writer-002",
        parent_task_id="test-parent-002",
        action="write_blog_post",
        description="Write blog post about teeth whitening",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "content_type": "blog_post",
            "topic": "teeth whitening",
            "niche": "cosmetic dentistry",
        },
    )

    # Execute
    result = await content_writer_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert "structure" in result.result

    # Verify quality metrics
    quality_score = result.result["quality_score"]
    readability_score = result.result["readability_score"]
    seo_score = result.result["seo_score"]

    # Verify scores are in valid range
    assert 0 <= quality_score <= 100
    assert 0 <= readability_score <= 100
    assert 0 <= seo_score <= 100

    # Verify structure quality
    structure = result.result["structure"]
    assert len(structure) >= 4  # Blog post should have multiple sections

    # Verify word count estimation
    word_count = result.result["word_count"]
    assert 800 <= word_count <= 1500  # Blog post range

    # Verify specialty detection
    assert result.result["specialty"] == "dentistry"


@pytest.mark.asyncio
async def test_content_revision(content_writer_agent, mock_api_clients):
    """Test content revision based on feedback"""
    # Mock OpenAI revision response
    mock_api_clients["openai"].generate.return_value = {
        "content": "Dental implants are a long-term solution for missing teeth. The cost typically ranges from $1,000 to $3,000 per implant, depending on the complexity of the procedure and materials used.",
        "word_count": 150,
        "tokens_used": 200,
    }

    # Create task for landing page
    task = Task(
        task_id="test-writer-003",
        subtask_id="test-writer-003",
        parent_task_id="test-parent-003",
        action="write_landing_page",
        description="Write landing page for dental implants",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "content_type": "landing_page",
            "topic": "dental implants",
            "niche": "implant dentistry",
        },
    )

    # Execute
    result = await content_writer_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert "structure" in result.result

    # Verify landing page structure
    structure = result.result["structure"]
    section_names = [s["section"] for s in structure]

    # Landing page should have specific sections
    assert "hero" in section_names
    assert "benefits" in section_names
    assert "cta" in section_names

    # Verify word count is appropriate for landing page
    word_count = result.result["word_count"]
    assert 500 <= word_count <= 1000  # Landing page range

    # Verify SEO optimization
    seo_score = result.result["seo_score"]
    assert seo_score > 60  # Should have decent SEO

    # Verify recommendations include actionable items
    recommendations = result.result["recommendations"]
    assert len(recommendations) > 0
    assert any("testimonial" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_service_description_generation(content_writer_agent, mock_api_clients):
    """Test service description content generation"""
    # Create task for service description
    task = Task(
        task_id="test-writer-004",
        subtask_id="test-writer-004",
        parent_task_id="test-parent-004",
        action="write_service_description",
        description="Write service description for laser eye surgery",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "content_type": "service_description",
            "topic": "laser eye surgery",
            "niche": "ophthalmology",
        },
    )

    # Execute
    result = await content_writer_agent.execute_task(task)

    # Verify success
    assert result.status == "success"

    # Verify specialty detection
    assert result.result["specialty"] == "ophthalmology"

    # Verify service description structure
    structure = result.result["structure"]
    section_names = [s["section"] for s in structure]

    # Service description should have specific sections
    assert "overview" in section_names
    assert "process" in section_names
    assert "benefits" in section_names
    assert "pricing" in section_names

    # Verify word count is appropriate
    word_count = result.result["word_count"]
    assert 600 <= word_count <= 1200  # Service description range

    # Verify quality metrics
    assert result.result["quality_score"] > 70
    assert result.result["readability_score"] > 0
    assert result.result["seo_score"] > 0


@pytest.mark.asyncio
async def test_medical_specialty_detection(content_writer_agent, mock_api_clients):
    """Test medical specialty detection from topic"""
    # Test different specialties
    test_cases = [
        ("dental implants", "dentistry"),
        ("botox treatment", "dermatology"),
        ("rhinoplasty procedure", "plastic_surgery"),
        ("lasik surgery", "ophthalmology"),
        ("general health tips", "general"),
    ]

    for topic, expected_specialty in test_cases:
        task = Task(
            task_id=f"test-specialty-{topic}",
            subtask_id=f"test-specialty-{topic}",
            parent_task_id=f"test-parent-specialty-{topic}",
            action="create_content",
            description=f"Create content about {topic}",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            data={
                "content_type": "article",
                "topic": topic,
                "niche": "",
            },
        )

        result = await content_writer_agent.execute_task(task)

        assert result.status == "success"
        assert result.result["specialty"] == expected_specialty, \
            f"Expected {expected_specialty} for topic '{topic}', got {result.result['specialty']}"


@pytest.mark.asyncio
async def test_error_handling(content_writer_agent, mock_api_clients):
    """Test error handling with invalid task data"""
    # Create task with missing required data
    task = Task(
        task_id="test-writer-error",
        subtask_id="test-writer-error",
        parent_task_id="test-parent-error",
        action="create_content",
        description="Test error handling with empty data",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={},  # Empty data
    )

    # Execute - should handle gracefully
    result = await content_writer_agent.execute_task(task)

    # Should still succeed with defaults
    assert result.status == "success"
    assert "structure" in result.result

    # Verify defaults were used
    assert result.result["content_type"] == "article"  # Default
    assert result.result["specialty"] == "general"  # Default when no topic match
