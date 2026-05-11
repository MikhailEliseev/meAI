# Board Memo: Keyword Research Agent Implementation

**Date:** 2026-05-11
**Feature:** Keyword Research Agent - Full API Integration
**Governance:** Standard | **Git Workflow:** parallel_wave_prs
**Run ID:** 7AD77690-2B7F-4555-81AE-656913E6A089

---

## Executive Summary

Replace 474-line stub implementation with production-grade Keyword Research Agent using **Primary + Fallback API strategy**, **Tiered Compliance Gates**, and **Adaptive Prioritization Formula**. Delivers high-quality medical keyword research with regulatory compliance in 5 parallel waves over 5 sprints.

**Key Decision:** Start with SEMrush (primary) + Ahrefs (fallback) for quality data, add 4 enrichment APIs later. Prioritize compliance defensibility (audit trail) over perfect accuracy.

---

## Problem Statement

Current implementation is a 474-line stub with internal logic only. Specification requires:
- **6+ API integrations:** SEMrush, Ahrefs, GSC, Yandex Webmaster, Wordstat, Keyword Planner
- **Medical compliance checks:** FDA enforcement, HIPAA, AMA ethical standards
- **Multi-factor prioritization:** (Volume × Intent × Position) / (Difficulty × Competition) with compliance penalties
- **Production-grade resilience:** Circuit breakers, retry with exponential backoff, rate limiting

---

## Expert Panel Findings

### API Integration Architect

**Recommended:** Primary + Fallback Strategy
- SEMrush as primary (best medical keyword data per research)
- Ahrefs as fallback if SEMrush fails
- Other 4 APIs as optional enrichment (parallel, non-blocking)

**Key Insight:** Avoid "silent data quality degradation" — requiring "any 3 APIs" allows garbage data to pass as success. Need quality threshold: at least 1 of {SEMrush, Ahrefs} + 2 others.

**Challenge:** Graceful degradation without quality gates = weak medical data → bad recommendations → wasted client budget.

### Medical Compliance Expert

**Recommended:** Tiered Compliance Gates with Audit Trail
- **Stage 1:** Pattern matching against prohibited language library (<10ms)
- **Stage 2:** openFDA API lookup for flagged terms (cached 24h)
- **Stage 3:** Risk score calculation (Likelihood × Severity = 1-25)
- **Actions:** CRITICAL (20-25) = block + log, HIGH (15-19) = reduce priority 50% + flag for review, MEDIUM/LOW = pass with documentation

**Key Insight:** Compliance is risk management with documentation, not binary pass/fail. Audit trail proves due diligence when FDA questions a keyword in 2027.

**Challenge:** "Compliance Theater" — real-time FDA blocking creates false confidence while missing 95% of actual violations (only warning letters in database).

### SEO Strategy Expert

**Recommended:** Adaptive Weight System with Medical Intent Boost
- **Intent weight:** 40% for transactional (vs 30% standard) — medical marketing lives/dies on intent accuracy
- **Dynamic SERP penalties:** Track actual CTR by SERP feature, auto-adjust penalties (AI Overviews expanding 40% → 60%+)
- **Trend momentum:** 3-month velocity to catch rising opportunities early

**Key Insight:** Static weights + static SERP penalties = strategy decay. AI Overview coverage changes weekly — hardcoded -50% penalty will be wrong within 3-6 months.

**Challenge:** Medical marketing has sparse conversion data. ROI-weighted priority sounds good but is fragile in practice.

---

## Recommended Approach

### Architecture (3 Layers)

1. **API Layer:** Primary (SEMrush) + Fallback (Ahrefs) + Optional Enrichment (4 APIs)
   - Circuit breaker (pybreaker): fail_max=5, reset_timeout=60s
   - Retry with exponential backoff (tenacity): initial=1s, max=30s, jitter
   - Token bucket rate limiting per API
   - Pydantic schemas for data normalization

2. **Compliance Layer:** Tiered gates with audit trail
   - Prohibited language pattern library (100+ hours initial build)
   - openFDA API integration (cached 24h)
   - Risk scoring framework (1-25 scale)
   - Audit trail for every keyword decision

3. **Prioritization Layer:** Adaptive weights with dynamic penalties
   - Medical intent boost (40% transactional, 30% informational)
   - SERP feature detection + CTR tracking
   - Dynamic penalty calculation (auto-adjust based on real data)
   - Priority classification (P0-P3)

### Implementation Phases (5 Waves)

**Wave 1: Core Infrastructure (Sprint 1, 3-5 days)**
- Unified API client with three-layer resilience
- Primary/fallback pattern (SEMrush → Ahrefs)
- Basic Pydantic schemas for normalization
- Token bucket rate limiting

