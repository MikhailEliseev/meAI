# University Magisters + Hybrid Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 6 Magister agents with hybrid search (local → Teacher → Researcher) and domain-specific knowledge management.

**Architecture:** Each Magister has local memory (Obsidian vault), searches Teacher's Qdrant when needed, and requests Researcher for new knowledge. Magisters specialize in their domains (SEO, Content, Ads, SMM, Analytics, Intelligence).

**Tech Stack:** Python 3.11+, Obsidian (markdown vaults), Qdrant, Event Bus, SQLAlchemy

**Dependencies:** Plan 1 must be completed (Qdrant, Teacher, Researcher)

---

## File Structure

**New files:**
```
src/meai/
├── agents/
│   ├── magisters/
│   │   ├── __init__.py
│   │   ├── base_magister.py       # Base Magister class
│   │   ├── seo_magister.py        # SEO Magister
│   │   ├── content_magister.py    # Content Magister
│   │   ├── ads_magister.py        # Ads Magister
│   │   ├── smm_magister.py        # SMM Magister
│   │   ├── analytics_magister.py  # Analytics Magister
│   │   └── intelligence_magister.py # Intelligence Magister

obsidian/
├── seo-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── content-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── ads-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── smm-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── analytics-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
└── intelligence-magister/
    ├── knowledge/
    ├── tasks/
    └── decisions/

tests/
├── unit/
│   ├── test_base_magister.py
│   ├── test_seo_magister.py
│   ├── test_content_magister.py
│   ├── test_ads_magister.py
│   ├── test_smm_magister.py
│   ├── test_analytics_magister.py
│   └── test_intelligence_magister.py
│
├── integration/
│   ├── test_magister_hybrid_search.py
│   └── test_magister_teacher_flow.py

scripts/
├── setup_magisters.py
└── test_magisters_core.py
```

---

## Task 1: Base Magister Class

**Files:**
- Create: `src/meai/agents/magisters/__init__.py`
- Create: `src/meai/agents/magisters/base_magister.py`
- Create: `tests/unit/test_base_magister.py`

**Implementation:** Base class for all Magisters with hybrid search logic.

**Key features:**
- Local memory (Obsidian vault)
- Hybrid search: local → Teacher → Researcher
- Domain-specific capabilities
- Task execution and delegation
- Knowledge caching

**Hybrid Search Flow:**
1. Search local Obsidian vault first
2. If not found → query Teacher (Qdrant)
3. If Teacher doesn't have → request Researcher
4. Cache results locally

**Database tables:**
- `magister_tasks`
- `magister_knowledge_cache`
- `magister_queries`
- `magister_decisions`

**Commit:** `feat: add base Magister class with hybrid search`

---

## Task 2: SEO Magister

**Files:**
- Create: `src/meai/agents/magisters/seo_magister.py`
- Create: `tests/unit/test_seo_magister.py`
- Create: `obsidian/seo-magister/` structure

**Implementation:** SEO specialist Magister.

**Capabilities:**
- `analyze_keywords` — keyword research and analysis
- `optimize_content` — on-page SEO optimization
- `analyze_competitors` — competitor analysis
- `track_rankings` — position tracking
- `audit_technical_seo` — technical SEO audit

**Knowledge domains:**
- Keyword research
- On-page optimization
- Link building
- Technical SEO
- SEO tools and analytics

**Commit:** `feat: add SEO Magister with domain-specific capabilities`

---

## Task 3: Content Magister

**Files:**
- Create: `src/meai/agents/magisters/content_magister.py`
- Create: `tests/unit/test_content_magister.py`
- Create: `obsidian/content-magister/` structure

**Implementation:** Content marketing specialist Magister.

**Capabilities:**
- `generate_content` — content creation
- `edit_content` — content editing and improvement
- `plan_content` — content calendar planning
- `analyze_performance` — content performance analysis
- `optimize_for_seo` — SEO content optimization

**Knowledge domains:**
- Content strategy
- Copywriting
- Content formats
- Editorial guidelines
- Content distribution

**Commit:** `feat: add Content Magister with content marketing capabilities`

---

## Task 4: Ads Magister

**Files:**
- Create: `src/meai/agents/magisters/ads_magister.py`
- Create: `tests/unit/test_ads_magister.py`
- Create: `obsidian/ads-magister/` structure

**Implementation:** Advertising specialist Magister.

**Capabilities:**
- `create_campaign` — ad campaign creation
- `optimize_budget` — budget optimization
- `analyze_performance` — campaign performance analysis
- `ab_test` — A/B testing
- `target_audience` — audience targeting

**Knowledge domains:**
- Google Ads
- Facebook Ads
- PPC strategies
- Ad copywriting
- Conversion optimization

**Commit:** `feat: add Ads Magister with advertising capabilities`

---

## Task 5: SMM Magister

