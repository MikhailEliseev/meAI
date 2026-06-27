---
phase: 04-new-sections-data-depth
plan: 02
subsystem: experts
tags: [regalia, doctor-handles, site-scrape, structured-data, merge-helper]

# Dependency graph
requires:
  - phase: 03-instagram-integration
    provides: run_instagram_content batch response shape (top_by_followers, profiles) — consumed by _merge_doctor_data
provides:
  - "_extract_structured_regalia(text) → typed dict (degree, academic_title, experience_years, education)"
  - "_merge_doctor_data(site_doctors, instagram_data) → merged list with source field (both|site|instagram_only)"
  - "_names_match(name_a, name_b) → initials-aware ФИО matcher (И.И. ↔ Иван Иванович)"
  - "structured_regalia field on every doctor dict in find_doctor_handles output"
  - "_EMPTY_STRUCTURED_REGALIA module-level singleton for default fallbacks"
affects: [04-05 (Pass 3 prompt регалии), 04-06 (HTML Experts section), 04-07 (HTML competitor cards)]

# Tech tracking
tech-stack:
  added: []  # pure Python stdlib (re, json) — no new packages
  patterns:
    - "Typed regalia extraction alongside existing keyword list (backward compat)"
    - "Initials-aware Russian ФИО matching (last name exact + initials by first letter)"
    - "Deterministic merge helper exposed for LLM consumer (no LLM call inside)"

key-files:
  created:
    - AIM/hermes/app/tools/test_regalia_extraction.py
  modified:
    - AIM/hermes/app/tools/find_doctor_handles.py

key-decisions:
  - "Initials-aware matching (И.И. ↔ Иван Иванович) chosen over exact normalized match — plan verification expects Иванов И.И. to match Иванов Иван Иванович; last name exact + token-prefix initials handles this without LLM"
  - "_EMPTY_STRUCTURED_REGALIA module-level singleton reused across handler fallback paths (5 doctors_context.append branches) to avoid per-doctor allocation"
  - "_merge_doctor_data uses first-match-wins per site doctor; multi-match ambiguities deferred to LLM consumer (per D-09 'LLM resolves')"
  - "structured_regalia added ADDITIVELY to _scrape_doctor_profile return — existing regalia keyword list preserved for backward compatibility"
  - "Merge helper exposed at module level (not invoked in handler) — Instagram data not available at handler time, comes from separate run_instagram_content call"

patterns-established:
  - "Pattern: typed-field extraction helper + keyword-list field coexist (additive, not replacing)"
  - "Pattern: deterministic name matcher with initials awareness as pre-LLM filter"
  - "Pattern: module-level empty-default singleton for structured dict fallbacks"

requirements-completed: [SEC-04]

# Metrics
duration: 10min
completed: 2026-06-24
---

# Phase 4 Plan 04-02: Extend find_doctor_handles — Structured Регалии + Merge Helper Summary

**Typed regalia extraction (degree/title/experience/education) + initials-aware ФИО merge helper for combining site-scraped doctors with Instagram metrics**

## Performance

- **Duration:** ~10 min (608s)
- **Started:** 2026-06-23T23:54:31Z
- **Completed:** 2026-06-24T00:04:39Z
- **Tasks:** 2 (Task 1 TDD: RED→GREEN; Task 2: wiring + merge helper)
- **Files modified:** 2 (1 source file, 1 test file created)
- **Commits:** 3 (test RED, feat GREEN, feat wiring+merge)

## Accomplishments

- `_extract_structured_regalia(text)` extracts typed regalia fields (degree КМН/ДМН, academic_title with priority профессор > доцент > академик > член-корр, experience_years via 3 regex patterns, education list with denylist filtering) — 20 unit tests pass
- `_scrape_doctor_profile` now returns `structured_regalia` dict alongside existing `regalia` keyword list (backward compatible — no removal of existing fields)
- `handle_find_doctor_handles` injects `structured_regalia` into every doctor dict in output (from site scrape or empty default for Perplexity-only doctors)
- `_merge_doctor_data(site_doctors, instagram_data)` produces 3 cohorts: `both` (site+IG matched), `site` (регалии only), `instagram_only` (IG not on site) — exposed at module level for Pass 3 LLM import
- `_names_match` initials-aware matcher enables "Иванов И.И." ↔ "Иванов Иван Иванович" deterministic resolution

## Task Commits

Each task was committed atomically (TDD gate preserved):

1. **Task 1 RED:** `test(04-02): add failing tests for structured_regalia extraction` — `34c38fe`
2. **Task 1 GREEN:** `feat(04-02): implement _extract_structured_regalia helper` — `25e452f`
3. **Task 2 wiring + merge:** `feat(04-02): wire structured_regalia + add _merge_doctor_data helper` — `8eb14aa`

TDD gate compliance: `test(...)` commit precedes `feat(...)` commit. ✓

## Files Created/Modified

