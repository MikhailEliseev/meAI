# Phase 1 Research & Diagnosis — Hermes v5

**Created:** 2026-06-23
**Phase:** 1 (Research & Diagnosis)
**Plans consolidated:** 01-01, 01-02, 01-04, 01-03
**Requirements addressed:** RES-01, RES-02, RES-03, RES-04, RES-05
**Status:** Phase 1 COMPLETE — ready for Phase 2 (3-Pass Orchestrator)

---

## Executive Summary

**Why does v4 LLM skip tools?** The LLM is not actually skipping — **the pipeline physically cannot call most of the catalogue.** Of 49 tools registered for the LLM, only 22 are wired into `PipelineEngine._TOOL_HANDLERS`. The other **27 tools are unreachable**, including every Instagram, Ads, Lighthouse, and orchestration tool. When the LLM decides to call one of these (e.g., `run_instagram_content`), the pipeline rejects with `"No handler mapping for tool: ..."`. Compounding this, `SOUL.md` tells the LLM "you are a free artist, choose tools yourself" while `SKILL.md` tells it "you are an interpreter, Python controls everything" — **the two documents contradict each other**, so the LLM is set up to fail by contradicting instructions. A secondary amplifier is DeepSeek V4 Pro's ~120 s stream ceiling, and a NEW code regression (`NameError: _unwrap_tool_output`) turns 40% of recent reports into empty templates.

**Baselines measured:**
- Tool coverage: **15/49 modules (30.6%)** — average unique tools called per session across 5 sessions (Plan 01)
- Section coverage: **3.0/10 sections (30%)** — average sections present per HTML report across 5 reports (Plan 01)
- 21 of 39 named tools (54%) never called in any of 5 sessions (Plan 01)
- 2 of 5 reports (40%) completely empty — `NameError: _unwrap_tool_output` (Plan 02)
- 28 skip/truncate points catalogued across 5 sessions (Plan 02)
- Instagram tool works manually but is pipeline-blocked (Plan 04)

**Top 3 findings:**
1. **Pipeline handler gap is the primary cause** — 22 `_TOOL_HANDLERS` vs 49 LLM-registered modules = 27 unreachable tools. This is a wiring problem, not an LLM problem.
2. **Document paradox confuses the LLM** — SOUL.md says "free artist", SKILL.md says "Python controls". Production runs mix both modes and fail at the seam.
3. **NEW code regression (`_unwrap_tool_output` NameError)** introduced Jun 20-21 — breaks HTML BUILD + PRESENTATION in 40% of recent sessions. Independent of root cause but masks it.

**Primary recommendation for Phase 2:** Build the **LLM-orchestrator with 3-pass cycle** (Collect → Gap-analyze → Fill+Assemble) using a QC checklist as the gap-analysis reference. The orchestrator should bypass `PipelineEngine._TOOL_HANDLERS` for tool dispatch (or extend the dict to cover all 49 modules). Fix the `_unwrap_tool_output` bug as the very first Phase 2 task — it is blocking 40% of reports today.

**One-line root cause:** Hypothesis D (combination) — primary C (pipeline blocks 27/49 tools) + primary A (SOUL/SKILL document paradox) + secondary B (~120 s stream ceiling) + NEW code bug (`_unwrap_tool_output` NameError).

---

## 1. Baseline Coverage (from Plan 01)

*Source: `evidence/coverage-baseline.md`*

### 1.1 Tool Coverage Baseline — RES-02

**Measurement:** 5 most recent sessions in `/opt/data/sessions-archive/`, tool names extracted from per-phase result files.

| # | Session | Clinic | Unique Tools | Total Calls |
|---|---------|--------|:---:|:---:|
| 1 | `tg:322367335` | arclinic.ru | 15 | 15 |
| 2 | `1609c5d1` | iphk.ru | 16 | 16 |
| 3 | `7282c8f7` | iphk.ru | 16 | 16 |
| 4 | `full-test-1782061034` | iphk.ru | 16 | 16 |
| 5 | `test-iphk-002` | iphk.ru | 14 | 15 |

**Baseline: 15.4 unique tools per session (rounded to 15/49 = 30.6%)**

Union of all called tools across 5 sessions: **18 unique tools**.

**Never-called tools (21 of 39 named tools, 54%):**

| Category | Tools |
|----------|-------|
| Perplexity (advanced) | `perplexity_deep_analyze` |
| Firecrawl | `firecrawl_extract`, `firecrawl_batch_scrape`, `firecrawl_agent` |
| Crawlee/Scrapy | `crawlee_scrape`, `crawlee_search`, `scrapy_crawl` |
| Ads | `run_ads_intelligence`, `run_ads_report` |
| Lighthouse | `run_lighthouse` |
| Prescan | `run_prescan`, `quick_overview` |
| Geo | `geo_optimizer_tools` |
| Presentation | `present_competitors`, `finalize_research`, `run_validation_check` |
| Publishing | `post_report` |
| Orchestration | `orchestrate`, `run_aim_scout`, `run_full_scout`, `run_background_pipeline` |

