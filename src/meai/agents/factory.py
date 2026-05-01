"""Agent Factory for creating and managing agents"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from meai.memory.obsidian import ObsidianVault


@dataclass
class AgentMetadata:
    """Agent metadata"""

    agent_id: str
    agent_type: str
    department: str
    role: str
    vault_path: str
    created_at: str
    updated_at: str


class AgentFactory:
    """Factory for creating and managing agents"""

    def __init__(self, vault_path: str, database_url: str):
        """Initialize Agent Factory

        Args:
            vault_path: Path to Obsidian vault root
            database_url: SQLAlchemy database URL
        """
        self.vault_path = Path(vault_path)
        self.database_url = database_url
        self._engine: AsyncEngine | None = None
        self._vault: ObsidianVault | None = None

    async def initialize(self) -> None:
        """Initialize database and vault"""
        # Initialize database
        self._engine = create_async_engine(self.database_url, echo=False)

        async with self._engine.begin() as conn:
            # Create agents table
            await conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_type TEXT NOT NULL,
                    department TEXT NOT NULL,
                    role TEXT NOT NULL,
                    vault_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type)")
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_agents_department ON agents(department)"
                )
            )

        # Initialize vault
        self._vault = ObsidianVault(str(self.vault_path))
        await self._vault.initialize()

    async def close(self) -> None:
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None

    async def create_agent(
        self,
        agent_id: str,
        agent_type: str,
        department: str,
        role: str,
    ) -> AgentMetadata:
        """Create new agent with vault and metadata

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (e.g., "subagent", "operator")
            department: Department (e.g., "seo", "content", "ads")
            role: Agent role description

        Returns:
            Agent metadata

        Raises:
            ValueError: If agent already exists
        """
        if not self._engine or not self._vault:
            raise RuntimeError("AgentFactory not initialized")

        # Check if agent already exists
        existing = await self.get_agent(agent_id)
        if existing:
            raise ValueError(f"Agent {agent_id} already exists")

        # Create agent vault
        agent_vault_path = await self._vault.create_agent_vault(agent_id)

        # Store agent metadata
        now = datetime.now(timezone.utc).isoformat()

        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                INSERT INTO agents (
                    agent_id, agent_type, department, role,
                    vault_path, created_at, updated_at
                ) VALUES (
                    :agent_id, :agent_type, :department, :role,
                    :vault_path, :created_at, :updated_at
                )
            """
                ),
                {
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "department": department,
                    "role": role,
                    "vault_path": str(agent_vault_path),
                    "created_at": now,
                    "updated_at": now,
                },
            )

        return AgentMetadata(
            agent_id=agent_id,
            agent_type=agent_type,
            department=department,
            role=role,
            vault_path=str(agent_vault_path),
            created_at=now,
            updated_at=now,
        )

    async def get_agent(self, agent_id: str) -> AgentMetadata | None:
        """Get agent metadata

        Args:
            agent_id: Agent identifier

        Returns:
            Agent metadata or None if not found
        """
        if not self._engine:
            raise RuntimeError("AgentFactory not initialized")

        async with self._engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM agents WHERE agent_id = :agent_id"),
                {"agent_id": agent_id},
            )
            row = result.fetchone()

        if not row:
            return None

        return AgentMetadata(
            agent_id=row[0],
            agent_type=row[1],
            department=row[2],
            role=row[3],
            vault_path=row[4],
            created_at=row[5],
            updated_at=row[6],
        )

    async def list_agents(
        self,
        agent_type: str | None = None,
        department: str | None = None,
    ) -> list[AgentMetadata]:
        """List all agents with optional filters

        Args:
            agent_type: Filter by agent type
            department: Filter by department

        Returns:
            List of agent metadata
        """
        if not self._engine:
            raise RuntimeError("AgentFactory not initialized")

        # Build query
        query = "SELECT * FROM agents WHERE 1=1"
        params: dict[str, str] = {}

        if agent_type:
            query += " AND agent_type = :agent_type"
            params["agent_type"] = agent_type

        if department:
            query += " AND department = :department"
            params["department"] = department

        query += " ORDER BY created_at ASC"

        # Execute query
        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params)
            rows = result.fetchall()

        # Convert to AgentMetadata objects
        agents = []
        for row in rows:
            agents.append(
                AgentMetadata(
                    agent_id=row[0],
                    agent_type=row[1],
                    department=row[2],
                    role=row[3],
                    vault_path=row[4],
                    created_at=row[5],
                    updated_at=row[6],
                )
            )

        return agents

    async def delete_agent(self, agent_id: str) -> None:
        """Delete agent metadata (vault is preserved)

        Args:
            agent_id: Agent identifier
        """
        if not self._engine:
            raise RuntimeError("AgentFactory not initialized")

        async with self._engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM agents WHERE agent_id = :agent_id"),
                {"agent_id": agent_id},
            )
