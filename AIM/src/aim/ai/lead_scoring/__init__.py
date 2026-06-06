"""AI Lead Scoring Module

Provides AI-powered lead scoring with 30+ factors and ML-based prediction.

Components:
- LeadFeatureExtractor: Extract 30+ features from lead data
- LeadScoringService: Score leads and assign tiers (Hot/Warm/Cold)
- ModelTrainer: Train and evaluate XGBoost models

Part of: Phase 11 Sprint 2 - Task 2.2
"""

from src.aim.ai.lead_scoring.feature_extractor import LeadFeatureExtractor
from src.aim.ai.lead_scoring.schemas import LeadScore
from src.aim.ai.lead_scoring.scoring_service import LeadScoringService

__all__ = [
    "LeadFeatureExtractor",
    "LeadScore",
    "LeadScoringService",
]
