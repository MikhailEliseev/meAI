# src/meai/agents/magisters/analytics_magister.py
"""Analytics Magister - Analytics specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class AnalyticsMagister(BaseMagister):
    """Analytics Magister - specializes in data analytics and reporting"""

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
    ):
        """Initialize Analytics Magister

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
        """Return analytics domain"""
        return "analytics"

    def get_capabilities(self) -> list[str]:
        """Return Analytics Magister capabilities"""
        return [
            "search",
            "store_knowledge",
            "analyze_traffic",
            "generate_report",
            "track_conversions",
        ]

    async def analyze_traffic(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze website traffic.

        Args:
            data: Traffic data

        Returns:
            Traffic analysis
        """
        # Search for analysis best practices
        query = f"traffic analysis metrics interpretation"
        results = await self.hybrid_search(query)

        # Extract metrics
        sessions = data.get("sessions", 0)
        users = data.get("users", 0)
        pageviews = data.get("pageviews", 0)
        bounce_rate = data.get("bounce_rate", 0)
        avg_session_duration = data.get("avg_session_duration", 0)

        # Calculate derived metrics
        pages_per_session = pageviews / sessions if sessions > 0 else 0
        new_users_rate = ((users - sessions) / users * 100) if users > 0 else 0

        # Generate analysis
        analysis = self._generate_traffic_analysis(
            bounce_rate,
            pages_per_session,
            avg_session_duration
        )

        return {
            "status": "success",
            "metrics": {
                "sessions": sessions,
                "users": users,
                "pageviews": pageviews,
                "bounce_rate": bounce_rate,
                "avg_session_duration": avg_session_duration,
                "pages_per_session": round(pages_per_session, 2),
            },
            "analysis": analysis,
            "source": results.get("source", "unknown"),
        }

    async def generate_report(
        self,
        report_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate analytics report.

        Args:
            report_type: Type of report (daily, weekly, monthly)
            data: Report data

        Returns:
            Generated report
        """
        # Generate report sections
        report = {
            "type": report_type,
            "summary": self._generate_summary(data),
            "traffic": data.get("traffic", {}),
            "conversions": data.get("conversions", {}),
            "recommendations": self._generate_recommendations(data),
        }

        return {
            "status": "success",
            "report_type": report_type,
            "report": report,
        }

    async def track_conversions(
        self,
        goal: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Track conversion metrics.

        Args:
            goal: Conversion goal
            data: Conversion data

        Returns:
            Conversion tracking results
        """
        # Search for conversion tracking best practices
        query = f"conversion tracking {goal} metrics"
        results = await self.hybrid_search(query)

        # Calculate conversion metrics
        total_visitors = data.get("total_visitors", 0)
        conversions = data.get("conversions", 0)
        value = data.get("value", 0)

        conversion_rate = (conversions / total_visitors * 100) if total_visitors > 0 else 0
        value_per_conversion = value / conversions if conversions > 0 else 0

        # Generate insights
        insights = self._generate_conversion_insights(conversion_rate, value_per_conversion)

        return {
            "status": "success",
            "goal": goal,
            "conversion_rate": round(conversion_rate, 2),
            "total_conversions": conversions,
            "value_per_conversion": round(value_per_conversion, 2),
            "total_value": value,
            "insights": insights,
            "source": results.get("source", "unknown"),
        }

    def _generate_traffic_analysis(
        self,
        bounce_rate: float,
        pages_per_session: float,
        avg_session_duration: float,
    ) -> str:
        """Generate traffic analysis"""
        analysis = []

        if bounce_rate < 40:
            analysis.append("Low bounce rate indicates engaging content")
        elif bounce_rate < 60:
            analysis.append("Bounce rate is acceptable")
        else:
            analysis.append("High bounce rate - consider improving landing pages")

        if pages_per_session > 3:
            analysis.append("Good page depth - users exploring content")
        elif pages_per_session > 2:
            analysis.append("Average page depth")
        else:
            analysis.append("Low page depth - improve internal linking")

        if avg_session_duration > 180:
            analysis.append("Good session duration - users engaged")
        elif avg_session_duration > 60:
            analysis.append("Average session duration")
        else:
            analysis.append("Short sessions - improve content quality")

        return ". ".join(analysis)

    def _generate_summary(self, data: dict[str, Any]) -> str:
        """Generate report summary"""
        traffic = data.get("traffic", {})
        conversions = data.get("conversions", {})

        sessions = traffic.get("sessions", 0)
        conversion_rate = conversions.get("rate", 0)

        return f"Total sessions: {sessions}. Conversion rate: {conversion_rate}%."

    def _generate_recommendations(self, data: dict[str, Any]) -> list[str]:
        """Generate recommendations"""
        recommendations = []

        traffic = data.get("traffic", {})
        conversions = data.get("conversions", {})

        if traffic.get("sessions", 0) < 1000:
            recommendations.append("Increase traffic through SEO and content marketing")

        if conversions.get("rate", 0) < 2.0:
            recommendations.append("Optimize conversion funnel")

        if not recommendations:
            recommendations.append("Continue current strategy")

        return recommendations

    def _generate_conversion_insights(
        self,
        conversion_rate: float,
        value_per_conversion: float,
    ) -> str:
        """Generate conversion insights"""
        insights = []

        if conversion_rate > 5.0:
            insights.append("Excellent conversion rate")
        elif conversion_rate > 2.0:
            insights.append("Good conversion rate")
        else:
            insights.append("Conversion rate needs improvement")

        if value_per_conversion > 100:
            insights.append("High value per conversion")
        elif value_per_conversion > 50:
            insights.append("Moderate value per conversion")
        else:
            insights.append("Consider increasing conversion value")

        return ". ".join(insights)

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute Analytics-specific tasks.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        try:
            if task.action == "analyze_traffic":
                # Parse: data_json
                data = eval(task.description) if task.description else {}

                result = await self.analyze_traffic(data)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "generate_report":
                # Parse: report_type|data_json
                parts = task.description.split("|", 1)
                report_type = parts[0]
                data = eval(parts[1]) if len(parts) > 1 else {}

                result = await self.generate_report(report_type, data)
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    result=result,
                )

            elif task.action == "track_conversions":
                # Parse: goal|data_json
                parts = task.description.split("|", 1)
                goal = parts[0]
                data = eval(parts[1]) if len(parts) > 1 else {}

                result = await self.track_conversions(goal, data)
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
