---
phase: 03-instagram-integration
plan: 03
subsystem: orchestrator
tags: [orchestrator, prompt-engineering, qc-checklist-helpers, conditional-checklist, instagram-mandatory, hard-fail-prompt]

# Dependency graph
requires:
  - phase: 03-instagram-integration
    provides: 03-02 — state.niche field + state.collected_data["niche_detection"] dict populated by mini-call
  - phase: 02-3-pass-orchestrator-coverage-checklist
    provides: ORC-01..05 — 3-pass orchestrator core (pass_collect.py, pass_gap_analyze.py, qc_checklist.py) where prompts + helpers are inserted
provides:
  - qc_checklist.CRITICAL_NICHES — tuple constant ("plastic_surgery", "cosmetology")
  - qc_checklist.is_item_applicable(item_id, niche) -> bool (unknown => True)
  - qc_checklist.applicable_items(niche) -> list[dict] (14 for non-critical, 15 for critical)
  - qc_checklist.is_niche_instagram_critical(niche) -> bool
  - qc_checklist.VERSION == "1.1.0" (bumped from 1.0.0)
  - pass_collect._build_pass_collect_prompt(state) — niche-aware Pass 1 prompt builder
  - pass_gap_analyze._CHECKLIST_PROMPT_TEMPLATE — now carries {niche_instruction} placeholder
  - pass_gap_analyze.run_pass_gap_analyze — injects niche_instruction based on state.niche
  - Items in gap_report.summary now include `not_applicable` count (D-08)
  - Item 5 in QC_CHECKLIST carries conditional_on_niche: True flag
affects: [03-04, 03-05, 03-06, phase-08]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure Python stdlib (logging, ast.parse for verification)
  patterns:
  - "Niche-aware prompt branching: prompt builder reads state.collected_data['niche_detection'] + state.niche to choose mandatory vs optional Instagram language"
  - "Prompt-level hard-FAIL rule: Pass 2 prompt explicitly tells LLM that missing Instagram in critical niche = coverage=FAIL even at 14/15"
  - "Data-model conditional flag: item 5 carries conditional_on_niche: True; runtime application lives in Plan 03-06"
  - "Helper trio exported for downstream plans: is_item_applicable + applicable_items + is_niche_instagram_critical"
  - "Defensive dict access: niche_verdict = state.collected_data.get('niche_detection', {}); if not isinstance(dict) -> {} (corrupt-state safe)"
  - "not_applicable status as 4th value in gap_report items — separate from filled/partial/missing, counted separately in summary"

key-files:
  created: []
  modified:
  - AIM/hermes/app/orchestrator/qc_checklist.py (+111 lines: CRITICAL_NICHES + 3 helpers + item 5 conditional flag + docstring)
  - AIM/hermes/app/orchestrator/pass_collect.py (+82 lines: _build_pass_collect_prompt helper + Phase 3 docstring)
  - AIM/hermes/app/orchestrator/pass_gap_analyze.py (+73 lines: niche_instruction build + not_applicable count + Phase 3 docstring)

key-decisions:
  - "VERSION bumped 1.0.0 -> 1.1.0 per module's own versioning rule (lines 22-25): items got a new field + helpers exported"
  - "Item 5 is the ONLY item carrying conditional_on_niche: True — other 14 items byte-identical (universal applicability)"
  - "is_item_applicable returns True for 'unknown' niche (mini-call failed) — safer to over-require than under-require; Pass 2 LLM uses evidence-driven judgment"
  - "is_niche_instagram_critical returns False for 'unknown' — helpers are conservative; the prompt layer has its own cautious wording for the unknown case"
  - "Prompt builder extracted into _build_pass_collect_prompt(state) module-level function for testability (Plan 03-03 Task 2 acceptance criteria explicitly required the prompt logic to be unit-testable)"
  - "Defensive isinstance(niche_verdict, dict) check in _build_pass_collect_prompt — handles corrupt state where niche_detection is set to a non-dict value without crashing"
  - "Pass 2 template now has 3 placeholders: {client_url}, {checklist_render}, {niche_instruction} — niche_instruction built at call time from state.niche"
  - "_ensure_summary setdefault for not_applicable (not assignment) — preserves LLM-provided counts if present, only fills in when missing"
  - "Hard-FAIL language ('HARD FAIL', 'coverage=FAIL даже при 14/15') is bilingual: English 'HARD FAIL' tag + Russian explanatory text — matches LLM working language"
  - "Runtime hard-FAIL override + conditional-total math explicitly DEFERRED to Plan 03-06 per plan revision — this plan ships prompt + data-model scaffolding only"

