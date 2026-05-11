"""
openFDA API Client

Client for FDA drug enforcement reports API.
Used to check if keywords appear in FDA enforcement actions.

API: https://open.fda.gov/apis/drug/enforcement/
Rate limit: 240 requests per minute (4 req/sec)
Cache: 24 hours (enforcement data changes slowly)
"""

import time
from typing import Any, Optional, List

import httpx
import structlog
from aiocache import Cache
from aiocache.serializers import JsonSerializer

from aim.subagents.schemas.compliance import FDAEnforcementRecord

logger = structlog.get_logger()


class FDAClient:
    """openFDA API client for drug enforcement lookups

    Features:
    - 24h cache (enforcement data changes slowly)
    - Rate limiting (240 req/min = 4 req/sec)
    - Graceful degradation on timeout/error
    - No API key required (public API)

    Args:
        cache_ttl: Cache TTL in seconds (default 86400 = 24h)
        rate_limit_per_minute: Max requests per minute (default 240)
    """

    def __init__(
        self,
        cache_ttl: int = 86400,  # 24 hours
        rate_limit_per_minute: int = 240,
    ):
        self.base_url = "https://api.fda.gov"
        self.cache_ttl = cache_ttl
        self.rate_limit_per_minute = rate_limit_per_minute

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,  # 10s timeout for graceful degradation
        )

        # Cache (24h TTL)
        self.cache = Cache(
            Cache.MEMORY,
            serializer=JsonSerializer(),
            ttl=cache_ttl,
        )

        # Simple rate limiter (track last request time)
        self._last_request_time = 0.0
        self._min_interval = 60.0 / rate_limit_per_minute  # seconds between requests

        # Logger
        self.logger = logger.bind(client="FDAClient")

    async def _rate_limit(self) -> None:
        """Simple rate limiting - wait if needed"""
        now = time.time()
        elapsed = now - self._last_request_time

        if elapsed < self._min_interval:
            wait_time = self._min_interval - elapsed
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    async def search_enforcement(
        self,
        keyword: str,
        limit: int = 10,
    ) -> Optional[List[FDAEnforcementRecord]]:
        """Search FDA drug enforcement reports for keyword

        Args:
            keyword: Keyword to search for
            limit: Maximum results to return

        Returns:
            List of enforcement records or None on error/timeout

        Note:
            Returns None on error for graceful degradation.
            Caller should handle None by falling back to pattern matching only.
        """
        # Check cache first
        cache_key = f"fda_enforcement:{keyword}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            self.logger.info("cache_hit", keyword=keyword)
            return cached

        # Rate limiting
        await self._rate_limit()

        try:
            start_time = time.time()

            # Build search query
            # Search in product_description and reason_for_recall fields
            search_query = f'product_description:"{keyword}" OR reason_for_recall:"{keyword}"'

            params = {
                "search": search_query,
                "limit": limit,
            }

            # Make request
            response = await self.client.get(
                "/drug/enforcement.json",
                params=params,
            )

            duration = time.time() - start_time

            # Handle 404 (no results) as empty list
            if response.status_code == 404:
                self.logger.info(
                    "no_enforcement_found",
                    keyword=keyword,
                    duration=duration,
                )
                result = []
                await self.cache.set(cache_key, result)
                return result

            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            # Parse results into FDAEnforcementRecord objects
            records = []
            for item in results:
                try:
                    record = FDAEnforcementRecord(
                        recall_number=item.get("recall_number", ""),
                        product_description=item.get("product_description", ""),
                        reason_for_recall=item.get("reason_for_recall", ""),
                        classification=item.get("classification", ""),
                        recall_initiation_date=item.get("recall_initiation_date"),
                    )
                    records.append(record)
                except Exception as e:
                    self.logger.warning(
                        "failed_to_parse_record",
                        error=str(e),
                        item=item,
                    )
                    continue

            self.logger.info(
                "enforcement_search_success",
                keyword=keyword,
                found=len(records),
                duration=duration,
            )

            # Cache results
            await self.cache.set(cache_key, records)

            return records

        except httpx.TimeoutException as e:
            # Graceful degradation on timeout
            self.logger.warning(
                "fda_timeout",
                keyword=keyword,
                error=str(e),
            )
            return None

        except httpx.HTTPError as e:
            # Graceful degradation on HTTP error
            self.logger.warning(
                "fda_http_error",
                keyword=keyword,
                error=str(e),
                status_code=getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
            )
            return None

        except Exception as e:
            # Graceful degradation on any other error
            self.logger.error(
                "fda_unexpected_error",
                keyword=keyword,
                error=str(e),
            )
            return None

    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

    def __repr__(self) -> str:
        """String representation"""
        return f"<FDAClient(cache_ttl={self.cache_ttl}s, rate_limit={self.rate_limit_per_minute}/min)>"


# Import asyncio for sleep
import asyncio
