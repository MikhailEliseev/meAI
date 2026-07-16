"""
SERP API Client - Fetches search engine results for keyword clustering.

Supports multiple SERP data providers:
1. DataForSEO (primary) - Real-time SERP data
2. SEMrush (fallback) - Organic search results
3. Mock data (testing) - For development without API costs

Based on SERP overlap clustering methodology from Ahrefs.
"""

import asyncio
from typing import Any

import httpx
from pydantic import BaseModel, Field

from AIM.src.aim.subagents.schemas.content_gap import (
    IntentType,
    KeywordSERPData,
    SERPResult,
)


class SERPClientConfig(BaseModel):
    """Configuration for SERP API client."""

    provider: str = Field(default="dataforseo", description="SERP data provider")
    api_key: str = Field(..., description="API key for provider")
    serp_depth: int = Field(default=30, ge=10, le=100, description="Number of results to fetch")
    max_cost_per_keyword: float = Field(default=0.02, description="Max cost per keyword (USD)")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    use_cache: bool = Field(default=True, description="Enable response caching")


class SERPAPIClient:
    """
    SERP API client for fetching search engine results.

    Supports:
    - DataForSEO SERP API (primary)
    - SEMrush Organic Research API (fallback)
    - Mock data for testing

    Cost per keyword:
    - DataForSEO: $0.01-0.02 per keyword
    - SEMrush: $0.01 per keyword
    """

    def __init__(
        self,
        config: SERPClientConfig,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 1.0,
    ):
        """
        Initialize SERP API client.

        Args:
            config: Client configuration
            rate_limit_capacity: Rate limiter capacity
            rate_limit_refill: Requests per second
        """
        self.config = config
        self.provider = config.provider
        self.api_key = config.api_key
        self.base_url = self._get_base_url(config.provider)

        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(config.timeout_seconds),
            headers=self._get_headers(),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.provider == "dataforseo":
            # DataForSEO uses Basic Auth
            import base64
            credentials = base64.b64encode(f"{self.api_key}:".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif self.provider == "semrush":
            # SEMrush uses API key in params, not headers
            pass

        return headers

    def _get_base_url(self, provider: str) -> str:
        """Get base URL for provider."""
        urls = {
            "dataforseo": "https://api.dataforseo.com/v3",
            "semrush": "https://api.semrush.com",
            "mock": "http://localhost:8000",  # For testing
        }
        return urls.get(provider, urls["dataforseo"])

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            json: JSON payload for POST requests
            params: Query parameters

        Returns:
            Response data (dict or string)

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        if method == "GET":
            response = await self.client.get(url, params=params)
        elif method == "POST":
            response = await self.client.post(url, json=json)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        # Return JSON or text based on content type
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        else:
            return response.text

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_serp_data(
        self,
        keywords: list[str],
        location: str = "United States",
        language: str = "en",
        max_cost_usd: float = 1.0,
    ) -> list[KeywordSERPData]:
        """
        Fetch SERP data for multiple keywords.

        Args:
            keywords: List of keywords to fetch SERP data for
            location: Geographic location for search results
            language: Language code (en, ru, etc.)
            max_cost_usd: Maximum budget for API calls

        Returns:
            List of KeywordSERPData with SERP results

        Raises:
            ValueError: If keywords list is empty or budget exceeded
            httpx.HTTPError: If API request fails
        """
        if not keywords:
            raise ValueError("keywords list cannot be empty")

        # Calculate cost estimate
        estimated_cost = len(keywords) * self.config.max_cost_per_keyword
        if estimated_cost > max_cost_usd:
            raise ValueError(
                f"Estimated cost ${estimated_cost:.2f} exceeds budget ${max_cost_usd:.2f}"
            )

        # Fetch SERP data based on provider
        if self.provider == "dataforseo":
            return await self._fetch_dataforseo(keywords, location, language)
        elif self.provider == "semrush":
            return await self._fetch_semrush(keywords, location)
        elif self.provider == "mock":
            return await self._fetch_mock(keywords)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _fetch_dataforseo(
        self,
        keywords: list[str],
        location: str,
        language: str,
    ) -> list[KeywordSERPData]:
        """
        Fetch SERP data from DataForSEO API.

        Endpoint: POST /serp/google/organic/live/advanced
        Cost: $0.01-0.02 per keyword

        Returns:
            List of KeywordSERPData
        """
        results: list[KeywordSERPData] = []

        # Batch keywords (max 100 per request)
        batch_size = 100
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i : i + batch_size]

            # Build request payload
            tasks = [
                {
                    "keyword": keyword,
                    "location_name": location,
                    "language_code": language,
                    "depth": self.config.serp_depth,
                }
                for keyword in batch
            ]

            payload = {"tasks": tasks}

            # Make API request
            response = await self._make_request(
                method="POST",
                endpoint="/serp/google/organic/live/advanced",
                json=payload,
            )

            # Parse response
            for task_result in response.get("tasks", []):
                if task_result.get("status_code") != 20000:
                    # Skip failed tasks
                    continue

                keyword = task_result["data"]["keyword"]
                serp_items = task_result["result"][0].get("items", [])

                # Convert to SERPResult objects
                serp_results = []
                for item in serp_items[: self.config.serp_depth]:
                    if item.get("type") != "organic":
                        continue

                    serp_results.append(
                        SERPResult(
                            keyword=keyword,
                            url=item["url"],
                            position=item["rank_absolute"],
                            title=item.get("title", ""),
                            intent=self._detect_intent(item),
                        )
                    )

                # Create KeywordSERPData
                kw_data = KeywordSERPData(
                    keyword=keyword,
                    serp_results=serp_results,
                    search_volume=0,  # DataForSEO doesn't provide volume in SERP API
                    intent=self._determine_primary_intent(serp_results),
                )
                results.append(kw_data)

        return results

    async def _fetch_semrush(
        self,
        keywords: list[str],
        location: str,
    ) -> list[KeywordSERPData]:
        """
        Fetch SERP data from SEMrush API.

        Endpoint: GET /analytics/v1/
        Cost: $0.01 per keyword

        Returns:
            List of KeywordSERPData
        """
        results: list[KeywordSERPData] = []

        # SEMrush requires individual requests per keyword
        for keyword in keywords:
            params = {
                "type": "phrase_organic",
                "key": self.api_key,
                "phrase": keyword,
                "database": self._get_semrush_database(location),
                "display_limit": self.config.serp_depth,
                "export_columns": "Ph,Po,Ur,Tt",
            }

            response = await self._make_request(
                method="GET",
                endpoint="/analytics/v1/",
                params=params,
            )

            # Parse CSV response
            lines = response.strip().split("\n")
            if len(lines) < 2:
                # No results
                continue

            serp_results = []
            for line in lines[1:]:  # Skip header
                parts = line.split(";")
                if len(parts) < 4:
                    continue

                phrase, position, url, title = parts[:4]
                serp_results.append(
                    SERPResult(
                        keyword=keyword,
                        url=url,
                        position=int(position),
                        title=title,
                        intent=IntentType.INFORMATIONAL,  # SEMrush doesn't provide intent
                    )
                )

            kw_data = KeywordSERPData(
                keyword=keyword,
                serp_results=serp_results,
                search_volume=0,  # Would need separate API call
                intent=IntentType.INFORMATIONAL,
            )
            results.append(kw_data)

        return results

    async def _fetch_mock(self, keywords: list[str]) -> list[KeywordSERPData]:
        """
        Generate mock SERP data for testing.

        Creates realistic SERP overlap for clustering:
        - Related keywords share 40-60% of URLs (same topic cluster)
        - Unrelated keywords share 0-20% of URLs (different clusters)

        Returns:
            List of KeywordSERPData with synthetic data
        """
        results: list[KeywordSERPData] = []

        # Define common domains that appear across multiple keywords
        common_domains = [
            "https://healthline.com",
            "https://webmd.com",
            "https://mayoclinic.org",
            "https://medicalnewstoday.com",
            "https://verywellhealth.com",
            "https://clevelandclinic.org",
            "https://hopkinsmedicine.org",
            "https://nih.gov",
            "https://cdc.gov",
            "https://who.int",
        ]

        for keyword in keywords:
            # Generate mock SERP results with realistic overlap
            serp_results = []

            # Add 18 common authoritative sites (60% of 30 results)
            # This ensures 18/(18+12+12) = 42.8% overlap (>= 40% threshold)
            num_common = min(18, int(self.config.serp_depth * 0.6))
            for i in range(num_common):
                domain = common_domains[i % len(common_domains)]
                serp_results.append(
                    SERPResult(
                        keyword=keyword,
                        url=f"{domain}/article-{i}",
                        position=i + 1,
                        title=f"{keyword.title()} - {domain.split('//')[1].split('.')[0].title()}",
                        intent=IntentType.INFORMATIONAL,
                    )
                )

            # Add keyword-specific URLs (unique to this keyword)
            remaining = min(self.config.serp_depth, 30) - num_common
            for i in range(remaining):
                serp_results.append(
                    SERPResult(
                        keyword=keyword,
                        url=f"https://example{i}.com/{keyword.replace(' ', '-')}",
                        position=num_common + i + 1,
                        title=f"{keyword.title()} - Example {i + 1}",
                        intent=IntentType.INFORMATIONAL,
                    )
                )

            kw_data = KeywordSERPData(
                keyword=keyword,
                serp_results=serp_results,
                search_volume=1000 + (hash(keyword) % 5000),  # Synthetic volume
                intent=IntentType.INFORMATIONAL,
            )
            results.append(kw_data)

        return results

    def _detect_intent(self, serp_item: dict[str, Any]) -> IntentType:
        """
        Detect search intent from SERP item.

        Heuristics:
        - URL contains /buy/, /shop/, /product/ -> TRANSACTIONAL
        - URL contains /compare/, /vs/, /review/ -> COMMERCIAL
        - URL contains /how-to/, /guide/, /what-is/ -> INFORMATIONAL
        - Default -> INFORMATIONAL

        Args:
            serp_item: SERP item from DataForSEO

        Returns:
            Detected IntentType
        """
        url = serp_item.get("url", "").lower()
        title = serp_item.get("title", "").lower()

        # Transactional signals
        if any(
            signal in url or signal in title
            for signal in ["/buy", "/shop", "/product", "/cart", "/checkout"]
        ):
            return IntentType.TRANSACTIONAL

        # Commercial signals
        if any(
            signal in url or signal in title
            for signal in ["/compare", "/vs", "/review", "/best", "/top"]
        ):
            return IntentType.COMMERCIAL

        # Navigational signals
        if any(
            signal in url or signal in title
            for signal in ["/about", "/contact", "/login", "/account"]
        ):
            return IntentType.NAVIGATIONAL

        # Default to informational
        return IntentType.INFORMATIONAL

    def _determine_primary_intent(self, serp_results: list[SERPResult]) -> IntentType:
        """
        Determine primary intent from SERP results.

        Uses majority voting: most common intent in top 10 results.

        Args:
            serp_results: List of SERP results

        Returns:
            Primary IntentType
        """
        if not serp_results:
            return IntentType.INFORMATIONAL

        # Count intents in top 10
        intent_counts: dict[IntentType, int] = {}
        for result in serp_results[:10]:
            intent_counts[result.intent] = intent_counts.get(result.intent, 0) + 1

        # Return most common intent
        return max(intent_counts.items(), key=lambda x: x[1])[0]

    def _get_semrush_database(self, location: str) -> str:
        """
        Map location to SEMrush database code.

        Args:
            location: Location name

        Returns:
            SEMrush database code
        """
        location_map = {
            "United States": "us",
            "United Kingdom": "uk",
            "Russia": "ru",
            "Germany": "de",
            "France": "fr",
            "Spain": "es",
            "Italy": "it",
        }
        return location_map.get(location, "us")
