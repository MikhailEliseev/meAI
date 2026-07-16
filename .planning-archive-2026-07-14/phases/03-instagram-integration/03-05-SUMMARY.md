---
phase: 03-instagram-integration
plan: 05
subsystem: orchestrator
tags: [html-report, design-system, honest-reporting, no-instagram-block, qc-conditional-render, pass-3-prompt, d-07, d-08, ig-04]

# Dependency graph
requires:
  - phase: 03-instagram-integration
    provides: 03-06 — CoverageReport.not_applicable_items field + _apply_niche_conditional_coverage helper populating it
  - phase: 03-instagram-integration
    provides: 03-02 — state.collected_data["niche_detection"]["niche"] populated by mini-call
  - phase: 03-instagram-integration
    provides: 03-03 — CRITICAL_NICHES tuple + is_niche_instagram_critical helper
  - phase: 02-3-pass-orchestrator-coverage-checklist
    provides: ORC-04 — honest-data principle ("данные недоступны" never fabricated)
provides:
  - generate_html_report._build_no_instagram_block(reason) helper — renders design-system HTML block for 4 reason variants per D-07
  - generate_html_report._maybe_build_no_instagram_block(niche, instagram_data) gatekeeper — returns block HTML or empty string based on niche criticality + instagram_data shape
  - generate_html_report._build_report_html — extended signature with niche + instagram_data kwargs (backward compatible)
  - generate_html_report._build_qc_coverage_section — reads metadata['not_applicable_items'] canonical source (per Fix #2) + renders ⚪ icon + qc-not-applicable class with neutral styling
  - generate_html_report.handle_generate_html_report — extracts niche + instagram_data from kwargs with safe defaults
  - pass_fill_assemble._build_prompt — items 5 + 6 added instructing LLM to pass niche + instagram_data kwargs to generate_html_report
  - D-07 SATISFIED (HTML side): transparent "Instagram: данные недоступны — {reason}" block renders in sections 03 + 04 for critical-niche clinics with missing Instagram
  - D-08 SATISFIED (HTML side): QC Coverage section reads not_applicable_items from canonical CoverageReport field (populated by Plan 03-06) and renders with ⚪ icon + gray styling distinct from missing
  - IG-04 SATISFIED: if a clinic has no Instagram, the report notes this honestly (with specific reason) and does not block remaining phases — Phase 2 soft QC gate (warning only) + Phase 3 honest block rendering work together
  - Checker issue #1 CLOSED: Pass 3 prompt explicitly instructs LLM to pass niche + instagram_data kwargs
affects: [phase-04, phase-08]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure Python stdlib (ast, json, logging)
  patterns:
  - "Honest-reporting HTML block: separate <div class='no-instagram-block surface-card'> with scoped <style> — explains WHY data is missing instead of silently omitting the section"
  - "Lazy import of qc_checklist helpers inside HTML rendering: avoids top-level orchestrator dependency for the generate_html_report module (which is also called from PipelineEngine ORC-05 fallback path)"
  - "Reason variant mapping dict: 4 known reason keys (no_account/handle_not_found/private_profile/perplexity_outside_index) → Russian user-facing text; generic fallback for unknown reasons (preserves raw reason, XSS-escaped)"
  - "Canonical source consumption: _build_qc_coverage_section reads metadata['not_applicable_items'] (populated upstream by Plan 03-06 helper) — no status-scan fallback per Fix #2"
  - "CSS class for de-emphasis: .qc-not-applicable { color: var(--text-dim); opacity: 0.6 } — visually distinct from filled (✅ green) / partial (🟡 yellow) / missing (❌ red)"
  - "F-string brace escaping for inline CSS: {{...}} in f-strings to avoid Python expression-placeholder interpretation (Rule 1 auto-fix after smoke test caught NameError)"
  - "Two-new-kwargs backward compat pattern: _build_report_html(data, title, coverage_metadata=None, niche='unknown', instagram_data=None) — defaults preserve Phase 2 caller behavior"
  - "Prompt-level data-contract closure: Pass 3 prompt items 5+6 explicitly name the kwargs (niche, instagram_data) + source paths (state.collected_data.niche_detection.niche, Pass 1 tool-call history) — no implicit LLM guess"

key-files:
  created: []
  modified:
  - AIM/hermes/app/tools/generate_html_report.py (+275 lines net: _build_no_instagram_block + _maybe_build_no_instagram_block helpers + _build_report_html signature extension + section 03/04 conditional render + _build_qc_coverage_section not_applicable branch + handle_generate_html_report kwargs extraction + module docstring)
  - AIM/hermes/app/orchestrator/pass_fill_assemble.py (+22 lines: items 5+6 in _build_prompt return + module docstring update)

key-decisions:
  - "Block design reuses design-system surface-card + metric-tag-warning + text-dim classes — consistent with qc-coverage-section aesthetic, matches dual theme (light monochrome + dark Art Deco gold)"
  - "Block scoped under .no-instagram-block CSS selector with [data-theme='dark'] variant — matches qc-coverage-section's dark-theme override pattern (rgba(201,169,110,0.05) bg + 0.18 border)"
  - "Reason variant mapping uses dict lookup with generic fallback — preserves raw reason text XSS-escaped for unknown variants (defensive against future reason types)"
  - "_maybe_build_no_instagram_block gatekeeper returns empty string for non-critical niches — matches D-07 spec: 'For non-critical niches, the block is NOT rendered — section appears without Instagram content (no warning needed)'"
  - "Reason selection: instagram_data is None → 'no_account'; analyzed_count == 0 → 'perplexity_outside_index'; default fallback → 'handle_not_found' (most common real-world case)"
  - "Block appended INSIDE section 03/04 HTML (not as a standalone section) — contextual to doctors/content. If section doesn't render (no data), block doesn't render either. Confirmed by integration smoke test 7."
  - "Lazy import of is_niche_instagram_critical inside _maybe_build_no_instagram_block — avoids top-level orchestrator dependency. If qc_checklist unavailable (legacy deploy), helper returns empty string safely."
  - "qc_checklist.not_applicable_items consumed as canonical source (per Fix #2) — NO fallback to scan metadata['items'] for status=='not_applicable'. Plan 03-06 is the single source of truth."
  - "CSS class .qc-not-applicable with opacity 0.6 + var(--text-dim) color — visually clearly distinct from .qc-missing (no opacity change, normal weight) and .qc-partial (no opacity change)"
  - "Summary line N/A count note uses · separator: 'QC Coverage: 13/14 (92.8%) — PASS · 1 item N/A (не critical ниша)' — matches existing summary line punctuation style"
  - "Items 5+6 placed AFTER item 4 in Pass 3 prompt — preserves existing 4-item task list ordering (rules: fill gaps → generate_html_report → honest mark → coverage_metadata). New kwargs are downstream refinements."
  - "Both new prompt items use ОБЯЗАТЕЛЬНО передай параметр language — matches item 4 mandatory language for consistency. Defensive defaults on the receiver side (niche='unknown', instagram_data=None) protect against LLM forgetting."

patterns-established:
  - "Reason-variant mapping pattern for honest-reporting blocks: dict of known variants → user-facing text, generic fallback for unknowns. Reusable for future 'data unavailable' scenarios (e.g., no SMI mentions, no forum pains found)."
  - "Canonical source consumption in HTML rendering: read populated fields directly (not_applicable_items from CoverageReport), avoid re-deriving from raw items scan. Separation of concerns: business logic populates, HTML renders."
  - "Conditional block rendering via gatekeeper function: _maybe_build_X(args) → returns HTML or empty string. Caller doesn't need to know the gate logic; just appends the result to section HTML."
  - "Prompt-level data-contract closure: when an orchestrator-side helper accepts new kwargs, the corresponding Pass 3 prompt must explicitly name them + their source path. Defensive defaults on receiver side handle LLM forgetting."

requirements-completed: [IG-04]

# Metrics
duration: 8.6min
completed: 2026-06-23
---

# Phase 3 Plan 05: HTML no-Instagram Block + QC not_applicable Rendering + Pass 3 Prompt Wiring Summary

**generate_html_report.py gained `_build_no_instagram_block(reason)` + `_maybe_build_no_instagram_block(niche, instagram_data)` helpers that render a design-system-consistent "Instagram: данные недоступны — {reason}" block with 4 reason variants (no_account / handle_not_found / private_profile / perplexity_outside_index) inside sections 03 (Experts) + 04 (Content Analysis) — but ONLY for critical niches (plastic_surgery, cosmetology) with missing Instagram data; `_build_qc_coverage_section` now reads `metadata['not_applicable_items']` (populated by Plan 03-06 `_apply_niche_conditional_coverage`) as the canonical source and renders those items with a distinct ⚪ icon + `.qc-not-applicable` CSS class (gray, opacity 0.6) separate from filled/missing/partial; Pass 3 prompt in pass_fill_assemble.py gained items 5 + 6 explicitly instructing the LLM to pass `niche` + `instagram_data` kwargs to `generate_html_report`, closing the cross-plan data-contract gap flagged by Checker issue #1.**

## Performance

- **Duration:** ~8.6 min (start 18:25:13Z, end 18:33:48Z)
- **Tasks:** 3/3 complete (all `type="auto"`, no checkpoints)
- **Files modified:** 2 (generate_html_report.py, pass_fill_assemble.py)
- **Files created:** 0
- **Commits:** 3 task commits + 1 Rule 1 auto-fix commit + 1 final docs commit (this SUMMARY)

## Accomplishments

- `_build_no_instagram_block(reason: str) -> str` helper added near `_build_qc_coverage_section`
- `_maybe_build_no_instagram_block(niche, instagram_data) -> str` gatekeeper added — returns block HTML for critical niche + missing data, empty string otherwise
- 4 reason variants encoded in `reason_map` dict (per D-07):
  - `no_account` → "У клиники нет аккаунта Instagram"
  - `handle_not_found` → "Instagram-handle врача не найден на сайте клиники"
  - `private_profile` → "Instagram-профиль приватный — данные недоступны"
  - `perplexity_outside_index` → "Instagram-handle не в индексе Perplexity — данные недоступны (вызовы были произведены, ни один не вернул данных)"
  - Generic fallback for unknown reasons: `f"Instagram: данные недоступны — {_esc(str(reason))}"`
- `_build_report_html` signature extended:
  - `niche: str = "unknown"` (4th arg, default preserves Phase 2 behavior)
  - `instagram_data: dict | None = None` (5th arg)
  - Both kwargs backward-compatible (defaults handle Phase 2 callers)
- Section 03 (Ключевые врачи) conditionally renders the no-Instagram block when `_maybe_build_no_instagram_block` returns non-empty
- Section 04 (Контент-анализ сайта) conditionally renders the same block
- `_build_qc_coverage_section` updated:
  - Reads `metadata.get("not_applicable_items", [])` (canonical source per Fix #2)
  - Builds `not_applicable_by_id` dict
  - Adds new `elif item_id in not_applicable_by_id:` branch BEFORE `elif item_id in missing_by_id:`
  - Uses ⚪ icon + `qc-not-applicable` CSS class
  - Reason text: `f' — <em class="qc-reason">N/A для данной ниши: {_esc(str(reason))}</em>'`
  - Default fallback when reason empty: `' — <em class="qc-reason">N/A — не critical ниша</em>'`
- New CSS for `.qc-not-applicable` (light + dark theme):
  - `color: var(--text-dim, #888);`
  - `opacity: 0.6;`
  - `.qc-not-applicable .qc-icon { color: #aaa; }` (light)
  - `[data-theme="dark"] .qc-not-applicable .qc-icon { color: #888; }` (dark)
- QC summary line gains N/A count note: `· {na_count} item N/A (не critical ниша)` when applicable
- `handle_generate_html_report` extracts `niche` + `instagram_data` from kwargs with safe defaults (defensive if LLM forgets)
- Pass 3 prompt (`pass_fill_assemble._build_prompt`) extended with items 5 + 6:
  - Item 5: instructs LLM to pass `niche` from `state.collected_data.niche_detection.niche`
  - Item 6: instructs LLM to pass `instagram_data` from Pass 1 tool-call history (or None)
  - Both items use mandatory language "ОБЯЗАТЕЛЬНО передай параметр"
- Module docstrings (both files) updated with Phase 3 / D-07 + D-08 paragraphs

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _build_no_instagram_block helper + conditional rendering in sections 03/04** — `49352a9` (feat)
2. **Task 2: Update _build_qc_coverage_section to read metadata['not_applicable_items'] canonical source with neutral styling** — `1db3880` (feat)
3. **Task 3: Extend Pass 3 prompt with niche + instagram_data kwargs instructions** — `c34be29` (feat)
4. **Rule 1 auto-fix: Escape CSS braces in _build_no_instagram_block f-string** — `4614ea9` (fix)

**Plan metadata commit:** created after this SUMMARY.

## Files Modified

### `AIM/hermes/app/tools/generate_html_report.py` (+275 lines, -2 lines)

- Module docstring: extended with Phase 3 / D-07 paragraph documenting `_build_no_instagram_block` helper + the 4 reason variants + conditional rendering rules
- `_build_no_instagram_block(reason: str) -> str` — new helper function:
  - Maps 4 reason variants via `reason_map` dict
  - Generic fallback for unknown reasons (preserves raw text XSS-escaped)
  - Returns HTML `<div class="no-instagram-block surface-card">` with:
    - `<h4>Instagram: данные недоступны</h4>` heading
    - `<p class="text-dim">{reason_text}</p>` body
    - `<span class="metric-tag metric-tag-warning">Instagram N/A</span>` warning badge
    - Scoped `<style>` block with `.no-instagram-block` + `[data-theme="dark"]` variants
- `_maybe_build_no_instagram_block(niche, instagram_data) -> str` — new gatekeeper:
  - Lazy imports `is_niche_instagram_critical` from qc_checklist
  - Returns empty string for non-critical niches (defensive if qc_checklist unavailable too)
  - Determines reason: None → "no_account"; analyzed_count == 0 → "perplexity_outside_index"; has analyzed profiles → empty string (no block)
- `_build_report_html` — signature extended with `niche: str = "unknown"` and `instagram_data: dict | None = None`; both default to backward-compat values
- Section 03 rendering (Ключевые врачи) — appends `{no_ig_block_03}` inside `<section>` after the doctor grid
- Section 04 rendering (Контент-анализ сайта) — appends `{no_ig_block_04}` inside `<section>` after the content analysis grid
- `_build_qc_coverage_section`:
  - Docstring extended with Phase 3 / D-08 paragraph + Plan 03-06 reference
  - Reads `not_applicable_items = metadata.get("not_applicable_items", []) or []`
  - Builds `not_applicable_by_id = {item.get("id"): item for item in not_applicable_items if isinstance(item, dict)}`
  - New `elif item_id in not_applicable_by_id:` branch BEFORE `elif item_id in missing_by_id:` — renders ⚪ icon + qc-not-applicable class + N/A label
  - Computes `na_count = len(not_applicable_by_id)` and `na_note` for summary line
  - Summary line: `QC Coverage: {len(filled_ids)}/{total} ({pct_str}) — {badge}{na_note}`
  - New CSS: `.qc-not-applicable` + dark-theme variant
- `handle_generate_html_report` — extracts `niche` and `instagram_data` from kwargs with safe defaults; falls back to args dict if needed (matches existing `coverage_metadata` pattern)

### `AIM/hermes/app/orchestrator/pass_fill_assemble.py` (+22 lines, -0 lines)

- Module docstring: extended with Phase 3 / D-07 paragraph documenting items 5+6 + cross-plan data-contract closure (Checker issue #1)
- `_build_prompt` return string: items 5 + 6 added AFTER item 4 and BEFORE closing `)`:
  - Item 5: "КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр niche со значением из state.collected_data.niche_detection.niche ..."
  - Item 6: "КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр instagram_data с полным ответом инструмента run_instagram_content из твоей Pass 1 tool-call history ..."
- Items 1-4 preserved byte-identical (regression-safe)
- `gap_report` parsing, `missing_items` extraction, `summary_line` formatting, `coverage_hint` construction — unchanged
- `_PASS_FILL_TIMEOUT` (600s), `run_pass_fill_assemble` structure, exception handling — unchanged

## Function Signatures Introduced

```python
# generate_html_report.py
def _build_no_instagram_block(reason: str) -> str:
    """Render an honest "Instagram: данные недоступны — {reason}" block.

    Supports 4 known reason variants per D-07; falls back to generic
    XSS-escaped message for unknown reasons.
    """

def _maybe_build_no_instagram_block(
    niche: str, instagram_data: dict | None,
) -> str:
    """Return _build_no_instagram_block(reason) HTML or empty string.

    Per Phase 3 / D-07: render the no-Instagram block ONLY when niche is
    critical AND instagram_data is missing/empty. Returns empty string
    for non-critical niches (no warning shown).
    """

def _build_report_html(
    data: dict,
    title: str,
    coverage_metadata: dict | None = None,
    niche: str = "unknown",            # NEW (Plan 03-05)
    instagram_data: dict | None = None,  # NEW (Plan 03-05)
) -> str:
    """Build full HTML page — extended with niche + instagram_data kwargs."""
```

## Reason Variant Matrix

| `reason` arg | Russian user-facing text | When chosen |
|---|---|---|
| `no_account` | У клиники нет аккаунта Instagram | `instagram_data is None` OR not a dict OR empty dict |
| `handle_not_found` | Instagram-handle врача не найден на сайте клиники | (Defensive default — currently not auto-selected by `_maybe_build_no_instagram_block`, available for future Perplexity response shape detection) |
| `private_profile` | Instagram-профиль приватный — данные недоступны | (Defensive — currently not auto-selected, available for future Perplexity response shape detection) |
| `perplexity_outside_index` | Instagram-handle не в индексе Perplexity — данные недоступны (вызовы были произведены, ни один не вернул данных) | `analyzed_count == 0` (handles tried, all failed) |
| (any other value) | Instagram: данные недоступны — {reason} (XSS-escaped) | Generic fallback |

## Runtime Behavior Matrix

| Niche | instagram_data shape | `_maybe_build_no_instagram_block` returns | Section 03/04 block |
|-------|----------------------|-------------------------------------------|---------------------|
| plastic_surgery | None | Block HTML, reason="no_account" | ✅ Rendered |
| plastic_surgery | `{}` (empty) | Block HTML, reason="no_account" | ✅ Rendered |
| plastic_surgery | `{analyzed_count: 0}` | Block HTML, reason="perplexity_outside_index" | ✅ Rendered |
| plastic_surgery | `{analyzed_count: 5}` | Empty string | ❌ Not rendered (real data exists) |
| cosmetology | (any of above) | Same as plastic_surgery | Same |
| dental | (any) | Empty string | ❌ Not rendered (non-critical) |
| general_medicine | (any) | Empty string | ❌ Not rendered (non-critical) |
| other | (any) | Empty string | ❌ Not rendered (non-critical) |
| unknown | (any) | Empty string | ❌ Not rendered (non-critical) |
| "" (not set) | (any) | Empty string | ❌ Not rendered (non-critical) |

## QC Section not_applicable Rendering

| Branch | Icon | CSS class | Opacity | When |
|--------|------|-----------|---------|------|
| filled | ✅ | `qc-filled` | 1.0 | item_id in filled_set |
| partial | 🟡 | `qc-partial` | 1.0 | item_id in partial_by_id |
| **not_applicable** | **⚪** | **`qc-not-applicable`** | **0.6** | **item_id in not_applicable_by_id (Plan 03-05/D-08)** |
| missing | ❌ | `qc-missing` | 1.0 | item_id in missing_by_id |
| unevaluated | ❌ | `qc-missing` | 1.0 | (fallthrough) |

## Verification Artifacts

| Check | Result |
|-------|--------|
| `generate_html_report.py` AST parse | OK |
| `pass_fill_assemble.py` AST parse | OK |
| `_build_no_instagram_block` function defined | Yes |
| `_maybe_build_no_instagram_block` function defined | Yes |
| `_build_report_html` signature has niche + instagram_data | Yes — 5 args, 3 defaults (backward compat) |
| 4 reason variants encoded | Yes (no_account, handle_not_found, private_profile, perplexity_outside_index) |
| `_esc()` used for all user-facing strings | Yes (T-03-05-XSS mitigated) |
| `plastic_surgery` + `cosmetology` referenced | Yes (via is_niche_instagram_critical lazy import) |
| `not_applicable_items` canonical source read | Yes (`metadata.get("not_applicable_items", [])`) |
| No status-scan fallback | Yes (per Fix #2 — no scan of `metadata["items"]`) |
| `qc-not-applicable` CSS class defined | Yes (with light + dark theme variants) |
| ⚪ icon for not_applicable | Yes |
| `opacity: 0.6` for de-emphasis | Yes |
| Pre-existing `qc-filled` / `qc-partial` / `qc-missing` intact | Yes (regression-safe) |
| PASS/FAIL badge logic unchanged | Yes (`metric-tag-success` / `metric-tag-warning`) |
| N/A count note in summary line | Yes (`· {na_count} item N/A (не critical ниша)`) |
| Pass 3 prompt items 5+6 present | Yes (niche + instagram_data kwargs) |
| `niche_detection` source path referenced | Yes |
| "Pass 1 tool-call history" referenced | Yes |
| Mandatory language "ОБЯЗАТЕЛЬНО" used | Yes |
| Pre-existing items 1-4 preserved | Yes (regression-safe) |
| `_PASS_FILL_TIMEOUT` (600s) unchanged | Yes |
| `gap_report` parsing / `missing_items` / `summary_line` / `coverage_hint` unchanged | Yes |
| Backward compat: `_build_report_html(data, title)` works | Yes (verified by smoke test 6) |
| Smoke test 1: All 4 reason variants render correctly | PASS (690-770 chars each, all required elements) |
| Smoke test 2: Unknown reason fallback works | PASS (XSS-escaped generic message) |
| Smoke test 3: Critical niche + None → block with no_account | PASS |
| Smoke test 3b: Critical niche + analyzed_count=0 → block with perplexity_outside_index | PASS |
| Smoke test 4: Critical niche + analyzed_count=5 → empty string | PASS |
| Smoke test 5: Non-critical niches → empty string | PASS (dental, general_medicine, other, unknown) |
| Smoke test 6: Backward compat `_build_report_html(data, title)` | PASS — valid HTML, no block |
| Smoke test 7a: doctor_list + critical niche → block in section 03 | PASS |
| Smoke test 7b: content_analysis + critical niche → block in section 04 | PASS |
| Smoke test 7c: Both sections + both blocks (2 total) | PASS |
| Smoke test 7d: Non-critical niche + full data → no block | PASS |
| QC section smoke test: not_applicable item renders with ⚪ + 13/14 summary + N/A note | PASS |
| Regression: ORCHESTRATOR_MODE=0 default path | Yes — Phase 3 changes only fire when ORCHESTRATOR_MODE=1 (orchestrator path). PipelineEngine fallback (`_build_report_html(data, title)`) unaffected. |
| Regression: Phase 2 `_build_qc_coverage_section` filled/partial/missing rendering | Yes — only ADDED new elif branch between partial and missing; pre-existing branches unchanged |
| Post-commit deletion check | None (no tracked files deleted across 4 commits) |
| Untracked file check | None created by this plan |

## Test Output

### Test 1: All 4 reason variants render correctly

```
OK: no_account → 690 chars, all required elements present
OK: handle_not_found → 707 chars, all required elements present
OK: private_profile → 705 chars, all required elements present
OK: perplexity_outside_index → 770 chars, all required elements present
```

### Test 3: Critical niche scenarios

```
OK: plastic_surgery + None → block with no_account reason text
OK: cosmetology + analyzed_count=0 → block with perplexity reason text
```

### Test 7: Integration via `_build_report_html` kwargs

```
OK: section 03 (Ключевые врачи) renders + no-instagram-block appended
OK: section 04 (Контент-анализ сайта) renders + no-instagram-block appended
Metrics: 2 block(s) rendered in HTML   # both sections
OK: both sections render block (2 total)
OK: non-critical niche → no block rendered
```

### QC Section smoke test

```
--- Rendered N/A row ---
<li class="qc-item qc-not-applicable"><span class="qc-icon">⚪</span> <strong>#5.</strong> Instagram analysis for cosmetology/plastic — <em class="qc-reason">N/A для данной ниши: not_applicable for non-critical niche (dental)</em></li>

--- Rendered summary line ---
<p class="qc-summary">
    QC Coverage: 13/14 (92.8%) — <span class="metric-tag metric-tag-success">PASS</span> · 1 item N/A (не critical ниша)
</p>
```

### Pass 3 prompt smoke test

```
--- Prompt items 5+6 snippet ---
5. КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр niche со значением из state.collected_data.niche_detection.niche (это ниша клиники, определённая мини-коллом между Pass 1 и Pass 2 — нужно для рендеринга 'Instagram: данные недоступны' блока в секциях 03+04 для critical ниш, per Phase 3 D-07).
6. КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр instagram_data с полным ответом инструмента run_instagram_content из твоей Pass 1 tool-call history (если вызов был). Если Instagram не вызывался — передай instagram_data=None. Это нужно для определения 'no data' vs 'no account' причины в HTML блоке (per Phase 3 D-07).
```

## Decisions Made

1. **Block design reuses `surface-card` + `metric-tag-warning` + `text-dim` classes** — Consistent with qc-coverage-section aesthetic. The block reads as a "soft warning" (yellow badge) rather than "hard error" (red badge), matching the ORC-04 honest-data principle that "недоступно" is not a failure but a transparent status.

2. **Reason variant mapping dict with generic fallback** — Known variants get curated Russian text. Unknown reasons (e.g., future error types) fall through to `f"Instagram: данные недоступны — {_esc(str(reason))}"` — preserves the raw reason XSS-escaped. No silent drop of unknown reason strings.

3. **`_maybe_build_no_instagram_block` gatekeeper returns empty string for non-critical niches** — Per D-07 spec: "For non-critical niches, the block is NOT rendered — section appears without Instagram content (no warning needed)". Non-critical niches have item 5 in `not_applicable_items` (Plan 03-06) which the QC section renders with ⚪ — no need to also warn in sections 03/04.

4. **Reason selection logic in `_maybe_build_no_instagram_block`: None → "no_account"; analyzed_count==0 → "perplexity_outside_index"; default → "handle_not_found"** — Maps to the most likely real-world causes. The "handle_not_found" and "private_profile" variants are not currently auto-selected because Perplexity response shape doesn't distinguish them in the current run_instagram_content v2 schema; they're available for future Perplexity response shape detection or LLM-explicit reason passing.

5. **Block appended INSIDE section 03/04 HTML, not as standalone section** — Contextual to doctors/content. If section doesn't render (e.g., no doctor data), block doesn't render either. This matches the philosophy that the block explains "why Instagram metrics for THESE doctors are missing" — if there are no doctors, the question is moot.

6. **Lazy import of `is_niche_instagram_critical` inside `_maybe_build_no_instagram_block`** — Avoids top-level orchestrator dependency. `generate_html_report.py` is also called from PipelineEngine (ORC-05 fallback) which doesn't have orchestrator context — top-level import would create an unnecessary coupling. The lazy import in a try/except returns empty string if qc_checklist is unavailable (defensive against legacy deploy scenarios).

7. **Canonical source consumption per Fix #2** — `metadata["not_applicable_items"]` is the canonical source populated by Plan 03-06 `_apply_niche_conditional_coverage` helper. NO fallback to scan `metadata["items"]` for status=='not_applicable'. Plan 03-06 is the single source of truth; this plan just renders what it populates.

8. **CSS opacity 0.6 for de-emphasis** — Visually clearly distinct from `.qc-filled` (no opacity), `.qc-partial` (no opacity), `.qc-missing` (no opacity). The 0.6 value matches common design-system patterns for "disabled/muted" state without being unreadable.

9. **Summary line N/A count note uses · separator** — Matches existing summary line punctuation: `QC Coverage: 13/14 (92.8%) — PASS · 1 item N/A (не critical ниша)`. The `·` (middle dot) is already used elsewhere in design-system meta text.

10. **Items 5+6 placed AFTER item 4 in Pass 3 prompt** — Preserves existing 4-item task list ordering (rules: fill gaps → generate_html_report → honest mark → coverage_metadata). The new kwargs (niche + instagram_data) are downstream refinements of item 2 (call generate_html_report) — placing them after item 4 keeps the LLM's attention on the most critical rules first.

11. **Both new prompt items use "ОБЯЗАТЕЛЬНО передай параметр" language** — Matches item 4 mandatory language for consistency. The receiver side (`handle_generate_html_report`) has defensive defaults (`niche="unknown"`, `instagram_data=None`) — if LLM forgets, the report still renders without the no-Instagram block but doesn't crash.

12. **F-string CSS brace escaping (Rule 1 auto-fix)** — Discovered during Task 1 smoke test: f-string literal CSS `{...}` rule bodies were interpreted as Python expression placeholders, causing NameError at runtime. Fixed by escaping as `{{...}}` per f-string spec. Committed as separate Rule 1 auto-fix commit `4614ea9` immediately after Task 1 commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] F-string CSS brace escaping in `_build_no_instagram_block`**
- **Found during:** Task 1 (smoke test verification)
- **Issue:** The f-string literal CSS block contained unescaped `{margin-top: 1rem; ...}` rule bodies which Python interpreted as expression placeholders, causing `NameError: name 'margin' is not defined` at runtime. AST parse did NOT catch this — only runtime invocation surfaced it.
- **Fix:** Escaped all CSS `{` and `}` as `{{` and `}}` in the f-string. Only `{reason_text}` remains as a single Python expression placeholder.
- **Files modified:** `AIM/hermes/app/tools/generate_html_report.py`
- **Verification:** Comprehensive smoke test now runs to completion — all 4 reason variants render 690-770 char HTML with `<style>` block intact.
- **Committed in:** `4614ea9` (separate fix commit immediately after Task 1)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for the helper to actually work at runtime. No scope creep — fix is mechanical (f-string escaping), preserves the original design intent.

## Known Stubs

None. The `_build_no_instagram_block` helper renders actual HTML for all 4 reason variants; `_maybe_build_no_instagram_block` returns definitive HTML or empty string for all (niche, instagram_data) combinations; `_build_qc_coverage_section` renders actual `<li>` rows for not_applicable items with the CSS class defined. No placeholder values, no TODO/FIXME, no hardcoded empty buckets that flow to UI rendering.

## Threat Flags

None. The threat surface (HTML rendering helpers + prompt text extension) is fully covered by the plan's existing threat model:

- T-03-05-S (Spoofing — LLM passes wrong niche to suppress block): accept — Plan 03-03 hard-FAIL logic is independent of HTML rendering; LLM niche value is convenience for HTML, not gate; actual niche verdict lives in `state.collected_data["niche_detection"]` (Plan 03-02). The HTML block is purely informational — no security decision rides on its rendering.
- T-03-05-T (Tampering — HTML modified post-render): accept — HTML is generated server-side and published as static; no client-side mutation expected.
- T-03-05-R (Repudiation — "why no Instagram?" client question): mitigated — the no-Instagram block explicitly states the reason (4 variants per D-07), so the client always knows why data is missing. No ambiguity to repudiate.
- T-03-05-I (Info disclosure — reason text mentions Perplexity by name): accept — Perplexity is a public third-party service; mentioning it in client-facing reports aligns with ORC-04 honest-data principle. Not a trade secret.
- T-03-05-D (DoS): accept — HTML rendering is in-process, bounded by data size; helpers are O(N) in checklist items.
- T-03-05-E (EoP): N/A — no privilege boundary, static HTML output.
- T-03-05-XSS (XSS — reason/handle text injection): mitigated — all user-facing strings pass through `_esc()` helper (consistent with Phase 2 T-02-03-XSS mitigation). Verified by code inspection + acceptance criterion.

## User Setup Required

None — purely additive HTML rendering + prompt changes, opt-in via `ORCHESTRATOR_MODE=1` (default OFF). Production presale flow unaffected. No external service configuration required. No deployment required for this plan (changes are Python-level; they take effect next time the orchestrator runs and the LLM invokes `generate_html_report`).

## Next Phase Readiness

- **Ready for Phase 4** (New Sections & Data Depth) — Phase 3 work across plans 03-01..06 is complete (subject to this plan's verification). Phase 4 can extend the report with new sections (Strategy 5-direction, Offer section) building on the Phase 3 foundation.
- **D-07 SATISFIED (HTML side)** — HTML renders a "Instagram: данные недоступны — {reason}" block in sections 03+04 for critical-niche clinics with missing Instagram. 4 reason variants supported per spec. The block uses design-system classes (`surface-card`, `metric-tag-warning`, `text-dim`) and includes light + dark theme variants.
- **D-08 SATISFIED (HTML side — canonical source)** — QC Coverage section reads `metadata["not_applicable_items"]` (populated by Plan 03-06 `_apply_niche_conditional_coverage`) and renders not_applicable items with neutral styling (⚪ icon, gray, opacity 0.6); effective total (14 vs 15) reflected in summary line via `metadata["total_items"]` (already adjusted by Plan 03-06 helper).
- **IG-04 SATISFIED** — If a clinic has no Instagram, the report notes this honestly (with specific reason) and does not block the remaining phases. Phase 2 soft QC gate (warning only, non-blocking) + Phase 3 honest block rendering work together: missing Instagram never breaks the presale flow, and the client always sees WHY data is missing.
- **Checker issue #1 CLOSED** — Pass 3 prompt now explicitly instructs the LLM to pass `niche` + `instagram_data` kwargs to `generate_html_report`. Source paths named in prompt: `state.collected_data.niche_detection.niche` (niche) + Pass 1 tool-call history (instagram_data).
- **Checker issue #2 CLOSED** (Plan 03-06 + this plan Task 2) — CoverageReport.not_applicable_items field (Plan 03-06 Task 1) is consumed by `_build_qc_coverage_section` (this plan Task 2) as the canonical source.

## Self-Check: PASSED

- FOUND: `AIM/hermes/app/tools/generate_html_report.py` (with `_build_no_instagram_block` helper at module level + `_maybe_build_no_instagram_block` gatekeeper + `_build_report_html` extended signature with niche + instagram_data kwargs + sections 03/04 conditional rendering + `_build_qc_coverage_section` reading `metadata["not_applicable_items"]` canonical source + `qc-not-applicable` CSS class with opacity 0.6 + `handle_generate_html_report` extracting niche + instagram_data from kwargs)
- FOUND: `AIM/hermes/app/orchestrator/pass_fill_assemble.py` (with items 5+6 in `_build_prompt` return string + niche_detection source path + Pass 1 tool-call history reference + module docstring updated)
- FOUND: commit `49352a9` (Task 1: feat — `_build_no_instagram_block` helper + conditional rendering in sections 03/04)
- FOUND: commit `1db3880` (Task 2: feat — QC section reads `metadata[not_applicable_items]` canonical source with neutral styling)
- FOUND: commit `c34be29` (Task 3: feat — Pass 3 prompt extended with niche + instagram_data kwargs instructions)
- FOUND: commit `4614ea9` (Rule 1 auto-fix: escape CSS braces in f-string)
- FOUND: `.planning/phases/03-instagram-integration/03-05-SUMMARY.md` (this file)

---
*Phase: 03-instagram-integration*
*Completed: 2026-06-23*
