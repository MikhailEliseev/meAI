# Tutorial: Creating Your First Agent

> Step-by-step guide to creating an agent with meAI

## Overview

В этом туториале мы создадим простого SEO-агента, который:
- Имеет собственный Obsidian vault для памяти
- Регистрируется в SYSTEM.md
- Может выполнять задачи
- Логирует все действия в Event Store

**Time:** ~15 minutes  
**Level:** Beginner

---

## Prerequisites

- meAI установлен и запущен
- Python 3.11+
- Базовое понимание async/await

---

## Step 1: Setup

Создайте файл `create_agent.py`:

```python
import asyncio
from meai.storage.database import Database
from meai.agents.factory import AgentFactory
from meai.agents.system_registry import SystemRegistry
from meai.memory.obsidian import ObsidianVault

async def main():
    # Initialize database
    db = Database("sqlite+aiosqlite:///./data/meai.db")
    await db.connect()
    
    print("✅ Database connected")
    
    # Initialize vault
    vault = ObsidianVault("./obsidian")
    await vault.initialize()
    
    print("✅ Vault initialized")
    
    # Initialize factory
    factory = AgentFactory(
        vault_root="./obsidian",
        db=db
    )
    
    print("✅ Factory ready")

if __name__ == "__main__":
    asyncio.run(main())
```

Запустите:
```bash
python create_agent.py
```

**Expected output:**
```
✅ Database connected
✅ Vault initialized
✅ Factory ready
```

---

## Step 2: Create Agent

Добавьте создание агента:

```python
async def main():
    # ... previous code ...
    
    # Create SEO agent
    agent = await factory.create_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist for medical marketing",
        parent_id=None  # No parent (top-level agent)
    )
    
    print(f"✅ Agent created: {agent.agent_id}")
    print(f"   Vault: {agent.vault_path}")
    print(f"   Prompt length: {len(agent.prompt)} chars")
```

Запустите снова:
```bash
python create_agent.py
```

**Expected output:**
```
✅ Database connected
✅ Vault initialized
✅ Factory ready
✅ Agent created: seo-agent
   Vault: ./obsidian/agents/seo-agent
   Prompt length: 1234 chars
```

---

## Step 3: Verify Agent Vault

Проверьте, что vault создан:

```python
async def main():
    # ... previous code ...
    
    # Check vault contents
    agent_vault = ObsidianVault(agent.vault_path)
    
    # Read README
    readme = await agent_vault.read_file("README.md")
    print("\n📄 Agent README:")
    print(readme[:200] + "...")
```

**Expected output:**
```
📄 Agent README:
# seo-agent

**Type:** subagent
**Department:** seo
**Role:** SEO specialist for medical marketing

## Memory

This vault contains the agent's memory...
```

---

## Step 4: Check System Registry

Проверьте регистрацию в SYSTEM.md:

```python
async def main():
    # ... previous code ...
    
    # Check system registry
    registry = SystemRegistry("./obsidian")
    agents = await registry.list_agents()
    
    print(f"\n📋 Registered agents: {len(agents)}")
    for a in agents:
        print(f"   - {a.agent_id} ({a.agent_type})")
```

**Expected output:**
```
📋 Registered agents: 1
   - seo-agent (subagent)
```

---

## Step 5: Write to Agent Memory

Добавьте запись в память агента:

```python
async def main():
    # ... previous code ...
    
    # Write to agent memory
    agent_vault = ObsidianVault(agent.vault_path)
    
    await agent_vault.write_file(
        "tasks/first-task.md",
        """# First Task

**Date:** 2026-05-02
**Status:** Completed

## Task
Analyze competitor SEO strategy

## Results
- Competitor uses 50+ keywords
- Strong backlink profile (DR 65)
- Content updated weekly

## Recommendations
1. Increase content frequency
2. Build quality backlinks
3. Target long-tail keywords
"""
    )
    
    print("\n✅ Task logged to agent memory")
```

---

## Step 6: Log Events

Добавьте логирование в Event Store:

```python
from meai.events.event_store import EventStore, Event
from datetime import datetime, timezone

async def main():
    # ... previous code ...
    
    # Initialize event store
    event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
    await event_store.initialize()
    
    # Log agent creation event
    event = Event(
        aggregate_id="seo-agent",
        aggregate_type="agent",
        event_type="agent_created",
        event_version=1,
        payload={
            "agent_id": "seo-agent",
            "department": "seo",
            "role": "SEO specialist",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
        idempotency_key="seo-agent-created"
    )
    
    await event_store.append_event(event)
    
    print("✅ Event logged")
    
    # Cleanup
    await event_store.close()
    await db.disconnect()
```

---

## Complete Code

Полный код `create_agent.py`:

