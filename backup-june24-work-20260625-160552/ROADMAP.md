# Roadmap: Hermes v5 — Full Coverage Reports

## Overview

Переработка Hermes от 30% покрытия к полным отчётам пресейла на уровне референса ИПХиК (2).html. Путь: исследовать почему v4 пропускает инструменты → построить 3-проходный LLM-оркестратор с QC-чек-листом → подключить Instagram → наполнить отчёт всеми 10 секциями с глубокими данными → переписать интерпретацию под нарратив → синхронизировать SOUL/SKILL/phases → протестировать на 3 нишах → задеплоить без даунтайма.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Research & Diagnosis** - Root cause analysis: why v4 LLM skips tools, with measured baseline coverage
- [x] **Phase 2: 3-Pass Orchestrator + Coverage Checklist** - LLM-оркестратор с 3-проходным циклом и QC-чек-листом как метрикой покрытия
- [ ] **Phase 3: Instagram Integration** - run_instagram_content в оркестраторе, обязательный для косметологии/пластики
- [x] **Phase 4: New Sections & Data Depth** - Все 10 секций референса: Strategy, Offer, Whitefields + 3-year revenue, media links, competitor cards (completed 2026-06-24)
- [x] **Phase 5: Deep Interpretation** - Нарратив вместо дампа метрик, cross-linked секции, бизнес-язык (completed 2026-06-24)
- [x] **Phase 6: Documentation Sync** - SOUL.md, SKILL.md, phases.py, engine.py — единая истина, без рассинхрона (completed 2026-06-24)
- [ ] **Phase 7: Test on 3 Niches** - Валидация на 3 реальных пресейлах: пластика, стоматология, косметология
- [ ] **Phase 8: Zero-Downtime Deploy** - Деплой в production через docker cp без прерывания пресейлов

## Phase Details

### Phase 1: Research & Diagnosis

**Goal**: Admin understands WHY v4 LLM skips tools and has measured baseline coverage — root cause confirmed, not guessed
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: RES-01, RES-02, RES-03, RES-04, RES-05
**Success Criteria** (what must be TRUE):

  1. Admin can read a research report identifying the confirmed root cause(s) of LLM tool-skipping (prompt issue, model limitation, pipeline constraint, or combination — with evidence)
  2. Baseline coverage measured: X out of 40+ tools actually called by LLM in a typical v4 presale run
  3. Reference section coverage measured: Y out of 10 sections from ИПХиК (2).html actually appear in v4 reports
  4. Log analysis of 3-5 past sessions (from /opt/data/sessions-archive/) shows specific decision points where LLM truncated or skipped — with timestamps and tool names
  5. run_instagram_content tested manually on 1 clinic — returns expected data shape, and whether a dedicated handler is needed is confirmed

**Plans**: 4 plans
Plans:

- [x] 01-01-PLAN.md — Baseline coverage measurement (RES-02 tool coverage + RES-03 section coverage)
- [x] 01-02-PLAN.md — Session log deep dive with skip/truncate decision points (RES-04)
- [x] 01-03-PLAN.md — Root cause confirmation + RESEARCH.md consolidation (RES-01)
- [x] 01-04-PLAN.md — Instagram tool manual test + handler need confirmation (RES-05)

### Phase 2: 3-Pass Orchestrator + Coverage Checklist

**Goal**: Hermes runs an automatic 3-pass cycle (Collect → Gap-analyze → Fill+Assemble) with a QC checklist as the gap-analysis reference — no manual intervention
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: ORC-01, ORC-02, ORC-03, ORC-04, ORC-05, QC-01, QC-02, QC-03, QC-04
**Success Criteria** (what must be TRUE):

  1. Admin triggers a presale and observes 3 distinct passes executing automatically (Сбор → Гэп-анализ → Допосбор + Сборка) with no manual intervention
  2. LLM-оркестратор selects tools by situation (like v1), not by a rigid pipeline sequence — at least 2 different tool-call patterns observed across 2 different clinics
  3. After pass 2, LLM produces a gap-analysis report comparing collected data against the QC checklist (10-20 items) — showing which items are covered vs missing
  4. If gaps remain after pass 3, the report honestly marks them as "данные недоступны" — no fabricated data
  5. PipelineEngine still works as an alternative mode (not deleted), and each run ends with a coverage % report (target: ≥ 80% of checklist items filled with real data)

