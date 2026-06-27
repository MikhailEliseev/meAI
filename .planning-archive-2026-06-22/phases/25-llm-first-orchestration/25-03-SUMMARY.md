---
phase: 25-llm-first-orchestration
plan: 03
status: complete
completed: 2026-06-06
subsystem: presale-pipeline/hermes-skills
tags: [presale, tech-audit, content-analysis, skills, hermetic-tools]
requires: ["25-01 (social-verifier extraction)", "25-02 (SKILL.md cleanup)"]
provides: ["tech-auditor (standalone tech audit tool)", "content-analyzer (ALL-experts content analysis)"]
affects: ["SKILL.md v2.57.0 (routing + delegation)"]
tech-stack:
  added: []
  patterns: ["standalone SKILL.md tool extraction", "skill_view fallback delegation", "base64-over-SSH deployment"]
key-files:
  created:
    - "/root/.hermes/skills/software-development/presale-pipeline/tech-auditor/SKILL.md (351 lines)"
    - "/root/.hermes/skills/software-development/presale-pipeline/content-analyzer/SKILL.md (338 lines)"
  modified:
    - "/root/.hermes/skills/software-development/presale-pipeline/SKILL.md (621 lines, v2.57.0)"
decisions:
  - "Tech-auditor is a standalone tool extracting Phase 0 pre-flight into a dedicated skill"
  - "Content-analyzer analyzes ALL experts in the input list, not just top performers"
  - "All tools are universal — zero client-specific names, works for any medical clinic"
duration: ~20 min
---

# Phase 25 Plan 03: Gap Closure Tools — Tech Auditor + Content Analyzer

**One-liner:** Two new universal presale-pipeline tools deployed: 8-parameter technical website audit and ALL-expert content analysis with 4 winning formats framework.

## Result: SUCCESS

All 3 tasks completed successfully. Two new standalone skills deployed, main SKILL.md updated to v2.57.0 with routing table entries and Phase 4 delegation.

## Tasks

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Create tech-auditor SKILL.md | Complete | `b442e8e` |
| 2 | Create content-analyzer SKILL.md | Complete | `80fa97e` |
| 3 | Update SKILL.md v2.56.0 → v2.57.0 | Complete | `b6108ef` |

### Task 1: tech-auditor SKILL.md

**Deployed:** `/root/.hermes/skills/software-development/presale-pipeline/tech-auditor/SKILL.md` (351 lines)

**8 parameters audited:**
1. Lighthouse/PageSpeed — API + browser_console, Core Web Vitals
2. Broken links — 15-20 page crawl with medical URL template
3. Meta tags — title, description, viewport, OG tags
4. H1 tags — exactly 1 per page, uniqueness check
5. Alt text — image accessibility, >20% missing = critical
6. Sitemap + robots.txt — presence, freshness, completeness
7. SSL/HTTPS — certificate validity, HTTP→HTTPS redirect
8. Mobile responsiveness — viewport 375x812, overflow, touch targets

**Input:** `url` (required), `competitor_urls` (optional), `crawl_pages` (optional)
**Output:** Per-parameter table + CRITICAL/RECOMMENDATIONS/GOOD grouping + competitor comparison
**Fallback:** `skill_view(name='presale-pipeline')` → Phase 0 Pre-flight

### Task 2: content-analyzer SKILL.md

**Deployed:** `/root/.hermes/skills/software-development/presale-pipeline/content-analyzer/SKILL.md` (338 lines)

**Key features:**
- **ALL-experts rule:** Every expert with verified socials gets a full analysis card — not just TOP-2
- **4 Winning Formats Framework:** Show/Series, Intrigue+Engagement, Author's Methodology, Educational Expertise — universal patterns applicable to any medical market
- **Google fallback:** If Apify blocks, `web_search("site:instagram.com")` extract from snippets — never leave a card empty
- **Telegram MTProto:** `tg-mtproto.py messages @channel 20` for TG content analysis
- **White space analysis:** Format, topic, platform, and audience white spaces identified per client
- **Card format:** Topics, Format, Signature Move, Top Post (with numbers), Insight — border-left styling for client vs competitor

**Input:** Array of experts from social-verifier output
**Output:** Per-expert cards + 4 formats analysis + white space + content plan stitching notes
**Fallback:** `skill_view(name='presale-pipeline')` → Phase 4 Content Strategy

### Task 3: SKILL.md v2.57.0 Update

**Changes made (4 edits, 0 deletions):**

1. **Extracted metadata** — Added tech-auditor and content-analyzer routing entries
2. **Pre-flight checklist** — tech-auditor as item 0 (first step before knowledge/second-brain)
3. **Phase 0** — Tech audit reference: run before data collection for 2x argument multiplier
4. **Phase 4** — Delegation block: content-analyzer handles ALL-expert analysis, original algorithm preserved as fallback

**Backup:** `SKILL.md.bak-250603` created before edits
**Verification:** 2 YAML fences intact, all 7 phases preserved, 621 lines total

## Deviations from Plan

None — plan executed exactly as written. All acceptance criteria met for all 3 tasks.

## Verification Results

### End-to-End (all 22 checks passed)

```
tech-auditor: EXISTS (351 lines), 9/9 params OK, FALLBACK OK
content-analyzer: EXISTS (338 lines), ALL EXPERTS/4 FORMATS/WHITE SPACE/FALLBACK — all OK
SKILL.md v2.57.0: VERSION/TECH-AUDITOR ROUTE/CONTENT-ANALYZER ROUTE/PHASE 4 DELEGATION/YAML FENCES(2)/BACKUP — all OK
```

### Universal Design Verification

Zero client-specific names found in either new file. Checked against: Ampermy, Wellcure, Некрасова, Алифер, Анаит, erasmile, Erasmile, Ковынцев, Егорова, Свиридов, Кузин, Круглик, Никор — all returned 0 matches. Tools work for ANY medical client.

## Known Stubs

None — all 3 files are production-ready with concrete algorithms, tool references, input/output contracts, and fallback protocols. No placeholder data or TODO markers.

## Threat Flags

None — no new threat surface introduced. All files are markdown skill definitions deployed over authenticated SSH. No secrets, keys, or PII in content (only references to key file paths). Falls within existing T-25-01/T-25-02/T-25-03 threat model dispositions.

## Decisions Made

1. **Universal-only design** — Per user instruction, all tools contain zero client-specific names. Examples use generic patterns (example-clinic.ru, Expert Name, Client Clinic) rather than real clinic references.

2. **Line-based editing for SKILL.md** — Used Python line insertion for pre-flight checklist (item 0) rather than pattern matching, avoiding Unicode/quote escaping issues with the Russian text content.

3. **Local commits with --allow-empty** — Server-side deployments have no local file changes; used descriptive commit messages to document each task's deployment artifacts.

## Dependencies for Next Plans

- **25-04 (reel-scraper + competitor viral topics):** Depends on content-analyzer's expert card format. Reel scraper inputs social-verifier output, same as content-analyzer. Competitor viral topic analysis complements content-analyzer's white space detection.
