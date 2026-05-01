# meAI

Personal AI assistant for building AIM (AI-first medical marketing agency). Uses Obsidian for memory, integrates all Claude skills, helps with infrastructure and daily tasks.

## Project Vision

**AIM Agency** (iamaim.ru) — AI-first medical marketing agency combining:
- **AI**Marketing
- **AI**Management  
- **AI**Agency
- **AI**Medicine

This assistant helps build the agency from ground up, managing tasks, remembering context, and automating infrastructure.

## Getting Started

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Initialize Obsidian vault
mkdir -p obsidian/{AIM,tasks,decisions,learnings}

# Run tests
pytest
```

## Development

- `pytest` — run tests
- `ruff check .` — lint code
- `ruff format .` — format code
- `mypy src/` — type check
- `uvicorn meai.main:app --reload` — start dev server

## Structure

- `src/meai/` — Core assistant code
- `obsidian/` — Obsidian vault (memory system)
- `scripts/` — Automation utilities
- `tests/` — Test suite
- `data/` — SQLite database

## Key Features

- **Obsidian Integration** — Long-term memory and context
- **Claude Skills** — Access to all available skills
- **Task Management** — Track AIM agency building progress
- **Infrastructure Automation** — Proxy setup, configs, etc.
- **Learning System** — Improves based on past experience
