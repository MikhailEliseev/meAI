---
phase: 06-documentation-sync
plan: 02
subsystem: docs
tags: [skill-md, legacy-marker, orchestrator, qc-checklist, llm-prompt, deploy, docker, ssh]

# Dependency graph
requires:
  - phase: 02-3-pass-orchestrator-coverage-checklist
    provides: 3-pass cycle (three_pass.py) + 18-item QC_CHECKLIST v1.2.0 + ORCHESTRATOR_MODE env var
  - phase: 04-new-sections-data-depth
    provides: 26 _TOOL_HANDLERS (run_forum_pains + run_media_urls added, 24→26)
  - phase: 06-documentation-sync
    provides: SOUL.md v5 baseline terminology (3-pass orchestrator + QC-чеклист)
provides:
  - aim-scout SKILL.md v2.0.0 (was 1.0.0) — describes 3-pass orchestrator as primary mode + PipelineEngine 14 фаз as LEGACY fallback
  - phases.py module docstring carries LEGACY marker + ORCHESTRATOR_MODE reference (per D-06)
  - Server /opt/aim/AIM/hermes/skills/aim-scout/SKILL.md updated (host source for container ro-mount)
  - Server /opt/hermes/app/pipeline/phases.py updated (container writable path)
  - Server backups retained at .phase6-backup-20260624 suffixes for rollback
affects:
  - 06-documentation-sync (Plan 06-03 engine.py assertion test)
  - 07-test-on-3-niches (LLM sees new SKILL.md on next skill_view() call — no container restart needed)
  - Future readers of phases.py (LEGACY marker makes fallback status explicit)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - skill-md-dual-mode-description (primary + fallback mode with env-var switch)
    - legacy-marker-in-docstring (mark deprecated-but-used modules with LEGACY + primary alternative path)
    - host-source-deploy-for-ro-mount (when container path is read-only mount, update host source instead)
    - pipe-through-stdin-deploy (cat local | ssh aim "docker exec -i tee remote")

key-files:
  created: []
  modified:
    - AIM/hermes/skills/aim-scout/SKILL.md (131→193 lines, +193/-131, v1.0.0→v2.0.0)
    - AIM/hermes/app/pipeline/phases.py (docstring +6 lines, code unchanged)
    - /opt/aim/AIM/hermes/skills/aim-scout/SKILL.md (server host source, md5 matches local)
    - /opt/hermes/app/pipeline/phases.py (container writable path, md5 matches local)

key-decisions:
  - "D-04 fully applied: aim-scout SKILL.md now describes 3-pass orchestrator as primary mode (ORCHESTRATOR_MODE=1) with PipelineEngine 14 фаз as explicit fallback (ORCHESTRATOR_MODE=0/unset). 'Единственный способ запуска' claim removed."
  - "D-05 fully applied: 'FULL AUTO' language entirely removed (0 mentions, was 1 in v1.0.0). Replaced with 'автоматический режим для пользователя — без промежуточных вопросов'."
  - "D-06 fully applied: phases.py module docstring marked LEGACY with explicit ORCHESTRATOR_MODE switch reference + pointer to app/orchestrator/three_pass.py as primary mode."
  - "D-09 fully applied: 26 _TOOL_HANDLERS enumerated in 11-category catalogue (Search & Research / Scraping / Audit / Review / Content / People / Market / Media / Patients / Finance / Report) so LLM and human readers share same inventory."
  - "Container path /opt/hermes/skills/aim-scout/SKILL.md is read-only mount (same as /opt/hermes/skills/aim/SOUL.md in Plan 06-01). Deployed to host source /opt/aim/AIM/hermes/skills/aim-scout/SKILL.md instead — container sees update via the ro-mount immediately, no restart needed."
  - "phases.py deployed directly to container /opt/hermes/app/pipeline/ (writable Docker image layer path) — pipe-through-stdin pattern. Container Python 3.11 AST parse OK + import OK with phases_count=14."

