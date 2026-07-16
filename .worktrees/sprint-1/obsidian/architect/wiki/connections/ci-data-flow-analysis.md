---
title: "CI System Data Flow Analysis"
created: "2026-05-05T16:42:00"
updated: "2026-05-05T16:42:00"
status: active
tags: [ci-system, data-flow, architecture, analysis]
---

# CI System Data Flow Analysis

## Current Architecture

### Phase Flow

```
Phase 1: CI Scout (Competitor Discovery)
  ↓
  Output: ci-competitors.json
  {
    "competitors": [
      {"name": "X", "url": "auto-generated", "cluster": "direct"},
      ...
    ],
    "top_for_analysis": [...]
  }
  
Phase 2-4: Quick Analysis (Auditor, Reputation)
  ↓
  Input: ci-competitors.json
  Output: enriched profiles
  
Phase 5: Deep Analysis (7 parallel agents)
  ↓
  Input: top_for_analysis from Phase 1
  Agents: Finance, Vacancies, Tech, Site Crawler, Content, Pricing, Ecosystem
  Output: deep profiles per agent
  
Phase 6-9: Synthesis (FactChecker, Strategist, Prioritizer)
  ↓
  Input: all previous phases
  Output: strategic insights
  
Phase 10-16: Full Pipeline (TW agents, Offer Generator)
  ↓
  Input: strategic insights
  Output: commercial offer
```

## Data Flow Problems

### Problem 1: No URL Validation Between Phases

**Current:**
```
CI Scout → generates URL → saves to JSON → CI Deep reads → fails silently
```

**Missing:**
- URL accessibility check
- User confirmation for auto-generated URLs
- Validation gate between Phase 1 and Phase 5

### Problem 2: CI Scout Auto-Generates URLs

**Location:** `ci_scout.py:269`

```python
profile = {
    "name": name,
    "url": f"https://{self._slugify(name)}.ru",  # ❌ Auto-generated
    ...
}
```

**Problems:**
- Assumes all competitors have `.ru` domain
- Doesn't check if URL exists
- Doesn't ask user for correct URL
- Example: "Клиника Юлии Щербатовой" → `doctor-shcherbatova.ru` (wrong!)
- Correct: `juliasherbatova.ru`

### Problem 3: CI Deep Analyzer Doesn't Ask User

**Location:** `ci_deep_analyzer.py:62-129`

```python
async def execute_task(self, task: Task) -> TaskResult:
    try:
        competitors = task.payload["competitors"]
        
        for comp in competitors:
            # ❌ Starts analysis immediately without validation
            result = await self._analyze_competitor(comp)
            
            # ❌ If fails, returns 0% quality silently
            if result["quality_score"] == 0:
                # No user interaction!
                pass
```

**Missing:**
- Pre-analysis URL validation
- User interaction on failure
- Retry logic with user corrections

### Problem 4: No Data Quality Gates

**Current:** Each phase trusts previous phase data blindly

**Missing:**
- Data validation between phases
- Quality checks before expensive operations
- User confirmation checkpoints

## Data Usage Analysis

### What CI Deep Analyzer Produces

**Output:** `AIM/data/ci-deep/deep_analysis_TIMESTAMP.json`

```json
{
  "analysis_date": "2026-05-05T16:19:02",
  "total_analyzed": 5,
  "deep_profiles": [
    {
      "name": "Competitor Name",
      "url": "https://...",
      "total_pages_found": 50,
      "pages_analyzed": 50,
      "page_types": {
        "homepage": [...],
        "services": [...],
        "about": [...],
        "contacts": [...],
        "prices": [...],
        "blog": [...],
        "other": [...]
      },
      "deep_analysis": {
        "total_pages": 50,
        "page_types": {...},
        "seo_coverage": {
          "title": "50/50",
          "description": "50/50",
          "h1": "50/50"
        },
        "schema_coverage": "50/50",
        "quality_score": 100.0
      }
    }
  ],
  "market_insights": {
    "total_competitors": 5,
    "avg_pages_analyzed": 40.2,
    "analysis_depth": "deep"
  }
}
```

### Who Should Use This Data

**Phase 6: CI FactChecker**
- Input: deep_profiles
- Purpose: Verify claims, check contradictions
- Needs: URLs, page content, SEO data

**Phase 7-8: CI Strategist**
- Input: deep_profiles + market_insights
- Purpose: Generate strategic recommendations
- Needs: Quality scores, page types, positioning

**Phase 9: CI Prioritizer**
- Input: all previous phases
- Purpose: Rank competitors by threat level
- Needs: Complete profiles with quality metrics

**Phase 10+: TW Agents**
- Input: top competitors from prioritizer
- Purpose: Analyze traffic, ads, creatives
- Needs: URLs, positioning, ad presence

