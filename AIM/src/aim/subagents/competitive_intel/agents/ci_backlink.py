"""
CI Backlink Agent - Backlink Profile Analysis.

Analyzes competitor backlink profiles using Ahrefs API.
Provides insights on link building opportunities and strategies.

Based on: ahrefs-python SDK (official)
Source: https://github.com/ahrefs/ahrefs-python
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
import structlog

from meai.agents.base_agent import Agent, Task, TaskResult


@dataclass
class BacklinkStats:
    """Backlink statistics."""

    live: int
    live_refdomains: int
    dofollow: int
    nofollow: int
    gov: int
    edu: int
    text: int
    image: int
    redirect: int
    canonical: int


@dataclass
class DomainMetrics:
    """Domain authority metrics."""

    domain_rating: float
    ahrefs_rank: int
    org_keywords: int
    org_traffic: int
    refdomains: int


@dataclass
class BacklinkOpportunity:
    """Link building opportunity."""

    domain: str
    domain_rating: float
    backlinks_to_competitor: int
    backlinks_to_us: int
    gap: int
    opportunity_score: float


@dataclass
class BacklinkAnalysisResult:
    """Complete backlink analysis result."""

    target_url: str
    our_url: str
    timestamp: str

    # Our metrics
    our_stats: BacklinkStats
    our_metrics: DomainMetrics

    # Competitor metrics
    competitor_stats: BacklinkStats
    competitor_metrics: DomainMetrics

    # Gap analysis
    backlink_gap: int
    refdomains_gap: int
    dr_gap: float

    # Opportunities
    opportunities: list[BacklinkOpportunity]

    # Summary
    summary: str
    recommendations: list[str]


class CIBacklinkAgent(Agent):
    """
    Competitive Intelligence Backlink Agent.

    Analyzes competitor backlink profiles and identifies
    link building opportunities using Ahrefs API.
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str | None = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian",
    ):
        """
        Initialize CI Backlink Agent.

        Args:
            agent_id: Unique agent identifier
            api_key: Ahrefs API key (or set AHREFS_API_KEY env var)
            database_url: Database connection URL
            vault_path: Obsidian vault path
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-backlink",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.logger = structlog.get_logger()
        self.api_key = api_key or os.getenv("AHREFS_API_KEY")
        self.base_url = "https://api.ahrefs.com/v3"
        self.timeout = httpx.Timeout(30.0)

    async def analyze(
        self,
        target_url: str,
        our_url: str,
        date: str | None = None,
    ) -> BacklinkAnalysisResult:
        """
        Analyze competitor backlink profile vs ours.

        Args:
            target_url: Competitor URL to analyze
            our_url: Our URL for comparison
            date: Analysis date (YYYY-MM-DD), defaults to latest

        Returns:
            Complete backlink analysis with opportunities
        """
        self.logger.info(
            "backlink_analysis_start",
            target=target_url,
            our_url=our_url,
        )

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Fetch competitor data
            competitor_stats = await self._fetch_backlinks_stats(
                client, target_url, date
            )
            competitor_metrics = await self._fetch_metrics(
                client, target_url, date
            )

            # Fetch our data
            our_stats = await self._fetch_backlinks_stats(
                client, our_url, date
            )
            our_metrics = await self._fetch_metrics(
                client, our_url, date
            )

            # Calculate gaps
            backlink_gap = competitor_stats.live - our_stats.live
            refdomains_gap = (
                competitor_stats.live_refdomains - our_stats.live_refdomains
            )
            dr_gap = competitor_metrics.domain_rating - our_metrics.domain_rating

            # Find opportunities (domains linking to competitor but not us)
            opportunities = await self._find_opportunities(
                client,
                target_url,
                our_url,
                date,
            )

            # Generate summary and recommendations
            summary = self._generate_summary(
                competitor_stats,
                our_stats,
                backlink_gap,
                refdomains_gap,
                dr_gap,
            )
            recommendations = self._generate_recommendations(
                backlink_gap,
                refdomains_gap,
                dr_gap,
                opportunities,
            )

        result = BacklinkAnalysisResult(
            target_url=target_url,
            our_url=our_url,
            timestamp=datetime.now().isoformat(),
            our_stats=our_stats,
            our_metrics=our_metrics,
            competitor_stats=competitor_stats,
            competitor_metrics=competitor_metrics,
            backlink_gap=backlink_gap,
            refdomains_gap=refdomains_gap,
            dr_gap=dr_gap,
            opportunities=opportunities,
            summary=summary,
            recommendations=recommendations,
        )

        self.logger.info(
            "backlink_analysis_complete",
            backlink_gap=backlink_gap,
            refdomains_gap=refdomains_gap,
            opportunities_found=len(opportunities),
        )

        return result

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute backlink analysis task from orchestrator.

        Args:
            task: Task with payload:
                - competitors: list of competitor dicts with 'url' key
                - our_url: our site URL (optional, uses first competitor as reference)

        Returns:
            TaskResult with backlink analysis
        """
        try:
            competitors = task.payload.get("competitors", [])
            our_url = task.payload.get("our_url", "")

            if not competitors:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={"error": "No competitors provided"},
                    error="No competitors provided",
                    duration_seconds=0.0,
                    completed_at=datetime.now(),
                )

            # Use first competitor URL as target
            target = competitors[0]
            target_url = target.get("url", "") if isinstance(target, dict) else str(target)

            if not target_url:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={"error": "No valid competitor URL"},
                    error="No valid competitor URL",
                    duration_seconds=0.0,
                    completed_at=datetime.now(),
                )

            # If no our_url, use a placeholder (real analysis needs our URL)
            if not our_url:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={
                        "error": "our_url is required for backlink comparison",
                        "target_url": target_url,
                    },
                    error="our_url is required",
                    duration_seconds=0.0,
                    completed_at=datetime.now(),
                )

            # Run real Ahrefs analysis
            if not self.api_key:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={
                        "target_url": target_url,
                        "our_url": our_url,
                        "error": "AHREFS_API_KEY not configured",
                        "backlink_gap": None,
                        "refdomains_gap": None,
                        "dr_gap": None,
                        "opportunities": [],
                        "summary": "Ahrefs API key not available. Backlink analysis skipped.",
                        "recommendations": ["Configure AHREFS_API_KEY to enable backlink analysis."],
                    },
                    error="AHREFS_API_KEY not configured",
                    duration_seconds=0.0,
                    completed_at=datetime.now(),
                )

            start_time = datetime.now()
            result = await self.analyze(target_url=target_url, our_url=our_url)

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result={
                    "target_url": result.target_url,
                    "our_url": result.our_url,
                    "backlink_gap": result.backlink_gap,
                    "refdomains_gap": result.refdomains_gap,
                    "dr_gap": result.dr_gap,
                    "our_stats": {
                        "live": result.our_stats.live,
                        "live_refdomains": result.our_stats.live_refdomains,
                        "dofollow": result.our_stats.dofollow,
                    },
                    "competitor_stats": {
                        "live": result.competitor_stats.live,
                        "live_refdomains": result.competitor_stats.live_refdomains,
                        "dofollow": result.competitor_stats.dofollow,
                    },
                    "opportunities": [
                        {
                            "domain": o.domain,
                            "domain_rating": o.domain_rating,
                            "gap": o.gap,
                            "opportunity_score": o.opportunity_score,
                        }
                        for o in result.opportunities[:10]
                    ],
                    "summary": result.summary,
                    "recommendations": result.recommendations,
                },
                error=None,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error("backlink_execute_task_failed", error=str(e))
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
            "backlink_analysis",
            "link_gap_analysis",
            "domain_authority_analysis",
            "link_building_opportunities",
        ]

    async def _fetch_backlinks_stats(
        self,
        client: httpx.AsyncClient,
        target: str,
        date: str,
    ) -> BacklinkStats:
        """Fetch backlink statistics from Ahrefs API."""
        url = f"{self.base_url}/site-explorer/backlinks-stats"
        params = {
            "target": target,
            "date": date,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = await client.get(url, params=params, headers=headers)
        await response.raise_for_status()
        data = await response.json()

        return BacklinkStats(
            live=data.get("live", 0),
            live_refdomains=data.get("live_refdomains", 0),
            dofollow=data.get("dofollow", 0),
            nofollow=data.get("nofollow", 0),
            gov=data.get("gov", 0),
            edu=data.get("edu", 0),
            text=data.get("text", 0),
            image=data.get("image", 0),
            redirect=data.get("redirect", 0),
            canonical=data.get("canonical", 0),
        )

    async def _fetch_metrics(
        self,
        client: httpx.AsyncClient,
        target: str,
        date: str,
    ) -> DomainMetrics:
        """Fetch domain metrics from Ahrefs API."""
        url = f"{self.base_url}/site-explorer/metrics"
        params = {
            "target": target,
            "date": date,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = await client.get(url, params=params, headers=headers)
        await response.raise_for_status()
        data = await response.json()

        return DomainMetrics(
            domain_rating=data.get("domain_rating", 0.0),
            ahrefs_rank=data.get("ahrefs_rank", 0),
            org_keywords=data.get("org_keywords", 0),
            org_traffic=data.get("org_traffic", 0),
            refdomains=data.get("refdomains", 0),
        )

    async def _find_opportunities(
        self,
        client: httpx.AsyncClient,
        target_url: str,
        our_url: str,
        date: str,
    ) -> list[BacklinkOpportunity]:
        """
        Find link building opportunities.

        Identifies domains linking to competitor but not to us.
        """
        # Fetch competitor's referring domains
        url = f"{self.base_url}/site-explorer/linkeddomains"
        params = {
            "target": target_url,
            "date": date,
            "limit": 50,  # Top 50 referring domains
            "order_by": "domain_rating:desc",
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = await client.get(url, params=params, headers=headers)
        await response.raise_for_status()
        response_data = await response.json()
        competitor_domains = response_data.get("linkeddomains", [])

        # Fetch our referring domains
        params["target"] = our_url
        response = await client.get(url, params=params, headers=headers)
        await response.raise_for_status()
        response_data = await response.json()
        our_domains = response_data.get("linkeddomains", [])

        # Create set of our domains for fast lookup
        our_domain_set = {d["domain"] for d in our_domains}

        # Find gaps (domains linking to competitor but not us)
        opportunities = []
        for domain_data in competitor_domains:
            domain = domain_data["domain"]
            if domain not in our_domain_set:
                # Calculate opportunity score
                # Higher DR + more backlinks to competitor = better opportunity
                dr = domain_data.get("domain_rating", 0.0)
                backlinks = domain_data.get("backlinks", 0)

                opportunity_score = (dr / 100.0) * 0.7 + (
                    min(backlinks, 100) / 100.0
                ) * 0.3

                opportunities.append(
                    BacklinkOpportunity(
                        domain=domain,
                        domain_rating=dr,
                        backlinks_to_competitor=backlinks,
                        backlinks_to_us=0,
                        gap=backlinks,
                        opportunity_score=round(opportunity_score, 2),
                    )
                )

        # Sort by opportunity score
        opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)

        return opportunities[:20]  # Top 20 opportunities

    def _generate_summary(
        self,
        competitor_stats: BacklinkStats,
        our_stats: BacklinkStats,
        backlink_gap: int,
        refdomains_gap: int,
        dr_gap: float,
    ) -> str:
        """Generate analysis summary."""
        if backlink_gap > 0:
            gap_direction = f"Competitor has {backlink_gap:,} more backlinks"
        else:
            gap_direction = f"We have {abs(backlink_gap):,} more backlinks"

        if refdomains_gap > 0:
            domain_direction = f"Competitor has {refdomains_gap:,} more referring domains"
        else:
            domain_direction = f"We have {abs(refdomains_gap):,} more referring domains"

        if dr_gap > 0:
            dr_direction = f"Competitor has {dr_gap:.1f} higher Domain Rating"
        else:
            dr_direction = f"We have {abs(dr_gap):.1f} higher Domain Rating"

        return f"""
Backlink Profile Comparison:

Total Backlinks:
- Competitor: {competitor_stats.live:,} live backlinks
- Us: {our_stats.live:,} live backlinks
- Gap: {gap_direction}

Referring Domains:
- Competitor: {competitor_stats.live_refdomains:,} domains
- Us: {our_stats.live_refdomains:,} domains
- Gap: {domain_direction}

Domain Authority:
- {dr_direction}

Link Quality:
- Competitor dofollow: {competitor_stats.dofollow:,} ({competitor_stats.dofollow/max(competitor_stats.live,1)*100:.1f}%)
- Our dofollow: {our_stats.dofollow:,} ({our_stats.dofollow/max(our_stats.live,1)*100:.1f}%)
""".strip()

    def _generate_recommendations(
        self,
        backlink_gap: int,
        refdomains_gap: int,
        dr_gap: float,
        opportunities: list[BacklinkOpportunity],
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Gap-based recommendations
        if backlink_gap > 1000:
            recommendations.append(
                f"CRITICAL: Large backlink gap ({backlink_gap:,}). "
                "Prioritize aggressive link building campaign."
            )
        elif backlink_gap > 100:
            recommendations.append(
                f"Moderate backlink gap ({backlink_gap:,}). "
                "Increase link building efforts."
            )

        if refdomains_gap > 50:
            recommendations.append(
                f"Focus on domain diversity. Need {refdomains_gap} more referring domains."
            )

        if dr_gap > 10:
            recommendations.append(
                f"Domain Rating gap is significant ({dr_gap:.1f}). "
                "Focus on high-authority backlinks."
            )

        # Opportunity-based recommendations
        if opportunities:
            top_opportunities = opportunities[:5]
            avg_dr = sum(o.domain_rating for o in top_opportunities) / len(
                top_opportunities
            )
            recommendations.append(
                f"Found {len(opportunities)} link building opportunities. "
                f"Top 5 have average DR of {avg_dr:.1f}."
            )

            # Specific outreach targets
            for i, opp in enumerate(top_opportunities[:3], 1):
                recommendations.append(
                    f"Priority {i}: Reach out to {opp.domain} "
                    f"(DR {opp.domain_rating:.0f}, {opp.backlinks_to_competitor} links to competitor)"
                )

        if not recommendations:
            recommendations.append(
                "Backlink profile is competitive. Maintain current link building pace."
            )

        return recommendations


async def main():
    """Example usage."""
    import os

    api_key = os.getenv("AHREFS_API_KEY")
    if not api_key:
        print("Error: AHREFS_API_KEY environment variable not set")
        return

    agent = CIBacklinkAgent(api_key=api_key)

    result = await agent.analyze(
        target_url="competitor.com",
        our_url="oursite.com",
    )

    print(result.summary)
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"- {rec}")

    print(f"\nTop 5 Opportunities:")
    for opp in result.opportunities[:5]:
        print(
            f"- {opp.domain} (DR {opp.domain_rating:.0f}, "
            f"Score {opp.opportunity_score:.2f})"
        )


if __name__ == "__main__":
    asyncio.run(main())
