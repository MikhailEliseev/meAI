---
phase: 21-ci-pipeline-unification
verified: 2026-05-31T18:15:00Z
status: gaps_found
score: 4/9 roadmap success criteria verified
overrides_applied: 0
overrides: []
gaps:
  - truth: "Quick tier → PipelineRunner + ComparisonMatrix + локальный анализ (~10 сек)"
    status: failed
    reason: "Method _run_quick_analysis does not exist on CIOrchestrator. execute_ci_analysis() routes all tiers through the same EventBus-based _execute_single_phase() path. The test expects it: 'assert \"_run_quick_analysis\" in src' (test_ci_pipeline_integration.py:626). Also, the API endpoint at competitors.py:226 calls orchestrator._run_quick_analysis() which will raise AttributeError at runtime."
    artifacts:
      - path: "AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py"
        issue: "No _run_quick_analysis method defined. All 24 methods listed; none implement quick-tier PipelineRunner + ComparisonMatrix path."
      - path: "AIM/src/aim/api/competitors.py"
        issue: "Line 226 calls orchestrator._run_quick_analysis(...) — method does not exist, endpoint is broken."
    missing:
      - "Implement _run_quick_analysis(task_data) on CIOrchestrator routing to PipelineRunner + ComparisonMatrix for ~10s quick tier"
      - "Or: Remove the broken competitors.py API endpoint that calls nonexistent method"

  - truth: "CiMarketingAnalyzer → thin backward-compatible proxy"
    status: failed
    reason: "CiMarketingAnalyzer (ci_marketing_analysis.py:797) is a full 1000+ line standalone class with its own CompetitorPageScraper, SwotEngine, TacticExtractor, FeatureMapper, PricingAnalyzer, PositioningMapper, ReportFormatter. It does NOT delegate to CIOrchestrator. The CONTEXT.md declared this 'DONE' in wave 2, but the code was never actually converted to a proxy."
    artifacts:
      - path: "AIM/src/aim/services/ci_marketing_analysis.py"
        issue: "Full standalone analyzer (class CiMarketingAnalyzer at line 797, ~1000 lines). Uses its own CiAnalysisResult dataclass (line 108), not UnifiedCiResult. Shares zero code with CIOrchestrator."
    missing:
      - "Convert CiMarketingAnalyzer.analyze() to delegate to CIOrchestrator.execute_ci_analysis(tier='quick')"
      - "Or: Delete CiMarketingAnalyzer and route all callers through CIOrchestrator"
      - "Use UnifiedCiResult instead of local CiAnalysisResult dataclass"

  - truth: "/api/competitors/analyze/stream → алиас на /api/seo/audit?tier=quick"
    status: failed
    reason: "The stream endpoint (competitors.py:304) is NOT an alias. It calls _run_quick_ci_analysis() which instantiates its own CIOrchestrator and calls orchestrator._run_quick_analysis(...) — a method that does not exist. The endpoint is broken at runtime. It does NOT call POST /api/seo/audit."
    artifacts:
      - path: "AIM/src/aim/api/competitors.py"
        issue: "Lines 304-350 define an independent SSE stream endpoint, not an alias. It calls _run_quick_ci_analysis() → orchestrator._run_quick_analysis() which doesn't exist."
    missing:
      - "Either make /analyze/stream an actual alias/redirect to /api/seo/audit?tier=quick with SSE wrapping"
      - "Or implement _run_quick_analysis on CIOrchestrator so the endpoint works"

  - truth: "Все 49 CI-интеграционных тестов проходят"
    status: failed
    reason: "23 tests pass, 26 fail. Failures span 9 test classes. Key failures: test_path2_stubs_removed (legacy methods still exist), test_orchestrator_tier_routing_has_quick_path (_run_quick_analysis missing), test_high_impact_keywords (tactic classification mismatch)."
    artifacts:
      - path: "AIM/tests/subagents/test_ci_pipeline_integration.py"
        issue: "26/49 tests fail. 23 pass."
    missing:
      - "Fix 26 failing tests by implementing missing functionality or updating test expectations"

  - truth: "Единый CI пайплайн без дублирования (H1)"
    status: failed
    reason: "CIOrchestrator has TWO parallel execution paths: (1) execute_ci_analysis() → _execute_single_phase() with EventBus delegation (new), and (2) execute_task() → _execute_phases() → _execute_single_agent() → _delegate_to_agent() which returns stub {'status': 'delegated'} (old). The old path still contains a TODO marker (line 993). Test test_path2_stubs_removed fails because legacy methods _delegate_to_agent, _execute_single_agent, _execute_phase_stub still exist."
    artifacts:
      - path: "AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py"
        issue: "Dual execution paths: execute_ci_analysis() (lines 215-382, EventBus) vs execute_task() → _delegate_to_agent() (lines 732-999, stub). Methods _delegate_to_agent (L970), _execute_single_agent (L942), _execute_phase_stub (L713) are legacy stubs with unreferenced TODO comments."
    missing:
      - "Remove legacy stub path: _delegate_to_agent, _execute_single_agent, _execute_phase_stub, and old execute_task() → _execute_phases() chain"
      - "Route all execution through execute_ci_analysis() → EventBus delegation only"
      - "Remove unreferenced TODO markers at lines 724 and 993"

  - truth: "EventBus-события публикуются для каждой CI-фазы (audit trail) — old execute_task() path"
    status: partial
    reason: "The new execute_ci_analysis() path publishes ci.execution.started, ci.task.dispatched, ci.agent.completed, ci.execution.completed. The old execute_task() → _delegate_to_agent() path publishes task.{agent_id} events but returns stub results — no ci.agent.completed events are published for the old path since agents are not invoked."
    artifacts:
      - path: "AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py"
        issue: "Old _delegate_to_agent (L970-999) publishes a task.{agent_id} Event but never triggers agent processing, so ci.agent.completed is never published for the old path."
    missing:
      - "Once the old path is removed, this resolves — the new path already publishes full audit trail"
