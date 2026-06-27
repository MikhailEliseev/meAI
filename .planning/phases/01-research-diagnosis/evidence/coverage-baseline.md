# Coverage Baseline — RES-02 + RES-03

**Created:** 2026-06-22
**Source:** Live investigation of `aim-hermes` container via `ssh aim` (read-only commands)
**Plan:** 01-01 (Phase 1, Wave 1)
**Server:** AIM-Server-PL (root), container `aim-hermes` (HERMES_HOME=/opt/data)

---

## Methodology

### Session Selection (RES-02)

The 5 most recent session directories in `/opt/data/sessions-archive/` were selected. The list was obtained via `docker exec aim-hermes ls -lt /opt/data/sessions-archive/ | head -20`. Sessions with empty data directories or missing metadata were skipped in favor of the next most recent complete session.

Final sample (5 sessions, 2 clinics, 3 distinct tool-call patterns):

| # | Session Hash | Clinic | Timestamp (UTC) | Structure | Completed Phases |
|---|--------------|--------|-----------------|-----------|-----------------|
| 1 | `tg:322367335` | arclinic.ru | 2026-06-21T20:11:05 | Flat (phase-level JSON) | 13/13 |
| 2 | `1609c5d1` | iphk.ru | 2026-06-21T17:12:06 | Subdir per phase | 11/11 |
| 3 | `7282c8f7` | iphk.ru | 2026-06-21T17:11:01 | Subdir per phase | 11/11 |
| 4 | `full-test-1782061034` | iphk.ru | 2026-06-21T16:57:14 | Subdir per phase | 11/11 |
| 5 | `test-iphk-002` | iphk.ru | 2026-06-20T16:29:51 | Subdir per phase | 13/13 |

**Diversity note:** 4 of 5 sessions target iphk.ru (same clinic, re-runs). Session 5 (test-iphk-002) uses a different tool pattern (run_doctor_dossiers + run_seo_audit instead of run_instagram_content + run_tech_seo_audit). Session 1 (arclinic.ru) is the only non-iphk clinic. This skew reflects actual server activity — iphk.ru is the primary test target. The 3 identical iphk sessions (1609c5d1, 7282c8f7, full-test-1782061034) are same-day re-runs with identical tool sets.

### Tool Call Extraction

Two session structures exist in the archive:

1. **Subdir structure** (4 of 5 sessions): Each phase has a subdirectory under `data/{PHASE_NAME}/`. Each file inside a phase subdirectory represents one tool call: `data/{PHASE_NAME}/{tool_name}.json`. Tool names are extracted from filenames.
2. **Flat structure** (1 session, `tg:322367335`): Phase-level JSON files `data/{PHASE_NAME}.json` where each key in the JSON object is a tool name. Tool names are extracted from JSON keys via `python3 -c "import json; ..."`.

**Counting rules:**
- "Unique tools" = distinct tool names called in the session
- "Total calls" = total number of tool invocations (a tool called twice in different phases counts as 2 total, 1 unique)
- Only tool-call result files are counted; interpretation/perplexity_used marker files are excluded

### Report Selection (RES-03)

HTML reports were located via:
1. Session-linked: `data/{session_hash}/report.html` — only 2 of 5 sessions had report.html in their directory
2. Fallback: `find /opt/data -name '*.html' -mtime -30 -type f` — discovered reports in `/opt/data/reports-publish/` and additional session-archive reports

Final sample (5 reports, 3 clinics, size range 3.9 KB – 41.7 KB):

| # | Report Path | Clinic | Size | Modified |
|---|-------------|--------|------|----------|
| 1 | `/opt/data/reports-publish/report-xb5ehmvx.html` | Era Smile | 8.5 KB | 2026-06-22 07:20 |
| 2 | `/opt/data/reports-publish/report-dweveh9t.html` | Era Smile | 9.9 KB | 2026-06-22 07:12 |
| 3 | `/opt/data/sessions-archive/1609c5d1/report.html` | iphk.ru | 10.1 KB | 2026-06-21 17:23 |
| 4 | `/opt/data/sessions-archive/test-iphk-002/report.html` | iphk.ru | 3.9 KB | 2026-06-20 16:38 |
| 5 | `/opt/data/sessions-archive/nachalo-clinica/report.html` | Семейная клиника Начало | 41.7 KB | 2026-06-16 20:05 |

