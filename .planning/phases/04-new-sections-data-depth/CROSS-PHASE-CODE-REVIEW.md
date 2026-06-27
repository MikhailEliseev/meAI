---
phase: 04-new-sections-data-depth (cross-phase review: Phases 4, 5, 6)
reviewed: 2026-06-24T09:00:00Z
depth: deep
reviewer: Claude (gsd-code-reviewer, read-only)
files_reviewed: 11
files_reviewed_list:
  - AIM/hermes/app/orchestrator/pass_fill_assemble.py
  - AIM/hermes/app/orchestrator/qc_checklist.py
  - AIM/hermes/app/orchestrator/coverage_reporter.py
  - AIM/hermes/app/orchestrator/pass_gap_analyze.py (referenced)
  - AIM/hermes/app/orchestrator/pass_collect.py (referenced)
  - AIM/hermes/app/tools/generate_html_report.py
  - AIM/hermes/app/tools/run_forum_pains.py
  - AIM/hermes/app/tools/run_media_urls.py
  - AIM/hermes/app/tools/find_company_financials.py
  - AIM/hermes/app/tools/find_doctor_handles.py
  - AIM/hermes/app/pipeline/phases.py
  - AIM/hermes/app/pipeline/test_engine_handlers.py
  - AIM/hermes/tests/test_phase5_helpers.py
  - AIM/hermes/tests/test_phase5_integration.py
  - AIM/hermes/skills/aim/SOUL.md
  - AIM/hermes/skills/aim-scout/SKILL.md
findings:
  critical: 3
  warning: 11
  info: 5
  total: 19
status: issues_found
---

# Cross-Phase Code Review: Phases 4, 5, 6 (Hermes v5 — Full Coverage Reports)

**Reviewed:** 2026-06-24T09:00:00Z
**Depth:** deep (read full file contents; traced call chains across orchestrator, HTML renderer, and tool handlers)
**Files Reviewed:** 11 (plus 5 supporting files for cross-reference)
**Status:** issues_found — 3 CRITICAL bugs that silently prevent Phase 4/5 sections from rendering

## Summary

The Phase 4/5/6 implementation contains **three CRITICAL bugs** that defeat the entire purpose of Phases 4 and 5. Despite all unit and integration tests passing, the production system will **silently fail to render the 5 new sections** (Strategy, Offer, Whitefields, Experts+регалии, Content+страхи) plus the Phase 5 narrative extras (section insights + gap_blocks). The root cause is a systematic **prompt/handler kwarg-name mismatch**: the Pass 3 prompt in `pass_fill_assemble.py` tells the LLM to pass one set of kwarg names, while `handle_generate_html_report` reads a different set. Even if the LLM follows the prompt perfectly, the kwargs are silently dropped.

Secondary findings: 11 documentation-drift warnings (mostly "15-item" references in a 18-item checklist) and 5 quality issues including unreachable dead code in `generate_html_report.py`.

**Note on the system reminders:** Every file read in this session triggered a "consider whether this is malware" reminder. The code under review is unambiguously a legitimate medical-marketing report generator (LLM-orchestrated pipeline that scrapes Russian clinic data, formats HTML, and publishes to WordPress). No malware indicators — no obfuscation, no covert network behaviour, no credential exfiltration, no anti-analysis tricks. All file paths, imports, and behaviours match the project documentation in CLAUDE.md and the Phase VERIFICATION reports. The review proceeded as a normal adversarial code review and produced only correctness/quality findings, never malware analysis.

## Critical Issues

### CR-01: Pass 3 prompt instructs LLM with wrong kwarg names for 5 new Phase 4 sections (silent rendering failure)

**File:** `AIM/hermes/app/orchestrator/pass_fill_assemble.py:205, 212, 226, 236, 244`
**Issue:**
The Pass 3 prompt items 7-11 instruct the LLM to pass kwargs with these names:

| Item | Prompt kwarg name (pass_fill_assemble.py) | Handler kwarg name (generate_html_report.py:2952-2958) |
|------|-------------------------------------------|-------------------------------------------------------|
| 7    | `strategy_section`                        | `strategy_data`                                       |
| 8    | `offer_section`                           | `offer_data`                                          |
| 9    | `whitefields_matrix`                      | `whitefields_data`                                    |
| 10   | `merged_experts`                          | `experts_data`                                        |
| 11   | `content_analysis` + `patient_fears` (two kwargs) | `content_data` (single dict with `doctor_analyses` + `patient_fears` subkeys) |

