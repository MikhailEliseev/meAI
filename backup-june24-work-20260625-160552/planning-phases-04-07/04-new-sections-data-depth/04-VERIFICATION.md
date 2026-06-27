---
phase: 04-new-sections-data-depth
verified: 2026-06-24T02:30:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "End-to-end presale test with ORCHESTRATOR_MODE=1 (Plan 04-08 Task 2 — checkpoint:human-verify pending)"
    expected: "Trigger test presale on a known clinic URL (plastic surgery / cosmetology for full Phase 4 section coverage). HTML report generated in /opt/data/memories/proposals/ contains >=8 of 10 Phase 4 section markers. Container health remains 200. No regression in existing presale flow."
    why_human: "Requires ORCHESTRATOR_MODE=1 opt-in (architectural decision to enable orchestrator in production). Requires 15-minute LLM call with many tool invocations. Cannot verify prompt-following behavior of LLM programmatically — must observe actual tool_calls + HTML output. Plan 04-08 explicitly lists this as checkpoint:human-verify (blocking gate)."
  - test: "Visual inspection of generated HTML report for 10 reference sections"
    expected: "Open generated report in browser. Verify: Strategy has 5 named directions (Контент/Telegram/GEO/Репутация/Кросс-промо) with concrete steps; Offer has CTA + concrete steps; Whitefields is 4×4 table (not just content_gaps list); Revenue table has 3 rows (2021/2022/2023) + YoY % + blockquote summary; Media has clickable hyperlinks with publication dates; Competitor cards show year/revenue/surgeons/IG handle/specialization; Experts have structured regalia (КМН/ДМН/title/ стаж/education); Content Analysis shows per-doctor themes + top-5 patient fears with mention counts."
    why_human: "Visual quality of LLM-generated content cannot be assessed via grep. Depth of narrative (D-01 'concrete steps with цифрами from data') is subjective. Reference ИПХиК (2).html comparison requires human judgement."
  - test: "LLM tool-calling verification: LLM actually calls run_forum_pains + run_media_urls in Pass 1"
    expected: "Inspect Pass 1 transcript (session DB or SSE events). Confirm LLM invoked both new tools at least once. Confirm tool results contain patient_fears_hint and mentions_by_source fields per Plan 04-03 output contract."
    why_human: "Prompt instructions don't guarantee LLM behavior. The Pass 1 phase4_rules block instructs but does not force. Only runtime observation confirms LLM follows the new rules. Local-env limitation: cannot run AIAgent locally without hermes-agent package."
  - test: "LLM kwargs population: LLM passes strategy_data/offer_data/whitefields_data/experts_data/content_data to generate_html_report"
    expected: "Inspect Pass 3 transcript. Confirm generate_html_report tool call includes all 5 new kwargs with non-empty values. Confirm resulting HTML contains data-aim attributes for all 5 new sections (strategy, offer, whitefields-matrix, experts-regalia, content-fears)."
    why_human: "Plan 04-07 auto-fixed missing handler kwargs wiring (Rule 2 — critical functionality). But wiring correctness does not guarantee LLM populates the kwargs. Only runtime observation confirms the LLM understands the prompt instructions and generates the kwargs."
---

# Phase 4: New Sections & Data Depth — Verification Report

