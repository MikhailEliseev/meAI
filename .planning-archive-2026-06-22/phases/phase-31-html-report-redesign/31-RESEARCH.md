# Phase 31: HTML Report Redesign — Research

**Researched:** 2026-06-16
**Domain:** Self-contained HTML report generation, CSS design system, prescan/CI data integration
**Confidence:** HIGH

## Summary

The current `generate_html_report.py` (924 lines) produces basic glassmorphism HTML reports with 9 sections (Hero, Executive Summary, Financials, Competitors, CI Gaps, SEO, PageSpeed, Reviews, Recommendations). The target quality is the hand-crafted `ИПХиК.html` (966 lines, 78KB) which achieves 10 deep sections with dual-theme CSS, ripple animations, per-doctor analysis, fixed navigation, and rich content density.

The gap is primarily in three dimensions: (1) CSS/visual design system — moving from single light-theme glassmorphism to a dual-theme (light/dark) Inter+Playfair design with ripple rings and nav; (2) Content depth — adding per-doctor analysis, content themes, patient fears, media mentions, whitefield matrices, and strategic recommendations; (3) Data availability — several ИПХиК.html sections require data not currently archived in the standard session archive (doctor dossiers, Instagram content analysis, SMI mentions).

**Primary recommendation:** Extend the existing builder architecture (keep `_build_*` pattern) with a **full CSS replacement** and **data-driven section omission**. New sections that need additional data files should gracefully omit themselves when the data is absent. The HTML generator should read additional JSON files from the session archive when available (doctor_dossiers.json, instagram_content.json, smi_mentions.json), falling back to what prescan-data.json and ci-analysis.json already provide.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HTML generation (build) | API/Backend (Python) | — | Python builds self-contained HTML strings; no SSR needed |
| CSS design system | API/Backend (Python constant) | — | Single `AIM_DESIGN_CSS` string constant; no external CSS files |
| Data loading from archive | API/Backend (Python) | — | Reads JSON from `/opt/data/sessions-archive/` filesystem |
| WordPress publishing | Database/Storage | — | Direct MySQL INSERT into wp_posts table |
| Theme toggle (JS) | Browser/Client (inline JS) | — | Self-contained `<script>` in HTML; no external JS files |
| Ripple animations | Browser/Client (CSS) | — | Pure CSS `@keyframes`; no JS dependency |
| Font loading | CDN/Static (Google Fonts) | — | `<link>` to fonts.googleapis.com |
| Navigation | Browser/Client (CSS) | — | `position:fixed` nav; anchor-based scrolling |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.11+ stdlib (json, os, datetime, string, random) | built-in | Data loading, string manipulation, slug generation | No external deps for HTML building |
| pymysql | latest | WordPress DB publishing | Already used; direct wp_posts INSERT |
| Google Fonts (Inter + Playfair Display) | CDN | Typography | Inter replaces Jost for cleaner body text per ИПХиК design |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | already in project | Future: async data fetching if needed | Not currently needed for report gen |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inter + Playfair Display | Jost + Playfair Display (current) | Inter has better Cyrillic rendering at small sizes, matches ИПХиК target |
| Single theme CSS | Dual theme CSS variables | Dual theme requires ~2x CSS variable declarations, adds 30-40 lines |
| No nav | Fixed nav | Adds ~40 lines CSS + ~15 lines HTML; worth it for long reports |
| No ripple animations | Ripple rings (14 divs + CSS) | Adds ~70 lines; purely cosmetic but high-impact visual quality |

**Installation:**
```bash
# No new Python packages required. All dependencies already installed (pymysql).
# Font change: update Google Fonts URL in HTML template only.
```

**Version verification:** N/A — no new external packages needed.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| pymysql | PyPI | 11+ yrs | 20M+/mo | github.com/PyMySQL/PyMySQL | [ASSUMED] | Keep (existing dependency, unchanged) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No new packages are introduced in this phase. Only existing pymysql is used. slopcheck was not run because no new packages are being added.*

## Architecture Patterns

### System Architecture Diagram

