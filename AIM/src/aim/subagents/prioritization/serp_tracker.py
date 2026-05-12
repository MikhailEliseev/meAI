"""SERP Feature Tracker

Tracks SERP features (AI Overview, Featured Snippet, PAA) and their impact on CTR.
Dynamically adjusts penalties based on real CTR data.
"""

from datetime import datetime, timezone
from typing import Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class SERPFeature(str):
    """SERP feature types"""

    AI_OVERVIEW = "ai_overview"
    FEATURED_SNIPPET = "featured_snippet"
    PEOPLE_ALSO_ASK = "people_also_ask"
    LOCAL_PACK = "local_pack"
    KNOWLEDGE_PANEL = "knowledge_panel"
    IMAGE_PACK = "image_pack"
    VIDEO_CAROUSEL = "video_carousel"
    SHOPPING_RESULTS = "shopping_results"


class SERPFeatureData(BaseModel):
    """SERP feature detection data"""

    keyword: str = Field(..., description="Keyword")
    features: list[str] = Field(..., description="Detected SERP features")
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    # CTR data (if available from GSC)
    organic_ctr: Optional[float] = Field(None, ge=0, le=1, description="Organic CTR")
    impressions: Optional[int] = Field(None, ge=0, description="Impressions")
    clicks: Optional[int] = Field(None, ge=0, description="Clicks")
    position: Optional[float] = Field(None, ge=1, description="Average position")


