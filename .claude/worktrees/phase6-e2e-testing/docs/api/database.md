# Database API Reference

> Async SQLite operations with SQLAlchemy

## Overview

**Database** — компонент для работы с SQLite через SQLAlchemy 2.0 async. Управляет подключением, сессиями и транзакциями.

## Class: `Database`

### Constructor & Methods

```python
from meai.storage.database import Database

# Initialize
db = Database("sqlite+aiosqlite:///./data/meai.db")
await db.connect()

# Use session
async with db.session() as session:
    result = await session.execute("SELECT * FROM agents")
    agents = result.fetchall()

# Health check
health = await db.health()
print(health["status"])  # "healthy"

# Disconnect
await db.disconnect()
```

## Key Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `connect()` | Initialize connection and create tables | None |
| `disconnect()` | Close connection | None |
| `session()` | Get async session context manager | AsyncSession |
| `health()` | Check database health | dict |
| `is_connected()` | Check connection status | bool |

## Session Usage

```python
# Read operation
async with db.session() as session:
    query = select(Agent).where(Agent.agent_id == "seo-agent")
    result = await session.execute(query)
    agent = result.scalar_one()

# Write operation
async with db.session() as session:
    agent = Agent(agent_id="new-agent", ...)
    session.add(agent)
    # Auto-commits on exit

# Error handling
async with db.session() as session:
    try:
        # operations
        pass
    except Exception:
        # Auto-rollback on error
        raise
```

## Models

All models inherit from `Base`:

```python
from meai.storage.models import Base
from sqlalchemy.orm import Mapped, mapped_column

class MyModel(Base):
    __tablename__ = "my_table"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
```

## Best Practices

- Always use `async with db.session()` for transactions
- Let session auto-commit/rollback
- Check `is_connected()` before operations
- Use `health()` for monitoring

## See Also

- [Event Store API](event-store.md)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
