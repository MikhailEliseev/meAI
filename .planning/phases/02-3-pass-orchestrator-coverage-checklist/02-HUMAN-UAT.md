---
status: partial
phase: 02-3-pass-orchestrator-coverage-checklist
source: [02-VERIFICATION.md]
started: 2026-06-23T14:30:00Z
updated: 2026-06-23T14:30:00Z
---

## Current Test

[awaiting human testing — Phase 8 deploy]

## Tests

### 1. End-to-end runtime activation (ORC-01, ORC-02)
expected: С `ORCHESTRATOR_MODE=1` в docker-compose.yml и при PRESALE+URL → логи показывают три последовательных pass-перехода: "Pass 1 (Collect) starting" → "Pass 2 (Gap-analyze) starting" → "Pass 3 (Fill+Assemble) starting" → "Orchestrator: 3-pass cycle complete"
result: [pending]

### 2. Pass 2 LLM JSON output parsing (ORC-03, QC-02)
expected: Pass 2 LLM возвращает strict JSON вида `{"items":[...], "summary":{"filled":N,"total":15}}` — парсинг через `re.search(r"\{.*\}", raw, re.DOTALL)` succeeds без fallback к `{"parse_error": "..."}`
result: [pending]

### 3. Real coverage ≥80% on reference clinic (QC-04)
expected: На эталонной клинике (например iphk.ru из Phase 1 reference) Pass 2 отчёт о покрытии составляет ≥12/15 пунктов (≥80%) — QC gate проходит без предупреждений
result: [pending]

### 4. ORCHESTRATOR_MODE=0 no-regression (ORC-05)
expected: При `ORCHESTRATOR_MODE=0` (или unset) производство работает идентично pre-Phase-2: пресейл-поток через один `AIAgent.run_conversation()`, PipelineEngine доступен как fallback
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
