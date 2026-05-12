# Teacher Agent — Continuous Learning Pattern

**Version:** 1.0.0  
**Date:** 2026-05-13  
**Status:** ✅ Validated (Competitor Content Analyzer test case)

---

## Overview

**Teacher Agent** — это Chief Learning Officer системы meAI. Единственная задача Teacher Agent — следить за всеми источниками знаний и обучать остальных агентов.

**Принцип:** Система должна постоянно учиться и улучшаться, не устаревать.

**Validated Approach:** GitHub-integrated deep research (протестировано на Competitor Content Analyzer, 2026-05-12)

---

## Architecture

```
Teacher Agent (Chief Learning Officer)
  ↓
1. Monitors Knowledge Sources
   ├─ GitHub (new repos, updates, patterns)
   ├─ Industry (articles, best practices, API updates)
   └─ Performance (metrics, benchmarks, bottlenecks)
  ↓
2. Identifies Learning Opportunities
   ├─ Critical subagents (priority list)
   ├─ Last learning date (staleness check)
   └─ Gap analysis (current vs best practices)
  ↓
3. Executes Deep Research
   ├─ GitHub Search (top repos by stars)
   ├─ Deep Research (comprehensive analysis)
   └─ Cost tracking (budget control)
  ↓
4. Generates Learning Reports
   ├─ Gap analysis (what's missing)
   ├─ Priority matrix (CRITICAL/HIGH/LOW)
   └─ Actionable recommendations
  ↓
5. Updates Subagents
   ├─ Specification updates
   ├─ Implementation improvements
   └─ Performance optimizations
  ↓
6. Stores Knowledge
   └─ obsidian/teacher/wiki/learning-cycles/
```

---

## Learning Cycle Workflow

### Frequency: Every 2-4 Weeks

**Trigger:**
- Scheduled (cron job every 2 weeks)
- Manual (user request)
- Event-driven (new major GitHub repo, API breaking change)

### Steps

#### 1. Read Critical Subagents List

**Location:** `docs/subagents-specs/` or `obsidian/teacher/wiki/critical-subagents.md`

**Criteria for "Critical":**
- Core functionality (Keyword Research, Content Gap Analysis, Competitor Analysis)
- High usage frequency
- Direct impact on client deliverables
- Complex domain knowledge

**Example:**
```markdown
# Critical Subagents

## P0 (Check every 2 weeks)
- Keyword Research Agent
- Content Gap Analysis Agent
- Competitor Content Analyzer
- Technical SEO Analyzer

## P1 (Check every 4 weeks)
- Backlink Analyzer
- Content Quality Scorer
- SERP Feature Tracker
```

#### 2. Check Last Learning Date

**For each critical subagent:**
- Read `obsidian/teacher/wiki/learning-cycles/[subagent-name]/last-update.md`
- Calculate staleness: `days_since_last_update = today - last_update_date`
- If `days_since_last_update > 14` (P0) or `> 28` (P1) → trigger learning cycle

#### 3. GitHub Monitoring

**Search Strategy:**

```python
# Example: Competitor Content Analyzer
github_queries = [
    "seo analysis python stars:>100",
    "competitor analysis seo stars:>50",
    "keyword density analyzer stars:>50",
    "ai content detection stars:>100",
    "technical seo audit stars:>50",
]

# Filter by:
# - Stars (>50, >100, >150)
# - Recent activity (commits in last 6 months)
# - Language (Python preferred, but check JS/PHP/Ruby)
# - License (MIT, Apache 2.0 preferred)
```

**What to Extract:**
- Architecture patterns (circuit breaker, retry, caching)
- API integrations (real examples with error handling)
- Edge cases handling
- Performance optimizations
- Cost optimization strategies
- Testing approaches

#### 4. Deep Research Execution

**Use spec-writer skill with GitHub-integrated approach:**

```bash
# Trigger deep research
/spec-writer [Subagent Name]

# Research will automatically:
# 1. Search GitHub for top repos
# 2. Analyze production code
# 3. Extract best practices
# 4. Document API costs
# 5. Identify architecture patterns
# 6. Generate comprehensive report
```

**Budget Control:**
- Standard research: ~$0.50 (6 phases, 5-10 min)
- Deep research: ~$1-3 (8 phases, 10-20 min)
- GitHub-integrated: ~$0.15-0.50 (efficient search)

**Quality Metrics:**
- Sources: 10-15 (avg credibility >80/100)
- Claims verified: 100%
- GitHub repos: 3-5 (total stars >500)
- Code examples: 20-30 (adapted, not copied)

#### 5. Gap Analysis

**Compare:**
- Current implementation (read `docs/subagents-specs/[SUBAGENT]_SPEC.md`)
- Research findings (read `~/Documents/[Topic]_Research_[YYYYMMDD]/report.md`)

