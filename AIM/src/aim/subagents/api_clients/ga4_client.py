"""
Google Analytics 4 API Client.

Based on Google Analytics Data API (GA4).
Provides traffic metrics, user behavior, and conversion data.

Features:
- OAuth 2.0 or Service Account authentication
- Dimensions and metrics queries
- Date range support
- Automatic pagination
- Response caching
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import structlog
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunReportResponse,
)
from google.oauth2 import service_account

logger = structlog.get_logger(__name__)


class TokenBucketRateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary."""
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill

                # Refill tokens
                self.tokens = min(
                    self.capacity,
                    self.tokens + elapsed * self.refill_rate
                )
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Wait for next refill
                wait_time = (tokens - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)


@dataclass
class GA4Credentials:
    """GA4 authentication credentials."""

    property_id: str  # GA4 property ID (e.g., "123456789")
    service_account_file: Optional[str] = None  # Path to service account JSON
    credentials_json: Optional[dict] = None  # Service account JSON dict


@dataclass
class GA4TrafficData:
    """Traffic data from GA4."""

    source: str
    medium: str
    sessions: int
    users: int
    new_users: int
    pageviews: int
    bounce_rate: float
    avg_session_duration: float
    conversions: int = 0


@dataclass
class GA4ConversionData:
    """Conversion data from GA4."""

    event_name: str
    event_count: int
    total_users: int
    event_value: float
    conversion_rate: float