deferred: []
human_verification:
  - test: "Call POST /api/competitors/analyze/stream with valid body"
    expected: "Should return SSE stream with progress events and final result"
    why_human: "Broken code path — calls nonexistent method. Needs implementation before testing."
  - test: "Run deep-tier CI analysis end-to-end via /api/seo/audit"
    expected: "All 16 phases execute via EventBus delegation, results collected, HTML/JSON reports generated"
    why_human: "Requires running server and external agents; EventBus timing-dependent"
  - test: "Visual inspection: old stub methods removed"
    expected: "No _delegate_to_agent, _execute_single_agent, _execute_phase_stub methods on CIOrchestrator"
    why_human: "Requires code review after remediation"
---

# Phase 21: CI Pipeline Unification Verification Report

**Phase Goal:** Унификация двух параллельных CI-пайплайнов (CiMarketingAnalyzer + CIOrchestrator) в единую архитектуру с tier-based routing, реальным EventBus-делегированием и унифицированными моделями данных.

**Verified:** 2026-05-31T18:15:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                 | Status     | Evidence                                                                   |
| --- | --------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------- |
| SC1 | Единый CIOrchestrator с `execute_ci_analysis(task_data, tier)`       | VERIFIED   | Method at ci_orchestrator.py:215, tiers dict at :51 with quick/deep/full   |
| SC2 | Quick tier → PipelineRunner + ComparisonMatrix (~10 сек)             | FAILED     | `_run_quick_analysis` missing. All tiers use same EventBus path.           |
| SC3 | Deep tier → EventBus delegation (не прямые вызовы)                   | PARTIAL    | New path uses EventBus. Old `execute_task()` → `_delegate_to_agent()` path returns stubs. |
| SC4 | CiMarketingAnalyzer → thin backward-compatible proxy                 | FAILED     | Full standalone class (1000+ lines, ci_marketing_analysis.py:797).         |
| SC5 | UnifiedCiResult — единая модель данных                               | VERIFIED   | Defined at ci/models.py:206 with tier, findings, phases_executed fields.   |
| SC6 | Единый эндпоинт `/api/seo/audit?tier=quick\|deep`                    | VERIFIED   | seo.py:113 POST /api/seo/audit, accepts tier param, calls execute_ci_analysis(). |
| SC7 | `/api/competitors/analyze/stream` → алиас                            | FAILED     | NOT an alias. Calls `_run_quick_analysis()` which doesn't exist. Broken.   |
| SC8 | Все 49 CI-интеграционных тестов проходят                             | FAILED     | 23 passed, 26 failed (53% pass rate).                                      |
| SC9 | EventBus-события для каждой CI-фазы (audit trail)                    | VERIFIED   | New path: ci.execution.started/dispatched/completed + ci.agent.completed. Old path: no audit trail. |

