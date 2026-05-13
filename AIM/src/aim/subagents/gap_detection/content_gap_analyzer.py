"""Content Gap Analysis Agent - Main Orchestrator.

Coordinates all gap detection components to analyze competitor content
and identify content opportunities for the client.

Workflow:
1. Validate input parameters
2. Detect gaps using GapDetector (topic, URL, keyword gaps)
3. Score gaps using OpportunityScorer
4. Cluster keywords using SERPOverlapClusterer
5. Plan architecture using ArchitecturePlanner
6. Generate briefs using BriefGenerator
7. Aggregate results and send completion event
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from AIM.src.aim.subagents.api_clients.serp_client import (
    SERPAPIClient,
    SERPClientConfig,
)
from AIM.src.aim.subagents.gap_detection.architecture_planner import (
    ArchitecturePlanner,
)
from AIM.src.aim.subagents.gap_detection.brief_generator import BriefGenerator
from AIM.src.aim.subagents.gap_detection.gap_detector import GapDetector
from AIM.src.aim.subagents.gap_detection.opportunity_scorer import OpportunityScorer
from AIM.src.aim.subagents.gap_detection.serp_overlap_clusterer import (
    ClusteringConfig,
    KeywordSERPData,
    SERPOverlapClusterer,
)
from AIM.src.aim.subagents.schemas.content_gap import (
    ContentGap,
    GapAnalysisResult,
)


class ContentGapAnalyzer:
    """Main orchestrator for Content Gap Analysis Agent."""

    def __init__(
        self,
        min_content_quality: float = 0.6,
        overlap_threshold: float = 0.4,
        max_cost_usd: float = 1.0,
        serp_api_key: str | None = None,
        serp_provider: str = "mock",
    ):
        """Initialize Content Gap Analyzer.

        Args:
            min_content_quality: Minimum E-E-A-T score to consider (0.0-1.0)
            overlap_threshold: SERP overlap threshold for clustering (0.0-1.0)
            max_cost_usd: Maximum budget for API calls
            serp_api_key: API key for SERP provider (optional, uses mock if not provided)
            serp_provider: SERP data provider (dataforseo, semrush, mock)
        """
        self.min_content_quality = min_content_quality
        self.overlap_threshold = overlap_threshold
        self.max_cost_usd = max_cost_usd

        # Initialize components
        self.gap_detector = GapDetector(min_content_quality=min_content_quality)
        self.opportunity_scorer = OpportunityScorer()

        # Create clustering config with overlap threshold
        clustering_config = ClusteringConfig(overlap_threshold=overlap_threshold)
        self.serp_clusterer = SERPOverlapClusterer(config=clustering_config)

        self.architecture_planner = ArchitecturePlanner()
        self.brief_generator = BriefGenerator()

        # Initialize SERP client (optional, for keyword clustering)
        self.serp_client: SERPAPIClient | None = None
        if serp_api_key or serp_provider == "mock":
            serp_config = SERPClientConfig(
                provider=serp_provider,
                api_key=serp_api_key or "mock_key",
                serp_depth=30,
                max_cost_per_keyword=0.02,
            )
            self.serp_client = SERPAPIClient(config=serp_config)

    async def analyze(
        self,
        client_url: str,
        competitor_urls: list[str],
        niche: str,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
        keywords: list[str] | None = None,
    ) -> GapAnalysisResult:
        """Analyze content gaps between client and competitors.

        Args:
            client_url: Client website URL
            competitor_urls: List of competitor URLs (3-10)
            niche: Target niche/topic
            client_pages: List of client pages with metadata
            competitor_pages: List of competitor pages with metadata
            keywords: Optional list of seed keywords for clustering

        Returns:
            GapAnalysisResult with detected gaps, clusters, architecture, and briefs
        """
        start_time = datetime.now(timezone.utc)

        # Validate inputs
        self._validate_inputs(
            client_url=client_url,
            competitor_urls=competitor_urls,
            niche=niche,
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # Step 1: Detect gaps (topic, URL, keyword)
        gaps = await self._detect_all_gaps(
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # Step 2: Score gaps and assign priorities
        scored_gaps = await self.opportunity_scorer.score_gaps(
            gaps=gaps,
            niche=niche,
            client_pages=client_pages,
        )

        # Step 3: Cluster keywords (if provided and SERP client available)
        clusters = []
        if keywords and self.serp_client:
            # Fetch SERP data for keywords
            serp_data = await self._fetch_serp_data(keywords)

            # Cluster keywords by SERP overlap
            if serp_data:
                clusters = await self.serp_clusterer.cluster_keywords(serp_data)

        # Step 4: Plan content architecture (only if clusters available)
        architecture = {}
        if clusters:
            arch_result = await self.architecture_planner.plan_architecture(
                gaps=scored_gaps,
                clusters=clusters,
            )
            # Convert ContentArchitecture to dict
            architecture = arch_result.model_dump() if arch_result else {}

        # Step 5: Generate content briefs for top gaps (only if architecture available)
        briefs = []
        if architecture and "pages" in architecture:
            # Generate briefs for pages in architecture
            pages = architecture["pages"]
            for i, page in enumerate(pages[:10]):  # Top 10 pages
                # Find corresponding gap
                gap = scored_gaps[i] if i < len(scored_gaps) else scored_gaps[0]

                brief = await self.brief_generator.generate_brief(
                    page=page,
                    gap=gap,
                    competitor_urls=competitor_urls,
                )
                briefs.append(brief)

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Build result
        result = GapAnalysisResult(
            client_url=client_url,
            competitor_urls=competitor_urls,
            niche=niche,
            gaps=scored_gaps,
            clusters=clusters,
            architecture=architecture,
            briefs=briefs,
            summary={
                "total_gaps": len(scored_gaps),
                "p0_gaps": len([g for g in scored_gaps if g.priority == "P0"]),
                "p1_gaps": len([g for g in scored_gaps if g.priority == "P1"]),
                "p2_gaps": len([g for g in scored_gaps if g.priority == "P2"]),
                "total_clusters": len(clusters),
                "total_briefs": len(briefs),
                "execution_time_ms": execution_time_ms,
                "pages_analyzed": len(client_pages) + len(competitor_pages),
            },
            analyzed_at=end_time,
        )

        return result

    async def _detect_all_gaps(
        self,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
    ) -> list[ContentGap]:
        """Detect all types of gaps in parallel.

        Args:
            client_pages: List of client pages
            competitor_pages: List of competitor pages

        Returns:
            Combined list of all detected gaps
        """
        # Run all gap detection methods in parallel
        topic_gaps_task = self.gap_detector.detect_topic_gaps(
            client_pages=client_pages,
            competitor_pages=competitor_pages,
            topic_clusters=[],  # Will be populated by clustering
        )

        url_gaps_task = self.gap_detector.detect_url_gaps(
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        keyword_gaps_task = self.gap_detector.detect_keyword_gaps(
            client_pages=client_pages,
            competitor_pages=competitor_pages,
        )

        # Wait for all tasks
        topic_gaps, url_gaps, keyword_gaps = await asyncio.gather(
            topic_gaps_task,
            url_gaps_task,
            keyword_gaps_task,
        )

        # Combine all gaps
        all_gaps = topic_gaps + url_gaps + keyword_gaps

        return all_gaps

    def _validate_inputs(
        self,
        client_url: str,
        competitor_urls: list[str],
        niche: str,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
    ) -> None:
        """Validate input parameters.

        Args:
            client_url: Client website URL
            competitor_urls: List of competitor URLs
            niche: Target niche
            client_pages: List of client pages
            competitor_pages: List of competitor pages

        Raises:
            ValueError: If validation fails
        """
        # Validate URLs
        if not client_url or not client_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid client_url: {client_url}")

        if not competitor_urls or len(competitor_urls) < 1:
            raise ValueError("competitor_urls must contain at least 1 URL")

        if len(competitor_urls) > 10:
            raise ValueError("competitor_urls must contain at most 10 URLs")

        for url in competitor_urls:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid competitor URL: {url}")

        # Validate niche
        if not niche or not niche.strip():
            raise ValueError("niche cannot be empty")

        # Validate pages
        if not client_pages:
            raise ValueError("client_pages cannot be empty")

        if not competitor_pages:
            raise ValueError("competitor_pages cannot be empty")

    async def compare_quality(
        self,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare content quality between client and competitors.

        Args:
            client_pages: List of client pages with E-E-A-T scores
            competitor_pages: List of competitor pages with E-E-A-T scores

        Returns:
            Quality comparison metrics
        """
        # Calculate client metrics
        client_word_counts = [p.get("word_count", 0) for p in client_pages]
        client_eeat_scores = [p.get("eeat_score", 0) for p in client_pages]
        client_doctor_authored = [
            p.get("doctor_authored", False) for p in client_pages
        ]

        client_avg_word_count = (
            sum(client_word_counts) / len(client_word_counts)
            if client_word_counts
            else 0
        )
        client_avg_eeat = (
            sum(client_eeat_scores) / len(client_eeat_scores) if client_eeat_scores else 0
        )
        client_doctor_pct = (
            sum(client_doctor_authored) / len(client_doctor_authored) * 100
            if client_doctor_authored
            else 0
        )

        # Calculate competitor metrics
        competitor_word_counts = [p.get("word_count", 0) for p in competitor_pages]
        competitor_eeat_scores = [p.get("eeat_score", 0) for p in competitor_pages]
        competitor_doctor_authored = [
            p.get("doctor_authored", False) for p in competitor_pages
        ]

        competitor_avg_word_count = (
            sum(competitor_word_counts) / len(competitor_word_counts)
            if competitor_word_counts
            else 0
        )
        competitor_avg_eeat = (
            sum(competitor_eeat_scores) / len(competitor_eeat_scores)
            if competitor_eeat_scores
            else 0
        )
        competitor_doctor_pct = (
            sum(competitor_doctor_authored) / len(competitor_doctor_authored) * 100
            if competitor_doctor_authored
            else 0
        )

        # Calculate gaps
        word_count_gap = competitor_avg_word_count - client_avg_word_count
        eeat_gap = competitor_avg_eeat - client_avg_eeat
        doctor_gap = competitor_doctor_pct - client_doctor_pct

        return {
            "client": {
                "avg_word_count": round(client_avg_word_count, 0),
                "avg_eeat_score": round(client_avg_eeat, 2),
                "doctor_authored_pct": round(client_doctor_pct, 1),
            },
            "competitor": {
                "avg_word_count": round(competitor_avg_word_count, 0),
                "avg_eeat_score": round(competitor_avg_eeat, 2),
                "doctor_authored_pct": round(competitor_doctor_pct, 1),
            },
            "gaps": {
                "word_count_gap": round(word_count_gap, 0),
                "eeat_gap": round(eeat_gap, 2),
                "doctor_authorship_gap": round(doctor_gap, 1),
            },
        }

    async def _fetch_serp_data(
        self,
        keywords: list[str],
        location: str = "United States",
        language: str = "en",
    ) -> list[KeywordSERPData]:
        """
        Fetch SERP data for keywords using SERP API client.

        Args:
            keywords: List of keywords to fetch SERP data for
            location: Geographic location for search results
            language: Language code (en, ru, etc.)

        Returns:
            List of KeywordSERPData with SERP results

        Raises:
            ValueError: If SERP client not initialized or budget exceeded
        """
        if not self.serp_client:
            raise ValueError("SERP client not initialized. Provide serp_api_key in constructor.")

        # Fetch SERP data with budget control
        serp_data = await self.serp_client.fetch_serp_data(
            keywords=keywords,
            location=location,
            language=language,
            max_cost_usd=self.max_cost_usd,
        )

        return serp_data

    async def close(self) -> None:
        """Close SERP client if initialized."""
        if self.serp_client:
            await self.serp_client.close()