class SERPFeatureImpact(BaseModel):
    """SERP feature impact on CTR"""

    feature: str = Field(..., description="SERP feature")
    baseline_ctr: float = Field(..., ge=0, le=1, description="Baseline CTR without feature")
    actual_ctr: float = Field(..., ge=0, le=1, description="Actual CTR with feature")
    ctr_reduction: float = Field(..., ge=0, le=1, description="CTR reduction (0-1)")
    sample_size: int = Field(..., ge=0, description="Number of keywords in sample")
    confidence: float = Field(..., ge=0, le=1, description="Statistical confidence")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SERPTracker:
    """Track SERP features and their impact on CTR

    Dynamically adjusts penalties based on real CTR data from Google Search Console.
    """

    def __init__(self):
        """Initialize SERP tracker"""
        self.logger = logger.bind(component="serp_tracker")

        # Default penalties (from config)
        self.default_penalties = {
            SERPFeature.AI_OVERVIEW: 0.5,
            SERPFeature.FEATURED_SNIPPET: 0.3,
            SERPFeature.PEOPLE_ALSO_ASK: 0.2,
            SERPFeature.LOCAL_PACK: 0.25,
            SERPFeature.KNOWLEDGE_PANEL: 0.4,
            SERPFeature.IMAGE_PACK: 0.15,
            SERPFeature.VIDEO_CAROUSEL: 0.2,
            SERPFeature.SHOPPING_RESULTS: 0.3,
        }

        # Learned penalties (updated from real data)
        self.learned_penalties: dict[str, float] = {}

        # Impact tracking
        self.feature_impacts: dict[str, SERPFeatureImpact] = {}

    def detect_features(self, keyword: str, serp_html: Optional[str] = None) -> list[str]:
        """Detect SERP features for a keyword

        Args:
            keyword: Keyword to check
            serp_html: Optional SERP HTML for parsing

        Returns:
            List of detected features

        Note:
            In production, this would parse SERP HTML or use SERP API.
            For now, returns empty list (features provided by caller).
        """
        # TODO: Implement SERP scraping or API integration
        # Options:
        # 1. SerpAPI (paid, reliable)
        # 2. DataForSEO (paid, comprehensive)
        # 3. Custom scraping (free, fragile)

        self.logger.info("serp_detection_not_implemented", keyword=keyword)
        return []

    def get_penalty(self, feature: str) -> float:
        """Get penalty for a SERP feature

        Args:
            feature: SERP feature name

        Returns:
            Penalty multiplier (0.0-1.0)
        """
        # Use learned penalty if available, otherwise default
        return self.learned_penalties.get(feature, self.default_penalties.get(feature, 0.0))

    def calculate_total_penalty(self, features: list[str]) -> float:
        """Calculate total penalty from multiple features

        Args:
            features: List of SERP features

        Returns:
            Total penalty (0.0-1.0)
        """
        total_penalty = 0.0

        for feature in features:
            penalty = self.get_penalty(feature)
            total_penalty += penalty

        # Cap at 100% penalty
        return min(1.0, total_penalty)

    def update_from_ctr_data(
        self,
        keyword: str,
        features: list[str],
        organic_ctr: float,
        position: float,
        impressions: int,
    ) -> None:
        """Update feature impact from real CTR data

        Args:
            keyword: Keyword
            features: Detected SERP features
            organic_ctr: Actual organic CTR
            position: Average position
            impressions: Number of impressions
        """
        # Calculate expected CTR for position (without features)
        expected_ctr = self._get_expected_ctr(position)

        # Calculate CTR reduction
        ctr_reduction = max(0, (expected_ctr - organic_ctr) / expected_ctr) if expected_ctr > 0 else 0

        # Update impact for each feature
        for feature in features:
            if feature not in self.feature_impacts:
                self.feature_impacts[feature] = SERPFeatureImpact(
                    feature=feature,
                    baseline_ctr=expected_ctr,
                    actual_ctr=organic_ctr,
                    ctr_reduction=ctr_reduction,
                    sample_size=1,
                    confidence=0.1,  # Low confidence with 1 sample
                )
            else:
                # Update running average
                impact = self.feature_impacts[feature]
                n = impact.sample_size
                impact.baseline_ctr = (impact.baseline_ctr * n + expected_ctr) / (n + 1)
                impact.actual_ctr = (impact.actual_ctr * n + organic_ctr) / (n + 1)
                impact.ctr_reduction = (impact.ctr_reduction * n + ctr_reduction) / (n + 1)
                impact.sample_size += 1
                impact.confidence = min(1.0, impact.sample_size / 100)  # 100 samples = full confidence
                impact.last_updated = datetime.now(timezone.utc)

        self.logger.info(
            "ctr_data_updated",
            keyword=keyword,
            features=features,
            organic_ctr=round(organic_ctr, 4),
            expected_ctr=round(expected_ctr, 4),
            ctr_reduction=round(ctr_reduction, 4),
        )

    def adjust_penalties(self, min_confidence: float = 0.7) -> dict[str, float]:
        """Adjust penalties based on learned CTR impact

        Args:
            min_confidence: Minimum confidence to adjust penalty

        Returns:
            Updated penalties
        """
        adjusted = {}

        for feature, impact in self.feature_impacts.items():
            if impact.confidence >= min_confidence:
                # Use learned CTR reduction as penalty
                adjusted[feature] = impact.ctr_reduction
                self.learned_penalties[feature] = impact.ctr_reduction

                self.logger.info(
                    "penalty_adjusted",
                    feature=feature,
                    old_penalty=self.default_penalties.get(feature, 0.0),
                    new_penalty=round(impact.ctr_reduction, 4),
                    sample_size=impact.sample_size,
                    confidence=round(impact.confidence, 2),
                )

        return adjusted

    def _get_expected_ctr(self, position: float) -> float:
        """Get expected CTR for a position (without SERP features)

        Args:
            position: Average position

        Returns:
            Expected CTR (0.0-1.0)

        Note:
            Based on industry benchmarks:
            - Position 1: 28.5% CTR
            - Position 2: 15.7% CTR
            - Position 3: 11.0% CTR
            - Position 4-10: exponential decay
            - Position 11+: <2% CTR
        """
        if position <= 1:
            return 0.285
        elif position <= 2:
            return 0.157
        elif position <= 3:
            return 0.110
        elif position <= 10:
            # Exponential decay from position 3 to 10
            return 0.110 * (0.7 ** (position - 3))
        else:
            # Very low CTR for position 11+
            return max(0.01, 0.02 * (0.8 ** (position - 10)))

    def get_feature_impact(self, feature: str) -> Optional[SERPFeatureImpact]:
        """Get impact data for a feature

        Args:
            feature: SERP feature

        Returns:
            Impact data if available
        """
        return self.feature_impacts.get(feature)

    def get_all_impacts(self) -> dict[str, SERPFeatureImpact]:
        """Get all feature impacts

        Returns:
            Dictionary of feature impacts
        """
        return self.feature_impacts.copy()
