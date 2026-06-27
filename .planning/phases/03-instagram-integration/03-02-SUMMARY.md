---
phase: 03-instagram-integration
plan: 02
subsystem: orchestrator
tags: [orchestrator, niche-detection, mini-call, pass-1-2-boundary, llm-call, instagram-critical]

# Dependency graph
requires:
  - phase: 03-instagram-integration
    provides: 03-01 — Instagram tools wired into _TOOL_HANDLERS (downstream consumers can call them)
  - phase: 02-3-pass-orchestrator-coverage-checklist
    provides: ORC-01..05 — 3-pass orchestrator core (states.py, three_pass.py, pass_collect.py, pass_gap_analyze.py) where mini-call is inserted
provides:
  - OrchestratorState.niche field (str, default "") carries the verdict from mini-call
  - detect_instagram_critical_niche(state) -> dict mini-call function in app/orchestrator/niche_detector.py
  - state.collected_data["niche_detection"] full verdict dict for downstream consumers
  - three_pass.py invokes mini-call BETWEEN Pass 1 and Pass 2 (Phase 3 / D-01..03)
affects: [03-03, 03-04, 03-05, 03-06, phase-04, phase-08]

# Tech tracking
tech-stack:
  added: []  # no new libraries — asyncio, json, logging, re only
  patterns:
  - "Mini-call pattern: short LLM call between orchestrator passes, reuses same AIAgent session_id for context continuity"
  - "Boundary-rule prompt: explicit >50% threshold + 'add-on service' exclusion in natural language (not keyword matching)"
  - "Robust fallback dict on ANY exception (timeout/parse/agent error) — orchestrator never aborts on mini-call failure"
  - "Module self-sufficiency: _extract_reply_text + _JSON_BLOCK_RE replicated in detector (not imported) so module survives future refactors of pass_gap_analyze"

key-files:
  created:
  - AIM/hermes/app/orchestrator/niche_detector.py (203 lines)
  modified:
  - AIM/hermes/app/orchestrator/states.py (+7 lines: niche field + docstring)
  - AIM/hermes/app/orchestrator/three_pass.py (+27 lines: mini-call section + docstring note)

key-decisions:
  - "Mini-call reuses _get_agent_for_session helper from pass_collect.py — shares Pass 1 AIAgent + SQLite conversation history (per D-02)"
  - "Detector owns its failure path: try/except inside detect_instagram_critical_niche returns {instagram_critical=False, niche=unknown} on ANY exception — three_pass.py trusts the contract and does NOT wrap the call in try/except"
  - "_extract_reply_text + _JSON_BLOCK_RE replicated in detector module instead of imported from pass_gap_analyze — keeps detector self-contained, avoids future refactor coupling"
  - "30s timeout ceiling (_NICHE_DETECT_TIMEOUT) — D-02 budgets ~5s API time with margin for DeepSeek V4 Pro latency variance"
  - "Verdict is LLM-judgment based (D-01) — not keyword/ОКВЭД. Boundary rule (>50%, ОСНОВНОЙ профиль) encoded in Russian prompt text matching LLM working language"

patterns-established:
  - "Mini-call between passes: short async LLM call via _get_agent_for_session + asyncio.wait_for(asyncio.to_thread(agent.run_conversation, prompt), timeout=N)"
  - "Mini-call return contract: dict with structured keys + deterministic fallback on failure — caller never has to try/except"
  - "Module-level constants for timeouts (_NICHE_DETECT_TIMEOUT) — greppable, easy to tune"

requirements-completed: []  # IG-02 marked complete only after Plan 03-03 + 03-06 enforce the rule

# Metrics
duration: 4.5min
completed: 2026-06-23
---

# Phase 3 Plan 02: Niche Detection Mini-call Summary

**New mini-call between Pass 1 and Pass 2 determines Instagram-criticality of the clinic via a short LLM call; verdict populates `state.niche` and `state.collected_data["niche_detection"]` for downstream Pass 2 enforcement (Plan 03-03 will consume the signal)**

## Performance

- **Duration:** 4.5 min
- **Started:** 2026-06-23T17:44:03Z
- **Completed:** 2026-06-23T17:48:29Z
- **Tasks:** 3/3 complete (all `type="auto"`)
- **Files modified:** 2 (states.py, three_pass.py)
- **Files created:** 1 (niche_detector.py, 203 lines)
- **Commits:** 3 task commits + 1 final docs commit

## Accomplishments

