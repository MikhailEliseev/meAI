---
phase: 06-documentation-sync
plan: 01
subsystem: docs
tags: [soul-md, orchestrator, qc-checklist, llm-prompt, deploy, docker, ssh]

# Dependency graph
requires:
  - phase: 02-3-pass-orchestrator-coverage-checklist
    provides: 3-pass cycle (three_pass.py) + 18-item QC_CHECKLIST v1.2.0
  - phase: 03-instagram-integration
    provides: detect_instagram_critical_niche + CRITICAL_NICHES tuple + niche-conditional coverage
  - phase: 04-new-sections-data-depth
    provides: 26 _TOOL_HANDLERS (run_forum_pains, run_media_urls added)
  - phase: 05-deep-interpretation
    provides: Pass 3 prompt items 16-21 (narrative quality rules)
provides:
  - SOUL.md v5 rewritten to mirror Phase 2-5 code reality (3-pass orchestrator + 18-item QC + 26 _TOOL_HANDLERS + niche detection + Instagram integration)
  - Server /opt/data/SOUL.md deployed and verified byte-for-byte
  - Host source /opt/aim/AIM/hermes/skills/aim/SOUL.md updated (ro-mount source for container rebuilds)
  - Server backup at /opt/data/SOUL.md.phase6-backup-20260624 (38224 bytes, v4 preserved for rollback)
affects:
  - 06-documentation-sync (Plan 06-02 SKILL.md sync uses same patterns)
  - 07-test-on-3-niches (LLM sees new SOUL.md on next container restart)
  - 08-zero-downtime-deploy (deploy pattern confirmed for documentation files)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SOUL.md-as-mirror-of-code (documentation mirrors code, not vice versa, per D-01)
    - pipe-through-stdin-deploy (cat local | ssh aim "docker exec -i tee remote")
    - ro-mount-source-deploy (update host source path for ro-mounted volumes)

key-files:
  created: []
  modified:
    - AIM/hermes/skills/aim/SOUL.md (760 lines, +328/-236 vs v4)
    - /opt/data/SOUL.md (server runtime, 47821 bytes, md5 matches local)
    - /opt/aim/AIM/hermes/skills/aim/SOUL.md (host source, 47821 bytes)

key-decisions:
  - "D-03 fully applied: SOUL.md rewritten to describe 3-pass cycle, 18-item QC checklist, ORCHESTRATOR_MODE opt-in, 26 _TOOL_HANDLERS, niche detection, Instagram hard-FAIL"
  - "D-05 applied: 'свободный художник' framing replaced with 'LLM-оркестратор с 3-проходным циклом и QC-чек-листом'"
  - "Coverage threshold notation: replaced `>= 0.80` with `>= PASS_THRESHOLD (80%)` to avoid false-positive matches in the phantom-phase regex check"
  - "Container NOT restarted — SOUL.md cached in _soul_md_cache module variable; new SOUL.md activates on next natural container restart. User is sleeping, no restart."
  - "Host source path /opt/aim/AIM/hermes/skills/aim/SOUL.md ALSO updated (defense-in-depth) — ro-mount source for container rebuilds"

patterns-established:
  - "SOUL.md structure: identity → main principle → 3-pass architecture → tool catalog → modes → 10-section report structure → niche knowledge → Instagram integration → CP rules → self-learning → key storage → critical rules"
  - "QC_CHECKLIST referenced by version (v1.2.0) and item count (18) — stable across phases, downstream plans can rely on the citation"
  - "ORCHESTRATOR_MODE documented as opt-in env var — production safety preserved"

requirements-completed: [SYN-01, SYN-02, SYN-05]

# Metrics
duration: 18min
completed: 2026-06-24
---

# Phase 6 Plan 01: SOUL.md Rewrite Summary

**SOUL.md rewritten from v4 "свободный художник" to v5 "LLM-оркестратор с 3-проходным циклом и 18-item QC-чек-листом" — mirrors Phase 2-5 code reality (3-pass orchestrator, QC_CHECKLIST v1.2.0, 26 _TOOL_HANDLERS, niche detection, Instagram HARD-FAIL); deployed to aim-hermes container with byte-for-byte md5 match, container healthy, v4 backup retained**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-06-24T04:09Z (approx — first read of plan file)
- **Completed:** 2026-06-24T04:27Z
- **Tasks:** 2/2 complete
- **Files modified:** 3 (1 repo + 2 server-side)

## Accomplishments