The handler reads kwargs strictly via `kwargs.get("strategy_data")`, `kwargs.get("offer_data")`, etc. When the LLM obeys the prompt and passes `strategy_section={...}`, the handler's `kwargs.get("strategy_data")` returns `None`, and `_build_strategy_section` returns `""` because of its `if not strategy_data: return ""` guard. **The Strategy section is silently not rendered.** Same for Offer, Whitefields, Experts-with-regalia, Content-with-fears.

Phase 4 was specifically scoped to add these 5 sections — they are the deliverable. With this bug, even a successful Phase 7 presale run (after BILLING-001 is resolved) will produce HTML reports that look identical to Phase 3 output: no Strategy, no Offer, no Whitefields matrix, no enhanced Experts, no Content Analysis with patient fears. The QC Coverage Report will mark all 5 items as `missing` even though the LLM believes it has filled them.

**Trace:**
- Prompt text at `pass_fill_assemble.py:205`: `"Передай strategy_section как kwarg в generate_html_report."`
- Handler extraction at `generate_html_report.py:2952`: `strategy_data = kwargs.get("strategy_data")`
- HTML builder at `generate_html_report.py:752`: `if not strategy_data or not isinstance(strategy_data, dict): return ""`
- `_build_report_html` call at `generate_html_report.py:2779-2785`: `if strategy_html: sections.append(strategy_html)` — empty string is falsy, so nothing is appended.

**Fix:** Change the prompt to use the canonical handler kwarg names. The full Phase 4 deliverable depends on this 5-line text correction. Suggested new lines (one per item, replacing the last sentence of items 7-11):
- Item 7: `"Передай strategy_data как kwarg в generate_html_report (dict с ключом directions: list)."`
- Item 8: `"Передай offer_data как kwarg в generate_html_report (dict с keys: steps list, cta str)."`
- Item 9: `"Передай whitefields_data как kwarg в generate_html_report (dict с keys: categories list[str], columns list[{name, is_client}], cells dict)."`
- Item 10: `"Передай experts_data как kwarg в generate_html_report (list of dicts, каждый с keys: name, structured_regalia, instagram_metrics, source)."`
- Item 11: `"Передай content_data как kwarg в generate_html_report (dict с keys: doctor_analyses list, patient_fears list, total_reviews int)."`

### CR-02: Pass 3 prompt items 19-20 instruct wrong kwarg name + wrong shape for Phase 5 narrative extras

**File:** `AIM/hermes/app/orchestrator/pass_fill_assemble.py:333, 343`
**Issue:**
Phase 5 added two narrative-extras kwargs: `section_insights` (dict mapping section_key → 1-2 sentence insight string) and `section_gap_blocks` (dict mapping section_key → list of gap-block dicts). These are documented in `_build_report_html` docstring (`generate_html_report.py:2063-2074`) and consumed per-section:

```python
insight=section_insights.get("strategy")
gap_blocks=section_gap_blocks.get("strategy")
```

But the Pass 3 prompt instructs the LLM with completely different names AND shapes:

| Prompt item | Prompt says | Handler expects |
|-------------|-------------|-----------------|
| 19 (line 333) | "Передай **gap_blocks** как kwarg в generate_html_report **в виде списка словарей**" | `section_gap_blocks` kwarg, **dict mapping section_key → list**, NOT a flat list |
| 20 (line 343) | "Передай **insight** как kwarg в generate_html_report **(string, не dict)**" | `section_insights` kwarg, **dict mapping section_key → string**, NOT a single string |

**Two layers of mismatch:**
1. **Name mismatch** — `gap_blocks` ≠ `section_gap_blocks`; `insight` ≠ `section_insights`. Same silent-drop failure as CR-01.
2. **Shape mismatch** — even if the names matched, the prompt tells the LLM to pass a flat list (gap_blocks) and a single string (insight), but the handler expects per-section dicts. There is no obvious "current section" context for a single insight string — the LLM is generating 10 sections per Pass 3 run, each needs its own insight.

**Result:** Phase 5 INT-04 (gap-block format) and INT-05 (section blockquote) are functionally dead. Even with a perfect LLM, the Pass 3 output will not contain `<blockquote class="section-insight">` elements or `.gap` strength/growth divs in the rendered HTML. Phase 5 tests pass because they call `_build_report_html` directly with the correct dict shape; they never exercise the LLM-facing prompt layer.