**Two distinct iphk.ru tool patterns observed:**
- **Pattern A (3 sessions, Jun 21):** `find_doctor_handles` + `run_instagram_content` + `run_tech_seo_audit`
- **Pattern B (1 session, Jun 20):** `run_doctor_dossiers` + `run_seo_audit`

Pattern switch between Jun 20 and Jun 21 suggests code or config change in that window.

### 1.2 Section Coverage Baseline — RES-03

**Measurement:** 5 HTML reports, headings extracted via Python regex, matched against 10 reference section patterns from `ИПХиК (2).html` (78 KB, 965 lines, 10 sections).

| # | Report | Clinic | Size | Sections Present | Sections Missing |
|---|--------|--------|------|:---:|---|
| 1 | `report-xb5ehmvx.html` | Era Smile | 8.5 KB | **0/10** | ALL |
| 2 | `report-dweveh9t.html` | Era Smile | 9.9 KB | **0/10** | ALL |
| 3 | `1609c5d1/report.html` | iphk.ru | 10.1 KB | 4/10 | About, Market, Content Analysis, Competitors, Whitefields, Offer |
| 4 | `test-iphk-002/report.html` | iphk.ru | 3.9 KB | 3/10 | About, Market, Content Analysis, Competitors, Whitefields, Presence, Offer |
| 5 | `nachalo-clinica/report.html` | Начало | 41.7 KB | 8/10 | About, Market |

**Baseline: 3.0/10 sections per report (30%)**

### 1.3 Consistently Missing Sections

| Section | Missing Rate | Impact |
|---------|:---:|--------|
| **1. About** (ОКВЭД, licenses, 3-year revenue) | 100% (5/5) | Foundational context absent in every report |
| **2. Market** (competitor table) | 100% (5/5) | Competitive landscape never rendered |
| **4. Content Analysis** (style, themes, gaps) | 80% (4/5) | Only nachalo-clinica has it |
| **6. Competitors** (detail cards) | 80% (4/5) | Only nachalo-clinica has it |
| **7. Whitefields** (comparison matrix) | 80% (4/5) | Only nachalo-clinica has it |
| **10. Offer** ("Что AIM может") | 80% (4/5) | Only nachalo-clinica has it |

### 1.4 Quality Degradation Trend

| Report Date | Size | Sections | Notes |
|-------------|------|:---:|-------|
| Jun 16 (nachalo) | 41.7 KB | 8/10 | Outlier — best report in sample |
| Jun 20 (test-iphk-002) | 3.9 KB | 3/10 | Smallest non-empty report |
| Jun 21 (1609c5d1) | 10.1 KB | 4/10 | Typical recent quality |
| Jun 22 (Era Smile ×2) | 8-10 KB | 0/10 | **Empty templates** — `_unwrap_tool_output` regression |

**The most recent reports (Jun 22) are the worst.** Regression introduced between Jun 16 and Jun 22.

---

## 2. Session Log Analysis (from Plan 02)

*Source: `evidence/session-log-analysis.md`*

### 2.1 Sessions Analyzed — RES-04

5 sessions, 4 iphk.ru + 1 arclinic.ru, spanning Jun 20-21:

| Session | Clinic | Phases Completed | Duration | Notes |
|---------|--------|:---:|:---:|-------|
| `tg:322367335` | arclinic.ru | 13/13 | 19 min | Telegram-triggered, flat JSON structure |
| `1609c5d1` | iphk.ru | 11/11 | 6 min | Subdir structure |
| `full-test-1782061034` | iphk.ru | 11/11 | 7 min | Subdir structure |
| `4975ef15-de5` | (crashed) | 1/13 | <1 min | **ABORTED** — no metadata.json, no events.jsonl |
| `test-iphk-002` | iphk.ru | 13/13 | 9 min | Oldest in sample, no `_unwrap_tool_output` bug |

### 2.2 Skip/Truncate Decision Points

**28 specific skip/truncate points catalogued** with quoted evidence:

| Category | Count | Examples |
|----------|:---:|---------|
| ERROR | 9 | `_unwrap_tool_output` NameError (×2 sessions), `"No handler mapping"` (×5+), `"inn required"` (×2) |
| NO_DATA | 7 | `competitors: []` (iphk.ru in megapolise), empty `run_smi_mentions`, empty forum pains |
| SKIPPED_TOOL | 13 | 21 tools never called (see Plan 01 list) |
| SKIPPED_PHASE | 12 | Session 4 crash skipped 12 of 13 phases |
| LLM_DECISION | 5 | LLM honestly wrote "10/10 FAIL", "врачи не найдены", etc. |

