# Expert Panel Synthesis

## API Integration Architect

**Recommended:** Primary + Fallback Strategy (Proposal 2)
- SEMrush as primary (best medical keyword data)
- Ahrefs as fallback
- Other 4 APIs (GSC, Yandex, Wordstat, Keyword Planner) as optional enrichment
- **Effort:** Medium (1-2 days)
- **Key Insight:** Avoid "silent data quality degradation" — require high-quality primary data, not just "any 3 APIs"

**Challenge:** Graceful degradation without quality threshold = garbage data passes as "success"

## Medical Compliance Expert

**Recommended:** Tiered Compliance Gates with Audit Trail (Proposal 3)
- Stage 1: Pattern matching (<10ms)
- Stage 2: openFDA lookup (cached 24h)
- Stage 3: Risk score + compliance penalty
- Actions: CRITICAL=block, HIGH=reduce 50%, MEDIUM/LOW=pass
- **Effort:** Medium (2-3 weeks)
- **Key Insight:** Compliance is risk management with documentation, not binary pass/fail. Audit trail proves due diligence.

**Challenge:** "Compliance Theater" — real-time FDA blocking creates false confidence while missing 95% of actual violations

## SEO Strategy Expert

**Recommended:** Adaptive Weight System with Medical Intent Boost (Proposal 1)
- Intent weight: 40% for transactional, 30% for informational
- Dynamic SERP penalties (track actual CTR, auto-adjust)
- Trend momentum factor (3-month velocity)
- **Effort:** Medium
- **Key Insight:** Static weights + static SERP penalties = strategy decay. Make SERP penalties dynamic based on real CTR data.

**Challenge:** AI Overviews expanding (40% → 60%+ coverage). Hardcoded -50% penalty will be wrong within 3-6 months.

## Unified Recommendation

### Architecture
1. **API Layer:** Primary (SEMrush) + Fallback (Ahrefs) + Optional Enrichment (4 APIs)
2. **Compliance Layer:** Tiered gates (pattern → openFDA → risk score) with audit trail
3. **Prioritization Layer:** Adaptive weights with dynamic SERP penalties

### Implementation Sequence (parallel_wave_prs)

**Wave 1: Core Infrastructure (Sprint 1)**
- Unified API client with circuit breaker + retry + rate limiting
- Primary/fallback pattern (SEMrush → Ahrefs)
- Basic Pydantic schemas for normalization

**Wave 2: Compliance Integration (Sprint 2)**
- Prohibited language pattern library (100+ hours initial build)
- openFDA API integration with 24h caching
- Risk scoring framework (1-25 scale)
- Audit trail logging

**Wave 3: Prioritization Formula (Sprint 3)**
- Multi-factor formula with medical intent boost
- SERP feature detection
- Dynamic penalty calculation (track CTR)
- Priority classification (P0-P3)

**Wave 4: Optional Enrichment (Sprint 4)**
- GSC + Yandex Webmaster (position data)
- Yandex Wordstat + Google Keyword Planner (volume data)
- Parallel calls with graceful degradation

**Wave 5: Testing & Deployment (Sprint 5)**
- Unit tests (80%+ coverage)
- Integration tests (Event Bus, Obsidian, DB)
- E2E tests with real APIs
- Performance benchmarks

### Key Trade-offs

**Chosen Approach:**
- ✅ Fast to production (Wave 1-3 = 3 sprints)
- ✅ High-quality data (primary/fallback prevents garbage)
- ✅ Compliance defensibility (audit trail)
- ✅ Adapts to SERP changes (dynamic penalties)
- ❌ Doesn't use all 6 APIs immediately (enrichment in Wave 4)
- ❌ Requires ongoing calibration (SERP penalties, intent weights)

**Rejected Alternatives:**
- **Unified Client with All 6 APIs (parallel):** Risk of silent data quality degradation
- **Real-Time FDA Blocking:** API rate limits bottleneck, false confidence
- **Competitive Gap Prioritization:** Too much infrastructure, uncertain payoff
- **ROI-Weighted Priority:** Fragile (conversion data sparse in medical marketing)

### Success Criteria

**Performance:**
- Success rate > 95% (with primary/fallback)
- Execution time < 15 min (standard analysis)
- API availability > 99% (circuit breakers)

**Quality:**
- Keywords found > 100 per project
- Compliance violations = 0 (audit trail proves due diligence)
- Priority accuracy > 80% (validated by user feedback)

**Business:**
- Cost per analysis < $5 (SEMrush + Ahrefs primary)
- Time saved vs manual > 90%
- Actionable recommendations > 60%