**Identify Gaps:**

```markdown
## Gap Analysis: [Subagent Name]

### Architecture Gaps
- ❌ Missing: Circuit breaker pattern
- ❌ Missing: Exponential backoff retry
- ✅ Has: Rate limiting (but basic implementation)

### Feature Gaps
- ❌ Missing: AI content detection
- ❌ Missing: Russian market optimization (Yandex)
- ✅ Has: Keyword density analysis (but outdated thresholds)

### Performance Gaps
- Current: 10 keywords/sec
- Benchmark (GitHub): 50 keywords/sec
- Gap: 5x slower

### Cost Gaps
- Current: No caching (repeat API calls)
- Best practice: 1-hour cache TTL
- Potential savings: 60-80% API costs
```

#### 6. Priority Matrix

**Classify updates:**

```markdown
## Priority Matrix

### 🔴 CRITICAL (Implement immediately)
**Impact:** High | **Effort:** Any | **Risk:** Low

1. Add circuit breaker pattern
   - Why: Prevents cascade failures
   - Effort: 2-4 hours
   - Risk: Low (well-tested pattern)

2. Update keyword density thresholds
   - Why: Current thresholds outdated (2024 → 2026)
   - Effort: 1 hour
   - Risk: Low (just config change)

### 🟡 HIGH (Plan for next sprint)
**Impact:** Medium-High | **Effort:** Medium | **Risk:** Low-Medium

1. Add AI content detection
   - Why: 51.7% of web content is AI-generated
   - Effort: 8-12 hours
   - Risk: Medium (new dependency)

2. Implement caching layer
   - Why: 60-80% cost savings
   - Effort: 4-6 hours
   - Risk: Low (standard pattern)

### 🟢 LOW (Backlog)
**Impact:** Low-Medium | **Effort:** High | **Risk:** Medium-High

1. Add video SEO analysis
   - Why: Growing trend, but not core
   - Effort: 16-20 hours
   - Risk: Medium (new domain)
```

**Priority Formula:**
```
priority_score = (impact * 10) + (1 / effort_hours) - (risk * 5)

impact: 1-10 (1=low, 10=critical)
effort_hours: 1-40
risk: 0-2 (0=low, 1=medium, 2=high)
```

#### 7. Generate Learning Report

**Template:**

```markdown
# Learning Cycle: [Subagent Name]

**Date:** YYYY-MM-DD  
**Cycle:** #N  
**Last Update:** YYYY-MM-DD (X days ago)  
**Research Cost:** $X.XX  
**Research Duration:** X minutes

---

## Executive Summary

[2-3 sentences: what changed in the industry, why this matters]

---

## GitHub Findings

### New Repositories

**1. [user/repo](https://github.com/user/repo)** (XXX stars, last updated YYYY-MM-DD)
- **What:** [Brief description]
- **Key Feature:** [What's innovative]
- **Architecture:** [Approach used]
- **Relevance:** [Why this matters for our subagent]
- **Action:** [What to implement]

**2. [user/repo](https://github.com/user/repo)** (XXX stars)
- ...

### Updated Repositories

**[user/repo](https://github.com/user/repo)** (XXX stars)
- **Update:** [What changed]
- **Impact:** [How this affects us]
- **Action:** [What to do]

---

## Industry Updates

### Best Practices

**1. [Practice Name]**
- **Source:** [Article/Documentation URL]
- **Change:** [What's new]
- **Why:** [Reason for change]
- **Action:** [How to implement]

### API Updates

**[API Name]**
- **Change:** [Breaking change / New feature]
- **Impact:** [How this affects our integration]
- **Action:** [Update required]

### Algorithm Changes

**[Search Engine] Update**
- **Date:** YYYY-MM-DD
- **Change:** [What changed]
- **Impact:** [Effect on rankings/metrics]
- **Action:** [Optimization needed]

---

## Performance Gap Analysis

### Current State
- Metric 1: [current value]
- Metric 2: [current value]
- Metric 3: [current value]

### Benchmark (GitHub)
- Metric 1: [benchmark value] (source: [repo])
- Metric 2: [benchmark value] (source: [repo])
- Metric 3: [benchmark value] (source: [repo])

### Gap
- Metric 1: [X% slower/faster]
- Metric 2: [X% worse/better]
- Metric 3: [X% difference]

### Root Cause
[Why the gap exists]

### Optimization Opportunity
[How to close the gap]

---

## Recommendations

### 🔴 CRITICAL (Implement now)

**1. [Recommendation Title]**
- **Why:** [Business/technical reason]
- **What:** [Specific action]
- **How:** [Implementation approach]
- **Effort:** [X hours]
- **Risk:** [Low/Medium/High]
- **Expected Impact:** [Quantified benefit]

### 🟡 HIGH (Plan for next sprint)

**1. [Recommendation Title]**
- ...

### 🟢 LOW (Backlog)

**1. [Recommendation Title]**
- ...

---

## Implementation Plan

### Phase 1: Critical Updates (Week 1)
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Phase 2: High Priority (Week 2-3)
- [ ] Task 1
- [ ] Task 2

### Phase 3: Low Priority (Backlog)
- [ ] Task 1
- [ ] Task 2

---

## Cost-Benefit Analysis

### Investment
- Research: $X.XX
- Implementation: X hours = $XXX (at $50/hour)
- Testing: X hours = $XX
- **Total:** $XXX

### Expected Return
- Performance improvement: X%
- Cost savings: $XX/month
- Quality improvement: X%
- **ROI:** X% over Y months

---

## Appendix A: Research Summary

[Link to full research report]

**Key Statistics:**
- Sources: X (avg credibility: XX/100)
- Claims verified: X/X (100%)
- GitHub repos: X (total stars: XXX)
- Code examples: X

---

**Next Review:** YYYY-MM-DD (in X weeks)
```

