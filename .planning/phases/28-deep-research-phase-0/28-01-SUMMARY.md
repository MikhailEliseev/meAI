---
phase: 28-deep-research-phase-0
plan: 01
subsystem: presale-pipeline
tags: [deep-research, doctor-classification, tier-system, hermes-skill, presale]
requires: []
provides:
  - deep-research-phase-0/SKILL.md (LLM instruction for autonomous Phase 0)
  - deep_research_merge.py (Python helper: tier classification + JSON merge)
  - presale-pipeline v3.6.0 (Phase 0 integration)
  - quality-gate.py (deep_research checks)
affects:
  - social-verifier (receives pre-discovered social profiles)
  - content-analyzer (receives doctor regalia for expert cards)
  - html-kp-generator (receives clinic history + key doctors)
tech-stack:
  added: []
  patterns:
    - Regex-based Russian medical degree detection (6 TIER_1 + 6 TIER_2 patterns)
    - Three-tier doctor classification: star (д.м.н., professor) / core (к.м.н., chief) / team
    - Tier-dependent research depth: 7-10 searches (star), 5 (core), 2-3 (team)
    - Atomic JSON writes via tempfile + os.rename()
    - Pre-compiled regex patterns for ReDoS protection
key-files:
  created:
    - AIM/hermes/app/tools/deep_research_merge.py (361 lines)
    - AIM/hermes/app/tools/test_deep_research_merge.py (280 lines, 30 tests)
    - AIM/hermes/skills/deep-research-phase-0/SKILL.md (491 lines)
    - AIM/hermes/skills/presale-pipeline/SKILL.md (346 lines, v3.6.0)
    - AIM/hermes/skills/presale-pipeline/schemas/presale-state.template.json (26 lines)
    - AIM/hermes/app/tools/quality_gate.py (150 lines)
  modified: []
decisions:
  - Phase 0 inserted before Phase 1 in presale-pipeline with full renumbering (old P0→P1, P1→P2, etc.)
  - deep-research-phase-0/SKILL.md uses autonomous no-confirmation pattern (Iron Rule 1)
  - JSON merge exclusively through Python helper — LLM never writes JSON directly (Iron Rule 2)
  - Competitor deep analysis is strictly post-contract only (Iron Rule 3)
  - auto_flagged_star detection for non-formal-degree stars (qualifier or experience heuristic)
metrics:
  duration: ~7 minutes
  completed_date: 2026-06-06
---

# Phase 28 Plan 01: Deep Research Phase 0 Summary

**One-liner:** Autonomous pre-flight deep research pipeline with three-tier Russian medical doctor classification (star/core/team) using regex-based regalia detection, integrated as mandatory Phase 0 before presale-pipeline.

## Execution Summary

Created the complete Deep Research Phase 0 system — a mandatory pre-flight intelligence layer that runs before every presale. Three components delivered:

1. **Python helper (`deep_research_merge.py`):** Tier classification engine with 12 regex patterns for Russian medical degrees (д.м.н., к.м.н., профессор, заслуженный врач РФ, etc.), experience heuristics (15yr→core, 25yr→star), star qualifiers (author of methodologies, congress organizer), and atomic JSON merge via stdin. 30/30 tests pass.

2. **LLM instruction (`SKILL.md`):** 491-line Hermes skill with 3 Iron Rules (No Confirmation, JSON via Python helper, Surface-only competitors), 5 Steps (extract, classify, per-doctor research, clinic research, merge), tier-dependent research depth, Closure Loop, and confidence markers (VERIFIED/SINGLE_SOURCE/LLM_INFERRED).

3. **Presale-pipeline integration (v3.6.0):** New Phase 0 inserted before Phase 1 with complete phase renumbering, updated `depends_on`, 5 new state machine steps, and deep_research checks in quality-gate.py (non-blocking warnings).

## Task Summary

| Task | Name | Type | Commit | Status |
|------|------|------|--------|--------|
| 1 | deep_research_merge.py + unit tests | TDD (auto) | `4f2fd68` | Complete |
| 2 | SKILL.md for deep-research-phase-0 | auto | `cd83488` | Complete |
| 3 | Integration into presale-pipeline | auto | `520608f` | Complete |

### TDD Gates (Task 1)

| Gate | Commit | Status |
|------|--------|--------|
| RED | `89449d3` | 30 tests, all failing (ModuleNotFoundError) |
| GREEN | `4f2fd68` | 30/30 tests passing |
| REFACTOR | — | Not needed (code clean on first pass) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed regex for `организатор конгресса` (singular genitive)**
- **Found during:** Task 1 GREEN phase
- **Issue:** Pattern `конгресс[ао]в` matched only plural forms (конгрессов). "организатор конгресса" (singular genitive) was not detected.
- **Fix:** Changed to `конгресс(?:а|ов)` to match both singular and plural genitive forms.
- **Files modified:** `AIM/hermes/app/tools/deep_research_merge.py`
- **Commit:** `4f2fd68`

