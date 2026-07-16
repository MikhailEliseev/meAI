---
phase: 01-research-diagnosis
plan: 03
subsystem: research
tags: [root-cause, hypothesis-testing, research-consolidation, res-01, phase-2-handoff, qc-checklist]

# Dependency graph
requires:
  - phase: 01-research-diagnosis
    provides: "Wave 1 evidence (Plans 01-01, 01-02, 01-04) — coverage baselines, session log analysis, Instagram tool test"
provides:
  - "Confirmed root cause for v4 LLM tool-skipping: Hypothesis D (A+C primary, B secondary, NEW code bug amplifier)"
  - "Authoritative tool counts: 22 _TOOL_HANDLERS vs 49 LLM-registered modules = 27 unreachable"
  - "Per-hypothesis verdicts with cited evidence: A=PARTIAL, B=PARTIAL, C=CONFIRMED-PRIMARY, D=CONFIRMED"
  - "SOUL.md vs SKILL.md document paradox identified (permissive vs strict)"
  - "15-item QC checklist for Phase 2 coverage measurement"
  - "Phase 2 architectural recommendation: orchestrator-first (bypass _TOOL_HANDLERS)"
  - "RESEARCH.md — single readable consolidated report for admin (595 lines)"
  - "Evidence file: .planning/phases/01-research-diagnosis/evidence/root-cause-analysis.md (491 lines)"
