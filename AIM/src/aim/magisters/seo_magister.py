"""SEO Magister - Coordinates SEO Analysis Workflow

Orchestrates Technical, Content, and Links SEO agents to perform
comprehensive website SEO analysis.

Part of: Superflow Vertical Slice - SEO Analysis Workflow
Sprint: 4 (Operator Coordination)
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from src.aim.subagents.seo.technical_agent import TechnicalSEOAgent
from src.aim.subagents.seo.content_agent import ContentSEOAgent
from src.aim.subagents.seo.links_agent import LinksSEOAgent


class SEOMagister:
    """SEO Magister - Coordinates comprehensive SEO analysis

    Orchestrates three specialized agents:
    - Technical SEO Agent (40% weight)
    - Content SEO Agent (30% weight)
    - Links SEO Agent (30% weight)

    Aggregates results using weighted scoring and generates
    actionable recommendations.
    """

    def __init__(
        self,
        timeout: int = 600,
        technical_agent: TechnicalSEOAgent | None = None,
        content_agent: ContentSEOAgent | None = None,
        links_agent: LinksSEOAgent | None = None,
        event_bus=None,
    ):
        """Initialize SEO Magister

        Args:
            timeout: Maximum time for analysis in seconds (default: 10 minutes)
            technical_agent: Optional TechnicalSEOAgent instance (for testing)
            content_agent: Optional ContentSEOAgent instance (for testing)
            links_agent: Optional LinksSEOAgent instance (for testing)
            event_bus: Optional EventBus instance for publishing results
        """
        self.technical_agent = technical_agent or TechnicalSEOAgent()
        self.content_agent = content_agent or ContentSEOAgent()
        self.links_agent = links_agent or LinksSEOAgent()
        self.timeout = timeout
        self.event_bus = event_bus

    async def coordinate_analysis(self, url: str, correlation_id: str | None = None) -> dict[str, Any]:
        """Coordinate comprehensive SEO analysis

        Dispatches three agents in parallel, aggregates results,
        calculates weighted scores, and generates recommendations.

        Args:
            url: Website URL to analyze
            correlation_id: Optional correlation ID for tracking

        Returns:
            Comprehensive SEO analysis report with scores and recommendations
        """
        if correlation_id is None:
            correlation_id = f"seo-analysis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        start_time = datetime.now(timezone.utc)

        try:
            # Dispatch all three agents in parallel
            technical_result, content_result, links_result = await self._dispatch_subagents(
                url, correlation_id
            )

            # Aggregate results
            report = await self._aggregate_results(
                url=url,
                correlation_id=correlation_id,
                technical_result=technical_result,
                content_result=content_result,
                links_result=links_result,
                start_time=start_time
            )

            # Publish completion event if EventBus is available
            if self.event_bus is not None:
                try:
                    from meai.events.event_bus import Event

                    await self.event_bus.publish(Event(
                        event_type="seo.analysis.completed",
                        payload={
                            "url": url,
                            "correlation_id": correlation_id,
                            "overall_score": report.get("scores", {}).get("overall"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    ))
                except Exception:
                    pass

            return report

        except asyncio.TimeoutError:
            return {
                "url": url,
                "correlation_id": correlation_id,
                "status": "error",
                "error": f"Analysis timeout after {self.timeout} seconds",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "url": url,
                "correlation_id": correlation_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _dispatch_subagents(
        self, url: str, correlation_id: str
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Dispatch three SEO agents in parallel

        Args:
            url: Website URL to analyze
            correlation_id: Correlation ID for tracking

        Returns:
            Tuple of (technical_result, content_result, links_result)

        Raises:
            asyncio.TimeoutError: If analysis exceeds timeout
        """
        # Execute all three agents in parallel with timeout
        technical_result, content_result, links_result = await asyncio.wait_for(
            asyncio.gather(
                self.technical_agent.analyze(url, correlation_id),
                self.content_agent.analyze(url, correlation_id),
                self.links_agent.analyze(url, correlation_id),
                return_exceptions=True
            ),
            timeout=self.timeout
        )

        # Handle exceptions from individual agents
        if isinstance(technical_result, Exception):
            technical_result = {
                "agent": "technical-agent",
                "status": "error",
                "error": str(technical_result)
            }

        if isinstance(content_result, Exception):
            content_result = {
                "agent": "content-agent",
                "status": "error",
                "error": str(content_result)
            }

        if isinstance(links_result, Exception):
            links_result = {
                "agent": "links-agent",
                "status": "error",
                "error": str(links_result)
            }

        return technical_result, content_result, links_result

    async def _aggregate_results(
        self,
        url: str,
        correlation_id: str,
        technical_result: dict[str, Any],
        content_result: dict[str, Any],
        links_result: dict[str, Any],
        start_time: datetime
    ) -> dict[str, Any]:
        """Aggregate results from three agents

        Calculates weighted scores (40% technical, 30% content, 30% links),
        generates recommendations, and creates comprehensive report.

        Args:
            url: Website URL
            correlation_id: Correlation ID
            technical_result: Technical agent result
            content_result: Content agent result
            links_result: Links agent result
            start_time: Analysis start time

        Returns:
            Comprehensive SEO analysis report
        """
        # Calculate individual scores
        technical_score = self._calculate_technical_score(technical_result)
        content_score = self._calculate_content_score(content_result)
        links_score = self._calculate_links_score(links_result)

        # Calculate weighted overall score (40% tech, 30% content, 30% links)
        overall_score = (
            technical_score * 0.4 +
            content_score * 0.3 +
            links_score * 0.3
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            technical_result, content_result, links_result,
            technical_score, content_score, links_score
        )

        # Generate summary
        summary = self._generate_summary(
            overall_score, technical_score, content_score, links_score
        )

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        return {
            "url": url,
            "correlation_id": correlation_id,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "scores": {
                "overall": round(overall_score, 1),
                "technical": round(technical_score, 1),
                "content": round(content_score, 1),
                "links": round(links_score, 1)
            },
            "summary": summary,
            "recommendations": recommendations,
            "details": {
                "technical": technical_result,
                "content": content_result,
                "links": links_result
            }
        }

    def _calculate_technical_score(self, technical_result: dict[str, Any]) -> float:
        """Calculate technical SEO score (0-100)

        Scoring breakdown:
        - robots.txt: 15 points (exists + allows crawling)
        - sitemap.xml: 15 points (exists + valid)
        - meta tags: 20 points (title + description quality)
        - performance: 30 points (PageSpeed score)
        - schema.org: 20 points (structured data present)

        Args:
            technical_result: Technical agent result

        Returns:
            Score from 0 to 100
        """
        if technical_result.get("status") != "success":
            return 0.0

        results = technical_result.get("results", {})
        score = 0.0

        # robots.txt (15 points)
        robots = results.get("robots_txt", {})
        if robots.get("exists"):
            score += 10
            if robots.get("allows_crawling"):
                score += 5

        # sitemap.xml (15 points)
        sitemap = results.get("sitemap_xml", {})
        if sitemap.get("exists"):
            score += 10
            if sitemap.get("valid"):
                score += 5

        # meta tags (20 points)
        meta = results.get("meta_tags", {})
        if meta.get("title"):
            title_len = len(meta["title"])
            if 30 <= title_len <= 60:
                score += 10
            elif title_len > 0:
                score += 5

        if meta.get("description"):
            desc_len = len(meta["description"])
            if 120 <= desc_len <= 160:
                score += 10
            elif desc_len > 0:
                score += 5

        # performance (30 points)
        perf = results.get("performance", {})
        if "score" in perf:
            # PageSpeed score is 0-100, map to 0-30
            score += (perf["score"] / 100) * 30

        # schema.org (20 points)
        schema = results.get("schema_org", {})
        schema_count = schema.get("count", 0)
        if schema_count > 0:
            score += min(schema_count * 5, 20)  # 5 points per schema, max 20

        return min(score, 100.0)

    def _calculate_content_score(self, content_result: dict[str, Any]) -> float:
        """Calculate content SEO score (0-100)

        Scoring breakdown:
        - headers: 25 points (H1 present, hierarchy valid)
        - readability: 25 points (Flesch Reading Ease 60-80)
        - content quality: 30 points (word count, images, alt text)
        - structure: 20 points (semantic HTML5)

        Args:
            content_result: Content agent result

        Returns:
            Score from 0 to 100
        """
        if content_result.get("status") != "success":
            return 0.0

        results = content_result.get("results", {})
        score = 0.0

        # headers (25 points)
        headers = results.get("headers", {})
        if headers.get("h1_count") == 1:
            score += 15
        elif headers.get("h1_count", 0) > 0:
            score += 5

        if not headers.get("broken_hierarchy"):
            score += 10

        # readability (25 points)
        readability = results.get("readability", {})
        flesch = readability.get("flesch_reading_ease", 0)
        if 60 <= flesch <= 80:
            score += 25
        elif 50 <= flesch < 60 or 80 < flesch <= 90:
            score += 15
        elif flesch > 0:
            score += 5

        # content quality (30 points)
        quality = results.get("content_quality", {})

        # word count (10 points)
        word_count = quality.get("word_count", 0)
        if word_count >= 1000:
            score += 10
        elif word_count >= 500:
            score += 7
        elif word_count >= 300:
            score += 5
        elif word_count > 0:
            score += 2

        # images (10 points)
        image_count = quality.get("image_count", 0)
        if image_count >= 3:
            score += 5
        elif image_count > 0:
            score += 3

        # alt text (10 points)
        alt_coverage = quality.get("alt_text_coverage", 0)
        if alt_coverage >= 90:
            score += 10
        elif alt_coverage >= 70:
            score += 7
        elif alt_coverage >= 50:
            score += 5
        elif alt_coverage > 0:
            score += 2

        # structure (20 points)
        structure = results.get("structure", {})
        semantic_score = structure.get("semantic_score", 0)
        score += (semantic_score / 100) * 20

        return min(score, 100.0)

    def _calculate_links_score(self, links_result: dict[str, Any]) -> float:
        """Calculate links SEO score (0-100)

        Scoring breakdown:
        - internal links: 30 points (presence, distribution)
        - external links: 25 points (quality, nofollow ratio)
        - anchor text: 25 points (descriptive, not generic)
        - broken links: 20 points (no broken links)

        Args:
            links_result: Links agent result

        Returns:
            Score from 0 to 100
        """
        if links_result.get("status") != "success":
            return 0.0

        results = links_result.get("results", {})
        score = 0.0

        # internal links (30 points)
        internal = results.get("internal_links", {})
        internal_count = internal.get("total", 0)
        if internal_count >= 20:
            score += 20
        elif internal_count >= 10:
            score += 15
        elif internal_count >= 5:
            score += 10
        elif internal_count > 0:
            score += 5

        unique_internal = internal.get("unique", 0)
        if unique_internal >= 10:
            score += 10
        elif unique_internal >= 5:
            score += 7
        elif unique_internal > 0:
            score += 3

        # external links (25 points)
        external = results.get("external_links", {})
        external_count = external.get("total", 0)
        if external_count >= 5:
            score += 10
        elif external_count > 0:
            score += 5

        nofollow_pct = external.get("nofollow_percentage", 0)
        if 20 <= nofollow_pct <= 40:
            score += 15
        elif 10 <= nofollow_pct < 20 or 40 < nofollow_pct <= 60:
            score += 10
        elif nofollow_pct > 0:
            score += 5

        # anchor text (25 points)
        anchor = results.get("anchor_text", {})
        empty_pct = anchor.get("empty_percentage", 0)
        if empty_pct == 0:
            score += 10
        elif empty_pct < 5:
            score += 7
        elif empty_pct < 10:
            score += 5

        generic_pct = anchor.get("generic_percentage", 0)
        if generic_pct < 10:
            score += 15
        elif generic_pct < 20:
            score += 10
        elif generic_pct < 30:
            score += 5

        # broken links (20 points)
        broken = results.get("broken_links", {})
        broken_pct = broken.get("broken_percentage", 0)
        if broken_pct == 0:
            score += 20
        elif broken_pct < 5:
            score += 15
        elif broken_pct < 10:
            score += 10
        elif broken_pct < 20:
            score += 5

        return min(score, 100.0)

    def _generate_recommendations(
        self,
        technical_result: dict[str, Any],
        content_result: dict[str, Any],
        links_result: dict[str, Any],
        technical_score: float,
        content_score: float,
        links_score: float
    ) -> list[dict[str, str]]:
        """Generate actionable recommendations

        Args:
            technical_result: Technical agent result
            content_result: Content agent result
            links_result: Links agent result
            technical_score: Technical score
            content_score: Content score
            links_score: Links score

        Returns:
            List of recommendations with priority and category
        """
        recommendations = []

        # Technical recommendations
        if technical_score < 70:
            tech_results = technical_result.get("results", {})

            if not tech_results.get("robots_txt", {}).get("exists"):
                recommendations.append({
                    "priority": "high",
                    "category": "technical",
                    "issue": "Missing robots.txt",
                    "action": "Create robots.txt file to guide search engine crawlers"
                })

            if not tech_results.get("sitemap_xml", {}).get("exists"):
                recommendations.append({
                    "priority": "high",
                    "category": "technical",
                    "issue": "Missing sitemap.xml",
                    "action": "Generate and submit XML sitemap to search engines"
                })

            perf = tech_results.get("performance", {})
            if perf.get("score", 100) < 50:
                recommendations.append({
                    "priority": "high",
                    "category": "technical",
                    "issue": f"Poor performance score ({perf.get('score', 0)})",
                    "action": "Optimize images, enable caching, minify CSS/JS"
                })

            if tech_results.get("schema_org", {}).get("count", 0) == 0:
                recommendations.append({
                    "priority": "medium",
                    "category": "technical",
                    "issue": "No structured data",
                    "action": "Add Schema.org markup for better search visibility"
                })

        # Content recommendations
        if content_score < 70:
            content_results = content_result.get("results", {})

            headers = content_results.get("headers", {})
            if headers.get("h1_count", 0) != 1:
                recommendations.append({
                    "priority": "high",
                    "category": "content",
                    "issue": f"Invalid H1 count ({headers.get('h1_count', 0)})",
                    "action": "Use exactly one H1 tag per page"
                })

            quality = content_results.get("content_quality", {})
            if quality.get("word_count", 0) < 300:
                recommendations.append({
                    "priority": "high",
                    "category": "content",
                    "issue": f"Thin content ({quality.get('word_count', 0)} words)",
                    "action": "Expand content to at least 500-1000 words"
                })

            if quality.get("alt_text_coverage", 0) < 80:
                recommendations.append({
                    "priority": "medium",
                    "category": "content",
                    "issue": f"Low alt text coverage ({quality.get('alt_text_coverage', 0)}%)",
                    "action": "Add descriptive alt text to all images"
                })

            readability = content_results.get("readability", {})
            flesch = readability.get("flesch_reading_ease", 0)
            if flesch < 50:
                recommendations.append({
                    "priority": "medium",
                    "category": "content",
                    "issue": f"Difficult to read (Flesch: {flesch})",
                    "action": "Simplify language, use shorter sentences"
                })

        # Links recommendations
        if links_score < 70:
            links_results = links_result.get("results", {})

            internal = links_results.get("internal_links", {})
            if internal.get("total", 0) < 10:
                recommendations.append({
                    "priority": "high",
                    "category": "links",
                    "issue": f"Few internal links ({internal.get('total', 0)})",
                    "action": "Add more internal links to improve site structure"
                })

            anchor = links_results.get("anchor_text", {})
            if anchor.get("generic_percentage", 0) > 20:
                recommendations.append({
                    "priority": "medium",
                    "category": "links",
                    "issue": f"Too many generic anchors ({anchor.get('generic_percentage', 0)}%)",
                    "action": "Use descriptive anchor text instead of 'click here'"
                })

            broken = links_results.get("broken_links", {})
            if broken.get("broken_count", 0) > 0:
                recommendations.append({
                    "priority": "high",
                    "category": "links",
                    "issue": f"{broken.get('broken_count', 0)} broken links found",
                    "action": "Fix or remove broken links"
                })

        # Sort by priority (high > medium > low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return recommendations

    def _generate_summary(
        self,
        overall_score: float,
        technical_score: float,
        content_score: float,
        links_score: float
    ) -> str:
        """Generate human-readable summary

        Args:
            overall_score: Overall SEO score
            technical_score: Technical score
            content_score: Content score
            links_score: Links score

        Returns:
            Summary text
        """
        # Determine overall rating
        if overall_score >= 80:
            rating = "Excellent"
        elif overall_score >= 60:
            rating = "Good"
        elif overall_score >= 40:
            rating = "Fair"
        else:
            rating = "Poor"

        # Find strongest and weakest areas
        scores = {
            "technical": technical_score,
            "content": content_score,
            "links": links_score
        }
        strongest = max(scores.items(), key=lambda x: x[1])
        weakest = min(scores.items(), key=lambda x: x[1])

        summary = f"{rating} SEO health (score: {overall_score:.1f}/100). "
        summary += f"Strongest area: {strongest[0]} ({strongest[1]:.1f}). "
        summary += f"Needs improvement: {weakest[0]} ({weakest[1]:.1f})."

        return summary
