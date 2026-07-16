# src/meai/agents/magisters/intelligence_magister.py
"""Intelligence Magister - Market intelligence specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class IntelligenceMagister(BaseMagister):
    """Intelligence Magister - specializes in market intelligence and competitive analysis"""

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
    ):
        """Initialize Intelligence Magister

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
        """Return intelligence domain"""
        return "intelligence"

    def get_capabilities(self) -> list[str]:
        """Return Intelligence Magister capabilities"""
        return [
            "search",
            "store_knowledge",
            "gather_intelligence",
            "analyze_trends",
            "monitor_competitors",
        ]

    async def gather_intelligence(
        self,
        topic: str,
        sources: list[str],
    ) -> dict[str, Any]:
        """
        Gather market intelligence.

        Args:
            topic: Intelligence topic
            sources: Intelligence sources

        Returns:
            Gathered intelligence
        """
        # Search for intelligence on topic
        query = f"market intelligence {topic} {' '.join(sources)}"
        results = await self.hybrid_search(query)

        # Compile intelligence
        intelligence = self._compile_intelligence(results, sources)

        return {
            "status": "success",
            "topic": topic,
            "sources": sources,
            "intelligence": intelligence,
            "source": results.get("source", "unknown"),
        }

    async def analyze_trends(
        self,
        industry: str,
        timeframe: str,
        data_points: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze industry trends.

        Args:
            industry: Industry to analyze
            timeframe: Analysis timeframe
            data_points: Historical data points

        Returns:
            Trend analysis
        """
        # Calculate trend metrics
        if len(data_points) < 2:
            return {
                "status": "success",
                "industry": industry,
                "timeframe": timeframe,
                "trends": "Insufficient data for trend analysis",
                "growth_rate": 0,
            }

        # Calculate growth rate
        first_value = data_points[0].get("value", 0)
        last_value = data_points[-1].get("value", 0)

        growth_rate = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0

        # Analyze trend direction
        trends = self._analyze_trend_direction(data_points, growth_rate)

        return {
            "status": "success",
            "industry": industry,
            "timeframe": timeframe,
            "data_points": len(data_points),
            "growth_rate": round(growth_rate, 2),
            "trends": trends,
        }

    async def monitor_competitors(
        self,
        competitors: list[str],
        metrics: list[str],
    ) -> dict[str, Any]:
        """
        Monitor competitor activities.

        Args:
            competitors: List of competitors
            metrics: Metrics to monitor

        Returns:
            Monitoring report
        """
        # Search for competitor intelligence
        query = f"competitor monitoring {' '.join(competitors)} {' '.join(metrics)}"
        results = await self.hybrid_search(query)

        # Generate monitoring report
        monitoring_report = self._generate_monitoring_report(
            competitors,
            metrics,
            results
        )

        return {
            "status": "success",
            "competitors": competitors,
            "metrics": metrics,
            "monitoring_report": monitoring_report,
            "source": results.get("source", "unknown"),
        }

    def _compile_intelligence(
        self,
        search_results: dict[str, Any],
        sources: list[str],
    ) -> dict[str, Any]:
        """Compile intelligence from search results"""
        intelligence = {
            "summary": "",
            "key_findings": [],
            "sources_used": sources,
        }

        # Extract key findings from results
        for result in search_results.get("results", [])[:3]:
            content = result.get("content", "")
            intelligence["key_findings"].append(content[:200])

        # Generate summary
        if intelligence["key_findings"]:
            intelligence["summary"] = "Intelligence gathered from multiple sources"
        else:
            intelligence["summary"] = "Limited intelligence available - research requested"

        return intelligence

    def _analyze_trend_direction(
        self,
        data_points: list[dict[str, Any]],
        growth_rate: float,
    ) -> str:
        """Analyze trend direction"""
        if growth_rate > 20:
            return "Strong upward trend - significant growth"
        elif growth_rate > 10:
            return "Moderate upward trend - steady growth"
        elif growth_rate > 0:
            return "Slight upward trend - slow growth"
        elif growth_rate > -10:
            return "Slight downward trend - minor decline"
        else:
            return "Strong downward trend - significant decline"

    def _generate_monitoring_report(
        self,
        competitors: list[str],
        metrics: list[str],
        search_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate competitor monitoring report"""
        report = {
            "overview": f"Monitoring {len(competitors)} competitors across {len(metrics)} metrics",
            "competitor_insights": {},
            "recommendations": [],
        }

        # Generate insights for each competitor
        for competitor in competitors:
            report["competitor_insights"][competitor] = {
                "status": "active",
                "metrics_tracked": metrics,
                "last_updated": "recent",
            }

        # Generate recommendations
        if search_results.get("results"):
            report["recommendations"].append("Continue monitoring - activity detected")
        else:
            report["recommendations"].append("Increase monitoring frequency")

        return report

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute Intelligence-specific tasks.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        try:
            if task.action == "gather_intelligence":
                # Parse: topic|sources_json
                parts = task.description.split("|", 1)
                topic = parts[0]
                sources = eval(parts[1]) if len(parts) > 1 else []

                result = await self.gather_intelligence(topic, sources)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "analyze_trends":
                # Parse: industry|timeframe|data_points_json
                parts = task.description.split("|")
                industry = parts[0]
                timeframe = parts[1] if len(parts) > 1 else "monthly"
                data_points = eval(parts[2]) if len(parts) > 2 else []

                result = await self.analyze_trends(industry, timeframe, data_points)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "monitor_competitors":
                # Parse: competitors_json|metrics_json
                parts = task.description.split("|", 1)
                competitors = eval(parts[0]) if parts else []
                metrics = eval(parts[1]) if len(parts) > 1 else []

                result = await self.monitor_competitors(competitors, metrics)
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