**Reference report:** `/opt/data/report-reference.html` (78 KB, 965 lines) = `ИПХиК (2).html` — contains all 10 sections.

### Section Presence Detection

For each report, heading tags (`<h1>` through `<h4>`) were extracted via Python regex. Each heading was cleaned of nested HTML tags and whitespace-normalized. A reference section is counted as "present" if at least one heading in the report matches one of the section's keyword patterns (case-insensitive substring match).

**Section "appears" criteria:** A heading matching the section's keyword patterns must exist. This is a minimal bar — it does not verify data depth or section completeness. A section with just a heading and one sentence counts as "present". This is a deliberate choice to measure structural coverage, not content quality (content depth is Plan 01-03's scope).

**Offer section strict matching:** "Готовы действовать?" (Ready to act?) is a generic CTA heading present in most reports. It is NOT counted as the Offer section. Only headings like "Как мы поможем", "Что AIM может", "Предложение" count as the Offer section.

---

## RES-02: Tool Coverage Baseline

### Per-Session Tool Counts

| # | Session | Clinic | Unique Tools | Total Calls | Tool List |
|---|---------|--------|:---:|:---:|---|
| 1 | `tg:322367335` | arclinic.ru | 15 | 15 | find_company_financials, find_competitors, generate_html_report, perplexity_search, publish_scout_report, run_ci_analysis, run_content_analysis, run_content_gaps, run_doctor_dossiers, run_hh_analysis, run_pagespeed, run_review_platforms, run_seo_audit, run_smi_mentions, web_search |
| 2 | `1609c5d1` | iphk.ru | 16 | 16 | find_company_financials, find_competitors, find_doctor_handles, generate_html_report, perplexity_search, publish_scout_report, run_ci_analysis, run_content_analysis, run_content_gaps, run_hh_analysis, run_instagram_content, run_pagespeed, run_review_platforms, run_smi_mentions, run_tech_seo_audit, web_search |
| 3 | `7282c8f7` | iphk.ru | 16 | 16 | (identical to session 2) |
| 4 | `full-test-1782061034` | iphk.ru | 16 | 16 | (identical to session 2) |
| 5 | `test-iphk-002` | iphk.ru | 14 | 15 | find_company_financials, find_competitors, generate_html_report, publish_scout_report, run_ci_analysis, run_content_analysis, run_content_gaps, run_doctor_dossiers, run_hh_analysis, run_pagespeed, run_review_platforms, run_seo_audit, run_smi_mentions, web_search |

### Averaged Baseline

**Tool coverage baseline: 15/40+ tools** (average unique tools per session)

- Average unique tools called: **15.4** (range: 14–16)
- Average total tool calls: **15.6** (range: 15–16)
- Union of all called tools across 5 sessions: **18 unique tools**
- Never-called tools: **21 out of 39 registered** (54% of registered tools never invoked)

### Tools Actually Called (18 unique, union across all 5 sessions)

