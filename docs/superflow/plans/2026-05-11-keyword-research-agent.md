# Implementation Plan: Keyword Research Agent

**Date:** 2026-05-11
**Feature:** Keyword Research Agent - Full API Integration
**Product Brief:** [2026-05-11-keyword-research-agent-brief.md](../specs/2026-05-11-keyword-research-agent-brief.md)
**Technical Spec:** [2026-05-11-keyword-research-agent-design-v2.md](../specs/2026-05-11-keyword-research-agent-design-v2.md)
**Git Workflow:** parallel_wave_prs
**Governance:** standard

---

## Overview

Replace 474-line stub implementation with production-grade Keyword Research Agent in **3 sprints over 3-4 weeks**.

**Key Improvements from Spec Review:**
- ✅ Cost reduced 90-95% ($3-5 → $0.04-$0.50 per analysis)
- ✅ Timeline reduced 25-33% (4-6 weeks → 3-4 weeks)
- ✅ Scope clarified (enrichment APIs moved to future enhancement)
- ✅ All 12 critical gaps addressed

---

## Sprint Breakdown

### Wave 1: Sprint 1 - Core Infrastructure [complexity: medium]
**Duration:** 3-5 days
**Goal:** API layer with primary/fallback, resilience patterns, cost control

**Files:**
- AIM/src/aim/subagents/api_clients/__init__.py
- AIM/src/aim/subagents/api_clients/base.py
- AIM/src/aim/subagents/api_clients/semrush.py
- AIM/src/aim/subagents/api_clients/ahrefs.py
- AIM/src/aim/subagents/schemas/__init__.py
- AIM/src/aim/subagents/schemas/api_responses.py
- AIM/src/aim/config/settings.py
- .env.example
- requirements.txt

**Dependencies:** []

### Wave 2: Sprint 2 - Compliance Integration [complexity: high]
**Duration:** 1-2 weeks
**Goal:** Tiered compliance gates, audit trail, database storage

**Files:**
- AIM/src/aim/subagents/compliance/__init__.py
- AIM/src/aim/subagents/compliance/checker.py
- AIM/src/aim/subagents/compliance/patterns.py
- AIM/src/aim/subagents/compliance/fda_client.py
- AIM/src/aim/subagents/compliance/risk_scorer.py
- AIM/src/aim/subagents/schemas/compliance.py
- AIM/src/aim/storage/models.py
- AIM/config/compliance_patterns.yaml
- AIM/alembic/versions/001_add_audit_trail.py
- AIM/alembic/versions/002_add_user_feedback.py

**Dependencies:** [1]

### Wave 3: Sprint 3 - Prioritization + Testing [complexity: medium]
**Duration:** 1 week
**Goal:** Adaptive prioritization, user feedback, comprehensive testing

**Files:**
- AIM/src/aim/subagents/prioritization/__init__.py
- AIM/src/aim/subagents/prioritization/calculator.py
- AIM/src/aim/subagents/prioritization/serp_tracker.py
- AIM/src/aim/subagents/prioritization/weights.py
- AIM/src/aim/subagents/schemas/prioritization.py
- AIM/src/aim/subagents/schemas/results.py
- AIM/src/aim/subagents/keyword_research_agent.py (MAJOR REWRITE)
- AIM/config/prioritization_weights.yaml
- AIM/tests/subagents/test_keyword_research_agent.py
- AIM/tests/subagents/api_clients/test_base.py
- AIM/tests/subagents/api_clients/test_semrush.py
- AIM/tests/subagents/api_clients/test_ahrefs.py
- AIM/tests/subagents/compliance/test_checker.py
- AIM/tests/subagents/prioritization/test_calculator.py
- AIM/tests/fixtures/keyword_data.py

**Dependencies:** [1, 2]

---

## Sprint 1: Core Infrastructure

**Goal:** Build API layer with SEMrush (primary) + Ahrefs (fallback), resilience patterns, cost control

### Task 1.1: Base API Client with Resilience [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/api_clients/base.py`

**Steps:**
1. Create `APIClientBase` class with httpx async client
2. Implement `TokenBucketRateLimiter` (capacity, refill_rate)
3. Add circuit breaker (pybreaker: fail_max=5, reset_timeout=60s)
4. Add retry with exponential backoff (tenacity: 1s → 30s max)
5. Add caching (aiocache: 1h TTL)
6. Add Prometheus metrics (api_calls_total, api_latency, api_cost_total)
7. Add structured logging (structlog)

