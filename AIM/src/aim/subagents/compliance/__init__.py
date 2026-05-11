"""
Compliance Module for Keyword Research Agent

Medical marketing compliance checking with FDA prohibited language detection,
openFDA enforcement lookup, and risk scoring.
"""

from AIM.src.aim.subagents.compliance.patterns import ProhibitedPatternLibrary
from AIM.src.aim.subagents.compliance.fda_client import FDAClient
from AIM.src.aim.subagents.compliance.risk_scorer import RiskScorer
from AIM.src.aim.subagents.compliance.checker import ComplianceChecker

__all__ = [
    "ProhibitedPatternLibrary",
    "FDAClient",
    "RiskScorer",
    "ComplianceChecker",
]