- `OrchestratorState.niche: str = ""` field added (default empty — mini-call not yet run)
- `detect_instagram_critical_niche(state) -> dict` async function implemented
- Mini-call wired into `three_pass.py` between Pass 1 (Collect) and Pass 2 (Gap-analyze) — execution order verified by source-position scan
- Boundary rule (D-03) encoded in Russian prompt: `>50% услуг`, `ОСНОВНОЙ профиль`, `косметология/пластическая хирургия` as primary triggers, `доп. услуга` (e.g., dental+cosmetic) excludes
- Robust failure path: ANY exception → `{instagram_critical=False, niche="unknown", reason="mini-call failed — treating as non-critical to avoid false hard-FAIL", error=str(exc)}` — 3-pass cycle never aborts on mini-call failure
- `state.collected_data["niche_detection"]` retains full verdict for Plan 03-03 Pass 2 enforcement + Plan 03-05 HTML rendering
- Greppable audit trail via `logger.info` with client_url + instagram_critical + niche + reason (T-03-02-R mitigation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add `niche` field to OrchestratorState dataclass** — `53a4db8` (feat)
2. **Task 2: Create niche_detector.py module** — `e911542` (feat)
3. **Task 3: Wire mini-call into three_pass.py between Pass 1 and Pass 2** — `ff4d28f` (feat)

**Plan metadata:** created by the docs commit after this SUMMARY.

## Files Created/Modified

### Created

- `AIM/hermes/app/orchestrator/niche_detector.py` (203 lines)
  - Module docstring traceable to Phase 3 D-01..03
  - Imports: `asyncio`, `json`, `logging`, `re`, `OrchestratorState`
  - Module logger + `_NICHE_DETECT_TIMEOUT = 30` constant
  - `_JSON_BLOCK_RE` regex (replicated from pass_gap_analyze for module self-sufficiency)
  - `_NICHE_DETECT_PROMPT_TEMPLATE` Russian prompt with boundary rule
  - 4 functions: `detect_instagram_critical_niche` (public async), `_extract_reply_text`, `_parse_verdict_json`, `_normalize_verdict` (private helpers)

### Modified

- `AIM/hermes/app/orchestrator/states.py` (+7 lines)
  - New field `niche: str = ""` added after `error_message` (now 13 fields total)
  - Docstring documents Phase 3 D-01..03 semantics with all possible values

- `AIM/hermes/app/orchestrator/three_pass.py` (+27 lines)
  - Module docstring updated with Phase 3 / D-01..03 note (lines 11-16)
  - New section at lines 100-118: `# ── Niche detection mini-call (Phase 3 / D-01..03) ──`
  - Pass 1 logic byte-identical (lines 87-98, was 80-91)
  - Pass 2 logic byte-identical (lines 120+, was 93+)

## Function Signatures Introduced

```python
async def detect_instagram_critical_niche(state: OrchestratorState) -> dict:
    """Returns {instagram_critical: bool, niche: str, reason: str}.
    On ANY failure returns fallback dict with niche="unknown"."""

def _extract_reply_text(result) -> str: ...  # mirrors pass_gap_analyze._extract_reply_text
def _parse_verdict_json(reply_text: str): ...  # returns dict or None
def _normalize_verdict(verdict) -> dict: ...  # coerces parsed JSON into canonical shape
```

## Mini-call Prompt Template (load-bearing)

Stored in `niche_detector.py` as `_NICHE_DETECT_PROMPT_TEMPLATE`:

```
Ты только что собрал данные о клинике {client_url} в Pass 1.

Определи, является ли Instagram-маркетинг КРИТИЧНЫМ для этой клиники:
- instagram_critical=true только если косметология или пластическая хирургия — ОСНОВНОЙ профиль клиники (>50% услуг или заявлен как главный)
- Если эстетические процедуры — доп. услуга (стоматология с косметологией, общая медицина с косметологией) → instagram_critical=false
- Учитывай:specialization_clinic > specialization_doctor. Если клиника позиционируется как "многопрофильная" — проверь, занимает ли косметология/пластика >50% visible услуг на сайте.

ВЫВЕДИ результат КАК JSON (без markdown, без текста вокруг):
{"instagram_critical": true|false, "niche": "plastic_surgery"|"cosmetology"|"dental"|"general_medicine"|"other", "reason": "1 предложение пояснение"}

ВАЖНО: только валидный JSON, без markdown fences, без пояснений.
```

## Insertion Location in three_pass.py

- **Module docstring:** lines 11-16 — Phase 3 / D-01..03 narrative
- **Mini-call section:** lines 100-118 — between Pass 1 abort block (ends line 98) and Pass 2 lazy import (starts line 120)
- **Source-position scan verified:** `run_pass_collect(state)` at 3370, `detect_instagram_critical_niche(state)` at 4312, `run_pass_gap_analyze(state)` at 5176 — strict ordering Pass 1 → Mini-call → Pass 2

## AST Inspection Results

All 3 plan-level checks pass:

```
OK: app/orchestrator/states.py parses cleanly
OK: app/orchestrator/niche_detector.py parses cleanly
OK: app/orchestrator/three_pass.py parses cleanly
OK: all cross-file wiring present
```

Plus per-task AST scans (see each Task section above).

## Decisions Made

1. **Reuse `_get_agent_for_session` from pass_collect.py** — Same helper as Pass 1 uses to get the cached AIAgent. This is the canonical way to share the LLM session_id between passes per Phase 2's design. Avoids creating a fresh agent that would have no Pass 1 conversation history.

2. **Detector owns its failure path** — three_pass.py does NOT wrap `await detect_instagram_critical_niche(state)` in try/except. The detector has an internal try/except that returns a deterministic fallback dict on ANY exception (timeout, parse error, agent error). This is a cleaner contract than forcing every caller to handle exceptions — the caller can always trust the return value is a dict.

3. **Self-contained `_extract_reply_text` + `_JSON_BLOCK_RE`** — Instead of importing `_extract_reply_text` from `pass_gap_analyze`, the helper and regex constant are replicated in `niche_detector.py`. This keeps the module self-contained — if `pass_gap_analyze` is ever refactored or split, the detector still works. Trade-off: small code duplication. Worth it for module isolation.

4. **30s timeout ceiling** — D-02 budgets ~5s API time, but DeepSeek V4 Pro latency varies (Perplexity calls in Plan 01-04 took 90-300s for full Instagram analysis, but this mini-call is much simpler — boolean verdict from existing context). 30s gives a generous margin without blocking the 3-pass cycle for too long.

5. **Russian prompt matching LLM working language** — Pass 1 prompt in pass_collect.py is Russian (lines 49-56). The mini-call prompt is also Russian to match. Boundary rule keywords (`>50%`, `ОСНОВНОЙ профиль`, `косметология`, `пластическая хирургия`) are baked into the natural language — the LLM extracts them via semantic understanding, not keyword matching.

## Deviations from Plan

None — plan executed exactly as written. All 3 tasks followed the action steps verbatim:
- Task 1: added `niche: str = ""` after `error_message`, documented in docstring ✓
- Task 2: created `niche_detector.py` with all 10 acceptance criteria met ✓
- Task 3: inserted mini-call section between Pass 1 abort and Pass 2 invocation, populated `state.niche` + `state.collected_data["niche_detection"]`, logged outcome ✓

## Verification Artifacts

| Check | Result |
|-------|--------|
| `states.py` AST parse | OK (13 fields, niche present, all 12 pre-existing intact) |
| `niche_detector.py` AST parse | OK (async detect_instagram_critical_niche + 3 helpers) |
| `three_pass.py` AST parse | OK (mini-call wired, ordering Pass1<MiniCall<Pass2) |
| D-03 boundary rule keywords | All present: `>50%`, `ОСНОВНОЙ профиль`, `косметология`, `пластическая хирургия` |
| Fallback dict contract | Returns `{instagram_critical=False, niche="unknown"}` on ANY exception |
| Shared session via `_get_agent_for_session(state.session_id, state.mode)` | Yes |
| Logging (T-03-02-R mitigation) | `logger.info` with client_url + instagram_critical + niche + reason |
| No tests inside detector module | Confirmed (no `def test_` in source) |
| No calls to function from within module | Confirmed (function exported, not invoked) |
| `ORCHESTRATOR_MODE=0` regression | Mini-call only fires inside `run_three_pass`, which only runs when `ORCHESTRATOR_MODE=1` — default OFF path unaffected |

## Known Stubs

None. The `niche: str = ""` default is intentional — it represents "mini-call not yet run" state and is documented in the docstring. Once `run_three_pass` executes, the field is populated by the mini-call.

## Threat Flags

None. The mini-call's trust boundaries (LLM prompt + verdict ingestion) are covered by the plan's existing threat model:
- T-03-02-S (Spoofing): mitigated by Plan 03-03 hard-FAIL logic that checks `run_instagram_content` invocation independently
- T-03-02-R (Repudiation): mitigated by `logger.info` greppable audit trail
- T-03-02-D (DoS): mitigated by `_NICHE_DETECT_TIMEOUT = 30` (asyncio.wait_for)

## User Setup Required

None — purely additive orchestrator change, opt-in via `ORCHESTRATOR_MODE=1` (default OFF). Production presale flow unaffected.

## Next Phase Readiness

- **Ready for Plan 03-03** (Pass 1+2 prompts + QC checklist helpers) — `state.niche` and `state.collected_data["niche_detection"]` are now populated and available for consumption. Plan 03-03 will:
  - Add Pass 1 prompt rule "if niche=critical → ОБЯЗАТЕЛЬНО вызови run_instagram_content"
  - Add Pass 2 hard-FAIL rule for missing Instagram in critical niches
  - Add QC helpers `is_niche_instagram_critical(state)` + `is_item_applicable(item, state)`
- **NOT yet enforcing Instagram-mandatory** — this plan only adds detection plumbing. The enforcement rule comes in Plan 03-03 (prompts + checklist helpers) and Plan 03-06 (runtime hard-FAIL override).
- **IG-02 status:** partially addressed by this plan (detection enables downstream enforcement). Full IG-02 completion requires Plans 03-03 + 03-06.

## Self-Check: PASSED

- FOUND: `AIM/hermes/app/orchestrator/niche_detector.py`
- FOUND: `AIM/hermes/app/orchestrator/states.py` (with `niche` field)
- FOUND: `AIM/hermes/app/orchestrator/three_pass.py` (with mini-call wired)
- FOUND: commit `53a4db8` (Task 1: feat — niche field)
- FOUND: commit `e911542` (Task 2: feat — niche_detector module)
- FOUND: commit `ff4d28f` (Task 3: feat — wire mini-call)

---
*Phase: 03-instagram-integration*
*Completed: 2026-06-23*
