---
phase: 4
plan: 04-01
subsystem: hermes-tools/financials
tags: [financials, revenue, clinic-metrics, data-depth, dat-01, dat-04]
requires:
  - "AIM backend /api/companies/financials endpoint (existing)"
  - "bo.nalog.gov.ru via existing AIM pipeline (D-12)"
provides:
  - "find_company_financials._format_revenue_dynamics() helper"
  - "find_company_financials._format_clinic_metrics() helper"
  - "company.revenue_dynamics JSON field (dynamics_available, years, total_growth_pct, summary_text)"
  - "company.clinic_metrics JSON field (revenue_latest, profit_latest, employees, okved_codes, licenses, status, legal_address)"
affects:
  - "Hermes LLM-orchestrator (consumes new fields in Pass 3 for HTML report)"
  - "generate_html_report.py (will render these fields in Plan 04-06)"
tech-stack:
  added: []
  patterns:
    - "Strict 3-year gate (D-13) — partial data returns dynamics_available=False, no table"
    - "Inline _fmt_revenue_short — avoids circular dependency with HTML reporter"
    - "LLM-deferred OKVED translation — description field left empty, Pass 3 fills per D-21"
    - "Additive output fields — existing fields preserved, backward compatible"
key-files:
  created:
    - AIM/hermes/app/tools/test_financials_dynamics.py (12 unit tests)
  modified:
    - AIM/hermes/app/tools/find_company_financials.py (added 2 helpers + 2 output fields + inline _fmt_revenue_short)
decisions:
  - "D-13 enforced strictly — <3 years = NO partial-data table (returns honest reason only)"
  - "D-21 OKVED descriptions left empty for LLM to translate in Pass 3 — keeps tool deterministic"
  - "licenses=[] placeholder — nalog.ru has no license data; HTML reporter merges from run_prescan"
  - "Inline _fmt_revenue_short replicates generate_html_report logic — prevents circular import"
metrics:
  duration: 3.5min
  tasks_completed: 2
  files_touched: 2
  tests_added: 12
completed: 2026-06-24
---

# Phase 4 Plan 04-01: Extend find_company_financials (Revenue Dynamics + Clinic Metrics) Summary

**One-liner:** Added `_format_revenue_dynamics()` (strict 3-year gate per D-13) and `_format_clinic_metrics()` (LLM-deferred OKVED per D-21) helpers to `find_company_financials.py`; both wired into handler JSON output additively — backward compatible with all existing callers.

---

## What Was Built

### New module-level helpers (in `AIM/hermes/app/tools/find_company_financials.py`)

**`_format_revenue_dynamics(revenue_by_year: dict) -> dict`** (Task 1, DAT-01/D-12..14)

Builds a 3-year revenue dynamics block from the existing `revenue_by_year` data already returned by the AIM backend (nalog.ru source). Enforces strict 3-year gate per D-13.

- Empty / None / non-dict input → `{"dynamics_available": False, "reason": "нет данных о выручке"}`
- 1 or 2 years available → `{"dynamics_available": False, "reason": "доступно N год(а) — нужно минимум 3 для динамики"}` (no partial-data table)
- 3+ years → `{"dynamics_available": True, "years": [...], "total_growth_pct": ..., "summary_text": "Выручка выросла на 79.2% за 3 года (2.4 млрд → 3.4 млрд → 4.3 млрд)"}`
- More than 3 years → takes latest 3 only (sorted descending)
- Handles both growth (positive total_growth_pct) and decline (negative) cases
- Per-year `yoy_pct` formula: `((current - prior) / prior) * 100`, rounded to 1 decimal
- Oldest year in the 3-year window has `yoy_pct: None` (no prior year in window)
- Summary text in Russian for LLM blockquote consumption per D-14

**`_format_clinic_metrics(company: dict) -> dict`** (Task 2, DAT-04/D-21)

