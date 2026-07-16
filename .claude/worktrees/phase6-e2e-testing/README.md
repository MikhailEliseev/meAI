# meAI - AI Agency Architect

> **meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency).

[![Tests](https://img.shields.io/badge/tests-133%2F133-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-green)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 🎯 What is meAI?

**meAI** — это архитектор AI-агентства, который:
- 🏗️ Проектирует архитектуру агентства
- 🤖 Создаёт Опера и агентов
- 📊 Управляет инфраструктурой и системами
- 🧠 Принимает стратегические решения
- 🔄 Обеспечивает надёжность и восстановление

### Two-Level System

```
┌─────────────────────────────────────────┐
│  meAI (CEO-Architect)                   │
│  /Users/.../Desktop/Dev/!meAI           │
│                                         │
│  • Проектирует архитектуру             │
│  • Создаёт агентов                     │
│  • Управляет инфраструктурой           │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  AIM Agency (Operational)               │
│  /Users/.../Desktop/Dev/AIM             │
│                                         │
│  • Опер (операционный директор)        │
│  • Агенты (SEO, Content, Ads, etc.)    │
│  • Выполнение задач                    │
└─────────────────────────────────────────┘
```

---

## ✨ Features

### 🏗️ Core Components

- **Architect** — Автономное принятие решений с анализом контекста
- **Decision Maker** — Выбор оптимальных стратегий с обучением
- **Orchestrator** — Асинхронная координация компонентов
- **Rollback Manager** — Откат через snapshot + event replay

### 💾 Storage Layer

- **SQLite** — Структурированные данные (async)
- **Obsidian** — Хранилища знаний (markdown vaults)
- **Event Store** — Immutable audit log с idempotency
- **Event Bus** — Async message queue с приоритетами (P0-P3)

### 🤖 Agent System

- **Agent Factory** — Создание агентов с vaults и промптами
- **Prompt Generator** — Генерация промптов (operator vs subagent)
- **System Registry** — Управление SYSTEM.md и иерархией

### 🛡️ Safety Mechanisms

- **Loop Detector** — Предотвращение бесконечной делегации (max depth 5)
- **Timeout Manager** — Таймауты операций (5 min default)
- **Context Monitor** — Правило 40% для контекста
- **Shutdown Handler** — Graceful cleanup при завершении

### 📊 Monitoring

- **Health Checker** — Проверка здоровья компонентов
- **Metrics Collector** — Counter, Gauge, Histogram
- **Rate Limiter** — Sliding window algorithm для Claude API

---

## 🚀 Quick Start

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

---

## 📖 Usage Examples

### Creating an Agent

```python
from meai.agents.factory import AgentFactory
from meai.storage.database import Database

# Initialize
db = Database("sqlite+aiosqlite:///./data/meai.db")
await db.connect()

factory = AgentFactory(
    vault_root="./obsidian",
    db=db
)

# Create agent
agent = await factory.create_agent(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist for medical marketing",
    parent_id="operator"
)

print(f"Agent created: {agent.agent_id}")
print(f"Vault: {agent.vault_path}")
```

### Making Decisions

```python
from meai.core.architect import Architect, DecisionContext

architect = Architect(db)

# Define decision context
context = DecisionContext(
    goal="Optimize SEO strategy",
    constraints=["budget < 1000", "timeline < 2 weeks"],
    available_resources={"team": 3, "tools": ["ahrefs", "semrush"]}
)

# Make decision
decision = await architect.make_decision(context)

print(f"Action: {decision.action}")
print(f"Rationale: {decision.rationale}")
print(f"Confidence: {decision.confidence}")
```

### Event Sourcing

```python
from meai.events.event_store import EventStore, Event
from datetime import datetime, timezone

event_store = EventStore("sqlite+aiosqlite:///:memory:")
await event_store.initialize()

# Append event
event = Event(
    aggregate_id="agent-123",
    aggregate_type="agent",
    event_type="task_completed",
    event_version=1,
    payload={"task": "SEO audit", "result": "success"},
    timestamp=datetime.now(timezone.utc).isoformat(),
    idempotency_key="task-123-completed"
)

await event_store.append_event(event)

# Replay events
events = await event_store.replay_events(
    aggregate_id="agent-123",
    from_timestamp="2026-05-01T00:00:00Z"
)
```

### Rollback & Recovery

```python
from meai.core.rollback import RollbackManager
from meai.memory.obsidian import ObsidianVault

vault = ObsidianVault("./obsidian")
await vault.initialize()

rollback_mgr = RollbackManager(vault, event_store)

# Create checkpoint
checkpoint_id = await rollback_mgr.create_checkpoint("before-changes")

# Make changes
await vault.write_file("agent.md", "new content")

# Rollback if needed
await rollback_mgr.rollback_to_checkpoint(checkpoint_id)
```

---

## 🏗️ Architecture

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
├─────────────────────────────────────────────────────────────┤
│                   Agent System                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Agent   │  │  Prompt  │  │  System  │                 │
│  │ Factory  │  │Generator │  │ Registry │                 │
│  │          │  │          │  │          │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
meAI/
├── src/meai/
│   ├── core/
│   │   ├── architect.py          # Autonomous decision making
│   │   ├── decision_maker.py     # Strategy selection & learning
│   │   ├── orchestrator.py       # Async coordination
│   │   └── rollback.py           # Snapshot + event replay
│   │
│   ├── storage/
│   │   ├── database.py           # SQLite async connection
│   │   └── models.py             # SQLAlchemy models
│   │
│   ├── memory/
│   │   └── obsidian.py           # Obsidian vault integration
│   │
│   ├── events/
│   │   ├── event_store.py        # Event sourcing
│   │   └── event_bus.py          # Async message queue
│   │
│   ├── agents/
│   │   ├── factory.py            # Agent creation
│   │   ├── prompt_generator.py   # Prompt templates
│   │   └── system_registry.py    # SYSTEM.md management
│   │
│   ├── safety/
│   │   ├── loop_detector.py      # Loop detection
│   │   ├── timeout_manager.py    # Timeout policies
│   │   ├── context_monitor.py    # 40% rule enforcement
│   │   └── shutdown_handler.py   # Graceful shutdown
│   │
│   └── monitoring/
│       ├── health.py             # Health checks
│       └── metrics.py            # Metrics collection
│
├── tests/
│   ├── unit/                     # 120 unit tests
│   └── integration/              # 13 integration tests
│
├── obsidian/                     # Memory vaults
├── data/                         # SQLite database
└── docs/                         # Documentation
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=meai --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_architect.py -v
```

**Test Results:**
- ✅ **133/133 tests passing**
- 120 unit tests
- 13 integration tests
- ~80%+ coverage
- 4.39s execution time

---

## 🛠️ Development

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | SQLite (aiosqlite) |
| ORM | SQLAlchemy 2.0 async |
| Memory | Obsidian (markdown) |
| Testing | pytest, pytest-asyncio |
| Logging | structlog |
| Container | Docker |

### Code Style

- ✅ Type hints everywhere
- ✅ Async/await for I/O operations
- ✅ TDD approach (test-first)
- ✅ Pydantic for validation
- ✅ Structured logging with structlog

### Commands

```bash
# Development
uvicorn meai.main:app --reload    # Start dev server
pytest                            # Run tests
pytest --cov=meai                 # Run with coverage

# Code Quality
ruff check .                      # Lint code
ruff format .                     # Format code
mypy src/                         # Type check

# Docker
docker-compose up -d              # Start services
docker-compose logs -f            # View logs
docker-compose down               # Stop services
```

---

## ⚙️ Configuration

Environment variables (`.env`):

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-...

# Paths
OBSIDIAN_VAULT_PATH=./obsidian
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db

# Logging
LOG_LEVEL=INFO

# Optional: Telegram notifications
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with service info |
| `/health` | GET | Health check with component status |
| `/metrics` | GET | Metrics collection (counter, gauge, histogram) |
| `/status` | GET | System status with uptime |

**Example Response:**

```json
{
  "service": "meAI",
  "version": "0.1.0",
  "status": "healthy",
  "components": {
    "database": {"status": "healthy"},
    "event_store": {"status": "healthy"},
    "vault": {"status": "healthy"}
  },
  "uptime": "2h 15m 30s"
}
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Core Foundation (COMPLETED)
- [x] Storage Layer (SQLite + Obsidian)
- [x] Event Sourcing system
- [x] Event Bus with priorities
- [x] Agent Factory
- [x] Safety Mechanisms
- [x] Monitoring & Health Checks
- [x] FastAPI + Docker
- [x] **Architect** (autonomous decisions)
- [x] **Decision Maker** (strategy selection)
- [x] **Orchestrator** (async coordination)
- [x] **Rollback System** (snapshot + replay)

**Status:** ✅ 25/25 tasks completed | 133/133 tests passing

### 🚧 Phase 2: AIM Agency (Next)
- [ ] Create Опер (operational director)
- [ ] Build first agent (SEO-agent)
- [ ] Test agent hierarchy
- [ ] Deploy to production

### 📋 Phase 3: Intelligence System
- [ ] Market intelligence gathering
- [ ] Competitor analysis
- [ ] Trend detection
- [ ] Learning & adaptation

### 🔮 Phase 4: Advanced Features
- [ ] Analytics & Optimization Engine
- [ ] Strategic Planning System
- [ ] Web UI (monitoring dashboard)
- [ ] Multi-agent collaboration

---

## 📚 Documentation

- [API Reference](docs/api/) — Detailed API documentation
- [Tutorials](docs/tutorials/) — Step-by-step guides
- [Architecture](docs/architecture/) — System design
- [ADR](docs/adr/) — Architecture Decision Records

---

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome!

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 📧 Contact

- **Author:** Mikhail Eliseev
- **Email:** me@mikhaileliseev.com
- **Project:** meAI - AI Agency Architect
- **Domain:** iamaim.ru

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) — Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — SQL toolkit
- [Obsidian](https://obsidian.md/) — Knowledge management
- [Claude](https://claude.ai/) — AI assistance

---

**Status:** 🟢 Production Ready | **Version:** 0.1.0 | **Last Updated:** 2026-05-02
