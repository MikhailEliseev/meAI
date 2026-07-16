# Pipeline Performance Optimization Plan

> **Critical Issue:** Pipeline takes 300+ seconds (5+ minutes) and times out before returning results to chat UI.

**Root Cause Analysis:**
- toriclinic.ru: 330.6s elapsed, but **chat timeout is 240s** → user sees nothing
- erasmile.ru: 200.6s elapsed, barely fits in timeout
- Problem: 3 Perplexity prompts → 98 brands → 139 brand resolution attempts → massive Firecrawl enrichment
- **User requirement:** Show 10 competitors (not 5) → enrichment doubles

**Goal:** Reduce pipeline time from 300s+ to **90-150s** (under 180s guaranteed for 10 competitors)

---

## Architecture Overview

Current flow:
```
Stage 0: extract_clinic_profile (Perplexity) ~5-10s
Stage 1: discover_competitors (3× Perplexity) ~90-120s
  → Returns 40-98 brands
Stage 2: resolve_brands_batch (bo.nalog + Firecrawl) ~120-180s
  → Resolves ALL brands (5 concurrent)
  → Level 1: bo.nalog search
  → Level 2: Firecrawl scrape (budget=5, but Level 1 still processes all)
Stage 3: rank_by_revenue (ФНС financials) ~10-20s
  → TOP 10 selected (was 5)
Stage 3.5: enrich_websites_batch (Firecrawl × 10) ~60-100s (was 30-50s for 5)
Stage 3.5c: client audit (Firecrawl × 3) ~15-25s
Stage 4: instagram enrichment (Apify × 10) ~40-60s (was 20-30s for 5)
```

**Total with 10 competitors:** 330-550 seconds (5.5-9 minutes)

**Bottlenecks:**
1. **Stage 1:** 98 brands from Perplexity (3 prompts accumulate too much)
2. **Stage 2:** Processes ALL 98 brands even though only top 10 used
3. **Stage 2:** Semaphore=5 too conservative for bo.nalog
4. **Stage 3.5 + 4:** 10 competitors × enrichment = 2× slower than before

---

## Task 1: Limit Perplexity results to 20 per prompt

**Problem:** Each prompt returns 12-43 brands. Accumulation gives 98 unique brands for small clinic.

**Files:**
- Modify: `AIM/src/aim/services/competitor_matcher_v2.py` lines ~110-140 (Stage 1 accumulation)

- [ ] **Step 1.1: Add TOP_N_PER_PROMPT = 20 constant**

```python
_MAX_BRANDS_PER_PROMPT = 20  # limit each Perplexity prompt result
```

- [ ] **Step 1.2: Truncate each prompt result before deduplication**

Find where `perp_results` is accumulated (after 3 Perplexity calls). Before deduplication:

```python
# Truncate each prompt to top N before merging
perp_results = [brands[:_MAX_BRANDS_PER_PROMPT] for brands in perp_results]
```

**Expected reduction:** 98 brands → 40-50 brands after dedup

**Time saved:** Stage 2 processes 40 instead of 98 → saves ~60-80s

- [ ] **Step 1.3: Deploy and test**

---

## Task 2: Increase bo.nalog concurrency semaphore 5 → 15

**Problem:** `resolve_brands_batch` uses `Semaphore(5)`. For 98 brands: 98/5 = 20 batches × 5s = 100s.

**Files:**
- Modify: `AIM/src/aim/services/brand_resolver.py` line ~470

- [ ] **Step 2.1: Change semaphore from 5 to 15**

```python
# Was: semaphore = asyncio.Semaphore(max_concurrent)  # max_concurrent=5
semaphore = asyncio.Semaphore(15)  # bo.nalog can handle higher concurrency
```

**Expected reduction:** 40 brands / 15 = 3 batches × 5s = 15s (was 40s)

**Time saved:** ~25-30s

- [ ] **Step 2.2: Deploy and test**

---

## Task 3: Add max_brands budget to resolve_brands_batch

**Problem:** Even with Perplexity limit, Stage 2 still resolves all 40 brands. Only top 10 by revenue are used.