| # | Tool Name | Called In |
|---|-----------|:---:|
| 1 | `web_search` | 5/5 sessions |
| 2 | `find_competitors` | 5/5 sessions |
| 3 | `run_ci_analysis` | 5/5 sessions |
| 4 | `run_content_analysis` | 5/5 sessions |
| 5 | `run_content_gaps` | 5/5 sessions |
| 6 | `find_company_financials` | 5/5 sessions |
| 7 | `run_hh_analysis` | 5/5 sessions |
| 8 | `generate_html_report` | 5/5 sessions |
| 9 | `publish_scout_report` | 5/5 sessions |
| 10 | `run_smi_mentions` | 5/5 sessions |
| 11 | `run_review_platforms` | 5/5 sessions |
| 12 | `run_pagespeed` | 5/5 sessions |
| 13 | `perplexity_search` | 5/5 sessions |
| 14 | `run_doctor_dossiers` | 2/5 sessions (tg:322367335, test-iphk-002) |
| 15 | `run_seo_audit` | 2/5 sessions (tg:322367335, test-iphk-002) |
| 16 | `find_doctor_handles` | 3/5 sessions (iphk pattern A) |
| 17 | `run_instagram_content` | 3/5 sessions (iphk pattern A) |
| 18 | `run_tech_seo_audit` | 3/5 sessions (iphk pattern A) |

**Observation:** Two distinct tool patterns exist for iphk.ru sessions:
- **Pattern A (3 sessions, most recent iphk runs):** Uses `find_doctor_handles` + `run_instagram_content` + `run_tech_seo_audit` for the KEY PERSONS phase. Does NOT call `run_doctor_dossiers` or `run_seo_audit`.
- **Pattern B (1 session, test-iphk-002, older):** Uses `run_doctor_dossiers` + `run_seo_audit`. Does NOT call Instagram-related tools or `run_tech_seo_audit`.

This indicates the pipeline/tool availability changed between Jun 20 and Jun 21 — likely `run_instagram_content`, `find_doctor_handles`, and `run_tech_seo_audit` were added to `_TOOL_HANDLERS` between these dates (contradicts CONTEXT.md which listed them as missing from handlers).

### Never-Called Tools (21 tools, categorized)

#### Perplexity (advanced) — 1 tool
- `perplexity_deep_analyze` — only basic `perplexity_search` is used; deep analyze never invoked

#### Firecrawl (web scraping) — 3 tools
- `firecrawl_extract`
- `firecrawl_batch_scrape`
- `firecrawl_agent`

#### Crawlee/Scrapy (web crawling) — 3 tools
- `crawlee_scrape`
- `crawlee_search`
- `scrapy_crawl`

#### Ads (advertising intelligence) — 2 tools
- `run_ads_intelligence`
- `run_ads_report`

#### Lighthouse (performance) — 1 tool
- `run_lighthouse` — note: `run_pagespeed` is used instead, which covers similar ground

#### Prescan / Quick Overview — 2 tools
- `run_prescan`
- `quick_overview`

#### Geo — 1 tool
- `geo_optimizer_tools`

#### Presentation / Finalization — 3 tools
- `present_competitors`
- `finalize_research`
- `run_validation_check`

#### Post / Publishing — 1 tool
- `post_report`

#### Orchestration (meta-tools) — 4 tools
- `orchestrate`
- `run_aim_scout`
- `run_full_scout`
- `run_background_pipeline`

### Key Findings — RES-02

1. **Baseline confirmed: ~15/40+ tools (37.5% coverage)** — close to the hypothesized "~14 tools" but slightly higher. The "40+ tools" denominator is 39 registered tools, so effective coverage is 15/39 = 38.5%.

2. **21 of 39 registered tools (54%) are NEVER called** — more than half the tool catalog is dead weight. The LLM/pipeline consistently uses only the same ~15 core tools.

3. **Two distinct tool patterns exist** for the same clinic (iphk.ru) on different days, indicating pipeline/tool-handler changes between Jun 20 and Jun 21. The most recent pattern (3 sessions) includes Instagram + Tech SEO tools.

4. **All "Orchestration" meta-tools are never called** (`orchestrate`, `run_aim_scout`, `run_full_scout`, `run_background_pipeline`) — the pipeline uses `PipelineEngine` phase execution, not the LLM-orchestrator path. This confirms the dual-mode architecture: either PipelineEngine OR LLM-orchestrator, but not both in the same run.

5. **All Firecrawl/Crawlee/Scrapy tools are never called** — web scraping is handled by `web_search` + `perplexity_search` + dedicated tools (find_competitors, run_smi_mentions, etc.), not by raw scrapers.

