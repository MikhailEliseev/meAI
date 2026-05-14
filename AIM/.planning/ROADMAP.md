---
version: 1.0
status: in_progress
last_updated: 2026-05-14
---

# AIM Testing Infrastructure - Roadmap

## Overview

6-phase roadmap for building comprehensive test coverage for the AIM agency system. Phases 1-3 completed (8 hours), Phases 4-6 planned (9 hours).

**Total Target:** 70+ tests, 17 hours, 75%+ coverage

---

## Phase 1: Foundation Tests ✅

**Status:** COMPLETED (2026-05-14)  
**Time:** 2 hours (actual)  
**Tests:** 22 tests passing

### Goal
Test core infrastructure components to ensure reliability of Event Bus and Event Store.

### Deliverables
- [x] Event Bus tests (10 tests)
  - Publish/subscribe patterns
  - Priority queues (P0-P3)
  - Unsubscribe functionality
  - Error handling
- [x] Event Store tests (12 tests)
  - Append events
  - Replay from timestamp
  - Query by correlation ID
  - Persistence validation

### Files Created
- `tests/unit/test_event_bus.py` (10 tests)
- `tests/unit/test_event_store.py` (12 tests)

### Success Metrics
- ✅ 22/22 tests passing
- ✅ Core infrastructure validated
- ✅ Async patterns working
- ✅ Error handling verified

---

## Phase 2: Event Flow Testing ✅

**Status:** COMPLETED (2026-05-14)  
**Time:** 3 hours (actual)  
**Tests:** 8 tests passing

### Goal
Test event correlation and flow tracking to ensure end-to-end event chains work correctly.

### Deliverables
- [x] EventFlowTracker + Event Bus integration (8 tests)
  - Correlation chain tracking
  - Async synchronization with asyncio.Event
  - Error propagation patterns
  - Multi-subscriber event flow
  - Event Bus + Event Store integration

### Files Created
- `tests/integration/test_event_flow.py` (8 tests)

### Success Metrics
- ✅ 8/8 tests passing
- ✅ Correlation chains tracked correctly
- ✅ Async synchronization works
- ✅ Error propagation validated

### Commit
- `d270bd8` - feat(tests): add Phase 2 - Event Flow Testing (8 integration tests)

---

## Phase 3: API Integration Tests ✅

**Status:** COMPLETED (2026-05-14)  
**Time:** 3 hours (actual)  
**Tests:** 8 tests passing

### Goal
Test API clients with resilience patterns to ensure reliable external API integration.

### Deliverables
- [x] Token bucket rate limiter tests (4 tests)
  - Acquire single/multiple tokens
  - Refill over time
  - Blocking when empty
- [x] SEMrush client tests (3 tests)
  - Keyword expansion with mocks
  - Budget guard
  - Empty results handling
- [x] Ahrefs client tests (1 test)
  - Keyword expansion with mocks
- [x] VCR cassettes documentation

### Files Created
- `tests/unit/test_api_clients.py` (8 tests)
- `tests/fixtures/vcr_cassettes/README.md`

### Success Metrics
- ✅ 8/8 tests passing
- ✅ Rate limiter validated
- ✅ API clients tested with mocks
- ✅ Budget guards working
- ✅ VCR cassettes documented

### Commit
- `0cfc0ae` - feat(tests): add Phase 3 - API Integration Tests (8 unit tests)

---

## Phase 4: Magister Tests ⏳

**Status:** IN PROGRESS (Plans 1-3 completed ✅)  
**Time:** 3 hours (estimated), 0.22h (actual so far)  
**Tests:** 24 tests (target), 18 tests (completed)

### Goal
Test Magister orchestration workflows to ensure proper task delegation and coordination.

### Deliverables
- [x] SEO Magister tests (6 tests) ✅ COMPLETED
  - Action routing (identify_subagents)
  - Result aggregation with weighted scoring
  - Timeout handling
  - Partial and full failure scenarios
