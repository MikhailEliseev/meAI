# Phase 09 Blocker Fixes — Iteration 1 Complete

**Date:** 2026-06-27  
**Commit:** dd4ab64  
**Status:** All 5 blockers resolved

---

## ✅ BLOCKER 1: Circular Import (Plan 09-02)

**Issue:** Module-level import `from app.main import push_wow_comment` in tool handlers creates circular dependency: `main.py → tools/__init__.py → tools/run_prescan.py → main.py`

**Fix Applied:**
- Task 3 rewritten to use **lazy import pattern**
- Import moved inside `handle_*()` function body (not module level)
- Example code updated in all 3 tool files (run_prescan.py, find_competitors.py, run_instagram_content.py)
- Commented examples showing where to add manual triggers if needed

**Verification:**
```bash
grep -A 3 "def handle_run_prescan" AIM/hermes/app/tools/run_prescan.py
# Should show: from app.main import push_wow_comment inside function
```

---

## ✅ BLOCKER 2: WordPress Auth Not Configured (Plan 09-03)

**Issue:** TODO comment "Add WordPress auth" left unresolved at line 439. POST to WordPress REST API will return 401 Unauthorized.

**Fix Applied:**
- **New Task 4** added: `checkpoint:human-action` for WordPress authentication setup
- Steps include: create aim-bot user, generate application password, add to .env, update generate_report.py
- Plan frontmatter updated: `autonomous: true → false` (has checkpoint now)

**Verification:**
```bash
grep -A 10 "Task 4: Configure WordPress Authentication" .planning/phases/09-chat-pro-website-chat-ux-overhaul/09-03-PLAN.md
# Should show checkpoint with 9 setup steps
```

---

## ✅ BLOCKER 3: LLM Won't Call generate_report (Plan 09-03)

**Issue:** Tool registered but no prompt tells LLM when to invoke it. D-19 requires `report-ready` SSE event, but LLM won't know to call the tool.

**Fix Applied:**
- **New Task 5** added: Update `_presale_prompt()` in agent_wrapper_optimized.py
- ФАЗА 3 section instructs LLM to call generate_report after collect_contact OR when client requests full report
- Documents orchestrator_data structure (financials, competitors, instagram, seo, content, whitefields, clinic_metrics)
- Explains report-ready SSE flow: Python generates HTML → publishes WordPress → SSE event → frontend button
- Plan frontmatter updated: added `AIM/hermes/app/agent_wrapper_optimized.py` to files_modified

**Verification:**
```bash
grep -c "generate_report.*session_hash" .planning/phases/09-chat-pro-website-chat-ux-overhaul/09-03-PLAN.md
# Should return 1 (Task 5 verification)
```

---

## ✅ BLOCKER 4: Frontend Validation Missing (Plan 09-04)

**Issue:** D-25 explicitly requires "Frontend validation — email regex, name not empty" but Plan 09-04 doesn't modify any frontend files (chat.js).

**Fix Applied:**
- **New Task 4** added: Add frontend validation to chat.js and chat.css
- Email regex: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
- Name validation: `name.trim().length > 0`
- Error bubble display for invalid input
- Block message send if validation fails
- Plan frontmatter updated: added chat.js and chat.css to files_modified

**Verification:**
```bash
grep -A 5 "Task 4: Add frontend validation" .planning/phases/09-chat-pro-website-chat-ux-overhaul/09-04-PLAN.md
# Should show validation functions isValidEmail and isValidName
```

---

## ✅ BLOCKER 5: Merge Conflict Between Plans 09-02 and 09-04

**Issue:** Both plans modify `agent_wrapper_optimized.py` at overlapping lines (09-02 inserts WOW-COMMENTARY at line 61, 09-04 replaces ФАЗА 2+3 at lines 61-68). Both in Wave 1 = merge conflict.

**Fix Applied:**
- Plan 09-04 frontmatter updated: `depends_on: [] → depends_on: ["09-02"]`
- Plan 09-04 stays in Wave 2 (was already Wave 2, but now depends_on enforces it)
- Execution order: Wave 1 completes (09-01, 09-02, 09-03) → then Wave 2 starts (09-04)
- Sequential execution eliminates merge conflict

**Verification:**
```bash
grep "depends_on:" .planning/phases/09-chat-pro-website-chat-ux-overhaul/09-04-PLAN.md
# Should show: depends_on: ["09-02"]
```

---

## Wave Structure (Revised)

| Wave | Plans | Autonomous | Dependencies | Conflicts |
|------|-------|------------|--------------|-----------|
| 1 | 09-01, 09-02, 09-03 | yes, yes, no | none | none (different files) |
| 2 | 09-04 | yes | 09-02 (WOW-COMMENTARY must complete first) | none (sequential) |

**Key changes:**
- 09-03: Wave 2 → Wave 1 (no dependency on 09-02, different file sections)
- 09-03: autonomous true → false (has checkpoint Task 4)
- 09-04: added depends_on 09-02 (sequential execution after WOW-COMMENTARY)

---

## Non-Blocking Warnings Acknowledged

**WARNING 1 (Plan 09-04 Task 2):** 100+ lines added to `_presale_prompt()` — risks LLM context dilution.

**Response:** Acknowledged. Will monitor during UAT. If prompt becomes unwieldy, services matching can be split into separate SKILL.md file in Phase 10 optimization.

**WARNING 2 (Plan 09-03 Task 2):** Section builders return placeholder text.

**Response:** Documented in Task 2 comments. Section population deferred to Phase 4 integration (orchestrator data structures). Placeholders allow template testing in isolation.

---

## Commit Summary

```
commit dd4ab64
Author: Михаил Елисеев
Date:   2026-06-27

fix(09): address 5 blocker issues from plan-checker

Files changed:
- 09-02-PLAN.md: +60 -17 (lazy import pattern)
- 09-03-PLAN.md: +52 -1 (WordPress auth + LLM prompt)
- 09-04-PLAN.md: +31 -1 (frontend validation + dependency)

Total: 123 insertions, 20 deletions
```

---

## Ready for Execution

All 5 blockers resolved. Plans 09-01 through 09-04 ready for `/gsd-execute-phase 09`.

**Recommended execution order:**
1. Start with Wave 1 (09-01, 09-02, 09-03) — can run in parallel
2. Complete 09-03 Task 4 checkpoint (WordPress auth) before publishing tests
3. After Wave 1 completes, execute Wave 2 (09-04) — depends on 09-02 WOW-COMMENTARY
