"""Magister agents - domain specialists with hybrid search"""

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.magisters.ads_magister import AdsMagister
from meai.agents.magisters.smm_magister import SMMMagister
from meai.agents.magisters.analytics_magister import AnalyticsMagister
from meai.agents.magisters.intelligence_magister import IntelligenceMagister

__all__ = [
    "BaseMagister",
    "SEOMagister",
    "ContentMagister",
    "AdsMagister",
    "SMMMagister",
    "AnalyticsMagister",
    "IntelligenceMagister",
]
