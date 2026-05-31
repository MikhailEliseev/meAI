# Phase 21: CI Pipeline Unification -- Research

**Date:** 2026-05-29
**Status:** Complete
**Purpose:** Technical research to inform the PLAN.md

---

## 1. Current State: Two Pipelines, One Purpose

### 1.1 Pipeline A: CiMarketingAnalyzer (Press-Release)

**Location:** `AIM/src/aim/services/ci_marketing_analysis.py` (547 lines)

**Flow:**
```
AnalyzeCompetitorsRequest
  → CiMarketingAnalyzer.analyze(url, competitors, ...)
    → PipelineRunner.run(client_url, named_competitors)
        → Parallel: financials, SEO, social, website, reviews per competitor
        → Returns list[CompetitorFull]
    → ComparisonMatrixBuilder.build(client_url, client_features, collected)
        → Compacts CompetitorFull into ~5000-token matrix
    → Local analysis (no LLM):
        → _extract_tactics_from_matrix() → tactics (max 8)
        → _extract_swot_from_matrix() → SWOT (5 items per quadrant)
        → _top_rec_from_matrix() → single strategic recommendation
    → compute_wow_numbers() → WowMetrics (3 WOW numbers)
    → _generate_analysis_summary() → markdown chat_summary
  → Returns CiAnalysisResult dataclass
```

**Characteristics:**
- Synchronous (fast, ~10s)
- No LLM -- deterministic rule-based analysis
- Output: `CiAnalysisResult` dataclass with chat_summary, feature_matrix, pricing, positioning, SWOT, tactics, WOW
- Uses shared `aic/services/ci/` modules: pipeline_runner, comparison_matrix, wow_estimator, models
- API: `POST /api/competitors/analyze` and `POST /api/competitors/analyze/stream` (SSE)

**Data model (CiAnalysisResult):**
```python
@dataclass
class CiAnalysisResult:
    chat_summary: str
    feature_matrix: dict
    pricing_comparison: dict
    positioning_map: dict
    swot_per_competitor: list
    aggregate_swot: Optional[SwotQuadrant]
    steal_worthy_tactics: list
    top_recommendation: str
    wow: Optional[dict]  # {patients_per_month, time_to_result_weeks, cost_per_patient_rub}
    scraped_at: str
    analysis_duration_seconds: float
    error: str
```

### 1.2 Pipeline B: CIOrchestrator (16-Phase)

**Location:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (619 lines)

**Flow:**
```
POST /api/seo/audit {url, competitors, niche, tier}
  → Background asyncio.create_task(_run_audit_background)
    → CIOrchestrator.execute_ci_analysis(task_data)
        → Extract client profile (city, specialization) via service_extractor
        → For each phase in tier.phases:
            → Phase 1-4: Single agent phases (ci-scout, ci-auditor, ci-deep-analyzer, ci-reputation)
            → Phase 5: 9 parallel agents (ci-finance, ci-vacancies, ci-tech, ci-site-crawler,
                          ci-content, ci-pricing, ci-ecosystem, ci-backlink, ci-rank-tracker)
            → Phase 6-16: FactChecker, Strategist, Prioritizer, Marketing, Offer Generator
            → Phase 11-15: TW agents (NOT IMPLEMENTED -- stubs return None)
        → _calculate_quality_score()
        → _generate_reports() → HTML + JSON to AIM/reports/{task_id}/
  → Returns raw dict with findings, reports, quality_score
```

**Characteristics:**
- Async (slow, 1-10 min for deep tier)
- Agent-based: 23 specialized agents, 16 phases
- Output: raw dict (not a dataclass) with nested findings per phase
- API: `POST /api/seo/audit` (async fire-and-forget), `GET /api/seo/audit/{task_id}` (poll)
- Already has tier system: quick (phases 1-4), deep (1-9), full (1-16) -- but all use agents

