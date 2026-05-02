# Rollback Manager API Reference

> Snapshot + event replay for recovery

## Overview

**Rollback Manager** — компонент для отката системы к предыдущему состоянию. Использует комбинацию snapshot'ов Obsidian vault и event replay для полного восстановления.

## Class: `RollbackManager`

### Constructor

```python
from meai.core.rollback import RollbackManager
from meai.memory.obsidian import ObsidianVault
from meai.events.event_store import EventStore

vault = ObsidianVault("./obsidian")
await vault.initialize()

event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
await event_store.initialize()

rollback_mgr = RollbackManager(vault, event_store)
```

**Parameters:**
- `vault` (ObsidianVault) — Vault for snapshots
- `event_store` (EventStore) — Event store for replay

---

## Methods

### `create_checkpoint(name: str) -> str`

Create checkpoint with vault snapshot and event marker.

**Parameters:**
- `name` (str) — Checkpoint name (unique identifier)

**Returns:**
- `str` — Checkpoint ID

**Example:**

```python
# Before making risky changes
checkpoint_id = await rollback_mgr.create_checkpoint("before-migration")

print(f"Checkpoint created: {checkpoint_id}")
```

**What happens:**
1. Creates vault snapshot (copies all files)
2. Records checkpoint event in event store
3. Returns checkpoint ID

---

### `rollback_to_checkpoint(checkpoint_id: str) -> None`

Rollback to checkpoint.

**Parameters:**
- `checkpoint_id` (str) — Checkpoint ID to rollback to

**Returns:**
- None

**Raises:**
- `ValueError` — If checkpoint not found

**Example:**

```python
# Make changes
await vault.write_file("agent.md", "new content")

# Something went wrong, rollback
await rollback_mgr.rollback_to_checkpoint("before-migration")

# Vault restored to checkpoint state
content = await vault.read_file("agent.md")
# content == original content before changes
```

**What happens:**
1. Finds checkpoint event in event store
2. Restores vault from snapshot
3. Replays events after checkpoint (if any)

---

### `list_checkpoints() -> list[dict]`

List all available checkpoints.

**Parameters:**
- None

**Returns:**
- `list[dict]` — List of checkpoints with metadata

**Example:**

```python
checkpoints = await rollback_mgr.list_checkpoints()

for cp in checkpoints:
    print(f"{cp['name']}: {cp['timestamp']}")
    print(f"  Snapshot: {cp['snapshot_path']}")
```

**Output:**
```
before-migration: 2026-05-02T10:30:00Z
  Snapshot: ./obsidian/.snapshots/before-migration

after-agent-creation: 2026-05-02T11:15:00Z
  Snapshot: ./obsidian/.snapshots/after-agent-creation
```

---

### `delete_checkpoint(checkpoint_id: str) -> None`

Delete checkpoint and its snapshot.

**Parameters:**
- `checkpoint_id` (str) — Checkpoint ID to delete

**Returns:**
- None

**Raises:**
- `ValueError` — If checkpoint not found

**Example:**

```python
# Delete old checkpoint
await rollback_mgr.delete_checkpoint("old-checkpoint")

print("Checkpoint deleted")
```

**What happens:**
1. Finds checkpoint event
2. Deletes vault snapshot
3. Records deletion event

---

## Use Cases

### 1. Safe Migrations

```python
# Create checkpoint before migration
checkpoint = await rollback_mgr.create_checkpoint("before-schema-migration")

try:
    # Run migration
    await run_database_migration()
    await update_vault_structure()
    
    print("✅ Migration successful")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    
    # Rollback to safe state
    await rollback_mgr.rollback_to_checkpoint(checkpoint)
    
    print("✅ Rolled back to pre-migration state")
```

---

### 2. Experimental Changes

```python
# Try experimental feature
checkpoint = await rollback_mgr.create_checkpoint("before-experiment")

# Make experimental changes
await vault.write_file("config.md", "experimental: true")
await agent_factory.create_agent("experimental-agent")

# Test the changes
result = await test_experimental_feature()

if not result.success:
    # Revert experiment
    await rollback_mgr.rollback_to_checkpoint(checkpoint)
    print("Experiment failed, reverted")
else:
    # Keep changes
    print("Experiment successful, keeping changes")
```

---

### 3. Checkpoint Strategy

```python
# Create checkpoints at key milestones
checkpoints = []

# Milestone 1: Initial setup
cp1 = await rollback_mgr.create_checkpoint("01-initial-setup")
checkpoints.append(cp1)
await setup_system()

# Milestone 2: Agents created
cp2 = await rollback_mgr.create_checkpoint("02-agents-created")
checkpoints.append(cp2)
await create_all_agents()

# Milestone 3: Configuration done
cp3 = await rollback_mgr.create_checkpoint("03-config-complete")
checkpoints.append(cp3)
await configure_system()

# If something fails, rollback to last good checkpoint
try:
    await deploy_to_production()
except Exception as e:
    print(f"Deploy failed: {e}")
    await rollback_mgr.rollback_to_checkpoint(checkpoints[-1])
```

---

### 4. Cleanup Old Checkpoints

```python
# List all checkpoints
checkpoints = await rollback_mgr.list_checkpoints()

# Delete checkpoints older than 7 days
from datetime import datetime, timedelta, timezone

cutoff = datetime.now(timezone.utc) - timedelta(days=7)

for cp in checkpoints:
    cp_time = datetime.fromisoformat(cp['timestamp'])
    
    if cp_time < cutoff:
        print(f"Deleting old checkpoint: {cp['name']}")
        await rollback_mgr.delete_checkpoint(cp['name'])
```

