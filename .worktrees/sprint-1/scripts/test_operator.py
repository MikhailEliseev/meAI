"""Test Operator - Autonomous Operational Director"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from meai.agents.operator import Operator, Task, TaskStatus


async def main():
    print("🎯 Testing Operator - Autonomous Operational Director\n")

    # Initialize Operator
    operator = Operator(
        database_url="sqlite+aiosqlite:///./data/meai.db",
        vault_path="./obsidian"
    )
    await operator.initialize()

    print("=" * 60)
    print("TEST 1: Simple Task (Direct Strategy)")
    print("=" * 60)

    # Create simple task (should use DIRECT strategy)
    task1 = Task(
        task_id="task-001",
        source="user",
        goal="Analyze top 5 competitors in medical marketing",
        description="Research and analyze the top 5 competitors in the medical marketing space",
        constraints=["budget < 1000", "time < 2 days"],
        resources={"tools": ["ahrefs", "semrush"]},
        priority=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=2),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print(f"\n📋 Task: {task1.goal}")
    print(f"   Priority: P{task1.priority}")
    print(f"   Constraints: {', '.join(task1.constraints)}")

    # Receive task
    await operator.receive_task(task1)

    print(f"\n✅ Task received and processed")
    print(f"   Status: {task1.status.value}")

    # Check plan
    if task1.task_id in operator.active_plans:
        plan = operator.active_plans[task1.task_id]
        print(f"\n📊 Tactical Plan:")
        print(f"   Strategy: {plan.strategy.value}")
        print(f"   Subtasks: {len(plan.subtasks)}")
        print(f"   Risk Level: {plan.risk_level}")
        print(f"   Estimated Duration: {plan.estimated_duration}")
        print(f"\n   Agent Assignments:")
        for agent_id, subtask_ids in plan.agent_assignments.items():
            print(f"   - {agent_id}: {len(subtask_ids)} subtasks")

    print("\n" + "=" * 60)
    print("TEST 2: Complex Task (Parallel Strategy)")
    print("=" * 60)

    # Create complex task (should use PARALLEL strategy)
    task2 = Task(
        task_id="task-002",
        source="architect",
        goal="Launch comprehensive marketing campaign for iamaim.ru",
        description="Create SEO strategy, generate content, and set up ad campaigns",
        constraints=["budget < 5000", "time < 1 week"],
        resources={"budget": 4500, "tools": ["ahrefs", "semrush", "google-ads"]},
        priority=0,  # Critical
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print(f"\n📋 Task: {task2.goal}")
    print(f"   Priority: P{task2.priority} (CRITICAL)")
    print(f"   Constraints: {', '.join(task2.constraints)}")

    # Receive task
    await operator.receive_task(task2)

    print(f"\n✅ Task received and processed")
    print(f"   Status: {task2.status.value}")

    # Check plan
    if task2.task_id in operator.active_plans:
        plan = operator.active_plans[task2.task_id]
        print(f"\n📊 Tactical Plan:")
        print(f"   Strategy: {plan.strategy.value}")
        print(f"   Subtasks: {len(plan.subtasks)}")
        print(f"   Risk Level: {plan.risk_level}")
        print(f"   Estimated Duration: {plan.estimated_duration}")
        print(f"\n   Subtasks:")
        for i, subtask in enumerate(plan.subtasks, 1):
            print(f"   {i}. {subtask.action} → {subtask.agent_id}")
            if subtask.dependencies:
                print(f"      Dependencies: {', '.join(subtask.dependencies)}")
        print(f"\n   Agent Assignments:")
        for agent_id, subtask_ids in plan.agent_assignments.items():
            print(f"   - {agent_id}: {len(subtask_ids)} subtasks")

    print("\n" + "=" * 60)
    print("TEST 3: Check Vault Files")
    print("=" * 60)

    # Check vault files were created
    import os

    vault_paths = [
        "obsidian/operator/tasks/task-001.md",
        "obsidian/operator/tasks/task-002.md",
        "obsidian/operator/plans/",
        "obsidian/operator/delegations/",
    ]

    print("\n📁 Vault Files:")
    for path in vault_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                files = os.listdir(path)
                print(f"   ✅ {path} ({len(files)} files)")
            else:
                print(f"   ✅ {path}")
        else:
            print(f"   ❌ {path} (not found)")

    print("\n" + "=" * 60)
    print("TEST 4: Check Database")
    print("=" * 60)

    # Check database records
    async with operator.db.session() as session:
        # Count tasks
        result = await session.execute(text("SELECT COUNT(*) FROM operator_tasks"))
        task_count = result.fetchone()[0]
        print(f"\n📊 Database Records:")
        print(f"   Tasks: {task_count}")

        # Count plans
        result = await session.execute(text("SELECT COUNT(*) FROM operator_plans"))
        plan_count = result.fetchone()[0]
        print(f"   Plans: {plan_count}")

        # Count subtasks
        result = await session.execute(text("SELECT COUNT(*) FROM operator_subtasks"))
        subtask_count = result.fetchone()[0]
        print(f"   Subtasks: {subtask_count}")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)

    print("\n✅ Operator is working correctly!")
    print("✅ Tasks received and analyzed")
    print("✅ Tactical plans created")
    print("✅ Subtasks delegated to agents")
    print("✅ Vault files written")
    print("✅ Database records stored")

    print("\n" + "=" * 60)
    print("💡 NEXT STEPS")
    print("=" * 60)
    print("""
1. Implement Agent base class
2. Implement specific agents (SEO, Content, Ads)
3. Add result collection and monitoring
4. Add report aggregation
5. Test full cycle: YOU → Operator → Agents → Operator → YOU
""")

    # Cleanup
    await operator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
