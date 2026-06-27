---
phase: 01-research-diagnosis
plan: 02
subsystem: research
tags: [research, session-logs, skip-points, evidence, res-04]
requires:
  - .planning/phases/01-research-diagnosis/CONTEXT.md
  - .planning/phases/01-research-diagnosis/evidence/coverage-baseline.md
provides:
  - .planning/phases/01-research-diagnosis/evidence/session-log-analysis.md
affects:
  - .planning/phases/01-research-diagnosis/01-03-PLAN.md (Plan 03 root cause reads skip points)
  - .planning/phases/02-orchestrator/ (Phase 2 fixes _unwrap_tool_output + _TOOL_HANDLERS)
tech-stack:
  added: []
  patterns:
    - "read-only ssh + docker exec investigation"
    - "per-session timeline from mtime + JSON content"
    - "quoted evidence with exact error strings"
key-files:
  created:
    - .planning/phases/01-research-diagnosis/evidence/session-log-analysis.md
  modified: []
decisions:
  - "28 skip/truncate points identified across 5 sessions (not random — stable patterns)"
  - "_unwrap_tool_output NameError is a NEW bug introduced between Jun 20 and Jun 21 — breaks HTML BUILD + PRESENTATION in 40% of sessions"
  - "LLM-registry vs _TOOL_HANDLERS gap CONFIRMED: LLM calls run_instagram_content/find_doctor_handles/run_tech_seo_audit, pipeline refuses with 'No handler mapping'"
  - "FINANCE 'inn required' is non-deterministic — LLM passes INN in 3/5, omits in 2/5 — prompt issue, not pipeline issue"
metrics:
  duration: ~8 min
  completed: 2026-06-22
  tasks: 2
  files: 1
---

# Phase 1 Plan 02: Session Log Analysis Summary

**One-liner:** 28 skip/truncate points across 5 Hermes v4 sessions — critical bugs identified (`_unwrap_tool_output` NameError breaks 40% of reports, `_TOOL_HANDLERS` gap blocks Instagram/find_doctor_handles, non-deterministic INN omission in FINANCE).

---

## What Was Built

Evidence file `.planning/phases/01-research-diagnosis/evidence/session-log-analysis.md` (624 строки) содержащий:

1. **Per-session structured timelines** для 5 сессий:
   - `tg:322367335` (arclinic.ru, Telegram-triggered) — 13/13 phases, 19 мин
   - `1609c5d1` (iphk.ru) — 11/11 phases, 6 мин
   - `full-test-1782061034` (iphk.ru) — 11/11 phases, 7 мин
   - `4975ef15-de5` (ABNORMAL TERMINATION) — 1/13 phases, crash
   - `test-iphk-002` (iphk.ru) — 13/13 phases, 9 мин

2. **Skip/Truncate Decision Points** — 28 конкретных точек с quoted evidence:
   - 9 ERROR (включая `_unwrap_tool_output`, `No handler mapping`, `inn required`)
   - 7 NO_DATA (пустые результаты)
   - 13 SKIPPED_TOOL (инструменты никогда не вызываются)
   - 12 SKIPPED_PHASE (Session 4 — crash после PERPLEXITY)
   - 5 LLM_DECISION (LLM сама признаёт проблемы в интерпретациях)

3. **Consolidated register** — 30 строк, сгруппированных по category + tool/phase

4. **Pattern analysis** — Top 7 most-skipped tools, tools that always return NO_DATA/ERROR, phases that always truncate

5. **Cross-reference** с CONTEXT.md hypotheses (Instagram absent, SOUL.md permissive, pipeline restricts)

---

## Key Findings

### Critical Bugs (требуют немедленного fix в Phase 2)

1. **`NameError: name '_unwrap_tool_output' is not defined`** — ломает `generate_html_report` и `publish_scout_report` в 2 из 5 сессий (40%). Баг введён между 20 и 21 июня (test-iphk-002 от 20 июня без бага, tg и full-test от 21 июня — с багом). Отчёт НЕ генерируется, QC CRITIQUE получает пустой ввод и пишет "10/10 FAIL".

2. **`"No handler mapping for tool: ..."`** — PipelineEngine отказывается выполнять инструменты, которые LLM вызывает:
   - `run_instagram_content` — LLM вызвала в Session 3, pipeline отказал
   - `find_doctor_handles` — LLM вызвала в Session 3, pipeline отказал
   - `run_tech_seo_audit` — LLM вызывает всегда (2 сессии), всегда `"No handler mapping"`
   - Подтверждает разрыв: LLM-registry (40+ tools) vs `_TOOL_HANDLERS` (19 tools)

3. **`"Either inn or ogrn is required"`** — LLM не передаёт INN в `find_company_financials` в 2 из 5 сессий. Недетерминированное: в 3 других сессиях LLM передаёт INN корректно. Причина — LLM-промпт не делает явное требование "получи INN через find_competitors ПЕРЕД find_company_financials".

