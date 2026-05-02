# System Registry API Reference

> SYSTEM.md management and agent discovery

## Overview

**System Registry** — компонент для управления SYSTEM.md файлом. Регистрирует агентов, отслеживает иерархию и предоставляет discovery.

## Class: `SystemRegistry`

### Methods

```python
from meai.agents.system_registry import SystemRegistry

registry = SystemRegistry("./obsidian")
await registry.initialize()

# Register agent
await registry.register_agent(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist",
    vault_path="./obsidian/agents/seo-agent",
    parent_id="operator"
)

# List agents
agents = await registry.list_agents()
for agent in agents:
    print(f"{agent.agent_id}: {agent.role}")

# Update agent
await registry.update_agent(
    agent_id="seo-agent",
    role="Senior SEO specialist"
)

# Remove agent
await registry.remove_agent("old-agent")
```

## AgentInfo Data Class

```python
@dataclass
class AgentInfo:
    agent_id: str
    agent_type: str
    department: str
    role: str
    vault_path: str
    parent_id: Optional[str] = None
```

## SYSTEM.md Format

```markdown
# AIM Agency System

## Agents

### operator
- **Type:** operator
- **Department:** operations
- **Role:** Operations director
- **Vault:** ./obsidian/agents/operator

### seo-agent
- **Type:** subagent
- **Department:** seo
- **Role:** SEO specialist
- **Vault:** ./obsidian/agents/seo-agent
- **Parent:** operator

## Communication

- Event Bus: Async message queue
- Event Store: Immutable audit log

## Safety

- Loop detection: Max depth 5
- Timeouts: 5 minutes default
- Context monitoring: 40% rule
```

## Agent Discovery

```python
# Get all agents
all_agents = await registry.list_agents()

# Filter by type
operators = [a for a in all_agents if a.agent_type == "operator"]
subagents = [a for a in all_agents if a.agent_type == "subagent"]

# Filter by department
seo_agents = [a for a in all_agents if a.department == "seo"]

# Find by parent
operator_children = [a for a in all_agents if a.parent_id == "operator"]
```

## Best Practices

- Always register agents after creation
- Keep SYSTEM.md as single source of truth
- Use descriptive roles
- Maintain hierarchy with parent_id
- Remove agents when deleted

## See Also

- [Agent Factory API](agent-factory.md)
- [Obsidian Vault API](obsidian.md)
