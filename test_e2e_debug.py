"""Debug E2E test with detailed logging"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from meai.agents.operator import Operator
from meai.agents.magisters.intelligence_magister import IntelligenceMagister
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.magisters.ads_magister import AdsMagister
from meai.agents.magisters.analytics_magister import AnalyticsMagister
from meai.agents.magisters.social_magister import SocialMagister
from meai.agents.base_agent import Task

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# Focus on specific loggers
logging.getLogger('meai.agents.magisters.content_magister').setLevel(logging.DEBUG)
logging.getLogger('meai.agents.operator').setLevel(logging.INFO)
logging.getLogger('meai.events.event_bus').setLevel(logging.DEBUG)


async def test_e2e_debug():
    """E2E test with detailed logging"""

    print("\n" + "="*80)
    print("E2E DEBUG TEST - Focus on Content Magister")
    print("="*80)

    # Use persistent DB
    db_path = "data/test_e2e_debug.db"
    Path(db_path).unlink(missing_ok=True)

    # Initialize Operator
    operator = Operator(
        database_url=f"sqlite+aiosqlite:///./{db_path}",
        vault_path="./test_vault"
    )
    await operator.initialize()
    print("✅ Operator initialized")

    # Initialize only Content Magister for focused debugging
    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url=f"sqlite+aiosqlite:///./{db_path}"
    )
    print("✅ Content Magister initialized")

    # Create simple task (using Operator's Task, not base_agent.Task)
    from meai.agents.operator import Task as OperatorTask, TaskStatus as OperatorTaskStatus

    task = OperatorTask(
        task_id="task-e2e-debug-001",
        source="user",
        goal="Launch medical marketing campaign",
        description="Test campaign for dental clinic",
        constraints=["budget < 10000", "time < 1 month"],
        resources={"target": "dental clinic", "niche": "dentistry", "geo": "Moscow"},
        priority=1,
        deadline=None,
        status=OperatorTaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print("\n" + "="*80)
    print("STEP 1: Operator receives and analyzes task")
    print("="*80)

    await operator.receive_task(task)
    print("✅ Task received and analyzed")

    # Check plan
    plan = operator.active_plans.get(task.task_id)
    if plan:
        print(f"   Subtasks created: {len(plan.subtasks)}")

        # Show all subtasks
        print(f"\n   All subtasks:")
        for st in plan.subtasks:
            print(f"      - {st.action} → {st.agent_id} (subtask_id={st.subtask_id})")

        # Find Content Magister subtasks
        content_subtasks = [
            st for st in plan.subtasks
            if st.agent_id == "content-magister-1"
        ]
        print(f"\n   Content Magister subtasks: {len(content_subtasks)}")
        for st in content_subtasks:
            print(f"      - {st.action} (subtask_id={st.subtask_id})")

    print("\n" + "="*80)
    print("STEP 2: Content Magister polls and executes")
    print("="*80)

    # Poll Content Magister
    await content_magister.poll_and_process_tasks()
    print("✅ Content Magister polled")

    print("\n" + "="*80)
    print("STEP 3: Operator polls for results")
    print("="*80)

    # Poll Operator multiple times
    for i in range(5):
        print(f"   Poll {i+1}/5...")
        await operator.poll_and_collect_results()
        await asyncio.sleep(0.2)

    print("✅ Operator polled")

    print("\n" + "="*80)
    print("STEP 4: Check results")
    print("="*80)

    # Get results
    results = await operator._collect_subtask_results(task.task_id)
    print(f"   Total subtasks: {len(results)}")

    # Check Content Magister results
    content_results = [
        r for r in results
        if r.get('agent_id') == 'content-magister-1'
    ]
    print(f"   Content Magister results: {len(content_results)}")

    for r in content_results:
        action = r.get('action', 'unknown')
        status = r.get('result', {}).get('status', 'unknown')
        has_result = bool(r.get('result'))
        print(f"      - {action}: status={status}, has_result={has_result}")

    # Cleanup
    await operator.shutdown()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_e2e_debug())
