---
phase: 4
plan: 04-04
subsystem: orchestrator
tags: [orchestrator, pass1, pass2, qc-checklist, prompts, d-25, sec-04, sec-05, dat-01, dat-02, dat-04, dat-05]

# Dependency graph
requires:
  - "04-01: find_company_financials revenue_dynamics + clinic_metrics output fields"
  - "04-02: find_doctor_handles structured_regalia field"
  - "04-03: run_forum_pains + run_media_urls tools (registered in _TOOL_HANDLERS)"
provides:
  - "QC_CHECKLIST with 18 items (was 15) — items 16 clinic_metrics, 17 ratings, 18 expert_regalia"
  - "VERSION 1.2.0 in qc_checklist.py"
  - "PASS_MIN_ITEMS=15 (80% of 18, rounded up)"
  - "_build_pass_collect_prompt extended with phase4_rules block"
  - "_CHECKLIST_PROMPT_TEMPLATE references 18 items"
  - "_fallback_report defaults to 18 total/missing"
  - "CoverageReport.total_items default = 18"
affects:
  - "04-05 (Pass 3 prompt Strategy/Offer/Whitefields rendering — reads collected Phase 4 data)"
  - "04-06 (HTML Data Sections — renders QC items 16-18 status)"
  - "04-08 (deploy — all 5 files ship in docker cp)"
  - "three_pass.py _apply_niche_conditional_coverage (Rule 1 auto-fix — log message now uses dynamic total)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive prompt block (phase4_rules) — existing base_prompt + instagram_rule + closing unchanged"
    - "Versioned checklist constant (QC_CHECKLIST) — downstream modules read len() dynamically"
    - "Stale-log auto-fix (Rule 1) — log format string uses %d/%d with report.total_items instead of hardcoded /15"

key-files:
  created: []
  modified:
    - AIM/hermes/app/orchestrator/qc_checklist.py
    - AIM/hermes/app/orchestrator/pass_collect.py
    - AIM/hermes/app/orchestrator/pass_gap_analyze.py
    - AIM/hermes/app/orchestrator/coverage_reporter.py
    - AIM/hermes/app/orchestrator/three_pass.py

key-decisions:
  - "PASS_MIN_ITEMS = 15 (80% of 18 = 14.4 → round up) — preserves QC-04 80% threshold semantics"
  - "Items 16-18 universally applicable (not niche-conditional) — clinic_metrics/ratings/regalia apply to all clinics regardless of niche"
  - "Item 8 refined to require concrete URLs from 5 target СМИ (Forbes, RBC, Vademecum, Kommersant, ТАСС) — was vague '>=3 mentions with URLs'"
  - "Item 11 refined to require YoY % AND total growth % with explicit D-13 strict <3-year rule handling"
  - "phase4_rules block placed AFTER instagram_rule, BEFORE closing — preserves Instagram-critical priority ordering"
  - "Rule 1 auto-fix: three_pass.py log message '/15' → '/%d' with dynamic total — directly caused by Task 1 expansion (was correct before, misleading after)"

patterns-established:
  - "Pattern: versioned checklist constant + dynamic len() reads — no hardcoding totals in downstream modules"
  - "Pattern: additive prompt blocks — new rules append, existing blocks untouched for backward compatibility"
  - "Pattern: Rule 1 auto-fix scope — stale references in dependencies ARE in scope when directly caused by current task changes"

requirements-completed: [SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, DAT-01, DAT-02, DAT-04, DAT-05]

# Metrics
duration: 8min
completed: 2026-06-24
---

# Phase 4 Plan 04-04: Expand Pass 1+2 Prompts + QC Checklist 15→18 Summary

**QC checklist expanded from 15 to 18 items (clinic_metrics DAT-04, ratings DAT-05, expert_regalia SEC-04); Pass 1 prompt gains phase4_rules block instructing LLM to call run_media_urls/run_forum_pains/find_company_financials/run_review_platforms; Pass 2 template + fallback defaults + CoverageReport all updated to reference 18 items.**

## Performance

- **Duration:** ~8 min (PLAN_START 00:20:32Z → PLAN_END 00:28:05Z, 453s)
- **Started:** 2026-06-24T00:20:32Z
- **Completed:** 2026-06-24T00:28:05Z
- **Tasks:** 2 (Task 1: QC_CHECKLIST expansion; Task 2: Pass 1+2 prompts + coverage_reporter + three_pass log fix)
- **Files modified:** 5 (4 plan-scoped + 1 auto-fix in three_pass.py)
- **Commits:** 2

## Accomplishments