#### 8. Store Knowledge

**Obsidian Vault Structure:**

```
obsidian/teacher/
├── wiki/
│   ├── learning-cycles/
│   │   ├── keyword-research-agent/
│   │   │   ├── 2026-05-13-cycle-01.md
│   │   │   ├── 2026-05-27-cycle-02.md
│   │   │   └── last-update.md
│   │   ├── content-gap-analysis-agent/
│   │   │   └── ...
│   │   └── competitor-content-analyzer/
│   │       ├── 2026-05-13-cycle-01.md
│   │       └── last-update.md
│   ├── critical-subagents.md
│   ├── github-tracking/
│   │   ├── seo-analysis-repos.md
│   │   ├── content-analysis-repos.md
│   │   └── ai-detection-repos.md
│   ├── industry-updates/
│   │   ├── google-algorithm-updates.md
│   │   ├── yandex-algorithm-updates.md
│   │   └── api-changes.md
│   └── statistics/
│       ├── learning-cycles-summary.md
│       └── roi-tracking.md
└── decisions/
    └── learning-strategy.md
```

---

## Metrics & KPIs

### Coverage Metrics

**Subagent Coverage:**
```
coverage = (subagents_reviewed / total_critical_subagents) * 100%
target: 100% every 4 weeks
```

**Freshness:**
```
avg_staleness = sum(days_since_last_update) / total_subagents
target: < 14 days for P0, < 28 days for P1
```

### Quality Metrics

**Research Quality:**
- Sources credibility: >80/100
- Claim verification: 100%
- GitHub repos: >3 per research
- Total stars: >500 per research

**Implementation Rate:**
```
implementation_rate = (recommendations_implemented / total_recommendations) * 100%
target: >80% for CRITICAL, >60% for HIGH
```

### Impact Metrics

**Performance Improvement:**
```
performance_gain = (new_metric - old_metric) / old_metric * 100%
track: speed, accuracy, cost, quality
```

**Cost Savings:**
```
monthly_savings = old_cost - new_cost
roi = monthly_savings * 12 / implementation_cost
target: ROI > 200% over 12 months
```

**Quality Improvement:**
```
quality_score = (precision + recall + f1_score) / 3
track: before vs after updates
```

---

## GitHub-Integrated Research Approach

### Validated: 2026-05-12 (Competitor Content Analyzer)

**Results:**
- ✅ Found 4 production repos (880+ stars)
- ✅ 25+ code examples adapted
- ✅ Real API costs documented
- ✅ Architecture patterns extracted
- ✅ 100% claim verification
- ✅ Cost: $0.15 (95% under budget)
- ✅ Duration: 58 minutes

**What Worked:**
1. **GitHub Search First**
   - Top repos by stars (>50, >100, >150)
   - Recent activity (commits in last 6 months)
   - Production-ready code (not tutorials)

2. **Code Pattern Extraction**
   - Circuit breaker implementations
   - Retry logic with exponential backoff
   - Rate limiting (token bucket)
   - Caching strategies (TTL, invalidation)
   - Error handling patterns

3. **Real-World Data**
   - API costs (not marketing prices)
   - Performance benchmarks (from production)
   - Edge cases (from issues/PRs)
   - Integration examples (working code)

4. **Market-Specific Insights**
   - Russian market (Yandex vs Google)
   - Regional differences (keyword density, ranking factors)
   - Compliance requirements (E-E-A-T for medical)

**What to Improve:**
- Consider JavaScript/PHP repos (not just Python)
- Include enterprise pricing analysis
- Add regional variations (not just Russia-wide)
- Test code examples before including

---

## Cost Analysis

