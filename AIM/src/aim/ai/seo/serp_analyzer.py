"""
SERP Analyzer for SEO

Analyzes SERP features, competitor gaps, and ranking opportunities.
Uses SerpAPI for real-time SERP data.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None

from .schemas import SERPAnalysis, SERPFeature


class SERPAnalyzer:
    """
    SERP feature analysis and competitor gap detection.

    Features:
    - SerpAPI integration (Google, Yandex)
    - Featured snippet detection
    - People Also Ask extraction
    - Knowledge Panel analysis
    - SERP feature identification
    - Competitor gap analysis
    - Top 10 URL tracking
    """

    # SERP feature types
    SERP_FEATURES = {
        "featured_snippet": "Featured Snippet",
        "knowledge_graph": "Knowledge Graph",
        "people_also_ask": "People Also Ask",
        "local_pack": "Local Pack",
        "image_pack": "Image Pack",
        "video_carousel": "Video Carousel",
        "news_results": "News Results",
        "shopping_results": "Shopping Results",
        "related_searches": "Related Searches",
        "site_links": "Site Links",
    }

    def __init__(self, api_key: str, engine: str = "google"):
        """
        Initialize SERP analyzer.

        Args:
            api_key: SerpAPI key
            engine: Search engine (google, yandex)
        """
        if httpx is None:
            raise ImportError("httpx is required. Install with: pip install httpx")

        self.api_key = api_key
        self.engine = engine
        self.base_url = "https://serpapi.com/search"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def analyze(
        self,
        query: str,
        location: str = "Russia",
        language: str = "ru",
    ) -> SERPAnalysis:
        """
        Analyze SERP for query.

        Args:
            query: Search query
            location: Location (default: Russia)
            language: Language (default: ru)

        Returns:
            SERPAnalysis with features, gaps, top URLs
        """
        # Fetch SERP data
        serp_data = await self._fetch_serp(query, location, language)

        # Extract featured snippet
        featured_snippet = self._extract_featured_snippet(serp_data)

        # Extract PAA questions
        paa_questions = self._extract_paa(serp_data)

        # Extract knowledge panel
        knowledge_panel = self._extract_knowledge_panel(serp_data)

        # Identify SERP features
        serp_features = self._identify_features(serp_data)

        # Extract top 10 URLs
        top_10_urls = self._extract_top_urls(serp_data)

        # Analyze competitor gaps
        competitor_gaps = self._analyze_gaps(serp_data, serp_features)

        return SERPAnalysis(
            query=query,
            featured_snippet=featured_snippet,
            paa_questions=paa_questions,
            knowledge_panel=knowledge_panel,
            competitor_gaps=competitor_gaps,
            serp_features=serp_features,
            top_10_urls=top_10_urls,
        )

    async def _fetch_serp(
        self,
        query: str,
        location: str,
        language: str,
    ) -> Dict[str, Any]:
        """
        Fetch SERP data from SerpAPI.

        Args:
            query: Search query
            location: Location
            language: Language

        Returns:
            SERP data dict
        """
        params = {
            "api_key": self.api_key,
            "engine": self.engine,
            "q": query,
            "location": location,
            "hl": language,
            "gl": "ru" if language == "ru" else "us",
        }

        try:
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            # Return empty dict on error
            return {}

    def _extract_featured_snippet(self, serp_data: Dict[str, Any]) -> Optional[str]:
        """Extract featured snippet text."""
        # Google featured snippet
        if "answer_box" in serp_data:
            answer_box = serp_data["answer_box"]
            if "snippet" in answer_box:
                return answer_box["snippet"]
            if "answer" in answer_box:
                return answer_box["answer"]

        # Yandex featured snippet
        if "featured_snippet" in serp_data:
            return serp_data["featured_snippet"].get("snippet")

        return None

    def _extract_paa(self, serp_data: Dict[str, Any]) -> List[str]:
        """Extract People Also Ask questions."""
        questions = []

        # Google PAA
        if "related_questions" in serp_data:
            for q in serp_data["related_questions"]:
                if "question" in q:
                    questions.append(q["question"])

        # Yandex similar queries
        if "related_searches" in serp_data:
            for search in serp_data["related_searches"]:
                if "query" in search:
                    questions.append(search["query"])

        return questions[:10]  # Limit to 10

    def _extract_knowledge_panel(self, serp_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract Knowledge Panel data."""
        # Google Knowledge Graph
        if "knowledge_graph" in serp_data:
            kg = serp_data["knowledge_graph"]
            return {
                "title": kg.get("title"),
                "type": kg.get("type"),
                "description": kg.get("description"),
                "source": kg.get("source", {}).get("name"),
            }

        return None

    def _identify_features(self, serp_data: Dict[str, Any]) -> List[SERPFeature]:
        """
        Identify SERP features present.

        Args:
            serp_data: SERP data

        Returns:
            List of SERPFeature objects
        """
        features = []

        # Featured snippet
        if "answer_box" in serp_data or "featured_snippet" in serp_data:
            features.append(
                SERPFeature(
                    type="featured_snippet",
                    present=True,
                    owned=False,  # TODO: Check if our URL owns it
                    opportunity_score=90.0,
                )
            )

        # Knowledge Graph
        if "knowledge_graph" in serp_data:
            features.append(
                SERPFeature(
                    type="knowledge_graph",
                    present=True,
                    owned=False,
                    opportunity_score=95.0,
                )
            )

        # People Also Ask
        if "related_questions" in serp_data:
            features.append(
                SERPFeature(
                    type="people_also_ask",
                    present=True,
                    owned=False,
                    opportunity_score=80.0,
                )
            )

        # Local Pack
        if "local_results" in serp_data:
            features.append(
                SERPFeature(
                    type="local_pack",
                    present=True,
                    owned=False,
                    opportunity_score=85.0,
                )
            )

        # Image Pack
        if "images_results" in serp_data:
            features.append(
                SERPFeature(
                    type="image_pack",
                    present=True,
                    owned=False,
                    opportunity_score=70.0,
                )
            )

        # Video Carousel
        if "video_results" in serp_data:
            features.append(
                SERPFeature(
                    type="video_carousel",
                    present=True,
                    owned=False,
                    opportunity_score=75.0,
                )
            )

        # News Results
        if "news_results" in serp_data:
            features.append(
                SERPFeature(
                    type="news_results",
                    present=True,
                    owned=False,
                    opportunity_score=65.0,
                )
            )

        # Shopping Results
        if "shopping_results" in serp_data:
            features.append(
                SERPFeature(
                    type="shopping_results",
                    present=True,
                    owned=False,
                    opportunity_score=60.0,
                )
            )

        # Related Searches
        if "related_searches" in serp_data:
            features.append(
                SERPFeature(
                    type="related_searches",
                    present=True,
                    owned=False,
                    opportunity_score=50.0,
                )
            )

        return features

    def _extract_top_urls(self, serp_data: Dict[str, Any]) -> List[str]:
        """Extract top 10 organic URLs."""
        urls = []

        # Google organic results
        if "organic_results" in serp_data:
            for result in serp_data["organic_results"][:10]:
                if "link" in result:
                    urls.append(result["link"])

        return urls

    def _analyze_gaps(
        self,
        serp_data: Dict[str, Any],
        serp_features: List[SERPFeature],
    ) -> List[str]:
        """
        Analyze competitor gaps and opportunities.

        Args:
            serp_data: SERP data
            serp_features: Identified SERP features

        Returns:
            List of gap descriptions
        """
        gaps = []

        # Featured snippet opportunity
        if any(f.type == "featured_snippet" and not f.owned for f in serp_features):
            gaps.append(
                "Featured Snippet не занят - возможность захватить позицию #0 "
                "через структурированный ответ и schema.org"
            )

        # Knowledge Graph opportunity
        if any(f.type == "knowledge_graph" and not f.owned for f in serp_features):
            gaps.append(
                "Knowledge Graph присутствует - оптимизировать сущности и "
                "schema.org для попадания в граф знаний"
            )

        # PAA opportunity
        if any(f.type == "people_also_ask" and not f.owned for f in serp_features):
            paa_count = len(serp_data.get("related_questions", []))
            gaps.append(
                f"People Also Ask ({paa_count} вопросов) - создать FAQ-секцию "
                "с ответами на эти вопросы"
            )

        # Local Pack opportunity
        if any(f.type == "local_pack" and not f.owned for f in serp_features):
            gaps.append(
                "Local Pack присутствует - оптимизировать Google Business Profile "
                "и локальные сигналы"
            )

        # Image Pack opportunity
        if any(f.type == "image_pack" and not f.owned for f in serp_features):
            gaps.append(
                "Image Pack присутствует - оптимизировать изображения "
                "(alt text, file names, ImageObject schema)"
            )

        # Video opportunity
        if any(f.type == "video_carousel" and not f.owned for f in serp_features):
            gaps.append(
                "Video Carousel присутствует - создать видео-контент "
                "и оптимизировать с VideoObject schema"
            )

        # Content depth gap
        if "organic_results" in serp_data:
            top_result = serp_data["organic_results"][0] if serp_data["organic_results"] else None
            if top_result and "snippet" in top_result:
                snippet_length = len(top_result["snippet"])
                if snippet_length > 200:
                    gaps.append(
                        f"Топ-1 имеет развёрнутый сниппет ({snippet_length} символов) - "
                        "увеличить глубину контента и структурированность"
                    )

        return gaps