**Score:** 4/9 roadmap success criteria fully verified

### Plan 21-01 Must-Have Truths

| #   | Truth                                                      | Status   | Evidence |
| --- | ---------------------------------------------------------- | -------- | -------- |
| P1  | Each CI agent subscribes to EventBus via background poll   | VERIFIED | `_get_agent()` calls `agent.initialize()` (L188), starts `_listen_for_tasks()` poll loop |
| P2  | Orchestrator publishes task.request Messages               | VERIFIED | `_execute_single_phase()` publishes Message(to_agent=agent_id, message_type="task.request") at L452-471 |
| P3  | Agents publish ci.agent.completed Events                   | VERIFIED | `_bridged_report` at L169-183 publishes Event(event_type="ci.agent.completed") on shared EventBus |

**Plan 21-01 Score:** 3/3 verified (EventBus lifecycle infrastructure is correctly wired)

### Plan 21-02 Must-Have Truths

| #   | Truth                                                      | Status   | Evidence |
| --- | ---------------------------------------------------------- | -------- | -------- |
| P4  | EventBus delegation path NEVER falls back to direct call   | VERIFIED | `_execute_single_phase()` (L384-508) has NO `agent.execute_task()` call. Timeout returns error dict, not fallback. |
| P5  | Deep-tier CI completes using EventBus-delegated agents     | PARTIAL  | New `execute_ci_analysis()` path uses EventBus. Old `execute_task()` path (L732-774) uses stubs. |
| P6  | All 49 CI integration tests pass                           | FAILED   | 23/49 pass. 26 fail across 9 test classes. |

**Plan 21-02 Score:** 1/3 fully verified, 1 partial, 1 failed

### Requirements Coverage (H1, H6, L4 from audit)

| Requirement | Description                                           | Status     | Evidence |
| ----------- | ----------------------------------------------------- | ---------- | -------- |
| H1          | Eliminate pipeline duplication                        | FAILED     | Dual paths: `execute_ci_analysis()` (new) and `execute_task()` → `_delegate_to_agent()` (old stub path). Old path has TODO at L993. |
| H6          | Real EventBus delegation (not stub)                   | PARTIAL    | New path: real EventBus. Old path: `_delegate_to_agent()` returns `{"status": "delegated"}` stub. |
| L4          | Unified data models                                   | PARTIAL    | `UnifiedCiResult` exists in ci/models.py:206. But `CiMarketingAnalyzer` still uses local `CiAnalysisResult` (ci_marketing_analysis.py:108), not `UnifiedCiResult`. |

| Requirement | Description                                           | Status     | Evidence |
| ----------- | ----------------------------------------------------- | ---------- | -------- |
| D-05        | EventBus publish instead of direct calls              | VERIFIED   | `_execute_single_phase()` uses EventBus-only delegation. No `agent.execute_task()` call. |
| D-06        | CI agents subscribe to EventBus                       | VERIFIED   | `agent.initialize()` starts `_listen_for_tasks()` poll loop on shared EventBus. |
| D-07        | Results collected via EventBus events                 | VERIFIED   | `_bridged_report` publishes `ci.agent.completed` Event. `_on_agent_completed` handler collects. |

**Note:** D-05, D-06, D-07 are phase-specific requirement IDs from CONTEXT.md, not REQUIREMENTS.md. The phase instruction references H1, H6, L4 as the "audit" requirements.

### Dual Execution Path Architecture

The CIOrchestrator contains two parallel execution paths — the core unification objective (H1) remains unachieved:

**Path 1 — NEW (execute_ci_analysis):** Lines 215-382
```
execute_ci_analysis(task_data, tier)  →  _execute_single_phase()  →  EventBus publish task.request Message  →  agent._listen_for_tasks()  →  agent._execute_and_report()  →  agent.execute_task()  →  _bridged_report publishes ci.agent.completed  →  _on_agent_completed stores result
```
- Uses real EventBus delegation
- No fallback to direct call
- 60s timeout with structured error
- Publishes full audit trail (ci.execution.started, ci.task.dispatched, ci.agent.completed, ci.execution.completed)

