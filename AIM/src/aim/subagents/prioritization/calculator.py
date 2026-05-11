"""Priority Calculator

Calculates keyword priority scores using multi-factor formula with adaptive learning.

Formula: (Volume × Intent × Position) / (Difficulty × Competition)

Adjustments:
- Medical intent boost: +40% transactional, +30% informational
- SERP penalty: -20% to -50% based on AI Overview/Featured Snippet presence
- Compliance penalty: -50% for HIGH risk, -100% (blocked) for CRITICAL risk
"""

import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
import yaml

from src.aim.subagents.schemas.api_responses import KeywordDataUnified
from src.aim.subagents.schemas.compliance import ComplianceCheckResult, RiskLevel
from src.aim.subagents.schemas.prioritization import (
    KeywordPriority,
    PriorityTier,
)

logger = structlog.get_logger()


class PriorityCalculator:
    """Calculate keyword priority scores with adaptive learning

    Loads weights from YAML config and adjusts based on user feedback.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize calculator with config

        Args:
            config_path: Path to prioritization_weights.yaml (default: AIM/config/)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "prioritization_weights.yaml"

        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logger.bind(component="priority_calculator")

    def _load_config(self) -> dict:
        """Load configuration from YAML"""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def calculate_priority(
        self,
        keyword_data: KeywordDataUnified,
        compliance_result: ComplianceCheckResult,
        current_position: Optional[int] = None,
        serp_features: Optional[list[str]] = None,
    ) -> KeywordPriority:
        """Calculate keyword priority score

        Args:
            keyword_data: Unified keyword data from API
            compliance_result: Compliance check result
            current_position: Current ranking position (None if not ranking)
            serp_features: SERP features present (e.g., ["ai_overview", "featured_snippet"])

        Returns:
            KeywordPriority with score and tier
        """
        start_time = datetime.utcnow()

        # Step 1: Calculate base components
        volume_score = self._normalize_volume(keyword_data.volume)
        intent_score = self._get_intent_multiplier(keyword_data.intent)
        position_score = self._get_position_bonus(current_position)
        difficulty_score = keyword_data.difficulty
        # Use difficulty as competition proxy (both measure ranking difficulty)
        # Normalize difficulty (0-100) to competition range (0-1)
        competition_score = difficulty_score / 100.0

        # Step 2: Calculate base score
        # Formula: (Volume × Intent × Position) / (Difficulty × Competition)
        numerator = volume_score * intent_score * position_score
        denominator = max(difficulty_score, 1) * max(competition_score, 0.01)
        base_score = (numerator / denominator) * 100

        # Clamp to 0-100
        base_score = max(0, min(100, base_score))

        # Step 3: Apply medical intent boost
        medical_boost = self._get_medical_boost(keyword_data.intent, keyword_data.keyword)
        adjusted_score = base_score * (1 + medical_boost)

        # Step 4: Apply SERP penalties
        serp_penalty = self._calculate_serp_penalty(serp_features or [])
        adjusted_score = adjusted_score * (1 - serp_penalty)

        # Step 5: Apply compliance penalty
        compliance_penalty = self._get_compliance_penalty(compliance_result.risk_level)
        adjusted_score = adjusted_score * (1 - compliance_penalty)

        # Clamp final score to 0-100
        adjusted_score = max(0, min(100, adjusted_score))

        # Step 6: Classify tier
        tier = self._classify_tier(adjusted_score)

        # Step 7: Calculate confidence
        confidence = self._calculate_confidence(keyword_data, compliance_result)

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        self.logger.info(
            "priority_calculated",
            keyword=keyword_data.keyword,
            base_score=round(base_score, 2),
            adjusted_score=round(adjusted_score, 2),
            tier=tier.value,
            duration_ms=round(duration, 2),
        )

        return KeywordPriority(
            keyword=keyword_data.keyword,
            base_score=base_score,
            adjusted_score=adjusted_score,
            tier=tier,
            volume_score=volume_score,
            intent_score=intent_score,
            position_score=position_score,
            difficulty_score=difficulty_score,
            competition_score=competition_score,
            medical_boost=medical_boost,
            serp_penalty=serp_penalty,
            compliance_penalty=compliance_penalty,
            confidence=confidence,
        )

    def _normalize_volume(self, volume: int) -> float:
        """Normalize search volume to 0-100 scale using log

        Args:
            volume: Raw search volume

        Returns:
            Normalized score 0-100
        """
        min_vol = self.config["volume"]["min_volume"]
        max_vol = self.config["volume"]["max_volume"]
        log_base = self.config["volume"]["log_base"]

        if volume < min_vol:
            return 0.0

        # Logarithmic scale
        log_vol = math.log(volume, log_base)
        log_max = math.log(max_vol, log_base)

        normalized = (log_vol / log_max) * 100
        return max(0, min(100, normalized))

    def _get_intent_multiplier(self, intent: str) -> float:
        """Get intent multiplier from config

        Args:
            intent: Intent type (transactional, commercial, informational, navigational)

        Returns:
            Intent multiplier (1.0-1.4)
        """
        intent_lower = intent.lower()
        return self.config["intent"].get(intent_lower, 1.0)

    def _get_position_bonus(self, position: Optional[int]) -> float:
        """Get position bonus multiplier

        Args:
            position: Current ranking position (None if not ranking)

        Returns:
            Position bonus (0.5-1.0)
        """
        if position is None:
            return self.config["position"]["not_ranking"]

        if position <= 3:
            return self.config["position"]["top_3"]
        elif position <= 10:
            return self.config["position"]["top_10"]
        elif position <= 20:
            return self.config["position"]["top_20"]
        elif position <= 50:
            return self.config["position"]["top_50"]
        elif position <= 100:
            return self.config["position"]["top_100"]
        else:
            return self.config["position"]["not_ranking"]

    def _get_medical_boost(self, intent: str, keyword: str) -> float:
        """Get medical intent boost

        Args:
            intent: Intent type
            keyword: Keyword text (for medical detection)

        Returns:
            Medical boost (0.0-0.4)
        """
        # Check if keyword is medical (simple heuristic)
        medical_terms = [
            "dental", "dentist", "implant", "surgery", "treatment",
            "doctor", "clinic", "medical", "health", "care",
            "therapy", "procedure", "diagnosis", "patient"
        ]

        is_medical = any(term in keyword.lower() for term in medical_terms)

        if not is_medical:
            return 0.0

        intent_lower = intent.lower()
        return self.config["medical_boost"].get(intent_lower, 0.0)

    def _calculate_serp_penalty(self, serp_features: list[str]) -> float:
        """Calculate SERP feature penalty

        Args:
            serp_features: List of SERP features present

        Returns:
            Total penalty (0.0-1.0)
        """
        total_penalty = 0.0

        for feature in serp_features:
            feature_lower = feature.lower()
            penalty = self.config["serp_penalties"].get(feature_lower, 0.0)
            total_penalty += penalty

        # Cap at 100% penalty
        return min(1.0, total_penalty)

    def _get_compliance_penalty(self, risk_level: RiskLevel) -> float:
        """Get compliance penalty from risk level

        Args:
            risk_level: Compliance risk level

        Returns:
            Penalty (0.0-1.0)
        """
        risk_lower = risk_level.value.lower()
        return self.config["compliance_penalties"].get(risk_lower, 0.0)

    def _classify_tier(self, score: float) -> PriorityTier:
        """Classify priority tier from score

        Args:
            score: Adjusted priority score

        Returns:
            Priority tier (P0-P3)
        """
        if score >= self.config["tiers"]["p0_min"]:
            return PriorityTier.P0
        elif score >= self.config["tiers"]["p1_min"]:
            return PriorityTier.P1
        elif score >= self.config["tiers"]["p2_min"]:
            return PriorityTier.P2
        else:
            return PriorityTier.P3

    def _calculate_confidence(
        self,
        keyword_data: KeywordDataUnified,
        compliance_result: ComplianceCheckResult,
    ) -> float:
        """Calculate confidence in priority calculation

        Args:
            keyword_data: Keyword data
            compliance_result: Compliance result

        Returns:
            Confidence (0.0-1.0)
        """
        # Start with full confidence
        confidence = 1.0

        # Reduce confidence for low volume
        if keyword_data.volume < self.config["volume"]["min_volume"]:
            confidence *= 0.7

        # Reduce confidence for high difficulty
        if keyword_data.difficulty > self.config["difficulty"]["threshold_hard"]:
            confidence *= 0.8

        # Reduce confidence for compliance issues
        if compliance_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            confidence *= 0.6

        return max(0.0, min(1.0, confidence))
