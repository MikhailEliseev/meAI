"""SEMrush API Client with Keyword Magic Tool

Keyword expansion using SEMrush Keyword Magic Tool API with budget guard,
zero-volume handling, and intent detection.
"""

from typing import Any, Optional

from ..schemas.api_responses import KeywordDataUnified, SEMrushKeywordData
from .base import APIClientBase


class SEMrushClient(APIClientBase):
    """SEMrush API client for keyword research

    Features:
    - Keyword Magic Tool API integration
    - Pagination (100 keywords per page)
    - Budget guard (stops at max_cost_usd)
    - Zero-volume handling with suggestions
    - Intent detection
    - Min volume filtering

    Args:
        api_key: SEMrush API key
        rate_limit_capacity: Max requests in bucket (default 10)
        rate_limit_refill: Requests per second (default 1.0)
        cache_ttl: Cache TTL in seconds (default 3600)
    """

    # SEMrush API pricing (approximate)
    COST_PER_REQUEST = 0.01  # $0.01 per API call
    KEYWORDS_PER_PAGE = 100

    def __init__(
        self,
        api_key: str,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 1.0,
        cache_ttl: int = 3600,
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://api.semrush.com",
            rate_limit_capacity=rate_limit_capacity,
            rate_limit_refill=rate_limit_refill,
            cache_ttl=cache_ttl,
        )

    async def expand_keywords(
        self,
        seed_keyword: str,
        max_keywords: int = 100,
        min_volume: int = 10,
        max_cost_usd: float = 5.0,
    ) -> list[dict[str, Any]]:
        """Expand seed keyword using Keyword Magic Tool

        Args:
            seed_keyword: Seed keyword to expand
            max_keywords: Maximum keywords to return
            min_volume: Minimum search volume
            max_cost_usd: Maximum cost in USD

        Returns:
            List of unified keyword data dictionaries

        Raises:
            ValueError: If zero volume found and no alternatives
            RuntimeError: If budget exceeded
        """
        keywords: list[dict[str, Any]] = []
        total_cost = 0.0
        offset = 0

        self.logger.info(
            "keyword_expansion_start",
            seed_keyword=seed_keyword,
            max_keywords=max_keywords,
            min_volume=min_volume,
            max_cost_usd=max_cost_usd,
        )

        while len(keywords) < max_keywords:
            # Budget guard
            if total_cost + self.COST_PER_REQUEST >= max_cost_usd:
                self.logger.warning(
                    "budget_limit_reached",
                    total_cost=total_cost,
                    max_cost=max_cost_usd,
                    keywords_collected=len(keywords),
                )
                break

            # Fetch page
            try:
                page_data = await self._fetch_keyword_page(
                    seed_keyword=seed_keyword,
                    offset=offset,
                    limit=self.KEYWORDS_PER_PAGE,
                    min_volume=min_volume,
                )

                total_cost += self.COST_PER_REQUEST

                # Track cost metric
                from .base import api_cost_total
                api_cost_total.labels(
                    client=self.__class__.__name__,
                    endpoint="keyword_magic",
                ).inc(self.COST_PER_REQUEST)

            except Exception as e:
                self.logger.error(
                    "keyword_fetch_error",
                    error=str(e),
                    offset=offset,
                )
                break

            # Check for zero volume
            if not page_data or len(page_data) == 0:
                if min_volume > 0:
                    # Retry with min_volume=0
                    self.logger.info(
                        "zero_volume_retry",
                        seed_keyword=seed_keyword,
                        original_min_volume=min_volume,
                    )
                    return await self.expand_keywords(
                        seed_keyword=seed_keyword,
                        max_keywords=max_keywords,
                        min_volume=0,
                        max_cost_usd=max_cost_usd - total_cost,
                    )
                else:
                    # No results even with min_volume=0
                    suggestions = await self._get_keyword_suggestions(seed_keyword)
                    raise ValueError(
                        f"No keywords found for '{seed_keyword}'. "
                        f"Suggestions: {', '.join(suggestions)}"
                    )

            # Process keywords
            for kw_data in page_data:
                if len(keywords) >= max_keywords:
                    break

                # Parse and validate
                try:
                    semrush_kw = SEMrushKeywordData(**kw_data)
                    unified_kw = KeywordDataUnified.from_semrush(semrush_kw)
                    keywords.append(unified_kw.model_dump())
                except Exception as e:
                    self.logger.warning(
                        "keyword_validation_error",
                        keyword=kw_data.get("keyword"),
                        error=str(e),
                    )
                    continue

            # Check if we got all available keywords
            if len(page_data) < self.KEYWORDS_PER_PAGE:
                break

            offset += self.KEYWORDS_PER_PAGE

        self.logger.info(
            "keyword_expansion_complete",
            seed_keyword=seed_keyword,
            keywords_collected=len(keywords),
            total_cost=total_cost,
        )

        return keywords

    async def _fetch_keyword_page(
        self,
        seed_keyword: str,
        offset: int,
        limit: int,
        min_volume: int,
    ) -> list[dict[str, Any]]:
        """Fetch single page of keywords from Keyword Magic Tool

        Args:
            seed_keyword: Seed keyword
            offset: Pagination offset
            limit: Results per page
            min_volume: Minimum search volume

        Returns:
            List of keyword data dictionaries
        """
        params = {
            "type": "phrase_related",
            "key": self.api_key,
            "phrase": seed_keyword,
            "database": "us",  # US database
            "display_limit": limit,
            "display_offset": offset,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td",  # Phrase, Volume, CPC, Competition, Results, Trend
        }

        if min_volume > 0:
            params["display_filter"] = f"+|Nq|Gt|{min_volume}"

        response = await self._make_request(
            method="GET",
            endpoint="/analytics/v1/",
            params=params,
        )

        # Parse SEMrush response format
        keywords = []
        if "data" in response:
            for row in response["data"]:
                keyword_data = self._parse_semrush_row(row)
                if keyword_data:
                    keywords.append(keyword_data)

        return keywords

    def _parse_semrush_row(self, row: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Parse SEMrush API row into keyword data

        Args:
            row: SEMrush API row

        Returns:
            Keyword data dictionary or None if invalid
        """
        try:
            keyword = row.get("Ph", "").strip()
            volume = int(row.get("Nq", 0))
            cpc = float(row.get("Cp", 0.0))
            competition = float(row.get("Co", 0.0))
            trend = row.get("Td", "")

            # Calculate difficulty from competition (0-1 → 0-100)
            difficulty = int(competition * 100)

            # Detect intent
            intent = self._detect_intent(keyword)

            return {
                "keyword": keyword,
                "volume": volume,
                "difficulty": difficulty,
                "cpc": cpc,
                "intent": intent,
                "trend": trend,
                "competition": competition,
            }

        except (ValueError, KeyError) as e:
            self.logger.warning(
                "row_parse_error",
                row=row,
                error=str(e),
            )
            return None

    def _detect_intent(self, keyword: str) -> str:
        """Detect search intent from keyword

        Args:
            keyword: Keyword phrase

        Returns:
            Intent type: informational, commercial, navigational, local
        """
        keyword_lower = keyword.lower()

        # Local intent
        if any(loc in keyword_lower for loc in ["near me", "local", "nearby", "in "]):
            return "local"

        # Informational intent
        if any(
            q in keyword_lower
            for q in ["what", "how", "why", "when", "benefits", "risks", "guide"]
        ):
            return "informational"

        # Commercial intent
        if any(
            c in keyword_lower
            for c in [
                "cost",
                "price",
                "buy",
                "book",
                "consultation",
                "appointment",
                "cheap",
                "affordable",
            ]
        ):
            return "commercial"

        # Navigational intent
        if any(n in keyword_lower for n in ["best", "top", "review", "vs"]):
            return "navigational"

        return "informational"  # Default

    async def _get_keyword_suggestions(self, seed_keyword: str) -> list[str]:
        """Get keyword suggestions for zero-volume keywords

        Args:
            seed_keyword: Original seed keyword

        Returns:
            List of suggested keywords
        """
        # Try related keywords
        try:
            params = {
                "type": "phrase_related",
                "key": self.api_key,
                "phrase": seed_keyword,
                "database": "us",
                "display_limit": 5,
                "export_columns": "Ph,Nq",
            }

            response = await self._make_request(
                method="GET",
                endpoint="/analytics/v1/",
                params=params,
            )

            suggestions = []
            if "data" in response:
                for row in response["data"]:
                    keyword = row.get("Ph", "").strip()
                    if keyword and keyword != seed_keyword:
                        suggestions.append(keyword)

            return suggestions[:5]  # Top 5 suggestions

        except Exception as e:
            self.logger.error(
                "suggestions_fetch_error",
                error=str(e),
            )
            return []