**Output format (raw dict):**
```python
{
    "task_id": str,
    "tier": str,
    "phases_executed": list[int],
    "execution_time_seconds": int,
    "competitors_analyzed": int,
    "findings": {
        "phase_1": {"phase": 1, "agent": "ci-scout", "status": "success", "result": {...}},
        "phase_2": {...},
        ...
    },
    "reports": {"html_path": str, "json_path": str},
    "quality_score": {"score": int, "confidence": str, ...},
    "errors": list[str],
    "correlation_id": str,
}
```

### 1.3 What's Already Shared

Both pipelines use:
- `ci/models.py` -- CompetitorFull, ComparisonMatrix, WowMetrics, SeoAuditResult, etc.
- `ci/wow_estimator.py` -- compute_wow_numbers() (shared WOW calculator)
- `ci/pipeline_runner.py` -- only used by CiMarketingAnalyzer
- `ci/comparison_matrix.py` -- only used by CiMarketingAnalyzer

### 1.4 What's Different

| Aspect | CiMarketingAnalyzer | CIOrchestrator |
|--------|-------------------|----------------|
| **Architecture** | Monolithic class with methods | Agent-based, phased |
| **Data collection** | PipelineRunner (5 parallel collectors) | Individual agents (ci-finance, ci-tech, ci-pricing...) |
| **Analysis** | Rule-based, deterministic | Agent-based, each agent has its own logic |
| **Output model** | CiAnalysisResult dataclass | Raw dict (no dataclass) |
| **Time** | ~10s | 1-10 min |
| **LLM usage** | None (deterministic) | Each agent may use LLM |
| **SWOT** | Yes (rule-based) | Implicitly in ci-strategist |
| **Tactics** | Yes (rule-based, max 8) | Implicitly in ci-strategist |
| **WOW** | Yes (via shared wow_estimator) | No (WOW not computed) |
| **chat_summary** | Yes (markdown) | No (HTML report instead) |
| **API** | Synchronous + SSE stream | Async fire-and-forget + poll |

---

## 2. Problem H6: EventBus Delegation -- Stub Analysis

### 2.1 Current State

In `CIOrchestrator._execute_single_phase()` (lines 321-385):

```python
# Path 1: Direct call (THE ONLY PATH)
result = await agent.execute_task(task)

# Path 2: EventBus publish (audit only, NOT delegation)
await self.event_bus.publish(Event(
    event_type="ci.agent.completed",
    payload={...}
))
```

The EventBus publish at line 369 is for AUDIT/notification only -- it fires AFTER execution. It does NOT trigger the agent's work. The delegation itself (`agent.execute_task(task)`) is a direct Python call.

### 2.2 Why It's a Stub

1. CIOrchestrator creates agent instances lazily in `_get_agent()` -- they're local objects, not running services
2. Agents implement `execute_task(task)` as an abstract method -- synchronous call pattern
3. The EventBus `subscribe()` is in-memory only -- for publish to trigger an agent, the agent must register a handler via `subscribe()` first
4. None of the CI agents register themselves as subscribers

### 2.3 What Real EventBus Delegation Requires

Three architectural approaches:

**Approach A: In-Process Subscribe (Minimal Change)**
- CIOrchestrator creates agents at init, subscribes them to phase-specific event types
- `publish(task_event)` triggers the agent's handler directly (in-memory callback)
- Works because both orchestrator and agents are in the same process
- PRO: Minimal code change, same process, fast
- CON: Not truly decoupled, no persistence of task routing

**Approach B: Poll-Based Agent Loop (Decoupled)**
- Each CI agent runs as a background task with a polling loop
- Agent calls `event_bus.get_events(target=self.agent_id, status="pending")` in a loop
- When it finds a task event, it processes and marks it as "processed"
- PRO: Truly decoupled, persistent task queue
- CON: Each agent needs a background task, polling overhead, complex lifecycle

**Approach C: Hybrid -- Subscribe for Delegation + Queue for Resilience**
- Primary: Use Approach A (subscribe) for normal operation
- Fallback: Agents check `get_events()` on startup for any missed events (crash recovery)
- PRO: Fast path + resilience
- CON: Most complex, two code paths

