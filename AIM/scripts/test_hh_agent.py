"""Test HH Agent with real competitors."""

import asyncio
from datetime import datetime
from pathlib import Path

from aim.agents.ci_swarm.hh_agent import Competitor, HHAgent
from meai.agents.base_agent import Task, TaskStatus


async def main():
    """Test HH Agent."""
    # Define competitors (example: major IT companies in Russia)
    competitors = [
        Competitor(
            employer_id="1740",  # Яндекс
            name="Яндекс",
            industry="IT",
            website="https://yandex.ru",
        ),
        Competitor(
            employer_id="3529",  # Сбер
            name="Сбер",
            industry="IT/Finance",
            website="https://sber.ru",
        ),
        Competitor(
            employer_id="3776",  # VK
            name="VK",
            industry="IT",
            website="https://vk.company",
        ),
    ]

    # Initialize agent
    vault_path = str(Path(__file__).parent.parent / "obsidian" / "ci-hh")
    database_url = "sqlite+aiosqlite:///./data/aim.db"

    agent = HHAgent(
        agent_id="hh-agent-001",
        database_url=database_url,
        vault_path=vault_path,
        competitors=competitors,
    )

    print("🔍 HH Agent initialized")
    print(f"📁 Vault: {vault_path}")
    print(f"🎯 Monitoring {len(competitors)} competitors:")
    for c in competitors:
        print(f"   - {c.name} (ID: {c.employer_id})")
    print()

    # Test 1: Monitor competitors
    print("=" * 60)
    print("TEST 1: Monitor Competitors")
    print("=" * 60)

    task1 = Task(
        task_id="task-001",
        subtask_id="subtask-001",
        parent_task_id="parent-001",
        action="monitor_competitors",
        description="Collect vacancy snapshots from all competitors",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
    )

    result1 = await agent.execute_task(task1)
    print(f"Status: {result1.status}")
    print(f"Result: {result1.result}")
    print()

    # Test 2: Detect changes (will work after second run)
    print("=" * 60)
    print("TEST 2: Detect Changes")
    print("=" * 60)

    task2 = Task(
        task_id="task-002",
        subtask_id="subtask-002",
        parent_task_id="parent-001",
        action="detect_changes",
        description="Detect changes between snapshots",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
    )

    result2 = await agent.execute_task(task2)
    print(f"Status: {result2.status}")
    print(f"Result: {result2.result}")
    print()

    # Test 3: Generate report
    print("=" * 60)
    print("TEST 3: Generate Report")
    print("=" * 60)

    task3 = Task(
        task_id="task-003",
        subtask_id="subtask-003",
        parent_task_id="parent-001",
        action="generate_report",
        description="Generate weekly CI report",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now(),
    )

    result3 = await agent.execute_task(task3)
    print(f"Status: {result3.status}")
    print(f"Result: {result3.result}")
    print()

    print("✅ All tests completed!")
    print()
    print("📊 Check results:")
    print(f"   - Snapshots: {vault_path}/raw/snapshots/")
    print(f"   - Reports: {vault_path}/wiki/insights/")
    print(f"   - Alerts: {vault_path}/wiki/alerts/")


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