---

### 5. Disaster Recovery

```python
# Regular backups
import asyncio

async def backup_loop():
    while True:
        # Create daily checkpoint
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        checkpoint = await rollback_mgr.create_checkpoint(f"daily-{timestamp}")
        
        print(f"✅ Daily backup created: {checkpoint}")
        
        # Wait 24 hours
        await asyncio.sleep(86400)

# Run in background
asyncio.create_task(backup_loop())
```

---

## How It Works

### Checkpoint Creation

```
1. User calls create_checkpoint("my-checkpoint")
   ↓
2. Vault creates snapshot
   - Copies all files to .snapshots/my-checkpoint/
   ↓
3. Event Store records checkpoint event
   - Event type: "checkpoint_created"
   - Payload: {name, snapshot_path, timestamp}
   ↓
4. Returns checkpoint ID
```

### Rollback Process

```
1. User calls rollback_to_checkpoint("my-checkpoint")
   ↓
2. Find checkpoint event in Event Store
   ↓
3. Restore vault from snapshot
   - Deletes current files
   - Copies files from .snapshots/my-checkpoint/
   ↓
4. Replay events after checkpoint (optional)
   - Replays events that happened after checkpoint
   - Skips side effects (idempotent)
   ↓
5. System restored to checkpoint state
```

---

## Best Practices

### 1. Name Checkpoints Clearly

```python
# ❌ Bad: Unclear names
await rollback_mgr.create_checkpoint("cp1")
await rollback_mgr.create_checkpoint("test")

# ✅ Good: Descriptive names
await rollback_mgr.create_checkpoint("before-agent-deletion")
await rollback_mgr.create_checkpoint("pre-production-deploy")
await rollback_mgr.create_checkpoint("2026-05-02-daily-backup")
```

### 2. Create Checkpoints Before Risky Operations

```python
# Always checkpoint before:
# - Deleting data
# - Schema migrations
# - Production deploys
# - Experimental features
# - Bulk operations

checkpoint = await rollback_mgr.create_checkpoint("before-bulk-delete")

try:
    await delete_old_agents()
except Exception as e:
    await rollback_mgr.rollback_to_checkpoint(checkpoint)
```

### 3. Test Rollback Regularly

```python
# Test rollback in staging
async def test_rollback():
    # Create test data
    await vault.write_file("test.md", "original")
    
    # Checkpoint
    cp = await rollback_mgr.create_checkpoint("test-checkpoint")
    
    # Modify
    await vault.write_file("test.md", "modified")
    
    # Rollback
    await rollback_mgr.rollback_to_checkpoint(cp)
    
    # Verify
    content = await vault.read_file("test.md")
    assert content == "original", "Rollback failed!"
    
    print("✅ Rollback test passed")

# Run monthly
await test_rollback()
```

### 4. Clean Up Old Checkpoints

```python
# Keep only recent checkpoints
checkpoints = await rollback_mgr.list_checkpoints()

# Keep last 10
if len(checkpoints) > 10:
    old_checkpoints = checkpoints[:-10]
    
    for cp in old_checkpoints:
        await rollback_mgr.delete_checkpoint(cp['name'])
        print(f"Deleted old checkpoint: {cp['name']}")
```

---

## Storage Requirements

Checkpoints consume disk space:

```python
# Estimate checkpoint size
import os

def get_vault_size(vault_path: str) -> int:
    total = 0
    for root, dirs, files in os.walk(vault_path):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total

vault_size = get_vault_size("./obsidian")
print(f"Vault size: {vault_size / 1024 / 1024:.2f} MB")

# Each checkpoint = ~vault_size
# 10 checkpoints = ~10x vault_size
```

**Recommendations:**
- Keep 5-10 recent checkpoints
- Delete checkpoints older than 30 days
- Monitor disk usage

---

## Error Handling

```python
# Checkpoint creation
try:
    checkpoint = await rollback_mgr.create_checkpoint("my-checkpoint")
except Exception as e:
    print(f"Failed to create checkpoint: {e}")

# Rollback
try:
    await rollback_mgr.rollback_to_checkpoint("my-checkpoint")
except ValueError as e:
    print(f"Checkpoint not found: {e}")
except Exception as e:
    print(f"Rollback failed: {e}")
```

---

## Performance

- **Checkpoint creation:** ~100-500ms (depends on vault size)
- **Rollback:** ~200-1000ms (depends on vault size)
- **List checkpoints:** ~10-50ms
- **Disk usage:** ~vault_size per checkpoint

---

## Limitations

1. **Vault only:** Only rolls back Obsidian vault, not SQLite database
2. **Disk space:** Each checkpoint = full vault copy
3. **No incremental:** Snapshots are full copies, not diffs
4. **Manual cleanup:** Old checkpoints must be deleted manually

---

## Future Improvements

- [ ] Incremental snapshots (only changed files)
- [ ] Database rollback support
- [ ] Automatic checkpoint cleanup
- [ ] Compression for old checkpoints
- [ ] Remote backup support

---

## See Also

- [Event Store API](event-store.md) — Event replay
- [Obsidian API](obsidian.md) — Vault snapshots
- [Orchestrator API](orchestrator.md) — Workflow coordination
