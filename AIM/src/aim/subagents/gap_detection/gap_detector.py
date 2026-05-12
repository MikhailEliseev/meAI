"""Gap Detector for Content Gap Analysis Agent.

Detects three types of content gaps:
1. URL-based gaps (missing pages)
2. Topic-based gaps (underrepresented topics)
3. Keyword-based gaps (missing keywords)
"""

from datetime import datetime, timezone
from typing import Any

from AIM.src.aim.subagents.schemas.content_gap import (
    ContentGap,
    GapSeverity,
    GapType,
)


class GapDetector:
    """Detects content gaps between client and competitors."""

    def __init__(self, min_content_quality: float = 0.6):
        """Initialize gap detector.

        Args:
            min_content_quality: Minimum E-E-A-T score to consider (0.0-1.0)
        """
        self.min_content_quality = min_content_quality

    async def detect_topic_gaps(
        self,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
        topic_clusters: list[dict[str, Any]],
    ) -> list[ContentGap]:
        """Detect topic-based gaps.

        Args:
            client_pages: List of client pages with topics
            competitor_pages: List of competitor pages with topics
            topic_clusters: List of topic clusters from BERTopic

        Returns:
            List of detected content gaps
        """
        gaps: list[ContentGap] = []

        # Group pages by topic cluster
        client_by_topic = self._group_by_topic(client_pages)
        competitor_by_topic = self._group_by_topic(competitor_pages)

        # Detect gaps for each topic cluster
        for cluster in topic_clusters:
            cluster_id = cluster["cluster_id"]
            cluster_name = cluster["name"]

            # Skip outlier cluster (-1)
            if cluster_id == -1:
                continue

            client_coverage = len(client_by_topic.get(cluster_id, []))
            competitor_coverage = len(competitor_by_topic.get(cluster_id, []))

            # Filter competitor pages by quality
            quality_competitor_pages = [
                p
                for p in competitor_by_topic.get(cluster_id, [])
                if p.get("eeat_score", 0) >= self.min_content_quality
            ]
            quality_competitor_coverage = len(quality_competitor_pages)

            # Detect gap
            if quality_competitor_coverage > client_coverage:
                gap = self._create_topic_gap(
                    cluster_id=cluster_id,
                    cluster_name=cluster_name,
                    client_coverage=client_coverage,
                    competitor_coverage=quality_competitor_coverage,
                    competitor_pages=quality_competitor_pages,
                )
                gaps.append(gap)

        return gaps

    async def detect_url_gaps(
        self,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
    ) -> list[ContentGap]:
        """Detect URL-based gaps (missing pages).

        Args:
            client_pages: List of client pages
            competitor_pages: List of competitor pages

        Returns:
            List of detected content gaps
        """
        gaps: list[ContentGap] = []

        # Extract client URLs (normalized)
        client_urls = {self._normalize_url(p["url"]) for p in client_pages}

        # Group competitor pages by similar URLs
        url_groups = self._group_similar_urls(competitor_pages)

        # Detect missing URLs
        for url_pattern, pages in url_groups.items():
            # Check if client has similar URL
            has_similar = any(
                self._urls_similar(url_pattern, client_url)
                for client_url in client_urls
            )

            if not has_similar:
                # Filter by quality
                quality_pages = [
                    p
                    for p in pages
                    if p.get("eeat_score", 0) >= self.min_content_quality
                ]

                if quality_pages:
                    gap = self._create_url_gap(
                        url_pattern=url_pattern,
                        competitor_pages=quality_pages,
                    )
                    gaps.append(gap)

        return gaps

    async def detect_keyword_gaps(
        self,
        client_pages: list[dict[str, Any]],
        competitor_pages: list[dict[str, Any]],
    ) -> list[ContentGap]:
        """Detect keyword-based gaps (missing keywords).

        Args:
            client_pages: List of client pages with keywords
            competitor_pages: List of competitor pages with keywords

        Returns:
            List of detected content gaps
        """
        gaps: list[ContentGap] = []

        # Extract client keywords
        client_keywords = set()
        for page in client_pages:
            client_keywords.update(page.get("keywords", []))

        # Extract competitor keywords
        competitor_keywords: dict[str, list[dict[str, Any]]] = {}
        for page in competitor_pages:
            for keyword in page.get("keywords", []):
                if keyword not in competitor_keywords:
                    competitor_keywords[keyword] = []
                competitor_keywords[keyword].append(page)

        # Detect missing keywords
        for keyword, pages in competitor_keywords.items():
            if keyword not in client_keywords:
                # Filter by quality
                quality_pages = [
                    p
                    for p in pages
                    if p.get("eeat_score", 0) >= self.min_content_quality
                ]

                if quality_pages:
                    gap = self._create_keyword_gap(
                        keyword=keyword,
                        competitor_pages=quality_pages,
                    )
                    gaps.append(gap)

        return gaps

    def _group_by_topic(
        self, pages: list[dict[str, Any]]
    ) -> dict[int, list[dict[str, Any]]]:
        """Group pages by topic cluster ID."""
        grouped: dict[int, list[dict[str, Any]]] = {}
        for page in pages:
            cluster_id = page.get("cluster_id", -1)
            if cluster_id not in grouped:
                grouped[cluster_id] = []
            grouped[cluster_id].append(page)
        return grouped

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")
        # Remove trailing slash
        url = url.rstrip("/")
        # Remove www
        url = url.replace("www.", "")
        return url.lower()

    def _group_similar_urls(
        self, pages: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group pages by similar URL patterns."""
        groups: dict[str, list[dict[str, Any]]] = {}

        for page in pages:
            url = page["url"]
            # Extract URL pattern (path without domain)
            pattern = self._extract_url_pattern(url)

            if pattern not in groups:
                groups[pattern] = []
            groups[pattern].append(page)

        return groups

    def _extract_url_pattern(self, url: str) -> str:
        """Extract URL pattern from full URL."""
        # Remove protocol and domain
        parts = url.split("/")
        if len(parts) > 3:
            # Keep path after domain
            return "/" + "/".join(parts[3:])
        return "/"

    def _urls_similar(self, pattern1: str, pattern2: str) -> bool:
        """Check if two URL patterns are similar."""
        # Simple similarity: same path structure
        parts1 = [p for p in pattern1.split("/") if p]  # Remove empty parts
        parts2 = [p for p in pattern2.split("/") if p]

        if len(parts1) != len(parts2):
            return False

        if not parts1:  # Both are root
            return True

        # Check if at least 50% of parts match (more lenient for URL patterns)
        matches = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
        return matches / len(parts1) >= 0.5

    def _create_topic_gap(
        self,
        cluster_id: int,
        cluster_name: str,
        client_coverage: int,
        competitor_coverage: int,
        competitor_pages: list[dict[str, Any]],
    ) -> ContentGap:
        """Create topic-based content gap."""
        # Calculate severity
        if client_coverage == 0:
            severity = GapSeverity.HIGH
        elif client_coverage < competitor_coverage / 2:
            severity = GapSeverity.MEDIUM
        else:
            severity = GapSeverity.LOW

        # Extract competitor coverage details
        competitor_coverage_dict = {}
        for page in competitor_pages:
            domain = self._extract_domain(page["url"])
            if domain not in competitor_coverage_dict:
                competitor_coverage_dict[domain] = {
                    "url": page["url"],
                    "quality_score": page.get("eeat_score", 0),
                    "traffic_estimate": page.get("traffic_estimate", 0),
                    "word_count": page.get("word_count", 0),
                    "doctor_authored": page.get("doctor_authored", False),
                    "medical_citations": page.get("medical_citations", 0),
                }

        # Generate recommendations
        avg_word_count = sum(p.get("word_count", 0) for p in competitor_pages) / len(
            competitor_pages
        )
        recommendations = [
            f"Create comprehensive content ({int(avg_word_count)}+ words)",
            "Include doctor author credentials (DDS/DMD)",
            "Add medical citations (PubMed)",
        ]

        # Extract target keywords
        target_keywords = []
        for page in competitor_pages:
            target_keywords.extend(page.get("keywords", []))
        target_keywords = list(set(target_keywords))[:10]  # Top 10 unique

        return ContentGap(
            topic=cluster_name,
            gap_type=GapType.MISSING_TOPIC,
            severity=severity,
            opportunity_score=0.0,  # Will be calculated by OpportunityScorer
            priority="P3",  # Will be assigned by OpportunityScorer
            competitor_coverage=competitor_coverage_dict,
            recommended_actions=recommendations,
            target_keywords=target_keywords,
            detected_at=datetime.now(timezone.utc),
        )

    def _create_url_gap(
        self,
        url_pattern: str,
        competitor_pages: list[dict[str, Any]],
    ) -> ContentGap:
        """Create URL-based content gap."""
        # Extract topic from URL pattern
        topic = url_pattern.replace("/", " ").replace("-", " ").strip()

        # Calculate severity (missing URL = HIGH)
        severity = GapSeverity.HIGH

        # Extract competitor coverage details
        competitor_coverage_dict = {}
        for page in competitor_pages:
            domain = self._extract_domain(page["url"])
            if domain not in competitor_coverage_dict:
                competitor_coverage_dict[domain] = {
                    "url": page["url"],
                    "quality_score": page.get("eeat_score", 0),
                    "traffic_estimate": page.get("traffic_estimate", 0),
                    "word_count": page.get("word_count", 0),
                    "doctor_authored": page.get("doctor_authored", False),
                    "medical_citations": page.get("medical_citations", 0),
                }

        # Generate recommendations
        avg_word_count = sum(p.get("word_count", 0) for p in competitor_pages) / len(
            competitor_pages
        )
        recommendations = [
            f"Create page at similar URL: {url_pattern}",
            f"Target word count: {int(avg_word_count)}+ words",
            "Match competitor content structure",
        ]

        # Extract target keywords
        target_keywords = []
        for page in competitor_pages:
            target_keywords.extend(page.get("keywords", []))
        target_keywords = list(set(target_keywords))[:10]

        return ContentGap(
            topic=topic,
            gap_type=GapType.MISSING_URL,
            severity=severity,
            opportunity_score=0.0,
            priority="P3",
            competitor_coverage=competitor_coverage_dict,
            recommended_actions=recommendations,
            target_keywords=target_keywords,
            detected_at=datetime.now(timezone.utc),
        )

    def _create_keyword_gap(
        self,
        keyword: str,
        competitor_pages: list[dict[str, Any]],
    ) -> ContentGap:
        """Create keyword-based content gap."""
        # Calculate severity (missing keyword = MEDIUM)
        severity = GapSeverity.MEDIUM

        # Extract competitor coverage details
        competitor_coverage_dict = {}
        for page in competitor_pages:
            domain = self._extract_domain(page["url"])
            if domain not in competitor_coverage_dict:
                competitor_coverage_dict[domain] = {
                    "url": page["url"],
                    "quality_score": page.get("eeat_score", 0),
                    "traffic_estimate": page.get("traffic_estimate", 0),
                    "word_count": page.get("word_count", 0),
                    "doctor_authored": page.get("doctor_authored", False),
                    "medical_citations": page.get("medical_citations", 0),
                }

        # Generate recommendations
        recommendations = [
            f"Create content targeting keyword: {keyword}",
            "Optimize for search intent",
            "Include keyword in title and headings",
        ]

        return ContentGap(
            topic=keyword,
            gap_type=GapType.MISSING_KEYWORD,
            severity=severity,
            opportunity_score=0.0,
            priority="P3",
            competitor_coverage=competitor_coverage_dict,
            recommended_actions=recommendations,
            target_keywords=[keyword],
            detected_at=datetime.now(timezone.utc),
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")
        # Get domain (first part before /)
        domain = url.split("/")[0]
        # Remove www
        domain = domain.replace("www.", "")
        return domain