**Phase 16: CI Offer Generator**
- Input: all phases
- Purpose: Generate commercial offer for client
- Needs: Complete competitive landscape

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: CI Scout                                           │
│ Output: competitors list with auto-generated URLs          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
         ❌ MISSING: URL Validator
         Should validate URLs here!
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2-4: Quick Analysis                                   │
│ Input: competitors list                                     │
│ Output: enriched profiles (ratings, channels, etc.)        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
         ❌ MISSING: Data Quality Gate
         Should check data completeness!
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: CI Deep Analyzer (7 parallel agents)              │
│ Input: top_for_analysis (5-10 competitors)                 │
│ Output: deep_profiles with 50 pages per competitor         │
│                                                             │
│ ❌ PROBLEM: Fails silently if URL wrong                    │
│ ❌ PROBLEM: No user interaction on failure                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 6: CI FactChecker                                     │
│ Input: deep_profiles                                        │
│ Purpose: Verify claims, detect contradictions              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 7-8: CI Strategist                                    │
│ Input: verified profiles + market insights                 │
│ Purpose: Generate strategic recommendations                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 9: CI Prioritizer                                     │
│ Input: all previous phases                                 │
│ Purpose: Rank competitors by threat level                  │
│ Output: prioritized competitor list                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 10-15: TW Agents (Traffic, Ads, Creatives)          │
│ Input: top competitors from prioritizer                    │
│ Purpose: Analyze traffic sources, ad strategies            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 16: CI Offer Generator                                │
│ Input: complete competitive intelligence                   │
│ Output: commercial offer for client                        │
└─────────────────────────────────────────────────────────────┘
```

## Proposed Solution

### Add Validation Gates

```
Phase 1: CI Scout
  ↓
  Output: competitors with URLs
  ↓
✅ NEW: URL Validator Gate
  - Check URL accessibility
  - Ask user for corrections
  - Validate all URLs before Phase 5
  ↓
Phase 2-4: Quick Analysis
  ↓
✅ NEW: Data Quality Gate
  - Check profile completeness
  - Verify required fields
  - Ask user for missing data
  ↓
Phase 5: CI Deep Analyzer
  - Receives validated URLs
  - If fails → asks user (not silent)
  - Retries with corrections
  ↓
Phase 6-16: Continue with validated data
```

### Data Storage Strategy

**Current:**
- `AIM/data/ci-competitors.json` - Phase 1 output
- `AIM/data/ci-deep/deep_analysis_TIMESTAMP.json` - Phase 5 output

**Proposed:**
- `AIM/data/ci-competitors.json` - Phase 1 output (with validation status)
- `AIM/data/ci-competitors-validated.json` - After URL Validator
- `AIM/data/ci-quick-analysis.json` - Phase 2-4 output
- `AIM/data/ci-deep/deep_analysis_TIMESTAMP.json` - Phase 5 output
- `AIM/data/ci-strategic-insights.json` - Phase 6-9 output
- `AIM/data/ci-final-report.json` - Phase 16 output

### Data Schema Enhancement

**Add validation metadata:**
```json
{
  "name": "Competitor Name",
  "url": "https://...",
  "url_validation": {
    "validated": true,
    "validated_at": "2026-05-05T16:00:00",
    "validation_method": "user_confirmed",
    "original_url": "https://old-url.ru",
    "redirect_detected": false,
    "accessible": true,
    "robots_txt_allows": true
  },
  "data_quality": {
    "completeness": 0.95,
    "last_updated": "2026-05-05T16:00:00",
    "stale": false
  }
}
```

## Implementation Priority

### P0 (Critical - blocks Phase 5)
1. ✅ Document problem
2. ⏳ Create URL Validator agent
3. ⏳ Add validation gate in CI Orchestrator
4. ⏳ Enhance CI Deep Analyzer with failure handling

### P1 (High - improves data quality)
1. ⏳ Enhance CI Scout with URL discovery
2. ⏳ Add data quality gates between phases
3. ⏳ Add user interaction checkpoints

### P2 (Medium - nice to have)
1. ⏳ Add data schema validation
2. ⏳ Add stale data detection
3. ⏳ Add data versioning

## Success Metrics

✅ **Zero silent failures** - all failures trigger user interaction
✅ **100% URL validation** - all URLs validated before deep analysis
✅ **< 5% retry rate** - most URLs correct on first try
✅ **User satisfaction** - clear error messages, helpful prompts

## Related Documents

- [CI URL Validation Problem](../decisions/2026-05-05-16-42-ci-url-validation-problem.md)
- [CI System Architecture](../wiki/agents/ci-orchestrator.md)
- [Data Quality Standards](../wiki/concepts/data-quality.md)

---

**Analysis Date:** 2026-05-05T16:42:00
**Analyst:** meAI Architect
**Status:** Active - ready for implementation
