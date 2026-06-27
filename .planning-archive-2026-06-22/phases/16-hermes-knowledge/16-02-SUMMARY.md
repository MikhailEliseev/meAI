---
phase: 16-hermes-knowledge
plan: 02
type: execute
subsystem: hermes-knowledge-validation
tags: [hermes, soul, validation, automated-checks]
status: complete
completed: 2026-05-20

requires: [16-01]
provides:
  - "Automated verification of SOUL.md against all 10 knowledge domains (D-01..D-10)"
  - "Cross-reference of subagent names against actual codebase files"
  - "Tool registration schema verification"
  - "Security scan (secrets, ADMIN gating)"
  - "Structural checks (sections, frontmatter, closing)"
affects:
  - "AIM/hermes/skills/aim/SOUL.md — removed 3 deprecated file references (ci_content.py, ci_tech.py, ci_tech_improved.py)"

tech-stack:
  added: []
  patterns:
    - "Grep-based automated verification — 22 checks across 4 layers"
    - "Filesystem cross-reference — every .py name in SOUL.md checked against actual codebase"

key-files:
  created: []
  modified:
    - "AIM/hermes/skills/aim/SOUL.md (line 316: removed ci_tech.py + ci_tech_improved.py; line 404: removed ci_content.py)"

decisions: []

metrics:
  tasks: 1  (Task 2 = human checkpoint, pending Mikhail review)
  files_modified: 1
  lines_changed: 2
  duration: "~10 minutes"
---

# Phase 16 Plan 02: SOUL.md Validation — Task 1 Complete

## Task 1: Automated Verification ✅

All 4 verification steps passed:

### Step 1: Decision Coverage (V-D01..V-D10) — 0 failures
| Check | Description | Result |
|-------|-------------|--------|
| V-D01-a | SEO Magister names | 14 (>=10) ✅ |
| V-D01-b | Content Magister names | 10 (>=8) ✅ |
| V-D01-c | Ads Magister names | 11 (>=6) ✅ |
| V-D01-d | Analytics Magister names | 6 (>=4) ✅ |
| V-D01-e | CI ecosystem | 11 (>=5) ✅ |
| V-D02-a | PRESALE mode | 20 (>=3) ✅ |
| V-D02-b | ACTIVE mode | 22 (>=3) ✅ |
| V-D02-c | ADMIN mode | 30 (>=4) ✅ |
| V-D03 | WOW blocks | 8 (>=5) ✅ |
| V-D04 | 3 numbers | 14 (>=2) ✅ |
| V-D05-a | Token tiers | 28 (>=4) ✅ |
| V-D05-b | Token rules | 6 (>=1) ✅ |
| V-D06 | Lead statuses | 2 (>=1) ✅ |
| V-D07 | Omni-Channel days | 7 (>=3) ✅ |
| V-D08 | Orchestration HTTP | 5 (>=2) ✅ |
| V-D09-a | Russian laws | 7 (>=2) ✅ |
| V-D09-b | Russian platforms | 26 (>=5) ✅ |
| V-D09-c | NOT Western | 5 (>=2) ✅ |
| V-D10-a | 8 tools | All 8 found ✅ |
| V-D10-b | Tool I/O | 16 (>=3) ✅ |

### Step 2: Accuracy vs Codebase — 3 fixes applied
- Removed `ci_content.py` (deprecated, deleted in Phase 17)
- Removed `ci_tech.py` (deprecated, deleted in Phase 17)
- Removed `ci_tech_improved.py` (deprecated, deleted in Phase 17)
- All 8 tool names verified against `registry.register()` calls ✅
- 0 old inaccurate subagent names found ✅
- 70+ real `.py` files cross-referenced against codebase ✅

### Step 3: Security — 0 secrets, ADMIN gates OK
- 0 secrets/API keys/tokens found ✅
- All 3 ADMIN-gated tools (show_all_leads, search_telegram_chats, send_telegram_message) have ADMIN context nearby ✅

### Step 4: Structure — All checks pass
- All 13 required H2 sections present ✅
- YAML frontmatter intact (name: aim-operator, license: MIT) ✅
- Closing signature present ✅
- Line count: 753 (slightly over 700, acknowledged as comprehensive content per 16-01 summary) ⚠️

## Task 2: Human Checkpoint ✅

**APPROVED** by Mikhail on 2026-05-20.

SOUL.md is production-ready: all 10 knowledge domains covered, subagent names verified, tool schemas accurate, no secrets, mode gating correct.

## Phase Status

Phase 16: 2/2 plans complete ✅
Phase 17: 1/1 plans complete ✅
Phase 18: 2/2 plans complete ✅
All critical phases shipped. Only Phase 13-02 (marketing campaigns) remains — deferred post-MVP.
