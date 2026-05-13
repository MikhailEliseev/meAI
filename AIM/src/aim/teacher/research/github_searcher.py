"""
GitHub Searcher - Search top GitHub repositories.

Searches GitHub for top repositories using dual strategy:
1. GitHub API search
2. Exa web search (parallel)

Merges and ranks results by stars, activity, and quality.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class GitHubRepo:
    """GitHub repository information."""
    url: str
    name: str
    description: str
    stars: int
    forks: int
    last_updated: datetime
    language: str
    topics: list[str]
    readme_summary: str


class GitHubSearcher:
    """
    Search GitHub repositories using dual strategy.

    Strategy:
    1. GitHub API Search:
       - Query: {query} language:{language} stars:>={min_stars}
       - Sort by: stars, updated
       - Filter: active repos (updated in last 6 months)

    2. Exa GitHub Search (parallel):
       - Query: {query} site:github.com
       - Extract repo URLs
       - Cross-reference with GitHub API results

    3. Merge & Deduplicate:
       - Combine results from both sources
       - Remove duplicates
       - Return top N by stars
    """

    def __init__(self):
        logger.info("github_searcher_initialized")

    async def search(
        self,
        query: str,
        language: str = "Python",
        min_stars: int = 100,
        max_results: int = 20,
    ) -> list[GitHubRepo]:
        """
        Search GitHub repositories.

        Args:
            query: Search query (e.g., "SEO analysis")
            language: Programming language filter
            min_stars: Minimum stars threshold
            max_results: Maximum results to return

        Returns:
            List of GitHubRepo sorted by stars
        """
        logger.info(
            "searching_github",
            query=query,
            language=language,
            min_stars=min_stars,
            max_results=max_results,
        )

        # Mock implementation - would use GitHub API + Exa
        # For now, return mock repos
        repos = self._create_mock_repos(query, language, min_stars, max_results)

        logger.info(
            "github_search_complete",
            query=query,
            repos_found=len(repos),
        )

        return repos

    def _create_mock_repos(
        self,
        query: str,
        language: str,
        min_stars: int,
        max_results: int,
    ) -> list[GitHubRepo]:
        """Create mock repositories for testing."""
        repos = []

        # Create mock repos with decreasing stars
        for i in range(min(max_results, 10)):
            stars = 1000 - (i * 100)
            if stars < min_stars:
                break

            repo = GitHubRepo(
                url=f"https://github.com/user{i}/repo{i}",
                name=f"user{i}/repo{i}",
                description=f"Repository for {query} in {language}",
                stars=stars,
                forks=stars // 10,
                last_updated=datetime.now(),
                language=language,
                topics=[query.lower().replace(" ", "-"), language.lower()],
                readme_summary=f"This is a {language} library for {query}. "
                               f"It provides comprehensive tools and utilities.",
            )
            repos.append(repo)

        return repos

    async def _search_github_api(
        self,
        query: str,
        language: str,
        min_stars: int,
        max_results: int,
    ) -> list[GitHubRepo]:
        """
        Search GitHub using GitHub API.

        Would use GitHub REST API:
        GET /search/repositories?q={query}+language:{language}+stars:>={min_stars}&sort=stars&order=desc
        """
        # Mock implementation
        return []

    async def _search_exa(
        self,
        query: str,
        max_results: int,
    ) -> list[GitHubRepo]:
        """
        Search GitHub using Exa.

        Would use Exa MCP tool:
        mcp__exa__web_search_exa(query="{query} site:github.com", numResults=max_results)
        """
        # Mock implementation
        return []

    def _merge_and_deduplicate(
        self,
        github_repos: list[GitHubRepo],
        exa_repos: list[GitHubRepo],
    ) -> list[GitHubRepo]:
        """
        Merge results from GitHub API and Exa, remove duplicates.

        Deduplication by URL.
        """
        all_repos = github_repos + exa_repos
        unique_repos = {repo.url: repo for repo in all_repos}
        return list(unique_repos.values())

    def _sort_by_stars(self, repos: list[GitHubRepo]) -> list[GitHubRepo]:
        """Sort repositories by stars (descending)."""
        return sorted(repos, key=lambda r: r.stars, reverse=True)