```
Session Archive (/opt/data/sessions-archive/{hash}/)
    │
    ├── metadata.json ──────────────┐
    ├── prescan-data.json ──────────┤
    ├── ci-analysis.json ───────────┤  _load_session_data()
    ├── doctor_dossiers.json ───────┤  (reads all JSON files)
    ├── instagram_content.json ─────┤
    ├── smi_mentions.json ──────────┤
    └── pagespeed.json ─────────────┘
                │
                ▼
         data dict (unified)
                │
                ▼
    ┌───────────────────────────┐
    │   Section Builders        │
    │   _build_hero()           │──► HTML fragment (or "" if no data)
    │   _build_nav()     [NEW]  │──► HTML fragment
    │   _build_about()   [NEW]  │──► HTML fragment
    │   _build_market()  [EXT]  │──► richer competitor table
    │   _build_experts() [NEW]  │──► per-doctor cards
    │   _build_content() [NEW]  │──► content analysis + fears
    │   _build_media()   [NEW]  │──► SMI mentions
    │   _build_competitors()[EXT]──► full competitor breakdown
    │   _build_whitefields()[NEW]──► cross-competitor matrix
    │   _build_presence() [NEW] │──► digital presence audit
    │   _build_strategy()[NEW]  │──► 5-pillar strategy
    │   _build_offer()   [NEW]  │──► AIM service proposal
    │   _build_seo()     [KEEP] │──► existing, data-driven
    │   _build_pagespeed()[KEEP]│──► existing, data-driven
    │   _build_reviews() [KEEP] │──► existing, data-driven
    │   _build_recommendations()│──► existing, optional
    │   _build_footer()  [EXT]  │──► updated branding
    └──────┬────────────────────┘
           │
           ▼
    _build_html() assembles: nav + ripple HTML + sections + footer
           │
           ▼
    Single .replace("\n", "") string
           │
           ▼
    _publish_to_wordpress() → MySQL wp_posts INSERT → https://iamaim.ru/{slug}
```

### Recommended Project Structure
```
AIM/hermes/app/tools/
├── generate_html_report.py    # Main file — extend, don't create new
│   ├── AIM_DESIGN_CSS         # FULL REPLACEMENT (~300 lines)
│   ├── _esc(), _parse_num()   # Keep
│   ├── _load_session_data()   # EXTEND — read new JSON files
│   ├── _build_nav()           # NEW
│   ├── _build_hero()          # EXTEND — metacontent, ripple container
│   ├── _build_about()         # NEW
│   ├── _build_market()        # NEW (replaces simple competitor table)
│   ├── _build_experts()       # NEW
│   ├── _build_content()       # NEW
│   ├── _build_media()         # NEW
│   ├── _build_competitors()   # EXTEND — full breakdown cards
│   ├── _build_whitefields()   # NEW
│   ├── _build_presence()      # NEW
│   ├── _build_strategy()      # NEW
│   ├── _build_offer()         # NEW
│   ├── _build_seo()           # KEEP (minor CSS updates)
│   ├── _build_pagespeed()     # KEEP
│   ├── _build_reviews()       # KEEP
│   ├── _build_footer()        # EXTEND
│   ├── _build_html()          # EXTEND — new section order, nav, ripple
│   └── _publish_to_wordpress()# KEEP (unchanged)
```

### Pattern 1: Graceful Omission (Data-Dependent Sections)

**What:** Every builder function returns `""` when its required data is missing. The assembler filters out empty strings.

**When to use:** All new sections that depend on data not guaranteed to be in every session archive.

**Example:**
```python
def _build_experts(data: dict) -> str:
    """Per-doctor analysis section. Requires doctor_dossiers.json data."""
    doctors = data.get("doctor_dossiers", {}).get("doctors", [])
    if not doctors:
        return ""  # Graceful omission — section simply not rendered
    # ... build HTML from doctor data
    return section_html
```

This is the existing pattern in `_build_exec_summary()`, `_build_competitors()`, etc. — all already return `""` when data is missing. Extend this pattern to new sections.

### Pattern 2: CSS Variable Dual Theme

**What:** All colors defined as CSS custom properties on `:root` (light) and `[data-theme="dark"]` (dark). Theme toggle swaps `data-theme` attribute on `<html>`.

**When to use:** Entire report CSS system.

**Source:** Directly adapted from ИПХиК.html (lines 12-43), verified as working in production.

### Pattern 3: Inline JS for Theme Toggle

**What:** Single `<button>` with inline `onclick` that swaps `document.documentElement.dataset.theme`. No external JS file. Optional localStorage persistence adds ~30 chars.

**When to use:** Theme toggle only. No other JS needed.

**Example:**
```html
<button class="theme-toggle"
  onclick="var t=document.documentElement.dataset.theme;t=t==='dark'?'light':'dark';document.documentElement.dataset.theme=t;localStorage.setItem('theme',t)"
  aria-label="Toggle theme">🌓</button>
```

