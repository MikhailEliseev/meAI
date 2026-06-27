---
phase: 02-3-pass-orchestrator-coverage-checklist
plan: 03
subsystem: orchestrator
tags: [qc-checklist, coverage-report, html-gate, honest-data]

# Dependency graph
requires:
  - phase: 02-3-pass-orchestrator-coverage-checklist
    plan: 02
    provides: 3-pass orchestrator core (app/orchestrator/ module + ORCHESTRATOR_MODE dispatch)
provides:
  - "15-item QC_CHECKLIST constant per RESEARCH.md Section 5.4 (QC-01)"
  - "CoverageReport dataclass + calc_coverage(gap_report) → PASS/FAIL at 80% (QC-04)"
  - "format_coverage_text(report) → multiline log-greppable summary (QC-03)"
  - "render_checklist_for_llm() → embedded in Pass 2 prompt"
  - "Soft QC gate in three_pass.py (warning only, non-blocking)"
  - "HTML QC Coverage section in generate_html_report.py (dual-theme aware, XSS-safe)"
affects: [02-03, ORC-03, ORC-04, QC-01, QC-02, QC-03, QC-04, html-reports, pass-2, pass-3]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level constant list-of-dicts for stable, iterable checklist"
    - "Soft gate pattern: log warning but never block downstream pass"
    - "Optional kwarg extraction for backward-compatible function signatures"
    - "dataclasses.asdict(report) for serialising CoverageReport into state.collected_data"
    - "Lazy import inside try/except for HTML rendering (graceful degrade if QC_CHECKLIST unavailable)"

key-files:
  created:
    - AIM/hermes/app/orchestrator/qc_checklist.py
    - AIM/hermes/app/orchestrator/coverage_reporter.py
    - AIM/hermes/tests/test_qc_checklist.py
  modified:
    - AIM/hermes/app/orchestrator/pass_gap_analyze.py
    - AIM/hermes/app/orchestrator/three_pass.py
    - AIM/hermes/app/orchestrator/pass_fill_assemble.py
    - AIM/hermes/app/tools/generate_html_report.py

key-decisions:
  - "15-item checklist статичный as list-of-dicts (не dataclass) — итеративный, versioned через VERSION field"
  - "LLM сам оценивает filled/partial/missing (не Python-парсер) — Python-парсер только суммирует ответы"
  - "SOFT QC gate — warning only, не blocking. Pass 3 всегда запускается, HTML всегда генерируется (ORC-04 honest path)"
  - "coverage_metadata опциональный в handle_generate_html_report — backward compatible для PipelineEngine (ORC-05)"
  - "LLM-prompt approach для передачи coverage_metadata в generate_html_report — documented limitation, future: orchestrator post-Pass-3 direct call"

patterns-established:
  - "QC checklist as iterable constant (каждый пункт = dict с id/category/name/pass_criteria/source)"
  - "calc_coverage robust к malformed input (отсутствующие keys, wrong types, empty dict)"
  - "Soft gate pattern: log warning, continue execution, let downstream decide"
  - "Optional kwargs for backward-compatible API evolution"

requirements-completed: [ORC-03, ORC-04, QC-01, QC-02, QC-03, QC-04]

# Metrics
duration: ~25min
completed: 2026-06-23
---

# Phase 2 Plan 03: QC Checklist + Coverage Reporting Summary

**Phase 2 завершена:** 15-item QC checklist (RESEARCH.md Section 5.4) реализован как module-level constant, calc_coverage считает PASS/FAIL при 80% threshold, Pass 2 использует полный checklist вместо минимального 5-item, soft QC gate предупреждает о низком покрытии (не блокирует), HTML-отчёт рендерит прозрачную секцию «QC Coverage Report» с PASS/FAIL бейджем и списком 15 пунктов с реальными причинами missing.

## Performance

