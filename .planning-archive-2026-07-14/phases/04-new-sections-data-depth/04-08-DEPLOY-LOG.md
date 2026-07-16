# Plan 04-08 Deploy Log

**Plan:** 04-08 (Deploy all Phase 4 files to aim-hermes container + integration validation)
**Phase:** 4 — New Sections & Data Depth
**Executed:** 2026-06-24T01:26:46Z – 2026-06-24T01:35:00Z (UTC)
**Operator:** Claude executor (sequential mode, ssh aim non-interactive)

## Deploy Summary

15 files deployed to production `aim-hermes` container via SSH + `docker exec -i ... tee` (atomic pipe-through-stdin pattern per Phase 3 / Plan 03-01).

**Files deployed:**

| # | Container Path | Origin Plan | New File? |
|---|----------------|-------------|-----------|
| 1 | `/opt/hermes/app/tools/find_company_financials.py` | 04-01 | No |
| 2 | `/opt/hermes/app/tools/find_doctor_handles.py` | 04-02 | No |
| 3 | `/opt/hermes/app/tools/run_forum_pains.py` | 04-03 | YES |
| 4 | `/opt/hermes/app/tools/run_media_urls.py` | 04-03 | YES |
| 5 | `/opt/hermes/app/pipeline/engine.py` | 04-03 | No |
| 6 | `/opt/hermes/app/orchestrator/__init__.py` | 02-02 | YES |
| 7 | `/opt/hermes/app/orchestrator/states.py` | 02-02 | YES |
| 8 | `/opt/hermes/app/orchestrator/three_pass.py` | 02-02/03-02/03-06 | YES |
| 9 | `/opt/hermes/app/orchestrator/niche_detector.py` | 03-02 | YES |
| 10 | `/opt/hermes/app/orchestrator/pass_collect.py` | 02-02/03-03/04-04 | YES |
| 11 | `/opt/hermes/app/orchestrator/pass_gap_analyze.py` | 02-02/03-03/04-04 | YES |
| 12 | `/opt/hermes/app/orchestrator/qc_checklist.py` | 02-03/03-03/03-06/04-04 | YES |
| 13 | `/opt/hermes/app/orchestrator/coverage_reporter.py` | 02-03/04-04 | YES |
| 14 | `/opt/hermes/app/orchestrator/pass_fill_assemble.py` | 02-02/03-05/04-05 | YES |
| 15 | `/opt/hermes/app/tools/generate_html_report.py` | 02-01/03-05/04-06/04-07/04-08 | No |

**Plan listed 11 files (1-5, 10-15).** Files 6-9 (orchestrator/__init__.py, states.py, three_pass.py, niche_detector.py) were added as a **Rule 3 deviation** — orchestrator/ directory did not exist in container before this deploy (Phase 2 never deployed these to container), and the 5 deployed Phase 4 orchestrator modules import from `app.orchestrator.states` / `app.orchestrator.three_pass` / `app.orchestrator.niche_detector` — they would have failed import without these 4 dependency files.

## MD5 Verification

### Pre-existing files (4) — backup + overwrite

| File | Local pre-deploy | Container pre-deploy | Container post-deploy | Match |
|------|------------------|----------------------|-----------------------|-------|
| `find_company_financials.py` | `26b8e7b2f57c07dcd6a48b2833cfa7e4` | `d224e8a4667c5a7ad07eb9ab12e9896b` | `26b8e7b2f57c07dcd6a48b2833cfa7e4` | OK |
| `find_doctor_handles.py` | `ac778fe0dd74b39442c31d2c0aa81cdf` | `c29f936da8d8fe85ca9b8850c280e2a3` | `ac778fe0dd74b39442c31d2c0aa81cdf` | OK |
| `generate_html_report.py` | `0ffe643fba31727d44b9d23ef2ee47d0` (pre-fix) → `ee0eb8c8dbfed1c0aa1ae486d645901d` (post-Rule-1-fix) | `dac69f6d33e07f210c23dbd83faa3c9b` | `ee0eb8c8dbfed1c0aa1ae486d645901d` | OK |
| `engine.py` | `ccb79d6f42aa4efdfaa236fb1c70a086` | `25e3066bea7c4675645307d266904d27` (Phase-3 state, 24 entries) | `ccb79d6f42aa4efdfaa236fb1c70a086` (26 entries) | OK |

