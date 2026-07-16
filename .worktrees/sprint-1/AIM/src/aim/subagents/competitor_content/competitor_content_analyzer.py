"""
Competitor Content Analyzer - Main Orchestrator.

Integrates all analysis components: keyword, E-E-A-T, content structure, AI detection, technical SEO.
"""

from datetime import datetime
from typing import Optional

from AIM.src.aim.subagents.competitor_content.content_structure_analyzer import (
    ContentStructureAnalyzer,
)
from AIM.src.aim.subagents.competitor_content.eeat_scorer import EEATScorer
from AIM.src.aim.subagents.competitor_content.keyword_analyzer import KeywordAnalyzer
from AIM.src.aim.subagents.competitor_content.technical_seo_analyzer import (
    TechnicalSEOAnalyzer,
)
from AIM.src.aim.subagents.utils.ai_content_detector import AIContentDetector
from AIM.src.aim.subagents.utils.text_extractor import TextExtractor


class CompetitorContentAnalyzer:
    """
    Main orchestrator for competitor content analysis.

    Integrates:
    - Keyword analysis (density, placement, LSI)
    - E-E-A-T scoring (medical YMYL compliance)
    - Content structure analysis (readability, quality)
    - AI content detection
    - Technical SEO analysis (Core Web Vitals, mobile, speed, schema)

    Provides comprehensive competitor analysis with actionable recommendations.
    """

    def __init__(
        self,
        target_market: str = "russia",
        min_word_count: int = 300,
        freshness_months: int = 12,
    ):
        """
        Initialize Competitor Content Analyzer.

        Args:
            target_market: Target market ("russia" or "global")
            min_word_count: Minimum word count for quality content
            freshness_months: Content freshness requirement in months
        """
        self.target_market = target_market
        self.min_word_count = min_word_count
        self.freshness_months = freshness_months

        # Initialize components
        self.text_extractor = TextExtractor()
        self.keyword_analyzer = KeywordAnalyzer()
        self.eeat_scorer = EEATScorer(
            min_word_count=min_word_count, freshness_months=freshness_months
        )
        self.content_structure_analyzer = ContentStructureAnalyzer(
            min_word_count=min_word_count
        )
        self.ai_detector = AIContentDetector()
        self.technical_seo_analyzer = TechnicalSEOAnalyzer()

    def analyze(
        self,
        html: str,
        url: str,
        keywords: list[str],
        updated_date: Optional[datetime] = None,
        core_web_vitals: Optional[dict] = None,
    ) -> dict:
        """
        Perform comprehensive competitor content analysis.

        Args:
            html: Raw HTML content
            url: Page URL
            keywords: List of target keywords to analyze
            updated_date: Optional last updated date for freshness scoring
            core_web_vitals: Optional Core Web Vitals metrics (LCP, INP, CLS)

        Returns:
            Dictionary with complete analysis results
        """
        # Extract text and metadata
        extracted = self.text_extractor.extract_content(html, url)
        text = extracted["text"]
        soup = extracted["soup"]
        meta_tags = self.text_extractor.extract_meta_tags(soup)

        # 1. Keyword Analysis
        keyword_analysis = {
            "keywords": {},
            "lsi_keywords": [],
            "market_optimization": {},
        }

        # Count total words
        total_words = len(text.split()) if text else 0

        # Extract title and headings for placement analysis
        title = meta_tags.get("title", "")
        headings = self.text_extractor.extract_headings(soup)

        for keyword in keywords:
            # Density analysis
            density = self.keyword_analyzer.analyze_keyword_density(
                text=text, target_keyword=keyword, total_words=total_words
            )

            # Placement analysis
            placement = self.keyword_analyzer.analyze_keyword_placement(
                target_keyword=keyword, title=title, headings=headings, text=text
            )

            keyword_analysis["keywords"][keyword] = {
                **density,
                **placement,
            }

        # LSI keywords (for first keyword)
        if keywords:
            # Get keyword density data for LSI extraction
            keyword_density_data = self.text_extractor.calculate_keyword_density(text)
            keyword_analysis["lsi_keywords"] = self.keyword_analyzer.extract_lsi_keywords(
                keywords=keyword_density_data.get("keywords", {}),
                target_keyword=keywords[0],
                min_count=2,
            )

        # Market optimization (use first keyword's data)
        if keywords and keyword_analysis["keywords"]:
            first_keyword_data = keyword_analysis["keywords"][keywords[0]]
            keyword_analysis["market_optimization"] = self.keyword_analyzer.analyze_market_optimization(
                density_analysis=first_keyword_data,
                placement_analysis=first_keyword_data,
                lsi_keywords=keyword_analysis["lsi_keywords"],
                total_words=total_words,
            )
        else:
            keyword_analysis["market_optimization"] = {}

        # 2. E-E-A-T Scoring (Medical YMYL)
        eeat_score = self.eeat_scorer.score(
            html=html, text=text, url=url, updated_date=updated_date
        )

        # 3. Content Structure Analysis
        content_structure = self.content_structure_analyzer.analyze(html=html, text=text)

        # 4. AI Content Detection
        ai_detection = self.ai_detector.detect(text)

        # 5. Technical SEO Analysis
        technical_seo = self.technical_seo_analyzer.analyze(
            html=html, url=url, metrics=core_web_vitals
        )

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            keyword_analysis=keyword_analysis,
            eeat_score=eeat_score,
            content_structure=content_structure,
            ai_detection=ai_detection,
            technical_seo=technical_seo,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            keyword_analysis=keyword_analysis,
            eeat_score=eeat_score,
            content_structure=content_structure,
            ai_detection=ai_detection,
            technical_seo=technical_seo,
        )

        # Priority actions (top 5 most critical)
        priority_actions = self._get_priority_actions(recommendations)

        return {
            "url": url,
            "analyzed_at": datetime.now().isoformat(),
            "target_market": self.target_market,
            "meta_tags": meta_tags,
            "keyword_analysis": keyword_analysis,
            "eeat_score": eeat_score,
            "content_structure": content_structure,
            "ai_detection": ai_detection,
            "technical_seo": technical_seo,
            "overall_score": round(overall_score, 2),
            "overall_level": self._get_overall_level(overall_score),
            "recommendations": recommendations,
            "priority_actions": priority_actions,
        }

    def compare(
        self,
        competitor_html: str,
        competitor_url: str,
        client_html: str,
        client_url: str,
        keywords: list[str],
        competitor_updated: Optional[datetime] = None,
        client_updated: Optional[datetime] = None,
        competitor_cwv: Optional[dict] = None,
        client_cwv: Optional[dict] = None,
    ) -> dict:
        """
        Compare competitor and client content.

        Args:
            competitor_html: Competitor HTML
            competitor_url: Competitor URL
            client_html: Client HTML
            client_url: Client URL
            keywords: Target keywords
            competitor_updated: Competitor last updated date
            client_updated: Client last updated date
            competitor_cwv: Competitor Core Web Vitals
            client_cwv: Client Core Web Vitals

        Returns:
            Dictionary with comparison results and gap analysis
        """
        # Analyze both
        competitor_analysis = self.analyze(
            html=competitor_html,
            url=competitor_url,
            keywords=keywords,
            updated_date=competitor_updated,
            core_web_vitals=competitor_cwv,
        )

        client_analysis = self.analyze(
            html=client_html,
            url=client_url,
            keywords=keywords,
            updated_date=client_updated,
            core_web_vitals=client_cwv,
        )

        # Calculate gaps
        gaps = self._calculate_gaps(competitor_analysis, client_analysis)

        # Generate improvement actions
        improvement_actions = self._generate_improvement_actions(gaps)

        return {
            "competitor": competitor_analysis,
            "client": client_analysis,
            "gaps": gaps,
            "improvement_actions": improvement_actions,
            "comparison_summary": self._generate_comparison_summary(gaps),
        }

    def _calculate_overall_score(
        self,
        keyword_analysis: dict,
        eeat_score: dict,
        content_structure: dict,
        ai_detection: dict,
        technical_seo: dict,
    ) -> float:
        """
        Calculate overall content quality score.

        Weighted components:
        - Keyword optimization: 20%
        - E-E-A-T compliance: 25%
        - Content structure: 20%
        - AI detection (penalty): -10% if AI-generated
        - Technical SEO: 25%
        - Bonus: +10% if all components are excellent
        """
        score = 0.0

        # Keyword optimization (20%)
        keyword_score = 0.0
        for kw_data in keyword_analysis.get("keywords", {}).values():
            if kw_data.get("density_status") == "optimal":
                keyword_score += 5.0
            if kw_data.get("placement_score", 0) >= 80:
                keyword_score += 5.0
        keyword_score = min(keyword_score, 20.0)
        score += keyword_score

        # E-E-A-T compliance (25%)
        eeat_overall = eeat_score.get("overall_score", 0)
        score += eeat_overall * 0.25

        # Content structure (20%)
        structure_score = content_structure.get("quality_score", 0)
        score += structure_score * 0.20

        # AI detection penalty (-10% if AI-generated)
        if ai_detection.get("is_ai_generated", False):
            score -= 10.0

        # Technical SEO (25%)
        technical_score = technical_seo.get("technical_score", 0)
        score += technical_score * 0.25

        # Bonus for excellence (all components >= 80)
        if (
            eeat_overall >= 80
            and structure_score >= 80
            and technical_score >= 80
            and not ai_detection.get("is_ai_generated", False)
        ):
            score += 10.0

        return max(0.0, min(100.0, score))

    def _get_overall_level(self, score: float) -> str:
        """Get overall quality level."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"

    def _generate_recommendations(
        self,
        keyword_analysis: dict,
        eeat_score: dict,
        content_structure: dict,
        ai_detection: dict,
        technical_seo: dict,
    ) -> list[dict]:
        """
        Generate actionable recommendations.

        Returns list of recommendations with priority, category, and action.
        """
        recommendations = []

        # Keyword recommendations
        for keyword, data in keyword_analysis.get("keywords", {}).items():
            if data.get("density_status") != "optimal":
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "keyword_optimization",
                        "issue": f"Keyword '{keyword}' density not optimal",
                        "current": f"{data.get('density_percent', 0):.2f}%",
                        "target": f"{data.get('optimal_range', (0, 0))[0]}-{data.get('optimal_range', (0, 0))[1]}%",
                        "action": f"Adjust keyword density to {data.get('optimal_range', (0, 0))[0]}-{data.get('optimal_range', (0, 0))[1]}%",
                    }
                )

        # E-E-A-T recommendations
        for rec in eeat_score.get("recommendations", []):
            recommendations.append(
                {
                    "priority": "critical" if "author credentials" in rec.lower() else "high",
                    "category": "eeat_compliance",
                    "issue": rec,
                    "action": rec,
                }
            )

        # Content structure recommendations
        structure_score = content_structure.get("quality_score", 0)
        if structure_score < 60:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "content_quality",
                    "issue": f"Content quality score low ({structure_score:.0f}/100)",
                    "action": "Improve readability, heading hierarchy, and visual elements",
                }
            )

        # AI detection warning
        if ai_detection.get("is_ai_generated", False):
            recommendations.append(
                {
                    "priority": "critical",
                    "category": "content_authenticity",
                    "issue": f"Content appears AI-generated ({ai_detection.get('confidence', 0):.0f}% confidence)",
                    "action": "Add human expertise, personal experience, and unique insights",
                }
            )

        # Technical SEO recommendations
        technical_score = technical_seo.get("technical_score", 0)
        if technical_score < 60:
            if not technical_seo.get("mobile_optimization", {}).get("mobile_friendly", False):
                recommendations.append(
                    {
                        "priority": "critical",
                        "category": "technical_seo",
                        "issue": "Not mobile-friendly",
                        "action": "Add viewport meta tag and responsive design",
                    }
                )

            if not technical_seo.get("security", {}).get("is_https", False):
                recommendations.append(
                    {
                        "priority": "critical",
                        "category": "technical_seo",
                        "issue": "Not using HTTPS",
                        "action": "Migrate to HTTPS immediately",
                    }
                )

            if not technical_seo.get("schema_markup", {}).get("has_structured_data", False):
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "technical_seo",
                        "issue": "No structured data (schema markup)",
                        "action": "Add JSON-LD schema markup (MedicalOrganization, Article)",
                    }
                )

        return recommendations

    def _get_priority_actions(self, recommendations: list[dict]) -> list[dict]:
        """Get top 5 priority actions."""
        # Sort by priority: critical > high > medium > low
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_recs = sorted(
            recommendations, key=lambda x: priority_order.get(x.get("priority", "low"), 3)
        )
        return sorted_recs[:5]

    def _calculate_gaps(self, competitor: dict, client: dict) -> dict:
        """Calculate gaps between competitor and client."""
        return {
            "overall_score_gap": competitor["overall_score"] - client["overall_score"],
            "eeat_gap": competitor["eeat_score"]["overall_score"]
            - client["eeat_score"]["overall_score"],
            "content_quality_gap": competitor["content_structure"]["quality_score"]
            - client["content_structure"]["quality_score"],
            "technical_seo_gap": competitor["technical_seo"]["technical_score"]
            - client["technical_seo"]["technical_score"],
            "keyword_gaps": self._calculate_keyword_gaps(
                competitor["keyword_analysis"], client["keyword_analysis"]
            ),
        }

    def _calculate_keyword_gaps(
        self, competitor_keywords: dict, client_keywords: dict
    ) -> list[dict]:
        """Calculate keyword-specific gaps."""
        gaps = []
        for keyword in competitor_keywords.get("keywords", {}).keys():
            comp_data = competitor_keywords["keywords"].get(keyword, {})
            client_data = client_keywords.get("keywords", {}).get(keyword, {})

            if comp_data and client_data:
                density_gap = comp_data.get("density_percent", 0) - client_data.get(
                    "density_percent", 0
                )
                placement_gap = comp_data.get("placement_score", 0) - client_data.get(
                    "placement_score", 0
                )

                if abs(density_gap) > 0.5 or abs(placement_gap) > 10:
                    gaps.append(
                        {
                            "keyword": keyword,
                            "density_gap": round(density_gap, 2),
                            "placement_gap": round(placement_gap, 2),
                        }
                    )

        return gaps

    def _generate_improvement_actions(self, gaps: dict) -> list[dict]:
        """Generate improvement actions based on gaps."""
        actions = []

        # Overall score gap
        if gaps["overall_score_gap"] > 10:
            actions.append(
                {
                    "priority": "critical",
                    "category": "overall",
                    "gap": f"{gaps['overall_score_gap']:.1f} points",
                    "action": "Comprehensive content improvement needed across all areas",
                }
            )

        # E-E-A-T gap
        if gaps["eeat_gap"] > 15:
            actions.append(
                {
                    "priority": "critical",
                    "category": "eeat",
                    "gap": f"{gaps['eeat_gap']:.1f} points",
                    "action": "Add author credentials, citations, and medical expertise signals",
                }
            )

        # Content quality gap
        if gaps["content_quality_gap"] > 15:
            actions.append(
                {
                    "priority": "high",
                    "category": "content_quality",
                    "gap": f"{gaps['content_quality_gap']:.1f} points",
                    "action": "Improve readability, structure, and visual elements",
                }
            )

        # Technical SEO gap
        if gaps["technical_seo_gap"] > 15:
            actions.append(
                {
                    "priority": "high",
                    "category": "technical_seo",
                    "gap": f"{gaps['technical_seo_gap']:.1f} points",
                    "action": "Fix mobile optimization, page speed, and schema markup",
                }
            )

        # Keyword gaps
        for kw_gap in gaps.get("keyword_gaps", []):
            if abs(kw_gap["density_gap"]) > 1.0:
                actions.append(
                    {
                        "priority": "medium",
                        "category": "keyword",
                        "keyword": kw_gap["keyword"],
                        "gap": f"{kw_gap['density_gap']:.2f}% density",
                        "action": f"Adjust '{kw_gap['keyword']}' density",
                    }
                )

        return actions

    def _generate_comparison_summary(self, gaps: dict) -> str:
        """Generate human-readable comparison summary."""
        overall_gap = gaps["overall_score_gap"]

        if overall_gap > 20:
            verdict = "Competitor significantly outperforms client"
        elif overall_gap > 10:
            verdict = "Competitor moderately outperforms client"
        elif overall_gap > -10:
            verdict = "Client and competitor are comparable"
        elif overall_gap > -20:
            verdict = "Client moderately outperforms competitor"
        else:
            verdict = "Client significantly outperforms competitor"

        return f"{verdict} (gap: {overall_gap:.1f} points)"