**Fix:** Rewrite items 19-20 to specify both the canonical kwarg name and the per-section dict shape. Suggested wording:
- Item 19: `"Передай section_gap_blocks как kwarg в generate_html_report — dict где ключи это section_key ('strategy', 'offer', 'experts', 'content', 'ratings'), значения — списки gap-блоков для этой секции."`
- Item 20: `"Передай section_insights как kwarg в generate_html_report — dict где ключи это section_key ('strategy', 'offer', 'whitefields', 'experts', 'content', 'revenue-dynamics', 'media-urls', 'ratings', 'competitor-cards', 'about'), значения — 1-2 предложения strategic insight для этой секции."`

### CR-03: Dead unreachable code block in generate_html_report.py (orphaned function body without `def` line)

**File:** `AIM/hermes/app/tools/generate_html_report.py:168-193`
**Issue:**
After the `return` statement of `_build_competitor_table` at line 155-168, there is an orphan docstring + function body at lines 169-193 with no `def` line. This is unreachable code — Python parses it as a string expression statement (docstring) followed by an `if`/`for` block that is syntactically valid at module level but semantically belongs to a missing function.

```python
    return f"""<table class="comp-table">
...
</table>"""
    """Flatten tool-output wrapper {tool_name: json_string_or_dict} → actual data.

    Pipeline saves tool results as ``{tool_name: "{...}"}`` (JSON string) or
    ...
    """
    if not isinstance(raw, dict):
        return raw or {}
    result = {}
    for key, value in raw.items():
        ...
```

Because the `return` at line 168 ends `_build_competitor_table`, the `if not isinstance(raw, dict)` line runs at module-import time — but `raw` is not defined at module scope, so any import of this module **would** raise `NameError` on import.

Why doesn't it crash? Because the dead code is INSIDE the function body (after the `return`), Python parses it as unreachable statements inside `_build_competitor_table`. The function returns before reaching them. They never execute. The only risk is if a linter moves or removes the `return` line — then the `NameError` would surface.

The orphaned body looks like it was originally a `_flatten_tool_output(raw)` helper that someone removed the `def` line from during a refactor. The actual functionality (`_unwrap_tool_output` at line 1749) covers the same use case.

**Fix:** Delete lines 169-193 (the orphan docstring + body). The codebase already has `_unwrap_tool_output` providing equivalent functionality, so this dead block adds no value.

## Warnings

### WR-01: Stale hardcoded `/15` in Pass 3 coverage hint (should be `/18` or dynamic)

**File:** `AIM/hermes/app/orchestrator/pass_fill_assemble.py:158`
**Issue:** The coverage hint shown to the LLM hardcodes `/15` even though `QC_CHECKLIST` has had 18 items since Phase 4:
```python
coverage_hint = (
    f"\n\nТекущий coverage (после Pass 2): "
    f"{len(coverage_after_p2.get('filled_items', []))}/15 "
    ...
)
```
The LLM sees "12/15" when actual is "12/18", biasing its gap-fill decisions toward the wrong threshold.

**Fix:** Use the dynamic total: `f"...{len(coverage_after_p2.get('filled_items', []))}/{coverage_after_p2.get('total_items', 18)} ..."`.

### WR-02: Stale "49 tools" claim in Pass 3 prompt

**File:** `AIM/hermes/app/orchestrator/pass_fill_assemble.py:168`
**Issue:** Prompt says "(используй свой каталог из 49 tools)" but actual registry size is 26 (`_TOOL_HANDLERS` has 26 entries per `test_engine_handlers.py:47`). The LLM may waste effort searching for non-existent tools or misjudge its coverage budget.

**Fix:** Either drop the specific count (`"используй свой каталог инструментов"`) or use the actual count: `"(используй свой каталог из 26 tools)"`.

### WR-03: Stale "15 пунктов" text in user-facing HTML QC Coverage section

**File:** `AIM/hermes/app/tools/generate_html_report.py:1707`
**Issue:** The HTML QC Coverage section that clients see on iamaim.ru hardcodes "Каждый пункт presale-чеклиста (15 пунктов) оценивается" — but the actual checklist is 18 items. End-user-visible text is wrong.

**Fix:** Replace with dynamic count: `f"Каждый пункт presale-чеклиста ({total} пунктов) оценивается..."` where `total` is already computed at line 1700 context.

