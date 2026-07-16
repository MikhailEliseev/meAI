# SEO Magister Integration - Implementation Plan

**Date:** 2026-05-06T18:28:50Z  
**Based on:** SPEC.md v1.0  
**Approach:** Copy & Adapt Intelligence Magister

---

## 📋 Overview

**Goal:** Integrate SEO Magister with SEO System in 3 sprints (3.5 hours)

**Strategy:** Copy Intelligence Magister pattern, adapt for SEO

---

## 🎯 Sprints

### Sprint 1: SEO Magister Interface (1.5h)
**Goal:** SEO Magister with DI, progress, validation

**Tasks:**
1. Backup existing `seo_magister.py`
2. Copy `intelligence_magister.py` → `seo_magister.py`
3. Replace CI references with SEO
4. Update capabilities (analyze_keywords, optimize_content, etc.)
5. Update method names (_handle_keyword_analysis, etc.)
6. Create unit tests (copy from test_intelligence_magister.py)
7. Run tests, verify 10/10 passing

**Files:**
- `src/meai/agents/magisters/seo_magister.py` (~400 lines)
- `tests/test_seo_magister.py` (~350 lines)

**Branch:** `feat/seo-magister-interface`

---

### Sprint 2: SEO Orchestrator (1h)
**Goal:** Minimal SEO Orchestrator with KeywordResearchAgent

**Tasks:**
1. Create directory `AIM/src/aim/subagents/seo/orchestrator/`
2. Create `seo_orchestrator.py` (minimal, like CIOrchestrator stub)
3. Implement `execute_seo_analysis()` method
4. Integrate KeywordResearchAgent for keyword analysis
5. Add progress callback support
6. Create integration tests
7. Run tests, verify 7/7 passing

**Files:**
- `AIM/src/aim/subagents/seo/orchestrator/__init__.py` (new)
- `AIM/src/aim/subagents/seo/orchestrator/seo_orchestrator.py` (~150 lines)
- `tests/test_seo_integration.py` (~200 lines)

**Branch:** `feat/seo-orchestrator-integration`

---

### Sprint 3: Operator & E2E (1h)
**Goal:** Operator SEO detection + E2E tests

**Tasks:**
1. Add SEO keywords to Operator `_identify_required_capabilities()`
2. Create E2E tests (copy from test_e2e_intelligence.py)
3. Test Operator → SEO Magister → SEO Orchestrator flow
4. Run all tests, verify 23/23 passing
5. Update documentation

**Files:**
- `src/meai/agents/operator.py` (+20 lines)
- `tests/test_e2e_seo.py` (~180 lines)

**Branch:** `feat/operator-seo-enhancement`

---

## 📝 Detailed Steps

### Sprint 1: SEO Magister Interface

#### Step 1.1: Backup & Copy (15 min)
```bash
# Backup existing
cp src/meai/agents/magisters/seo_magister.py src/meai/agents/magisters/seo_magister.py.backup

# Copy Intelligence Magister
cp src/meai/agents/magisters/intelligence_magister.py src/meai/agents/magisters/seo_magister.py
```

#### Step 1.2: Replace References (30 min)
**Find & Replace:**
- `IntelligenceMagister` → `SEOMagister`
- `intelligence` → `seo`
- `Intelligence` → `SEO`
- `CI` → `SEO`
- `monitor_competitors` → `analyze_keywords`
- `research_market` → `optimize_content`
- `analyze_trends` → `audit_technical_seo`

**Update capabilities:**
```python
def get_capabilities(self) -> list[str]:
    return [
        "analyze_keywords",
        "optimize_content",
        "analyze_competitors",
        "track_rankings",
        "audit_technical_seo"
    ]
```

#### Step 1.3: Update Methods (30 min)
- `_handle_competitor_analysis` → `_handle_keyword_analysis`
- `_handle_market_research` → `_handle_content_optimization`
- `_store_ci_result` → `_store_seo_result`
- `_validate_ci_result` → `_validate_seo_result`

#### Step 1.4: Create Tests (15 min)
```bash
# Copy tests
cp tests/test_intelligence_magister.py tests/test_seo_magister.py

# Replace references (same as above)
# Run tests
pytest tests/test_seo_magister.py -v
```

---

