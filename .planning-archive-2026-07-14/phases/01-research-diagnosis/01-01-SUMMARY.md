---
phase: 01-research-diagnosis
plan: 01
subsystem: research
tags: [hermes, coverage-analysis, tool-coverage, section-coverage, baseline-measurement, ssh-aim]

# Dependency graph
requires: []
provides:
  - "Tool coverage baseline: 15/40+ tools (37.5%) — measured across 5 sessions"
  - "Section coverage baseline: 3.0/10 sections (30%) — measured across 5 HTML reports"
  - "Categorized list of 21 never-called tools (54% of catalog)"
  - "Consistently missing sections: About (100% missing), Market (100% missing), Offer/Whitefields/Competitors/Content Analysis (80% missing)"
  - "Evidence of report quality degradation: recent reports (Jun 20-22) are shorter and less complete than older reports (Jun 16)"
  - "Evidence file: .planning/phases/01-research-diagnosis/evidence/coverage-baseline.md"
affects: [01-03-PLAN, 02-orchestrator, phase-02, phase-04]

# Tech tracking
tech-stack:
  added: []
  patterns: ["read-only server investigation via ssh aim + docker exec aim-hermes", "heading-based section detection via python3 regex on h1-h4 tags"]

key-files:
  created:
    - ".planning/phases/01-research-diagnosis/evidence/coverage-baseline.md"
  modified: []

key-decisions:
  - "Used heading-based section detection (h1-h4 tag extraction) instead of keyword-only matching to avoid false positives from CTA text and navigation"
  - "Strict Offer section matching: 'Готовы действовать?' CTA does NOT count as Offer section — only 'Как мы поможем'/'Что AIM может' patterns qualify"
  - "Selected 5 reports from mixed sources (2 from reports-publish, 3 from sessions-archive) per plan's fallback instructions, since only 2 of 5 sessions had session-linked report.html"
  - "Included test-iphk-002 (Jun 20) as 5th session for tool-pattern diversity, since 4 of 5 most recent sessions were identical iphk.ru re-runs"

patterns-established:
  - "Coverage measurement methodology: session-hash → tool-call extraction → unique count → average → gap analysis"
  - "Section coverage methodology: HTML heading extraction → keyword pattern match → per-report mapping → average → consistently-missing identification"

requirements-completed: [RES-02, RES-03]

# Metrics
duration: 15min
completed: 2026-06-22
---

# Phase 1 Plan 01: Baseline Coverage Measurement Summary

**Tool coverage 15/40+ (37.5%) and section coverage 3.0/10 (30%) measured across 5 live sessions and 5 HTML reports — 21 tools never called, About + Market sections absent in 100% of reports, 2 most recent reports completely empty**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-22T16:40:00Z (approximate — first ssh command)
- **Completed:** 2026-06-22T16:52:21Z
- **Tasks:** 2 (both completed)
- **Files modified:** 1 (evidence document created)

## Accomplishments

- **RES-02 baseline established:** 15/40+ tools called per typical v4 presale run (average of 15.4 unique tools across 5 sessions). 21 of 39 registered tools (54%) were never called by any session, categorized by type (Firecrawl, Crawlee/Scrapy, Ads, Lighthouse, Prescan, Geo, Presentation, Orchestration).
- **RES-03 baseline established:** 3.0/10 reference sections present in v4 HTML reports (average across 5 reports). About and Market sections missing in 100% of reports; Offer, Whitefields, Competitors, Content Analysis missing in 80%.
- **Critical regression discovered:** 2 of 5 reports (Era Smile, published Jun 22) are completely empty — 0/10 sections, only title and CTA. Report quality has degraded over time: oldest report (Jun 16) had 8/10 sections, newest reports (Jun 20-22) have 0-4.
- **CONTEXT.md hypotheses cross-referenced:** "About missing" CONFIRMED, "Market missing" CONFIRMED, "Offer/Whitefields missing" CONFIRMED, "Instagram absent" REFUTED at tool level (3/5 sessions call run_instagram_content), "Strategy missing" PARTIALLY REFUTED (present in 3/5 but in weak form).
- **Tool pattern discovery:** Two distinct tool-call patterns exist for iphk.ru — Pattern A (most recent, includes Instagram + Tech SEO) and Pattern B (older, uses doctor_dossiers + seo_audit). Indicates pipeline/tool-handler changes between Jun 20 and Jun 21.
- **Server state verified unchanged:** All investigation via read-only commands (ls, cat, find, stat, python3 JSON parsing). SOUL.md, engine.py, phases.py mtimes confirmed older than plan execution.

## Task Commits

Each task was committed atomically:

1. **Task 1: Sample sessions and measure tool coverage (RES-02)** - `dccd10f` (docs) — combined commit with Task 2 since both tasks write to the same evidence file
2. **Task 2: Measure section coverage against reference (RES-03)** - `dccd10f` (docs) — same commit as Task 1

Both tasks produce a single evidence file (`coverage-baseline.md`), so they were committed together in one atomic commit as the plan's `files_modified` field specifies a single file for both tasks.

**Plan metadata:** not yet committed (will be included in final metadata commit)

## Files Created/Modified