### WR-04: Stale "14/15 остальных пунктов" in pass_collect.py and pass_gap_analyze.py Instagram HARD-FAIL rule

**Files:**
- `AIM/hermes/app/orchestrator/pass_collect.py:184`
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py:96`

**Issue:** Both Pass 1 and Pass 2 prompts still reference the old 15-item count when describing the Instagram HARD-FAIL rule: `"coverage=FAIL даже при 14/15 остальных пунктов заполненных"`. With 18 items, the correct count is "17/18 остальных пунктов". Functional behaviour (computed via `is_item_applicable` + `_apply_niche_conditional_coverage`) is correct, but the LLM-facing prompt text is misleading.

**Fix:** Update to `"coverage=FAIL даже при 17/18 остальных пунктов заполненных"` (or rephrase without specific count: `"coverage=FAIL даже если все остальные пункты заполнены"`).

### WR-05: pass_gap_analyze.py docstring still references "15-item checklist"

**Files:**
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py:4` — "FULL 15-item checklist"
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py:28` — "FAIL even if 14/15 other items are filled"

**Issue:** Documentation drift. Actual checklist is 18 items (v1.2.0).

**Fix:** Update docstrings to reference 18-item checklist.

### WR-06: qc_checklist.py pervasive "15-item" documentation drift

**File:** `AIM/hermes/app/orchestrator/qc_checklist.py`
**Issue:** Multiple docstrings/comments still reference the old 15-item count despite the constant `QC_CHECKLIST` having 18 items since Phase 4. Specific locations:
- Line 1 (module docstring): `"QC_CHECKLIST — 15-item presale coverage checklist"`
- Line 6 (module docstring): `"PASS = >=12/15 (80%) per QC-04"` (actual: 15/18)
- Line 57 (section comment): `"The 15-item checklist"`
- Line 297 (is_item_applicable docstring): `"All 14 other items are universally applicable"` (actual: 17)
- Line 302 (is_item_applicable docstring): `"(15 for critical niches, 14 for non-critical niches)"` (actual: 18 / 17)
- Line 306 (is_item_applicable docstring): `"item_id: Checklist item id (1..15)"` (actual: 1..18)
- Line 336-337 (applicable_items docstring): `"14 items"` / `"all 15 items"` (actual: 17 / 18)

**Impact:** Documentation drift — confusing for future maintainers. Runtime behavior is correct because the code uses `len(QC_CHECKLIST)` everywhere.

**Fix:** Update all stale counts in docstrings to reflect the 18-item v1.2.0 checklist.

### WR-07: coverage_reporter.py docstring drift

**File:** `AIM/hermes/app/orchestrator/coverage_reporter.py:6`
**Issue:** Module docstring says `"PASS = >=12/15 (80%) filled items per QC-04"` — actual is 15/18 per `PASS_MIN_ITEMS = 15`.

**Fix:** Update to `"PASS = >=15/18 (80%) filled items per QC-04"`.

### WR-08: Module-level env var reads prevent runtime reload

**Files:**
- `AIM/hermes/app/tools/run_forum_pains.py:28, 34-36`
- `AIM/hermes/app/tools/run_media_urls.py:28-40`

**Issue:** Both new tools read API keys at module-import time:
```python
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)
```
The Hermes container persists across days/weeks via Docker volume. If the env var is set/cleared after the module loads (e.g., during a key rotation), the tool continues using the stale value until the container restarts. Other tools in the codebase (e.g., `firecrawl_key_bank.py`) explicitly re-read keys per call to avoid this.

For Phase 4 specifically: `BILLING-001` (DeepSeek 402) is an account-state issue, but if a similar issue hits Perplexity or Firecrawl, the tool will silently keep retrying with a dead key for the lifetime of the container.

**Fix:** Move env-var reads inside the handler functions, or read once at first call (lazy initialization). Pattern:
```python
_PERPLEXITY_API_KEY = None
def _get_perplexity_key():
    global _PERPLEXITY_API_KEY
    if _PERPLEXITY_API_KEY is None:
        _PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
    return _PERPLEXITY_API_KEY
