---
phase: 31-html-report-redesign
reviewed: 2026-06-16T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - AIM/hermes/app/tools/generate_html_report.py
  - AIM/hermes/app/tools/registry.py
  - AIM/tests/unit/test_html_report.py
findings:
  blocker: 1
  warning: 5
  info: 6
  total: 12
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-06-16
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed 3 files in the HTML report redesign phase: the main report generator (1632 lines), the tool registry stub (31 lines), and the test suite (395 lines). The code is well-structured overall with thorough graceful-omission patterns and good XSS protection via the `_esc()` helper.

However, 1 blocker-level data-access inconsistency was found that would silently drop the "steal-worthy tactics" pillar from the strategy section. 5 warnings cover potential TypeError crashes from joining non-string list items, conflicting section IDs from dead code, a looser count-formatting check, and the single-quote gap in the HTML escaping function. 6 informational items note hardcoded URLs, unreadable single-line HTML output, the enormous single-file module, duplicate review-rendering logic, and magic numbers.

## Blocker Issues

### BL-01: `_build_strategy` and `_build_ci_gaps` use inconsistent data paths for steal-worthy tactics

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 484 vs 1281

**Issue:** `_build_ci_gaps` (line 484) reads steal-worthy tactics from `ci_analysis.best_practices.steal_worthy_tactics`:
```python
best_practices = ci.get("best_practices", {}) or {}
steal_worthy = best_practices.get("steal_worthy_tactics", [])
```

But `_build_strategy` (line 1281) reads them from `ci_analysis.steal_worthy` directly:
```python
steal_worthy = ci.get("steal_worthy", [])
```

If the data source writes steal-worthy tactics under `best_practices.steal_worthy_tactics` (the path `_load_session_data` would produce from a `ci-analysis.json` file), then `_build_strategy` will silently find `[]` and skip rendering the "04 — Белые поля" strategy pillar entirely. The opposite scenario (data written at `ci_analysis.steal_worthy`) would cause `_build_ci_gaps` to skip its steal-worthy section.

**Fix:** Pick one canonical path and use it consistently. The `best_practices` nesting is the more structured choice:
```python
# In _build_strategy, replace line 1281:
best_practices = ci.get("best_practices", {}) or {}
steal_worthy = best_practices.get("steal_worthy_tactics", [])
```

## Warnings

### WR-01: `_build_competitors` can raise `TypeError` when `services` list contains non-strings

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 419-421

**Issue:** When `comp.get("services")` is a list, the code does `", ".join(services[:5])`. If any item in the list is not a string (e.g., a dict like `{"name": "Терапия"}`), `str.join()` raises `TypeError`, crashing the entire report generation.

**Fix:** Force string conversion on each item:
```python
if isinstance(services, list):
    services = ", ".join(str(s) for s in services[:5])
```

### WR-02: `_build_exec_summary` is dead code with conflicting section ID `market`

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 350-403

**Issue:** `_build_exec_summary` is defined and exported (imported in tests) but is **never called** from `_build_html` (see lines 1401-1419). Its section ID is `market` (line 395), which would collide with `_build_market`'s `<section id="market">` (line 973) if someone accidentally adds it back to the `sections` list. Two elements with the same `id` break HTML semantics and anchor-based navigation.

This function was superseded by `_build_about` (see comment on line 1405: "Always (merges exec_summary + financials)").

**Fix:** Either delete `_build_exec_summary` entirely, or rename its section ID to `exec-summary` if it may be re-added later. Update the test file to remove/rename the corresponding test class.

### WR-03: `_build_presence` uses a looser count-formatting condition than `_build_reviews`

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 1226-1231 (presence) vs 678-683 (reviews)

**Issue:** `_build_reviews` (line 680) uses:
```python
elif count_str.isdigit() or (count_str.startswith("~") and count_str[1:].isdigit()):
```
which requires digits after `~`. But `_build_presence` (line 1228) uses:
```python
elif count_str.startswith("~") or count_str.isdigit() or (count_str.replace(",", "").isdigit()):
```
which accepts `~` even when NOT followed by digits (e.g., `~abc`). A count value like `"~no_data"` would be formatted as `"~no_data отзывов"` instead of falling through to the raw-string else branch.

**Fix:** Align `_build_presence` with `_build_reviews`:
```python
elif count_str.isdigit() or (count_str.startswith("~") and count_str[1:].isdigit()) or (count_str.replace(",", "").isdigit()):
```

### WR-04: `_esc()` does not escape single-quote character

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Line:** 166

**Issue:** The `_esc` function escapes `&`, `<`, `>`, and `"` but not `'` (single quote). While all current HTML attributes use double quotes, any future attribute using single quotes would be vulnerable to injection. This is a defense-in-depth gap — a single-quoted attribute added during maintenance would silently introduce an XSS vector.