### New tools (2) — first deploy

| File | Local | Container post-deploy | Match |
|------|-------|-----------------------|-------|
| `run_forum_pains.py` | `1e3d4a9297a66de88158322b854b28b1` | `1e3d4a9297a66de88158322b854b28b1` | OK |
| `run_media_urls.py` | `92f3372b8da64b54ba3df9e07c04ac48` | `92f3372b8da64b54ba3df9e07c04ac48` | OK |

### Orchestrator dependency files (4) — first deploy (Rule 3)

| File | Local | Container post-deploy | Match |
|------|-------|-----------------------|-------|
| `__init__.py` | `eefdc485b026c643c602dcf726b9149e` | `eefdc485b026c643c602dcf726b9149e` | OK |
| `states.py` | `99130a5d378cfa38b8d728e8f9f3f848` | `99130a5d378cfa38b8d728e8f9f3f848` | OK |
| `three_pass.py` | `4a23d8d88b689b17b10b1f86a2f0320e` | `4a23d8d88b689b17b10b1f86a2f0320e` | OK |
| `niche_detector.py` | `01196cc48149a17c8f1c8054b36c8e2e` | `01196cc48149a17c8f1c8054b36c8e2e` | OK |

### Phase 4 orchestrator files (5) — first deploy

| File | Local | Container post-deploy | Match |
|------|-------|-----------------------|-------|
| `pass_collect.py` | `0ace8688158b00b19d8e1d54d348abd3` | `0ace8688158b00b19d8e1d54d348abd3` | OK |
| `pass_gap_analyze.py` | `be94c2015b1368d0ff425f98f03558a8` | `be94c2015b1368d0ff425f98f03558a8` | OK |
| `qc_checklist.py` | `8038422015d99fe7a3ae9c250dbac26a` | `8038422015d99fe7a3ae9c250dbac26a` | OK |
| `coverage_reporter.py` | `d695de4b8eee98c7a7a74789c2e6e9f5` | `d695de4b8eee98c7a7a74789c2e6e9f5` | OK |
| `pass_fill_assemble.py` | `2f1d2268f2feb51f5b70220c260c6e05` | `2f1d2268f2feb51f5b70220c260c6e05` | OK |

## Backups (inside container, for rollback — DPL-05)

4 pre-existing files backed up with suffix `.phase4-backup-20260624`:

```
/opt/hermes/app/pipeline/engine.py.phase4-backup-20260624                 (91177 bytes, 24 entries — Phase 3 state)
/opt/hermes/app/tools/find_company_financials.py.phase4-backup-20260624   (7059 bytes — pre-04-01)
/opt/hermes/app/tools/find_doctor_handles.py.phase4-backup-20260624       (53472 bytes — pre-04-02)
/opt/hermes/app/tools/generate_html_report.py.phase4-backup-20260624      (48307 bytes — pre-04-06/04-07)
```

11 other deployed files were NEW to the container (no pre-existing file to backup).

## Deploy Method

Per Phase 3 / Plan 03-01 pattern — `docker cp` over SSH fails because source path resolves on SSH host, not executor host. Use pipe-through-stdin instead:

```bash
cat /local/path | ssh aim "docker exec -i aim-hermes tee /container/path > /dev/null && echo DEPLOYED"
```

Atomic, binary-safe, no host temp file.

## Verification Steps (all passed)

1. **SSH connectivity:** `ssh aim "hostname && whoami && pwd"` → `AIM-Server-PL / root / root`
2. **Container status pre-deploy:** `Up 42 hours (healthy)`
3. **Local Phase 4 markers verified:** revenue_dynamics(4), structured_regalia(19), run_forum_pains in engine.py(1), VERSION 1.2.0(1), _build_strategy_section(2)
4. **Pre-deploy md5 captured** for 4 pre-existing container files
5. **Backups created** for 4 pre-existing files (.phase4-backup-20260624)
6. **15 files deployed** via pipe-through-stdin (11 from plan + 4 Rule-3 orchestrator dependencies)
7. **Post-deploy md5** matches local for all 15 files
8. **New tools importable:**
   ```
   from app.tools.run_forum_pains import handle_run_forum_pains
   from app.tools.run_media_urls import handle_run_media_urls
   OK: new tools importable
   ```