patterns-established:
  - "SKILL.md dual-mode structure: YAML frontmatter → title with modes → РЕЖИМЫ ЗАПУСКА (primary + fallback) → tool catalogue → Iron Rules → Завершение. Applicable to other Hermes skills that span orchestrator + legacy paths."
  - "LEGACY docstring format: title gets '(LEGACY fallback)' suffix + 4-line notice paragraph referencing primary alternative + env var switch. Pure-docstring change, no code touched — safe to apply to other deprecated-but-used modules."
  - "Tool catalogue 11-category grouping: Search & Research (5) / Scraping (4) / Audit (3) / Review (1) / Content (2) / People (3) / Market (2) / Media (2) / Patients (1) / Finance (1) / Report (2) = 26 total. Matches _TOOL_HANDLERS dict size exactly."
  - "Plan verification regex caveat: `grep -c '^PHASE_...= Phase('` counts DATACLASS DEFINITIONS, not PHASES LIST ENTRIES. phases.py has 15 definitions (incl. unused PHASE_0_PREFLIGHT) but PHASES list contains 14. Future plans should use AST iter_child_nodes for list-length assertions, not grep."

requirements-completed: [SYN-01, SYN-03, SYN-04]

# Metrics
duration: 8min
completed: 2026-06-24
---

# Phase 6 Plan 02: aim-scout SKILL.md v2.0.0 + phases.py LEGACY marker Summary

**aim-scout SKILL.md rewritten v1.0.0→v2.0.0 (131→193 lines): "FULL AUTO pipeline" framing replaced with "3-pass LLM-orchestrator + 18-item QC checklist" (primary mode) plus PipelineEngine 14 фаз (LEGACY fallback); phases.py module docstring marked LEGACY with ORCHESTRATOR_MODE switch reference; both files deployed byte-for-byte (md5 matches) — SKILL.md to host source path /opt/aim/AIM/hermes/skills/aim-scout/ (ro-mount source for container), phases.py directly to container /opt/hermes/app/pipeline/; container healthy, 18 orchestrator mentions live, 0 FULL AUTO mentions, PHASES list still 14 entries (ids 0-13)**

## Performance

- **Duration:** ~8 min (453s)
- **Started:** 2026-06-24T04:30:36Z
- **Completed:** 2026-06-24T04:38:09Z
- **Tasks:** 3/3 complete (2 atomic commits + 1 deploy-only)
- **Files modified:** 4 (2 repo + 2 server-side)

## Accomplishments

- SKILL.md v2.0.0 (193 lines) written with 7 sections: YAML frontmatter → title with dual-mode framing → "РЕЖИМЫ ЗАПУСКА" (primary + fallback) → PipelineEngine 14 фаз table (LEGACY marker) → 26-tool catalogue in 11 categories → Iron Rules (6 rules, 3 reframed for orchestrator model) → Завершение (covers both modes)
- 3-pass orchestrator described as primary mode with references to `three_pass.py`, `pass_collect.py`, `pass_gap_analyze.py`, `pass_fill_assemble.py`, `niche_detector.py` — all 5 orchestrator source files cited
- QC_CHECKLIST v1.2.0 (18 items) referenced as coverage metric; PASS_THRESHOLD (80%) and Instagram HARD-FAIL rule for `CRITICAL_NICHES = ("plastic_surgery", "cosmetology")` documented
- 26 _TOOL_HANDLERS enumerated in 11-category table matching `_TOOL_HANDLERS` dict in `engine.py` exactly (verified line-by-line: 5+4+3+1+2+3+2+2+1+1+2 = 26)
- phases.py module docstring (lines 1-28) updated: title gains "(LEGACY fallback)" suffix, 4-line LEGACY notice added referencing ORCHESTRATOR_MODE switch + three_pass.py primary alternative + qc_checklist.py coverage metric, sequential-execution line tagged "(LEGACY behavior)"
- All Phase dataclasses, PHASES list, interpretation_prompt strings — UNTOUCHED. git diff shows only +6 -2 docstring lines
- Server-side deploy byte-for-byte verified: SKILL.md md5 `c3ab516930d26662fe4e755ac7b78500` matches across local / host source / container ro-mount; phases.py md5 `798d471627d70ab8f52180ff65a487b9` matches across local / container writable path
- Container Python 3.11 AST parse OK + import test returns `phases_count=14`; container health endpoint returns `status:ok, hermes:healthy`
- Server-side SKILL.md has 18 orchestrator mentions + 9 ORCHESTRATOR_MODE mentions + 0 FULL AUTO mentions + 0 "PipelineEngine — единственный" claims + 0 "Ты НЕ оркестрируешь" statements

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite aim-scout SKILL.md to v2.0.0 (orchestrator primary + legacy fallback)** — `026c715` (docs)
2. **Task 2: Add LEGACY marker to phases.py module docstring** — `89cf727` (docs)
3. **Task 3: Deploy SKILL.md and phases.py to aim-hermes container** — no commit (deploy-only, no local file changes per plan spec `<files>(no local file changes — deploy only)</files>`)

