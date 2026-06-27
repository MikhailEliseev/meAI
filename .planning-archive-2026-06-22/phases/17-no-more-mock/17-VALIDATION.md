# Phase 17: No More Mock — Nyquist Validation

**Phase:** 17-no-more-mock
**Date:** 2026-05-20
**Source:** RESEARCH.md Validation Architecture section + line-by-line agent audit

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Wave |
|--------|----------|-----------|-------------------|------|
| NO-MOCK-01 | No agent imports `random` in production code | smoke | `grep -rn "import random\|from random" AIM/src/aim/subagents/competitive_intel/agents/*.py \| grep -v DEPRECATED \| grep -v ci_content.py \| grep -v ci_tech.py` | 1 |
| NO-MOCK-02 | API-gated agents return structured null without API key | unit | `pytest AIM/tests/aim/subagents/competitive_intel/agents/test_structured_null.py -v -x` | 1 |
| NO-MOCK-03 | ci_scout discovers real competitors (not hardcoded names) | integration | `pytest AIM/tests/aim/subagents/competitive_intel/agents/test_ci_scout.py -v -x` | 1 |
| NO-MOCK-04 | "3 numbers" computation uses real traffic/CPC data when available | unit | `pytest AIM/tests/aim/subagents/competitive_intel/agents/test_ci_strategist.py -v -x` | 1 |
| NO-MOCK-05 | CIOrchestrator quality_score reflects structured null rate | unit | `pytest AIM/tests/aim/subagents/competitive_intel/agents/test_orchestrator.py -v -x` | 1 |
| NO-MOCK-06 | Deprecated files (ci_content.py, ci_tech.py) cannot be imported | smoke | `python -c "from aim.subagents.competitive_intel.agents.ci_content import CIContentAgent" 2>&1 \|\| true` | 1 |
| NO-MOCK-07 | API client resilience (circuit breaker, retry) works in CI pipeline | integration | `pytest AIM/tests/subagents/api_clients/test_base.py -v` | 1 |

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (asyncio mode) |
| Coverage target | All 7 requirements |
| Timeout | 30s per test |

## Wave 0 Gaps (from RESEARCH)

- [x] `AIM/tests/aim/subagents/competitive_intel/agents/test_structured_null.py` — NO-MOCK-02 (Task 3)
- [x] `AIM/tests/aim/subagents/competitive_intel/agents/test_ci_scout.py` — NO-MOCK-03 (Task 4)
- [x] `AIM/tests/aim/subagents/competitive_intel/agents/test_ci_strategist.py` — NO-MOCK-04 (Task 4)
- [x] `AIM/tests/aim/subagents/competitive_intel/agents/test_orchestrator.py` — NO-MOCK-05 (Task 4)
- [x] `AIM/tests/aim/subagents/competitive_intel/agents/conftest.py` — shared fixtures (Task 3)

## Verification Commands

```bash
# Smoke: no random imports
grep -rn "import random\|from random" AIM/src/aim/subagents/competitive_intel/agents/*.py | grep -v __pycache__ | grep -v ".pyc"
# Expected: empty

# Unit: structured null pattern
cd AIM && python -m pytest tests/aim/subagents/competitive_intel/agents/test_structured_null.py -v -x --timeout=30

# Unit: ci_scout real discovery
cd AIM && python -m pytest tests/aim/subagents/competitive_intel/agents/test_ci_scout.py -v -x --timeout=30

# Unit: "3 numbers" computation
cd AIM && python -m pytest tests/aim/subagents/competitive_intel/agents/test_ci_strategist.py -v -x --timeout=30

# Unit: orchestrator quality_score
cd AIM && python -m pytest tests/aim/subagents/competitive_intel/agents/test_orchestrator.py -v -x --timeout=30

# Integration: API client resilience (existing 27 tests)
cd AIM && python -m pytest tests/subagents/api_clients/ -v

# Orchestrator import chain
python -c "from aim.subagents.competitive_intel.agents.ci_content_improved import CIContentAgentImproved"
python -c "from aim.subagents.competitive_intel.agents.ci_tech_real import CITechAgent"
```

## Sampling Continuity

| Check | Value |
|-------|-------|
| Watch mode | No (grep/one-shot runs) |
| Repeat interval | N/A (single-wave phase) |
| Manual re-run | Full verification block above |
