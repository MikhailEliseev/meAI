# Tutorial: Rollback & Recovery

> Using checkpoints and event replay for recovery

## Overview

Rollback Manager позволяет откатывать систему к предыдущему состоянию через комбинацию vault snapshots и event replay.

**Time:** ~10 minutes  
**Level:** Intermediate

---

## Step 1: Understanding Rollback

Rollback состоит из двух частей:

1. **Vault Snapshot** — копия всех файлов памяти
2. **Event Replay** — восстановление состояния из событий

```
Checkpoint = Snapshot + Event Marker
```

---

## Step 2: Creating Checkpoint

```python
from meai.core.rollback import RollbackManager
from meai.memory.obsidian import ObsidianVault
from meai.events.event_store import EventStore

# Initialize
vault = ObsidianVault("./obsidian")
await vault.initialize()

event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
await event_store.initialize()

rollback_mgr = RollbackManager(vault, event_store)

# Create checkpoint before risky operation
checkpoint_id = await rollback_mgr.create_checkpoint("before-migration")

print(f"✅ Checkpoint created: {checkpoint_id}")
```

---

## Step 3: Making Changes

```python
# Make changes to vault
await vault.write_file(
    "agents/seo-agent/config.md",
    "# New Configuration\n\nUpdated settings..."
)

# Make changes to database
# ... database operations ...

print("✅ Changes applied")
```

---

## Step 4: Rolling Back

```python
# Something went wrong, rollback!
try:
    await risky_operation()
except Exception as e:
    print(f"❌ Operation failed: {e}")
    
    # Rollback to checkpoint
    await rollback_mgr.rollback_to_checkpoint("before-migration")
    
    print("✅ Rolled back to safe state")
```

---

## Step 5: Checkpoint Strategy

```python
# Create checkpoints at key milestones
checkpoints = []

# Milestone 1: Before agent creation
cp1 = await rollback_mgr.create_checkpoint("01-before-agents")
checkpoints.append(cp1)

# Create agents
await create_all_agents()

# Milestone 2: After agent creation
cp2 = await rollback_mgr.create_checkpoint("02-agents-created")
checkpoints.append(cp2)

# Configure agents
await configure_all_agents()

# Milestone 3: After configuration
cp3 = await rollback_mgr.create_checkpoint("03-configured")
checkpoints.append(cp3)

# If deployment fails, rollback to last good checkpoint
try:
    await deploy_to_production()
except Exception as e:
    print(f"Deploy failed: {e}")
    await rollback_mgr.rollback_to_checkpoint(checkpoints[-1])
```

---

## Step 6: Listing Checkpoints

```python
# List all checkpoints
checkpoints = await rollback_mgr.list_checkpoints()

print(f"Available checkpoints: {len(checkpoints)}")
for cp in checkpoints:
    print(f"  {cp['name']}: {cp['timestamp']}")
```

---

## Step 7: Cleanup Old Checkpoints

```python
from datetime import datetime, timedelta, timezone

# Delete checkpoints older than 7 days
checkpoints = await rollback_mgr.list_checkpoints()
cutoff = datetime.now(timezone.utc) - timedelta(days=7)

for cp in checkpoints:
    cp_time = datetime.fromisoformat(cp['timestamp'])
    
    if cp_time < cutoff:
        print(f"Deleting old checkpoint: {cp['name']}")
        await rollback_mgr.delete_checkpoint(cp['name'])
```

---

## Step 8: Complete Example

```python
import asyncio
from meai.core.rollback import RollbackManager
from meai.memory.obsidian import ObsidianVault
from meai.events.event_store import EventStore

async def main():
    # Initialize
    vault = ObsidianVault("./obsidian")
    await vault.initialize()
    
    event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
    await event_store.initialize()
    
    rollback_mgr = RollbackManager(vault, event_store)
    
    # Create initial state
    await vault.write_file("test.md", "version 1")
    print("✅ Initial state created")
    
    # Checkpoint
    checkpoint = await rollback_mgr.create_checkpoint("test-checkpoint")
    print(f"✅ Checkpoint: {checkpoint}")
    
    # Make changes
    await vault.write_file("test.md", "version 2")
    print("✅ Changes made")
    
    # Verify changes
    content = await vault.read_file("test.md")
    assert content == "version 2"
    
    # Rollback
    await rollback_mgr.rollback_to_checkpoint(checkpoint)
    print("✅ Rolled back")
    
    # Verify rollback
    content = await vault.read_file("test.md")
    assert content == "version 1"
    print("✅ Rollback verified")
    
    # Cleanup
    await rollback_mgr.delete_checkpoint(checkpoint)
    await event_store.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Use Cases

### 1. Safe Migrations

```python
# Before schema migration
checkpoint = await rollback_mgr.create_checkpoint("before-schema-v2")

try:
    await migrate_to_schema_v2()
    print("✅ Migration successful")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    await rollback_mgr.rollback_to_checkpoint(checkpoint)
    print("✅ Rolled back to schema v1")
```

### 2. Experimental Features

```python
# Try experimental feature
checkpoint = await rollback_mgr.create_checkpoint("before-experiment")

await enable_experimental_feature()
result = await test_feature()

if not result.success:
    await rollback_mgr.rollback_to_checkpoint(checkpoint)
    print("Experiment failed, reverted")
```

### 3. Daily Backups

```python
import asyncio

async def daily_backup():
    while True:
        # Create daily checkpoint
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        checkpoint = await rollback_mgr.create_checkpoint(f"daily-{timestamp}")
        
        print(f"✅ Daily backup: {checkpoint}")
        
        # Wait 24 hours
        await asyncio.sleep(86400)

# Run in background
asyncio.create_task(daily_backup())
```

---

## Best Practices

1. **Create checkpoints before risky operations**
2. **Use descriptive names** (include date/purpose)
3. **Test rollback regularly** in staging
4. **Clean up old checkpoints** to save disk space
5. **Monitor checkpoint size** (each = full vault copy)

---

## Limitations

- Only rolls back Obsidian vault (not SQLite database)
- Snapshots are full copies (not incremental)
- Requires disk space (~vault_size per checkpoint)

---

## See Also

- [Rollback Manager API](../api/rollback.md)
- [Event Store API](../api/event-store.md)
- [Obsidian Vault API](../api/obsidian.md)