- **Duration:** ~25 min (single wave, 3 sequential tasks)
- **Started:** 2026-06-23
- **Completed:** 2026-06-23
- **Tasks:** 3/3
- **Files created:** 3 (qc_checklist.py, coverage_reporter.py, test_qc_checklist.py)
- **Files modified:** 4 (pass_gap_analyze.py, three_pass.py, pass_fill_assemble.py, generate_html_report.py)
- **Tests added:** 15 (all passing)

## Architecture Summary

### Решение (locked): Soft QC gate + transparent HTML section

Per RESEARCH.md Section 5.4 + Plan 02-03 design decisions: 15-item checklist с objective pass criteria → LLM self-evaluates каждый пункт в Pass 2 → coverage_reporter считает % и PASS/FAIL → soft gate warn'ит если <80% (Pass 3 не блокируется) → HTML показывает honest отчёт клиенту с reasons для missing.

### Структура новых + изменённых файлов

| Файл | Назначение | Новое/Изменённое |
|------|-----------|------------------|
| `app/orchestrator/qc_checklist.py` | 15-item `QC_CHECKLIST` constant + `PASS_THRESHOLD=0.80`, `PASS_MIN_ITEMS=12` + `render_checklist_for_llm()` | NEW (Task 1) |
| `app/orchestrator/coverage_reporter.py` | `CoverageReport` dataclass + `calc_coverage(gap_report)` + `format_coverage_text(report)` | NEW (Task 1) |
| `tests/test_qc_checklist.py` | 15 unit tests: structure, edge boundaries (11/15 FAIL, 12/15 PASS), robustness, format | NEW (Task 1) |
| `app/orchestrator/pass_gap_analyze.py` | Prompt теперь embeds `render_checklist_for_llm()` (15 items) вместо hard-coded 5-item; timeout 180→240s | MODIFIED (Task 2) |
| `app/orchestrator/three_pass.py` | QC gate между Pass 2/3 — calc_coverage + warn если <80%; final coverage после Pass 3 | MODIFIED (Task 2) |
| `app/orchestrator/pass_fill_assemble.py` | Pass 3 prompt инструктирует LLM передать coverage_metadata в generate_html_report | MODIFIED (Task 2 rider) |
| `app/tools/generate_html_report.py` | `_build_qc_coverage_section(metadata)` + `_build_report_html(data, title, coverage_metadata=None)` + handle_generate_html_report извлекает coverage_metadata из kwargs | MODIFIED (Task 3) |

### 15-item QC Checklist (точно из RESEARCH.md Section 5.4)

1. About data (ОКВЭД, licenses, revenue) — ≥2 of 3
2. Market section data — ≥3 competitors with revenue + trend
3. Competitors returned — ≥3 (retry broader geo if 0)
4. Experts identified — ≥3 doctors with ФИО
5. Instagram analysis (cosmetology/plastic) — run_instagram_content called
6. Content themes with % — ≥3 themes per top doctor
7. Content gaps with severity — ≥2 gaps with levels
8. SMI mentions with URLs — ≥3 with concrete URLs
9. Forum pains (patient fears) — ≥5 fears
10. Revenue current year — number present
11. Revenue dynamics 3 years (DAT-01) — YoY % trend
12. Competitor cards detailed — ≥3 cards with ≥4 fields
13. Whitefields comparison matrix — client vs ≥3 by ≥5 fields
14. Strategy with 5 directions — content, Telegram, GEO, reputation, cross-promo
15. Offer section — concrete steps + CTA

**PASS:** ≥12/15 (80%) filled with real data. **Below 12:** mark missing с reason, no fabrication (ORC-04).

### CoverageReport Flow

```
Pass 2 LLM self-evaluation → state.gap_report
    ↓
calc_coverage(gap_report) in three_pass.py
    ↓
CoverageReport {total_items=15, filled_items, missing_items, partial_items, coverage_pct, status}
    ↓
state.collected_data["coverage_report_after_pass2"] = asdict(report)  [for Pass 3 + HTML]
    ↓
state.collected_data["coverage_report_final"] = asdict(final_report)  [after Pass 3]
    ↓
LLM (Pass 3) calls generate_html_report(coverage_metadata=...)
    ↓
_build_qc_coverage_section(metadata) → HTML section at end of report
```