### 2.4 Recommendation: Approach A for Phase 21

Given the constraints (Phase 21 already has H1-H6 + L4 to solve, all agents run in-process), Approach A is the right first step:
1. CIOrchestrator creates agent instances at `__init__` (not lazy)
2. Each agent registers a handler via `self.event_bus.subscribe("ci.phase.execute", agent_handler)`
3. CIOrchestrator publishes task events instead of direct calls
4. The handler calls `agent.execute_task(task)` and publishes result back
5. CIOrchestrator collects results via `get_events(correlation_id=...)` or a shared future dict

Approach B can be deferred to a future phase when CI agents become independent services.

---

## 3. Problem L4: Model Inconsistency

### 3.1 Current State

**CiMarketingAnalyzer** returns `CiAnalysisResult` dataclass (defined locally in ci_marketing_analysis.py):
- Structured, typed fields
- Used by API endpoint `POST /api/competitors/analyze`
- Tests validate against this type

**CIOrchestrator** returns raw `dict`:
- No type safety
- Nested dicts with string keys ("phase_1", "phase_2", ...)
- Different structure from CiAnalysisResult
- Used by API endpoint `POST /api/seo/audit`

### 3.2 Unification Strategy

**Option 1: Extend CiAnalysisResult with CIOrchestrator fields**
- Add optional fields for CIOrchestrator output (findings, reports, quality_score, etc.)
- Both pipelines return the same dataclass
- PRO: One type, existing tests don't break
- CON: CiAnalysisResult becomes a "god object" with many optional fields

**Option 2: Create a new unified CiAnalysisResult in ci/models.py**
- Move CiAnalysisResult to `ci/models.py` (canonical location)
- Define it with all fields from both pipelines
- Both pipelines return this new unified type
- PRO: Clean separation, canonical location
- CON: Migration needed

**Option 3: Use Pydantic with discriminated union**
- Define BaseCiResult with common fields and a `tier` discriminator
- QuickAnalysisResult and DeepAnalysisResult inherit with tier-specific fields
- PRO: Type-safe, no god objects
- CON: More complex, API consumers need to handle both types

### 3.3 Recommendation: Option 2 (Single Unified Dataclass in ci/models.py)

The dataclass should be:

```python
@dataclass
class UnifiedCiResult:
    # ── Common (both tiers) ──
    tier: str  # "quick" | "deep" | "full"
    chat_summary: str
    top_recommendation: str
    wow: Optional[dict]
    scraped_at: str
    analysis_duration_seconds: float
    error: str

    # ── Quick-tier specific ──
    feature_matrix: dict
    pricing_comparison: dict
    positioning_map: dict
    aggregate_swot: Optional[SwotQuadrant]
    steal_worthy_tactics: list

    # ── Deep-tier specific ──
    findings: dict  # per-phase results
    reports: dict  # HTML/JSON paths
    quality_score: dict
    phases_executed: list[int]
    competitors_analyzed: int
```

All optional fields default to empty/falsy values. This preserves backward compatibility -- existing consumers of CiAnalysisResult see the same fields.

---

## 4. Unification Pattern: Tier-Based Routing

### 4.1 Target Architecture

```
POST /api/seo/audit?tier=quick|deep|full
  │
  ▼
CIOrchestrator.execute_ci_analysis(task_data, tier)
  │
  ├─ tier == "quick":
  │   _run_quick_analysis(task_data)
  │     → PipelineRunner.run()
  │     → ComparisonMatrixBuilder.build()
  │     → _extract_tactics, _extract_swot, _top_rec
  │     → compute_wow_numbers()
  │     → _generate_analysis_summary()
  │     → Return UnifiedCiResult
  │
  ├─ tier == "deep":
  │   _run_deep_analysis(task_data)
  │     → Phase 1: ci-scout (EventBus delegate)
  │     → Phase 2: ci-auditor
  │     → Phase 3-4: ci-deep-analyzer, ci-reputation
  │     → Phase 5: Parallel (ci-finance, ci-tech, ...)
  │     → Phase 6-9: ci-factchecker, ci-strategist, ci-prioritizer
  │     → Return UnifiedCiResult
  │
  └─ tier == "full":
      _run_deep_analysis(task_data, phases=1..16)
```

