---
phase: 07-test-on-3-niches
plan: "01"
subsystem: testing
tags: [phase7, scout, test-harness, autonomous, orchestrator, perplexity, docker-exec]

# Dependency graph
requires:
  - phase: 06-documentation-sync
    provides: SOUL.md v5 + SKILL.md v2.0.0 + phases.py LEGACY docstring + engine.py regression guard (all deployed in container)
  - phase: 04-new-sections-data-depth
    provides: 26 _TOOL_HANDLERS + QC_CHECKLIST 18 items v1.2.0 + 3-pass orchestrator deployed
provides:
  - "Verified container pre-flight: 8 checks PASS (healthy, 26 handlers, QC 1.2.0, ref HTML md5 match)"
  - "Test harness run_presale_test.py — 195-line async wrapper around run_three_pass with 30-min timeout + heartbeat"
  - "3 selected clinic URLs: plastic-iphk (locked), dental-belgravia, cosmetology-renew (both Perplexity-sourced + URL-verified)"
  - "Server-side output directories /opt/data/memories/proposals/{plastic-iphk,dental-belgravia,cosmetology-renew}/ ready to receive artifacts"
  - "Server-side harness deployment /opt/data/phase7/run_presale_test.py (md5 9f61fe93411c46ee547e76cd62fe3189)"
affects: [07-02-plastic-surgery-test, 07-03-dentistry-test, 07-04-cosmetology-test]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "asyncio.wait_for(state, timeout=1800) — 30-min hard ceiling for presale runs"
    - "Heartbeat task: asyncio.Event + asyncio.wait_for(stop_event.wait(), timeout=60) loop for periodic stdout"
    - "Late import of app.orchestrator.three_pass INSIDE async function — env (ORCHESTRATOR_MODE) must be set before any app.* import"
    - "Container deployment via cat | ssh aim 'docker exec -i aim-hermes tee remote' — pipe-through-stdin pattern"
    - "Perplexity clinic search via app.tools.perplexity_tools.handle_perplexity_search(question=..., model='sonar-pro')"

key-files:
  created:
    - ".planning/phases/07-test-on-3-niches/07-01-scout-report.md"
    - ".planning/phases/07-test-on-3-niches/07-01-selected-clinics.md"
    - ".planning/phases/07-test-on-3-niches/run_presale_test.py"
    - "aim-hermes:/opt/data/phase7/run_presale_test.py"
    - "aim-hermes:/opt/data/memories/proposals/plastic-iphk/ (dir)"
    - "aim-hermes:/opt/data/memories/proposals/dental-belgravia/ (dir)"
    - "aim-hermes:/opt/data/memories/proposals/cosmetology-renew/ (dir)"
  modified: []

key-decisions:
  - "Belgravia Dental Studio (belgraviadent.ru) selected for dental test — Forbes #1 network, premium segment mirrors IPHK reference, 6+ branches = deep doctor pool"
  - "Re:new clinic (renewclinic.ru) selected for cosmetology test — modern 3-branch chain, confirmed URL, IG-critical niche exercises Phase 3 hard-fail path"
  - "inwhite.ru rejected despite 32top 2026 #1 ranking — connection failed in httpx reachability check (would block Plan 07-03)"
  - "Dental mode = ADMIN (per D-07), Cosmetology mode = PRESALE (per D-04 variation) — exercises both mode paths across the 3-niche test matrix"
  - "Heartbeat task only logs elapsed time (not live pass_status) — run_three_pass does not expose intermediate state to its caller; documented as harness limitation"
  - "ORCHESTRATOR_MODE=1 injected per-exec via docker exec -e flag — no container restart needed, production presale flow unaffected"

patterns-established:
  - "Pattern: pre-flight scout report with 8-check matrix before any test plan runs — catches container drift early"
  - "Pattern: standalone Python harness script for orchestrator invocation — decouples testing from production Hermes API entry points"
  - "Pattern: metadata.json + proposal.html paired output per slug dir — enables post-test scoring + comparison with reference HTML"
  - "Pattern: Perplexity clinic selection with httpx reachability verification — avoids selecting URLs that 404/block in actual test runs"

requirements-completed: [TST-01, TST-05]

# Metrics
duration: 10min
completed: 2026-06-24
---

# Phase 7 Plan 01: Pre-flight Scout + Test Harness Setup Summary

