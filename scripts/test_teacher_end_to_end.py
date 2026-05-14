#!/usr/bin/env python3
"""
Test Teacher Agent end-to-end on Keyword Research Agent.

This script tests the complete teaching workflow:
1. Research domain-specific solutions (GitHub search)
2. Clone ALL found repositories
3. Extract skills from ALL repos
4. Compare and rank skills
5. Extract best implementation
6. Apply to codebase
7. Run tests
8. Create git commit
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.skills.skill_teacher import SkillTeacher


async def main():
    """Run end-to-end teaching test."""
    print("=" * 80)
    print("Teacher Agent End-to-End Test")
    print("=" * 80)
    print()

    # Initialize teacher
    aim_root = project_root / "AIM"
    print(f"Project root: {aim_root}")
    print()

    teacher = SkillTeacher(project_root=aim_root)

    # Teach Keyword Research Agent
    print("Teaching Keyword Research Agent...")
    print("Domain: keyword research automation python")
    print()

    try:
        report = await teacher.teach_subagent(
            subagent_name="keyword-research",
            domain="keyword research automation python"
        )

        # Print report
        print()
        print("=" * 80)
        print("Teaching Report")
        print("=" * 80)
        print()
        print(f"Subagent: {report.subagent_name}")
        print(f"Domain: {report.domain}")
        print(f"Success: {report.success}")
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
        print()

        print(f"Files modified: {len(report.files_modified)}")
        for f in report.files_modified:
            print(f"  - {f}")
        print()

        print(f"Dependencies added: {len(report.dependencies_added)}")
        for dep in report.dependencies_added:
            print(f"  - {dep}")
        print()

        print(f"Tests created: {len(report.tests_created)}")
        for t in report.tests_created:
            print(f"  - {t}")
        print()

        if report.test_results:
            print("Test Results:")
            print(f"  Success: {report.test_results.success}")
            print(f"  Summary: {report.test_results.summary}")
            if report.test_results.failures:
                print(f"  Failures: {report.test_results.failures}")
            print()

        if report.commit_hash:
            print(f"Commit: {report.commit_hash}")
            print()

        if report.error:
            print(f"Error: {report.error}")
            print()

        # Final verdict
        print("=" * 80)
        if report.success:
            print("✅ SUCCESS: Teacher Agent workflow completed successfully!")
        else:
            print("❌ FAILED: Teacher Agent workflow failed!")
            print(f"Error: {report.error}")
        print("=" * 80)

        return 0 if report.success else 1

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ EXCEPTION: Teacher Agent workflow crashed!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
