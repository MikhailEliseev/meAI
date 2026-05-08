"""E2E test with detailed logging to find Content Magister error"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta

from meai.agents.operator import Operator, Task, TaskStatus
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.magisters.ads_magister import AdsMagister
from meai.agents.magisters.seo_magister import SEOMagister

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout
)

# Focus on specific modules
logging.getLogger('meai.agents.magisters.base_magister').setLevel(logging.DEBUG)
logging.getLogger('meai.agents.magisters.content_magister').setLevel(logging.DEBUG)
logging.getLogger('meai.agents.operator').setLevel(logging.INFO)
logging.getLogger('meai.events.event_bus').setLevel(logging.INFO)


async def test_e2e_with_logging():
    """E2E test with detailed logging"""
    
    print("\n" + "="*80)
    print("E2E TEST WITH DETAILED LOGGING")
    print("="*80)
    
    # Initialize
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault"
    )
    await operator.initialize()
    
    # Initialize only Content and Ads Magisters for comparison
    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:"
    )
    
    ads_magister = AdsMagister(
        agent_id="ads-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:"
    )
    
    print("✅ Initialized")
    
    # Create task like real E2E test
    task = Task(
        task_id="task-e2e-log-001",
        source="user",
        goal="Launch complete medical marketing campaign for new clinic",
        description="""
        Launch comprehensive marketing campaign for new medical clinic:
        
        1. CONTENT: Create 5 blog posts about medical services
        2. ADS: Set up Google Ads campaign with $5000 budget
        
        All tasks must be coordinated and executed in parallel.
        """,
        constraints=["budget < 10000", "time < 2 weeks"],
        resources={
            "budget": 8000,
            "target": "new dental clinic",
            "niche": "dentistry",
            "geo": "Moscow"
        },
        priority=0,
        deadline=datetime.now(timezone.utc) + timedelta(days=14),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    print("\n" + "="*80)
    print("STEP 1: Operator receives task")
    print("="*80)
    
    await operator.receive_task(task)
    
    plan = operator.active_plans.get(task.task_id)
    print(f"\n✅ Plan created: {len(plan.subtasks)} subtasks")
    
    # Show Content and Ads subtasks
    content_subtasks = [st for st in plan.subtasks if st.agent_id == "content-magister-1"]
    ads_subtasks = [st for st in plan.subtasks if st.agent_id == "ads-magister-1"]
    
    print(f"   Content Magister: {len(content_subtasks)} subtasks")
    for st in content_subtasks:
        print(f"      - {st.action} (id={st.subtask_id})")
    
    print(f"   Ads Magister: {len(ads_subtasks)} subtasks")
    for st in ads_subtasks:
        print(f"      - {st.action} (id={st.subtask_id})")
    
    print("\n" + "="*80)
    print("STEP 2: Magisters execute in parallel")
    print("="*80)
    
    # Execute in parallel like real E2E test
    print("\n🔄 Starting parallel execution...")
    await asyncio.gather(
        content_magister.poll_and_process_tasks(),
        ads_magister.poll_and_process_tasks()
    )
    print("✅ Parallel execution complete")
    
    print("\n" + "="*80)
    print("STEP 3: Operator collects results")
    print("="*80)
    
    # Poll multiple times
    for i in range(10):
        await operator.poll_and_collect_results()
        await asyncio.sleep(0.1)
    
    print("✅ Results collected")
    
    print("\n" + "="*80)
    print("STEP 4: Check results")
    print("="*80)
    
    results = await operator._collect_subtask_results(task.task_id)
    
    content_results = [r for r in results if r.get('agent_id') == 'content-magister-1']
    ads_results = [r for r in results if r.get('agent_id') == 'ads-magister-1']
    
    print(f"\n📊 Content Magister results: {len(content_results)}")
    for r in content_results:
        action = r.get('action')
        status = r.get('result', {}).get('status', 'unknown')
        has_result = bool(r.get('result'))
        print(f"   - {action}: status={status}, has_result={has_result}")
    
    print(f"\n📊 Ads Magister results: {len(ads_results)}")
    for r in ads_results:
        action = r.get('action')
        status = r.get('result', {}).get('status', 'unknown')
        has_result = bool(r.get('result'))
        print(f"   - {action}: status={status}, has_result={has_result}")
    
    await operator.shutdown()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_e2e_with_logging())