### 4.2 API Unification

Per decisions D-10 and D-11:
- `POST /api/seo/audit` becomes the single endpoint with `tier` parameter
- `POST /api/competitors/analyze` becomes an alias redirecting to `/api/seo/audit?tier=quick`
- `POST /api/competitors/analyze/stream` (SSE) preserved for streaming progress on quick tier

**Route mapping:**

| Old Route | New Route |
|-----------|-----------|
| `POST /api/competitors/analyze` | `POST /api/seo/audit` with `{"tier": "quick"}` |
| `POST /api/competitors/analyze/stream` | `POST /api/seo/audit/stream` with `{"tier": "quick"}` |
| `POST /api/seo/audit` | `POST /api/seo/audit` with `{"tier": "deep"}` (same) |

### 4.3 What MOVES from CiMarketingAnalyzer to CIOrchestrator

Per decision D-04, these methods move into CIOrchestrator as private methods:

| CiMarketingAnalyzer method | Becomes CIOrchestrator method |
|---|---|
| `analyze()` | `_run_quick_analysis()` |
| `_extract_tactics_from_matrix()` | `_extract_tactics_from_matrix()` |
| `_extract_swot_from_matrix()` | `_extract_swot_from_matrix()` |
| `_top_rec_from_matrix()` | `_top_rec_from_matrix()` |
| `_generate_analysis_summary()` | `_generate_analysis_summary()` |
| `_feature_matrix_legacy()` | `_feature_matrix_legacy()` |
| `_pricing_legacy()` | `_pricing_legacy()` |
| `_positioning_legacy()` | `_positioning_legacy()` |

Helper function `_tactic_impact_effort()` also moves.

CiMarketingAnalyzer itself can be deleted or kept as a thin wrapper for backward compatibility.

---

## 5. EventBus Delegation Implementation Plan

### 5.1 Event Types

New event types for CI agent delegation:

```
ci.task.dispatched  -- Published by orchestrator when assigning task to agent
ci.task.completed   -- Published by agent when task is done
ci.task.failed      -- Published by agent when task fails
```

**Task dispatched event:**
```python
BaseEvent(
    type="ci.task.dispatched",
    source="ci-orchestrator",
    target="ci-scout",  # specific agent ID
    correlation_id="ci-abc123",
    metadata={
        "phase": 1,
        "task_data": {...},
    }
)
```

**Task completed event:**
```python
BaseEvent(
    type="ci.task.completed",
    source="ci-scout",
    target="ci-orchestrator",
    correlation_id="ci-abc123",
    reply_to="evt-xxx",  # ID of the dispatched event
    metadata={
        "phase": 1,
        "result": {...},
    }
)
```

### 5.2 Subscribe Pattern

CIOrchestrator registers handlers for completion events:

```python
# In CIOrchestrator.__init__:
self._pending_tasks: dict[str, asyncio.Future] = {}

self.event_bus.subscribe("ci.task.completed", self._on_agent_completed)
self.event_bus.subscribe("ci.task.failed", self._on_agent_failed)
```

When dispatching:
```python
async def _dispatch_to_agent(self, agent_id: str, task_data: dict) -> dict:
    future = asyncio.get_event_loop().create_future()
    self._pending_tasks[task_data["correlation_id"]] = future

    await self.event_bus.publish(BaseEvent(
        type="ci.task.dispatched",
        source=self.agent_id,
        target=agent_id,
        correlation_id=task_data["correlation_id"],
        metadata=task_data,
    ))

    # Also call agent directly (hybrid approach -- EventBus for audit, direct for execution)
    agent = self._get_agent(agent_id)
    if agent:
        task = self._build_task(task_data)
        result = await agent.execute_task(task)
        future.set_result(result.result)

    return await future
```

