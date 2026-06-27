---
phase: 22-hermes-first-communication-flow
reviewed: 2026-06-01T09:00:00Z
depth: quick
files_reviewed: 3
files_reviewed_list:
  - AIM/hermes/skills/aim/SOUL.md
  - AIM/hermes/app/agent_wrapper.py
  - AIM/hermes/tests/test_presale_flow.py
findings:
  critical: 0
  warning: 3
  info: 1
  total: 4
status: issues_found
---

# Phase 22: Code Review Report

**Reviewed:** 2026-06-01T09:00:00Z
**Depth:** quick
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Phase 22 redesigned Hermes PRESALE mode from a "parallel-first fire-everything" approach into an 8-step conversational dialogue. The changes are primarily in SOUL.md (prompt/design) and `agent_wrapper.py` (`_presale_prompt()`), plus a new test file.

Three warnings were found: one ordering constraint in the PRESALE flow where `present_competitors` (Step 5) requires a `lead_id` that is only created by `collect_contact` (Step 8); one documentation gap where SOUL.md instructs Hermes to extract output fields that the actual `run_seo_audit` tool does not return; and one test fragility issue where regex-based source parsing silently skips tests on failure.

No blockers — the lead_id ordering issue will cause a recoverable tool error (not data loss or security breach), and the missing output fields can be compensated by Hermes via the tool's other outputs or by asking the client.

## Warnings

### WR-01: `present_competitors` requires `lead_id` that is not yet created at Step 5

**File:** `AIM/hermes/skills/aim/SOUL.md:109`, `AIM/hermes/app/tools/present_competitors.py:58-59`
**Severity:** WARNING
**Issue:** The PRESALE flow in SOUL.md instructs Hermes to call `present_competitors(lead_id, status, competitors)` at Step 5 (line 109). However, `present_competitors` (present_competitors.py:58-59) REQUIRES a valid `lead_id` — it returns `{"error": "lead_id is required"}` if the field is missing or empty. The tool's own schema description (present_competitors.py:124) states "Lead ID from collect_contact result", but `collect_contact` is only called at Step 8 (SOUL.md line 160). The `lead_id` is not available anywhere in Steps 1-5.

When Hermes attempts to call `present_competitors` at Step 5 without a `lead_id`, the tool will fail with a validation error. This will break the dialogue flow — Hermes will need to recover by either skipping the step or calling `collect_contact` early (which contradicts the flow's principle of "сначала покажи ценность, потом собирай контакт").

**Fix:** Two options:
1. **Reorder:** Move `present_competitors` to after `collect_contact` (Step 8), or
2. **Pre-create lead:** Call `collect_contact` at Step 2 with minimal data (just `website`) to obtain a `lead_id` early, then update the contact details at Step 8. The tool description in SOUL.md line 262 says `collect_contact` optionally takes `name`, `source` — it can be called with just `website` to create a lead skeleton. However, this approach needs to be explicitly documented in SOUL.md so Hermes knows to do it.
3. **Make lead_id optional:** Modify `present_competitors` to accept without `lead_id` (store against the session instead), or auto-create a lead if none exists.

The cleanest fix is option 2 — update SOUL.md Step 2 or Step 5 to note: "Если `lead_id` ещё не создан — сначала вызови `collect_contact` только с полем `website` чтобы создать досье, потом обновишь контакт на шаге 8."

### WR-02: SOUL.md Step 2 instructs Hermes to extract fields not returned by `run_seo_audit`

**File:** `AIM/hermes/skills/aim/SOUL.md:64-67`, `AIM/hermes/app/tools/run_seo_audit.py:153-212`
**Severity:** WARNING
**Issue:** SOUL.md Step 2 (lines 64-67) tells Hermes to extract `specialization`, `city`, and `services` from the `run_seo_audit` result. However, the actual tool's compacted output (`_compact_audit_result`, lines 188-211) only returns: `wow` (patients_per_month, time_to_result_weeks, cost_per_patient_rub), `market` (competitive_intensity, digital_maturity, niche_size), `competitors` (list of name/url), `insights`, `opportunities`, `actions`, and `meta`. The `_compact_quick_result` function similarly lacks these fields.

The SOUL.md "Знание ниш" section (line 427) mentions that `run_seo_audit` triggers `service_extractor.py` internally to determine specialization, but the determined specialization is not included in the compacted output sent to Hermes. Hermes will look for `specialization`, `city`, and `services` fields in the tool result, find nothing, and be unable to follow the Step 2 instructions as written.

**Fix:** Either:
1. Add `specialization`, `city`, and `services` fields to the compacted output in `_compact_audit_result` and `_compact_quick_result` (pull from the raw API response before compaction), or
2. Update SOUL.md Step 2 to acknowledge these aren't in the tool output: "Если специализация, город и услуги не вернулись от `run_seo_audit` — спроси у клиента или попробуй извлечь из `market` / `competitors`."

### WR-03: `run_ci_analysis` requires `client_revenue` and `client_rating` with no specified source

**File:** `AIM/hermes/skills/aim/SOUL.md:115,221`
**Severity:** WARNING
**Issue:** Step 6 (line 115) calls `run_ci_analysis(url, specialization, city, services, competitors, client_revenue, client_rating)`. The tool catalog (line 221) lists `client_revenue` (int, required) and `client_rating` (float, required) as inputs. However, no earlier step in the flow specifies how Hermes obtains these values:
- `run_seo_audit` (Step 2) does not return revenue or rating for the client
- The SEO audit compacted output has no client financial fields
- No Step instructs Hermes to ask the client for annual revenue or rating

Without these values, Hermes may call `run_ci_analysis` with `client_revenue=0` or fabricated numbers, or the tool may reject the call, or the CI analysis quality may degrade.

**Fix:** Add to SOUL.md Step 5 or Step 6 a note about sourcing these values: "Если `client_revenue` не известен — оцени по конкурентам (20-40% от средней выручки 2-3 ближайших конкурентов). Если `client_rating` не известен — используй средний рейтинг по рынку (из `competitor_comparison` поля `run_seo_audit`)."

## Info

### IN-01: Test fixture uses fragile regex-based source parsing with silent skip on failure

**File:** `AIM/hermes/tests/test_presale_flow.py:54-71`
**Severity:** INFO
**Issue:** The `presale_prompt` fixture parses `agent_wrapper.py` source code with regex to extract the `_presale_prompt()` return string. Both regex patterns are structurally fragile — they depend on the function having a docstring followed by a `return """..."""` statement. If the function is refactored (e.g., docstring removed, intermediate variable introduced before return, additional `"""` in a comment), the regex will silently fail to match and `pytest.skip` will be called (line 71), causing 4 tests to disappear from the test run without any error or explicit failure.

**Fix:** Consider one of:
1. Use Python's `ast` module to parse the function and extract string literals from `Return` nodes — this is structural and survives refactoring
2. Add an assertion/check in the fixture so that if both regexes fail, a clear warning is emitted (but the test still skips for now since `hermes_state` can't be imported)
3. Accept the fragility but document it with a comment in the test file explaining when to update the regex

---

_Reviewed: 2026-06-01T09:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
