"""Tests for Obsidian vault integration"""

import pytest
from pathlib import Path
from meai.memory.obsidian import ObsidianVault


@pytest.mark.asyncio
async def test_vault_initialization(tmp_path):
    """Test vault initialization creates directory structure"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))

    await vault.initialize()

    assert vault_path.exists()
    assert vault_path.is_dir()


@pytest.mark.asyncio
async def test_create_agent_vault(tmp_path):
    """Test creating agent-specific vault directory"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))
    await vault.initialize()

    agent_id = "test-agent"
    agent_vault_path = await vault.create_agent_vault(agent_id)

    assert agent_vault_path.exists()
    assert agent_vault_path.is_dir()
    assert agent_vault_path.name == agent_id


@pytest.mark.asyncio
async def test_write_and_read_file(tmp_path):
    """Test writing and reading files"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))
    await vault.initialize()

    content = "# Test Note\n\nThis is a test."
    file_path = "test.md"

    await vault.write_file(file_path, content)
    read_content = await vault.read_file(file_path)

    assert read_content == content


@pytest.mark.asyncio
async def test_write_file_with_frontmatter(tmp_path):
    """Test writing file with YAML frontmatter"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))
    await vault.initialize()

    content = "# Test Note"
    metadata = {"title": "Test", "tags": ["test", "demo"]}
    file_path = "test.md"

    await vault.write_file(file_path, content, metadata=metadata)
    read_content = await vault.read_file(file_path)

    # Should contain frontmatter
    assert "---" in read_content
    assert "title: Test" in read_content
    assert "tags:" in read_content


@pytest.mark.asyncio
async def test_create_snapshot(tmp_path):
    """Test creating vault snapshot"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))
    await vault.initialize()

    # Create some files
    await vault.write_file("file1.md", "Content 1")
    await vault.write_file("file2.md", "Content 2")

    snapshot_name = "test-snapshot"
    snapshot_path = await vault.create_snapshot(snapshot_name)

    assert snapshot_path.exists()
    assert snapshot_path.is_dir()
    assert (snapshot_path / "file1.md").exists()
    assert (snapshot_path / "file2.md").exists()


@pytest.mark.asyncio
async def test_restore_snapshot(tmp_path):
    """Test restoring vault from snapshot"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))
    await vault.initialize()

    # Create files and snapshot
    await vault.write_file("file1.md", "Original content")
    snapshot_name = "test-snapshot"
    await vault.create_snapshot(snapshot_name)

    # Modify file
    await vault.write_file("file1.md", "Modified content")

    # Restore snapshot
    await vault.restore_snapshot(snapshot_name)

    # Should have original content
    content = await vault.read_file("file1.md")
    assert content == "Original content"


@pytest.mark.asyncio
async def test_file_locking(tmp_path):
    """Test file locking prevents concurrent writes"""
    vault_path = tmp_path / "vault"
    vault = ObsidianVault(str(vault_path))
    await vault.initialize()

    file_path = "locked.md"

    # First write should succeed
    await vault.write_file(file_path, "Content 1")

    # Concurrent writes should be serialized (no corruption)
    import asyncio

    async def write_task(content: str):
        await vault.write_file(file_path, content)

    # Run concurrent writes
    await asyncio.gather(
        write_task("Content A"),
        write_task("Content B"),
        write_task("Content C"),
    )

    # File should have one of the contents (not corrupted)
    final_content = await vault.read_file(file_path)
    assert final_content in ["Content A", "Content B", "Content C"]
