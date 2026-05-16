"""Linear Integration Module

Automatic task creation in Linear for Hot/Warm leads.

Components:
- LinearClient: GraphQL API client
- LinearService: Business logic for task management
- Schemas: Pydantic models for Linear data

Part of: Phase 11 Sprint 2 - Task 2.3
"""

from AIM.src.aim.integrations.linear.client import LinearClient
from AIM.src.aim.integrations.linear.schemas import (
    LinearIssue,
    LinearLabel,
    LinearProject,
    LinearTask,
    LinearTeam,
    LinearUser,
    LinearWorkflowState,
)
from AIM.src.aim.integrations.linear.service import LinearService

__all__ = [
    "LinearClient",
    "LinearService",
    "LinearIssue",
    "LinearProject",
    "LinearTask",
    "LinearTeam",
    "LinearWorkflowState",
    "LinearUser",
    "LinearLabel",
]
