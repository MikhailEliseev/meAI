"""Lead Scoring Service

AI-powered lead scoring using XGBoost model with 30+ features.

Features:
- Score leads 0-100 based on conversion probability
- Assign tier (Hot/Warm/Cold)
- Provide explainable AI (top 5 factors)
- Real-time inference (<100ms)

Part of: Phase 11 Sprint 2 - Task 2.2
"""

from datetime import datetime, timezone
from typing import Any

import numpy as np

from aim.ai.lead_scoring.feature_extractor import LeadFeatureExtractor
from aim.ai.lead_scoring.schemas import LeadScore
from aim.models.lead import Lead


class LeadScoringService:
    """AI-powered lead scoring service

    Uses XGBoost model to score leads based on 30+ features.
    Assigns tier (Hot/Warm/Cold) and provides explanation.
    """

    # Tier thresholds
    HOT_THRESHOLD = 80
    WARM_THRESHOLD = 50

    # Feature weights (for rule-based scoring until ML model is trained)
    FEATURE_WEIGHTS = {
        # Demographic (10 points)
        "specialty_value": 5,
        "location_value": 3,
        "clinic_size": 2,
        # Behavioral (20 points)
        "message_quality": 10,
        "response_time": 5,
        "utm_campaign_value": 5,
        # Engagement (15 points)
        "form_completion": 5,
        "message_length": 5,
        "has_phone_and_email": 5,
        # Technical (10 points)
        "device_type": 3,
        "browser": 2,
        "session_duration": 5,
        # Timing (10 points)
        "is_business_hours": 5,
        "day_of_week": 5,
        # Source (15 points)
        "is_organic": 10,
        "is_referral": 5,
        # Historical (10 points)
        "previous_submissions": 5,
        "email_domain_type": 5,
        # Compliance (10 points)
        "fz152_consent": 5,
        "data_completeness": 5,
    }

    def __init__(self, model_path: str | None = None):
        """Initialize lead scoring service

        Args:
            model_path: Path to trained XGBoost model (optional)
                       If None, uses rule-based scoring
        """
        self.model_path = model_path
        self.model = None
        self.feature_extractor = LeadFeatureExtractor()

        # Load model if path provided
        if model_path:
            self._load_model(model_path)

    def _load_model(self, model_path: str) -> None:
        """Load trained XGBoost model

        Args:
            model_path: Path to model file

        Note:
            For MVP, we use rule-based scoring.
            ML model will be trained after collecting 100+ leads with conversions.
        """
        try:
            import xgboost as xgb

            self.model = xgb.Booster()
            self.model.load_model(model_path)
        except ImportError:
            print("[WARNING] XGBoost not installed. Using rule-based scoring.")
            self.model = None
        except Exception as e:
            print(f"[WARNING] Failed to load model: {e}. Using rule-based scoring.")
            self.model = None

    async def score_lead(
        self,
        lead: Lead,
        metadata: dict[str, Any],
    ) -> LeadScore:
        """Score lead and assign tier

        Args:
            lead: Lead record from database
            metadata: Request metadata (user_agent, utm, session_duration)

        Returns:
            LeadScore with score, tier, explanation
        """
        # Extract features
        features = self.feature_extractor.extract(lead, metadata)

        # Calculate score
        if self.model:
            score = self._score_with_model(features)
        else:
            score = self._score_with_rules(features)

        # Assign tier
        tier = self._assign_tier(score)

        # Generate explanation
        explanation = self._explain_score(features, score)

        return LeadScore(
            score=score,
            tier=tier,
            explanation=explanation,
            factors=features,
            scored_at=datetime.now(timezone.utc),
        )

    def _score_with_model(self, features: dict[str, Any]) -> int:
        """Score lead using ML model

        Args:
            features: Extracted features

        Returns:
            Score 0-100
        """
        import xgboost as xgb

        # Convert features to array
        X = self._features_to_array(features)

        # Predict probability
        dmatrix = xgb.DMatrix(X)
        probability = self.model.predict(dmatrix)[0]

        # Convert to score (0-100)
        score = int(probability * 100)
        return max(0, min(100, score))

    def _score_with_rules(self, features: dict[str, Any]) -> int:
        """Score lead using rule-based system

        Args:
            features: Extracted features

        Returns:
            Score 0-100

        Note:
            This is a fallback for MVP until ML model is trained.
            Uses weighted sum of features.
        """
        total_score = 0

        # Demographic factors (10 points)
        total_score += features.get("specialty_value", 0)
        total_score += self._normalize_location_value(features.get("location_value", 0))
        total_score += 2 if features.get("clinic_size") == "chain" else 1

        # Behavioral factors (20 points)
        total_score += features.get("message_quality", 0)
        total_score += self._score_response_time(features.get("response_time", ""))
        total_score += features.get("utm_campaign_value", 0)

        # Engagement factors (15 points)
        total_score += int(features.get("form_completion", 0) * 5)
        total_score += self._score_message_length(features.get("message_length", 0))
        total_score += 5 if features.get("has_phone_and_email") else 0

        # Technical factors (10 points)
        total_score += self._score_device(features.get("device_type", ""))
        total_score += self._score_browser(features.get("browser", ""))
        total_score += self._score_session_duration(features.get("session_duration", 0))

        # Timing factors (10 points)
        total_score += 5 if features.get("is_business_hours") else 2
        total_score += self._score_day_of_week(features.get("day_of_week", 0))

        # Source factors (15 points)
        total_score += 10 if features.get("is_organic") else 0
        total_score += 5 if features.get("is_referral") else 0

        # Historical factors (10 points)
        total_score += self._score_previous_submissions(
            features.get("previous_submissions", 0)
        )
        total_score += 5 if features.get("email_domain_type") == "business" else 0

        # Compliance factors (10 points)
        total_score += 5 if features.get("fz152_consent") else 0
        total_score += int(features.get("data_completeness", 0) * 5)

        # Normalize to 0-100
        return max(0, min(100, total_score))

    def _normalize_location_value(self, value: int) -> int:
        """Normalize location value to 0-3 range"""
        if value >= 10:
            return 3
        elif value >= 8:
            return 2
        elif value >= 5:
            return 1
        else:
            return 0

    def _score_response_time(self, response_time: str) -> int:
        """Score response time category"""
        scores = {
            "business_hours": 5,
            "evening": 3,
            "weekend": 2,
            "night": 1,
        }
        return scores.get(response_time, 0)

    def _score_message_length(self, length: int) -> int:
        """Score message length"""
        if length > 200:
            return 5
        elif length > 100:
            return 3
        elif length > 50:
            return 2
        else:
            return 1

    def _score_device(self, device_type: str) -> int:
        """Score device type"""
        scores = {
            "desktop": 3,
            "tablet": 2,
            "mobile": 1,
            "unknown": 0,
        }
        return scores.get(device_type, 0)

    def _score_browser(self, browser: str) -> int:
        """Score browser type"""
        scores = {
            "chrome": 2,
            "safari": 2,
            "firefox": 2,
            "edge": 2,
            "other": 1,
            "unknown": 0,
        }
        return scores.get(browser, 0)

    def _score_session_duration(self, duration: int) -> int:
        """Score session duration"""
        if duration > 180:  # >3 minutes
            return 5
        elif duration > 120:  # >2 minutes
            return 3
        elif duration > 60:  # >1 minute
            return 2
        else:
            return 1

    def _score_day_of_week(self, day: int) -> int:
        """Score day of week (0=Monday, 6=Sunday)"""
        if 0 <= day <= 4:  # Weekday
            return 5
        else:  # Weekend
            return 2

    def _score_previous_submissions(self, count: int) -> int:
        """Score previous submissions (fewer is better)"""
        if count == 0:
            return 5
        elif count == 1:
            return 3
        else:
            return 0

    def _assign_tier(self, score: int) -> str:
        """Assign tier based on score

        Args:
            score: Lead score 0-100

        Returns:
            "Hot", "Warm", or "Cold"
        """
        if score >= self.HOT_THRESHOLD:
            return "Hot"
        elif score >= self.WARM_THRESHOLD:
            return "Warm"
        else:
            return "Cold"

    def _explain_score(
        self,
        features: dict[str, Any],
        score: int,
    ) -> list[str]:
        """Generate explanation for score

        Returns top 5 factors that influenced the score.

        Args:
            features: Extracted features
            score: Calculated score

        Returns:
            List of human-readable explanations
        """
        explanations = []

        # Specialty
        specialty_value = features.get("specialty_value", 0)
        if specialty_value >= 4:
            specialty_name = features.get("specialty", "").replace("_", " ").title()
            explanations.append(
                f"High-value specialty: {specialty_name} (+{specialty_value} points)"
            )

        # Message quality
        message_quality = features.get("message_quality", 0)
        if message_quality >= 7:
            explanations.append(f"Detailed inquiry message (+{message_quality} points)")

        # Business hours
        if features.get("is_business_hours"):
            explanations.append("Business hours submission (+5 points)")

        # Organic traffic
        if features.get("is_organic"):
            explanations.append("Organic search traffic (+10 points)")

        # First-time submission
        if features.get("previous_submissions", 0) == 0:
            explanations.append("First-time submission (+5 points)")

        # Location
        location_value = features.get("location_value", 0)
        if location_value >= 8:
            location = features.get("location", "").title()
            explanations.append(f"High-value location: {location} (+{location_value} points)")

        # UTM campaign
        utm_value = features.get("utm_campaign_value", 0)
        if utm_value >= 3:
            explanations.append(f"High-intent campaign (+{utm_value} points)")

        # Session duration
        session_duration = features.get("session_duration", 0)
        if session_duration > 120:
            explanations.append(f"Long session duration: {session_duration}s (+5 points)")

        # Business email
        if features.get("email_domain_type") == "business":
            explanations.append("Business email domain (+5 points)")

        # Complete data
        completeness = features.get("data_completeness", 0)
        if completeness >= 0.8:
            explanations.append(f"Complete data: {int(completeness * 100)}% (+5 points)")

        # Return top 5
        return explanations[:5]

    def _features_to_array(self, features: dict[str, Any]) -> np.ndarray:
        """Convert features dict to numpy array for ML model

        Args:
            features: Extracted features

        Returns:
            Numpy array of feature values
        """
        # Feature order (must match training data)
        feature_order = [
            "specialty_value",
            "location_value",
            "message_quality",
            "utm_campaign_value",
            "form_completion",
            "message_length",
            "session_duration",
            "is_business_hours",
            "day_of_week",
            "is_organic",
            "is_referral",
            "previous_submissions",
            "data_completeness",
        ]

        # Extract values in order
        values = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0)
            # Convert boolean to int
            if isinstance(value, bool):
                value = int(value)
            values.append(value)

        return np.array([values])