class GA4Client:
    """
    Google Analytics 4 API client.

    Provides traffic metrics, user behavior, and conversion tracking.
    """

    def __init__(
        self,
        credentials: GA4Credentials,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 1.0,
        cache_ttl: int = 3600,
    ):
        """
        Initialize GA4 client.

        Args:
            credentials: GA4 authentication credentials
            rate_limit_capacity: Rate limiter capacity (requests)
            rate_limit_refill: Rate limiter refill rate (requests/second)
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.credentials = credentials
        self.property_id = credentials.property_id
        self.cache_ttl = cache_ttl

        # Rate limiter
        self.rate_limiter = TokenBucketRateLimiter(
            capacity=rate_limit_capacity,
            refill_rate=rate_limit_refill,
        )

        # Cache
        self.cache = Cache(
            Cache.MEMORY,
            serializer=JsonSerializer(),
            ttl=cache_ttl,
        )

        # Initialize GA4 client
        if credentials.service_account_file:
            creds = service_account.Credentials.from_service_account_file(
                credentials.service_account_file,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        elif credentials.credentials_json:
            creds = service_account.Credentials.from_service_account_info(
                credentials.credentials_json,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        else:
            raise ValueError("Either service_account_file or credentials_json required")

        self.client = BetaAnalyticsDataClient(credentials=creds)

        logger.info(
            "ga4_client_initialized",
            property_id=self.property_id,
        )

    async def _get_cached(self, key: str) -> Any:
        """Get value from cache."""
        return await self.cache.get(key)

    async def _set_cached(self, key: str, value: Any) -> None:
        """Set value in cache."""
        await self.cache.set(key, value)

    async def get_traffic_sources(
        self,
        start_date: str,  # YYYY-MM-DD
        end_date: str,  # YYYY-MM-DD
        limit: int = 100,
    ) -> list[GA4TrafficData]:
        """
        Get traffic sources breakdown.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of sources to return

        Returns:
            List of traffic sources with metrics
        """
        cache_key = f"traffic_sources:{self.property_id}:{start_date}:{end_date}:{limit}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("ga4_traffic_sources_cache_hit", cache_key=cache_key)
            return [GA4TrafficData(**item) for item in cached]

        # Rate limiting
        await self.rate_limiter.acquire()

        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="newUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=limit,
        )

        # Execute request
        try:
            response: RunReportResponse = await asyncio.to_thread(
                self.client.run_report,
                request=request,
            )

            # Parse response
            traffic_sources = []
            for row in response.rows:
                source = row.dimension_values[0].value
                medium = row.dimension_values[1].value
                sessions = int(row.metric_values[0].value)
                users = int(row.metric_values[1].value)
                new_users = int(row.metric_values[2].value)
                pageviews = int(row.metric_values[3].value)
                bounce_rate = float(row.metric_values[4].value)
                avg_duration = float(row.metric_values[5].value)

                traffic_sources.append(
                    GA4TrafficData(
                        source=source,
                        medium=medium,
                        sessions=sessions,
                        users=users,
                        new_users=new_users,
                        pageviews=pageviews,
                        bounce_rate=bounce_rate,
                        avg_session_duration=avg_duration,
                    )
                )

            # Cache result
            await self._set_cached(
                cache_key,
                [vars(item) for item in traffic_sources],
            )

            logger.info(
                "ga4_traffic_sources_fetched",
                sources_count=len(traffic_sources),
                start_date=start_date,
                end_date=end_date,
            )

            return traffic_sources

        except Exception as e:
            logger.error(
                "ga4_traffic_sources_error",
                error=str(e),
                property_id=self.property_id,
            )
            raise

    async def get_user_behavior(
        self,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """
        Get user behavior metrics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            User behavior metrics (new/returning users, pages per session, etc.)
        """
        cache_key = f"user_behavior:{self.property_id}:{start_date}:{end_date}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("ga4_user_behavior_cache_hit", cache_key=cache_key)
            return cached

        # Rate limiting
        await self.rate_limiter.acquire()

        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            metrics=[
                Metric(name="totalUsers"),
                Metric(name="newUsers"),
                Metric(name="screenPageViewsPerSession"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        # Execute request
        try:
            response: RunReportResponse = await asyncio.to_thread(
                self.client.run_report,
                request=request,
            )

            # Parse response
            if response.rows:
                row = response.rows[0]
                total_users = int(row.metric_values[0].value)
                new_users = int(row.metric_values[1].value)
                pages_per_session = float(row.metric_values[2].value)
                avg_duration = float(row.metric_values[3].value)

                returning_users = total_users - new_users
                new_user_rate = (new_users / total_users * 100) if total_users > 0 else 0

                result = {
                    "total_users": total_users,
                    "new_users": new_users,
                    "returning_users": returning_users,
                    "new_user_rate": round(new_user_rate, 2),
                    "pages_per_session": round(pages_per_session, 2),
                    "avg_session_duration": round(avg_duration, 2),
                }
            else:
                result = {
                    "total_users": 0,
                    "new_users": 0,
                    "returning_users": 0,
                    "new_user_rate": 0.0,
                    "pages_per_session": 0.0,
                    "avg_session_duration": 0.0,
                }

            # Cache result
            await self._set_cached(cache_key, result)

            logger.info(
                "ga4_user_behavior_fetched",
                total_users=result["total_users"],
                new_user_rate=result["new_user_rate"],
            )

            return result

        except Exception as e:
            logger.error(
                "ga4_user_behavior_error",
                error=str(e),
                property_id=self.property_id,
            )
            raise

    async def get_conversions(
        self,
        start_date: str,
        end_date: str,
        event_names: Optional[list[str]] = None,
    ) -> list[GA4ConversionData]:
        """
        Get conversion events data.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            event_names: Optional list of event names to filter (e.g., ["purchase", "sign_up"])

        Returns:
            List of conversion events with metrics
        """
        cache_key = f"conversions:{self.property_id}:{start_date}:{end_date}:{event_names}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("ga4_conversions_cache_hit", cache_key=cache_key)
            return [GA4ConversionData(**item) for item in cached]

        # Rate limiting
        await self.rate_limiter.acquire()

        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="eventName"),
            ],
            metrics=[
                Metric(name="eventCount"),
                Metric(name="totalUsers"),
                Metric(name="eventValue"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        # Execute request
        try:
            response: RunReportResponse = await asyncio.to_thread(
                self.client.run_report,
                request=request,
            )

            # Parse response
            conversions = []
            for row in response.rows:
                event_name = row.dimension_values[0].value

                # Filter by event names if provided
                if event_names and event_name not in event_names:
                    continue

                event_count = int(row.metric_values[0].value)
                total_users = int(row.metric_values[1].value)
                event_value = float(row.metric_values[2].value)

                # Calculate conversion rate (events per user)
                conversion_rate = (event_count / total_users * 100) if total_users > 0 else 0

                conversions.append(
                    GA4ConversionData(
                        event_name=event_name,
                        event_count=event_count,
                        total_users=total_users,
                        event_value=event_value,
                        conversion_rate=round(conversion_rate, 2),
                    )
                )

            # Cache result
            await self._set_cached(
                cache_key,
                [vars(item) for item in conversions],
            )

            logger.info(
                "ga4_conversions_fetched",
                conversions_count=len(conversions),
                start_date=start_date,
                end_date=end_date,
            )

            return conversions

        except Exception as e:
            logger.error(
                "ga4_conversions_error",
                error=str(e),
                property_id=self.property_id,
            )
            raise

    async def get_bounce_rate_by_page(
        self,
        start_date: str,
        end_date: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get bounce rate by page.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of pages to return

        Returns:
            List of pages with bounce rates
        """
        cache_key = f"bounce_by_page:{self.property_id}:{start_date}:{end_date}:{limit}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("ga4_bounce_by_page_cache_hit", cache_key=cache_key)
            return cached

        # Rate limiting
        await self.rate_limiter.acquire()

        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="pagePath"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=limit,
            order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        )

        # Execute request
        try:
            response: RunReportResponse = await asyncio.to_thread(
                self.client.run_report,
                request=request,
            )

            # Parse response
            pages = []
            for row in response.rows:
                page = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value)
                bounce_rate = float(row.metric_values[1].value)

                pages.append({
                    "page": page,
                    "sessions": sessions,
                    "bounce_rate": round(bounce_rate, 2),
                })

            # Cache result
            await self._set_cached(cache_key, pages)

            logger.info(
                "ga4_bounce_by_page_fetched",
                pages_count=len(pages),
            )

            return pages

        except Exception as e:
            logger.error(
                "ga4_bounce_by_page_error",
                error=str(e),
                property_id=self.property_id,
            )
            raise

    async def get_attribution_data(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """
        Get conversion attribution data by source/medium/campaign.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of attribution data with conversions and revenue
        """
        cache_key = f"attribution:{self.property_id}:{start_date}:{end_date}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("ga4_attribution_cache_hit", cache_key=cache_key)
            return cached

        # Rate limiting
        await self.rate_limiter.acquire()

        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
                Dimension(name="sessionCampaignName"),
            ],
            metrics=[
                Metric(name="conversions"),
                Metric(name="totalRevenue"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        # Execute request
        try:
            response: RunReportResponse = await asyncio.to_thread(
                self.client.run_report,
                request=request,
            )

            # Parse response
            attributions = []
            for row in response.rows:
                source = row.dimension_values[0].value
                medium = row.dimension_values[1].value
                campaign = row.dimension_values[2].value
                conversions = int(float(row.metric_values[0].value))
                revenue = float(row.metric_values[1].value)

                attributions.append({
                    "source": source,
                    "medium": medium,
                    "campaign": campaign,
                    "conversions": conversions,
                    "revenue": revenue,
                })

            # Cache result
            await self._set_cached(cache_key, attributions)

            logger.info(
                "ga4_attribution_fetched",
                attributions_count=len(attributions),
            )

            return attributions

        except Exception as e:
            logger.error(
                "ga4_attribution_error",
                error=str(e),
                property_id=self.property_id,
            )
            raise

    async def get_revenue_data(
        self,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """
        Get revenue metrics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Revenue metrics dictionary
        """
        cache_key = f"revenue:{self.property_id}:{start_date}:{end_date}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("ga4_revenue_cache_hit", cache_key=cache_key)
            return cached

        # Rate limiting
        await self.rate_limiter.acquire()

        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            metrics=[
                Metric(name="totalRevenue"),
                Metric(name="transactions"),
                Metric(name="averagePurchaseRevenue"),
                Metric(name="sessions"),
                Metric(name="totalUsers"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        # Execute request
        try:
            response: RunReportResponse = await asyncio.to_thread(
                self.client.run_report,
                request=request,
            )

            # Parse response
            if response.rows:
                row = response.rows[0]
                total_revenue = float(row.metric_values[0].value)
                transactions = int(float(row.metric_values[1].value))
                avg_order_value = float(row.metric_values[2].value)
                sessions = int(float(row.metric_values[3].value))
                users = int(float(row.metric_values[4].value))

                result = {
                    "total_revenue": total_revenue,
                    "transactions": transactions,
                    "avg_order_value": avg_order_value,
                    "revenue_per_session": total_revenue / sessions if sessions > 0 else 0.0,
                    "revenue_per_user": total_revenue / users if users > 0 else 0.0,
                }
            else:
                result = {
                    "total_revenue": 0.0,
                    "transactions": 0,
                    "avg_order_value": 0.0,
                    "revenue_per_session": 0.0,
                    "revenue_per_user": 0.0,
                }

            # Cache result
            await self._set_cached(cache_key, result)

            logger.info(
                "ga4_revenue_fetched",
                total_revenue=result["total_revenue"],
                transactions=result["transactions"],
            )

            return result

        except Exception as e:
            logger.error(
                "ga4_revenue_error",
                error=str(e),
                property_id=self.property_id,
            )
            raise

    async def close(self) -> None:
        """Close client and cleanup resources."""
        await self.cache.close()
        logger.info("ga4_client_closed", property_id=self.property_id)


async def main():
    """Example usage."""
    # Initialize client
    credentials = GA4Credentials(
        property_id="123456789",
        service_account_file="/path/to/service-account.json",
    )

    client = GA4Client(credentials=credentials)

    # Get traffic sources
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    traffic_sources = await client.get_traffic_sources(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=10,
    )

    print("Traffic Sources:")
    for source in traffic_sources:
        print(f"  {source.source}/{source.medium}: {source.sessions:,} sessions")

    # Get user behavior
    user_behavior = await client.get_user_behavior(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    print(f"\nUser Behavior:")
    print(f"  Total Users: {user_behavior['total_users']:,}")
    print(f"  New Users: {user_behavior['new_users']:,} ({user_behavior['new_user_rate']:.1f}%)")
    print(f"  Pages/Session: {user_behavior['pages_per_session']:.2f}")

    # Get conversions
    conversions = await client.get_conversions(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        event_names=["purchase", "sign_up"],
    )

    print(f"\nConversions:")
    for conv in conversions:
        print(f"  {conv.event_name}: {conv.event_count:,} events (${conv.event_value:.2f})")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
