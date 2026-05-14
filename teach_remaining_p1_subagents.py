#!/usr/bin/env python3
"""
Teach remaining 9 P1 subagents (excluding content-brief which is already done).
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.skills.skill_teacher import SkillTeacher


# Remaining P1 Subagents (excluding content-brief)
REMAINING_SUBAGENTS = [
    ("ad-copy", "advertising copy generation"),
    ("traffic-analyzer", "web traffic analysis"),
    ("conversion-tracker", "conversion tracking and optimization"),
    ("schema-generator", "schema markup generation"),
    ("quality-checker", "content quality checking"),
    ("landing-page", "landing page analysis"),
    ("bid-optimizer", "bid optimization for ads"),
    ("report-generator", "analytics report generation"),
    ("calendar-manager", "content calendar management"),
]


async def teach_remaining_subagents():
    """Teach remaining 9 P1 subagents."""
    print("=" * 80)
    print("🎓 Teaching remaining 9 P1 subagents...")
    print("=" * 80)
    print()

    teacher = SkillTeacher(project_root=project_root / "AIM")
    results = []

    for i, (subagent_name, domain) in enumerate(REMAINING_SUBAGENTS, 1):
        print(f"\n[{i}/9] Teaching {subagent_name}...")
        print("-" * 80)

        try:
            result = await teacher.teach_subagent(
                subagent_name=subagent_name,
                domain=domain,
            )
            results.append((subagent_name, result, None))

            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"{status}: {subagent_name}")
            print(f"  Skills extracted: {result.skills_extracted}")
            print(f"  Files modified: {result.files_modified}")
            if result.test_results:
                print(f"  Tests: {'✅ PASS' if result.test_results.success else '❌ FAIL'}")
            else:
                print(f"  Tests: ⚠️  NOT RUN")

        except Exception as e:
            results.append((subagent_name, None, str(e)))
            print(f"❌ ERROR: {subagent_name}")
            print(f"  {e}")

    # Generate summary report
    print("\n" + "=" * 80)
    print("📊 FINAL REPORT")
    print("=" * 80)

    successful = sum(1 for _, result, error in results if result and result.success)
    failed = sum(1 for _, result, error in results if result and not result.success)
    errors = sum(1 for _, result, error in results if error)

    print(f"\nTotal subagents: {len(REMAINING_SUBAGENTS)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Errors: {errors}")
    print()

    # Detailed results
    print("Detailed Results:")
    print("-" * 80)
    for subagent_name, result, error in results:
        if error:
            print(f"❌ {subagent_name}: ERROR - {error}")
        elif result:
            status = "✅" if result.success else "❌"
            print(f"{status} {subagent_name}:")
            print(f"   Skills: {result.skills_extracted}")
            print(f"   Files modified: {result.files_modified}")
            if result.test_results:
                print(f"   Tests: {'PASS' if result.test_results.success else 'FAIL'}")
            else:
                print(f"   Tests: NOT RUN")
            if result.best_skill:
                print(f"   Best skill: {result.best_skill.name}")

    print("\n" + "=" * 80)
    print(f"Teaching complete: {successful}/{len(REMAINING_SUBAGENTS)} successful")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(teach_remaining_subagents())
