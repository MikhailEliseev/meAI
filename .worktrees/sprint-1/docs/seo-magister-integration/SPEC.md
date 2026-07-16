# SEO Magister Integration - Technical Specification v1.0

**Date:** 2026-05-06T18:28:02Z  
**Status:** Draft  
**Approach:** Copy & Adapt Intelligence Magister

---

## 1. Overview

Integrate SEO Magister with SEO System using proven Intelligence Magister pattern.

**Goal:** SEO Magister operational with DI, progress updates, and result validation.

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        OPERATOR                              │
│  - Enhanced SEO detection                                    │
│  - Publishes magister_task messages                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Event Bus (P1 message)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SEO MAGISTER                                    │
│  - Task routing (analyze_keywords, optimize_content)        │
│  - Dependency Injection (SEO Orchestrator)                  │
│  - Progress updates                                          │
│  - Result validation                                         │
│  - Vault storage                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Direct method call (DI)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SEO ORCHESTRATOR                                │
│  - execute_seo_analysis() interface                         │
│  - Task type selection (keyword/content/technical)          │
│  - Progress callbacks                                        │
│  - Result aggregation                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Agent execution
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           SEO AGENTS                                         │
│  - KeywordResearchAgent (production ready)                  │
│  - ContentWriterAgent (exists)                              │
│  - (Future: TechnicalSEOAgent, LinkBuilderAgent)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 SEO Magister

**File:** `src/meai/agents/magisters/seo_magister.py`

**Responsibilities:**
- Receive tasks from Operator via Event Bus
- Route SEO tasks to appropriate orchestrator
- Provide progress updates
- Validate results
- Store results in vault

**Key Methods:**
```python
async def execute_task(task: Task) -> TaskResult:
    """Route task based on action"""
    
async def _handle_keyword_analysis(task: Task) -> TaskResult:
    """Handle analyze_keywords action"""
    
async def _handle_content_optimization(task: Task) -> TaskResult:
    """Handle optimize_content action"""
    
async def _store_seo_result(result: Dict) -> str:
    """Store result in vault"""
    
def _validate_seo_result(result: Dict) -> bool:
    """Validate result structure"""
```

**Capabilities:**
- `analyze_keywords` - Keyword research and analysis
- `optimize_content` - Content SEO optimization
- `analyze_competitors` - Competitor SEO analysis
- `track_rankings` - Position tracking
- `audit_technical_seo` - Technical SEO audit

---

### 3.2 SEO Orchestrator

**File:** `AIM/src/aim/subagents/seo/orchestrator/seo_orchestrator.py` (new)

**Responsibilities:**
- Execute SEO analysis tasks
- Coordinate SEO agents
- Provide progress callbacks
- Aggregate results

**Key Methods:**
```python
async def execute_seo_analysis(
    task_data: Dict[str, Any],
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """Execute SEO analysis
    
    Args:
        task_data: {
            "task_id": str,
            "analysis_type": "keyword" | "content" | "technical",
            "target": str (URL or keyword),
            "niche": str,
            "geo": str
        }
        progress_callback: async callback(step, status, message)
        
    Returns:
        {
            "task_id": str,
            "analysis_type": str,
            "results": Dict,
            "execution_time_seconds": int,
            "errors": List[str]
        }
    """
```

---

### 3.3 Operator Enhancement

**File:** `src/meai/agents/operator.py`

**Changes:**
- Add SEO keyword detection in `_identify_required_capabilities()`

**Keywords:**
```python
seo_keywords = [
    "seo", "keyword", "keywords", "ключевые слова",
    "optimize", "оптимизация",
    "ranking", "позиции", "ранжирование",
    "content optimization", "оптимизация контента",
    "technical seo", "технический seo"
]
```

---

## 4. Data Flow

### 4.1 Keyword Analysis Flow

```
1. User → Operator: "Analyze keywords for dental implants Moscow"
2. Operator → Event Bus: magister_task (action: analyze_keywords)
3. SEO Magister receives task
4. SEO Magister → SEO Orchestrator: execute_seo_analysis()
5. SEO Orchestrator → KeywordResearchAgent: analyze keywords
6. KeywordResearchAgent returns results
7. SEO Orchestrator aggregates results
8. SEO Magister validates results
9. SEO Magister stores in vault
10. SEO Magister → Operator: TaskResult
```

---

## 5. Implementation Details

### 5.1 Dependency Injection

**Pattern:** Constructor injection (same as Intelligence Magister)

```python
class SEOMagister(BaseMagister):
    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        database_url: str,
        vault_path: str,
        seo_orchestrator: Optional[SEOOrchestrator] = None
    ):
        self.seo_orchestrator = seo_orchestrator
```

