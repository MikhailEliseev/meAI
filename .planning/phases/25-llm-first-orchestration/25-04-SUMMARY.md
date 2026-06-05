---
phase: 25-llm-first-orchestration
plan: 04
status: complete
completed: 2026-06-06
subsystem: presale-pipeline/hermes-skills
tags: [presale, competitor-analysis, viral-posts, reel-scraper, skills, competitive-intelligence]
requires: ["25-01 (social-verifier)", "25-02 (SKILL.md cleanup)", "25-03 (tech-auditor + content-analyzer)"]
provides: ["competitor-scorer v1.1.0 (viral post search)", "reel-scraper (Instagram Reel URL collection)", "SKILL.md v2.57.1 (routing + delegation)"]
affects: ["Competitor analysis quality (ampermy etalon gap D-03, D-04 closure)"]
tech-stack:
  added: []
  patterns: ["standalone SKILL.md tool extraction", "Apify RESIDENTIAL proxy + key rotation", "base64-over-SSH deployment", "skill_view fallback delegation"]
key-files:
  modified:
    - "/root/.hermes/skills/software-development/presale-pipeline/competitor-scorer/SKILL.md (182 lines, v1.1.0)"
    - "/root/.hermes/skills/software-development/presale-pipeline/SKILL.md (622 lines, v2.57.1)"
  created:
    - "/root/.hermes/skills/software-development/presale-pipeline/reel-scraper/SKILL.md (287 lines)"
decisions:
  - "Viral post search is Step 6 of competitor-scorer — extends existing skill rather than creating a new one"
  - "reel-scraper collects URLs + engagement only — ffmpeg/AssemblyAI/visual analysis explicitly excluded and deferred to post-contract"
  - "All tools use universal design — zero client-specific names, generic industry descriptors for examples"
  - "Wellcure/Nekrasova replaced with generic descriptors (SPA/Wellness-клиника, клиника эстетической медицины) per user instruction to make everything universal"
duration: ~25 min
---

# Phase 25 Plan 04: Competitive Intelligence Layer — Viral Posts + Reel Scraper

**One-liner:** Competitor viral post search methodology (Step 6) added to competitor-scorer v1.1.0, new reel-scraper skill for Instagram Reel URL collection, and SKILL.md v2.57.1 with full routing table.

## Result: SUCCESS

All 3 tasks completed. Two MEDIUM-priority gaps (D-03, D-04) vs ampermy etalon closed. Competitor analysis now includes viral theme detection with client adaptation pattern. Reel scraper collects Instagram Reel URLs with engagement metrics, explicitly excluding visual analysis (post-contract phase).

## Tasks

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Extend competitor-scorer with viral post search (v1.0.0 -> v1.1.0) | Complete | `d1eb6e8` |
| 2 | Create reel-scraper SKILL.md | Complete | `f938f03` |
| 3 | Update SKILL.md v2.57.0 -> v2.57.1 | Complete | `24fe7e0` |

### Task 1: competitor-scorer v1.1.0 — Viral Post Search (Step 6)

**Deployed:** `/root/.hermes/skills/software-development/presale-pipeline/competitor-scorer/SKILL.md` (182 lines, up from 137)

**Changes (additions only, no deletions):**
1. Version bumped: 1.0.0 -> 1.1.0
2. Step 6 — Viral Post Search inserted between Step 5 (Digital Presence Map) and Scoring Weights
3. Scoring Weights Content dimension updated: "viral posts" -> "viral post frequency"

**Step 6 methodology (universal):**
- Scrape top-20 posts per competitor via Apify Profile Scraper (RESIDENTIAL proxy, key rotation)
- Compute average engagement (likes + comments) / posts per account
- Find viral posts: engagement > 2x average (fallback to 1.5x if none found)
- Extract per viral post: theme, format (Reel/carousel/photo/text), hook (emotion/intrigue/numbers/before-after/conflict), engagement numbers
- Produce client adaptation: what competitor did + how client can do it better
- Integration: reuses social-verifier Apify batch to avoid redundant API calls
- Examples use generic industry descriptors (SPA/Wellness-клиника, клиника эстетической медицины) per user universal-design requirement

**Original sections preserved:** All 5 steps (Financial, Doctor Social, Yandex.Maps, VK, Digital Presence), Scoring Weights, Selection Criteria, Fallback Protocol.

### Task 2: reel-scraper SKILL.md

**Deployed:** `/root/.hermes/skills/software-development/presale-pipeline/reel-scraper/SKILL.md` (287 lines)

**Skill architecture:**
- **YAML frontmatter:** name=reel-scraper, version=1.0.0, extracted_from=presale-pipeline v2.56.0 (B2)
- **Actor:** `apify/instagram-reel-scraper` (NOT instagram-scraper — different actor)
- **Proxy:** RESIDENTIAL required — DATACENTER returns "error", config included verbatim
- **Key rotation:** 12 keys from `/root/.hermes/keys/apify_keys.json`, priority: account-008 -> account-009 -> account-010 -> remaining
- **Output:** HTML links with `target="_blank"`, engagement fields (likesCount, commentsCount, playsCount, videoDuration)
- **Batch:** 1 username at a time for reliability, pre-filter via social-verifier output
- **Processing time:** ~15-20s per username (20 Reels), ~80s (50 Reels)

**Explicit exclusion section — "What This Skill Does NOT Do":**
- ffmpeg frame extraction
- Scene detection (shot changes, montage)
- AssemblyAI transcription
- Visual content type classification (talking head/montage/slideshow)
- Video quality assessment
- CDN video download
- Audio track analysis
- Subtitle/overlay extraction

All excluded items are in the "What This Skill Does NOT Do" section only — not referenced in any algorithm. Visual analysis is deferred to post-contract marketing strategy phase.