- **QC_CHECKLIST** grew from 15 to 18 items. Three new items added with explicit pass_criteria + source citations:
  - **Item 16 (clinic_metrics, DAT-04, D-21):** revenue + profit + employees + licenses + ОКВЭД codes (LLM translates in Pass 3) from `find_company_financials.clinic_metrics` block
  - **Item 17 (ratings, DAT-05, D-22-23):** ratings on at least 2 platforms (ПроДокторов + Яндекс.Карты) via `run_review_platforms`, each with rating + review count
  - **Item 18 (expert_regalia, SEC-04, D-08):** ≥3 doctors with `structured_regalia` (degree КМН/ДМН, academic_title профессор/доцент, experience_years, education) from `find_doctor_handles`
- **Existing items refined:**
  - **Item 8** (SMI mentions): "concrete URLs from target СМИ (Forbes, RBC, Vademecum, Kommersant, ТАСС) — via run_media_urls tool" (was vague "≥3 mentions with URLs")
  - **Item 11** (Revenue dynamics): "3-year trend with YoY % AND total growth % — from find_company_financials revenue_dynamics block. If <3 years: status='missing' with reason 'недостаточно данных для динамики' (D-13 strict rule)" (was generic "3-year trend with year-over-year %")
- **VERSION** bumped 1.1.0 → 1.2.0; comment block documents Phase 4 changes for traceability
- **PASS_MIN_ITEMS** updated 12 → 15 (preserves QC-04 80% threshold: 18 × 0.8 = 14.4 → round up)
- **Pass 1 prompt** (`_build_pass_collect_prompt`) extended with new `phase4_rules` block (5 numbered rules). The block is placed AFTER `instagram_rule` and BEFORE `closing` — preserves Instagram-critical priority ordering. The return statement concatenates: `base_prompt + instagram_rule + phase4_rules + closing`
- **Pass 2 prompt** (`_CHECKLIST_PROMPT_TEMPLATE`) updated: "ПОЛНЫМ 15-item" → "ПОЛНЫМ 18-item", "Для КАЖДОГО из 15 пунктов" → "из 18 пунктов", JSON template `"total": 15` → `"total": 18`
- **Fallback paths** updated: `_ensure_summary` default total 15 → 18; `_fallback_report` missing/total 15 → 18; `run_pass_gap_analyze` exception-catch gap_report total 15 → 18
- **CoverageReport** default `total_items` 15 → 18; docstring "Always 15" → "Always 18 (len of QC_CHECKLIST after Phase 4 expansion)"; inline comment `# 15` → `# 18 after Phase 4 expansion`
- **Rule 1 auto-fix (three_pass.py):** HARD FAIL log message format string `/15` → `/%d` with dynamic `report.total_items` argument. Was directly caused by Task 1 expansion — the literal "15" was correct before, misleading after. Two docstring occurrences of "14 vs 15" also updated to "17 vs 18 after Phase 4 expansion" for accuracy.

## Task Commits

Each task was committed atomically:

1. **Task 1:** `feat(04-04): expand QC_CHECKLIST from 15 to 18 items (D-25)` — `373adc2`
2. **Task 2:** `feat(04-04): extend Pass 1 prompt + update Pass 2 + coverage_reporter for 18 items` — `ee6e42a`

## Files Modified

| File | Lines Changed | Reason |
|------|---------------|--------|
| `AIM/hermes/app/orchestrator/qc_checklist.py` | +49/-9 | Items 16-18 added, items 8 + 11 refined, VERSION bump, PASS_MIN_ITEMS update |
| `AIM/hermes/app/orchestrator/pass_collect.py` | +22/-2 | `phase4_rules` block added, return statement extended |
| `AIM/hermes/app/orchestrator/pass_gap_analyze.py` | +12/-12 | Template 15→18 (3 places), fallback defaults 15→18 (3 places), docstring + comments updated |
| `AIM/hermes/app/orchestrator/coverage_reporter.py` | +3/-3 | `total_items` default 15→18, docstring + comment updated |
| `AIM/hermes/app/orchestrator/three_pass.py` | +4/-4 | Rule 1 auto-fix: HARD FAIL log `/15` → `/%d` dynamic, 2 docstring refs `14 vs 15` → `17 vs 18` |

## Decisions Made