```python
import asyncio
from datetime import datetime, timezone
from meai.storage.database import Database
from meai.agents.factory import AgentFactory
from meai.agents.system_registry import SystemRegistry
from meai.memory.obsidian import ObsidianVault
from meai.events.event_store import EventStore, Event


async def main():
    # Initialize database
    db = Database("sqlite+aiosqlite:///./data/meai.db")
    await db.connect()
    print("✅ Database connected")
    
    # Initialize vault
    vault = ObsidianVault("./obsidian")
    await vault.initialize()
    print("✅ Vault initialized")
    
    # Initialize factory
    factory = AgentFactory(
        vault_root="./obsidian",
        db=db
    )
    print("✅ Factory ready")
    
    # Create SEO agent
    agent = await factory.create_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist for medical marketing",
        parent_id=None
    )
    print(f"✅ Agent created: {agent.agent_id}")
    print(f"   Vault: {agent.vault_path}")
    
    # Check vault contents
    agent_vault = ObsidianVault(agent.vault_path)
    readme = await agent_vault.read_file("README.md")
    print(f"\n📄 Agent README:")
    print(readme[:200] + "...")
    
    # Check system registry
    registry = SystemRegistry("./obsidian")
    agents = await registry.list_agents()
    print(f"\n📋 Registered agents: {len(agents)}")
    for a in agents:
        print(f"   - {a.agent_id} ({a.agent_type})")
    
    # Write to agent memory
    await agent_vault.write_file(
        "tasks/first-task.md",
        """# First Task

**Date:** 2026-05-02
**Status:** Completed

## Task
Analyze competitor SEO strategy

## Results
- Competitor uses 50+ keywords
- Strong backlink profile (DR 65)
- Content updated weekly

## Recommendations
1. Increase content frequency
2. Build quality backlinks
3. Target long-tail keywords
"""
    )
    print("\n✅ Task logged to agent memory")
    
    # Initialize event store
    event_store = EventStore("sqlite+aiosqlite:///./data/meai.db")
    await event_store.initialize()
    
    # Log agent creation event
    event = Event(
        aggregate_id="seo-agent",
        aggregate_type="agent",
        event_type="agent_created",
        event_version=1,
        payload={
            "agent_id": "seo-agent",
            "department": "seo",
            "role": "SEO specialist",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
        idempotency_key="seo-agent-created"
    )
    
    await event_store.append_event(event)
    print("✅ Event logged")
    
    # Cleanup
    await event_store.close()
    await db.disconnect()
    
    print("\n🎉 Agent creation complete!")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Run It

```bash
python create_agent.py
```

**Expected output:**
```
✅ Database connected
✅ Vault initialized
✅ Factory ready
✅ Agent created: seo-agent
   Vault: ./obsidian/agents/seo-agent

📄 Agent README:
# seo-agent

**Type:** subagent
**Department:** seo
**Role:** SEO specialist for medical marketing...

📋 Registered agents: 1
   - seo-agent (subagent)

✅ Task logged to agent memory
✅ Event logged

🎉 Agent creation complete!
```

---

## Verify Results

### 1. Check Vault Structure

```bash
tree obsidian/agents/seo-agent/
```

**Expected:**
```
obsidian/agents/seo-agent/
├── README.md
├── memory/
└── tasks/
    └── first-task.md
```

### 2. Check SYSTEM.md

```bash
cat obsidian/SYSTEM.md
```

**Expected:**
```markdown
# AIM Agency System

## Agents

### seo-agent
- **Type:** subagent
- **Department:** seo
- **Role:** SEO specialist for medical marketing
- **Vault:** ./obsidian/agents/seo-agent
```

### 3. Check Events

```python
# Query events
events = await event_store.get_events(
    aggregate_id="seo-agent",
    event_type="agent_created"
)

print(f"Found {len(events)} events")
for event in events:
    print(f"  {event.event_type}: {event.payload}")
```

---

## Next Steps

Now that you have created your first agent, you can:

1. **Add more agents** — Create Content agent, Ads agent, etc.
2. **Create hierarchy** — Add parent_id to create subagents
3. **Use Decision Maker** — Let agents make strategic decisions
4. **Add checkpoints** — Use Rollback Manager for safety
5. **Build workflows** — Use Orchestrator for complex tasks

---

## Troubleshooting

### Error: "Database not connected"

```python
# Make sure to await connect()
await db.connect()
```

### Error: "Vault path already exists"

```python
# Agent already exists, use different agent_id or delete old one
await factory.delete_agent("seo-agent")
```

### Error: "Permission denied"

```bash
# Check file permissions
chmod -R 755 obsidian/
```

---

## What You Learned

✅ How to initialize meAI components  
✅ How to create an agent with Agent Factory  
✅ How agent vaults work  
✅ How System Registry tracks agents  
✅ How to write to agent memory  
✅ How to log events to Event Store

---

## See Also

- [Memory System Tutorial](02-memory-system.md)
- [Event Sourcing Tutorial](03-event-sourcing.md)
- [Agent Factory API](../api/agent-factory.md)
- [Event Store API](../api/event-store.md)
