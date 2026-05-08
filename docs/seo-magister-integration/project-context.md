# SEO Magister Integration - Project Context

**Date:** 2026-05-06  
**Project:** SEO Magister Integration  
**Goal:** Integrate SEO Magister with SEO System using proven Intelligence Magister pattern

---

## 🎯 Project Overview

Integrate SEO Magister with SEO orchestration system, following the same architecture pattern that was successfully implemented for Intelligence Magister.

---

## 📊 Current State

### What Exists ✅
1. **Intelligence Magister** - fully operational (reference implementation)
   - DI pattern with orchestrators
   - Progress updates via Event Bus
   - Result validation
   - Vault storage
   - 25 tests passing

2. **SEO Magister** - basic implementation exists
   - File: `src/meai/agents/magisters/seo_magister.py`
   - Has basic capabilities (analyze_keywords, optimize_content, etc.)
   - Uses BaseMagister
   - **Missing:** Orchestrator integration, DI pattern, progress updates

3. **Operator** - enhanced CI detection
   - Needs SEO detection enhancement

### What's Missing ❌
1. SEO Orchestrator integration (like CIOrchestrator)
2. DI pattern for SEO orchestrator
3. Progress updates for SEO tasks
4. Result validation for SEO
5. Operator SEO detection
6. Tests for SEO integration

---

## 🏗️ Target Architecture

```
Operator (SEO detection)
  ↓ Event Bus (P1 message)
SEO Magister (DI, progress, validation)
  ↓ Direct method call (DI)
SEO Orchestrator (keyword research, content optimization)
  ↓ Phase execution
SEO Agents (keyword analyzer, content optimizer, technical auditor)
```

**Pattern:** Same as Intelligence Magister
- Dependency Injection for orchestrators
- Progress callbacks
- Result validation
- Vault storage

---

## 📋 Requirements

### Functional
1. SEO Magister receives tasks from Operator via Event Bus
2. SEO Magister routes SEO tasks to orchestrator
3. SEO Orchestrator executes phases based on task type
4. Results aggregated and returned
5. Results stored in Obsidian vault
6. Operator receives final report

### Non-Functional
1. Timeout handling for long-running tasks
2. Partial results on failures
3. Retry logic for transient errors
4. No Framework → Application dependencies (DI)
5. Event Bus as communication channel

### Quality
1. Unit test coverage > 80%
2. Integration tests pass
3. E2E tests pass
4. Documentation complete

---

## 🎓 Lessons from Intelligence Magister

**What worked well:**
1. ✅ DI pattern - clean separation of concerns
2. ✅ Progress callbacks - user visibility
3. ✅ Result validation - data quality
4. ✅ Stacked PRs - parallel development
5. ✅ Critical governance - dual-model review caught issues

**What to replicate:**
1. Same DI pattern for orchestrator injection
2. Same progress callback interface
3. Same result validation approach
4. Same test structure (unit + integration + E2E)
5. Same documentation approach

---

## 📦 Deliverables

### Sprint 1: SEO Magister Interface
- Update SEO Magister with DI pattern
- Add orchestrator injection
- Add progress updates
- Add result validation
- Unit tests (10+)

### Sprint 2: SEO Orchestrator Integration
- Create/update SEO Orchestrator
- Implement execute_seo_analysis() method
- Add progress callbacks
- Integration tests (7+)

### Sprint 3: Operator & E2E
- Enhance Operator SEO detection
- E2E tests
- Documentation

---

## ⏱️ Time Estimate

- **Phase 1 (Discovery):** 2-3 hours
  - Context ✅
  - Research (check existing SEO agents)
  - Brainstorm approaches
  - Spec + Review
  - Plan + Review
  - Charter

- **Phase 2 (Execution):** 4-6 hours
  - Sprint 1: SEO Magister Interface (2h)
  - Sprint 2: SEO Orchestrator Integration (1.5h)
  - Sprint 3: Operator & E2E (1h)

- **Phase 3 (Merge):** 0.5 hours
  - Merge 3 branches
  - Run full tests
  - Push to GitHub

**Total:** 6.5-9.5 hours

---

## 🎯 Success Criteria

1. ✅ SEO Magister uses DI pattern
2. ✅ SEO Orchestrator integrated
3. ✅ Progress updates work
4. ✅ Results validated
5. ✅ All tests passing (20+)
6. ✅ Operator detects SEO tasks
7. ✅ E2E flow works

---

## 📚 Reference Implementation

**Intelligence Magister:**
- File: `src/meai/agents/magisters/intelligence_magister.py`
- Tests: `tests/test_intelligence_magister.py`
- Integration: `tests/test_ci_integration.py`
- E2E: `tests/test_e2e_intelligence.py`

**Use as template for SEO Magister implementation.**

---

**Status:** Phase 1 - Discovery  
**Next:** Research existing SEO agents and orchestrator