- **PASS_MIN_ITEMS = 15** (not 14). Pure 80% × 18 = 14.4 — Python `int()` truncates to 14, but rounding up (15) is more conservative: requires 83% actual coverage, leaves less room for false PASS. Aligns with QC-04's "80% threshold" intent (closer to 80% from above than from below).
- **Items 16-18 universally applicable** (not `conditional_on_niche`). Per plan: "Items 16-18 are universally applicable — no changes needed [to `is_item_applicable`]." Clinic metrics, ratings, and expert регалии apply to every clinic regardless of niche.
- **`phase4_rules` placed AFTER `instagram_rule`** in the Pass 1 prompt. Instagram-critical rule is the load-bearing collection priority (Phase 3 HARD FAIL); Phase 4 rules are additive and come after to preserve LLM attention hierarchy.
- **Rule 1 auto-fix scope applied to `three_pass.py`** despite plan listing only 4 files in `files_modified`. The "/15" log message became directly misleading after Task 1's checklist expansion (was correct before, incorrect after). Plan's regression check explicitly says "_apply_niche_conditional_coverage in three_pass.py still works" — behavior works correctly, log message format string was the only stale reference. Auto-fixed per Rule 1 (incorrect output directly caused by current task).
- **Item 8 + 11 refinement scope:** Plan said "Refine existing items 8 and 11 to match Phase 4 depth". Refined pass_criteria now references concrete Phase 4 tool/field names (`run_media_urls`, `find_company_financials revenue_dynamics block`, D-13 strict rule). This makes the LLM's self-evaluation more accurate.

## Phase 4 Collection Rules Block (Pass 1)

The new `phase4_rules` block instructs the LLM to call 5 tools with specific purpose:

```text
ПРАВИЛА СБОРА ДАННЫХ (Phase 4):
1. run_media_urls — вызови ОБЯЗАТЕЛЬНО для 5 целевых СМИ: Forbes, RBC,
   Vademecum, Kommersant, ТАСС. [секция Media (05)]
2. run_forum_pains — вызови для сбора страхов пациентов с ПроДокторов,
   Otzovik, IRecommend, Woman.ru. [секция Content Analysis (04)]
3. find_company_financials — вызови с INN клиента. Смотри поля
   revenue_dynamics (3-летняя динамика) и clinic_metrics. Если
   dynamics_available=False — НЕ показывай секцию динамики (D-13).
4. run_review_platforms — вызови для рейтингов: ПроДокторов +
   Яндекс.Карты минимум (DAT-05).
5. find_doctor_handles — ответ содержит structured_regalia (degree,
   academic_title, experience_years, education). [секции 03 + 04]
```

## Verification Results

| Check | Result |
|-------|--------|
| qc_checklist.py: VERSION == '1.2.0' | OK |
| qc_checklist.py: len(QC_CHECKLIST) == 18 | OK |
| qc_checklist.py: PASS_MIN_ITEMS == 15 | OK |
| qc_checklist.py: item 16 'Clinic metrics (DAT-04)' present | OK |
| qc_checklist.py: item 17 'Ratings on 2 platforms (DAT-05)' present | OK |
| qc_checklist.py: item 18 'Expert регалии from site scrape (SEC-04)' present | OK |
| qc_checklist.py: item 8 refined (concrete URLs from 5 СМИ) | OK |
| qc_checklist.py: item 11 refined (YoY %, D-13 strict rule) | OK |
| qc_checklist.py: CRITICAL_NICHES unchanged ('plastic_surgery', 'cosmetology') | OK |
| qc_checklist.py: item 5 `conditional_on_niche=True` preserved | OK |
| qc_checklist.py: applicable_items('plastic_surgery') == 18 items | OK |
| qc_checklist.py: applicable_items('dental') == 17 items (item 5 filtered) | OK |
| qc_checklist.py: is_item_applicable(16/17/18, any niche) == True | OK |
| qc_checklist.py: render_checklist_for_llm() includes items 16, 17, 18 | OK |
| pass_collect.py: phase4_rules block added | OK |
| pass_collect.py: mentions run_media_urls, run_forum_pains, find_company_financials, run_review_platforms, structured_regalia | OK |
| pass_collect.py: return statement includes phase4_rules | OK |
| pass_gap_analyze.py: template 'ПОЛНЫМ 18-item QC checklist' | OK |
| pass_gap_analyze.py: template 'Для КАЖДОГО из 18 пунктов' | OK |
| pass_gap_analyze.py: template JSON 'total': 18 | OK |
| pass_gap_analyze.py: _fallback_report total=18, missing=18 | OK |
| pass_gap_analyze.py: _ensure_summary default total=18 | OK |
| pass_gap_analyze.py: run_pass_gap_analyze exception fallback total=18 | OK |
| coverage_reporter.py: CoverageReport().total_items == 18 | OK |
| coverage_reporter.py: calc_coverage(gap_18_items) → 18/18 PASS | OK |
| three_pass.py: HARD FAIL log now reads 'filled=17/18' (dynamic) | OK |
| three_pass.py: HARD FAIL still triggers for critical niche + item 5 missing | OK |
| three_pass.py: _apply_niche_conditional_coverage identity-preserving (returns same instance) | OK |
| AST parse: all 5 modified files syntax valid | OK |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale log message in three_pass.py after Task 1 expansion**
- **Found during:** Task 1 verification (regression test emitted "filled=17/15")
- **Issue:** `_apply_niche_conditional_coverage` in `three_pass.py` had hardcoded `/15` in the HARD FAIL warning log format string. After Task 1 expanded `QC_CHECKLIST` from 15 to 18 items, this became misleading (would always print `/15` regardless of actual `report.total_items`).
- **Fix:** Changed format string from `"filled=%d/15"` to `"filled=%d/%d"` with `report.total_items` as additional argument. Also updated 2 docstring references from "14 vs 15" to "17 vs 18 after Phase 4 expansion".
- **Files modified:** `AIM/hermes/app/orchestrator/three_pass.py`
- **Verification:** Regression test now prints "filled=17/18" (accurate); HARD FAIL behavior still triggers correctly for critical niche + missing item 5.
- **Committed in:** `ee6e42a` (Task 2 commit — included with related prompt + reporter updates)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Auto-fix was directly caused by Task 1 changes (the `/15` was correct before, misleading after). Plan's regression check "_apply_niche_conditional_coverage still works" — behavior preserved, only the log format string updated for accuracy.

