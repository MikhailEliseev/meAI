# Testing Patterns

**Analysis Date:** 2026-06-19

## Overview

**Testing is sparse.** The Hermes codebase has exactly 3 test files totaling ~21 tests. There is no CI/CD pipeline, no coverage enforcement, and no test runner configuration file (no `pyproject.toml` with pytest config, no `conftest.py`). Tests are developer-initiated manual runs.

**Test files found:**
- `tests/test_presale_flow.py` — 7 tests (content/string assertions)
- `app/tools/test_deep_research_merge.py` — 27 tests (unit tests for classification)
- `app/tools/test_service_categorizer.py` — 5 tests (manual-run categorization tests)
- Server-side: `/opt/hermes-data/app/tools/test_presale_pipeline.py` — E2E httpx integration test (not committed locally)

## Test Framework

**Runner:**
- pytest (detected via `import pytest` and `@pytest.fixture` decorators)
- No version pinned in `requirements.txt`
- No `pytest.ini`, `pyproject.toml`, `conftest.py`, or `tox.ini` configuration files

**Assertion Library:**
- Standard Python `assert` statements — no external assertion library (no `pytest-check`, `unittest.mock`, etc.)

**Run Commands (inferred):**
```bash
pytest AIM/hermes/tests/                          # Run presale flow tests
pytest AIM/hermes/app/tools/test_deep_research_merge.py  # Run classification tests
python AIM/hermes/app/tools/test_service_categorizer.py   # Run categorizer tests (manual, no pytest)
```

## Test File Organization

**Location:**
Mixed — one test file in dedicated `tests/` directory, two co-located alongside source in `app/tools/`.

```
AIM/hermes/
├── tests/
│   └── test_presale_flow.py        # Content/consistency tests
├── app/tools/
│   ├── test_deep_research_merge.py  # Unit tests co-located with source
│   ├── test_service_categorizer.py  # Manual-run tests co-located with source
│   └── deep_research_merge.py       # Source module for the tests above
└── app/
    └── tools/
        └── service_categorizer.py   # Source module for the tests above
```

**Naming:**
- `test_<module>.py` for test files
- `test_<description>` for test functions

**Pattern:** Tests are placed near the code they test, with only the cross-cutting presale flow test in the dedicated `tests/` directory.

## Test Structure

**Suite Organization — test_deep_research_merge.py (best example):**

```python
"""Unit tests for deep_research_merge.py — tier classification and JSON merge.
14 behaviour cases from PLAN.md Task 1.
"""
import json
import os
import sys
import tempfile
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deep_research_merge import classify_doctor, validate_and_merge

# ── Test fixtures ──────────────────────────────────────────────────
@pytest.fixture
def empty_data_json():
    return {"meta": {}, "clinic": {}, "doctors": [], "competitors": [], "content": {}, "geo": {}}

# ── Test 1: Tier 1 (star) — д.м.н. ─────────────────────────────────
def test_tier_1_star_dmn():
    result = classify_doctor("Иванова А.П.", "Иванова А.П., д.м.н., пластический хирург", 20)
    assert result["tier"] == "star"
    assert "д.м.н." in result["degrees"]
```

**Patterns:**
- Tests are organized as flat functions (not classes). No `unittest.TestCase` subclassing.
- Section header comments: `# ── Test 1: Tier 1 (star) — д.м.н. ──`
- Each test is self-contained with all data inline — no external fixtures, no database setup.
- Fixtures defined in the same file, not in `conftest.py`.
- Test function names are descriptive English: `test_<what_it_tests>`. Example: `test_tier_1_star_dmn`, `test_regex_safety_no_catastrophic_backtracking`.

**Setup Pattern (test_presale_flow.py):**
```python
@pytest.fixture(scope="module")
def soul_md():
    if not SOUL_PATH.exists():
        pytest.skip(f"SOUL.md not found at {SOUL_PATH}")
    return SOUL_PATH.read_text()
```
Uses `pytest.skip()` for graceful skip when required files are absent rather than failing.

**Teardown Pattern:**
- Not used — tests have no side effects (no database writes, no network calls).

**Assertion Pattern:**
```python
# Simple existence check
assert result["tier"] == "star"

# Collection membership check
assert any(s.id == 'seo_rebuild' and s.category == 'recommended' for s in result)

# Multi-condition with message
assert found >= 2, f"Only {found}/7 conversational markers found"

# Performance guard
elapsed_ms = (time.perf_counter() - start) * 1000
assert elapsed_ms < 100, f"classify_doctor took {elapsed_ms:.0f}ms, expected <100ms"
```

## Mocking

**Framework:** No mocking framework used. No `unittest.mock`, `pytest-mock`, or `responses` library.

**What is NOT mocked:**
Tests use real code directly:
- `test_deep_research_merge.py` imports and calls `classify_doctor()` and `validate_and_merge()` directly — these are pure functions with no external dependencies.
- `test_service_categorizer.py` instantiates `ServiceCategorizer()` and passes dict data — no database or network calls.
- `test_presale_flow.py` reads and parses actual source files (`SOUL.md`, `agent_wrapper.py`) from disk but does not import the modules (to avoid dependency issues with `hermes_state`).
- Server-side `test_presale_pipeline.py` uses `httpx.AsyncClient` to make real HTTP calls to `http://localhost:8000` — a live integration test.

**Why no mocking:** The tested functions (classification, categorization, content assertions) are pure logic with no external side effects. The E2E test makes real API calls against a running server.

## Fixtures and Factories

**Test Data — inline dict construction:**
```python
data = {
    'seo_score': 34,
    'has_sitemap': False,
    'has_structured_data': False,
    'total_pages': 25,
    'has_ads': False,
    'social_links': {},
}
result = cat.categorize(data)
```