### 2.3 Top 7 Most-Skipped Tools

| Tool | Skip Pattern | Root Cause |
|------|--------------|------------|
| `run_instagram_content` | Never succeeds — LLM doesn't call (4/5) OR pipeline refuses (1/5) | Not in `_TOOL_HANDLERS` + v1 broken (Apify key bug) |
| `find_doctor_handles` | LLM calls in 1/5, pipeline refuses | Not in `_TOOL_HANDLERS` |
| `run_tech_seo_audit` | LLM calls in 3/5, pipeline refuses all 3 | Not in `_TOOL_HANDLERS` |
| `run_doctor_dossiers` | Called but with wrong arg (`doctor_name: "Arclinic"` instead of ФИО) | Prompt issue — LLM passes clinic name |
| `find_company_financials` | Fails with `"inn required"` in 2/5 | Non-deterministic LLM omits INN |
| `find_competitors` | Returns `competitors: []` for iphk.ru in megapolise | Tool limitation — geographic filter |
| `generate_html_report` | Crashes with NameError in 2/5 | Code bug — `_unwrap_tool_output` undefined |

### 2.4 Phases That Always Truncate

| Phase | Issue |
|-------|-------|
| HTML BUILD (Phase 10) | Crashes in 40% of sessions — `_unwrap_tool_output` NameError |
| PRESENTATION (Phase 12) | Crashes after HTML BUILD; `url: null` even when it succeeds |
| QC CRITIQUE (Phase 11) | Operates on empty input when HTML BUILD fails — produces "10/10 FAIL" honestly |

### 2.5 Stream Break / Truncation Frequency

- Per-phase timeouts (config.yaml): `perplexity=120s`, `html_build=120s`, `qc_critique=90s`, `presentation=60s`
- DeepSeek V4 Pro reported stream-break ceiling: ~120s
- **Alignment:** 4 of 13 phases sit at or above the stream ceiling
- Result: Long perplexity queries and complex HTML generation may time out mid-stream
- Observability gap: `events.jsonl` files absent in all 5 sampled sessions — cannot directly count stream breaks

### 2.6 LLM-признания (LLM Honest Acknowledgments)

The LLM is honest about failures in its interpretation text:

- **COMPETITORS (Session 1):** *"Конкурентный анализ не может быть выполнен в полном объёме: инструмент CI-анализа завершился ошибкой"*
- **KEY PERSONS (Session 1):** *"идентифицировать конкретных врачей не удалось: все найденные 10 профилей — это страницы клиники на отзовиках"*
- **CONTENT ANALYSIS (Session 1):** *"содержит только техническую ошибку – инструмент не смог обратиться к сайту arclinic.ru"*
- **CONTENT PLAN (Session 1):** *"инструмент не выявил расхождений, поскольку в качестве конкурента ошибочно использовался сам сайт клиники"*
- **QC CRITIQUE (Session 1):** *"10/10 FAIL. Причина – отсутствие готового отчёта"*

These are not "LLM decides to skip" — they are LLM reacting to upstream failures. The LLM is correctly reporting what broke.

---

## 3. Instagram Tool Test (from Plan 04)

*Source: `evidence/instagram-tool-test.md`*

### 3.1 Tool State — RES-05

| Property | Container (v1) | Local repo (v2) |
|----------|----------------|-----------------|
| Lines | 371 | 718 |
| md5 | `a7a7a1dde5dc4cfc8bf8b6c1543c122f` | `0bf035e1d7faaf621bc921b9db531b63` |
| Approach | Apify Instagram Profile Scraper | Perplexity `sonar-pro` with web search |
| External dep | Apify API (13 keys in file) | Perplexity API (`PERPLEXITY_API_KEY` in env) |
| Fallback | None — hard fails | DeepSeek LLM |
| Batch support | No (single handle only) | Yes (up to 5 handles) |
| Status | **BROKEN** — Apify key loader has field name bug | **WORKING** — verified via direct Perplexity API call |
| Deployed? | Yes (in container) | **NO** — never deployed |

### 3.2 v1 Bug Detail

```python
# /opt/hermes/app/tools/run_instagram_content.py lines 34-42 (v1 in container)
def _load_apify_keys() -> list[str]:
    try:
        with open(APIFY_KEYS_PATH) as f:
            data = json.load(f)
        return [k["token"] for k in data.get("keys", []) if k.get("status") == "active"]
    except Exception:
        logger.warning("Cannot load Apify keys from %s", APIFY_KEYS_PATH)
        return []
```

Code reads `k["token"]` but `/opt/data/apify_keys.json` stores keys under `k["key"]`. All 13 keys have `status="active"` and `exhausted_at=null`, but `k["token"]` raises `KeyError`. The `except Exception` swallows it → returns `[]` → tool returns `"No active Apify keys available"`.