## Issues Encountered

None beyond the auto-fixed log message above.

## User Setup Required

None — pure Python code changes, no external services or environment variables.

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-04-04-T (Tampering — LLM could mark items 16-18 filled without calling tools) | accept — existing soft QC gate pattern. LLM is trusted to self-evaluate honestly; hard-FAIL override only exists for item 5 (Phase 3 niche-critical). Items 16-18 follow the same soft-gate semantics as items 1-15. |
| T-04-04-D (DoS — more items → longer Pass 2 LLM call) | accept — `_PASS_GAP_TIMEOUT=240s` (up from 180s in 02-02). 18 items vs 15 is ~20% more work — well within the 60s headroom. |
| T-04-04-E (EoP — not applicable) | accept — pure prompt expansion, no privilege change. |
| T-04-04-SC (Supply chain — no new packages) | accept — pure Python string/dataclass changes in existing modules. |

## Next Phase Readiness

- **Ready for downstream consumers:**
  - **04-05 (Pass 3 prompt):** Can now reference items 16-18 in Pass 3 instructions (e.g., "translate OKVED codes to human language for item 16", "consume `patient_fears_hint` from `run_forum_pains` for item 9 + section 04 rendering", "render `structured_regalia` in Experts section for item 18")
  - **04-06 (HTML Data Sections):** QC Coverage section will now show 18 items (3 more rows in the table); new CSS classes not required (existing `qc-filled`, `qc-missing`, `qc-partial`, `qc-not-applicable` cover all states)
  - **04-08 (Deploy):** All 5 modified files ship via `docker cp` to `aim-hermes` container. No new pip dependencies, no schema migrations, no container restart needed (Python lazy-imports).
- **No blockers** — code is local-only (not deployed), deployment happens in Plan 04-08 (Wave 5).

## Self-Check: PASSED

- ✓ `AIM/hermes/app/orchestrator/qc_checklist.py` — file exists, AST parses cleanly, 359 lines (was 303 — +56 for items 16-18 + comment expansion)
- ✓ `AIM/hermes/app/orchestrator/pass_collect.py` — file exists, AST parses cleanly, 247 lines (was 223 — +24 for phase4_rules block)
- ✓ `AIM/hermes/app/orchestrator/pass_gap_analyze.py` — file exists, AST parses cleanly, 309 lines (was 301 — +8 net for Phase 4 docstring + 15→18 replacements)
- ✓ `AIM/hermes/app/orchestrator/coverage_reporter.py` — file exists, AST parses cleanly, 196 lines (unchanged line count — 3 in-place edits)
- ✓ `AIM/hermes/app/orchestrator/three_pass.py` — file exists, AST parses cleanly (Rule 1 auto-fix target)
- ✓ Commit `373adc2` — FOUND in git log (Task 1: QC_CHECKLIST expansion)
- ✓ Commit `ee6e42a` — FOUND in git log (Task 2: Pass 1+2 prompts + coverage_reporter + three_pass log)
- ✓ All plan verification assertions pass (both Task 1 and Task 2 inline checks)
- ✓ Regression: Phase 3 niche helpers + Instagram HARD FAIL preserved
- ✓ Final log message reads "filled=17/18" (was misleading "/15" before auto-fix)

---
*Phase: 04-new-sections-data-depth*
*Completed: 2026-06-24T00:28:05Z*