patterns-established:
  - "Niche-aware prompt template with {placeholder} filled at call time — Pass 1 reads state.niche directly, Pass 2 uses is_niche_instagram_critical helper"
  - "Helper trio as the canonical niche API across the orchestrator: is_niche_instagram_critical + is_item_applicable + applicable_items — all downstream plans import from qc_checklist"
  - "4-value status enum for gap_report items: filled | partial | missing | not_applicable — not_applicable counted separately, not lumped into missing"
  - "Defensive .get() + isinstance() chain for niche_detection dict access — robust against corrupt state"

requirements-completed: []  # IG-02 marked complete only after Plan 03-06 adds runtime hard-FAIL override

# Metrics
duration: 5.3min
completed: 2026-06-23
---

# Phase 3 Plan 03: Mandatory Instagram Prompt + QC Checklist Helpers Summary

**Pass 1 prompt now mandates Instagram analysis (find_doctor_handles → run_instagram_content ordering, batch 8-10, D-06 retry pattern) for critical niches and marks it optional for non-critical niches; Pass 2 prompt encodes the HARD FAIL rule (critical niche + Instagram not called → coverage=FAIL even at 14/15) plus a `not_applicable` status for non-critical niches; qc_checklist.py exports `CRITICAL_NICHES` + three helper functions and item 5 carries a `conditional_on_niche: True` flag — the data-model scaffolding Plan 03-06 needs to apply the runtime override**

## Performance

- **Duration:** 5.3 min (319s)
- **Started:** 2026-06-23T17:52:27Z
- **Completed:** 2026-06-23T17:57:46Z
- **Tasks:** 3/3 complete (all `type="auto"`, no checkpoints)
- **Files modified:** 3 (qc_checklist.py, pass_collect.py, pass_gap_analyze.py)
- **Files created:** 0
- **Commits:** 3 task commits (docs commit follows SUMMARY)

## Accomplishments

- `CRITICAL_NICHES = ("plastic_surgery", "cosmetology")` module constant added (canonical niche list)
- Item 5 (Instagram) carries `"conditional_on_niche": True` flag — the only item with this field
- Three helper functions exported for downstream consumption:
  - `is_niche_instagram_critical(niche) -> bool` — True iff niche is plastic_surgery or cosmetology
  - `is_item_applicable(item_id, niche) -> bool` — False only for item 5 in non-critical niches; True for "unknown" (safer to over-require)
  - `applicable_items(niche) -> list[dict]` — returns 14 items for non-critical niches, 15 for critical or unknown
- `VERSION` bumped 1.0.0 → 1.1.0 per module's own versioning rule
- Pass 1 prompt builder `_build_pass_collect_prompt(state)` — niche-aware:
  - **Critical niche:** MANDATORY language ("ОБЯЗАТЕЛЬНОЕ ПРАВИЛО"), explicit ordering "СНАЧАЛА find_doctor_handles → ЗАТЕМ run_instagram_content", batch size 8-10, D-06 retry pattern, explicit "HARD FAIL ... 14/15 остальных пунктов" warning
  - **Non-critical niche:** "ОПЦИОНАЛЬНЫЙ ... не трать токены"
  - Defensive: corrupt `niche_detection` dict falls back to `state.niche in CRITICAL_NICHES` check
- Pass 2 `_CHECKLIST_PROMPT_TEMPLATE` now has `{niche_instruction}` placeholder + 4-value status enum (`filled | partial | missing | not_applicable`) + Instagram HARD FAIL rule block
- `run_pass_gap_analyze` builds `niche_instruction` string based on `state.niche`:
  - **Critical:** "Instagram-critical=True, пункт 5 ОБЯЗАТЕЛЕН, HARD FAIL on missing"
  - **Non-critical:** "Instagram-critical=False, пункт 5 = not_applicable"
  - **Unknown:** cautious wording ("apply HARD FAIL if cosmetology signs present in collected data")
- `_ensure_summary` now counts `not_applicable` items separately via `setdefault("not_applicable", N)`
- `_fallback_report` default summary includes `"not_applicable": 0`
- Pass 2 prompt explicitly encodes the D-05 HARD FAIL rule and the D-06 "filled with reason" path
- Module docstrings updated to reference Phase 3 / D-04..D-08

