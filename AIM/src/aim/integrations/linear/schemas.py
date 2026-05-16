"""Pydantic schemas for Linear API data

Models for Linear issues, tasks, teams, workflow states, users, and labels.

Part of: Phase 11 Sprint 2 - Task 2.3
"""

from datetime import datetime

from pydantic import BaseModel, Field


class LinearWorkflowState(BaseModel):
    """Linear workflow state (backlog, unstarted, started, completed, canceled)"""

    id: str = Field(..., description="Workflow state ID")
    name: str = Field(..., description="State name (e.g., 'Backlog', 'In Progress')")
    type: str = Field(
        ...,
        description="State type: backlog, unstarted, started, completed, canceled",
    )
    color: str | None = Field(None, description="State color hex code")
    position: float | None = Field(None, description="Position in workflow")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "state_abc123",
                "name": "In Progress",
                "type": "started",
                "color": "#f2c94c",
                "position": 2.0,
            }
        }


class LinearUser(BaseModel):
    """Linear user (assignee)"""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User full name")
    email: str = Field(..., description="User email")
    avatar_url: str | None = Field(None, description="User avatar URL")
    active: bool = Field(default=True, description="User is active")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "user_abc123",
                "name": "John Doe",
                "email": "john@example.com",
                "avatar_url": "https://avatar.linear.app/user_abc123",
                "active": True,
            }
        }


class LinearLabel(BaseModel):
    """Linear label (Hot Lead, Warm Lead, etc.)"""

    id: str = Field(..., description="Label ID")
    name: str = Field(..., description="Label name")
    color: str = Field(..., description="Label color hex code")
    description: str | None = Field(None, description="Label description")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "label_hot123",
                "name": "Hot Lead",
                "color": "#eb5757",
                "description": "High-priority lead (score >= 80)",
            }
        }


class LinearTeam(BaseModel):
    """Linear team"""

    id: str = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    key: str = Field(..., description="Team key (e.g., 'SALES')")
    description: str | None = Field(None, description="Team description")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "team_abc123",
                "name": "Sales Team",
                "key": "SALES",
                "description": "Sales and lead management",
            }
        }


class LinearProject(BaseModel):
    """Linear project"""

    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    state: str = Field(..., description="Project state (planned, started, completed, canceled)")
    teamId: str = Field(..., description="Team ID")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "proj-123",
                "name": "Marketing Campaign",
                "description": "Q2 2026 campaign",
                "state": "planned",
                "teamId": "team-123",
            }
        }


class LinearIssue(BaseModel):
    """Linear issue (task)"""

    id: str = Field(..., description="Issue ID")
    identifier: str = Field(..., description="Issue identifier (e.g., 'SALES-123')")
    title: str = Field(..., description="Issue title")
    description: str | None = Field(None, description="Issue description (markdown)")
    priority: int = Field(..., ge=0, le=4, description="Priority (0=none, 1=urgent, 4=low)")
    state: LinearWorkflowState = Field(..., description="Current workflow state")
    assignee: LinearUser | None = Field(None, description="Assigned user")
    labels: list[LinearLabel] = Field(default_factory=list, description="Issue labels")
    url: str = Field(..., description="Issue URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "issue_abc123",
                "identifier": "SALES-42",
                "title": "[Hot] Plastic Surgery Lead - Score 87",
                "description": "## Lead Information\n\n**Name:** Dr. Smith...",
                "priority": 1,
                "state": {
                    "id": "state_backlog",
                    "name": "Backlog",
                    "type": "backlog",
                },
                "assignee": {
                    "id": "user_abc123",
                    "name": "John Doe",
                    "email": "john@example.com",
                },
                "labels": [
                    {
                        "id": "label_hot123",
                        "name": "Hot Lead",
                        "color": "#eb5757",
                    }
                ],
                "url": "https://linear.app/aim/issue/SALES-42",
                "created_at": "2026-05-16T12:00:00Z",
                "updated_at": "2026-05-16T12:00:00Z",
            }
        }


class LinearTask(BaseModel):
    """Linear task metadata stored in AIM database"""

    id: str = Field(..., description="Task ID (UUID)")
    lead_id: str = Field(..., description="Associated lead ID")
    linear_issue_id: str = Field(..., description="Linear issue ID")
    linear_url: str = Field(..., description="Linear issue URL")
    status: str = Field(
        ...,
        description="Task status: backlog, in_progress, completed, canceled",
    )
    assignee_id: str | None = Field(None, description="Assigned user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "task_abc123",
                "lead_id": "lead_20260516_hot123",
                "linear_issue_id": "issue_abc123",
                "linear_url": "https://linear.app/aim/issue/SALES-42",
                "status": "backlog",
                "assignee_id": "user_abc123",
                "created_at": "2026-05-16T12:00:00Z",
                "updated_at": "2026-05-16T12:00:00Z",
            }
        }


class LinearCreateIssueInput(BaseModel):
    """Input for creating Linear issue"""

    team_id: str = Field(..., description="Team ID")
    title: str = Field(..., description="Issue title")
    description: str | None = Field(None, description="Issue description (markdown)")
    priority: int = Field(default=0, ge=0, le=4, description="Priority (0-4)")
    label_ids: list[str] = Field(default_factory=list, description="Label IDs")
    assignee_id: str | None = Field(None, description="Assignee user ID")
    state_id: str | None = Field(None, description="Initial workflow state ID")

    class Config:
        json_schema_extra = {
            "example": {
                "team_id": "team_abc123",
                "title": "[Hot] Plastic Surgery Lead - Score 87",
                "description": "## Lead Information\n\n**Name:** Dr. Smith...",
                "priority": 1,
                "label_ids": ["label_hot123"],
                "assignee_id": "user_abc123",
            }
        }


class LinearUpdateIssueInput(BaseModel):
    """Input for updating Linear issue"""

    state_id: str | None = Field(None, description="New workflow state ID")
    assignee_id: str | None = Field(None, description="New assignee user ID")
    priority: int | None = Field(None, ge=0, le=4, description="New priority")
    title: str | None = Field(None, description="New title")
    description: str | None = Field(None, description="New description")

    class Config:
        json_schema_extra = {
            "example": {
                "state_id": "state_in_progress",
                "assignee_id": "user_xyz789",
            }
        }
