"""
AI SEO Analyzer Module

Comprehensive SEO analysis powered by AI:
- Content quality (N-E-E-A-T-T framework)
- Entity optimization (Knowledge Graph)
- SERP analysis (features, gaps)
- Conversational optimization (AI Overviews, ChatGPT, Perplexity)
"""

from .analyzer import SEOAnalyzer, analyze_url
from .content_quality import ContentQualityAnalyzer
from .entity_optimizer import EntityOptimizer
from .serp_analyzer import SERPAnalyzer
from .conversational_optimizer import ConversationalOptimizer
from .schemas import (
    Entity,
    ContentQualityScore,
    EntityAnalysis,
    SERPAnalysis,
    SERPFeature,
    ConversationalOptimization,
    SEOAnalysisResult,
)

__all__ = [
    # Main analyzer
    "SEOAnalyzer",
    "analyze_url",
    # Component analyzers
    "ContentQualityAnalyzer",
    "EntityOptimizer",
    "SERPAnalyzer",
    "ConversationalOptimizer",
    # Schemas
    "Entity",
    "ContentQualityScore",
    "EntityAnalysis",
    "SERPAnalysis",
    "SERPFeature",
    "ConversationalOptimization",
    "SEOAnalysisResult",
]
