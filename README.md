# meAI - AI-First Medical Marketing Agency Architecture

> CEO-архитектор для создания AIM (AI-first medical marketing agency)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

**meAI** — это CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru). Система состоит из трёх уровней:

1. **Strategy Layer** - Architect принимает стратегические решения
2. **Tactical Layer** - Operator управляет операциями и делегирует задачи
3. **Execution Layer** - 6 специализированных Magisters выполняют задачи

## 🏗️ Architecture

```
YOU (Human)
  ↓ strategic questions
ARCHITECT (Strategy Layer)
  ↓ strategic decisions
OPERATOR (Tactical Layer)
  ↓ task delegation
MAGISTERS (Execution Layer)
  ├─ SEO Magister
  ├─ Content Magister
  ├─ Ads Magister
  ├─ SMM Magister
  ├─ Analytics Magister
  └─ Intelligence Magister
  ↓ knowledge requests
TEACHER (Knowledge Management)
  ↓ research requests
RESEARCHER (Knowledge Collection)
```

## ✨ Key Features

### 🎓 University Knowledge System

**Three-layer knowledge architecture:**

1. **Researcher** - Собирает знания из Perplexity, YouTube, Telegram
2. **Teacher** - Хранит знания в Qdrant, синтезирует с Karpathy Pattern
3. **Magisters** - Используют знания с hybrid search

### 🔍 Hybrid Search

Трёхуровневая система поиска знаний:

```
Local Cache (1-5ms) → Teacher/Qdrant (50-200ms) → Researcher (2-10s)
```

- **Local Cache**: SQLite + Obsidian vault (24h TTL)
- **Teacher**: Qdrant vector search с embeddings
- **Researcher**: Живой поиск в источниках

### 📊 Experience Learning

Система обучения на опыте:

- **ExperienceTracker** - Записывает результаты задач
- **QualityUpdater** - Обновляет качество знаний (weighted algorithm)
- **DeprecationManager** - Удаляет устаревшие знания
- **LearningAnalytics** - Аналитика и insights

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (для Qdrant)
- Obsidian (опционально, для просмотра vaults)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd meAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Initialize system
python scripts/setup_magisters.py
```

### Basic Usage

```python
from meai.agents.magisters import SEOMagister
from meai.events.event_bus import EventBus

# Initialize
event_bus = EventBus()
seo_magister = SEOMagister(event_bus=event_bus)
await seo_magister.initialize()

# Search knowledge
results = await seo_magister.search_knowledge(
    query="SEO best practices 2026",
    search_local=True,
    search_teacher=True,
)

print(f"Found {len(results)} results")
```

## 📚 Documentation

### Core Components

- [**Architect**](docs/architect.md) - Strategic decision making
- [**Operator**](docs/operator.md) - Tactical operations management
- [**Magisters**](docs/magisters.md) - Domain specialists
- [**Teacher**](docs/teacher.md) - Knowledge management
- [**Researcher**](docs/researcher.md) - Knowledge collection

### Systems

- [**Hybrid Search**](docs/hybrid-search.md) - Three-layer search system
- [**Experience Learning**](docs/experience-learning.md) - Learning from outcomes
- [**Event Bus**](docs/event-bus.md) - Async messaging
- [**Memory System**](docs/memory.md) - Obsidian integration

### Guides

- [**Getting Started**](docs/getting-started.md) - Step-by-step tutorial
- [**API Reference**](docs/api-reference.md) - Complete API docs
- [**Deployment**](docs/deployment.md) - Production setup
- [**Contributing**](docs/contributing.md) - Development guide

## 🎯 Use Cases

### 1. SEO Optimization

```python
from meai.agents.magisters import SEOMagister

seo = SEOMagister(event_bus=event_bus)
await seo.initialize()

# Analyze keywords
result = await seo.execute_task(Task(
    task_id="task-1",
    description="Analyze keywords for medical SEO",
    metadata={
        "capability": "analyze_keywords",
        "keywords": ["medical SEO", "healthcare marketing"],
    }
))
```

### 2. Content Generation

```python
from meai.agents.magisters import ContentMagister

content = ContentMagister(event_bus=event_bus)
await content.initialize()

# Generate content
result = await content.execute_task(Task(
    task_id="task-2",
    description="Generate blog post",
    metadata={
        "capability": "generate_content",
        "topic": "Medical marketing trends 2026",
        "content_type": "article",
    }
))
```

### 3. Experience Learning

```python
from meai.learning import ExperienceTracker, QualityUpdater

tracker = ExperienceTracker()
await tracker.initialize()

# Record experience
await tracker.record_experience(
    magister_id="seo-magister-1",
    task_id="task-1",
    knowledge_ids=["knowledge-123"],
    outcome="success",
    outcome_score=0.9,
)

# Update quality
updater = QualityUpdater(experience_tracker=tracker)
result = await updater.update_knowledge_quality(
    knowledge_id="knowledge-123",
    current_score=7.0,
)

print(f"New score: {result['new_score']}")
```

## 📊 Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Local cache hit | 1-5ms | SQLite query |
| Teacher query | 50-200ms | Qdrant vector search |
| Researcher request | 2-10s | External API calls |
| Experience recording | 5-10ms | SQLite insert + stats |
| Quality update | 10-20ms | Calculate + log |
| Analytics query | 50-200ms | Aggregation queries |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src/meai --cov-report=html

# Run E2E tests
python scripts/test_magisters_core.py
python scripts/test_experience_learning.py
```

## 📈 Project Status

### Completed ✅

- **Plan 1**: University Infrastructure + Core
  - Qdrant integration
  - Teacher Agent with Karpathy Pattern
  - Researcher Agent (Perplexity, YouTube, Telegram)
  
- **Plan 2**: Magisters + Hybrid Search
  - Base Magister class
  - 6 domain-specific Magisters
  - Hybrid search system
  
- **Plan 3**: Experience Learning
  - ExperienceTracker
  - QualityUpdater
  - DeprecationManager
  - LearningAnalytics

### In Progress 🚧

- **Documentation** - API docs, guides, diagrams
- **Operator Integration** - Connect Magisters to Operator
- **Production Testing** - Real-world validation

### Planned 📋

- **Plan 4**: Operator Integration
- **Plan 5**: Production Deployment
- **Plan 6**: Monitoring & Observability

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **Vector DB**: Qdrant
- **Embeddings**: bge-m3 (sentence-transformers)
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Memory**: Obsidian (markdown vaults)
- **APIs**: Perplexity, YouTube, Telegram
- **Framework**: FastAPI (planned)
- **Testing**: pytest, pytest-asyncio

## 📝 Configuration

### Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OBSIDIAN_VAULT_PATH=./obsidian
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
QDRANT_URL=http://localhost:6333
LOG_LEVEL=INFO

# API Keys
PERPLEXITY_API_KEY=pplx-...
YOUTUBE_API_KEY=...
TELEGRAM_BOT_TOKEN=...
```

### Configuration Files

- `CLAUDE.md` - Project instructions for Claude Code
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker services
- `.env` - Environment variables

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linters
ruff check .
ruff format .
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.ai/code)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Vector search by [Qdrant](https://qdrant.tech/)
- Embeddings by [bge-m3](https://huggingface.co/BAAI/bge-m3)

## 📞 Contact

- **Project**: meAI - AI-First Medical Marketing Agency
- **Domain**: iamaim.ru
- **Focus**: Medical marketing with AI

---

**Built with ❤️ by Claude Opus 4.6**