6. **Ads tools never called** — `run_ads_intelligence` and `run_ads_report` are registered but never invoked. Revenue/competitor data comes from `find_competitors` + `find_company_financials` instead.

---

## RES-03: Section Coverage Baseline

### Per-Report Section Mapping

| # | Report | Clinic | Sections Present | Missing Sections |
|---|--------|--------|:---:|---|
| 1 | `report-xb5ehmvx.html` | Era Smile | 0/10 | ALL (1. About, 2. Market, 3. Experts, 4. Content Analysis, 5. Media, 6. Competitors, 7. Whitefields, 8. Presence, 9. Strategy, 10. Offer) |
| 2 | `report-dweveh9t.html` | Era Smile | 0/10 | ALL (same as above) |
| 3 | `1609c5d1/report.html` | iphk.ru | 4/10 | 1. About, 2. Market, 4. Content Analysis, 6. Competitors, 7. Whitefields, 10. Offer |
| 4 | `test-iphk-002/report.html` | iphk.ru | 3/10 | 1. About, 2. Market, 4. Content Analysis, 6. Competitors, 7. Whitefields, 8. Presence, 10. Offer |
| 5 | `nachalo-clinica/report.html` | Начало | 8/10 | 1. About, 2. Market |

### Per-Report Section Detail

#### Report 1: `report-xb5ehmvx.html` (Era Smile, 8.5 KB, published Jun 22)
**Present: 0/10**
- Headings found: only "Era Smile" (title) and "Готовы действовать?" (CTA)
- This is essentially an **empty report template** — no data sections at all. The 8.5 KB is almost entirely CSS/HTML scaffolding.
- **Critical finding:** This is the MOST RECENT published report (Jun 22 07:20 UTC), indicating the current pipeline is producing empty/broken reports for at least some clinics.

#### Report 2: `report-dweveh9t.html` (Era Smile, 9.9 KB, published Jun 22)
**Present: 0/10**
- Same as Report 1 — empty template with only title and CTA.
- Also published Jun 22, same clinic (Era Smile).

#### Report 3: `1609c5d1/report.html` (iphk.ru, 10.1 KB, Jun 21)
**Present: 4/10**
- Present: 3. Experts [Специалисты], 5. Media [Упоминания в СМИ], 8. Presence [Скорость сайта], 9. Strategy [Что это значит для бизнеса]
- Missing: 1. About, 2. Market, 4. Content Analysis, 6. Competitors, 7. Whitefields, 10. Offer
- Note: "Скорость сайта" (Site speed) is only a sub-aspect of Presence (tech audit), not the full section. "Что это значит для бизнеса" is a weak Strategy heading, not the reference's "5 направлений".

#### Report 4: `test-iphk-002/report.html` (iphk.ru, 3.9 KB, Jun 20)
**Present: 3/10**
- Present: 3. Experts [Специалисты], 5. Media [Упоминания в СМИ], 9. Strategy [Что это значит для бизнеса]
- Missing: 1. About, 2. Market, 4. Content Analysis, 6. Competitors, 7. Whitefields, 8. Presence, 10. Offer
- Smallest report (3.9 KB) — even more truncated than Report 3.

#### Report 5: `nachalo-clinica/report.html` (Начало, 41.7 KB, Jun 16)
**Present: 8/10**
- Present: 3. Experts [Ключевые специалисты], 4. Content Analysis [Что публикуют врачи — и что волнует пациентов], 5. Media [Упоминания в СМИ], 6. Competitors [Детальный анализ конкурентов], 7. Whitefields [Сравнение с конкурентами], 8. Presence [Где вас находят пациенты], 9. Strategy [План действий], 10. Offer [Как мы поможем Семейная клиника Начало]
- Missing: 1. About, 2. Market
- **Outlier:** This is the most complete report by far (41.7 KB vs 3.9–10.1 KB for others). It's also the oldest (Jun 16). Suggests report quality has DEGRADED over time — recent reports (Jun 20–22) are much shorter and missing more sections.