**Plans**: 3 plans
Plans:

- [x] 02-01-PLAN.md — P0 bugfix: _unwrap_tool_output NameError (unblocks HTML BUILD, ORC-05 baseline preserved)
- [x] 02-02-PLAN.md — 3-Pass Orchestrator Core: new app/orchestrator/ module + ORCHESTRATOR_MODE env var opt-in (ORC-01, ORC-02, ORC-05)
- [x] 02-03-PLAN.md — QC Checklist + Coverage Reporting: 15-item checklist, soft QC gate, HTML rendering (ORC-03, ORC-04, QC-01, QC-02, QC-03, QC-04)

*Deferred to Phase 3:* Plan 02-04 (wire 17 missing tools to _TOOL_HANDLERS + phase chunking) — naturally belongs with Instagram integration (IG-01 needs _TOOL_HANDLERS entry); orchestrator-first mode in 02-02 bypasses _TOOL_HANDLERS entirely, so fallback path can wait.

### Phase 3: Instagram Integration

**Goal**: Instagram analysis runs for niches where it's critical (cosmetology, plastic surgery), producing per-doctor metrics matching the reference sections 03+04
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: IG-01, IG-02, IG-03, IG-04
**Success Criteria** (what must be TRUE):

  1. run_instagram_content is callable by both the LLM-orchestrator and the PipelineEngine (added to engine.py _TOOL_HANDLERS, not just the LLM registry)
  2. For cosmetology and plastic surgery niches, Instagram analysis always runs — LLM does not skip it as "optional"
  3. For each top-5 doctor, the report contains: followers, avg likes, avg views, content style, topics (in %), gaps, potential — matching reference sections 03+04
  4. If a clinic has no Instagram, the report notes this honestly and does not block the remaining phases

**Plans**: 6 plans
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Deploy + wire Instagram tools to engine.py _TOOL_HANDLERS + v2 docker cp (IG-01, D-12, D-13)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — Niche detection mini-call between Pass 1 and Pass 2 + OrchestratorState.niche field (IG-02, D-01..03)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-03-PLAN.md — Pass 1+2 prompts + QC checklist helpers (is_item_applicable, applicable_items, is_niche_instagram_critical) (IG-02, D-04, D-06, D-08 data-model)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-06-PLAN.md — Runtime hard-FAIL override + conditional-total logic in three_pass.py + CoverageReport.not_applicable_items field + tests (IG-02, D-05, D-08 runtime)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 03-04-PLAN.md — Adaptive top-5 doctor discovery Pass 1+2 prompts + batch cohort logic (IG-03, D-09, D-10, D-11)
- [x] 03-05-PLAN.md — HTML no-Instagram block + QC not_applicable rendering + Pass 3 prompt niche/instagram_data kwargs (IG-04, D-07, D-08 HTML side)

### Phase 4: New Sections & Data Depth

**Goal**: Reports contain all 10 reference sections with deep data — Strategy, Offer, Whitefields added; revenue covers 3 years; media has concrete URLs; competitor cards are detailed
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, DAT-01, DAT-02, DAT-03, DAT-04, DAT-05
**Success Criteria** (what must be TRUE):

  1. Report includes a Strategy section with 5 specific directions (content, Telegram, GEO, reputation, cross-promo) based on collected data — not generic advice
  2. Report includes an Offer section ("Что AIM может сделать для клиники") with concrete steps and CTA — matching reference section 10
  3. Whitefields section shows a matrix: client vs 3-5 competitors by field (not just content_gaps list)
  4. Revenue dynamics cover 3 years (not just current year) with year-over-year comparison — matching reference "+79% over 3 years"
  5. Media section lists concrete publication URLs with dates (Forbes, RBC, Vademecum, Kommersant) — not just category counts

**Plans**: 8 plans
Plans:
**Wave 1** *(parallel — no file conflicts)*

