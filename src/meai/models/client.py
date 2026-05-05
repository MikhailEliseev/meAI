"""Client Model - Customer management for AIM Agency

Manages client information, subscription tiers, and client lifecycle.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class SubscriptionTier(str, Enum):
    """Client subscription tiers"""

    BASIC = "basic"  # 1 project, standard SLA, basic support
    PRO = "pro"  # 3 projects, priority SLA, priority support
    ENTERPRISE = "enterprise"  # unlimited projects, premium SLA, dedicated manager


class ClientStatus(str, Enum):
    """Client lifecycle status"""

    LEAD = "lead"  # Potential client, not yet onboarded
    ONBOARDING = "onboarding"  # In onboarding process
    ACTIVE = "active"  # Active client with projects
    PAUSED = "paused"  # Temporarily paused (payment issues, vacation, etc.)
    CHURNED = "churned"  # Left the agency
    ARCHIVED = "archived"  # Historical record


@dataclass
class ClientContact:
    """Client contact information"""

    name: str
    role: str  # e.g., "CEO", "Marketing Director", "Owner"
    email: str
    phone: str | None = None
    telegram: str | None = None
    is_primary: bool = False


@dataclass
class Client:
    """Client entity

    Represents a customer of the AIM Agency.
    """

    client_id: str
    name: str  # Company name (e.g., "Стоматология Смайл")
    industry: str  # e.g., "dentistry", "dermatology", "plastic_surgery"
    subscription_tier: SubscriptionTier
    status: ClientStatus

    # Contact information
    contacts: list[ClientContact]
    website: str | None = None
    location: str | None = None  # e.g., "Москва, Арбат"

    # Business information
    target_audience: str | None = None  # e.g., "25-45 лет, средний+ доход"
    competitors: list[str] = field(default_factory=list)
    unique_selling_points: list[str] = field(default_factory=list)

    # Financial
    monthly_budget: int | None = None  # RUB
    payment_method: str | None = None  # e.g., "invoice", "card", "wire_transfer"

    # Metadata
    tags: list[str] = field(default_factory=list)  # e.g., ["premium", "high-priority"]
    notes: str | None = None
    custom_fields: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    onboarded_at: datetime | None = None
    churned_at: datetime | None = None

    # Relationships
    assigned_manager: str | None = None  # User ID of account manager
    projects: list[str] = field(default_factory=list)  # Project IDs

    @classmethod
    def create(
        cls,
        name: str,
        industry: str,
        subscription_tier: SubscriptionTier,
        primary_contact: ClientContact,
        **kwargs: Any,
    ) -> "Client":
        """Create a new client

        Args:
            name: Company name
            industry: Industry/specialty
            subscription_tier: Subscription tier
            primary_contact: Primary contact person
            **kwargs: Additional client fields

        Returns:
            New Client instance
        """
        client_id = f"client-{uuid4().hex[:8]}"

        return cls(
            client_id=client_id,
            name=name,
            industry=industry,
            subscription_tier=subscription_tier,
            status=ClientStatus.LEAD,
            contacts=[primary_contact],
            **kwargs,
        )

    def get_primary_contact(self) -> ClientContact | None:
        """Get primary contact person"""
        for contact in self.contacts:
            if contact.is_primary:
                return contact
        # If no primary set, return first contact
        return self.contacts[0] if self.contacts else None

    def add_contact(self, contact: ClientContact) -> None:
        """Add a new contact person"""
        self.contacts.append(contact)
        self.updated_at = datetime.now(timezone.utc)

    def update_status(self, new_status: ClientStatus) -> None:
        """Update client status with timestamp tracking"""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        if new_status == ClientStatus.ACTIVE and not self.onboarded_at:
            self.onboarded_at = datetime.now(timezone.utc)
        elif new_status == ClientStatus.CHURNED and not self.churned_at:
            self.churned_at = datetime.now(timezone.utc)

    def add_project(self, project_id: str) -> None:
        """Add a project to this client"""
        if project_id not in self.projects:
            self.projects.append(project_id)
            self.updated_at = datetime.now(timezone.utc)

    def remove_project(self, project_id: str) -> None:
        """Remove a project from this client"""
        if project_id in self.projects:
            self.projects.remove(project_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this client"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this client"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc)

    def get_max_projects(self) -> int | None:
        """Get maximum number of projects allowed for this tier

        Returns:
            Max projects, or None for unlimited (Enterprise)
        """
        limits = {
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PRO: 3,
            SubscriptionTier.ENTERPRISE: None,  # Unlimited
        }
        return limits.get(self.subscription_tier)

    def can_add_project(self) -> bool:
        """Check if client can add another project"""
        max_projects = self.get_max_projects()
        if max_projects is None:  # Unlimited
            return True
        return len(self.projects) < max_projects

    def get_sla_response_time_hours(self) -> int:
        """Get SLA response time in hours for this tier"""
        sla_times = {
            SubscriptionTier.BASIC: 24,
            SubscriptionTier.PRO: 12,
            SubscriptionTier.ENTERPRISE: 4,
        }
        return sla_times.get(self.subscription_tier, 24)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "client_id": self.client_id,
            "name": self.name,
            "industry": self.industry,
            "subscription_tier": self.subscription_tier.value,
            "status": self.status.value,
            "contacts": [
                {
                    "name": c.name,
                    "role": c.role,
                    "email": c.email,
                    "phone": c.phone,
                    "telegram": c.telegram,
                    "is_primary": c.is_primary,
                }
                for c in self.contacts
            ],
            "website": self.website,
            "location": self.location,
            "target_audience": self.target_audience,
            "competitors": self.competitors,
            "unique_selling_points": self.unique_selling_points,
            "monthly_budget": self.monthly_budget,
            "payment_method": self.payment_method,
            "tags": self.tags,
            "notes": self.notes,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "onboarded_at": self.onboarded_at.isoformat() if self.onboarded_at else None,
            "churned_at": self.churned_at.isoformat() if self.churned_at else None,
            "assigned_manager": self.assigned_manager,
            "projects": self.projects,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Client":
        """Create Client from dictionary"""
        contacts = [
            ClientContact(
                name=c["name"],
                role=c["role"],
                email=c["email"],
                phone=c.get("phone"),
                telegram=c.get("telegram"),
                is_primary=c.get("is_primary", False),
            )
            for c in data.get("contacts", [])
        ]

        return cls(
            client_id=data["client_id"],
            name=data["name"],
            industry=data["industry"],
            subscription_tier=SubscriptionTier(data["subscription_tier"]),
            status=ClientStatus(data["status"]),
            contacts=contacts,
            website=data.get("website"),
            location=data.get("location"),
            target_audience=data.get("target_audience"),
            competitors=data.get("competitors", []),
            unique_selling_points=data.get("unique_selling_points", []),
            monthly_budget=data.get("monthly_budget"),
            payment_method=data.get("payment_method"),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            custom_fields=data.get("custom_fields", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            onboarded_at=datetime.fromisoformat(data["onboarded_at"])
            if data.get("onboarded_at")
            else None,
            churned_at=datetime.fromisoformat(data["churned_at"])
            if data.get("churned_at")
            else None,
            assigned_manager=data.get("assigned_manager"),
            projects=data.get("projects", []),
        )