### 3.3 v2 Verification Results

Direct Perplexity API call from container (bypassing v1):

| Test Target | Time | Status | Data Returned |
|-------------|------|--------|---------------|
| @nasa (sanity) | 33.7s | 200 | Real data: 104M followers, 5 themes, Reels dominant, 0.7-1% ER |
| @lancette.clinic (iphk.ru) | 17.1s | 200 | Honest "no data" (handle not in Perplexity index) |
| @doctor.titov | 9.8s | 200 | Honest "no data" |
| @dr.khritinin | 9.6s | 200 | Honest "no data" |

**Key behavior:** v2 does NOT fabricate data when handle is not found. Returns structured JSON with 0/null values + explicit `content_gaps` explaining what's missing. This aligns with Phase 2 QC requirement: "no fabricated data".

### 3.4 Handler Need: CONFIRMED

`run_instagram_content` is:
- Registered in `__init__.py:74` for LLM invocation
- **NOT in `_TOOL_HANDLERS`** (22 entries, `run_instagram_content` absent — verified by direct grep)
- Pipeline cannot invoke it. Phase 5 (KEY PERSONS) in `phases.py` is hard-coded to `[run_hh_analysis, run_doctor_dossiers]` only.

**Verdict for IG-01 (Phase 3):** YES, handler needed + deploy v2. Both gaps must be closed together — adding the handler alone still leaves v1 broken; deploying v2 alone still leaves the pipeline unable to invoke it.

### 3.5 Field Coverage: 9.5/10 for Reference Sections 03+04

| Section 03 (Experts) | v2 returns? | Section 04 (Content Analysis) | v2 returns? |
|----------------------|:---:|----------------------|:---:|
| ФИО | YES (`profile.full_name`) | Стиль контента | YES (`dominant_format` + themes) |
| Регалии | PARTIAL (in `profile.biography`) | Темы (%) | YES (`content_themes[].pct`) |
| Подписчики | YES (`profile.followers`) | Пробелы | YES (`content_gaps[]` w/ severity) |
| Avg лайки | YES (may default to 0) | Потенциал | YES (`recommendations[]`) |
| Avg просмотры | YES (may default to 0) | | |
| Стиль контента | YES (`dominant_format` + themes) | | |

**Coverage: 9.5/10 (5.5/6 + 4/4)**. Only structured `Регалии` field is partial — derivable from bio text.

---

## 4. Root Cause Analysis (from Plan 01-03 Task 1)

*Source: `evidence/root-cause-analysis.md`*

### 4.1 Hypothesis A — Prompt Problem

**Verdict: PARTIAL**

- SOUL.md has explicit permissive language: "Свободный художник: сам выбирает инструменты" (line 3), "ЕСЛИ НУЖНО" (line 210), "Свободный тон" (line 553)
- SKILL.md (aim-scout) is strict: "Python-controlled execution. LLM = data interpreter, NOT orchestrator"
- **The paradox itself is the A problem** — two documents contradict on "who decides tools?"
- Plan 02 LLM-признания are not "decides to skip" — they are reactions to upstream failures

### 4.2 Hypothesis B — Model Limitation

**Verdict: PARTIAL (secondary)**

- DeepSeek V4 Pro configured (`LLM_MODEL=deepseek-v4-pro`, `LLM_BASE_URL=https://api.deepseek.com`)
- Per-phase timeouts align with ~120 s stream ceiling: `perplexity=120s`, `html_build=120s`
- Only 5 of 28 skip points are LLM_DECISION (model acknowledging limits)
- Most skips are ERROR (code bug) or SKIPPED_TOOL (pipeline block) — not model issues

### 4.3 Hypothesis C — Pipeline Constraint

**Verdict: CONFIRMED — PRIMARY CAUSE**

- **22 entries in `_TOOL_HANDLERS`** (authoritative Python introspection)
- **49 `_import_tool` calls in `__init__.py`** (authoritative grep count)
- **Gap: 27 modules registered for LLM but pipeline-unreachable**
- 17 of those 27 are presale-critical (Instagram, find_doctor_handles, run_tech_seo_audit, run_lighthouse, run_prescan, quick_overview, run_ads_*, geo_optimizer_tools, present_competitors, finalize_research, run_validation_check, post_report, orchestrate, run_aim_scout, run_full_scout, run_background_pipeline)
- Direct log evidence: `"No handler mapping for tool: run_instagram_content"` in production sessions
- Phase rigidity: `phases.py` hard-codes `tools=[...]` per phase
- Phase desync: HIRING SIGNALS phase runs in production but absent from `phases.py` source

### 4.4 Hypothesis D — Combination

**Verdict: CONFIRMED**

