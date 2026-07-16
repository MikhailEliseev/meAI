# meAI Core Foundation - Technical Specification

**Date:** 2026-05-01  
**Version:** 1.1 (Updated after Critical Review)  
**Status:** Ready for Implementation  
**Approach:** Follow Existing Plan (Archive v1.0)

**Related Documents:**
- Event Sourcing Design: `.superflow/event-sourcing-design.md`
- Spec Review Summary: `.superflow/spec-review-summary.md`
- Original Plan: `docs/superpowers/archive/v1.0-2026-05-01/`

---

## Overview

This specification defines the technical implementation of meAI Core Foundation MVP, following the pre-approved plan from `docs/superpowers/archive/v1.0-2026-05-01/`.

**Source Plan:** 6130 lines, 25 tasks, Quality 98/100

---

## Architecture

### System Layers

```
meAI Core Foundation
├── Storage Layer
│   ├── SQLite (events, messages, metrics, costs)
│   └── Obsidian (context, vaults, snapshots)
├── Messaging Layer
│   ├── Event Store (immutable log)
│   ├── Event Bus (async pub/sub)
│   └── Priority Queue (P0-P3)
├── Agent Layer
│   ├── Agent Factory (creation)
│   ├── Prompt Generator (templates)
│   └── System Registry (SYSTEM.md)
├── Safety Layer
│   ├── Loop Detector (max depth 5)
│   ├── Timeout Manager (5 min default)
│   ├── Context Monitor (40% rule)
│   └── Shutdown Handler (graceful)
├── Monitoring Layer
│   ├── Health Checker (component status)
│   ├── Metrics Collector (counter/gauge/histogram)
│   ├── Alerting (Telegram)
│   └── Rate Limiter (cost tracking)
├── Core Layer
│   ├── Architect (structure creation, agent orchestration)
│   ├── Decision Maker (autonomous + human-in-loop)
│   ├── Orchestrator (async coordination)
│   └── Rollback Manager (snapshot + event replay)
└── API Layer
    └── FastAPI (REST endpoints)
```

---

## Implementation Plan

### Timeline: 5-6 Weeks (Realistic)

**Original estimate:** 3-4 weeks  
**Adjusted after review:** 5-6 weeks

**Breakdown:**
- Week 1: Tasks 1-7 (Storage & Events)
- Week 2: Tasks 8-14 (Agent Factory & Safety)
- Week 3: Tasks 15-17 (Monitoring & Operations)
- Week 4-5: Tasks 21-25 (Core Components) - Switch to Opus
- Week 6: Tasks 18-20 (Deployment & Testing)

**Why longer:**
- Event sourcing complexity (first-time implementation)
- TDD approach adds 20-30% overhead
- Async patterns require careful testing
- Critical mode = dual-model reviews

### Phase 1: Storage & Events (Tasks 1-7)

**Task 1: Project Setup & Dependencies**
- Python 3.11+ with uv/pip
- Dependencies: FastAPI, SQLAlchemy 2.0 async, aiosqlite, Pydantic, structlog, pytest
- Project structure: src/meai/, tests/, docs/
- pyproject.toml with dependencies

**Task 2: Configuration Management**
- Settings class with Pydantic
- .env file for secrets
- Environment variables: ANTHROPIC_API_KEY, DATABASE_URL, OBSIDIAN_VAULT_PATH, LOG_LEVEL

**Task 3: Database Layer - SQLite Setup**
- SQLAlchemy async models
- Database connection manager with session factory
- Alembic migrations
- Health check method

**Task 4: Obsidian Integration**
- ObsidianVault class with async file I/O
- Vault initialization
- Agent vault creation (per-agent directories)
- Snapshot creation & restore
- File read/write with frontmatter support

**Task 5: Event Store**
- Event sourcing implementation
- Immutable append-only log
- Event replay capability
- Event queries by type/aggregate

**Task 6: Event Bus**
- Async message queue (asyncio.Queue)
- Pub/sub pattern
- Message routing by agent ID
- Priority queue integration

**Task 7: Priority Queue**
- P0-P3 priority levels
- Queue management (enqueue/dequeue)
- Message ordering by priority + timestamp

---

### Phase 2: Agent Factory (Tasks 8-10)

**Task 8: Agent Factory Core**
- Agent creation logic
- Vault initialization per agent
- Prompt generation
- Agent metadata management

