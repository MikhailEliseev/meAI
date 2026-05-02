# Architecture Overview

> High-level system design of meAI

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     meAI Core                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Architect   │  │Decision Maker│  │ Orchestrator │    │
│  │              │  │              │  │              │    │
│  │ Autonomous   │  │  Strategy    │  │    Async     │    │
│  │  Decisions   │  │  Selection   │  │ Coordination │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    Storage Layer                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ SQLite   │  │ Obsidian │  │  Event   │  │  Event   │  │
│  │          │  │  Vaults  │  │  Store   │  │   Bus    │  │
│  │ Async DB │  │ Markdown │  │ Audit Log│  │ Messages │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    Safety Layer                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Loop   │  │ Timeout  │  │ Context  │  │ Shutdown │  │
│  │ Detector │  │ Manager  │  │ Monitor  │  │ Handler  │  │
│  │ Max: 5   │  │ 5min def │  │ 40% rule │  │ Graceful │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

### 1. Dual Storage
- **SQLite** для структурированных данных (метаданные, метрики)
- **Obsidian** для неструктурированных знаний (память агентов)

### 2. Event Sourcing
- Все изменения логируются как immutable события
- Полный audit trail
- Возможность replay для восстановления

### 3. Async-First
- Полная поддержка asyncio
- Параллельное выполнение задач
- Неблокирующие операции

### 4. Safety by Design
- Loop detection (max depth 5)
- Operation timeouts (5 min default)
- Context monitoring (40% rule)
- Graceful shutdown

### 5. Agent Hierarchy
- Operator управляет subagents
- Каждый агент имеет свой vault
- Коммуникация через Event Bus

## Data Flow

```
User Request
    ↓
Architect (decision)
    ↓
Orchestrator (coordination)
    ↓
Agent Factory (create agents)
    ↓
Agents (execute tasks)
    ↓
Event Store (log events)
    ↓
Obsidian Vault (save memory)
    ↓
Response
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | SQLite (aiosqlite) |
| ORM | SQLAlchemy 2.0 async |
| Memory | Obsidian (markdown) |
| Testing | pytest, pytest-asyncio |
| Logging | structlog |
| Container | Docker |

## Scalability

- **Horizontal:** Multiple agents работают параллельно
- **Vertical:** Async operations максимизируют throughput
- **Storage:** SQLite для MVP, PostgreSQL для scale

## Security

- No external API calls без explicit permission
- Secrets в .env файлах
- Event Store для audit trail
- Graceful error handling

## See Also

- [Storage Layer](storage.md)
- [Event Sourcing](event-sourcing.md)
- [Agent System](agents.md)
- [Safety Mechanisms](safety.md)
