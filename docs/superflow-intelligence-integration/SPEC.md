# Intelligence Magister Integration - Technical Specification

**Version:** 1.0  
**Date:** 2026-05-06  
**Status:** Draft  
**Governance:** Critical  
**Git Workflow:** Stacked PRs

---

## 1. Executive Summary

Integrate Intelligence Magister with CI System to enable the first fully operational Magister in the AIM agency architecture. This creates a working proof-of-concept for the Operator → Magister → Subagents pattern.

**Approach:** Hybrid (Approach #3)
- Intelligence Magister remains generic (Framework layer)
- CIOrchestrator acts as adapter (Application layer)
- Communication via Event Bus (loose coupling)

**Timeline:** 3 sprints, 3.5 hours total

---

## 2. Architecture

### 2.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        OPERATOR                              │
│  - Receives task from user                                   │
│  - Identifies "monitor_competitors" capability               │
│  - Creates subtask for Intelligence Magister                 │
│  - Publishes magister_task message to Event Bus             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Event Bus (P1 message)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              INTELLIGENCE MAGISTER (NEW)                      │
│  - Polls Event Bus for magister_task messages                │
│  - Routes task based on action:                              │
│    * monitor_competitors → CI analysis                       │
│    * research_market → Market research                       │
│    * analyze_trends → Trend analysis                         │
│  - Delegates to appropriate orchestrator                     │
│  - Aggregates results                                        │
│  - Stores in Obsidian vault                                  │
│  - Publishes task_result message to Event Bus               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Direct method call
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CI ORCHESTRATOR (REFACTORED)                    │
│  - Receives task from Intelligence Magister                  │
│  - Selects tier (quick/deep/full)                           │
│  - Executes phases sequentially                              │
│  - Phase 5: parallel execution (7 agents)                    │
│  - Collects and aggregates results                           │
│  - Returns structured result                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ asyncio.gather() for Phase 5
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           CI SUBAGENTS (21 specialized agents)               │
│  - ci_scout, ci_auditor, ci_reputation                      │
│  - ci_finance, ci_tech, ci_content, ci_pricing, etc.        │
│  - ci_factchecker, ci_strategist, ci_prioritizer           │
│  - ci_offer_generator, business_report                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

#### Intelligence Magister (Framework Layer)
**Location:** `src/meai/agents/magisters/intelligence_magister.py`

**Responsibilities:**
- Poll Event Bus for tasks
- Route tasks to appropriate handlers
- Delegate to orchestrators (CI, Market Research, etc.)
- Aggregate results
- Store results in Obsidian vault
- Report back to Operator via Event Bus

**Does NOT:**
- Know about specific CI agents
- Implement CI logic
- Depend on AIM application code

#### CIOrchestrator (Application Layer)
**Location:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`

**Responsibilities:**
- Coordinate 21 CI subagents
- Execute phases (1-16) based on tier
- Handle parallel execution (Phase 5)
- Aggregate CI results
- Generate business reports

**Does NOT:**
- Know about Event Bus
- Know about Operator
- Communicate directly with other Magisters

---

## 3. Data Structures

### 3.1 Task Message (Operator → Intelligence Magister)

```python
{
    "message_id": "msg-uuid",
    "type": "magister_task",
    "priority": 1,  # P1 = High
    "agent_id": "intelligence-magister-1",
    "payload": {
        "subtask_id": "subtask-uuid",
        "parent_task_id": "task-uuid",
        "action": "monitor_competitors",  # or research_market, analyze_trends
        "description": "Analyze 6 competitors in dental implants niche",
        "data": {
            "niche": "dental implants",
            "geo": "Moscow",
            "target_audience": "patients 35-55",
            "price_segment": "mid",
            "depth": "deep",  # quick/deep/full
            "competitors": [
                "https://example1.com",
                "https://example2.com",
                ...
            ]
        },
        "deadline": "2026-05-06T18:00:00Z"
    },
    "created_at": "2026-05-06T14:00:00Z"
}
```

### 3.2 Result Message (Intelligence Magister → Operator)

```python
{
    "message_id": "msg-uuid",
    "type": "task_result",
    "priority": 1,
    "agent_id": "operator-1",
    "payload": {
        "subtask_id": "subtask-uuid",
        "parent_task_id": "task-uuid",
        "status": "completed",  # or failed
        "result": {
            "tier": "deep",
            "phases_executed": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "execution_time_seconds": 2700,  # 45 minutes
            "competitors_analyzed": 6,
            "findings": {
                "market_overview": {...},
                "competitor_profiles": [...],
                "technology_stack": {...},
                "content_strategy": {...},
                "pricing_analysis": {...},
                "strategic_recommendations": [...]
            },
            "reports": {
                "pdf_path": "/path/to/report.pdf",
                "html_path": "/path/to/report.html"
            }
        },
        "error": null
    },
    "created_at": "2026-05-06T14:45:00Z"
}
```

### 3.3 CI Task (Intelligence Magister → CIOrchestrator)

```python
@dataclass
class CITask:
    """Task for CI analysis"""
    task_id: str
    niche: str
    geo: str
    target_audience: str
    price_segment: str
    tier: str  # quick/deep/full
    competitors: list[str]
    deadline: datetime | None
```

### 3.4 CI Result (CIOrchestrator → Intelligence Magister)

```python
@dataclass
class CIResult:
    """Result from CI analysis"""
    task_id: str
    tier: str
    phases_executed: list[int]
    execution_time_seconds: int
    competitors_analyzed: int
    findings: dict[str, Any]
    reports: dict[str, str]  # pdf_path, html_path
    errors: list[str]
```

---

## 4. Implementation Details

### 4.1 Intelligence Magister Changes

**File:** `src/meai/agents/magisters/intelligence_magister.py`

**Constructor Changes:**

```python
def __init__(
    self,
    agent_id: str = "intelligence-magister-1",
    event_bus: EventBus = None,
    vault_path: Path = None,
    database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    orchestrators: dict[str, Any] = None,
):
    """Initialize Intelligence Magister with orchestrators
    
    Args:
        orchestrators: Dict of orchestrator name -> orchestrator instance
                      e.g., {"ci": CIOrchestrator(...)}
    """
    super().__init__(...)
    self.orchestrators = orchestrators or {}
```

**New Methods:**

```python
async def execute_task(self, task: Task) -> TaskResult:
    """Execute Intelligence-specific task
    
    Routes to appropriate handler based on action:
    - monitor_competitors → _handle_competitor_analysis()
    - research_market → _handle_market_research()
    - analyze_trends → _handle_trend_analysis()
    """
    action = task.data.get("action", "")
    
    if action == "monitor_competitors":
        return await self._handle_competitor_analysis(task)
    elif action == "research_market":
        return await self._handle_market_research(task)
    elif action == "analyze_trends":
        return await self._handle_trend_analysis(task)
    else:
        return await self._handle_generic_intelligence(task)

async def _handle_competitor_analysis(self, task: Task) -> TaskResult:
    """Handle competitor analysis via CI system"""
    # 1. Get orchestrator via dependency injection
    orchestrator = self.orchestrators.get("ci")
    if not orchestrator:
        raise ValueError("CI orchestrator not registered")
    
    # 2. Create CI task
    ci_task = CITask(
        task_id=task.task_id,
        niche=task.data["niche"],
        geo=task.data["geo"],
        target_audience=task.data["target_audience"],
        price_segment=task.data["price_segment"],
        tier=task.data.get("depth", "deep"),
        competitors=task.data.get("competitors", []),
        deadline=task.deadline
    )
    
    # 3. Execute via orchestrator with progress updates
    ci_result = await orchestrator.execute_ci_analysis(
        ci_task,
        progress_callback=self._publish_progress
    )
    
    # 4. Validate result
    validated_result = self._validate_ci_result(ci_result)
    
    # 4. Store in vault
    await self._store_ci_result(ci_result)
    
    # 5. Return result
    return TaskResult(
        task_id=task.task_id,
        agent_id=self.agent_id,
        status="completed",
        result=ci_result.to_dict(),
        completed_at=datetime.now(timezone.utc)
    )

async def _publish_progress(self, phase: int, status: str, message: str) -> None:
    """Publish progress update via Event Bus"""
    await self.event_bus.publish(Message(
        type="task_progress",
        priority=2,  # P2 = Normal
        agent_id="operator-1",
        payload={
            "task_id": self.current_task_id,
            "phase": phase,
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ))

def _validate_ci_result(self, result: CIResult) -> CIResult:
    """Validate CI result using Pydantic schema"""
    from pydantic import ValidationError
    
    try:
        # Validate structure
        if not result.task_id:
            raise ValueError("Missing task_id")
        if not result.findings:
            raise ValueError("Missing findings")
        if result.competitors_analyzed < 1:
            raise ValueError("No competitors analyzed")
        
        # Validate reports exist
        if result.reports:
            for report_type, path in result.reports.items():
                if path and not Path(path).exists():
                    logger.warning(f"Report file not found: {path}")
        
        return result
    except (ValueError, ValidationError) as e:
        logger.error(f"CI result validation failed: {e}")
        raise

async def _store_ci_result(self, result: CIResult) -> None:
    """Store CI result in Obsidian vault"""
    # Create markdown file in vault
    result_file = self.vault_path / "wiki" / "sources" / f"ci-{result.task_id}.md"
    
    content = f"""---
type: ci-analysis
task_id: {result.task_id}
tier: {result.tier}
date: {datetime.now(timezone.utc).isoformat()}
status: processed
---

# CI Analysis: {result.task_id}

## Summary
- Tier: {result.tier}
- Phases: {result.phases_executed}
- Competitors: {result.competitors_analyzed}
- Time: {result.execution_time_seconds}s

## Findings
{json.dumps(result.findings, indent=2)}

## Reports
- PDF: {result.reports.get('pdf_path')}
- HTML: {result.reports.get('html_path')}
"""
    
    result_file.parent.mkdir(parents=True, exist_ok=True)
    result_file.write_text(content)
```

### 4.2 CIOrchestrator Changes

**File:** `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py`

**New Interface:**

```python
async def execute_ci_analysis(self, task: CITask) -> CIResult:
    """Execute CI analysis for given task
    
    This is the main entry point called by Intelligence Magister.
    """
    start_time = datetime.now(timezone.utc)
    
    # Select phases based on tier
    phases = self._select_phases(task.tier)
    
    # Execute phases
    results = []
    for phase_num in phases:
        phase_result = await self._execute_phase(phase_num, task)
        results.append(phase_result)
    
    # Aggregate results
    findings = self._aggregate_findings(results)
    
    # Generate reports
    reports = await self._generate_reports(findings, task)
    
    # Calculate execution time
    execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    return CIResult(
        task_id=task.task_id,
        tier=task.tier,
        phases_executed=phases,
        execution_time_seconds=int(execution_time),
        competitors_analyzed=len(task.competitors),
        findings=findings,
        reports=reports,
        errors=[]
    )

def _select_phases(self, tier: str) -> list[int]:
    """Select phases based on tier"""
    if tier == "quick":
        return [1, 2, 3, 4]  # 15 min
    elif tier == "deep":
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]  # 45 min
    elif tier == "full":
        return list(range(1, 17))  # 90 min
    else:
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]  # default to deep
```

### 4.3 Operator Changes

**File:** `src/meai/agents/operator.py`

**Enhanced CI Detection:**

```python
def _identify_required_capabilities(self, task: Task) -> list[str]:
    """Identify required capabilities from task
    
    Enhanced CI detection for competitor analysis tasks.
    """
    capabilities = []
    
    # Existing logic...
    
    # Enhanced CI detection
    ci_keywords = [
        "competitor", "конкурент",
        "market analysis", "анализ рынка",
        "competitive intelligence", "конкурентная разведка",
        "benchmark", "бенчмарк"
    ]
    
    description_lower = task.description.lower()
    
    if any(keyword in description_lower for keyword in ci_keywords):
        capabilities.append("monitor_competitors")
    
    # Check for explicit CI request in data
    if task.data.get("analysis_type") == "competitive_intelligence":
        capabilities.append("monitor_competitors")
    
    return capabilities