**Phase Goal:** Reports contain all 10 reference sections with deep data — Strategy, Offer, Whitefields added; revenue covers 3 years; media has concrete URLs; competitor cards are detailed
**Verified:** 2026-06-24T02:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | Strategy section with 5 specific directions based on collected data | VERIFIED | `_build_strategy_section` (line 676) renders 5 directions with name, basis, steps, expected_impact. Pass 3 prompt item 7 instructs LLM with 5 fixed names (Контент/Telegram/GEO/Репутация/Кросс-промо) + 4 basis sources (конкуренты/content_gaps/страхи/reputation). Behavioral spot-check: 5 directions rendered, length 3533 chars, all named directions present. |
| 2   | Offer section with concrete steps and CTA — matching reference section 10 | VERIFIED | `_build_offer_section` (line 776) renders steps with timeline + CTA accent block. Pass 3 prompt item 8 instructs LLM with same pattern as Strategy (concrete steps + CTA from collected data). Behavioral spot-check: CTA "Запишитесь" rendered in HTML. |
| 3   | Whitefields matrix: client vs 3-5 competitors by field (not just content_gaps list) | VERIFIED | `_build_whitefields_matrix` (line 846) renders HTML `<table>` with 4 categories (Услуги/Цены/Врачи/Digital) × 4 columns (Клиент/Конкурент 1/2/3). Client column has golden border. Pass 3 prompt item 9 explicitly defines matrix structure. Behavioral spot-check: 4 categories + 4 columns rendered, has `<table>` tag, D-06 honest note for <3 competitors implemented. |
| 4   | Revenue dynamics cover 3 years with year-over-year comparison | VERIFIED | `_format_revenue_dynamics` (find_company_financials.py:173) enforces strict 3-year gate (D-13) with YoY %, total_growth_pct, summary_text. `_build_revenue_dynamics_section` (line 199) renders 3-row table + blockquote with summary. Behavioral spot-check: 3-year input produces "+79.2% за 3 года (2.4 млрд → 3.4 млрд → 4.3 млрд)" matching reference. <3 years input produces honest "доступно N год(а) — нужно минимум 3" block, NO table. |
| 5   | Media section lists concrete publication URLs with dates | VERIFIED | `run_media_urls` tool (381 lines) queries 5 specific СМИ (Forbes/RBC/Vademecum/Kommersant/ТАСС) via firecrawl+perplexity. `_build_media_urls_section` (line 380) renders simple hyperlink list per D-17. Behavioral spot-check: URLs with dates parsed correctly, hyperlinks rendered with `href` attribute. D-18 honest block for 0 mentions implemented. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `AIM/hermes/app/tools/find_company_financials.py` | `_format_revenue_dynamics` + `_format_clinic_metrics` helpers | VERIFIED | 360 lines. Helpers at lines 173 (`_format_revenue_dynamics`) and 271 (`_format_clinic_metrics`). Wired into handler output at lines 99-100. Behavioral tests pass: 3-year dynamics, <3-year strict gate, clinic metrics structure. |
| `AIM/hermes/app/tools/find_doctor_handles.py` | `_extract_structured_regalia` + `_merge_doctor_data` + `_names_match` | VERIFIED | 1542 lines. Helpers at lines 337, 479, 535. Module-level exposure confirmed. Behavioral tests: spelled-out "кандидат медицинских наук" → КМН; "д.м.н" → ДМН; initials-aware name matching works (Иванов И.И. ↔ Иванов Иван Иванович = True). |
| `AIM/hermes/app/tools/run_forum_pains.py` | New tool — patient fears from 4 forums via Perplexity | VERIFIED | 381 lines. FORUM_SOURCES (4 entries: ПроДокторов/Otzovik/IRecommend/Woman.ru). handle_run_forum_pains at line 237. _extract_fears regex parses "Больно — 47 упоминаний" → `{"fear": "Больно", "mention_count": 47}`. |
| `AIM/hermes/app/tools/run_media_urls.py` | New tool — 5-СМИ targeted URL search | VERIFIED | 429 lines. TARGET_MEDIA (5 outlets: Forbes/RBC/Vademecum/Kommersant/ТАСС). handle_run_media_urls at line 259. _parse_perplexity_results at line 163 parses URLs+dates. Container test: 2 URLs with dates parsed correctly. |
| `AIM/hermes/app/pipeline/engine.py` | `_TOOL_HANDLERS` has 26 entries (24 + 2 new) | VERIFIED | Lines 41-71. Container verified: `len(_TOOL_HANDLERS) == 26`. New entries at lines 69-70 (run_forum_pains, run_media_urls). |
| `AIM/hermes/app/orchestrator/pass_collect.py` | Phase 4 collection rules block | VERIFIED | phase4_rules block at lines 221-243. References run_media_urls, run_forum_pains, find_company_financials, run_review_platforms, structured_regalia. Container prompt length 1908 chars. |
| `AIM/hermes/app/orchestrator/pass_gap_analyze.py` | 18-item references in template + fallbacks | VERIFIED | Lines 1, 49-51, 84, 90, 96, 106, 194, 295, 304. Template "ПОЛНЫМ 18-item QC checklist" + "Для КАЖДОГО из 18 пунктов" + JSON `"total": 18`. Container confirmed. |
| `AIM/hermes/app/orchestrator/qc_checklist.py` | VERSION 1.2.0, 18 items, PASS_MIN_ITEMS=15 | VERIFIED | VERSION = "1.2.0" (line 39). QC_CHECKLIST has 18 items (ids 1-18). PASS_MIN_ITEMS = 15 (line 45). Items 16-18 are clinic_metrics/ratings/expert_regalia. All items 16-18 universally applicable (no niche condition). Container verified. |
| `AIM/hermes/app/orchestrator/coverage_reporter.py` | `total_items` default = 18 | VERIFIED | Line 66: `total_items: int = 18`. Line 86: `total = len(QC_CHECKLIST)  # 18 after Phase 4 expansion`. |
| `AIM/hermes/app/orchestrator/pass_fill_assemble.py` | 9 new section rules (items 7-15) | VERIFIED | Items 7-15 at lines 169-256. Covers STRATEGY (169), OFFER (188), WHITEFIELDS (195), EXPERTS (209), CONTENT+STРАХИ (219), REVENUE DYNAMICS (228), CLINIC METRICS (237), MEDIA URLS (245), RATINGS (252). Container prompt length 6426 chars. |
| `AIM/hermes/app/tools/generate_html_report.py` | 10 new HTML section builders | VERIFIED | 2893 lines. All 10 functions present: `_build_strategy_section` (676), `_build_offer_section` (776), `_build_whitefields_matrix` (846), `_build_experts_with_regalia` (972), `_build_content_analysis_with_fears` (1126), `_build_revenue_dynamics_section` (199), `_build_clinic_metrics_block` (304), `_build_media_urls_section` (380), `_build_ratings_section` (462), `_build_competitor_cards_section` (556). `_build_report_html` signature has 10 params (5 existing + 5 new). Container import: all 10 functions load cleanly. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| Pass 1 prompt | Phase 4 tools (run_forum_pains, run_media_urls, find_company_financials, run_review_platforms, find_doctor_handles) | `_build_pass_collect_prompt` returns `base_prompt + instagram_rule + phase4_rules + closing` (line 243) | WIRED | Container prompt contains all 5 tool references. |
| Pass 2 prompt | 18-item QC checklist | `_CHECKLIST_PROMPT_TEMPLATE` references "ПОЛНЫМ 18-item QC checklist", "Для КАЖДОГО из 18 пунктов", JSON `"total": 18` | WIRED | Container template confirmed via behavioral test. |
| Pass 3 prompt | 9 new section generation rules (items 7-15) | `_build_prompt` returns prompt with STRATEGY/OFFER/WHITEFIELDS/EXPERTS/CONTENT/REVENUE/CLINIC_METRICS/MEDIA/RATINGS markers | WIRED | Container prompt length 6426 chars, all 9 section markers present. |
| PipelineEngine `_TOOL_HANDLERS` | run_forum_pains + run_media_urls handlers | Dict entries at engine.py:69-70 | WIRED | Container verified: `_get_handler("run_forum_pains")` and `_get_handler("run_media_urls")` resolve. |
| `handle_generate_html_report` | `_build_report_html` with 5 new kwargs | Handler extracts strategy_data/offer_data/whitefields_data/experts_data/content_data from kwargs, passes to `_build_report_html` | WIRED | Container signature: `_build_report_html(data, title, coverage_metadata, niche, instagram_data, strategy_data, offer_data, whitefields_data, experts_data, content_data)`. Integration test: full report renders with all 5 new sections. |
| Tool layer `find_company_financials` | `revenue_dynamics` JSON field consumed by HTML builder | `_build_revenue_dynamics_section(financials)` reads `financials["revenue_dynamics"]` | WIRED | Behavioral test: revenue_dynamics block → 3-year HTML table + blockquote. |
| Tool layer `run_media_urls` | `media_urls` JSON field consumed by HTML builder | `_build_media_urls_section(data)` reads `data["media_urls"]` | WIRED | Behavioral test: media_urls block → hyperlink list with URLs+dates. |
| Tool layer `find_doctor_handles` | `structured_regalia` field consumed by HTML builder + Pass 3 merge helper | `_build_experts_with_regalia(experts_data)` reads `expert["structured_regalia"]` per item; `_merge_doctor_data` exposed at module level | WIRED | Behavioral test: site_doctors + instagram_data → merged list with `source='both'` when names match. |
| Container `_TOOL_HANDLERS` 26 entries | Production dispatch path | `docker exec aim-hermes python -c 'from app.pipeline.engine import _TOOL_HANDLERS; print(len(_TOOL_HANDLERS))'` | WIRED | 26 entries (24 + run_forum_pains + run_media_urls), matches local repo. |
| Container QC checklist v1.2.0/18 items | Production gap analysis | `docker exec aim-hermes python -c 'from app.orchestrator.qc_checklist import VERSION, QC_CHECKLIST; print(VERSION, len(QC_CHECKLIST))'` | WIRED | Output: `1.2.0 18`. Items 16-18 are clinic_metrics/ratings/expert_regalia. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `_build_revenue_dynamics_section` | `financials["revenue_dynamics"]` | `find_company_financials._format_revenue_dynamics` | YES — 3-year data → table+blockquote; <3 years → honest block | FLOWING |
| `_build_clinic_metrics_block` | `financials["clinic_metrics"]` | `find_company_financials._format_clinic_metrics` | YES — revenue/profit/status/okved_codes structure | FLOWING |
| `_build_media_urls_section` | `data["media_urls"]` | `run_media_urls.handle_run_media_urls` | YES — `all_mentions` flat list with URLs+dates; `pr_needed` flag | FLOWING |
| `_build_ratings_section` | `reviews["ratings_extracted"]` | Pass 3 LLM populates from `run_review_platforms` results | DEPENDS ON LLM — extraction is LLM-driven (no test) | PENDING_LLM |
| `_build_competitor_cards_section` | `competitors["competitor_cards"]` (fallback `ci_analysis["competitor_cards"]`) | Pass 3 LLM populates from `find_company_financials` + `run_instagram_content` + Perplexity | DEPENDS ON LLM — population is LLM-driven | PENDING_LLM |
| `_build_strategy_section` | `strategy_data` kwarg | Pass 3 LLM generates from `find_competitors + content_gaps + run_forum_pains + run_review_platforms` results | DEPENDS ON LLM — generation is LLM-driven | PENDING_LLM |
| `_build_offer_section` | `offer_data` kwarg | Pass 3 LLM generates from collected data | DEPENDS ON LLM | PENDING_LLM |
| `_build_whitefields_matrix` | `whitefields_data` kwarg | Pass 3 LLM constructs 4×4 matrix from multiple tool results | DEPENDS ON LLM | PENDING_LLM |
| `_build_experts_with_regalia` | `experts_data` kwarg | Pass 3 LLM merges via `_merge_doctor_data(site_doctors, instagram_data)` | DEPENDS ON LLM | PENDING_LLM |
| `_build_content_analysis_with_fears` | `content_data` kwarg | Pass 3 LLM combines `run_instagram_content` per-doctor + `run_forum_pains patient_fears_hint` | DEPENDS ON LLM | PENDING_LLM |

