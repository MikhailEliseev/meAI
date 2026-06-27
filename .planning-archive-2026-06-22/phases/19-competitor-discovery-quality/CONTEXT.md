# Phase 19: Competitor Discovery Quality — Context

## Source: Competitor Matching Validity Analysis (2026-05-23)

Полный аудит пайплайна поиска конкурентов выявил 8 проблем в 3 категориях критичности.

## Pipeline Overview

```
Client URL → service_extractor.py → CompetitorMatcher → API response
                ↓                        ↓
         specialization         _search_candidates()
         city                   _score_candidates()
         services               diversity swap → top-3
```

Scoring: service_overlap (0.25) + specialization_purity (0.15) + location_score (0.15) + data_quality (0.14) + popularity (0.11) + revenue_match (0.10) + visibility (0.10)

## 🔴 CRITICAL Issues

### C1: Specialization Detection — First-Match-Wins
**File:** `AIM/src/aim/services/service_extractor.py:_detect_specialization()` (line 282)
**Problem:** Iterates `_SPECIALIZATIONS` dict in fixed order: стоматология → косметология → многопрофильная → пластическая хирургия → диагностический → офтальмология → педиатрия. First keyword match wins. Многопрофильная клиника со стоматологическим отделением определяется как «стоматология».
**Fix:** Count keyword matches per specialization, pick the one with most matches (dominance-based).

### C2: Competitor Services — Constructed, Not Scraped
**File:** `AIM/src/aim/services/competitor_matcher.py:_candidate_services()` (line 1103-1165)
**Problem:** Competitor services are constructed from: source_specialization hardcoded maps, OKVED→service keyword mapping, company name keyword extraction. Competitor websites are NOT scraped. Service overlap score (25% weight) compares client's REAL scraped services vs competitor's CONSTRUCTED services — apples to oranges.
**Fix:** Add competitor website scraping step OR lower service_overlap weight significantly until real scraping is implemented.

### C3: Service Detection — Pure Substring Matching
**File:** `AIM/src/aim/services/service_extractor.py:_detect_services()` (line 271)
**Problem:** «имплантация» anywhere on page = service detected. False positives: «противопоказания к имплантации», «не используем имплантацию», blog posts, testimonials.
**Fix:** Context-aware extraction — require service mention in positive/service context, exclude negations.

## 🟡 SIGNIFICANT Issues

### S1: Popularity Score Weight Too Low
**File:** `AIM/src/aim/services/competitor_matcher.py:_score_one()` (weights dict)
**Problem:** Popularity (ratings + reviews) only 11% weight. Real patient reviews are the strongest signal of clinic quality and relevance as a competitor.
**Fix:** Raise popularity to 0.18-0.20, lower service_overlap to compensate.

### S2: Service Overlap Weight Too High (compounds C2)
**Problem:** 25% weight on a metric comparing real client services vs constructed competitor services. With C2 unfixed, this metric is unreliable — inflating its weight produces misleading scores.
**Fix:** Lower to 0.10-0.12 until C2 is fixed (real competitor service scraping).

### S3: City Detection — Limited Scope
**File:** `AIM/src/aim/services/service_extractor.py:_detect_city()` (line 302)
**Problem:** Only searches «в Городе» prepositional pattern in first 5000 chars, plus direct city name matches with declined forms. Misses cities in address blocks, Yandex Maps embeds, schema.org markup.
**Fix:** Add JSON-LD/schema.org parsing for city extraction, expand search to full page.

### S4: No `named_competitors` Support
**Files:** `AIM/src/aim/api/competitors.py:FindCompetitorsRequest`, `AIM/hermes/app/tools/find_competitors.py`
**Problem:** API only takes `url` and `count`. Can't pass competitor URLs/names that the client specifically wants to compare against. This is a critical UX gap — clients often know their competitors by name.
**Fix:** Add optional `named_competitors: list[str]` field to FindCompetitorsRequest, implement by-name search + enrichment.

## 🟢 MINOR Issues

### M1: TF-IDF on Tiny Strings
**Problem:** TF-IDF cosine similarity (70% of service_overlap) computed against short constructed strings (5-10 words). TF-IDF needs document-length text to be meaningful. On 5-word strings, it's essentially a keyword overlap with extra math.
**Fix:** Use pure Jaccard until real service lists are available (from competitor website scraping).

## Files to Modify

| File | Changes |
|------|---------|
| `AIM/src/aim/services/service_extractor.py` | C1 specialization, C3 service detection, S3 city detection |
| `AIM/src/aim/services/competitor_matcher.py` | C2 competitor services, S1/S2/M1 scoring weights |
| `AIM/src/aim/api/competitors.py` | S4 named_competitors field |
| `AIM/hermes/app/tools/find_competitors.py` | S4 named_competitors param |

## Success Criteria

1. Specialization detection uses dominance-based approach (not first-match-wins)
2. Service detection filters negation contexts
3. Scoring weights rebalanced: popularity up, service_overlap down
4. `named_competitors` supported in API and Hermes tool
5. City detection uses JSON-LD/schema.org + full page search
6. All existing tests pass, new tests for fixes
7. End-to-end: стоматология «Все Свои» в Москве finds relevant competitors with real financials
