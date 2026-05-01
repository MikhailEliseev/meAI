# meAI Assistant

## Project Overview

**meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru).

**Two-Level System:**
- **meAI** (здесь, `/Users/mikhaileliseev/Desktop/Dev/!meAI`) — архитектор агентства
- **AIM Agency** (там, `/Users/mikhaileliseev/Desktop/Dev/AIM`) — само агентство с Опером и агентами

**User Role:** Medical marketer building AI-first agency  
**Stack:** Python 3.11+, FastAPI, SQLite, Obsidian  
**Started:** 2026-05-01 with Superflow greenfield scaffolding

## Model Selection Strategy

### Task-Based Model Usage

Используй разные модели для разных типов задач (см. `docs/superpowers/IMPLEMENTATION-STRATEGY.md`):

- **Tasks 1-10 (Infrastructure):** Sonnet 4.5 - Setup, config, database, Obsidian, event store
- **Tasks 11-17 (Safety & Monitoring):** Sonnet 4.5 - Loop detector, timeouts, health checks, metrics
- **Tasks 18-20 (Deployment):** Haiku 4.5 + Opus review - FastAPI, Docker, tests, docs
- **Tasks 21-25 (Core Components):** Opus 4.6 ⭐ - Architect, Decision Maker, Orchestrator, Registry, Rollback

### Switching Models in Claude Code

Use `/model <name>` command:
- `/model opus` - For complex architecture (Tasks 21-25)
- `/model sonnet` - For standard implementation (Tasks 1-17)
- `/model haiku` - For boilerplate code (Tasks 18-20)

### Why This Strategy?

- **Quality:** Opus для сложной логики (Tasks 21-25)
- **Cost:** Sonnet для стандартных задач (Tasks 1-17)
- **Speed:** Haiku для boilerplate (Tasks 18-20)
- **Savings:** ~60% vs all-Opus (~$85-160 vs $200-300)

## Architecture

### meAI Role (CEO-Architect)

**meAI** — генеральный директор и архитектор, который:
1. Проектирует архитектуру агентства
2. Создаёт Опера и агентов
3. Определяет структуру и иерархию
4. Строит инфраструктуру и системы
5. Принимает стратегические решения

### AIM Agency Structure (в /AIM)

**Опер** — операционный директор агентства, оркестратор:
- Управляет всеми агентами
- Распределяет задачи
- Координирует работу

**Агенты** (примеры):
- SEO-агент → суб-агенты (мониторинг позиций, SEO-тексты, оптимизация, ссылки)
- Content-агент → суб-агенты (копирайтинг, редактура, дизайн)
- Ads-агент → суб-агенты (таргет, креативы, аналитика)
- Intelligence-агент → суб-агенты (мониторинг рынка, конкуренты, тренды)

### Core Components (meAI)

1. **Memory System** (`obsidian/`)
   - `AIM/` — Agency context, strategy, decisions
   - `market/` — Market intelligence (players, segments, events)
   - `decisions/` — Architecture decisions and rationale
   - `learnings/` — Patterns, solutions, experience

2. **Assistant Core** (`src/meai/`)
   - `core/` — Main orchestration logic
   - `memory/` — Obsidian integration, context retrieval
   - `skills/` — Claude skills wrappers and automation
   - `agents/` — Agent creation and management
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