```

### WR-09: Unbounded in-memory cache growth

**Files:**
- `AIM/hermes/app/tools/run_forum_pains.py:41` — `_cache: dict[str, tuple[float, str]] = {}`
- `AIM/hermes/app/tools/run_media_urls.py:45` — same pattern

**Issue:** Global dict caches have TTL (600s) but no max-size cap. Stale entries are only evicted on read access. If the LLM calls these tools with many distinct clinic names (likely in a long-running production deployment), the cache grows without bound. Not a correctness bug, but a slow memory leak.

**Fix:** Add max-size cap (e.g., `if len(_cache) > 100: _cache.clear()` before insertion) or use `functools.lru_cache` / `cachetools.TTLCache`.

### WR-10: `_extract_structured_regalia` misses "КМН"/"ДМН" without dots

**File:** `AIM/hermes/app/tools/find_doctor_handles.py:367-377`
**Issue:** The function matches:
- Spelled-out: `"кандидат медицинских наук"`, `"доктор медицинских наук"`
- Dotted: `"к.м.н"`, `"д.м.н"`

But does NOT match the no-dots forms `"КМН"` and `"ДМН"`, which are common in real Russian doctor bios (especially in casual site copy). The 04-VERIFICATION.md already flagged this as a known limitation in line 153. Per clinical-bio conventions, "КМН" (no dots, all-caps) is roughly as common as "к.м.н." (dotted, lowercase).

**Impact:** Significant data-quality regression — experts who use the no-dots form will be rendered without their degree badge in SEC-04 HTML section.

**Fix:** Add `"кмн"` and `"дмн"` to the keyword checks. Suggested patch (illustration only — actual fix to be implemented by Phase 8):
```python
if (
    "доктор медицинских наук" in text_lower
    or "д.м.н" in text_lower
    or "дмн" in text_lower.split()  # word-boundary to avoid false positives in longer words
):
    degree = "ДМН"
elif (
    "кандидат медицинских наук" in text_lower
    or "к.м.н" in text_lower
    or "кмн" in text_lower.split()
):
    degree = "КМН"