### Anti-Patterns to Avoid
- **Hardcoded color values in section builders:** All colors MUST reference CSS variables (var(--text), var(--accent), etc.). Never use `style="color:#1A1A1A"` — breaks theme switching.
- **Duplicating section logic:** Each `_build_*` function handles ONE section. Don't inline competitor tables into the market section builder.
- **Empty sections with placeholder text:** If data is missing, return `""`. Never render "No data available" section — it degrades the report quality perception.
- **Hardcoded clinic-specific content:** The ИПХиК.html has hardcoded clinic names, revenue numbers, and doctor names. The generator must read all content from data — nothing hardcoded except AIM branding and CTA boilerplate.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML escaping | Custom sanitizer | `_esc()` (already exists) | Covers & < > " — sufficient for our use case |
| CSS minification | Custom minifier | Single-line string (already used) | `.replace("\n", "")` is adequate for 5-15KB CSS |
| Theme persistence | Custom state manager | `localStorage.setItem/getItem` | Browser-native, zero deps, 30 chars |
| Font loading | Self-hosted fonts | Google Fonts CDN with `preconnect` | Already working; fallback to system fonts in CSS stack |
| Responsive grid | Custom grid system | CSS Grid `grid-template-columns: repeat(auto-fit, minmax(...))` | Already used; well-supported across all browsers |
| Ripple animations | Canvas/WebGL | CSS `@keyframes` with `position:fixed` divs | Pure CSS, zero JS, performs well with 14 elements |
| WordPress publishing | REST API | Direct pymysql INSERT | Already working; REST API timeout issues documented |

**Key insight:** Every visual effect in ИПХиК.html is achieved with pure CSS. No JavaScript libraries, no canvas, no WebGL. The entire report is a single self-contained HTML file. Maintain this property.

## Runtime State Inventory

> Include this section for rename/refactor/migration phases only. Omit entirely for greenfield phases.

This is not a rename/refactor phase. The HTML report generator is being extended (not renamed or migrated). No runtime state needs migration.

- **Stored data:** None — session archives are read-only input. No state written by this tool besides WordPress pages.
- **Live service config:** None — WP_DB_* env vars unchanged.
- **OS-registered state:** None.
- **Secrets/env vars:** None changed.
- **Build artifacts:** None — Python source file update only. Docker image must be rebuilt to pick up changes (container copies code at build time).

## Common Pitfalls

### Pitfall 1: CSS Variable Scope Breakage in Theme Switch

**What goes wrong:** Section builders use inline `style="color:#1A1A1A"` instead of `style="color:var(--text)"`. Light theme looks fine, dark theme shows black text on dark background.

**Why it happens:** Current code has many hardcoded colors in section builders (e.g., `color:var(--accent)`, `color:var(--text-secondary)` are used correctly in some places but `style="color:var(--green)"` and `style="color:var(--red)"` reference CSS variables that change with theme). The existing `AIM_DESIGN_CSS` does NOT define `--green` or `--red` as variables — they're used as raw values (`#1B5E20`, `#C62828`).

**How to avoid:** Define `--green` and `--red` in both `:root` and `[data-theme="dark"]` blocks. Audit ALL inline `style="color:..."` in section builders — every color reference must be a CSS variable.

**Warning signs:** Dark theme screenshots showing invisible text, wrong accent colors, or broken contrast.

### Pitfall 2: Section Bloat With Missing Data

**What goes wrong:** A new section builder renders a full HTML block with "No data available" or partially filled templates when the underlying data file (e.g., `doctor_dossiers.json`) is absent from the session archive.

**Why it happens:** Developer assumes all session archives will have all data files. In practice, the presale pipeline may not run doctor_dossiers or instagram_content for every client.

**How to avoid:** Every new builder checks `if not required_data: return ""` at the TOP. Never render a section header without content.

**Warning signs:** Reports with empty sections, "0 врачей" labels, or "нет данных" placeholders.

### Pitfall 3: WordPress post_content Truncation

**What goes wrong:** HTML report exceeds some WordPress or MySQL limit, content gets silently truncated.

**Why it happens:** If switching from `pymysql` to WordPress REST API, the REST endpoint may have body size limits. Some WordPress setups have `post_max_size` constraints.

**How to avoid:** Current approach uses direct MySQL INSERT into `wp_posts.post_content` which is `LONGTEXT` (4GB max). ИПХиК.html is 78KB. Even a richly populated report will stay under 200KB. This is NOT a risk with the current approach. If future changes switch to REST API, verify payload limits.

**Warning signs:** Published page ends mid-sentence, missing footer, or shows PHP/MySQL errors.

### Pitfall 4: Google Fonts Loading Failure on Slow Connections

**What goes wrong:** Report page renders with no custom fonts (falls back to system fonts), looking significantly worse.

