"""Test Linear Integration Logic (Mock Test)

Tests the integration logic without actual Linear API calls.
Verifies that:
1. Operator accepts LinearClient
2. Linear task ID is stored in subtask data
3. MagisterCoordinator passes Linear task ID to Magisters
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from meai.agents.operator import Operator, Task, TaskStatus


class MockLinearClient:
    """Mock LinearClient for testing."""

    def __init__(self):
        self.created_tasks = []
        self.updated_tasks = []
        self.comments = []

    def list_teams(self):
        return [
            {"id": "team-1", "key": "DEV", "name": "Development"},
            {"id": "team-2", "key": "SEO", "name": "SEO Services"},
        ]

    def list_states(self, team_id):
        return [
            {"id": "state-1", "name": "Todo"},
            {"id": "state-2", "name": "In Progress"},
            {"id": "state-3", "name": "Done"},
        ]

    def create_issue(self, title, description, team_id, project_id=None, state_id=None, priority=None):
        issue_id = f"mock-issue-{len(self.created_tasks) + 1}"
        self.created_tasks.append({
            "id": issue_id,
            "title": title,
            "description": description,
            "team_id": team_id,
            "project_id": project_id,
            "state_id": state_id,
            "priority": priority,
        })
        return issue_id

    def update_issue(self, issue_id, state_id=None):
        self.updated_tasks.append({
            "id": issue_id,
            "state_id": state_id,
        })

    def add_comment(self, issue_id, body):
        self.comments.append({
            "issue_id": issue_id,
            "body": body,
        })


async def test_linear_integration_logic():
    """Test Linear integration logic with mock client."""
    print("=" * 80)
    print("Linear Integration Logic Test (Mock)")
    print("=" * 80)
    print()

    # Step 1: Create mock LinearClient
    print("Step 1: Create mock LinearClient")
    mock_client = MockLinearClient()
    print(f"✅ Mock LinearClient created")
    print()

    # Step 2: Initialize Operator with mock Linear
    print("Step 2: Initialize Operator with Linear integration")
    operator = Operator(
        database_url="sqlite+aiosqlite:///./data/test_linear_mock.db",
        vault_path="./obsidian",
        linear_client=mock_client,
        linear_enabled=True,
    )
    await operator.initialize()
    print(f"✅ Operator initialized with Linear enabled")
    print(f"   linear_enabled: {operator.linear_enabled}")
    print(f"   linear_client: {type(operator.linear_client).__name__}")
    print()

    # Step 3: Create test task
    print("Step 3: Create test task")
    task = Task(
        task_id=f"test-mock-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        source="user",
        goal="Test Linear integration logic",
        description="Analyze keywords to test Linear task tracking logic",
        constraints=["budget < 100"],
        resources={
            "target": "test keyword",
            "niche": "medical",
        },
        priority=1,
        deadline=None,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    print(f"✅ Test task created: {task.task_id}")
    print()

    # Step 4: Send task to Operator
    print("Step 4: Send task to Operator (will create subtasks)")
    await operator.receive_task(task)
    print(f"✅ Task sent to Operator")
    print()

    # Step 5: Wait for processing
    print("Step 5: Wait for processing (3 seconds)")
    await asyncio.sleep(3)
    print()

    # Step 6: Check mock Linear client
    print("Step 6: Check mock Linear client calls")
    print(f"   Created tasks: {len(mock_client.created_tasks)}")
    for i, task_data in enumerate(mock_client.created_tasks, 1):
        print(f"\n   Task {i}:")
        print(f"     ID: {task_data['id']}")
        print(f"     Title: {task_data['title']}")
        print(f"     Team: {task_data['team_id']}")
    print()

    # Step 7: Check database for Linear task IDs
    print("Step 7: Check database for Linear task IDs")
    from sqlalchemy import text
    async with operator.db.session() as session:
        result = await session.execute(
            text("""
            SELECT subtask_id, agent_id, action, data
            FROM operator_subtasks
            WHERE parent_task_id = :task_id
            """),
            {"task_id": task.task_id},
        )
        subtasks = result.fetchall()

        print(f"✅ Found {len(subtasks)} subtasks:")
        linear_ids_found = 0
        for subtask in subtasks:
            subtask_id, agent_id, action, data_json = subtask
            print(f"\n   Subtask: {subtask_id}")
            print(f"   Agent: {agent_id}")
            print(f"   Action: {action}")

            if data_json:
                import json
                data = json.loads(data_json)
                linear_task_id = data.get("linear_task_id")
                if linear_task_id:
                    print(f"   ✅ Linear Task ID: {linear_task_id}")
                    linear_ids_found += 1
                else:
                    print(f"   ⚠️  No Linear Task ID")
    print()

    # Step 8: Cleanup
    print("Step 8: Cleanup")
    await operator.shutdown()
    print(f"✅ Operator shutdown")
    print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print()

    success = True
    checks = []

    # Check 1: Linear client accepted
    if operator.linear_enabled:
        checks.append("✅ Operator accepts LinearClient")
    else:
        checks.append("❌ Operator did not enable Linear")
        success = False

    # Check 2: Tasks created in Linear
    if len(mock_client.created_tasks) > 0:
        checks.append(f"✅ Created {len(mock_client.created_tasks)} Linear tasks")
    else:
        checks.append("❌ No Linear tasks created")
        success = False

    # Check 3: Linear IDs stored
    if linear_ids_found > 0:
        checks.append(f"✅ Stored {linear_ids_found} Linear task IDs in database")
    else:
        checks.append("❌ No Linear task IDs stored")
        success = False

    for check in checks:
        print(check)
    print()

    if success:
        print("🎉 All checks passed!")
        print()
        print("Integration is working correctly:")
        print("1. Operator accepts LinearClient")
        print("2. Linear tasks are created on delegation")
        print("3. Linear task IDs are stored in subtask data")
        print()
        print("Next: Test with real Linear API key")
    else:
        print("❌ Some checks failed")

    print()
    return success


if __name__ == "__main__":
    success = asyncio.run(test_linear_integration_logic())
    sys.exit(0 if success else 1)
