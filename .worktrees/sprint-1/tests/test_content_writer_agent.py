"""Content Writer Agent Test - Real content generation logic

Tests Content Writer Agent with real content structure generation.
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.subagents.content_writer_agent import ContentWriterAgent
from meai.agents.base_agent import Task, TaskStatus
from datetime import datetime, timezone


class TestContentWriterAgent:
    """Content Writer Agent tests"""

    @pytest.mark.asyncio
    async def test_content_generation_blog_post(self):
        """Test Content Writer Agent generates blog post structure"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content_writer.db"

        agent = ContentWriterAgent(
            agent_id="test-content-writer",
            database_url=database_url,
        )

        await agent.initialize()

        try:
            task = Task(
                task_id="test-1",
                subtask_id="test-sub-1",
                parent_task_id="test-parent-1",
                action="write_blog_post",
                description='Write blog post about "dental implants"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await agent.execute_task(task)

            # Validate result
            assert result.status == "success"
            assert result.result["content_type"] == "blog_post"
            assert result.result["topic"] == "dental implants"
            assert result.result["specialty"] == "dentistry"
            assert len(result.result["structure"]) > 0
            assert result.result["quality_score"] > 0
            assert result.result["readability_score"] > 0
            assert result.result["seo_score"] > 0

            print("\n✅ Content generation works!")
            print(f"\n📝 Generated Content:")
            print(f"   Type: {result.result['content_type']}")
            print(f"   Topic: {result.result['topic']}")
            print(f"   Specialty: {result.result['specialty']}")
            print(f"   Sections: {len(result.result['structure'])}")
            print(f"   Word count: {result.result['word_count']}")
            print(f"   Quality: {result.result['quality_score']}/100")
            print(f"   Readability: {result.result['readability_score']}/100")
            print(f"   SEO: {result.result['seo_score']}/100")

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_content_structure_details(self):
        """Test Content Writer Agent generates detailed structure"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content_writer.db"

        agent = ContentWriterAgent(
            agent_id="test-content-writer",
            database_url=database_url,
        )

        await agent.initialize()

        try:
            task = Task(
                task_id="test-2",
                subtask_id="test-sub-2",
                parent_task_id="test-parent-2",
                action="create_content",
                description='Create article about "laser skin treatment"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await agent.execute_task(task)

            # Validate structure
            assert result.status == "success"
            structure = result.result["structure"]
            assert len(structure) > 0

            # Check each section has required fields
            for section in structure:
                assert "section" in section
                assert "title" in section
                assert "estimated_words" in section
                assert "key_points" in section
                assert len(section["key_points"]) > 0

            print("\n✅ Content structure is detailed!")
            print(f"\n📋 Structure Details:")
            for i, section in enumerate(structure, 1):
                print(f"\n   Section {i}: {section['section']}")
                print(f"   Title: {section['title']}")
                print(f"   Words: {section['estimated_words']}")
                print(f"   Key points: {len(section['key_points'])}")

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_recommendations_generation(self):
        """Test Content Writer Agent generates recommendations"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_content_writer.db"

        agent = ContentWriterAgent(
            agent_id="test-content-writer",
            database_url=database_url,
        )

        await agent.initialize()

        try:
            task = Task(
                task_id="test-3",
                subtask_id="test-sub-3",
                parent_task_id="test-parent-3",
                action="write_article",
                description='Write article about "botox treatment"',
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await agent.execute_task(task)

            # Validate recommendations
            assert result.status == "success"
            assert "recommendations" in result.result
            assert len(result.result["recommendations"]) > 0

            print("\n✅ Recommendations generated!")
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(result.result["recommendations"], 1):
                print(f"   {i}. {rec}")

        finally:
            await agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
