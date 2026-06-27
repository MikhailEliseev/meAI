# Phase 28: Deep Research Phase 0 — Validation Strategy

**Created:** 2026-06-06
**Status:** Active

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (Python) |
| Config file | none — Wave 0 |
| Quick run command | `python3 -m pytest AIM/hermes/app/tools/test_deep_research_merge.py -x` |
| Full suite command | `python3 -m pytest AIM/hermes/app/tools/test_deep_research_merge.py -v` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-1 (auto Phase 0 before Phase 1) | presale-pipeline SKILL.md invokes deep-research-phase-0 first | Manual (skill text review) | Review SKILL.md phase ordering | N/A (docs test) |
| SC-2 (doctor deep research) | Hermes skill produces per-doctor research with experience, degrees, publications | Integration | `python3 -m pytest tests/test_deep_research_skill.py::test_doctor_research_output -x` | ❌ Wave 0 |
| SC-3 (star doctor detection) | regex classifies д.м.н., профессор, заслуженный врач as star | Unit | `python3 -m pytest tests/test_deep_research_merge.py::test_tier_classification -x` | ❌ Wave 0 |
| SC-4 (clinic deep research) | data.json contains clinic ratings from prodoctorov, docdoc, 2gis, yandex | Integration | `python3 -m pytest tests/test_deep_research_skill.py::test_clinic_research_output -x` | ❌ Wave 0 |
| SC-5 (surface-level competitors) | Competitor section in data.json is marked as surface-level | Unit | `python3 -m pytest tests/test_deep_research_skill.py::test_competitor_depth_marker -x` | ❌ Wave 0 |
| SC-6 (post-contract deep competitor analysis) | Phase 0 does NOT trigger deep competitor research | Manual (architecture review) | Review SKILL.md boundary language | N/A (docs test) |
| SC-7 (data.json persistence) | deep_research section is written to data.json and consumed by downstream tools | Integration | `python3 -m pytest tests/test_deep_research_merge.py::test_json_merge -x` | ❌ Wave 0 |

## Sampling Rate

- **Per task commit:** `python3 -m pytest tests/test_deep_research_merge.py -x` (unit tests only)
- **Per wave merge:** `python3 -m pytest tests/test_deep_research_*.py -v` (full suite)
- **Phase gate:** All tests green + manual review of SKILL.md against presale-pipeline integration

## Wave 0 Gaps

- [ ] `tests/test_deep_research_merge.py` — covers REQ-SC3 (tier classification), REQ-SC7 (JSON merge)
- [ ] `tests/test_deep_research_skill.py` — covers REQ-SC2 (doctor research), REQ-SC4 (clinic research), REQ-SC5 (competitor depth marker)
- [ ] `tests/conftest.py` — shared fixtures (sample doctor bios, sample clinic data, sample data.json)
- [ ] SKILL.md review checklist — manual validation of SC-1, SC-6 (phase ordering, competitor boundary)

## Verification Commands

### Automated (for CI/gate)
```bash
# After Task 1 (deep-research-merge.py + tests)
python3 -m pytest AIM/hermes/app/tools/test_deep_research_merge.py -x -v

# After Task 2 (deep-research-phase-0 SKILL.md)
python3 -m pytest AIM/hermes/app/tools/test_deep_research_merge.py -x -v

# After Task 3 (presale-pipeline integration)
python3 -m pytest AIM/hermes/app/tools/test_deep_research_*.py -v
```

### Manual (for reviewer)
```bash
# Verify SKILL.md exists on server
ssh root@138.16.224.188 "ls -la /root/.hermes/skills/software-development/deep-research-phase-0/SKILL.md"

# Verify presale-pipeline has Phase 0 integration
ssh root@138.16.224.188 "grep -n 'deep-research-phase-0' /root/.hermes/skills/software-development/presale-pipeline/SKILL.md"

# Verify quality-gate.py checks deep_research
ssh root@138.16.224.188 "grep -n 'deep_research' /root/bin/quality-gate.py"

# Verify deep-research-merge.py runs on server
ssh root@138.16.224.188 "python3 /root/.hermes/skills/software-development/deep-research-phase-0/deep-research-merge.py --help"
```

## Security Validation

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | JSON schema validation for data.json merge; URL sanitization before web_extract; regex injection prevention |

### Threat Mitigations to Verify

| Pattern | Mitigation | Verify |
|---------|------------|--------|
| LLM JSON corruption | Python merge script validates JSON before writing | Unit test: malformed JSON input → reject |
| URL injection | Validate against allowlist (Russian medical domains only) | Manual code review |
| Regex DoS | Timeout on regex matching (max 100ms per pattern) | Unit test: pathological input → timeout, not hang |

---

*Phase: 28-deep-research-phase-0*
*Validation strategy derived from RESEARCH.md Validation Architecture*
