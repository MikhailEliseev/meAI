"""Pydantic Schemas for API Responses

Validated data models for keyword research API responses and competitor analysis.
"""

from .api_responses import (
    AhrefsKeywordData,
    KeywordExpansionRequest,
    SEMrushKeywordData,
)
from .compliance import (
    RiskLevel,
    ComplianceAction,
    PatternMatch,
    FDAEnforcementRecord,
    ComplianceCheckResult,
    AuditTrailEntry,
)
from .competitor_analysis import (
    AnalysisMode,
    TargetMarket,
    CompetitorAnalysisRequest,
    KeywordAnalysisResult,
    AIDetectionResult,
    EEATScore,
    ContentStructure,
    TechnicalSEOResult,
    CompetitorAnalysisResult,
    CompetitorComparisonReport,
)

__all__ = [
    "SEMrushKeywordData",
    "AhrefsKeywordData",
    "KeywordExpansionRequest",
    "RiskLevel",
    "ComplianceAction",
    "PatternMatch",
    "FDAEnforcementRecord",
    "ComplianceCheckResult",
    "AuditTrailEntry",
    "AnalysisMode",
    "TargetMarket",
    "CompetitorAnalysisRequest",
    "KeywordAnalysisResult",
    "AIDetectionResult",
    "EEATScore",
    "ContentStructure",
    "TechnicalSEOResult",
    "CompetitorAnalysisResult",
    "CompetitorComparisonReport",
]
