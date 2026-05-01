"""System Registry for managing SYSTEM.md"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re
import structlog

logger = structlog.get_logger()


@dataclass
class AgentInfo:
    """Agent information"""

    agent_id: str
    agent_type: str
    department: str
    role: str
    vault_path: str
    parent_id: Optional[str] = None


class SystemRegistry:
    """Manage SYSTEM.md agent registry"""

    def __init__(self, vault_path: str):
        """Initialize System Registry

        Args:
            vault_path: Path to Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.system_file = self.vault_path / "SYSTEM.md"

    async def initialize(self) -> None:
        """Initialize vault directory"""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        logger.info("system_registry.initialized", path=str(self.vault_path))

    async def create_system_md(self) -> None:
        """Create SYSTEM.md file"""
        content = """# AIM Agency System

**Created:** System initialization
**Managed by:** meAI Architect

---

## Agents

(Agents will be registered here)

---

## Communication

- **Event Bus:** Async message queue with P0-P3 priorities
- **Event Store:** Immutable event log for audit trail

---

## Safety

- Loop detection: Max depth 5
- Timeouts: 5 minutes default
- Context monitoring: 40% rule
- Graceful shutdown: SIGINT/SIGTERM handlers

---

**System Status:** Active
"""
        self.system_file.write_text(content)
        logger.info("system_registry.system_md_created", path=str(self.system_file))

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        department: str,
        role: str,
        vault_path: str,
        parent_id: Optional[str] = None,
    ) -> None:
        """Register agent in SYSTEM.md

        Args:
            agent_id: Agent identifier
            agent_type: Type of agent (e.g., "operator", "subagent")
            department: Department (e.g., "seo", "content")
            role: Agent role description
            vault_path: Path to agent's vault
            parent_id: Optional parent agent ID for hierarchy
        """
        if not self.system_file.exists():
            await self.create_system_md()

        content = self.system_file.read_text()

        # Create agent entry
        agent_entry = f"""
### {agent_id}
- **Type:** {agent_type}
- **Department:** {department}
- **Role:** {role}
- **Vault:** {vault_path}
"""
        if parent_id:
            agent_entry += f"- **Parent:** {parent_id}\n"

        # Insert after "## Agents" section
        if "(Agents will be registered here)" in content:
            # First agent - replace placeholder
            content = content.replace(
                "(Agents will be registered here)",
                agent_entry.strip(),
            )
        elif "## Agents" in content:
            # Already has agents - find the section and append
            # Find the position after "## Agents\n"
            agents_pos = content.find("## Agents\n")
            if agents_pos != -1:
                # Find the next section (starts with ##) or end of file
                next_section_pos = content.find("\n##", agents_pos + len("## Agents\n"))
                if next_section_pos == -1:
                    next_section_pos = len(content)

                # Insert before the next section
                content = (
                    content[:next_section_pos]
                    + agent_entry
                    + content[next_section_pos:]
                )
        else:
            content += f"\n## Agents\n{agent_entry}"

        self.system_file.write_text(content)
        logger.info("system_registry.agent_registered", agent_id=agent_id)

    async def remove_agent(self, agent_id: str) -> None:
        """Remove agent from SYSTEM.md

        Args:
            agent_id: Agent identifier
        """
        if not self.system_file.exists():
            return

        content = self.system_file.read_text()

        # Remove agent section
        pattern = rf"### {re.escape(agent_id)}\n(?:- \*\*.*\n)*"
        content = re.sub(pattern, "", content)

        self.system_file.write_text(content)
        logger.info("system_registry.agent_removed", agent_id=agent_id)

    async def list_agents(self) -> list[AgentInfo]:
        """List all agents from SYSTEM.md

        Returns:
            List of AgentInfo objects
        """
        if not self.system_file.exists():
            return []

        content = self.system_file.read_text()
        agents = []

        # Parse agent sections
        pattern = r"### ([^\n]+)\n- \*\*Type:\*\* ([^\n]+)\n- \*\*Department:\*\* ([^\n]+)\n- \*\*Role:\*\* ([^\n]+)\n- \*\*Vault:\*\* ([^\n]+)(?:\n- \*\*Parent:\*\* ([^\n]+))?"
        matches = re.findall(pattern, content)

        for match in matches:
            agent_id, agent_type, department, role, vault_path, parent_id = match
            agents.append(
                AgentInfo(
                    agent_id=agent_id.strip(),
                    agent_type=agent_type.strip(),
                    department=department.strip(),
                    role=role.strip(),
                    vault_path=vault_path.strip(),
                    parent_id=parent_id.strip() if parent_id else None,
                )
            )

        return agents

    async def update_agent(
        self,
        agent_id: str,
        role: Optional[str] = None,
        vault_path: Optional[str] = None,
    ) -> None:
        """Update agent metadata in SYSTEM.md

        Args:
            agent_id: Agent identifier
            role: New role (optional)
            vault_path: New vault path (optional)
        """
        if not self.system_file.exists():
            raise ValueError(f"SYSTEM.md not found")

        content = self.system_file.read_text()

        # Find agent section
        pattern = rf"(### {re.escape(agent_id)}\n(?:- \*\*.*\n)*)"
        match = re.search(pattern, content)

        if not match:
            raise ValueError(f"Agent {agent_id} not found in SYSTEM.md")

        agent_section = match.group(1)
        updated_section = agent_section

        # Update role if provided
        if role:
            updated_section = re.sub(
                r"- \*\*Role:\*\* [^\n]+\n",
                f"- **Role:** {role}\n",
                updated_section,
            )

        # Update vault path if provided
        if vault_path:
            updated_section = re.sub(
                r"- \*\*Vault:\*\* [^\n]+\n",
                f"- **Vault:** {vault_path}\n",
                updated_section,
            )

        content = content.replace(agent_section, updated_section)
        self.system_file.write_text(content)

        logger.info("system_registry.agent_updated", agent_id=agent_id)
