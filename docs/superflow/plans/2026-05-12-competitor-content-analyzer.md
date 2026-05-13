# Implementation Plan: Competitor Content Analyzer

**Date:** 2026-05-12
**Feature:** Competitor Content Analyzer - Full Implementation
**Spec:** [COMPETITOR_CONTENT_ANALYZER_SPEC.md](../../subagents-specs/COMPETITOR_CONTENT_ANALYZER_SPEC.md)
**Git Workflow:** sprint_pr_queue
**Governance:** standard

---

## Overview

Implement production-grade Competitor Content Analyzer based on GitHub-integrated research (4 repos, 880+ stars). Full SEO analysis with Russian market optimization (Yandex + Google).

**Key Features:**
- ✅ Text extraction with trafilatura (from python-seo-analyzer)
- ✅ Keyword density analysis (market-specific: 2-3% Yandex, 0.5-1.5% Google)
- ✅ AI content detection (statistical features, no ML models)
- ✅ E-E-A-T scoring for medical YMYL content
- ✅ Technical SEO analysis (Core Web Vitals, mobile, speed)
- ✅ Production patterns (circuit breaker, retry, rate limiting, caching)

---

## Sprint Breakdown

### Sprint 1: Core Infrastructure [complexity: medium]
**Duration:** 3-5 days
**Goal:** Text extraction, keyword analysis, base utilities

**Components:**
1. Text Extractor (trafilatura integration)
2. Keyword Analyzer (density, LSI, placement)
3. Base schemas and validation
4. Configuration management

**Files:** 8-10 files
**Tests:** 15-20 tests

### Sprint 2: Content Analysis [complexity: high]
**Duration:** 5-7 days
**Goal:** AI detection, E-E-A-T scoring, content structure

**Components:**
1. AI Content Detector (statistical features)
2. E-E-A-T Scorer (medical YMYL)
3. Content Structure Analyzer
4. Readability Calculator

**Files:** 8-10 files
**Tests:** 20-25 tests

### Sprint 3: Technical SEO + Integration [complexity: medium]
**Duration:** 4-6 days
**Goal:** Technical analysis, main agent, full integration

**Components:**
1. Technical SEO Analyzer (Core Web Vitals, mobile, speed)
2. Main Agent (orchestration)
3. Event Bus integration
4. Database storage
5. Obsidian vault integration

**Files:** 6-8 files
**Tests:** 15-20 tests

---

## Sprint 1: Core Infrastructure

**Goal:** Build foundation with text extraction and keyword analysis

### Task 1.1: Text Extractor with trafilatura [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/utils/text_extractor.py` (ALREADY EXISTS ✅)

**Status:** ✅ Already implemented from GitHub integration
- Uses trafilatura for clean text extraction
- Keyword density calculation (unigrams, bigrams, trigrams)
- Meta tags extraction
- Content hash for duplicate detection

**Action:** Verify and enhance if needed

### Task 1.2: Keyword Analyzer [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content/keyword_analyzer.py`

**Steps:**
1. Create `KeywordAnalyzer` class
2. Implement keyword density calculation (market-specific thresholds)
3. Add LSI keyword extraction (5-10 per 1000 words)
4. Add keyword placement analysis (title, h1, first 100 words, last 100 words)
5. Add market-specific optimization (Yandex 2-3%, Google 0.5-1.5%)

**Commit:**
```
feat(competitor): add keyword analyzer with market-specific thresholds

- Keyword density: 2-3% (Yandex), 0.5-1.5% (Google)
- LSI keyword extraction (5-10 per 1000 words)
- Placement analysis (title, h1, first/last 100 words)
- Market-specific optimization

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.3: Base Schemas [1-2 hours]

**Files:**
- `AIM/src/aim/subagents/schemas/competitor_analysis.py`

**Steps:**
1. Create `CompetitorAnalysisRequest` schema
2. Create `KeywordAnalysisResult` schema
3. Create `CompetitorAnalysisResult` schema
4. Add validation for URLs, analysis modes, target markets

**Commit:**
```
feat(schemas): add competitor analysis data models

- CompetitorAnalysisRequest with validation
- KeywordAnalysisResult with market-specific data
- CompetitorAnalysisResult with full structure
- URL and parameter validation

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.4: Configuration [1 hour]

**Files:**
- `AIM/src/aim/config/competitor_analysis_settings.py`

**Steps:**
1. Create `CompetitorAnalysisSettings` with pydantic-settings
2. Add market-specific thresholds (Yandex vs Google)
3. Add timeout and retry settings
4. Add cost control parameters