## Task Commits

Each task was committed atomically:

1. **Task 1: Add `is_item_applicable` + `applicable_items` + `is_niche_instagram_critical` + CRITICAL_NICHES + item 5 conditional flag** — `e197549` (feat)
2. **Task 2: Augment Pass 1 prompt with niche-aware Instagram-mandatory rule + doctor-discovery ordering** — `7201765` (feat)
3. **Task 3: Augment Pass 2 prompt with Instagram HARD FAIL rule + conditional niche reference + not_applicable status** — `09b867a` (feat)

**Plan metadata commit:** created after this SUMMARY.

## Files Modified

### `AIM/hermes/app/orchestrator/qc_checklist.py` (+111 lines, -1 line)

- Module docstring: added Phase 3 / Plan 03-03 narrative block listing the 3 new helpers + the conditional_on_niche flag semantics
- `VERSION = "1.1.0"` (bumped from 1.0.0)
- New constant `CRITICAL_NICHES: tuple[str, ...] = ("plastic_surgery", "cosmetology")` after `PASS_MIN_ITEMS`
- Item 5 (Instagram) — added `"conditional_on_niche": True` after the existing `"source"` key (only item with this field)
- Three new helper functions at end of module:
  - `is_niche_instagram_critical(niche) -> bool`
  - `is_item_applicable(item_id, niche) -> bool`
  - `applicable_items(niche) -> list[dict]`
- `render_checklist_for_llm`, `get_item_by_id`, `PASS_THRESHOLD`, `PASS_MIN_ITEMS` unchanged

### `AIM/hermes/app/orchestrator/pass_collect.py` (+82 lines, -8 lines)

- Module docstring: added Phase 3 / Plan 03-03 paragraph documenting D-04 mandatory mechanism + D-06 retry + ordering rule
- `run_pass_collect` body: replaced inline `prompt = (...)` with `prompt = _build_pass_collect_prompt(state)` call
- New module-level function `_build_pass_collect_prompt(state: OrchestratorState) -> str`:
  - Reads `state.collected_data.get("niche_detection", {})` with isinstance dict guard
  - Computes `is_critical = bool(niche_verdict.get("instagram_critical", False)) or state.niche in CRITICAL_NICHES`
  - Builds base_prompt + instagram_rule (critical or non-critical branch) + closing
  - Critical branch includes: find_doctor_handles FIRST, run_instagram_content SECOND, batch 8-10, D-06 retry, HARD FAIL warning
  - Non-critical branch: optional + "не трать токены"
- `_get_agent_for_session`, `_PASS_COLLECT_TIMEOUT` (600s), exception handling unchanged

### `AIM/hermes/app/orchestrator/pass_gap_analyze.py` (+73 lines, -6 lines)

- Module docstring: added Phase 3 / Plan 03-03 paragraph documenting D-05 HARD FAIL rule + D-08 conditional item + 4-value status enum
- `_CHECKLIST_PROMPT_TEMPLATE` rewritten:
  - Added `{niche_instruction}` placeholder after `{checklist_render}`
  - Added `'not_applicable'` as 4th valid status value in instructions
  - Added explicit Instagram rule block (3 sub-rules for critical + Instagram missing / critical + Instagram no-data / non-critical)
  - Updated JSON output schema to include `not_applicable: NA` in summary
- `run_pass_gap_analyze` body: added niche_instruction builder before template format call
  - Imports `is_niche_instagram_critical` from qc_checklist (lazy, inside function body)
  - Three branches: critical / unknown / non-critical
  - Passes `niche_instruction=niche_instruction` to `.format()`
- `_ensure_summary`: added `not_applicable` count via `setdefault`
- `_fallback_report`: default summary now includes `"not_applicable": 0`
- `_extract_reply_text`, `_parse_gap_json`, `_JSON_BLOCK_RE`, `_PASS_GAP_TIMEOUT` (240s) unchanged

## Function Signatures Introduced

```python
# qc_checklist.py
def is_niche_instagram_critical(niche: str) -> bool: ...
def is_item_applicable(item_id: int, niche: str) -> bool: ...
def applicable_items(niche: str) -> list[dict]: ...

# pass_collect.py
def _build_pass_collect_prompt(state: OrchestratorState) -> str: ...
```

## Pass 1 Instagram-mandatory Rule (Critical Niche Branch)