```

---

## 5. Error Handling

### 5.1 Timeout Handling

**Intelligence Magister:**
```python
async def _handle_competitor_analysis(self, task: Task) -> TaskResult:
    try:
        # Set timeout based on tier
        tier = task.data.get("depth", "deep")
        timeout_seconds = {
            "quick": 900,   # 15 min
            "deep": 2700,   # 45 min
            "full": 5400    # 90 min
        }.get(tier, 2700)
        
        # Execute with timeout
        ci_result = await asyncio.wait_for(
            orchestrator.execute_ci_analysis(ci_task),
            timeout=timeout_seconds
        )
        
        return self._create_success_result(ci_result)
        
    except asyncio.TimeoutError:
        return self._create_timeout_result(task, timeout_seconds)
    except Exception as e:
        return self._create_error_result(task, e)
```

### 5.2 Partial Results

**CIOrchestrator:**
```python
async def _execute_phase(self, phase_num: int, task: CITask) -> dict:
    """Execute phase with error handling"""
    try:
        if phase_num == 5:
            # Parallel execution with partial results
            return await self._execute_parallel_agents_safe(task)
        else:
            return await self._execute_sequential_phase(phase_num, task)
    except Exception as e:
        logger.error(f"Phase {phase_num} failed: {e}")
        return {
            "phase": phase_num,
            "status": "failed",
            "error": str(e),
            "partial_results": {}
        }

