"""
Test Agent Learning Integration with CI System
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "AIM" / "src"))
sys.path.insert(0, str(project_root / "src"))

from aim.core.agent_learning import AgentLearning


async def test_agent_learning():
    """Test Agent Learning system"""

    print("=" * 80)
    print("TEST: Agent Learning Integration")
    print("=" * 80)

    # Test 1: Read lessons
    print("\n" + "=" * 80)
    print("TEST 1: Read Lessons from Obsidian")
    print("=" * 80)

    learning = AgentLearning(agent_id="test-agent")

    lessons = await learning.get_lessons(
        tags=["validation", "ci-system"],
        severity="critical"
    )

    print(f"\n✅ Found {len(lessons)} lessons")
    for lesson in lessons:
        print(f"\n📚 Lesson: {lesson['title']}")
        print(f"   Severity: {lesson['severity']}")
        print(f"   Tags: {', '.join(lesson['tags'])}")
        print(f"   Prevention Rules: {len(lesson['prevention_rules'])}")

        for i, rule in enumerate(lesson['prevention_rules'][:3], 1):
            print(f"     {i}. {rule['type']}: {rule['rule'][:80]}...")

    # Test 2: Extract prevention rules
    print("\n" + "=" * 80)
    print("TEST 2: Extract Prevention Rules")
    print("=" * 80)

    rules = learning.extract_prevention_rules(lessons)
    print(f"\n✅ Extracted {len(rules)} prevention rules")

    for i, rule in enumerate(rules[:5], 1):
        print(f"  {i}. {rule['type']}: {rule['rule'][:80]}...")

    # Test 3: Apply lessons to task
    print("\n" + "=" * 80)
    print("TEST 3: Apply Lessons to Task")
    print("=" * 80)

    from meai.agents.base_agent import Task

    task = Task(
        task_id="test-task",
        subtask_id="test-task-1",
        parent_task_id="test-parent",
        action="validate_urls",
        description="Test task for learning",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )

    applied = await learning.apply_lessons(task, lessons)

    print(f"\n✅ Applied lessons:")
    print(f"   Lessons count: {applied['lessons_count']}")
    print(f"   Rules applied: {len(applied['rules_applied'])}")
    print(f"   Recommendations: {len(applied['recommendations'])}")

    for rec in applied['recommendations']:
        print(f"   • {rec}")

    # Test 4: Record success
    print("\n" + "=" * 80)
    print("TEST 4: Record Success")
    print("=" * 80)

    await learning.record_success(
        task=task,
        result={"status": "ok"},
        metrics={
            "quality_score": 85.0,
            "duration": 10.5
        }
    )

    print(f"\n✅ Success recorded")
    print(f"   Total tasks: {learning.history['total_tasks']}")
    print(f"   Total successes: {learning.history['total_successes']}")
    print(f"   Lessons applied: {len(learning.history['lessons_applied'])}")

    # Test 5: Record failure
    print("\n" + "=" * 80)
    print("TEST 5: Record Failure")
    print("=" * 80)

    try:
        raise ValueError("Test error")
    except Exception as e:
        await learning.record_failure(
            task=task,
            error=e,
            context={"test": True}
        )

    print(f"\n✅ Failure recorded")
    print(f"   Total tasks: {learning.history['total_tasks']}")
    print(f"   Total failures: {learning.history['total_failures']}")

    # Test 6: Check learning history
    print("\n" + "=" * 80)
    print("TEST 6: Learning History")
    print("=" * 80)

    print(f"\n📊 Learning History:")
    print(f"   Agent ID: {learning.history['agent_id']}")
    print(f"   Total tasks: {learning.history['total_tasks']}")
    print(f"   Successes: {learning.history['total_successes']}")
    print(f"   Failures: {learning.history['total_failures']}")
    print(f"   Success rate: {learning.history['total_successes'] / learning.history['total_tasks'] * 100:.1f}%")
    print(f"   Lessons applied: {len(learning.history['lessons_applied'])}")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_agent_learning())