- `.planning/phases/01-research-diagnosis/evidence/coverage-baseline.md` - Combined evidence file with RES-02 (tool coverage) and RES-03 (section coverage) baselines, per-session/per-report breakdowns, categorized never-called tools list, consistently missing sections with CONTEXT.md hypothesis cross-reference, methodology notes, and server state verification

## Decisions Made

1. **Heading-based section detection over keyword-only matching** — Initial keyword matching produced false positives (e.g., "Готовы действовать?" CTA matched Offer section keywords). Switched to extracting h1-h4 heading tags and matching section patterns against heading text only. This is more accurate but still a minimal bar — a heading with one sentence counts as "present".

2. **Strict Offer section matching** — "Готовы действовать?" (Ready to act?) is a generic CTA present in most reports. It is NOT the Offer section. Only headings like "Как мы поможем", "Что AIM может", "Предложение" count. This reduced the Offer section presence from 5/5 (false positive) to 1/5 (only nachalo-clinica).

3. **Mixed-source report sample for RES-03** — Only 2 of 5 Task-1 sessions had session-linked report.html. Used plan's fallback instructions to include 2 reports from `/opt/data/reports-publish/` and 1 additional session-archive report (nachalo-clinica). This provides better diversity (3 clinics, 4x size range) but breaks session-to-report linkage for 3/5 reports.

4. **Included test-iphk-002 for tool-pattern diversity** — 4 of 5 most recent sessions were identical iphk.ru re-runs (same 16 tools). Added test-iphk-002 (Jun 20, 1 day older) as 5th session because it uses a different tool pattern (14 tools, includes run_doctor_dossiers + run_seo_audit instead of Instagram + Tech SEO). This provides a more representative baseline.

## Deviations from Plan

None - plan executed exactly as written.

The plan specified fallback locations for HTML reports (reports-publish, proposals directory, find by mtime) and these were used as intended. The plan's `files_modified` field lists a single evidence file for both tasks, so both tasks were committed in one atomic commit rather than two separate commits.

## Issues Encountered

- **Flat vs subdir session structures:** Session `tg:322367335` (arclinic.ru) uses a flat JSON structure where each phase file contains multiple tool results as JSON keys, while other sessions use subdirectories with one file per tool call. Resolved by using `python3 -c` to parse JSON keys for flat-structure sessions and filename extraction for subdir-structure sessions.
- **jq not available in container:** Initial attempt to parse JSON with jq failed (not installed). Used `python3` instead, which is available at `/usr/local/bin/python3`.
- **2/5 reports completely empty:** The two Era Smile reports (published Jun 22) contain only CSS scaffolding and a CTA heading — no data sections. This was unexpected and is a critical finding for Plan 01-03 (root cause analysis). The reports were still counted in the baseline (0/10 sections) as this represents actual v4 output quality.

## Next Phase Readiness

- **Plan 01-02 (RES-04):** Session log deep dive can use the same 5 sessions identified here. The two tool-call patterns (A vs B) and the empty-report regression (Era Smile) are high-priority investigation targets.
- **Plan 01-03 (RES-01):** Root cause analysis has concrete evidence to work with:
  - Tool coverage gap (15/40+) is NOT caused by tools being unavailable — 18 tools are called, 21 are registered but never selected by the LLM/pipeline
  - Section coverage gap (3.0/10) is NOT caused by data missing — sessions collect 14-16 tool outputs but reports only render 0-4 sections. The gap is in HTML BUILD and interpretation, not collection
  - Report quality degradation (Jun 16: 8/10 → Jun 22: 0/10) suggests a regression introduced between Jun 16 and Jun 20 — code commit history in that window should be investigated
- **Phase 2 (3-Pass Orchestrator):** Baselines established. Phase 2's success criteria (≥80% checklist coverage) now has a measured starting point: 15/40+ tools → target ≥32/40+, and 3.0/10 sections → target 10/10.

### Key Numbers for Phase 2 Target-Setting

| Metric | Current Baseline | Phase 2 Target | Gap |
|--------|:---:|:---:|:---:|
| Tool coverage | 15/40+ (37.5%) | ≥80% of applicable tools | +17 tools |
| Section coverage | 3.0/10 (30%) | 10/10 (100%) | +7 sections |
| Never-called tools | 21/39 (54%) | <5/39 (13%) | -16 tools |
| Empty reports | 2/5 (40%) | 0/5 (0%) | -2 reports |
| Avg report size | 14.4 KB | ~78 KB (reference) | +63.6 KB |

## Self-Check: PASSED

- FOUND: `.planning/phases/01-research-diagnosis/evidence/coverage-baseline.md`
- FOUND: `.planning/phases/01-research-diagnosis/01-01-SUMMARY.md`
- FOUND: commit `dccd10f` in git log
- PASS: RES-02 marker in evidence file
- PASS: "X/40+ tools" pattern in evidence file
- PASS: RES-03 marker in evidence file
- PASS: "Y/10 sections" pattern in evidence file
- PASS: Server state unchanged — SOUL.md mtime 1782078325 (Jun 21), engine.py mtime 1782063956 (Jun 21), both before plan execution (Jun 22)

---

*Phase: 01-research-diagnosis*
*Plan: 01*
*Completed: 2026-06-22*
