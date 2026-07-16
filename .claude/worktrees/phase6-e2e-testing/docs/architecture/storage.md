# Storage Layer Architecture

> Dual storage: SQLite + Obsidian

## Design Decision

meAI использует **dual storage** подход:

1. **SQLite** — структурированные данные
2. **Obsidian** — неструктурированные знания

## Why Dual Storage?

### SQLite для:
- Метаданные агентов
- Event Store (audit log)
- Метрики и статистика
- Быстрые queries

### Obsidian для:
- Память агентов
- Контекст и learnings
- Task logs
- Decision records
- Human-readable format

## SQLite Schema

```sql
-- Agents
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    agent_id TEXT UNIQUE,
    agent_type TEXT,
    department TEXT,
    role TEXT,
    vault_path TEXT,
    created_at DATETIME
);

-- Events
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    aggregate_id TEXT,
    event_type TEXT,
    payload TEXT,
    timestamp TEXT,
    idempotency_key TEXT UNIQUE
);

-- Metrics
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY,
    name TEXT,
    value REAL,
    metric_type TEXT,
    timestamp DATETIME
);
```

## Obsidian Structure

```
obsidian/
├── agents/
│   ├── operator/
│   │   ├── README.md
│   │   ├── memory/
│   │   ├── tasks/
│   │   └── decisions/
│   └── seo-agent/
│       └── ...
├── .snapshots/
│   └── checkpoint-name/
└── SYSTEM.md
```

## Data Consistency

- SQLite = source of truth для метаданных
- Obsidian = source of truth для памяти
- Event Store связывает оба

## Backup Strategy

- **SQLite:** Regular database backups
- **Obsidian:** Snapshots через Rollback Manager
- **Events:** Immutable, never deleted

## Performance

- SQLite: ~5-10ms queries
- Obsidian: ~5-20ms file operations
- Both: Async operations

## See Also

- [Event Sourcing](event-sourcing.md)
- [Database API](../api/database.md)
- [Obsidian API](../api/obsidian.md)
- [ADR-001: Dual Storage](../adr/001-dual-storage.md)
