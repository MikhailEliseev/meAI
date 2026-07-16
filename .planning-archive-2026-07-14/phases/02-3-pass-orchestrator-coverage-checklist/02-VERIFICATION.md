---
phase: 02-3-pass-orchestrator-coverage-checklist
verified: 2026-06-23T15:05:00Z
status: human_needed
score: 16/16 must-haves verified at code level
overrides_applied: 0
mode: mvp
re_verification:
  previous_status: none
  previous_score: N/A
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "End-to-end runtime test: deploy ORCHESTRATOR_MODE=1 to aim-hermes container, trigger PRESALE + URL via Telegram/web, verify logs show 'Orchestrator: starting 3-pass cycle' + 3 distinct 'Orchestrator Pass N' log lines + 'Final QC coverage: X%' line"
    expected: "3 passes execute sequentially without exception, final coverage >0%, HTML report generated"
    why_human: "Requires live LLM (DeepSeek V4 Pro), Docker container deploy, and external AIM API at app:8000 — cannot be exercised in static verification. Per Phase 2 Plan 02-02 + 02-03 SUMMARYs: 'Полный smoke-test с live LLM вызовами требует деплоя в aim-hermes контейнер (через docker cp + gateway restart). Это отдельный шаг Phase 8 deploy plans.'"
  - test: "Pass 2 LLM JSON parsing under live DeepSeek response"
    expected: "Live LLM returns strict JSON {\"items\":[...],\"summary\":{...}} — direct json.loads succeeds (no regex-fallback path triggered)"
    why_human: "Prompt engineering quality vs. real model behavior cannot be verified without live API call. Static check confirms fallback chain exists, but primary (non-fallback) path success rate requires runtime measurement."
  - test: "Coverage >= 80% achieved on a real presale (e.g., iphk.ru reference or new clinic)"
    expected: "Final coverage_report shows status=PASS (>=12/15 filled) — matches QC-04 target"
    why_human: "LLM self-assessment honesty (T-02-03-S) + actual tool coverage depends on which tools LLM invokes against real clinic data. Cannot be measured statically."
  - test: "ORCHESTRATOR_MODE=0 (default) production behavior unchanged"
    expected: "Existing PRESALE flow (single AIAgent.run_conversation) still handles presale traffic without regression after Phase 2 deploy"
    why_human: "Requires Phase 8 deploy + observation of live production traffic — admin must verify no regression in aim-hermes presale flow."
---

# Phase 2: 3-Pass Orchestrator + Coverage Checklist — Verification Report

**Phase Goal:** Hermes runs an automatic 3-pass cycle (Collect → Gap-analyze → Fill+Assemble) with a QC checklist as the gap-analysis reference — no manual intervention
**Mode:** mvp
**Verified:** 2026-06-23T15:05:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### User Flow Coverage (MVP Mode)