**Verified container is healthy + ready (8/8 scout checks PASS) and built a 195-line async test harness with 3 Perplexity-selected clinic URLs (Belgravia Dental + Re:new Cosmetology) wired to slug-tagged output directories on the server.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-24T05:31:13Z
- **Completed:** 2026-06-24T05:40:35Z
- **Tasks:** 2/2
- **Files created:** 3 local + 4 server-side (1 harness deploy + 3 directories)

## Accomplishments

- All 8 pre-flight checks PASS — container is `Up 46 hours healthy`, TOOL_HANDLERS=26, QC_CHECKLIST=18 items v1.2.0, reference HTML md5 matches both server and local (`e957099790fd65a59065d5df6f21bed5`)
- Test harness `run_presale_test.py` (195 lines, under 200 cap) — async wrapper around `run_three_pass` with 30-min hard timeout, 60s heartbeat, metadata+HTML output, 3-status result reporting (SUCCESS/TIMEOUT/FAILED)
- Container deployment verified byte-identical (md5 `9f61fe93411c46ee547e76cd62fe3189` local + container), Python 3.11 syntax OK, `--help` works
- 3 clinic URLs selected via Perplexity sonar-pro + httpx reachability verification:
  - `plastic-iphk` → https://iphk.ru (locked per D-01)
  - `dental-belgravia` → https://belgraviadent.ru (Forbes #1 network)
  - `cosmetology-renew` → https://renewclinic.ru (3-branch modern chain)
- 3 server-side output directories created and verified empty, ready to receive artifacts from Plans 07-02/03/04

## Task Commits

1. **Task 1: Pre-flight scout (container verification + directory setup)** — `8ae4a9c` (scout)
2. **Task 2: Test harness + 3 clinic URLs selection** — `4716bf9` (feat)

**Plan metadata commit:** (pending — will be created after SUMMARY/STATE/ROADMAP update)

## Files Created/Modified

- `.planning/phases/07-test-on-3-niches/07-01-scout-report.md` — 8-check pre-flight verification report with raw command outputs
- `.planning/phases/07-test-on-3-niches/07-01-selected-clinics.md` — 3 selected clinic URLs with slugs, modes, rationale, and Perplexity raw output (audit trail)
- `.planning/phases/07-test-on-3-niches/run_presale_test.py` — 195-line async test harness (also deployed to container)
- `aim-hermes:/opt/data/phase7/run_presale_test.py` — server-side harness (md5 match)
- `aim-hermes:/opt/data/memories/proposals/plastic-iphk/` — output directory for Plan 07-02
- `aim-hermes:/opt/data/memories/proposals/dental-belgravia/` — output directory for Plan 07-03
- `aim-hermes:/opt/data/memories/proposals/cosmetology-renew/` — output directory for Plan 07-04

## Decisions Made

### Clinic Selection (D-02 fallback path NOT triggered — Perplexity succeeded)

1. **Belgravia Dental Studio** chosen over 4 other dental candidates — Forbes/Startsmile TOP #1 network recognition, 6+ Moscow branches (vs single-location competitors), confirmed reachable URL with deep homepage (1.17 MB), premium segment mirrors IPHK reference for fair style comparison.
2. **Re:new clinic** chosen over 4 other cosmetology candidates — explicit confirmed URL (Quantum and Beautyway had no URL in Perplexity snippet), 3-branch network = richer CI dataset, modern positioning correlates with active Instagram (key for IG-02 hard-fail path test).
3. **inwhite.ru rejected** despite being 32top 2026 #1 — failed httpx reachability check (would have blocked Plan 07-03 mid-test).

### Mode Assignment (per D-04, D-06, D-07)

