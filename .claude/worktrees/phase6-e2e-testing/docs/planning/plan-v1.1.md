# meAI Core Foundation - Implementation Plan v1.1

**Date:** 2026-05-01  
**Version:** 1.1 (Revised after Critical Review)  
**Status:** Ready for Execution  
**Based on:** Spec v1.1 + Archive v1.0 Plan + Plan Review Recommendations

---

## Overview

This plan implements meAI Core Foundation MVP following the pre-approved 25-task plan from archive, with critical fixes and plan review recommendations applied.

**Timeline:** 6-7 weeks (realistic)  
**Approach:** TDD (test-first)  
**Model Strategy:** Hybrid (Sonnet + Opus + Haiku)  
**Governance:** Critical (dual-model reviews)  
**Cost:** $95-180 (optimized for quality)

---

## Key Changes from v1.0

1. ✅ **Task 10/24 merged** - System Registry now single task in Sprint 2
2. ✅ **Sprint 1 split** - Foundation (1A) + Event System (1B)
3. ✅ **FastAPI moved** - Now in Sprint 4 (before Decision Maker needs it)
4. ✅ **Model strategy optimized** - Opus for Tasks 5-6 (event sourcing)
5. ✅ **Timeline extended** - 5-6 weeks → 6-7 weeks (realistic)
6. ✅ **Integration testing added** - 0.5 days per sprint
7. ✅ **Buffer week added** - Week 7 for integration fixes

---

## Execution Strategy

### Sprint Structure (Revised)

**Sprint 1A (Week 1): Foundation**
- Tasks 1-4: Setup, Config, Database, Obsidian
- Duration: 5 days
- Model: Sonnet 4.5
- Integration test: 0.5 days

**Sprint 1B (Week 1.5): Event System**
- Tasks 5-6: Event Store, Event Bus
- Duration: 3-4 days
- Model: **Opus 4.6** ⭐ (event sourcing complexity)
- Integration test: 0.5 days

**Sprint 2 (Week 2-2.5): Agent Factory & Safety**
- Tasks 8-10: Agent Factory, Prompt Generator, System Registry (merged 10+24)
- Tasks 11-14: Loop Detector, Timeout Manager, Context Monitor, Shutdown Handler
- Duration: 5-7 days
- Model: Sonnet 4.5
- Integration test: 0.5 days

**Sprint 3 (Week 3): Monitoring & Priority Queue**
- Task 7: Priority Queue (moved from Sprint 1)
- Tasks 15-17: Health Checks, Metrics, Rate Limiter
- Duration: 5 days
- Model: Sonnet 4.5
- Integration test: 0.5 days

**Sprint 4 (Week 4): FastAPI + Core Components Start**
- Task 18: FastAPI Application (moved from Sprint 6)
- Tasks 21-22: Core Architect, Decision Maker
- Duration: 5 days
- Model: **Opus 4.6** ⭐
- Integration test: 0.5 days

**Sprint 5 (Week 5): Core Components Complete**
- Tasks 23-25: Orchestrator, Rollback Orchestration
- Duration: 5 days
- Model: **Opus 4.6** ⭐
- Integration test: 1 day

**Sprint 6 (Week 6): Deployment & E2E Testing**
- Task 19: Docker, systemd, deployment docs
- Task 20: End-to-End Integration Test
- Duration: 5 days
- Model: Haiku 4.5 (Task 19), Sonnet 4.5 (Task 20)

**Buffer Week (Week 7): Integration & Polish**
- Fix issues found in E2E
- Documentation polish
- Final review
- Duration: 3-5 days

**Total: 6-7 weeks**

---

## Task List (24 Tasks - Task 24 merged into Task 10)

### Sprint 1A: Foundation (Tasks 1-4)

**Task 1: Project Setup & Dependencies** ✅ DONE
- Status: Dependencies added to pyproject.toml
- Next: Install dependencies with `pip install -e .`

**Task 2: Configuration Management**
- Create Settings class with Pydantic
- Create .env.example
- Validate environment variables on startup
- Test: Settings loads from .env correctly

**Task 3: Database Layer - SQLite Setup**
- SQLAlchemy async models
- Database connection manager with session factory
- Alembic migrations setup
- WAL mode configuration (for concurrency)
- Health check method
- Test: Database connects, migrations run

**Task 4: Obsidian Integration**
- ObsidianVault class with aiofiles
- Vault initialization
- Agent vault creation (per-agent directories)
- Snapshot creation & restore
- File read/write with frontmatter support
- File locking (prevent corruption)
- Test: Vault operations work, snapshots restore correctly

**Integration Test (0.5 days):**
- Database + Obsidian integration
- Verify config loads, database connects, vault initializes