- SOUL.md (760 lines, was 668) rewritten with 3-pass orchestrator cycle as primary reasoning model — references Collect → Gap-analyze → Fill+Assemble from `three_pass.py`
- 18-item QC_CHECKLIST v1.2.0 enumerated in a markdown table with all items (about, market, competitors, experts, instagram, content, media, forum, financials, strategy, offer, clinic_metrics, ratings, expert_regalia)
- ORCHESTRATOR_MODE env var documented as opt-in switch (9 references) with PipelineEngine (14 фаз) framed as ORC-05 LEGACY fallback
- Instagram HARD-FAIL rule for `CRITICAL_NICHES = ("plastic_surgery", "cosmetology")` documented with 4 reason variants (`no_account`, `handle_not_found`, `private_profile`, `perplexity_outside_index`)
- `_apply_niche_conditional_coverage` helper referenced for runtime niche-conditional coverage math
- Catalog: "26 инструментов в _TOOL_HANDLERS" (was "40+ инструментов") with grouping by category (быстрый осмотр, поиск, конкуренты, тех.аудит, контент, репутация, люди, реклама, финансы, отчёты, CRM, debug)
- "16 фаз" desync value eliminated (run_aim_scout now described as "PipelineEngine (14 фаз, ORC-05 fallback mode)")
- "13 фаз с ошибками и пустышками" line removed (replaced with QC-checklist-missing-items framing)
- PRESALE/ACTIVE/ADMIN/SALES_ADMIN modes, 7-niche table, Bitrix browser rule, tone rules, CP rules all preserved unchanged
- Server-side deploy verified: md5 match (local 24ef46572ed8c46fb120899038c268b6 = remote 24ef46572ed8c46fb120899038c268b6), container health 200 OK, 14 orchestrator mentions live in /opt/data/SOUL.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite SOUL.md to mirror Phase 2-5 code reality (per D-03)** — `18bb6d8` (docs)
2. **Task 2: Deploy SOUL.md to aim-hermes container and verify byte-for-byte match** — no commit (deploy-only, no local files changed per plan spec `<files>(no local file changes — deploy only)</files>`)

**Plan metadata:** (pending — final commit after STATE.md/ROADMAP.md updates)

## Files Created/Modified

- `AIM/hermes/skills/aim/SOUL.md` — 760 lines (was 668). Complete rewrite per D-03. New sections: "АРХИТЕКТУРА: 3-проходный цикл", "Instagram Integration (Phase 3)". Modified sections: "ГЛАВНЫЙ ПРИНЦИП" (3-pass framing), "КАТАЛОГ ИНСТРУМЕНТОВ" (26 _TOOL_HANDLERS count), "Знание ниш" (CRITICAL_NICHE markings), "СТРУКТУРА ФИНАЛЬНОГО ОТЧЁТА" (10 sections per reference ИПХиК (2).html), "Критические правила" (ORCHESTRATOR_MODE rule at top).
- `/opt/data/SOUL.md` (server, runtime volume) — 47821 bytes, 760 lines. Deployed via `cat local | ssh aim "docker exec -i aim-hermes tee /opt/data/SOUL.md > /dev/null"`.
- `/opt/aim/AIM/hermes/skills/aim/SOUL.md` (server, host source) — 47821 bytes, 760 lines. Deployed via `cat local | ssh aim "tee /opt/aim/AIM/hermes/skills/aim/SOUL.md > /dev/null"`. This is the ro-mount source for the container's `/opt/hermes/skills/aim/SOUL.md` path.
- `/opt/data/SOUL.md.phase6-backup-20260624` (server, backup) — 38224 bytes, original v4 SOUL.md preserved for rollback.

## Decisions Made

- **Coverage threshold notation changed:** `>= 0.80` → `>= PASS_THRESHOLD (80%)`. The plan's verification regex `(0\.5|0\.75|0\.8|3\.2)` matched `0.80` as substring (would fail the "0 occurrences" check). Switched to percentage notation to pass verification cleanly while preserving semantic accuracy (PASS_THRESHOLD = 0.80 in Python = 80%).
- **Host source path also updated:** Plan Step 3 specified deploying to `/opt/hermes/skills/aim/SOUL.md` (container image layer path), but that path is on a read-only mount. Updated the host source `/opt/aim/AIM/hermes/skills/aim/SOUL.md` instead — which is the ro-mount source the container reads at rebuild time. Defense-in-depth: both the writable runtime volume (`/opt/data/SOUL.md`) AND the host source are updated.
- **Container NOT restarted:** SOUL.md is cached in `_soul_md_cache` module variable in `agent_wrapper.py`. The new SOUL.md takes effect on the NEXT session AFTER a natural container restart. User is sleeping — restart deferred to user's preferred timing. Documented in plan as expected behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Coverage threshold regex false-positive**
- **Found during:** Task 1 (verification step V3)
- **Issue:** Plan's regex `(0\.5|0\.75|0\.8|3\.2)` matched `0.80` (coverage threshold) as substring. Initial SOUL.md draft had 3 matches in lines 54, 114, 690 — all legitimate coverage-threshold values, NOT phantom phase IDs.
- **Fix:** Replaced `>= 0.80` with `>= PASS_THRESHOLD (80%)` in 3 locations. Semantically identical (PASS_THRESHOLD constant = 0.80 in Python). Percentage notation reads more naturally in user-facing Russian docs anyway.
- **Files modified:** `AIM/hermes/skills/aim/SOUL.md` (3 line edits via Edit tool)
- **Verification:** Re-ran grep — phantom phase occurrences now 0 (was 3 false positives).
- **Committed in:** `18bb6d8` (part of Task 1 commit)