**Path 2 — OLD (execute_task):** Lines 732-999
```
execute_task(task)  →  _execute_phases()  →  _execute_phase()  →  _execute_single_agent()  →  _delegate_to_agent()  →  returns {"status": "delegated", ...} STUB
```
- Contains TODO marker at line 993: `# TODO: Ждать результат от агента через Event Bus`
- Returns stub result immediately without actual analysis
- Still present in the file, violates "unified pipeline" goal

### Required Artifacts

| Artifact                                             | Expected                  | Status     | Details |
| ---------------------------------------------------- | ------------------------- | ---------- | ------- |
| `ci_orchestrator.py`                                 | Unified orchestrator      | PARTIAL    | New EventBus path correct. Old stub path still present. `_run_quick_analysis` missing. |
| `ci/models.py`                                       | UnifiedCiResult model     | VERIFIED   | Lines 206-265. Fields: tier, findings, phases_executed, wow, quality_score, etc. |
| `ci_marketing_analysis.py`                           | Thin backward-compat proxy | FAILED     | Full 1000+ line standalone analyzer. NOT a proxy. Uses local CiAnalysisResult, not UnifiedCiResult. |
| `api/seo.py`                                         | /api/seo/audit endpoint   | VERIFIED   | POST /api/seo/audit accepts tier param, calls execute_ci_analysis(). Lazy-initializes CIOrchestrator. |
| `api/competitors.py`                                 | /analyze + /analyze/stream | FAILED     | /analyze/stream calls nonexistent `_run_quick_analysis`. Not an alias. |
| `tests/test_ci_pipeline_integration.py`              | 49 tests passing          | FAILED     | 23 pass, 26 fail. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Real Data? | Status |
| -------- | ------------- | ------ | ---------- | ------ |
| `execute_ci_analysis()` findings | `phase_result` from `_execute_single_phase` | EventBus → agent poll loop → `execute_task` on sub-agent → result via `ci.agent.completed` Event | Yes (for agents that return real data) | FLOWING (new path) |
| `execute_task()` phase_results | `_delegate_to_agent()` return | `{"status": "delegated", "agent_id": ..., "task_id": ...}` | No — stub | DISCONNECTED (old path) |
| `CiMarketingAnalyzer.analyze()` | Local scraper + SWOT engine | `CompetitorPageScraper.scrape_all()` via httpx | Yes (but bypasses CIOrchestrator) | STATIC (independent pipeline, not unified) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `_execute_single_phase()` | CI agent | `task.request` Message on shared EventBus | WIRED | Agent poll loop picks up message, processes task |
| Agent `report_result()` | `_on_agent_completed()` | `ci.agent.completed` Event | WIRED | Bridge at L169-183 publishes Event with correlation_id |
| `_on_agent_completed` handler | `_completed_results` dict | Persistent subscriber at L85 | WIRED | Stores all completions for audit trail |
| `_get_agent()` | Agent lifecycle | `agent.initialize()` → `_listen_for_tasks()` | WIRED | L188 starts poll loop on shared EventBus |
| `/api/competitors/analyze/stream` | CIOrchestrator | `_run_quick_analysis()` method | **BROKEN** | Method does not exist |
| `CiMarketingAnalyzer` → `CIOrchestrator` | Proxy delegation | None | **NOT WIRED** | CiMarketingAnalyzer is standalone, not a proxy |
| Old `_delegate_to_agent()` → actual agent | EventBus | Publishes `task.{agent_id}` Event | **STUB** | Returns static dict; no agent processing |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| `_get_agent` is async | `grep "async def _get_agent" ci_orchestrator.py` | Match at line 87 | PASS |
| No fallback in _execute_single_phase | `grep "agent.execute_task(task)" ci_orchestrator.py` | No match | PASS |
| `asyncio.wait_for` used | `grep -c "asyncio.wait_for(completion_event" ci_orchestrator.py` | 1 match (L488) | PASS |
| `_on_agent_completed` persistent subscriber | `grep "self._on_agent_completed" ci_orchestrator.py` | Match at line 85 | PASS |
| `_bridged_report` publishes ci.agent.completed | `grep "ci.agent.completed" ci_orchestrator.py` | Match at lines 85, 175, 485, 507 | PASS |
| `_run_quick_analysis` exists | `grep "def _run_quick_analysis" ci_orchestrator.py` | **No match** | FAIL |
| All 49 tests pass | `pytest test_ci_pipeline_integration.py -v` | 23 passed, 26 failed | FAIL |
| Stub methods removed | `grep "_delegate_to_agent\|_execute_single_agent\|_execute_phase_stub" ci_orchestrator.py` | 5 matches (methods still exist) | FAIL |
| CiMarketingAnalyzer is a proxy | `grep "class CiMarketingAnalyzer" ci_marketing_analysis.py` | Full class at L797, 1000+ lines | FAIL |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `ci_orchestrator.py` | 724 | `# TODO: Implement real phase execution with CI agents` | BLOCKER | Unreferenced debt marker in `_execute_phase_stub` — no follow-up issue referenced |
| `ci_orchestrator.py` | 993 | `# TODO: Ждать результат от агента через Event Bus` | BLOCKER | Unreferenced debt marker in `_delegate_to_agent` — no follow-up issue referenced |
| `ci_orchestrator.py` | 399-406 | `"status": "stub"` return in `_execute_single_phase` | WARNING | Agent-not-found path returns stub status (defensive, but will produce low-quality results) |
| `ci_orchestrator.py` | 713-730 | `_execute_phase_stub()` method | WARNING | Entire method is a stub with TODO, never called by new path but still present |
| `ci_orchestrator.py` | 970-999 | `_delegate_to_agent()` returns hardcoded `{"status": "delegated"}` | BLOCKER | Returns stub without actual delegation — called by old `execute_task()` path |
| `api/competitors.py` | 226 | `orchestrator._run_quick_analysis(...)` | BLOCKER | Calls nonexistent method — endpoint will raise AttributeError at runtime |