---

### Sprint 1B: Event System (Tasks 5-6) ⭐ OPUS

**Task 5: Event Store**
- Implement based on event-sourcing-design.md
- Events table with versioning + idempotency
- Append event with optimistic locking
- Get events with filters
- Replay events (skip side effects)
- Concurrent write handling
- Test: Append, replay, idempotency, concurrent writes

**Task 6: Event Bus**
- Implement based on event-sourcing-design.md
- Messages table with priority
- Publish message (persist to SQLite first)
- Subscribe with asyncio.Queue
- Mark processed
- Priority-based routing (P0-P3)
- Durability (persist before processing)
- Test: Publish, subscribe, priority ordering, crash recovery

**Integration Test (0.5 days):**
- Event Store + Event Bus integration
- Verify events append, messages route correctly

---

### Sprint 2: Agent Factory & Safety (Tasks 8-10, 11-14)

**Task 8: Agent Factory Core**
- Agent creation logic
- Vault initialization per agent
- Prompt generation integration
- Agent metadata management
- Test: Create agent, vault initialized

**Task 9: Prompt Generator**
- Template-based prompts
- Agent-specific customization
- Vault path injection
- Role and department context
- Test: Prompts generate correctly

**Task 10: System Registry** (MERGED with Task 24)
- SystemRegistry class
- SYSTEM.md management (create, parse, update)
- Agent registration (add/remove)
- Agent listing with metadata
- Hierarchy tracking
- Test: Register agent, list agents, parse SYSTEM.md

**Task 11: Loop Detector**
- Track delegation depth
- Detect circular calls
- Max depth enforcement (5 levels)
- Clear error messages
- Test: Detect loops, enforce max depth

**Task 12: Timeout Manager**
- Operation timeouts (5 min default)
- Timeout handlers with asyncio
- Graceful cancellation
- Configurable per-operation
- Test: Timeout fires, cancellation works

**Task 13: Context Monitor**
- 40% rule enforcement
- Context usage tracking (tokens)
- Auto-compact triggers
- Warning at 40%, error at 100%
- Test: Track usage, trigger warnings

**Task 14: Shutdown Handler**
- Signal handlers (SIGINT, SIGTERM)
- Graceful cleanup (async)
- State persistence before exit
- Cleanup callback registration
- Test: Graceful shutdown, callbacks execute

**Integration Test (0.5 days):**
- Agent Factory + Safety integration
- Verify agent creation with safety mechanisms active

---

### Sprint 3: Monitoring & Priority Queue (Task 7, 15-17)

**Task 7: Priority Queue** (moved from Sprint 1)
- Integrate with Event Bus
- P0-P3 priority levels
- Queue management (enqueue/dequeue)
- Message ordering by priority + timestamp
- Test: Priority ordering works

**Task 15: Health Checks + Telegram Alerting**
- HealthChecker with component registration
- TelegramAlerter (optional, falls back to logging)
- HealthAlerter for status change detection
- Alert on component failures
- Test: Health checks, alerts fire

**Task 16: Metrics Collection**
- MetricsCollector with SQLite persistence
- Counter, gauge, histogram metrics
- Metric queries (by name, time range)
- Aggregation (sum, avg, min, max)
- Test: Metrics collect, query correctly

**Task 17: Rate Limiter + Cost Persistence**
- RateLimiter with aiolimiter
- Budget tracking (monthly)
- Cost persistence to SQLite (api_costs table)
- Per-agent cost tracking
- Alert at 80% budget
- Database migration for api_costs
- Test: Rate limiting, cost tracking, budget alerts

**Integration Test (0.5 days):**
- Monitoring stack integration
- Verify health checks, metrics, rate limiting work together

---

### Sprint 4: FastAPI + Core Components Start (Task 18, 21-22) ⭐ OPUS

**Task 18: FastAPI Application** (moved from Sprint 6)
- FastAPI app with lifespan management
- Health check endpoint (/health)
- Status endpoint (/status)
- Root endpoint (/)
- Component initialization on startup
- Graceful shutdown on exit
- Test: Endpoints respond, startup/shutdown work

**Task 21: Core Architect Implementation**
- Architect class with real functionality
- create_aim_structure() - creates AIM directory structure
- create_agent() - orchestrates agent creation
- SYSTEM.md generation
- Event recording for all operations
- Integration with Agent Factory
- Test: Create AIM structure, create agent end-to-end