**Fixtures:** Only `test_deep_research_merge.py` uses `@pytest.fixture` for reusable test data:
```python
@pytest.fixture
def sample_research_input():
    return {
        "clinic": {"history": "Founded in 2008", ...},
        "doctors": [...],
        "_meta": {...}
    }
```

**Location:** All fixtures and test data inline in test files. No shared fixture module.

## Coverage

**Requirements:** None enforced. No `--cov` flags, no `coverage` package in `requirements.txt`, no coverage threshold.

**What IS tested:**
- **Doctor tier classification:** 27 tests covering star/core/team tiers, degree extraction, experience promotion, edge cases (ReDoS safety, empty bio, `д. м. н.` with spaces, full-word degrees like "доктор медицинских наук")
- **JSON merge logic:** 6 tests covering new sections, existing field preservation, idempotency, _meta generation, clinic-only and doctors-only inputs
- **Service categorization:** 5 tests covering SEO/ads/social scenarios with different prescan data
- **PRESALE flow consistency:** 7 tests verifying SOUL.md and agent_wrapper.py don't contain deprecated parallel-first patterns, have step-by-step guidance, and retain core principles

**What is NOT tested:**
- **Tool handlers:** Zero tests for any `handle_*` function (no testing of `handle_run_prescan`, `handle_find_competitors`, `handle_collect_contact`, etc.)
- **Agent wrapper:** Zero tests for `run_agent_sync()`, `run_agent()`, session management, or agent caching
- **Error handling paths:** Zero tests verifying error responses from tool handlers
- **SSE streaming:** Zero tests for `chat_stream` endpoint or progress event generation
- **Authentication:** Zero tests for `verify_api_key()` or Bearer token validation
- **Token economy:** Zero tests for `TokenEconomy` budget tracking
- **Connections:** Zero tests for AIM API integration, Telegram gateway, or database operations
- **Shell exec security:** Zero tests for command allowlist/blocklist validation
- **Key rotation:** Zero tests for `rotate_keys.py` logic

**View Coverage:**
```bash
# No coverage tool configured. Manual estimation:
# ~5% code coverage overall (classification + categorization only)
# ~0% coverage of async tool handlers, API integration, error handling
```

## Test Types

**Unit Tests:**
- Location: `app/tools/test_deep_research_merge.py`, `app/tools/test_service_categorizer.py`
- Scope: Pure logic functions (classification, categorization, JSON merge)
- Approach: Direct function calls with inline test data. No fixtures, no setup/teardown. Tests are deterministic with no external dependencies.

**Integration Tests:**
- Location: Server-side `/opt/hermes-data/app/tools/test_presale_pipeline.py` (not committed to repo)
- Scope: End-to-end pipeline against live AIM API on `localhost:8000`
- Approach: Runs through a list of 3 real clinics, calls `find_competitors` + analyze, logs results and issues found. Uses `httpx.AsyncClient` with 120s timeout.
- Pattern: Each clinic is processed independently, results analyzed for completeness (revenue missing, competitors empty, etc.)

**E2E Tests:**
- Not formally present. Earlier testing was documented in `TESTING_REPORT.md` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/TESTING_REPORT.md`) with 4 manual chat tests against the live Hermes instance.

**Content Tests:**
- Location: `tests/test_presale_flow.py`
- Scope: Verify that SOUL.md and agent_wrapper.py contain (or don't contain) expected text patterns
- Approach: Parse source files as plain text, use regex to extract specific sections, assert on string presence/absence. These are not behavioral tests — they enforce that documentation and code stay synchronized.

## Common Patterns

**Async Testing:**
No async tests exist. All tests are synchronous and call functions directly.

**Error Testing:**
No dedicated error path tests. The classification tests include edge cases (empty bio, long strings) but test correct behavior, not error handling.

**Performance Testing:**
One test explicitly checks performance: `test_regex_safety_no_catastrophic_backtracking()` uses `time.perf_counter()` to verify `classify_doctor()` completes in under 100ms with 10KB input.

**Manual Run Pattern (test_service_categorizer.py):**
```python
if __name__ == '__main__':
    test_seo_poor_no_ads_no_social()
    test_seo_good_has_ads_active_social()
    test_critical_case_revenue_gap()
    test_all_categories_valid()
    test_audit_always_base_locked()
    print('\nALL TESTS PASSED')
```
This file has both `pytest`-style test functions AND a manual `if __name__ == '__main__'` runner that calls them sequentially. It also uses `print()` for pass/fail reporting instead of assertions only.

## CI/CD

**CI Pipeline:** None detected for Hermes testing.
- No GitHub Actions workflow files in Hermes directory.
- No Jenkinsfile, GitLab CI, or CircleCI config.
- Dockerfile healthcheck uses `curl -f http://localhost:8000/health` — liveness only, not functional testing.

**Pre-deploy checks:** None automated. Testing is developer-initiated via manual test execution.

## Gaps Summary

| Area | Status | Risk |
|------|--------|------|
| Tool handler unit tests | Missing entirely | High — regression risk on tool changes |
| Error handling tests | Missing entirely | Medium — error paths untested |
| Agent wrapper tests | Missing entirely | High — session/cache logic untested |
| API integration tests | Server-side only, not version-controlled | Medium — drift between test code and production |
| Async/streaming tests | Missing entirely | High — SSE streaming untested |
| Coverage enforcement | Not configured | Low — no coverage targets set |
| Mocking infrastructure | Not set up | Low — current tests are pure logic |

---

*Testing analysis: 2026-06-19*
