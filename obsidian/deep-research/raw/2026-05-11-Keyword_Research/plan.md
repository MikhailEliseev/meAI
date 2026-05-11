# Research Plan: Keyword Research для медицинского маркетинга

**Date:** 2026-05-11  
**Current Year:** 2026 (for date-filtered queries)

---

## Search Query Strategy

### Batch 1: Core Methods & Techniques (5 queries)

1. **Medical keyword research methods 2025-2026**
   - Target: Recent best practices, medical-specific approaches
   - Mode: general + news
   - Expected: Industry blogs, SEO guides, case studies

2. **Long-tail keyword research healthcare medical**
   - Target: Long-tail strategies for medical niche
   - Mode: general
   - Expected: SEO tutorials, methodology guides

3. **Medical terminology keyword mapping ICD-10**
   - Target: Professional vs lay term mapping
   - Mode: general + academic
   - Expected: Medical SEO guides, terminology databases

4. **Local SEO keyword research medical clinics**
   - Target: Regional/local keyword strategies
   - Mode: general
   - Expected: Local SEO guides, case studies

5. **Question-based keywords medical healthcare**
   - Target: Question keyword discovery methods
   - Mode: general
   - Expected: Content marketing guides, SEO tools

### Batch 2: Tools & APIs (5 queries)

6. **Yandex Wordstat API documentation pricing limits**
   - Target: Official API docs, pricing, rate limits
   - Mode: general
   - Expected: Official Yandex docs, developer guides

7. **Google Keyword Planner API documentation 2026**
   - Target: Official API docs, recent updates
   - Mode: general
   - Expected: Google Ads API docs, tutorials

8. **Ahrefs API pricing capabilities documentation**
   - Target: API features, pricing tiers, limits
   - Mode: general
   - Expected: Official Ahrefs docs, comparison reviews

9. **Semrush API vs SE Ranking API comparison**
   - Target: Feature comparison, pricing, use cases
   - Mode: general
   - Expected: Tool comparison articles, reviews

10. **TopVisor API position tracking documentation**
    - Target: Russian position tracking tool API
    - Mode: general
    - Expected: Official docs, integration guides

### Batch 3: Clustering & Metrics (4 queries)

11. **Keyword clustering algorithms SERP-based semantic**
    - Target: Clustering methodologies, implementations
    - Mode: general + academic
    - Expected: SEO research papers, technical guides

12. **Keyword Difficulty calculation formula metrics**
    - Target: KD calculation methods, benchmarks
    - Mode: general
    - Expected: SEO tool documentation, methodology papers

13. **Search intent classification commercial informational**
    - Target: Intent classification frameworks
    - Mode: general + academic
    - Expected: NLP papers, SEO guides

14. **KEI Keyword Effectiveness Index formula**
    - Target: KEI calculation, usage, benchmarks
    - Mode: general
    - Expected: SEO methodology guides

### Batch 4: Russian Legal Compliance (3 queries)

15. **ФЗ-38 статья 24 медицинская реклама запреты**
    - Target: Russian medical advertising law
    - Mode: general
    - Language: Russian
    - Expected: Legal texts, compliance guides

16. **ФЗ-323 реклама медицинских услуг требования**
    - Target: Healthcare law advertising requirements
    - Mode: general
    - Language: Russian
    - Expected: Legal texts, regulatory guides

17. **штрафы нарушение медицинская реклама Россия**
    - Target: Penalties for violations, case examples
    - Mode: general + news
    - Language: Russian
    - Expected: Legal news, case studies, regulatory updates

---

## Sub-Agent Tasks (3 agents)

### Agent 1: API Documentation Deep Dive
**Task:** Extract detailed API documentation for Yandex.Wordstat, Google Keyword Planner, Ahrefs, Semrush, SE Ranking
**Focus:** Authentication, endpoints, rate limits, pricing, code examples
**Output Format:** Structured JSON with API specs per tool

### Agent 2: Clustering Algorithm Analysis
**Task:** Analyze keyword clustering algorithms (semantic, SERP-based, intent-based) with implementation examples
**Focus:** Algorithm descriptions, pros/cons, code snippets, tool implementations
**Output Format:** Structured comparison with code examples

### Agent 3: Russian Legal Compliance Research
**Task:** Deep dive into FZ-38 and FZ-323, extract prohibited terms, requirements, penalties
**Focus:** Specific articles, prohibited formulations, license requirements, case examples
**Output Format:** Structured legal compliance guide with citations

---

## Knowledge Dependencies

**Must understand first:**
1. Medical keyword characteristics (low frequency, high conversion) → informs tool selection
2. Russian market specifics (Yandex dominance) → prioritizes Yandex.Wordstat
3. Legal constraints (FZ-38, FZ-323) → shapes keyword filtering requirements

**Then investigate:**
4. Tool capabilities and APIs → enables implementation planning
5. Clustering algorithms → enables keyword organization
6. Quality metrics → enables keyword evaluation

---

## Triangulation Strategy

**Cross-verify across source types:**
- Official documentation (APIs, legal texts) — authoritative
- Academic papers (clustering, metrics) — methodologically rigorous
- Industry blogs (best practices, case studies) — practical application
- Tool comparison reviews — independent evaluation

**Validation checkpoints:**
- API pricing: Cross-check official docs vs user reviews
- Legal requirements: Cross-check law text vs compliance guides vs case law
- Clustering methods: Cross-check academic papers vs tool implementations
- Metrics formulas: Cross-check multiple SEO sources for consistency

---

## Quality Gates

**Minimum thresholds:**
- 10+ unique sources (not just search result count)
- 3+ sources per major claim (cluster-independent)
- Mix of source types (docs, academic, industry, legal)
- Recent sources (2024-2026) for tools/APIs
- Primary sources for legal requirements (actual law text)

**Stop conditions:**
- 15+ high-quality sources collected
- All critical components have 3+ source backing
- Diminishing returns (new searches yield redundant info)

---

## Time Allocation

- Phase 3 (RETRIEVE): 3-4 minutes (parallel execution)
- Phase 4 (TRIANGULATE): 1-2 minutes (cross-verification)
- Phase 5 (SYNTHESIZE): 2-3 minutes (report drafting)
- Phase 6 (PACKAGE): 1 minute (HTML/PDF generation)

**Total:** 7-10 minutes

---

**Status:** Plan complete ✅  
**Next:** Phase 3 - RETRIEVE (parallel search execution)