**Plan metadata:** (pending — final commit after STATE.md/ROADMAP.md updates)

## Files Created/Modified

- `AIM/hermes/skills/aim-scout/SKILL.md` — 193 lines (was 131). Complete rewrite per D-04 + D-05. NEW sections: "РЕЖИМЫ ЗАПУСКА" (primary + fallback mode description), "Каталог инструментов (26 _TOOL_HANDLERS)" (11-category table). MODIFIED sections: title (now dual-mode), Iron Rules (removed rules 1+7 "не оркестрируешь" + "единственный способ запуска", reframed rule 1 as "не прерываешься для подтверждений" without FULL AUTO language, added rule 6 "в оркестраторе LLM решает какие инструменты вызывать"), Завершение (covers both modes + final coverage check for orchestrator).
- `AIM/hermes/app/pipeline/phases.py` — 585 lines (was 577). Module docstring updated per D-06. NEW in docstring: "(LEGACY fallback)" in title, 4-line LEGACY notice paragraph referencing ORCHESTRATOR_MODE + three_pass.py + qc_checklist.py, "(LEGACY behavior — оркестратор в app/orchestrator/three_pass.py не использует эту последовательность)" annotation on sequential-execution line. UNCHANGED: Phase dataclass, all 15 Phase definitions (PHASE_0_PREFLIGHT through PHASE_13_PRESENTATION), PHASES list (14 entries), all interpretation_prompt strings.
- `/opt/aim/AIM/hermes/skills/aim-scout/SKILL.md` (server, host source) — 193 lines, 9398 bytes, md5 c3ab516930d26662fe4e755ac7b78500. Deployed via `cat local | ssh aim "tee /opt/aim/AIM/hermes/skills/aim-scout/SKILL.md"`. This is the ro-mount source the container reads at `/opt/hermes/skills/aim-scout/SKILL.md`.
- `/opt/hermes/app/pipeline/phases.py` (container, writable Docker image layer path) — 585 lines, md5 798d471627d70ab8f52180ff65a487b9. Deployed via `cat local | ssh aim "docker exec -i aim-hermes tee /opt/hermes/app/pipeline/phases.py"`.
- `/opt/aim/AIM/hermes/skills/aim-scout/SKILL.md.phase6-backup-20260624` (server, backup) — original v1.0.0 SKILL.md preserved for rollback.
- `/opt/hermes/app/pipeline/phases.py.phase6-backup-20260624` (container, backup) — original phases.py docstring preserved for rollback.

## Decisions Made

- **Removed "FULL AUTO" entirely per D-05:** Initial draft kept "FULL AUTO для пользователя" in Iron Rule #1 (meaning "fully automatic for the user"). Verification regex flagged it. Reframed as "Автоматический режим для пользователя — без промежуточных вопросов «продолжить?» / «показать?»." — semantically equivalent without using the deprecated phrase.
- **11-category tool catalogue grouping:** Plan suggested "12-category structure" but the actual list in `<tool_catalogue>` was 11 categories. Used the actual list (Search & Research, Scraping, Audit, Review, Content, People, Market, Media, Patients, Finance, Report) — verified sum equals 26.
- **SKILL.md deployed to host source path (not container path):** `/opt/hermes/skills/aim-scout/SKILL.md` in container is read-only (ro-mount), same as `/opt/hermes/skills/aim/SOUL.md` discovered in Plan 06-01. Deployed to host source `/opt/aim/AIM/hermes/skills/aim-scout/SKILL.md` instead. Container reads new content immediately via the ro-mount on next skill_view() call — no restart needed.
- **phases.py deployed directly to container writable path:** Unlike skills/, `/opt/hermes/app/pipeline/` is writable. Direct pipe-through-stdin deploy succeeded. Container Python 3.11 AST parse + import test pass immediately (lazy-import — no restart needed).
- **Container NOT restarted:** SKILL.md is loaded by LLM via `skill_view()` on demand. phases.py is lazy-imported by PipelineEngine on next execution. Both files activate on next LLM/session activity — no container restart required per plan spec. User is sleeping, restart deferred.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Initial SKILL.md draft kept one "FULL AUTO" mention**
- **Found during:** Task 1 (verification step V1)
- **Issue:** Initial draft included "FULL AUTO для пользователя" in Iron Rule #1. The plan's `must_haves.truths` requires "zero occurrences of the phrase 'FULL AUTO'" and D-05 explicitly says "Remove 'FULL AUTO' language entirely". The phrase was carried over from v1.0.0's framing without realizing it violated D-05.
- **Fix:** Reframed Iron Rule #1 to "Автоматический режим для пользователя — без промежуточных вопросов «продолжить?» / «показать?»." — preserves the "no interruptions" semantic without using the deprecated phrase.
- **Files modified:** `AIM/hermes/skills/aim-scout/SKILL.md` (1 line edit via Edit tool)
- **Verification:** Re-ran grep — FULL AUTO count now 0 (was 1 false positive).
- **Committed in:** `026c715` (part of Task 1 commit)