| Step | User Action | Expected | Code Evidence | Status |
|------|-------------|----------|---------------|--------|
| 1 | Admin sends PRESALE + URL message (with ORCHESTRATOR_MODE=1) | Routing detects PRESALE + URL + opt-in flag | `agent_wrapper.py:777-784` — `if mode_upper in ("ONBOARDING","PRESALE")` AND `client_url` AND `ORCHESTRATOR_MODE` | ✓ VERIFIED (code) |
| 2 | Pass 1 (Collect) starts | LLM picks any of 49 tools by situation | `pass_collect.py:28-78` — single `agent.run_conversation(prompt)` call, prompt says "Вызывай ЛЮБЫЕ релевантные инструменты" | ✓ VERIFIED (code) |
| 3 | Pass 2 (Gap-analyze) runs against 15-item checklist | LLM produces strict JSON with filled/partial/missing + reason per item | `pass_gap_analyze.py:45-62, 65-125` — uses `render_checklist_for_llm()`, parses JSON via direct + regex fallback | ✓ VERIFIED (code) |
| 4 | QC gate runs between Pass 2 and Pass 3 | Soft warning if <80%, Pass 3 not blocked | `three_pass.py:114-134` — `coverage_after_p2 = calc_coverage(...)`, SOFT gate logs warning | ✓ VERIFIED (code) |
| 5 | Pass 3 (Fill+Assemble) runs | LLM fills gaps, calls generate_html_report | `pass_fill_assemble.py:28-80` — prompt requires `generate_html_report` call + `coverage_metadata` arg | ✓ VERIFIED (code) |
| 6 | HTML report rendered with QC Coverage section | Section shows X/15 (Y%) PASS/FAIL + per-item list with reasons | `generate_html_report.py:178-290, 1203-1204` — `_build_qc_coverage_section(metadata)` conditionally appended | ✓ VERIFIED (code) |
| 7 | Without URL: PRESALE behavior unchanged | Existing path (single AIAgent call) still runs | `agent_wrapper.py:832-833` — `else: logger.info("v8 routing: PRESALE без URL → AIAgent (приветствие)")` | ✓ VERIFIED (code) |
| 8 | PipelineEngine preserved as alternative (ORC-05) | engine.py NOT modified, _TOOL_HANDLERS intact | `pipeline/engine.py` — 50 internal references, mtime Jun 21 (pre-Phase 2) | ✓ VERIFIED (code) |

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin triggers a presale and observes 3 distinct passes executing automatically (SC-1) | ✓ VERIFIED | `three_pass.py:80-161` — three sequential `await run_pass_collect` / `run_pass_gap_analyze` / `run_pass_fill_assemble` calls, each with logger.info transitions |
| 2 | LLM-orchestrator selects tools by situation (SC-2 / ORC-02) | ✓ VERIFIED | `pass_collect.py:49-56` — prompt says "Вызывай ЛЮБЫЕ релевантные инструменты из твоего каталога (49 tools available)"; no hardcoded tool names in orchestrator/ (grep-confirmed) |
| 3 | After Pass 2, LLM produces gap-analysis report comparing collected data against 10-20 item checklist (SC-3) | ✓ VERIFIED | `qc_checklist.py:36-168` — 15 items (within 10-20 range); `pass_gap_analyze.py:45-62` — prompt embeds full 15-item checklist |
| 4 | Remaining gaps honestly marked "данные недоступны" — no fabricated data (SC-4 / ORC-04) | ✓ VERIFIED | `pass_gap_analyze.py:59` — "НЕ выдумывай данные"; `generate_html_report.py:242-256` — HTML section emits `данные недоступны: {reason}` for missing/partial |
| 5 | PipelineEngine still works as alternative mode (SC-5 / ORC-05) | ✓ VERIFIED | `pipeline/engine.py` — 90KB, 50 internal PipelineEngine/_TOOL_HANDLERS references, mtime 2026-06-21 (pre-Phase 2); 0 imports of `app.pipeline` from `app/orchestrator/` |
| 6 | Each run ends with coverage % report (target: ≥80% of checklist items filled) (SC-5 / QC-03+04) | ✓ VERIFIED | `three_pass.py:146-153` — `format_coverage_text(final_coverage)` logged; `qc_checklist.py:30-31` — `PASS_THRESHOLD=0.80`, `PASS_MIN_ITEMS=12` |
| 7 | `_unwrap_tool_output` NameError fixed (P02-01) | ✓ VERIFIED | `generate_html_report.py:375` — `def _unwrap_tool_output(phase_data: dict) -> dict | None:` at module level (AST-verified); called from line 465 in same module; `publish_scout_report.py:107` imports `_build_report_html` which inherits fix |
| 8 | ORCHESTRATOR_MODE env var OPT-IN, default OFF (P02-02) | ✓ VERIFIED | `agent_wrapper.py:66` — `ORCHESTRATOR_MODE = os.getenv("ORCHESTRATOR_MODE", "0") == "1"`; tested: `ORCHESTRATOR_MODE=0 → False`, `ORCHESTRATOR_MODE=1 → True` |
| 9 | 3 distinct AIAgent.run_conversation() calls on same session_id (P02-02) | ✓ VERIFIED | `pass_collect.py:58`, `pass_gap_analyze.py:90`, `pass_fill_assemble.py:60` — three separate `asyncio.wait_for(asyncio.to_thread(agent.run_conversation, prompt), ...)` calls; same `session_id` reused via `_get_agent_for_session` |
| 10 | Exception in orchestrator → fallback to AIAgent direct path (P02-02) | ✓ VERIFIED | `agent_wrapper.py:819-824` — `except Exception: logger.exception("Orchestrator failed, falling back to AIAgent direct path (session=%s)", sid)` then falls through (no return) |
| 11 | PRESALE без URL behavior unchanged (P02-02) | ✓ VERIFIED | `agent_wrapper.py:832-833` — `else: logger.info("v8 routing: PRESALE без URL → AIAgent (приветствие)")` — URL gate (`if client_url:`) at line 779 |
| 12 | OrchestratorState in-memory dataclass with pass_status / collected_data / gap_report (P02-02) | ✓ VERIFIED | `states.py:23-75` — `@dataclass class OrchestratorState` with all required fields; `mark_pass()` + `is_complete()` methods; tested: transitions work correctly |
| 13 | QC_CHECKLIST = exactly 15 items with required schema (P02-03 / QC-01) | ✓ VERIFIED | `qc_checklist.py:36-168` — `len(QC_CHECKLIST) == 15`; every item has `id`, `category`, `name`, `pass_criteria`, `source`; test `test_qc_checklist_pass_criteria_defined` PASSED |
| 14 | Pass 2 uses full 15-item checklist, not minimal 5-item (P02-03 / ORC-03) | ✓ VERIFIED | `pass_gap_analyze.py:25-28, 87` — imports `QC_CHECKLIST, render_checklist_for_llm`; uses `render_checklist_for_llm()` in prompt; old "competitors: find_competitors вызван?" pattern absent (grep-confirmed) |
| 15 | Soft QC gate between Pass 2 and Pass 3 (P02-03 / QC-02) | ✓ VERIFIED | `three_pass.py:109-134` — `if coverage_after_p2.status == "FAIL": logger.warning(...)` — non-blocking, Pass 3 always runs (verified via `await run_pass_fill_assemble(state)` at line 138 regardless of coverage status) |
| 16 | Coverage report rendered in HTML with PASS/FAIL badge + per-item list (P02-03 / QC-03) | ✓ VERIFIED | `generate_html_report.py:178-290` — `_build_qc_coverage_section(metadata)` renders `<span class="metric-tag metric-tag-success">PASS</span>` or `metric-tag-warning FAIL`; smoke test confirmed: 4499-char HTML with PASS badge + "QC Coverage Report" header + "данные недоступны" markers; backward compat verified: `_build_report_html(data, title)` without `coverage_metadata` produces no QC section |