9. **Phase 4 extensions importable:**
   ```
   from app.tools.find_company_financials import _format_revenue_dynamics, _format_clinic_metrics
   from app.tools.find_doctor_handles import _extract_structured_regalia, _merge_doctor_data
   OK: Phase 4 extensions importable
   ```
10. **`_TOOL_HANDLERS` count from inside container:** `26` (24 Phase 3 + 2 Phase 4: run_forum_pains, run_media_urls)
11. **Both new handlers resolve:** `_get_handler("run_forum_pains")` + `_get_handler("run_media_urls")` no error
12. **QC checklist from inside container:** `VERSION 1.2.0` with `18 items`
13. **All 10 Phase 4 HTML section builders importable:** _build_revenue_dynamics_section, _build_clinic_metrics_block, _build_media_urls_section, _build_ratings_section, _build_competitor_cards_section, _build_strategy_section, _build_offer_section, _build_whitefields_matrix, _build_experts_with_regalia, _build_content_analysis_with_fears
14. **Orchestrator prompts reference Phase 4 sections:**
    ```
    from app.orchestrator.three_pass import run_three_pass
    from app.orchestrator.pass_collect import _build_pass_collect_prompt
    from app.orchestrator.pass_fill_assemble import _build_prompt
    state = OrchestratorState(session_id="test", client_url="https://test.ru", client_name="Test")
    prompt1 = _build_pass_collect_prompt(state)  # contains "run_forum_pains" + "run_media_urls"
    prompt3 = _build_prompt(state)  # contains "Strategy" + "Whitefields" + "Offer"
    INTEGRATION PROMPT CHECK: OK
    ```
15. **Health check (inside container):** `GET /health` → HTTP 200, body `{"status":"ok",...}`
16. **Container status post-deploy:** `Up 42 hours (healthy)` — no restart, no production regression

## Health-Check Port Note

`aim-hermes` has NO port published to the Docker host (`docker port aim-hermes` returns empty). Plan's acceptance criterion `curl http://localhost:8000/health from the server` is impossible by design — nginx fronts Hermes externally. Correct test is `docker exec aim-hermes curl http://127.0.0.1:8000/health`, which returned HTTP 200. This matches Phase 3 / Plan 03-01's finding.

## ORCHESTRATOR_MODE Note

`ORCHESTRATOR_MODE` env var is **unset** in the container (orchestrator is OPT-IN per Phase 2 / Plan 02-02 design). Default production path (PRESALE flow) is unchanged — orchestrator code lives in container but is not invoked.

To enable orchestrator for testing or production, set:
```bash
docker exec aim-hermes bash -c 'echo "ORCHESTRATOR_MODE=1" >> /opt/data/.env'
docker restart aim-hermes
```

Or pass inline for a one-off test:
```bash
docker exec -e ORCHESTRATOR_MODE=1 aim-hermes python -c 'from app.orchestrator.three_pass import run_three_pass; ...'
```

## Rollback Instructions

### Full rollback (revert all Phase 4 changes)

```bash
# Restore the 4 pre-existing files
ssh aim "docker exec aim-hermes bash -c '
  cp /opt/hermes/app/pipeline/engine.py.phase4-backup-20260624 /opt/hermes/app/pipeline/engine.py
  cp /opt/hermes/app/tools/find_company_financials.py.phase4-backup-20260624 /opt/hermes/app/tools/find_company_financials.py
  cp /opt/hermes/app/tools/find_doctor_handles.py.phase4-backup-20260624 /opt/hermes/app/tools/find_doctor_handles.py
  cp /opt/hermes/app/tools/generate_html_report.py.phase4-backup-20260624 /opt/hermes/app/tools/generate_html_report.py
'"

# Remove new files (orchestrator dir + 2 new tools)
ssh aim "docker exec aim-hermes bash -c '
  rm -rf /opt/hermes/app/orchestrator/
  rm -f /opt/hermes/app/tools/run_forum_pains.py
  rm -f /opt/hermes/app/tools/run_media_urls.py
'"

# Restart container to clear Python module cache
ssh aim "docker restart aim-hermes"
```

