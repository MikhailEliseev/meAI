"""Opportunity Scorer for Content Gap Analysis Agent.

Calculates opportunity scores and assigns priority tiers to content gaps.
"""

from typing import Any

from aim.subagents.schemas.content_gap import ContentGap


class OpportunityScorer:
    """Calculates opportunity scores for content gaps."""

    def __init__(
        self,
        traffic_weight: float = 0.4,
        quality_weight: float = 0.3,
        relevance_weight: float = 0.2,
        volume_weight: float = 0.1,
        difficulty_weight: float = 0.6,
        coverage_weight: float = 0.4,
    ):
        """Initialize opportunity scorer.

        Args:
            traffic_weight: Weight for competitor traffic (0.0-1.0)
            quality_weight: Weight for competitor quality (0.0-1.0)
            relevance_weight: Weight for topic relevance (0.0-1.0)
            volume_weight: Weight for keyword volume (0.0-1.0)
            difficulty_weight: Weight for content difficulty (0.0-1.0)
            coverage_weight: Weight for existing coverage (0.0-1.0)
        """
        self.traffic_weight = traffic_weight
        self.quality_weight = quality_weight
        self.relevance_weight = relevance_weight
        self.volume_weight = volume_weight
        self.difficulty_weight = difficulty_weight
        self.coverage_weight = coverage_weight

    async def score_gaps(
        self,
        gaps: list[ContentGap],
        niche: str,
        client_pages: list[dict[str, Any]],
    ) -> list[ContentGap]:
        """Calculate opportunity scores for all gaps.

        Args:
            gaps: List of detected content gaps
            niche: Target niche for relevance calculation
            client_pages: List of client pages for coverage calculation

        Returns:
            List of gaps with calculated scores and priorities
        """
        scored_gaps = []

        for gap in gaps:
            # Calculate opportunity score
            score = await self._calculate_opportunity_score(
                gap=gap,
                niche=niche,
                client_pages=client_pages,
            )

            # Assign priority tier
            priority = self._assign_priority_tier(score)

            # Update gap
            gap.opportunity_score = score
            gap.priority = priority

            scored_gaps.append(gap)

        # Sort by score (descending)
        scored_gaps.sort(key=lambda g: g.opportunity_score, reverse=True)

        return scored_gaps

    async def _calculate_opportunity_score(
        self,
        gap: ContentGap,
        niche: str,
        client_pages: list[dict[str, Any]],
    ) -> float:
        """Calculate opportunity score for a single gap.

        Formula:
        opportunity_score = (
            competitor_avg_traffic * 0.4 +
            competitor_avg_quality * 0.3 +
            topic_relevance_to_niche * 0.2 +
            keyword_search_volume * 0.1
        ) / (
            content_difficulty * 0.6 +
            existing_client_coverage * 0.4
        )

        Normalized to 0-100 scale.
        """
        # Calculate numerator components
        competitor_traffic = self._calculate_competitor_traffic(gap)
        competitor_quality = self._calculate_competitor_quality(gap)
        topic_relevance = self._calculate_topic_relevance(gap, niche)
        keyword_volume = self._calculate_keyword_volume(gap)

        numerator = (
            competitor_traffic * self.traffic_weight
            + competitor_quality * self.quality_weight
            + topic_relevance * self.relevance_weight
            + keyword_volume * self.volume_weight
        )

        # Calculate denominator components
        content_difficulty = self._calculate_content_difficulty(gap)
        client_coverage = self._calculate_client_coverage(gap, client_pages)

        denominator = (
            content_difficulty * self.difficulty_weight
            + client_coverage * self.coverage_weight
        )

        # Avoid division by zero
        if denominator == 0:
            denominator = 0.1

        # Calculate score
        score = (numerator / denominator) * 100

        # Normalize to 0-100
        score = max(0.0, min(100.0, score))

        return round(score, 2)

    def _calculate_competitor_traffic(self, gap: ContentGap) -> float:
        """Calculate average competitor traffic (normalized 0-1)."""
        if not gap.competitor_coverage:
            return 0.0

        traffic_estimates = [
            page.get("traffic_estimate", 0)
            for page in gap.competitor_coverage
        ]

        if not traffic_estimates:
            return 0.0

        avg_traffic = sum(traffic_estimates) / len(traffic_estimates)

        # Normalize: 0 traffic = 0.0, 10000+ traffic = 1.0
        normalized = min(avg_traffic / 10000, 1.0)

        return normalized

    def _calculate_competitor_quality(self, gap: ContentGap) -> float:
        """Calculate average competitor quality (normalized 0-1)."""
        if not gap.competitor_coverage:
            return 0.0

        quality_scores = [
            page.get("quality_score", 0)
            for page in gap.competitor_coverage
        ]

        if not quality_scores:
            return 0.0

        avg_quality = sum(quality_scores) / len(quality_scores)

        return avg_quality  # Already 0-1

    def _calculate_topic_relevance(self, gap: ContentGap, niche: str) -> float:
        """Calculate topic relevance to niche (normalized 0-1)."""
        # Simple keyword matching for now
        # TODO: Use embeddings for semantic similarity
        niche_keywords = set(niche.lower().split())
        topic_keywords = set(gap.topic.lower().split())

        if not topic_keywords:
            return 0.5  # Neutral

        # Calculate overlap
        overlap = len(niche_keywords & topic_keywords)
        relevance = overlap / len(topic_keywords)

        return min(relevance, 1.0)

    def _calculate_keyword_volume(self, gap: ContentGap) -> float:
        """Calculate keyword search volume (normalized 0-1)."""
        # Placeholder: assume medium volume
        # TODO: Integrate with Keyword Research Agent
        return 0.5

    def _calculate_content_difficulty(self, gap: ContentGap) -> float:
        """Calculate content creation difficulty (normalized 0-1)."""
        if not gap.competitor_coverage:
            return 0.5  # Medium difficulty

        # Factors:
        # 1. Average word count (longer = harder)
        # 2. Doctor authorship requirement (yes = harder)
        # 3. Medical citations requirement (more = harder)

        word_counts = [
            page.get("word_count", 0) for page in gap.competitor_coverage
        ]
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0

        doctor_authored = [
            page.get("doctor_authored", False)
            for page in gap.competitor_coverage
        ]
        doctor_pct = sum(doctor_authored) / len(doctor_authored) if doctor_authored else 0

        citations = [
            page.get("medical_citations", 0)
            for page in gap.competitor_coverage
        ]
        avg_citations = sum(citations) / len(citations) if citations else 0

        # Normalize components
        word_count_difficulty = min(avg_word_count / 3000, 1.0)  # 3000+ words = 1.0
        doctor_difficulty = doctor_pct  # Already 0-1
        citation_difficulty = min(avg_citations / 10, 1.0)  # 10+ citations = 1.0

        # Weighted average
        difficulty = (
            word_count_difficulty * 0.4
            + doctor_difficulty * 0.3
            + citation_difficulty * 0.3
        )

        return difficulty

    def _calculate_client_coverage(
        self, gap: ContentGap, client_pages: list[dict[str, Any]]
    ) -> float:
        """Calculate existing client coverage (normalized 0-1)."""
        # Check if client has any pages on this topic
        topic_keywords = set(gap.topic.lower().split())

        matching_pages = 0
        for page in client_pages:
            page_keywords = set(page.get("title", "").lower().split())
            page_keywords.update([k.lower() for k in page.get("keywords", [])])

            # Check overlap - require at least 50% of topic keywords to match
            overlap = len(topic_keywords & page_keywords)
            if overlap >= len(topic_keywords) * 0.5:
                matching_pages += 1

        # Normalize: 0 pages = 0.0, 5+ pages = 1.0
        coverage = min(matching_pages / 5, 1.0)

        return coverage

    def _assign_priority_tier(self, score: float) -> str:
        """Assign priority tier based on opportunity score.

        Args:
            score: Opportunity score (0-100)

        Returns:
            Priority tier: P0, P1, P2, or P3
        """
        if score >= 80:
            return "P0"  # High Priority
        elif score >= 60:
            return "P1"  # Medium Priority
        elif score >= 40:
            return "P2"  # Low Priority
        else:
            return "P3"  # Very Low Priority

    async def calculate_quality_comparison(
        self,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate quality comparison between client and competitors.

        Args:
            client_pages: List of client pages
            competitor_pages: List of competitor pages

        Returns:
            Quality comparison metrics
        """
        # Client metrics
        client_metrics = self._aggregate_metrics(client_pages)

        # Competitor metrics
        competitor_metrics = self._aggregate_metrics(competitor_pages)

        # Calculate gaps
        gaps = {
            "word_count_gap": competitor_metrics["avg_word_count"]
            - client_metrics["avg_word_count"],
            "eeat_gap": competitor_metrics["avg_eeat_score"]
            - client_metrics["avg_eeat_score"],
            "doctor_authorship_gap": competitor_metrics["doctor_authored_pct"]
            - client_metrics["doctor_authored_pct"],
            "citations_gap": competitor_metrics["medical_citations_per_page"]
            - client_metrics["medical_citations_per_page"],
        }

        return {
            "client": client_metrics,
            "competitors_avg": competitor_metrics,
            "gaps": gaps,
        }

    def _aggregate_metrics(self, pages: list[dict[str, Any]]) -> dict[str, float]:
        """Aggregate metrics for a list of pages."""
        if not pages:
            return {
                "avg_word_count": 0.0,
                "avg_eeat_score": 0.0,
                "doctor_authored_pct": 0.0,
                "medical_citations_per_page": 0.0,
            }

        word_counts = [p.get("word_count", 0) for p in pages]
        eeat_scores = [p.get("eeat_score", 0) for p in pages]
        doctor_authored = [p.get("doctor_authored", False) for p in pages]
        citations = [p.get("medical_citations", 0) for p in pages]

        return {
            "avg_word_count": sum(word_counts) / len(word_counts),
            "avg_eeat_score": sum(eeat_scores) / len(eeat_scores),
            "doctor_authored_pct": sum(doctor_authored) / len(doctor_authored),
            "medical_citations_per_page": sum(citations) / len(citations),
        }
