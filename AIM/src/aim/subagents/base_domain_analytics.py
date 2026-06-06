"""
Base Domain Analytics Agent

Base class for all Domain Analytics subagents.
Each Magister has its own Domain Analytics subagent (5th subagent).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from meai.events.event_bus import EventBus, Event, EventPriority
from src.aim.models.analytics_models import DomainMetrics, AggregatedMetrics


class BaseDomainAnalytics(ABC):
    """Base class for Domain Analytics Subagents

    Each Domain Analytics subagent:
    1. Collects domain-specific metrics from data sources
    2. Aggregates raw metrics into domain summary
    3. Publishes aggregated metrics to Analytics Magister

    Domain Analytics subagents:
    - SEO Analytics (organic traffic, rankings, backlinks)
    - Content Analytics (publications, engagement, quality)
    - Ads Analytics (campaigns, ROAS, budget)
    - AI Analytics (tokens, latency, quality)
    """

    def __init__(
        self,
        domain: str,
        event_bus: EventBus,
        vault_path: Path,
        data_path: Path
    ):
        """Initialize Domain Analytics subagent

        Args:
            domain: Domain name (seo, content, ads, ai)
            event_bus: Event Bus for communication
            vault_path: Path to Magister's Obsidian vault
            data_path: Path to data storage
        """
        self.domain = domain
        self.event_bus = event_bus
        self.vault_path = vault_path
        self.data_path = data_path

        # Create analytics directory in vault
        self.analytics_path = vault_path / "wiki" / "analytics"
        self.analytics_path.mkdir(parents=True, exist_ok=True)

        # Create data directory
        self.data_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def collect_metrics(
        self,
        date_range: Dict[str, str]
    ) -> List[DomainMetrics]:
        """Collect domain-specific metrics from data sources

        This method must be implemented by each Domain Analytics subagent
        to collect metrics from their specific data sources.

        Args:
            date_range: Time period {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

        Returns:
            List of raw domain metrics from all sources

        Example:
            SEO Analytics collects from:
            - Google Search Console
            - Яндекс.Вебмастер
            - Ahrefs API
            - Google Analytics (organic segment)
        """
        pass

    @abstractmethod
    async def aggregate_metrics(
        self,
        raw_metrics: List[DomainMetrics]
    ) -> AggregatedMetrics:
        """Aggregate raw metrics into domain summary

        This method must be implemented by each Domain Analytics subagent
        to aggregate their domain-specific metrics.

        Args:
            raw_metrics: List of raw metrics from collect_metrics()

        Returns:
            Aggregated metrics with summary, KPIs, trends, insights

        Example:
            SEO Analytics aggregates:
            - Sum organic traffic
            - Calculate average position
            - Analyze backlinks growth
            - Generate SEO insights
        """
        pass

    async def publish_to_analytics(
        self,
        metrics: AggregatedMetrics
    ) -> None:
        """Publish aggregated metrics to Analytics Magister

        Sends aggregated metrics via Event Bus to Analytics Magister
        for cross-domain analysis and strategic insights.

        Args:
            metrics: Aggregated domain metrics
        """
        await self.event_bus.publish(Event(
            event_type="analytics.domain_metrics_ready",
            payload={
                "domain": self.domain,
                "metrics": metrics.dict(),
                "timestamp": datetime.now().isoformat()
            },
            priority=EventPriority.P2
        ))

        # Log to vault
        await self._log_to_vault(
            f"Published metrics to Analytics Magister: {len(metrics.insights)} insights"
        )

    async def execute_collection(
        self,
        date_range: Dict[str, str]
    ) -> AggregatedMetrics:
        """Execute full collection and aggregation workflow

        This is the main entry point for Domain Analytics subagents.

        Workflow:
        1. Collect raw metrics from data sources
        2. Aggregate metrics into domain summary
        3. Save to vault and data storage
        4. Publish to Analytics Magister

        Args:
            date_range: Time period {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

        Returns:
            Aggregated metrics
        """
        # Step 1: Collect raw metrics
        await self._log_to_vault(
            f"Starting metrics collection for {date_range['start']} to {date_range['end']}"
        )

        raw_metrics = await self.collect_metrics(date_range)

        await self._log_to_vault(
            f"Collected {len(raw_metrics)} raw metrics from {len(set(m.source for m in raw_metrics if m.source))} sources"
        )

        # Step 2: Aggregate metrics
        aggregated = await self.aggregate_metrics(raw_metrics)

        await self._log_to_vault(
            f"Aggregated metrics: {len(aggregated.insights)} insights, {len(aggregated.kpis)} KPIs"
        )

        # Step 3: Save to storage
        await self._save_metrics(aggregated)

        # Step 4: Publish to Analytics Magister
        await self.publish_to_analytics(aggregated)

        return aggregated

    async def _save_metrics(
        self,
        metrics: AggregatedMetrics
    ) -> None:
        """Save aggregated metrics to vault and data storage

        Args:
            metrics: Aggregated metrics to save
        """
        # Save to vault (markdown)
        daily_metrics_file = self.analytics_path / "daily-metrics.md"

        entry = f"""
## [{metrics.aggregated_at.strftime('%Y-%m-%d %H:%M')}] {self.domain.upper()} Metrics

**Period:** {metrics.period['start']} → {metrics.period['end']}

**Summary:**
{self._format_dict(metrics.summary)}

**KPIs:**
{self._format_dict(metrics.kpis)}

**Trends:**
{self._format_dict(metrics.trends)}

**Insights:**
{self._format_list(metrics.insights)}

---
"""

        # Append to daily metrics log
        with open(daily_metrics_file, 'a', encoding='utf-8') as f:
            f.write(entry)

        # Save to data storage (JSON)
        import json
        data_file = self.data_path / f"{self.domain}_metrics_{metrics.aggregated_at.strftime('%Y%m%d_%H%M%S')}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(metrics.dict(), f, ensure_ascii=False, indent=2, default=str)

    async def _log_to_vault(
        self,
        message: str
    ) -> None:
        """Log operation to Obsidian vault

        Args:
            message: Log message
        """
        log_file = self.analytics_path / "log.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"## [{timestamp}] {self.domain.upper()} Analytics | {message}\n\n"

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry)

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary for markdown

        Args:
            data: Dictionary to format

        Returns:
            Formatted markdown string
        """
        if not data:
            return "- (empty)"

        lines = []
        for key, value in data.items():
            if isinstance(value, float):
                lines.append(f"- **{key}:** {value:.2f}")
            else:
                lines.append(f"- **{key}:** {value}")
        return "\n".join(lines)

    def _format_list(self, items: List[str]) -> str:
        """Format list for markdown

        Args:
            items: List to format

        Returns:
            Formatted markdown string
        """
        if not items:
            return "- (none)"

        return "\n".join(f"- {item}" for item in items)

    def get_capabilities(self) -> List[str]:
        """Get Domain Analytics capabilities

        Returns:
            List of capabilities
        """
        return [
            "collect_metrics",
            "aggregate_metrics",
            "publish_to_analytics",
            "execute_collection"
        ]