async def _execute_parallel_agents_safe(self, task: CITask) -> dict:
    """Execute parallel agents with individual error handling"""
    agents = [
        self._run_ci_finance,
        self._run_ci_tech,
        self._run_ci_content,
        self._run_ci_pricing,
        self._run_ci_ecosystem,
        self._run_ci_vacancies,
        self._run_ci_site_crawler
    ]
    
    # Run with return_exceptions=True to collect partial results
    results = await asyncio.gather(
        *[agent(task) for agent in agents],
        return_exceptions=True
    )
    
    # Separate successful results from errors
    successful = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append(f"Agent {i} failed: {result}")
        else:
            successful.append(result)
    
    return {
        "phase": 5,
        "status": "partial" if errors else "completed",
        "results": successful,
        "errors": errors
    }
```

### 5.3 Retry Logic

**Intelligence Magister:**
```python
async def _handle_competitor_analysis_with_retry(
    self, task: Task, max_retries: int = 2
) -> TaskResult:
    """Handle competitor analysis with retry logic"""
    for attempt in range(max_retries + 1):
        try:
            return await self._handle_competitor_analysis(task)
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"All {max_retries + 1} attempts failed: {e}")
                return self._create_error_result(task, e)
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Intelligence Magister:**
- Test task routing (monitor_competitors → CI handler)
- Test result storage in vault
- Test error handling (timeout, exceptions)
- Test retry logic