**Files:**
- Modify: `AIM/src/aim/services/brand_resolver.py` lines 450-483 (`resolve_brands_batch`)
- Modify: `AIM/src/aim/services/competitor_matcher_v2.py` line ~180 (Stage 2 call)

- [ ] **Step 3.1: Add max_brands parameter to resolve_brands_batch**

```python
async def resolve_brands_batch(
    brand_names: list[str],
    okved_prefix: str = "86.",
    max_concurrent: int = 5,
    max_brands: int = 40,  # NEW: only resolve first N brands (was 30, now 40 for 10 competitors)
) -> list[Optional[ResolvedBrand]]:
    """Resolve brands to INN via ФНС. Only processes first max_brands."""
    brand_names = brand_names[:max_brands]
    # ... rest unchanged
```

- [ ] **Step 3.2: Update call site in competitor_matcher_v2**

```python
resolved = await resolve_brands_batch(all_brands, max_brands=40)
```

**Expected reduction:** Resolve 40 brands instead of 98

**Time saved:** 40/15 = 3 batches × 5s = 15s (was 40s) → saves 25s

- [ ] **Step 3.3: Deploy and test**

---

## Task 4: Add chat timeout warning + async response

**Problem:** Chat timeout is 240s but pipeline takes 300s+ → user sees nothing.

**Files:**
- Modify: `AIM/hermes-v2/app/llm.py` lines ~420-450 (tool execution)
- Modify: `AIM/hermes-v2/app/tools/competitors.py` (proxy tool)

**Option A (Quick):** Return partial results if timeout approaching

- [ ] **Step 4.1: Wrap find_competitors in asyncio.wait_for(timeout=200)**

```python
try:
    result = await asyncio.wait_for(
        http.post(...),
        timeout=200  # leave 40s buffer before chat timeout
    )
except asyncio.TimeoutError:
    return {"error": "Analysis takes longer than expected. Results will be cached for next request."}
```

**Option B (Better):** Background job + cache

- [ ] **Step 4.2: If analysis > 120s, return immediately with "processing" status**
- [ ] **Step 4.3: Store result in cache (Redis/file) by URL hash**
- [ ] **Step 4.4: Next request for same URL returns cached result**

**Time saved:** User gets response (even if "processing") within 120s

- [ ] **Step 4.5: Deploy and test**

---

## Task 5: Cache competitor search results (24h TTL)

**Problem:** Same spec+city combinations repeat (tests, similar clinics).

**Files:**
- Modify: `AIM/src/aim/services/competitor_matcher_v2.py` Stage 1

- [ ] **Step 5.1: Add cache key generation**

```python
import hashlib
cache_key = hashlib.md5(f"{spec}:{city}:{count}".encode()).hexdigest()
cache_file = f"/app/data/cache/competitors_{cache_key}.json"
```

- [ ] **Step 5.2: Check cache before Perplexity**

```python
if os.path.exists(cache_file):
    age = time.time() - os.path.getmtime(cache_file)
    if age < 86400:  # 24h TTL
        with open(cache_file) as f:
            return json.load(f)["brands"]
```

- [ ] **Step 5.3: Write cache after Stage 1**

```python
with open(cache_file, "w") as f:
    json.dump({"brands": all_brands, "timestamp": time.time()}, f)
```

**Time saved:** Repeat requests: 0s for Stage 1 (was 90-120s)

- [ ] **Step 5.4: Deploy and test**

---

## Expected Results

| Before | After (Task 1-3) | After (Task 4-5) |
|--------|------------------|------------------|
| 300-450s | 80-120s | 0s (cached) or 80s |
| Timeout | Success | Success + fast repeat |

**Target:** 90% of requests under 120s, 100% under 180s.

---

## Testing Plan

1. Test toriclinic.ru (was 330s) → should be <120s
2. Test erasmile.ru (was 200s) → should be <90s
3. Test arclinic.ru (was ~150s) → should be <90s
4. Test same clinic twice → second should be <5s (cache)

---

## Post-Implementation

- Monitor logs: `docker logs aim-app | grep "CompetitorMatcherV2 done"`
- Check `elapsed=` time
- If still >120s → investigate specific bottleneck (Firecrawl? Perplexity?)