**Commit:**
```
feat(config): add competitor analysis settings

- Market-specific thresholds (Yandex/Google)
- Timeout and retry configuration
- Cost control parameters
- Environment variable validation

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 1.5: Unit Tests [2-3 hours]

**Files:**
- `AIM/tests/subagents/competitor_content/test_keyword_analyzer.py`
- `AIM/tests/fixtures/competitor_data.py`

**Steps:**
1. Test keyword density calculation (Yandex vs Google thresholds)
2. Test LSI keyword extraction
3. Test keyword placement analysis
4. Test market-specific optimization
5. Add mock data fixtures

**Commit:**
```
test(competitor): add keyword analyzer tests

- Keyword density (market-specific)
- LSI keyword extraction
- Placement analysis
- Market optimization
- Mock data fixtures

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

---

## Sprint 2: Content Analysis

**Goal:** AI detection, E-E-A-T scoring, content structure analysis

### Task 2.1: AI Content Detector [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/utils/ai_content_detector.py` (ALREADY EXISTS ✅)

**Status:** ✅ Already implemented from GitHub integration
- Statistical features (entropy, perplexity, burstiness, TTR, readability)
- No ML models needed (production-ready)
- 5 detection signals with confidence scoring

**Action:** Verify and enhance if needed

### Task 2.2: E-E-A-T Scorer [4-5 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content/eeat_scorer.py`

**Steps:**
1. Create `EEATScorer` class
2. Implement Experience scoring (first-person, case studies)
3. Implement Expertise scoring (credentials, degrees, certifications)
4. Implement Authoritativeness scoring (citations, references, author bio)
5. Implement Trustworthiness scoring (sources, transparency, contact info)
6. Add medical YMYL specific checks (qualified reviewer, update frequency)

**Commit:**
```
feat(competitor): add E-E-A-T scorer for medical YMYL

- Experience scoring (first-person, case studies)
- Expertise scoring (credentials, certifications)
- Authoritativeness scoring (citations, author bio)
- Trustworthiness scoring (sources, transparency)
- Medical YMYL checks (reviewer, updates)

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.3: Content Structure Analyzer [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content/structure_analyzer.py`

**Steps:**
1. Create `StructureAnalyzer` class
2. Implement readability scoring (Flesch Reading Ease, Flesch-Kincaid)
3. Implement heading hierarchy analysis (h1-h6 structure)
4. Implement content length analysis (word count, paragraph count)
5. Implement formatting analysis (lists, bold, images)

**Commit:**
```
feat(competitor): add content structure analyzer

- Readability scoring (Flesch metrics)
- Heading hierarchy analysis (h1-h6)
- Content length analysis
- Formatting analysis (lists, bold, images)

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.4: Content Analysis Schemas [1-2 hours]

**Files:**
- `AIM/src/aim/subagents/schemas/content_analysis.py`

**Steps:**
1. Create `AIDetectionResult` schema
2. Create `EEATScore` schema
3. Create `ContentStructure` schema
4. Create `ReadabilityScore` schema

**Commit:**
```
feat(schemas): add content analysis data models

- AIDetectionResult with confidence
- EEATScore with component breakdown
- ContentStructure with hierarchy
- ReadabilityScore with metrics

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 2.5: Content Analysis Tests [3-4 hours]

**Files:**
- `AIM/tests/subagents/competitor_content/test_eeat_scorer.py`
- `AIM/tests/subagents/competitor_content/test_structure_analyzer.py`

**Steps:**
1. Test E-E-A-T scoring (all 4 components)
2. Test medical YMYL checks
3. Test readability scoring
4. Test heading hierarchy analysis
5. Test content length and formatting

**Commit:**
```
test(competitor): add content analysis tests

- E-E-A-T scoring (4 components)
- Medical YMYL checks
- Readability scoring
- Heading hierarchy
- Content length and formatting

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

---

## Sprint 3: Technical SEO + Integration

**Goal:** Technical analysis, main agent orchestration, full integration

### Task 3.1: Technical SEO Analyzer [3-4 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content/technical_analyzer.py`

**Steps:**
1. Create `TechnicalAnalyzer` class
2. Implement Core Web Vitals measurement (LCP, INP, CLS)
3. Implement mobile optimization check
4. Implement page speed analysis
5. Implement schema markup detection
6. Integrate with Playwright for metrics

**Commit:**
```
feat(competitor): add technical SEO analyzer

- Core Web Vitals (LCP, INP, CLS)
- Mobile optimization check
- Page speed analysis
- Schema markup detection
- Playwright integration

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.2: Main Agent (Orchestration) [4-5 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content_analyzer.py`

**Steps:**
1. Create `CompetitorContentAnalyzer` class extending `BaseAgent`
2. Implement 10-step algorithm from spec
3. Integrate all analyzers (keyword, AI, E-E-A-T, structure, technical)
4. Add comparison logic (client vs competitor)
5. Add recommendations generation
6. Add priority actions calculation

