# Intelligence Magister Enhancement - Real CI Agents Integration

**Date:** 2026-05-06  
**Goal:** Replace stub implementation with real CI agents  
**Priority:** HIGH (Production readiness)

---

## 🎯 Current State

### What Works ✅
- Intelligence Magister interface (DI, progress, validation)
- CIOrchestrator integration interface
- Operator CI detection
- Event Bus communication
- All tests passing (18/18)

### What's Missing ⚠️
- **Stub implementation:** `_execute_phase_stub()` just sleeps 0.1s
- Real CI agents exist but not connected
- No actual competitor analysis happening

---

## 📊 Available CI Agents (19 agents)

**Phase 1-4 (Quick):**
1. ✅ `ci_scout.py` - Initial competitor discovery
2. ✅ `ci_auditor.py` - Technical audit
3. ✅ `ci_auditor.py` - (Phase 3 reuse)
4. ✅ `ci_reputation.py` - Reputation analysis

**Phase 5-9 (Deep):**
5. ✅ 7 parallel agents:
   - `ci_finance.py` - Financial analysis
   - `ci_vacancies.py` - Job postings analysis
   - `ci_tech.py` / `ci_tech_real.py` - Tech stack
   - `ci_site_crawler.py` - Site structure
   - `ci_content.py` - Content analysis
   - `ci_pricing.py` - Pricing analysis
   - `ci_ecosystem.py` - Ecosystem mapping
6. ✅ `ci_factchecker.py` - Fact verification
7. ✅ `ci_strategist.py` - Strategic analysis
8. ✅ `ci_strategist.py` - (Phase 8 reuse)
9. ✅ `ci_prioritizer.py` - Priority ranking

**Phase 10-16 (Full):**
10. ⚠️ `tw-marketing-strategy` - (TW = TargetWorks, not implemented yet)
11. ⚠️ `tw-competitor-scout`
12. ⚠️ `tw-creative-collector`
13. ⚠️ `tw-creative-analyzer`
14. ⚠️ `tw-pattern-finder`
15. ⚠️ `tw-traffic-analyzer`
16. ✅ `ci_offer_generator.py` - Offer generation

**Additional:**
- ✅ `ci_deep_analyzer.py` - Deep analysis
- ✅ `ci_marketing_strategy.py` - Marketing strategy
- ✅ `ci_qa_validator.py` - Quality validation
- ✅ `ci_url_validator.py` - URL validation
- ✅ `business_report.py` - Report generation

---

## 🔧 Implementation Plan

### Sprint 1: Connect Real Agents (Phases 1-9)
**Goal:** Replace stub with real agent execution for Quick + Deep tiers

**Tasks:**
1. Create agent factory/registry
2. Implement `_execute_phase()` with real agents
3. Handle Phase 5 parallel execution (7 agents)
4. Add error handling for agent failures
5. Update tests to use real agents

**Files:**
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (~150 lines)
- `tests/test_ci_real_agents.py` (new, ~200 lines)

**Duration:** 2-3 hours

---

### Sprint 2: Report Generation & Storage
**Goal:** Generate PDF/HTML reports and store in vault

**Tasks:**
1. Integrate `business_report.py`
2. Generate PDF reports
3. Generate HTML reports
4. Store reports in Obsidian vault
5. Update Intelligence Magister to handle report paths

**Files:**
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (+50 lines)
- `tests/test_ci_reports.py` (new, ~100 lines)

**Duration:** 1-2 hours

---

### Sprint 3: Quality & Validation
**Goal:** Add validation and quality checks

**Tasks:**
1. Integrate `ci_qa_validator.py`
2. Integrate `ci_url_validator.py`
3. Add result quality scoring
4. Add confidence levels
5. E2E test with real competitors

**Files:**
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (+80 lines)
- `tests/test_ci_e2e_real.py` (new, ~150 lines)

**Duration:** 1-2 hours

---

## 📈 Success Criteria

### Functional
- ✅ Quick tier (Phases 1-4) executes real agents
- ✅ Deep tier (Phases 1-9) executes real agents
- ✅ Phase 5 runs 7 agents in parallel
- ✅ Reports generated (PDF + HTML)
- ✅ Results stored in vault
- ✅ Quality validation passes

### Performance
- ✅ Quick tier: < 15 minutes (real execution)
- ✅ Deep tier: < 45 minutes (real execution)
- ✅ Phase 5 parallel: < 10 minutes (not 70)

### Quality
- ✅ All tests passing
- ✅ Real competitor analysis works
- ✅ Reports are readable and useful
- ✅ No data loss or corruption

---

## 🚀 Execution Strategy

**Approach:** Incremental replacement
1. Keep stub as fallback
2. Add real agent execution alongside
3. Test with real competitors
4. Remove stub when confident

**Testing:**
- Unit tests for each agent integration
- Integration tests for phase execution
- E2E test with real competitor URLs
- Performance tests with timing

**Rollback:**
- Keep stub implementation
- Feature flag for real/stub mode
- Easy to revert if issues

---

## 📝 Notes

**TW Agents (Phases 10-16):**
- Not implemented yet
- Can be added later (Full tier)
- Quick + Deep tiers are priority

**Agent Interface:**
- All agents should have consistent interface
- Input: task_data dict
- Output: result dict
- Error handling: exceptions

**Parallel Execution:**
- Phase 5: use `asyncio.gather()` with `return_exceptions=True`
- Collect partial results on failures
- Continue even if some agents fail

---

**Status:** Ready to start Sprint 1  
**Next:** Implement agent factory and real execution
