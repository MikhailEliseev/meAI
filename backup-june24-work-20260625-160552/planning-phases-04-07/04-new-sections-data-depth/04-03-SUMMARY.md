---
phase: 4
plan: 04-03
subsystem: hermes-tools
tags: [forums, media, new-tools, tool-handlers, perplexity, firecrawl, sec-05, dat-02]
requires:
  - engine.py:_TOOL_HANDLERS (24 entries from Phase 3)
  - PERPLEXITY_API_KEY, FIRECRAWL_API_KEY env vars
provides:
  - "run_forum_pains — patient fears from 4 review platforms via Perplexity"
  - "run_media_urls — 5-СМИ targeted URL search via firecrawl+perplexity"
  - "_TOOL_HANDLERS 26 entries (was 24)"
affects:
  - "AIM/hermes/app/pipeline/engine.py (_TOOL_HANDLERS dict)"
  - "LLM tool catalog (aim-operations toolset grows by 2)"
tech-stack:
  added: []
  patterns:
    - "Perplexity sonar-pro with structured step-by-step prompt (mirror run_review_platforms)"
    - "firecrawl_search → perplexity_search fallback chain (per D-16)"
    - "asyncio.gather for parallel 5-СМИ search"
    - "Module-level regex parser for free-text LLM response"
    - "Honest reporting: pr_needed flag when 0 mentions (per D-18)"
key-files:
  created:
    - AIM/hermes/app/tools/run_forum_pains.py (381 lines)
    - AIM/hermes/app/tools/run_media_urls.py (429 lines)
  modified:
    - AIM/hermes/app/pipeline/engine.py (+3 lines — 2 dict entries + 1 comment)
decisions:
  - "Firecrawl invoked via existing handle_firecrawl_search wrapper (not direct SDK) — avoids new pip dependency + uses key-bank rotation"
  - "Perplexity fallback parses URLs from free-text response via regex (not structured JSON) — Perplexity doesn't always honor JSON-mode; line-based parse is robust"
  - "_extract_fears regex accepts dash variants —, –, - (em-dash, en-dash, hyphen) because LLMs use any of them"
  - "Fear name deduplication via lowercase+normalize key prevents «Больно» + «больно» appearing as 2 separate fears"
metrics:
  duration: "3 min"
  completed: "2026-06-24T00:15:35Z"
  tasks: 3
  files: 3
requirements: [SEC-05, DAT-02]
commits:
  - "c210404: feat(04-03): add run_forum_pains tool — patient fears extractor (SEC-05)"
  - "f2ff43c: feat(04-03): add run_media_urls tool — 5-СМИ targeted search (DAT-02)"
  - "8b24eed: chore(04-03): register run_forum_pains + run_media_urls in _TOOL_HANDLERS"
---

# Phase 4 Plan 04-03: Create run_forum_pains + run_media_urls Tools Summary

Patient fears extractor (4 review platforms + Perplexity) and 5-СМИ URL search (Forbes/RBC/Vademecum/Kommersant/ТАСС) with firecrawl+perplexity fallback chain — wired into PipelineEngine `_TOOL_HANDLERS` (24 → 26 entries).

## What Was Built

### 1. `run_forum_pains.py` (NEW — 381 lines)

Perplexity-based scraper for 4 patient review platforms per D-10. Per D-11, extracts top-5 patient fears from review TEXTS (not star ratings) with mention counts.

**FORUM_SOURCES** (4 entries with weights):
| Platform | Domain | Weight |
|----------|--------|--------|
| ПроДокторов | prodoctorov.ru | 0.35 |
| Otzovik | otzovik.com | 0.25 |
| IRecommend | irecommend.ru | 0.20 |
| Woman.ru | woman.ru | 0.20 |

**Output shape:**
```python
{
    "clinic": "Начало",
    "city": "Ростов-на-Дону",
    "sources_checked": 4,
    "forum_sources": ["ПроДокторов", "Otzovik", "IRecommend", "Woman.ru"],
    "patient_fears_hint": [
        {"fear": "Больно", "mention_count": 47, "context": "..."},
        ...
    ],
    "fears_found": 5,
    "raw_analysis": "...",
    "source": "perplexity (sonar-pro)",
    "searched_at": "2026-06-24T...",
}
```

**`_extract_fears` regex pattern:**
```python
_FEAR_PATTERN = re.compile(
    r"([А-Яа-яЁё][А-Яа-яЁё\s\-]{2,60}?)\s*[—–-]\s*(\d+)\s*упоминан",
    re.IGNORECASE,
)
```
Accepts em-dash (—), en-dash (–), and hyphen (-) separators. Filters out «Топ-5 страхов» section headers. Dedup via lowercase key. Returns up to 5 sorted by `mention_count` desc.

**Fallback chain:** Perplexity sonar-pro (web search) → DeepSeek via OMNIROUTE (no web search).

**Verified:** test input parses «Больно — 47 упоминаний из 120 отзывов» correctly → `{"fear": "Больно", "mention_count": 47}` first in sorted output.

### 2. `run_media_urls.py` (NEW — 429 lines)

