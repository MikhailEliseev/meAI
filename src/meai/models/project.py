"""Project Model - Project management for AIM Agency

Manages client projects, deliverables, and project lifecycle.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


class ProjectType(str, Enum):
    """Type of marketing project"""

    SEO = "seo"  # SEO optimization and promotion
    CONTENT = "content"  # Content creation and marketing
    ADS = "ads"  # Advertising campaigns
    FULL_MARKETING = "full_marketing"  # Complete marketing package
    CONSULTING = "consulting"  # Marketing consulting
    AUDIT = "audit"  # Marketing audit


class ProjectStatus(str, Enum):
    """Project lifecycle status"""

    PLANNING = "planning"  # Initial planning phase
    ACTIVE = "active"  # Work in progress
    ON_HOLD = "on_hold"  # Temporarily paused
    REVIEW = "review"  # Under review/approval
    COMPLETED = "completed"  # Successfully completed
    CANCELLED = "cancelled"  # Cancelled by client or agency
    ARCHIVED = "archived"  # Historical record


class DeliverableStatus(str, Enum):
    """Status of individual deliverable"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Deliverable:
    """Project deliverable/milestone"""

    deliverable_id: str
    name: str
    description: str
    status: DeliverableStatus
    due_date: datetime | None = None
    completed_at: datetime | None = None
    assigned_to: str | None = None  # Agent or Magister ID
    result: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None


