"""Client Manager - Client and project management for AIM Agency

Handles CRUD operations for clients and projects, manages relationships,
and provides business logic for client lifecycle.
"""

import json
from typing import Any

from sqlalchemy import text

from meai.models.client import Client, ClientContact, ClientStatus, SubscriptionTier
from meai.models.project import Project, ProjectStatus, ProjectType
from meai.storage.database import Database


class ClientManager:
    """Manages clients and projects for the agency

    Responsibilities:
    - Client CRUD operations
    - Project CRUD operations
    - Client-project relationships
    - Subscription tier management
    - SLA tracking
    """

    def __init__(self, database_url: str):
        """Initialize Client Manager

        Args:
            database_url: Database connection URL
        """
        self.db = Database(database_url)

    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown database connection"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create clients and projects tables"""
        async with self.db.session() as session:
            # Clients table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS clients (
                    client_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """)
            )

            # Projects table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (client_id) REFERENCES clients(client_id)
                )
                """)
            )

            # Indexes for performance
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id)")
            )

            await session.commit()

    # ==================== Client Operations ====================

    async def create_client(
        self,
        name: str,
        industry: str,
        subscription_tier: SubscriptionTier,
        primary_contact: ClientContact,
        **kwargs: Any,
    ) -> Client:
        """Create a new client

        Args:
            name: Company name
            industry: Industry/specialty
            subscription_tier: Subscription tier
            primary_contact: Primary contact person
            **kwargs: Additional client fields

        Returns:
            Created Client instance
        """
        client = Client.create(
            name=name,
            industry=industry,
            subscription_tier=subscription_tier,
            primary_contact=primary_contact,
            **kwargs,
        )

        # Save to database
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO clients (client_id, data, created_at, updated_at)
                VALUES (:client_id, :data, :created_at, :updated_at)
                """),
                {
                    "client_id": client.client_id,
                    "data": json.dumps(client.to_dict()),
                    "created_at": client.created_at,
                    "updated_at": client.updated_at,
                },
            )
            await session.commit()

        return client

    async def get_client(self, client_id: str) -> Client | None:
        """Get client by ID

        Args:
            client_id: Client ID

        Returns:
            Client instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("SELECT data FROM clients WHERE client_id = :client_id"),
                {"client_id": client_id},
            )
            row = result.fetchone()

        if not row:
            return None

        data = json.loads(row[0])
        return Client.from_dict(data)

    async def update_client(self, client: Client) -> None:
        """Update client in database

        Args:
            client: Client instance to update
        """
        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE clients
                SET data = :data, updated_at = :updated_at
                WHERE client_id = :client_id
                """),
                {
                    "client_id": client.client_id,
                    "data": json.dumps(client.to_dict()),
                    "updated_at": client.updated_at,
                },
            )
            await session.commit()

    async def delete_client(self, client_id: str) -> None:
        """Delete client from database

        Args:
            client_id: Client ID
        """
        async with self.db.session() as session:
            # Delete all projects first
            await session.execute(
                text("DELETE FROM projects WHERE client_id = :client_id"),
                {"client_id": client_id},
            )

            # Delete client
            await session.execute(
                text("DELETE FROM clients WHERE client_id = :client_id"),
                {"client_id": client_id},
            )
            await session.commit()

    async def list_clients(
        self,
        status: ClientStatus | None = None,
        subscription_tier: SubscriptionTier | None = None,
        limit: int = 100,
    ) -> list[Client]:
        """List clients with optional filters

        Args:
            status: Filter by status
            subscription_tier: Filter by subscription tier
            limit: Maximum number of clients to return

        Returns:
            List of Client instances
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("SELECT data FROM clients ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit},
            )
            rows = result.fetchall()

        clients = [Client.from_dict(json.loads(row[0])) for row in rows]

        # Apply filters
        if status:
            clients = [c for c in clients if c.status == status]
        if subscription_tier:
            clients = [c for c in clients if c.subscription_tier == subscription_tier]

        return clients

    # ==================== Project Operations ====================

    async def create_project(
        self,
        client_id: str,
        name: str,
        project_type: ProjectType,
        **kwargs: Any,
    ) -> Project:
        """Create a new project

        Args:
            client_id: Client ID
            name: Project name
            project_type: Type of project
            **kwargs: Additional project fields

        Returns:
            Created Project instance

        Raises:
            ValueError: If client doesn't exist or can't add more projects
        """
        # Check if client exists
        client = await self.get_client(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        # Check if client can add more projects
        if not client.can_add_project():
            max_projects = client.get_max_projects()
            raise ValueError(
                f"Client has reached maximum projects ({max_projects}) for {client.subscription_tier.value} tier"
            )

        # Create project
        project = Project.create(
            client_id=client_id,
            name=name,
            project_type=project_type,
            **kwargs,
        )

        # Save to database
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO projects (project_id, client_id, data, created_at, updated_at)
                VALUES (:project_id, :client_id, :data, :created_at, :updated_at)
                """),
                {
                    "project_id": project.project_id,
                    "client_id": project.client_id,
                    "data": json.dumps(project.to_dict()),
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                },
            )
            await session.commit()

        # Add project to client
        client.add_project(project.project_id)
        await self.update_client(client)

        return project

    async def get_project(self, project_id: str) -> Project | None:
        """Get project by ID

        Args:
            project_id: Project ID

        Returns:
            Project instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("SELECT data FROM projects WHERE project_id = :project_id"),
                {"project_id": project_id},
            )
            row = result.fetchone()

        if not row:
            return None

        data = json.loads(row[0])
        return Project.from_dict(data)

    async def update_project(self, project: Project) -> None:
        """Update project in database

        Args:
            project: Project instance to update
        """
        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE projects
                SET data = :data, updated_at = :updated_at
                WHERE project_id = :project_id
                """),
                {
                    "project_id": project.project_id,
                    "data": json.dumps(project.to_dict()),
                    "updated_at": project.updated_at,
                },
            )
            await session.commit()

    async def delete_project(self, project_id: str) -> None:
        """Delete project from database

        Args:
            project_id: Project ID
        """
        # Get project to find client
        project = await self.get_project(project_id)
        if project:
            # Remove from client
            client = await self.get_client(project.client_id)
            if client:
                client.remove_project(project_id)
                await self.update_client(client)

        # Delete project
        async with self.db.session() as session:
            await session.execute(
                text("DELETE FROM projects WHERE project_id = :project_id"),
                {"project_id": project_id},
            )
            await session.commit()

    async def list_projects(
        self,
        client_id: str | None = None,
        status: ProjectStatus | None = None,
        project_type: ProjectType | None = None,
        limit: int = 100,
    ) -> list[Project]:
        """List projects with optional filters

        Args:
            client_id: Filter by client ID
            status: Filter by status
            project_type: Filter by project type
            limit: Maximum number of projects to return

        Returns:
            List of Project instances
        """
        async with self.db.session() as session:
            if client_id:
                result = await session.execute(
                    text("""
                    SELECT data FROM projects
                    WHERE client_id = :client_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """),
                    {"client_id": client_id, "limit": limit},
                )
            else:
                result = await session.execute(
                    text("SELECT data FROM projects ORDER BY created_at DESC LIMIT :limit"),
                    {"limit": limit},
                )
            rows = result.fetchall()

        projects = [Project.from_dict(json.loads(row[0])) for row in rows]

        # Apply filters
        if status:
            projects = [p for p in projects if p.status == status]
        if project_type:
            projects = [p for p in projects if p.project_type == project_type]

        return projects

    async def get_client_projects(self, client_id: str) -> list[Project]:
        """Get all projects for a client

        Args:
            client_id: Client ID

        Returns:
            List of Project instances
        """
        return await self.list_projects(client_id=client_id)

    # ==================== Business Logic ====================

    async def onboard_client(self, client_id: str) -> None:
        """Mark client as onboarded and activate

        Args:
            client_id: Client ID
        """
        client = await self.get_client(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        client.update_status(ClientStatus.ACTIVE)
        await self.update_client(client)

    async def get_client_stats(self, client_id: str) -> dict[str, Any]:
        """Get statistics for a client

        Args:
            client_id: Client ID

        Returns:
            Dictionary with client statistics
        """
        client = await self.get_client(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        projects = await self.get_client_projects(client_id)

        active_projects = [p for p in projects if p.status == ProjectStatus.ACTIVE]
        completed_projects = [p for p in projects if p.status == ProjectStatus.COMPLETED]

        total_budget = sum(p.total_budget or 0 for p in projects)
        spent_budget = sum(p.spent_budget for p in projects)

        return {
            "client_id": client_id,
            "client_name": client.name,
            "subscription_tier": client.subscription_tier.value,
            "status": client.status.value,
            "total_projects": len(projects),
            "active_projects": len(active_projects),
            "completed_projects": len(completed_projects),
            "total_budget": total_budget,
            "spent_budget": spent_budget,
            "remaining_budget": total_budget - spent_budget,
            "sla_response_time_hours": client.get_sla_response_time_hours(),
            "max_projects": client.get_max_projects(),
            "can_add_project": client.can_add_project(),
        }