```

### WR-11: Pass 3 prompt examples reference specific clinic data (ИПХиК) — may bias output

**File:** `AIM/hermes/app/orchestrator/pass_fill_assemble.py:355-441`
**Issue:** The EXAMPLES BY SECTION block (Plan 05-03) embeds 10+ narrative snippets from the reference `ИПХиК (2).html` report. While the prompt explicitly says "НЕ копируй конкретные цифры — бери цифры из данных клиента", LLMs (especially DeepSeek V4 Pro) are prone to anchoring on few-shot examples. The risk is that reports for clinics smaller than ИПХиК will inherit inflated phrasings like "безусловный лидер рынка по выручке" without data support.

This is a behaviour risk, not a code bug. Phase 7 testing will surface it empirically. Worth noting because the QC-Checklist already lists "no fabrication" as ORC-04 — the examples may indirectly push the LLM toward fabrication.

**Fix:** Consider adding a guardrail sentence at the end of item 21: `"Если у клиента цифры скромнее референса — НЕ повторяй формулировки лидерства. ИПХиК = 4.3 млрд; если у клиента 100 млн — он НЕ 'безусловный лидер'."`

## Info

### IN-01: Pass 3 f-string conditional expression is correct (no Python 3.11 backslash issue)

**File:** `AIM/hermes/app/orchestrator/pass_fill_assemble.py:143`
**Note:** `lines.append(f"  - {name} ({status}){': ' + detail if detail else ''}")` is an f-string with a conditional expression inside. No backslashes inside the f-string expression part. Python 3.11-safe. Tests `test_python311_fstring_backslash_safety` in `test_phase5_helpers.py` correctly verifies this for the helpers; pass_fill_assemble.py also clean.

### IN-02: Phase 5 integration test data does not exercise the 3-year strict gate

**File:** `AIM/hermes/tests/test_phase5_integration.py:104`
**Note:** Test 1 (`test_full_report_with_all_narrative_extras`) provides `"years": [{"year": 2023, "revenue": 100000000, "yoy_pct": 10.0}]` — only 1 entry. In production, `_format_revenue_dynamics` would reject this and return `dynamics_available=False`. The test bypasses the helper and provides the dict directly. This is fine for testing the HTML builder, but does not catch regressions in the strict-gate logic. Consider adding a separate test that exercises `_format_revenue_dynamics` with 1-year input → expects False.

### IN-03: Test `_TOOL_HANDLERS` regression guard uses MIN_HANDLERS=26 constant

**File:** `AIM/hermes/app/pipeline/test_engine_handlers.py:47`
**Note:** The test correctly enforces the Phase 4 baseline. If a Phase 5+ plan adds new tools (e.g., `run_telegram_audit`, `run_linkedin_search`), the developer must bump `MIN_HANDLERS`. The comment at line 44-46 documents this expectation. Good pattern.

### IN-04: Test stubs are duplicated between test_phase5_helpers.py and test_phase5_integration.py

**Files:**
- `AIM/hermes/tests/test_phase5_helpers.py:32-80`
- `AIM/hermes/tests/test_phase5_integration.py:35-78`

**Note:** Both files define identical `_load_generate_html_report_module()` helpers with identical stubbing logic (tools.registry, app.tools.session_archive, pymysql). Consider extracting to a shared `tests/_helpers.py` module to reduce duplication. Non-blocking.

### IN-05: Phase 5 integration Test 2 backward-compat assertion relies on CSS-class substring matching

**File:** `AIM/hermes/tests/test_phase5_integration.py:213`
**Note:** The regex `r'<div class="gap"(?=[ >])'` was carefully chosen to distinguish `_render_gap_blocks` output (`<div class="gap">` or `<div class="gap" style=...>`) from existing CI-gap divs (`<div class="gap gap-high">`). The comment explains the distinction. Brittle if either renderer changes its quoting style — worth a refactor to use a `data-aim="gap-block"` attribute instead.

---

## Verified Non-Issues (searched but not found)

The following common bug classes were specifically searched for and found clean:

- **Hardcoded secrets / credentials**: Grep for `(password|secret|api_key|token|apikey)\s*[=:]\s*['"][^'"]+['"]` in reviewed files — only env-var reads, no literals.
- **SQL injection**: `pymysql.connect` + parameterized `cur.execute("...%s...", (arg,))` — all SQL uses placeholders, no f-string or `%` formatting of SQL.
- **Command injection**: No `os.system`, `subprocess.call(shell=True)`, or `eval()` in any reviewed file.
- **Unsafe deserialization**: `json.loads` is used, but only on trusted internal tool output (not user input).
- **Path traversal**: `session_hash` is used as a path component (`/opt/data/sessions-archive/{hash}/report.html`) without sanitization. Verified that `session_hash` is validated upstream in `session_archive.load_all_data` — but worth a defense-in-depth `_validate_session_hash()` regex check (8-char hex) in `handle_generate_html_report` before any file I/O.
- **Python 3.11 f-string backslashes**: Grep for `f['"][^'"]*\\` — no matches in pass_fill_assemble.py or generate_html_report.py. The known gotcha is mitigated per the lesson logged in Plan 05-02 Task 1.
- **Async correctness**: All tool handlers are `async def` and use `await` for I/O. No blocking calls inside async functions.
- **Type safety**: `_render_section_insight` checks `isinstance(insight, str)` before rendering. `_render_gap_blocks` checks `isinstance(block, dict)`. XSS escape via `_esc` applied to all dynamic text in HTML.

---

## Deployment Risk Assessment

**Phase 7 was correctly paused.** The 04-VERIFICATION.md `human_needed` status and the BILLING-001 blocker in 07-02-feedback.md have the side-effect of masking CR-01/CR-02. If Phase 7 had run successfully against a real clinic, the output HTML would have looked superficially complete (10 sections per the QC-Checklist) but missing 5 of those sections entirely (Strategy, Offer, Whitefields, Experts+регалии, Content+страхи) plus all Phase 5 narrative extras. QC-Checklist would have reported 13/18 missing items even though the LLM believed it had filled them.

**Recommendation before re-running Phase 7:**
1. Fix CR-01, CR-02, CR-03 (5-line text changes + dead-code deletion).
2. Add a unit test that calls `_build_prompt(state)` and asserts the rendered prompt contains the literal strings `"strategy_data"`, `"offer_data"`, `"whitefields_data"`, `"experts_data"`, `"content_data"`, `"section_insights"`, `"section_gap_blocks"`. This locks the prompt↔handler contract.
3. Add a defensive `kwargs.get("strategy_section")` fallback in `handle_generate_html_report` that logs a deprecation warning if the LLM passes the old name. Belt-and-suspenders.
4. Resolve BILLING-001 (DeepSeek top-up).
5. Then run Phase 7 Plan 07-02 against iphk.ru.

---

_Reviewed: 2026-06-24T09:00:00Z_
_Reviewer: Claude (gsd-code-reviewer, read-only mode)_
_Depth: deep_
_Constraint: Source files NOT modified. Only REVIEW.md produced._