- [x] 04-01-PLAN.md — Extend find_company_financials: 3-year revenue dynamics + clinic metrics (DAT-01, DAT-04, D-12..14, D-21)
- [x] 04-02-PLAN.md — Extend find_doctor_handles: structured регалии + _merge_doctor_data (SEC-04, D-08..09)
- [x] 04-03-PLAN.md — Create run_forum_pains + run_media_urls tools + register in _TOOL_HANDLERS (SEC-05, DAT-02, D-10..11, D-15..18)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-04-PLAN.md — Pass 1+2 prompts + QC checklist expansion 15→18 items (D-25, D-01..03 collection rules)
- [x] 04-05-PLAN.md — Pass 3 prompt with Strategy/Offer/Whitefields/регалии/страхи generation rules (D-24, SEC-01..05)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-06-PLAN.md — HTML Data Sections: revenue table, media URLs, ratings, clinic metrics, competitor cards (DAT-01..05)

**Wave 4** *(blocked on Wave 3 completion — same file as 04-06)*

- [x] 04-07-PLAN.md — HTML LLM Sections: Strategy, Offer, Whitefields matrix, Experts+регалии, Content+страхи (SEC-01..05)

**Wave 5** *(blocked on Wave 4 completion — deploy + integration)*

- [x] 04-08-PLAN.md — Deploy all Phase 4 files via docker cp + end-to-end integration validation (DPL-01..05)

### Phase 5: Deep Interpretation

**Goal**: Each report section reads as narrative with business insights, not metric dumps — matching reference quality and cross-linking sections
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: INT-01, INT-02, INT-03, INT-04, INT-05
**Success Criteria** (what must be TRUE):

  1. Each section's interpretation_prompt produces narrative text with concrete conclusions — not a dump of metrics
  2. Sections are cross-linked: patient fears (section 04) → doctor content gaps (section 04) → strategy (section 09) — not isolated blocks
  3. Business language used throughout ("каждая секунда задержки теряет пациентов" not "LCP 7.3s")
  4. Gap blocks present in format: strength (with number) + growth point (with competitor benchmark)
  5. Each section has a blockquote with the main strategic insight (1-2 sentences)

**Plans**: 3 plans
Plans:

**Wave 1** *(foundational — prompt rules first)*

- [x] 05-01-PLAN.md — Pass 3 prompt items 16-21: narrative style + business language + cross-references + gap-block format + section blockquote + short reference calibration (INT-01..05 prompt layer, D-01..11)

**Wave 2** *(parallel — different files, both depend on Wave 1)*

- [x] 05-02-PLAN.md — HTML helpers (_render_gap_blocks + _render_section_insight) + extend 10 Phase 4 section builders with insight/gap_blocks kwargs + wiring (INT-04, INT-05 HTML layer, D-07..10)
- [x] 05-03-PLAN.md — Reference calibration: EXAMPLES BY SECTION block with 10+ narrative snippets extracted from ИПХиК (2).html (D-11 full satisfaction)

### Phase 6: Documentation Sync

**Goal**: SOUL.md, SKILL.md, phases.py, and engine.py all describe the same system — no desync, no phantom phases, all tools in handlers
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: SYN-01, SYN-02, SYN-03, SYN-04, SYN-05
**Success Criteria** (what must be TRUE):

  1. phases.py, SKILL.md, and SOUL.md all reference the same phase set — the 13/14/16 desync is eliminated
  2. SOUL.md describes the 3-pass cycle, LLM-orchestrator, and tool catalogue — without a rigid phase sequence
  3. SKILL.md (aim-scout) describes the orchestrator + coverage checklist — not "FULL AUTO pipeline"
  4. engine.py _TOOL_HANDLERS includes all tools the LLM can call (not a subset) — pipeline mode fully functional
  5. No phantom phases (0.5, 0.75, 0.8, 3.2) remain in SOUL.md or SKILL.md

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 06-01-PLAN.md — SOUL.md comprehensive rewrite + deploy (SYN-01, SYN-02, SYN-05; D-03)

