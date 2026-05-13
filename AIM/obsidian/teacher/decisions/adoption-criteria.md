---
type: criteria
date: 2026-05-13
status: active
---

# Skill Adoption Criteria

## Overview

This document defines **when and why** Teacher Agent adopts a skill from external sources. All adoption decisions must pass these criteria.

## Scoring Framework

### Multi-Dimensional Scoring (0-100 scale)

Each skill evaluated across 4 dimensions:

#### 1. Quality (Weight: 40%)

**Code Quality (50%):**
- Cyclomatic complexity <10 per function
- No code smells (duplicates, long methods, god classes)
- Type hints coverage >80%
- Docstrings for all public APIs
- Clean architecture (separation of concerns)

**Test Coverage (30%):**
- Unit tests >80% coverage
- Integration tests present
- Edge cases covered
- Mocks used appropriately
- CI/CD pipeline exists

**Documentation (20%):**
- README with examples
- API documentation
- Architecture diagrams
- Changelog maintained
- Contributing guidelines

**Scoring:**
- 90-100: Excellent (production-ready)
- 70-89: Good (minor improvements needed)
- 50-69: Fair (significant work required)
- <50: Poor (reject)

#### 2. Completeness (Weight: 25%)

**Feature Coverage (60%):**
- All core features implemented
- Error handling comprehensive
- Edge cases handled
- Configuration flexible
- Extensibility considered

**Dependencies (20%):**
- Minimal external dependencies
- Dependencies well-maintained
- No security vulnerabilities
- License compatible (MIT, Apache, BSD)

**Integration (20%):**
- Easy to integrate
- Clear API surface
- No breaking changes
- Backward compatible

**Scoring:**
- 90-100: Complete (ready to use)
- 70-89: Mostly complete (minor gaps)
- 50-69: Incomplete (missing features)
- <50: Very incomplete (reject)

#### 3. Maintainability (Weight: 20%)

**Community Health (50%):**
- GitHub stars >100
- Active maintenance (commits in last 3 months)
- Issues resolved quickly (<7 days median)
- PRs reviewed and merged
- Contributors >5

**Code Health (30%):**
- Consistent style (follows PEP 8)
- Modular design
- Low coupling, high cohesion
- No technical debt
- Refactoring history

**Longevity (20%):**
- Project age >1 year
- Stable release (v1.0+)
- Semantic versioning
- Deprecation policy
- Migration guides

**Scoring:**
- 90-100: Highly maintainable
- 70-89: Maintainable
- 50-69: Questionable
- <50: Unmaintainable (reject)

#### 4. Performance (Weight: 15%)

**Efficiency (60%):**
- Time complexity optimal
- Space complexity reasonable
- No memory leaks
- Async/await where appropriate
- Benchmarks provided

**Scalability (30%):**
- Handles high load
- Horizontal scaling possible
- Resource usage predictable
- Bottlenecks identified

**Optimization (10%):**
- Caching implemented
- Database queries optimized
- Network calls minimized
- Profiling done

**Scoring:**
- 90-100: Highly optimized
- 70-89: Good performance
- 50-69: Acceptable
- <50: Poor performance (reject)

### Overall Score Calculation

```python
overall_score = (
    quality * 0.40 +
    completeness * 0.25 +
    maintainability * 0.20 +
    performance * 0.15
)
```

## Adoption Thresholds

### Minimum Scores

- **Overall:** ≥70/100 (required)
- **Quality:** ≥60/100 (required)
- **Completeness:** ≥50/100 (required)
- **Maintainability:** ≥50/100 (required)
- **Performance:** ≥40/100 (optional, can be improved)

### Priority Levels

**🔴 CRITICAL (adopt immediately):**
- Security vulnerability fixed
- Breaking API change (must adapt)
- Overall score ≥90/100
- Performance improvement >50%
- New algorithm (proven better)

**🟡 HIGH (plan for next sprint):**
- Overall score 80-89/100
- Performance improvement 20-50%
- New feature (high user value)
- Code quality improvement
- Better error handling

**🟢 LOW (backlog):**
- Overall score 70-79/100
- Performance improvement <20%
- Optional feature
- Refactoring (no functional change)
- Documentation improvement

**❌ REJECT:**
- Overall score <70/100
- Any dimension <minimum threshold
- License incompatible
- Security vulnerabilities
- Unmaintained (no commits >6 months)

## Decision Matrix

| Dimension | Min Score | Weight | Critical If |
|-----------|-----------|--------|-------------|
| Quality | 60 | 40% | <50 (reject) |
| Completeness | 50 | 25% | <40 (reject) |
| Maintainability | 50 | 20% | <40 (reject) |
| Performance | 40 | 15% | <30 (review) |

## Special Cases

### 1. Security-Critical Skills

**Higher thresholds:**
- Quality ≥80/100
- Test coverage ≥90%
- Security audit required
- Manual code review mandatory

**Examples:**
- Authentication/authorization
- Encryption/decryption
- API key management
- Data validation

### 2. Performance-Critical Skills