When `state.niche in ("plastic_surgery", "cosmetology")` OR `state.collected_data["niche_detection"]["instagram_critical"] == True`, the Pass 1 prompt includes:

```
ОБЯЗАТЕЛЬНОЕ ПРАВИЛО (Instagram-critical ниша — {niche}):
1. СНАЧАЛА вызови find_doctor_handles(url={client_url}) — получи Instagram
   handles топ-врачей клиники (8-10 handles, включая тех, кто реально ведёт
   соцсети, а не только титулованных).
2. ЗАТЕМ вызови run_instagram_content с полученным списком handles одним
   batch-вызовом (до 8-10 handles за раз) — получи метрики каждого врача.
3. Если run_instagram_content вернул 'no data' для конкретного handle —
   попробуй альтернативный handle из ответа find_doctor_handles. Если все
   handles не дали данных — отметь 'Instagram: handle не найден в Perplexity
   index / приватный профиль / нет аккаунта' (легитимный filled, не missing).
4. НЕ пропускай Instagram-анализ — это critical для данной ниши. Pass 2
   пометит coverage=FAIL (HARD FAIL) даже при 14/15 остальных пунктов.
```

## Pass 2 HARD FAIL Rule (Instagram Item 5)

The `_CHECKLIST_PROMPT_TEMPLATE` now includes the Instagram rule block:

```
ВАЖНОЕ ПРАВИЛО ДЛЯ INSTAGRAM (пункт 5):
- Если niche=instagram-critical (cosmetology или plastic_surgery) И
  run_instagram_content НЕ вызывался в Pass 1 → пункт 5 status='missing' с
  reason='Instagram critical для данной ниши, но инструмент не вызван'. Это
  HARD FAIL: coverage=FAIL даже при 14/15 остальных пунктов заполненных.
- Если niche=instagram-critical И run_instagram_content вызван, но вернул
  'no data' для всех handles → пункт 5 status='filled' с reason='Instagram
  вызван, данные недоступны: ...'. Это легитимный filled.
- Если niche=NON-critical → пункт 5 status='not_applicable' с reason='Ниша
  не Instagram-critical'.
```

## Verification Artifacts

| Check | Result |
|-------|--------|
| `qc_checklist.py` AST parse | OK (3 new FunctionDef: is_item_applicable, applicable_items, is_niche_instagram_critical; 1 new constant CRITICAL_NICHES; VERSION bumped to 1.1.0) |
| `pass_collect.py` AST parse | OK (1 new FunctionDef: _build_pass_collect_prompt; critical branch + non-critical branch present) |
| `pass_gap_analyze.py` AST parse | OK (_CHECKLIST_PROMPT_TEMPLATE has {niche_instruction}; run_pass_gap_analyze imports is_niche_instagram_critical) |
| `is_niche_instagram_critical("plastic_surgery")` | True |
| `is_niche_instagram_critical("cosmetology")` | True |
| `is_niche_instagram_critical("dental")` | False |
| `is_niche_instagram_critical("unknown")` | False (helpers are conservative) |
| `applicable_items("dental")` length | 14 (item 5 filtered out) |
| `applicable_items("plastic_surgery")` length | 15 |
| `applicable_items("unknown")` length | 15 (over-require on mini-call failure) |
| `is_item_applicable(5, "dental")` | False |
| `is_item_applicable(5, "plastic_surgery")` | True |
| `is_item_applicable(5, "unknown")` | True |
| Item 5 carries `conditional_on_niche: True` | Yes (only item with this field) |
| Other 14 items unchanged | Yes (no conditional_on_niche field on items 1-4, 6-15) |
| `_build_pass_collect_prompt` critical niche output | Contains ОБЯЗАТЕЛЬНОЕ ПРАВИЛО, СНАЧАЛА, find_doctor_handles, run_instagram_content, 8-10, HARD FAIL |
| `_build_pass_collect_prompt` non-critical output | Contains ОПЦИОНАЛЬНЫЙ, "не critical", "не трать токены" |
| `_build_pass_collect_prompt` corrupt niche_detection | Falls back to state.niche check, does not crash |
| `_CHECKLIST_PROMPT_TEMPLATE.format(client_url, checklist_render, niche_instruction)` | OK — all 3 placeholders filled |
| `_ensure_summary` counts `not_applicable` separately | Yes — setdefault key added |
| `_fallback_report` includes `not_applicable: 0` | Yes |
| `_parse_gap_json` preserves `not_applicable` via setdefault | Yes |
| Regression: `ORCHESTRATOR_MODE=0` default path unaffected | Yes — all changes inside orchestrator/; main.py, agent_wrapper.py, engine.py untouched |
| Regression: `_PASS_COLLECT_TIMEOUT` (600s) unchanged | Yes |
| Regression: `_PASS_GAP_TIMEOUT` (240s) unchanged | Yes |
| Regression: `PASS_THRESHOLD` (0.80) + `PASS_MIN_ITEMS` (12) unchanged | Yes |
| Regression: `render_checklist_for_llm` iterates all 15 items | Yes |
| Regression: PipelineEngine `_TOOL_HANDLERS` not touched | Yes (Plan 03-01 territory, not 03-03) |
| Post-commit deletion check | None (no tracked files deleted) |
| Untracked file check | None (no stray files in orchestrator/) |

