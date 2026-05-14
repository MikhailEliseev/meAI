#!/usr/bin/env python3
"""
Script to teach a subagent using Teacher Agent.

Usage:
    python scripts/teach_subagent.py <subagent_name> <domain>

Example:
    python scripts/teach_subagent.py content-brief "content brief generation for SEO"
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.skills.skill_teacher import SkillTeacher


async def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/teach_subagent.py <subagent_name> <domain>")
        print('Example: python scripts/teach_subagent.py content-brief "content brief generation for SEO"')
        sys.exit(1)

    subagent_name = sys.argv[1]
    domain = sys.argv[2]

    print(f"🎓 Teaching {subagent_name} about {domain}...")
    print()

    # Create teacher
    teacher = SkillTeacher(project_root=project_root / "AIM")

    # Teach subagent
    report = await teacher.teach_subagent(subagent_name, domain)

    # Print report
    print()
    print("=" * 80)
    print("📊 TEACHING REPORT")
    print("=" * 80)
    print(f"Subagent: {report.subagent_name}")
    print(f"Domain: {report.domain}")
    print(f"Success: {'✅' if report.success else '❌'}")
    print()
    print(f"Repos found: {report.repos_found}")
    print(f"Repos cloned: {report.repos_cloned}")
    print(f"Skills extracted: {report.skills_extracted}")
    print()

    if report.best_skill:
        print(f"Best skill: {report.best_skill.name}")
        print(f"Source: {report.best_skill.source_repo}")
        print(f"Quality score: {report.best_skill.quality_score:.1f}")
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
    for d in report.dependencies_added:
        print(f"  - {d}")
    print()

    print(f"Tests created: {len(report.tests_created)}")
    for t in report.tests_created:
        print(f"  - {t}")
    print()

    if report.test_results:
        print(f"Tests: {'✅ PASSED' if report.test_results.success else '❌ FAILED'}")
        print(f"Summary: {report.test_results.summary}")
        if report.test_results.failures:
            print("Failures:")
            for failure in report.test_results.failures:
                print(f"  - {failure}")
        print()

    if report.commit_hash:
        print(f"Commit: {report.commit_hash}")
        print()

    if report.error:
        print(f"❌ Error: {report.error}")
        print()

    print("=" * 80)

    if report.success:
        print("✅ Teaching completed successfully!")
    else:
        print("❌ Teaching failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
