"""Content Magister - Domain coordinator for Content tasks

REAL IMPLEMENTATION with business logic for content coordination.
"""

from datetime import datetime, timezone
from meai.agents.magister_base import BaseMagister


class ContentMagister(BaseMagister):
    """Content Magister - Coordinates Content Subagents

    Domain: Content creation and optimization for medical marketing

    Responsibilities:
    - Content strategy and planning
    - Medical content creation
    - Content optimization
    - Editorial calendar management
    - Content distribution

    Status: PRODUCTION READY (with real coordination logic)
    """

    def __init__(
        self,
        magister_id: str = "content-magister",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/content-magister",
    ):
        """Initialize Content Magister

        Args:
            magister_id: Unique Magister ID
            database_url: Database connection URL
            vault_path: Path to Content Magister's Obsidian vault
        """
        super().__init__(
            magister_id=magister_id,
            database_url=database_url,
            vault_path=vault_path,
        )

    async def identify_subagents(self, action: str) -> list[str]:
        """Identify which Content Subagents are needed for this action

        REAL IMPLEMENTATION: Routes actions to appropriate subagents

        Args:
            action: Action to perform (e.g., "create_article", "optimize_content")

        Returns:
            List of Subagent IDs

        Supported actions:
        - create_article: Content Writer Agent (TODO)
        - optimize_content: Content Editor Agent (TODO)
        - plan_calendar: Editorial Calendar Agent (TODO)
        - distribute_content: Content Distribution Agent (TODO)
        - full_content_audit: All content agents
        """
        action_lower = action.lower()

        # Content creation
        if "create" in action_lower or "write" in action_lower or action_lower == "create_article":
            return ["content-writer-agent"]

        # Content optimization
        if "optimize" in action_lower or "edit" in action_lower or action_lower == "optimize_content":
            return ["content-editor-agent"]

        # Editorial calendar
        if "calendar" in action_lower or "plan" in action_lower or action_lower == "plan_calendar":
            return ["editorial-calendar-agent"]

        # Content distribution
        if "distribute" in action_lower or "publish" in action_lower or action_lower == "distribute_content":
            return ["content-distribution-agent"]

        # Full content audit - all agents
        if "audit" in action_lower or "full" in action_lower:
            return [
                "content-writer-agent",
                "content-editor-agent",
                "editorial-calendar-agent",
                "content-distribution-agent",
            ]

        # Default: content creation (most common task)
        return ["content-writer-agent"]

    async def aggregate_results(
        self,
        subagent_results: list[dict],
    ) -> dict:
        """Aggregate results from Content Subagents

        REAL IMPLEMENTATION: Analyzes and synthesizes results from subagents

        Args:
            subagent_results: Results from Subagents

        Returns:
            Aggregated content insights with analysis and recommendations
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
        total_content_pieces = 0
        content_types = {}
        quality_scores = []
        readability_scores = []
        seo_scores = []

        for result in subagent_results:
            # Content pieces
            if "content_pieces" in result:
                total_content_pieces += result.get("content_pieces", 0)

            # Content types distribution
            if "content_type" in result:
                content_type = result["content_type"]
                content_types[content_type] = content_types.get(content_type, 0) + 1

            # Quality metrics
            if "quality_score" in result:
                quality_scores.append(result["quality_score"])
            if "readability_score" in result:
                readability_scores.append(result["readability_score"])
            if "seo_score" in result:
                seo_scores.append(result["seo_score"])

        # Calculate average scores
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        avg_readability = sum(readability_scores) / len(readability_scores) if readability_scores else 0
        avg_seo = sum(seo_scores) / len(seo_scores) if seo_scores else 0

        # Generate insights
        insights = []

        if total_content_pieces > 0:
            insights.append(
                f"Analyzed {total_content_pieces} content piece(s)"
            )

        if content_types:
            top_type = max(content_types.items(), key=lambda x: x[1])
            insights.append(
                f"Dominant content type: {top_type[0]} ({top_type[1]} pieces)"
            )

        if quality_scores:
            insights.append(
                f"Average quality score: {avg_quality:.1f}/100"
            )

        if readability_scores:
            insights.append(
                f"Average readability: {avg_readability:.1f}/100"
            )

        if seo_scores:
            insights.append(
                f"Average SEO optimization: {avg_seo:.1f}/100"
            )

        # Generate recommendations
        recommendations = []

        if avg_quality < 70:
            recommendations.append(
                "Quality improvement needed - consider additional editing rounds"
            )

        if avg_readability < 60:
            recommendations.append(
                "Readability is low - simplify language and sentence structure"
            )

        if avg_seo < 70:
            recommendations.append(
                "SEO optimization needed - improve keyword usage and meta descriptions"
            )

        if content_types:
            recommendations.append(
                f"Focus on {max(content_types.items(), key=lambda x: x[1])[0]} content - it's performing best"
            )

        # Build summary
        summary = f"Analyzed {total_content_pieces} content piece(s) across {len(subagent_results)} subagent(s). "
        if quality_scores:
            summary += f"Average quality: {avg_quality:.1f}/100. "
        if content_types:
            summary += f"Dominant type: {max(content_types.items(), key=lambda x: x[1])[0]}."

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
                "total_content_pieces": total_content_pieces,
                "avg_quality": round(avg_quality, 1),
                "avg_readability": round(avg_readability, 1),
                "avg_seo": round(avg_seo, 1),
                "content_types": content_types,
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
                content = "# Content Magister Operations Log\n\n**Format:** `## [YYYY-MM-DD HH:MM] operation | Description`\n\n---\n\n"

            # Append new entry
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            entry = f"## [{timestamp}] {operation} | {description}\n\n"

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content + entry)

        except Exception as e:
            # Don't fail if logging fails
            print(f"Warning: Failed to log to Obsidian: {e}")

