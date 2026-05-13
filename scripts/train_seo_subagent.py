"""
Train SEO subagent with domain-specific research.

This script:
1. Uses SkillSelector.research_domain_specific() for SEO
2. Finds specialized repos (e.g., python-seo-analyzer, serp-api)
3. Clones and analyzes each repo
4. Extracts domain-specific patterns
5. Generates training report
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


async def main():
    """Train SEO subagent with domain-specific research."""
    logger.info("seo_training_start")

    # Initialize components
    selector = SkillSelector()

    # Phase 1: Domain-specific research
    logger.info("phase_1_research", subagent="seo")

    research_results = await selector.research_domain_specific(
        subagent_name="seo",
        domain="seo analysis and optimization",
    )

    # Log research results
    total_repos = sum(len(repos) for repos in research_results.values())
    logger.info(
        "research_complete",
        queries_executed=len(research_results),
        total_repos=total_repos,
    )

    # Print detailed results
    print("\n" + "="*80)
    print("SEO SUBAGENT - DOMAIN-SPECIFIC RESEARCH RESULTS")
    print("="*80 + "\n")

    for query, repos in research_results.items():
        print(f"\nQuery: {query}")
        print(f"Repos found: {len(repos)}")
        print("-" * 80)

        for i, repo in enumerate(repos, 1):
            print(f"{i}. {repo.url}")
            print(f"   Stars: {repo.stars}")
            print(f"   Description: {repo.description}")
            print()

    # Phase 2: Clone and analyze top repos
    logger.info("phase_2_analysis", subagent="seo")

    # Get top 5 repos by stars across all queries
    all_repos = [repo for repos in research_results.values() for repo in repos]
    top_repos = sorted(all_repos, key=lambda r: r.stars, reverse=True)[:5]

    print("\n" + "="*80)
    print("TOP 5 REPOS FOR ANALYSIS")
    print("="*80 + "\n")

    for i, repo in enumerate(top_repos, 1):
        print(f"{i}. {repo.url} ({repo.stars} stars)")

    # Phase 3: Extract skills from top repos
    logger.info("phase_3_extraction", repos_count=len(top_repos))

    all_skills = []
    for repo in top_repos:
        try:
            repo_name = repo.url.split("/")[-1]
            clone_path = Path(f"/tmp/teacher_repos/seo/{repo_name}")
            clone_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"\nCloning {repo.url}...")
            await selector.clone_repo(repo.url, clone_path)

            print(f"Extracting skills from {repo_name}...")
            skills = await selector.extract_skills(clone_path)

            for skill in skills:
                skill.source_repo = repo.url

            all_skills.extend(skills)

            print(f"✓ Extracted {len(skills)} skills from {repo_name}")

        except Exception as e:
            logger.error("repo_processing_failed", repo=repo.url, error=str(e))
            print(f"✗ Failed to process {repo.url}: {e}")
            continue

    # Phase 4: Generate training report
    print("\n" + "="*80)
    print("TRAINING REPORT")
    print("="*80 + "\n")

    print(f"Total skills extracted: {len(all_skills)}")
    print(f"Repos analyzed: {len(top_repos)}")
    print(f"Queries executed: {len(research_results)}")
    print()

    if all_skills:
        print("Skills by pattern:")
        pattern_counts = {}
        for skill in all_skills:
            pattern = skill.name
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {pattern}: {count}")

        print(f"\nAverage quality score: {sum(s.quality_score for s in all_skills) / len(all_skills):.1f}/100")

    logger.info(
        "seo_training_complete",
        skills_extracted=len(all_skills),
        repos_analyzed=len(top_repos),
    )


if __name__ == "__main__":
    asyncio.run(main())
