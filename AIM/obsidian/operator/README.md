# Operator Vault

**Role:** Tactical coordinator and task delegator

**Owner:** Operator Agent

**Purpose:** Manage tactical decisions, task delegation, and result aggregation

## Structure

This vault follows the LLM Wiki pattern (Andrej Karpathy):

```
operator/
├── raw/                    # Layer 1: Sources (immutable)
├── wiki/                   # Layer 2: Structured knowledge
│   ├── index.md           # Content-oriented catalog
│   ├── log.md             # Chronological operations log
│   ├── concepts/          # Concepts and patterns
│   ├── technologies/      # Technologies and tools
│   ├── strategies/        # Strategies and methods
│   ├── agents/            # Agents in the system
│   ├── workflows/         # Processes and workflows
│   ├── projects/          # Projects
│   ├── sources/           # Processed sources (summary)
│   └── connections/       # Links and syntheses
├── decisions/             # Layer 3: Tactical decisions
└── SCHEMA.md             # Rules and conventions
```

## Operations

1. **Ingest** - raw/ → wiki/ (create/update pages by category)
2. **Query** - question → read wiki/ → answer with citations → new page
3. **Lint** - check contradictions, orphans, gaps, stale data

## Status

- Created: 2026-05-03
- Status: initialized
- Owner: Operator
