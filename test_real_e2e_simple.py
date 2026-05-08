"""Simplified E2E test focusing on Content Magister"""

import asyncio
import logging
from datetime import datetime, timezone

from meai.agents.operator import Operator, Task, TaskStatus
from meai.agents.magisters.content_magister import ContentMagister

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_simple():
    """Simple E2E test"""
    
    # Initialize
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault"
    )
    await operator.initialize()
    
    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:"
    )
    
    # Create task like real E2E test
    task = Task(
        task_id="task-001",
        source="user",
        goal="Launch complete medical marketing campaign for new clinic",
        description="Create comprehensive marketing strategy",
        constraints=["budget < 10000", "time < 3 months", "focus on digital"],
        resources={
            "target": "new dental clinic",
            "niche": "dentistry",
            "geo": "Moscow",
            "budget": 8000
        },
        priority=1,
        deadline=None,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    # Operator receives task
    await operator.receive_task(task)
    
    plan = operator.active_plans.get(task.task_id)
    print(f"\n📋 Plan created:")
    print(f"   Subtasks: {len(plan.subtasks)}")
    
    # Count Content Magister tasks
    content_tasks = [st for st in plan.subtasks if st.agent_id == "content-magister-1"]
    print(f"   Content Magister tasks: {len(content_tasks)}")
    for st in content_tasks:
        print(f"      - {st.action}")
    
    # Execute Content Magister
    print(f"\n🔄 Content Magister executing...")
    await content_magister.poll_and_process_tasks()
    
    # Operator collects results
    print(f"\n📥 Operator collecting results...")
    for i in range(10):
        await operator.poll_and_collect_results()
        await asyncio.sleep(0.1)
    
    # Check results
    results = await operator._collect_subtask_results(task.task_id)
    content_results = [r for r in results if r.get('agent_id') == 'content-magister-1']
    
    print(f"\n📊 Results:")
    print(f"   Total: {len(results)}")
    print(f"   Content Magister: {len(content_results)}")
    
    for r in content_results:
        action = r.get('action')
        status = r.get('result', {}).get('status', 'unknown')
        has_error = bool(r.get('result', {}).get('error'))
        print(f"      - {action}: status={status}, error={has_error}")
    
    await operator.shutdown()


if __name__ == "__main__":
    asyncio.run(test_simple())
