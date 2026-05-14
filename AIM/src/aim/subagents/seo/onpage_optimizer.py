"""
On-Page SEO Optimizer - Technical SEO Analysis and Optimization.

Analyzes on-page SEO factors: title tags, meta descriptions, headers,
content optimization, internal linking, image optimization, URL structure.

Based on: Google Search Central Guidelines + Yandex Webmaster Guidelines
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog


@dataclass
class TitleTagAnalysis:
    """Title tag analysis."""

    title: str
    length: int
    has_keyword: bool
    keyword_position: int  # 0 = not found, 1 = first word, etc.
    is_optimal_length: bool  # 50-60 chars
    issues: list[str]
    recommendations: list[str]


@dataclass
class MetaDescriptionAnalysis:
    """Meta description analysis."""

    description: str
    length: int
    has_keyword: bool
    has_cta: bool
    is_optimal_length: bool  # 150-160 chars
    issues: list[str]
    recommendations: list[str]


@dataclass
class HeaderStructure:
    """Header structure analysis."""

    h1_count: int
    h1_text: list[str]
    h2_count: int
    h3_count: int
    has_keyword_in_h1: bool
    hierarchy_valid: bool  # H1 → H2 → H3 order
    issues: list[str]
    recommendations: list[str]


@dataclass
class ContentAnalysis:
    """Content quality analysis."""

    word_count: int
    keyword_density: float  # %
    keyword_count: int
    readability_score: float  # Flesch Reading Ease
    paragraph_count: int
    avg_paragraph_length: float
    has_lists: bool
    has_images: bool
    issues: list[str]
    recommendations: list[str]


@dataclass
class InternalLinking:
    """Internal linking analysis."""

    total_links: int
    internal_links: int
    external_links: int
    broken_links: int
    anchor_text_optimized: bool
    link_depth: int  # clicks from homepage
    issues: list[str]
    recommendations: list[str]


@dataclass
class ImageOptimization:
    """Image optimization analysis."""

    total_images: int
    images_with_alt: int
    images_without_alt: int
    alt_text_quality: float  # % with descriptive alt
    large_images: int  # > 100KB
    webp_usage: float  # % using WebP
    issues: list[str]
    recommendations: list[str]


@dataclass
class URLAnalysis:
    """URL structure analysis."""

    url: str
    length: int
    has_keyword: bool
    is_readable: bool
    has_special_chars: bool
    depth: int  # number of slashes
    issues: list[str]
    recommendations: list[str]


@dataclass
class OnPageReport:
    """Complete on-page SEO report."""

    url: str
    timestamp: str

    # Core elements
    title_tag: TitleTagAnalysis
    meta_description: MetaDescriptionAnalysis
    headers: HeaderStructure
    content: ContentAnalysis

    # Technical elements
    internal_linking: InternalLinking
    images: ImageOptimization
    url_analysis: URLAnalysis

    # Overall score
    overall_score: float  # 0-100
    priority_issues: list[str]
    quick_wins: list[str]


class OnPageOptimizer:
    """
    On-Page SEO Optimizer.

    Analyzes on-page SEO factors and provides optimization recommendations.
    """

    def __init__(self):
        """Initialize On-Page SEO Optimizer."""
        self.logger = structlog.get_logger()

    async def analyze(
        self,
        url: str,
        target_keyword: str,
        html_content: str | None = None,
    ) -> OnPageReport:
        """
        Analyze on-page SEO for URL.

        Args:
            url: URL to analyze
            target_keyword: Target keyword for optimization
            html_content: HTML content (if None, will fetch)

        Returns:
            Complete on-page SEO report
        """
        self.logger.info(
            "onpage_analysis_start",
            url=url,
            keyword=target_keyword,
        )

        # Step 1: Fetch HTML if not provided
        if html_content is None:
            html_content = await self._fetch_html(url)

        # Step 2: Analyze title tag
        title_tag = await self._analyze_title_tag(html_content, target_keyword)

        # Step 3: Analyze meta description
        meta_description = await self._analyze_meta_description(
            html_content,
            target_keyword,
        )

        # Step 4: Analyze header structure
        headers = await self._analyze_headers(html_content, target_keyword)

        # Step 5: Analyze content
        content = await self._analyze_content(html_content, target_keyword)

        # Step 6: Analyze internal linking
        internal_linking = await self._analyze_internal_linking(html_content)

        # Step 7: Analyze images
        images = await self._analyze_images(html_content)

        # Step 8: Analyze URL structure
        url_analysis = await self._analyze_url(url, target_keyword)

        # Step 9: Calculate overall score
        overall_score = self._calculate_overall_score(
            title_tag,
            meta_description,
            headers,
            content,
            internal_linking,
            images,
            url_analysis,
        )

        # Step 10: Identify priority issues and quick wins
        priority_issues = self._identify_priority_issues(
            title_tag,
            meta_description,
            headers,
            content,
        )
        quick_wins = self._identify_quick_wins(
            title_tag,
            meta_description,
            images,
        )

        report = OnPageReport(
            url=url,
            timestamp=datetime.now().isoformat(),
            title_tag=title_tag,
            meta_description=meta_description,
            headers=headers,
            content=content,
            internal_linking=internal_linking,
            images=images,
            url_analysis=url_analysis,
            overall_score=round(overall_score, 1),
            priority_issues=priority_issues,
            quick_wins=quick_wins,
        )

        self.logger.info(
            "onpage_analysis_complete",
            url=url,
            score=overall_score,
            issues=len(priority_issues),
        )

        return report

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL."""
        # Mock data for now (real implementation would use httpx)
        return """
        <html>
        <head>
            <title>Dental Implants in Moscow - Best Clinic 2026</title>
            <meta name="description" content="Professional dental implants in Moscow. 15 years experience. Book consultation today!">
        </head>
        <body>
            <h1>Dental Implants in Moscow</h1>
            <p>We provide professional dental implant services with 15 years of experience.</p>
            <h2>Why Choose Us</h2>
            <p>Our clinic offers the best dental implant solutions in Moscow.</p>
            <h3>Our Services</h3>
            <ul>
                <li>Single tooth implants</li>
                <li>Multiple tooth implants</li>
                <li>Full arch restoration</li>
            </ul>
            <img src="clinic.jpg" alt="Dental clinic">
            <img src="doctor.jpg">
            <a href="/services">Our Services</a>
            <a href="/contact">Contact Us</a>
            <a href="https://example.com">External Link</a>
        </body>
        </html>
        """

    async def _analyze_title_tag(
        self,
        html: str,
        keyword: str,
    ) -> TitleTagAnalysis:
        """Analyze title tag."""
        # Extract title
        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        title = title_match.group(1) if title_match else ""

        length = len(title)
        has_keyword = keyword.lower() in title.lower()

        # Find keyword position
        keyword_position = 0
        if has_keyword:
            words = title.lower().split()
            keyword_words = keyword.lower().split()
            for i, word in enumerate(words):
                if word == keyword_words[0]:
                    keyword_position = i + 1
                    break

        is_optimal_length = 50 <= length <= 60

        # Identify issues
        issues = []
        recommendations = []

        if not title:
            issues.append("Title tag missing")
            recommendations.append("Add title tag with target keyword")
        elif length < 30:
            issues.append(f"Title too short ({length} chars)")
            recommendations.append("Expand title to 50-60 characters")
        elif length > 60:
            issues.append(f"Title too long ({length} chars)")
            recommendations.append("Shorten title to 50-60 characters")

        if not has_keyword:
            issues.append("Target keyword not in title")
            recommendations.append(f"Add '{keyword}' to title tag")
        elif keyword_position > 3:
            issues.append("Keyword too far in title")
            recommendations.append("Move keyword closer to beginning")

        return TitleTagAnalysis(
            title=title,
            length=length,
            has_keyword=has_keyword,
            keyword_position=keyword_position,
            is_optimal_length=is_optimal_length,
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_meta_description(
        self,
        html: str,
        keyword: str,
    ) -> MetaDescriptionAnalysis:
        """Analyze meta description."""
        # Extract meta description
        desc_match = re.search(
            r'<meta\s+name="description"\s+content="(.*?)"',
            html,
            re.IGNORECASE,
        )
        description = desc_match.group(1) if desc_match else ""

        length = len(description)
        has_keyword = keyword.lower() in description.lower()

        # Check for CTA
        cta_words = ["book", "call", "contact", "get", "order", "buy", "запись", "звоните"]
        has_cta = any(word in description.lower() for word in cta_words)

        is_optimal_length = 150 <= length <= 160

        # Identify issues
        issues = []
        recommendations = []

        if not description:
            issues.append("Meta description missing")
            recommendations.append("Add meta description with keyword and CTA")
        elif length < 120:
            issues.append(f"Description too short ({length} chars)")
            recommendations.append("Expand description to 150-160 characters")
        elif length > 160:
            issues.append(f"Description too long ({length} chars)")
            recommendations.append("Shorten description to 150-160 characters")

        if not has_keyword:
            issues.append("Target keyword not in description")
            recommendations.append(f"Add '{keyword}' to meta description")

        if not has_cta:
            issues.append("No CTA in description")
            recommendations.append("Add CTA (e.g., 'Book consultation today')")

        return MetaDescriptionAnalysis(
            description=description,
            length=length,
            has_keyword=has_keyword,
            has_cta=has_cta,
            is_optimal_length=is_optimal_length,
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_headers(
        self,
        html: str,
        keyword: str,
    ) -> HeaderStructure:
        """Analyze header structure."""
        # Extract headers
        h1_tags = re.findall(r"<h1>(.*?)</h1>", html, re.IGNORECASE)
        h2_tags = re.findall(r"<h2>(.*?)</h2>", html, re.IGNORECASE)
        h3_tags = re.findall(r"<h3>(.*?)</h3>", html, re.IGNORECASE)

        h1_count = len(h1_tags)
        h2_count = len(h2_tags)
        h3_count = len(h3_tags)

        has_keyword_in_h1 = any(keyword.lower() in h1.lower() for h1 in h1_tags)

        # Check hierarchy (simplified)
        hierarchy_valid = h1_count == 1 and h2_count > 0

        # Identify issues
        issues = []
        recommendations = []

        if h1_count == 0:
            issues.append("No H1 tag found")
            recommendations.append("Add H1 tag with target keyword")
        elif h1_count > 1:
            issues.append(f"Multiple H1 tags ({h1_count})")
            recommendations.append("Use only one H1 tag per page")

        if not has_keyword_in_h1:
            issues.append("Target keyword not in H1")
            recommendations.append(f"Add '{keyword}' to H1 tag")

        if h2_count == 0:
            issues.append("No H2 tags found")
            recommendations.append("Add H2 subheadings for content structure")

        return HeaderStructure(
            h1_count=h1_count,
            h1_text=h1_tags,
            h2_count=h2_count,
            h3_count=h3_count,
            has_keyword_in_h1=has_keyword_in_h1,
            hierarchy_valid=hierarchy_valid,
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_content(
        self,
        html: str,
        keyword: str,
    ) -> ContentAnalysis:
        """Analyze content quality."""
        # Extract text content (simplified)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        words = text.split()
        word_count = len(words)

        # Count keyword occurrences
        keyword_count = text.lower().count(keyword.lower())
        keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

        # Count paragraphs (simplified)
        paragraphs = re.findall(r"<p>(.*?)</p>", html, re.IGNORECASE)
        paragraph_count = len(paragraphs)
        avg_paragraph_length = (
            sum(len(p.split()) for p in paragraphs) / paragraph_count
            if paragraph_count > 0
            else 0
        )

        # Check for lists and images
        has_lists = bool(re.search(r"<ul>|<ol>", html, re.IGNORECASE))
        has_images = bool(re.search(r"<img", html, re.IGNORECASE))

        # Readability score (simplified Flesch Reading Ease)
        readability_score = 100 - (word_count / 100)  # Mock calculation

        # Identify issues
        issues = []
        recommendations = []

        if word_count < 300:
            issues.append(f"Content too short ({word_count} words)")
            recommendations.append("Expand content to at least 500 words")

        if keyword_density < 0.5:
            issues.append(f"Low keyword density ({keyword_density:.1f}%)")
            recommendations.append(f"Increase '{keyword}' usage to 1-2%")
        elif keyword_density > 3:
            issues.append(f"High keyword density ({keyword_density:.1f}%)")
            recommendations.append("Reduce keyword stuffing, aim for 1-2%")

        if not has_lists:
            issues.append("No lists found")
            recommendations.append("Add bullet points or numbered lists")

        if not has_images:
            issues.append("No images found")
            recommendations.append("Add relevant images with alt text")

        return ContentAnalysis(
            word_count=word_count,
            keyword_density=round(keyword_density, 2),
            keyword_count=keyword_count,
            readability_score=round(readability_score, 1),
            paragraph_count=paragraph_count,
            avg_paragraph_length=round(avg_paragraph_length, 1),
            has_lists=has_lists,
            has_images=has_images,
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_internal_linking(self, html: str) -> InternalLinking:
        """Analyze internal linking."""
        # Extract all links
        links = re.findall(r'<a\s+href="(.*?)"', html, re.IGNORECASE)

        total_links = len(links)
        internal_links = sum(1 for link in links if not link.startswith("http"))
        external_links = total_links - internal_links
        broken_links = 0  # Would need to check each link

        # Check anchor text optimization (simplified)
        anchor_texts = re.findall(r"<a[^>]*>(.*?)</a>", html, re.IGNORECASE)
        generic_anchors = ["click here", "read more", "here", "link"]
        anchor_text_optimized = not any(
            anchor.lower() in generic_anchors for anchor in anchor_texts
        )

        link_depth = 2  # Mock value (would calculate from homepage)

        # Identify issues
        issues = []
        recommendations = []

        if internal_links < 3:
            issues.append(f"Few internal links ({internal_links})")
            recommendations.append("Add more internal links to related pages")

        if not anchor_text_optimized:
            issues.append("Generic anchor text found")
            recommendations.append("Use descriptive anchor text with keywords")

        if link_depth > 3:
            issues.append(f"Deep link depth ({link_depth} clicks)")
            recommendations.append("Reduce clicks from homepage to 3 or less")

        return InternalLinking(
            total_links=total_links,
            internal_links=internal_links,
            external_links=external_links,
            broken_links=broken_links,
            anchor_text_optimized=anchor_text_optimized,
            link_depth=link_depth,
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_images(self, html: str) -> ImageOptimization:
        """Analyze image optimization."""
        # Extract images
        images = re.findall(r"<img[^>]*>", html, re.IGNORECASE)
        total_images = len(images)

        # Count images with alt text
        images_with_alt = sum(1 for img in images if 'alt="' in img)
        images_without_alt = total_images - images_with_alt

        # Check alt text quality (simplified)
        alt_texts = re.findall(r'alt="(.*?)"', html, re.IGNORECASE)
        descriptive_alts = sum(1 for alt in alt_texts if len(alt.split()) >= 3)
        alt_text_quality = (
            (descriptive_alts / len(alt_texts) * 100) if alt_texts else 0
        )

        # Mock values for file size and format
        large_images = 1  # Would need to check actual file sizes
        webp_usage = 0.0  # Would need to check image formats

        # Identify issues
        issues = []
        recommendations = []

        if images_without_alt > 0:
            issues.append(f"{images_without_alt} images without alt text")
            recommendations.append("Add descriptive alt text to all images")

        if alt_text_quality < 50:
            issues.append("Poor alt text quality")
            recommendations.append("Use descriptive alt text (3+ words)")

        if large_images > 0:
            issues.append(f"{large_images} large images (>100KB)")
            recommendations.append("Compress images to reduce file size")

        if webp_usage < 50:
            issues.append("Low WebP usage")
            recommendations.append("Convert images to WebP format")

        return ImageOptimization(
            total_images=total_images,
            images_with_alt=images_with_alt,
            images_without_alt=images_without_alt,
            alt_text_quality=round(alt_text_quality, 1),
            large_images=large_images,
            webp_usage=round(webp_usage, 1),
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_url(self, url: str, keyword: str) -> URLAnalysis:
        """Analyze URL structure."""
        length = len(url)
        has_keyword = keyword.lower().replace(" ", "-") in url.lower()

        # Check readability (no special chars except - and /)
        is_readable = not bool(re.search(r"[^a-zA-Z0-9\-/:]", url))

        has_special_chars = bool(re.search(r"[?&=]", url))

        # Count depth (number of slashes after domain)
        depth = url.count("/") - 2  # Subtract protocol slashes

        # Identify issues
        issues = []
        recommendations = []

        if length > 100:
            issues.append(f"URL too long ({length} chars)")
            recommendations.append("Shorten URL to under 100 characters")

        if not has_keyword:
            issues.append("Target keyword not in URL")
            recommendations.append(f"Add '{keyword}' to URL slug")

        if not is_readable:
            issues.append("URL contains special characters")
            recommendations.append("Use only letters, numbers, and hyphens")

        if has_special_chars:
            issues.append("URL has query parameters")
            recommendations.append("Use clean URLs without parameters")

        if depth > 3:
            issues.append(f"URL too deep ({depth} levels)")
            recommendations.append("Reduce URL depth to 3 levels or less")

        return URLAnalysis(
            url=url,
            length=length,
            has_keyword=has_keyword,
            is_readable=is_readable,
            has_special_chars=has_special_chars,
            depth=depth,
            issues=issues,
            recommendations=recommendations,
        )

    def _calculate_overall_score(
        self,
        title: TitleTagAnalysis,
        meta: MetaDescriptionAnalysis,
        headers: HeaderStructure,
        content: ContentAnalysis,
        linking: InternalLinking,
        images: ImageOptimization,
        url: URLAnalysis,
    ) -> float:
        """Calculate overall on-page SEO score."""
        score = 100.0

        # Title tag (20 points)
        if not title.has_keyword:
            score -= 10
        if not title.is_optimal_length:
            score -= 5
        if title.keyword_position > 3:
            score -= 5

        # Meta description (15 points)
        if not meta.has_keyword:
            score -= 7
        if not meta.has_cta:
            score -= 5
        if not meta.is_optimal_length:
            score -= 3

        # Headers (20 points)
        if headers.h1_count != 1:
            score -= 10
        if not headers.has_keyword_in_h1:
            score -= 7
        if headers.h2_count == 0:
            score -= 3

        # Content (25 points)
        if content.word_count < 300:
            score -= 10
        if content.keyword_density < 0.5 or content.keyword_density > 3:
            score -= 8
        if not content.has_lists:
            score -= 4
        if not content.has_images:
            score -= 3

        # Internal linking (10 points)
        if linking.internal_links < 3:
            score -= 5
        if not linking.anchor_text_optimized:
            score -= 5

        # Images (5 points)
        if images.images_without_alt > 0:
            score -= 3
        if images.alt_text_quality < 50:
            score -= 2

        # URL (5 points)
        if not url.has_keyword:
            score -= 3
        if not url.is_readable:
            score -= 2

        return max(0, score)

    def _identify_priority_issues(
        self,
        title: TitleTagAnalysis,
        meta: MetaDescriptionAnalysis,
        headers: HeaderStructure,
        content: ContentAnalysis,
    ) -> list[str]:
        """Identify priority issues to fix."""
        priority = []

        # Critical issues
        if not title.has_keyword:
            priority.append("🔴 CRITICAL: Add target keyword to title tag")
        if headers.h1_count != 1:
            priority.append("🔴 CRITICAL: Fix H1 tag (should be exactly one)")
        if not headers.has_keyword_in_h1:
            priority.append("🔴 CRITICAL: Add target keyword to H1")

        # High priority
        if not meta.has_keyword:
            priority.append("🟡 HIGH: Add target keyword to meta description")
        if content.word_count < 300:
            priority.append("🟡 HIGH: Expand content to at least 500 words")
        if content.keyword_density < 0.5:
            priority.append("🟡 HIGH: Increase keyword density to 1-2%")

        return priority[:5]  # Top 5 issues

    def _identify_quick_wins(
        self,
        title: TitleTagAnalysis,
        meta: MetaDescriptionAnalysis,
        images: ImageOptimization,
    ) -> list[str]:
        """Identify quick wins (easy fixes with high impact)."""
        quick_wins = []

        if not meta.has_cta:
            quick_wins.append("Add CTA to meta description (2 min)")
        if images.images_without_alt > 0:
            quick_wins.append(f"Add alt text to {images.images_without_alt} images (5 min)")
        if title.length < 50:
            quick_wins.append("Expand title tag to optimal length (2 min)")

        return quick_wins[:3]  # Top 3 quick wins


async def main():
    """Example usage."""
    optimizer = OnPageOptimizer()

    report = await optimizer.analyze(
        url="https://example.com/dental-implants-moscow",
        target_keyword="dental implants",
    )

    print(f"On-Page SEO Report: {report.url}")
    print(f"Overall Score: {report.overall_score}/100")
    print()

    print("Priority Issues:")
    for issue in report.priority_issues:
        print(f"  {issue}")

    print()
    print("Quick Wins:")
    for win in report.quick_wins:
        print(f"  ✅ {win}")


if __name__ == "__main__":
    asyncio.run(main())