**Wave 2** *(blocked on Wave 1 completion — consistent terminology)*

- [x] 06-02-PLAN.md — aim-scout SKILL.md rewrite (dual-mode) + phases.py LEGACY marker + deploy (SYN-01, SYN-03, SYN-04; D-04, D-05, D-06)
- [x] 06-03-PLAN.md — engine.py _TOOL_HANDLERS assertion test + phantom phase grep audit + deploy (SYN-04, SYN-05; D-07, D-08, D-10)

### Phase 7: Test on 3 Niches

**Goal**: System validated on 3 real presales across different niches — each achieving ≥ 80% checklist coverage
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: TST-01, TST-02, TST-03, TST-04, TST-05
**Success Criteria** (what must be TRUE):

  1. 3 test presales completed: plastic surgery (iphk.ru — has reference), dentistry, cosmetology — each produces a full HTML report
  2. Each test report scored against the QC checklist with ≥ 80% coverage of items filled with real data
  3. PRESALE mode test via Telegram bot (as a real client would trigger) produces a full report end-to-end
  4. ADMIN mode test (manual trigger for a specific clinic) produces a full report end-to-end
  5. Results fixed: proposal.html + feedback.md saved in /opt/data/memories/proposals/[client-slug]/ for each test

**Plans**: 4 plans
Plans:
**Wave 1** *(pre-flight — must complete before niche tests)*

- [x] 07-01-PLAN.md — Pre-flight scout: verify container state (handlers=26, QC=18, healthy) + build reusable test harness + select dental/cosmetology clinics (TST-01 prep, TST-05 prep)

**Wave 2** *(sequential for autonomous reliability — shared container resource)*

- [x] 07-02-PLAN.md — Plastic surgery test (iphk.ru) PRESALE mode: trigger → wait ≤30min → QC score 18 items (Instagram HARD-FAIL) → style vs reference + feedback.md (TST-01 1/3, TST-02, TST-03, TST-05)

**Wave 3** *(blocked on 07-02 completion)*

- [ ] 07-03-PLAN.md — Dental test ADMIN mode: trigger → wait → QC score 17 items (item 4 not_applicable) → feedback.md (TST-01 2/3, TST-02, TST-04, TST-05)

**Wave 4** *(blocked on 07-03 completion)*

- [ ] 07-04-PLAN.md — Cosmetology test PRESALE mode + aggregate report: trigger → wait → QC score 18 items (Instagram HARD-FAIL) → feedback.md + 3-niche aggregate + Phase 8 GO/NO-GO per D-12 (TST-01 3/3, TST-02, TST-03, TST-05)

### Phase 8: Zero-Downtime Deploy

**Goal**: Final system deployed to production (aim-hermes container) without interrupting any active presale
**Mode:** mvp
**Depends on**: Phase 7
**Requirements**: DPL-01, DPL-02, DPL-03, DPL-04, DPL-05
**Success Criteria** (what must be TRUE):

  1. Deploy via docker cp + gateway restart (no image rebuild) completes successfully
  2. No presale interrupted during deploy — zero downtime verified (no in-flight request fails)
  3. Health check (/health) returns 200 after deploy
  4. Backup created locally and on server (hermes-backup-YYYYMMDD/) before deploy — contains SOUL.md, SKILL.md, config.yaml, keys, memory
  5. Rollback plan tested: can revert to previous SOUL/SKILL in under 5 minutes if a presale breaks after deploy

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Research & Diagnosis | 4/4 | Complete | 2026-06-23 |
| 2. 3-Pass Orchestrator + Coverage Checklist | 3/3 | Complete | 2026-06-23 |
| 3. Instagram Integration | 4/6 | In Progress|  |
| 4. New Sections & Data Depth | 8/8 | Complete   | 2026-06-24 |
| 5. Deep Interpretation | 3/3 | Complete   | 2026-06-24 |
| 6. Documentation Sync | 3/3 | Complete   | 2026-06-24 |
| 7. Test on 3 Niches | 2/4 | In Progress|  |
| 8. Zero-Downtime Deploy | 0/TBD | Not started | - |
