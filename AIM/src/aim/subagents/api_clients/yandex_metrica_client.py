"""
Yandex Metrica API Client.

Based on Yandex Metrica Reporting API v1.
Provides traffic metrics, user behavior, and conversion data for Russian market.

Features:
- OAuth 2.0 authentication
- Traffic sources breakdown
- User behavior metrics
- Bounce rate analysis
- Response caching
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import structlog
from aiocache import Cache
from aiocache.serializers import JsonSerializer

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
class YandexMetricaCredentials:
    """Yandex Metrica authentication credentials."""

    counter_id: str  # Metrica counter ID
    access_token: str  # OAuth access token


@dataclass
class YandexMetricaTrafficData:
    """Traffic data from Yandex Metrica."""

    source: str
    visits: int
    users: int
    pageviews: int
    bounce_rate: float
    avg_visit_duration: float


class YandexMetricaClient:
    """
    Yandex Metrica API client.

    Provides traffic metrics, user behavior, and bounce rate analysis
    for Russian market websites.
    """

    BASE_URL = "https://api-metrika.yandex.net/stat/v1/data"

    def __init__(
        self,
        credentials: YandexMetricaCredentials,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 1.0,
        cache_ttl: int = 3600,
    ):
        """
        Initialize Yandex Metrica client.

        Args:
            credentials: Yandex Metrica authentication credentials
            rate_limit_capacity: Rate limiter capacity (requests)
            rate_limit_refill: Rate limiter refill rate (requests/second)
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.credentials = credentials
        self.counter_id = credentials.counter_id
        self.access_token = credentials.access_token
        self.cache_ttl = cache_ttl

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"OAuth {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

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

        logger.info(
            "yandex_metrica_client_initialized",
            counter_id=self.counter_id,
        )

    async def _get_cached(self, key: str) -> Any:
        """Get value from cache."""
        return await self.cache.get(key)

    async def _set_cached(self, key: str, value: Any) -> None:
        """Set value in cache."""
        await self.cache.set(key, value)

    async def _make_request(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Make API request with rate limiting.

        Args:
            params: Query parameters

        Returns:
            API response JSON
        """
        # Rate limiting
        await self.rate_limiter.acquire()

        try:
            response = await self.client.get("", params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(
                "yandex_metrica_request_error",
                error=str(e),
                params=params,
            )
            raise

    async def get_traffic_sources(
        self,
        start_date: str,  # YYYY-MM-DD
        end_date: str,  # YYYY-MM-DD
        limit: int = 100,
    ) -> list[YandexMetricaTrafficData]:
        """
        Get traffic sources breakdown.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of sources to return

        Returns:
            List of traffic sources with metrics
        """
        cache_key = f"traffic_sources:{self.counter_id}:{start_date}:{end_date}:{limit}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("yandex_metrica_traffic_sources_cache_hit", cache_key=cache_key)
            return [YandexMetricaTrafficData(**item) for item in cached]

        # Build request params
        params = {
            "ids": self.counter_id,
            "date1": start_date,
            "date2": end_date,
            "metrics": "ym:s:visits,ym:s:users,ym:s:pageviews,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
            "dimensions": "ym:s:trafficSource",
            "limit": limit,
        }

        # Execute request
        try:
            response = await self._make_request(params)

            # Parse response
            traffic_sources = []
            data = response.get("data", [])

            for row in data:
                dimensions = row.get("dimensions", [])
                metrics = row.get("metrics", [])

                if len(dimensions) > 0 and len(metrics) >= 5:
                    source = dimensions[0].get("name", "unknown")
                    visits = int(metrics[0])
                    users = int(metrics[1])
                    pageviews = int(metrics[2])
                    bounce_rate = float(metrics[3])
                    avg_duration = float(metrics[4])

                    traffic_sources.append(
                        YandexMetricaTrafficData(
                            source=source,
                            visits=visits,
                            users=users,
                            pageviews=pageviews,
                            bounce_rate=bounce_rate,
                            avg_visit_duration=avg_duration,
                        )
                    )

            # Cache result
            await self._set_cached(
                cache_key,
                [vars(item) for item in traffic_sources],
            )

            logger.info(
                "yandex_metrica_traffic_sources_fetched",
                sources_count=len(traffic_sources),
                start_date=start_date,
                end_date=end_date,
            )

            return traffic_sources

        except Exception as e:
            logger.error(
                "yandex_metrica_traffic_sources_error",
                error=str(e),
                counter_id=self.counter_id,
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
            User behavior metrics (new/returning users, pages per visit, etc.)
        """
        cache_key = f"user_behavior:{self.counter_id}:{start_date}:{end_date}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("yandex_metrica_user_behavior_cache_hit", cache_key=cache_key)
            return cached

        # Build request params
        params = {
            "ids": self.counter_id,
            "date1": start_date,
            "date2": end_date,
            "metrics": "ym:s:users,ym:s:newUsers,ym:s:pageviewsPerVisit,ym:s:avgVisitDurationSeconds",
        }

        # Execute request
        try:
            response = await self._make_request(params)

            # Parse response
            data = response.get("totals", [])

            if len(data) >= 4:
                total_users = int(data[0])
                new_users = int(data[1])
                pages_per_visit = float(data[2])
                avg_duration = float(data[3])

                returning_users = total_users - new_users
                new_user_rate = (new_users / total_users * 100) if total_users > 0 else 0

                result = {
                    "total_users": total_users,
                    "new_users": new_users,
                    "returning_users": returning_users,
                    "new_user_rate": round(new_user_rate, 2),
                    "pages_per_session": round(pages_per_visit, 2),
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
                "yandex_metrica_user_behavior_fetched",
                total_users=result["total_users"],
                new_user_rate=result["new_user_rate"],
            )

            return result

        except Exception as e:
            logger.error(
                "yandex_metrica_user_behavior_error",
                error=str(e),
                counter_id=self.counter_id,
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
        cache_key = f"bounce_by_page:{self.counter_id}:{start_date}:{end_date}:{limit}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("yandex_metrica_bounce_by_page_cache_hit", cache_key=cache_key)
            return cached

        # Build request params
        params = {
            "ids": self.counter_id,
            "date1": start_date,
            "date2": end_date,
            "metrics": "ym:pv:pageviews,ym:pv:bounceRate",
            "dimensions": "ym:pv:URLPath",
            "limit": limit,
            "sort": "-ym:pv:pageviews",
        }

        # Execute request
        try:
            response = await self._make_request(params)

            # Parse response
            pages = []
            data = response.get("data", [])

            for row in data:
                dimensions = row.get("dimensions", [])
                metrics = row.get("metrics", [])

                if len(dimensions) > 0 and len(metrics) >= 2:
                    page = dimensions[0].get("name", "unknown")
                    pageviews = int(metrics[0])
                    bounce_rate = float(metrics[1])

                    pages.append({
                        "page": page,
                        "sessions": pageviews,  # Using pageviews as proxy for sessions
                        "bounce_rate": round(bounce_rate, 2),
                    })

            # Cache result
            await self._set_cached(cache_key, pages)

            logger.info(
                "yandex_metrica_bounce_by_page_fetched",
                pages_count=len(pages),
            )

            return pages

        except Exception as e:
            logger.error(
                "yandex_metrica_bounce_by_page_error",
                error=str(e),
                counter_id=self.counter_id,
            )
            raise

    async def close(self) -> None:
        """Close client and cleanup resources."""
        await self.client.aclose()
        await self.cache.close()
        logger.info("yandex_metrica_client_closed", counter_id=self.counter_id)


async def main():
    """Example usage."""
    # Initialize client
    credentials = YandexMetricaCredentials(
        counter_id="12345678",
        access_token="your_oauth_token_here",
    )

    client = YandexMetricaClient(credentials=credentials)

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
        print(f"  {source.source}: {source.visits:,} visits")

    # Get user behavior
    user_behavior = await client.get_user_behavior(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    print(f"\nUser Behavior:")
    print(f"  Total Users: {user_behavior['total_users']:,}")
    print(f"  New Users: {user_behavior['new_users']:,} ({user_behavior['new_user_rate']:.1f}%)")
    print(f"  Pages/Visit: {user_behavior['pages_per_session']:.2f}")

    # Get bounce rate by page
    pages = await client.get_bounce_rate_by_page(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=10,
    )

    print(f"\nTop Pages by Bounce Rate:")
    for page in pages[:5]:
        print(f"  {page['page']}: {page['bounce_rate']:.1f}%")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