## Decisions Made

1. **VERSION bumped to 1.1.0 (not 1.0.1)** — Per the module's own versioning rule at lines 22-25: "Bump when checklist items are added, removed, or their pass criteria change". Adding a new field (`conditional_on_niche`) to an existing item changes the item schema, which is a minor version bump (1.x.0), not a patch. The rule explicitly calls out "criteria change" — adding a conditional flag is a criteria change for item 5.

2. **`is_item_applicable` returns True for "unknown"** — When the mini-call fails and `state.niche == "unknown"`, we keep item 5 in scope. Rationale: safer to over-require (Pass 2 LLM evaluates evidence and decides) than under-require (silently drop Instagram analysis when we don't know the niche). This mirrors the niche_detector fallback rationale from Plan 03-02.

3. **`is_niche_instagram_critical` returns False for "unknown"** — At the *helper* level, we are strict: "unknown" is not critical. The prompt layer (`_build_pass_collect_prompt` and the niche_instruction builder in `pass_gap_analyze`) has its own cautious wording for the "unknown" case that tells the LLM to look at actual evidence. This keeps the helper API simple (boolean in/out) while letting the prompt layer express nuance.

4. **Prompt builder extracted to `_build_pass_collect_prompt(state)` module-level function** — Plan acceptance criteria explicitly required the prompt logic to be unit-testable. An inline `prompt = (...)` block inside `run_pass_collect` is hard to unit-test without mocking the AIAgent. A module-level function takes `state` and returns a str — trivially testable across all 3 niche branches (critical / non-critical / unknown) plus the corrupt-state branch.

5. **Defensive `isinstance(niche_verdict, dict)` guard** — `state.collected_data.get("niche_detection", {})` returns `{}` only when the key is absent. If a buggy upstream sets the value to a non-dict (string, list, None), the guard coerces to `{}` so the subsequent `.get("instagram_critical", False)` doesn't crash. Cheap defense, no downside.

6. **Hard-FAIL language is bilingual** — The prompt uses the English tag "HARD FAIL" alongside Russian explanatory text. Rationale: the LLM (DeepSeek V4 Pro) handles both fluently, and "HARD FAIL" is a recognizable tag the LLM can pattern-match on for emphasis. The explanatory text in Russian matches the LLM's working language for the rest of the prompt.

7. **Runtime hard-FAIL override explicitly DEFERRED to Plan 03-06** — Per plan revision: this plan ships prompt + data-model scaffolding only. Plan 03-06 will (a) wire the actual coverage-total recomputation (`total = 15 - not_applicable`) and (b) the runtime hard-FAIL override that forces coverage=FAIL regardless of LLM self-evaluation when critical niche + Instagram missing. Reason for the split: prompt + helpers are one review unit; runtime override touches `three_pass.py` + `coverage_reporter.py` and warrants its own verification surface.

## Deviations from Plan

None — plan executed exactly as written. All 3 tasks followed the action steps verbatim:

- Task 1: `CRITICAL_NICHES` added after `PASS_MIN_ITEMS`; `conditional_on_niche: True` added to item 5 only; 3 helpers added at end of file; VERSION bumped to 1.1.0; docstring updated ✓
- Task 2: Pass 1 prompt extracted to `_build_pass_collect_prompt(state)` helper; reads `state.collected_data["niche_detection"]`; critical branch has mandatory rule + ordering + batch + D-06 retry; non-critical branch says optional + token-savings guidance; module docstring updated ✓
- Task 3: `_CHECKLIST_PROMPT_TEMPLATE` rewritten with `{niche_instruction}` placeholder + 4-value status enum + Instagram HARD FAIL block; `run_pass_gap_analyze` builds niche_instruction from `state.niche`; `_ensure_summary` + `_fallback_report` updated to count `not_applicable`; docstring updated ✓

## Known Stubs

None. All helpers + prompt logic are fully implemented and unit-tested across all branches (critical, non-critical, unknown, corrupt state).

## Threat Flags

None. The threat surface (LLM prompt text + helper function returns) is fully covered by the plan's existing threat model:

- T-03-03-S (Spoofing — LLM ignores prompt rules): mitigated by Plan 03-06 runtime hard-FAIL override that will check `run_instagram_content` invocation independent of LLM self-evaluation. This plan adds the prompt-level instruction as the first layer (per threat disposition `mitigate`).
- T-03-03-R (Repudiation — prompt rules not visible in logs): accept; prompt text lives in source files (pass_collect.py, pass_gap_analyze.py), fully auditable via code review.
- T-03-03-I (Info disclosure — niche label in prompt): accept; niche derived from public clinic website data, no PII.
- T-03-03-D (DoS): N/A — prompt string build is O(1).
- T-03-03-T (Tampering — state.niche overwritten): accept; OrchestratorState is single-threaded per session, niche set once by Plan 03-02 mini-call.

## User Setup Required

None — purely additive orchestrator change, opt-in via `ORCHESTRATOR_MODE=1` (default OFF). Production presale flow unaffected. No deployment required for this plan (changes are prompt-level + helper-level; they take effect next time the orchestrator runs).

## Next Phase Readiness

- **Ready for Plan 03-04** (Adaptive top-5 doctor selection) — `state.collected_data["niche_detection"]` is populated by Plan 03-02 and Pass 1 prompt now mandates `find_doctor_handles` + `run_instagram_content` ordering for critical niches. Plan 03-04 will consume the Instagram batch results to implement the followers_count-based reordering fallback (D-10).
- **Ready for Plan 03-05** (HTML rendering) — `is_niche_instagram_critical(niche)` + `applicable_items(niche)` helpers are available for the HTML renderer to decide whether to show the Instagram section. `not_applicable` status is counted separately in gap_report.summary, ready for coverage-report rendering.
- **Ready for Plan 03-06** (Runtime hard-FAIL override) — All three helpers (`is_niche_instagram_critical`, `is_item_applicable`, `applicable_items`) are exported and unit-tested. Plan 03-06 will:
  - Wire `_apply_niche_conditional_coverage(gap_report, niche)` into `coverage_reporter.calc_coverage` (recompute total = 15 - not_applicable for non-critical niches)
  - Add runtime check in `three_pass.py` post-Pass-2: if `is_niche_instagram_critical(state.niche)` AND item 5 status == "missing" → force coverage = FAIL regardless of LLM self-evaluation
- **NOT yet enforcing Instagram-mandatory at runtime** — this plan adds prompt-level enforcement + data-model scaffolding. Runtime enforcement completes in Plan 03-06.
- **IG-02 status:** partially addressed by this plan (prompt layer + helpers ready). Full IG-02 completion requires Plan 03-06 runtime hard-FAIL override.

## Self-Check: PASSED

- FOUND: `AIM/hermes/app/orchestrator/qc_checklist.py` (with `CRITICAL_NICHES`, `is_item_applicable`, `applicable_items`, `is_niche_instagram_critical`, item 5 `conditional_on_niche: True`, `VERSION = "1.1.0"`)
- FOUND: `AIM/hermes/app/orchestrator/pass_collect.py` (with `_build_pass_collect_prompt(state)` helper, references to `instagram_critical` + `find_doctor_handles` + `run_instagram_content`)
- FOUND: `AIM/hermes/app/orchestrator/pass_gap_analyze.py` (with `{niche_instruction}` placeholder, `is_niche_instagram_critical` import, `not_applicable` count, HARD FAIL rule)
- FOUND: commit `e197549` (Task 1: feat — QC checklist helpers + conditional item 5)
- FOUND: commit `7201765` (Task 2: feat — Pass 1 prompt augmented with niche-aware Instagram rule)
- FOUND: commit `09b867a` (Task 3: feat — Pass 2 prompt augmented with HARD FAIL rule)

---
*Phase: 03-instagram-integration*
*Completed: 2026-06-23*
