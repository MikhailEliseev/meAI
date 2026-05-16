"""
Repo Ranker - Rank repositories by quality and relevance.

Ranks GitHub repositories using multiple criteria:
- Stars (30%): Community popularity
- Activity (25%): Recent commits and releases
- Quality (25%): Code quality indicators
- Relevance (20%): Match to search query
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog

from aim.teacher.research.github_searcher import GitHubRepo

logger = structlog.get_logger()


@dataclass
class RepoScore:
    """Repository quality score."""
    repo: GitHubRepo
    total_score: float
    stars_score: float
    activity_score: float
    quality_score: float
    relevance_score: float


class RepoRanker:
    """
    Rank repositories by quality and relevance.

    Scoring criteria:
    1. Stars (30%): Normalized by max stars in results
    2. Activity (25%): Recent updates, commits frequency
    3. Quality (25%): README, tests, documentation
    4. Relevance (20%): Topic match, description match

    Score range: 0-100
    """

    def __init__(
        self,
        stars_weight: float = 0.30,
        activity_weight: float = 0.25,
        quality_weight: float = 0.25,
        relevance_weight: float = 0.20,
    ):
        self.stars_weight = stars_weight
        self.activity_weight = activity_weight
        self.quality_weight = quality_weight
        self.relevance_weight = relevance_weight

        logger.info(
            "repo_ranker_initialized",
            stars_weight=stars_weight,
            activity_weight=activity_weight,
            quality_weight=quality_weight,
            relevance_weight=relevance_weight,
        )

    async def rank(
        self,
        repos: list[GitHubRepo],
        query: str = "",
    ) -> list[RepoScore]:
        """
        Rank repositories by quality and relevance.

        Args:
            repos: List of repositories to rank
            query: Original search query for relevance scoring

        Returns:
            List of RepoScore sorted by total_score (descending)
        """
        logger.info("ranking_repos", count=len(repos), query=query)

        if not repos:
            return []

        # Calculate scores for each repo
        scores = []
        for repo in repos:
            score = await self._score_repo(repo, repos, query)
            scores.append(score)

        # Sort by total score (descending)
        sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)

        logger.info(
            "ranking_complete",
            count=len(sorted_scores),
            top_score=sorted_scores[0].total_score if sorted_scores else 0,
        )

        return sorted_scores

    async def _score_repo(
        self,
        repo: GitHubRepo,
        all_repos: list[GitHubRepo],
        query: str,
    ) -> RepoScore:
        """
        Calculate quality score for a repository.

        Returns:
            RepoScore with breakdown
        """
        # 1. Stars score (30%)
        stars_score = self._score_stars(repo, all_repos)

        # 2. Activity score (25%)
        activity_score = self._score_activity(repo)

        # 3. Quality score (25%)
        quality_score = self._score_quality(repo)

        # 4. Relevance score (20%)
        relevance_score = self._score_relevance(repo, query)

        # Calculate total score
        total_score = (
            stars_score * self.stars_weight +
            activity_score * self.activity_weight +
            quality_score * self.quality_weight +
            relevance_score * self.relevance_weight
        ) * 100  # Scale to 0-100

        return RepoScore(
            repo=repo,
            total_score=total_score,
            stars_score=stars_score * 100,
            activity_score=activity_score * 100,
            quality_score=quality_score * 100,
            relevance_score=relevance_score * 100,
        )

    def _score_stars(self, repo: GitHubRepo, all_repos: list[GitHubRepo]) -> float:
        """
        Score based on stars (normalized).

        Returns:
            Score 0.0-1.0
        """
        if not all_repos:
            return 0.0

        max_stars = max(r.stars for r in all_repos)
        if max_stars == 0:
            return 0.0

        # Normalize to 0-1
        return repo.stars / max_stars

    def _score_activity(self, repo: GitHubRepo) -> float:
        """
        Score based on recent activity.

        Factors:
        - Last updated (more recent = higher score)
        - Forks (indicator of active use)

        Returns:
            Score 0.0-1.0
        """
        # Calculate days since last update
        days_since_update = (datetime.now() - repo.last_updated).days

        # Score based on recency (exponential decay)
        # 0 days = 1.0, 30 days = 0.5, 180 days = 0.1
        if days_since_update <= 30:
            recency_score = 1.0
        elif days_since_update <= 90:
            recency_score = 0.7
        elif days_since_update <= 180:
            recency_score = 0.4
        else:
            recency_score = 0.1

        # Forks indicate active use (normalize by stars)
        fork_ratio = repo.forks / repo.stars if repo.stars > 0 else 0
        fork_score = min(fork_ratio * 10, 1.0)  # Cap at 1.0

        # Combine (70% recency, 30% forks)
        return recency_score * 0.7 + fork_score * 0.3

    def _score_quality(self, repo: GitHubRepo) -> float:
        """
        Score based on quality indicators.

        Factors:
        - README exists and has content
        - Topics/tags present
        - Description quality

        Returns:
            Score 0.0-1.0
        """
        score = 0.0

        # README summary exists and has content (40%)
        if repo.readme_summary and len(repo.readme_summary) > 50:
            score += 0.4

        # Topics present (30%)
        if repo.topics and len(repo.topics) > 0:
            # More topics = better (up to 5)
            topic_score = min(len(repo.topics) / 5, 1.0)
            score += 0.3 * topic_score

        # Description exists and has content (30%)
        if repo.description and len(repo.description) > 20:
            score += 0.3

        return score

    def _score_relevance(self, repo: GitHubRepo, query: str) -> float:
        """
        Score based on relevance to search query.

        Factors:
        - Query terms in topics
        - Query terms in description
        - Query terms in name

        Returns:
            Score 0.0-1.0
        """
        if not query:
            return 1.0  # No query = all equally relevant

        query_lower = query.lower()
        query_terms = query_lower.split()

        score = 0.0

        # Check topics (40%)
        if repo.topics:
            topics_text = " ".join(repo.topics).lower()
            matching_terms = sum(1 for term in query_terms if term in topics_text)
            if query_terms:
                score += 0.4 * (matching_terms / len(query_terms))

        # Check description (40%)
        if repo.description:
            desc_lower = repo.description.lower()
            matching_terms = sum(1 for term in query_terms if term in desc_lower)
            if query_terms:
                score += 0.4 * (matching_terms / len(query_terms))

        # Check name (20%)
        name_lower = repo.name.lower()
        matching_terms = sum(1 for term in query_terms if term in name_lower)
        if query_terms:
            score += 0.2 * (matching_terms / len(query_terms))

        return min(score, 1.0)  # Cap at 1.0