### Sprint 2: SEO Orchestrator

#### Step 2.1: Create Structure (10 min)
```bash
mkdir -p AIM/src/aim/subagents/seo/orchestrator
touch AIM/src/aim/subagents/seo/__init__.py
touch AIM/src/aim/subagents/seo/orchestrator/__init__.py
```

#### Step 2.2: Create Orchestrator (30 min)
**File:** `seo_orchestrator.py`

```python
class SEOOrchestrator(Agent):
    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, database_url, vault_path)
        self.event_bus = event_bus
        
    async def execute_seo_analysis(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute SEO analysis"""
        
        analysis_type = task_data.get("analysis_type", "keyword")
        
        if analysis_type == "keyword":
            return await self._execute_keyword_analysis(task_data, progress_callback)
        else:
            # Stub for other types
            return {"task_id": task_data["task_id"], "results": {}}
            
    async def _execute_keyword_analysis(self, task_data, progress_callback):
        """Execute keyword analysis using KeywordResearchAgent"""
        
        # Create agent
        agent = KeywordResearchAgent(...)
        
        # Execute
        result = await agent.execute_task(...)
        
        return result
```

#### Step 2.3: Integration Tests (20 min)
```bash
# Copy tests
cp tests/test_ci_integration.py tests/test_seo_integration.py

# Adapt for SEO
# Run tests
pytest tests/test_seo_integration.py -v
```

---

### Sprint 3: Operator & E2E

#### Step 3.1: Operator Enhancement (20 min)
**File:** `src/meai/agents/operator.py`

**Add to `_identify_required_capabilities()`:**
```python
# SEO capabilities
seo_keywords = [
    "seo", "keyword", "keywords", "ключевые слова",
    "optimize", "оптимизация",
    "ranking", "позиции", "ранжирование",
    "content optimization", "оптимизация контента"
]

if any(kw in action_lower or kw in desc_lower for kw in seo_keywords):
    capabilities.append("analyze_keywords")
```

#### Step 3.2: E2E Tests (30 min)
```bash
# Copy tests
cp tests/test_e2e_intelligence.py tests/test_e2e_seo.py

# Adapt for SEO
# Run tests
pytest tests/test_e2e_seo.py -v
```

#### Step 3.3: Full Test Suite (10 min)
```bash
pytest tests/test_seo_magister.py tests/test_seo_integration.py tests/test_e2e_seo.py -v
```

---

## ✅ Acceptance Criteria

### Sprint 1
- ✅ SEO Magister file created
- ✅ DI pattern implemented
- ✅ Progress updates work
- ✅ Result validation works
- ✅ 10/10 unit tests passing

### Sprint 2
- ✅ SEO Orchestrator created
- ✅ execute_seo_analysis() works
- ✅ KeywordResearchAgent integrated
- ✅ Progress callbacks work
- ✅ 7/7 integration tests passing

### Sprint 3
- ✅ Operator detects SEO tasks
- ✅ E2E flow works
- ✅ 6/6 E2E tests passing
- ✅ Documentation updated

### Overall
- ✅ 23/23 tests passing
- ✅ All 3 branches merged to main
- ✅ Code pushed to GitHub

---

## 🎯 Success Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Execution Time | 3.5h | TBD |
| Tests Passing | 23/23 | TBD |
| Code Quality | Production-ready | TBD |
| Documentation | Complete | TBD |

---

## 🚀 Execution Order

1. **Sprint 1** → Branch: `feat/seo-magister-interface`
2. **Sprint 2** → Branch: `feat/seo-orchestrator-integration`
3. **Sprint 3** → Branch: `feat/operator-seo-enhancement`
4. **Merge all 3** → main
5. **Push** → GitHub

---

## 📚 Reference Files

**Copy from:**
- `src/meai/agents/magisters/intelligence_magister.py`
- `tests/test_intelligence_magister.py`
- `tests/test_ci_integration.py`
- `tests/test_e2e_intelligence.py`

**Adapt to:**
- `src/meai/agents/magisters/seo_magister.py`
- `tests/test_seo_magister.py`
- `tests/test_seo_integration.py`
- `tests/test_e2e_seo.py`

---

**Status:** Plan complete, ready for execution  
**Next:** Create Charter, then execute!
