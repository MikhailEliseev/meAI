# Phase 19: Competitor Discovery Quality Fixes

> **Goal:** Fix the three critical issues found in batch testing (10 URLs): brand_name garbage from Google Maps, self-match competitors, and missing financial data (90% revenue=None).

**Batch test results (2026-05-26):** 9/10 success, 40 competitors, avg 127s. Only 4/40 have revenue data.

**Root cause:** Google Maps titles are long/descriptive ("Darmed | Косметология Фрунзенская | Лазерная эпиляция, масса"), but DaData enrichment uses `brand_core` = first 2 words = "Darmed |" → garbage search query → no INN match → no rusprofile enrichment → no revenue.

---

## Fix 1: Google Maps Brand Name Cleanup

**File:** `AIM/src/aim/services/apify_google_maps.py`

**What:** Extract clean brand name from GM titles before passing to the pipeline.

**Rules:**
- Text before first `|` or `·` separator → brand_name
- Strip addresses ("Москва, ул. ...", "г. Казань")
- Strip legal forms ("ООО", "ИП") from brand_name
- Keep original title in `legal_name` (for DaData matching by full name)

**Implementation:**
```python
def _clean_gm_brand_name(title: str) -> str:
    """Extract clean brand name from Google Maps title."""
    # Split on common separators, take first meaningful part
    for sep in (" | ", " · ", " • ", " — "):
        if sep in title:
            parts = title.split(sep)
            # First part is usually the brand name
            brand = parts[0].strip()
            # Filter out address-looking parts (contain "ул.", "пр-т", etc.)
            if not _looks_like_address(brand):
                return brand
    
    # No separator — use whole title but clean it
    return _strip_address_suffix(title)

def _looks_like_address(text: str) -> bool:
    """Check if text looks like an address fragment."""
    addr_markers = ["ул.", "улица", "пр-т", "проспект", "д.", "дом", 
                    "г.", "город", "мкр.", "шоссе", "наб.", "пер."]
    text_lower = text.lower()
    return any(m in text_lower for m in addr_markers)
```

---

## Fix 2: Self-Match Filtering

**File:** `AIM/src/aim/services/competitor_matcher.py` (in `find_competitors`)

**What:** Exclude competitors that match the client's own clinic.

**Three detection methods:**
1. **Domain match** — competitor website domain == client domain
2. **Name substring** — client company_name is a substring of competitor name (or vice versa)
3. **INN match** — same INN (should never happen, but safety check)

**Implementation (in `find_competitors`, after step 2):**
```python
# Filter out self-matches
if client.company_name:
    gm_candidates = [
        c for c in gm_candidates
        if not _is_self_match(c, client)
    ]

def _is_self_match(candidate: CompanyProfile, client: ClientProfile) -> bool:
    """Check if candidate is the client's own clinic."""
    # Domain match
    if client.url and candidate.website:
        client_domain = _extract_domain(client.url)
        cand_domain = _extract_domain(candidate.website)
        if client_domain and cand_domain and client_domain == cand_domain:
            return True
    
    # Name match
    if client.company_name:
        client_words = set(client.company_name.lower().split())
        cand_words = set(candidate.legal_name.lower().split())
        if len(client_words & cand_words) >= min(len(client_words), 3):
            return True
    
    # INN match
    if client.inn and candidate.inn and client.inn == candidate.inn:
        return True
    
    return False
```

---

## Fix 3: Better DaData Enrichment Matching

**File:** `AIM/src/aim/services/competitor_matcher.py` (`_enrich_gm_with_dadata`)

**What:** Use cleaned brand_name for DaData search instead of `brand_core` (first 2 words of dirty title).

**Changes:**
1. Use the new cleaned `brand_name` (from Fix 1) for DaData lookup
2. Try multiple search strategies sequentially:
   a. Clean brand name + city
   b. First meaningful word + city
   c. Full title without separators + city
3. Lower name similarity threshold for noisy GM data (0.25 instead of 0.3)

**Implementation:**
```python
async def _enrich_one(c: CompanyProfile) -> CompanyProfile:
    # Use cleaned brand_name (from Fix 1) instead of first 2 words
    search_name = c.brand_name or c.legal_name  # brand_name is now cleaned
    if not search_name:
        return c
    
    # Try multiple search strategies
    for query in _build_search_queries(search_name, client.city):
        results = await self.dadata.find_medical_companies(
            query=query, city=client.city, count=3,
        )
        for r in results:
            if _name_similarity(search_name, r.legal_name) > 0.25:
                # ... merge enrichment
                break
        if c.inn:
            break  # found INN, stop trying
    
    return c
```

---

## Fix 4: Increase rusprofile Enrichment Rate

**File:** `AIM/src/aim/services/competitor_matcher.py` (`_enrich_with_rusprofile`)

**What:** After Fix 3 gives us more INNs, rusprofile will naturally get more data. Add:
1. **Batch logging** — log INN → rusprofile hit rate
2. **Retry on timeout** — rusprofile sometimes slow, retry once

**No major code changes needed** — Fix 1-3 should already 10x the INN discovery rate.

---

## Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Revenue data coverage | 10% (4/40) | 60-80% |
| Self-matches in results | 2/10 URLs | 0/10 |
| Clean brand names | "Darmed \| Космет..." | "Darmed" |
| DaData match rate | ~20% | 60-80% |
| Pipeline time | 127s avg | ~130s (minor increase from retries) |

---

## Implementation Order

1. **Fix 1** — brand_name cleanup (unblocks Fix 3)
2. **Fix 2** — self-match filtering (quick win)
3. **Fix 3** — better DaData matching (depends on Fix 1)
4. **Fix 4** — rusprofile retry/logging (observability)
5. **Re-test** — run batch test on same 10 URLs, compare results
