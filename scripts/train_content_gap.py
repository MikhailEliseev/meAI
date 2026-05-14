#!/usr/bin/env python3
"""
Train Content Gap Analyzer with Teacher Agent.

Uses import-based skill extraction and domain relevance scoring.
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
    print("Training Content Gap Analyzer with Teacher Agent")
    print("=" * 80)
    print()

    # Setup
    aim_root = project_root / "AIM"
    teacher = SkillTeacher(project_root=aim_root)

    print(f"Project root: {aim_root}")
    print(f"Target: content-gap subagent")
    print(f"Domain: content gap analysis and SERP overlap")
    print()

    # Run teaching workflow
    print("Starting teaching workflow...")
    print()

    report = await teacher.teach_subagent(
        subagent_name="content-gap",
        domain="content gap analysis serp overlap python"
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

    print()

    if report.error:
        print(f"❌ Error: {report.error}")
    else:
        print("✅ SUCCESS: Content Gap Analyzer training completed!")

    print()
    print("=" * 80)

    return 0 if report.success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