Site-restricted search across 5 specific Russian media outlets per D-15. Uses firecrawl with perplexity fallback per D-16. Returns simple list of {source, title, url, date} per D-17 (not card-grid). Sets `pr_needed=True` when 0 mentions per D-18.

**TARGET_MEDIA** (5 outlets):
| Outlet | Domain |
|--------|--------|
| Forbes | forbes.ru |
| RBC | rbc.ru |
| Vademecum | vademec.ru |
| Kommersant | kommersant.ru |
| ТАСС | tass.ru |

**Search flow per source (parallel via `asyncio.gather`):**
1. Build query: `f'"{clinic_name}" site:{domain}'`
2. If `USE_FIRECRAWL`: call `handle_firecrawl_search(query, limit=5)` from existing `app.tools.firecrawl_web` — uses key-bank rotation, no new pip dependency
3. If firecrawl returns 0 results OR `USE_FIRECRAWL=False`: call Perplexity with same site-restricted query; parse URLs/titles/dates from free-text response via regex
4. Aggregate into `mentions_by_source` (5 entries) + `all_mentions` (flat list for HTML rendering)

**Output shape:**
```python
{
    "clinic": "Начало",
    "total_mentions": 3,
    "media_with_mentions": 2,
    "media_total": 5,
    "mentions_by_source": [
        {"source": "Forbes", "domain": "forbes.ru", "mentions_found": 1, "mentions": [...]},
        {"source": "RBC", "domain": "rbc.ru", "mentions_found": 2, "mentions": [...]},
        {"source": "Vademecum", "domain": "vademec.ru", "mentions_found": 0, "mentions": []},
        {"source": "Kommersant", "domain": "kommersant.ru", "mentions_found": 0, "mentions": []},
        {"source": "ТАСС", "domain": "tass.ru", "mentions_found": 0, "mentions": []},
    ],
    "all_mentions": [...],
    "source": "firecrawl" | "perplexity (fallback)" | "mixed" | "none",
    "searched_at": "2026-06-24T...",
    "pr_needed": false,  # D-18: True when total_mentions == 0
}
```

**`_parse_perplexity_results` regex pattern:**
```python
_URL_PATTERN = re.compile(r'https?://[^\s<>"\)\]\']+')
date_re = re.compile(r'(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}|\d{4}-\d{2}-\d{2})')
```
Per-line URL extraction, dedup by URL, title = text before URL on same line, date = first DD.MM.YYYY or YYYY-MM-DD match.

**Verified:** test input parses 2 URLs with dates correctly (Forbes + RBC). «Не найдено» response → empty list.

### 3. `engine.py:_TOOL_HANDLERS` (MODIFIED — 24 → 26 entries)

Added 2 entries after Phase 3 Instagram tools, before closing brace:
```python
# ── Phase 4 / SEC-05 + DAT-02: Forum pains + Media URLs ────────
"run_forum_pains":         ("app.tools.run_forum_pains",        "handle_run_forum_pains"),
"run_media_urls":          ("app.tools.run_media_urls",         "handle_run_media_urls"),
```

Existing 24 entries unchanged. Verified via AST: keys `[..., scrapy_crawl, run_instagram_content, find_doctor_handles, run_forum_pains, run_media_urls]` — placement correct.

## Deviations from Plan

None. Plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| run_forum_pains.py AST parse | OK |
| run_forum_pains.py _extract_fears parses test input | OK (5 fears, sorted desc, «Больно» first at 47) |
| run_media_urls.py AST parse | OK |
| run_media_urls.py TARGET_MEDIA = 5 outlets | OK (Forbes, RBC, Vademecum, Kommersant, ТАСС) |
| run_media_urls.py _parse_perplexity_results parses 2 URLs+dates | OK |
| run_media_urls.py pr_needed flag present | OK |
| engine.py _TOOL_HANDLERS = 26 entries | OK (verified via AST) |
| Both tools use `from tools.registry import registry` (same as run_smi_mentions) | OK |
| Registry.register calls present with `aim-operations` toolset | OK |

**Local-env limitation (not a bug):** `_get_handler()` cannot resolve handlers locally because `tools` (hermes-agent package) isn't pip-installed outside Docker. The EXISTING `run_smi_mentions` fails the same way — confirms this is an env issue, not a code defect. Both new tools follow the production pattern; they will resolve inside the `aim-hermes` container.

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-04-03-T (Tampering — wrong search results) | D-18 honest block when 0 results; Perplexity cross-references multiple platforms |
| T-04-03-D (DoS — 5 parallel firecrawl searches) | asyncio.gather with return_exceptions=True; 60s timeout per call; 10-min cache prevents repeats |
| T-04-03-S/R/I/E/SC | accept — existing patterns, no new secrets/supply-chain |

## Self-Check: PASSED

- All 3 files exist on disk (run_forum_pains.py, run_media_urls.py, engine.py)
- All 3 commits found in git log (c210404, f2ff43c, 8b24eed)
- engine.py `_TOOL_HANDLERS` has exactly 26 entries with both `run_forum_pains` and `run_media_urls` (AST-verified)
- SUMMARY.md exists at expected path