- Plastic (Niche 1): PRESALE mode — D-06 specifies Telegram-bot style trigger
- Dental (Niche 2): ADMIN mode — D-07 exercises the ADMIN path as counterpart
- Cosmetology (Niche 3): PRESALE mode — exercises PRESALE with the IG-critical niche (complementary to Niche 1)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] SSH shell chaining split `docker exec` from `ls`**
- **Found during:** Task 1 (Check 7 + Check 8)
- **Issue:** Command `ssh aim "docker exec aim-hermes mkdir -p X && ls -ld X"` parses `&&` at the REMOTE HOST shell level — `mkdir` runs inside container (succeeds) but `ls` runs on the host (`/opt/data/phase7` doesn't exist on host → exit 2). Initial output falsely suggested failure.
- **Fix:** Split each compound command into separate `ssh aim "docker exec ..."` invocations so every command runs inside the container.
- **Files modified:** None (procedural fix only)
- **Verification:** Re-ran each `ls` via separate `ssh aim "docker exec aim-hermes ls ..."` — all directories confirmed present inside container.
- **Committed in:** 8ae4a9c (scout report documents the deviation)

**2. [Rule 3 — Blocking] Perplexity module path was wrong in plan**
- **Found during:** Task 2 Step C (first invocation)
- **Issue:** Plan said `from app.tools.perplexity_search import handle_perplexity_search` — actual module is `app.tools.perplexity_tools` (singular file containing both `handle_perplexity_search` and `handle_perplexity_deep_analyze`).
- **Fix:** Used `grep` to find the actual module name in container filesystem, then used correct import path. Function name `handle_perplexity_search` was correct.
- **Files modified:** None (no code change — used the correct module dynamically)
- **Verification:** Perplexity call succeeded with HTTP 200 from `api.perplexity.ai`.
- **Committed in:** 4716bf9 (selection rationale mentions `perplexity_tools`)

**3. [Rule 3 — Blocking] Plan's perplexity_search signature said `query=` — actual is `question=`**
- **Found during:** Task 2 Step C
- **Issue:** Plan suggested `handle_perplexity_search(query="...", model="sonar-pro")` — actual signature is `handle_perplexity_search(question="...", model="sonar-pro")`.
- **Fix:** Used `inspect.signature` to discover the correct kwarg name before calling.
- **Files modified:** None (procedural)
- **Verification:** Both Perplexity calls returned valid JSON responses.
- **Committed in:** 4716bf9

---

**Total deviations:** 3 auto-fixed (all Rule 3 — blocking issues, all procedural fixes without code changes)
**Impact on plan:** All fixes kept the plan on-track. No scope creep. All plan objectives achieved.

## Issues Encountered

- `inwhite.ru` connection failure — rejected as dental candidate despite #1 ranking. Mitigation: documented in selected-clinics.md, picked #4 (Belgravia) which is reachable + has stronger brand recognition.
- `/opt/data/phase7` directory did not exist before Task 1 — created in Check 7 (no issues).

## User Setup Required

None — no external service configuration required. All credentials (Perplexity API key, SSH access) already configured by prior phases.

## Next Phase Readiness

### Ready for Plan 07-02 (Plastic Surgery — iphk.ru)

Yes — all prerequisites met:
- Test harness deployed at `/opt/data/phase7/run_presale_test.py`
- Output directory `/opt/data/memories/proposals/plastic-iphk/` ready
- Reference HTML at `/opt/data/report-reference.html` (md5 match confirmed)
- Trigger command:
  ```
  ssh aim "docker exec -e ORCHESTRATOR_MODE=1 aim-hermes python3 /opt/data/phase7/run_presale_test.py --url https://iphk.ru --slug plastic-iphk --mode PRESALE --niche plastic_surgery"
  ```

### Ready for Plan 07-03 (Dentistry — belgraviadent.ru)

Yes — output directory `/opt/data/memories/proposals/dental-belgravia/` ready. Mode: ADMIN.

### Ready for Plan 07-04 (Cosmetology — renewclinic.ru)

Yes — output directory `/opt/data/memories/proposals/cosmetology-renew/` ready. Mode: PRESALE.

### No blockers

All systems green. The 30-min per-test timeout (T-07-01-D DoS mitigation) is enforced inside the harness via `asyncio.wait_for`.

---

*Phase: 07-test-on-3-niches*
*Plan: 01*
*Completed: 2026-06-24*

## Self-Check: PASSED

All claimed artifacts verified to exist:

**Local files:**
- FOUND: `.planning/phases/07-test-on-3-niches/07-01-scout-report.md`
- FOUND: `.planning/phases/07-test-on-3-niches/07-01-selected-clinics.md`
- FOUND: `.planning/phases/07-test-on-3-niches/run_presale_test.py`
- FOUND: `.planning/phases/07-test-on-3-niches/07-01-SUMMARY.md`

**Commits:**
- FOUND: `8ae4a9c` (Task 1 scout)
- FOUND: `4716bf9` (Task 2 feat)

**Server-side artifacts (verified via ssh aim docker exec):**
- FOUND: `/opt/data/phase7/run_presale_test.py` (7028 bytes, root:root)
- FOUND: `/opt/data/memories/proposals/plastic-iphk/` (directory)
- FOUND: `/opt/data/memories/proposals/dental-belgravia/` (directory)
- FOUND: `/opt/data/memories/proposals/cosmetology-renew/` (directory)