**Files:**
- Create: `src/meai/agents/magisters/smm_magister.py`
- Create: `tests/unit/test_smm_magister.py`
- Create: `obsidian/smm-magister/` structure

**Implementation:** Social media marketing specialist Magister.

**Capabilities:**
- `create_post` — social media post creation
- `schedule_posts` — content scheduling
- `engage_audience` — community engagement
- `analyze_metrics` — social media analytics
- `manage_campaigns` — social media campaigns

**Knowledge domains:**
- Social media platforms
- Community management
- Influencer marketing
- Social media advertising
- Engagement strategies

**Commit:** `feat: add SMM Magister with social media capabilities`

---

## Task 6: Analytics Magister

**Files:**
- Create: `src/meai/agents/magisters/analytics_magister.py`
- Create: `tests/unit/test_analytics_magister.py`
- Create: `obsidian/analytics-magister/` structure

**Implementation:** Analytics specialist Magister.

**Capabilities:**
- `analyze_data` — data analysis
- `create_report` — report generation
- `track_metrics` — metrics tracking
- `predict_trends` — trend prediction
- `optimize_performance` — performance optimization

**Knowledge domains:**
- Google Analytics
- Data visualization
- KPI tracking
- Attribution modeling
- Predictive analytics

**Commit:** `feat: add Analytics Magister with data analysis capabilities`

---

## Task 7: Intelligence Magister

**Files:**
- Create: `src/meai/agents/magisters/intelligence_magister.py`
- Create: `tests/unit/test_intelligence_magister.py`
- Create: `obsidian/intelligence-magister/` structure

**Implementation:** Market intelligence specialist Magister.

**Capabilities:**
- `research_market` — market research
- `analyze_trends` — trend analysis
- `monitor_competitors` — competitor monitoring
- `identify_opportunities` — opportunity identification
- `strategic_insights` — strategic recommendations

**Knowledge domains:**
- Market research
- Competitive intelligence
- Industry trends
- Strategic planning
- Business intelligence

**Commit:** `feat: add Intelligence Magister with market intelligence capabilities`

---

## Task 8: Integration Test - Hybrid Search

**Files:**
- Create: `tests/integration/test_magister_hybrid_search.py`

**Implementation:** Test hybrid search flow across all layers.

**Test scenarios:**
1. **Local hit:** Knowledge found in Magister's vault
2. **Teacher hit:** Knowledge found in Teacher's Qdrant
3. **Researcher request:** Knowledge not found, Researcher fetches it
4. **Caching:** Results cached locally after retrieval

**Commit:** `test: add hybrid search integration tests`

---

## Task 9: Integration Test - Magister → Teacher Flow

**Files:**
- Create: `tests/integration/test_magister_teacher_flow.py`

**Implementation:** Test Magister-Teacher communication.

**Test scenarios:**
1. Magister queries Teacher
2. Teacher returns results
3. Magister caches results locally
4. Teacher notifies Magister of new knowledge

**Commit:** `test: add Magister-Teacher integration tests`

---

## Task 10: Setup Script

**Files:**
- Create: `scripts/setup_magisters.py`

**Implementation:** Initialize all Magister vaults and databases.

**Functionality:**
- Create Obsidian vault structure for each Magister
- Initialize database tables
- Create default knowledge files
- Set up Event Bus subscriptions

**Commit:** `feat: add Magisters setup script`

---

## Task 11: End-to-End Test

**Files:**
- Create: `scripts/test_magisters_core.py`

**Implementation:** Complete E2E test of Magisters system.

**Test flow:**
1. Initialize all 6 Magisters
2. SEO Magister queries: "SEO best practices 2026"
3. Local search → not found
4. Teacher search → not found
5. Researcher request → finds knowledge
6. Teacher stores → distributes to SEO Magister
7. SEO Magister caches locally
8. Second query → local hit (cached)

**Commit:** `test: add end-to-end test for Magisters system`

---

## Success Criteria

- [ ] ✅ Base Magister class implemented
- [ ] ✅ All 6 Magisters implemented with domain-specific capabilities
- [ ] ✅ Hybrid search working (local → Teacher → Researcher)
- [ ] ✅ Local caching in Obsidian vaults
- [ ] ✅ Event Bus communication working
- [ ] ✅ All unit tests passing
- [ ] ✅ All integration tests passing
- [ ] ✅ End-to-end test passing

---

## Next Steps

After completing this plan:

**Plan 3: Experience Learning**
- Experience analysis in Magisters
- Quality score updates in Teacher
- Deprecation system
- Success/failure tracking

---

## Notes

- **Obsidian vaults:** Each Magister has isolated vault in `obsidian/<magister-name>/`
- **Knowledge format:** Markdown with frontmatter metadata
- **Caching strategy:** Cache Teacher results locally for 24 hours
- **Event subscriptions:** Each Magister subscribes to `knowledge.distributed` for their domain