- [x] Content Magister tests (6 tests) ✅ COMPLETED
  - Action routing (create, optimize, plan, distribute)
  - Result aggregation with content metrics
  - Partial failure with missing metrics
  - E2E flow with real coordination logic
- [x] Ads Magister tests (6 tests) ✅ COMPLETED
  - Action routing (campaign, budget, test, conversion)
  - Campaign metrics aggregation (CTR, conversion rate)
  - Partial failure with missing predictions
  - E2E flow with vault error handling
- [ ] Analytics Magister tests (6 tests)
  - Action routing
  - Data aggregation
  - Error handling
  - E2E flow

### Files Created
- `tests/fixtures/magister_fixtures.py` (pytest fixtures)
- `tests/unit/test_seo_magister.py` (4 unit tests)
- `tests/integration/test_seo_magister_e2e.py` (2 integration tests)
- `tests/unit/test_content_magister.py` (4 unit tests)
- `tests/integration/test_content_magister_e2e.py` (2 integration tests)
- `tests/unit/test_ads_magister.py` (4 unit tests)
- `tests/integration/test_ads_magister_e2e.py` (2 integration tests)

### Success Metrics
- ✅ 18/24 tests passing (75%)
- ✅ SEO, Content, Ads Magisters tested
- ✅ Orchestration workflows validated
- ✅ Dependency injection implemented
- ⏳ Analytics Magister remaining

### Commits
- `a04dd90` - feat(04-01): add dependency injection to SEO Magister
- `dd0dc5a` - feat(04-01): create pytest fixtures for SEO Magister
- `cf9f408` - test(04-01): add SEO Magister unit tests (4 tests)
- `5685e4e` - test(04-01): add SEO Magister integration tests (2 tests)
- `907b107` - feat(04-02): add dependency injection to Content Magister
- `0a6ef4b` - feat(04-02): add Content Magister fixtures
- `4498aaa` - test(04-02): add Content Magister unit tests (4 tests)
- `abcaddb` - test(04-02): add Content Magister integration tests (2 tests)
- `5dcb3d7` - feat(04-03): add dependency injection to Ads Magister
- `5cc3429` - feat(04-03): add Ads Magister fixtures
- `823d32f` - test(04-03): add Ads Magister unit tests (4 tests)
- `cbe3891` - test(04-03): add Ads Magister integration tests (2 tests)

---

## Phase 5: Subagent Tests ⏳

**Status:** PLANNED  
**Time:** 4 hours (estimated)  
**Tests:** 15+ tests (target)

### Goal
Test domain-specific subagents to ensure correct business logic and API integration.

### Deliverables
- [ ] Keyword Research Agent tests (3+ tests)
  - Keyword expansion
  - Clustering and grouping
  - Priority scoring
- [ ] Competitor Analysis Agent tests (3+ tests)
  - Competitor identification
  - Content gap analysis
  - Backlink analysis
- [ ] Content Generation Agent tests (3+ tests)
  - Content creation
  - SEO optimization
  - Quality validation
- [ ] Campaign Management Agent tests (3+ tests)
  - Campaign creation
  - Budget optimization
  - Performance tracking
- [ ] Data Collection Agent tests (3+ tests)
  - Metrics collection
  - Data validation
  - Storage integration

### Files to Create
- `tests/unit/test_keyword_research_agent.py`
- `tests/unit/test_competitor_analysis_agent.py`
- `tests/unit/test_content_generation_agent.py`
- `tests/unit/test_campaign_management_agent.py`
- `tests/unit/test_data_collection_agent.py`

### Success Metrics
- [ ] 15+ tests passing
- [ ] Each subagent has 3+ tests
- [ ] Domain logic validated
- [ ] API integration tested
- [ ] Error handling verified

### Dependencies
- Subagent implementations in `AIM/src/aim/subagents/`
- API clients (SEMrush, Ahrefs, GA4, Yandex)
- Mock data for offline testing

---

## Phase 6: End-to-End Tests ⏳

**Status:** PLANNED  
**Time:** 2 hours (estimated)  
**Tests:** 5+ tests (target)

