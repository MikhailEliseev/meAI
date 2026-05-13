#!/usr/bin/env python3
"""
Test Teacher Agent v2.0 on real subagent.

Validates full workflow:
1. Deep audit Content Gap Analysis Agent
2. Compare solutions from GitHub
3. Adopt best practices
4. Generate markdown report
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.teacher_agent import TeacherAgent


async def main():
    """Test Teacher Agent v2.0 workflow."""
    print("=" * 80)
    print("Teacher Agent v2.0 - Full Workflow Test")
    print("=" * 80)
    print()

    # Initialize Teacher Agent
    print("Initializing Teacher Agent...")
    teacher = TeacherAgent()
    print("✅ Teacher Agent initialized")
    print()

    # Target subagent
    subagent_path = project_root / "AIM" / "src" / "aim" / "subagents" / "content_gap_analysis"

    # Try multiple search strategies
    search_queries = [
        "python async rate limiting",  # High stars repos
        "python api client circuit breaker",
        "python httpx retry exponential backoff",
    ]

    print(f"Target: {subagent_path.name}")
    print(f"Search strategies: {len(search_queries)}")
    print()

    all_skills = []

    # Step 1: Deep audit with multiple queries
    print("-" * 80)
    print("Step 1: Deep Audit - Searching GitHub for best practices")
    print("-" * 80)

    for i, query in enumerate(search_queries, 1):
        print(f"\nStrategy {i}/{len(search_queries)}: {query}")

        try:
            skills = await teacher.deep_audit_subagent(subagent_path, query)
            print(f"  Found {len(skills)} skills")
            all_skills.extend(skills)
        except Exception as e:
            print(f"  ⚠️  Search failed: {e}")
            continue

    print(f"\n✅ Total skills found: {len(all_skills)}")

    if all_skills:
        print("\nTop 10 skills:")
        for i, skill in enumerate(all_skills[:10], 1):
            print(f"  {i}. {skill.name}")
            print(f"     Source: {Path(skill.source_repo).name}")
            print(f"     Quality: {skill.quality_score:.1f}/100")
            print()

    if not all_skills:
        print("⚠️  No skills found. Exiting.")
        return

    # Step 2: Compare solutions
    print("-" * 80)
    print("Step 2: Compare Solutions - Ranking by quality")
    print("-" * 80)

    try:
        comparison = await teacher.compare_solutions(all_skills)
        print(f"✅ Compared {len(all_skills)} skills")

        if comparison.best_skill:
            print(f"\n🏆 Best skill: {comparison.best_skill.name}")
            print(f"   Source: {Path(comparison.best_skill.source_repo).name}")
            print(f"   Quality: {comparison.best_skill.quality_score:.1f}/100")
            print()

            # Show dimension scores
            if comparison.best_skill.source_repo in comparison.dimension_scores:
                scores = comparison.dimension_scores[comparison.best_skill.source_repo]
                print("   Dimension scores:")
                for dimension, score in scores.items():
                    print(f"     - {dimension}: {score:.1f}/100")
                print()

            # Show top 5 ranked skills
            print("   Top 5 ranked skills:")
            for i, skill in enumerate(comparison.ranked_skills[:5], 1):
                print(f"     {i}. {skill.name} ({Path(skill.source_repo).name})")
                print(f"        Quality: {skill.quality_score:.1f}/100")
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return

    if not comparison.best_skill:
        print("⚠️  No best skill found. Exiting.")
        return

    # Step 3: Adopt solution
    print()
    print("-" * 80)
    print("Step 3: Adopt Solution - Integrating best practices")
    print("-" * 80)

    target_dir = subagent_path
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = await teacher.adopt_solution(comparison.best_skill, target_dir)

        if result.success:
            print("✅ Adoption successful!")
            print(f"\nFiles created: {len(result.files_created)}")
            for file in result.files_created:
                print(f"  - {file}")

            print(f"\nDependencies added: {len(result.dependencies_added)}")
            for dep in result.dependencies_added:
                print(f"  - {dep}")

            print(f"\nCode adapted: {result.code_adapted}")
            print()
        else:
            print(f"❌ Adoption failed: {result.error}")
            return
    except Exception as e:
        print(f"❌ Adoption failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Generate report
    print("-" * 80)
    print("Step 4: Generate Report")
    print("-" * 80)

    report_path = project_root / "AIM" / "obsidian" / "teacher" / "wiki" / "adoption-reports"
    report_path.mkdir(parents=True, exist_ok=True)

    report_file = report_path / f"content-gap-analysis-{comparison.best_skill.name.lower().replace(' ', '-')}.md"

    try:
        from AIM.src.aim.teacher.adoption_report import AdoptionReportGenerator

        generator = AdoptionReportGenerator()
        report = generator.generate(comparison.best_skill, result)
        generator.save(report, report_file)

        print(f"✅ Report saved: {report_file}")
        print()
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Skills found: {len(all_skills)}")
    print(f"  - Best skill: {comparison.best_skill.name}")
    print(f"  - Quality score: {comparison.best_skill.quality_score:.1f}/100")
    print(f"  - Files created: {len(result.files_created)}")
    print(f"  - Dependencies added: {len(result.dependencies_added)}")
    print(f"  - Report: {report_file.name}")
    print()
    print("✅ Teacher Agent v2.0 validated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
