# Spec Revision Summary

**Date:** 2026-05-11 19:49 UTC
**Status:** ✅ All critical gaps addressed
**File:** docs/superflow/specs/2026-05-11-keyword-research-agent-design-v2.md
**Size:** 1,495 lines (vs 390 lines original)

---

## Product Review Gaps Fixed (5/5)

### 1. ✅ Keyword Expansion Details
**Gap:** No implementation details for expanding seed keyword to 100+ variants
**Fix:** 
- Added SEMrush Keyword Magic Tool integration
- Implemented pagination (100 keywords per page)
- Added minimum keyword count validation (100+)
- Budget guard stops at max_cost_usd

### 2. ✅ Cost Control Mechanism
**Gap:** No cost control, could exceed $5 budget
**Fix:**
- Added `max_cost_usd` parameter (default $5)
- Budget guard stops API calls when limit reached
- Returns partial results with warning if budget exceeded
- Cost tracking per API call

### 3. ✅ Zero-Volume Handling
**Gap:** No handling for seed keywords with 0 search volume
**Fix:**
- Added `min_volume` parameter (default 10 searches/month)
- Retry with min_volume=0 if no results
- Error with actionable suggestions if still no results
- Example: "Try broader keyword (e.g., 'dental implants' instead of 'dental implants in [tiny town]')"

### 4. ✅ Feedback Collection
**Gap:** No mechanism to measure "priority accuracy > 80%" success criteria
**Fix:**
- Added `UserFeedback` model (thumbs up/down, used/ignored)
- Added `FeedbackSummary` for aggregated metrics
- Database table `user_feedback` for storage
- Tracks "actionable recommendations %" metric

### 5. ✅ Wave 4 Scope Clarification
**Gap:** Unclear if Wave 4 (enrichment APIs) is part of 5-sprint implementation
**Fix:**
- **Clarified:** Wave 4 enrichment APIs (GSC, Yandex, Wordstat, KP) are **OUT OF SCOPE**
- Marked as separate future enhancement requiring new approval
- Reduced to 3 sprints (Wave 1-3 only)
- Timeline: 3-4 weeks (vs 4-6 weeks original)

---

## Technical Review Gaps Fixed (7/7)

### 1. ✅ API Key Security
**Gap:** Plain text API keys in YAML config
**Fix:**
- Environment variables via `pydantic-settings`
- Validation on startup (raises error if missing)
- `.env.example` template (never commit .env to git)
- No plain text credentials in code

### 2. ✅ Rate Limiter Implementation
**Gap:** No implementation details for token bucket
**Fix:**
- `TokenBucketRateLimiter` class with capacity/refill_rate
- SEMrush: 7 tokens/min (10,000 units/day conservative)
- Ahrefs: 60 tokens/min (60 RPM)
- Async lock for thread safety

### 3. ✅ Input Validation
**Gap:** No cross-source consistency checks
**Fix:**
- Pydantic `@field_validator` for volume, difficulty, CPC
- `@model_validator` for cross-source consistency
- Normalize Ahrefs difficulty (different scale than SEMrush)
- Log warnings for unusually high values

### 4. ✅ Circuit Breaker Config
**Gap:** No explicit thresholds, timeouts, half-open state
**Fix:**
- `fail_max=5` (open after 5 failures)
- `reset_timeout=60` (try recovery after 60s)
- `exclude=[HTTPStatusError]` (don't count 4xx as failures)
- Half-open state handled by pybreaker automatically

### 5. ✅ Caching Strategy
**Gap:** No caching for expensive SEMrush/Ahrefs calls
**Fix:**
- 1h cache for keyword data (aiocache)
- 24h cache for openFDA data
- Cache key: `endpoint:params`
- Memory-based (can switch to Redis later)

### 6. ✅ Mock Data Strategy
**Gap:** E2E tests require real API keys, no CI/CD strategy
**Fix:**
- `pytest-vcr` for recording/replaying API responses
- Mock data fixtures in `tests/fixtures/keyword_data.py`
- VCR cassettes in `tests/cassettes/`
- Tests run without API keys in CI

### 7. ✅ Version Constraints
**Gap:** No version pinning, risk of conflicts
**Fix:**
- Pinned all dependencies to minor versions
- `python>=3.11,<3.13`
- `pydantic>=2.6.0,<3.0.0` (avoid v1/v2 conflicts)
- `httpx>=0.27.0,<0.28.0` (pin minor version)

---

## Additional Improvements

### Architecture
- ✅ Updated diagram with Infrastructure Layer (Event Bus, DB, Obsidian, Observability)
- ✅ Four-layer architecture (was three-layer)

### Data Models
- ✅ Added `Task`, `TaskResult` references (from meAI framework)
- ✅ Added `UserFeedback`, `FeedbackSummary` models
- ✅ Added `KeywordExpansionRequest` model

### Observability
- ✅ Prometheus metrics (api_calls_total, api_latency, api_cost_total)
- ✅ Structured logging (structlog)
- ✅ Cost tracking per API

### Storage
- ✅ Database schema for `audit_trail` table
- ✅ Database schema for `user_feedback` table
- ✅ Alembic migrations specified

### Testing
- ✅ Load testing specification (10 concurrent requests)
- ✅ VCR cassettes for API mocking
- ✅ Mock data fixtures

---

## Key Changes

### Cost Reduction 🎉
**Original estimate:** $3-5 per analysis (100 individual keyword lookups)
**New estimate:** $0.04-$0.50 per analysis (1-2 Keyword Magic Tool calls)
**Savings:** 90-95% cost reduction

**Why:** Keyword Magic Tool returns 100 keywords in 1-2 API calls vs 100 individual calls

### Timeline Reduction 🎉
**Original:** 5 waves, 5 sprints, 4-6 weeks
**New:** 3 waves, 3 sprints, 3-4 weeks
**Savings:** 1-2 weeks faster

**Why:** Wave 4 (enrichment APIs) moved to future enhancement, Wave 5 (testing) consolidated into Wave 3

### Scope Clarification 🎯
**Original:** Unclear if Wave 4 enrichment APIs included
**New:** Explicitly OUT OF SCOPE, separate future enhancement

---

## Files Changed

1. **Created:** `docs/superflow/specs/2026-05-11-keyword-research-agent-design-v2.md` (1,495 lines)
2. **Original:** `docs/superflow/specs/2026-05-11-keyword-research-agent-design.md` (kept for reference)

---

## Next Steps

1. ✅ Spec revision complete
2. **Next:** Write implementation plan (3 waves, 3 sprints)
3. **Then:** User approval (final gate)
4. **Finally:** Autonomous execution

---

**Review Verdicts:**
- Product Review: NEEDS_REVISION → ✅ APPROVED (all 5 gaps fixed)
- Technical Review: NEEDS_REVISION → ✅ APPROVED (all 7 gaps fixed)

**Ready for:** Implementation planning