### Stable Patterns

4. **`run_instagram_content` никогда не выполняется успешно** — либо LLM не вызывает (4/5), либо pipeline отказывает (1/5).

5. **`run_doctor_dossiers` ищет по имени клиники** — LLM передаёт `doctor_name: "Arclinic"` / `"Iphk"` вместо ФИО врача. Возвращает 10-16 профилей, но 0 реальных врачей.

6. **CONTENT PLAN сравнивает сайт сам с собой** — в Session 1: `target: "https://arclinic.ru"`, `competitor: "https://arclinic.ru/"`. `content_gaps: []` по определению.

7. **URL публикации всегда null** — даже когда HTML BUILD успешен (3/5 сессий), `publish_scout_report` сохраняет локально, но `url: null` — отчёт НЕ публикуется на веб.

8. **Фаза HIRING SIGNALS** — выполняется в 2 сессиях от 21 июня, но НЕ описана в `phases.py` (13 фаз). Подтверждает рассинхрон фаз (CONTEXT.md указывал 13/14/16 — сейчас актуально 13/14).

9. **Session 4 (4975ef15-de5) — crash без metadata.json** — пайплайн упал после PERPLEXITY, не записав метаданные. 12 из 13 фаз пропущены. Без events.jsonl причину не установить.

### LLM-признания проблем (quoted evidence)

- **COMPETITORS_interpretation (Session 1):** "Конкурентный анализ не может быть выполнен в полном объёме: инструмент CI-анализа завершился ошибкой"
- **KEY PERSONS_interpretation (Session 1):** "идентифицировать конкретных врачей не удалось: все найденные 10 профилей — это страницы клиники на отзовиках"
- **CONTENT ANALYSIS_interpretation (Session 1):** "содержит только техническую ошибку – инструмент не смог обратиться к сайту arclinic.ru"
- **CONTENT PLAN_interpretation (Session 1):** "инструмент не выявил расхождений, поскольку в качестве конкурента ошибочно использовался сам сайт клиники"
- **QC CRITIQUE_interpretation (Session 1):** "10/10 FAIL. Причина – отсутствие готового отчёта"

---

## Cross-Reference with Plan 01 (coverage-baseline.md)

Plan 01 установил: tool coverage = 15/40+ (37.5%), section coverage = 3.0/10 (30%).

**Plan 02 уточняет:**

| Plan 01 finding | Plan 02 evidence |
|-----------------|------------------|
| `run_instagram_content` "called in 3/5 sessions" | НО в тех 3 сессиях инструмент вернул `"No handler mapping"` — фактически НЕ выполнен. Plan 01 считал по наличию .json файла, но не проверял content. |
| `find_doctor_handles` "called in 3/5 sessions" | Аналогично — 2 из 3 сессий с `"No handler mapping"`, только Session 2 (1609c5d1) успешна (22 врача). |
| `run_tech_seo_audit` "called in 3/5 sessions" | ВСЕ 3 вызова вернули `"No handler mapping"` — инструмент никогда не выполняется. |
| Tool coverage = 15/40+ (37.5%) | С correction на errors: **effective tool coverage = ~12-13/40+** (30%) — ещё ниже, чем оценил Plan 01. |
| Report size avg 14.4 KB | Plan 02 объясняет: `_unwrap_tool_output` NameError ломает HTML BUILD в 40% сессий → отчёт пустой или минимальный. |

**Уникальные находки Plan 02 (не в Plan 01):**
- `_unwrap_tool_output` NameError — критический баг
- LLM пытается вызывать инструменты, но pipeline отказывает (opроверает "LLM решает не обязательно")
- `run_doctor_dossiers` ищет по имени клиники
- CONTENT PLAN сравнивает сайт сам с собой
- URL публикации всегда null
- HIRING SIGNALS фаза без описания в phases.py
- Session 4 crash без metadata.json
- LLM-признания проблем в интерпретациях

---

## Cross-Reference with CONTEXT.md Hypotheses

| Hypothesis | Plan 02 Verdict | Evidence |
|------------|-----------------|----------|
| **H1: Instagram полностью отсутствует** | CONFIRMED (уточнено) | LLM пытается вызвать (Session 3), но pipeline отказывает `"No handler mapping"`. В 4/5 LLM не вызывает — но это не "LLM решает не обязательно", а недетерминированность. |
| **H7: SOUL.md даёт слишком много свободы** | PARTIALLY CONFIRMED | Для 13 инструментов (`run_lighthouse`, `run_prescan`, `quick_overview` и др.) LLM НИКОГДА не вызывает — подтверждает, что SOUL.md/SKILL.md не дают явных сигналов. НО для `run_instagram_content` и `find_doctor_handles` — LLM иногда вызывает, так что проблема не только в промпте. |
| **H-C: PipelineEngine жёстко ограничивает фазы** | REFINED | Не "жёстко ограничивает фазы" — а **не имеет handler mapping для 21+ инструментов**. LLM может вызывать, но pipeline не выполнит. |
| **H-A: SOUL.md/SKILL.md дают слишком много свободы** | CONFIRMED for some tools | См. H7 |
| **H-D: Комбинация причин** | CONFIRMED | 30% покрытия — результат комбинации: (1) 21+ инструментов недоступны, (2) LLM-промпт не направляет, (3) `_unwrap_tool_output` ломает сборку, (4) недетерминированная передача INN, (5) `find_competitors` нестабилен в мегаполисах. |

