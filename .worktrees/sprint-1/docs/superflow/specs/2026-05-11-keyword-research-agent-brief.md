# Product Brief: Keyword Research Agent

**Date:** 2026-05-11
**Feature:** Keyword Research Agent - Full API Integration
**Status:** Awaiting Product Approval

---

## Product Summary

### What We're Building

Production-grade Keyword Research Agent that replaces the current 474-line stub with:

1. **Primary + Fallback API Strategy**
   - SEMrush as primary data source (best medical keyword data)
   - Ahrefs as automatic fallback if SEMrush fails
   - 4 enrichment APIs (GSC, Yandex Webmaster, Wordstat, Keyword Planner) added later

2. **Medical Compliance System**
   - Tiered compliance gates (pattern matching → openFDA lookup → risk scoring)
   - Audit trail for every keyword decision (regulatory defensibility)
   - Risk-based actions: CRITICAL = block, HIGH = reduce priority 50%, MEDIUM/LOW = pass with documentation

3. **Adaptive Prioritization Formula**
   - Multi-factor scoring: (Volume × Intent × Position) / (Difficulty × Competition)
   - Medical intent boost (40% transactional vs 30% standard)
   - Dynamic SERP penalties that auto-adjust based on real CTR data
   - Priority classification: P0 (80-100), P1 (60-79), P2 (40-59), P3 (0-39)

4. **Production-Grade Resilience**
   - Circuit breakers (pybreaker): fail_max=5, reset_timeout=60s
   - Retry with exponential backoff (tenacity): initial=1s, max=30s, jitter
   - Token bucket rate limiting per API
   - Pydantic schemas for data normalization

### Problems Solved

**For Medical Marketers:**
- ✅ High-quality keyword data (primary/fallback prevents garbage data)
- ✅ Compliance confidence (audit trail proves due diligence to FDA)
- ✅ Accurate prioritization (adapts to changing SERP landscape)
- ✅ Cost efficiency (~$3-5 per analysis vs $50-100 manual research)
- ✅ Time savings (15 min vs 4-8 hours manual research)

**For System:**
- ✅ Reliability (>95% success rate with primary/fallback)
- ✅ Resilience (circuit breakers prevent cascading failures)
- ✅ Maintainability (clear separation: API layer, compliance layer, prioritization layer)
- ✅ Observability (audit trail + Event Store logging)

### NOT in Scope

**Explicitly excluded from this implementation:**

1. **Competitive Gap Prioritization** — requires competitor tracking infrastructure (can add later if needed)
2. **ROI-Weighted Priority** — fragile due to sparse conversion data in medical marketing
3. **Real-Time FDA Enforcement Blocking** — API rate limits bottleneck large keyword sets, 24h cache is sufficient
4. **All 6 APIs in Wave 1** — start with quality (SEMrush + Ahrefs), add enrichment later

### Key Decisions + Rationale

| Decision | Choice | Rationale | Tradeoff |
|----------|--------|-----------|----------|
| **API Strategy** | Primary + Fallback | Prevents silent data quality degradation | Doesn't use all 6 APIs immediately |
| **Compliance Approach** | Tiered Gates + Audit Trail | Regulatory defensibility > perfect accuracy | 24h cache = 1-day blind spot for new FDA enforcement |
| **Prioritization** | Adaptive Weights + Dynamic Penalties | Adapts to SERP changes (AI Overviews expanding) | Requires ongoing calibration |
| **Implementation Sequence** | 5 waves over 5 sprints | Fast to production (Wave 1-3 = 3 weeks) | Enrichment APIs delayed to Wave 4 |
| **Git Workflow** | parallel_wave_prs | Independent waves run concurrently | Requires careful dependency management |

### Defaults Assumed

1. **SEMrush API credentials** — user will provide during Wave 1 implementation
2. **Ahrefs API credentials** — user will provide during Wave 1 implementation
3. **openFDA API** — public, no credentials needed
4. **Prohibited language library** — will build during Wave 2 (100+ hours initial effort)
5. **SERP feature CTR tracking** — will implement basic tracking in Wave 3, refine over time

---

## Problem Statement

Medical marketers need high-quality keyword research that balances SEO opportunity with regulatory compliance. Current stub implementation provides internal logic only — no real API data, no compliance checks, no production resilience.

