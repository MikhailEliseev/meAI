---
phase: 31-html-report-redesign
plan: 02
type: execute
subsystem: hermes
tags:
  - html
  - section-builders
  - data-driven
  - graceful-omission
  - test
depends_on:
  - 31-01
provides:
  - data-loading
  - section-builders
  - data-aware-nav
  - html-assembly
  - test-suite
affects:
  - AIM/hermes/app/tools/generate_html_report.py
  - AIM/tests/unit/test_html_report.py
tech-stack:
  added:
    - New JSON data sources (doctor_dossiers, instagram_content, smi_mentions, pagespeed)
    - 9 new section builders with graceful omission
  patterns:
    - Data-aware conditional navigation
    - Graceful omission (return "" when data missing)
    - CSS variables for all colors in builders
    - _esc() on all user-originated strings
    - rel="noopener noreferrer" on all target=_blank links
key-files:
  modified:
    - AIM/hermes/app/tools/generate_html_report.py
    - AIM/tests/unit/test_html_report.py
decisions:
  - "_build_about always renders if revenue/profit/legal_name exists; with truly minimal data (no financials), it correctly returns empty string"
  - "_build_nav now conditionally includes only links to sections that will render, based on available data"
  - "Old builders (_build_exec_summary, _build_financials, _build_ci_gaps, _build_recommendations) remain in file but removed from _build_html() assembly"
  - "Platform status table shows 'Не проверено' for unverified platforms — informative label, not a stub"
  - "29 tests total: 14 from PLAN-01 (1 updated for data-aware nav) + 15 new for PLAN-02 builders"
metrics:
  duration: 0
  completed_date: ""
  lines_added: 852
  lines_modified: 0
---

# Phase 31 Plan 02: Section Builders and Data-Aware HTML Assembly Summary

**One-liner:** Added 9 data-driven section builders with graceful omission, data-aware conditional navigation, and extended the test suite to 29 tests covering all 16 builders.

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend _load_session_data() for new JSON files, make _build_nav() data-aware | `271e93e` | AIM/hermes/app/tools/generate_html_report.py |
| 2 | Build 9 new section builders with graceful omission | `a21dc30` | AIM/hermes/app/tools/generate_html_report.py |
| 3 | Integrate builders into _build_html(), finalize test suite, verify backward compatibility | `83ded38` | AIM/hermes/app/tools/generate_html_report.py, AIM/tests/unit/test_html_report.py |

## What Was Built

### Task 1: Data Loading and Navigation
- `_load_session_data()` extended with optional loading loop for `doctor_dossiers.json`, `instagram_content.json`, `smi_mentions.json`, and `pagespeed.json`
- File absence is silent (no error, no warning) — graceful fallback
- JSON decode errors logged as warnings, data silently skipped
- `_build_nav()` rewritten as data-aware: 9 conditional nav anchors based on available data
- Always-present links: #about (renders when financial data exists)
- Conditional links: #market, #experts, #content-analysis, #media, #competitors, #whitefields, #presence, #strategy

### Task 2: 9 New Section Builders
All builders follow the graceful omission pattern — `return ""` at the top when required data is missing.

| Builder | Section | Data Source | Conditional |
|---------|---------|-------------|-------------|
| `_build_about` | 01 — О компании | `stage_1_financials` | revenue/profit/legal_name |
| `_build_market` | 02 — Рынок | `ci_analysis.feature_matrix` | Competitors present |
| `_build_experts` | 03 — Эксперты | `doctor_dossiers.doctors` | Doctor data exists |
| `_build_content` | 04 — Контент-анализ | `instagram_content` | IG content exists |
| `_build_media` | 05 — Медийное присутствие | `smi_mentions.articles` | SMI data exists |
| `_build_competitors` | Конкуренты | `ci_analysis.feature_matrix` | Competitors present |
| `_build_whitefields` | 06 — Белые поля | `ci_analysis.gaps/advantages` | CI gaps exist |
| `_build_presence` | 07 — Цифровое присутствие | `prescan.reviews.platforms` | Reviews exist |
| `_build_strategy` | 08 — Стратегия | `ci_analysis` multiple fields | CI data exists |
| `_build_offer` | 09 — Предложение AIM | Template-driven | Always renders |

**Enhanced:** `_build_competitors` now includes per-competitor detail cards with strengths/weaknesses after the comparison table.