Container restart IS required for rollback (Python caches imported modules in uvicorn workers).

### Partial rollback (keep orchestrator, revert specific file)

```bash
# Example: revert only engine.py to 24-entry Phase-3 state
ssh aim "docker exec aim-hermes cp /opt/hermes/app/pipeline/engine.py.phase4-backup-20260624 /opt/hermes/app/pipeline/engine.py"
ssh aim "docker restart aim-hermes"
```

## Deviations from Plan

### [Rule 3 — Auto-fix blocking issue] Deploy 4 orchestrator dependency files not listed in plan

- **Found during:** Task 1 step 4 verification (initial import test)
- **Issue:** Plan listed only 5 orchestrator files (pass_collect, pass_gap_analyze, qc_checklist, coverage_reporter, pass_fill_assemble). But the orchestrator/ directory did not exist in container (Phase 2 plan 02-02 created these files locally but never deployed). The 5 deployed modules import from `app.orchestrator.states.OrchestratorState`, `app.orchestrator.three_pass.run_three_pass`, and `app.orchestrator.niche_detector` — without these 4 additional files, ALL imports would have raised ModuleNotFoundError, breaking Phase 4 orchestrator entirely.
- **Fix:** Also deployed: `__init__.py`, `states.py`, `three_pass.py`, `niche_detector.py`. These are Phase 2/3 code (not Phase 4), but they are critical dependencies for Phase 4 code to function. No backup created for these 4 (they didn't exist pre-deploy).
- **Files deployed additionally:** 4 (orchestrator/__init__.py, states.py, three_pass.py, niche_detector.py)
- **Commit reference:** deploy log + commit `c063ecc` (Rule 1 fix on generate_html_report.py)

### [Rule 1 — Auto-fix bug] Python 3.11 f-string backslash SyntaxError in generate_html_report.py

- **Found during:** Task 1 step 4 verification (initial import test)
- **Issue:** Line 418 of generate_html_report.py had `{'<span class=\"metric-tag metric-tag-warning\">PR Needed</span>' if pr_needed else ''}` — a backslash-escaped double-quote INSIDE an f-string expression part. Python 3.12+ (local dev env) lifted this restriction, but Python 3.11 (container runtime, python:3.11-slim) raises SyntaxError at parse time. This is the same lesson Plan 03-05 documented in its deviation log (commit `4614ea9`): AST parse on 3.12+ does NOT catch 3.11-incompatible f-strings — only runtime import surfaces the error.
- **Fix:** Extracted the HTML string to a `pr_badge` variable outside the f-string, then referenced `{pr_badge}` inside the template literal. Eliminates backslash-in-expression. Also added inline comment documenting the 3.11 compat rationale.
- **Files modified:** `AIM/hermes/app/tools/generate_html_report.py` (+4 lines, -1 line)
- **Local commit:** `c063ecc` `fix(04-08): Python 3.11 f-string backslash syntax error`
- **Re-deployed:** Yes — post-fix md5 `ee0eb8c8dbfed1c0aa1ae486d645901d` now matches between local and container

## Success Criteria (per plan)

- [x] **DPL-01 SATISFIED:** Deploy via docker cp + pipe-through-stdin (no image rebuild)
- [x] **DPL-03 SATISFIED:** Health check returns 200 after deploy
- [x] **DPL-05 SATISFIED:** Backup files created for 4 pre-existing files (`.phase4-backup-20260624`)
- [x] All 11 plan-listed files deployed and importable from inside container
- [x] _TOOL_HANDLERS has 26 entries (24 Phase 3 + 2 Phase 4)
- [x] QC checklist VERSION 1.2.0 with 18 items
- [x] All 10 Phase 4 HTML section builders importable
- [x] Phase 4 extension functions importable
- [x] Orchestrator prompts reference Phase 4 sections (Strategy, Offer, Whitefields, forum_pains, media_urls)
- [x] No production regression (health 200, container still Up 42 hours, no restart)
- [ ] **Integration test (Task 2):** Awaiting user verification — requires ORCHESTRATOR_MODE=1 + 15-minute test presale run