**CIOrchestrator:**
- Test tier selection (quick/deep/full)
- Test phase execution
- Test parallel agent execution
- Test result aggregation

### 6.2 Integration Tests

**End-to-End Flow:**
```python
async def test_operator_to_ci_flow():
    """Test full flow: Operator → Intelligence → CI → Report"""
    # 1. Create task
    task = Task(
        task_id="test-task-1",
        source="user",
        goal="Analyze competitors",
        description="Analyze 3 competitors in dental implants",
        data={
            "niche": "dental implants",
            "geo": "Moscow",
            "depth": "quick",
            "competitors": [
                "https://example1.com",
                "https://example2.com",
                "https://example3.com"
            ]
        }
    )
    
    # 2. Operator delegates to Intelligence Magister
    operator = Operator(...)
    await operator.receive_task(task)
    
    # 3. Wait for result
    result = await operator.wait_for_result(task.task_id, timeout=1000)
    
    # 4. Verify result
    assert result.status == "completed"
    assert "findings" in result.result
    assert len(result.result["findings"]["competitor_profiles"]) == 3
```

### 6.3 Performance Tests

**Tier Performance:**
- Quick tier: < 15 minutes
- Deep tier: < 45 minutes
- Full tier: < 90 minutes

**Parallel Execution:**
- Phase 5: 7 agents complete in < 10 minutes (not 70 minutes)