### Task 3: Integration and Testing
- `_build_html()` section assembly updated to 15-builders in correct order
- Old builders (`_build_exec_summary`, `_build_financials`, `_build_ci_gaps`, `_build_recommendations`) removed from assembly (functions remain in file)
- Test suite extended from 14 to 29 tests (+15 new)
- New test class `TestNewBuilders` with safe try/except imports for forward compatibility
- `full_data` fixture extended with new data fields (doctor_dossiers, instagram_content, smi_mentions)
- `test_nav_links_match_sections` updated for data-aware nav behavior
- `test_minimal_session_has_core_sections` updated to match graceful omission behavior

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_minimal_session_has_core_sections expected _build_about to always render**
- **Found during:** Task 3 (test execution)
- **Issue:** The test asserted `'<section id="about">' in html` with minimal data, but `_build_about` correctly returns `""` when no revenue/profit/legal_name exists. With truly minimal data (`prescan: {}`), there is no financial data to display and the about section is gracefully omitted.
- **Fix:** Updated test to check for hero, offer, and footer presence (always-rendering sections) and assert about/experts/market are NOT present in minimal data. This correctly tests graceful omission.
- **Files modified:** `AIM/tests/unit/test_html_report.py`
- **Commit:** `83ded38`

**2. [Rule 3 - Blocking] gitignore pattern `hermes/` blocked `git add` for tracked file**
- **Found during:** Task 1 (commit)
- **Issue:** The `.gitignore` contains `hermes/` which matches `AIM/hermes/` at any directory depth. `git add AIM/hermes/app/tools/generate_html_report.py` was rejected despite the file being tracked.
- **Fix:** Used `git add -f` for the specific file. The file was already tracked — force-add only staged modifications, not new files.
- **Files modified:** None (git operation only)
- **Commit:** `271e93e`

**3. [Rule 3 - Blocking] cwd drift from worktree to main repo caused edits to land in wrong location**
- **Found during:** Task 1 (after first edit)
- **Issue:** A prior Bash call had `cd`'d to the main repo root. Subsequent Edit calls wrote to the main repo's copy instead of the worktree copy.
- **Fix:** Restored main repo file with `git checkout --`, then re-applied all edits from within the worktree directory after verifying cwd.
- **Files modified:** None (operation recovery only)

## Verification Results

**Test suite:** 29/29 passing
```bash
PYTHONPATH=AIM/hermes/app python3 -m pytest AIM/tests/unit/test_html_report.py -x -v --noconftest
```

**Automated checks (Task 1):**
- `doctor_dossiers`, `instagram_content`, `smi_mentions`, `pagespeed` loading blocks found ✓
- `_build_nav` accepts data parameter ✓
- All 9 conditional nav links (#about through #strategy) present in source ✓

**Automated checks (Task 2):**
- All 9 new builder functions exist ✓
- All builders (except `_build_offer`) have `return ""` graceful omission ✓
- All 10 section IDs (`about` through `offer`) present in source ✓

**Success criteria check:**
1. `_load_session_data()` reads 4 new optional JSON files (graceful fallback) ✓
2. 9 new section builders created, all with graceful omission ✓
3. `_build_nav()` dynamically includes only links to sections with data ✓
4. `_build_html()` assembles 15 sections in correct order, filtering empty strings ✓
5. 29 tests passing including graceful omission and backward compatibility ✓
6. Minimal session data produces valid HTML with hero, offer, footer — no errors ✓
7. All `target="_blank"` links have `rel="noopener noreferrer"` ✓
8. Handle function and registry registration remain unchanged ✓

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries introduced. All user data in new builders is escaped with `_esc()`. All external SMI links use `rel="noopener noreferrer"`.

## Known Stubs

None — all builders are fully wired. Platform status table entries "— Не проверено" are informative labels showing absence of data (not stubs — they accurately reflect the scan state).

## Self-Check: PASSED

- [x] `AIM/hermes/app/tools/generate_html_report.py` — FOUND (1631 lines, plan min: 1500)
- [x] `AIM/tests/unit/test_html_report.py` — FOUND (394 lines, plan min: 200)
- [x] Commit `271e93e` — FOUND (Task 1)
- [x] Commit `a21dc30` — FOUND (Task 2)
- [x] Commit `83ded38` — FOUND (Task 3)
- [x] All 29 tests pass (14 original + 15 new)
- [x] No file deletions across all commits