Note: For Phase 21, the hybrid approach works best -- EventBus for event audit/storage, direct calls for execution. Full decoupling (agents as independent services listening to events) is deferred.

### 5.3 Agent Subscription

Each CI agent registers to receive its tasks:

```python
# In CI agent __init__ or initialize():
async def initialize(self):
    await super().initialize()
    self.event_bus.subscribe("ci.task.dispatched", self._handle_dispatched)

async def _handle_dispatched(self, event: BaseEvent):
    if event.target != self.agent_id:
        return  # Not for me
    # Execute and publish result
    ...
```

However, since all agents are lazy-initialized in CIOrchestrator._get_agent(), the subscribe must happen there:

```python
def _get_agent(self, agent_name: str):
    ...
    agent = CIScoutAgent(...)
    # Register for events
    agent.event_bus.subscribe("ci.task.dispatched", agent._handle_dispatched)
    self._agent_instances[agent_name] = agent
    return agent
```

---

## 6. Risks and Mitigations

### 6.1 H1 Pipeline Duplication

| Risk | Impact | Mitigation |
|------|--------|------------|
| CiMarketingAnalyzer methods don't cleanly map to CIOrchestrator | Methods fail in new context | Keep all method signatures identical, only change `self` context. The methods don't depend on CiMarketingAnalyzer state -- they're pure functions on matrix data |
| PipelineRunner timeout (180s) conflicts with quick tier expectation (~10s) | Quick tier becomes slow | PipelineRunner already runs parallel collectors -- actual time is limited by SEO audit. Keep quick tier timeout at 15s (current behavior) |
| Tests break | 41 integration tests need updating | Tests use `CiMarketingAnalyzer` directly. They'll need to use `CIOrchestrator._run_quick_analysis()` or (better) keep CiMarketingAnalyzer as a thin proxy that delegates to CIOrchestrator |

### 6.2 H6 EventBus Stub

| Risk | Impact | Mitigation |
|------|--------|------------|
| EventBus subscribe is in-memory, not persistent | If orchestrator crashes, delegated tasks are lost | Accept for now. The task is already tracked by AuditTask store. If needed, replay from get_events() on restart |
| CI agents have their OWN EventBus instance | Agent publishes to ITS bus, not orchestrator's bus | CIOrchestrator must inject its event_bus into each agent. Currently agents create their own in Agent.__init__(). Fix by passing event_bus to agent constructor |
| Race condition: agent completes before orchestrator sets up future | Result lost | Use correlation_id lookup in completion handler, not just future dict. Completion handler stores result, orchestrator polls get_events() |

### 6.3 L4 Model Inconsistency

| Risk | Impact | Mitigation |
|------|--------|------------|
| Unified CiResult has too many optional fields | Consumers must null-check everything | Group fields by tier with clear docstrings. Use `is_quick` flag so consumers can branch |
| API response format changes | Hermes tool and frontend break | Maintain backward-compatible response shapes. The `POST /api/seo/audit` endpoint already returns a dict -- add the quick-tier fields to it |
| CiMarketingAnalyzer still used in 2 places | Stale code paths | After migration, CiMarketingAnalyzer becomes a thin wrapper that instantiates CIOrchestrator and calls _run_quick_analysis(). Deprecate, don't delete |

### 6.4 API Contract

| Risk | Impact | Mitigation |
|------|--------|------------|
| `/api/competitors/analyze` renamed | Hermes tool run_ci_analysis.py calls this | Keep old endpoint as redirect with deprecation warning |
| Response format changes | run_ci_analysis.py parses specific fields | Add all CiAnalysisResult fields to unified response. Fields like `feature_matrix`, `pricing_comparison` must remain at top level |
| SSE streaming changes | Frontend expects specific event format | Preserve SSE event format (`type: "progress"` and `type: "result"`) |

### 6.5 Test Migration