**Data-flow summary:** Tool-layer data flows are verified (revenue_dynamics, clinic_metrics, media_urls produce real data). LLM-populated kwargs (5 new sections) cannot be verified without an end-to-end presale run.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| 3-year revenue dynamics | `_format_revenue_dynamics({'2023': 4.3e9, '2022': 3.4e9, '2021': 2.4e9})` | `dynamics_available=True, total_growth_pct=79.2, summary="+79.2% за 3 года (2.4 млрд → 3.4 млрд → 4.3 млрд)"` | PASS |
| <3-year strict gate | `_format_revenue_dynamics({'2023': 100, '2022': 90})` | `dynamics_available=False, reason="доступно 2 год(а) — нужно минимум 3 для динамики"` | PASS |
| Clinic metrics structure | `_format_clinic_metrics({...})` | `revenue_latest, profit_latest, status, okved_codes=[{code, description}]` | PASS |
| Spelled-out КМН extraction | `_extract_structured_regalia("кандидат медицинских наук, доцент")` | `degree="КМН", academic_title="доцент"` | PASS |
| Initials-aware name match | `_names_match("Иванов И.И.", "Иванов Иван Иванович")` | `True` | PASS |
| Name mismatch detection | `_names_match("Иванов И.И.", "Петров Петр Петрович")` | `False` | PASS |
| Doctor data merge | `_merge_doctor_data(site, ig)` | `source='both'` for matching names | PASS |
| Forum fears parsing | `_extract_fears("Больно — 47 упоминаний...")` | 5 fears with mention_count sorted desc | PASS |
| Media URL parser | `_parse_perplexity_results(forbes_rbc_text)` | 2 mentions with url+date+title | PASS |
| 5 target СМИ | `len(TARGET_MEDIA)` | `5` (Forbes/RBC/Vademecum/Kommersant/ТАСС) | PASS |
| Strategy HTML rendering | `_build_strategy_section(5_directions)` | 3533 chars, 5 named directions, `<section>` tag | PASS |
| Whitefields 4×4 matrix | `_build_whitefields_matrix(...)` | `<table>` with 4 categories + 4 columns | PASS |
| Revenue strict gate HTML | `_build_revenue_dynamics_section(<3yr)` | Honest block, NO `<table>` | PASS |
| Media hyperlinks HTML | `_build_media_urls_section(...)` | `<a href>` tags with URLs | PASS |
| Full integration | `_build_report_html(...)` with all 5 new kwargs | 9005 chars HTML, all sections rendered | PASS |
| Container `_TOOL_HANDLERS` | `docker exec ... python -c 'len(_TOOL_HANDLERS)'` | `26` | PASS |
| Container QC VERSION | `docker exec ... python -c 'VERSION'` | `1.2.0` | PASS |
| Container items count | `docker exec ... python -c 'len(QC_CHECKLIST)'` | `18` | PASS |
| Container items 16-18 universal | `is_item_applicable(16/17/18, any_niche)` | `True` for all niches | PASS |
| Container health | `curl http://127.0.0.1:8000/health` | `HTTP 200` | PASS |
| Container import all 10 builders | `docker exec ... python -c 'from ... import _build_strategy_section, ...'` | `OK: all 10 Phase 4 HTML section builders importable` | PASS |
| Container orchestrator imports | `docker exec ... python -c 'from three_pass import run_three_pass; ...'` | `OK: orchestrator imports clean` | PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| `find_company_financials._format_revenue_dynamics` behavioral | Direct invocation via `docker exec aim-hermes python -c` | 3-year → 79.2% growth; <3-year → strict gate | PASS |
| `find_doctor_handles._extract_structured_regalia` behavioral | Direct invocation via `docker exec aim-hermes python -c` | КМН/ДМН/title/education extracted; initials matching works | PASS |
| `run_forum_pains._extract_fears` behavioral | Direct invocation via `docker exec aim-hermes python -c` | 5 fears parsed with mention_count | PASS |
| `run_media_urls._parse_perplexity_results` behavioral | Direct invocation via `docker exec aim-hermes python -c` | 2 URLs+dates parsed correctly | PASS |
| Container integration (orchestrator imports + tool registry + QC + HTML builders) | Direct invocation via `docker exec aim-hermes python -c` | All imports OK, _TOOL_HANDLERS=26, QC=1.2.0/18 items, health=200 | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| SEC-01 | 04-05 prompt + 04-07 HTML | Strategy section with 5 directions | SATISFIED | `_build_strategy_section` + Pass 3 prompt item 7 with 5 fixed names + 4 basis sources |
| SEC-02 | 04-05 prompt + 04-07 HTML | Offer section with CTA | SATISFIED | `_build_offer_section` + Pass 3 prompt item 8 with CTA pattern |
| SEC-03 | 04-05 prompt + 04-07 HTML | Whitefields matrix (not list) | SATISFIED | `_build_whitefields_matrix` 4×4 table + Pass 3 prompt item 9 with 4 categories |
| SEC-04 | 04-02 tool + 04-05 prompt + 04-07 HTML | Experts with structured регалии | SATISFIED | `_extract_structured_regalia` + `_merge_doctor_data` + Pass 3 prompt item 10 + `_build_experts_with_regalia` |
| SEC-05 | 04-03 tool + 04-05 prompt + 04-07 HTML | Content Analysis + top-5 patient fears | SATISFIED | `run_forum_pains` + Pass 3 prompt item 11 + `_build_content_analysis_with_fears` |
| DAT-01 | 04-01 tool + 04-06 HTML | 3-year revenue dynamics with YoY | SATISFIED | `_format_revenue_dynamics` (3-year strict gate, YoY %, total_growth %, summary_text) + `_build_revenue_dynamics_section` |
| DAT-02 | 04-03 tool + 04-06 HTML | Concrete media URLs with dates | SATISFIED | `run_media_urls` (5 СМИ targeted) + `_build_media_urls_section` (simple list with hyperlinks) |
| DAT-03 | 04-06 HTML | Detailed competitor cards | SATISFIED | `_build_competitor_cards_section` (all D-20 fields: name/year/revenue/surgeons/IG/specialization, cards[:10] DoS mitigation) |
| DAT-04 | 04-01 tool + 04-06 HTML | Clinic metrics with ОКВЭД | SATISFIED | `_format_clinic_metrics` (revenue/profit/employees/licenses/okved_codes) + `_build_clinic_metrics_block` + Pass 3 prompt item 13 (LLM OKVED translation) |
| DAT-05 | 04-06 HTML | Ratings on 2+ platforms | SATISFIED | `_build_ratings_section` (2-platform minimum: ПроДокторов + Яндекс.Карты) + Pass 3 prompt item 15 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `pass_fill_assemble.py` | 140 | Hardcoded `f"{len(...)}/15"` instead of dynamic `/18` or `/{report.total_items}` | WARNING | LLM-facing prompt shows wrong total (15 vs 18 actual). Doesn't affect runtime behavior — coverage report from coverage_reporter.py uses correct 18. LLM may be slightly confused about threshold. |
| `pass_gap_analyze.py` | 96 | LLM prompt: "Это HARD FAIL: coverage=FAIL даже при 14/15 остальных пунктов заполненных" | WARNING | Stale text references old 15-item count. LLM-facing inconsistency — actual HARD FAIL rule uses runtime 18-item check via `_apply_niche_conditional_coverage`. Functional behavior correct. |
| `pass_gap_analyze.py` | 4, 28 | Docstrings: "FULL 15-item checklist", "FAIL even if 14/15 other items are filled" | INFO | Docstring drift — actual is 18 items. Doesn't affect runtime. |
| `pass_collect.py` | 184 | Instagram HARD FAIL rule text: "14/15 остальных пунктов заполненных" | WARNING | LLM-facing stale text. Same issue as pass_gap_analyze.py:96. Functional behavior correct. |
| `qc_checklist.py` | 1, 3, 6, 57 | Docstrings/comments: "15-item presale coverage checklist", "PASS = >=12/15", "The 15-item checklist" | INFO | Documentation drift — actual checklist is 18 items, PASS_MIN_ITEMS=15. Runtime behavior correct. |
| `coverage_reporter.py` | 6 | Docstring: "PASS = >=12/15 (80%) filled items per QC-04" | INFO | Documentation drift — actual PASS_MIN_ITEMS=15 (80% of 18). |
| `find_doctor_handles.py:_extract_structured_regalia` | 366-377 | Function matches "кандидат медицинских наук" / "к.м.н" (dotted) but NOT "КМН" (no dots) | WARNING | Some real doctor bios use "КМН" without dots — those won't be detected. Function works for spelled-out and dotted-abbreviated forms per design. 20 unit tests pass per SUMMARY. Minor data-quality limitation. |
| `generate_html_report.py:handler` | n/a | Rule 2 auto-fix applied — handler now extracts all 5 new kwargs | INFO | Auto-fixed during Plan 04-07 (committed in 3 task commits). Not a debt marker. |