affects: [02-orchestrator, phase-02, phase-03, phase-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "4-hypothesis evidence-based root cause analysis with explicit verdicts (CONFIRMED/REFUTED/PARTIAL)"
    - "Direct Python introspection via docker exec for authoritative _TOOL_HANDLERS count"
    - "Read-only server verification with stat -c '%Y %n' mtime checks"
    - "Cross-referencing 3 Wave 1 evidence files + live server greps in single consolidated report"

key-files:
  created:
    - ".planning/phases/01-research-diagnosis/evidence/root-cause-analysis.md"
    - ".planning/phases/01-research-diagnosis/RESEARCH.md"
  modified: []

key-decisions:
  - "Hypothesis C confirmed as PRIMARY root cause — 22 _TOOL_HANDLERS vs 49 LLM-registered modules = 27 unreachable tools (authoritative Python introspection)"
  - "Hypothesis A verdict PARTIAL (not CONFIRMED) — permissive language in SOUL.md is real but document paradox with strict SKILL.md is the actual A problem, not pure prompt permissiveness"
  - "Hypothesis B verdict PARTIAL (not CONFIRMED) — only 5/28 skip points are LLM_DECISION; most skips are pipeline blocks or code bugs, not model limits"
  - "Identified _unwrap_tool_output NameError as NEW code regression (Jun 20-21) — independent of root cause but masks it; must be Phase 2 P0 fix"
  - "Recommended orchestrator-first architecture (Option 2) over pipeline-extension (Option 1) for Phase 2 — matches ROADMAP ORC-02 and fixes root cause directly"
  - "Proposed 15-item QC checklist within QC-01's 10-20 range — covers missing sections + never-called tools + Instagram verification"
  - "CONTEXT.md '19 _TOOL_HANDLERS' and Plan 04 '23 entries' both slightly stale — authoritative value at plan execution: 22"

patterns-established:
  - "Hypothesis testing pattern: 4 hypotheses with explicit verdicts (CONFIRMED/REFUTED/PARTIAL) + evidence citations + final consolidated root cause"
  - "Server state verification: stat -c '%Y %n' mtime check before/after every ssh investigation"
  - "Read-only ssh + docker exec pattern: grep/head/wc/find/stat/python3 -c/env/cat only — no sed -i, mv, rm, chmod, docker restart, docker cp (write)"
  - "Multi-source evidence synthesis: Wave 1 evidence files + live server greps + cross-references in single RESEARCH.md"

requirements-completed: [RES-01]

# Metrics
duration: ~15min
completed: 2026-06-23
---

# Phase 1 Plan 03: Root Cause Analysis + RESEARCH.md Synthesis Summary

**Confirmed root cause via 4-hypothesis testing against Wave 1 evidence: primary C (22 _TOOL_HANDLERS vs 49 LLM-registered = 27 unreachable tools) + primary A (SOUL.md/SKILL.md document paradox) + secondary B (~120s stream ceiling) + NEW code bug (_unwrap_tool_output NameError breaks 40% of reports)**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-23T08:58:38Z (first ssh command)
- **Completed:** 2026-06-23T09:13:00Z (approximate — final SUMMARY commit)
- **Tasks:** 2 (both completed)
- **Files created:** 2 (root-cause-analysis.md 491 lines, RESEARCH.md 595 lines)
- **Files modified:** 0

## Accomplishments

- **RES-01 confirmed root cause:** Hypothesis D (combination) — A (PARTIAL) + B (PARTIAL) + C (CONFIRMED-PRIMARY). All 4 hypotheses tested against Wave 1 evidence with explicit verdicts.
- **Authoritative tool gap measured:** 22 entries in `_TOOL_HANDLERS` (direct Python introspection) vs 49 `_import_tool` calls in `__init__.py` (direct grep) = **27 modules pipeline-unreachable**, of which **17 are presale-critical** (Instagram, find_doctor_handles, run_tech_seo_audit, run_lighthouse, run_prescan, quick_overview, run_ads_*, geo_optimizer_tools, present_competitors, finalize_research, run_validation_check, post_report, 4 orchestration meta-tools).
- **SOUL.md vs SKILL.md paradox documented:** SOUL.md line 3 says "Свободный художник: сам выбирает инструменты" (free artist); SKILL.md lines 4-6 say "Python-controlled execution. LLM = data interpreter, NOT orchestrator". The contradiction itself is a contributing cause.
- **HIRING SIGNALS phase desync confirmed:** Phase runs in production (4+ sessions in archive) but ABSENT from `phases.py` source code — confirms code/production behavior mismatch.
- **15-item QC checklist proposed** for Phase 2: covers About data, Market section, competitor count, expert ФИО, Instagram for cosmetology, content themes %, content gaps severity, SMI URLs, forum pains, 3-year revenue dynamics, competitor cards, Whitefields matrix, 5-direction Strategy, Offer section.
- **Phase 2 architectural recommendation:** orchestrator-first (bypass `_TOOL_HANDLERS` for tool dispatch) over pipeline-extension (add 17 handlers to dict). Matches ROADMAP ORC-02 success criterion.
- **Phase 2 priority order established:** P0 fix `_unwrap_tool_output` bug → P1 build 3-pass orchestrator → P2 QC checklist → P3 wire 17 missing tools → P4 chunk long phases → P5 align SOUL/SKILL docs.
- **RESEARCH.md consolidated** as single readable admin-facing report (595 lines): Executive Summary + 6 numbered sections + 3 appendices. Addresses all RES-01..05 requirements.
- **Read-only verification passed:** All 6 investigated server files have mtimes older than plan start (2026-06-23T08:58:38Z). No server files modified.

## Task Commits

Per user instruction (single combined commit after both tasks), both tasks share one atomic commit:

1. **Task 1: Test 4 hypotheses against evidence (RES-01)** - `8a24c67` (docs) — combined commit with Task 2
2. **Task 2: Consolidate RESEARCH.md with Phase 2 recommendations** - `8a24c67` (docs) — same commit as Task 1

Both tasks write to two separate files (`evidence/root-cause-analysis.md` and `RESEARCH.md`), committed together as the plan's `files_modified` field specifies both.

**Plan metadata:** not yet committed (will be included in final metadata commit with SUMMARY.md, STATE.md, ROADMAP.md, REQUIREMENTS.md updates)

## Files Created/Modified

- `.planning/phases/01-research-diagnosis/evidence/root-cause-analysis.md` (491 lines) - Per-hypothesis testing with evidence citations and final root cause verdict. Sections: Executive Summary, Hypothesis A (PARTIAL), Hypothesis B (PARTIAL), Hypothesis C (CONFIRMED-PRIMARY), Hypothesis D (CONFIRMED), Confirmed Root Cause(s) with primary/secondary/amplifier breakdown, Server State Verification, Cross-Reference Summary.
- `.planning/phases/01-research-diagnosis/RESEARCH.md` (595 lines) - Consolidated Phase 1 research report with 6 sections + 3 appendices: Executive Summary (answers "why v4 skips tools" in plain language), Baseline Coverage (from Plan 01), Session Log Analysis (from Plan 02), Instagram Tool Test (from Plan 04), Root Cause Analysis (from Plan 03 Task 1), Recommendations for Phase 2 (mapped to ORC/QC requirements + 15-item QC checklist), Methodology, Appendices A/B/C.

## Decisions Made

1. **Hypothesis C is PRIMARY, not just contributing** — based on direct log evidence (`"No handler mapping"` in 3+ tools across 5 sessions from Plan 02), authoritative count (22 vs 49 via Python introspection and grep), and manual test (Plan 04 Instagram tool works in isolation but blocked in pipeline). The LLM is not "deciding to skip" — the pipeline physically rejects the call.

2. **Hypothesis A verdict PARTIAL, not CONFIRMED** — initially looked like pure prompt problem, but Plan 02 LLM-признания show LLM reacting to upstream failures rather than deciding to skip. The real A problem is the document paradox (SOUL.md permissive vs SKILL.md strict), not pure permissive language.

3. **Hypothesis B verdict PARTIAL, not CONFIRMED** — per-phase timeouts (120s for perplexity/html_build) align with stream ceiling, but only 5/28 skip points are LLM_DECISION. Most skips are code bugs or pipeline blocks, not model limits.

4. **Recommended orchestrator-first (Option 2) over pipeline-extension (Option 1)** for Phase 2 — Option 1 (add 17 handlers) doesn't fix the A paradox and creates maintenance burden. Option 2 (orchestrator bypasses `_TOOL_HANDLERS`) directly addresses ORC-02 and fixes root cause.

5. **15 QC checklist items (not 10, not 20)** — within QC-01's 10-20 range. Derived from: 6 consistently-missing sections (Plan 01) + 5 never-called critical tools + 4 Instagram/data-depth items. Each item has explicit pass criterion for measurable coverage.

6. **_unwrap_tool_output NameError labeled as NEW code regression** — independent of root cause but masks it. Plan 02 dated it to Jun 20-21 introduction. Must be Phase 2 P0 fix (before any orchestrator work) because it blocks 40% of current reports.

7. **Combined single commit for both tasks** — per user instruction "Commit: docs(phase-01): 01-03 root cause analysis + RESEARCH.md — RES-01". Both files are deliverables of the same plan and were committed together.

## Deviations from Plan

None - plan executed exactly as written.

The plan specified `ssh aim` for additional server evidence (read-only commands only). Used: `grep`, `head`, `wc`, `find`, `stat`, `cat`, `python3 -c` (introspection), `env`, `ls`. No write commands. Server state verified unchanged via stat mtimes.

Plan suggested `grep -c 'def _handler_' /opt/hermes/app/pipeline/engine.py` as one way to count handlers. Used a more authoritative approach instead: direct Python introspection (`python3 -c 'from app.pipeline.engine import _TOOL_HANDLERS; print(len(_TOOL_HANDLERS))'`) which returned 22 (the actual dict size). This is more accurate than grep because it counts the populated dict, not the source code patterns.

Plan noted CONTEXT.md "19 tools" as the `_TOOL_HANDLERS` count. Authoritative count is **22** (CONTEXT.md slightly stale). Plan 04 said "23 entries" — also slightly stale. The 22 figure is what production code actually has at plan execution time.

## Issues Encountered

- **`events.jsonl` files absent in sessions-archive** — Plan 02 also noted this for Session 4 crash. Cannot directly verify stream breaks from structured event logs. Used indirect evidence (per-phase timeouts in config.yaml + report sizes + Plan 02 quoted LLM interpretations) instead. Observability gap documented in RESEARCH.md Section 6.6 Limitations.
- **`register_all_tools()` returned None** when called directly — the function has side effects (populates a global registry) but doesn't return the tool list. Switched to counting `_import_tool` calls in `__init__.py` source instead, which gave the authoritative 49 figure.
- **Pre-existing git modifications** — many files in working tree have unstaged modifications from earlier sessions. Carefully staged only the two new files created by this plan (`root-cause-analysis.md` and `RESEARCH.md`) — did NOT use `git add -A` or `git add .` to avoid contaminating the commit with unrelated work.

## User Setup Required

None - no external service configuration required. This was a research-only plan with read-only server access.

## Next Phase Readiness

### Phase 1 COMPLETE — All deliverables ready for Phase 2

- **RESEARCH.md is the single source of truth** for Phase 2 planning. Read sections 1-5 (especially Section 5 Recommendations) before starting Phase 2 PLAN.md.
- **15-item QC checklist** in RESEARCH.md Section 5.4 — directly usable as Phase 2's QC-01 deliverable.
- **Phase 2 priority order** in RESEARCH.md Section 5.3 — P0 (_unwrap_tool_output fix) → P1 (orchestrator) → P2 (QC) → P3 (tools) → P4 (chunking) → P5 (docs).

### Blockers/Concerns for Phase 2

- **_unwrap_tool_output NameError MUST be fixed first** (P0) — blocking 40% of reports today. Phase 2 orchestrator cannot be validated while this bug turns reports into empty templates.
- **Document paradox (SOUL.md vs SKILL.md)** must be resolved as part of Phase 2 design — decide canonical architecture before writing orchestrator code. Recommend orchestrator-first (matches ORC-02).
- **17 missing tools in `_TOOL_HANDLERS`** — even with orchestrator-first approach, these tools need to be callable. Either add to dict (for fallback mode) or ensure orchestrator can invoke them directly via the LLM-registry path.
- **events.jsonl observability gap** — Phase 2 should add structured event logging so future investigations don't have to rely on mtime + interpretation text.
- **DeepSeek V4 Pro stream ceiling (~120s)** — Phase 2 must chunk long phases (perplexity, html_build) to stay under 90s per LLM call.

### Handoff to Phase 2

| Artifact | Path | Use |
|----------|------|-----|
| Root cause analysis | `evidence/root-cause-analysis.md` | Cite in Phase 2 PLAN.md rationale |
| RESEARCH.md (consolidated) | `RESEARCH.md` | Read top-to-bottom before Phase 2 planning |
| 15-item QC checklist | `RESEARCH.md` Section 5.4 | Use as QC-01 deliverable template |
| Phase 2 priority order | `RESEARCH.md` Section 5.3 | Use as Phase 2 plan sequence |
| Phase 2 architectural options | `RESEARCH.md` Section 5.2 | Decide Option 1 vs Option 2 in Phase 2 planning |

## Self-Check: PASSED

- FOUND: `.planning/phases/01-research-diagnosis/evidence/root-cause-analysis.md`
- FOUND: `.planning/phases/01-research-diagnosis/RESEARCH.md`
- FOUND: commit `8a24c67` in git log
- PASS: RES-01 marker in root-cause-analysis.md (line 1)
- PASS: All 4 hypothesis sections ("## Hypothesis A/B/C/D") present in root-cause-analysis.md
- PASS: Explicit verdicts (CONFIRMED/REFUTED/PARTIAL) in root-cause-analysis.md — A=PARTIAL, B=PARTIAL, C=CONFIRMED, D=CONFIRMED
- PASS: "## Confirmed Root Cause(s)" section in root-cause-analysis.md
- PASS: "Executive Summary" in RESEARCH.md
- PASS: "Root Cause" in RESEARCH.md
- PASS: "Recommendations for Phase 2" in RESEARCH.md
- PASS: All RES-01..05 markers in RESEARCH.md
- PASS: Server file mtimes older than plan start (SOUL.md 1782078325, engine.py 1782063956, phases.py 1781980704, __init__.py 1782076237, SKILL.md 1782063174, config.yaml 1781878925 — all before 2026-06-23T08:58:38Z)
- PASS: Task 1 automated verify command (file exists + RES-01 + Hypothesis [ABCD] + verdict markers)
- PASS: Task 2 automated verify command (file exists + Executive Summary + Root Cause + Recommendations + RES markers)

---

*Phase: 01-research-diagnosis*
*Plan: 03*
*Completed: 2026-06-23*
*Phase 1 status: 4/4 plans complete, 5/5 requirements addressed — ready for Phase 2*
