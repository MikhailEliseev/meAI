"""
Research Orchestrator - Coordinate all research components.

Orchestrates the complete research workflow:
1. Web research (best practices, tools, insights)
2. GitHub search (top repositories)
3. Repository ranking (quality scoring)
4. Result synthesis (combined findings)
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from aim.teacher.research.web_researcher import (
    WebResearcher,
    ResearchDepth,
    WebResearchResult,
)
from aim.teacher.research.github_searcher import (
    GitHubSearcher,
    GitHubRepo,
)
from aim.teacher.research.repo_ranker import (
    RepoRanker,
    RepoScore,
)

logger = structlog.get_logger()


@dataclass
class ResearchFindings:
    """Complete research findings."""

    # Web research
    best_practices: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    web_sources: list[str] = field(default_factory=list)

    # GitHub research
    top_repos: list[RepoScore] = field(default_factory=list)

    # Metadata
    research_depth: str = "standard"
    total_cost: float = 0.0
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class ResearchOrchestrator:
    """
    Orchestrate complete research workflow.

    Workflow:
    1. Parallel execution:
       - Web research (Exa deep research)
       - GitHub search (GitHub API + Exa)
    2. Repository ranking (quality scoring)
    3. Result synthesis (combine findings)

    Cost estimation:
    - Quick: ~$0.50 (web) + $0.00 (GitHub) = $0.50
    - Standard: ~$1.50 (web) + $0.00 (GitHub) = $1.50
    - Deep: ~$3.00 (web) + $0.00 (GitHub) = $3.00
    """

    def __init__(
        self,
        web_researcher: WebResearcher | None = None,
        github_searcher: GitHubSearcher | None = None,
        repo_ranker: RepoRanker | None = None,
    ):
        self.web_researcher = web_researcher or WebResearcher()
        self.github_searcher = github_searcher or GitHubSearcher()
        self.repo_ranker = repo_ranker or RepoRanker()

        logger.info("research_orchestrator_initialized")

    async def research(
        self,
        topic: str,
        depth: ResearchDepth = ResearchDepth.STANDARD,
        focus: list[str] | None = None,
        github_language: str = "Python",
        github_min_stars: int = 100,
        github_max_results: int = 10,
    ) -> ResearchFindings:
        """
        Conduct complete research on topic.

        Args:
            topic: Topic to research (e.g., "SEO analysis Python")
            depth: Research depth (quick/standard/deep)
            focus: Focus areas for web research
            github_language: Programming language filter for GitHub
            github_min_stars: Minimum stars for GitHub repos
            github_max_results: Maximum GitHub results

        Returns:
            ResearchFindings with complete results
        """
        start_time = datetime.now()

        logger.info(
            "research_started",
            topic=topic,
            depth=depth,
            focus=focus,
            github_language=github_language,
        )

        # Step 1: Parallel execution (web + GitHub)
        web_result, github_repos = await asyncio.gather(
            self._web_research(topic, depth, focus),
            self._github_search(topic, github_language, github_min_stars, github_max_results),
        )

        # Step 2: Rank GitHub repositories
        ranked_repos = await self._rank_repos(github_repos, topic)

        # Step 3: Synthesize results
        findings = self._synthesize_findings(
            web_result=web_result,
            ranked_repos=ranked_repos,
            depth=depth,
            start_time=start_time,
        )

        logger.info(
            "research_complete",
            topic=topic,
            depth=depth,
            best_practices_count=len(findings.best_practices),
            tools_count=len(findings.tools),
            insights_count=len(findings.insights),
            repos_count=len(findings.top_repos),
            total_cost=findings.total_cost,
            duration_seconds=findings.duration_seconds,
        )

        return findings

    async def _web_research(
        self,
        topic: str,
        depth: ResearchDepth,
        focus: list[str] | None,
    ) -> WebResearchResult:
        """
        Conduct web research.

        Uses Exa deep research to find:
        - Best practices
        - Tools and libraries
        - Industry insights
        - Source URLs
        """
        logger.info("web_research_started", topic=topic, depth=depth)

        result = await self.web_researcher.research(
            topic=topic,
            depth=depth,
            focus=focus,
        )

        logger.info(
            "web_research_complete",
            best_practices=len(result.best_practices),
            tools=len(result.tools),
            insights=len(result.insights),
            sources=len(result.sources),
            cost=result.cost,
        )

        return result

    async def _github_search(
        self,
        topic: str,
        language: str,
        min_stars: int,
        max_results: int,
    ) -> list[GitHubRepo]:
        """
        Search GitHub repositories.

        Uses dual strategy:
        - GitHub API search
        - Exa web search (site:github.com)

        Merges and deduplicates results.
        """
        logger.info(
            "github_search_started",
            topic=topic,
            language=language,
            min_stars=min_stars,
        )

        repos = await self.github_searcher.search(
            query=topic,
            language=language,
            min_stars=min_stars,
            max_results=max_results,
        )

        logger.info(
            "github_search_complete",
            repos_found=len(repos),
        )

        return repos

    async def _rank_repos(
        self,
        repos: list[GitHubRepo],
        query: str,
    ) -> list[RepoScore]:
        """
        Rank repositories by quality.

        Scoring criteria:
        - Stars (30%): Community popularity
        - Activity (25%): Recent updates
        - Quality (25%): README, topics, description
        - Relevance (20%): Query match
        """
        if not repos:
            return []

        logger.info("ranking_repos", count=len(repos))

        ranked = await self.repo_ranker.rank(repos, query=query)

        logger.info(
            "ranking_complete",
            count=len(ranked),
            top_score=ranked[0].total_score if ranked else 0,
        )

        return ranked

    def _synthesize_findings(
        self,
        web_result: WebResearchResult,
        ranked_repos: list[RepoScore],
        depth: ResearchDepth,
        start_time: datetime,
    ) -> ResearchFindings:
        """
        Synthesize all research results.

        Combines:
        - Web research findings
        - GitHub repository rankings
        - Metadata (cost, duration)
        """
        duration = (datetime.now() - start_time).total_seconds()

        findings = ResearchFindings(
            # Web research
            best_practices=web_result.best_practices,
            tools=web_result.tools,
            insights=web_result.insights,
            web_sources=web_result.sources,

            # GitHub research
            top_repos=ranked_repos,

            # Metadata
            research_depth=depth.value,
            total_cost=web_result.cost,  # GitHub is free
            duration_seconds=duration,
            timestamp=datetime.now(),
        )

        return findings

    def format_findings(self, findings: ResearchFindings) -> str:
        """
        Format research findings as markdown.

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Research Findings",
            "",
            f"**Topic:** {findings.research_depth} research",
            f"**Cost:** ${findings.total_cost:.2f}",
            f"**Duration:** {findings.duration_seconds:.1f}s",
            f"**Timestamp:** {findings.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Best Practices",
            "",
        ]

        for i, practice in enumerate(findings.best_practices, 1):
            lines.append(f"{i}. {practice}")

        lines.extend([
            "",
            "## Tools & Libraries",
            "",
        ])

        for i, tool in enumerate(findings.tools, 1):
            lines.append(f"{i}. {tool}")

        lines.extend([
            "",
            "## Industry Insights",
            "",
        ])

        for i, insight in enumerate(findings.insights, 1):
            lines.append(f"{i}. {insight}")

        lines.extend([
            "",
            "## Top GitHub Repositories",
            "",
        ])

        for i, repo_score in enumerate(findings.top_repos, 1):
            repo = repo_score.repo
            lines.extend([
                f"### {i}. {repo.name} ({repo.stars} ⭐)",
                "",
                f"**URL:** {repo.url}",
                f"**Score:** {repo_score.total_score:.1f}/100",
                f"**Description:** {repo.description}",
                f"**Topics:** {', '.join(repo.topics)}",
                "",
                "**Score Breakdown:**",
                f"- Stars: {repo_score.stars_score:.1f}/100",
                f"- Activity: {repo_score.activity_score:.1f}/100",
                f"- Quality: {repo_score.quality_score:.1f}/100",
                f"- Relevance: {repo_score.relevance_score:.1f}/100",
                "",
            ])

        lines.extend([
            "## Web Sources",
            "",
        ])

        for i, source in enumerate(findings.web_sources, 1):
            lines.append(f"{i}. {source}")

        return "\n".join(lines)