**Task 9: Prompt Generator**
- Template-based prompts
- Agent-specific customization
- Vault path injection
- Role and department context

**Task 10: System Registry**
- SYSTEM.md management
- Agent registration (add/remove)
- Agent listing with parsing
- Hierarchy tracking

---

### Phase 3: Safety Mechanisms (Tasks 11-14)

**Task 11: Loop Detector**
- Track delegation depth
- Detect circular calls
- Max depth enforcement (5 levels)
- Clear error messages

**Task 12: Timeout Manager**
- Operation timeouts (5 min default)
- Timeout handlers with asyncio
- Graceful cancellation
- Configurable per-operation

**Task 13: Context Monitor**
- 40% rule enforcement
- Context usage tracking (tokens)
- Auto-compact triggers
- Warning at 40%, error at 100%

**Task 14: Shutdown Handler**
- Signal handlers (SIGINT, SIGTERM)
- Graceful cleanup (async)
- State persistence before exit
- Cleanup callback registration

---

### Phase 4: Monitoring & Operations (Tasks 15-17)

**Task 15: Health Checks + Telegram Alerting**
- HealthChecker with component registration
- Overall and per-component health checks
- TelegramAlerter for notifications
- HealthAlerter for status change detection
- Alert on component failures

**Task 16: Metrics Collection**
- MetricsCollector with SQLite persistence
- Counter, gauge, histogram metrics
- Metric queries (by name, time range)
- Aggregation (sum, avg, min, max)

**Task 17: Rate Limiter + Cost Persistence**
- RateLimiter with aiolimiter
- Budget tracking (monthly)
- Cost persistence to SQLite (api_costs table)
- Per-agent cost tracking
- Alert at 80% budget
- Database migration for api_costs

---

### Phase 5: Deployment & Testing (Tasks 18-20)

**Task 18: FastAPI Application**
- FastAPI app with lifespan management
- Health check endpoint (/health)
- Status endpoint (/status)
- Root endpoint (/)
- Component initialization on startup
- Graceful shutdown on exit

**Task 19: Deployment Configuration**
- Dockerfile (Python 3.11-slim)
- docker-compose.yml
- systemd service file (meai.service)
- DEPLOYMENT.md documentation
- Health check in Docker

**Task 20: End-to-End Integration Test + Documentation**
- E2E test covering full system integration
- Test agent creation workflow
- Test event bus messaging
- Test rollback workflow
- README.md (quick start)
- ARCHITECTURE.md (overview)
- API.md (endpoint reference)
- MVP-CHECKLIST.md (acceptance criteria)

---

### Phase 6: Core Components (Tasks 21-25)

**Task 21: Core Architect Implementation**
- Architect class with real functionality
- create_aim_structure() - creates AIM directory structure
- create_agent() - orchestrates agent creation
- SYSTEM.md generation
- Event recording for all operations
- Integration with Agent Factory

**Task 22: Decision Maker + Notifications**
- DecisionMaker class
- DecisionType enum (autonomous vs human-approval)
- Autonomous decision logic
- Human-in-loop gates
- Telegram notification system for approval requests
- FastAPI endpoints for approval (/approve, /reject)
- Pending approvals tracking
- Approval workflow (request → notify → approve/reject)

**Task 23: Orchestrator**
- Orchestrator class for async coordination
- Component registration
- Parallel health checks
- Sequential workflow execution
- Parallel operation execution

**Task 24: System Registry**
- SystemRegistry class
- SYSTEM.md parsing and management
- Agent registration (add/remove)
- Agent listing with metadata
- Initial SYSTEM.md creation

**Task 25: Rollback Orchestration**
- RollbackManager class
- Checkpoint creation (snapshot + event marker)
- Rollback to checkpoint (restore snapshot + replay events)
- Checkpoint listing
- Integration with ObsidianVault and EventStore

---

## Data Models

### SQLite Tables

**events** (Event Store - Audit Log)
- id (INTEGER PRIMARY KEY)
- aggregate_id (TEXT) - e.g., "agent-123"
- aggregate_type (TEXT) - e.g., "agent", "agency"
- event_type (TEXT) - e.g., "AgentCreated"
- event_version (INTEGER) - Schema version for evolution
- payload (JSON) - Event data
- timestamp (TEXT) - ISO 8601
- idempotency_key (TEXT UNIQUE) - Prevent duplicates
- created_at (TEXT) - When written to store