**User Pain:**
- Manual keyword research takes 4-8 hours per project
- Risk of FDA violations from non-compliant keywords
- Outdated prioritization (static weights don't adapt to SERP changes)
- No audit trail for regulatory defense

---

## Jobs to be Done

**When** planning a medical marketing campaign,
**I want to** get compliant, prioritized keyword recommendations with audit trail,
**so I can** confidently execute SEO strategy without regulatory risk.

**When** analyzing keyword opportunities,
**I want to** see multi-factor priority scores that adapt to SERP changes,
**so I can** focus budget on keywords with highest ROI potential.

**When** facing FDA scrutiny,
**I want to** provide audit trail showing reasonable safeguards,
**so I can** demonstrate due diligence and avoid enforcement action.

---

## User Stories

1. **As a medical marketer**, I want to input a seed keyword and get 100+ related keywords with volume, difficulty, CPC, and compliance risk, so that I can build a comprehensive SEO strategy.

2. **As a compliance officer**, I want to see audit trail for every keyword decision (why it was flagged, what risk score it received, what action was taken), so that I can demonstrate due diligence to regulators.

3. **As an SEO strategist**, I want priority scores that adapt to SERP feature changes (AI Overviews, Featured Snippets), so that my recommendations stay relevant as Google evolves.

4. **As a system operator**, I want circuit breakers and fallback APIs, so that one API failure doesn't crash the entire analysis.

5. **As a budget owner**, I want cost-efficient analysis (~$3-5 per project), so that I can scale keyword research across multiple clients without breaking the bank.

---

## Success Criteria

### Performance Metrics
- ✅ Success rate > 95% (with primary/fallback)
- ✅ Execution time < 15 min (standard analysis, 3 competitors)
- ✅ API availability > 99% (circuit breakers prevent cascading failures)

### Quality Metrics
- ✅ Keywords found > 100 per project
- ✅ Compliance violations = 0 (audit trail proves due diligence)
- ✅ Priority accuracy > 80% (validated by user feedback after 3 months)

### Business Metrics
- ✅ Cost per analysis < $5 (SEMrush + Ahrefs API costs)
- ✅ Time saved vs manual research > 90% (15 min vs 4-8 hours)
- ✅ Actionable recommendations > 60% (keywords user actually uses)

---

## Edge Cases

### Happy Path
1. User provides seed keyword "dental implants near me"
2. Agent calls SEMrush API → success (200+ keywords)
3. Agent runs compliance checks → 5 keywords flagged HIGH risk, 195 pass
4. Agent calculates priority scores → 50 P0/P1 keywords
5. Agent returns results with audit trail

### Failure Mode 1: Primary API Fails
1. User provides seed keyword
2. Agent calls SEMrush API → timeout (circuit breaker opens)
3. Agent automatically falls back to Ahrefs API → success
4. Agent continues with compliance and prioritization
5. Agent returns results with note: "Used Ahrefs (SEMrush unavailable)"

### Failure Mode 2: Both Primary APIs Fail
1. User provides seed keyword
2. Agent calls SEMrush → fails, Ahrefs → fails
3. Agent returns error: "Unable to retrieve keyword data (both primary sources unavailable)"
4. Agent logs failure to Event Store
5. User can retry later or check API status

### Failure Mode 3: Compliance API Fails
1. User provides seed keyword
2. Agent retrieves keywords successfully
3. Agent calls openFDA API → timeout
4. Agent falls back to pattern matching only
5. Agent returns results with warning: "Compliance check degraded (openFDA unavailable)"
6. Agent logs degraded mode to audit trail

---

## Implementation Timeline

**5 waves over 5 sprints, ~4-6 weeks total:**

- **Wave 1:** Core Infrastructure (Sprint 1, 3-5 days)
- **Wave 2:** Compliance Integration (Sprint 2, 1-2 weeks)
- **Wave 3:** Prioritization Formula (Sprint 3, 3-5 days)
- **Wave 4:** Optional Enrichment (Sprint 4, 3-5 days)
- **Wave 5:** Testing & Deployment (Sprint 5, 1 week)

---

**Next Step:** User approval to proceed to technical specification writing.
