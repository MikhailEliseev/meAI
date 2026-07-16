"""Tests for System Registry"""

import pytest
from pathlib import Path
from meai.agents.system_registry import SystemRegistry, AgentInfo


@pytest.mark.asyncio
async def test_create_system_md(tmp_path):
    """Test creating SYSTEM.md file"""
    vault_path = tmp_path / "vault"
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()

    # Create SYSTEM.md
    await registry.create_system_md()

    # Verify file exists
    system_file = vault_path / "SYSTEM.md"
    assert system_file.exists()

    # Verify content
    content = system_file.read_text()
    assert "# AIM Agency System" in content
    assert "## Agents" in content


@pytest.mark.asyncio
async def test_register_agent(tmp_path):
    """Test registering agent in SYSTEM.md"""
    vault_path = tmp_path / "vault"
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()
    await registry.create_system_md()

    # Register agent
    await registry.register_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist",
        vault_path=str(vault_path / "seo-agent"),
    )

    # Verify agent in SYSTEM.md
    system_file = vault_path / "SYSTEM.md"
    content = system_file.read_text()
    assert "seo-agent" in content
    assert "SEO specialist" in content


@pytest.mark.asyncio
async def test_list_agents(tmp_path):
    """Test listing agents from SYSTEM.md"""
    vault_path = tmp_path / "vault"
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()
    await registry.create_system_md()

    # Register multiple agents
    await registry.register_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist",
        vault_path=str(vault_path / "seo-agent"),
    )
    await registry.register_agent(
        agent_id="content-agent",
        agent_type="subagent",
        department="content",
        role="Content writer",
        vault_path=str(vault_path / "content-agent"),
    )

    # List agents
    agents = await registry.list_agents()
    assert len(agents) == 2
    assert any(a.agent_id == "seo-agent" for a in agents)
    assert any(a.agent_id == "content-agent" for a in agents)


@pytest.mark.asyncio
async def test_remove_agent(tmp_path):
    """Test removing agent from SYSTEM.md"""
    vault_path = tmp_path / "vault"
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()
    await registry.create_system_md()

    # Register agent
    await registry.register_agent(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
        vault_path=str(vault_path / "test-agent"),
    )

    # Remove agent
    await registry.remove_agent("test-agent")

    # Verify agent removed
    agents = await registry.list_agents()
    assert len(agents) == 0

    # Verify SYSTEM.md updated
    system_file = vault_path / "SYSTEM.md"
    content = system_file.read_text()
    assert "test-agent" not in content


@pytest.mark.asyncio
async def test_parse_system_md(tmp_path):
    """Test parsing existing SYSTEM.md"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir(parents=True)

    # Create SYSTEM.md manually
    system_file = vault_path / "SYSTEM.md"
    system_file.write_text("""# AIM Agency System

## Agents

### seo-agent
- **Type:** subagent
- **Department:** seo
- **Role:** SEO specialist
- **Vault:** /vault/seo-agent

### content-agent
- **Type:** subagent
- **Department:** content
- **Role:** Content writer
- **Vault:** /vault/content-agent
""")

    # Parse SYSTEM.md
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()

    agents = await registry.list_agents()
    assert len(agents) == 2
    assert agents[0].agent_id == "seo-agent"
    assert agents[0].role == "SEO specialist"
    assert agents[1].agent_id == "content-agent"
    assert agents[1].role == "Content writer"


@pytest.mark.asyncio
async def test_hierarchy_tracking(tmp_path):
    """Test tracking agent hierarchy"""
    vault_path = tmp_path / "vault"
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()
    await registry.create_system_md()

    # Register operator
    await registry.register_agent(
        agent_id="operator",
        agent_type="operator",
        department="operations",
        role="Operations director",
        vault_path=str(vault_path / "operator"),
    )

    # Register subagents
    await registry.register_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist",
        vault_path=str(vault_path / "seo-agent"),
        parent_id="operator",
    )

    # List agents
    agents = await registry.list_agents()
    assert len(agents) == 2

    # Find subagent
    seo_agent = next(a for a in agents if a.agent_id == "seo-agent")
    assert seo_agent.parent_id == "operator"


@pytest.mark.asyncio
async def test_update_agent_metadata(tmp_path):
    """Test updating agent metadata in SYSTEM.md"""
    vault_path = tmp_path / "vault"
    registry = SystemRegistry(str(vault_path))
    await registry.initialize()
    await registry.create_system_md()

    # Register agent
    await registry.register_agent(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
        vault_path=str(vault_path / "test-agent"),
    )

    # Update agent
    await registry.update_agent(
        agent_id="test-agent",
        role="Senior Tester",
    )

    # Verify update
    agents = await registry.list_agents()
    agent = next(a for a in agents if a.agent_id == "test-agent")
    assert agent.role == "Senior Tester"
