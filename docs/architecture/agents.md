# Agent System Architecture

> Hierarchical agent structure with communication

## Agent Hierarchy

```
Operator (CEO)
├── SEO Agent
│   ├── Keyword Research Subagent
│   ├── Content Optimization Subagent
│   └── Link Building Subagent
├── Content Agent
│   ├── Copywriting Subagent
│   └── Editing Subagent
└── Analytics Agent
    └── Reporting Subagent
```

## Agent Types

### Operator
- Top-level agent
- Manages subagents
- Makes strategic decisions
- Coordinates workflows

### Subagent
- Specialized role
- Reports to operator
- Executes specific tasks
- Maintains own memory

## Agent Components

Each agent has:

1. **Vault** — Obsidian vault for memory
2. **Prompt** — Generated instructions
3. **Metadata** — Stored in SQLite
4. **Registry Entry** — Listed in SYSTEM.md

## Communication

Agents communicate via **Event Bus**:

```python
# Operator → Subagent
message = Message(
    from_agent="operator",
    to_agent="seo-agent",
    message_type="task_assignment",
    priority=1,
    payload={"task": "analyze_competitors"}
)
```

## Agent Lifecycle

1. **Creation** — Agent Factory creates agent
2. **Registration** — Added to SYSTEM.md
3. **Execution** — Processes tasks
4. **Communication** — Sends/receives messages
5. **Logging** — Events to Event Store
6. **Memory** — Writes to vault
7. **Deletion** — Cleanup and removal

## See Also

- [Agent Factory API](../api/agent-factory.md)
- [Event Bus API](../api/event-bus.md)
- [Tutorial: Creating First Agent](../tutorials/01-first-agent.md)