**Higher thresholds:**
- Performance ≥70/100
- Benchmarks required
- Load testing mandatory
- Profiling results needed

**Examples:**
- Rate limiting
- Caching
- Database queries
- API clients

### 3. Experimental Skills

**Lower thresholds (with caution):**
- Overall ≥60/100
- Sandbox testing required
- Feature flag deployment
- Rollback plan mandatory

**Examples:**
- New algorithms (unproven)
- Beta libraries
- Cutting-edge patterns
- Research implementations

## Gap Analysis

### When to Adopt

**Adopt if:**
1. External skill scores higher than ours (gap >10 points)
2. External skill has features we lack
3. External skill fixes our known issues
4. External skill improves performance significantly (>20%)
5. External skill reduces complexity

**Keep ours if:**
1. Our score ≥ external score
2. Our implementation more maintainable
3. External skill adds unnecessary complexity
4. External skill has incompatible dependencies
5. Migration cost > benefit

**Improve ours if:**
1. Gap is small (<10 points)
2. External skill has specific good patterns
3. We can cherry-pick improvements
4. Migration cost too high
5. Our architecture better fits our needs

### Gap Calculation

```python
gap_score = external_score - our_score

if gap_score > 10:
    recommendation = "adopt"
elif gap_score > 0:
    recommendation = "improve"  # cherry-pick patterns
else:
    recommendation = "keep_ours"
```

## Cost-Benefit Analysis

### Adoption Costs

**Development:**
- Code adaptation time (hours)
- Testing time (hours)
- Documentation time (hours)
- Review time (hours)

**Risk:**
- Breaking changes probability
- Rollback complexity
- Learning curve
- Technical debt

**Maintenance:**
- Dependency updates
- Security patches
- Bug fixes
- Support burden

### Expected Benefits

**Performance:**
- Speed improvement (%)
- Resource reduction (%)
- Scalability increase (%)

**Quality:**
- Bug reduction (%)
- Test coverage increase (%)
- Code complexity reduction (%)

**Features:**
- New capabilities
- Better error handling
- Improved UX

### ROI Calculation

```python
roi = (expected_benefits - adoption_costs) / adoption_costs

if roi > 2.0:
    priority = "CRITICAL"
elif roi > 1.0:
    priority = "HIGH"
elif roi > 0.5:
    priority = "LOW"
else:
    priority = "REJECT"
```

## Validation Process

### Pre-Adoption Checklist

- [ ] Overall score ≥70/100
- [ ] All dimension minimums met
- [ ] License compatible (MIT/Apache/BSD)
- [ ] No security vulnerabilities
- [ ] Dependencies maintained
- [ ] Tests pass locally
- [ ] Documentation reviewed
- [ ] Code adapted to our structure
- [ ] Integration plan created
- [ ] Rollback plan prepared

### Post-Adoption Validation

- [ ] All tests pass (ours + new)
- [ ] Performance benchmarks run
- [ ] No regressions detected
- [ ] Documentation updated
- [ ] Team trained (if needed)
- [ ] Monitoring configured
- [ ] Adoption report generated

## Examples

### Example 1: Circuit Breaker (ADOPTED ✅)

**Scores:**
- Quality: 85/100 (excellent code, good tests)
- Completeness: 90/100 (all features, good docs)
- Maintainability: 80/100 (active repo, 635 stars)
- Performance: 85/100 (efficient, benchmarked)
- **Overall: 85.0/100** ✅

**Gap Analysis:**
- Our implementation: None (missing feature)
- Gap: +85 points
- **Recommendation: ADOPT** 🔴

**ROI:**
- Cost: 2 hours (adaptation + testing)
- Benefit: Prevents cascading failures (high value)
- **ROI: 10x** (critical feature)

**Decision: ADOPTED** ✅

### Example 2: Rate Limiter (HYPOTHETICAL)

**Scores:**
- Quality: 75/100 (good code, some tests)
- Completeness: 70/100 (core features only)
- Maintainability: 65/100 (small community)
- Performance: 80/100 (efficient)
- **Overall: 72.5/100** ✅

**Gap Analysis:**
- Our implementation: 70/100
- Gap: +2.5 points
- **Recommendation: IMPROVE** 🟡

**ROI:**
- Cost: 4 hours (full replacement)
- Benefit: Marginal improvement
- **ROI: 0.5x** (not worth full replacement)

**Decision: CHERRY-PICK** (take token bucket algorithm only)

### Example 3: Caching Library (HYPOTHETICAL)

**Scores:**
- Quality: 55/100 (poor tests)
- Completeness: 60/100 (missing features)
- Maintainability: 45/100 (unmaintained)
- Performance: 70/100 (fast but buggy)
- **Overall: 56.5/100** ❌

**Gap Analysis:**
- Our implementation: 75/100
- Gap: -18.5 points
- **Recommendation: KEEP OURS** ✅

**Decision: REJECTED** ❌

## Review Schedule

- **Weekly:** Review pending adoptions
- **Monthly:** Audit adoption decisions
- **Quarterly:** Update criteria based on learnings

---

**Last Updated:** 2026-05-13
**Next Review:** 2026-08-13
