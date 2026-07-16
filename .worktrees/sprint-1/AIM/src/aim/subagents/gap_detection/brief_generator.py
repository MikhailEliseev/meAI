"""
Brief Generator - SEO content brief generation with E-E-A-T optimization.

Generates comprehensive content briefs for content creation:
1. Target keywords and search intent
2. Competitor content analysis
3. E-E-A-T requirements (medical content)
4. Content structure and outline
5. Word count and readability targets
6. Internal linking recommendations

Based on: https://ahrefs.com/blog/content-brief/
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from AIM.src.aim.subagents.gap_detection.architecture_planner import ContentPage
from AIM.src.aim.subagents.schemas.content_gap import (
    ContentGap,
    IntentType,
)


class ReadabilityLevel(str, Enum):
    """Target readability level for content."""

    ELEMENTARY = "elementary"  # Grade 5-6
    MIDDLE_SCHOOL = "middle_school"  # Grade 7-8
    HIGH_SCHOOL = "high_school"  # Grade 9-12
    COLLEGE = "college"  # College level
    PROFESSIONAL = "professional"  # Professional/academic


class EEATRequirement(BaseModel):
    """E-E-A-T requirement for medical content."""

    category: str = Field(..., description="E-E-A-T category (Experience, Expertise, etc.)")
    requirement: str = Field(..., description="Specific requirement")
    examples: list[str] = Field(default_factory=list, description="Examples of compliance")
    priority: str = Field(default="high", description="Priority: critical, high, medium, low")


class ContentSection(BaseModel):
    """Section in content outline."""

    heading: str = Field(..., description="Section heading (H2/H3)")
    heading_level: int = Field(..., ge=2, le=4, description="Heading level (2-4)")
    target_word_count: int = Field(..., ge=50, description="Target word count for section")
    key_points: list[str] = Field(default_factory=list, description="Key points to cover")
    keywords_to_include: list[str] = Field(
        default_factory=list, description="Keywords to naturally include"
    )


class CompetitorInsight(BaseModel):
    """Insight from competitor content analysis."""

    url: str = Field(..., description="Competitor URL")
    word_count: int = Field(..., ge=0, description="Content word count")
    headings_count: int = Field(..., ge=0, description="Number of headings")
    images_count: int = Field(..., ge=0, description="Number of images")
    internal_links_count: int = Field(..., ge=0, description="Number of internal links")
    external_links_count: int = Field(..., ge=0, description="Number of external links")
    readability_score: float = Field(..., ge=0, le=100, description="Flesch reading ease")
    eeat_score: float = Field(..., ge=0, le=1, description="E-E-A-T score (0-1)")
    strengths: list[str] = Field(default_factory=list, description="Content strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Content weaknesses")


class ContentBrief(BaseModel):
    """Complete SEO content brief."""

    title: str = Field(..., description="Content title")
    target_keyword: str = Field(..., description="Primary target keyword")
    related_keywords: list[str] = Field(
        default_factory=list, description="Related keywords to include"
    )
    search_intent: IntentType = Field(..., description="Primary search intent")
    target_word_count: int = Field(..., ge=300, description="Target word count")
    readability_level: ReadabilityLevel = Field(
        ..., description="Target readability level"
    )
    eeat_requirements: list[EEATRequirement] = Field(
        default_factory=list, description="E-E-A-T requirements"
    )
    content_outline: list[ContentSection] = Field(
        default_factory=list, description="Content structure outline"
    )
    competitor_insights: list[CompetitorInsight] = Field(
        default_factory=list, description="Competitor analysis insights"
    )
    internal_links: list[str] = Field(
        default_factory=list, description="Recommended internal links (URL slugs)"
    )
    external_sources: list[str] = Field(
        default_factory=list, description="Recommended external sources to cite"
    )
    meta_description: str = Field(
        default="", max_length=160, description="Recommended meta description"
    )
    notes: str = Field(default="", description="Additional notes for content creator")

    @field_validator("meta_description")
    @classmethod
    def validate_meta_description(cls, v: str) -> str:
        """Validate meta description length."""
        if len(v) > 160:
            raise ValueError(f"Meta description too long: {len(v)} chars (max 160)")
        return v


@dataclass
class BriefConfig:
    """Configuration for brief generation."""

    min_word_count: int = 800  # Min words for medical content
    max_word_count: int = 3000  # Max words to avoid bloat
    target_readability: ReadabilityLevel = ReadabilityLevel.HIGH_SCHOOL
    min_eeat_score: float = 0.7  # Min E-E-A-T score for medical
    min_sections: int = 5  # Min content sections
    max_sections: int = 12  # Max content sections
    include_faq: bool = True  # Include FAQ section
    include_sources: bool = True  # Include sources section


class BriefGenerator:
    """
    Generates SEO content briefs with E-E-A-T optimization.

    Workflow:
    1. Analyze target keyword and intent
    2. Analyze competitor content
    3. Define E-E-A-T requirements (medical focus)
    4. Generate content outline
    5. Set word count and readability targets
    6. Recommend internal/external links
    7. Generate meta description
    """

    def __init__(self, config: BriefConfig | None = None):
        """Initialize generator with config."""
        self.config = config or BriefConfig()

    async def generate_brief(
        self,
        page: ContentPage,
        gap: ContentGap,
        competitor_urls: list[str],
    ) -> ContentBrief:
        """
        Generate content brief for a page.

        Args:
            page: Content page from architecture planner
            gap: Content gap this page addresses
            competitor_urls: Competitor URLs to analyze

        Returns:
            Complete content brief

        Raises:
            ValueError: If inputs are invalid
        """
        if not page.target_keyword:
            raise ValueError("page.target_keyword cannot be empty")
        if not competitor_urls:
            raise ValueError("competitor_urls cannot be empty")

        # Analyze competitors
        competitor_insights = await self._analyze_competitors(competitor_urls)

        # Calculate target word count
        target_word_count = self._calculate_target_word_count(competitor_insights)

        # Generate E-E-A-T requirements
        eeat_requirements = self._generate_eeat_requirements(page.intent)

        # Generate content outline
        content_outline = self._generate_content_outline(
            page, gap, competitor_insights
        )

        # Generate internal links
        internal_links = self._generate_internal_links(page)

        # Generate external sources
        external_sources = self._generate_external_sources(page.intent)

        # Generate meta description
        meta_description = self._generate_meta_description(page)

        return ContentBrief(
            title=page.title,
            target_keyword=page.target_keyword,
            related_keywords=page.related_keywords,
            search_intent=page.intent,
            target_word_count=target_word_count,
            readability_level=self.config.target_readability,
            eeat_requirements=eeat_requirements,
            content_outline=content_outline,
            competitor_insights=competitor_insights,
            internal_links=internal_links,
            external_sources=external_sources,
            meta_description=meta_description,
            notes=self._generate_notes(page, gap),
        )

    async def _analyze_competitors(
        self, competitor_urls: list[str]
    ) -> list[CompetitorInsight]:
        """
        Analyze competitor content.

        In production, this would:
        1. Scrape competitor pages
        2. Extract content metrics
        3. Calculate E-E-A-T scores
        4. Identify strengths/weaknesses

        For now, returns mock data.
        """
        insights: list[CompetitorInsight] = []

        for url in competitor_urls[:5]:  # Analyze top 5
            # Mock competitor analysis
            insight = CompetitorInsight(
                url=url,
                word_count=1500,
                headings_count=8,
                images_count=5,
                internal_links_count=10,
                external_links_count=8,
                readability_score=65.0,
                eeat_score=0.75,
                strengths=[
                    "Clear structure with H2/H3 headings",
                    "Multiple expert citations",
                    "High-quality images with alt text",
                ],
                weaknesses=[
                    "Missing FAQ section",
                    "No author credentials displayed",
                    "Limited internal linking",
                ],
            )
            insights.append(insight)

        return insights

    def _calculate_target_word_count(
        self, competitor_insights: list[CompetitorInsight]
    ) -> int:
        """
        Calculate target word count based on competitors.

        Strategy: Aim for 10-20% above average competitor length.
        """
        if not competitor_insights:
            return self.config.min_word_count

        avg_word_count = sum(c.word_count for c in competitor_insights) / len(
            competitor_insights
        )

        # Add 15% to beat competitors
        target = int(avg_word_count * 1.15)

        # Clamp to config limits
        target = max(self.config.min_word_count, target)
        target = min(self.config.max_word_count, target)

        return target

    def _generate_eeat_requirements(self, intent: IntentType) -> list[EEATRequirement]:
        """
        Generate E-E-A-T requirements for medical content.

        Medical content requires high E-E-A-T standards.
        """
        requirements = [
            EEATRequirement(
                category="Experience",
                requirement="Include real patient experiences or case studies",
                examples=[
                    "Patient testimonials with consent",
                    "Before/after case studies",
                    "Real-world treatment outcomes",
                ],
                priority="high",
            ),
            EEATRequirement(
                category="Expertise",
                requirement="Content reviewed by licensed dental professional",
                examples=[
                    "Author credentials (DDS, DMD)",
                    "Reviewer credentials displayed",
                    "Professional affiliations mentioned",
                ],
                priority="critical",
            ),
            EEATRequirement(
                category="Authoritativeness",
                requirement="Cite authoritative medical sources",
                examples=[
                    "PubMed studies",
                    "ADA (American Dental Association) guidelines",
                    "Peer-reviewed journals",
                ],
                priority="critical",
            ),
            EEATRequirement(
                category="Trustworthiness",
                requirement="Display trust signals and transparency",
                examples=[
                    "Last updated date",
                    "Editorial process disclosure",
                    "Contact information",
                    "Privacy policy link",
                ],
                priority="high",
            ),
        ]

        # Add intent-specific requirements
        if intent == IntentType.COMMERCIAL:
            requirements.append(
                EEATRequirement(
                    category="Transparency",
                    requirement="Clear pricing and no hidden costs",
                    examples=[
                        "Itemized cost breakdown",
                        "Insurance coverage info",
                        "Financing options",
                    ],
                    priority="high",
                )
            )

        return requirements

    def _generate_content_outline(
        self,
        page: ContentPage,
        gap: ContentGap,
        competitor_insights: list[CompetitorInsight],
    ) -> list[ContentSection]:
        """
        Generate content outline with sections.

        Structure based on search intent and competitor analysis.
        """
        outline: list[ContentSection] = []

        # Introduction section
        outline.append(
            ContentSection(
                heading="Introduction",
                heading_level=2,
                target_word_count=150,
                key_points=[
                    f"What is {page.target_keyword}",
                    "Why this topic matters",
                    "What readers will learn",
                ],
                keywords_to_include=[page.target_keyword],
            )
        )

        # Main content sections (based on intent)
        if page.intent == IntentType.COMMERCIAL:
            outline.extend(
                [
                    ContentSection(
                        heading="Cost Breakdown",
                        heading_level=2,
                        target_word_count=300,
                        key_points=[
                            "Average costs",
                            "Factors affecting price",
                            "Insurance coverage",
                        ],
                        keywords_to_include=["cost", "price", "insurance"],
                    ),
                    ContentSection(
                        heading="Financing Options",
                        heading_level=2,
                        target_word_count=200,
                        key_points=[
                            "Payment plans",
                            "Medical credit cards",
                            "HSA/FSA eligibility",
                        ],
                        keywords_to_include=["financing", "payment"],
                    ),
                ]
            )
        elif page.intent == IntentType.INFORMATIONAL:
            outline.extend(
                [
                    ContentSection(
                        heading="How It Works",
                        heading_level=2,
                        target_word_count=300,
                        key_points=[
                            "Step-by-step process",
                            "Timeline expectations",
                            "What to expect",
                        ],
                        keywords_to_include=["procedure", "process"],
                    ),
                    ContentSection(
                        heading="Benefits and Risks",
                        heading_level=2,
                        target_word_count=250,
                        key_points=[
                            "Key benefits",
                            "Potential risks",
                            "Success rates",
                        ],
                        keywords_to_include=["benefits", "risks"],
                    ),
                ]
            )

        # FAQ section (if enabled)
        if self.config.include_faq:
            outline.append(
                ContentSection(
                    heading="Frequently Asked Questions",
                    heading_level=2,
                    target_word_count=200,
                    key_points=[
                        "Common questions",
                        "Quick answers",
                        "Link to detailed pages",
                    ],
                    keywords_to_include=page.related_keywords[:3],
                )
            )

        # Sources section (if enabled)
        if self.config.include_sources:
            outline.append(
                ContentSection(
                    heading="Sources",
                    heading_level=2,
                    target_word_count=100,
                    key_points=[
                        "Medical sources cited",
                        "Expert reviews",
                        "Last updated date",
                    ],
                    keywords_to_include=[],
                )
            )

        return outline

    def _generate_internal_links(self, page: ContentPage) -> list[str]:
        """
        Generate internal linking recommendations.

        Links to:
        - Hub page (if spoke)
        - Related spoke pages (if hub)
        - Related keywords
        """
        internal_links: list[str] = []

        # Link to hub (if spoke)
        if page.hub_page_slug:
            internal_links.append(page.hub_page_slug)

        # Link to spokes (if hub)
        if page.spoke_page_slugs:
            internal_links.extend(page.spoke_page_slugs[:5])  # Top 5

        return internal_links

    def _generate_external_sources(self, intent: IntentType) -> list[str]:
        """
        Generate recommended external sources to cite.

        Medical content requires authoritative sources.
        """
        sources = [
            "https://pubmed.ncbi.nlm.nih.gov/",
            "https://www.ada.org/",  # American Dental Association
            "https://www.ncbi.nlm.nih.gov/",
            "https://www.mayoclinic.org/",
        ]

        if intent == IntentType.COMMERCIAL:
            sources.append("https://www.healthcare.gov/")  # Insurance info

        return sources

    def _generate_meta_description(self, page: ContentPage) -> str:
        """
        Generate meta description for SEO.

        Format: [Benefit] Learn about [keyword]. [CTA]
        Max 160 characters.
        """
        keyword = page.target_keyword
        intent = page.intent

        if intent == IntentType.COMMERCIAL:
            template = f"Compare {keyword} costs, financing options, and insurance coverage. Get transparent pricing from top providers."
        elif intent == IntentType.TRANSACTIONAL:
            template = f"Book your {keyword} consultation today. Expert care, flexible financing, and proven results."
        else:  # INFORMATIONAL
            template = f"Learn everything about {keyword}: procedure, benefits, risks, and recovery. Expert-reviewed medical guide."

        # Truncate to 160 chars
        if len(template) > 160:
            template = template[:157] + "..."

        return template

    def _generate_notes(self, page: ContentPage, gap: ContentGap) -> str:
        """Generate additional notes for content creator."""
        notes = []

        # Priority note (severity is already a string due to use_enum_values=True)
        if gap.severity == "critical":
            notes.append("⚠️ HIGH PRIORITY: This is a critical content gap.")

        # Opportunity note
        if gap.opportunity_score >= 0.8:
            notes.append(
                f"💰 HIGH OPPORTUNITY: Score {gap.opportunity_score:.2f} - strong traffic potential."
            )

        # Competitor note
        competitor_count = len(gap.competitor_coverage)
        if competitor_count >= 3:
            notes.append(
                f"🔍 COMPETITIVE: {competitor_count} competitors cover this topic - need to differentiate."
            )

        # E-E-A-T note
        notes.append(
            "📋 MEDICAL CONTENT: Must be reviewed by licensed dental professional before publishing."
        )

        return " ".join(notes)

    async def export_brief_markdown(self, brief: ContentBrief) -> str:
        """
        Export brief as markdown for content creators.

        Returns:
            Markdown-formatted content brief
        """
        md_lines = [
            f"# Content Brief: {brief.title}",
            "",
            "## Overview",
            f"- **Target Keyword:** {brief.target_keyword}",
            f"- **Search Intent:** {brief.search_intent.value}",
            f"- **Target Word Count:** {brief.target_word_count} words",
            f"- **Readability Level:** {brief.readability_level.value}",
            "",
            "## Related Keywords",
        ]

        for kw in brief.related_keywords:
            md_lines.append(f"- {kw}")

        md_lines.extend(["", "## E-E-A-T Requirements", ""])

        for req in brief.eeat_requirements:
            md_lines.append(f"### {req.category} ({req.priority})")
            md_lines.append(f"{req.requirement}")
            md_lines.append("")
            md_lines.append("Examples:")
            for example in req.examples:
                md_lines.append(f"- {example}")
            md_lines.append("")

        md_lines.extend(["## Content Outline", ""])

        for section in brief.content_outline:
            heading_prefix = "#" * section.heading_level
            md_lines.append(f"{heading_prefix} {section.heading}")
            md_lines.append(f"*Target: {section.target_word_count} words*")
            md_lines.append("")
            md_lines.append("Key points:")
            for point in section.key_points:
                md_lines.append(f"- {point}")
            md_lines.append("")

        if brief.internal_links:
            md_lines.extend(["## Internal Links", ""])
            for link in brief.internal_links:
                md_lines.append(f"- {link}")
            md_lines.append("")

        if brief.external_sources:
            md_lines.extend(["## External Sources to Cite", ""])
            for source in brief.external_sources:
                md_lines.append(f"- {source}")
            md_lines.append("")

        md_lines.extend(
            [
                "## Meta Description",
                f"{brief.meta_description}",
                "",
                "## Notes",
                brief.notes,
            ]
        )

        return "\n".join(md_lines)