### Per Learning Cycle

**Research Phase:**
- Standard research: $0.50 (5-10 min)
- Deep research: $1-3 (10-20 min)
- GitHub-integrated: $0.15-0.50 (efficient)

**Implementation Phase:**
- CRITICAL updates: 2-8 hours = $100-400
- HIGH updates: 4-12 hours = $200-600
- LOW updates: 8-20 hours = $400-1000

**Total per Subagent:**
- Research: $0.50
- Implementation: $300 (avg)
- **Total:** ~$300-350 per cycle

### ROI Calculation

**Example: Competitor Content Analyzer**

**Investment:**
- Research: $0.15
- Spec creation: 2 hours = $100
- Implementation: 16 hours = $800
- Testing: 4 hours = $200
- **Total:** $1,100

**Expected Return (12 months):**
- Time savings: 10 hours/month * $50 = $500/month = $6,000/year
- Quality improvement: 20% more accurate = 2 fewer client revisions/month = $1,000/year
- Cost savings: 60% API cost reduction = $300/year
- **Total:** $7,300/year

**ROI:** 564% over 12 months

---

## Automation Opportunities

### Phase 1: Manual (Current)
- Teacher Agent runs learning cycles manually
- User triggers via `/spec-writer` or direct request
- Reports reviewed manually

### Phase 2: Semi-Automated (Next)
- Scheduled GitHub monitoring (cron job every 2 weeks)
- Automatic staleness detection
- Notification when learning cycle needed
- Manual approval for deep research

### Phase 3: Fully Automated (Future)
- Automatic deep research trigger
- AI-powered gap analysis
- Automatic priority scoring
- Auto-generated implementation tasks
- Human approval only for CRITICAL updates

---

## Best Practices

### DO

✅ **Check GitHub first** — production code > theory  
✅ **Adapt, don't copy** — understand patterns, implement for our context  
✅ **Verify claims** — 100% verification rate required  
✅ **Track costs** — research budget control  
✅ **Document everything** — learning cycles, decisions, ROI  
✅ **Prioritize ruthlessly** — CRITICAL > HIGH > LOW  
✅ **Measure impact** — before/after metrics  
✅ **Update regularly** — P0 every 2 weeks, P1 every 4 weeks

### DON'T

❌ **Don't skip GitHub** — theory alone misses edge cases  
❌ **Don't copy code** — licensing issues, context mismatch  
❌ **Don't trust without verification** — always cross-check claims  
❌ **Don't ignore costs** — track research + implementation  
❌ **Don't implement everything** — focus on high-impact updates  
❌ **Don't forget ROI** — calculate expected return  
❌ **Don't let subagents stale** — >4 weeks = outdated

---

## Example: Competitor Content Analyzer Learning Cycle

**Date:** 2026-05-12  
**Cycle:** #1 (initial)  
**Research Cost:** $0.15  
**Duration:** 58 minutes

### GitHub Findings

**4 repos found (880+ stars):**
1. python-seo-analyzer (300★) - keyword density, meta tags
2. python-for-seo (250★) - API integrations, retry logic
3. seo-analyzer (150★) - circuit breaker, caching
4. ai-content-detector (180★) - DistilBERT, 94% accuracy

### Key Insights

**Architecture Patterns:**
- Circuit breaker (fail after 5 errors, reset 60s)
- Exponential backoff (1s → 30s max)
- Rate limiting (token bucket, 10 req/s)
- Caching (1-hour TTL)

**Market Specifics:**
- Yandex: keyword density 2-3%, user behavior > backlinks
- Google: keyword density 0.5-1.5%, backlinks > user behavior

**API Costs:**
- SEMrush: $499.95/month (50K units/day)
- Ahrefs: $949/month
- Playwright: Free

### Recommendations

🔴 **CRITICAL:**
1. Implement circuit breaker pattern
2. Update keyword density thresholds (market-specific)
3. Add E-E-A-T scoring for medical content

🟡 **HIGH:**
1. Add AI content detection (DistilBERT)
2. Implement caching layer (60-80% cost savings)
3. Add Russian market optimization (Yandex)

🟢 **LOW:**
1. Add video SEO analysis
2. Expand to local SEO

### Implementation

**Spec created:** 35KB, 1,089 lines  
**Status:** Ready for Sprint 5 implementation  
**Next review:** 2026-05-27 (in 2 weeks)

---

## Changelog

### v1.0.0 (2026-05-13)
- Initial pattern documentation
- Validated GitHub-integrated approach
- Added Competitor Content Analyzer example
- Defined metrics and KPIs
- Created learning cycle template

---

**Author:** Mikhail Eliseev (via meAI Architect)  
**Status:** ✅ Ready for use  
**Next Update:** After 3-5 learning cycles (collect more data)