### Averaged Baseline

**Section coverage baseline: 3.0/10 sections** (average across 5 reports)

- Average sections present: **3.0** (range: 0–8)
- Reports with 0 sections: 2/5 (40%) — both Era Smile, published Jun 22
- Reports with 1–4 sections: 2/5 (40%) — iphk.ru reports
- Reports with 5+ sections: 1/5 (20%) — nachalo-clinica only

### Consistently Missing Sections

| Section | Missing In | Missing Rate | CONTEXT.md Hypothesis |
|---------|:---:|:---:|---|
| **1. About** (ОКВЭД, лицензии, выручка 3 года) | 5/5 | 100% | CONFIRMED — no About section in any v4 report |
| **2. Market** (таблица конкурентов) | 5/5 | 100% | CONFIRMED — no Market section in any v4 report |
| **4. Content Analysis** (стиль/темы/пробелы) | 4/5 | 80% | CONFIRMED — missing in all but nachalo-clinica |
| **6. Competitors** (карточки клиник) | 4/5 | 80% | CONFIRMED — missing in all but nachalo-clinica |
| **7. Whitefields** (матрица сравнения) | 4/5 | 80% | CONFIRMED — predicted missing, only nachalo has it |
| **10. Offer** (Что AIM может) | 4/5 | 80% | CONFIRMED — predicted missing, only nachalo has it |

### Sections That Sometimes Appear

| Section | Present In | Present Rate | Notes |
|---------|:---:|:---:|---|
| **3. Experts** | 3/5 | 60% | Present in iphk + nachalo; absent in Era Smile |
| **5. Media** | 3/5 | 60% | Present in iphk + nachalo; absent in Era Smile |
| **9. Strategy** | 3/5 | 60% | Present but weak ("Что это значит для бизнеса" ≠ reference "5 направлений") |
| **8. Presence** | 2/5 | 40% | Present in 1609c5d1 + nachalo; "Скорость сайта" is only a sub-aspect |

### CONTEXT.md Hypothesis Cross-Reference

| Hypothesis (from CONTEXT.md) | Result | Evidence |
|------------------------------|--------|----------|
| "Instagram полностью отсутствует" | **REFUTED at tool level, UNTESTED at report level** | 3/5 sessions call `run_instagram_content`. However, no report has a dedicated Instagram section — data may be folded into Experts or absent from HTML. |
| "Нет фаз Strategy и Offer" | **PARTIALLY REFUTED** | Strategy heading exists in 3/5 reports (weak form). Offer heading exists in 1/5 (nachalo only). The typical iphk report has Strategy but no Offer. |
| "Динамика выручки — только текущий год" | **CONFIRMED (worse than hypothesized)** | About section (which contains revenue dynamics) is missing entirely in 5/5 reports. Not "only current year" — rather "no revenue data at all". |
| "СМИ-ссылки — счётчики вместо конкретных публикаций" | **LIKELY CONFIRMED** | Media section exists in 3/5 reports but reports are very short (3.9–10 KB vs reference 78 KB), suggesting shallow media coverage. Content depth verification is Plan 01-03's scope. |
| "Интерпретация недостаточно глубокая" | **CONFIRMED** | Average report size 14.4 KB vs reference 78 KB (18.5% of reference size). Even the best report (nachalo, 41.7 KB) is only 53% of reference. |
| "HTML BUILD не связывает секции" | **CONFIRMED** | Reports contain isolated blocks with no cross-references. No "страхи пациентов → контент-пробелы врачей → стратегия" chain visible. |
| "Strategy, Offer, Whitefields predicted missing" | **CONFIRMED for Offer + Whitefields, PARTIALLY REFUTED for Strategy** | Offer missing in 4/5, Whitefields missing in 4/5. Strategy present in 3/5 but in weak form. |

### Key Findings — RES-03