**Commit:**
```
feat(api): add base API client with resilience patterns

- Circuit breaker: fail_max=5, reset_timeout=60s
- Retry: exponential backoff 1s → 30s
- Token bucket rate limiter
- 1h cache for API responses
- Prometheus metrics + structlog

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.2: Pydantic Schemas with Validation [1-2 hours]

**Files:**
- `AIM/src/aim/subagents/schemas/api_responses.py`

**Steps:**
1. Create `SEMrushKeywordData` schema
2. Create `AhrefsKeywordData` schema with difficulty normalization
3. Create `KeywordExpansionRequest` schema with validation
4. Add `@field_validator` for volume, difficulty, CPC
5. Add `@model_validator` for cross-source consistency

**Commit:**
```
feat(schemas): add API response schemas with validation

- SEMrush and Ahrefs keyword data models
- KeywordExpansionRequest with budget/volume validation
- Cross-source consistency checks
- Normalize Ahrefs difficulty scores

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.3: SEMrush Client with Keyword Magic Tool [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/api_clients/semrush.py`

**Steps:**
1. Create `SEMrushClient` extending `APIClientBase`
2. Implement `expand_keywords()` with Keyword Magic Tool API
3. Add pagination (100 keywords per page)
4. Add budget guard (stops at max_cost_usd)
5. Add min_volume filtering
6. Add zero-volume handling (retry with min_volume=0, then error with suggestions)
7. Add intent detection (transactional, informational, navigational)

**Commit:**
```
feat(api): add SEMrush client with Keyword Magic Tool

- Keyword expansion to 100+ keywords
- Budget guard (max_cost_usd, default $5)
- Zero-volume handling with suggestions
- Intent detection
- Pagination support

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.4: Ahrefs Client (Fallback) [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/api_clients/ahrefs.py`

**Steps:**
1. Create `AhrefsClient` extending `APIClientBase`
2. Implement `expand_keywords()` with Keywords Explorer API
3. Add same budget guard and filtering as SEMrush
4. Add difficulty normalization (Ahrefs uses different scale)

**Commit:**
```
feat(api): add Ahrefs client as fallback

- Keywords Explorer API integration
- Budget guard and filtering
- Difficulty normalization
- Fallback for SEMrush failures

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.5: Settings with Environment Variables [1 hour]

**Files:**
- `AIM/src/aim/config/settings.py`
- `.env.example`

**Steps:**
1. Create `APISettings` with pydantic-settings
2. Add env var validation (SEMRUSH_API_KEY, AHREFS_API_KEY)
3. Add defaults (max_cost_usd=5.0, min_keywords=100, min_volume=10)
4. Create `.env.example` template
5. Add validation on startup

**Commit:**
```
feat(config): add settings with env var validation

- API keys from environment variables
- Validation on startup
- .env.example template
- Never commit credentials to git

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.6: Dependencies [30 min]

**Files:**
- `requirements.txt`

**Steps:**
1. Add httpx>=0.27.0,<0.28.0
2. Add pydantic>=2.6.0,<3.0.0
3. Add pydantic-settings>=2.2.0,<3.0.0
4. Add pybreaker>=1.0.0,<2.0.0
5. Add tenacity>=8.2.0,<9.0.0
6. Add aiolimiter>=1.1.0,<2.0.0
7. Add aiocache[redis]>=0.12.0,<0.13.0
8. Add prometheus-client>=0.20.0,<0.21.0
9. Add structlog>=24.1.0,<25.0.0

**Commit:**
```
chore(deps): add API client dependencies

- httpx, pydantic, pydantic-settings
- pybreaker, tenacity, aiolimiter
- aiocache, prometheus-client, structlog
- All pinned to minor versions

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.7: Unit Tests for API Clients [2-3 hours]

**Files:**
- `AIM/tests/subagents/api_clients/test_base.py`
- `AIM/tests/subagents/api_clients/test_semrush.py`
- `AIM/tests/fixtures/keyword_data.py`

**Steps:**
1. Test circuit breaker opens after 5 failures
2. Test token bucket rate limiting
3. Test caching reduces API calls
4. Test retry with exponential backoff
5. Test SEMrush keyword expansion
6. Test budget guard stops at max_cost_usd
7. Test zero-volume handling
8. Add mock data fixtures

**Commit:**
```
test(api): add unit tests for API clients

- Circuit breaker behavior
- Rate limiting enforcement
- Caching effectiveness
- Budget guard
- Zero-volume handling
- Mock data fixtures

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

---

## Sprint 2: Compliance Integration

**Goal:** Build tiered compliance gates with audit trail, database storage

### Task 2.1: Database Models [1-2 hours]

**Files:**
- `AIM/src/aim/storage/models.py`
- `AIM/alembic/versions/001_add_audit_trail.py`
- `AIM/alembic/versions/002_add_user_feedback.py`

**Steps:**
1. Create `AuditTrail` SQLAlchemy model
2. Create `UserFeedbackRecord` SQLAlchemy model
3. Add indexes (keyword, timestamp, risk_level, feedback_type)
4. Create Alembic migrations
5. Add to requirements.txt: sqlalchemy, alembic, aiosqlite

**Commit:**
```
feat(storage): add audit trail and feedback database models

- AuditTrail table for compliance tracking
- UserFeedbackRecord table for priority accuracy
- Indexes for efficient queries
- Alembic migrations

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.2: Compliance Schemas [1 hour]

**Files:**
- `AIM/src/aim/subagents/schemas/compliance.py`

**Steps:**
1. Create `RiskLevel` enum (CRITICAL, HIGH, MEDIUM, LOW)
2. Create `ComplianceCheckResult` model
3. Create `AuditTrailEntry` model

**Commit:**
```
feat(schemas): add compliance data models

- RiskLevel enum
- ComplianceCheckResult with risk scoring
- AuditTrailEntry for regulatory defense

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.3: Prohibited Language Patterns [4-6 hours]

**Files:**
- `AIM/src/aim/subagents/compliance/patterns.py`
- `AIM/config/compliance_patterns.yaml`

**Steps:**
1. Research FDA prohibited language (100+ patterns)
2. Create pattern library YAML (pattern, severity, rationale)
3. Create `ProhibitedPatternLibrary` class
4. Add pattern matching (<10ms per keyword)
5. Categories: cure claims, guarantees, FDA misrepresentation, etc.

**Commit:**
```
feat(compliance): add prohibited language pattern library

- 100+ FDA prohibited patterns
- Pattern matching <10ms per keyword
- Severity scoring (1-5)
- Rationale for each pattern

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.4: openFDA API Client [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/compliance/fda_client.py`

**Steps:**
1. Create `FDAClient` extending `APIClientBase`
2. Implement `/drug/enforcement.json` endpoint
3. Add 24h cache (aiocache)
4. Add rate limiting (240 req/min)
5. Add graceful degradation (fallback to pattern matching only)

**Commit:**
```
feat(compliance): add openFDA API client

- Drug enforcement letters lookup
- 24h cache for enforcement data
- Rate limiting (240 req/min)
- Graceful degradation on timeout

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.5: Risk Scoring Framework [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/compliance/risk_scorer.py`

**Steps:**
1. Create `RiskScorer` class
2. Implement Likelihood × Severity = Score (1-25)
3. Add action determination:
   - CRITICAL (20-25): block + log
   - HIGH (15-19): reduce priority 50% + flag
   - MEDIUM/LOW (1-14): pass + document
4. Add rationale generation

**Commit:**
```
feat(compliance): add risk scoring framework

- Likelihood × Severity = Score (1-25)
- Action determination (block, reduce, pass)
- Rationale generation
- Risk level classification

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.6: Compliance Checker (Tiered Gates) [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/compliance/checker.py`

**Steps:**
1. Create `ComplianceChecker` class
2. Implement Stage 1: Pattern matching (<10ms)
3. Implement Stage 2: openFDA lookup (cached 24h)
4. Implement Stage 3: Risk scoring (Likelihood × Severity)
5. Add audit trail creation
6. Add database storage (AuditTrail table)

**Commit:**
```
feat(compliance): add tiered compliance checker

- Stage 1: Pattern matching (<10ms)
- Stage 2: openFDA lookup (cached)
- Stage 3: Risk scoring (1-25)
- Audit trail to database
- Regulatory defense ready

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.7: Compliance Tests [2-3 hours]

**Files:**
- `AIM/tests/subagents/compliance/test_checker.py`

**Steps:**
1. Test CRITICAL risk blocks keyword
2. Test HIGH risk reduces priority 50%
3. Test MEDIUM/LOW risk passes with documentation
4. Test pattern matching accuracy
5. Test openFDA integration
6. Test audit trail creation
7. Test graceful degradation (openFDA timeout)

**Commit:**
```
test(compliance): add compliance checker tests

- Risk level actions (block, reduce, pass)
- Pattern matching accuracy
- openFDA integration
- Audit trail creation
- Graceful degradation

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

---

## Sprint 3: Prioritization + Testing

**Goal:** Adaptive prioritization, user feedback, comprehensive testing, agent rewrite

### Task 3.1: Prioritization Schemas [1 hour]

**Files:**
- `AIM/src/aim/subagents/schemas/prioritization.py`
- `AIM/src/aim/subagents/schemas/results.py`

**Steps:**
1. Create `PriorityTier` enum (P0, P1, P2, P3)
2. Create `KeywordPriority` model
3. Create `UserFeedback` model
4. Create `FeedbackSummary` model
5. Create `KeywordAnalysisResult` model
6. Create `KeywordResearchReport` model with recommendations

**Commit:**
```
feat(schemas): add prioritization and result models

- PriorityTier enum (P0-P3)
- KeywordPriority with components
- UserFeedback for accuracy tracking
- KeywordResearchReport with recommendations

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.2: Priority Calculator [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/prioritization/calculator.py`
- `AIM/config/prioritization_weights.yaml`

**Steps:**
1. Create `PriorityCalculator` class
2. Implement formula: (Volume × Intent × Position) / (Difficulty × Competition)
3. Add medical intent boost (40% transactional, 30% informational)
4. Add SERP penalty application
5. Add compliance penalty application
6. Add priority tier classification (P0-P3)
7. Create weights config YAML

**Commit:**
```
feat(prioritization): add priority calculator

- Multi-factor formula
- Medical intent boost (40% transactional)
- SERP and compliance penalties
- Priority tier classification (P0-P3)
- Configurable weights

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.3: SERP Feature Tracker [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/prioritization/serp_tracker.py`

**Steps:**
1. Create `SERPTracker` class
2. Add SERP feature detection (AI Overview, Featured Snippet, PAA)
3. Add CTR tracking by feature
4. Add dynamic penalty calculation
5. Add penalty auto-adjustment based on real CTR data

**Commit:**
```
feat(prioritization): add SERP feature tracker

- SERP feature detection
- CTR tracking by feature
- Dynamic penalty calculation
- Auto-adjustment based on real data

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.4: Keyword Research Agent Rewrite [4-6 hours]

**Files:**
- `AIM/src/aim/subagents/keyword_research_agent.py`

**Steps:**
1. Replace stub implementation with production code
2. Integrate API layer (SEMrush primary, Ahrefs fallback)
3. Integrate compliance layer (tiered gates)
4. Integrate prioritization layer (adaptive formula)
5. Add cost tracking and budget guard
6. Add user feedback collection endpoint
7. Add Event Bus integration
8. Add Obsidian vault integration
9. Add database storage
10. Add recommendations generation

**Commit:**
```
feat(agent): rewrite Keyword Research Agent (production-ready)

- API layer: SEMrush + Ahrefs with resilience
- Compliance: tiered gates + audit trail
- Prioritization: adaptive formula + feedback
- Cost control: budget guard (max $5)
- Event Bus, Database, Obsidian integration
- Recommendations generation

Replaces 474-line stub with production code.

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.5: Integration Tests [2-3 hours]

**Files:**
- `AIM/tests/subagents/test_keyword_research_agent.py`

**Steps:**
1. Test Event Bus integration (publish task, receive result)
2. Test Database integration (audit trail saved)
3. Test Obsidian integration (results saved to vault)
4. Test primary/fallback pattern (SEMrush fails → Ahrefs)
5. Test budget guard (stops at max_cost_usd)
6. Test zero-volume handling
7. Test compliance blocking (CRITICAL risk)

**Commit:**
```
test(agent): add integration tests

- Event Bus integration
- Database storage
- Obsidian vault
- Primary/fallback pattern
- Budget guard
- Zero-volume handling
- Compliance blocking

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.6: E2E Tests with VCR [2-3 hours]

**Files:**
- `AIM/tests/subagents/api_clients/test_semrush.py`
- `AIM/tests/subagents/api_clients/test_ahrefs.py`
- `AIM/tests/cassettes/`

**Steps:**
1. Add pytest-vcr to requirements.txt
2. Create VCR cassettes for SEMrush API
3. Create VCR cassettes for Ahrefs API
4. Test full workflow with real API responses (recorded)
5. Verify tests run without API keys in CI

**Commit:**
```
test(e2e): add E2E tests with VCR cassettes

- pytest-vcr for API mocking
- Recorded real API responses
- Tests run without API keys in CI
- Full workflow validation

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.7: Load Testing [1-2 hours]

**Files:**
- `AIM/tests/subagents/test_keyword_research_agent.py`

**Steps:**
1. Test 10 concurrent keyword research tasks
2. Verify all succeed
3. Verify rate limiter prevents API overload
4. Verify completion within reasonable time (<3 min)

**Commit:**
```
test(load): add load testing for concurrent requests

- 10 concurrent keyword research tasks
- Rate limiter enforcement
- Completion time validation
- API overload prevention

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.8: Prioritization Tests [2 hours]

**Files:**
- `AIM/tests/subagents/prioritization/test_calculator.py`

**Steps:**
1. Test priority formula calculation
2. Test medical intent boost (40% vs 30%)
3. Test SERP penalty application
4. Test compliance penalty application
5. Test priority tier classification (P0-P3)

**Commit:**
```
test(prioritization): add priority calculator tests

- Formula calculation accuracy
- Medical intent boost
- SERP and compliance penalties
- Priority tier classification

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

---

## Sprint Wave Plan

**Git Workflow:** parallel_wave_prs

### Wave 1: Sprint 1 (Independent)
- **Sprints:** [1]
- **Files:** API clients, schemas, settings, dependencies
- **Dependencies:** None
- **PR:** `feat/keyword-research-wave1-api-layer`

### Wave 2: Sprint 2 (Depends on Wave 1)
- **Sprints:** [2]
- **Files:** Compliance layer, database models, patterns
- **Dependencies:** [1]
- **PR:** `feat/keyword-research-wave2-compliance`

### Wave 3: Sprint 3 (Depends on Wave 1 + Wave 2)
- **Sprints:** [3]
- **Files:** Prioritization, agent rewrite, all tests
- **Dependencies:** [1, 2]
- **PR:** `feat/keyword-research-wave3-prioritization-tests`

**Estimated Speedup:** 3 sprints → 3 PRs (sequential due to dependencies)

---

## Merge Order

1. **Wave 1 PR** → main (after review + CI pass)
2. **Wave 2 PR** → main (after Wave 1 merged + review + CI pass)
3. **Wave 3 PR** → main (after Wave 2 merged + review + CI pass)

---

## Total Scope

**Sprints:** 3
**Waves:** 3 (sequential due to dependencies)
**Tasks:** 22 total
- Sprint 1: 7 tasks
- Sprint 2: 7 tasks
- Sprint 3: 8 tasks

**Files Created:** 32
**Files Modified:** 2
- `AIM/src/aim/subagents/keyword_research_agent.py` (MAJOR REWRITE)
- `requirements.txt` (add dependencies)

**Estimated Duration:** 3-4 weeks
- Sprint 1: 3-5 days
- Sprint 2: 1-2 weeks
- Sprint 3: 1 week

**Estimated Cost per Analysis:** $0.04-$0.50 (90-95% reduction from original $3-5)

---

## Success Criteria

**Performance:**
- ✅ Success rate > 95% (with primary/fallback)
- ✅ Execution time < 15 min (target: 5-10 seconds for 100 keywords)
- ✅ API availability > 99% (circuit breakers)

**Quality:**
- ✅ Keywords found > 100 per project
- ✅ Compliance violations = 0 (audit trail)
- ✅ Priority accuracy > 80% (user feedback after 3 months)

**Business:**
- ✅ Cost per analysis < $5 (target: $0.04-$0.50)
- ✅ Time saved vs manual > 90% (5-10s vs 4-8 hours)
- ✅ Actionable recommendations > 60% (user feedback tracking)

---

**Status:** Ready for user approval
**Next Step:** User approval (final gate before autonomous execution)
