"""
Train all remaining subagents with domain-specific research.

Subagents to train:
1. Content (content generation, ai content writer)
2. Analytics (google analytics api, yandex metrika api)
3. Gap Detection (content gap analysis, serp overlap)
4. Prioritization (task prioritization, scoring algorithm)
5. Social (social media api, telegram bot, vk api)
"""

import asyncio
import sys
from pathlib import Path

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
            clone_path.parent.mkdir(parents=True, exist_ok=True)

            await selector.clone_repo(repo.url, clone_path)
            skills = await selector.extract_skills(clone_path, subagent_type=subagent_name)

            for skill in skills:
                skill.source_repo = repo.url

            all_skills.extend(skills)

        except Exception as e:
            logger.error("repo_failed", repo=repo.url, error=str(e))
            continue

    # Summary
    print(f"\nSkills extracted: {len(all_skills)}")
    if all_skills:
        avg_quality = sum(s.quality_score for s in all_skills) / len(all_skills)
        print(f"Average quality: {avg_quality:.1f}/100")

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


async def main():
    """Train all remaining subagents."""
    subagents = [
        ("content", "content generation and optimization"),
        ("analytics", "web analytics and data analysis"),
        ("gap_detection", "content gap analysis"),
        ("prioritization", "task prioritization and scoring"),
        ("social", "social media automation"),
    ]

    results = []
    for subagent_name, domain in subagents:
        result = await train_subagent(subagent_name, domain)
        results.append(result)
        print("\n" + "="*80 + "\n")

    # Final summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY - ALL SUBAGENTS")
    print("="*80 + "\n")

    for result in results:
        print(f"{result['subagent'].upper()}:")
        print(f"  Queries: {result['queries']}")
        print(f"  Repos found: {result['repos_found']}")
        print(f"  Skills extracted: {result['skills_extracted']}")
        print(f"  Avg quality: {result['avg_quality']:.1f}/100")
        print()


if __name__ == "__main__":
    asyncio.run(main())
