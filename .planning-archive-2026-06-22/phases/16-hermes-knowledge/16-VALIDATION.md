---
phase: 16
name: "Hermes Knowledge Training"
date: "2026-05-19"
validation_type: manual-documentation
nyquist_note: >
  This is a documentation phase — the primary artifact is SOUL.md (text file).
  Validation uses grep-based automated checks embedded in PLAN.md <verify> blocks
  plus a mandatory human checkpoint review. No traditional test framework applies.
---

## Validation Architecture

### Why Manual Validation (Not Automated Tests)

This phase produces a **natural language knowledge file** (SOUL.md), not executable code. The correctness criteria are:
1. **Factual accuracy** — every claim in SOUL.md matches reality in the codebase
2. **Completeness** — all 10 knowledge domains (D-01..D-10) are covered
3. **Security** — no secrets, API keys, or credentials leaked

These cannot be validated by pytest — they require grep-based string matching (automated) + human review (manual).

### Validation Layers

| Layer | Method | Coverage | Plan |
|-------|--------|----------|------|
| L1: Automated grep | Shell commands in `<verify>` blocks | 28 checks covering D-01..D-10 | 16-02 Task 1 |
| L2: Security scan | `grep -iE '(sk-|api_key=|token=|secret=)' SOUL.md` | Credential leak detection | 16-02 Task 1 |
| L3: Human review | Checkpoint — read SOUL.md, verify against codebase | Subjective quality, tone, accuracy | 16-02 Task 2 |

### D-01..D-10 Verification Matrix

| Decision | What to verify | Grep check |
|----------|---------------|------------|
| D-01 | Magister architecture | `grep -c 'Magister' SOUL.md` ≥ 4 |
| D-02 | PRESALE/ACTIVE/ADMIN modes | `grep -c 'PRESALE\|ACTIVE\|ADMIN' SOUL.md` ≥ 3 |
| D-03 | WOW-Data 7 blocks | `grep -c 'Блок' SOUL.md` ≥ 7 |
| D-04 | 3 числа principle | `grep -c 'пациент\|срок\|цена\|CPA' SOUL.md` ≥ 4 |
| D-05 | Token Economy | `grep -c 'Tier\|Токен\|Token' SOUL.md` ≥ 3 |
| D-06 | Lead Dossier | `grep -c 'досье\|dossier\|lead_id' SOUL.md` ≥ 3 |
| D-07 | Omni-Channel | `grep -c 'сайт\|Telegram\|Email\|follow-up\|догонял' SOUL.md` ≥ 4 |
| D-08 | Agent Orchestration | `grep -c 'MCP\|tool\|инструмент\|оркестрац' SOUL.md` ≥ 5 |
| D-09 | Russian market | `grep -c 'ФЗ-152\|ЮKassa\|Яндекс\|Директ\|Метрика' SOUL.md` ≥ 5 |
| D-10 | 8 MCP tools | `grep -c 'run_seo_audit\|run_content_analysis\|run_ads_report\|show_project_status\|collect_contact\|show_all_leads\|search_telegram_chats\|send_telegram_message' SOUL.md` ≥ 8 |

### Validation Pass Threshold

- L1: 28/28 grep checks pass (100%)
- L2: 0 secrets found
- L3: Human approves with signature in 16-02-PLAN.md checkpoint

### Nyquist Compliance

Nyquist dimension (Check 8e) is satisfied by the combined L1+L2+L3 validation architecture above. Each check maps to a verifiable assertion. The `[BLOCKING]` checkpoint in 16-02 Task 2 ensures human verification before phase completion.
