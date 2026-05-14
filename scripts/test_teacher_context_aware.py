#!/usr/bin/env python3
"""
Test Teacher Agent with context-aware filtering.

Expected behavior:
1. Find repos with keyword research tools
2. Clone ALL repos
3. Extract skills from ALL repos
4. Analyze target context (base.py - async, httpx, raise)
5. Filter incompatible skills (sync, urllib, sys.exit)
6. Select best COMPATIBLE skill
7. Adapt code if needed
8. Apply to codebase
9. Run tests
10. Create commit

This should fix the issue where CLI sync code was applied to async API client.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.skills.skill_teacher import SkillTeacher


async def main():
    print("=" * 80)
    print("Testing Teacher Agent with Context-Aware Filtering")
    print("=" * 80)
    print()

    # Setup
    aim_root = project_root / "AIM"
    teacher = SkillTeacher(project_root=aim_root)

    print(f"Project root: {aim_root}")
    print(f"Target: keyword-research subagent")
    print(f"Domain: keyword research automation python")
    print()

    # Run teaching workflow
    print("Starting teaching workflow...")
    print()

    report = await teacher.teach_subagent(
        subagent_name="keyword-research",
        domain="keyword research automation python"
    )

    # Print results
    print()
    print("=" * 80)
    print("Teaching Report")
    print("=" * 80)
    print()

    print(f"Success: {report.success}")
    print(f"Subagent: {report.subagent_name}")
    print(f"Domain: {report.domain}")
    print()

    print(f"Repos found: {report.repos_found}")
    print(f"Repos cloned: {report.repos_cloned}")
    print(f"Skills extracted: {report.skills_extracted}")
    print()

    if report.best_skill:
        print(f"Best skill: {report.best_skill.name}")
        print(f"Source: {report.best_skill.source_repo}")
        print(f"Quality score: {report.best_skill.quality_score}")
        print()

    print(f"Files created: {len(report.files_created)}")
    for f in report.files_created:
        print(f"  - {f}")

    print(f"Files modified: {len(report.files_modified)}")
    for f in report.files_modified:
        print(f"  - {f}")

    print(f"Dependencies added: {len(report.dependencies_added)}")
    for d in report.dependencies_added:
        print(f"  - {d}")

    print(f"Tests created: {len(report.tests_created)}")
    for t in report.tests_created:
        print(f"  - {t}")

    print()

    if report.test_results:
        print(f"Test results: {'✅ PASSED' if report.test_results.success else '❌ FAILED'}")
        print(f"Summary: {report.test_results.summary}")
        if report.test_results.failures:
            print(f"Failures: {report.test_results.failures}")

    print()

    if report.commit_hash:
        print(f"Commit: {report.commit_hash}")
    else:
        print("No commit created")

    print()

    if report.error:
        print(f"❌ Error: {report.error}")
    else:
        print("✅ SUCCESS: Teacher Agent workflow completed successfully!")

    print()
    print("=" * 80)

    # Validation
    if report.success:
        print()
        print("Validating applied code...")
        print()

        # Check that applied code is async-compatible
        if report.files_modified:
            target_file = report.files_modified[0]
            content = target_file.read_text()

            print(f"Checking {target_file.name}:")
            print(f"  - Contains 'async def': {'✅' if 'async def' in content else '❌'}")
            print(f"  - Contains 'await': {'✅' if 'await ' in content else '❌'}")
            print(f"  - Contains 'httpx': {'✅' if 'httpx' in content else '❌'}")
            print(f"  - Contains 'urllib': {'❌ (should not)' if 'urllib' in content else '✅'}")
            print(f"  - Contains 'sys.exit': {'❌ (should not)' if 'sys.exit(' in content else '✅'}")
            print()

    return 0 if report.success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
