"""Integration test for Operator → Magisters → Operator flow"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from meai.agents.operator import Operator, Task, TaskStatus
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.magisters.ads_magister import AdsMagister


@pytest.mark.asyncio
async def test_operator_magisters_integration():
    """Test full Operator → Magisters → Operator flow

    Flow:
    1. Create Operator and Magisters
    2. Send task to Operator
    3. Operator delegates to Magisters
    4. Magisters poll and execute tasks
    5. Magisters report results back
    6. Operator collects results
    7. Operator aggregates report
    8. Verify complete flow
    """
    # 1. Create Operator
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault",
    )
    await operator.initialize()

    # 2. Create Magisters
    seo = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await seo.initialize()

    content = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await content.initialize()

    ads = AdsMagister(
        agent_id="ads-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await ads.initialize()

    # 3. Create and send task to Operator
    task = Task(
        task_id="task-integration-001",
        source="user",
        goal="Launch comprehensive marketing campaign",
        description="Create SEO strategy, generate content, and set up ads for medical marketing",
        constraints=["budget < 5000", "time < 1 week"],
        resources={"budget": 4500, "tools": ["ahrefs", "google-ads"]},
        priority=0,  # Critical
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # 4. Operator receives and delegates task
    await operator.receive_task(task)

    # Verify task was stored
    assert task.task_id in operator.active_tasks
    assert task.task_id in operator.active_plans

    plan = operator.active_plans[task.task_id]
    print(f"\n✅ Operator created plan: {plan.strategy.value}")
    print(f"   Subtasks: {len(plan.subtasks)}")
    print(f"   Agents: {list(plan.agent_assignments.keys())}")

    # 5. Magisters poll and execute tasks
    print("\n🔄 Magisters polling for tasks...")

    # Poll each magister
    await seo.poll_and_process_tasks()
    await content.poll_and_process_tasks()
    await ads.poll_and_process_tasks()

    print("✅ Magisters processed tasks")

    # 6. Operator collects results
    print("\n📊 Operator collecting results...")
    await operator.poll_and_collect_results()

    # 7. Wait a bit for async processing
    await asyncio.sleep(0.5)

    # 8. Verify results
    print("\n🔍 Verifying results...")

    # Check if task completed
    task_status = operator.active_tasks[task.task_id].status
    print(f"   Task status: {task_status.value}")

    # Check subtasks
    results = await operator._collect_subtask_results(task.task_id)
    print(f"   Subtasks completed: {len(results)}")

    for result in results:
        print(f"   - {result['action']} by {result['agent_id']}: {result['result'].get('status', 'unknown')}")

    # Verify at least some subtasks were created
    assert len(plan.subtasks) > 0, "No subtasks created"

    # Verify agents were assigned
    assert len(plan.agent_assignments) > 0, "No agents assigned"

    # Cleanup
    await operator.shutdown()
    await seo.shutdown()
    await content.shutdown()
    await ads.shutdown()

    print("\n✅ Integration test passed!")


@pytest.mark.asyncio
async def test_operator_single_magister():
    """Test Operator → Single Magister flow (simpler case)"""
    # Create Operator
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault",
    )
    await operator.initialize()

    # Create only SEO Magister
    seo = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await seo.initialize()

    # Simple SEO task
    task = Task(
        task_id="task-seo-001",
        source="user",
        goal="Analyze competitors for medical SEO",
        description="Analyze top 10 competitors in medical marketing space",
        constraints=["time < 2 hours"],
        resources={"tools": ["ahrefs"]},
        priority=1,
        deadline=datetime.now(timezone.utc) + timedelta(hours=2),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Operator delegates
    await operator.receive_task(task)

    # Verify delegation
    plan = operator.active_plans[task.task_id]
    assert plan.strategy.value in ["direct", "sequential", "parallel", "hybrid"], f"Unexpected strategy: {plan.strategy.value}"
    assert "seo-magister-1" in plan.agent_assignments

    print(f"\n✅ Single magister test: {plan.strategy.value} strategy")
    print(f"   Subtasks: {len(plan.subtasks)}")
    print(f"   Agents: {list(plan.agent_assignments.keys())}")

    # Magister processes
    await seo.poll_and_process_tasks()

    # Operator collects
    await operator.poll_and_collect_results()

    # Cleanup
    await operator.shutdown()
    await seo.shutdown()

    print("✅ Single magister test passed!")


if __name__ == "__main__":
    # Run tests
    print("=" * 60)
    print("Integration Test: Operator ↔ Magisters")
    print("=" * 60)

    asyncio.run(test_operator_magisters_integration())
    print("\n" + "=" * 60)
    asyncio.run(test_operator_single_magister())
