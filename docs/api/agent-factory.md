# Agent Factory API Reference

> Creating and managing agents with vaults and prompts

## Overview

**Agent Factory** — компонент для создания агентов. Автоматически создаёт Obsidian vault, генерирует промпт, регистрирует в SYSTEM.md и сохраняет метаданные в базу.

## Class: `AgentFactory`

### Constructor

```python
from meai.agents.factory import AgentFactory
from meai.storage.database import Database

db = Database("sqlite+aiosqlite:///./data/meai.db")
await db.connect()

factory = AgentFactory(
    vault_root="./obsidian",
    db=db
)
```

**Parameters:**
- `vault_root` (str) — Root path for Obsidian vaults
- `db` (Database) — Database instance for metadata

---

## Methods

### `create_agent(...) -> AgentMetadata`

Create new agent with vault, prompt, and registration.

**Parameters:**
- `agent_id` (str) — Unique agent identifier
- `agent_type` (str) — Type: "operator" or "subagent"
- `department` (str) — Department (e.g., "seo", "content")
- `role` (str) — Agent role description
- `parent_id` (str, optional) — Parent agent ID for hierarchy

**Returns:**
- `AgentMetadata` — Agent metadata with vault path and prompt

**Raises:**
- `ValueError` — If agent_id already exists

**Example:**

```python
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
print(f"   Prompt: {len(agent.prompt)} chars")
```

**What happens:**
1. Creates Obsidian vault at `{vault_root}/agents/{agent_id}/`
2. Generates agent prompt using Prompt Generator
3. Registers agent in SYSTEM.md
4. Saves metadata to database
5. Returns AgentMetadata

---

### `get_agent(agent_id: str) -> AgentMetadata`

Get agent metadata.

**Parameters:**
- `agent_id` (str) — Agent identifier

**Returns:**
- `AgentMetadata` — Agent metadata

**Raises:**
- `ValueError` — If agent not found

**Example:**

```python
agent = await factory.get_agent("seo-agent")

print(f"Agent: {agent.agent_id}")
print(f"Type: {agent.agent_type}")
print(f"Department: {agent.department}")
print(f"Vault: {agent.vault_path}")
```

---

### `list_agents() -> list[AgentMetadata]`

List all agents.

**Parameters:**
- None

**Returns:**
- `list[AgentMetadata]` — List of all agents

**Example:**

```python
agents = await factory.list_agents()

print(f"Total agents: {len(agents)}")
for agent in agents:
    print(f"  - {agent.agent_id} ({agent.agent_type})")
```

**Output:**
```
Total agents: 3
  - operator (operator)
  - seo-agent (subagent)
  - content-agent (subagent)
```

---

### `delete_agent(agent_id: str) -> None`

Delete agent and cleanup.

**Parameters:**
- `agent_id` (str) — Agent identifier

**Returns:**
- None

**Raises:**
- `ValueError` — If agent not found

**Example:**

```python
# Delete agent
await factory.delete_agent("old-agent")

print("✅ Agent deleted")
```

**What happens:**
1. Removes agent from SYSTEM.md
2. Deletes metadata from database
3. Optionally deletes vault (configurable)

---

### `update_agent(agent_id: str, role: str = None) -> None`

Update agent metadata.

**Parameters:**
- `agent_id` (str) — Agent identifier
- `role` (str, optional) — New role description

**Returns:**
- None

**Example:**

```python
# Update agent role
await factory.update_agent(
    agent_id="seo-agent",
    role="Senior SEO specialist with 5+ years experience"
)

print("✅ Agent updated")
```

---

## Data Classes

### `AgentMetadata`

Agent metadata.

**Fields:**
- `agent_id` (str) — Agent identifier
- `agent_type` (str) — Type: "operator" or "subagent"
- `department` (str) — Department
- `role` (str) — Role description
- `vault_path` (str) — Path to agent's vault
- `prompt` (str) — Generated prompt
- `parent_id` (str, optional) — Parent agent ID
- `created_at` (datetime) — Creation timestamp

**Example:**

```python
agent = await factory.create_agent(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist"
)

# Access fields
print(agent.agent_id)      # "seo-agent"
print(agent.agent_type)    # "subagent"
print(agent.department)    # "seo"
print(agent.vault_path)    # "./obsidian/agents/seo-agent"
print(len(agent.prompt))   # 1234
```

---

## Agent Types

### Operator

Top-level agent that manages subagents.

```python
operator = await factory.create_agent(
    agent_id="operator",
    agent_type="operator",
    department="operations",
    role="Operations director managing all agents",
    parent_id=None
)
```

**Characteristics:**
- No parent
- Manages subagents
- Coordinates workflows
- Makes strategic decisions

### Subagent

Specialized agent under operator.

```python
subagent = await factory.create_agent(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist",
    parent_id="operator"
)
```

**Characteristics:**
- Has parent (operator)
- Specialized role
- Reports to parent
- Executes specific tasks

---

## Agent Hierarchy

```python
# Create operator
operator = await factory.create_agent(
    agent_id="operator",
    agent_type="operator",
    department="operations",
    role="Operations director"
)

# Create subagents under operator
seo_agent = await factory.create_agent(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist",
    parent_id="operator"
)

content_agent = await factory.create_agent(
    agent_id="content-agent",
    agent_type="subagent",
    department="content",
    role="Content writer",
    parent_id="operator"
)

# Hierarchy:
# operator
# ├── seo-agent
# └── content-agent
```

