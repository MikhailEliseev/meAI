# Phase 1 Context: Keyword Research Agent Implementation

## Task Assessment

**Feature:** Keyword Research Agent - Full API Integration
**Novelty:** Medium (well-specified, but complex API integrations)
**Blast Radius:** Medium (SEO Magister subagent, affects SEO workflow)
**Ambiguity:** Low (2,008-line specification with detailed requirements)

## Governance Mode Recommendation: STANDARD

**Rationale:**
- Specification is complete and detailed (78 KB, 2,008 lines)
- API integrations are well-documented with pricing and limits
- Medical compliance requirements are clear
- Not critical infrastructure (can iterate if needed)
- Standard dual-model review sufficient

**Why not LIGHT:**
- Complex API integrations (SEMrush, Ahrefs, GSC, Yandex)
- Medical compliance requirements (FDA, HIPAA, AMA)
- Multi-source data aggregation logic
- Need thorough review of API error handling

**Why not CRITICAL:**
- Not affecting production systems yet
- Can be tested and iterated
- No patient data or financial transactions
- Specification already validated

## Git Workflow Mode Recommendation: SOLO_SINGLE_PR

**Rationale:**
- Single cohesive feature (one agent implementation)
- No parallel work needed
- Clear scope and boundaries
- First implementation of SEO Magister subagent

## Key Implementation Requirements

1. **API Integrations (Priority Order):**
   - SEMrush API (keyword gaps, domain overview)
   - Ahrefs API (backlinks, keyword difficulty)
   - Google Search Console API (real positions, queries)
   - Yandex Webmaster API (positions, queries)
   - Yandex Wordstat (frequency data)
   - Google Keyword Planner (search volume)

2. **Medical Compliance:**
   - FDA enforcement letter verification
   - HIPAA tracking pixel detection
   - AMA ethical standards check
   - Risk scoring (Critical/High/Medium/Low)

3. **Multi-Factor Prioritization:**
   - Formula: `(Volume × Intent × Position) / (Difficulty × Competition)`
   - 4 priority levels: P0 (80-100), P1 (60-79), P2 (40-59), P3 (0-39)

4. **Performance Targets:**
   - Quick analysis: < 5 min (1 competitor)
   - Standard analysis: < 15 min (3 competitors)
   - Comprehensive: < 30 min (5 competitors)
   - Deep analysis: < 60 min (5 competitors + compliance)

## Current State

**Existing File:** `AIM/src/aim/subagents/keyword_research_agent.py` (474 lines)
**Status:** Stub implementation with internal logic only
**Gap:** Missing all external API integrations and compliance checks

## Specification Location

`docs/subagents-specs/KEYWORD_RESEARCH_SPEC.md` (2,008 lines, 78 KB)