**Task 22: Decision Maker + Notifications**
- DecisionMaker class
- DecisionType enum (autonomous vs human-approval)
- Autonomous decision logic
- Human-in-loop gates
- Telegram notification system (optional)
- FastAPI endpoints for approval (/decisions/*)
- Pending approvals tracking
- Approval workflow (request → notify → approve/reject)
- Test: Autonomous decisions, approval workflow

**Integration Test (0.5 days):**
- FastAPI + Core Components integration
- Verify API endpoints work with Architect and Decision Maker

---

### Sprint 5: Core Components Complete (Tasks 23-25) ⭐ OPUS

**Task 23: Orchestrator**
- Orchestrator class for async coordination
- Component registration
- Parallel health checks
- Sequential workflow execution
- Parallel operation execution
- Test: Orchestrate components, workflows execute

**Task 25: Rollback Orchestration**
- RollbackManager class
- Checkpoint creation (snapshot + event marker)
- Rollback to checkpoint (restore snapshot + replay events)
- Checkpoint listing
- Integration with ObsidianVault and EventStore
- Dry-run mode
- Rollback validation
- Test: Create checkpoint, rollback, verify state restored

**Integration Test (1 day):**
- Full Core Components integration
- Verify Architect, Decision Maker, Orchestrator, Rollback work together
- Test full agent creation workflow
- Test rollback workflow

---

### Sprint 6: Deployment & E2E Testing (Tasks 19-20)

**Task 19: Deployment Configuration**
- Dockerfile (Python 3.11-slim)
- docker-compose.yml
- systemd service file (meai.service)
- DEPLOYMENT.md documentation
- Health check in Docker
- Test: Docker image builds, container runs

**Task 20: End-to-End Integration Test + Documentation**
- E2E test covering full system integration
- Test agent creation workflow (end-to-end)
- Test event bus messaging
- Test rollback workflow
- Test decision approval workflow
- README.md (quick start)
- ARCHITECTURE.md (system overview)
- API.md (endpoint reference)
- MVP-CHECKLIST.md (acceptance criteria)
- Test: E2E test passes, all 13 MVP criteria met

---

## Model Strategy (Revised)

### Week 1: Sonnet 4.5
```bash
/model sonnet
# Execute Tasks 1-4 (Foundation)
```

### Week 1.5: Opus 4.6 ⭐
```bash
/model opus
# Execute Tasks 5-6 (Event Sourcing)
```

### Week 2-3: Sonnet 4.5
```bash
/model sonnet
# Execute Tasks 7-17 (Agent Factory, Safety, Monitoring)
```

### Week 4-5: Opus 4.6 ⭐
```bash
/model opus
# Execute Tasks 18, 21-23, 25 (FastAPI + Core Components)
```

### Week 6: Haiku 4.5 + Sonnet 4.5
```bash
/model haiku
# Execute Task 19 (Deployment)

/model sonnet
# Execute Task 20 (E2E Test)
```

**Cost Breakdown:**
- Sonnet (Tasks 1-4, 7-17, 20): ~$40-60
- Opus (Tasks 5-6, 18, 21-23, 25): ~$50-110
- Haiku (Task 19): ~$5-10
- **Total: $95-180** (+$10-20 vs original for better quality)

---

## Context Management Plan

### Compaction Points

**After Sprint 2:**
- Compact before Sprint 3
- Preserve: Event sourcing design, agent factory patterns

**After Sprint 4:**
- Compact before Sprint 5
- Preserve: Core architecture decisions, API design

### Handoff Documents

**After Sprint 1B (Opus → Sonnet):**
- Event sourcing decisions
- Event Store vs Event Bus distinction
- Replay semantics

**After Sprint 3 (Sonnet → Opus):**
- Agent Factory patterns
- Safety mechanism implementations
- Monitoring setup

**After Sprint 5 (Opus → Sonnet/Haiku):**
- Core component integration points
- API endpoints
- Rollback workflow

---

## Implementation Guidelines

### TDD Approach (Every Task)

1. **Write failing test** - Test what you want to build
2. **Run test** - Verify it fails (red)
3. **Implement code** - Make it pass
4. **Run test** - Verify it passes (green)
5. **Refactor** - Clean up if needed
6. **Commit** - Atomic commit per task

### Code Quality Standards

- **Type hints:** All functions and methods
- **Docstrings:** All public APIs
- **Async/await:** Consistent async patterns
- **Error handling:** Try/except with specific exceptions
- **Logging:** structlog for all operations
- **Validation:** Pydantic for all inputs

### Testing Standards

- **Unit tests:** Per component, mocked dependencies
- **Integration tests:** 0.5-1 day per sprint
- **E2E test:** Sprint 6
- **Coverage:** > 80% target
- **Test time:** 5-10 minutes total (realistic)

### Commit Standards

```
<type>: <subject>

<body>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Types:** feat, fix, docs, test, refactor, chore

---

## Sprint Reviews (Critical Mode)

After each sprint:
1. **Code review** - Dual-model review of all code
2. **Integration test** - Verify sprint deliverable
3. **User approval** - Present progress, get feedback
4. **Adjust plan** - If needed based on feedback

**User Availability SLA:** 24-hour response time for approvals

---

## Risk Mitigation

### High-Risk Tasks

**Task 5 (Event Store):**
- Risk: Event sourcing complexity
- Mitigation: Use Opus model, follow event-sourcing-design.md exactly
- Extra testing: Concurrent writes, replay, idempotency

**Task 6 (Event Bus):**
- Risk: Async message queue complexity
- Mitigation: Use Opus model, persist before processing
- Extra testing: Priority ordering, crash recovery, durability

**Task 21 (Architect):**
- Risk: Many dependencies, orchestration hub
- Mitigation: Use Opus model, thorough integration tests
- Extra testing: Full agent creation workflow

**Task 25 (Rollback):**
- Risk: Snapshot + replay coordination
- Mitigation: Use Opus model, dry-run mode, validation
- Extra testing: Partial failures, rollback-rollback

---

## Success Criteria

### Sprint 1A Complete When:
- [ ] Database connects and migrations run
- [ ] Obsidian vault initializes
- [ ] Config loads from .env
- [ ] All tests pass (> 80% coverage)

### Sprint 1B Complete When:
- [ ] Events can be appended and replayed
- [ ] Messages can be published and consumed
- [ ] Concurrent writes handled correctly
- [ ] All tests pass

### Sprint 2 Complete When:
- [ ] Agent Factory creates agents with vaults
- [ ] Prompts generate correctly
- [ ] SYSTEM.md updates on agent creation
- [ ] Loop detector catches circular calls
- [ ] Timeouts work correctly
- [ ] Context monitor enforces 40% rule
- [ ] Graceful shutdown works
- [ ] All tests pass

### Sprint 3 Complete When:
- [ ] Priority queue orders messages correctly
- [ ] Health checks show component status
- [ ] Metrics collect and query correctly
- [ ] Rate limiter enforces budget
- [ ] Costs persist to database
- [ ] Alerts fire (Telegram or logs)
- [ ] All tests pass

### Sprint 4 Complete When:
- [ ] FastAPI app runs and serves endpoints
- [ ] Architect creates AIM structure
- [ ] Architect creates agents end-to-end
- [ ] Decision Maker handles autonomous decisions
- [ ] Decision Maker requests human approval
- [ ] All tests pass

### Sprint 5 Complete When:
- [ ] Orchestrator coordinates components
- [ ] Rollback restores from checkpoints
- [ ] All core components integrated
- [ ] All tests pass

### Sprint 6 Complete When:
- [ ] Docker image builds and runs
- [ ] systemd service works
- [ ] E2E test passes
- [ ] All documentation complete
- [ ] MVP checklist 13/13 ✅

---

## MVP Checklist (13 Criteria)

1. [ ] meAI can create AIM structure (folders, SYSTEM.md)
2. [ ] Agent Factory works (creates agents with vaults and prompts)
3. [ ] Event Bus works (SQLite + async)
4. [ ] Monitoring shows status (health checks)
5. [ ] Rollback works (versioning + restore)
6. [ ] Safety mechanisms work (loop detection, timeouts)
7. [ ] Secrets management (API keys in .env)
8. [ ] Automated backups (SQLite + Obsidian)
9. [ ] Rate limiting (Claude API)
10. [ ] Graceful shutdown
11. [ ] Testing infrastructure (> 80% coverage)
12. [ ] Deployment strategy (Docker/systemd)
13. [ ] Alerting system (Telegram or structlog)

---

## Reference Materials

**Archive:** `docs/superpowers/archive/v1.0-2026-05-01/`
- Original plan: 2026-05-01-meai-core-foundation-plan.md (6130 lines)
- Design spec: 2026-05-01-meai-architect-design.md (726 lines)

**Planning Docs:** `docs/planning/`
- Spec v1.1: spec-v1.1.md
- Event Sourcing Design: event-sourcing-design.md
- Plan Review Summary: plan-review-summary.md (in .superflow/)

---

## Next Steps

1. ✅ **Plan Review Complete** - Dual-model review done
2. ⬜ **User Final Approval** - Approve this revised plan
3. ⬜ **Create Charter** - Lock in plan, create execution charter
4. ⬜ **Phase 2: Execution** - Start Sprint 1A (Tasks 1-4)

---

**Status:** Ready for User Approval  
**Version:** 1.1 (Revised)  
**Created:** 2026-05-01T18:12:45Z