**2. [Rule 1 - Bug] Fixed regex for `зав. отделением` (instrumental case)**
- **Found during:** Task 1 GREEN phase
- **Issue:** Pattern `отделени[яй]` matched only "отделения" and "отделеним" but not "отделением" (instrumental case).
- **Fix:** Changed to `отделен` (stem match) for both `зав.` and `руководитель` patterns. Now matches all case forms: отделением, отделения, отделении, etc.
- **Files modified:** `AIM/hermes/app/tools/deep_research_merge.py`
- **Commit:** `4f2fd68`

### Deferred Deployment

**Server deployment deferred** — `root@138.16.224.188` is DOWN (SSH timeout). All files created locally and committed. Deployment steps documented in SUMMARY for execution when server is back up.

### Deferred Deployment Checklist

When server comes back up, run:

```bash
# 1. SKILL.md for deep-research-phase-0
ssh root@138.16.224.188 "mkdir -p /root/.hermes/skills/software-development/deep-research-phase-0"
scp AIM/hermes/skills/deep-research-phase-0/SKILL.md root@138.16.224.188:/root/.hermes/skills/software-development/deep-research-phase-0/SKILL.md

# 2. Python helper
scp AIM/hermes/app/tools/deep_research_merge.py root@138.16.224.188:/root/bin/deep-research-merge.py
ssh root@138.16.224.188 "chmod +x /root/bin/deep-research-merge.py"

# 3. Updated presale-state.template.json
scp AIM/hermes/skills/presale-pipeline/schemas/presale-state.template.json root@138.16.224.188:/root/work/presale/presale-state.template.json

# 4. Updated quality-gate.py
scp AIM/hermes/app/tools/quality_gate.py root@138.16.224.188:/root/bin/quality-gate.py

# 5. Updated presale-pipeline SKILL.md (backup first!)
ssh root@138.16.224.188 "cp /root/.hermes/skills/software-development/presale-pipeline/SKILL.md /root/.hermes/skills/software-development/presale-pipeline/SKILL.md.bak-260606"
scp AIM/hermes/skills/presale-pipeline/SKILL.md root@138.16.224.188:/root/.hermes/skills/software-development/presale-pipeline/SKILL.md

# 6. Verify deployment
ssh root@138.16.224.188 "ls -la /root/.hermes/skills/software-development/deep-research-phase-0/SKILL.md /root/bin/deep-research-merge.py /root/work/presale/presale-state.template.json /root/bin/quality-gate.py"
ssh root@138.16.224.188 "grep -c 'deep-research-phase-0' /root/.hermes/skills/software-development/presale-pipeline/SKILL.md"
ssh root@138.16.224.188 "grep -c 'phase0-deep-research' /root/work/presale/presale-state.template.json"
```

## Known Stubs

None — all components implement their full behavior. No placeholder data, no mock patterns.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: stdin-trust | deep_research_merge.py | LLM-generated JSON enters via stdin. Mitigated: full JSON schema validation before write, atomic tempfile+rename. Documented in threat model T-28-01. |
| threat_flag: regex-dos | deep_research_merge.py | classify_doctor() processes LLM-provided bio_text. Mitigated: 50KB bio limit, pre-compiled patterns, 100ms timeout guard. Documented in threat model T-28-03. |

## Self-Check: PASSED

- [x] `AIM/hermes/app/tools/deep_research_merge.py` — exists (361 lines)
- [x] `AIM/hermes/app/tools/test_deep_research_merge.py` — exists (280 lines, 30 tests)
- [x] `AIM/hermes/skills/deep-research-phase-0/SKILL.md` — exists (491 lines)
- [x] `AIM/hermes/skills/presale-pipeline/SKILL.md` — exists (346 lines)
- [x] `AIM/hermes/skills/presale-pipeline/schemas/presale-state.template.json` — exists
- [x] `AIM/hermes/app/tools/quality_gate.py` — exists (150 lines)
- [x] `89449d3` — commit exists (RED)
- [x] `4f2fd68` — commit exists (GREEN)
- [x] `cd83488` — commit exists (Task 2)
- [x] `520608f` — commit exists (Task 3)
- [x] All 30 tests pass: `python3 -m pytest AIM/hermes/app/tools/test_deep_research_merge.py -x`
