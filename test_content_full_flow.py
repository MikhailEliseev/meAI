"""Test full Content Magister flow with Operator"""

import asyncio
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

from meai.agents.operator import Operator
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.base_agent import Task


async def test_full_flow():
    """Test Content Magister with Operator delegation"""

    # Use persistent DB
    db_path = "data/test_full_flow.db"
    Path(db_path).unlink(missing_ok=True)

    print("\n" + "="*80)
    print("STEP 1: Initialize Operator and Content Magister")
    print("="*80)

    operator = Operator(
        database_url=f"sqlite+aiosqlite:///./{db_path}",
        vault_path="./test_vault"
    )
    await operator.initialize()

    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url=f"sqlite+aiosqlite:///./{db_path}"
    )

    print("✅ Initialized")

    print("\n" + "="*80)
    print("STEP 2: Create task and delegate to Content Magister")
    print("="*80)

    # Create task like Operator does
    task = Task(
        task_id="task-001",
        subtask_id="task-001",
        parent_task_id="task-001",
        action="generate_content",
        description="Generate blog post about dental implants",
        priority=1,
        status="received",
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "target": "dental implants",
            "niche": "dentistry",
            "geo": "Moscow"
        }
    )

    # Store subtask in DB (like Operator does)
    from meai.agents.operator import Subtask, TaskStatus
    subtask = Subtask(
        subtask_id="subtask-001",
        parent_task_id="task-001",
        agent_id="content-magister-1",
        action="generate_content",
        description="Generate blog post about dental implants",
        dependencies=[],
        priority=1,
        status=TaskStatus.DELEGATED,
        result=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
        data={
            "target": "dental implants",
            "niche": "dentistry",
            "geo": "Moscow"
        }
    )

    await operator._store_subtask(subtask)
    print("✅ Subtask stored in DB")

    # Delegate to Content Magister via Event Bus
    await operator.magister_coordinator.delegate_to_magister(subtask)
    print("✅ Delegated to Content Magister")

    print("\n" + "="*80)
    print("STEP 3: Content Magister polls and executes")
    print("="*80)

    # Content Magister polls for tasks
    await content_magister.poll_and_process_tasks()
    print("✅ Content Magister polled")

    # Wait for execution
    await asyncio.sleep(0.5)

    print("\n" + "="*80)
    print("STEP 4: Operator polls for results")
    print("="*80)

    # Operator polls for results
    for i in range(5):
        await operator.poll_and_collect_results()
        await asyncio.sleep(0.2)

    print("✅ Operator polled")

    print("\n" + "="*80)
    print("STEP 5: Check DB")
    print("="*80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check subtask
    cursor.execute("""
        SELECT subtask_id, action, status, result
        FROM operator_subtasks
        WHERE subtask_id = 'subtask-001'
    """)

    row = cursor.fetchone()
    if row:
        print(f"\n✅ Subtask in DB:")
        print(f"   subtask_id: {row[0]}")
        print(f"   action: {row[1]}")
        print(f"   status: {row[2]}")
        if row[3]:
            result = json.loads(row[3])
            print(f"   result keys: {list(result.keys())}")
            print(f"   result['status']: {result.get('status', 'NOT FOUND')}")
        else:
            print(f"   result: None")
    else:
        print(f"\n❌ Subtask NOT FOUND in DB!")

    # Check EventBus messages
    cursor.execute("""
        SELECT message_type, status, payload
        FROM event_bus_messages
        WHERE message_type IN ('magister_task', 'task_result')
        ORDER BY created_at DESC
        LIMIT 5
    """)

    print(f"\n📨 EventBus messages:")
    for row in cursor.fetchall():
        msg_type, status, payload = row
        payload_dict = json.loads(payload) if payload else {}
        print(f"   {msg_type} ({status}): subtask_id={payload_dict.get('subtask_id', 'N/A')}")

    conn.close()

    await operator.shutdown()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_full_flow())
