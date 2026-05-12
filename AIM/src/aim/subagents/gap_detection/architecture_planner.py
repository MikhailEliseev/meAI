"""
Architecture Planner - Hub-and-spoke content architecture planning.

Implements hub-and-spoke content architecture:
1. Identify hub pages (pillar content for main topics)
2. Identify spoke pages (supporting content for subtopics)
3. Plan internal linking structure
4. Prioritize content creation order
5. Estimate traffic potential

Based on: https://ahrefs.com/blog/hub-and-spoke-model/
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from AIM.src.aim.subagents.schemas.content_gap import (
    ContentCluster,
    ContentGap,
    GapSeverity,
    IntentType,
)


class PageType(str, Enum):
    """Type of page in hub-and-spoke architecture."""

    HUB = "hub"  # Pillar page covering broad topic
    SPOKE = "spoke"  # Supporting page covering specific subtopic
    STANDALONE = "standalone"  # Independent page not part of cluster


class ContentPage(BaseModel):
    """Planned content page in architecture."""

    title: str = Field(..., description="Page title")
    url_slug: str = Field(..., description="URL slug (e.g., /dental-implants-cost)")
    page_type: PageType = Field(..., description="Hub, spoke, or standalone")
    target_keyword: str = Field(..., description="Primary target keyword")
    related_keywords: list[str] = Field(
        default_factory=list, description="Related keywords to target"
    )
    search_volume: int = Field(default=0, ge=0, description="Total search volume")
    intent: IntentType = Field(..., description="Primary search intent")
    hub_page_slug: str | None = Field(
        default=None, description="Parent hub page slug (for spoke pages)"
    )
    spoke_page_slugs: list[str] = Field(
        default_factory=list, description="Child spoke page slugs (for hub pages)"
    )
    priority: int = Field(default=0, ge=0, le=100, description="Creation priority (0-100)")
    estimated_traffic: int = Field(
        default=0, ge=0, description="Estimated monthly traffic"
    )
    content_brief_required: bool = Field(
        default=True, description="Whether content brief is needed"
    )

    @field_validator("url_slug")
    @classmethod
    def validate_url_slug(cls, v: str) -> str:
        """Validate URL slug format."""
        if not v.startswith("/"):
            v = f"/{v}"
        if not v.replace("/", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid URL slug: {v}")
        return v


class ContentArchitecture(BaseModel):
    """Complete hub-and-spoke content architecture."""

    hub_pages: list[ContentPage] = Field(
        default_factory=list, description="Hub (pillar) pages"
    )
    spoke_pages: list[ContentPage] = Field(
        default_factory=list, description="Spoke (supporting) pages"
    )
    standalone_pages: list[ContentPage] = Field(
        default_factory=list, description="Standalone pages"
    )
    total_estimated_traffic: int = Field(
        default=0, ge=0, description="Total estimated monthly traffic"
    )
    creation_order: list[str] = Field(
        default_factory=list, description="Recommended creation order (URL slugs)"
    )

    @property
    def total_pages(self) -> int:
        """Total number of pages in architecture."""
        return len(self.hub_pages) + len(self.spoke_pages) + len(self.standalone_pages)


@dataclass
class PlanningConfig:
    """Configuration for architecture planning."""

    min_hub_volume: int = 500  # Min search volume for hub page
    min_spoke_volume: int = 50  # Min search volume for spoke page
    max_spokes_per_hub: int = 10  # Max spoke pages per hub
    traffic_multiplier: float = 0.3  # CTR estimate (30% of search volume)
    prioritize_by: str = "traffic"  # Priority metric: traffic, volume, or severity


class ArchitecturePlanner:
    """
    Plans hub-and-spoke content architecture from content gaps.

    Workflow:
    1. Group gaps by content clusters
    2. Identify hub pages (high-volume cluster centers)
    3. Identify spoke pages (supporting subtopics)
    4. Plan internal linking structure
    5. Prioritize content creation order
    6. Estimate traffic potential
    """

    def __init__(self, config: PlanningConfig | None = None):
        """Initialize planner with config."""
        self.config = config or PlanningConfig()

    async def plan_architecture(
        self,
        gaps: list[ContentGap],
        clusters: list[ContentCluster],
    ) -> ContentArchitecture:
        """
        Plan hub-and-spoke architecture from gaps and clusters.

        Args:
            gaps: Content gaps to address
            clusters: Topic clusters from SERP overlap analysis

        Returns:
            Complete content architecture with hub/spoke pages

        Raises:
            ValueError: If gaps or clusters are empty
        """
        if not gaps:
            raise ValueError("gaps cannot be empty")
        if not clusters:
            raise ValueError("clusters cannot be empty")

        # Build hub pages from clusters
        hub_pages = self._build_hub_pages(clusters, gaps)

        # Build spoke pages from cluster keywords
        spoke_pages = self._build_spoke_pages(clusters, gaps, hub_pages)

        # Build standalone pages from unclustered gaps
        standalone_pages = self._build_standalone_pages(gaps, clusters)

        # Calculate total estimated traffic
        all_pages = hub_pages + spoke_pages + standalone_pages
        total_traffic = sum(page.estimated_traffic for page in all_pages)

        # Determine creation order
        creation_order = self._determine_creation_order(all_pages)

        return ContentArchitecture(
            hub_pages=hub_pages,
            spoke_pages=spoke_pages,
            standalone_pages=standalone_pages,
            total_estimated_traffic=total_traffic,
            creation_order=creation_order,
        )

    def _build_hub_pages(
        self, clusters: list[ContentCluster], gaps: list[ContentGap]
    ) -> list[ContentPage]:
        """
        Build hub pages from content clusters.

        Hub page criteria:
        - Cluster hub keyword with volume >= min_hub_volume
        - Covers broad topic (cluster center)
        - Has multiple spoke pages (cluster size >= 3)
        """
        hub_pages: list[ContentPage] = []

        for cluster in clusters:
            # Check if cluster qualifies for hub page
            if cluster.total_search_volume < self.config.min_hub_volume:
                continue
            if len(cluster.keywords) < 3:
                continue

            # Find gap for hub keyword
            hub_gap = next(
                (g for g in gaps if g.missing_keyword == cluster.hub_keyword), None
            )
            if not hub_gap:
                continue

            # Create hub page
            hub_page = ContentPage(
                title=self._generate_title(cluster.hub_keyword),
                url_slug=self._generate_slug(cluster.hub_keyword),
                page_type=PageType.HUB,
                target_keyword=cluster.hub_keyword,
                related_keywords=cluster.spoke_keywords[: self.config.max_spokes_per_hub],
                search_volume=cluster.total_search_volume,
                intent=cluster.primary_intent,
                hub_page_slug=None,
                spoke_page_slugs=[],  # Will be populated later
                priority=self._calculate_priority(hub_gap, cluster.total_search_volume),
                estimated_traffic=int(
                    cluster.total_search_volume * self.config.traffic_multiplier
                ),
                content_brief_required=True,
            )
            hub_pages.append(hub_page)

        return hub_pages

    def _build_spoke_pages(
        self,
        clusters: list[ContentCluster],
        gaps: list[ContentGap],
        hub_pages: list[ContentPage],
    ) -> list[ContentPage]:
        """
        Build spoke pages from cluster keywords.

        Spoke page criteria:
        - Cluster spoke keyword with volume >= min_spoke_volume
        - Links to parent hub page
        - Covers specific subtopic
        """
        spoke_pages: list[ContentPage] = []
        hub_map = {hub.target_keyword: hub for hub in hub_pages}

        for cluster in clusters:
            # Find hub page for this cluster
            hub_page = hub_map.get(cluster.hub_keyword)
            if not hub_page:
                continue

            # Create spoke pages for cluster keywords
            for spoke_kw in cluster.spoke_keywords[: self.config.max_spokes_per_hub]:
                # Find gap for spoke keyword
                spoke_gap = next((g for g in gaps if g.missing_keyword == spoke_kw), None)
                if not spoke_gap:
                    continue

                # Check volume threshold
                if spoke_gap.search_volume < self.config.min_spoke_volume:
                    continue

                # Create spoke page
                spoke_page = ContentPage(
                    title=self._generate_title(spoke_kw),
                    url_slug=self._generate_slug(spoke_kw),
                    page_type=PageType.SPOKE,
                    target_keyword=spoke_kw,
                    related_keywords=[cluster.hub_keyword],
                    search_volume=spoke_gap.search_volume,
                    intent=cluster.primary_intent,
                    hub_page_slug=hub_page.url_slug,
                    spoke_page_slugs=[],
                    priority=self._calculate_priority(spoke_gap, spoke_gap.search_volume),
                    estimated_traffic=int(
                        spoke_gap.search_volume * self.config.traffic_multiplier
                    ),
                    content_brief_required=True,
                )
                spoke_pages.append(spoke_page)

                # Add to hub's spoke list
                hub_page.spoke_page_slugs.append(spoke_page.url_slug)

        return spoke_pages

    def _build_standalone_pages(
        self, gaps: list[ContentGap], clusters: list[ContentCluster]
    ) -> list[ContentPage]:
        """
        Build standalone pages from unclustered gaps.

        Standalone page criteria:
        - Gap not covered by any cluster
        - Volume >= min_spoke_volume
        - High priority (P0 or P1)
        """
        standalone_pages: list[ContentPage] = []

        # Get all clustered keywords
        clustered_keywords = set()
        for cluster in clusters:
            clustered_keywords.update(cluster.keywords)

        # Find unclustered gaps
        for gap in gaps:
            # Skip if already in cluster
            if gap.missing_keyword in clustered_keywords:
                continue

            # Check volume threshold
            if gap.search_volume < self.config.min_spoke_volume:
                continue

            # Check priority (only P0/P1)
            if gap.severity not in (GapSeverity.CRITICAL, GapSeverity.HIGH):
                continue

            # Create standalone page
            standalone_page = ContentPage(
                title=self._generate_title(gap.missing_keyword),
                url_slug=self._generate_slug(gap.missing_keyword),
                page_type=PageType.STANDALONE,
                target_keyword=gap.missing_keyword,
                related_keywords=[],
                search_volume=gap.search_volume,
                intent=IntentType.INFORMATIONAL,  # Default
                hub_page_slug=None,
                spoke_page_slugs=[],
                priority=self._calculate_priority(gap, gap.search_volume),
                estimated_traffic=int(gap.search_volume * self.config.traffic_multiplier),
                content_brief_required=True,
            )
            standalone_pages.append(standalone_page)

        return standalone_pages

    def _generate_title(self, keyword: str) -> str:
        """Generate page title from keyword."""
        # Capitalize first letter of each word
        return " ".join(word.capitalize() for word in keyword.split())

    def _generate_slug(self, keyword: str) -> str:
        """Generate URL slug from keyword."""
        # Replace spaces with hyphens, lowercase
        slug = keyword.lower().replace(" ", "-")
        return f"/{slug}"

    def _calculate_priority(self, gap: ContentGap, search_volume: int) -> int:
        """
        Calculate content creation priority (0-100).

        Priority factors:
        - Gap severity (P0=100, P1=75, P2=50, P3=25)
        - Search volume (normalized)
        - Opportunity score
        """
        # Base priority from severity
        severity_scores = {
            GapSeverity.CRITICAL: 100,
            GapSeverity.HIGH: 75,
            GapSeverity.MEDIUM: 50,
            GapSeverity.LOW: 25,
        }
        base_priority = severity_scores.get(gap.severity, 25)

        # Adjust by search volume (normalize to 0-20 range)
        volume_bonus = min(20, int(search_volume / 100))

        # Adjust by opportunity score (normalize to 0-10 range)
        opportunity_bonus = int(gap.opportunity_score * 10)

        # Total priority (capped at 100)
        priority = min(100, base_priority + volume_bonus + opportunity_bonus)

        return priority

    def _determine_creation_order(self, pages: list[ContentPage]) -> list[str]:
        """
        Determine optimal content creation order.

        Strategy:
        1. Create hub pages first (foundation)
        2. Create high-priority spoke pages
        3. Create remaining spoke pages
        4. Create standalone pages

        Within each group, sort by priority metric.
        """
        # Separate by page type
        hubs = [p for p in pages if p.page_type == PageType.HUB]
        spokes = [p for p in pages if p.page_type == PageType.SPOKE]
        standalones = [p for p in pages if p.page_type == PageType.STANDALONE]

        # Sort each group by priority metric
        if self.config.prioritize_by == "traffic":
            sort_key = lambda p: p.estimated_traffic
        elif self.config.prioritize_by == "volume":
            sort_key = lambda p: p.search_volume
        else:  # priority
            sort_key = lambda p: p.priority

        hubs.sort(key=sort_key, reverse=True)
        spokes.sort(key=sort_key, reverse=True)
        standalones.sort(key=sort_key, reverse=True)

        # Combine in order: hubs → spokes → standalones
        ordered_pages = hubs + spokes + standalones

        return [page.url_slug for page in ordered_pages]

    async def export_architecture_summary(
        self, architecture: ContentArchitecture
    ) -> dict[str, Any]:
        """
        Export architecture summary for reporting.

        Returns:
            Dict with architecture statistics and recommendations
        """
        return {
            "total_pages": architecture.total_pages,
            "hub_pages": len(architecture.hub_pages),
            "spoke_pages": len(architecture.spoke_pages),
            "standalone_pages": len(architecture.standalone_pages),
            "total_estimated_traffic": architecture.total_estimated_traffic,
            "avg_traffic_per_page": (
                architecture.total_estimated_traffic // architecture.total_pages
                if architecture.total_pages > 0
                else 0
            ),
            "creation_order_preview": architecture.creation_order[:5],
            "top_priority_pages": [
                {
                    "title": page.title,
                    "url_slug": page.url_slug,
                    "page_type": page.page_type.value,
                    "priority": page.priority,
                    "estimated_traffic": page.estimated_traffic,
                }
                for page in sorted(
                    architecture.hub_pages
                    + architecture.spoke_pages
                    + architecture.standalone_pages,
                    key=lambda p: p.priority,
                    reverse=True,
                )[:5]
            ],
        }