Structures clinic metadata for the About section. OKVED code descriptions intentionally left as empty strings — the Pass 3 LLM translates codes to human-readable specialization per Plan 04-05 (avoids stale hardcoded mapping).

- `revenue_latest` / `profit_latest`: prefer pre-computed `latest_revenue`/`latest_profit`, fall back to `_latest_value({year: amount})`
- `employees`: passthrough (backend may not return this — defaults to None)
- `okved_codes`: list of `{"code": "86.21", "description": ""}` dicts — description empty for LLM
- `licenses`: always `[]` — nalog.ru has no license data; HTML reporter merges from `run_prescan` site scrape
- `status`, `legal_address`: passthrough from backend response

### Handler output wiring

`handle_find_company_financials` JSON output now includes two new keys inside the `company` dict (additive — no existing fields removed):

```json
{
  "found": true,
  "company": {
    "inn": ..., "ogrn": ..., "name": ..., "full_name": ...,
    "status": ..., "okved_main": ..., "legal_address": ...,
    "latest_revenue": ..., "latest_profit": ...,
    "revenue_by_year": {...}, "profit_by_year": {...},
    "gross_profit_by_year": {...}, "operating_profit_by_year": {...},
    "revenue_trend": ..., "data_source": ...,
    "revenue_dynamics": {...},   // NEW (Plan 04-01)
    "clinic_metrics": {...}      // NEW (Plan 04-01)
  }
}
```

### Tests added (`AIM/hermes/app/tools/test_financials_dynamics.py`)

12 unit tests in 2 test classes — all passing:

- `TestFormatRevenueDynamics` (8 tests): empty dict, None input, 1-year strict gate, 2-year strict gate, 3-year growth case (+79.2%), 3-year decline case, >3-year truncation, year sorting
- `TestFormatClinicMetrics` (4 tests): full company dict, missing employees, missing OKVED, fallback to `_latest_value` helper

Test file stubs the `tools.registry` package via `sys.modules` manipulation so tests run locally without the `hermes-agent` package installed.

---

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (failing tests) | `ddec729` — `test(04-01): add failing tests for revenue dynamics + clinic metrics helpers` | ✓ |
| GREEN (implementation passes) | `6fd5273` — `feat(04-01): add _format_revenue_dynamics helper with strict 3-year gate` | ✓ |
| GREEN (Task 2 helpers + wiring) | `d14fd60` — `feat(04-01): add _format_clinic_metrics + wire both helpers into handler` | ✓ |
| REFACTOR | (skipped — implementation is clean, no duplication) | n/a |

All three TDD gate commits present in git log in correct order.

---

## Success Criteria Verification

- ✓ **DAT-01 SATISFIED (tool layer)**: `revenue_dynamics` block provides 3-year trend with YoY %, strict <3-year gate, summary text for LLM blockquote
- ✓ **DAT-04 SATISFIED (tool layer)**: `clinic_metrics` block structures clinic data for the About section; OKVED descriptions deferred to LLM (Pass 3 prompt in Plan 04-05)
- ✓ **D-12 (nalog.ru primary source)**: respected — tool uses existing AIM backend which queries bo.nalog.gov.ru; no new external calls
- ✓ **D-13 (strict <3-year rule)**: enforced — `dynamics_available=False` with honest Russian reason when <3 years
- ✓ **D-14 (table + blockquote format)**: `years[]` array provides table data; `summary_text` provides blockquote text for LLM
- ✓ **D-21 (OKVED to human language)**: `okved_codes[0].description = ""` — Pass 3 LLM translates per Plan 04-05 prompt
- ✓ **Backward compatible**: all existing output fields preserved; tool input schema unchanged (inn/ogrn only)

---

## Deviations from Plan

**None — plan executed exactly as written.** No auto-fixes needed (Rules 1-3 not triggered). No architectural changes (Rule 4 not triggered).

