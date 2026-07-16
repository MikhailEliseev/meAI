# src/meai/agents/magisters/seo_magister.py
"""SEO Magister - SEO specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class SEOMagister(BaseMagister):
    """SEO Magister - specializes in SEO strategies and optimization"""

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
    ):
        """Initialize SEO Magister

        Args:
            agent_id: Unique agent identifier
            database_url: Database URL
            vault_path: Path to Obsidian vault
            event_bus: Event bus for communication
            teacher: Teacher agent reference
        """
        super().__init__(
            agent_id=agent_id,
            database_url=database_url,
            vault_path=vault_path,
            event_bus=event_bus,
            teacher=teacher,
        )

    def get_domain(self) -> str:
        """Return SEO domain"""
        return "seo"

    def get_capabilities(self) -> list[str]:
        """Return SEO Magister capabilities"""
        return [
            "search",
            "store_knowledge",
            "analyze_keywords",
            "optimize_content",
            "analyze_competitors",
        ]

    async def analyze_keywords(self, topic: str) -> dict[str, Any]:
        """
        Analyze keywords for a topic.

        Args:
            topic: Topic to analyze

        Returns:
            Keyword analysis results
        """
        # Search for keyword knowledge
        results = await self.hybrid_search(f"keyword analysis {topic}")

        return {
            "status": "success",
            "topic": topic,
            "keywords": self._extract_keywords(results),
            "source": results.get("source", "unknown"),
        }

    async def optimize_content(
        self,
        content: str,
        target_keywords: list[str],
    ) -> dict[str, Any]:
        """
        Optimize content for SEO.

        Args:
            content: Content to optimize
            target_keywords: Target keywords

        Returns:
            Optimized content
        """
        # Simple optimization: ensure keywords are present
        optimized = content

        for keyword in target_keywords:
            if keyword.lower() not in content.lower():
                optimized += f"\n\nKeyword: {keyword}"

        return {
            "status": "success",
            "original_length": len(content),
            "optimized_length": len(optimized),
            "optimized_content": optimized,
            "keywords_added": target_keywords,
        }

    async def analyze_competitors(
        self,
        domain: str,
        keywords: list[str],
    ) -> dict[str, Any]:
        """
        Analyze competitors for domain and keywords.

        Args:
            domain: Competitor domain
            keywords: Keywords to analyze

        Returns:
            Competitor analysis
        """
        # Search for competitor knowledge
        query = f"competitor analysis {domain} {' '.join(keywords)}"
        results = await self.hybrid_search(query)

        return {
            "status": "success",
            "domain": domain,
            "keywords": keywords,
            "analysis": self._extract_competitor_insights(results),
            "source": results.get("source", "unknown"),
        }

    def _extract_keywords(self, search_results: dict[str, Any]) -> list[str]:
        """Extract keywords from search results"""
        keywords = []

        for result in search_results.get("results", []):
            content = result.get("content", "")
            # Simple extraction: split by spaces and take unique words
            words = content.lower().split()
            keywords.extend([w for w in words if len(w) > 3])

        # Return unique keywords
        return list(set(keywords))[:10]

    def _extract_competitor_insights(self, search_results: dict[str, Any]) -> str:
        """Extract competitor insights from search results"""
        insights = []

        for result in search_results.get("results", []):
            content = result.get("content", "")
            insights.append(content[:200])  # First 200 chars

        return "\n\n".join(insights) if insights else "No insights found"

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute SEO-specific tasks.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        try:
            if task.action == "analyze_keywords":
                result = await self.analyze_keywords(task.description)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "optimize_content":
                # Parse: content|keywords_json
                parts = task.description.split("|", 1)
                content = parts[0]
                keywords = eval(parts[1]) if len(parts) > 1 else []

                result = await self.optimize_content(content, keywords)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "analyze_competitors":
                # Parse: domain|keywords_json
                parts = task.description.split("|", 1)
                domain = parts[0]
                keywords = eval(parts[1]) if len(parts) > 1 else []

                result = await self.analyze_competitors(domain, keywords)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            else:
                # Delegate to base class
                return await super().execute_task(task)

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
            )