**Debt-marker gate:** No `TBD`, `FIXME`, or `XXX` markers found in any Phase 4 files. The `placeholder` matches in `pass_gap_analyze.py` are docstrings describing template substitution mechanics (not debt markers). No blockers from debt markers.

### Human Verification Required

The phase requires end-to-end validation that the LLM actually produces reports containing all 10 sections with deep data. Code infrastructure is in place and tested at the unit level, but production behavior depends on LLM following the new prompts. Plan 04-08 Task 2 explicitly listed this as `checkpoint:human-verify` (blocking gate) and was NOT auto-executed.

#### 1. End-to-End Presale Test (Plan 04-08 Task 2)

**Test:** Enable `ORCHESTRATOR_MODE=1` (one-off or permanent). Trigger test presale via curl POST to `/api/chat` on a known clinic URL (plastic surgery or cosmetology for full Phase 4 section coverage). Wait for 15-minute 3-pass orchestrator to complete.
**Expected:** HTML report generated in `/opt/data/memories/proposals/`. Report contains ≥8 of 10 Phase 4 section markers (`data-aim` attributes). Container health remains 200. No regression in existing presale flow (default PRESALE mode still works without orchestrator).
**Why human:** Requires ORCHESTRATOR_MODE=1 opt-in (architectural decision to enable orchestrator in production). Requires 15-minute LLM call with many tool invocations. Cannot verify prompt-following behavior of LLM programmatically — must observe actual tool_calls + HTML output. Plan 04-08 explicitly listed as `checkpoint:human-verify` (blocking gate).