Compound combination:
- **Primary: A + C** — document paradox + pipeline blocks 27 tools
- **Amplifier: B** — ~120 s stream ceiling
- **NEW: Code bug** — `_unwrap_tool_output` NameError (introduced Jun 20-21)

A and C multiply each other: LLM keeps trying to call blocked tools (because SOUL.md says "free artist"), pipeline keeps rejecting (because of C). The paradox hides the pipeline's rigidity.

### 4.5 Confirmed Root Cause (Single Statement)

> **Primary:** `PipelineEngine._TOOL_HANDLERS` contains only 22 entries, while `register_all_tools()` exposes 49 tool modules to the LLM. The 27-module gap includes every Instagram, Ads, Lighthouse, Firecrawl, and orchestration tool. The LLM cannot reach them.
>
> **Secondary:** `SOUL.md` (v4, "free artist") and `SKILL.md` (strict Python control) contradict each other, leaving the LLM in an ambiguous state that compounds with C.
>
> **Amplifier:** DeepSeek V4 Pro's ~120 s stream ceiling truncates long phases.
>
> **NEW regression:** `_unwrap_tool_output` NameError breaks 40% of recent reports at HTML BUILD phase.

---

## 5. Recommendations for Phase 2

### 5.1 Mapping to ROADMAP Phase 2 Requirements

| ROADMAP Req | Description | Phase 2 Action Based on Root Cause |
|-------------|-------------|------------------------------------|
| **ORC-01** | 3-pass cycle (Collect → Gap-analyze → Fill+Assemble) | Build the orchestrator that runs the cycle automatically. Each pass has a clear exit criterion. |
| **ORC-02** | LLM selects tools by situation (not rigid pipeline) | **Bypass `_TOOL_HANDLERS` for orchestrator mode** — let LLM call any of the 49 registered tools directly. Keep PipelineEngine as fallback mode (ORC-05). |
| **ORC-03** | Gap-analysis compares collected data vs QC checklist | Implement checklist-based gap detection. See QC items below (5.4). |
| **ORC-04** | Honest "данные недоступны" if gaps remain after pass 3 | Document in SOUL.md/SKILL.md — LLM must mark gaps explicitly, never fabricate. |
| **ORC-05** | PipelineEngine remains as alternative mode | Don't delete `phases.py` or `_TOOL_HANDLERS`. They serve as deterministic fallback. |
| **QC-01** | 10-20 item QC checklist | See proposed checklist below (5.4). |
| **QC-02** | Auto-check checklist before HTML generation | Gate HTML BUILD on QC pass — if items missing, return to gap-fill pass. |
| **QC-03** | Coverage % report at end of each run | Print QC checklist coverage to logs + interpret text. |
| **QC-04** | ≥80% coverage target | Measure: (filled items / total items) ≥ 0.8 |

### 5.2 Architectural Choice: Orchestrator-First vs Pipeline-First

Given the root cause (C primary + A paradox), Phase 2 has two options:

**Option 1: Extend `_TOOL_HANDLERS` to cover all 49 modules (pipeline-first)**
- Pro: Minimal change to architecture
- Pro: PipelineEngine remains deterministic
- Con: Doesn't fix the A paradox (SOUL.md still says "free artist")
- Con: Each new tool still needs manual handler entry — maintenance burden
- Con: Doesn't enable LLM to choose tools adaptively (ORC-02 unsatisfied)

