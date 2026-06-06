"""
Test CI URL Validator with correct URL for 5th competitor
"""

import asyncio
from datetime import datetime

from src.aim.subagents.competitive_intel.agents.ci_url_validator import CIURLValidator
from meai.agents.base_agent import Task


async def test_url_validator():
    """Test URL Validator with real competitors including corrected 5th"""

    print("=" * 80)
    print("TEST: CI URL Validator")
    print("=" * 80)

    # Create validator
    validator = CIURLValidator(
        agent_id="ci-url-validator-test",
        database_url="sqlite+aiosqlite:///./AIM/data/meai.db",
        vault_path="./AIM/obsidian/ci-url-validator"
    )

    # Test competitors (including corrected 5th competitor)
    competitors = [
        {"name": "Tori Clinic", "url": "https://toriclinic.ru/"},
        {"name": "Professional Clinic", "url": "https://profclinic.ru/"},
        {"name": "CIDK", "url": "https://cidk.ru/"},
        {"name": "Frau Clinic", "url": "https://frauklinik.ru/"},
        {"name": "Клиника Юлии Щербатовой", "url": "https://juliasherbatova.ru/"}  # ✅ CORRECTED!
    ]

    # Create task (using correct Task structure from base_agent.py)
    task = Task(
        task_id="test-url-validation",
        subtask_id="test-url-validation-1",
        parent_task_id="test-parent",
        action="validate_urls",
        description="Test URL validation with corrected 5th competitor",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )

    # Add payload separately (not part of Task dataclass)
    task.payload = {"competitors": competitors}

    # Execute validation
    print("\n🔍 Starting URL validation...")
    result = await validator.execute_task(task)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    validated = result.result.get("validated", [])
    failed = result.result.get("failed", [])
    success_rate = result.result.get("success_rate", 0)

    print(f"\n✅ Validated: {len(validated)}/{len(competitors)}")
    for comp in validated:
        status_icon = "🔄" if comp.get("corrected") else "✅"
        print(f"  {status_icon} {comp['name']}: {comp['url']}")
        if comp.get("corrected"):
            print(f"     (исправлено с {comp.get('original_url')})")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(competitors)}")
        for comp in failed:
            print(f"  ❌ {comp['name']}: {comp['url']}")
            print(f"     Error: {comp['error']}")
            print(f"     Action: {comp['action']}")

    print(f"\n📊 Success Rate: {success_rate:.1%}")
    print(f"⏱️  Duration: {result.duration_seconds:.1f}s")

    print("\n" + "=" * 80)

    # Check if 5th competitor passed
    fifth_competitor = next(
        (c for c in validated if c['name'] == "Клиника Юлии Щербатовой"),
        None
    )

    if fifth_competitor:
        print("✅ SUCCESS: 5th competitor validated with correct URL!")
        print(f"   URL: {fifth_competitor['url']}")
    else:
        print("❌ FAILED: 5th competitor still not validated")

    return result


if __name__ == "__main__":
    asyncio.run(test_url_validator())
