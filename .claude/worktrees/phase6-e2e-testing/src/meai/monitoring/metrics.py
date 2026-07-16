"""Metrics collection and storage"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from sqlalchemy import select, func
import structlog

from ..storage.database import Database
from ..storage.models import Metric

logger = structlog.get_logger()


class MetricsCollector:
    """Collect and store metrics"""

    def __init__(self, db: Database):
        """Initialize Metrics Collector

        Args:
            db: Database instance
        """
        self.db = db

    async def record_counter(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record counter metric

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels dictionary
        """
        await self._record_metric(name, "counter", value, labels or {})

    async def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record gauge metric

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels dictionary
        """
        await self._record_metric(name, "gauge", value, labels or {})

    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record histogram metric

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels dictionary
        """
        await self._record_metric(name, "histogram", value, labels or {})

    async def _record_metric(
        self,
        name: str,
        metric_type: str,
        value: float,
        labels: dict[str, str],
    ) -> None:
        """Record metric to database

        Args:
            name: Metric name
            metric_type: Type of metric (counter, gauge, histogram)
            value: Metric value
            labels: Labels dictionary
        """
        async with self.db.session() as session:
            metric = Metric(
                metric_name=name,
                metric_type=metric_type,
                value=value,
                labels=labels,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(metric)

        logger.debug(
            "metrics.recorded",
            name=name,
            type=metric_type,
            value=value,
        )

    async def get_metrics(
        self,
        name: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[Metric]:
        """Get metrics by name

        Args:
            name: Metric name
            since: Optional start timestamp
            limit: Maximum number of metrics to return

        Returns:
            List of Metric objects
        """
        async with self.db.session() as session:
            query = select(Metric).where(Metric.metric_name == name)

            if since:
                query = query.where(Metric.timestamp >= since)

            query = query.order_by(Metric.timestamp.desc()).limit(limit)

            result = await session.execute(query)
            metrics = list(result.scalars().all())

        return metrics

    async def get_metric_summary(
        self,
        name: str,
        since: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get metric summary statistics

        Args:
            name: Metric name
            since: Optional start timestamp

        Returns:
            Summary statistics dictionary
        """
        async with self.db.session() as session:
            query = select(
                func.count(Metric.id).label("count"),
                func.avg(Metric.value).label("avg"),
                func.min(Metric.value).label("min"),
                func.max(Metric.value).label("max"),
            ).where(Metric.metric_name == name)

            if since:
                query = query.where(Metric.timestamp >= since)

            result = await session.execute(query)
            row = result.one()

        return {
            "name": name,
            "count": row.count or 0,
            "avg": float(row.avg) if row.avg else 0.0,
            "min": float(row.min) if row.min else 0.0,
            "max": float(row.max) if row.max else 0.0,
        }

    async def cleanup_old_metrics(
        self,
        older_than: timedelta = timedelta(days=30),
    ) -> int:
        """Clean up old metrics

        Args:
            older_than: Delete metrics older than this timedelta

        Returns:
            Number of deleted metrics
        """
        cutoff = datetime.now(timezone.utc) - older_than

        async with self.db.session() as session:
            from sqlalchemy import delete
            stmt = delete(Metric).where(Metric.timestamp < cutoff)
            result = await session.execute(stmt)
            deleted = result.rowcount

        logger.info("metrics.cleanup", deleted=deleted)
        return deleted
