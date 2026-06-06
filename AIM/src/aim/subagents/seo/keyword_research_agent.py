"""
Keyword Research Agent - SEO Keyword Discovery and Analysis.

Finds profitable keywords for content strategy using SEMrush and Ahrefs APIs.
Provides keyword expansion, intent classification, clustering, and priority scoring.

Based on: SEMrush Keyword Magic Tool + Ahrefs Keywords Explorer
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

from src.aim.subagents.api_clients.semrush import SEMrushClient
from src.aim.subagents.api_clients.ahrefs import AhrefsClient
from src.aim.subagents.schemas.api_responses import KeywordDataUnified


@dataclass
class KeywordCluster:
    """Keyword cluster with related keywords."""

    main_keyword: str
    keywords: list[KeywordDataUnified]
    total_volume: int
    avg_difficulty: float
    avg_cpc: float
    cluster_size: int


@dataclass
class KeywordIntent:
    """Keyword intent classification."""

    keyword: str
    intent: str  # informational, commercial, transactional, navigational
    confidence: float
    signals: list[str]


@dataclass
class KeywordPriority:
    """Keyword priority scoring."""

    keyword: str
    priority_score: float  # 0-100
    volume: int
    difficulty: float
    cpc: float
    intent: str
    reason: str


@dataclass
class KeywordResearchResult:
    """Complete keyword research result."""

    seed_keyword: str
    timestamp: str

    # Expanded keywords
    keywords: list[KeywordDataUnified]
    total_keywords: int

    # Intent classification
    intents: list[KeywordIntent]

    # Clustering
    clusters: list[KeywordCluster]
    total_clusters: int

    # Priority scoring
    priorities: list[KeywordPriority]

    # Summary
    total_volume: int
    avg_difficulty: float
    avg_cpc: float
    top_opportunities: list[KeywordDataUnified]


class KeywordResearchAgent:
    """
    Keyword Research Agent.

    Discovers and analyzes keywords for SEO content strategy
    using SEMrush and Ahrefs APIs.
    """

    def __init__(
        self,
        semrush_api_key: str | None = None,
        ahrefs_api_key: str | None = None,
    ):
        """
        Initialize Keyword Research Agent.

        Args:
            semrush_api_key: SEMrush API key (primary source)
            ahrefs_api_key: Ahrefs API key (fallback source)
        """
        self.logger = structlog.get_logger()
        self.semrush_client = SEMrushClient(api_key=semrush_api_key) if semrush_api_key else None
        self.ahrefs_client = AhrefsClient(api_key=ahrefs_api_key) if ahrefs_api_key else None

    async def research(
        self,
        seed_keyword: str,
        max_keywords: int = 100,
        min_volume: int = 10,
        max_difficulty: float = 70.0,
    ) -> KeywordResearchResult:
        """
        Perform complete keyword research.

        Args:
            seed_keyword: Starting keyword for expansion
            max_keywords: Maximum keywords to return
            min_volume: Minimum search volume filter
            max_difficulty: Maximum difficulty filter

        Returns:
            Complete keyword research with clustering and priorities
        """
        self.logger.info(
            "keyword_research_start",
            seed=seed_keyword,
            max_keywords=max_keywords,
        )

        # Step 1: Expand keywords
        keywords = await self._expand_keywords(
            seed_keyword,
            max_keywords,
            min_volume,
            max_difficulty,
        )

        # Step 2: Classify intent
        intents = self._classify_intent(keywords)

        # Step 3: Cluster keywords
        clusters = self._cluster_keywords(keywords)

        # Step 4: Score priorities
        priorities = self._score_priorities(keywords, intents)

        # Step 5: Calculate summary
        total_volume = sum(k.volume for k in keywords)
        avg_difficulty = sum(k.difficulty for k in keywords) / len(keywords) if keywords else 0.0
        avg_cpc = sum(k.cpc for k in keywords) / len(keywords) if keywords else 0.0

        # Top opportunities: high volume, low difficulty, commercial/transactional intent
        top_opportunities = sorted(
            [k for k in keywords if k.difficulty < 40 and k.volume > 100],
            key=lambda x: x.volume,
            reverse=True,
        )[:10]

        result = KeywordResearchResult(
            seed_keyword=seed_keyword,
            timestamp=datetime.now().isoformat(),
            keywords=keywords,
            total_keywords=len(keywords),
            intents=intents,
            clusters=clusters,
            total_clusters=len(clusters),
            priorities=priorities,
            total_volume=total_volume,
            avg_difficulty=round(avg_difficulty, 1),
            avg_cpc=round(avg_cpc, 2),
            top_opportunities=top_opportunities,
        )

        self.logger.info(
            "keyword_research_complete",
            total_keywords=len(keywords),
            total_clusters=len(clusters),
            top_opportunities=len(top_opportunities),
        )

        return result

    async def _expand_keywords(
        self,
        seed_keyword: str,
        max_keywords: int,
        min_volume: int,
        max_difficulty: float,
    ) -> list[KeywordDataUnified]:
        """Expand keywords using SEMrush (primary) or Ahrefs (fallback)."""
        keywords = []

        # Try SEMrush first
        if self.semrush_client:
            try:
                keywords = await self.semrush_client.expand_keywords(
                    seed_keyword=seed_keyword,
                    max_keywords=max_keywords,
                    min_volume=min_volume,
                    max_cost_usd=5.0,
                )
                self.logger.info(
                    "semrush_expansion_success",
                    keywords_found=len(keywords),
                )
            except Exception as e:
                self.logger.warning(
                    "semrush_expansion_failed",
                    error=str(e),
                )

        # Fallback to Ahrefs if SEMrush failed or not available
        if not keywords and self.ahrefs_client:
            try:
                keywords = await self.ahrefs_client.expand_keywords(
                    seed_keyword=seed_keyword,
                    max_keywords=max_keywords,
                    min_volume=min_volume,
                )
                self.logger.info(
                    "ahrefs_expansion_success",
                    keywords_found=len(keywords),
                )
            except Exception as e:
                self.logger.error(
                    "ahrefs_expansion_failed",
                    error=str(e),
                )

        # Filter by difficulty
        keywords = [k for k in keywords if k.difficulty <= max_difficulty]

        return keywords

    def _classify_intent(
        self,
        keywords: list[KeywordDataUnified],
    ) -> list[KeywordIntent]:
        """
        Classify keyword intent.

        Intent types:
        - informational: how, what, why, guide, tutorial
        - commercial: best, top, review, comparison, vs
        - transactional: buy, price, discount, deal, order
        - navigational: brand names, specific sites
        """
        intents = []

        for keyword in keywords:
            kw_lower = keyword.keyword.lower()

            # Informational signals
            info_signals = ["how", "what", "why", "guide", "tutorial", "learn", "tips"]
            info_score = sum(1 for signal in info_signals if signal in kw_lower)

            # Commercial signals
            commercial_signals = ["best", "top", "review", "comparison", "vs", "versus"]
            commercial_score = sum(1 for signal in commercial_signals if signal in kw_lower)

            # Transactional signals
            transactional_signals = ["buy", "price", "discount", "deal", "order", "shop"]
            transactional_score = sum(1 for signal in transactional_signals if signal in kw_lower)

            # Determine intent
            scores = {
                "informational": info_score,
                "commercial": commercial_score,
                "transactional": transactional_score,
            }

            max_score = max(scores.values())
            if max_score == 0:
                intent = "navigational"
                confidence = 0.5
                signals = []
            else:
                intent = max(scores, key=scores.get)
                confidence = min(max_score / 3.0, 1.0)
                signals = [
                    s for s in (info_signals + commercial_signals + transactional_signals)
                    if s in kw_lower
                ]

            intents.append(
                KeywordIntent(
                    keyword=keyword.keyword,
                    intent=intent,
                    confidence=round(confidence, 2),
                    signals=signals,
                )
            )

        return intents

    def _cluster_keywords(
        self,
        keywords: list[KeywordDataUnified],
    ) -> list[KeywordCluster]:
        """
        Cluster keywords by similarity.

        Simple clustering based on common words (2+ words in common).
        """
        clusters = []
        clustered_keywords = set()

        for keyword in keywords:
            if keyword.keyword in clustered_keywords:
                continue

            # Find similar keywords (2+ words in common)
            words = set(keyword.keyword.lower().split())
            similar = [keyword]

            for other in keywords:
                if other.keyword in clustered_keywords or other.keyword == keyword.keyword:
                    continue

                other_words = set(other.keyword.lower().split())
                common_words = words & other_words

                if len(common_words) >= 2:
                    similar.append(other)
                    clustered_keywords.add(other.keyword)

            if len(similar) >= 2:  # Only create cluster if 2+ keywords
                clustered_keywords.add(keyword.keyword)

                total_volume = sum(k.volume for k in similar)
                avg_difficulty = sum(k.difficulty for k in similar) / len(similar)
                avg_cpc = sum(k.cpc for k in similar) / len(similar)

                clusters.append(
                    KeywordCluster(
                        main_keyword=keyword.keyword,
                        keywords=similar,
                        total_volume=total_volume,
                        avg_difficulty=round(avg_difficulty, 1),
                        avg_cpc=round(avg_cpc, 2),
                        cluster_size=len(similar),
                    )
                )

        return clusters

    def _score_priorities(
        self,
        keywords: list[KeywordDataUnified],
        intents: list[KeywordIntent],
    ) -> list[KeywordPriority]:
        """
        Score keyword priorities (0-100).

        Scoring factors:
        - Volume: 40% (higher = better)
        - Difficulty: 30% (lower = better)
        - CPC: 20% (higher = better, indicates commercial value)
        - Intent: 10% (transactional > commercial > informational)
        """
        priorities = []
        intent_dict = {i.keyword: i for i in intents}

        # Normalize factors
        max_volume = max(k.volume for k in keywords) if keywords else 1
        max_cpc = max(k.cpc for k in keywords) if keywords else 1

        for keyword in keywords:
            intent = intent_dict.get(keyword.keyword)

            # Volume score (0-40)
            volume_score = (keyword.volume / max_volume) * 40

            # Difficulty score (0-30, inverted)
            difficulty_score = (1 - keyword.difficulty / 100) * 30

            # CPC score (0-20)
            cpc_score = (keyword.cpc / max_cpc) * 20 if max_cpc > 0 else 0

            # Intent score (0-10)
            intent_scores = {
                "transactional": 10,
                "commercial": 7,
                "informational": 4,
                "navigational": 2,
            }
            intent_score = intent_scores.get(intent.intent if intent else "navigational", 2)

            # Total priority score
            priority_score = volume_score + difficulty_score + cpc_score + intent_score

            # Generate reason
            if priority_score >= 70:
                reason = f"High priority: {keyword.volume:,} volume, {keyword.difficulty:.0f} difficulty, {intent.intent if intent else 'unknown'} intent"
            elif priority_score >= 50:
                reason = f"Medium priority: {keyword.volume:,} volume, {keyword.difficulty:.0f} difficulty"
            else:
                reason = f"Low priority: {keyword.volume:,} volume, {keyword.difficulty:.0f} difficulty"

            priorities.append(
                KeywordPriority(
                    keyword=keyword.keyword,
                    priority_score=round(priority_score, 1),
                    volume=keyword.volume,
                    difficulty=keyword.difficulty,
                    cpc=keyword.cpc,
                    intent=intent.intent if intent else "navigational",
                    reason=reason,
                )
            )

        # Sort by priority score
        priorities.sort(key=lambda x: x.priority_score, reverse=True)

        return priorities


async def main():
    """Example usage."""
    import os

    semrush_key = os.getenv("SEMRUSH_API_KEY")
    ahrefs_key = os.getenv("AHREFS_API_KEY")

    agent = KeywordResearchAgent(
        semrush_api_key=semrush_key,
        ahrefs_api_key=ahrefs_key,
    )

    result = await agent.research(
        seed_keyword="dental implants",
        max_keywords=50,
        min_volume=100,
        max_difficulty=60.0,
    )

    print(f"Total Keywords: {result.total_keywords}")
    print(f"Total Volume: {result.total_volume:,}")
    print(f"Avg Difficulty: {result.avg_difficulty}")
    print(f"Total Clusters: {result.total_clusters}")
    print()

    print("Top 10 Priorities:")
    for priority in result.priorities[:10]:
        print(
            f"  {priority.keyword}: {priority.priority_score:.1f} "
            f"({priority.volume:,} vol, {priority.difficulty:.0f} diff, {priority.intent})"
        )


if __name__ == "__main__":
    asyncio.run(main())