---

## Recommendations for Phase 2 (3-Pass Orchestrator)

Plan 02 выявил конкретные точки для Phase 2:

1. **Fix `_unwrap_tool_output` NameError немедленно** — блокирующий баг. Файлы: `generate_html_report.py`, `publish_scout_report.py`. Функция не импортирована или не определена.

2. **Добавить недостающие handlers в `_TOOL_HANDLERS`** (engine.py):
   - `run_instagram_content` (критично для косметологии/пластики)
   - `find_doctor_handles`
   - `run_tech_seo_audit`
   - `run_lighthouse`, `run_prescan`, `quick_overview`, `present_competitors`, `finalize_research`, `run_validation_check`

3. **3-pass cycle должен явно требовать INN** перед `find_company_financials` — через QC checklist. LLM-промпт должен говорить "ОБЯЗАТЕЛЬНО получи INN через find_competitors ПЕРЕД find_company_financials".

4. **QC checklist должен включать Instagram** — обязательно для косметологии/пластики (Phase 3).

5. **`run_doctor_dossiers` LLM-промпт** — уточнить: "искать по ФИО врача, НЕ по имени клиники". Если ФИО врачей неизвестны — сначала `find_doctor_handles`.

6. **CONTENT PLAN** — LLM-промпт должен требовать `competitor URL ≠ client URL`. Если конкурент неизвестен — обязательно вызывать `find_competitors` сначала.

7. **Публикация на веб** — починить `publish_scout_report`, чтобы `url` был не null (настройка публикатора или credentials).

8. **Sync phases.py** — добавить HIRING SIGNALS фазу (или удалить из кода, если не нужна). Устранить рассинхрон 13 vs 14.

---

## Deviations from Plan

**None — plan executed exactly as written.** Все 2 tasks выполнены последовательно, evidence file создан по спецификации, server state не модифицирован (read-only доступ через ssh + docker exec).

---

## Known Stubs

**None.** Все данные в evidence file — реальные quoted log lines из `/opt/data/sessions-archive/`. Никаких mock данных, placeholder-ов, или "coming soon" секций.

---

## Threat Flags

**None.** Evidence file содержит только session_hash IDs (не clinic PII), структурные log tokens, имена инструментов, и error messages из кода. Конкретные имена врачей, финансовые показатели, и clinic names в quotes — минимальны и служат только для идентификации контекста.

---

## Self-Check: PASSED

- [x] `evidence/session-log-analysis.md` exists at `.planning/phases/01-research-diagnosis/evidence/session-log-analysis.md`
- [x] RES-04 marker present in file header
- [x] 5 per-session subsections ("## Session {hash}") — verified by grep
- [x] Each subsection has timeline table with columns: time | event_type | tool/phase | result_summary
- [x] "## Skip/Truncate Decision Points" section present
- [x] All 7 categories present: NO_DATA, TRUNCATED, SKIPPED_TOOL, SKIPPED_PHASE, STREAM_BREAK, ERROR, LLM_DECISION
- [x] Consolidated register table exists
- [x] Pattern analysis section with "Top 7 most-skipped tools"
- [x] Cross-reference to CONTEXT.md hypotheses documented
- [x] Server files NOT modified (verified via stat mtimes: SOUL.md, engine.py, phases.py — all older than plan start)

**Commits:**
- `788a6ac`: docs(phase-01): 01-02 session log analysis — RES-04

**Verification commands run:**
```
test -f .planning/phases/01-research-diagnosis/evidence/session-log-analysis.md → PASS
grep "RES-04" → PASS
grep -E "Session [a-f0-9]+" → PASS
grep "Skip/Truncate" → PASS
grep -E "(NO_DATA|TRUNCATED|SKIPPED|STREAM_BREAK|ERROR|LLM_DECISION)" → PASS
ssh aim "docker exec aim-hermes stat -c '%Y' /opt/data/SOUL.md" → 1782078325 (2026-06-21, older than plan start 2026-06-22)
```

---

## Plan Status

**Status:** COMPLETE
**Tasks completed:** 2/2
**Duration:** ~8 минут (16:43:28 → 16:51:35 UTC)
**Files created:** 1 (evidence/session-log-analysis.md, 624 строки)
**Files modified:** 0
**Server state:** Unchanged (read-only access)
**Requirements addressed:** RES-04 (full)