**Fix:** Add `'` escaping:
```python
return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
```

### WR-05: Theme toggle button uses emoji character without contrast guarantee

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Line:** 345

**Issue:** The theme toggle uses the emoji character `🌓` as its only visual element. Emoji rendering varies wildly across platforms — it may be invisible on some browsers or fail to convey "toggle theme" to screen readers. There is no `aria-label` fallback text.

**Fix:** Add `aria-label` (partially done — it IS present on the button: `aria-label="Toggle theme"`). The emoji is acceptable as a decorative element with the aria-label present. However, consider adding a text label or SVG icon for consistency:
```html
<button class="theme-toggle" onclick="..." aria-label="Toggle theme">
  <span aria-hidden="true">🌓</span>
</button>
```

## Info

### IN-01: Hardcoded URLs should be module-level constants

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 783, 1349, 1393 (Telegram link), 1511 (iamaim.ru)

**Issue:** The Telegram bot link `https://t.me/aim_hermes_bot` appears at 3 separate HTML generation sites, and the WordPress URL `https://iamaim.ru/` is hardcoded. Any rebranding or domain change requires hunting through the code.

**Fix:** Define constants at module level:
```python
AIM_TELEGRAM_URL = os.getenv("AIM_TELEGRAM_URL", "https://t.me/aim_hermes_bot")
AIM_SITE_URL = os.getenv("AIM_SITE_URL", "https://iamaim.ru")
```

### IN-02: `.replace("\n", "")` produces unreadable single-line HTML

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Line:** 1463

**Issue:** `_build_html` strips all newlines from the final output with `.replace("\n", "")`. The generated HTML delivered to WordPress is a single line of approximately 15,000-25,000 characters, making it impossible to debug or inspect with browser developer tools.

**Fix:** If the newline stripping is intentional to avoid extra spacing in WordPress post content, do a minimal whitespace collapse instead:
```python
# Collapse runs of whitespace, but keep structural readability
import re
html = re.sub(r'\n\s*\n', '\n', html)  # Collapse blank lines only
```

### IN-03: Enormous single-file module (1632 lines, ~80KB)

**File:** `AIM/hermes/app/tools/generate_html_report.py`

**Issue:** One file contains CSS (~130 lines), a WordPress database publisher (~60 lines), 16 section builders (~1100 lines), data loading, and tool registration. Each concern should be in its own module for maintainability and testability.

**Fix:** Split into:
- `tools/html_report/css.py` — `AIM_DESIGN_CSS`
- `tools/html_report/sections/` — one file per section builder
- `tools/html_report/publisher.py` — `_publish_to_wordpress`
- `tools/html_report/assembly.py` — `_build_html`, `handle_generate_html_report`, registry call

### IN-04: CSS embedded as a Python string literal — no linting or syntax highlighting

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 33-158

**Issue:** 125 lines of minified CSS stored as a Python `"""..."""` string. IDE tooling cannot validate or highlight this CSS. Any syntax error in the CSS will only be discovered at runtime when a report is generated.

**Fix:** Move `AIM_DESIGN_CSS` to a standalone `.css` file and load it at module import time:
```python
import os
_CSS_PATH = os.path.join(os.path.dirname(__file__), "aim_design.css")
with open(_CSS_PATH, "r") as f:
    AIM_DESIGN_CSS = f.read()
```

### IN-05: Duplicate review-platform rendering logic in `_build_reviews` and `_build_presence`

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 657-700 and 1206-1272

**Issue:** Both `_build_reviews` and `_build_presence` independently render review platform cards from the same `reviews_data.platforms` source, but with slightly different HTML structure. When both section builders are active in the same report (as they are in `_build_html`), review data is displayed twice with subtly different formatting. This is both code duplication and a potential UX confusion.

**Fix:** Extract a shared `_build_review_cards(platforms)` helper and call it from both sections, or decide which section owns review rendering and remove the duplicate.

### IN-06: Magic numbers throughout scoring and formatting logic

**File:** `AIM/hermes/app/tools/generate_html_report.py`
**Lines:** 205-208 (score thresholds: 80, 50), 421 (services limit: 5), 452 (strengths limit: 3), 1491 (slug retry max: 10), 1483 (connect_timeout: 5)

**Issue:** Thresholds and limits are inline literals. Changing the "good" SEO score threshold from 80 to 75 would require finding every occurrence.

**Fix:** Define module-level constants:
```python
SCORE_THRESHOLD_GREEN = 80
SCORE_THRESHOLD_YELLOW = 50
MAX_SERVICES_DISPLAY = 5
MAX_STRENGTHS_DISPLAY = 3
MAX_SLUG_RETRIES = 10
WP_CONNECT_TIMEOUT = 5
```

---

_Reviewed: 2026-06-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