**Score:** 16/16 truths verified at code level

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `AIM/hermes/app/orchestrator/__init__.py` | Package init exporting run_three_pass | ✓ VERIFIED | 16 lines, `from app.orchestrator.three_pass import run_three_pass`, `__all__ = ["run_three_pass"]` |
| `AIM/hermes/app/orchestrator/states.py` | OrchestratorState dataclass | ✓ VERIFIED | 80 lines, `@dataclass class OrchestratorState` with all required fields, `mark_pass()` / `is_complete()` |
| `AIM/hermes/app/orchestrator/three_pass.py` | Main entry point with sequential 3-pass flow | ✓ VERIFIED | 161 lines, `async def run_three_pass(session_id, client_url, client_name="", mode="PRESALE", chat_id=0) -> OrchestratorState` |
| `AIM/hermes/app/orchestrator/pass_collect.py` | Pass 1: LLM collect via any tools | ✓ VERIFIED | 99 lines, `async def run_pass_collect`, uses `agent.run_conversation` with 600s timeout via `asyncio.to_thread` |
| `AIM/hermes/app/orchestrator/pass_gap_analyze.py` | Pass 2: LLM gap-analysis vs 15-item checklist | ✓ VERIFIED | 217 lines, uses `render_checklist_for_llm()`, parses JSON with direct + regex fallback (`_JSON_BLOCK_RE`) |
| `AIM/hermes/app/orchestrator/pass_fill_assemble.py` | Pass 3: Fill gaps + assemble HTML | ✓ VERIFIED | 142 lines, `_build_prompt(state)` with coverage_hint + `coverage_metadata` instruction |
| `AIM/hermes/app/orchestrator/qc_checklist.py` | 15-item QC_CHECKLIST constant + thresholds | ✓ VERIFIED | 193 lines, `QC_CHECKLIST` 15-item list-of-dicts, `PASS_THRESHOLD=0.80`, `PASS_MIN_ITEMS=12`, `render_checklist_for_llm()` |
| `AIM/hermes/app/orchestrator/coverage_reporter.py` | calc_coverage + format_coverage_text + CoverageReport | ✓ VERIFIED | 177 lines, `@dataclass class CoverageReport`, `calc_coverage(gap_report)` robust to malformed input |
| `AIM/hermes/tests/test_qc_checklist.py` | 15 TDD tests covering structure + edges | ✓ VERIFIED | 223 lines, 15 tests, **15/15 PASSED** in pytest run |
| `AIM/hermes/app/agent_wrapper.py` | ORCHESTRATOR_MODE dispatch wired | ✓ VERIFIED | Lines 60-67 (env var), 492-516 (`_extract_orchestrator_reply`), 770-834 (PRESALE+URL+opt-in gate with try/except fallback) |
| `AIM/hermes/app/tools/generate_html_report.py` | _unwrap_tool_output fixed + QC section | ✓ VERIFIED | Line 375 (`_unwrap_tool_output` module-level def), line 178 (`_build_qc_coverage_section`), line 537 (`_build_report_html(data, title, coverage_metadata=None)`) |
| `AIM/hermes/app/tools/publish_scout_report.py` | No NameError (inherits fix via _build_report_html import) | ✓ VERIFIED | Line 107: `from app.tools.generate_html_report import _build_report_html` — inherits module-level `_unwrap_tool_output` |
| `AIM/hermes/app/pipeline/engine.py` | NOT modified (ORC-05 preserved) | ✓ VERIFIED | 90846 bytes, mtime Jun 21 2026 (pre-Phase 2), 50 internal `PipelineEngine`/`_TOOL_HANDLERS` references intact |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `agent_wrapper.py` | `orchestrator/three_pass.py` | `from app.orchestrator import run_three_pass` + dispatch in `run_agent_sync` | ✓ WIRED | `agent_wrapper.py:786` lazy import inside `if ORCHESTRATOR_MODE:` block; called at line 793 via `asyncio.run(run_three_pass(...))` |
| `three_pass.py` | `pass_collect.py` | `await run_pass_collect(state)` | ✓ WIRED | `three_pass.py:82` — single call after lazy import on line 81 |
| `three_pass.py` | `pass_gap_analyze.py` | `await run_pass_gap_analyze(state)` | ✓ WIRED | `three_pass.py:99` — single call after lazy import on line 98 |
| `three_pass.py` | `pass_fill_assemble.py` | `await run_pass_fill_assemble(state)` | ✓ WIRED | `three_pass.py:138` — single call after lazy import on line 137 |
| `three_pass.py` | `coverage_reporter.py` | `calc_coverage` + `format_coverage_text` | ✓ WIRED | `three_pass.py:30-33` — top-level import; called at lines 114, 146 |
| `three_pass.py` | `pipeline/engine.py` | fallback at agent_wrapper level (not in three_pass) | ✓ WIRED | Per design: fallback chain lives in `agent_wrapper.py:819-824` (exception handler); three_pass.py does NOT need pipeline import (architectural boundary respected) |
| `pass_gap_analyze.py` | `qc_checklist.py` | `from app.orchestrator.qc_checklist import QC_CHECKLIST, render_checklist_for_llm` | ✓ WIRED | `pass_gap_analyze.py:25-28` — top-level import; `render_checklist_for_llm()` called at line 87 |
| `pass_collect.py` | `agent_wrapper._create_agent` | lazy import: `from app.agent_wrapper import _agent_cache, _create_agent` | ✓ WIRED | `pass_collect.py:90` — lazy import inside `_get_agent_for_session()` to avoid circular dependency |
| `generate_html_report.py` | `orchestrator/coverage_reporter.py` | `from app.orchestrator.qc_checklist import QC_CHECKLIST` (inside `_build_qc_coverage_section`) | ✓ WIRED | `generate_html_report.py:220` — try/except wrapped lazy import for canonical item names |
| `generate_html_report.py` | `_build_qc_coverage_section` | conditional render at end of `_build_report_html` | ✓ WIRED | `generate_html_report.py:1203-1204` — `if coverage_metadata is not None: html_parts.append(_build_qc_coverage_section(coverage_metadata))` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|---------|
| `pass_collect.py` | `state.collected_data["pass_collect_result"]` | `agent.run_conversation(prompt)` → `result` dict | Yes — AIAgent returns `{text, tool_calls, tool_results}` per hermes-agent contract | ✓ FLOWING |
| `pass_gap_analyze.py` | `state.gap_report` | `_parse_gap_json(reply_text)` parses LLM JSON | Yes — LLM emits JSON per prompt contract; fallback to deterministic dict on parse failure | ✓ FLOWING |
| `three_pass.py` | `state.collected_data["coverage_report_after_pass2"]` | `asdict(calc_coverage(state.gap_report))` | Yes — computed from real gap_report; robust to malformed input (tests verify) | ✓ FLOWING |
| `three_pass.py` | `state.collected_data["coverage_report_final"]` | `asdict(calc_coverage(state.gap_report))` post-Pass-3 | Yes — recomputed after Pass 3 (may equal after_pass2 if Pass 3 doesn't mutate gap_report) | ✓ FLOWING |
| `generate_html_report.py` QC section | `coverage_metadata` (kwarg) | LLM Pass 3 prompt instructs: `coverage_metadata из доступного state.collected_data.coverage_report_after_pass2` | Conditional — depends on LLM following prompt instruction (documented limitation in 02-03 SUMMARY). Static fallback in `handle_generate_html_report:1260-1261`: reads from `args.get("coverage_metadata")` if not in kwargs | ⚠️ LLM-DEPENDENT |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All Phase 2 file syntax valid | `python3 -c "import ast; [ast.parse(open(f).read()) for f in [...]]"` | 10/10 files parse cleanly | ✓ PASS |
| QC_CHECKLIST structure | `python3 -c "from app.orchestrator.qc_checklist import QC_CHECKLIST; assert len(QC_CHECKLIST) == 15"` | 15 items confirmed | ✓ PASS |
| Coverage edge boundary 12/15 = PASS | `calc_coverage(gap_12_filled)` | `coverage_pct=0.8000, status=PASS` | ✓ PASS |
| Coverage edge boundary 11/15 = FAIL | `calc_coverage(gap_11_filled)` | `coverage_pct=0.7333, status=FAIL` | ✓ PASS |
| Empty gap_report robustness | `calc_coverage({})` | `coverage_pct=0.0, status=FAIL, total_items=15` (no crash) | ✓ PASS |
| ORCHESTRATOR_MODE=0 default | `ORCHESTRATOR_MODE=0 python3 -c "from app.agent_wrapper import ORCHESTRATOR_MODE; assert not ORCHESTRATOR_MODE"` | False | ✓ PASS |
| ORCHESTRATOR_MODE=1 opt-in | `ORCHESTRATOR_MODE=1 python3 -c "from app.agent_wrapper import ORCHESTRATOR_MODE; assert ORCHESTRATOR_MODE"` | True | ✓ PASS |
| State transitions | `OrchestratorState(...).mark_pass("collect","running"); assert s.pass_status == {"collect":"running"}` | Works | ✓ PASS |
| `is_complete()` after 3 completed passes | `s.mark_pass("collect","completed"); s.mark_pass("gap_analyze","completed"); s.mark_pass("fill_assemble","completed"); s.is_complete()` | True | ✓ PASS |
| `_unwrap_tool_output` at module level | AST scan of `generate_html_report.py` | FunctionDef in Module body at line 375 | ✓ PASS |
| `_build_qc_coverage_section` renders PASS case | `_build_qc_coverage_section(mock_metadata)` | 4499-char HTML with "QC Coverage Report", "PASS", "86.7%", "Whitefields", "insufficient competitor data", "данные недоступны" | ✓ PASS |
| Backward compat — no metadata | `_build_report_html(data, title)` (no 3rd arg) | No "QC Coverage Report" in HTML | ✓ PASS |
| 15 TDD tests in `test_qc_checklist.py` | `python3 -m pytest tests/test_qc_checklist.py -v` | **15/15 PASSED** | ✓ PASS |
| `_extract_orchestrator_reply` defined | AST scan of `agent_wrapper.py` | Top-level FunctionDef | ✓ PASS |
| `run_three_pass` references in agent_wrapper | grep count | 6 occurrences (import + call + docstring + comment) | ✓ PASS |
| `ORCHESTRATOR_MODE` references in agent_wrapper | grep count | 11 occurrences (env var + log + dispatch + comments) | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — no `scripts/*/tests/probe-*.sh` probes declared in Phase 2 PLANs. Phase 2 is code-implementation, not migration/tooling.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ORC-01 | 02-02-PLAN | 3-проходный цикл (Collect → Gap-analyze → Fill+Assemble), automatically | ✓ SATISFIED | `three_pass.py:80-161` — three sequential pass calls with state transitions, no manual intervention |
| ORC-02 | 02-02-PLAN | LLM-оркестратор выбирает инструменты по ситуации (как v1, не v3/v7) | ✓ SATISFIED | `pass_collect.py:49-56` — prompt instructs LLM to call ANY relevant tools; 0 hardcoded tool names in orchestrator/ (grep-confirmed) |
| ORC-03 | 02-03-PLAN | Гэп-анализ сравнивает собранные данные с QC-чек-листом | ✓ SATISFIED | `pass_gap_analyze.py:45-62` — full 15-item checklist prompt; `three_pass.py:114` — `calc_coverage(state.gap_report)` computes coverage from QC_CHECKLIST evaluation |
| ORC-04 | 02-03-PLAN | Если после 3-го прохода остаются пробелы — LLM честно отмечает «данные недоступны» | ✓ SATISFIED | `pass_gap_analyze.py:59` — "НЕ выдумывай данные"; `pass_fill_assemble.py:135-136` — "Если данные недоступны — честно отметь"; `generate_html_report.py:252-256` — HTML emits `данные недоступны: {reason}` |
| ORC-05 | 02-01-PLAN, 02-02-PLAN | PipelineEngine остаётся как опция (не удаляется) | ✓ SATISFIED | `pipeline/engine.py` 90KB unmodified (mtime 2026-06-21, pre-Phase 2); `_TOOL_HANDLERS` 22 entries intact; 0 imports of `app.pipeline` from `app/orchestrator/` |
| QC-01 | 02-03-PLAN | QC-чек-лист покрытия: 10-20 пунктов | ✓ SATISFIED | `qc_checklist.py:36-168` — exactly 15 items (within 10-20 range); test `test_qc_checklist_has_15_items` PASSED |
| QC-02 | 02-03-PLAN | Автоматическая проверка чек-листа перед генерацией HTML | ✓ SATISFIED | `three_pass.py:109-134` — SOFT QC gate between Pass 2 and Pass 3 (warning only, non-blocking); `pass_fill_assemble.py:131-141` — Pass 3 receives gap info and attempts to fill |
| QC-03 | 02-03-PLAN | Отчёт о покрытии в конце каждого прогона: % заполненных пунктов | ✓ SATISFIED | `three_pass.py:146-153` — `format_coverage_text(final_coverage)` logged at INFO (greppable summary); `generate_html_report.py:178-290` — HTML "QC Coverage Report" section with per-item breakdown |
| QC-04 | 02-03-PLAN | Цель покрытия: ≥ 80% пунктов чек-листа | ✓ SATISFIED | `qc_checklist.py:30-31` — `PASS_THRESHOLD: float = 0.80`, `PASS_MIN_ITEMS: int = 12`; tests `test_coverage_report_edge_12_of_15` (PASS) and `test_coverage_report_edge_11_of_15` (FAIL) verify boundary |

**Requirements:** 9/9 SATISFIED (ORC-01..05, QC-01..04). No orphaned requirements — REQUIREMENTS.md Traceability table maps all 9 to Phase 2 and all 9 are claimed by Phase 2 plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|---------|--------|
| (none) | — | — | — | No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers in any Phase 2 modified file (grep-confirmed across `app/orchestrator/*.py`, `app/tools/generate_html_report.py`, `app/tools/publish_scout_report.py`, `app/agent_wrapper.py`) |

No blocker anti-patterns found. The `generate_html_report_v7_backup.py` file (in `.planning/STATUS.md` working tree but not in git index for Phase 2) contains an OLD signature `_unwrap_tool_output(raw: dict)` — this is dead code intentionally preserved per Plan 02-01 (forbidden from refactoring). The CURRENT working definition at line 375 of `generate_html_report.py` uses the correct `phase_data` parameter matching the call site at line 465.

### Human Verification Required

#### 1. End-to-End Runtime Test (Phase 8 Deploy)

**Test:** Deploy `ORCHESTRATOR_MODE=1` to `aim-hermes` container via `docker cp` + gateway restart. Trigger PRESALE + URL message via Telegram bot or web chat. Tail logs for:
- `Orchestrator: starting 3-pass cycle for {url}`
- `Orchestrator Pass 1 (Collect): starting`
- `Orchestrator Pass 2 (Gap-analyze): starting`
- `Orchestrator Pass 3 (Fill+Assemble): starting`
- `Final QC coverage: X% — PASS|FAIL`

**Expected:** All 3 passes execute sequentially without exception. Final coverage >0%. HTML report generated with "QC Coverage Report" section.

**Why human:** Requires live DeepSeek V4 Pro LLM, Docker container deploy, and external AIM API at `app:8000` — none of which can be exercised in static verification. Per Plan 02-02 + 02-03 SUMMARYs: "Полный smoke-test с live LLM вызовами требует деплоя в `aim-hermes` контейнер. Это отдельный шаг Phase 8 deploy plans."

#### 2. Pass 2 LLM JSON Parsing (Live)

**Test:** Send PRESALE + URL with `ORCHESTRATOR_MODE=1`. Check `state.collected_data["pass_gap_analyze_result"]["raw_response"]` — verify LLM produced clean JSON that parsed via direct `json.loads` (not regex-fallback).

**Expected:** Direct parse succeeds on first try (no `_fallback_report()` invocation, no `parse_error` key in `state.gap_report`).

**Why human:** Prompt engineering quality vs. real DeepSeek response variability cannot be verified without live API call. Static check confirms fallback chain exists (`_parse_gap_json` at `pass_gap_analyze.py:148-185`), but primary (non-fallback) path success rate requires runtime measurement.

#### 3. Real Coverage ≥ 80% on Reference Clinic

**Test:** Run orchestrator on `iphk.ru` (Phase 1 reference) or new clinic. Check `state.collected_data["coverage_report_final"]["status"]`.

**Expected:** `status == "PASS"` (≥12/15 items filled) — matches QC-04 target on at least one real clinic.

**Why human:** LLM self-assessment honesty (T-02-03-S threat — "LLM may inflate coverage") + actual tool coverage depends on which tools LLM invokes against real clinic data. Cannot be measured statically. Future mitigation (Python validator) explicitly deferred in 02-03 SUMMARY Limitations section.

#### 4. ORCHESTRATOR_MODE=0 No-Regression (Production)

**Test:** Deploy Phase 2 to production with `ORCHESTRATOR_MODE=0` (default). Observe 1-2 days of normal presale traffic.

**Expected:** Existing PRESALE flow (single `AIAgent.run_conversation` call) handles traffic without exception. No regression in conversion rate or report quality.

**Why human:** Requires Phase 8 deploy + observation of live production traffic. Admin must verify no regression in aim-hermes presale flow when Phase 2 code is present but orchestrator opt-in is OFF.

### Gaps Summary

No code-level gaps found. All 16 truths verified, all 13 artifacts substantive and wired, all 10 key links connected, all 9 requirements satisfied.

**Status:** `human_needed` — code-level verification complete and passing, but 4 runtime verification items require Phase 8 deploy + live LLM testing to confirm end-to-end behavior. Per Phase 2 Mode: mvp, this is the expected verification level — code-first, deploy-validated later.

**Documented limitations (not gaps):**
- LLM-prompt approach for `coverage_metadata` transmission (02-03 SUMMARY): if Pass 3 LLM forgets to pass `coverage_metadata`, QC section doesn't appear in HTML (graceful degradation, no crash). Future improvement: orchestrator calls `generate_html_report` post-Pass-3 directly.
- LLM self-assessment honesty (T-02-03-S): `calc_coverage` trusts LLM filled/partial/missing evaluations. Mitigation via prompt instruction "НЕ выдумывай данные" + reason for missing. Future: Python validator could random-check items.
- No retroactive recalculation after Pass 3 unless LLM mutates `state.gap_report` (documented in 02-03 SUMMARY Limitations).

---

_Verified: 2026-06-23T15:05:00Z_
_Verifier: Claude (gsd-verifier)_