---

## 7. Success Criteria

### 7.1 Functional Requirements

- ✅ Intelligence Magister receives tasks from Operator via Event Bus
- ✅ Intelligence Magister routes "monitor_competitors" to CI
- ✅ CIOrchestrator executes phases based on tier
- ✅ Phase 5 executes 7 agents in parallel
- ✅ Results are aggregated and returned
- ✅ Results are stored in Obsidian vault
- ✅ Operator receives final report

### 7.2 Non-Functional Requirements

- ✅ Timeout handling for long-running tasks
- ✅ Partial results on agent failures
- ✅ Retry logic for transient errors
- ✅ Performance within tier limits
- ✅ No Framework → Application dependencies
- ✅ Event Bus as only communication channel

### 7.3 Quality Requirements

- ✅ Unit test coverage > 80%
- ✅ Integration tests pass
- ✅ Performance tests pass
- ✅ Documentation complete
- ✅ Code review approved (Critical mode)

---

## 8. Risks & Mitigations

### 8.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Event Bus message loss | HIGH | LOW | Persistent queue in SQLite |
| CI timeout on slow sites | MEDIUM | MEDIUM | Configurable timeouts per tier |
| Parallel agent failures | MEDIUM | MEDIUM | Partial result collection |
| Memory issues (21 agents) | MEDIUM | LOW | Sequential phases, parallel only Phase 5 |
| Framework → Application coupling | HIGH | MEDIUM | Strict interface, no direct imports |

### 8.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| First Magister integration | HIGH | MEDIUM | Critical mode review, thorough testing |
| Pattern not scalable | HIGH | LOW | Generic design, proven with CI first |
| Performance not acceptable | MEDIUM | LOW | Performance tests, tier system |

---

## 9. Dependencies

### 9.1 Internal Dependencies

- ✅ Operator (already implemented)
- ✅ Event Bus (already implemented)
- ✅ BaseMagister (already implemented)
- ✅ CI Subagents (already implemented)
- ✅ CIOrchestrator (needs refactoring)

### 9.2 External Dependencies

- Python 3.11+
- SQLite (Event Bus storage)
- Obsidian (vault storage)
- aiohttp (CI agents)
- BeautifulSoup4 (CI agents)

**No new dependencies required.**

---

## 10. Timeline

### Sprint 1: Intelligence Magister Interface (1.8h)
- Implement execute_task() routing
- Implement _handle_competitor_analysis() with DI
- Implement _publish_progress() for progress updates
- Implement _validate_ci_result() for validation
- Implement result storage
- Unit tests

### Sprint 2: CIOrchestrator Integration (1.1h)
- Add execute_ci_analysis() interface
- Add progress_callback support
- Refactor tier selection
- Test with Intelligence Magister
- Error handling

### Sprint 3: Operator & E2E (1.1h)
- Enhance CI detection
- End-to-end test with progress tracking
- Performance tests
- Documentation

**Total:** 4 hours (was 3.5h, +30min for critical fixes)

---

## 11. Open Questions

1. **Q:** Should Intelligence Magister cache CI results?
   **A:** Yes, store in vault with TTL metadata (24h for quick, 7d for deep/full)

2. **Q:** How to handle stale competitor data?
   **A:** CIOrchestrator already has stale detection logic - preserve it

3. **Q:** Should we support streaming results?
   **A:** Not in MVP, but design for it (phase-by-phase updates)

4. **Q:** How to handle very large reports (>10MB)?
   **A:** Store file path in result, not content

---

## 12. Future Enhancements

**Phase 2 (Post-MVP):**
- Streaming results (phase-by-phase updates)
- Result caching with TTL
- CI result comparison (track changes over time)
- Automated scheduling (weekly competitor checks)
- Multi-tier parallel execution (quick + deep simultaneously)

**Phase 3 (Advanced):**
- Real-time competitor monitoring
- Alert system for significant changes
- AI-generated strategic insights
- Integration with other Magisters (SEO, Content)

---

**Status:** Ready for review  
**Next Step:** Create Implementation Plan (PLAN.md)  
**Approval Required:** User + Spec Reviewer (Critical mode)
