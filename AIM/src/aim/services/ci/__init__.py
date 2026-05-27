"""CI Analysis — LLM-powered competitive intelligence for pre-sale."""

from .models import (
    ArticleInfo,
    ArticleSearchResult,
    CompetitorFull,
    ComparisonMatrix,
    DoctorInfo,
    DoctorSocialResult,
    PipelineProgress,
    SeoAuditResult,
    SocialScanResult,
)

# Lazy imports — each module is developed independently.
# Modules that don't exist yet are silently skipped.
_try_imports = {
    "ArticleScanner": ".article_scanner",
    "SeoAuditor": ".seo_auditor",
    "SocialScanner": ".social_scanner",
    "PipelineRunner": ".pipeline_runner",
    "ComparisonMatrixBuilder": ".comparison_matrix",
    "DialogueManager": ".dialogue_manager",
    "DoctorInfo": ".models",
    "extract_doctors": ".doctor_extractor",
    "compute_influence_score": ".doctor_extractor",
    "identify_leaders": ".doctor_extractor",
}

import importlib
import logging

_logger = logging.getLogger(__name__)

for _name, _mod in _try_imports.items():
    try:
        _module = importlib.import_module(_mod, package=__name__)
        globals()[_name] = getattr(_module, _name)
    except ModuleNotFoundError:
        pass
    except ImportError as e:
        _logger.warning("CI module %s failed to import: %s", _name, e)

__all__ = [
    "ArticleInfo",
    "ArticleScanner",
    "ArticleSearchResult",
    "CompetitorFull",
    "ComparisonMatrix",
    "ComparisonMatrixBuilder",
    "DialogueManager",
    "DoctorInfo",
    "DoctorSocialResult",
    "PipelineProgress",
    "PipelineRunner",
    "SeoAuditor",
    "SeoAuditResult",
    "SocialScanResult",
    "SocialScanner",
    "compute_influence_score",
    "extract_doctors",
    "identify_leaders",
]