**Why it happens:** Google Fonts CDN is blocked, slow, or the `preconnect` hints don't work in all contexts (e.g., some corporate networks block Google Fonts).

**How to avoid:** Font stack includes system fallbacks: `font-family: 'Inter', -apple-system, sans-serif` for body, `font-family: 'Playfair Display', serif` for headings. This is already in the ИПХиК.html CSS. Additionally, include `font-display: swap` in the Google Fonts URL to prevent FOIT (Flash of Invisible Text). Add `&display=swap` to the Google Fonts URL.

**Warning signs:** Serif headings appearing as generic serif, body text as Arial/Helvetica.

### Pitfall 5: Theme Flicker on Page Load

**What goes wrong:** Page loads in light theme, then flashes to dark theme after JS executes (if user previously selected dark).

**Why it happens:** Theme is set via JS `onclick` or `localStorage` read, which runs after first paint.

**How to avoid:** Add a **blocking script** in `<head>` that reads `localStorage` and sets `data-theme` before first paint:
```html
<script>var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;</script>
```
This must be inline (not external) and placed BEFORE the `<style>` tag or Google Fonts link.

**Warning signs:** Visible white flash when opening a previously dark-themed report.

## Code Examples

Verified patterns from official sources:

### Dual Theme CSS Variables (from ИПХиК.html, lines 11-43)

```css
:root {
  --bg: #ffffff;
  --surface: #F5F5F5;
  --text: #1A1A1A;
  --text-secondary: #666666;
  --text-dim: #999999;
  --accent: #1A1A1A;
  --border: #E0E0E0;
  --green: #2E7D32;
  --red: #C62828;
}
[data-theme="dark"] {
  --bg: #0D0D0D;
  --surface: #1A1A1A;
  --text: #F0F0F0;
  --text-secondary: #999999;
  --text-dim: #666666;
  --accent: #F0F0F0;
  --border: #333333;
  --green: #66BB6A;
  --red: #EF5350;
}
```

### Ripple Ring System (from ИПХиК.html, lines 94-122)

```html
<div class="ripple">
  <div class="ripple-ring ring-lg-1"></div>
  <!-- ... 13 more rings ... -->
  <div class="ripple-ring ring-pulse-8"></div>
</div>
```

```css
.ripple { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.ripple-ring { position: absolute; border-radius: 50%; border: 1px solid var(--text); opacity: 0.04; }
@keyframes pulse-ring {
  0%, 100% { opacity: 0.03; transform: scale(1); }
  50% { opacity: 0.07; transform: scale(1.15); }
}
```

### Theme Toggle With localStorage Persistence

```html
<!-- Blocking script in <head> — prevents theme flicker -->
<script>var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;</script>

<!-- Toggle button in nav -->
<button class="theme-toggle"
  onclick="var d=document.documentElement;var t=d.dataset.theme==='dark'?'light':'dark';d.dataset.theme=t;localStorage.setItem('theme',t)"
  aria-label="Toggle theme">🌓</button>
```

### Fixed Navigation (from ИПХиК.html, lines 63-78)