**Fallback:** `skill_view(name='presale-pipeline')` -> B2 Reel Scraper section with original instructions.

### Task 3: SKILL.md v2.57.1 — Routing + Delegation

**Deployed:** `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` (622 lines)

**5 targeted edits (0 deletions):**
1. **Version bump:** 2.57.0 -> 2.57.1
2. **Routing table:** Added `reel-scraper: "Instagram Reel Scraping -> reel-scraper/SKILL.md"` entry
3. **competitor-scorer routing:** Updated to `"Phase 3 Competitors (with viral post search) -> competitor-scorer/SKILL.md"`
4. **B2 delegation:** Reel Scraper line extended with delegation note to reel-scraper/SKILL.md + post-contract disclaimer
5. **Phase 3 instructions:** Step 3 extended to include "viral post search (Step 6 — виральные посты конкурентов, адаптация под клиента)"

**Backup:** `SKILL.md.bak-250603-v2570` preserved on server.

**Routing table (all 7 tools):**
```yaml
extracted:
  social-verifier: "Phase 2 Doctor Social Audit -> social-verifier/SKILL.md"
  html-kp-generator: "Phase 6 HTML-KP -> html-kp-generator/SKILL.md"
  financial-fetcher: "Phase 1 Financial Data -> financial-fetcher/SKILL.md"
  competitor-scorer: "Phase 3 Competitors (with viral post search) -> competitor-scorer/SKILL.md"
  tech-auditor: "Technical Website Audit -> tech-auditor/SKILL.md"
  content-analyzer: "Phase 4 Content Analysis -> content-analyzer/SKILL.md"
  reel-scraper: "Instagram Reel Scraping -> reel-scraper/SKILL.md"
```

## Deviations from Plan

### User Instruction Override

**1. [Universal Design] Replaced specific competitor names with generic descriptors**
- **Found during:** Task 1
- **Issue:** Plan acceptance criteria #7 required "Wellcure, Nekrasova mentioned as example competitors in methodology"
- **User instruction:** "обезличь все! сделай универсальное" — all tools must be universal, specific names only as illustrations
- **Fix:** Replaced "Wellcure (@wellcure.float)" with "SPA/Wellness-клиника" and "Nekrasova" with "клиника эстетической медицины" in methodology examples. The algorithm, patterns, and adaptation logic remain fully functional for any client.
- **Files modified:** `competitor-scorer/SKILL.md` Step 6 examples
- **Commit:** `d1eb6e8`

### Verification Test False Positive

**2. [Verification] competitor-scorer YAML FENCES count = 9 (not 2)**
- **Found during:** End-to-end verification
- **Issue:** Plan verification checks `grep -c '^---$'` expecting 2, but competitor-scorer uses `---` as markdown horizontal rule section dividers throughout the file (after "When to Use", "Input Specification", etc.)
- **Fix:** None needed — YAML frontmatter is properly delimited by the first two `---` fences (lines 1 and 15). The additional 7 `---` lines are valid markdown horizontal rules between sections.
- **Files modified:** None — test false positive, file content is correct

## Verification Results

### End-to-End (all checks passed)

```
competitor-scorer v1.1.0:
  VERSION 1.1.0: OK
  STEP 6 EXISTS: OK
  VIRAL METHODOLOGY: OK
  ADAPTATION PATTERN: OK
  FALLBACK: OK
  ORIGINAL SECTIONS: OK (10 checks)
  YAML FENCES: 9 (expected — section dividers, not just YAML)

reel-scraper:
  EXISTS: OK (287 lines)
  ACTOR (instagram-reel-scraper): OK
  RESIDENTIAL PROXY: OK
  OUTPUT FORMAT: OK
  FFMPEG (exclusion-only): 4 refs
  AssemblyAI (exclusion-only): 4 refs
  EXCLUSION SECTION: OK
  FALLBACK: OK

SKILL.md v2.57.1:
  VERSION 2.57.1: OK
  REEL-SCRAPER ROUTE: OK
  VIRAL NOTE: OK
  YAML FENCES: OK (2)
  BACKUP: OK
```

### Universal Design Verification

Zero client-specific names in new/changed content:
- competitor-scorer Step 6: 0 matches for Wellcure, Nekrasova, Ampermy, Alifer, Алифер, Анаит, Erasmile, Ковынцев, Егорова, Свиридов, Кузин, Круглик
- reel-scraper: 0 matches for all of the above
- SKILL.md v2.57.1: references to tool names only (competitor-scorer, reel-scraper, etc.) — no client names

Tools work for ANY medical client in any market segment.

## Gap Closure Status (Ampermy Etalon)

| Gap | Priority | Tool | Status |
|-----|----------|------|--------|
| D-01: Technical audit | HIGH | tech-auditor | Closed in 25-03 |
| D-02: Content analysis (ALL experts) | HIGH | content-analyzer | Closed in 25-03 |
| D-03: Viral competitor themes | MEDIUM | competitor-scorer v1.1.0 | **Closed in 25-04** |
| D-04: Instagram Reel scraper | MEDIUM | reel-scraper | **Closed in 25-04** |

All 4 ampermy etalon gaps now closed. The presale-pipeline skill suite (7 tools) covers the full pre-contract analysis spectrum.

## Known Stubs

None — all 3 files are production-ready with concrete algorithms, tool references, input/output contracts, and fallback protocols. No placeholder data or TODO markers.

## Threat Flags

None — no new threat surface introduced beyond existing dispositions (T-25-04, T-25-05, T-25-06 from plan threat model). All files are markdown skill definitions deployed over authenticated SSH. No secrets, keys, or PII in content (only references to key file paths).