**Option 2: LLM-orchestrator bypasses `_TOOL_HANDLERS` (orchestrator-first)** ← RECOMMENDED
- Pro: Directly addresses ORC-02 (LLM selects by situation)
- Pro: Fixes the A paradox (orchestrator mode matches SOUL.md's "free artist")
- Pro: 49 tools become reachable without per-tool handler entry
- Con: Larger change — new orchestrator module, gap-analysis logic, 3-pass loop
- Con: Less deterministic than pipeline mode (but PipelineEngine stays as fallback per ORC-05)

**Recommendation: Option 2** — matches ROADMAP Phase 2 success criteria and fixes root cause.

### 5.3 Specific Phase 2 Fixes (Priority Order)

**P0 — Fix `_unwrap_tool_output` NameError (FIRST, blocking)**
- Bug: function undefined, breaks HTML BUILD + PRESENTATION in 40% of sessions
- Files: `app/tools/generate_html_report.py`, `app/tools/publish_scout_report.py`
- Fix: add missing import or define function
- Verification: re-run one of the failed sessions, confirm HTML generates

**P1 — Build 3-pass orchestrator core**
- Pass 1 (Collect): LLM calls tools it thinks are relevant for this clinic type
- Pass 2 (Gap-analyze): LLM compares collected data vs QC checklist, produces gap report
- Pass 3 (Fill + Assemble): LLM fills gaps (calls missing tools) + generates HTML
- Files: new `app/orchestrator/` module (do not modify `app/pipeline/`)

**P2 — Implement QC checklist (QC-01..04)**
- Define 15-item checklist (see 5.4)
- Implement gap-analysis pass that compares collected data vs checklist
- Implement coverage % reporting
- Gate HTML BUILD on checklist pass OR explicit "data unavailable" markers

**P3 — Wire Instagram + Ads + Lighthouse tools (close C gap)**
- Add 17 presale-critical missing tools to `_TOOL_HANDLERS` (even though orchestrator mode bypasses the dict, this ensures fallback PipelineEngine mode also benefits)
- Deploy Instagram v2 to container (`docker cp` local v2 → container)
- See Phase 3 (IG-01..04) for Instagram-specific work

**P4 — Chunk long phases (address B)**
- `perplexity` (120 s ceiling): split into 2 sub-calls if query is complex
- `html_build` (120 s ceiling): pre-compute section data, then assemble HTML in <60 s
- Or: raise per-phase timeout to 180 s where the LLM has shown it can stay under stream ceiling

**P5 — Align SOUL.md and SKILL.md (address A paradox)**
- Decide canonical architecture: orchestrator-first (recommended) or pipeline-first
- Update SOUL.md to describe orchestrator mode + QC checklist
- Update SKILL.md (aim-scout) to match — remove "Python-controlled" if going orchestrator-first
- Remove phantom phases (HIRING SIGNALS — either add to `phases.py` or remove from production behavior)
- Detail in Phase 6 (SYN-01..05)

### 5.4 Proposed QC Checklist (15 items — within QC-01's 10-20 range)

Based on missing sections (Plan 01) + never-called critical tools (Plan 01) + Instagram verification (Plan 04):

| # | Checklist Item | Source | Pass Criterion |
|---|----------------|--------|----------------|
| 1 | **About data collected** (ОКВЭД, licenses, revenue) | Plan 01 (About missing 100%) | At least 2 of 3 fields populated |
| 2 | **Market section data** (competitor table with ≥3 competitors) | Plan 01 (Market missing 100%) | ≥3 competitors with revenue + trend |
| 3 | **Competitors returned by find_competitors** | Plan 02 (`competitors: []` for iphk.ru) | ≥3 competitors, retry with broader geo if initial 0 |
| 4 | **Experts identified** (top-5 doctor ФИО) | Plan 02 ("врачи не найдены") | ≥3 doctors with ФИО (not clinic name) |
| 5 | **Instagram analysis for cosmetology/plastic** | Plan 04 (Instagram never runs) | If clinic niche matches, `run_instagram_content` called (even if returns honest "no data") |
| 6 | **Content themes with %** | Plan 01 (Content Analysis 80% missing) | ≥3 themes with percentages per top doctor |
| 7 | **Content gaps with severity** | Plan 04 v2 schema | ≥2 gaps with severity levels |
| 8 | **SMI mentions with URLs** | Plan 01 (Media shallow) | ≥3 mentions with concrete URLs (not just counters) |
| 9 | **Forum pains (patient fears)** | Plan 01 (section 04 partial) | ≥5 patient fears from forums |
| 10 | **Revenue for current year** | Plan 01 (About missing) | Revenue number present |
| 11 | **Revenue dynamics 3 years** (NEW — DAT-01) | Plan 01 (only current year) | 3-year trend with year-over-year % |
| 12 | **Competitor cards detailed** (year founded, surgeons, Instagram) | Plan 01 (Competitors 80% missing) | ≥3 competitor cards with ≥4 fields each |
| 13 | **Whitefields comparison matrix** | Plan 01 (Whitefields 80% missing) | Matrix: client vs ≥3 competitors by ≥5 fields |
| 14 | **Strategy with 5 directions** | Plan 01 (Strategy weak) | 5 concrete directions: content, Telegram, GEO, reputation, cross-promo |
| 15 | **Offer section ("Что AIM может")** | Plan 01 (Offer 80% missing) | Concrete steps + CTA matching reference section 10 |

**Coverage target:** ≥12 of 15 items (80%) filled with real data → PASS
**Below 12:** LLM must mark missing items as "данные недоступны" — no fabrication (ORC-04)

### 5.5 Coverage Measurement

For each presale run, output:

```
QC Coverage: 13/15 (86.7%) — PASS
Filled: 1,2,3,4,5,6,7,8,10,11,12,13,14,15
Missing (marked unavailable): 9 (forum pains — no relevant forums found for this niche)
```

This becomes the measurable success metric for Phase 2's 3-pass cycle.

---

## 6. Methodology

### 6.1 Sessions Sampled

**Plan 01 (coverage baseline):** 5 most recent sessions in `/opt/data/sessions-archive/` as of 2026-06-22:
- `tg:322367335` (arclinic.ru, Jun 21)
- `1609c5d1`, `7282c8f7`, `full-test-1782061034` (iphk.ru, Jun 21)
- `test-iphk-002` (iphk.ru, Jun 20)

Skew note: 4 of 5 are iphk.ru (same clinic, re-runs). This reflects actual server activity.

**Plan 02 (session log analysis):** Same 5 sessions + `4975ef15-de5` (crashed session, Jun 21) = 6 total.

**Plan 04 (Instagram test):** iphk.ru clinic → `@lancette.clinic` handle (discovered via curl iphk.ru + grep for instagram.com).

### 6.2 Reports Sampled

5 HTML reports from mixed sources:
- 2 from `/opt/data/reports-publish/` (Era Smile ×2, Jun 22)
- 2 from session-linked `report.html` (iphk.ru ×2)
- 1 from session-archive (nachalo-clinica, Jun 16 — outlier)

Reference: `/opt/data/report-reference.html` (ИПХиК (2).html, 78 KB, 10 sections).

### 6.3 Logs Analyzed

For each session:
- `metadata.json` — session metadata (clinic URL, timestamps, completed phases)
- `data/{PHASE}/{tool_name}.json` — per-call tool results (subdir structure)
- `data/{PHASE}.json` — flat-structure alternative
- `data/{PHASE}_interpretation.json` — LLM interpretation of phase results
- `data/{PHASE}_perplexity_used.json` — marker files (excluded from tool counts)

Limitation: `events.jsonl` files absent in all sampled sessions — structured event-stream analysis not possible. Plan 02 used mtime + interpretation text instead.

### 6.4 Server Commands Used

All commands read-only: `grep`, `head`, `wc`, `find`, `stat`, `cat`, `python3 -c` (introspection), `env`, `ls`.

No `sed -i`, `mv`, `rm`, `chmod`, `docker restart`, `docker cp` (write direction), `git push`.

Server file mtimes verified older than plan execution start on all files investigated.

### 6.5 Evidence Files

| Path | Source Plan | Content |
|------|-------------|---------|
| `evidence/coverage-baseline.md` | 01-01 | RES-02 (tool coverage) + RES-03 (section coverage) |
| `evidence/session-log-analysis.md` | 01-02 | RES-04 (session log deep dive) |
| `evidence/instagram-tool-test.md` | 01-04 | RES-05 (manual Instagram test) |
| `evidence/root-cause-analysis.md` | 01-03 Task 1 | RES-01 (root cause with 4-hypothesis testing) |

### 6.6 Limitations

- **Sample size:** 5 sessions is small but covers the available recent activity (4 iphk.ru re-runs + 1 arclinic.ru)
- **No `events.jsonl`:** Cannot directly count stream breaks or token-level truncation
- **Plan 04 v2 verification indirect:** Tested v2 logic via direct Perplexity API call; did not deploy v2 to container (out of scope for Phase 1)
- **No 3-niche testing:** Phase 1 tested iphk.ru + arclinic.ru + Era Smile (incidentally). Full 3-niche coverage is Phase 7.
- **Coverage metric is structural:** "Section present" = heading exists with at least one sentence. Does not measure content depth. A section with a heading + one sentence counts as present. Content depth is Phase 5 scope.

---

## Appendices

### Appendix A: Per-Session Raw Data

See `evidence/coverage-baseline.md` Section "Per-Session Tool Counts" and `evidence/session-log-analysis.md` Section "Session {hash}" subsections for full per-session breakdowns.

Summary:

| Session | Tools Called | Sections in Report | Crash? |
|---------|:---:|:---:|:---:|
| tg:322367335 (arclinic.ru) | 15 | (no linked report) | No |
| 1609c5d1 (iphk.ru) | 16 | 4/10 | No |
| 7282c8f7 (iphk.ru) | 16 | (no linked report) | No |
| full-test-1782061034 (iphk.ru) | 16 | (no linked report) | No |
| 4975ef15-de5 (crashed) | 0 | (no report) | YES |
| test-iphk-002 (iphk.ru) | 14 | 3/10 | No |

### Appendix B: Tool Registry vs Handlers Gap

**LLM-registered modules (49 `_import_tool` calls in `__init__.py`):**

```
orchestrate, quick_overview, perplexity_tools, run_prescan, run_aim_scout,
run_full_scout, run_background_pipeline, run_validation_check, run_web_search,
find_company_financials, telegram_tools, find_competitors, present_competitors,
run_ci_analysis, run_seo_audit, run_content_analysis, run_content_gaps,
run_ads_report, run_ads_intelligence, run_pagespeed, run_lighthouse,
run_tech_seo_audit, run_review_platforms, run_smi_mentions, crawlee_web,
scrapy_runner, run_hh_analysis, run_doctor_dossiers, run_instagram_content,
find_doctor_handles, geo_optimizer_tools, finalize_research, publish_scout_report,
generate_html_report, post_report, read_report_reference, collect_contact,
qualify_lead, escalate_to_manager, show_all_leads, get_lead_pipeline,
show_project_status, update_knowledge, send_telegram_file, shell_exec,
web_scraper, external_api, bitrix_scraper, firecrawl_web
```

**Pipeline-callable (`_TOOL_HANDLERS` 22 entries, alphabetical):**

```
crawlee_scrape, crawlee_search, find_company_financials, find_competitors,
firecrawl_agent, firecrawl_batch_scrape, firecrawl_extract, generate_html_report,
perplexity_deep_analyze, perplexity_search, publish_scout_report, run_ci_analysis,
run_content_analysis, run_content_gaps, run_doctor_dossiers, run_hh_analysis,
run_pagespeed, run_review_platforms, run_seo_audit, run_smi_mentions,
scrapy_crawl, web_search
```

**Gap: 27 modules registered for LLM but pipeline-unreachable.**

**17 presale-critical missing from `_TOOL_HANDLERS`:**

| Tool | Phase 2+ Action |
|------|-----------------|
| `run_instagram_content` | Phase 3 (IG-01) — deploy v2 + add handler |
| `find_doctor_handles` | Phase 3 (IG-01) — add handler |
| `run_tech_seo_audit` | Phase 2 — add handler |
| `run_lighthouse` | Phase 2 — add handler (alternative to run_pagespeed) |
| `run_prescan` | Phase 2 — add handler (fast overview) |
| `quick_overview` | Phase 2 — add handler (faster overview) |
| `run_ads_intelligence` | Phase 4 (DAT) — add handler |
| `run_ads_report` | Phase 4 (DAT) — add handler |
| `geo_optimizer_tools` | Phase 4 (DAT) — add handler |
| `present_competitors` | Phase 5 (INT) — add handler |
| `finalize_research` | Phase 5 (INT) — add handler |
| `run_validation_check` | Phase 2 (QC) — add handler |
| `post_report` | Phase 8 (DPL) — add handler |
| `orchestrate` | Meta-tool — skip (orchestrator-first mode replaces) |
| `run_aim_scout` | Meta-tool — skip (same) |
| `run_full_scout` | Meta-tool — skip (same) |
| `run_background_pipeline` | Meta-tool — skip (same) |

### Appendix C: Reference Sections Checklist

The 10 sections of `ИПХиК (2).html` reference report (78 KB):

| # | Section | Content | Baseline Presence |
|---|---------|---------|:---:|
| 1 | About | ОКВЭД, licenses, 3-year revenue dynamics | 0/5 (100% missing) |
| 2 | Market | Competitor table (8 competitors: revenue, trend, surgeons, Instagram) | 0/5 (100% missing) |
| 3 | Experts | Top-5 doctors: ФИО, регалии, subscribers, avg likes/views, style | 3/5 (60%) |
| 4 | Content Analysis | Per-doctor: style, themes (in %), gaps, potential + Top-5 patient fears | 1/5 (20%) |
| 5 | Media | Forbes, RBC, Vademecum, Kommersant — concrete URLs + dates | 3/5 (60%) |
| 6 | Competitors | Detail cards (revenue, year, surgeons, Instagram, specifics) | 1/5 (20%) |
| 7 | Whitefields | Matrix: client vs 3-5 competitors by field | 1/5 (20%) |
| 8 | Presence | Tech audit: strengths, fixes, priorities | 2/5 (40%) |
| 9 | Strategy | 5 directions: content, Telegram, GEO, reputation, cross-promo | 3/5 (60%, weak) |
| 10 | Offer | "Что AIM может сделать для клиники" — concrete steps + CTA | 1/5 (20%) |

**Baseline average: 3.0/10 sections per report (30%)**

**Phase 2 target: ≥8/10 sections (80%)**

---

## Phase 1 Completion Status

| Requirement | Status | Plan | Evidence |
|-------------|--------|------|----------|
| RES-01 | COMPLETE | 01-03 | `evidence/root-cause-analysis.md` |
| RES-02 | COMPLETE | 01-01 | `evidence/coverage-baseline.md` |
| RES-03 | COMPLETE | 01-01 | `evidence/coverage-baseline.md` |
| RES-04 | COMPLETE | 01-02 | `evidence/session-log-analysis.md` |
| RES-05 | COMPLETE | 01-04 | `evidence/instagram-tool-test.md` |

**Phase 1: 4/4 plans complete, 5/5 requirements addressed.**

**Phase 2 can begin.** Read this RESEARCH.md top-to-bottom before starting Phase 2 planning.

---

*Consolidated by Plan 01-03 Task 2 executor — 2026-06-23*
*Phase 1 deliverable: single readable research report for admin*
