"""Tests for Rollback Manager"""

import pytest
from meai.core.rollback import RollbackManager
from meai.memory.obsidian import ObsidianVault
from meai.events.event_store import EventStore


@pytest.mark.asyncio
async def test_rollback_workflow(tmp_path):
    """Test full rollback workflow"""
    db_url = "sqlite+aiosqlite:///:memory:"
    event_store = EventStore(db_url)
    await event_store.initialize()

    vault = ObsidianVault(str(tmp_path))
    await vault.initialize()

    rollback_mgr = RollbackManager(vault, event_store)

    # Create initial state
    await vault.write_file("test.md", "version 1")

    # Create checkpoint
    checkpoint_id = await rollback_mgr.create_checkpoint("checkpoint-1")

    # Make changes
    await vault.write_file("test.md", "version 2")

    # Rollback
    await rollback_mgr.rollback_to_checkpoint(checkpoint_id)

    # Verify restored
    content = await vault.read_file("test.md")
    assert content == "version 1"

    await event_store.close()


@pytest.mark.asyncio
async def test_create_checkpoint(tmp_path):
    """Test creating checkpoint"""
    db_url = "sqlite+aiosqlite:///:memory:"
    event_store = EventStore(db_url)
    await event_store.initialize()

    vault = ObsidianVault(str(tmp_path))
    await vault.initialize()

    rollback_mgr = RollbackManager(vault, event_store)

    # Create checkpoint
    checkpoint_id = await rollback_mgr.create_checkpoint("test-checkpoint")

    assert checkpoint_id == "test-checkpoint"

    # Verify checkpoint event was recorded
    events = await event_store.get_events(event_type="checkpoint_created")
    assert len(events) > 0
    assert events[0].payload["name"] == "test-checkpoint"

    await event_store.close()


@pytest.mark.asyncio
async def test_list_checkpoints(tmp_path):
    """Test listing checkpoints"""
    db_url = "sqlite+aiosqlite:///:memory:"
    event_store = EventStore(db_url)
    await event_store.initialize()

    vault = ObsidianVault(str(tmp_path))
    await vault.initialize()

    rollback_mgr = RollbackManager(vault, event_store)

    # Create multiple checkpoints
    await rollback_mgr.create_checkpoint("checkpoint-1")
    await rollback_mgr.create_checkpoint("checkpoint-2")
    await rollback_mgr.create_checkpoint("checkpoint-3")

    # List checkpoints
    checkpoints = await rollback_mgr.list_checkpoints()

    assert len(checkpoints) == 3
    assert checkpoints[0]["name"] == "checkpoint-1"
    assert checkpoints[1]["name"] == "checkpoint-2"
    assert checkpoints[2]["name"] == "checkpoint-3"

    await event_store.close()


@pytest.mark.asyncio
async def test_rollback_to_nonexistent_checkpoint(tmp_path):
    """Test rollback to nonexistent checkpoint raises error"""
    db_url = "sqlite+aiosqlite:///:memory:"
    event_store = EventStore(db_url)
    await event_store.initialize()

    vault = ObsidianVault(str(tmp_path))
    await vault.initialize()

    rollback_mgr = RollbackManager(vault, event_store)

    # Try to rollback to nonexistent checkpoint
    with pytest.raises(ValueError, match="Checkpoint not found"):
        await rollback_mgr.rollback_to_checkpoint("nonexistent")

    await event_store.close()


@pytest.mark.asyncio
async def test_multiple_rollbacks(tmp_path):
    """Test multiple rollbacks in sequence"""
    db_url = "sqlite+aiosqlite:///:memory:"
    event_store = EventStore(db_url)
    await event_store.initialize()

    vault = ObsidianVault(str(tmp_path))
    await vault.initialize()

    rollback_mgr = RollbackManager(vault, event_store)

    # Version 1
    await vault.write_file("test.md", "version 1")
    checkpoint1 = await rollback_mgr.create_checkpoint("checkpoint-1")

    # Version 2
    await vault.write_file("test.md", "version 2")
    checkpoint2 = await rollback_mgr.create_checkpoint("checkpoint-2")

    # Version 3
    await vault.write_file("test.md", "version 3")

    # Rollback to checkpoint 2
    await rollback_mgr.rollback_to_checkpoint(checkpoint2)
    content = await vault.read_file("test.md")
    assert content == "version 2"

    # Rollback to checkpoint 1
    await rollback_mgr.rollback_to_checkpoint(checkpoint1)
    content = await vault.read_file("test.md")
    assert content == "version 1"

    await event_store.close()
