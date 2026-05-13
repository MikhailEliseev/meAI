---
type: framework
date: 2026-05-13
status: active
---

# Priority Framework

## Overview

When Teacher Agent finds multiple skills to adopt, this framework determines **execution order**. Not all skills are equal — some are critical, others can wait.

## Priority Levels

### 🔴 P0 - CRITICAL (Do Now)

**Definition:** System-breaking issues or major opportunities

**Criteria:**
- Security vulnerability (CVE published)
- Breaking API change (must adapt or break)
- Production incident (skill would prevent)
- Performance degradation >50%
- Data loss risk
- Compliance violation

**SLA:** Fix within 24 hours

**Examples:**
- API key exposed in logs → adopt secure key management
- Rate limit exceeded → adopt rate limiting
- Memory leak detected → adopt memory profiler
- SQL injection found → adopt parameterized queries

**Process:**
1. Stop current work
2. Assess impact
3. Adopt skill immediately
4. Deploy to production
5. Monitor for 24h
6. Post-mortem report

### 🟠 P1 - HIGH (Do This Sprint)

**Definition:** Important improvements with clear ROI

**Criteria:**
- Performance improvement 20-50%
- New feature (high user value)
- Code quality improvement (reduces bugs)
- Better error handling (improves reliability)
- Cost reduction >30%

**SLA:** Complete within 2 weeks

**Examples:**
- Circuit breaker pattern → prevents cascading failures
- Exponential backoff → reduces API costs
- Caching layer → improves response time
- Structured logging → easier debugging

**Process:**
1. Add to sprint backlog
2. Estimate effort (hours)
3. Assign to learning cycle
4. Adopt during sprint
5. Validate improvements
6. Document results

### 🟡 P2 - MEDIUM (Do Next Sprint)

**Definition:** Valuable but not urgent

**Criteria:**
- Performance improvement 10-20%
- New feature (medium user value)
- Code refactoring (no functional change)
- Documentation improvement
- Technical debt reduction

**SLA:** Complete within 1 month

**Examples:**
- Better type hints → improves IDE support
- More comprehensive tests → catches edge cases
- API documentation → easier onboarding
- Code comments → better maintainability

**Process:**
1. Add to backlog
2. Wait for capacity
3. Batch with similar tasks
4. Adopt when convenient
5. Validate improvements

### 🟢 P3 - LOW (Do Eventually)

**Definition:** Nice-to-have improvements

**Criteria:**
- Performance improvement <10%
- Optional feature (low user value)
- Cosmetic changes
- Experimental patterns
- Research implementations

**SLA:** Complete within 3 months (or never)

**Examples:**
- Alternative algorithm (unproven)
- Beta library (unstable)
- Cutting-edge pattern (risky)
- Minor optimization (marginal gain)

**Process:**
1. Add to backlog
2. Review quarterly
3. Adopt if time permits
4. Archive if outdated

## Prioritization Matrix

| Impact | Effort | Priority | Action |
|--------|--------|----------|--------|
| High | Low | P0 | Do now |
| High | Medium | P1 | Do this sprint |
| High | High | P1 | Do this sprint (split if needed) |
| Medium | Low | P1 | Do this sprint |
| Medium | Medium | P2 | Do next sprint |
| Medium | High | P2 | Do next sprint (split if needed) |
| Low | Low | P2 | Do next sprint |
| Low | Medium | P3 | Do eventually |
| Low | High | P3 | Do eventually (or reject) |

## Impact Assessment

### High Impact (Score: 3)

**Criteria:**
- Affects >50% of users
- Prevents critical failures
- Improves key metrics >30%
- Reduces costs significantly
- Enables new capabilities

**Examples:**
- Circuit breaker (prevents cascading failures)
- Rate limiting (prevents API bans)
- Caching (reduces costs + improves speed)
- Error tracking (faster debugging)

### Medium Impact (Score: 2)

**Criteria:**
- Affects 20-50% of users
- Improves reliability
- Improves key metrics 10-30%
- Reduces costs moderately
- Enhances existing capabilities

**Examples:**
- Retry logic (handles transient errors)
- Structured logging (easier debugging)
- Type hints (better IDE support)
- API documentation (easier onboarding)

### Low Impact (Score: 1)

**Criteria:**
- Affects <20% of users
- Minor improvements
- Improves key metrics <10%
- Minimal cost reduction
- Cosmetic changes

**Examples:**
- Code comments (readability)
- Alternative algorithm (marginal gain)
- Beta library (experimental)
- Minor refactoring (no functional change)

## Effort Assessment

### Low Effort (Score: 1)

**Criteria:**
- <4 hours total work
- Simple integration
- No breaking changes
- Minimal testing needed
- Clear documentation

**Examples:**
- Add library import
- Copy utility function
- Update configuration
- Add type hints

### Medium Effort (Score: 2)

**Criteria:**
- 4-16 hours total work
- Moderate integration
- Some refactoring needed
- Comprehensive testing required
- Documentation updates

**Examples:**
- Adopt circuit breaker pattern
- Implement retry logic
- Add caching layer
- Refactor error handling

### High Effort (Score: 3)

**Criteria:**
- >16 hours total work
- Complex integration
- Major refactoring needed
- Extensive testing required
- Architecture changes

**Examples:**
- Replace entire API client
- Migrate to new framework
- Rewrite core algorithm
- Change database schema

## Priority Score Calculation

```python
priority_score = (impact * 3) + (urgency * 2) - (effort * 1)

# Impact: 1-3 (low, medium, high)
# Urgency: 1-3 (can wait, should do soon, must do now)
# Effort: 1-3 (low, medium, high)

if priority_score >= 10:
    priority = "P0"  # Critical
elif priority_score >= 7:
    priority = "P1"  # High
elif priority_score >= 4:
    priority = "P2"  # Medium
else:
    priority = "P3"  # Low
```