### Goal
Test complete workflows from Operator to Magister to Subagent to ensure system integration.

### Deliverables
- [ ] SEO workflow test (1 test)
  - Operator → SEO Magister → Keyword Research Agent
  - Full keyword research workflow
  - Result aggregation
- [ ] Content workflow test (1 test)
  - Operator → Content Magister → Content Generation Agent
  - Full content creation workflow
  - Quality validation
- [ ] Ads workflow test (1 test)
  - Operator → Ads Magister → Campaign Management Agent
  - Full campaign creation workflow
  - Budget tracking
- [ ] Multi-agent coordination test (1 test)
  - Parallel execution of multiple workflows
  - Event Bus coordination
  - Error recovery
- [ ] Real-world scenario test (1 test)
  - Complete client onboarding workflow
  - Multiple Magisters and Subagents
  - End-to-end validation

### Files to Create
- `tests/e2e/test_seo_workflow.py`
- `tests/e2e/test_content_workflow.py`
- `tests/e2e/test_ads_workflow.py`
- `tests/e2e/test_multi_agent_coordination.py`
- `tests/e2e/test_real_world_scenario.py`

### Success Metrics
- [ ] 5+ tests passing
- [ ] Full workflow tested (Operator → Magister → Subagent)
- [ ] Multi-agent coordination validated
- [ ] Real-world scenarios covered
- [ ] Error recovery tested

### Dependencies
- All Magisters implemented
- All Subagents implemented
- Event Bus and Event Store working
- Database integration

---

## Timeline

| Phase | Status | Time | Tests | Completion |
|-------|--------|------|-------|------------|
| Phase 1: Foundation | ✅ Done | 2h | 22 | 100% |
| Phase 2: Event Flow | ✅ Done | 3h | 8 | 100% |
| Phase 3: API Integration | ✅ Done | 3h | 8 | 100% |
| Phase 4: Magister Tests | ⏳ Next | 3h | 12+ | 0% |
| Phase 5: Subagent Tests | 📋 Planned | 4h | 15+ | 0% |
| Phase 6: End-to-End Tests | 📋 Planned | 2h | 5+ | 0% |
| **Total** | **47%** | **8/17h** | **38/70+** | **54%** |

---

## Success Criteria

### Overall Targets
- [x] Phase 1-3 completed (8 hours, 38 tests)
- [ ] Phase 4-6 completed (9 hours, 32+ tests)
- [ ] 70+ tests passing
- [ ] 75%+ code coverage
- [ ] All critical paths tested
- [ ] CI/CD integration ready

### Quality Gates
- [ ] All tests pass consistently
- [ ] No flaky tests
- [ ] Coverage reports generated
- [ ] Documentation complete
- [ ] Performance benchmarks met

---

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| API rate limits | Medium | VCR cassettes for offline testing | ✅ Mitigated |
| Async test flakiness | High | Deterministic timeouts, proper sync | ✅ Mitigated |
| Mock data drift | Medium | Periodic VCR cassette re-recording | 📋 Planned |
| Test maintenance | Low | Keep tests simple, avoid over-mocking | ✅ Mitigated |
| Time overrun | Medium | Focus on critical paths, not 100% coverage | 🟡 Monitoring |

---

## Next Steps

1. **Immediate (Phase 4):**
   - Run `/gsd-plan-phase 4` to create detailed plan
   - Implement Magister tests (12+ tests)
   - Commit and update progress

2. **Short-term (Phase 5):**
   - Implement Subagent tests (15+ tests)
   - Validate domain logic
   - Test API integrations

3. **Medium-term (Phase 6):**
   - Implement E2E tests (5+ tests)
   - Validate full workflows
   - Test multi-agent coordination

4. **Long-term:**
   - CI/CD integration
   - Performance regression detection
   - Test architecture documentation

---

## Change Log

- **2026-05-14:** Initial roadmap (retroactive for Phase 1-3, planned for Phase 4-6)
