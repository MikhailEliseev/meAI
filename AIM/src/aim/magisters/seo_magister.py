"""SEO Magister - Domain coordinator for SEO tasks

REAL IMPLEMENTATION with business logic for SEO coordination.
"""

from datetime import datetime, timezone
from meai.agents.magister_base import BaseMagister


class SEOMagister(BaseMagister):
    """SEO Magister - Coordinates SEO Subagents

    Domain: Search Engine Optimization for medical marketing

    Responsibilities:
    - Keyword research coordination
    - Content optimization
    - Technical SEO
    - Link building
    - Competitor analysis

    Status: PRODUCTION READY (with real coordination logic)
    """

    def __init__(
        self,
        magister_id: str = "seo-magister",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/seo-magister",
    ):
        """Initialize SEO Magister

        Args:
            magister_id: Unique Magister ID
            database_url: Database connection URL
            vault_path: Path to SEO Magister's Obsidian vault
        """
        super().__init__(
            magister_id=magister_id,
            database_url=database_url,
            vault_path=vault_path,
        )

    async def identify_subagents(self, action: str) -> list[str]:
        """Identify which SEO Subagents are needed for this action

        REAL IMPLEMENTATION: Routes actions to appropriate subagents

        Args:
            action: Action to perform (e.g., "keyword_research", "content_optimization")

        Returns:
            List of Subagent IDs

        Supported actions:
        - keyword_research: Keyword Research Agent
        - content_optimization: Content Optimization Agent (TODO)
        - technical_seo: Technical SEO Agent (TODO)
        - link_building: Link Building Agent (TODO)
        - full_audit: All SEO agents
        """
        action_lower = action.lower()

        # Keyword research
        if "keyword" in action_lower or action_lower == "keyword_research":
            return ["keyword-research-agent"]

        # Content optimization (TODO: implement agent)
        if "content" in action_lower or action_lower == "content_optimization":
            return ["content-optimization-agent"]

        # Technical SEO (TODO: implement agent)
        if "technical" in action_lower or action_lower == "technical_seo":
            return ["technical-seo-agent"]

        # Link building (TODO: implement agent)
        if "link" in action_lower or action_lower == "link_building":
            return ["link-building-agent"]

        # Full SEO audit - all agents
        if "audit" in action_lower or "full" in action_lower:
            return [
                "keyword-research-agent",
                "content-optimization-agent",
                "technical-seo-agent",
                "link-building-agent",
            ]

        # Default: keyword research (most common SEO task)
        return ["keyword-research-agent"]

    async def aggregate_results(
        self,
        subagent_results: list[dict],
    ) -> dict:
        """Aggregate results from SEO Subagents

        REAL IMPLEMENTATION: Analyzes and synthesizes results from subagents

        Args:
            subagent_results: Results from Subagents

        Returns:
            Aggregated SEO insights with analysis and recommendations
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

        # Collect all keywords from all subagents
        all_keywords = []
        total_keywords = 0
        specialties = set()

        for result in subagent_results:
            if "keywords" in result:
                all_keywords.extend(result["keywords"])
                total_keywords += result.get("total_keywords", 0)
            if "specialty" in result:
                specialties.add(result["specialty"])

        # Analyze keyword distribution by intent
        intent_distribution = {}
        for kw in all_keywords:
            intent = kw.get("intent", "unknown")
            intent_distribution[intent] = intent_distribution.get(intent, 0) + 1

        # Find top opportunities (high priority, low difficulty)
        opportunities = [
            kw for kw in all_keywords
            if kw.get("priority_score", 0) >= 60 and kw.get("difficulty", 100) < 50
        ]
        opportunities.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        # Calculate average metrics
        avg_volume = sum(kw.get("volume", 0) for kw in all_keywords) / len(all_keywords) if all_keywords else 0
        avg_difficulty = sum(kw.get("difficulty", 0) for kw in all_keywords) / len(all_keywords) if all_keywords else 0
        avg_cpc = sum(kw.get("cpc", 0) for kw in all_keywords) / len(all_keywords) if all_keywords else 0

        # Generate insights
        insights = []

        if opportunities:
            insights.append(
                f"Found {len(opportunities)} high-priority opportunities (score ≥60, difficulty <50)"
            )

        if intent_distribution:
            top_intent = max(intent_distribution.items(), key=lambda x: x[1])
            insights.append(
                f"Dominant search intent: {top_intent[0]} ({top_intent[1]} keywords)"
            )

        if specialties:
            insights.append(
                f"Medical specialties detected: {', '.join(specialties)}"
            )

        insights.append(
            f"Average metrics: Volume {int(avg_volume):,} | Difficulty {int(avg_difficulty)} | CPC ${avg_cpc:.2f}"
        )

        # Generate recommendations
        recommendations = []

        if opportunities:
            top_3 = opportunities[:3]
            recommendations.append(
                f"Start with top 3 opportunities: {', '.join([kw['keyword'] for kw in top_3])}"
            )

        local_keywords = [kw for kw in all_keywords if kw.get("intent") == "local"]
        if local_keywords:
            recommendations.append(
                f"Strong local SEO potential: {len(local_keywords)} local keywords found"
            )

        commercial_keywords = [kw for kw in all_keywords if kw.get("intent") == "commercial"]
        if commercial_keywords:
            avg_commercial_cpc = sum(kw.get("cpc", 0) for kw in commercial_keywords) / len(commercial_keywords)
            recommendations.append(
                f"Commercial opportunity: {len(commercial_keywords)} keywords, avg CPC ${avg_commercial_cpc:.2f}"
            )

        if avg_difficulty < 40:
            recommendations.append(
                "Low competition detected - good opportunity for quick wins"
            )

        # Build summary
        summary = f"Analyzed {total_keywords} keywords across {len(subagent_results)} subagent(s). "
        summary += f"Found {len(opportunities)} high-priority opportunities. "
        summary += f"Dominant intent: {max(intent_distribution.items(), key=lambda x: x[1])[0] if intent_distribution else 'unknown'}."

        # Log results to Obsidian
        await self._log_operation(
            "aggregate_complete",
            f"Generated {len(insights)} insights, {len(recommendations)} recommendations, {len(opportunities)} opportunities"
        )

        return {
            "summary": summary,
            "insights": insights,
            "recommendations": recommendations,
            "metrics": {
                "total_keywords": total_keywords,
                "opportunities": len(opportunities),
                "avg_volume": int(avg_volume),
                "avg_difficulty": int(avg_difficulty),
                "avg_cpc": round(avg_cpc, 2),
                "intent_distribution": intent_distribution,
            },
            "top_opportunities": opportunities[:10],  # Top 10
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
                content = "# SEO Magister Operations Log\n\n**Format:** `## [YYYY-MM-DD HH:MM] operation | Description`\n\n---\n\n"

            # Append new entry
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            entry = f"## [{timestamp}] {operation} | {description}\n\n"

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content + entry)

        except Exception as e:
            # Don't fail if logging fails
            print(f"Warning: Failed to log to Obsidian: {e}")