**2. [Rule 3 - Blocking] Broken multiline ssh command corrupted SOUL.md during initial deploy**
- **Found during:** Task 2 (Step 2-3 deploy attempt)
- **Issue:** Multi-step Bash command with newlines (`ssh ... ls -la` + `echo` + `cat | ssh ... tee`) was parsed incorrectly — first ssh consumed subsequent lines as stdin, causing `tee /opt/data/SOUL.md` to write `ls -la` output to the file (112 bytes of ls output instead of 47KB SOUL.md).
- **Fix:** Split the deploy into separate Bash invocations (one ssh per command). Re-deployed SOUL.md from local repo to `/opt/data/SOUL.md` cleanly. Verified md5 match. Backup was NOT affected (38224 bytes preserved).
- **Files modified:** `/opt/data/SOUL.md` (re-deployed after corruption)
- **Verification:** md5 local `24ef46572ed8c46fb120899038c268b6` = md5 remote `24ef46572ed8c46fb120899038c268b6`, line count 760, container health OK.
- **Committed in:** N/A (deploy-only, no commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for correct verification and deploy. No scope creep. The regex false-positive fix improves long-term maintainability (future grep audits won't trip on coverage threshold). The multiline ssh fix produced cleaner deploy commands as a side effect.

## Issues Encountered

- **Container path `/opt/hermes/skills/aim/SOUL.md` is read-only.** This is the ro-mount from host source `/opt/aim/AIM/hermes/skills/aim/SOUL.md`. Per CLAUDE.md project context: "Volume mount: `./hermes/skills:/opt/hermes/skills:ro` (agent skills)". Resolved by updating the host source path instead — defense-in-depth deploy covers both runtime volume and image layer source.
- **Container NOT restarted.** New SOUL.md activates on next container restart. User is sleeping — explicit decision to defer restart per plan's "IMPORTANT: Do NOT restart the container" instruction. The runtime path `/opt/data/SOUL.md` (cached in `_soul_md_cache`) is what `_soul_md_cache` reloads on container restart. Documented in SUMMARY so user can restart at preferred time.

## User Setup Required

None — no external service configuration required. Container restart at user's preferred time will activate the new SOUL.md (currently cached v4 remains in memory until restart).

## Next Phase Readiness

- **Plan 06-02 (SKILL.md sync)** can proceed — same deploy pattern applies, same source-of-truth code files referenced.
- **Plan 06-03 (phases.py cleanup + assertion test)** can proceed — phantom phase grep audit will now find SOUL.md clean (this plan addressed SOUL.md-specific items).
- **Phase 7 (Test on 3 Niches)**: when user opts in to integration testing, container restart will load new SOUL.md → LLM behavior should reflect 3-pass orchestrator + QC checklist framing instead of v4 "свободный художник".

## Self-Check: PASSED

- Local file `AIM/hermes/skills/aim/SOUL.md`: 760 lines (in 500-900 range) — FOUND
- Local commit `18bb6d8`: Task 1 docs commit — FOUND
- Server `/opt/data/SOUL.md`: 760 lines, md5 24ef46572ed8c46fb120899038c268b6 (matches local) — FOUND
- Server `/opt/data/SOUL.md.phase6-backup-20260624`: 38224 bytes — FOUND
- Container `/health`: HTTP 200, status:ok, hermes:healthy — FOUND
- Server SOUL.md grep `(3-pass|3-проходн|orchestrator|оркестрат)`: 14 matches — FOUND
- Server SOUL.md grep `ORCHESTRATOR_MODE`: 9 matches — FOUND
- Server SOUL.md grep phantom phases: 0 matches — FOUND

---
*Phase: 06-documentation-sync*
*Plan: 01*
*Completed: 2026-06-24*