**Commit:**
```
feat(competitor): add main analyzer agent with orchestration

- 10-step analysis algorithm
- All analyzers integrated
- Client vs competitor comparison
- Recommendations generation
- Priority actions calculation

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.3: Event Bus Integration [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content_analyzer.py` (update)

**Steps:**
1. Add Event Bus subscription (subagent.task.assigned)
2. Add Event Bus publishing (subagent.task.completed)
3. Add error handling and retry
4. Add correlation ID tracking

**Commit:**
```
feat(competitor): add Event Bus integration

- Subscribe to task.assigned events
- Publish task.completed events
- Error handling and retry
- Correlation ID tracking

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.4: Database Storage [2-3 hours]

**Files:**
- `AIM/src/aim/storage/models.py` (update)
- `AIM/alembic/versions/003_add_competitor_analysis.py`

**Steps:**
1. Create `CompetitorAnalysis` SQLAlchemy model
2. Add indexes (url, timestamp, analysis_mode)
3. Create Alembic migration
4. Add storage methods to agent

**Commit:**
```
feat(storage): add competitor analysis database models

- CompetitorAnalysis table
- Indexes for efficient queries
- Alembic migration
- Storage integration

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.5: Obsidian Vault Integration [2-3 hours]

**Files:**
- `AIM/src/aim/subagents/competitor_content_analyzer.py` (update)

**Steps:**
1. Add vault integration (save results to obsidian/seo-magister/)
2. Create analysis report template
3. Add markdown formatting
4. Add cross-linking to related analyses

**Commit:**
```
feat(competitor): add Obsidian vault integration

- Save results to seo-magister vault
- Analysis report template
- Markdown formatting
- Cross-linking support

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.6: Integration Tests [3-4 hours]

**Files:**
- `AIM/tests/subagents/test_competitor_content_analyzer.py`

**Steps:**
1. Test full analysis workflow (end-to-end)
2. Test Event Bus integration
3. Test Database storage
4. Test Obsidian vault integration
5. Test error handling and retry
6. Test market-specific optimization (Yandex vs Google)

**Commit:**
```
test(competitor): add integration tests

- Full analysis workflow (E2E)
- Event Bus integration
- Database storage
- Obsidian vault integration
- Error handling and retry
- Market-specific optimization

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

### Task 3.7: Technical SEO Tests [2-3 hours]

**Files:**
- `AIM/tests/subagents/competitor_content/test_technical_analyzer.py`

**Steps:**
1. Test Core Web Vitals measurement
2. Test mobile optimization check
3. Test page speed analysis
4. Test schema markup detection

**Commit:**
```
test(competitor): add technical SEO tests

- Core Web Vitals measurement
- Mobile optimization check
- Page speed analysis
- Schema markup detection

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

---

## Dependencies

**Already Implemented (from GitHub integration):**
- ✅ `text_extractor.py` (trafilatura, keyword density)
- ✅ `ai_content_detector.py` (statistical features)
- ✅ Base API client patterns (circuit breaker, retry, rate limiting, caching)

**New Dependencies:**
- `playwright>=1.40.0` - For JavaScript rendering and Core Web Vitals
- `beautifulsoup4>=4.12.0` - For HTML parsing (already in requirements)
- `lxml>=5.0.0` - For fast XML/HTML parsing

---

## Total Scope

**Sprints:** 3
**Tasks:** 18 total
- Sprint 1: 5 tasks (Core Infrastructure)
- Sprint 2: 5 tasks (Content Analysis)
- Sprint 3: 8 tasks (Technical SEO + Integration)

**Files Created:** ~25-30
**Files Modified:** 2-3
- `requirements.txt` (add playwright)
- `AIM/src/aim/storage/models.py` (add CompetitorAnalysis model)

**Estimated Duration:** 12-18 days
- Sprint 1: 3-5 days
- Sprint 2: 5-7 days
- Sprint 3: 4-6 days

---

## Success Criteria

**Performance:**
- ✅ Analysis time < 60 seconds per page
- ✅ Success rate > 95%
- ✅ Cost per analysis < $0.10

**Quality:**
- ✅ Keyword density accuracy (market-specific)
- ✅ AI detection confidence > 80%
- ✅ E-E-A-T scoring comprehensive (4 components)
- ✅ Technical SEO metrics accurate (Core Web Vitals)

**Integration:**
- ✅ Event Bus integration working
- ✅ Database storage working
- ✅ Obsidian vault integration working
- ✅ All tests passing (50+ tests)

---

**Status:** Ready for user approval
**Next Step:** User approval → Sprint 1 execution