## Urgency Assessment

### High Urgency (Score: 3)

**Criteria:**
- Security vulnerability
- Production incident
- Breaking API change
- Compliance deadline
- User-facing bug

### Medium Urgency (Score: 2)

**Criteria:**
- Performance degradation
- Reliability issue
- Cost increase
- Technical debt
- User complaint

### Low Urgency (Score: 1)

**Criteria:**
- Nice-to-have feature
- Minor optimization
- Cosmetic change
- Research experiment
- Future-proofing

## Dependency Management

### Blocking Dependencies

**Rule:** P0 tasks block everything else

**Process:**
1. Identify blocking task
2. Pause other work
3. Complete blocker first
4. Resume other work

**Example:**
- P0: Fix security vulnerability
- P1: Add new feature (blocked)
- → Complete P0 first, then P1

### Parallel Work

**Rule:** Independent tasks can run in parallel

**Process:**
1. Identify independent tasks
2. Assign to different learning cycles
3. Execute in parallel
4. Merge results

**Example:**
- P1: Adopt circuit breaker (API client)
- P1: Adopt caching (database layer)
- → Can run in parallel (different areas)

### Sequential Work

**Rule:** Dependent tasks must run sequentially

**Process:**
1. Identify dependencies
2. Order tasks by dependency
3. Execute in sequence
4. Validate each step

**Example:**
- P1: Adopt rate limiting (foundation)
- P2: Adopt token bucket (depends on rate limiting)
- → Must run sequentially

## Capacity Planning

### Learning Cycle Budget

**Time Budget:** 16 hours per 2-week cycle

**Allocation:**
- P0: Unlimited (emergency)
- P1: 8-12 hours (50-75%)
- P2: 4-8 hours (25-50%)
- P3: 0-4 hours (0-25%)

**Example Cycle:**
- P0: 0 hours (no emergencies)
- P1: 10 hours (2 skills)
- P2: 4 hours (1 skill)
- P3: 2 hours (1 skill)
- **Total: 16 hours**

### Skill Budget

**Skills per Cycle:** 3-5 skills

**Allocation:**
- P0: Unlimited (emergency)
- P1: 2-3 skills
- P2: 1-2 skills
- P3: 0-1 skill

**Example Cycle:**
- P0: 0 skills
- P1: 2 skills (circuit breaker, retry logic)
- P2: 1 skill (caching)
- P3: 1 skill (type hints)
- **Total: 4 skills**

## Decision Examples

### Example 1: Circuit Breaker

**Assessment:**
- Impact: High (3) — prevents cascading failures
- Urgency: High (3) — production incidents possible
- Effort: Medium (2) — 8 hours work

**Score:** (3 × 3) + (3 × 2) - (2 × 1) = 13

**Priority:** P0 (Critical) 🔴

**Decision:** Adopt immediately

### Example 2: Type Hints

**Assessment:**
- Impact: Low (1) — improves IDE support
- Urgency: Low (1) — nice-to-have
- Effort: Low (1) — 2 hours work

**Score:** (1 × 3) + (1 × 2) - (1 × 1) = 4

**Priority:** P2 (Medium) 🟡

**Decision:** Do next sprint

### Example 3: New Framework

**Assessment:**
- Impact: Medium (2) — better features
- Urgency: Low (1) — current works fine
- Effort: High (3) — 40 hours work

**Score:** (2 × 3) + (1 × 2) - (3 × 1) = 5

**Priority:** P2 (Medium) 🟡

**Decision:** Do next sprint (or reject if ROI low)

## Review Process

### Weekly Review

**Goal:** Adjust priorities based on new information

**Process:**
1. Review all pending tasks
2. Re-assess impact/urgency/effort
3. Re-calculate priority scores
4. Re-order backlog
5. Communicate changes

### Monthly Review

**Goal:** Validate priority framework effectiveness

**Process:**
1. Analyze completed tasks
2. Compare estimated vs actual effort
3. Measure impact of adoptions
4. Update framework if needed
5. Document learnings

### Quarterly Review

**Goal:** Strategic alignment

**Process:**
1. Review business goals
2. Align priorities with goals
3. Archive outdated tasks
4. Plan next quarter
5. Update framework

## Escalation Process

### When to Escalate

**Criteria:**
- P0 task blocked >24 hours
- P1 task blocked >1 week
- Resource conflict (multiple P0s)
- Unclear priority (tie score)
- Strategic decision needed

**Process:**
1. Document issue
2. Gather context
3. Escalate to user (Misha)
4. Get decision
5. Document rationale
6. Execute decision

## Metrics

### Priority Distribution

**Target:**
- P0: <5% (emergencies rare)
- P1: 40-50% (important work)
- P2: 30-40% (valuable work)
- P3: 10-20% (nice-to-have)

**Current:**
- P0: 0% (0 tasks)
- P1: 100% (1 task)
- P2: 0% (0 tasks)
- P3: 0% (0 tasks)

### Completion Rate

**Target:**
- P0: 100% within 24h
- P1: >90% within 2 weeks
- P2: >80% within 1 month
- P3: >50% within 3 months

**Current:**
- P0: N/A (no P0 tasks)
- P1: 100% (1/1 completed)
- P2: N/A (no P2 tasks)
- P3: N/A (no P3 tasks)

### Effort Accuracy

**Target:** Actual effort within ±20% of estimate

**Current:** 100% accuracy (8h estimated, 8h actual)

---

**Last Updated:** 2026-05-13
**Next Review:** 2026-06-13
