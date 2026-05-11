"""
Compliance Module for Keyword Research Agent

Medical marketing compliance checking with FDA prohibited language detection,
openFDA enforcement lookup, and risk scoring.
"""

from aim.subagents.compliance.patterns import ProhibitedPatternLibrary

__all__ = [
    "ProhibitedPatternLibrary",
]