| Risk | Impact | Mitigation |
|------|--------|------------|
| 41 integration tests use CiMarketingAnalyzer | All tests need import changes | Keep CiMarketingAnalyzer as proxy during migration. Tests see no change |
| CIOrchestrator init requires EventBus | Tests need EventBus setup | Add test constructor: `CIOrchestrator.for_testing(event_bus=MemoryEventBus())` |
| Agent mocks need updating | Agent tests reference old patterns | Phase 21 scope is orchestrator, not individual agents. Agent tests not affected |

---

## 7. What Tests Expect -- Cannot Break

### 7.1 CiMarketingAnalyzer Tests (41 tests in test_ci_pipeline_integration.py)

**Direct dependencies:**
- `CiMarketingAnalyzer(timeout=30.0)` constructor
- `.analyze(url, specialization, city, services, competitors, ...)` method
- `._extract_tactics_from_matrix(matrix)` → list[dict] with keys: tactic, competitor, impact, effort, why
- `._extract_swot_from_matrix(matrix)` → dict with keys: strengths, weaknesses, opportunities, threats (max 5 each)
- `._top_rec_from_matrix(matrix)` → str
- `._generate_analysis_summary(matrix, swot, tactics, rec, wow)` → markdown with 6 required sections
- `_tactic_impact_effort(feature_name)` → (impact: str, effort: str) tuple
- `CiAnalysisResult` dataclass fields
- `SwotQuadrant` dataclass fields
- `WowMetrics` dataclass fields
- `compute_wow_numbers()` function

**What must stay:**
- All method signatures
- All return types
- WOW calculation logic (exact numbers: weak_competitors=63 patients, strong=50)
- SWOT quadrant limits (max 5)
- Tactics limit (max 8)
- Tactics sort order (impact then effort)

### 7.2 CIOrchestrator Tests

**Tests in test_ci_scout.py, test_ci_strategist.py, test_ci_content.py:**
- Agent-level tests, not orchestrator tests
- Test individual agents independently (not through orchestrator)
- These are NOT affected by Phase 21

### 7.3 API Tests (Hermes tools)

**run_ci_analysis.py** calls `/api/competitors/analyze`:
- Expects: `{"success": true, "chat_summary": ..., "feature_matrix": ..., ...}`
- These fields must be present in any unified response from the new endpoint

**run_seo_audit.py** calls `/api/seo/audit`:
- Expects: `{"task_id": ..., "status": ..., "result": {findings, reports, ...}}`
- Poll pattern (fire-and-forget + GET) must be preserved

---

## 8. Code Analysis: CIOrchestrator.__init__ vs Agent.__init__

### 8.1 Signature Mismatch

```python
# Agent.__init__ (base class)
def __init__(self, agent_id, agent_type, database_url, vault_path="./obsidian")

# CIOrchestrator.__init__ (current)
def __init__(self, agent_id, event_bus, database_url="sqlite+...", vault_path="AIM/obsidian/ci-orchestrator")
```

CIOrchestrator does NOT call `super().__init__()` with `agent_type`. It does call `super().__init__(agent_id, database_url, vault_path)` -- which is missing `agent_type`. This means:
- `self.agent_type` is never set on CIOrchestrator
- `self.db` and `self.vault` ARE set from Agent.__init__

### 8.2 The Fix: Proper Initialization

```python
class CIOrchestrator(Agent):
    def __init__(self, agent_id, event_bus, database_url=..., vault_path=...):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-orchestrator",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.event_bus = event_bus  # Use injected event_bus, not self.event_bus from Agent
        ...
```

Wait -- `Agent.__init__` creates `self.event_bus = EventBus(database_url)`. CIOrchestrator then overwrites with `self.event_bus = event_bus` (the injected one). This is intentional but messy. Better: Agent base should accept optional `event_bus` parameter:

```python
class Agent(ABC):
    def __init__(self, agent_id, agent_type, database_url, vault_path, event_bus=None):
        ...
        self.event_bus = event_bus or EventBus(database_url)
```

