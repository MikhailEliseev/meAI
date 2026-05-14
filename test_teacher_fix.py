#!/usr/bin/env python3
"""Test Teacher Agent fixes on content-brief subagent."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.skills.skill_teacher import SkillTeacher


async def main():
    """Test Teacher Agent on content-brief."""
    print("🎓 Testing Teacher Agent fixes on content-brief subagent...")
    print("=" * 80)

    # Create teacher
    teacher = SkillTeacher(project_root=project_root / "AIM")

    # Teach content-brief
    report = await teacher.teach_subagent(
        subagent_name="content-brief",
        domain="content brief generation for SEO"
    )

    # Print report
    print("\n" + "=" * 80)
    print("📊 TEACHING REPORT")
    print("=" * 80)
    print(f"Subagent: {report.subagent_name}")
    print(f"Domain: {report.domain}")
    print(f"Success: {'✅' if report.success else '❌'}")
    print(f"\nRepos found: {report.repos_found}")
    print(f"Repos cloned: {report.repos_cloned}")
    print(f"Skills extracted: {report.skills_extracted}")

    if report.best_skill:
        print(f"\nBest skill: {report.best_skill.name}")
        print(f"Source: {report.best_skill.source_repo}")

    print(f"\nFiles created: {len(report.files_created)}")
    for f in report.files_created:
        print(f"  ✅ {f}")

    print(f"\nFiles modified: {len(report.files_modified)}")
    for f in report.files_modified:
        print(f"  📝 {f}")

    print(f"\nDependencies added: {len(report.dependencies_added)}")
    for d in report.dependencies_added:
        print(f"  📦 {d}")

    if report.test_results:
        print(f"\nTests: {'✅ PASS' if report.test_results.success else '❌ FAIL'}")
        print(f"  {report.test_results.summary}")

    if report.commit_hash:
        print(f"\nCommit: {report.commit_hash}")

    if report.error:
        print(f"\n❌ Error: {report.error}")

    print("=" * 80)

    return 0 if report.success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
