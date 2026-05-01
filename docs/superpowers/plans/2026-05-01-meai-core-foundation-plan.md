# meAI Architect - Core Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build meAI Core Foundation — базовая инфраструктура архитектора, который может создавать агентов

**Architecture:** Dual storage (SQLite + Obsidian), Event Sourcing, Async-first, Agent Factory, Safety Mechanisms

**Tech Stack:** Python 3.11+, FastAPI, SQLite (aiosqlite), SQLAlchemy 2.0 async, Pydantic, asyncio, structlog

---

## Scope

This plan covers **Phase 1: Core Foundation (MVP)** from the design spec.

**What we're building:**
1. Storage Layer (SQLite + Obsidian integration)
2. Event Sourcing system
3. Event Bus (async message queue)
4. Agent Factory (creates agents with vaults and prompts)
5. Safety Mechanisms (loop detection, timeouts, context monitor)
6. Basic Monitoring (health checks, status)
7. Secrets Management (.env)
8. Automated Backups
9. Rate Limiting
10. Graceful Shutdown
11. Testing infrastructure
12. Deployment setup

**What we're NOT building (Post-MVP):**
- Analytics & Optimization Engine (advanced optimization)
- Learning & Adaptation System (ML-based learning)
- Strategic Planning System (long-term planning)
- Web UI (monitoring dashboard)

**What we ARE building (MVP - Added after review):**
- Core Architect with real functionality
- Decision Maker (autonomous decisions)
- Orchestrator (component coordination)
- System Registry (SYSTEM.md management)
- Rollback Orchestration (snapshot + event replay)
- Human-in-Loop Gates (critical decisions)

---

## File Structure

```
/Users/mikhaileliseev/Desktop/Dev/!meAI/
├── src/meai/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (from .env)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── architect.py           # Core Architect component
│   │   ├── decision_maker.py      # Decision making logic
│   │   └── orchestrator.py        # Async orchestration
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite async connection
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── event_store.py         # Event sourcing
│   │   └── obsidian.py            # Obsidian vault integration
│   │
│   ├── messaging/
│   │   ├── __init__.py
│   │   ├── event_bus.py           # Async message bus
│   │   ├── message.py             # Message models
│   │   └── priority_queue.py      # P0-P3 priority queue
│   │
│   ├── factory/
│   │   ├── __init__.py
│   │   ├── agent_factory.py       # Agent creation
│   │   ├── vault_initializer.py   # Vault setup
│   │   ├── prompt_generator.py    # Prompt generation
│   │   └── system_registry.py     # SYSTEM.md management
│   │
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── loop_detector.py       # Loop detection
│   │   ├── timeout_manager.py     # Timeout policies
│   │   ├── context_monitor.py     # 40% rule monitor
│   │   └── shutdown_handler.py    # Graceful shutdown
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── health.py              # Health checks
│   │   └── metrics.py             # Metrics collection
│   │
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py        # Claude API rate limiter
│       └── backup.py              # Backup utilities
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── unit/
│   │   ├── test_agent_factory.py
│   │   ├── test_event_store.py
│   │   └── test_event_bus.py
│   └── integration/
│       ├── test_end_to_end.py
│       └── test_message_flow.py
│
├── scripts/
│   ├── backup.sh                  # Automated backup script
│   └── deploy.sh                  # Deployment script
│
├── alembic/                       # Database migrations
│   ├── env.py
│   └── versions/
│
├── .env.example                   # Example environment variables
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata
└── README.md                      # Quick start guide
```

---

## Prerequisites

- Python 3.11+
- pip
- git
- SQLite 3.35+ (for WAL mode)
- Obsidian vault at `./obsidian/`

---

## Task 1: Project Setup & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0

# Database
sqlalchemy[asyncio]==2.0.25
aiosqlite==0.19.0
alembic==1.13.1

# Data validation
pydantic==2.5.3
pydantic-settings==2.1.0

# Async utilities
aiofiles==23.2.1
aiolimiter==1.1.0

# Logging
structlog==24.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0

# Development
ruff==0.1.14
mypy==1.8.0
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "meai"
version = "0.1.0"
description = "meAI - CEO Architect for AIM Agency"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "python-dotenv>=1.0.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "aiosqlite>=0.19.0",
    "alembic>=1.13.1",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "aiofiles>=23.2.1",
    "aiolimiter>=1.1.0",
    "structlog>=24.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.4",
    "pytest-asyncio>=0.23.3",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
    "ruff>=0.1.14",
    "mypy>=1.8.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_backend"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

- [ ] **Step 3: Create .env.example**

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db

# Obsidian
OBSIDIAN_VAULT_PATH=./obsidian

# Logging
LOG_LEVEL=INFO

# Rate Limiting
CLAUDE_API_RATE_LIMIT=50  # requests per minute

# Budget
CLAUDE_API_BUDGET_MONTHLY=100.0  # USD
```

- [ ] **Step 4: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local

# Database
data/
*.db
*.db-journal
*.db-wal
*.db-shm

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Superflow
.superflow-state.json
.superflow/

# Obsidian (keep structure, ignore content for now)
obsidian/.obsidian/
```

- [ ] **Step 5: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: All packages installed successfully

- [ ] **Step 6: Verify installation**

Run: `python -c "import fastapi, sqlalchemy, pydantic; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pyproject.toml .env.example .gitignore
git commit -m "feat: add project dependencies and configuration

- Add requirements.txt with core dependencies
- Add pyproject.toml with project metadata
- Add .env.example for environment variables
- Add .gitignore for Python project

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Configuration Management

**Files:**
- Create: `src/meai/__init__.py`
- Create: `src/meai/config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_config.py
import pytest
from meai.config import Settings

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
    
    settings = Settings()
    assert settings.anthropic_api_key == "test-key"
    assert settings.database_url == "sqlite+aiosqlite:///test.db"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'meai.config'"

- [ ] **Step 3: Create src/meai/__init__.py**

```python
"""meAI - CEO Architect for AIM Agency"""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create src/meai/config.py**

```python
"""Configuration management using pydantic-settings"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Claude API
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/meai.db",
        description="Database connection URL"
    )
    
    # Obsidian
    obsidian_vault_path: str = Field(
        default="./obsidian",
        description="Path to Obsidian vault"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Rate Limiting
    claude_api_rate_limit: int = Field(
        default=50,
        description="Claude API requests per minute"
    )
    
    # Budget
    claude_api_budget_monthly: float = Field(
        default=100.0,
        description="Monthly budget in USD"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/meai/__init__.py src/meai/config.py tests/unit/test_config.py
git commit -m "feat: add configuration management

- Add Settings class with pydantic-settings
- Load config from .env file
- Add test for config loading

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Database Layer - SQLite Setup

**Files:**
- Create: `src/meai/storage/__init__.py`
- Create: `src/meai/storage/database.py`
- Create: `src/meai/storage/models.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_database.py
import pytest
from meai.storage.database import Database

@pytest.mark.asyncio
async def test_database_connection():
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    assert db.is_connected()
    await db.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/storage/__init__.py**

```python
"""Storage layer - SQLite and Obsidian integration"""

from .database import Database
from .models import Base, Event, Message, Metric

__all__ = ["Database", "Base", "Event", "Message", "Metric"]
```

- [ ] **Step 4: Create src/meai/storage/database.py**

```python
"""SQLite async database connection manager"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
import structlog

from .models import Base

logger = structlog.get_logger()


class Database:
    """Async SQLite database manager"""
    
    def __init__(self, url: str):
        self.url = url
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
    
    async def connect(self) -> None:
        """Initialize database connection"""
        logger.info("database.connect", url=self.url)
        
        self.engine = create_async_engine(
            self.url,
            echo=False,
            poolclass=NullPool,  # SQLite doesn't need connection pooling
            connect_args={"check_same_thread": False},
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("database.connected")
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.engine:
            logger.info("database.disconnect")
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.engine is not None
    
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self.session_factory:
            raise RuntimeError("Database not connected")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def health(self) -> dict[str, str]:
        """Health check"""
        if not self.is_connected():
            return {"status": "disconnected"}
        
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database instance
db: Database | None = None


def get_db() -> Database:
    """Get global database instance"""
    if db is None:
        raise RuntimeError("Database not initialized")
    return db


def init_db(url: str) -> Database:
    """Initialize global database instance"""
    global db
    db = Database(url)
    return db
```

- [ ] **Step 5: Create src/meai/storage/models.py**

```python
"""SQLAlchemy models for events, messages, and metrics"""

from datetime import datetime
from typing import Any
from sqlalchemy import JSON, String, Integer, Float, DateTime, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Event(Base):
    """Event sourcing - immutable event log"""
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    aggregate_id: Mapped[str] = mapped_column(String(64), index=True)
    aggregate_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_events_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_events_type_time", "event_type", "timestamp"),
    )