**messages** (Event Bus - Async Messaging)
- id (INTEGER PRIMARY KEY)
- from_agent (TEXT) - Sender
- to_agent (TEXT) - Receiver (or "*" for broadcast)
- message_type (TEXT) - e.g., "CreateAgent", "Notify"
- priority (INTEGER) - 0 (highest) to 3 (lowest)
- payload (JSON) - Message data
- timestamp (TEXT) - ISO 8601
- processed (BOOLEAN) - Processed flag
- processed_at (TEXT) - When processed
- error (TEXT) - Error if processing failed

**metrics**
- id (INTEGER PRIMARY KEY)
- name (TEXT)
- metric_type (TEXT)
- value (REAL)
- labels (JSON)
- timestamp (TEXT)

**api_costs** (NEW in Task 17)
- id (INTEGER PRIMARY KEY)
- timestamp (TEXT)
- cost (REAL)
- agent_id (TEXT, nullable)
- operation (TEXT, nullable)

### Events vs Messages Clarification

**Events** = Immutable facts about what happened (past tense)
- Stored in Event Store (`events` table)
- Used for audit trail and replay
- Never deleted, only appended
- Examples: "AgentCreated", "StructureBuilt", "DecisionMade"

**Messages** = Commands or queries between agents (imperative)
- Stored in Event Bus (`messages` table)
- Used for async communication
- Marked as processed, can be deleted after 7 days
- Examples: "CreateAgent", "SendNotification", "CheckHealth"

**See:** `.superflow/event-sourcing-design.md` for full design

### Obsidian Structure

```
obsidian/
├── AIM/
│   ├── SYSTEM.md (agent registry)
│   ├── seo/
│   ├── content/
│   ├── ads/
│   └── intelligence/
├── agents/
│   └── {agent-name}/
│       ├── context.md
│       ├── decisions.md
│       └── learnings.md
└── snapshots/
    └── {checkpoint-name}/
```

---

## API Endpoints

### Health & Status

**GET /health**
- Returns: Overall health status + component health
- Status codes: 200 (healthy), 503 (unhealthy)

**GET /status**
- Returns: Architect status (uptime, timestamp)
- Status code: 200