#### 2. Visual Inspection of HTML Report

**Test:** Open generated HTML report in browser. Compare to reference `ИПХиК (2).html`.
**Expected:**
- Strategy has 5 named directions (Контент/Telegram/GEO/Репутация/Кросс-промо) with concrete steps (not generic advice)
- Offer has CTA + concrete steps
- Whitefields is 4×4 table (not just content_gaps list)
- Revenue table has 3 rows (2021/2022/2023) + YoY % + blockquote summary matching "+79% over 3 years"
- Media has clickable hyperlinks with publication dates (Forbes/RBC/Vademecum/Kommersant/ТАСС)
- Competitor cards show year/revenue/surgeons/IG handle/specialization
- Experts have structured regalia (КМН/ДМН/title/стаж/education)
- Content Analysis shows per-doctor themes + top-5 patient fears with mention counts
**Why human:** Visual quality of LLM-generated content cannot be assessed via grep. Depth of narrative (D-01 "concrete steps with цифрами from data") is subjective. Reference comparison requires human judgement.

#### 3. LLM Tool-Calling Verification

**Test:** Inspect Pass 1 transcript (session DB or SSE events) from the test presale.
**Expected:** LLM invoked both new tools (`run_forum_pains`, `run_media_urls`) at least once. Tool results contain `patient_fears_hint` and `mentions_by_source` fields per Plan 04-03 output contract.
**Why human:** Prompt instructions don't guarantee LLM behavior. The Pass 1 phase4_rules block instructs but does not force. Only runtime observation confirms LLM follows the new rules. Local-env limitation: cannot run AIAgent locally without `hermes-agent` package.

