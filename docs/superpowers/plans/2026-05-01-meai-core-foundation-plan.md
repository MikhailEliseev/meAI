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
- Analytics & Optimization Engine
- Learning & Adaptation System
- Strategic Planning System
- Decision Arbiter
- Researcher Agent (separate plan)
- Web UI

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

*[Plan continues with Tasks 3-20 covering all components...]*

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

**Plan Status:** Task 1-2 detailed, Tasks 3-20 to be written

**Next:** Continue writing detailed tasks for Storage Layer, Event Sourcing, Event Bus, Agent Factory, Safety, Monitoring, Deployment

---

Хочешь, чтобы я продолжил писать все 20 задач детально? Или сначала обсудим структуру Tasks 1-2?