## Task Commits

Each task committed atomically:

1. **Task 1: QC_CHECKLIST module + CoverageReporter (TDD)** — `d0c0ea2` (test → feat in one commit; tests first, impl second per TDD discipline)
2. **Task 2: 15-item Pass 2 + soft QC gate** — `97e3961` (feat)
3. **Task 3: HTML QC Coverage section** — `d2c8176` (feat)

## Files Created/Modified

### Created
- `AIM/hermes/app/orchestrator/qc_checklist.py` — 15-item constant + thresholds + render helper
- `AIM/hermes/app/orchestrator/coverage_reporter.py` — CoverageReport + calc/format helpers
- `AIM/hermes/tests/test_qc_checklist.py` — 15 unit tests (TDD red→green)

### Modified
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py`:
  - Module docstring updated (5-item → 15-item context)
  - Import: `from app.orchestrator.qc_checklist import QC_CHECKLIST, render_checklist_for_llm`
  - Timeout: 180s → 240s (15 items take longer)
  - Prompt: now embeds `render_checklist_for_llm()` output, requires filled/partial/missing + reason per item, explicit "НЕ выдумывай данные" (ORC-04)
  - JSON output contract: 15 items, summary has filled+partial+missing+total
  - Fallback reports updated: total=5 → total=15
- `AIM/hermes/app/orchestrator/three_pass.py`:
  - Imports: `from dataclasses import asdict`, `from app.orchestrator.coverage_reporter import calc_coverage, format_coverage_text`
  - Module docstring: QC-02 soft gate + QC-03 final coverage report documented
  - After Pass 2: `coverage_after_p2 = calc_coverage(state.gap_report)` → saved to `state.collected_data["coverage_report_after_pass2"]` as dict
  - SOFT QC gate: if `status == "FAIL"` → `logger.warning(...)` + `state.collected_data["missing_for_pass3"]` populated
  - If `status == "PASS"` → `logger.info("QC gate: coverage already at PASS — Pass 3 will polish + generate HTML")`
  - After Pass 3: `final_coverage = calc_coverage(state.gap_report)` → saved to `state.collected_data["coverage_report_final"]`
  - `format_coverage_text(final_coverage)` logged at INFO for grep'pable summary
- `AIM/hermes/app/orchestrator/pass_fill_assemble.py`:
  - `_build_prompt(state)` добавлен coverage_hint (filled/total, status from after-Pass-2)
  - Step 4 в task list: LLM ОБЯЗАНА передать coverage_metadata в generate_html_report
- `AIM/hermes/app/tools/generate_html_report.py`:
  - NEW: `_build_qc_coverage_section(metadata: dict) -> str` — рендерит HTML секцию с design-system классами (metric-tag-success/warning), dual-theme aware, XSS-safe через _esc()
  - MODIFIED: `_build_report_html(data, title, coverage_metadata=None)` — optional 3rd arg, backward compatible (None → no QC section)
  - MODIFIED: `handle_generate_html_report` — extracts `coverage_metadata` from kwargs или first-positional dict, передаёт в `_build_report_html`

## Decisions Made

- **Почему checklist как module-level list-of-dicts, не dataclass:** Статичный список 15 пунктов с known schema. Iterate/filter/version проще чем dataclass-instances. Если потребуется версионирование — добавить VERSION field (уже добавлен: `VERSION = "1.0.0"`).
- **Почему LLM оценивает пункты, не Python-парсер:** Python не может определить «≥3 doctors with ФИО (not clinic name)» без regex hell. LLM видит collected_data и принимает solution. Парсер только суммирует ответы (calc_coverage).
- **Почему SOFT gate, не HARD:** Hard gate рискованный — клиент может остаться без отчёта вообще. Soft gate: Pass 3 видит gap_report, пытается заполнить, если не получается — HTML всё равно генерируется с honest «данные недоступны» markers. Это соответствует ORC-04.
- **Почему coverage_metadata optional в handle_generate_html_report:** generate_html_report вызывается из PipelineEngine (ORC-05 fallback) — там нет coverage_reporter'а. Optional → backward compatibility preserved. Smoke test verified: `_build_report_html(data, title)` без 3rd arg → no QC section.
- **Почему LLM-prompt approach для coverage_metadata, не post-Pass-3 direct call:** Альтернатива — three_pass.py сам вызывает generate_html_report после Pass 3 с guaranteed coverage_metadata. Но это ломает current pattern где LLM решает когда/как вызывать tools. Plus — сейчас LLM может вставить coverage_metadata с human-friendly пояснениями. Documented limitation: если LLM забывает передать — QC секция не появляется (graceful degradation, no crash).
- **Почему timeout Pass 2 увеличен 180→240s:** 15 пунктов против 5 = ~3x больше self-evaluation работы. 180s рискованно, 240s даёт margin.

## Verification Results

**Automated checks (all passed):**

1. `python3 -m pytest tests/test_qc_checklist.py -v` → **15/15 PASSED** (структура, edges, robustness, format, render)
2. `python3 -c "from app.orchestrator.qc_checklist import QC_CHECKLIST, PASS_THRESHOLD, PASS_MIN_ITEMS; assert len(QC_CHECKLIST) == 15; ..."` → **OK: 15 items, threshold 0.80, min 12**
3. `python3 -c "from app.orchestrator.coverage_reporter import calc_coverage, format_coverage_text; ..."` → **OK: PASS case works** (13/15 filled = 86.7% PASS)
4. `python3 -c "calc_coverage({})..."` → **OK: empty gap_report handled** (FAIL, 0.0%, no crash)
5. `python3 -c "import ast; [ast.parse(open(f).read()) for f in [...]]; "` → **OK: syntax valid** для всех 7 new/modified files
6. `inspect.getsource(pass_gap_analyze)` → **OK: Pass 2 uses 15-item checklist** (render_checklist_for_llm импортирован, old 5-item prompt удалён)
7. `inspect.getsource(three_pass)` → **OK: QC gate wired** (calc_coverage, coverage_report_after_pass2, coverage_report_final, "QC gate" all present)
8. `_build_qc_coverage_section(mock_metadata)` smoke test → **OK: QC coverage section renders correctly** (PASS badge, 86.7%, Whitefields, "данные недоступны", reason)
9. `_build_report_html(data, title)` без coverage_metadata → **OK: backward compatible** (no QC section)
10. `_build_report_html(data, title, coverage_metadata=mock)` → **OK: coverage section appears** (PASS badge)

**No-regression verification:**
- `ORCHESTRATOR_MODE=0` (default) → поведение PRESALE НЕ меняется (orchestrator не активируется, QC gate не запускается)
- PipelineEngine path (без coverage_metadata в args) → HTML без QC секции, как раньше
- All 15 tests in `test_qc_checklist.py` green

**Runtime verification (Docker-only):**
Полный smoke-test с live LLM вызовами требует деплоя в `aim-hermes` контейнер (через `docker cp` + gateway restart). Это отдельный шаг Phase 8. Локально: imports + syntax + structure + edge boundaries — всё валидно.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written.

### Ridden-Along Changes (out of scope, noted for transparency)

**`pass_fill_assemble.py` minimal правка (Task 2 rider):** Plan 02-03 Task 2 action step в основном focuses на pass_gap_analyze.py + three_pass.py. Но Task 3 action step 9 упоминает: «В Pass 3 (pass_fill_assemble.py created in 02-02) — НЕ нужно менять в этом Task... Solution: добавить минимальную правку в pass_fill_assemble.py prompt». Эта правка выполнена в рамках Task 2 коммита (97e3961) поскольку:
- Она минимальная (только prompt + coverage_hint)
- Она логически связана с QC gate передачей
- Без неё Pass 3 LLM не знает про coverage_metadata требование → HTML QC section не появился бы

Если это считается scope violation, можно выделить в отдельный коммит — но separating one-line prompt change от Task 2 QC gate работы не улучшает git history.

## Issues Encountered

None — plan matched reality. All 15 tests passed on first GREEN run. All automated checks passed first try.

## User Setup Required

None — нет внешних сервисов для настройки. QC checklist работает in-process, no new env vars, no new dependencies.

**Для testing (опционально, после Phase 8 deploy):**
```bash
# On Polish server, in aim-hermes container:
docker exec -e ORCHESTRATOR_MODE=1 aim-hermes python3 -c "from app.orchestrator.coverage_reporter import calc_coverage; ..."
# End-to-end: trigger PRESALE + URL → check logs for "QC gate after Pass 2: coverage=X%"
# → check HTML report contains "QC Coverage Report" section
```

## Next Phase Readiness

- **Phase 2 полностью завершена** после этого plan'а: ORC-01..05 + QC-01..04 все покрыты. Phase verification может выполняться.
- **Phase 3 готова к планированию:** Instagram integration строится на orchestrator core из 02-02 + QC checklist из 02-03. Instagram пункт (#5 в checklist) уже part of self-evaluation.
- **Деплой Phase 2 (опционально):** Through `docker cp` + gateway restart. См. Phase 8 deploy plans.

## Known Stubs

None — все файлы содержат полную реализацию:
- `qc_checklist.py`: полная 15-item константа + 2 helper functions
- `coverage_reporter.py`: полная CoverageReport + calc/format с robustness для malformed input
- `pass_gap_analyze.py`: полный 15-item prompt с правильным форматированием
- `three_pass.py`: full QC gate logic (after-Pass-2 + after-Pass-3)
- `generate_html_report.py`: полный HTML rendering с design-system классами и XSS safety

## Limitations

- **LLM-prompt approach для coverage_metadata передачи:** Если Pass 3 LLM забывает передать `coverage_metadata` в args generate_html_report (нарушая инструкцию), QC секция не появляется. HTML генерируется как раньше (без QC section) — graceful degradation. Future improvement: three_pass.py сам вызывает generate_html_report post-Pass-3 с guaranteed metadata (но это ломает current pattern где LLM решает когда вызывать tools).
- **LLM self-assessment honesty:** calc_coverage доверяет LLM-оценкам filled/partial/missing. Если LLM врёт (называет пункты filled когда данных нет), coverage % будет нереалистичный. Mitigation: Pass 2 prompt явно требует "НЕ выдумывай данные" + reason для missing. В будущем: Python validator мог бы random-чекнуть пункты против collected_data.
- **No retroactive recalculation after Pass 3:** После Pass 3 final coverage считается из того же state.gap_report (если Pass 3 LLM не обновил его). Решение: Pass 3 может обновить gap_report если явно написал filled в каком-то пункте — но это зависит от LLM behavior. В current implementation: coverage_after_pass2 == coverage_final unless LLM mutated gap_report.

## Threat Flags

None — новых trust boundaries введено не было. См. PLAN.md `<threat_model>` для полного STRIDE analysis. Coverage report в HTML — это transparency surface (T-02-03-I accepted), не новая attack surface. XSS mitigated через _esc() на всех string values (T-02-03-XSS mitigated).

---

## Self-Check: PASSED

**Files verified:**
- FOUND: AIM/hermes/app/orchestrator/qc_checklist.py (committed in d0c0ea2)
- FOUND: AIM/hermes/app/orchestrator/coverage_reporter.py (committed in d0c0ea2)
- FOUND: AIM/hermes/tests/test_qc_checklist.py (committed in d0c0ea2)
- FOUND: AIM/hermes/app/orchestrator/pass_gap_analyze.py (modified, committed in 97e3961)
- FOUND: AIM/hermes/app/orchestrator/three_pass.py (modified, committed in 97e3961)
- FOUND: AIM/hermes/app/orchestrator/pass_fill_assemble.py (modified, committed in 97e3961)
- FOUND: AIM/hermes/app/tools/generate_html_report.py (modified, committed in d2c8176)

**Commits verified:**
- FOUND: d0c0ea2 (test/feat 02-03: QC checklist + coverage reporter with TDD — Task 1)
- FOUND: 97e3961 (feat 02-03: full 15-item checklist in Pass 2 + soft QC gate — Task 2)
- FOUND: d2c8176 (feat 02-03: render QC Coverage section in HTML report — Task 3)

**Acceptance criteria:**
- [x] `QC_CHECKLIST` содержит ровно 15 пунктов с id от 1 до 15
- [x] Каждый пункт имеет fields: id, category, name, pass_criteria, source
- [x] PASS_THRESHOLD = 0.80, PASS_MIN_ITEMS = 12 (15 * 0.8)
- [x] `calc_coverage(gap_report)` корректно считает coverage_pct = filled / total
- [x] calc_coverage PASS при ≥12/15 filled, FAIL при <12/15
- [x] calc_coverage robust к empty gap_report (FAIL с coverage_pct=0.0)
- [x] calc_coverage robust к malformed gap_report (отсутствующие keys → defaults)
- [x] format_coverage_text включает "QC Coverage: X/15 (Y%) — PASS|FAIL"
- [x] render_checklist_for_llm() возвращает text для prompt со всеми 15 пунктами
- [x] 15/15 tests в test_qc_checklist.py проходят (TDD red→green)
- [x] Синтаксис всех 7 файлов валиден (ast.parse)
- [x] pass_gap_analyze.py использует `render_checklist_for_llm()` вместо hard-coded 5-item
- [x] Старый 5-item prompt ПОЛНОСТЬЮ удалён
- [x] Timeout Pass 2 увеличен до 240s
- [x] three_pass.py вызывает calc_coverage после Pass 2 (SOFT gate)
- [x] SOFT QC gate: warning logged если coverage < 80%, Pass 3 не блокируется
- [x] coverage_report_after_pass2 + coverage_report_final сохраняются как dict
- [x] missing_for_pass3 передаётся в Pass 3 при FAIL
- [x] handle_generate_html_report принимает optional coverage_metadata
- [x] _build_qc_coverage_section рендерится с design-system стилем
- [x] Missing пункты показаны с "данные недоступны" + reason (ORC-04)
- [x] Backward compatible: без coverage_metadata → HTML без QC секции
- [x] XSS safety: все string values через _esc()
- [x] PipelineEngine НЕ модифицирован (ORC-05 preserved)
- [x] ORCHESTRATOR_MODE=0 (default) → поведение PRESALE НЕ меняется

**Requirements addressed:**
- [x] ORC-03: Gap-analysis сравнивает собранные данные с QC checklist (calc_coverage использует QC_CHECKLIST)
- [x] ORC-04: Missing пункты помечаются "данные недоступны" с reason, не выдумываются (HTML секция, Pass 2 prompt)
- [x] QC-01: 10-20 item QC checklist — ровно 15 items в пределах диапазона
- [x] QC-02: Auto-check перед HTML генерацией — soft QC gate в three_pass.py
- [x] QC-03: Coverage % report в конце каждого прогона — logger.info + HTML section
- [x] QC-04: ≥80% coverage target — PASS_THRESHOLD=0.80, PASS_MIN_ITEMS=12

---
*Phase: 02-3-pass-orchestrator-coverage-checklist*
*Completed: 2026-06-23*