**Wave 2: Compliance Integration (Sprint 2, 1-2 weeks)**
- Prohibited language pattern library
- openFDA API integration with 24h caching
- Risk scoring framework (1-25 scale)
- Audit trail logging (Event Store)

**Wave 3: Prioritization Formula (Sprint 3, 3-5 days)**
- Multi-factor formula with medical intent boost
- SERP feature detection
- Dynamic penalty calculation (track CTR)
- Priority classification (P0-P3)

**Wave 4: Optional Enrichment (Sprint 4, 3-5 days)**
- GSC + Yandex Webmaster (position data)
- Yandex Wordstat + Google Keyword Planner (volume data)
- Parallel calls with graceful degradation

**Wave 5: Testing & Deployment (Sprint 5, 1 week)**
- Unit tests (80%+ coverage)
- Integration tests (Event Bus, Obsidian, DB)
- E2E tests with real APIs
- Performance benchmarks

**Total Timeline:** 5 sprints, ~4-6 weeks

---

## Trade-offs & Alternatives

### Chosen Approach

**Pros:**
- ✅ Fast to production (Wave 1-3 = 3 sprints, ~3 weeks)
- ✅ High-quality data (primary/fallback prevents garbage)
- ✅ Compliance defensibility (audit trail proves due diligence)
- ✅ Adapts to SERP changes (dynamic penalties)
- ✅ Cost-efficient (SEMrush + Ahrefs primary, ~$3-5 per analysis)

**Cons:**
- ❌ Doesn't use all 6 APIs immediately (enrichment in Wave 4)
- ❌ Requires ongoing calibration (SERP penalties, intent weights)
- ❌ Prohibited language library needs 100+ hours initial build
- ❌ 24h cache = 1-day blind spot for new FDA enforcement

### Rejected Alternatives

**Unified Client with All 6 APIs (parallel):**
- **Why not:** Risk of silent data quality degradation. If SEMrush + Ahrefs fail but 3 weak APIs succeed, system returns "success" with garbage data.

**Real-Time FDA Enforcement Blocking:**
- **Why not:** API rate limits (240 req/min) bottleneck large keyword sets. 200-500ms latency per keyword. False positives from specialty mismatch.

**Competitive Gap Prioritization:**
- **Why not:** Too much infrastructure (competitor tracking, SERP analysis, backlink scraping) for uncertain payoff. Can add later if needed.

**ROI-Weighted Priority:**
- **Why not:** Fragile — conversion data sparse in medical marketing. LTV estimates speculative. Ranking cost estimation unreliable for new keywords.

---

## Success Criteria

### Performance
- Success rate > 95% (with primary/fallback)
- Execution time < 15 min (standard analysis, 3 competitors)
- API availability > 99% (circuit breakers prevent cascading failures)

### Quality
- Keywords found > 100 per project
- Compliance violations = 0 (audit trail proves due diligence)
- Priority accuracy > 80% (validated by user feedback after 3 months)

### Business
- Cost per analysis < $5 (SEMrush + Ahrefs API costs)
- Time saved vs manual research > 90%
- Actionable recommendations > 60% (keywords user actually uses)

---

## Risk Mitigation

### High-Risk Areas

1. **API Rate Limits**
   - **Mitigation:** Token bucket per API, circuit breaker prevents cascading failures
   - **Fallback:** Primary/fallback pattern ensures high-quality data even if one API fails

2. **API Costs**
   - **Mitigation:** Quota monitoring + alerts, circuit breaker stops wasting money on failing APIs
   - **Estimate:** SEMrush ~$40/100K requests, Ahrefs ~$50/100K → ~$3-5 per analysis (100-200 keywords)

3. **Medical Compliance**
   - **Mitigation:** Tiered gates with audit trail, monthly compliance review for HIGH-risk keywords
   - **Defensibility:** Audit trail proves reasonable safeguards when FDA questions a keyword

4. **Data Quality**
   - **Mitigation:** Primary/fallback pattern requires at least 1 of {SEMrush, Ahrefs}
   - **Validation:** Multi-source validation, graceful degradation (partial results > no results)

---

## Next Steps

1. **User Approval** — Review this Board Memo, approve approach
2. **Technical Specification** — Write detailed spec with dual-model review (product + technical lens)
3. **Implementation Plan** — Break down 5 waves into specific tasks with dependencies
4. **Execution** — Parallel wave implementation (Wave 1-3 first, then Wave 4-5)

---

**Approval Required:** User sign-off before proceeding to specification writing

**Estimated Timeline:**
- Specification writing: 1-2 days
- Implementation (Wave 1-5): 4-6 weeks
- Total: ~5-7 weeks to production