**2. [Rule 3 - Blocking] Container path /opt/hermes/skills/aim-scout/ is read-only**
- **Found during:** Task 3 (Step 1 backup attempt)
- **Issue:** `ssh aim "docker exec aim-hermes cp /opt/hermes/skills/aim-scout/SKILL.md /opt/hermes/skills/aim-scout/SKILL.md.phase6-backup-20260624"` failed with "Read-only file system". Same root cause as Plan 06-01's `/opt/hermes/skills/aim/SOUL.md` — the entire `/opt/hermes/skills/` tree is a Docker ro-mount from host source `/opt/aim/AIM/hermes/skills/`.
- **Fix:** Switched deploy target to host source path `/opt/aim/AIM/hermes/skills/aim-scout/SKILL.md`. Backed up the host source file first, then deployed new content via `cat local | ssh aim "tee /opt/aim/AIM/hermes/skills/aim-scout/SKILL.md"`. Container sees new content immediately via ro-mount.
- **Files modified:** `/opt/aim/AIM/hermes/skills/aim-scout/SKILL.md` (host source for container's ro-mount)
- **Verification:** md5 match local = host source = container ro-mount (`c3ab516930d26662fe4e755ac7b78500`). Container `/health` returns `status:ok`. Container grep `FULL AUTO /opt/hermes/skills/aim-scout/SKILL.md` returns 0. Container grep `(3-pass|orchestrator|оркестрат)` returns 18.
- **Committed in:** N/A (deploy-only task)

**3. [Rule 3 - Blocking] Plan verification regex `^PHASE_...= Phase(` counts dataclass definitions, not PHASES list entries**
- **Found during:** Task 2 (verification step V4)
- **Issue:** Plan's `<verify>` block specified `grep -c "^PHASE_[A-Z_0-9]* = Phase(" AIM/hermes/app/pipeline/phases.py | awk '{if ($1 == 14) ...}'`. The regex matches 15 Phase DEFINITIONS (PHASE_0_PREFLIGHT, PHASE_0_PERPLEXITY, ..., PHASE_13_PRESENTATION), but the plan's `must_haves.truths` says "phases.py PHASES list (14 entries, 0-13) is unchanged in structure". The 15-vs-14 discrepancy is because PHASE_0_PREFLIGHT is defined but NOT included in the PHASES list. This is a pre-existing condition in the file (verified via `git show HEAD:...` — also 15 definitions before my edit).
- **Fix:** Confirmed via direct Python import (`from app.pipeline.phases import PHASES; len(PHASES)`) that the PHASES LIST contains 14 entries with ids 0-13 — exactly what the plan's structural requirement specifies. The verification regex was buggy (counted definitions instead of list entries). No code change needed; structural requirement is met.
- **Files modified:** None (verification-only)
- **Verification:** `python3 -c "from app.pipeline.phases import PHASES; print(len(PHASES), [p.id for p in PHASES])"` returns `14 [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]`. Also container-side import: `ssh aim "docker exec aim-hermes python -c 'from app.pipeline.phases import PHASES; print(f\"phases_count={len(PHASES)}\")'"` returns `phases_count=14`.
- **Committed in:** N/A (no fix needed — verification regex was incorrect, actual code is correct)

---

**Total deviations:** 3 auto-fixed (1 bug + 2 blocking)
**Impact on plan:** All 3 deviations necessary for correct verification and deploy. No scope creep. Deviation #3 is a plan-verification-regex bug, not a code bug — future plans should use AST iter_child_nodes for list-length assertions rather than grep.

## Issues Encountered

- **Container ro-mount for skills/ tree:** This is now the 2nd time this has happened (Plan 06-01 with SOUL.md, now Plan 06-02 with aim-scout/SKILL.md). The pattern is consistent: `/opt/hermes/skills/*` paths are Docker ro-mounts from host source `/opt/aim/AIM/hermes/skills/*`. Future plans deploying to `/opt/hermes/skills/...` should preemptively use the host source path. Consider adding this to the deploy pattern in CLAUDE.md or project memory.
- **Plan verification regex vs must_haves truth misalignment:** Plan's `<verify>` regex for "14 Phase definitions" counted dataclass definitions (15) but must_haves truth was about "PHASES list (14 entries)". Verified the structural requirement is met via direct Python import — PHASES list has 14 entries with ids 0-13, which is what the plan actually wanted to enforce.

## User Setup Required

None — no external service configuration required. Container restart at user's preferred time will activate any remaining caches, but both SKILL.md (LLM skill_view() loads on demand) and phases.py (lazy-imported by PipelineEngine) are already live in the container's filesystem. Next LLM call that triggers aim-scout skill will load new v2.0.0 content.

## Next Phase Readiness

- **Plan 06-03 (engine.py assertion test + phantom phase grep removal)** can proceed — SOUL.md (Plan 06-01) + SKILL.md (Plan 06-02) + phases.py (Plan 06-02) all now describe the same 3-pass orchestrator + 14-фаз LEGACY fallback architecture. Plan 06-03 will close SYN-02 (engine.py _TOOL_HANDLERS assertion) and SYN-05 (final phantom phase grep audit across all docs).
- **Phase 7 (Test on 3 Niches)** readiness improved: SKILL.md now describes the orchestrator model the LLM will actually run in ORCHESTRATOR_MODE=1. When the user opts in to integration testing, the LLM's skill_view() will load the new v2.0.0 content on next call.
- **Phase 8 (Zero-Downtime Deploy):** Both files deployed via proven pipe-through-stdin pattern (SKILL.md via host source path for ro-mount, phases.py via container writable path). No container restart needed. Pattern validated for future Phase 8 deploys.

## Self-Check: PASSED

- Local file `AIM/hermes/skills/aim-scout/SKILL.md`: 193 lines (in 150-250 target range) — FOUND
- Local file `AIM/hermes/app/pipeline/phases.py`: 585 lines (was 577, +8 docstring lines) — FOUND
- Local commit `026c715`: Task 1 docs commit — FOUND
- Local commit `89cf727`: Task 2 docs commit — FOUND
- Server `/opt/aim/AIM/hermes/skills/aim-scout/SKILL.md`: md5 c3ab516930d26662fe4e755ac7b78500 (matches local) — FOUND
- Server container `/opt/hermes/skills/aim-scout/SKILL.md`: md5 c3ab516930d26662fe4e755ac7b78500 (ro-mount reflects host source) — FOUND
- Server container `/opt/hermes/app/pipeline/phases.py`: md5 798d471627d70ab8f52180ff65a487b9 (matches local) — FOUND
- Container `/health`: HTTP 200, status:ok, hermes:healthy — FOUND
- Container import `from app.pipeline.phases import PHASES`: phases_count=14 — FOUND
- Server SKILL.md grep `(3-pass|3-проходн|orchestrator|оркестрат)`: 18 matches — FOUND
- Server SKILL.md grep `ORCHESTRATOR_MODE`: 9 matches — FOUND
- Server SKILL.md grep `FULL AUTO`: 0 matches — FOUND
- Server phases.py grep `LEGACY`: 3 matches — FOUND
- Server phases.py grep `ORCHESTRATOR_MODE`: 1 match — FOUND

---
*Phase: 06-documentation-sync*
*Plan: 02*
*Completed: 2026-06-24*
