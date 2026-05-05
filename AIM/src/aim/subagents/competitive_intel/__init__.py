"""
Competitive Intelligence Subagents Package

Система конкурентной разведки с 23 специализированными агентами.
"""

from .orchestrator.ci_orchestrator import CIOrchestrator
from .agents.ci_scout import CIScoutAgent

__all__ = [
    "CIOrchestrator",
    "CIScoutAgent",
]
