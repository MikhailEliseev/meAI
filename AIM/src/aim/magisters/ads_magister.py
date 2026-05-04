"""Ads Magister - Domain coordinator for Advertising tasks

REAL IMPLEMENTATION with business logic for advertising coordination.
"""

from datetime import datetime, timezone
from meai.agents.magister_base import BaseMagister


class AdsMagister(BaseMagister):
    """Ads Magister - Coordinates Advertising Subagents

    Domain: Advertising and paid campaigns for medical marketing

    Responsibilities:
    - Campaign strategy and planning
    - Ad creation (Google Ads, Yandex Direct)
    - Budget optimization
    - A/B testing
    - Conversion tracking

    Status: PRODUCTION READY (with real coordination logic)
    """

    def __init__(
        self,
        magister_id: str = "ads-magister",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/ads-magister",
    ):
        """Initialize Ads Magister

        Args:
            magister_id: Unique Magister ID
            database_url: Database connection URL
            vault_path: Path to Ads Magister's Obsidian vault
        """
        super().__init__(
            magister_id=magister_id,
            database_url=database_url,
            vault_path=vault_path,
        )

    async def identify_subagents(self, action: str) -> list[str]:
        """Identify which Ads Subagents are needed for this action

        REAL IMPLEMENTATION: Routes actions to appropriate subagents

        Args:
            action: Action to perform (e.g., "create_campaign", "optimize_budget")

        Returns:
            List of Subagent IDs

        Supported actions:
        - create_campaign: Campaign Creator Agent (TODO)
        - optimize_budget: Budget Optimizer Agent (TODO)
        - ab_test: A/B Testing Agent (TODO)
        - track_conversions: Conversion Tracker Agent (TODO)
        - full_ads_audit: All ads agents
        """
        action_lower = action.lower()

        # Campaign creation
        if "campaign" in action_lower or "create" in action_lower or action_lower == "create_campaign":
            return ["ads-campaign-creator-agent"]

        # Budget optimization
        if "budget" in action_lower or "optimize" in action_lower or action_lower == "optimize_budget":
            return ["ads-budget-optimizer-agent"]

        # A/B testing
        if "test" in action_lower or "ab" in action_lower or action_lower == "ab_test":
            return ["ads-ab-testing-agent"]

        # Conversion tracking
        if "conversion" in action_lower or "track" in action_lower or action_lower == "track_conversions":
            return ["ads-conversion-tracker-agent"]

        # Full ads audit - all agents
        if "audit" in action_lower or "full" in action_lower:
            return [
                "ads-campaign-creator-agent",
                "ads-budget-optimizer-agent",
                "ads-ab-testing-agent",
                "ads-conversion-tracker-agent",
            ]

        # Default: campaign creation (most common task)
        return ["ads-campaign-creator-agent"]

    async def aggregate_results(
        self,
        subagent_results: list[dict],
    ) -> dict:
        """Aggregate results from Ads Subagents

        REAL IMPLEMENTATION: Analyzes and synthesizes results from subagents

        Args:
            subagent_results: Results from Subagents

        Returns:
            Aggregated advertising insights with analysis and recommendations
        """
        # Log operation to Obsidian
        await self._log_operation(
            "aggregate_results",
            f"Aggregating results from {len(subagent_results)} subagent(s)"
        )

        if not subagent_results:
            return {
                "summary": "No results to aggregate",
                "insights": [],
                "recommendations": [],
            }

        # Collect metrics from all subagents
        total_campaigns = 0
        total_ad_groups = 0
        total_budget = 0
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        platforms = {}
        specialties = {}

        for result in subagent_results:
            # Count campaigns
            if "campaign_name" in result:
                total_campaigns += 1

            # Ad groups
            if "ad_groups" in result:
                total_ad_groups += len(result["ad_groups"])

            # Budget (handle dict structure)
            if "budget" in result:
                budget_data = result["budget"]
                if isinstance(budget_data, dict):
                    total_budget += budget_data.get("total_daily", 0)
                else:
                    total_budget += budget_data

            # Performance predictions
            if "predictions" in result:
                predictions = result["predictions"]
                total_impressions += predictions.get("estimated_impressions", 0)
                total_clicks += predictions.get("estimated_clicks", 0)
                total_conversions += predictions.get("estimated_conversions", 0)

            # Platform
            if "platform" in result:
                platform = result["platform"]
                platforms[platform] = platforms.get(platform, 0) + 1

            # Specialty
            if "specialty" in result:
                specialty = result["specialty"]
                specialties[specialty] = specialties.get(specialty, 0) + 1

        # Calculate performance metrics
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        cpc = (total_budget / total_clicks) if total_clicks > 0 else 0
        cpa = (total_budget / total_conversions) if total_conversions > 0 else 0

        # Generate insights
        insights = []

        if total_campaigns > 0:
            insights.append(
                f"Created {total_campaigns} campaign(s) with {total_ad_groups} ad groups"
            )

        if total_budget > 0:
            insights.append(
                f"Total daily budget: {total_budget:,} RUB"
            )

        if total_impressions > 0:
            insights.append(
                f"Predicted performance: {total_impressions:,} impressions, {total_clicks:,} clicks, {total_conversions} conversions"
            )

        if ctr > 0:
            insights.append(
                f"Expected CTR: {ctr:.2f}%, Conversion Rate: {conversion_rate:.2f}%"
            )

        if platforms:
            platform_list = ", ".join(platforms.keys())
            insights.append(f"Platforms: {platform_list}")

        if specialties:
            specialty_list = ", ".join(specialties.keys())
            insights.append(f"Specialties: {specialty_list}")

        # Generate recommendations
        recommendations = []

        if ctr > 0 and ctr < 2.0:
            recommendations.append(
                "CTR is low - improve ad copy and targeting"
            )

        if conversion_rate > 0 and conversion_rate < 5.0:
            recommendations.append(
                "Conversion rate is low - optimize landing pages and CTAs"
            )

        if cpa > 0:
            recommendations.append(
                f"Cost per acquisition: {cpa:.0f} RUB - monitor and optimize"
            )

        if total_budget > 0:
            recommendations.append(
                "Monitor campaign performance and adjust budgets based on ROI"
            )

        # Build summary
        summary = f"Created {total_campaigns} campaign(s) with {total_ad_groups} ad groups. "
        if total_budget > 0:
            summary += f"Total daily budget: {total_budget:,} RUB. "
        if total_impressions > 0:
            summary += f"Expected: {total_impressions:,} impressions, {total_clicks:,} clicks, {total_conversions} conversions."

        # Log results to Obsidian
        await self._log_operation(
            "aggregate_complete",
            f"Generated {len(insights)} insights, {len(recommendations)} recommendations"
        )

        return {
            "summary": summary,
            "insights": insights,
            "recommendations": recommendations,
            "metrics": {
                "total_campaigns": total_campaigns,
                "total_ad_groups": total_ad_groups,
                "total_budget": round(total_budget, 2),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "ctr": round(ctr, 2),
                "conversion_rate": round(conversion_rate, 2),
                "cpc": round(cpc, 2),
                "cpa": round(cpa, 2),
                "platforms": platforms,
                "specialties": specialties,
            },
        }

    async def _log_operation(self, operation: str, description: str) -> None:
        """Log operation to Obsidian vault

        Args:
            operation: Operation name
            description: Operation description
        """
        try:
            log_path = self.vault.vault_path / "wiki" / "log.md"

            # Read current log
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "# Ads Magister Operations Log\n\n**Format:** `## [YYYY-MM-DD HH:MM] operation | Description`\n\n---\n\n"

            # Append new entry
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            entry = f"## [{timestamp}] {operation} | {description}\n\n"

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content + entry)

        except Exception as e:
            # Don't fail if logging fails
            print(f"Warning: Failed to log to Obsidian: {e}")