This is a small framework-level change needed for Phase 21.

---

## 9. Recommendations

### 9.1 Implementation Order

**Phase 21 should proceed in this order:**

1. **L4 (Models):** Move CiAnalysisResult to ci/models.py as UnifiedCiResult. Add deep-tier fields. CiMarketingAnalyzer imports from new location.

2. **H1 (Pipeline):** Move CiMarketingAnalyzer methods into CIOrchestrator as private methods. Add tier-based routing in execute_ci_analysis(). Keep CiMarketingAnalyzer as thin proxy for test compatibility.

3. **H6 (EventBus):** Implement Approach A (in-process subscribe). Add event types ci.task.dispatched/completed/failed. CIOrchestrator subscribes agents and publishes tasks instead of direct calls.

4. **API (D-10/D-11):** Unify endpoints. /api/seo/audit handles all tiers. /api/competitors/analyze becomes redirect/alias.

5. **Tests:** Update imports. Verify all 41 tests pass with new code paths.

### 9.2 What NOT to Do

- Do NOT delete PipelineRunner or ComparisonMatrix -- they're needed by quick tier
- Do NOT change individual CI agents -- they keep execute_task() interface
- Do NOT implement full event-driven agents (Approach B) -- deferred to future phase
- Do NOT change the WOW estimator -- it's already unified
- Do NOT deploy TW agents (phase 11-15) -- they remain stubs

### 9.3 Files That Will Change

| File | Change | Lines affected |
|------|--------|---------------|
| `ci/models.py` | Add UnifiedCiResult dataclass | +50 |
| `ci_orchestrator.py` | Add _run_quick_analysis, tier routing, EventBus delegate | +200, -50 (simplify) |
| `ci_marketing_analysis.py` | Thin proxy or delete methods | -400 (move to orchestrator) |
| `api/seo.py` | Add tier parameter, unified route | +30 |
| `api/competitors.py` | Redirect to /api/seo/audit | -100 (simplify) |
| `Agent base` (`base_agent.py`) | Accept optional event_bus param | +5 |
| `test_ci_pipeline_integration.py` | Update imports | ~10 |
| CI agent files (17 files) | Add event_bus injection (minimal) | +5 each |

### 9.4 Estimated Effort

- L4 Models: 1-2 hours
- H1 Pipeline merge: 3-4 hours
- H6 EventBus delegate: 3-4 hours
- API unification: 1-2 hours
- Test migration: 1-2 hours
- **Total:** ~10-14 hours

### 9.5 Success Criteria

1. Single `POST /api/seo/audit` endpoint with `tier` parameter
2. `tier=quick` returns the same response format as current `/api/competitors/analyze`
3. `tier=deep` returns the same response format as current `/api/seo/audit`
4. All 41 integration tests pass without modification to test assertions
5. EventBus events are published for every CI phase (audit trail)
6. CiMarketingAnalyzer is deprecated (thin proxy or removed)
7. CIOrchestrator.__init__ properly calls super().__init__() with agent_type

---

## 10. Open Questions

1. **Should CiMarketingAnalyzer be deleted or kept as proxy?**
   Recommendation: Keep as thin proxy for one release cycle, then delete. Tests can use proxy during transition.

2. **Should quick tier also use EventBus delegation?**
   Recommendation: No. Quick tier is synchronous for a reason (fast, deterministic). EventBus adds overhead for no benefit. Only deep/full tiers use EventBus.

3. **What about the SSE stream endpoint?**
   Recommendation: `/api/seo/audit/stream?tier=quick` replicates current `/api/competitors/analyze/stream` behavior. Deep tier doesn't stream (it's async poll-based).

4. **Should deep-tier also compute WOW numbers?**
   Recommendation: Yes. Add `compute_wow_numbers()` call at the end of deep analysis, using the collected competitor data (ratings, SEO scores, etc.). This makes deep tier output richer.

---
*Research complete: 2026-05-29*