**GET /**
- Returns: Service info (name, version, status)
- Status code: 200

### Decision Management (Task 22)

**POST /decisions/{decision_id}/approve**
- Approves pending decision
- Returns: {status: "approved", decision_id}
- Status codes: 200 (success), 404 (not found)

**POST /decisions/{decision_id}/reject**
- Rejects pending decision
- Body: {reason: string}
- Returns: {status: "rejected", decision_id}
- Status codes: 200 (success), 404 (not found)

**GET /decisions/pending**
- Lists all pending approval requests
- Returns: {pending: [decisions]}
- Status code: 200

---

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
OBSIDIAN_VAULT_PATH=./obsidian

# Optional
LOG_LEVEL=INFO
CLAUDE_API_RATE_LIMIT=50  # requests per minute
CLAUDE_API_BUDGET_MONTHLY=100.0  # USD

# Telegram Alerting (OPTIONAL - recommended for production)
# If not provided, alerts will be logged only
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Telegram Clarification:**
- **MVP:** Optional (alerts logged to structlog if not configured)
- **Production:** Recommended (real-time notifications)
- **Success Criteria #13:** "Alerting system works" = structlog alerts OR Telegram
- **Implementation:** TelegramAlerter checks for credentials, falls back to logging

### Settings Class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "sqlite+aiosqlite:///./data/meai.db"
    obsidian_vault_path: str = "./obsidian"
    log_level: str = "INFO"
    claude_api_rate_limit: int = 50
    claude_api_budget_monthly: float = 100.0
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    
    class Config:
        env_file = ".env"
```

---

## Testing Strategy

### Test Coverage Target: > 80%

**Unit Tests** (per task)
- Test each component in isolation
- Mock external dependencies
- Fast execution (< 1s per test)

**Integration Tests**
- Test component interactions
- Use in-memory SQLite
- Test async workflows

**End-to-End Test** (Task 20)
- Test full system integration
- Create agent → Event bus → Health checks → Rollback
- Verify all components work together

### TDD Approach (per task)

1. Write failing test
2. Run test to verify it fails
3. Implement code
4. Run test to verify it passes
5. Refactor if needed
6. Commit

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data backups
EXPOSE 8000
HEALTHCHECK --interval=30s CMD python -c "import requests; requests.get('http://localhost:8000/health')"
CMD ["uvicorn", "meai.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### systemd

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

---

## Security Considerations

### Secrets Management
- All secrets in .env (never in code)
- .env in .gitignore
- Environment variable validation on startup

### Input Validation
- Pydantic models for all inputs
- Type hints throughout
- Async pattern safety (no blocking I/O)

### API Security
- No authentication in MVP (internal use only)
- Rate limiting enforced
- Budget tracking prevents cost overruns

---

## Success Criteria

### Functional Requirements

1. ✅ meAI can create AIM structure (folders, SYSTEM.md)
2. ✅ Agent Factory creates agents with vaults and prompts
3. ✅ Event Bus handles async messaging with priorities
4. ✅ Health checks show component status
5. ✅ Rollback restores from checkpoints
6. ✅ Safety mechanisms prevent loops, timeouts, context explosion
7. ✅ Secrets managed via .env
8. ✅ Automated backups run successfully
9. ✅ Rate limiting enforces budget
10. ✅ Graceful shutdown works
11. ✅ Tests pass with > 80% coverage
12. ✅ Docker deployment works
13. ✅ Telegram alerts fire on failures

### Non-Functional Requirements

- **Performance:** < 100ms for health checks, < 1s for agent creation
- **Reliability:** Graceful degradation, no data loss on crash
- **Maintainability:** Type hints, docstrings, clear structure
- **Testability:** > 80% coverage, fast tests (< 30s total)

---

## Implementation Order

**Strict Sequential Execution (Dependencies Matter)**

1. Tasks 1-2: Setup & Config (foundation)
2. Tasks 3-4: Storage (database + Obsidian)
3. Tasks 5-7: Events (event store, bus, queue)
4. Tasks 8-10: Agent Factory (creation logic)
5. Tasks 11-14: Safety (loop, timeout, context, shutdown)
6. Tasks 15-17: Monitoring (health, metrics, rate limiter)
7. Tasks 21-25: Core Components (architect, decision maker, orchestrator, registry, rollback)
8. Tasks 18-20: Deployment & Testing (FastAPI, Docker, E2E, docs)

**Note:** Tasks 18-20 moved to end because they depend on all other components.

---

## Model Strategy

### Hybrid Approach (Cost Optimization)

**Tasks 1-17:** Sonnet 4.5 (~$30-50)
- Infrastructure, safety, monitoring
- Standard patterns, well-documented

**Tasks 21-25:** Opus 4.6 (~$50-100)
- Core components (Architect, Decision Maker, Orchestrator)
- Complex architecture, critical logic

**Tasks 18-20:** Haiku 4.5 + Opus review (~$5-10)
- Deployment, testing, documentation
- Boilerplate code with quality review

**Total Estimated Cost:** $85-160 (60% savings vs all-Opus)

---

## Risk Mitigation

### Technical Risks

1. **Async complexity** → Use proven patterns (asyncio, aiosqlite)
2. **Event sourcing bugs** → Simple append-only log, comprehensive tests
3. **Obsidian fragility** → Simple file I/O, git versioning
4. **Cost overruns** → Rate limiter with budget tracking

### Process Risks

1. **Scope creep** → Strict adherence to 25 tasks, no additions
2. **Quality issues** → TDD approach, > 80% coverage, dual-model review in Critical mode
3. **Time overruns** → Follow plan exactly, no improvisation

---

## Reference

**Source Plan:** `docs/superpowers/archive/v1.0-2026-05-01/2026-05-01-meai-core-foundation-plan.md`

**Quality:** 98/100 (Production Ready)  
**Review Cycles:** 3 (user + agent + critical)  
**Issues Fixed:** 24

---

## Approval

**Status:** Ready for Spec Review (Dual-Model in Critical Mode)

**Next Steps:**
1. Spec review by secondary model (if available) or split-focus Claude
2. Address review feedback
3. User approval
4. Create implementation plan
5. Plan review (dual-model)
6. Final user approval
7. Execute (Phase 2)

---

**Created:** 2026-05-01T17:11:51Z  
**Updated:** 2026-05-01T17:11:51Z
