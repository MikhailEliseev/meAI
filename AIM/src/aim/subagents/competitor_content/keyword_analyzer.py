"""
Keyword analysis with market-specific optimization.

Analyzes keyword density, LSI keywords, and placement for Yandex and Google markets.
"""

from collections import Counter
from typing import Optional

from bs4 import BeautifulSoup


class KeywordAnalyzer:
    """
    Analyze keyword usage with market-specific thresholds.

    Yandex: 2-3% keyword density (higher tolerance)
    Google: 0.5-1.5% keyword density (lower, more natural)
    """

    # Market-specific thresholds
    YANDEX_MIN_DENSITY = 0.02  # 2%
    YANDEX_MAX_DENSITY = 0.03  # 3%
    GOOGLE_MIN_DENSITY = 0.005  # 0.5%
    GOOGLE_MAX_DENSITY = 0.015  # 1.5%

    def __init__(self, market: str = "google"):
        """
        Initialize analyzer for specific market.

        Args:
            market: Target market ("yandex" or "google")
        """
        self.market = market.lower()
        if self.market == "yandex":
            self.min_density = self.YANDEX_MIN_DENSITY
            self.max_density = self.YANDEX_MAX_DENSITY
        else:
            self.min_density = self.GOOGLE_MIN_DENSITY
            self.max_density = self.GOOGLE_MAX_DENSITY

    def analyze_keyword_density(
        self, text: str, target_keyword: str, total_words: int
    ) -> dict:
        """
        Analyze keyword density for target keyword.

        Args:
            text: Clean text content
            target_keyword: Target keyword to analyze
            total_words: Total word count

        Returns:
            Dictionary with density analysis
        """
        if not text or not target_keyword or total_words == 0:
            return {
                "keyword": target_keyword,
                "count": 0,
                "density": 0.0,
                "status": "missing",
                "recommendation": "Add keyword to content",
            }

        # Count keyword occurrences (case-insensitive)
        keyword_lower = target_keyword.lower()
        text_lower = text.lower()
        count = text_lower.count(keyword_lower)

        # Calculate density
        density = count / total_words if total_words > 0 else 0.0

        # Determine status
        if density < self.min_density:
            status = "too_low"
            recommendation = f"Increase keyword usage (current: {density:.2%}, target: {self.min_density:.2%}-{self.max_density:.2%})"
        elif density > self.max_density:
            status = "too_high"
            recommendation = f"Reduce keyword usage (current: {density:.2%}, target: {self.min_density:.2%}-{self.max_density:.2%})"
        else:
            status = "optimal"
            recommendation = f"Keyword density is optimal ({density:.2%})"

        return {
            "keyword": target_keyword,
            "count": count,
            "density": density,
            "status": status,
            "recommendation": recommendation,
            "market": self.market,
            "target_range": f"{self.min_density:.2%}-{self.max_density:.2%}",
        }

    def extract_lsi_keywords(
        self, keywords: dict, target_keyword: str, min_count: int = 2
    ) -> list[dict]:
        """
        Extract LSI (Latent Semantic Indexing) keywords.

        LSI keywords are semantically related terms that appear frequently.
        Target: 5-10 LSI keywords per 1000 words.

        Args:
            keywords: Dictionary of keyword counts from TextExtractor
            target_keyword: Main target keyword
            min_count: Minimum occurrences to consider

        Returns:
            List of LSI keywords with counts
        """
        if not keywords:
            return []

        # Filter out target keyword and low-frequency terms
        target_lower = target_keyword.lower()
        lsi_candidates = {
            k: v
            for k, v in keywords.items()
            if k != target_lower and v >= min_count and len(k) > 3
        }

        # Sort by frequency
        sorted_lsi = sorted(lsi_candidates.items(), key=lambda x: x[1], reverse=True)

        # Return top LSI keywords
        return [
            {"keyword": keyword, "count": count, "type": "lsi"}
            for keyword, count in sorted_lsi[:20]  # Top 20 LSI keywords
        ]

    def analyze_keyword_placement(
        self,
        target_keyword: str,
        title: str,
        headings: dict,
        text: str,
    ) -> dict:
        """
        Analyze keyword placement in strategic locations.

        Critical placements:
        - Title tag
        - H1 heading
        - First 100 words
        - Last 100 words

        Args:
            target_keyword: Target keyword
            title: Page title
            headings: Dictionary of headings (h1-h6)
            text: Full text content

        Returns:
            Dictionary with placement analysis
        """
        keyword_lower = target_keyword.lower()
        placements = {
            "in_title": False,
            "in_h1": False,
            "in_first_100_words": False,
            "in_last_100_words": False,
            "in_h2": False,
            "in_h3": False,
        }

        # Check title
        if title and keyword_lower in title.lower():
            placements["in_title"] = True

        # Check H1
        h1_tags = headings.get("h1", [])
        if any(keyword_lower in h.lower() for h in h1_tags):
            placements["in_h1"] = True

        # Check H2
        h2_tags = headings.get("h2", [])
        if any(keyword_lower in h.lower() for h in h2_tags):
            placements["in_h2"] = True

        # Check H3
        h3_tags = headings.get("h3", [])
        if any(keyword_lower in h.lower() for h in h3_tags):
            placements["in_h3"] = True

        # Check first 100 words
        words = text.split()
        if len(words) >= 100:
            first_100 = " ".join(words[:100]).lower()
            if keyword_lower in first_100:
                placements["in_first_100_words"] = True

        # Check last 100 words
        if len(words) >= 100:
            last_100 = " ".join(words[-100:]).lower()
            if keyword_lower in last_100:
                placements["in_last_100_words"] = True

        # Calculate placement score (0-100)
        critical_placements = ["in_title", "in_h1", "in_first_100_words"]
        critical_score = sum(placements[p] for p in critical_placements) / len(
            critical_placements
        )

        optional_placements = ["in_last_100_words", "in_h2", "in_h3"]
        optional_score = sum(placements[p] for p in optional_placements) / len(
            optional_placements
        )

        total_score = (critical_score * 0.7 + optional_score * 0.3) * 100

        # Generate recommendations
        recommendations = []
        if not placements["in_title"]:
            recommendations.append("Add keyword to title tag")
        if not placements["in_h1"]:
            recommendations.append("Add keyword to H1 heading")
        if not placements["in_first_100_words"]:
            recommendations.append("Add keyword to first 100 words")
        if not placements["in_last_100_words"]:
            recommendations.append("Consider adding keyword to conclusion")

        return {
            "placements": placements,
            "score": round(total_score, 1),
            "recommendations": recommendations,
        }

    def analyze_market_optimization(
        self,
        density_analysis: dict,
        placement_analysis: dict,
        lsi_keywords: list[dict],
        total_words: int,
    ) -> dict:
        """
        Analyze overall market-specific optimization.

        Args:
            density_analysis: Keyword density analysis
            placement_analysis: Keyword placement analysis
            lsi_keywords: LSI keywords list
            total_words: Total word count

        Returns:
            Dictionary with market optimization analysis
        """
        # Calculate LSI keyword ratio (target: 5-10 per 1000 words)
        lsi_count = len(lsi_keywords)
        lsi_per_1000 = (lsi_count / total_words) * 1000 if total_words > 0 else 0
        lsi_target_min = 5
        lsi_target_max = 10

        lsi_status = "optimal"
        if lsi_per_1000 < lsi_target_min:
            lsi_status = "too_low"
        elif lsi_per_1000 > lsi_target_max:
            lsi_status = "too_high"

        # Overall optimization score (0-100)
        density_score = 100 if density_analysis["status"] == "optimal" else 50
        placement_score = placement_analysis["score"]
        lsi_score = 100 if lsi_status == "optimal" else 70

        overall_score = (density_score * 0.4 + placement_score * 0.4 + lsi_score * 0.2)

        # Market-specific recommendations
        recommendations = []

        if self.market == "yandex":
            recommendations.append(
                "Yandex optimization: Focus on exact keyword matches and user behavior signals"
            )
            if density_analysis["status"] == "too_low":
                recommendations.append(
                    "Yandex tolerates higher keyword density (2-3%) - increase usage"
                )
        else:
            recommendations.append(
                "Google optimization: Focus on natural language and semantic relevance"
            )
            if density_analysis["status"] == "too_high":
                recommendations.append(
                    "Google prefers lower keyword density (0.5-1.5%) - reduce usage"
                )

        if lsi_status == "too_low":
            recommendations.append(
                f"Add more LSI keywords (current: {lsi_per_1000:.1f} per 1000 words, target: {lsi_target_min}-{lsi_target_max})"
            )

        recommendations.extend(placement_analysis["recommendations"])

        return {
            "market": self.market,
            "overall_score": round(overall_score, 1),
            "density_score": density_score,
            "placement_score": placement_score,
            "lsi_score": lsi_score,
            "lsi_count": lsi_count,
            "lsi_per_1000_words": round(lsi_per_1000, 1),
            "lsi_status": lsi_status,
            "recommendations": recommendations,
        }