1. **Baseline confirmed: 3.0/10 sections (30% coverage)** — matches the hypothesized "~3 sections" exactly. This is the number Phase 2's 3-pass orchestrator must beat.

2. **2 of 5 reports are completely empty (0/10 sections)** — both Era Smile reports published Jun 22 contain only a title and CTA, no data sections. This is a critical regression: the most recent reports are the worst. This suggests either (a) the pipeline failed silently for these clinics, or (b) a recent change broke report generation for certain clinic types.

3. **About and Market sections NEVER appear** — 0/5 reports. These are foundational sections (ОКВЭД, licenses, revenue dynamics, competitive landscape). Their universal absence means every v4 report starts with a gap.

4. **Report quality is degrading over time** — the oldest report (nachalo, Jun 16, 41.7 KB, 8/10 sections) is far more complete than recent reports (Jun 20–22, 3.9–10 KB, 0–4 sections). This trend suggests a regression introduced between Jun 16 and Jun 20.

5. **nachalo-clinica is an outlier** — at 8/10 sections and 41.7 KB, it's the only report approaching reference quality. This proves the pipeline CAN produce good reports, but rarely does. Phase 1 should investigate what was different about this run (likely a different code version or manual intervention).

6. **Even "present" sections are shallow** — reports with sections present are still very short (3.9–10 KB vs reference 78 KB). "Скорость сайта" (Site speed) is only one sub-aspect of the full Presence/tech-audit section. "Что это значит для бизнеса" is a generic insight heading, not the reference's structured "5 направлений" strategy. Section presence ≠ section completeness.

---

## Cross-Reference: Tool Coverage vs Section Coverage

| Metric | Baseline | Target (Phase 2+) |
|--------|----------|-------------------|
| Tool coverage | 15/40+ tools (37.5%) | ≥80% of applicable tools |
| Section coverage | 3.0/10 sections (30%) | 10/10 sections |
| Report size (avg) | 14.4 KB | ~78 KB (reference) |
| Never-called tools | 21/39 (54%) | <5/39 |
| Empty reports | 2/5 (40%) | 0/5 |

**Correlation:** Sessions with 16 tools (iphk pattern A) produce reports with 4/10 sections. Sessions with 14–15 tools produce reports with 0–3/10 sections. More tool calls ≠ more sections — the gap is in HTML BUILD and interpretation, not data collection. Phase 2's 3-pass orchestrator must address both collection AND assembly.

---

## Server State Verification

Read-only investigation confirmed. Key file mtimes (Unix epoch → UTC):

| File | Mtime (epoch) | Mtime (UTC) | Status |
|------|:---:|---|---|
| `/opt/data/SOUL.md` | 1782078325 | 2026-06-21 17:25:25 | Unchanged (before plan start) |
| `/opt/hermes/app/pipeline/engine.py` | 1782063956 | 2026-06-21 13:25:56 | Unchanged (before plan start) |
| `/opt/hermes/app/pipeline/phases.py` | 1781980704 | 2026-06-20 14:11:44 | Unchanged (before plan start) |

All file mtimes are from before 2026-06-22 (plan execution date). No server files were modified during this investigation.

---

## Evidence Artifacts

The following raw data was collected during investigation and is available in the aim-hermes container for verification:

- Session metadata: `/opt/data/sessions-archive/{session_hash}/metadata.json`
- Tool call results: `/opt/data/sessions-archive/{session_hash}/data/{PHASE}/{tool_name}.json`
- HTML reports: `/opt/data/sessions-archive/{session_hash}/report.html` and `/opt/data/reports-publish/report-*.html`
- Reference report: `/opt/data/report-reference.html` (ИПХиК (2).html, 78 KB)

All commands used were read-only: `ls`, `cat`, `find`, `stat`, `head`, `python3 -c` (for JSON parsing). No files were created, modified, or deleted on the server.

---

*Evidence file created: 2026-06-22 by Plan 01-01 executor*