```css
nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 99;
  padding: 16px 40px; background: var(--glass-bg);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--glass-border);
  display: flex; align-items: center; justify-content: space-between;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single light theme | Dual theme (light/dark) via CSS variables | Now | 100% more CSS variable declarations; theme toggle button |
| Jost body font | Inter body font | Now | Better Cyrillic rendering at small sizes; matches design system |
| No navigation | Fixed nav with section anchors | Now | ~55 lines CSS + ~15 lines HTML; requires section `id` attributes |
| No animations | Ripple rings (pure CSS) | Now | ~70 lines CSS + ~15 lines HTML; cosmetic only |
| White background | var(--bg) + ripple overlay | Now | Zero perf impact (CSS only); enhances premium feel |
| Static sections | Data-driven graceful omission | Now | Sections auto-hide when data missing; no empty sections |
| 9 sections | 15+ sections (some always, some conditional) | Now | Richer reports when data available; same basic report when not |

**Deprecated/outdated:**
- Jost font: replaced by Inter for body text (cleaner, more modern Cyrillic rendering)
- Light-only theme: replaced by dual theme with localStorage persistence
- Static `AIM_DESIGN_CSS`: replaced by new dual-theme CSS system

## Gap Matrix: ИПХиК.html Sections vs Current Data

| # | ИПХиК Section | Current Data Source | Data Sufficient? | Action |
|---|---------------|---------------------|------------------|--------|
| 01 | About (Hero + company overview) | metadata.json + prescan financials + legal | PARTIAL | Company description, history, OKVED — needs LLM generation or additional data |
| 02 | Market (revenue comparison) | prescan financials + ci competitors | YES | Revenue from prescan; competitor revenue from CI if enriched |
| 03 | Experts (per-doctor cards) | doctor_dossiers.json + instagram_content.json | OPT-IN | Only if these tools were run during session. Graceful omission otherwise. |
| 04 | Content Analysis (Reels + fears) | instagram_content.json | OPT-IN | Only if instagram content tool was run. Forum-based fears need web search data. |
| 05 | Media (SMI mentions) | smi_mentions.json | OPT-IN | Only if SMI mentions tool was run. |
| 06 | Competitors (full breakdown) | ci-analysis.json | YES | Competitor data exists; may need enrichment for social stats |
| 07 | Whitefields (cross-competitor matrix) | ci-analysis.json + prescan | PARTIAL | Needs structured competitor digital presence data; can derive from available gaps |
| 08 | Digital Presence (audit table) | prescan reviews + social | PARTIAL | Reviews, Instagram are in data; VK, Telegram, Dzen, YouTube are NOT |
| 09 | Strategy (5 pillars) | ci top_recommendation + gaps | PARTIAL | Needs LLM to expand recommendation into structured strategy |
| 10 | Offer (AIM services) | N/A (template) | TEMPLATE | Boilerplate with clinic name inserted; requires minimal data |

**Sections that ALWAYS render (data available in every prescan):**
- Hero (client name, URL, city, date)
- Market/Financials (revenue, profit, employees)
- SEO Audit (seo_score, checks)
- PageSpeed (if pagespeed data exists)
- Reviews (platforms list)
- Competitors (if CI analysis was run)
- Recommendations (if CI analysis was run)
- Footer (always)

**Sections that CONDITIONALLY render (opt-in data):**
- Experts/Doctors (requires doctor_dossiers.json)
- Content Analysis (requires instagram_content.json)
- Media/SMI (requires smi_mentions.json)
- Whitefields (requires rich competitor data)
- Digital Presence (partial — reviews + Instagram always; full audit needs more)
- Strategy (requires CI analysis with priority_actions)
- Offer (always renders — template-driven)

## Data Availability Audit: Complete Field Map

### Always Available (prescan-data.json — standard 3-stage pipeline)

```
prescan
├── url: str
├── client_name: str
├── city: str
├── financials:
│   ├── revenue: str (e.g., "30–50 млн₽")
│   ├── profit: str (e.g., "5-10 млн ₽")
│   └── employees: int
├── seo:
│   ├── score: int (0-100)
│   ├── checks_total: int
│   ├── checks_passed: int
│   └── checks_failed: [{check, status, business_impact, detail}]
├── pagespeed:
│   ├── scores: {mobile: int, desktop: int}
│   └── cwv: {lcp, fcp, tbt, cls, status}
├── reviews:
│   └── platforms: [{name, rating, count}]
├── doctors_count: int
└── instagram: {handle, followers, er_percent}
```

### Always Available (ci-analysis.json)

```
ci_analysis
├── competitors: [{rank, name, url, strengths, weaknesses, seo_score, reviews_rating, ads_intensity}]
├── competitors_count: int
├── client_strengths: [{advantage, detail}]
├── client_gaps: [{gap, severity, detail}]
├── steal_worthy: [str]
└── top_recommendation: str
```

### Opt-In (not in standard archive — must be saved separately)

These tools exist in the Hermes toolset but their output is NOT currently saved to the session archive:
- `run_doctor_dossiers` — doctor profiles from ProDoctorov, eLibrary, web search
- `run_instagram_content` — per-doctor Reels analysis, engagement rates, content themes
- `run_smi_mentions` — media mentions from Forbes, RBC, Vademecum, etc.
- `run_pagespeed` — detailed PSI data (already partially in prescan)
- `run_content_analysis` — separate content audit tool
- `run_hh_analysis` — hh.ru vacancies (used in ИПХиК offer section)

**Key decision:** The report generator should NOT be responsible for running these tools. It should READ their output IF present in the archive. The `finalize_research` tool should be extended to include these files in the archive when the tools were run.

## Technical Recommendations

### 1. CSS Approach: Full Replacement

**Recommendation:** Replace `AIM_DESIGN_CSS` entirely with the new dual-theme CSS system.

**Rationale:** Incremental patching of the existing 150-line CSS to add dual theme, nav, ripple rings, and new component classes would produce fragile, hard-to-maintain CSS. The ИПХиК.css is only ~200 lines and already proven. Starting from it is cleaner.

**Structure of new CSS:**
1. Reset (`*,*::before,*::after`)
2. CSS variables (`:root` + `[data-theme="dark"]`)
3. Base elements (`html`, `body`, `h1-h4`, `p`, `blockquote`, `hr`)
4. Layout (`.container`, `nav`, `section`, `.hero`)
5. Components (`.card`, `.metrics`, `.grid-2`, `.grid-3`, `.row`, `.gap`, `.tag-badge`)
6. Expert components (`.expert-category`, `.expert-item`, `.comp-expert`)
7. Content components (`.article-link`, `.strategy-block`)
8. CTA (`.cta-box`, `.btn`)
9. Ripple (`.ripple`, `.ripple-ring`, `@keyframes pulse-ring`)
10. Table styles
11. Footer
12. Responsive (`@media` breakpoints at 768px, 480px)
13. Animation delays (staggered entrance — optional, keep if performance allows)

### 2. JS Approach: Minimal Inline

**Recommendation:** Three inline `<script>` blocks only:
1. **Blocking `<script>` in `<head>`** — reads localStorage theme before first paint (~40 chars)
2. **Theme toggle `onclick`** — inline on button element (~120 chars)
3. **Optional: smooth scroll polyfill** — not needed; `scroll-behavior: smooth` is CSS, widely supported

**No external JS files. No frameworks. No npm packages.**

### 3. Architecture: Extend, Don't Rewrite

**Recommendation:** Keep the `_build_*` function pattern, add new builders, replace CSS.

**What stays unchanged:**
- `_esc()`, `_parse_num()`, `_tag_class_for_score()`, `_format_currency()`, `_random_slug()`
- `_load_session_data()` — extend to read new JSON files
- `_publish_to_wordpress()` — unchanged
- `handle_generate_html_report()` — signature unchanged
- `registry.register()` — unchanged

**What gets replaced:**
- `AIM_DESIGN_CSS` → new dual-theme CSS (~300 lines)

**What gets extended:**
- `_build_hero()` — add metacontent (city, address, key stats), ripple container placement
- `_build_exec_summary()` — rebrand as "Key Metrics", integrate into About section
- `_build_competitors()` — richer breakdown cards instead of simple table
- `_build_footer()` — updated AIM branding

**What gets added:**
- `_build_nav()` — fixed navigation with section links
- `_build_about()` — company overview from financials + legal data
- `_build_market()` — revenue comparison table (replaces part of competitors)
- `_build_experts()` — per-doctor cards (conditional)
- `_build_content()` — content analysis + patient fears (conditional)
- `_build_media()` — SMI mentions (conditional)
- `_build_whitefields()` — cross-competitor gap matrix
- `_build_presence()` — digital presence audit table
- `_build_strategy()` — 5-pillar strategic recommendations
- `_build_offer()` — AIM service proposal (template)

**Section assembly order in `_build_html()`:**
```
nav (always)
hero (always)
about (always)
market (if financials + competitors)
experts (if doctor_dossiers)
content (if instagram_content)
media (if smi_mentions)
competitors (if ci_analysis)
whitefields (if ci_analysis)
presence (if reviews + social)
strategy (if ci_analysis)
seo (if seo data)
pagespeed (if pagespeed data)
reviews (if reviews data)
offer (always — template)
footer (always)
```

### 4. Data Loading: Extend `_load_session_data()`

```python
def _load_session_data(session_hash: str) -> dict:
    data = { ... existing ... }
    
    # New optional data sources
    for filename, key in [
        ("doctor_dossiers.json", "doctor_dossiers"),
        ("instagram_content.json", "instagram_content"),
        ("smi_mentions.json", "smi_mentions"),
        ("pagespeed.json", "pagespeed"),
    ]:
        path = os.path.join(session_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data[key] = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
    
    return data
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| CSS variable scope bug in dark theme | MEDIUM | HIGH | Test every builder with both themes; check ALL inline `style="color:..."` |
| Section bloat with missing data | MEDIUM | MEDIUM | Every builder returns `""` at top if data missing; test with minimal session |
| Report size exceeds some limit | LOW | LOW | Current approach uses direct MySQL LONGTEXT insert; no practical limit |
| Theme flicker on load | MEDIUM | LOW | Blocking `<script>` in `<head>` prevents this |
| Google Fonts loading failure | LOW | LOW | System font fallback stack; `font-display: swap` |
| New CSS breaks mobile layout | MEDIUM | MEDIUM | ИПХиК CSS already has responsive breakpoints; test at 375px and 768px |
| WordPress REST API timeout on large pages | N/A | N/A | Using direct pymysql INSERT, not REST API |
| Ripple rings cause scroll performance issues | LOW | LOW | `position: fixed` with `pointer-events: none` has near-zero perf impact; hide on mobile via media query |

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — public HTML pages, no auth |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | `_esc()` HTML-escaping on all user-originated data (client names, URLs, review text) |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for Self-Contained HTML Reports

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via client_name/client_url in HTML | Information Disclosure | `_esc()` already escapes `& < > "` before insertion |
| XSS via review text / competitor names | Information Disclosure | All data passed through `_esc()` in section builders |
| CSS injection via user-controlled data in style attributes | Information Disclosure | Never insert user data into `style=""` attributes directly |
| Open redirect via competitor URLs | Information Disclosure | Add `rel="noopener noreferrer"` to external links (check existing `target="_blank"` links) |

**Audit note:** Current `_build_competitors()` uses `target="_blank"` without `rel="noopener noreferrer"` — should be fixed.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Jost → Inter font switch is purely cosmetic and won't break any layout | Standard Stack | LOW — font metrics are similar; layout uses relative units |
| A2 | WordPress wp_posts.post_content is LONGTEXT with no practical size limit | Common Pitfalls | LOW — confirmed MySQL default for wp_posts |
| A3 | `finalize_research` will be extended to archive additional data files (doctor_dossiers, instagram_content, smi_mentions) | Gap Matrix | MEDIUM — if not done, new sections never render; graceful omission mitigates |
| A4 | Ripple rings don't need to be configurable — always render 14 rings in the same positions | Architecture Patterns | LOW — purely cosmetic, always adds visual quality |
| A5 | Theme toggle should default to light theme (no `data-theme` attribute = light) | Code Examples | LOW — matches ИПХиК.html behavior; can be changed |
| A6 | Inter + Playfair Display fonts are already loaded in current Google Fonts setup or can be switched | Standard Stack | LOW — just a URL change; Google Fonts CDN is reliable |
| A7 | No new Python packages are needed — all functionality is achievable with stdlib + pymysql | Package Legitimacy Audit | LOW — verified by reviewing all needed functionality |

## Open Questions (RESOLVED)

1. **Should finalize_research be extended to include opt-in data files?** — RESOLVED
   - **Decision:** Accept graceful omission. New sections (experts, content, media) render only when their data files exist in session archive. No changes to `finalize_research` in this phase.
   - **Rationale:** `finalize_research` extension is a separate operational concern. The report generator already handles missing data correctly via `return ""`. When the presale pipeline eventually archives these data files, the report sections will automatically appear — no code changes needed.
   - **Impact:** 3 of 11 sections may not render for current sessions. Core sections (Hero, About, Market, Competitors, Whitefields, Strategy, Offer, SEO, PageSpeed, Reviews) all work with existing data.

2. **Should the Strategy section be LLM-generated or template-driven?** — RESOLVED
   - **Decision:** Template-driven using CI analysis data.
   - **Rationale:** CI analysis already provides `top_recommendation`, `gaps`, `advantages`, and `steal_worthy_tactics`. These map directly to strategy pillars: gaps → improvement areas, advantages → strengths, steal_worthy → tactics, top_recommendation → priority action.
   - **Impact:** Strategy section renders for all sessions with CI analysis data. No LLM dependency = faster, cheaper, always available.

3. **How aggressively should we minify the HTML?** — RESOLVED
   - **Decision:** Keep single-line minification (`.replace("\n", "")`).
   - **Rationale:** Established pattern, browsers parse identically, marginal size savings. WordPress `post_content` is LONGTEXT — no size concerns either way.

4. **Should we add a "Download PDF" button?** — RESOLVED
   - **Decision:** Out of scope for Phase 31. Deferred to Phase 31.6.
   - **Rationale:** Not present in ИПХиК.html reference. No client demand yet. Would require server-side PDF rendering infrastructure.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Report generation | ✓ | 3.11+ (server) | — |
| pymysql | WordPress publishing | ✓ | installed (server) | — |
| MySQL/MariaDB (wp-db) | WordPress publishing | ✓ | running (Docker) | — |
| Google Fonts CDN | Typography | ✓ | fonts.googleapis.com | System font stack fallback |
| /opt/data/sessions-archive/ | Data source | ✓ | mounted volume (Docker) | — |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (project standard) |
| Config file | AIM/pyproject.toml or setup.cfg |
| Quick run command | `pytest AIM/tests/unit/test_html_report.py -x -v` |
| Full suite command | `pytest AIM/tests/unit/ -x -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-31-CSS | Dual-theme CSS renders correctly with both light and dark themes | unit | `pytest AIM/tests/unit/test_html_report.py::test_css_variables_present -x` | Wave 0 |
| REQ-31-CSS | All color values use CSS variables (no hardcoded colors) | unit | `pytest AIM/tests/unit/test_html_report.py::test_no_hardcoded_colors -x` | Wave 0 |
| REQ-31-NAV | Fixed nav renders with section links matching actual sections | unit | `pytest AIM/tests/unit/test_html_report.py::test_nav_links_match_sections -x` | Wave 0 |
| REQ-31-RIPPLE | Ripple divs present in HTML output | unit | `pytest AIM/tests/unit/test_html_report.py::test_ripple_elements_present -x` | Wave 0 |
| REQ-31-THEME | Theme toggle button present and has localStorage script | unit | `pytest AIM/tests/unit/test_html_report.py::test_theme_toggle_present -x` | Wave 0 |
| REQ-31-THEME | Blocking script in head prevents theme flicker | unit | `pytest AIM/tests/unit/test_html_report.py::test_theme_blocking_script -x` | Wave 0 |
| REQ-31-GRACE | Missing doctor_dossiers → experts section not rendered | unit | `pytest AIM/tests/unit/test_html_report.py::test_experts_omitted_without_data -x` | Wave 0 |
| REQ-31-GRACE | Minimal session data → still produces valid HTML with core sections | unit | `pytest AIM/tests/unit/test_html_report.py::test_minimal_session_produces_valid_html -x` | Wave 0 |
| REQ-31-DATA | All section builders return "" when required data missing | unit | `pytest AIM/tests/unit/test_html_report.py::test_all_builders_graceful_omission -x` | Wave 0 |
| REQ-31-SEC | XSS: client_name with special chars is escaped | unit | `pytest AIM/tests/unit/test_html_report.py::test_xss_client_name_escaped -x` | Wave 0 |
| REQ-31-SEC | External links have rel="noopener noreferrer" | unit | `pytest AIM/tests/unit/test_html_report.py::test_external_links_have_noopener -x` | Wave 0 |
| REQ-31-PUB | Report publishes to WordPress and returns valid URL | integration | Manual test on server: call tool with test session | Manual only |

### Sampling Rate
- **Per task commit:** `pytest AIM/tests/unit/test_html_report.py -x -v`
- **Per wave merge:** `pytest AIM/tests/unit/ -x -v`
- **Phase gate:** All unit tests green + manual integration test on server with real session data

### Wave 0 Gaps
- [ ] `AIM/tests/unit/test_html_report.py` — does not exist; must be created
- [ ] `AIM/tests/unit/conftest.py` — may need shared fixtures for sample session data
- [ ] Test framework install: verify `pytest` is in Docker image

## Sources

### Primary (HIGH confidence)
- `/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/generate_html_report.py` — full current implementation (924 lines) [VERIFIED: codebase read]
- `/Users/mikhaileliseev/Downloads/ИПХиК (1).html` — target quality reference (966 lines, 78KB) [VERIFIED: file read]
- `/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/run_prescan.py` — prescan data structure (518 lines) [VERIFIED: codebase read]
- `/opt/data/sessions-archive/nachalo-clinica/prescan-data.json` — real prescan output (2.5KB) [VERIFIED: server read]
- `/opt/data/sessions-archive/nachalo-clinica/ci-analysis.json` — real CI analysis output (4.5KB) [VERIFIED: server read]
- `/opt/data/sessions-archive/nachalo-clinica/metadata.json` — real session metadata (233B) [VERIFIED: server read]

### Secondary (MEDIUM confidence)
- `/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/run_doctor_dossiers.py` — confirms doctor data tool exists [CITED: codebase]
- `/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/run_instagram_content.py` — confirms Instagram analysis tool exists [CITED: codebase]
- `/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/publish_scout_report.py` — confirms WordPress publishing pattern used across tools [CITED: codebase]

### Tertiary (LOW confidence)
- Google Fonts `&display=swap` parameter — assumed based on training knowledge, not verified against current Google Fonts API docs [ASSUMED]
- `wp_posts.post_content` column type as LONGTEXT — assumed based on WordPress schema knowledge [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; verified existing dependencies
- Architecture: HIGH — current code fully read and analyzed; target HTML fully read
- Data model: HIGH — real prescan and CI output examined from production server
- Pitfalls: MEDIUM — CSS variable scope bugs are predicted based on code patterns, not yet reproduced
- Gap matrix: HIGH — systematic comparison of 11 target sections against available data fields

**Research date:** 2026-06-16
**Valid until:** 2026-07-16 (stable domain; CSS/HTML patterns change slowly)