@dataclass
class Project:
    """Project entity

    Represents a marketing project for a client.
    """

    project_id: str
    client_id: str
    name: str  # e.g., "SEO продвижение стоматологии"
    project_type: ProjectType
    status: ProjectStatus

    # Scope and goals
    description: str | None = None
    goals: list[str] = field(default_factory=list)  # e.g., ["Топ-3 по 20 ключам"]
    target_metrics: dict[str, Any] = field(default_factory=dict)  # e.g., {"traffic": "+50%"}

    # Timeline
    start_date: datetime | None = None
    end_date: datetime | None = None
    duration_months: int | None = None

    # Budget
    total_budget: int | None = None  # RUB
    spent_budget: int = 0  # RUB
    budget_currency: str = "RUB"

    # Deliverables
    deliverables: list[Deliverable] = field(default_factory=list)

    # Team
    assigned_magisters: list[str] = field(default_factory=list)  # Magister IDs
    assigned_agents: list[str] = field(default_factory=list)  # Agent IDs

    # Metadata
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    custom_fields: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    @classmethod
    def create(
        cls,
        client_id: str,
        name: str,
        project_type: ProjectType,
        duration_months: int | None = None,
        **kwargs: Any,
    ) -> "Project":
        """Create a new project

        Args:
            client_id: Client ID
            name: Project name
            project_type: Type of project
            duration_months: Project duration in months
            **kwargs: Additional project fields

        Returns:
            New Project instance
        """
        project_id = f"project-{uuid4().hex[:8]}"

        # Calculate end date if duration provided
        start_date = kwargs.get("start_date", datetime.now(timezone.utc))
        end_date = None
        if duration_months:
            end_date = start_date + timedelta(days=duration_months * 30)

        return cls(
            project_id=project_id,
            client_id=client_id,
            name=name,
            project_type=project_type,
            status=ProjectStatus.PLANNING,
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
            **kwargs,
        )

    def update_status(self, new_status: ProjectStatus) -> None:
        """Update project status with timestamp tracking"""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        if new_status == ProjectStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now(timezone.utc)
        elif new_status == ProjectStatus.CANCELLED and not self.cancelled_at:
            self.cancelled_at = datetime.now(timezone.utc)

    def add_deliverable(
        self,
        name: str,
        description: str,
        due_date: datetime | None = None,
        assigned_to: str | None = None,
    ) -> Deliverable:
        """Add a new deliverable to the project"""
        deliverable = Deliverable(
            deliverable_id=f"deliverable-{uuid4().hex[:8]}",
            name=name,
            description=description,
            status=DeliverableStatus.PENDING,
            due_date=due_date,
            assigned_to=assigned_to,
        )
        self.deliverables.append(deliverable)
        self.updated_at = datetime.now(timezone.utc)
        return deliverable

    def get_deliverable(self, deliverable_id: str) -> Deliverable | None:
        """Get deliverable by ID"""
        for deliverable in self.deliverables:
            if deliverable.deliverable_id == deliverable_id:
                return deliverable
        return None

    def update_deliverable_status(
        self, deliverable_id: str, new_status: DeliverableStatus
    ) -> None:
        """Update deliverable status"""
        deliverable = self.get_deliverable(deliverable_id)
        if deliverable:
            deliverable.status = new_status
            if new_status == DeliverableStatus.COMPLETED:
                deliverable.completed_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    def get_completion_percentage(self) -> float:
        """Calculate project completion percentage based on deliverables"""
        if not self.deliverables:
            return 0.0

        completed = sum(
            1
            for d in self.deliverables
            if d.status in [DeliverableStatus.COMPLETED, DeliverableStatus.APPROVED]
        )
        return (completed / len(self.deliverables)) * 100

    def get_budget_spent_percentage(self) -> float:
        """Calculate budget spent percentage"""
        if not self.total_budget or self.total_budget == 0:
            return 0.0
        return (self.spent_budget / self.total_budget) * 100

    def add_budget_expense(self, amount: int) -> None:
        """Add expense to spent budget"""
        self.spent_budget += amount
        self.updated_at = datetime.now(timezone.utc)

    def get_remaining_budget(self) -> int:
        """Get remaining budget"""
        if not self.total_budget:
            return 0
        return self.total_budget - self.spent_budget

    def is_over_budget(self) -> bool:
        """Check if project is over budget"""
        if not self.total_budget:
            return False
        return self.spent_budget > self.total_budget

    def is_overdue(self) -> bool:
        """Check if project is overdue"""
        if not self.end_date:
            return False
        return datetime.now(timezone.utc) > self.end_date and self.status not in [
            ProjectStatus.COMPLETED,
            ProjectStatus.CANCELLED,
            ProjectStatus.ARCHIVED,
        ]

    def get_days_remaining(self) -> int | None:
        """Get days remaining until end date"""
        if not self.end_date:
            return None
        delta = self.end_date - datetime.now(timezone.utc)
        return max(0, delta.days)

    def assign_magister(self, magister_id: str) -> None:
        """Assign a Magister to this project"""
        if magister_id not in self.assigned_magisters:
            self.assigned_magisters.append(magister_id)
            self.updated_at = datetime.now(timezone.utc)

    def assign_agent(self, agent_id: str) -> None:
        """Assign an Agent to this project"""
        if agent_id not in self.assigned_agents:
            self.assigned_agents.append(agent_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this project"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "project_id": self.project_id,
            "client_id": self.client_id,
            "name": self.name,
            "project_type": self.project_type.value,
            "status": self.status.value,
            "description": self.description,
            "goals": self.goals,
            "target_metrics": self.target_metrics,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_months": self.duration_months,
            "total_budget": self.total_budget,
            "spent_budget": self.spent_budget,
            "budget_currency": self.budget_currency,
            "deliverables": [
                {
                    "deliverable_id": d.deliverable_id,
                    "name": d.name,
                    "description": d.description,
                    "status": d.status.value,
                    "due_date": d.due_date.isoformat() if d.due_date else None,
                    "completed_at": d.completed_at.isoformat() if d.completed_at else None,
                    "assigned_to": d.assigned_to,
                    "result": d.result,
                    "notes": d.notes,
                }
                for d in self.deliverables
            ],
            "assigned_magisters": self.assigned_magisters,
            "assigned_agents": self.assigned_agents,
            "tags": self.tags,
            "notes": self.notes,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Create Project from dictionary"""
        deliverables = [
            Deliverable(
                deliverable_id=d["deliverable_id"],
                name=d["name"],
                description=d["description"],
                status=DeliverableStatus(d["status"]),
                due_date=datetime.fromisoformat(d["due_date"]) if d.get("due_date") else None,
                completed_at=datetime.fromisoformat(d["completed_at"])
                if d.get("completed_at")
                else None,
                assigned_to=d.get("assigned_to"),
                result=d.get("result", {}),
                notes=d.get("notes"),
            )
            for d in data.get("deliverables", [])
        ]

        return cls(
            project_id=data["project_id"],
            client_id=data["client_id"],
            name=data["name"],
            project_type=ProjectType(data["project_type"]),
            status=ProjectStatus(data["status"]),
            description=data.get("description"),
            goals=data.get("goals", []),
            target_metrics=data.get("target_metrics", {}),
            start_date=datetime.fromisoformat(data["start_date"])
            if data.get("start_date")
            else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            duration_months=data.get("duration_months"),
            total_budget=data.get("total_budget"),
            spent_budget=data.get("spent_budget", 0),
            budget_currency=data.get("budget_currency", "RUB"),
            deliverables=deliverables,
            assigned_magisters=data.get("assigned_magisters", []),
            assigned_agents=data.get("assigned_agents", []),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            custom_fields=data.get("custom_fields", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            cancelled_at=datetime.fromisoformat(data["cancelled_at"])
            if data.get("cancelled_at")
            else None,
        )
