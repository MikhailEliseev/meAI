# meAI Assistant

## Project Overview

Personal AI assistant for building **AIM** (AI-first medical marketing agency at iamaim.ru). This assistant operates through Claude Code CLI, using Obsidian as its memory system and integrating all available Claude skills.

**User Role:** Medical marketer building AI-first agency  
**Stack:** Python 3.11+, FastAPI, SQLite, Obsidian  
**Started:** 2026-05-01 with Superflow greenfield scaffolding

## Architecture

### Core Components

1. **Memory System** (`obsidian/`)
   - `AIM/` — Agency context, strategy, decisions
   - `tasks/` — Current and completed tasks
   - `decisions/` — Architecture decisions and rationale
   - `learnings/` — Patterns, solutions, experience

2. **Assistant Core** (`src/meai/`)
   - `core/` — Main orchestration logic
   - `memory/` — Obsidian integration, context retrieval
   - `skills/` — Claude skills wrappers and automation
   - `automation/` — Infrastructure scripts (proxy, configs)

3. **Data Layer** (`data/`)
   - SQLite for structured data (tasks, metrics, logs)
   - Obsidian for unstructured knowledge

## Key Files

| File | Purpose |
|------|---------|
| `src/meai/main.py` | FastAPI app entry point |
| `src/meai/core/assistant.py` | Main assistant orchestration |
| `src/meai/memory/obsidian.py` | Obsidian vault integration |
| `src/meai/skills/manager.py` | Claude skills discovery & execution |
| `obsidian/` | Memory vault (markdown files) |
| `data/meai.db` | SQLite database |

## Commands

- `uvicorn meai.main:app --reload` — Start development server
- `pytest` — Run tests
- `ruff check . && ruff format .` — Lint and format
- `mypy src/` — Type checking

## Conventions

### Code Style
- Python 3.11+ with type hints
- Async/await for I/O operations
- Pydantic for data validation
- SQLAlchemy 2.0 async for database

### Memory Management
- All context goes to `obsidian/` as markdown
- Use frontmatter for metadata
- Link related notes with `[[wikilinks]]`
- Daily notes in `obsidian/daily/YYYY-MM-DD.md`

### Skills Integration
- Discover available skills via `/help`
- Wrap skill calls in `src/meai/skills/`
- Log skill usage for learning

### AIM Agency Context
- Medical marketing focus
- AI-first approach
- Domain: iamaim.ru
- Target: Building agency infrastructure and processes

## Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OBSIDIAN_VAULT_PATH=./obsidian
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
LOG_LEVEL=INFO
```

## Workflow

1. User communicates via Claude Code CLI
2. Assistant reads context from Obsidian
3. Executes tasks using Claude skills
4. Saves results and learnings back to Obsidian
5. Updates structured data in SQLite

## Integration with Claude Skills

Available skills (use via `/skill-name`):
- `/gsd-*` — Get Stuff Done workflows
- `/superflow` — Full development workflow
- `/deep-research` — Multi-source research
- `/document-manager` — Document operations
- `/git-master` — Git operations
- And 100+ more (see `/help`)

## Notes

- This is a **terminal-based assistant** — no separate UI
- All interaction happens in Claude Code CLI
- Obsidian vault is the persistent memory
- Skills are invoked directly through Claude Code

<!-- updated-by-superflow:2026-05-01 -->