### Gaps Summary

The Phase 21 plans (21-01 and 21-02) successfully implemented the EventBus delegation infrastructure — the core lifecycle model is correct: `_get_agent()` is async, agents share the orchestrator's EventBus, the poll loop starts after `agent.initialize()`, and `_bridged_report` publishes `ci.agent.completed` Events. The `_execute_single_phase()` method has no fallback to `agent.execute_task()` and uses pure EventBus delegation with a 60s timeout.

However, **five of nine roadmap success criteria fail**, and the phase goal of "unification" is not achieved:

1. **H1 pipeline duplication persists:** `execute_task()` → `_delegate_to_agent()` (lines 732-999) is a parallel execution path that returns stubs. Two methods (`_delegate_to_agent`, `_execute_single_agent`, `_execute_phase_stub`) are legacy stubs with unreferenced TODO markers.

2. **Quick tier not implemented:** `_run_quick_analysis` method does not exist. The API endpoint at `competitors.py:226` calls it and is broken. Quick tier in `execute_ci_analysis()` routes through the same EventBus path as deep tier — no PipelineRunner + ComparisonMatrix shortcut.

3. **CiMarketingAnalyzer is not a proxy:** It remains a full 1000+ line standalone class with its own scraping, SWOT, and analysis engines independent of CIOrchestrator. This was the H1 "pipeline duplication" problem — NOT resolved.

4. **`/api/competitors/analyze/stream` is not an alias:** It's an independent SSE endpoint that calls `orchestrator._run_quick_analysis()` — which doesn't exist. The endpoint is broken at runtime.

5. **26 of 49 tests fail:** Including `test_path2_stubs_removed`, `test_orchestrator_tier_routing_has_quick_path`, and `test_high_impact_keywords`.

6. **Two unreferenced TODO markers** in production code violate the "Complete Before Next" rule — no follow-up issues referenced.

The EventBus delegation infrastructure built by plans 21-01/21-02 is sound. The gaps are in the surrounding architecture: old code not removed, quick tier not implemented, CiMarketingAnalyzer not converted to proxy, stream endpoint not made into alias.

---

_Verified: 2026-05-31T18:15:00Z_
_Verifier: Claude (gsd-verifier)_
