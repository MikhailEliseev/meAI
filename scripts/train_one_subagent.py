"""
Train single subagent with domain-specific research.

Usage:
    python scripts/train_one_subagent.py <subagent_name> <domain>

Example:
    python scripts/train_one_subagent.py content "content generation and optimization"
"""

import asyncio
import sys
from pathlib import Path
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.skills.skill_selector import SkillSelector
import structlog

logger = structlog.get_logger()


async def train_subagent(subagent_name: str, domain: str):
    """Train single subagent with domain-specific research."""
    logger.info("subagent_training_start", subagent=subagent_name)

    selector = SkillSelector()

    # Phase 1: Domain-specific research
    research_results = await selector.research_domain_specific(
        subagent_name=subagent_name,
        domain=domain,
    )

    total_repos = sum(len(repos) for repos in research_results.values())

    print(f"\n{'='*80}")
    print(f"{subagent_name.upper()} SUBAGENT - RESEARCH RESULTS")
    print(f"{'='*80}\n")
    print(f"Queries executed: {len(research_results)}")
    print(f"Total repos found: {total_repos}\n")

    # Get top 3 repos by stars
    all_repos = [repo for repos in research_results.values() for repo in repos]
    top_repos = sorted(all_repos, key=lambda r: r.stars, reverse=True)[:3]

    print("Top 3 repos:")
    for i, repo in enumerate(top_repos, 1):
        print(f"{i}. {repo.url} ({repo.stars} stars)")
        print(f"   {repo.description}")

    # Phase 2: Extract skills
    all_skills = []
    for repo in top_repos:
        try:
            repo_name = repo.url.split("/")[-1]
            clone_path = Path(f"/tmp/teacher_repos/{subagent_name}/{repo_name}")

            # Clean if exists
            if clone_path.exists():
                shutil.rmtree(clone_path)

            clone_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"\nCloning {repo.url}...")
            await selector.clone_repo(repo.url, clone_path)

            print(f"Extracting skills from {repo_name}...")
            skills = await selector.extract_skills(clone_path, subagent_type=subagent_name)

            for skill in skills:
                skill.source_repo = repo.url

            all_skills.extend(skills)
            print(f"✓ Extracted {len(skills)} skills from {repo_name}")

        except Exception as e:
            logger.error("repo_failed", repo=repo.url, error=str(e))
            print(f"✗ Failed to process {repo.url}: {e}")
            continue

    # Summary
    print(f"\n{'='*80}")
    print(f"TRAINING SUMMARY")
    print(f"{'='*80}\n")
    print(f"Skills extracted: {len(all_skills)}")
    print(f"Repos analyzed: {len(top_repos)}")
    if all_skills:
        avg_quality = sum(s.quality_score for s in all_skills) / len(all_skills)
        print(f"Average quality: {avg_quality:.1f}/100")

        # Skills by pattern
        print("\nSkills by pattern:")
        pattern_counts = {}
        for skill in all_skills:
            pattern = skill.name
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {pattern}: {count}")

    logger.info(
        "subagent_training_complete",
        subagent=subagent_name,
        skills=len(all_skills),
    )

    return {
        "subagent": subagent_name,
        "queries": len(research_results),
        "repos_found": total_repos,
        "repos_analyzed": len(top_repos),
        "skills_extracted": len(all_skills),
        "avg_quality": sum(s.quality_score for s in all_skills) / len(all_skills) if all_skills else 0,
        "top_repos": [(r.url, r.stars) for r in top_repos],
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/train_one_subagent.py <subagent_name> <domain>")
        sys.exit(1)

    subagent_name = sys.argv[1]
    domain = sys.argv[2]

    result = asyncio.run(train_subagent(subagent_name, domain))

    print(f"\n✅ Training complete for {subagent_name}")