**Registration:**
```python
# In main.py or initialization
seo_orchestrator = SEOOrchestrator(...)
seo_magister = SEOMagister(
    ...,
    seo_orchestrator=seo_orchestrator
)
```

---

### 5.2 Progress Updates

**Interface:** Same as Intelligence Magister

```python
async def progress_callback(step: int, status: str, message: str):
    """Progress callback
    
    Args:
        step: Current step number
        status: "in_progress" | "completed" | "failed"
        message: Human-readable message
    """
    await event_bus.publish(Event(
        type="magister_progress",
        data={
            "task_id": task_id,
            "step": step,
            "status": status,
            "message": message
        }
    ))
```

---

### 5.3 Result Validation

**Structure:**
```python
{
    "task_id": str,
    "analysis_type": str,  # "keyword" | "content" | "technical"
    "target": str,
    "results": {
        "keywords": List[Dict],  # For keyword analysis
        "content_score": int,    # For content optimization
        "technical_issues": List # For technical audit
    },
    "execution_time_seconds": int,
    "errors": List[str]
}
```

**Validation Rules:**
- task_id must be present
- analysis_type must be valid
- results must be dict
- execution_time_seconds >= 0

---

## 6. Testing Strategy

### 6.1 Unit Tests (10 tests)

**File:** `tests/test_seo_magister.py`

Tests:
1. `test_execute_task_routing_keyword_analysis` - Task routing works
2. `test_handle_keyword_analysis_success` - Keyword analysis succeeds
3. `test_store_seo_result` - Result storage works
4. `test_validate_seo_result_success` - Validation passes
5. `test_validate_seo_result_missing_task_id` - Validation fails
6. `test_progress_updates` - Progress updates sent
7. `test_orchestrator_not_registered` - Error handling
8. `test_timeout_handling` - Timeout works
9. `test_retry_logic` - Retry works
10. `test_generic_seo_fallback` - Fallback works

---

### 6.2 Integration Tests (7 tests)

**File:** `tests/test_seo_integration.py`

Tests:
1. `test_execute_seo_analysis_keyword` - Keyword analysis E2E
2. `test_execute_seo_analysis_content` - Content optimization E2E
3. `test_execute_seo_analysis_with_progress_callback` - Progress works
4. `test_seo_magister_to_orchestrator_integration` - Integration works
5. `test_seo_orchestrator_task_selection` - Task routing works
6. `test_seo_orchestrator_error_handling` - Errors handled
7. `test_seo_orchestrator_execution_time_tracking` - Time tracked

---

### 6.3 E2E Tests (6 tests)

**File:** `tests/test_e2e_seo.py`

Tests:
1. `test_operator_seo_detection_enhanced` - Operator detects SEO
2. `test_e2e_seo_analysis_flow` - Full flow works
3. `test_performance_keyword_analysis` - Performance OK
4. `test_seo_result_structure_validation` - Structure valid
5. `test_progress_updates_during_execution` - Progress works
6. `test_vault_storage` - Results stored

---

## 7. Success Criteria

### Functional
- ✅ SEO Magister receives tasks from Operator
- ✅ SEO Magister routes to orchestrator
- ✅ SEO Orchestrator executes analysis
- ✅ Results validated and stored
- ✅ Progress updates work

### Non-Functional
- ✅ Timeout handling (15 min default)
- ✅ Retry logic (3 attempts)
- ✅ Partial results on failure
- ✅ DI pattern (no direct imports)

### Quality
- ✅ 23 tests passing (10 + 7 + 6)
- ✅ Test coverage > 80%
- ✅ Documentation complete

---

## 8. Timeline

**Sprint 1:** SEO Magister Interface (1.5h)
**Sprint 2:** SEO Orchestrator (1h)
**Sprint 3:** Operator & E2E (1h)

**Total Execution:** 3.5 hours

---

## 9. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing SEO Magister conflicts | Medium | Backup old file, clean rewrite |
| KeywordResearchAgent interface mismatch | Low | Check interface, adapt if needed |
| Tests fail after copy | Medium | Adapt tests incrementally |
| Time overrun | Low | Pattern proven, low risk |

---

## 10. Dependencies

**Required:**
- Intelligence Magister (reference)
- KeywordResearchAgent (exists)
- Event Bus (exists)
- Operator (exists)

**Optional:**
- ContentWriterAgent (for content optimization)
- TechnicalSEOAgent (future)

---

**Status:** Spec complete, ready for review  
**Next:** Spec Review (dual-model if critical governance)