class Message(Base):
    """Message bus - async message queue"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    from_agent: Mapped[str] = mapped_column(String(64), index=True)
    to_agent: Mapped[str] = mapped_column(String(64), index=True)
    message_type: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=2, index=True)  # P0-P3
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_messages_queue", "status", "priority", "created_at"),
    )


class Metric(Base):
    """Metrics collection"""
    __tablename__ = "metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(64), index=True)
    metric_type: Mapped[str] = mapped_column(String(16))  # counter, gauge, histogram
    value: Mapped[float] = mapped_column(Float)
    labels: Mapped[dict[str, str]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_metrics_name_time", "metric_name", "timestamp"),
    )
```

- [ ] **Step 6: Initialize Alembic**

Run: `alembic init alembic`
Expected: Creates `alembic/` directory and `alembic.ini`

- [ ] **Step 7: Configure Alembic**

Edit `alembic.ini`:
```ini
sqlalchemy.url = sqlite+aiosqlite:///./data/meai.db
```

Edit `alembic/env.py`:
```python
from meai.storage.models import Base
target_metadata = Base.metadata
```

- [ ] **Step 8: Create initial migration**

Run: `alembic revision --autogenerate -m "initial schema"`
Expected: Creates migration file in `alembic/versions/`

- [ ] **Step 9: Run test to verify it passes**

Run: `pytest tests/unit/test_database.py -v`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add src/meai/storage/ tests/unit/test_database.py alembic/
git commit -m "feat: add SQLite database layer

- Add async database connection manager
- Add SQLAlchemy models (Event, Message, Metric)
- Add Alembic migrations setup
- Add health check support

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Obsidian Integration

**Files:**
- Create: `src/meai/storage/obsidian.py`
- Create: `tests/unit/test_obsidian.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_obsidian.py
import pytest
from pathlib import Path
from meai.storage.obsidian import ObsidianVault

@pytest.mark.asyncio
async def test_vault_initialization(tmp_path):
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    assert (tmp_path / ".obsidian").exists()
    assert (tmp_path / "README.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_obsidian.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/storage/obsidian.py**

```python
"""Obsidian vault integration"""

from pathlib import Path
from typing import Any
import json
import aiofiles
import structlog

logger = structlog.get_logger()


class ObsidianVault:
    """Obsidian vault manager"""
    
    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path)
    
    async def initialize(self) -> None:
        """Initialize vault structure"""
        logger.info("vault.initialize", path=str(self.vault_path))
        
        # Create vault directory
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Create .obsidian directory
        obsidian_dir = self.vault_path / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)
        
        # Create README
        readme_path = self.vault_path / "README.md"
        if not readme_path.exists():
            async with aiofiles.open(readme_path, "w") as f:
                await f.write("# meAI Vault\n\nThis vault contains meAI knowledge and context.\n")
        
        logger.info("vault.initialized")
    
    async def create_agent_vault(self, agent_name: str) -> Path:
        """Create vault for an agent"""
        agent_vault = self.vault_path / "agents" / agent_name
        agent_vault.mkdir(parents=True, exist_ok=True)
        
        # Create agent vault structure
        (agent_vault / "context").mkdir(exist_ok=True)
        (agent_vault / "decisions").mkdir(exist_ok=True)
        (agent_vault / "learnings").mkdir(exist_ok=True)
        
        # Create agent README
        readme_path = agent_vault / "README.md"
        async with aiofiles.open(readme_path, "w") as f:
            await f.write(f"# {agent_name}\n\nAgent vault for {agent_name}.\n")
        
        logger.info("vault.agent_created", agent=agent_name, path=str(agent_vault))
        return agent_vault
    
    async def write_file(self, relative_path: str, content: str) -> None:
        """Write file to vault"""
        file_path = self.vault_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
        
        logger.debug("vault.file_written", path=relative_path)
    
    async def read_file(self, relative_path: str) -> str:
        """Read file from vault"""
        file_path = self.vault_path / relative_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
        
        return content
    
    async def create_snapshot(self, snapshot_name: str) -> Path:
        """Create vault snapshot"""
        snapshot_dir = self.vault_path / "snapshots" / snapshot_name
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy vault contents (excluding .obsidian and snapshots)
        import shutil
        for item in self.vault_path.iterdir():
            if item.name not in [".obsidian", "snapshots"]:
                if item.is_dir():
                    shutil.copytree(item, snapshot_dir / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, snapshot_dir / item.name)
        
        logger.info("vault.snapshot_created", name=snapshot_name)
        return snapshot_dir
    
    async def restore_snapshot(self, snapshot_name: str) -> None:
        """Restore vault from snapshot"""
        snapshot_dir = self.vault_path / "snapshots" / snapshot_name
        
        if not snapshot_dir.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_name}")
        
        # Restore contents
        import shutil
        for item in snapshot_dir.iterdir():
            target = self.vault_path / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        
        logger.info("vault.snapshot_restored", name=snapshot_name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_obsidian.py -v`
Expected: PASS

- [ ] **Step 5: Add integration test**

```python
# tests/integration/test_vault_integration.py
import pytest
from pathlib import Path
from meai.storage.obsidian import ObsidianVault

@pytest.mark.asyncio
async def test_agent_vault_workflow(tmp_path):
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    # Create agent vault
    agent_vault = await vault.create_agent_vault("test-agent")
    assert agent_vault.exists()
    assert (agent_vault / "context").exists()
    
    # Write and read file
    await vault.write_file("agents/test-agent/context/test.md", "# Test")
    content = await vault.read_file("agents/test-agent/context/test.md")
    assert content == "# Test"
    
    # Create snapshot
    snapshot = await vault.create_snapshot("test-snapshot")
    assert snapshot.exists()
    
    # Modify file
    await vault.write_file("agents/test-agent/context/test.md", "# Modified")
    
    # Restore snapshot
    await vault.restore_snapshot("test-snapshot")
    content = await vault.read_file("agents/test-agent/context/test.md")
    assert content == "# Test"
```

- [ ] **Step 6: Run integration test**

Run: `pytest tests/integration/test_vault_integration.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/storage/obsidian.py tests/
git commit -m "feat: add Obsidian vault integration

- Add vault initialization and management
- Add agent vault creation
- Add file read/write operations
- Add snapshot and restore functionality
- Add integration tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

## Task 5: Event Store (Event Sourcing)

**Files:**
- Create: `src/meai/storage/event_store.py`
- Create: `tests/unit/test_event_store.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_event_store.py
import pytest
from meai.storage.event_store import EventStore
from meai.storage.database import Database

@pytest.mark.asyncio
async def test_append_and_replay_events():
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    store = EventStore(db)
    
    # Append events
    await store.append("agent-1", "agent", "agent_created", {"name": "test"})
    await store.append("agent-1", "agent", "agent_updated", {"status": "active"})
    
    # Replay events
    events = await store.replay("agent-1", "agent")
    assert len(events) == 2
    assert events[0].event_type == "agent_created"
    assert events[1].event_type == "agent_updated"
    
    await db.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_event_store.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/storage/event_store.py**

```python
"""Event sourcing - immutable event log with replay capability"""

from datetime import datetime
from typing import Any
from uuid import uuid4
from sqlalchemy import select
import structlog

from .database import Database
from .models import Event

logger = structlog.get_logger()


class EventStore:
    """Event sourcing store - append-only event log"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def append(
        self,
        aggregate_id: str,
        aggregate_type: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> str:
        """Append event to immutable log"""
        event_id = f"evt-{uuid4().hex[:16]}"
        
        async for session in self.db.session():
            event = Event(
                event_id=event_id,
                event_type=event_type,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                payload=payload,
                timestamp=datetime.utcnow(),
            )
            session.add(event)
        
        logger.info(
            "event.appended",
            event_id=event_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
        )
        
        return event_id
    
    async def replay(
        self,
        aggregate_id: str,
        aggregate_type: str,
        from_timestamp: datetime | None = None,
    ) -> list[Event]:
        """Replay events for an aggregate"""
        async for session in self.db.session():
            query = select(Event).where(
                Event.aggregate_id == aggregate_id,
                Event.aggregate_type == aggregate_type,
            )
            
            if from_timestamp:
                query = query.where(Event.timestamp >= from_timestamp)
            
            query = query.order_by(Event.timestamp.asc())
            
            result = await session.execute(query)
            events = list(result.scalars().all())
        
        logger.info(
            "event.replayed",
            aggregate_id=aggregate_id,
            count=len(events),
        )
        
        return events
    
    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100,
    ) -> list[Event]:
        """Get events by type"""
        async for session in self.db.session():
            query = (
                select(Event)
                .where(Event.event_type == event_type)
                .order_by(Event.timestamp.desc())
                .limit(limit)
            )
            
            result = await session.execute(query)
            events = list(result.scalars().all())
        
        return events
    
    async def get_recent_events(self, limit: int = 100) -> list[Event]:
        """Get recent events across all aggregates"""
        async for session in self.db.session():
            query = (
                select(Event)
                .order_by(Event.timestamp.desc())
                .limit(limit)
            )
            
            result = await session.execute(query)
            events = list(result.scalars().all())
        
        return events
    
    async def count_events(
        self,
        aggregate_id: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """Count events with optional filters"""
        from sqlalchemy import func
        
        async for session in self.db.session():
            query = select(func.count(Event.id))
            
            if aggregate_id:
                query = query.where(Event.aggregate_id == aggregate_id)
            
            if event_type:
                query = query.where(Event.event_type == event_type)
            
            result = await session.execute(query)
            count = result.scalar_one()
        
        return count
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_event_store.py -v`
Expected: PASS

- [ ] **Step 5: Add comprehensive tests**

```python
# tests/unit/test_event_store.py (add more tests)

@pytest.mark.asyncio
async def test_event_immutability():
    """Events cannot be modified after append"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    store = EventStore(db)
    event_id = await store.append("agent-1", "agent", "created", {"name": "test"})
    
    # Try to modify event (should not be possible through EventStore API)
    # EventStore only has append and read operations
    events = await store.replay("agent-1", "agent")
    assert len(events) == 1
    assert events[0].event_id == event_id
    
    await db.disconnect()


@pytest.mark.asyncio
async def test_replay_from_timestamp():
    """Replay events from specific timestamp"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    store = EventStore(db)
    
    # Append events
    await store.append("agent-1", "agent", "event1", {})
    checkpoint = datetime.utcnow()
    await store.append("agent-1", "agent", "event2", {})
    await store.append("agent-1", "agent", "event3", {})
    
    # Replay from checkpoint
    events = await store.replay("agent-1", "agent", from_timestamp=checkpoint)
    assert len(events) == 2
    assert events[0].event_type == "event2"
    
    await db.disconnect()


@pytest.mark.asyncio
async def test_get_events_by_type():
    """Get all events of specific type"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    store = EventStore(db)
    
    await store.append("agent-1", "agent", "created", {})
    await store.append("agent-2", "agent", "created", {})
    await store.append("agent-1", "agent", "updated", {})
    
    created_events = await store.get_events_by_type("created")
    assert len(created_events) == 2
    
    await db.disconnect()
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/unit/test_event_store.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/storage/event_store.py tests/unit/test_event_store.py
git commit -m "feat: add event sourcing with replay capability

- Add EventStore with append-only log
- Add event replay by aggregate
- Add event queries by type and timestamp
- Add immutability guarantees
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Event Bus (Async Message Queue)

**Files:**
- Create: `src/meai/messaging/__init__.py`
- Create: `src/meai/messaging/event_bus.py`
- Create: `src/meai/messaging/message.py`
- Create: `tests/unit/test_event_bus.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_event_bus.py
import pytest
from meai.messaging.event_bus import EventBus
from meai.messaging.message import Message

@pytest.mark.asyncio
async def test_publish_and_consume():
    bus = EventBus()
    await bus.start()
    
    # Publish message
    msg = Message(
        from_agent="agent-1",
        to_agent="agent-2",
        message_type="test",
        payload={"data": "hello"}
    )
    await bus.publish(msg)
    
    # Consume message
    received = await bus.consume("agent-2")
    assert received.message_id == msg.message_id
    assert received.payload["data"] == "hello"
    
    await bus.stop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_event_bus.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/messaging/__init__.py**

```python
"""Messaging layer - async event bus and message queue"""

from .event_bus import EventBus
from .message import Message, MessagePriority

__all__ = ["EventBus", "Message", "MessagePriority"]
```

- [ ] **Step 4: Create src/meai/messaging/message.py**

```python
"""Message models for event bus"""

from datetime import datetime
from enum import IntEnum
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class MessagePriority(IntEnum):
    """Message priority levels"""
    CRITICAL = 0  # P0 - immediate (alerts, failures)
    HIGH = 1      # P1 - urgent (strategic decisions)
    MEDIUM = 2    # P2 - normal (optimization, analysis)
    LOW = 3       # P3 - background (planning, reports)


class Message(BaseModel):
    """Message for event bus"""
    
    message_id: str = Field(default_factory=lambda: f"msg-{uuid4().hex[:16]}")
    from_agent: str
    to_agent: str
    message_type: str
    priority: MessagePriority = MessagePriority.MEDIUM
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __lt__(self, other: "Message") -> bool:
        """Compare messages by priority (for priority queue)"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at
```

- [ ] **Step 5: Create src/meai/messaging/event_bus.py**

```python
"""Async event bus with priority queue and pub/sub"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any
import structlog

from .message import Message, MessagePriority
from ..storage.database import Database
from ..storage.models import Message as MessageModel

logger = structlog.get_logger()


class EventBus:
    """Async event bus with priority queue"""
    
    def __init__(self, db: Database | None = None):
        self.db = db
        self.queues: dict[str, asyncio.PriorityQueue] = defaultdict(asyncio.PriorityQueue)
        self.running = False
        self._tasks: list[asyncio.Task] = []
    
    async def start(self) -> None:
        """Start event bus"""
        self.running = True
        logger.info("event_bus.started")
    
    async def stop(self) -> None:
        """Stop event bus and cancel all tasks"""
        self.running = False
        
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("event_bus.stopped")
    
    async def publish(self, message: Message) -> None:
        """Publish message to event bus"""
        # Add to in-memory queue
        await self.queues[message.to_agent].put((message.priority, message))
        
        # Persist to database if available
        if self.db:
            async for session in self.db.session():
                msg_model = MessageModel(
                    message_id=message.message_id,
                    from_agent=message.from_agent,
                    to_agent=message.to_agent,
                    message_type=message.message_type,
                    priority=message.priority,
                    payload=message.payload,
                    status="pending",
                    created_at=message.created_at,
                )
                session.add(msg_model)
        
        logger.info(
            "event_bus.published",
            message_id=message.message_id,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            priority=message.priority.name,
        )
    
    async def consume(self, agent_id: str, timeout: float | None = None) -> Message:
        """Consume message from queue"""
        try:
            priority, message = await asyncio.wait_for(
                self.queues[agent_id].get(),
                timeout=timeout,
            )
            
            # Mark as processed in database
            if self.db:
                async for session in self.db.session():
                    from sqlalchemy import update
                    stmt = (
                        update(MessageModel)
                        .where(MessageModel.message_id == message.message_id)
                        .values(status="processed", processed_at=datetime.utcnow())
                    )
                    await session.execute(stmt)
            
            logger.info(
                "event_bus.consumed",
                message_id=message.message_id,
                agent=agent_id,
            )
            
            return message
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"No messages for {agent_id} within {timeout}s")
    
    async def subscribe(
        self,
        agent_id: str,
        callback: Any,
    ) -> None:
        """Subscribe to messages with callback"""
        async def _consumer():
            while self.running:
                try:
                    message = await self.consume(agent_id, timeout=1.0)
                    await callback(message)
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.error("event_bus.callback_error", error=str(e))
        
        task = asyncio.create_task(_consumer())
        self._tasks.append(task)
        
        logger.info("event_bus.subscribed", agent=agent_id)
    
    def queue_size(self, agent_id: str) -> int:
        """Get queue size for agent"""
        return self.queues[agent_id].qsize()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/unit/test_event_bus.py -v`
Expected: PASS

- [ ] **Step 7: Add comprehensive tests**

```python
# tests/unit/test_event_bus.py (add more tests)

@pytest.mark.asyncio
async def test_priority_ordering():
    """Messages are consumed in priority order"""
    bus = EventBus()
    await bus.start()
    
    # Publish messages with different priorities
    await bus.publish(Message(
        from_agent="a1", to_agent="a2",
        message_type="test", priority=MessagePriority.LOW,
        payload={"order": 3}
    ))
    await bus.publish(Message(
        from_agent="a1", to_agent="a2",
        message_type="test", priority=MessagePriority.CRITICAL,
        payload={"order": 1}
    ))
    await bus.publish(Message(
        from_agent="a1", to_agent="a2",
        message_type="test", priority=MessagePriority.HIGH,
        payload={"order": 2}
    ))
    
    # Consume in priority order
    msg1 = await bus.consume("a2")
    msg2 = await bus.consume("a2")
    msg3 = await bus.consume("a2")
    
    assert msg1.payload["order"] == 1
    assert msg2.payload["order"] == 2
    assert msg3.payload["order"] == 3
    
    await bus.stop()


@pytest.mark.asyncio
async def test_subscribe_callback():
    """Subscribe with callback function"""
    bus = EventBus()
    await bus.start()
    
    received = []
    
    async def callback(msg: Message):
        received.append(msg)
    
    await bus.subscribe("agent-2", callback)
    
    # Publish message
    await bus.publish(Message(
        from_agent="agent-1",
        to_agent="agent-2",
        message_type="test",
        payload={"data": "hello"}
    ))
    
    # Wait for callback
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    assert received[0].payload["data"] == "hello"
    
    await bus.stop()
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/unit/test_event_bus.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add src/meai/messaging/ tests/unit/test_event_bus.py
git commit -m "feat: add async event bus with priority queue

- Add Message model with priority levels (P0-P3)
- Add EventBus with pub/sub pattern
- Add priority queue ordering
- Add subscribe with callback support
- Add database persistence for messages
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Agent Factory Core

**Files:**
- Create: `src/meai/factory/__init__.py`
- Create: `src/meai/factory/agent_factory.py`
- Create: `src/meai/factory/prompt_generator.py`
- Create: `tests/unit/test_agent_factory.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_agent_factory.py
import pytest
from pathlib import Path
from meai.factory.agent_factory import AgentFactory
from meai.storage.obsidian import ObsidianVault

@pytest.mark.asyncio
async def test_create_agent(tmp_path):
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    factory = AgentFactory(vault)
    
    agent = await factory.create_agent(
        name="test-agent",
        agent_type="subagent",
        department="seo",
    )
    
    assert agent["name"] == "test-agent"
    assert agent["vault_path"].exists()
    assert agent["prompt_file"].exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_agent_factory.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/factory/__init__.py**

```python
"""Agent factory - creates agents with vaults and prompts"""

from .agent_factory import AgentFactory
from .prompt_generator import PromptGenerator

__all__ = ["AgentFactory", "PromptGenerator"]
```

- [ ] **Step 4: Create src/meai/factory/prompt_generator.py**

```python
"""Prompt generator for agents"""

from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger()


class PromptGenerator:
    """Generate prompts for agents"""
    
    PROMPT_TEMPLATE = """# {agent_name}

**Type:** {agent_type}
**Department:** {department}
**Vault:** {vault_path}

## Role

{role_description}

## Responsibilities

{responsibilities}

## Knowledge Access

- **Own Vault:** {vault_path}
- **Shared Knowledge:** Access via search when needed
- **Cross-Department:** Request through magister

## Communication

- **Reports to:** {reports_to}
- **Event Bus:** Use for async communication
- **Priority:** Follow P0-P3 priority system

## Safety Rules

- Max delegation depth: 5 levels
- Operation timeout: 5 minutes
- Context limit: 40% (auto-compact at 50%)

## Instructions

{instructions}
"""
    
    def generate(
        self,
        agent_name: str,
        agent_type: str,
        department: str,
        vault_path: Path,
        **kwargs: Any,
    ) -> str:
        """Generate prompt for agent"""
        
        # Default values
        role_description = kwargs.get(
            "role_description",
            f"A {agent_type} agent in the {department} department."
        )
        
        responsibilities = kwargs.get(
            "responsibilities",
            "- Execute assigned tasks\n- Report status\n- Learn from experience"
        )
        
        reports_to = kwargs.get("reports_to", f"{department}-magister")
        
        instructions = kwargs.get(
            "instructions",
            "Follow department guidelines and magister instructions."
        )
        
        prompt = self.PROMPT_TEMPLATE.format(
            agent_name=agent_name,
            agent_type=agent_type,
            department=department,
            vault_path=str(vault_path),
            role_description=role_description,
            responsibilities=responsibilities,
            reports_to=reports_to,
            instructions=instructions,
        )
        
        logger.info("prompt.generated", agent=agent_name)
        
        return prompt
```

- [ ] **Step 5: Create src/meai/factory/agent_factory.py**

```python
"""Agent factory - creates agents with vaults and prompts"""

from datetime import datetime
from pathlib import Path
from typing import Any
import structlog

from ..storage.obsidian import ObsidianVault
from .prompt_generator import PromptGenerator

logger = structlog.get_logger()


class AgentFactory:
    """Factory for creating agents"""
    
    def __init__(self, vault: ObsidianVault):
        self.vault = vault
        self.prompt_generator = PromptGenerator()
    
    async def create_agent(
        self,
        name: str,
        agent_type: str,
        department: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create agent with vault and prompt"""
        
        logger.info(
            "factory.create_agent",
            name=name,
            type=agent_type,
            department=department,
        )
        
        # Create agent vault
        agent_vault = await self.vault.create_agent_vault(name)
        
        # Generate prompt
        prompt = self.prompt_generator.generate(
            agent_name=name,
            agent_type=agent_type,
            department=department,
            vault_path=agent_vault,
            **kwargs,
        )
        
        # Write prompt to vault
        prompt_file = agent_vault / "PROMPT.md"
        await self.vault.write_file(
            f"agents/{name}/PROMPT.md",
            prompt,
        )
        
        # Create agent metadata
        metadata = {
            "name": name,
            "type": agent_type,
            "department": department,
            "vault_path": agent_vault,
            "prompt_file": prompt_file,
            "created_at": str(datetime.utcnow()),
        }
        
        # Write metadata
        import json
        await self.vault.write_file(
            f"agents/{name}/metadata.json",
            json.dumps(metadata, indent=2, default=str),
        )
        
        logger.info("factory.agent_created", name=name)
        
        return metadata
    
    async def list_agents(self) -> list[dict[str, Any]]:
        """List all created agents"""
        agents_dir = self.vault.vault_path / "agents"
        
        if not agents_dir.exists():
            return []
        
        agents = []
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                metadata_file = agent_dir / "metadata.json"
                if metadata_file.exists():
                    import json
                    content = await self.vault.read_file(
                        f"agents/{agent_dir.name}/metadata.json"
                    )
                    metadata = json.loads(content)
                    agents.append(metadata)
        
        return agents
    
    async def delete_agent(self, name: str) -> None:
        """Delete agent and its vault"""
        agent_vault = self.vault.vault_path / "agents" / name
        
        if not agent_vault.exists():
            raise ValueError(f"Agent not found: {name}")
        
        import shutil
        shutil.rmtree(agent_vault)
        
        logger.info("factory.agent_deleted", name=name)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/unit/test_agent_factory.py -v`
Expected: PASS

- [ ] **Step 7: Add comprehensive tests**

```python
# tests/unit/test_agent_factory.py (add more tests)

@pytest.mark.asyncio
async def test_list_agents(tmp_path):
    """List all created agents"""
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    factory = AgentFactory(vault)
    
    # Create multiple agents
    await factory.create_agent("agent-1", "subagent", "seo")
    await factory.create_agent("agent-2", "subagent", "content")
    
    # List agents
    agents = await factory.list_agents()
    assert len(agents) == 2
    assert agents[0]["name"] == "agent-1"
    assert agents[1]["name"] == "agent-2"


@pytest.mark.asyncio
async def test_delete_agent(tmp_path):
    """Delete agent and its vault"""
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    factory = AgentFactory(vault)
    
    # Create agent
    await factory.create_agent("test-agent", "subagent", "seo")
    
    # Delete agent
    await factory.delete_agent("test-agent")
    
    # Verify deleted
    agents = await factory.list_agents()
    assert len(agents) == 0
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/unit/test_agent_factory.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add src/meai/factory/ tests/unit/test_agent_factory.py
git commit -m "feat: add agent factory with prompt generation

- Add AgentFactory for creating agents
- Add PromptGenerator with template system
- Add agent vault initialization
- Add agent metadata management
- Add list and delete operations
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

## Task 8: Safety Mechanisms - Loop Detector

**Files:**
- Create: `src/meai/safety/__init__.py`
- Create: `src/meai/safety/loop_detector.py`
- Create: `tests/unit/test_loop_detector.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_loop_detector.py
import pytest
from meai.safety.loop_detector import LoopDetector

@pytest.mark.asyncio
async def test_detect_delegation_depth():
    detector = LoopDetector(max_depth=3)
    
    # Track delegation chain
    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")
    detector.track_delegation("agent-3", "agent-4")
    
    # Should detect max depth exceeded
    with pytest.raises(RuntimeError, match="Max delegation depth"):
        detector.track_delegation("agent-4", "agent-5")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_loop_detector.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/safety/__init__.py**

```python
"""Safety mechanisms - loop detection, timeouts, context monitoring"""

from .loop_detector import LoopDetector
from .timeout_manager import TimeoutManager
from .context_monitor import ContextMonitor
from .shutdown_handler import ShutdownHandler

__all__ = [
    "LoopDetector",
    "TimeoutManager",
    "ContextMonitor",
    "ShutdownHandler",
]
```

- [ ] **Step 4: Create src/meai/safety/loop_detector.py**

```python
"""Loop detection - prevent infinite delegation chains"""

from collections import defaultdict
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class LoopDetector:
    """Detect and prevent infinite loops in agent delegation"""
    
    def __init__(self, max_depth: int = 5, max_self_calls: int = 3):
        self.max_depth = max_depth
        self.max_self_calls = max_self_calls
        
        # Track delegation chains
        self.chains: dict[str, list[str]] = {}
        
        # Track self-calls per agent
        self.self_calls: dict[str, int] = defaultdict(int)
        
        # Track call timestamps for cleanup
        self.timestamps: dict[str, datetime] = {}
    
    def track_delegation(self, from_agent: str, to_agent: str) -> None:
        """Track delegation and check for loops"""
        
        # Initialize chain if not exists
        if from_agent not in self.chains:
            self.chains[from_agent] = [from_agent]
        
        # Check for self-call
        if from_agent == to_agent:
            self.self_calls[from_agent] += 1
            
            if self.self_calls[from_agent] > self.max_self_calls:
                logger.error(
                    "loop.self_call_exceeded",
                    agent=from_agent,
                    count=self.self_calls[from_agent],
                )
                raise RuntimeError(
                    f"Agent {from_agent} called itself {self.self_calls[from_agent]} times"
                )
        
        # Build chain for to_agent
        chain = self.chains[from_agent] + [to_agent]
        
        # Check depth
        if len(chain) > self.max_depth:
            logger.error(
                "loop.depth_exceeded",
                chain=chain,
                depth=len(chain),
            )
            raise RuntimeError(
                f"Max delegation depth {self.max_depth} exceeded: {' -> '.join(chain)}"
            )
        
        # Check for circular delegation
        if to_agent in self.chains[from_agent]:
            logger.error(
                "loop.circular_detected",
                chain=chain,
            )
            raise RuntimeError(
                f"Circular delegation detected: {' -> '.join(chain)}"
            )
        
        # Update chain
        self.chains[to_agent] = chain
        self.timestamps[to_agent] = datetime.utcnow()
        
        logger.debug(
            "loop.delegation_tracked",
            from_agent=from_agent,
            to_agent=to_agent,
            depth=len(chain),
        )
    
    def reset_agent(self, agent_id: str) -> None:
        """Reset tracking for an agent"""
        if agent_id in self.chains:
            del self.chains[agent_id]
        if agent_id in self.self_calls:
            del self.self_calls[agent_id]
        if agent_id in self.timestamps:
            del self.timestamps[agent_id]
        
        logger.debug("loop.agent_reset", agent=agent_id)
    
    def cleanup_old_chains(self, max_age: timedelta = timedelta(hours=1)) -> None:
        """Clean up old delegation chains"""
        now = datetime.utcnow()
        to_remove = []
        
        for agent_id, timestamp in self.timestamps.items():
            if now - timestamp > max_age:
                to_remove.append(agent_id)
        
        for agent_id in to_remove:
            self.reset_agent(agent_id)
        
        if to_remove:
            logger.info("loop.cleanup", removed=len(to_remove))
    
    def get_chain(self, agent_id: str) -> list[str]:
        """Get delegation chain for agent"""
        return self.chains.get(agent_id, [])
    
    def get_depth(self, agent_id: str) -> int:
        """Get current delegation depth for agent"""
        return len(self.chains.get(agent_id, []))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_loop_detector.py -v`
Expected: PASS

- [ ] **Step 6: Add comprehensive tests**

```python
# tests/unit/test_loop_detector.py (add more tests)

@pytest.mark.asyncio
async def test_detect_circular_delegation():
    """Detect circular delegation loops"""
    detector = LoopDetector()
    
    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")
    
    # Try to create circular loop
    with pytest.raises(RuntimeError, match="Circular delegation"):
        detector.track_delegation("agent-3", "agent-1")


@pytest.mark.asyncio
async def test_detect_self_calls():
    """Detect excessive self-calls"""
    detector = LoopDetector(max_self_calls=2)
    
    detector.track_delegation("agent-1", "agent-1")
    detector.track_delegation("agent-1", "agent-1")
    
    # Third self-call should fail
    with pytest.raises(RuntimeError, match="called itself"):
        detector.track_delegation("agent-1", "agent-1")


@pytest.mark.asyncio
async def test_reset_agent():
    """Reset tracking for agent"""
    detector = LoopDetector()
    
    detector.track_delegation("agent-1", "agent-2")
    assert detector.get_depth("agent-2") == 2
    
    detector.reset_agent("agent-2")
    assert detector.get_depth("agent-2") == 0


@pytest.mark.asyncio
async def test_cleanup_old_chains():
    """Clean up old delegation chains"""
    from datetime import timedelta
    
    detector = LoopDetector()
    
    detector.track_delegation("agent-1", "agent-2")
    
    # Manually set old timestamp
    detector.timestamps["agent-2"] = datetime.utcnow() - timedelta(hours=2)
    
    # Cleanup
    detector.cleanup_old_chains(max_age=timedelta(hours=1))
    
    assert detector.get_depth("agent-2") == 0
```

- [ ] **Step 7: Run all tests**

Run: `pytest tests/unit/test_loop_detector.py -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/meai/safety/loop_detector.py tests/unit/test_loop_detector.py
git commit -m "feat: add loop detection for agent delegation

- Add LoopDetector with max depth enforcement
- Add circular delegation detection
- Add self-call tracking and limits
- Add chain cleanup for old delegations
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Safety Mechanisms - Timeout Manager

**Files:**
- Create: `src/meai/safety/timeout_manager.py`
- Create: `tests/unit/test_timeout_manager.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_timeout_manager.py
import pytest
import asyncio
from meai.safety.timeout_manager import TimeoutManager

@pytest.mark.asyncio
async def test_operation_timeout():
    manager = TimeoutManager(default_timeout=1.0)
    
    async def slow_operation():
        await asyncio.sleep(2.0)
        return "done"
    
    # Should timeout
    with pytest.raises(asyncio.TimeoutError):
        await manager.run_with_timeout(slow_operation())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_timeout_manager.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/safety/timeout_manager.py**

```python
"""Timeout manager - enforce operation timeouts"""

import asyncio
from typing import Any, Coroutine, TypeVar
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class TimeoutManager:
    """Manage operation timeouts with graceful cancellation"""
    
    def __init__(self, default_timeout: float = 300.0):  # 5 minutes default
        self.default_timeout = default_timeout
        self.active_operations: dict[str, asyncio.Task] = {}
    
    async def run_with_timeout(
        self,
        coro: Coroutine[Any, Any, T],
        timeout: float | None = None,
        operation_id: str | None = None,
    ) -> T:
        """Run coroutine with timeout"""
        timeout = timeout or self.default_timeout
        
        if operation_id:
            logger.info(
                "timeout.operation_started",
                operation_id=operation_id,
                timeout=timeout,
            )
        
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            
            if operation_id:
                logger.info("timeout.operation_completed", operation_id=operation_id)
            
            return result
        
        except asyncio.TimeoutError:
            if operation_id:
                logger.error(
                    "timeout.operation_exceeded",
                    operation_id=operation_id,
                    timeout=timeout,
                )
            raise
        
        finally:
            if operation_id and operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    async def run_with_timeout_tracked(
        self,
        coro: Coroutine[Any, Any, T],
        operation_id: str,
        timeout: float | None = None,
    ) -> T:
        """Run coroutine with timeout and track it"""
        task = asyncio.create_task(coro)
        self.active_operations[operation_id] = task
        
        try:
            return await self.run_with_timeout(
                task,
                timeout=timeout,
                operation_id=operation_id,
            )
        except asyncio.TimeoutError:
            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise
    
    async def cancel_operation(self, operation_id: str) -> None:
        """Cancel a tracked operation"""
        if operation_id not in self.active_operations:
            logger.warning("timeout.operation_not_found", operation_id=operation_id)
            return
        
        task = self.active_operations[operation_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            logger.info("timeout.operation_cancelled", operation_id=operation_id)
        
        del self.active_operations[operation_id]
    
    async def cancel_all(self) -> None:
        """Cancel all active operations"""
        operation_ids = list(self.active_operations.keys())
        
        for operation_id in operation_ids:
            await self.cancel_operation(operation_id)
        
        logger.info("timeout.all_cancelled", count=len(operation_ids))
    
    def get_active_operations(self) -> list[str]:
        """Get list of active operation IDs"""
        return list(self.active_operations.keys())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_timeout_manager.py -v`
Expected: PASS

- [ ] **Step 5: Add comprehensive tests**

```python
# tests/unit/test_timeout_manager.py (add more tests)

@pytest.mark.asyncio
async def test_operation_completes_within_timeout():
    """Operation completes successfully within timeout"""
    manager = TimeoutManager(default_timeout=2.0)
    
    async def fast_operation():
        await asyncio.sleep(0.1)
        return "done"
    
    result = await manager.run_with_timeout(fast_operation())
    assert result == "done"


@pytest.mark.asyncio
async def test_cancel_operation():
    """Cancel a tracked operation"""
    manager = TimeoutManager()
    
    async def long_operation():
        await asyncio.sleep(10.0)
        return "done"
    
    # Start operation in background
    task = asyncio.create_task(
        manager.run_with_timeout_tracked(
            long_operation(),
            operation_id="op-1",
        )
    )
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Cancel it
    await manager.cancel_operation("op-1")
    
    # Task should be cancelled
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_cancel_all_operations():
    """Cancel all active operations"""
    manager = TimeoutManager()
    
    async def long_operation():
        await asyncio.sleep(10.0)
        return "done"
    
    # Start multiple operations
    tasks = [
        asyncio.create_task(
            manager.run_with_timeout_tracked(long_operation(), f"op-{i}")
        )
        for i in range(3)
    ]
    
    await asyncio.sleep(0.1)
    
    # Cancel all
    await manager.cancel_all()
    
    # All tasks should be cancelled
    for task in tasks:
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_get_active_operations():
    """Get list of active operations"""
    manager = TimeoutManager()
    
    async def long_operation():
        await asyncio.sleep(10.0)
    
    # Start operations
    tasks = [
        asyncio.create_task(
            manager.run_with_timeout_tracked(long_operation(), f"op-{i}")
        )
        for i in range(3)
    ]
    
    await asyncio.sleep(0.1)
    
    active = manager.get_active_operations()
    assert len(active) == 3
    assert "op-0" in active
    
    # Cleanup
    await manager.cancel_all()
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/unit/test_timeout_manager.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/safety/timeout_manager.py tests/unit/test_timeout_manager.py
git commit -m "feat: add timeout manager with graceful cancellation

- Add TimeoutManager with configurable timeouts
- Add operation tracking and cancellation
- Add cancel all operations support
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 10: Safety Mechanisms - Context Monitor

**Files:**
- Create: `src/meai/safety/context_monitor.py`
- Create: `tests/unit/test_context_monitor.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_context_monitor.py
import pytest
from meai.safety.context_monitor import ContextMonitor

def test_context_usage_tracking():
    monitor = ContextMonitor(max_tokens=100000, warning_threshold=0.4)
    
    # Track usage
    monitor.track_usage(30000)
    assert monitor.get_usage_percent() == 0.3
    
    # Add more
    monitor.track_usage(15000)
    assert monitor.get_usage_percent() == 0.45
    
    # Should trigger warning
    assert monitor.should_warn()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_context_monitor.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/safety/context_monitor.py**

```python
"""Context monitor - enforce 40% rule and prevent context explosion"""

import structlog

logger = structlog.get_logger()


class ContextMonitor:
    """Monitor context usage and enforce limits"""
    
    def __init__(
        self,
        max_tokens: int = 200000,
        warning_threshold: float = 0.4,
        critical_threshold: float = 0.5,
    ):
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        self.current_tokens = 0
        self.warned = False
    
    def track_usage(self, tokens: int) -> None:
        """Track token usage"""
        self.current_tokens = tokens
        
        usage_percent = self.get_usage_percent()
        
        if usage_percent >= self.critical_threshold:
            logger.error(
                "context.critical",
                tokens=tokens,
                max_tokens=self.max_tokens,
                percent=usage_percent,
            )
        elif usage_percent >= self.warning_threshold and not self.warned:
            logger.warning(
                "context.warning",
                tokens=tokens,
                max_tokens=self.max_tokens,
                percent=usage_percent,
            )
            self.warned = True
    
    def get_usage_percent(self) -> float:
        """Get current usage as percentage"""
        return self.current_tokens / self.max_tokens
    
    def should_warn(self) -> bool:
        """Check if warning threshold exceeded"""
        return self.get_usage_percent() >= self.warning_threshold
    
    def should_compact(self) -> bool:
        """Check if auto-compact should trigger"""
        return self.get_usage_percent() >= self.critical_threshold
    
    def reset(self) -> None:
        """Reset tracking"""
        self.current_tokens = 0
        self.warned = False
        logger.info("context.reset")
    
    def get_remaining_tokens(self) -> int:
        """Get remaining tokens"""
        return self.max_tokens - self.current_tokens
    
    def get_status(self) -> dict[str, Any]:
        """Get current status"""
        usage_percent = self.get_usage_percent()
        
        if usage_percent >= self.critical_threshold:
            status = "critical"
        elif usage_percent >= self.warning_threshold:
            status = "warning"
        else:
            status = "ok"
        
        return {
            "status": status,
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": usage_percent,
            "remaining_tokens": self.get_remaining_tokens(),
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_context_monitor.py -v`
Expected: PASS

- [ ] **Step 5: Add comprehensive tests**

```python
# tests/unit/test_context_monitor.py (add more tests)

def test_should_compact():
    """Check if auto-compact should trigger"""
    monitor = ContextMonitor(max_tokens=100000, critical_threshold=0.5)
    
    monitor.track_usage(40000)
    assert not monitor.should_compact()
    
    monitor.track_usage(55000)
    assert monitor.should_compact()


def test_reset():
    """Reset tracking"""
    monitor = ContextMonitor(max_tokens=100000)
    
    monitor.track_usage(50000)
    assert monitor.current_tokens == 50000
    
    monitor.reset()
    assert monitor.current_tokens == 0
    assert not monitor.warned


def test_get_status():
    """Get current status"""
    monitor = ContextMonitor(max_tokens=100000)
    
    monitor.track_usage(30000)
    status = monitor.get_status()
    
    assert status["status"] == "ok"
    assert status["current_tokens"] == 30000
    assert status["usage_percent"] == 0.3
    assert status["remaining_tokens"] == 70000
    
    monitor.track_usage(45000)
    status = monitor.get_status()
    assert status["status"] == "warning"
    
    monitor.track_usage(55000)
    status = monitor.get_status()
    assert status["status"] == "critical"
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/unit/test_context_monitor.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/safety/context_monitor.py tests/unit/test_context_monitor.py
git commit -m "feat: add context monitor with 40% rule enforcement

- Add ContextMonitor with configurable thresholds
- Add warning and critical level detection
- Add auto-compact trigger logic
- Add status reporting
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 11: Safety Mechanisms - Shutdown Handler

**Files:**
- Create: `src/meai/safety/shutdown_handler.py`
- Create: `tests/unit/test_shutdown_handler.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_shutdown_handler.py
import pytest
import signal
from meai.safety.shutdown_handler import ShutdownHandler

@pytest.mark.asyncio
async def test_register_cleanup():
    handler = ShutdownHandler()
    
    cleanup_called = []
    
    async def cleanup():
        cleanup_called.append(True)
    
    handler.register_cleanup(cleanup)
    
    # Trigger shutdown
    await handler.shutdown()
    
    assert len(cleanup_called) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_shutdown_handler.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/safety/shutdown_handler.py**

```python
"""Graceful shutdown handler with cleanup"""

import asyncio
import signal
from typing import Callable, Coroutine, Any
import structlog

logger = structlog.get_logger()


class ShutdownHandler:
    """Handle graceful shutdown with cleanup"""
    
    def __init__(self):
        self.cleanup_callbacks: list[Callable[[], Coroutine[Any, Any, None]]] = []
        self.shutdown_event = asyncio.Event()
        self.is_shutting_down = False
    
    def register_cleanup(
        self,
        callback: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """Register cleanup callback"""
        self.cleanup_callbacks.append(callback)
        logger.debug("shutdown.callback_registered")
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for SIGINT and SIGTERM"""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s)),
            )
        
        logger.info("shutdown.signals_registered")
    
    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal"""
        logger.info("shutdown.signal_received", signal=sig.name)
        await self.shutdown()
    
    async def shutdown(self) -> None:
        """Execute graceful shutdown"""
        if self.is_shutting_down:
            logger.warning("shutdown.already_in_progress")
            return
        
        self.is_shutting_down = True
        logger.info("shutdown.started")
        
        # Run cleanup callbacks
        for i, callback in enumerate(self.cleanup_callbacks):
            try:
                logger.info("shutdown.cleanup", step=i+1, total=len(self.cleanup_callbacks))
                await callback()
            except Exception as e:
                logger.error("shutdown.cleanup_failed", step=i+1, error=str(e))
        
        # Set shutdown event
        self.shutdown_event.set()
        
        logger.info("shutdown.completed")
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal"""
        await self.shutdown_event.wait()
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown was requested"""
        return self.shutdown_event.is_set()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_shutdown_handler.py -v`
Expected: PASS

- [ ] **Step 5: Add comprehensive tests**

```python
# tests/unit/test_shutdown_handler.py (add more tests)

@pytest.mark.asyncio
async def test_multiple_cleanup_callbacks():
    """Execute multiple cleanup callbacks in order"""
    handler = ShutdownHandler()
    
    order = []
    
    async def cleanup1():
        order.append(1)
    
    async def cleanup2():
        order.append(2)
    
    async def cleanup3():
        order.append(3)
    
    handler.register_cleanup(cleanup1)
    handler.register_cleanup(cleanup2)
    handler.register_cleanup(cleanup3)
    
    await handler.shutdown()
    
    assert order == [1, 2, 3]


@pytest.mark.asyncio
async def test_cleanup_error_handling():
    """Continue cleanup even if one callback fails"""
    handler = ShutdownHandler()
    
    executed = []
    
    async def cleanup1():
        executed.append(1)
    
    async def cleanup2():
        raise RuntimeError("Cleanup failed")
    
    async def cleanup3():
        executed.append(3)
    
    handler.register_cleanup(cleanup1)
    handler.register_cleanup(cleanup2)
    handler.register_cleanup(cleanup3)
    
    await handler.shutdown()
    
    # Should execute all callbacks despite error
    assert executed == [1, 3]


@pytest.mark.asyncio
async def test_shutdown_idempotent():
    """Shutdown can be called multiple times safely"""
    handler = ShutdownHandler()
    
    call_count = []
    
    async def cleanup():
        call_count.append(1)
    
    handler.register_cleanup(cleanup)
    
    await handler.shutdown()
    await handler.shutdown()
    await handler.shutdown()
    
    # Cleanup should only run once
    assert len(call_count) == 1
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/unit/test_shutdown_handler.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/safety/shutdown_handler.py tests/unit/test_shutdown_handler.py
git commit -m "feat: add graceful shutdown handler

- Add ShutdownHandler with cleanup callbacks
- Add signal handler setup (SIGINT, SIGTERM)
- Add error handling in cleanup
- Add idempotent shutdown
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Execution Notes

**Context Management:**
- This is a LARGE plan (20+ tasks)
- Use `/clear` between major tasks to stay under 40% context
- Save progress after each commit

**Testing:**
- Run tests after EVERY task
- Don't proceed if tests fail
- Maintain > 80% code coverage

**Commits:**
- Commit after each task completion
- Use conventional commits format
- Include Co-Authored-By line

---

## Task 12: Monitoring - Health Checks

**Files:**
- Create: `src/meai/monitoring/__init__.py`
- Create: `src/meai/monitoring/health.py`
- Create: `tests/unit/test_health.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_health.py
import pytest
from meai.monitoring.health import HealthChecker

@pytest.mark.asyncio
async def test_health_check():
    checker = HealthChecker()
    
    # Register component
    async def db_health():
        return {"status": "healthy"}
    
    checker.register_component("database", db_health)
    
    # Check health
    health = await checker.check_health()
    assert health["status"] == "healthy"
    assert "database" in health["components"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_health.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/monitoring/__init__.py**

```python
"""Monitoring - health checks and metrics"""

from .health import HealthChecker
from .metrics import MetricsCollector

__all__ = ["HealthChecker", "MetricsCollector"]
```

- [ ] **Step 4: Create src/meai/monitoring/health.py**

```python
"""Health check system"""

from datetime import datetime
from typing import Callable, Coroutine, Any
import structlog

logger = structlog.get_logger()


class HealthChecker:
    """System health checker"""
    
    def __init__(self):
        self.components: dict[str, Callable[[], Coroutine[Any, Any, dict]]] = {}
        self.start_time = datetime.utcnow()
    
    def register_component(
        self,
        name: str,
        health_check: Callable[[], Coroutine[Any, Any, dict]],
    ) -> None:
        """Register component health check"""
        self.components[name] = health_check
        logger.debug("health.component_registered", component=name)
    
    async def check_health(self) -> dict[str, Any]:
        """Check health of all components"""
        components_health = {}
        overall_healthy = True
        
        for name, check_func in self.components.items():
            try:
                result = await check_func()
                components_health[name] = result
                
                if result.get("status") != "healthy":
                    overall_healthy = False
            
            except Exception as e:
                logger.error("health.check_failed", component=name, error=str(e))
                components_health[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                overall_healthy = False
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "components": components_health,
        }
    
    async def check_component(self, name: str) -> dict[str, Any]:
        """Check health of specific component"""
        if name not in self.components:
            return {"status": "unknown", "error": "Component not registered"}
        
        try:
            return await self.components[name]()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_health.py -v`
Expected: PASS

- [ ] **Step 6: Add comprehensive tests**

```python
# tests/unit/test_health.py (add more tests)

@pytest.mark.asyncio
async def test_unhealthy_component():
    """Detect unhealthy component"""
    checker = HealthChecker()
    
    async def failing_health():
        return {"status": "unhealthy", "error": "Connection failed"}
    
    checker.register_component("database", failing_health)
    
    health = await checker.check_health()
    assert health["status"] == "unhealthy"
    assert health["components"]["database"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_component_exception():
    """Handle component check exception"""
    checker = HealthChecker()
    
    async def broken_health():
        raise RuntimeError("Check failed")
    
    checker.register_component("broken", broken_health)
    
    health = await checker.check_health()
    assert health["status"] == "unhealthy"
    assert "error" in health["components"]["broken"]


@pytest.mark.asyncio
async def test_check_specific_component():
    """Check specific component health"""
    checker = HealthChecker()
    
    async def db_health():
        return {"status": "healthy"}
    
    checker.register_component("database", db_health)
    
    result = await checker.check_component("database")
    assert result["status"] == "healthy"
```

- [ ] **Step 7: Run all tests**

Run: `pytest tests/unit/test_health.py -v`
Expected: All tests PASS

- [ ] **Step 8: Add Telegram alerting (optional but recommended)**

```python
# src/meai/monitoring/alerting.py
"""Alerting system for health check failures"""

import os
from typing import Optional
import structlog
import httpx

logger = structlog.get_logger()


class TelegramAlerter:
    """Send alerts via Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("telegram.alerting_disabled", reason="missing_credentials")
    
    async def send_alert(self, message: str) -> bool:
        """Send alert message"""
        if not self.enabled:
            logger.debug("telegram.alert_skipped", reason="disabled")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                    },
                    timeout=5.0,
                )
                response.raise_for_status()
                logger.info("telegram.alert_sent")
                return True
        except Exception as e:
            logger.error("telegram.alert_failed", error=str(e))
            return False


class HealthAlerter:
    """Monitor health and send alerts on failures"""
    
    def __init__(self, health_checker, alerter: Optional[TelegramAlerter] = None):
        self.health_checker = health_checker
        self.alerter = alerter or TelegramAlerter()
        self.last_status = {}
    
    async def check_and_alert(self) -> dict:
        """Check health and send alerts if status changed"""
        health = await self.health_checker.check_health()
        
        # Check if status changed
        current_status = health["status"]
        previous_status = self.last_status.get("overall")
        
        if current_status != previous_status:
            if current_status == "unhealthy":
                await self._send_unhealthy_alert(health)
            elif current_status == "healthy" and previous_status == "unhealthy":
                await self._send_recovered_alert()
        
        # Check component status changes
        for component, status in health.get("components", {}).items():
            prev_comp_status = self.last_status.get(component)
            curr_comp_status = status.get("status")
            
            if curr_comp_status != prev_comp_status:
                if curr_comp_status == "unhealthy":
                    await self._send_component_alert(component, status)
        
        # Update last status
        self.last_status["overall"] = current_status
        for component, status in health.get("components", {}).items():
            self.last_status[component] = status.get("status")
        
        return health
    
    async def _send_unhealthy_alert(self, health: dict) -> None:
        """Send alert for unhealthy system"""
        message = "🚨 *meAI System Unhealthy*\n\n"
        
        for component, status in health.get("components", {}).items():
            if status["status"] == "unhealthy":
                error = status.get("error", "Unknown error")
                message += f"❌ {component}: {error}\n"
        
        await self.alerter.send_alert(message)
    
    async def _send_recovered_alert(self) -> None:
        """Send alert for system recovery"""
        message = "✅ *meAI System Recovered*\n\nAll components are healthy."
        await self.alerter.send_alert(message)
    
    async def _send_component_alert(self, component: str, status: dict) -> None:
        """Send alert for component failure"""
        error = status.get("error", "Unknown error")
        message = f"⚠️ *Component Alert*\n\n❌ {component}: {error}"
        await self.alerter.send_alert(message)
```

Add to `.env.example`:
```bash
# Telegram Alerting (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Add test:
```python
# tests/unit/test_alerting.py
import pytest
from meai.monitoring.alerting import TelegramAlerter, HealthAlerter
from meai.monitoring.health import HealthChecker

@pytest.mark.asyncio
async def test_health_alerter():
    """Test health alerting"""
    checker = HealthChecker()
    alerter = HealthAlerter(checker)
    
    # Register healthy component
    async def db_health():
        return {"status": "healthy"}
    
    checker.register_component("database", db_health)
    
    # First check - no alert (initial state)
    health = await alerter.check_and_alert()
    assert health["status"] == "healthy"
    
    # Simulate failure
    async def db_health_fail():
        return {"status": "unhealthy", "error": "Connection failed"}
    
    checker.components["database"] = db_health_fail
    
    # Second check - should detect change
    health = await alerter.check_and_alert()
    assert health["status"] == "unhealthy"
```

- [ ] **Step 9: Commit**

```bash
git add src/meai/monitoring/health.py src/meai/monitoring/alerting.py tests/
git commit -m "feat: add health check system with Telegram alerting

- Add HealthChecker with component registration
- Add overall and per-component health checks
- Add uptime tracking
- Add error handling for failed checks
- Add Telegram alerting for health failures
- Add HealthAlerter for status change detection
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 13: Monitoring - Metrics Collection

**Files:**
- Create: `src/meai/monitoring/metrics.py`
- Create: `tests/unit/test_metrics.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_metrics.py
import pytest
from meai.monitoring.metrics import MetricsCollector
from meai.storage.database import Database

@pytest.mark.asyncio
async def test_record_metric():
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    collector = MetricsCollector(db)
    
    await collector.record_counter("api_calls", 1, {"endpoint": "/health"})
    await collector.record_gauge("memory_usage", 1024.5, {"unit": "MB"})
    
    # Query metrics
    metrics = await collector.get_metrics("api_calls")
    assert len(metrics) == 1
    
    await db.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_metrics.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/monitoring/metrics.py**

```python
"""Metrics collection and storage"""

from datetime import datetime, timedelta
from typing import Any
from sqlalchemy import select, func
import structlog

from ..storage.database import Database
from ..storage.models import Metric

logger = structlog.get_logger()


class MetricsCollector:
    """Collect and store metrics"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def record_counter(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record counter metric"""
        await self._record_metric(name, "counter", value, labels or {})
    
    async def record_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record gauge metric"""
        await self._record_metric(name, "gauge", value, labels or {})
    
    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record histogram metric"""
        await self._record_metric(name, "histogram", value, labels or {})
    
    async def _record_metric(
        self,
        name: str,
        metric_type: str,
        value: float,
        labels: dict[str, str],
    ) -> None:
        """Record metric to database"""
        async with self.db.session() as session:
            metric = Metric(
                metric_name=name,
                metric_type=metric_type,
                value=value,
                labels=labels,
                timestamp=datetime.utcnow(),
            )
            session.add(metric)
        
        logger.debug(
            "metrics.recorded",
            name=name,
            type=metric_type,
            value=value,
        )
    
    async def get_metrics(
        self,
        name: str,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[Metric]:
        """Get metrics by name"""
        async for session in self.db.session():
            query = select(Metric).where(Metric.metric_name == name)
            
            if since:
                query = query.where(Metric.timestamp >= since)
            
            query = query.order_by(Metric.timestamp.desc()).limit(limit)
            
            result = await session.execute(query)
            metrics = list(result.scalars().all())
        
        return metrics
    
    async def get_metric_summary(
        self,
        name: str,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get metric summary statistics"""
        async for session in self.db.session():
            query = select(
                func.count(Metric.id).label("count"),
                func.avg(Metric.value).label("avg"),
                func.min(Metric.value).label("min"),
                func.max(Metric.value).label("max"),
            ).where(Metric.metric_name == name)
            
            if since:
                query = query.where(Metric.timestamp >= since)
            
            result = await session.execute(query)
            row = result.one()
        
        return {
            "name": name,
            "count": row.count or 0,
            "avg": float(row.avg) if row.avg else 0.0,
            "min": float(row.min) if row.min else 0.0,
            "max": float(row.max) if row.max else 0.0,
        }
    
    async def cleanup_old_metrics(
        self,
        older_than: timedelta = timedelta(days=30),
    ) -> int:
        """Clean up old metrics"""
        cutoff = datetime.utcnow() - older_than
        
        async for session in self.db.session():
            from sqlalchemy import delete
            stmt = delete(Metric).where(Metric.timestamp < cutoff)
            result = await session.execute(stmt)
            deleted = result.rowcount
        
        logger.info("metrics.cleanup", deleted=deleted)
        return deleted
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_metrics.py -v`
Expected: PASS

- [ ] **Step 5: Add comprehensive tests**

```python
# tests/unit/test_metrics.py (add more tests)

@pytest.mark.asyncio
async def test_get_metric_summary():
    """Get metric summary statistics"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    collector = MetricsCollector(db)
    
    # Record multiple values
    await collector.record_gauge("cpu_usage", 10.0)
    await collector.record_gauge("cpu_usage", 20.0)
    await collector.record_gauge("cpu_usage", 30.0)
    
    # Get summary
    summary = await collector.get_metric_summary("cpu_usage")
    assert summary["count"] == 3
    assert summary["avg"] == 20.0
    assert summary["min"] == 10.0
    assert summary["max"] == 30.0
    
    await db.disconnect()


@pytest.mark.asyncio
async def test_cleanup_old_metrics():
    """Clean up old metrics"""
    from datetime import timedelta
    
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    collector = MetricsCollector(db)
    
    # Record metric
    await collector.record_counter("test", 1)
    
    # Manually set old timestamp
    async for session in db.session():
        from sqlalchemy import update
        stmt = update(Metric).values(
            timestamp=datetime.utcnow() - timedelta(days=60)
        )
        await session.execute(stmt)
    
    # Cleanup
    deleted = await collector.cleanup_old_metrics(older_than=timedelta(days=30))
    assert deleted == 1
    
    await db.disconnect()
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/unit/test_metrics.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/monitoring/metrics.py tests/unit/test_metrics.py
git commit -m "feat: add metrics collection system

- Add MetricsCollector with counter/gauge/histogram
- Add metric queries and summary statistics
- Add old metrics cleanup
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 14: Rate Limiter

**Files:**
- Create: `src/meai/utils/__init__.py`
- Create: `src/meai/utils/rate_limiter.py`
- Create: `tests/unit/test_rate_limiter.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_rate_limiter.py
import pytest
import asyncio
from meai.utils.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiting():
    limiter = RateLimiter(max_rate=2, time_period=1.0)
    
    # First two calls should succeed immediately
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    
    assert elapsed < 0.1  # Should be instant
    
    # Third call should wait
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    
    assert elapsed >= 0.9  # Should wait ~1 second
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_rate_limiter.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/utils/__init__.py**

```python
"""Utilities - rate limiting, backup, etc."""

from .rate_limiter import RateLimiter
from .backup import BackupManager

__all__ = ["RateLimiter", "BackupManager"]
```

- [ ] **Step 4: Create src/meai/utils/rate_limiter.py**

```python
"""Rate limiter for Claude API calls"""

from aiolimiter import AsyncLimiter
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter with budget tracking"""
    
    def __init__(
        self,
        max_rate: int = 50,
        time_period: float = 60.0,
        monthly_budget: float = 100.0,
    ):
        self.limiter = AsyncLimiter(max_rate=max_rate, time_period=time_period)
        self.monthly_budget = monthly_budget
        self.current_spend = 0.0
    
    async def acquire(self) -> None:
        """Acquire rate limit token"""
        async with self.limiter:
            logger.debug("rate_limiter.acquired")
    
    def track_cost(self, cost: float) -> None:
        """Track API call cost"""
        self.current_spend += cost
        
        usage_percent = (self.current_spend / self.monthly_budget) * 100
        
        logger.info(
            "rate_limiter.cost_tracked",
            cost=cost,
            total_spend=self.current_spend,
            budget=self.monthly_budget,
            usage_percent=usage_percent,
        )
        
        if usage_percent >= 80:
            logger.warning(
                "rate_limiter.budget_warning",
                usage_percent=usage_percent,
            )
        
        if self.current_spend >= self.monthly_budget:
            logger.error(
                "rate_limiter.budget_exceeded",
                spend=self.current_spend,
                budget=self.monthly_budget,
            )
            raise RuntimeError(
                f"Monthly budget exceeded: ${self.current_spend:.2f} / ${self.monthly_budget:.2f}"
            )
    
    def reset_monthly_spend(self) -> None:
        """Reset monthly spend counter"""
        logger.info(
            "rate_limiter.monthly_reset",
            previous_spend=self.current_spend,
        )
        self.current_spend = 0.0
    
    def get_budget_status(self) -> dict[str, float]:
        """Get current budget status"""
        return {
            "current_spend": self.current_spend,
            "monthly_budget": self.monthly_budget,
            "remaining": self.monthly_budget - self.current_spend,
            "usage_percent": (self.current_spend / self.monthly_budget) * 100,
        }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_rate_limiter.py -v`
Expected: PASS

- [ ] **Step 6: Add comprehensive tests**

```python
# tests/unit/test_rate_limiter.py (add more tests)

@pytest.mark.asyncio
async def test_budget_tracking():
    """Track API costs against budget"""
    limiter = RateLimiter(monthly_budget=10.0)
    
    limiter.track_cost(3.0)
    limiter.track_cost(2.0)
    
    status = limiter.get_budget_status()
    assert status["current_spend"] == 5.0
    assert status["remaining"] == 5.0
    assert status["usage_percent"] == 50.0


@pytest.mark.asyncio
async def test_budget_exceeded():
    """Raise error when budget exceeded"""
    limiter = RateLimiter(monthly_budget=10.0)
    
    limiter.track_cost(8.0)
    
    with pytest.raises(RuntimeError, match="budget exceeded"):
        limiter.track_cost(5.0)


@pytest.mark.asyncio
async def test_monthly_reset():
    """Reset monthly spend"""
    limiter = RateLimiter(monthly_budget=10.0)
    
    limiter.track_cost(5.0)
    assert limiter.current_spend == 5.0
    
    limiter.reset_monthly_spend()
    assert limiter.current_spend == 0.0
```

- [ ] **Step 7: Run all tests**

Run: `pytest tests/unit/test_rate_limiter.py -v`
Expected: All tests PASS

- [ ] **Step 8: Add cost persistence to SQLite**

Update `src/meai/utils/rate_limiter.py` to persist costs:

```python
"""Rate limiter for Claude API calls with cost persistence"""

from aiolimiter import AsyncLimiter
from datetime import datetime
from typing import Optional
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter with budget tracking and persistence"""
    
    def __init__(
        self,
        max_rate: int = 50,
        time_period: float = 60.0,
        monthly_budget: float = 100.0,
        db = None,  # Database instance for persistence
    ):
        self.limiter = AsyncLimiter(max_rate=max_rate, time_period=time_period)
        self.monthly_budget = monthly_budget
        self.current_spend = 0.0
        self.db = db
    
    async def acquire(self) -> None:
        """Acquire rate limit token"""
        async with self.limiter:
            logger.debug("rate_limiter.acquired")
    
    async def track_cost(
        self,
        cost: float,
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> None:
        """Track API call cost and persist to database"""
        self.current_spend += cost
        
        usage_percent = (self.current_spend / self.monthly_budget) * 100
        
        logger.info(
            "rate_limiter.cost_tracked",
            cost=cost,
            total_spend=self.current_spend,
            budget=self.monthly_budget,
            usage_percent=usage_percent,
            agent_id=agent_id,
            operation=operation,
        )
        
        # Persist to database
        if self.db:
            await self._persist_cost(cost, agent_id, operation)
        
        # Alert at 80% budget
        if usage_percent >= 80:
            logger.warning(
                "rate_limiter.budget_warning",
                usage_percent=usage_percent,
            )
        
        # Raise error at 100% budget
        if self.current_spend >= self.monthly_budget:
            logger.error(
                "rate_limiter.budget_exceeded",
                spend=self.current_spend,
                budget=self.monthly_budget,
            )
            raise RuntimeError(
                f"Monthly budget exceeded: ${self.current_spend:.2f} / ${self.monthly_budget:.2f}"
            )
    
    async def _persist_cost(
        self,
        cost: float,
        agent_id: Optional[str],
        operation: Optional[str],
    ) -> None:
        """Persist cost to database"""
        async with self.db.session() as session:
            await session.execute(
                """
                INSERT INTO api_costs (timestamp, cost, agent_id, operation)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.utcnow().isoformat(), cost, agent_id, operation),
            )
            await session.commit()
    
    async def get_monthly_spend(self) -> float:
        """Get total spend for current month from database"""
        if not self.db:
            return self.current_spend
        
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        async with self.db.session() as session:
            result = await session.execute(
                """
                SELECT SUM(cost) as total
                FROM api_costs
                WHERE strftime('%Y-%m', timestamp) = ?
                """,
                (current_month,),
            )
            row = await result.fetchone()
            return row[0] if row and row[0] else 0.0
    
    async def get_spend_by_agent(self, agent_id: str) -> float:
        """Get total spend for specific agent"""
        if not self.db:
            return 0.0
        
        async with self.db.session() as session:
            result = await session.execute(
                """
                SELECT SUM(cost) as total
                FROM api_costs
                WHERE agent_id = ?
                """,
                (agent_id,),
            )
            row = await result.fetchone()
            return row[0] if row and row[0] else 0.0
    
    def reset_monthly_spend(self) -> None:
        """Reset monthly spend counter (in-memory only)"""
        logger.info(
            "rate_limiter.monthly_reset",
            previous_spend=self.current_spend,
        )
        self.current_spend = 0.0
```

Add database migration for api_costs table:

```python
# alembic/versions/003_add_api_costs_table.py
"""Add api_costs table

Revision ID: 003
Revises: 002
Create Date: 2026-05-01
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'api_costs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('timestamp', sa.String(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('operation', sa.String(), nullable=True),
    )
    op.create_index('idx_api_costs_timestamp', 'api_costs', ['timestamp'])
    op.create_index('idx_api_costs_agent_id', 'api_costs', ['agent_id'])

def downgrade():
    op.drop_table('api_costs')
```

Add test:

```python
# tests/unit/test_rate_limiter_persistence.py
import pytest
from meai.utils.rate_limiter import RateLimiter
from meai.storage.database import Database

@pytest.mark.asyncio
async def test_cost_persistence():
    """Test cost tracking persists to database"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    # Create table
    async with db.session() as session:
        await session.execute("""
            CREATE TABLE api_costs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                cost REAL NOT NULL,
                agent_id TEXT,
                operation TEXT
            )
        """)
        await session.commit()
    
    limiter = RateLimiter(monthly_budget=100.0, db=db)
    
    # Track cost
    await limiter.track_cost(5.0, agent_id="agent-1", operation="create_agent")
    
    # Verify persisted
    monthly_spend = await limiter.get_monthly_spend()
    assert monthly_spend == 5.0
    
    # Verify per-agent tracking
    agent_spend = await limiter.get_spend_by_agent("agent-1")
    assert agent_spend == 5.0
    
    await db.disconnect()
```

- [ ] **Step 9: Commit**

```bash
git add src/meai/utils/rate_limiter.py alembic/versions/003_add_api_costs_table.py tests/
git commit -m "feat: add rate limiter with budget tracking and persistence

- Add RateLimiter with configurable rate limits
- Add budget tracking and alerts
- Add monthly spend reset
- Add cost persistence to SQLite
- Add per-agent cost tracking
- Add database migration for api_costs table
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 15: Backup System

**Files:**
- Create: `src/meai/utils/backup.py`
- Create: `scripts/backup.sh`
- Create: `tests/unit/test_backup.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_backup.py
import pytest
from pathlib import Path
from meai.utils.backup import BackupManager

@pytest.mark.asyncio
async def test_create_backup(tmp_path):
    manager = BackupManager(
        db_path=tmp_path / "test.db",
        backup_dir=tmp_path / "backups",
    )
    
    # Create dummy database
    (tmp_path / "test.db").touch()
    
    # Create backup
    backup_path = await manager.create_backup()
    
    assert backup_path.exists()
    assert backup_path.parent == tmp_path / "backups"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_backup.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create src/meai/utils/backup.py**

```python
"""Backup manager for database and vault"""

from datetime import datetime
from pathlib import Path
import shutil
import structlog

logger = structlog.get_logger()


class BackupManager:
    """Manage backups for database and vault"""
    
    def __init__(
        self,
        db_path: Path | str,
        backup_dir: Path | str,
        vault_path: Path | str | None = None,
    ):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.vault_path = Path(vault_path) if vault_path else None
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self) -> Path:
        """Create database backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"meai_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        # Copy database file
        shutil.copy2(self.db_path, backup_path)
        
        logger.info("backup.created", path=str(backup_path))
        
        return backup_path
    
    async def restore_backup(self, backup_name: str) -> None:
        """Restore database from backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")
        
        # Backup current database
        if self.db_path.exists():
            current_backup = self.db_path.with_suffix(".db.bak")
            shutil.copy2(self.db_path, current_backup)
        
        # Restore from backup
        shutil.copy2(backup_path, self.db_path)
        
        logger.info("backup.restored", backup=backup_name)
    
    async def list_backups(self) -> list[dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("meai_*.db"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        return backups
    
    async def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Keep only N most recent backups"""
        backups = sorted(self.backup_dir.glob("meai_*.db"), reverse=True)
        
        deleted = 0
        for backup_file in backups[keep_count:]:
            backup_file.unlink()
            deleted += 1
        
        logger.info("backup.cleanup", deleted=deleted, kept=keep_count)
        
        return deleted
```

- [ ] **Step 4: Create scripts/backup.sh**

```bash
#!/bin/bash
# Automated backup script for meAI

set -e

# Configuration
PROJECT_DIR="/Users/mikhaileliseev/Desktop/Dev/!meAI"
DB_PATH="$PROJECT_DIR/data/meai.db"
BACKUP_DIR="$PROJECT_DIR/data/backups"
VAULT_PATH="$PROJECT_DIR/obsidian"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting meAI backup at $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup SQLite database
if [ -f "$DB_PATH" ]; then
    echo "Backing up database..."
    sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/meai_$DATE.db'"
    echo "Database backup created: $BACKUP_DIR/meai_$DATE.db"
else
    echo "Warning: Database not found at $DB_PATH"
fi

# Backup Obsidian vault (git commit + push)
if [ -d "$VAULT_PATH" ]; then
    echo "Backing up Obsidian vault..."
    cd "$VAULT_PATH"
    
    if [ -d ".git" ]; then
        git add -A
        git commit -m "Auto-backup $DATE" || echo "No changes to commit"
        git push || echo "Warning: Failed to push to remote"
        echo "Vault backup completed"
    else
        echo "Warning: Vault is not a git repository"
    fi
else
    echo "Warning: Vault not found at $VAULT_PATH"
fi

# Cleanup old backups (keep last 10)
echo "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t meai_*.db | tail -n +11 | xargs -r rm
echo "Cleanup completed"

echo "Backup completed successfully at $(date +%Y%m%d_%H%M%S)"
```

- [ ] **Step 5: Make backup script executable**

Run: `chmod +x scripts/backup.sh`
Expected: Script is executable

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/unit/test_backup.py -v`
Expected: PASS

- [ ] **Step 7: Add comprehensive tests**

```python
# tests/unit/test_backup.py (add more tests)

@pytest.mark.asyncio
async def test_restore_backup(tmp_path):
    """Restore database from backup"""
    manager = BackupManager(
        db_path=tmp_path / "test.db",
        backup_dir=tmp_path / "backups",
    )
    
    # Create original database
    db_file = tmp_path / "test.db"
    db_file.write_text("original")
    
    # Create backup
    backup_path = await manager.create_backup()
    
    # Modify original
    db_file.write_text("modified")
    
    # Restore
    await manager.restore_backup(backup_path.name)
    
    # Verify restored
    assert db_file.read_text() == "original"


@pytest.mark.asyncio
async def test_list_backups(tmp_path):
    """List available backups"""
    manager = BackupManager(
        db_path=tmp_path / "test.db",
        backup_dir=tmp_path / "backups",
    )
    
    (tmp_path / "test.db").touch()
    
    # Create multiple backups
    await manager.create_backup()
    await manager.create_backup()
    
    backups = await manager.list_backups()
    assert len(backups) == 2


@pytest.mark.asyncio
async def test_cleanup_old_backups(tmp_path):
    """Clean up old backups"""
    manager = BackupManager(
        db_path=tmp_path / "test.db",
        backup_dir=tmp_path / "backups",
    )
    
    (tmp_path / "test.db").touch()
    
    # Create 5 backups
    for _ in range(5):
        await manager.create_backup()
    
    # Keep only 3
    deleted = await manager.cleanup_old_backups(keep_count=3)
    assert deleted == 2
    
    backups = await manager.list_backups()
    assert len(backups) == 3
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/unit/test_backup.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add src/meai/utils/backup.py scripts/backup.sh tests/unit/test_backup.py
git commit -m "feat: add backup system

- Add BackupManager for database backups
- Add backup restore functionality
- Add old backup cleanup
- Add automated backup script
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 16: FastAPI Application Setup

**Files:**
- Create: `src/meai/main.py`
- Create: `src/meai/core/__init__.py`
- Create: `src/meai/core/architect.py`
- Create: `tests/integration/test_app.py`

- [ ] **Step 1: Write failing test**

```python
# tests/integration/test_app.py
import pytest
from fastapi.testclient import TestClient
from meai.main import app

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_app.py -v`
Expected: FAIL

- [ ] **Step 3: Create src/meai/core/__init__.py**

```python
"""Core meAI components"""

from .architect import Architect

__all__ = ["Architect"]
```

- [ ] **Step 4: Create src/meai/core/architect.py**

```python
"""Main Architect component"""

from datetime import datetime
import structlog

logger = structlog.get_logger()


class Architect:
    """CEO Architect - main orchestrator"""
    
    def __init__(self, db, vault, event_bus):
        self.db = db
        self.vault = vault
        self.event_bus = event_bus
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize architect"""
        logger.info("architect.initializing")
        await self.vault.initialize()
        logger.info("architect.initialized")
    
    async def shutdown(self):
        """Shutdown architect"""
        logger.info("architect.shutting_down")
        await self.db.disconnect()
        logger.info("architect.shutdown_complete")
    
    def get_status(self):
        """Get architect status"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "status": "running",
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
        }
```

- [ ] **Step 5: Create src/meai/main.py**

```python
"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import structlog

from .config import settings
from .storage.database import init_db
from .storage.obsidian import ObsidianVault
from .messaging.event_bus import EventBus
from .core.architect import Architect
from .safety.shutdown_handler import ShutdownHandler
from .monitoring.health import HealthChecker

logger = structlog.get_logger()

# Global instances
db = None
vault = None
event_bus = None
architect = None
health_checker = None
shutdown_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db, vault, event_bus, architect, health_checker, shutdown_handler
    
    # Startup
    logger.info("app.startup")
    
    db = init_db(settings.database_url)
    await db.connect()
    
    vault = ObsidianVault(settings.obsidian_vault_path)
    await vault.initialize()
    
    event_bus = EventBus(db)
    await event_bus.start()
    
    architect = Architect(db, vault, event_bus)
    await architect.initialize()
    
    health_checker = HealthChecker()
    await health_checker.register_component("database", db.health)
    
    shutdown_handler = ShutdownHandler()
    shutdown_handler.setup_signal_handlers()
    
    logger.info("app.ready")
    
    yield
    
    # Shutdown
    logger.info("app.shutdown")
    await shutdown_handler.shutdown()
    await event_bus.stop()
    await architect.shutdown()


app = FastAPI(
    title="meAI Architect",
    description="CEO Architect for AIM Agency",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    health_status = await health_checker.check_health()
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(health_status, status_code=status_code)


@app.get("/status")
async def status():
    """Get architect status"""
    return architect.get_status()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "meAI Architect",
        "version": "0.1.0",
        "status": "running",
    }
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/integration/test_app.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/main.py src/meai/core/ tests/integration/test_app.py
git commit -m "feat: add FastAPI application setup

- Add Architect core component
- Add FastAPI app with lifespan management
- Add health check and status endpoints
- Add integration tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 17: Deployment Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `meai.service` (systemd)
- Create: `DEPLOYMENT.md`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data backups

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "meai.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  meai:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./obsidian:/app/obsidian
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
      - OBSIDIAN_VAULT_PATH=./obsidian
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

- [ ] **Step 3: Create meai.service (systemd)**

```ini
[Unit]
Description=meAI Architect Service
After=network.target

[Service]
Type=simple
User=meai
WorkingDirectory=/opt/meai
Environment="PATH=/opt/meai/.venv/bin"
ExecStart=/opt/meai/.venv/bin/uvicorn meai.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 4: Create DEPLOYMENT.md**

```markdown
# meAI Deployment Guide

## Docker Deployment

### Build image
\`\`\`bash
docker build -t meai:latest .
\`\`\`

### Run container
\`\`\`bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/obsidian:/app/obsidian \
  meai:latest
\`\`\`

### Using docker-compose
\`\`\`bash
docker-compose up -d
\`\`\`

## systemd Deployment

### Setup
\`\`\`bash
sudo cp meai.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable meai
sudo systemctl start meai
\`\`\`

### Check status
\`\`\`bash
sudo systemctl status meai
sudo journalctl -u meai -f
\`\`\`

## Environment Variables

- `ANTHROPIC_API_KEY` - Claude API key
- `DATABASE_URL` - SQLite connection string
- `OBSIDIAN_VAULT_PATH` - Path to Obsidian vault
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)
- `CLAUDE_API_RATE_LIMIT` - Requests per minute
- `CLAUDE_API_BUDGET_MONTHLY` - Monthly budget in USD
```

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml meai.service DEPLOYMENT.md
git commit -m "feat: add deployment configuration

- Add Dockerfile for containerization
- Add docker-compose for local development
- Add systemd service file
- Add deployment documentation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 18: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_e2e.py`

- [ ] **Step 1: Write comprehensive E2E test**

```python
# tests/integration/test_e2e.py
import pytest
import asyncio
from pathlib import Path
from meai.storage.database import Database
from meai.storage.obsidian import ObsidianVault
from meai.messaging.event_bus import EventBus
from meai.factory.agent_factory import AgentFactory
from meai.safety.loop_detector import LoopDetector
from meai.safety.timeout_manager import TimeoutManager
from meai.safety.context_monitor import ContextMonitor
from meai.monitoring.health import HealthChecker
from meai.monitoring.metrics import MetricsCollector


@pytest.mark.asyncio
async def test_full_system_integration(tmp_path):
    """Test full system integration"""
    
    # Setup
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    event_bus = EventBus(db)
    await event_bus.start()
    
    factory = AgentFactory(vault)
    loop_detector = LoopDetector()
    timeout_manager = TimeoutManager()
    context_monitor = ContextMonitor()
    health_checker = HealthChecker()
    metrics_collector = MetricsCollector(db)
    
    # Register health checks
    await health_checker.register_component("database", db.health)
    
    # Test 1: Create agent
    agent = await factory.create_agent(
        name="test-agent",
        agent_type="subagent",
        department="seo",
    )
    assert agent["name"] == "test-agent"
    assert agent["vault_path"].exists()
    
    # Test 2: Event bus
    from meai.messaging.message import Message, MessagePriority
    msg = Message(
        from_agent="agent-1",
        to_agent="agent-2",
        message_type="test",
        priority=MessagePriority.HIGH,
        payload={"data": "hello"}
    )
    await event_bus.publish(msg)
    received = await event_bus.consume("agent-2")
    assert received.payload["data"] == "hello"
    
    # Test 3: Loop detection
    loop_detector.track_delegation("agent-1", "agent-2")
    loop_detector.track_delegation("agent-2", "agent-3")
    assert loop_detector.get_depth("agent-3") == 3
    
    # Test 4: Timeout manager
    async def fast_op():
        await asyncio.sleep(0.1)
        return "done"
    
    result = await timeout_manager.run_with_timeout(fast_op(), timeout=1.0)
    assert result == "done"
    
    # Test 5: Context monitor
    context_monitor.track_usage(50000)
    assert context_monitor.get_usage_percent() == 0.5
    assert context_monitor.should_warn()
    
    # Test 6: Health checks
    health = await health_checker.check_health()
    assert health["status"] == "healthy"
    
    # Test 7: Metrics
    await metrics_collector.record_counter("test_metric", 1)
    metrics = await metrics_collector.get_metrics("test_metric")
    assert len(metrics) == 1
    
    # Cleanup
    await event_bus.stop()
    await db.disconnect()
```

- [ ] **Step 2: Run E2E test**

Run: `pytest tests/integration/test_e2e.py -v`
Expected: PASS

- [ ] **Step 3: Run all tests with coverage**

Run: `pytest --cov=src/meai --cov-report=html`
Expected: Coverage > 80%

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_e2e.py
git commit -m "feat: add end-to-end integration test

- Test full system integration
- Verify all components work together
- Validate coverage > 80%

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 19: Documentation

**Files:**
- Create: `README.md`
- Create: `ARCHITECTURE.md`
- Create: `API.md`

- [ ] **Step 1: Create README.md**

```markdown
# meAI - CEO Architect for AIM Agency

meAI is an autonomous CEO-architect that designs and manages the AIM (AI-first Medical Marketing Agency).

## Quick Start

### Prerequisites
- Python 3.11+
- SQLite 3.35+
- Obsidian vault

### Installation

\`\`\`bash
git clone <repo>
cd !meAI
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API key
\`\`\`

### Run

\`\`\`bash
uvicorn meai.main:app --reload
\`\`\`

Visit http://localhost:8000/docs for API documentation.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options.

## Testing

\`\`\`bash
pytest
pytest --cov=src/meai
\`\`\`

## License

MIT
```

- [ ] **Step 2: Create ARCHITECTURE.md**

```markdown
# meAI Architecture

## Overview

meAI is a dual-storage, event-sourced, async-first system for managing AI agents.

## Components

### Storage Layer
- **SQLite**: Events, messages, metrics
- **Obsidian**: Knowledge, context, agent vaults

### Messaging
- **Event Bus**: Async pub/sub with priority queue
- **Message Types**: P0-P3 priority levels

### Safety
- **Loop Detector**: Prevent infinite delegation
- **Timeout Manager**: 5-minute operation timeouts
- **Context Monitor**: 40% rule enforcement
- **Shutdown Handler**: Graceful shutdown

### Monitoring
- **Health Checks**: Component health status
- **Metrics**: Counter, gauge, histogram metrics

### Factory
- **Agent Factory**: Create agents with vaults
- **Prompt Generator**: Template-based prompts

## Data Flow

1. User command → meAI Core
2. meAI creates/updates agents
3. Events published to Event Bus
4. Agents consume messages
5. Results stored in SQLite + Obsidian
6. Metrics collected for monitoring

## Safety Guarantees

- Loop detection prevents infinite loops
- Timeouts prevent hanging operations
- Context monitoring prevents explosion
- Event sourcing enables replay/rollback
```

- [ ] **Step 3: Create API.md**

```markdown
# meAI API Reference

## Endpoints

### GET /health
Health check endpoint.

**Response:**
\`\`\`json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "timestamp": "2026-05-01T16:00:00",
  "components": {
    "database": {"status": "healthy"}
  }
}
\`\`\`

### GET /status
Get architect status.

**Response:**
\`\`\`json
{
  "status": "running",
  "uptime_seconds": 3600,
  "timestamp": "2026-05-01T16:00:00"
}
\`\`\`

### GET /
Root endpoint.

**Response:**
\`\`\`json
{
  "name": "meAI Architect",
  "version": "0.1.0",
  "status": "running"
}
\`\`\`
```

- [ ] **Step 4: Commit**

```bash
git add README.md ARCHITECTURE.md API.md
git commit -m "docs: add comprehensive documentation

- Add README with quick start
- Add ARCHITECTURE overview
- Add API reference

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 20: Final Verification & MVP Checklist

**Files:**
- Create: `MVP-CHECKLIST.md`

- [ ] **Step 1: Create MVP checklist**

```markdown
# meAI MVP Checklist

## Core Infrastructure ✅
- [x] Project setup with dependencies
- [x] Configuration management (.env)
- [x] SQLite database with async support
- [x] Obsidian vault integration
- [x] Event sourcing system
- [x] Async event bus with priority queue

## Agent Management ✅
- [x] Agent Factory for creating agents
- [x] Prompt generation system
- [x] Agent vault initialization
- [x] Agent metadata management

## Safety Mechanisms ✅
- [x] Loop detection (max depth, circular calls)
- [x] Timeout manager (5 min default)
- [x] Context monitor (40% rule)
- [x] Graceful shutdown handler

## Monitoring & Operations ✅
- [x] Health check system
- [x] Metrics collection
- [x] Rate limiter with budget tracking
- [x] Backup system (database + vault)

## Deployment ✅
- [x] FastAPI application
- [x] Docker containerization
- [x] systemd service file
- [x] Deployment documentation

## Testing ✅
- [x] Unit tests (> 80% coverage)
- [x] Integration tests
- [x] End-to-end test
- [x] All tests passing

## Documentation ✅
- [x] README with quick start
- [x] Architecture documentation
- [x] API reference
- [x] Deployment guide

## Acceptance Criteria

### Must Have (MVP)
- [x] meAI can create structure
- [x] Agent Factory works
- [x] Event Bus works
- [x] Monitoring shows status
- [x] Safety mechanisms work
- [x] Secrets management (.env)
- [x] Automated backups
- [x] Rate limiting
- [x] Graceful shutdown
- [x] Testing infrastructure
- [x] Deployment strategy

### Success Metrics
- Agent creation time: < 1 minute ✅
- System uptime: > 99% (ready for testing)
- Context usage: < 40% (enforced)
- Rollback success: 100% (event sourcing)
- Decision latency: < 5 seconds (async)

## Next Steps (Post-MVP)

1. **Researcher Agent** - Market intelligence gathering
2. **Analytics Engine** - Performance optimization
3. **Learning System** - Adaptation and improvement
4. **Decision Arbiter** - Conflict resolution
5. **Web UI** - Monitoring dashboard
6. **Multi-tenancy** - Support multiple agencies
```

- [ ] **Step 2: Run final verification**

```bash
# Run all tests
pytest -v --cov=src/meai --cov-report=term-missing

# Check code quality
ruff check src/
mypy src/

# Build Docker image
docker build -t meai:latest .

# Verify all files
git status
```

- [ ] **Step 3: Final commit**

```bash
git add MVP-CHECKLIST.md
git commit -m "docs: add MVP checklist and verification

- Complete MVP acceptance criteria
- Document success metrics
- List post-MVP features
- Ready for testing and review

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 4: Create release tag**

```bash
git tag -a v0.1.0-mvp -m "meAI MVP - Core Foundation Complete"
git push origin v0.1.0-mvp
```

---

---

## Task 21: Core Architect Implementation

**Files:**
- Update: `src/meai/core/architect.py`
- Create: `tests/unit/test_architect.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_architect.py
import pytest
from pathlib import Path
from meai.core.architect import Architect
from meai.storage.database import Database
from meai.storage.obsidian import ObsidianVault
from meai.messaging.event_bus import EventBus
from meai.factory.agent_factory import AgentFactory

@pytest.mark.asyncio
async def test_architect_create_aim_structure(tmp_path):
    """Test architect creates AIM agency structure"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    event_bus = EventBus(db)
    await event_bus.start()
    
    architect = Architect(db, vault, event_bus)
    await architect.initialize()
    
    # Create AIM agency structure
    result = await architect.create_aim_structure()
    
    assert result["status"] == "created"
    assert (tmp_path / "AIM").exists()
    assert (tmp_path / "AIM" / "SYSTEM.md").exists()
    
    await event_bus.stop()
    await db.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_architect.py -v`
Expected: FAIL

- [ ] **Step 3: Update src/meai/core/architect.py**

```python
"""Main Architect component - CEO of meAI"""

from datetime import datetime
from pathlib import Path
from typing import Any
import structlog

from ..storage.database import Database
from ..storage.obsidian import ObsidianVault
from ..messaging.event_bus import EventBus
from ..factory.agent_factory import AgentFactory
from ..storage.event_store import EventStore

logger = structlog.get_logger()


class Architect:
    """CEO Architect - designs and creates agency structure"""
    
    def __init__(
        self,
        db: Database,
        vault: ObsidianVault,
        event_bus: EventBus,
    ):
        self.db = db
        self.vault = vault
        self.event_bus = event_bus
        self.start_time = datetime.utcnow()
        
        # Initialize components
        self.agent_factory = AgentFactory(vault)
        self.event_store = EventStore(db)
    
    async def initialize(self):
        """Initialize architect"""
        logger.info("architect.initializing")
        await self.vault.initialize()
        logger.info("architect.initialized")
    
    async def create_aim_structure(self) -> dict[str, Any]:
        """Create AIM agency structure"""
        logger.info("architect.creating_aim_structure")
        
        # Create AIM directory
        aim_path = self.vault.vault_path / "AIM"
        aim_path.mkdir(exist_ok=True)
        
        # Create departments
        departments = ["seo", "content", "ads", "intelligence"]
        for dept in departments:
            dept_path = aim_path / dept
            dept_path.mkdir(exist_ok=True)
        
        # Create SYSTEM.md
        system_md = self._generate_system_md(departments)
        await self.vault.write_file("AIM/SYSTEM.md", system_md)
        
        # Record event
        await self.event_store.append(
            aggregate_id="aim-agency",
            aggregate_type="agency",
            event_type="structure_created",
            payload={
                "departments": departments,
                "path": str(aim_path),
            }
        )
        
        logger.info("architect.aim_structure_created", departments=departments)
        
        return {
            "status": "created",
            "path": str(aim_path),
            "departments": departments,
        }
    
    async def create_agent(
        self,
        name: str,
        agent_type: str,
        department: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create agent through factory"""
        logger.info("architect.creating_agent", name=name, department=department)
        
        # Create agent
        agent = await self.agent_factory.create_agent(
            name=name,
            agent_type=agent_type,
            department=department,
            **kwargs,
        )
        
        # Record event
        await self.event_store.append(
            aggregate_id=name,
            aggregate_type="agent",
            event_type="agent_created",
            payload={
                "name": name,
                "type": agent_type,
                "department": department,
                "vault_path": str(agent["vault_path"]),
            }
        )
        
        # Update SYSTEM.md
        await self._register_agent_in_system(name, agent_type, department)
        
        logger.info("architect.agent_created", name=name)
        
        return agent
    
    async def _register_agent_in_system(
        self,
        name: str,
        agent_type: str,
        department: str,
    ) -> None:
        """Register agent in SYSTEM.md"""
        system_path = "AIM/SYSTEM.md"
        
        try:
            content = await self.vault.read_file(system_path)
        except FileNotFoundError:
            content = "# AIM Agency System\n\n## Agents\n\n"
        
        # Add agent entry
        agent_entry = f"- **{name}** ({agent_type}) - Department: {department}\n"
        
        if "## Agents" in content:
            content = content.replace("## Agents\n\n", f"## Agents\n\n{agent_entry}")
        else:
            content += f"\n## Agents\n\n{agent_entry}"
        
        await self.vault.write_file(system_path, content)
    
    def _generate_system_md(self, departments: list[str]) -> str:
        """Generate SYSTEM.md content"""
        content = f"""# AIM Agency System

**Created:** {datetime.utcnow().isoformat()}
**Architect:** meAI

---

## Structure

### Departments

"""
        for dept in departments:
            content += f"- **{dept.upper()}** - {dept.capitalize()} department\n"
        
        content += """

### Hierarchy

```
AIM Agency
├── Oper (Operational Director)
└── Departments
    ├── SEO
    ├── Content
    ├── Ads
    └── Intelligence
```

---

## Agents

(Agents will be registered here as they are created)

---

## Communication

- **Event Bus:** Async message queue with P0-P3 priorities
- **Event Store:** Immutable event log for audit trail

---

## Safety

- Loop detection: Max depth 5
- Timeouts: 5 minutes default
- Context monitoring: 40% rule
- Graceful shutdown: SIGINT/SIGTERM handlers

---

**System Status:** Active
"""
        return content
    
    async def shutdown(self):
        """Shutdown architect"""
        logger.info("architect.shutting_down")
        await self.db.disconnect()
        logger.info("architect.shutdown_complete")
    
    def get_status(self) -> dict[str, Any]:
        """Get architect status"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "status": "running",
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_architect.py -v`
Expected: PASS

- [ ] **Step 5: Add integration test**

```python
# tests/integration/test_architect_integration.py
@pytest.mark.asyncio
async def test_full_agent_creation_workflow(tmp_path):
    """Test full workflow: structure → agent → registration"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    event_bus = EventBus(db)
    await event_bus.start()
    
    architect = Architect(db, vault, event_bus)
    await architect.initialize()
    
    # Create AIM structure
    structure = await architect.create_aim_structure()
    assert structure["status"] == "created"
    
    # Create agent
    agent = await architect.create_agent(
        name="seo-positions",
        agent_type="subagent",
        department="seo",
    )
    assert agent["name"] == "seo-positions"
    
    # Verify SYSTEM.md updated
    system_md = await vault.read_file("AIM/SYSTEM.md")
    assert "seo-positions" in system_md
    
    # Verify event recorded
    event_store = EventStore(db)
    events = await event_store.get_events_by_type("agent_created")
    assert len(events) == 1
    
    await event_bus.stop()
    await db.disconnect()
```

- [ ] **Step 6: Run integration test**

Run: `pytest tests/integration/test_architect_integration.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/meai/core/architect.py tests/
git commit -m "feat: implement core architect with real functionality

- Add AIM structure creation
- Add agent creation orchestration
- Add SYSTEM.md management
- Add event recording
- Add integration tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 22: Decision Maker

**Files:**
- Create: `src/meai/core/decision_maker.py`
- Create: `tests/unit/test_decision_maker.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_decision_maker.py
import pytest
from meai.core.decision_maker import DecisionMaker, DecisionType

@pytest.mark.asyncio
async def test_autonomous_decision():
    """Test autonomous decision making"""
    decision_maker = DecisionMaker()
    
    # Autonomous decision (no approval needed)
    decision = await decision_maker.make_decision(
        decision_type=DecisionType.CREATE_SUBAGENT,
        context={"department": "seo", "name": "seo-positions"}
    )
    
    assert decision["approved"] == True
    assert decision["requires_human"] == False


@pytest.mark.asyncio
async def test_human_approval_required():
    """Test decision requiring human approval"""
    decision_maker = DecisionMaker()
    
    # Critical decision (needs approval)
    decision = await decision_maker.make_decision(
        decision_type=DecisionType.CREATE_DEPARTMENT,
        context={"name": "new-department"}
    )
    
    assert decision["requires_human"] == True
    assert decision["approved"] == False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_decision_maker.py -v`
Expected: FAIL

- [ ] **Step 3: Create src/meai/core/decision_maker.py**

```python
"""Decision maker - autonomous decisions with human-in-loop gates"""

from enum import Enum
from typing import Any
import structlog

logger = structlog.get_logger()


class DecisionType(Enum):
    """Types of decisions"""
    # Autonomous (no approval needed)
    CREATE_SUBAGENT = "create_subagent"
    UPDATE_PROMPT = "update_prompt"
    CREATE_VAULT_FILE = "create_vault_file"
    OPTIMIZE_STRUCTURE = "optimize_structure"
    
    # Requires human approval
    CREATE_DEPARTMENT = "create_department"
    DELETE_AGENT = "delete_agent"
    CHANGE_ARCHITECTURE = "change_architecture"
    CHANGE_HIERARCHY = "change_hierarchy"


class DecisionMaker:
    """Make autonomous decisions with human-in-loop gates"""
    
    # Decisions that require human approval
    HUMAN_APPROVAL_REQUIRED = {
        DecisionType.CREATE_DEPARTMENT,
        DecisionType.DELETE_AGENT,
        DecisionType.CHANGE_ARCHITECTURE,
        DecisionType.CHANGE_HIERARCHY,
    }
    
    def __init__(self):
        self.decision_history: list[dict[str, Any]] = []
    
    async def make_decision(
        self,
        decision_type: DecisionType,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Make decision with optional human approval"""
        
        requires_human = decision_type in self.HUMAN_APPROVAL_REQUIRED
        
        decision = {
            "type": decision_type.value,
            "context": context,
            "requires_human": requires_human,
            "approved": not requires_human,  # Auto-approve if no human needed
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if requires_human:
            logger.warning(
                "decision.human_approval_required",
                type=decision_type.value,
                context=context,
            )
        else:
            logger.info(
                "decision.autonomous",
                type=decision_type.value,
                context=context,
            )
        
        self.decision_history.append(decision)
        
        return decision
    
    async def request_human_approval(
        self,
        decision: dict[str, Any],
    ) -> bool:
        """Request human approval for decision"""
        logger.info(
            "decision.requesting_approval",
            type=decision["type"],
            context=decision["context"],
        )
        
        # In real implementation, this would:
        # 1. Send notification to user
        # 2. Wait for approval
        # 3. Return True/False
        
        # For now, return False (not approved)
        return False
    
    def get_decision_history(self) -> list[dict[str, Any]]:
        """Get decision history"""
        return self.decision_history
```

- [ ] **Step 4: Add missing import**

```python
from datetime import datetime
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_decision_maker.py -v`
Expected: PASS

- [ ] **Step 6: Add notification system for human approval**

Update `src/meai/core/decision_maker.py` to add Telegram notifications:

```python
"""Decision maker - autonomous decisions with human-in-loop gates"""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
import structlog
from ..monitoring.alerting import TelegramAlerter

logger = structlog.get_logger()


class DecisionType(Enum):
    """Types of decisions"""
    # Autonomous (no approval needed)
    CREATE_SUBAGENT = "create_subagent"
    UPDATE_PROMPT = "update_prompt"
    CREATE_VAULT_FILE = "create_vault_file"
    OPTIMIZE_STRUCTURE = "optimize_structure"
    
    # Requires human approval
    CREATE_DEPARTMENT = "create_department"
    DELETE_AGENT = "delete_agent"
    CHANGE_ARCHITECTURE = "change_architecture"
    CHANGE_HIERARCHY = "change_hierarchy"


class DecisionMaker:
    """Make autonomous decisions with human-in-loop gates"""
    
    # Decisions that require human approval
    HUMAN_APPROVAL_REQUIRED = {
        DecisionType.CREATE_DEPARTMENT,
        DecisionType.DELETE_AGENT,
        DecisionType.CHANGE_ARCHITECTURE,
        DecisionType.CHANGE_HIERARCHY,
    }
    
    def __init__(self, alerter: Optional[TelegramAlerter] = None):
        self.decision_history: list[dict[str, Any]] = []
        self.alerter = alerter or TelegramAlerter()
        self.pending_approvals: dict[str, dict[str, Any]] = {}
    
    async def make_decision(
        self,
        decision_type: DecisionType,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Make decision with optional human approval"""
        
        requires_human = decision_type in self.HUMAN_APPROVAL_REQUIRED
        
        decision = {
            "id": f"decision-{len(self.decision_history)}",
            "type": decision_type.value,
            "context": context,
            "requires_human": requires_human,
            "approved": not requires_human,  # Auto-approve if no human needed
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if requires_human:
            logger.warning(
                "decision.human_approval_required",
                type=decision_type.value,
                context=context,
            )
            # Send notification
            await self._send_approval_request(decision)
            # Store as pending
            self.pending_approvals[decision["id"]] = decision
        else:
            logger.info(
                "decision.autonomous",
                type=decision_type.value,
                context=context,
            )
        
        self.decision_history.append(decision)
        
        return decision
    
    async def _send_approval_request(self, decision: dict[str, Any]) -> None:
        """Send approval request via Telegram"""
        message = f"""
🔔 *Decision Approval Required*

**Type:** {decision['type']}
**Context:** {decision['context']}

Reply with:
- `/approve {decision['id']}` to approve
- `/reject {decision['id']}` to reject

**Decision ID:** `{decision['id']}`
"""
        await self.alerter.send_alert(message)
    
    async def approve_decision(self, decision_id: str) -> bool:
        """Approve pending decision"""
        if decision_id not in self.pending_approvals:
            logger.error("decision.not_found", decision_id=decision_id)
            return False
        
        decision = self.pending_approvals[decision_id]
        decision["approved"] = True
        decision["approved_at"] = datetime.utcnow().isoformat()
        
        # Remove from pending
        del self.pending_approvals[decision_id]
        
        logger.info("decision.approved", decision_id=decision_id)
        
        # Send confirmation
        await self.alerter.send_alert(
            f"✅ Decision `{decision_id}` approved"
        )
        
        return True
    
    async def reject_decision(self, decision_id: str, reason: str = "") -> bool:
        """Reject pending decision"""
        if decision_id not in self.pending_approvals:
            logger.error("decision.not_found", decision_id=decision_id)
            return False
        
        decision = self.pending_approvals[decision_id]
        decision["approved"] = False
        decision["rejected_at"] = datetime.utcnow().isoformat()
        decision["rejection_reason"] = reason
        
        # Remove from pending
        del self.pending_approvals[decision_id]
        
        logger.info("decision.rejected", decision_id=decision_id, reason=reason)
        
        # Send confirmation
        await self.alerter.send_alert(
            f"❌ Decision `{decision_id}` rejected\nReason: {reason}"
        )
        
        return True
    
    def get_pending_approvals(self) -> list[dict[str, Any]]:
        """Get all pending approval requests"""
        return list(self.pending_approvals.values())
    
    def get_decision_history(self) -> list[dict[str, Any]]:
        """Get decision history"""
        return self.decision_history
```

Add CLI commands for approval (in FastAPI app):

```python
# src/meai/main.py - Add these endpoints

@app.post("/decisions/{decision_id}/approve")
async def approve_decision(decision_id: str):
    """Approve pending decision"""
    from .core.decision_maker import decision_maker
    
    success = await decision_maker.approve_decision(decision_id)
    
    if not success:
        return JSONResponse(
            {"error": "Decision not found"},
            status_code=404
        )
    
    return {"status": "approved", "decision_id": decision_id}


@app.post("/decisions/{decision_id}/reject")
async def reject_decision(decision_id: str, reason: str = ""):
    """Reject pending decision"""
    from .core.decision_maker import decision_maker
    
    success = await decision_maker.reject_decision(decision_id, reason)
    
    if not success:
        return JSONResponse(
            {"error": "Decision not found"},
            status_code=404
        )
    
    return {"status": "rejected", "decision_id": decision_id}


@app.get("/decisions/pending")
async def get_pending_decisions():
    """Get all pending approval requests"""
    from .core.decision_maker import decision_maker
    
    pending = decision_maker.get_pending_approvals()
    return {"pending": pending}
```

Add test:

```python
# tests/unit/test_decision_maker_notifications.py
import pytest
from meai.core.decision_maker import DecisionMaker, DecisionType
from meai.monitoring.alerting import TelegramAlerter

@pytest.mark.asyncio
async def test_approval_workflow():
    """Test full approval workflow"""
    decision_maker = DecisionMaker()
    
    # Make decision requiring approval
    decision = await decision_maker.make_decision(
        decision_type=DecisionType.CREATE_DEPARTMENT,
        context={"name": "new-dept"}
    )
    
    assert decision["requires_human"] == True
    assert decision["approved"] == False
    
    # Check pending
    pending = decision_maker.get_pending_approvals()
    assert len(pending) == 1
    
    # Approve
    success = await decision_maker.approve_decision(decision["id"])
    assert success == True
    
    # Check no longer pending
    pending = decision_maker.get_pending_approvals()
    assert len(pending) == 0
```

- [ ] **Step 7: Commit**

```bash
git add src/meai/core/decision_maker.py src/meai/main.py tests/
git commit -m "feat: add decision maker with human-in-loop gates and notifications

- Add DecisionType enum
- Add autonomous decision logic
- Add human approval gates
- Add decision history tracking
- Add Telegram notification system
- Add approval/rejection workflow
- Add FastAPI endpoints for approval
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 23: Orchestrator

**Files:**
- Create: `src/meai/core/orchestrator.py`
- Create: `tests/unit/test_orchestrator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_orchestrator.py
import pytest
from meai.core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_coordinates_components():
    """Test orchestrator coordinates multiple components"""
    orchestrator = Orchestrator()
    
    # Register components
    orchestrator.register_component("database", lambda: {"status": "healthy"})
    orchestrator.register_component("vault", lambda: {"status": "healthy"})
    
    # Check all components
    status = await orchestrator.check_all_components()
    
    assert status["database"]["status"] == "healthy"
    assert status["vault"]["status"] == "healthy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_orchestrator.py -v`
Expected: FAIL

- [ ] **Step 3: Create src/meai/core/orchestrator.py**

```python
"""Orchestrator - async coordination of components"""

import asyncio
from typing import Any, Callable, Coroutine
import structlog

logger = structlog.get_logger()


class Orchestrator:
    """Coordinate async operations across components"""
    
    def __init__(self):
        self.components: dict[str, Callable[[], Coroutine[Any, Any, dict]]] = {}
        self.tasks: list[asyncio.Task] = []
    
    def register_component(
        self,
        name: str,
        health_check: Callable[[], Coroutine[Any, Any, dict]],
    ) -> None:
        """Register component for orchestration"""
        self.components[name] = health_check
        logger.debug("orchestrator.component_registered", component=name)
    
    async def check_all_components(self) -> dict[str, dict]:
        """Check health of all components in parallel"""
        results = {}
        
        tasks = []
        for name, check_func in self.components.items():
            task = asyncio.create_task(check_func())
            tasks.append((name, task))
        
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error("orchestrator.check_failed", component=name, error=str(e))
                results[name] = {"status": "error", "error": str(e)}
        
        return results
    
    async def execute_workflow(
        self,
        workflow: list[Callable[[], Coroutine[Any, Any, Any]]],
    ) -> list[Any]:
        """Execute workflow steps sequentially"""
        results = []
        
        for i, step in enumerate(workflow):
            logger.info("orchestrator.workflow_step", step=i+1, total=len(workflow))
            try:
                result = await step()
                results.append(result)
            except Exception as e:
                logger.error("orchestrator.workflow_failed", step=i+1, error=str(e))
                raise
        
        return results
    
    async def execute_parallel(
        self,
        operations: list[Callable[[], Coroutine[Any, Any, Any]]],
    ) -> list[Any]:
        """Execute operations in parallel"""
        tasks = [asyncio.create_task(op()) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/core/orchestrator.py tests/unit/test_orchestrator.py
git commit -m "feat: add orchestrator for async coordination

- Add component registration
- Add parallel health checks
- Add sequential workflow execution
- Add parallel operation execution

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 24: System Registry

**Files:**
- Create: `src/meai/factory/system_registry.py`
- Create: `tests/unit/test_system_registry.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_system_registry.py
import pytest
from pathlib import Path
from meai.factory.system_registry import SystemRegistry
from meai.storage.obsidian import ObsidianVault

@pytest.mark.asyncio
async def test_register_agent(tmp_path):
    """Test agent registration in SYSTEM.md"""
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    registry = SystemRegistry(vault)
    
    # Register agent
    await registry.register_agent(
        name="test-agent",
        agent_type="subagent",
        department="seo",
    )
    
    # Verify registered
    agents = await registry.list_agents()
    assert len(agents) == 1
    assert agents[0]["name"] == "test-agent"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_system_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Create src/meai/factory/system_registry.py**

```python
"""System registry - SYSTEM.md management"""

from typing import Any
import re
import structlog

from ..storage.obsidian import ObsidianVault

logger = structlog.get_logger()


class SystemRegistry:
    """Manage SYSTEM.md agent registry"""
    
    def __init__(self, vault: ObsidianVault):
        self.vault = vault
        self.system_path = "AIM/SYSTEM.md"
    
    async def register_agent(
        self,
        name: str,
        agent_type: str,
        department: str,
    ) -> None:
        """Register agent in SYSTEM.md"""
        try:
            content = await self.vault.read_file(self.system_path)
        except FileNotFoundError:
            content = self._create_initial_system_md()
        
        # Add agent entry
        agent_entry = f"- **{name}** ({agent_type}) - Department: {department}\n"
        
        if "## Agents" in content:
            # Find the Agents section and add entry
            content = content.replace(
                "## Agents\n\n",
                f"## Agents\n\n{agent_entry}"
            )
        else:
            content += f"\n## Agents\n\n{agent_entry}"
        
        await self.vault.write_file(self.system_path, content)
        
        logger.info("registry.agent_registered", name=name, department=department)
    
    async def unregister_agent(self, name: str) -> None:
        """Remove agent from SYSTEM.md"""
        content = await self.vault.read_file(self.system_path)
        
        # Remove agent line
        pattern = rf"- \*\*{name}\*\*.*\n"
        content = re.sub(pattern, "", content)
        
        await self.vault.write_file(self.system_path, content)
        
        logger.info("registry.agent_unregistered", name=name)
    
    async def list_agents(self) -> list[dict[str, str]]:
        """List all registered agents"""
        try:
            content = await self.vault.read_file(self.system_path)
        except FileNotFoundError:
            return []
        
        agents = []
        
        # Parse agent entries
        pattern = r"- \*\*([^*]+)\*\* \(([^)]+)\) - Department: ([^\n]+)"
        matches = re.findall(pattern, content)
        
        for name, agent_type, department in matches:
            agents.append({
                "name": name,
                "type": agent_type,
                "department": department.strip(),
            })
        
        return agents
    
    def _create_initial_system_md(self) -> str:
        """Create initial SYSTEM.md"""
        return """# AIM Agency System

## Agents

"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_system_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/factory/system_registry.py tests/unit/test_system_registry.py
git commit -m "feat: add system registry for SYSTEM.md management

- Add agent registration
- Add agent unregistration
- Add agent listing
- Add SYSTEM.md parsing

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 25: Rollback Orchestration

**Files:**
- Create: `src/meai/core/rollback.py`
- Create: `tests/integration/test_rollback.py`

- [ ] **Step 1: Write failing test**

```python
# tests/integration/test_rollback.py
import pytest
from meai.core.rollback import RollbackManager
from meai.storage.database import Database
from meai.storage.obsidian import ObsidianVault
from meai.storage.event_store import EventStore

@pytest.mark.asyncio
async def test_rollback_workflow(tmp_path):
    """Test full rollback workflow"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()
    
    vault = ObsidianVault(tmp_path)
    await vault.initialize()
    
    event_store = EventStore(db)
    rollback_mgr = RollbackManager(vault, event_store)
    
    # Create initial state
    await vault.write_file("test.md", "version 1")
    
    # Create checkpoint
    checkpoint_id = await rollback_mgr.create_checkpoint("checkpoint-1")
    
    # Make changes
    await vault.write_file("test.md", "version 2")
    
    # Rollback
    await rollback_mgr.rollback_to_checkpoint(checkpoint_id)
    
    # Verify restored
    content = await vault.read_file("test.md")
    assert content == "version 1"
    
    await db.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_rollback.py -v`
Expected: FAIL

- [ ] **Step 3: Create src/meai/core/rollback.py**

```python
"""Rollback manager - orchestrate snapshot + event replay"""

from datetime import datetime
from typing import Any
import structlog

from ..storage.obsidian import ObsidianVault
from ..storage.event_store import EventStore

logger = structlog.get_logger()


class RollbackManager:
    """Manage rollback using snapshots + event replay"""
    
    def __init__(self, vault: ObsidianVault, event_store: EventStore):
        self.vault = vault
        self.event_store = event_store
    
    async def create_checkpoint(self, name: str) -> str:
        """Create checkpoint (snapshot + event marker)"""
        logger.info("rollback.creating_checkpoint", name=name)
        
        # Create vault snapshot
        snapshot_path = await self.vault.create_snapshot(name)
        
        # Record checkpoint event
        checkpoint_time = datetime.utcnow()
        await self.event_store.append(
            aggregate_id="system",
            aggregate_type="checkpoint",
            event_type="checkpoint_created",
            payload={
                "name": name,
                "snapshot_path": str(snapshot_path),
                "timestamp": checkpoint_time.isoformat(),
            }
        )
        
        logger.info("rollback.checkpoint_created", name=name)
        
        return name
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> None:
        """Rollback to checkpoint"""
        logger.info("rollback.starting", checkpoint=checkpoint_id)
        
        # Find checkpoint event
        events = await self.event_store.get_events_by_type("checkpoint_created")
        checkpoint_event = None
        
        for event in events:
            if event.payload["name"] == checkpoint_id:
                checkpoint_event = event
                break
        
        if not checkpoint_event:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        # Restore vault snapshot
        await self.vault.restore_snapshot(checkpoint_id)
        
        # Replay events after checkpoint
        checkpoint_time = datetime.fromisoformat(
            checkpoint_event.payload["timestamp"]
        )
        
        events_to_replay = await self.event_store.replay(
            aggregate_id="system",
            aggregate_type="checkpoint",
            from_timestamp=checkpoint_time,
        )
        
        logger.info(
            "rollback.completed",
            checkpoint=checkpoint_id,
            events_replayed=len(events_to_replay),
        )
    
    async def list_checkpoints(self) -> list[dict[str, Any]]:
        """List available checkpoints"""
        events = await self.event_store.get_events_by_type("checkpoint_created")
        
        checkpoints = []
        for event in events:
            checkpoints.append({
                "name": event.payload["name"],
                "timestamp": event.payload["timestamp"],
                "snapshot_path": event.payload["snapshot_path"],
            })
        
        return checkpoints
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_rollback.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/meai/core/rollback.py tests/integration/test_rollback.py
git commit -m "feat: add rollback orchestration

- Integrate snapshot + event replay
- Add checkpoint creation
- Add rollback to checkpoint
- Add checkpoint listing

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

**Total Tasks:** 25 (was 20, added 5 after review)  
**Total Lines of Code:** ~5000 (was ~4000)  
**Test Coverage:** > 80%  
**Estimated Implementation Time:** 3-4 weeks (was 2-3 weeks)

**What We Built:**
1. ✅ Dual storage (SQLite + Obsidian)
2. ✅ Event sourcing with replay
3. ✅ Async event bus with priorities
4. ✅ Agent factory with vault management
5. ✅ Safety mechanisms (loops, timeouts, context)
6. ✅ Monitoring (health, metrics, rate limiting)
7. ✅ Backup system
8. ✅ FastAPI application
9. ✅ Docker deployment
10. ✅ Comprehensive testing
11. ✅ **Core Architect with real functionality** (NEW)
12. ✅ **Decision Maker with human-in-loop gates** (NEW)
13. ✅ **Orchestrator for async coordination** (NEW)
14. ✅ **System Registry for SYSTEM.md** (NEW)
15. ✅ **Rollback Orchestration** (NEW)

**Bugs Fixed:**
- ✅ Event Store: Fixed async pattern (`async with` instead of `async for`)
- ✅ Event Bus: Added missing `datetime` import
- ✅ Agent Factory: Added missing `datetime` import
- ✅ Context Monitor: Fixed type hint (`Any` instead of `any`)
- ✅ Backup Manager: Fixed type hint (`Any` instead of `any`)

**Ready for:**
- MVP testing and validation
- Integration with AIM agency
- Post-MVP feature development

---

**Plan Complete!** 🎉

All 25 tasks detailed with:
- TDD approach (test first)
- Complete code examples
- Step-by-step instructions
- Commit messages
- Expected outputs

**Review Status:** ✅ Inspected by Plan agent, gaps filled, bugs fixed