- `AIM/hermes/app/tools/test_regalia_extraction.py` — 20 unit tests covering empty/none, КМН/ДМН, профессор/доцент/академик/член-корр priority, стаж N лет / N лет опыта / опыт работы N лет, окончил/образование patterns, denylist filtering, dedup, 3-entry cap, 100-char truncation
- `AIM/hermes/app/tools/find_doctor_handles.py` — Added `_extract_structured_regalia`, `_normalize_full_name`, `_names_match`, `_merge_doctor_data` helpers + `_EMPTY_STRUCTURED_REGALIA` constant. Wired `structured_regalia` into `_scrape_doctor_profile` return and `handle_find_doctor_handles` output. 214 lines added (1205→1542 net +337 with Task 1 + Task 2 combined).

## Decisions Made

- **Initials-aware matching chosen over exact normalized match.** Plan verification expects "Иванов И.И." to match "Иванов Иван Иванович". Pure normalization (lowercase + remove dots/hyphens) leaves "иванов и и" vs "иванов иван иванович" which don't match as strings. `_names_match` adds: last name MUST match exactly + subsequent tokens compared with initial-aware logic (single letter matches first letter of full token) + subset accepted (shorter side omits tokens).
- **First-match-wins in _merge_doctor_data per site doctor.** If two Instagram profiles match a site doctor, the first one wins; the LLM consumer resolves any remaining ambiguities from conversation context (per D-09 "LLM responsible for resolution").
- **structured_regalia preserved as additive field.** Plan explicitly requires backward compatibility: existing `regalia` keyword list field stays. New `structured_regalia` dict adds typed fields alongside it.
- **Merge helper exposed at module level, NOT invoked in handler.** Instagram data comes from a separate `run_instagram_content` call — not available when `handle_find_doctor_handles` runs. The merge function is imported by Pass 3 orchestrator/LLM after both tool calls complete.

## Regex Patterns Used

**Experience years (priority order, first match wins):**
1. `r"стаж\s+(?:работы\s+)?(\d+)\s*лет"` — matches "стаж 15 лет" / "стаж работы 20 лет"
2. `r"(\d+)\s*лет\s+опыта"` — matches "15 лет опыта"
3. `r"опыт\s+работы\s+(\d+)\s*лет"` — matches "опыт работы 12 лет"

**Education (both patterns run, results merged):**
1. `r"окончил[а]?\s+([^.]{5,100})"` — matches "окончил МГМУ" / "окончила РНИМУ"
2. `r"образование[:\s]+([^.]{5,100})"` — matches "Образование: МГМСУ"

**Education denylist (false-positive filter):**
- `работу`, `врачом`, `стаж`, `обучение`, `повышени`, `лекцию`, `практик`, `курс`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Initials-aware matching required for plan verification**
- **Found during:** Task 2 verification
- **Issue:** Initial `_normalize_full_name` produced `"иванов и и"` vs `"иванов иван иванович"` which don't string-match, but plan verification test expected `"Иванов И.И."` to match `"Иванов Иван Иванович"` and merge their data
- **Fix:** Added `_names_match(name_a, name_b)` helper with initials-aware logic — last name MUST match exactly; subsequent tokens compared position-by-position with initial (single letter) matching first letter of full token; subset matches accepted. Updated `_merge_doctor_data` to use `_names_match` instead of dict-lookup by normalized string.
- **Files modified:** `AIM/hermes/app/tools/find_doctor_handles.py`
- **Verification:** All 4 plan verification assertions pass (Иванов matched with metrics, Сидоров instagram_only, Петров site-only, 3+ merged entries)
- **Committed in:** `8eb14aa` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Auto-fix was required to satisfy plan verification assertions. No scope creep — added helper makes the deterministic matching smarter without invoking LLM (preserves D-09 contract).

## Issues Encountered

None beyond the auto-fixed matching bug above.

## User Setup Required

None — pure Python stdlib code, no external services or environment variables.

## Next Phase Readiness

- **Ready for downstream consumers:**
  - Plan 04-05 (Pass 3 prompt) can instruct LLM to read `structured_regalia` from each doctor dict and render in Experts section
  - Plan 04-06 (HTML rendering) can render регалии typed fields in section 03
  - Plan 04-07 (competitor cards) can call `_merge_doctor_data` to combine site + IG data per competitor
- **No blockers** — code is local-only (not deployed), deployment happens in Plan 04-08 (Wave 5)

## Self-Check: PASSED

- `AIM/hermes/app/tools/find_doctor_handles.py` — file exists, AST parses cleanly, 1542 lines
- `AIM/hermes/app/tools/test_regalia_extraction.py` — file exists, 20 tests pass
- Commit `34c38fe` — FOUND in git log (test RED)
- Commit `25e452f` — FOUND in git log (feat GREEN)
- Commit `8eb14aa` — FOUND in git log (feat wiring+merge)
- All plan verification assertions pass (both Task 1 and Task 2 inline checks)

---
*Phase: 04-new-sections-data-depth*
*Completed: 2026-06-24*
