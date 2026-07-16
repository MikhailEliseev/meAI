"""Tests for Agent Factory"""

import pytest
from pathlib import Path
from meai.agents.factory import AgentFactory, AgentMetadata


@pytest.mark.asyncio
async def test_create_agent(tmp_path):
    """Test creating agent with vault and metadata"""
    vault_path = tmp_path / "vault"
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    factory = AgentFactory(vault_path=str(vault_path), database_url=db_url)
    await factory.initialize()

    # Create agent
    agent = await factory.create_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist",
    )

    assert agent is not None
    assert agent.agent_id == "seo-agent"
    assert agent.agent_type == "subagent"
    assert agent.department == "seo"
    assert agent.role == "SEO specialist"
    assert agent.vault_path is not None

    await factory.close()


@pytest.mark.asyncio
async def test_agent_vault_initialization(tmp_path):
    """Test agent vault is created"""
    vault_path = tmp_path / "vault"
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    factory = AgentFactory(vault_path=str(vault_path), database_url=db_url)
    await factory.initialize()

    agent = await factory.create_agent(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
    )

    # Verify vault directory exists
    agent_vault = Path(agent.vault_path)
    assert agent_vault.exists()
    assert agent_vault.is_dir()
    assert agent_vault.name == "test-agent"

    await factory.close()


@pytest.mark.asyncio
async def test_agent_metadata_storage(tmp_path):
    """Test agent metadata is stored in database"""
    vault_path = tmp_path / "vault"
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    factory = AgentFactory(vault_path=str(vault_path), database_url=db_url)
    await factory.initialize()

    # Create agent
    await factory.create_agent(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
    )

    # Retrieve agent metadata
    agent = await factory.get_agent("test-agent")
    assert agent is not None
    assert agent.agent_id == "test-agent"
    assert agent.agent_type == "subagent"
    assert agent.department == "test"

    await factory.close()


@pytest.mark.asyncio
async def test_list_agents(tmp_path):
    """Test listing all agents"""
    vault_path = tmp_path / "vault"
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    factory = AgentFactory(vault_path=str(vault_path), database_url=db_url)
    await factory.initialize()

    # Create multiple agents
    await factory.create_agent(
        agent_id="agent-1", agent_type="subagent", department="seo", role="SEO"
    )
    await factory.create_agent(
        agent_id="agent-2", agent_type="subagent", department="content", role="Writer"
    )
    await factory.create_agent(
        agent_id="agent-3", agent_type="subagent", department="ads", role="Ads Manager"
    )

    # List all agents
    agents = await factory.list_agents()
    assert len(agents) == 3
    assert any(a.agent_id == "agent-1" for a in agents)
    assert any(a.agent_id == "agent-2" for a in agents)
    assert any(a.agent_id == "agent-3" for a in agents)

    await factory.close()


@pytest.mark.asyncio
async def test_delete_agent(tmp_path):
    """Test deleting agent"""
    vault_path = tmp_path / "vault"
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    factory = AgentFactory(vault_path=str(vault_path), database_url=db_url)
    await factory.initialize()

    # Create agent
    agent = await factory.create_agent(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
    )

    # Delete agent
    await factory.delete_agent("test-agent")

    # Verify agent is deleted
    deleted_agent = await factory.get_agent("test-agent")
    assert deleted_agent is None

    # Verify vault still exists (not deleted by factory)
    agent_vault = Path(agent.vault_path)
    assert agent_vault.exists()  # Vault preserved for safety

    await factory.close()


@pytest.mark.asyncio
async def test_duplicate_agent_id(tmp_path):
    """Test creating agent with duplicate ID fails"""
    vault_path = tmp_path / "vault"
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    factory = AgentFactory(vault_path=str(vault_path), database_url=db_url)
    await factory.initialize()

    # Create first agent
    await factory.create_agent(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
    )

    # Try to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        await factory.create_agent(
            agent_id="test-agent",
            agent_type="subagent",
            department="test",
            role="Tester",
        )

    await factory.close()
