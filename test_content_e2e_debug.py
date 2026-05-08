"""Debug Content Magister in E2E scenario with persistent DB"""

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from meai.agents.operator import Operator
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.base_agent import Task, TaskStatus


async def test_content_e2e():
    """Test Content Magister in E2E scenario with DB inspection"""

    # Use persistent DB for debugging
    db_path = "data/test_content_e2e.db"
    Path(db_path).unlink(missing_ok=True)  # Clean start

    # Initialize Operator
    operator = Operator(
        database_url=f"sqlite+aiosqlite:///./{db_path}",
        vault_path="./test_vault"
    )
    await operator.initialize()

    # Initialize Content Magister
    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url=f"sqlite+aiosqlite:///./{db_path}"
    )

    # Create task
    task = Task(
        task_id="task-001",
        subtask_id="subtask-001",
        parent_task_id="task-001",
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

    print("\n" + "="*80)
    print("STEP 1: Content Magister executes task")
    print("="*80)

    # Execute task
    result = await content_magister.execute_task(task)

    print(f"\n✅ Task executed")
    print(f"   Status: {result.status}")
    print(f"   Error: {result.error}")
    print(f"   Result keys: {list(result.result.keys())}")
    print(f"   Result['status']: {result.result.get('status', 'NOT FOUND')}")

    print("\n" + "="*80)
    print("STEP 2: Content Magister reports result to Operator")
    print("="*80)

    # Report result (this is what BaseMagister does)
    from meai.events.event_bus import Message

    message = Message(
        from_agent="content-magister-1",
        to_agent="operator",
        message_type="task_result",
        priority=1,
        payload={
            "subtask_id": result.subtask_id,
            "parent_task_id": "task-001",
            "status": result.status,
            "result": result.result,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    await operator.event_bus.publish(message)
    print(f"✅ Message published to EventBus")

    print("\n" + "="*80)
    print("STEP 3: Operator polls for results")
    print("="*80)

    # Poll for results
    await operator.poll_and_collect_results()
    await asyncio.sleep(0.1)
    await operator.poll_and_collect_results()

    print(f"✅ Polling complete")

    print("\n" + "="*80)
    print("STEP 4: Check DB directly")
    print("="*80)

    # Check DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subtask_id, action, status, result
        FROM operator_subtasks
        WHERE subtask_id = 'subtask-001'
    """)

    row = cursor.fetchone()
    if row:
        print(f"\n✅ Found in DB:")
        print(f"   subtask_id: {row[0]}")
        print(f"   action: {row[1]}")
        print(f"   status: {row[2]}")
        print(f"   result: {row[3][:200] if row[3] else 'None'}...")
    else:
        print(f"\n❌ NOT FOUND in DB!")

    # Check EventBus messages
    cursor.execute("""
        SELECT message_id, message_type, status, payload
        FROM event_bus_messages
        WHERE message_type = 'task_result'
        ORDER BY created_at DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    if row:
        print(f"\n✅ EventBus message:")
        print(f"   message_id: {row[0]}")
        print(f"   message_type: {row[1]}")
        print(f"   status: {row[2]}")
        print(f"   payload: {row[3][:200] if row[3] else 'None'}...")
    else:
        print(f"\n❌ No EventBus messages!")

    conn.close()

    # Cleanup
    await operator.shutdown()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_content_e2e())
