"""CI Analysis — LLM-powered competitive intelligence for pre-sale."""

from .models import (
    SeoAuditResult,
    SocialScanResult,
    CompetitorFull,
    ComparisonMatrix,
    PipelineProgress,
)

# Lazy imports — each module is developed independently.
# Modules that don't exist yet are silently skipped.
_try_imports = {
    "SeoAuditor": ".seo_auditor",
    "SocialScanner": ".social_scanner",
    "PipelineRunner": ".pipeline_runner",
    "ComparisonMatrixBuilder": ".comparison_matrix",
    "DialogueManager": ".dialogue_manager",
}

import importlib

for _name, _mod in _try_imports.items():
    try:
        _module = importlib.import_module(_mod, package=__name__)
        globals()[_name] = getattr(_module, _name)
    except ModuleNotFoundError:
        pass

__all__ = [
    "SeoAuditResult",
    "SocialScanResult",
    "CompetitorFull",
    "ComparisonMatrix",
    "PipelineProgress",
    "SeoAuditor",
    "SocialScanner",
    "PipelineRunner",
    "ComparisonMatrixBuilder",
    "DialogueManager",
]