Minor implementation note: added inline `_fmt_revenue_short()` helper to replicate the formatting logic from `generate_html_report.py` rather than importing it. This avoids a circular dependency (the HTML reporter imports from tools, and the tool would import from the HTML reporter). The plan mentioned this option explicitly: "replicate the billion/million abbreviation logic inline".

---

## Known Stubs

**None.** Both helpers contain real logic — no hardcoded empty values that flow to UI rendering, no placeholder text, no TODO/FIXME markers. The intentionally empty fields (`okved_codes[0].description=""`, `licenses=[]`) are documented design decisions per D-21 and have a clear resolution path (Pass 3 LLM translation + run_prescan merge at HTML reporter layer).

---

## Threat Surface Scan

**No new threat surface introduced.** The trust boundary is unchanged — the tool still makes a single HTTP call to the existing AIM backend (`http://aim-app:8000/api/companies/financials`). The new helpers are pure local computation on data already returned by the existing API. No new endpoints, auth paths, file access patterns, or schema changes at trust boundaries.

The threat register entries in the plan (T-04-01-I/T/D/SC) are all `accept` disposition — confirmed accurate.

---

## Self-Check: PASSED

**Files verified to exist:**

- ✓ `AIM/hermes/app/tools/find_company_financials.py` (modified, 296 lines)
- ✓ `AIM/hermes/app/tools/test_financials_dynamics.py` (created, 168 lines)

**Commits verified in git log:**

- ✓ `ddec729` — test(04-01): add failing tests
- ✓ `6fd5273` — feat(04-01): _format_revenue_dynamics helper
- ✓ `d14fd60` — feat(04-01): _format_clinic_metrics + wiring

**Test results:**

- ✓ 12/12 unit tests pass (`python3 -m unittest app.tools.test_financials_dynamics`)
- ✓ AST parse succeeds
- ✓ Plan verification script passes for both Task 1 and Task 2
- ✓ Smoke test: handler output structure matches the reference "Выручка выросла на 79.2% за 3 года (2.4 млрд → 3.4 млрд → 4.3 млрд)" pattern

---

## Downstream Dependencies

**Plans that consume this plan's output:**

- **04-04-PLAN.md** (Pass 1+2 prompts + QC checklist): Pass 1 collection rules will instruct LLM to call `find_company_financials`; Pass 2 QC items 9-10 (revenue 3-year, clinic metrics) check the new JSON fields
- **04-05-PLAN.md** (Pass 3 prompt): LLM consumes `clinic_metrics.okved_codes[0]` and translates the code to Russian specialization per D-21
- **04-06-PLAN.md** (HTML Data Sections): `generate_html_report.py` reads `company.revenue_dynamics` and `company.clinic_metrics` to render the About section + revenue table

**Field contracts downstream plans can rely on:**

```python
# revenue_dynamics — when dynamics_available=True
{
    "dynamics_available": True,
    "years": [
        {"year": "2023", "revenue": 4300000000, "yoy_pct": 26.5},
        {"year": "2022", "revenue": 3400000000, "yoy_pct": 41.7},
        {"year": "2021", "revenue": 2400000000, "yoy_pct": None},
    ],
    "total_growth_pct": 79.2,
    "summary_text": "Выручка выросла на 79.2% за 3 года (2.4 млрд → 3.4 млрд → 4.3 млрд)",
}

# revenue_dynamics — when dynamics_available=False
{"dynamics_available": False, "reason": "доступно 2 год(а) — нужно минимум 3 для динамики"}

# clinic_metrics — always present
{
    "revenue_latest": int|None,
    "profit_latest": int|None,
    "employees": int|None,
    "okved_codes": [{"code": "86.21", "description": ""}],  # description LLM-filled
    "licenses": [],  # HTML reporter merges from run_prescan
    "status": "Действующее"|None,
    "legal_address": str|None,
}
```

---

*Phase 4 Plan 04-01 complete. Phase 4 Wave 1 proceeds with Plans 04-02 and 04-03 in parallel.*