---

## Vault Structure

Each agent gets its own Obsidian vault:

```
obsidian/agents/{agent_id}/
├── README.md              # Agent info
├── memory/                # Agent memory
│   ├── context.md
│   └── learnings.md
├── tasks/                 # Task logs
│   ├── task-001.md
│   └── task-002.md
└── decisions/             # Decision logs
    └── decision-001.md
```

**Example:**

```python
from meai.memory.obsidian import ObsidianVault

# Access agent vault
agent_vault = ObsidianVault(agent.vault_path)

# Write to memory
await agent_vault.write_file(
    "memory/context.md",
    "# Current Context\n\nWorking on SEO audit..."
)

# Read from memory
context = await agent_vault.read_file("memory/context.md")
```

---

## Prompt Generation

Factory automatically generates prompts using Prompt Generator:

```python
agent = await factory.create_agent(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist"
)

# Generated prompt includes:
# - Agent identity
# - Role and responsibilities
# - Vault path
# - Communication protocols
# - Safety guidelines

print(agent.prompt[:200])
```

**Example prompt:**
```
You are seo-agent, a subagent in the seo department.

Role: SEO specialist

Your vault is located at: ./obsidian/agents/seo-agent

You can:
- Read and write to your vault
- Log events to Event Store
- Communicate with other agents
...
```

---

## Database Schema

Agent metadata is stored in `agents` table:

```sql
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    agent_id TEXT UNIQUE NOT NULL,
    agent_type TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    vault_path TEXT NOT NULL,
    prompt TEXT NOT NULL,
    parent_id TEXT,
    created_at DATETIME NOT NULL
);

CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_department ON agents(department);
CREATE INDEX idx_agents_parent ON agents(parent_id);
```

---

## Use Cases

### 1. Create Agent Team

```python
# Create operator
operator = await factory.create_agent(
    agent_id="operator",
    agent_type="operator",
    department="operations",
    role="Operations director"
)

# Create specialized agents
departments = [
    ("seo", "SEO specialist"),
    ("content", "Content writer"),
    ("ads", "Advertising manager"),
    ("analytics", "Data analyst")
]

for dept, role in departments:
    agent = await factory.create_agent(
        agent_id=f"{dept}-agent",
        agent_type="subagent",
        department=dept,
        role=role,
        parent_id="operator"
    )
    print(f"✅ Created {agent.agent_id}")
```

---

### 2. Agent Discovery

```python
# List all agents
agents = await factory.list_agents()

# Filter by type
operators = [a for a in agents if a.agent_type == "operator"]
subagents = [a for a in agents if a.agent_type == "subagent"]

print(f"Operators: {len(operators)}")
print(f"Subagents: {len(subagents)}")

# Filter by department
seo_agents = [a for a in agents if a.department == "seo"]
print(f"SEO agents: {len(seo_agents)}")
```

---

### 3. Agent Lifecycle

```python
# Create
agent = await factory.create_agent(
    agent_id="test-agent",
    agent_type="subagent",
    department="test",
    role="Test agent"
)

# Use
agent_vault = ObsidianVault(agent.vault_path)
await agent_vault.write_file("test.md", "Hello")

# Update
await factory.update_agent(
    agent_id="test-agent",
    role="Updated test agent"
)

# Delete
await factory.delete_agent("test-agent")
```

---

## Best Practices

### 1. Use Descriptive IDs

```python
# ✅ Good: Clear, descriptive IDs
"seo-agent"
"content-writer-agent"
"analytics-specialist"

# ❌ Bad: Vague IDs
"agent1"
"test"
"a"
```

### 2. Organize by Department

```python
# ✅ Good: Clear department structure
departments = ["seo", "content", "ads", "analytics"]

for dept in departments:
    agent = await factory.create_agent(
        agent_id=f"{dept}-agent",
        agent_type="subagent",
        department=dept,
        role=f"{dept.upper()} specialist"
    )
```

### 3. Use Hierarchy

```python
# ✅ Good: Clear hierarchy
operator = await factory.create_agent(
    agent_id="operator",
    agent_type="operator",
    department="operations",
    role="Operations director"
)

# Subagents under operator
for dept in ["seo", "content"]:
    await factory.create_agent(
        agent_id=f"{dept}-agent",
        agent_type="subagent",
        department=dept,
        role=f"{dept} specialist",
        parent_id="operator"  # Link to parent
    )
```

### 4. Check Before Creating

```python
# ✅ Good: Check if exists
try:
    existing = await factory.get_agent("seo-agent")
    print(f"Agent already exists: {existing.agent_id}")
except ValueError:
    # Create new
    agent = await factory.create_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist"
    )
```

---

## Error Handling

```python
try:
    agent = await factory.create_agent(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist"
    )
except ValueError as e:
    print(f"Agent already exists: {e}")
except Exception as e:
    print(f"Failed to create agent: {e}")
```

---

## Performance

- **Create agent:** ~100-200ms
- **Get agent:** ~5-10ms
- **List agents:** ~10-50ms
- **Delete agent:** ~50-100ms

---

## See Also

- [Prompt Generator API](prompt-generator.md) — Prompt generation
- [System Registry API](system-registry.md) — SYSTEM.md management
- [Obsidian Vault API](obsidian.md) — Vault operations
- [Tutorial: Creating First Agent](../tutorials/01-first-agent.md)
