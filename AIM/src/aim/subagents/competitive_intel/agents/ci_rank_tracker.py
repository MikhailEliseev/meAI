"""
CI Rank Tracker Agent - SERP Position Tracking.

Tracks keyword rankings using Google Search Console API
and SerpAPI for real-time SERP data.

Based on:
- Google Search Console API (official)
- SerpAPI for real-time SERP scraping
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog

from meai.agents.base_agent import Agent, Task, TaskResult


@dataclass
class KeywordPosition:
    """Keyword position data."""

    keyword: str
    position: float
    url: str
    impressions: int
    clicks: int
    ctr: float
    date: str


@dataclass
class PositionChange:
    """Position change over time."""

    keyword: str
    current_position: float
    previous_position: float
    change: float
    change_percent: float
    trend: str  # "up", "down", "stable"


@dataclass
class CompetitorPosition:
    """Competitor position for keyword."""

    keyword: str
    competitor_url: str
    position: int
    title: str
    snippet: str


@dataclass
class RankTrackingResult:
    """Complete rank tracking result."""

    target_url: str
    date_range: tuple[str, str]
    timestamp: str

    # Current positions
    positions: list[KeywordPosition]

    # Position changes
    changes: list[PositionChange]

    # Competitor positions
    competitor_positions: list[CompetitorPosition]

    # Summary metrics
    avg_position: float
    total_keywords: int
    top_3_count: int
    top_10_count: int
    top_100_count: int

    # Insights
    biggest_gains: list[PositionChange]
    biggest_losses: list[PositionChange]
    new_rankings: list[KeywordPosition]
    lost_rankings: list[str]


class CIRankTrackerAgent(Agent):
    """
    Competitive Intelligence Rank Tracker Agent.

    Tracks keyword rankings using SerpAPI for real-time SERP data
    and monitors competitor positions.
    """

    def __init__(
        self,
        agent_id: str,
        serpapi_key: str | None = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian",
    ):
        """
        Initialize CI Rank Tracker Agent.

        Args:
            agent_id: Unique agent identifier
            serpapi_key: SerpAPI key for real-time SERP data
            database_url: Database connection URL
            vault_path: Obsidian vault path
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-rank-tracker",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.logger = structlog.get_logger()
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        self.serpapi_base_url = "https://serpapi.com/search"
        self.timeout = httpx.Timeout(30.0)

    async def track_rankings(
        self,
        target_url: str,
        keywords: list[str] | None = None,
        days: int = 7,
        compare_days: int = 7,
    ) -> RankTrackingResult:
        """
        Track keyword rankings for target URL using SerpAPI.

        Args:
            target_url: URL to track rankings for
            keywords: Specific keywords to track (required)
            days: Number of days to analyze (for metadata only — SerpAPI gives current)
            compare_days: Days to compare against (not used in SerpAPI mode)

        Returns:
            Complete rank tracking result with changes and insights
        """
        self.logger.info(
            "rank_tracking_start",
            target=target_url,
            keywords_count=len(keywords) if keywords else 0,
            days=days,
        )

        if not keywords:
            keywords = []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Fetch current positions via SerpAPI
            current_positions = await self._fetch_our_positions(
                client, target_url, keywords
            )

            # Previous positions not available via SerpAPI (would need historical storage)
            previous_positions = []

            # Calculate changes (empty if no historical data)
            changes = self._calculate_changes(
                current_positions, previous_positions
            )

            # Fetch competitor positions for top keywords
            competitor_positions = await self._fetch_competitor_positions(
                client,
                [p.keyword for p in current_positions[:10]],
            )

        # Calculate summary metrics
        avg_position = (
            sum(p.position for p in current_positions) / len(current_positions)
            if current_positions
            else 0.0
        )
        top_3_count = sum(1 for p in current_positions if p.position <= 3)
        top_10_count = sum(1 for p in current_positions if p.position <= 10)
        top_100_count = sum(1 for p in current_positions if p.position <= 100)

        # Identify insights
        biggest_gains = sorted(
            [c for c in changes if c.change < 0],  # Negative = improvement
            key=lambda x: x.change,
        )[:10]

        biggest_losses = sorted(
            [c for c in changes if c.change > 0],  # Positive = decline
            key=lambda x: x.change,
            reverse=True,
        )[:10]

        # Find new and lost rankings
        current_keywords = {p.keyword for p in current_positions}
        previous_keywords = {p.keyword for p in previous_positions}

        new_rankings = [
            p
            for p in current_positions
            if p.keyword not in previous_keywords and p.position <= 100
        ]
        lost_rankings = list(previous_keywords - current_keywords)

        result = RankTrackingResult(
            target_url=target_url,
            date_range=(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ),
            timestamp=datetime.now().isoformat(),
            positions=current_positions,
            changes=changes,
            competitor_positions=competitor_positions,
            avg_position=round(avg_position, 1),
            total_keywords=len(current_positions),
            top_3_count=top_3_count,
            top_10_count=top_10_count,
            top_100_count=top_100_count,
            biggest_gains=biggest_gains,
            biggest_losses=biggest_losses,
            new_rankings=new_rankings,
            lost_rankings=lost_rankings,
        )

        self.logger.info(
            "rank_tracking_complete",
            total_keywords=len(current_positions),
            avg_position=avg_position,
            top_10_count=top_10_count,
        )

        return result

    async def _fetch_our_positions(
        self,
        client: httpx.AsyncClient,
        target_url: str,
        keywords: list[str],
    ) -> list[KeywordPosition]:
        """
        Fetch our real keyword positions using SerpAPI.

        Searches for each keyword and finds our URL in the organic results.
        """
        if not self.serpapi_key:
            self.logger.warning("serpapi_key_not_set", action="returning_empty")
            return []

        domain = self._extract_domain(target_url)
        positions = []

        for keyword in keywords[:20]:
            try:
                params = {
                    "q": keyword,
                    "api_key": self.serpapi_key,
                    "engine": "google",
                    "hl": "ru",
                    "gl": "ru",
                    "num": 100,
                }
                response = await client.get(self.serpapi_base_url, params=params)
                response.raise_for_status()
                data = response.json()

                organic_results = data.get("organic_results", [])
                our_position = None
                our_url_match = ""

                for i, result in enumerate(organic_results, 1):
                    link = result.get("link", "")
                    if domain in link:
                        our_position = float(i)
                        our_url_match = link
                        break

                if our_position:
                    positions.append(
                        KeywordPosition(
                            keyword=keyword,
                            position=our_position,
                            url=our_url_match,
                            impressions=0,   # SerpAPI doesn't provide impressions
                            clicks=0,         # SerpAPI doesn't provide clicks
                            ctr=0.0,
                            date=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )

                await asyncio.sleep(0.5)  # Rate limit between keyword searches

            except Exception as e:
                self.logger.error("serpapi_position_fetch_error", keyword=keyword, error=str(e))
                continue

        return positions

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import re
        match = re.search(r"https?://([^/]+)", url)
        return match.group(1) if match else url

    async def _fetch_competitor_positions(
        self,
        client: httpx.AsyncClient,
        keywords: list[str],
    ) -> list[CompetitorPosition]:
        """
        Fetch competitor positions using SerpAPI.

        Note: Requires SerpAPI key for real data.
        """
        if not self.serpapi_key:
            self.logger.warning("serpapi_key_not_set")
            return []

        competitor_positions = []

        for keyword in keywords[:5]:  # Limit to 5 keywords to save API calls
            try:
                params = {
                    "q": keyword,
                    "api_key": self.serpapi_key,
                    "engine": "google",
                    "num": 10,
                }

                response = await client.get(
                    self.serpapi_base_url, params=params
                )
                await response.raise_for_status()
                data = await response.json()

                # Extract organic results
                organic_results = data.get("organic_results", [])

                for i, result in enumerate(organic_results, 1):
                    competitor_positions.append(
                        CompetitorPosition(
                            keyword=keyword,
                            competitor_url=result.get("link", ""),
                            position=i,
                            title=result.get("title", ""),
                            snippet=result.get("snippet", ""),
                        )
                    )

            except Exception as e:
                self.logger.error(
                    "serpapi_fetch_error",
                    keyword=keyword,
                    error=str(e),
                )

        return competitor_positions

    def _calculate_changes(
        self,
        current: list[KeywordPosition],
        previous: list[KeywordPosition],
    ) -> list[PositionChange]:
        """Calculate position changes between periods."""
        changes = []

        # Create lookup dict for previous positions
        previous_dict = {p.keyword: p.position for p in previous}

        for curr_pos in current:
            if curr_pos.keyword in previous_dict:
                prev_position = previous_dict[curr_pos.keyword]
                change = curr_pos.position - prev_position

                # Determine trend
                if abs(change) < 1:
                    trend = "stable"
                elif change < 0:
                    trend = "up"  # Lower position = better
                else:
                    trend = "down"

                # Calculate percent change
                change_percent = (
                    (change / prev_position * 100) if prev_position > 0 else 0.0
                )

                changes.append(
                    PositionChange(
                        keyword=curr_pos.keyword,
                        current_position=curr_pos.position,
                        previous_position=prev_position,
                        change=round(change, 1),
                        change_percent=round(change_percent, 1),
                        trend=trend,
                    )
                )

        return changes

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute rank tracking task from orchestrator.

        Args:
            task: Task with payload:
                - competitors: list of competitor dicts with 'url' key
                - keywords: list of keywords to track
                - our_url: our site URL

        Returns:
            TaskResult with rank tracking data
        """
        try:
            competitors = task.payload.get("competitors", [])
            keywords = task.payload.get("keywords", [])
            our_url = task.payload.get("our_url", "")

            # Generate keywords from niche if not provided
            if not keywords:
                niche = task.payload.get("niche", "")
                geo = task.payload.get("geo", "")
                if niche:
                    keywords = [
                        f"{niche} {geo}",
                        f"клиника {niche} {geo}",
                        f"лучшие {niche} {geo}",
                        f"{niche} {geo} цены",
                        f"{niche} {geo} отзывы",
                    ]

            if not our_url:
                # Use first competitor url or require our_url
                if not competitors:
                    return TaskResult(
                        subtask_id=task.subtask_id,
                        agent_id=self.agent_id,
                        action=task.action,
                        status="failed",
                        result={"error": "our_url or competitors required"},
                        error="our_url or competitors required",
                        duration_seconds=0.0,
                        completed_at=datetime.now(),
                    )
                our_url = competitors[0].get("url", "") if isinstance(competitors[0], dict) else str(competitors[0])

            if not self.serpapi_key:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={
                        "our_url": our_url,
                        "error": "SERPAPI_KEY not configured",
                        "avg_position": None,
                        "total_keywords": 0,
                        "positions": [],
                        "changes": [],
                        "competitor_positions": [],
                        "recommendation": "Configure SERPAPI_KEY to enable rank tracking.",
                    },
                    error="SERPAPI_KEY not configured",
                    duration_seconds=0.0,
                    completed_at=datetime.now(),
                )

            start_time = datetime.now()
            result = await self.track_rankings(
                target_url=our_url,
                keywords=keywords,
                days=7,
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result={
                    "target_url": result.target_url,
                    "avg_position": result.avg_position,
                    "total_keywords": result.total_keywords,
                    "top_3_count": result.top_3_count,
                    "top_10_count": result.top_10_count,
                    "top_100_count": result.top_100_count,
                    "positions": [
                        {
                            "keyword": p.keyword,
                            "position": p.position,
                            "url": p.url,
                        }
                        for p in result.positions[:20]
                    ],
                    "changes": [
                        {
                            "keyword": c.keyword,
                            "current_position": c.current_position,
                            "change": c.change,
                            "trend": c.trend,
                        }
                        for c in result.changes[:10]
                    ],
                    "competitor_positions": [
                        {
                            "keyword": cp.keyword,
                            "competitor_url": cp.competitor_url,
                            "position": cp.position,
                        }
                        for cp in result.competitor_positions[:20]
                    ],
                    "biggest_gains": [
                        {"keyword": bg.keyword, "change": bg.change}
                        for bg in result.biggest_gains[:5]
                    ],
                    "biggest_losses": [
                        {"keyword": bl.keyword, "change": bl.change}
                        for bl in result.biggest_losses[:5]
                    ],
                },
                error=None,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error("rank_tracker_execute_task_failed", error=str(e))
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=0.0,
                completed_at=datetime.now(),
            )

    def get_capabilities(self) -> list[str]:
        """Return list of agent capabilities."""
        return [
            "rank_tracking",
            "serp_position_monitoring",
            "keyword_performance",
            "competitor_position_analysis",
        ]


async def main():
    """Example usage."""
    import os

    serpapi_key = os.getenv("SERPAPI_KEY")

    agent = CIRankTrackerAgent(serpapi_key=serpapi_key)

    result = await agent.track_rankings(
        target_url="https://example.com",
        keywords=["seo tools", "keyword research", "backlink analysis"],
        days=7,
        compare_days=7,
    )

    print(f"Total Keywords: {result.total_keywords}")
    print(f"Average Position: {result.avg_position}")
    print(f"Top 10 Count: {result.top_10_count}")
    print()

    print("Biggest Gains:")
    for change in result.biggest_gains[:5]:
        print(
            f"  {change.keyword}: {change.previous_position:.1f} → "
            f"{change.current_position:.1f} ({change.change:+.1f})"
        )

    print("\nBiggest Losses:")
    for change in result.biggest_losses[:5]:
        print(
            f"  {change.keyword}: {change.previous_position:.1f} → "
            f"{change.current_position:.1f} ({change.change:+.1f})"
        )


if __name__ == "__main__":
    asyncio.run(main())
