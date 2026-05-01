# meAI - AI Agency Architect

**meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru).

## Architecture

### Two-Level System

- **meAI** (этот проект) — архитектор агентства
- **AIM Agency** (`/AIM`) — само агентство с Опером и агентами

### Core Components

```
meAI/
├── src/meai/
│   ├── agents/          # Agent Factory, Prompt Generator, System Registry
│   ├── events/          # Event Store, Event Bus
│   ├── memory/          # Obsidian integration
│   ├── monitoring/      # Health, Metrics, Rate Limiter
│   ├── safety/          # Loop Detector, Timeout Manager, Context Monitor, Shutdown Handler
│   └── storage/         # Database layer (SQLite + SQLAlchemy)
├── obsidian/            # Memory vault (markdown files)
├── data/                # SQLite database
└── tests/               # Unit and integration tests
```

## Features

### ✅ Implemented (Sprint 1-4)

**Storage Layer:**
- SQLite with async support (aiosqlite)
- Obsidian vault integration
- Event Store with idempotency
- Event Bus with priority queue

**Agent System:**
- Agent Factory (create agents with vaults)
- Prompt Generator (operator vs subagent templates)
- System Registry (SYSTEM.md management)

**Safety Mechanisms:**
- Loop Detector (prevent infinite delegation)
- Timeout Manager (operation timeouts)
- Context Monitor (40% rule enforcement)
- Shutdown Handler (graceful cleanup)

**Monitoring:**
- Health Checker (component health)
- Metrics Collector (counter, gauge, histogram)
- Rate Limiter (sliding window algorithm)

**API & Deployment:**
- FastAPI REST endpoints
- Docker containerization
- Health checks and metrics

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd meAI

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

### Running

**Local development:**
```bash
uvicorn meai.main:app --reload
```

**Docker:**
```bash
docker-compose up -d
```

**Access API:**
- API: http://localhost:8000
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- Docs: http://localhost:8000/docs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with service info |
| `/health` | GET | Health check with component status |
| `/metrics` | GET | Metrics collection |
| `/status` | GET | System status with uptime |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=meai --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

**Test Coverage:**
- 89 unit tests
- 4 integration tests
- 100% coverage for core components

## Development

### Project Structure

```
meAI/
├── src/meai/           # Source code
├── tests/              # Tests
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── obsidian/          # Memory vault
├── data/              # SQLite database
├── docs/              # Documentation
└── pyproject.toml     # Dependencies
```

### Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** SQLite (async with aiosqlite)
- **ORM:** SQLAlchemy 2.0
- **Memory:** Obsidian (markdown files)
- **Testing:** pytest, pytest-asyncio
- **Logging:** structlog
- **Containerization:** Docker

### Code Style

- Type hints everywhere
- Async/await for I/O
- TDD approach (test-first)
- Pydantic for validation
- Structured logging

### Commands

- `pytest` — run tests
- `ruff check .` — lint code
- `ruff format .` — format code
- `mypy src/` — type check
- `uvicorn meai.main:app --reload` — start dev server

## Configuration

Environment variables (`.env`):

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-...

# Paths
OBSIDIAN_VAULT_PATH=./obsidian
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db

# Logging
LOG_LEVEL=INFO
```

## Roadmap

### ✅ Phase 1: Core Foundation (MVP) - COMPLETED
- Storage Layer (SQLite + Obsidian)
- Event Sourcing system
- Agent Factory
- Safety Mechanisms
- Monitoring & Health Checks
- FastAPI + Docker

### 🚧 Phase 2: Core Intelligence (Next)
- Architect (autonomous decision making)
- Decision Maker (strategy selection)
- Orchestrator (component coordination)
- Rollback System (snapshot + replay)

### 📋 Phase 3: Advanced Features
- Analytics & Optimization
- Learning & Adaptation
- Strategic Planning
- Web UI

## Contributing

This is a personal project, but feedback and suggestions are welcome!

## License

MIT

## Contact

- Author: Mikhail Eliseev
- Email: me@mikhaileliseev.com
- Project: meAI - AI Agency Architect

