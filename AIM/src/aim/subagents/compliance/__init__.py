"""
Compliance Module for Keyword Research Agent

Medical marketing compliance checking with FDA prohibited language detection,
openFDA enforcement lookup, and risk scoring.
"""

from aim.subagents.compliance.patterns import ProhibitedPatternLibrary
from aim.subagents.compliance.fda_client import FDAClient

__all__ = [
    "ProhibitedPatternLibrary",
    "FDAClient",
]