#### 4. LLM Kwargs Population

**Test:** Inspect Pass 3 transcript from the test presale.
**Expected:** `generate_html_report` tool call includes all 5 new kwargs with non-empty values: `strategy_data`, `offer_data`, `whitefields_data`, `experts_data`, `content_data`. Resulting HTML contains `data-aim` attributes for all 5 new sections.
**Why human:** Plan 04-07 auto-fixed missing handler kwargs wiring (Rule 2 — critical functionality). But wiring correctness does not guarantee LLM populates the kwargs. Only runtime observation confirms the LLM understands the prompt instructions and generates the kwargs.

### Gaps Summary

No code-level gaps identified. All 10 required artifacts exist, are substantive (no stubs), and are wired (handler extracts kwargs, _build_report_html receives them, _TOOL_HANDLERS has 26 entries, prompts reference Phase 4 tools/sections).

Minor inconsistencies (warnings, not blockers):
1. **Stale `/15` references** in 3 LLM-facing prompt strings (`pass_fill_assemble.py:140`, `pass_gap_analyze.py:96`, `pass_collect.py:184`) and several docstrings. The runtime checks use the correct 18-item count via `len(QC_CHECKLIST)` and `report.total_items`. The LLM sees slightly inconsistent numbers in prompt text but functional behavior is correct.

2. **`_extract_structured_regalia` abbreviation handling** — function matches "к.м.н" (dotted) and spelled-out "кандидат медицинских наук" but NOT "КМН" without dots. Some real doctor bios may use the no-dots form. 20 unit tests pass per SUMMARY — function works for designed patterns.

3. **No end-to-end validation** — Phase 4 code is deployed but has NOT been used in a real presale. The LLM has not actually populated the new kwargs in a production report. The HTML reports in `/opt/data/memories/proposals/` are all pre-Phase-4.

**Status decision:** `human_needed` per Step 9 decision tree — automated checks pass (5/5 truths verified at code level), but the phase goal "Reports contain all 10 reference sections with deep data" requires actually generating a report. Plan 04-08 Task 2 explicitly listed this as `checkpoint:human-verify` (blocking gate). User must opt-in (ORCHESTRATOR_MODE=1) and trigger a test presale.

---

_Verified: 2026-06-24T02:30:00Z_
_Verifier: Claude (gsd-verifier)_
