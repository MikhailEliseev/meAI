"""Debug Content Magister errors"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.base_agent import Task, TaskStatus
from meai.events.event_bus import EventBus

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_content_magister():
    """Test Content Magister with detailed error logging"""

    # Initialize
    event_bus = EventBus()
    magister = ContentMagister(
        agent_id="content-magister-test",
        event_bus=event_bus,
        database_url="sqlite+aiosqlite:///:memory:"
    )

    # Test 1: generate_content
    print("\n" + "="*80)
    print("TEST 1: generate_content")
    print("="*80)

    task1 = Task(
        task_id="test-001",
        subtask_id="subtask-001",
        parent_task_id="parent-001",
        action="generate_content",
        description="Generate blog post about dental implants",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "target": "dental implants",
            "niche": "dentistry",
            "geo": "Moscow"
        }
    )

    try:
        result1 = await magister.execute_task(task1)
        print(f"\n✅ Result: {result1.status}")
        print(f"   Error: {result1.error}")
        if result1.result:
            print(f"   Result keys: {list(result1.result.keys())}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: edit_content
    print("\n" + "="*80)
    print("TEST 2: edit_content")
    print("="*80)

    task2 = Task(
        task_id="test-002",
        subtask_id="subtask-002",
        parent_task_id="parent-002",
        action="edit_content",
        description="Edit content about teeth whitening",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "target": "teeth whitening",
            "niche": "dentistry",
            "geo": "Moscow"
        }
    )

    try:
        result2 = await magister.execute_task(task2)
        print(f"\n✅ Result: {result2.status}")
        print(f"   Error: {result2.error}")
        if result2.result:
            print(f"   Result keys: {list(result2.result.keys())}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: optimize_for_seo
    print("\n" + "="*80)
    print("TEST 3: optimize_for_seo")
    print("="*80)

    task3 = Task(
        task_id="test-003",
        subtask_id="subtask-003",
        parent_task_id="parent-003",
        action="optimize_for_seo",
        description="Optimize content for SEO",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "target": "orthodontics",
            "niche": "dentistry",
            "geo": "Moscow"
        }
    )

    try:
        result3 = await magister.execute_task(task3)
        print(f"\n✅ Result: {result3.status}")
        print(f"   Error: {result3.error}")
        if result3.result:
            print(f"   Result keys: {list(result3.result.keys())}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_content_magister())
