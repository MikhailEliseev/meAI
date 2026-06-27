# Phase 14: Final Integration — Operability & Client Dashboard

**Created:** 2026-05-18
**Status:** PLANNED
**Depends on:** Phase 13 (Landing Page & Marketing)

---

## Reality Check

Phase 7.5 docs say Parts 3-4 are COMPLETED. Code says otherwise:

| Doc Claim | Code Reality |
|-----------|-------------|
| "LinearMixin applied to all Magisters" | Only on SEOMagisterV2 (5/6 Magisters missing) |
| "update_linear_status() works" | No-op — maps status string but never calls LinearClient API |
| "Client dashboard ready" | 3 stub pages (billing/contracts/onboarding) with hardcoded mock data |
| "Web dashboard exists" | No `/dashboard` layout, no auth, no nav, no `/dashboard/tasks` page |
| "Progress API endpoints" | `lead-score/route.ts` returns mock, analytics return mock |

**Bottom line:** Phase 7.5 built the Python CLI tools and infrastructure (genuinely done), but the web-facing dashboard and full Magister integration were never completed.

---

## What's Actually Left

### Part A: Finish LinearMixin → All Magisters (2-3h)

**A1. Fix `update_linear_status()` no-op**
- File: `AIM/src/aim/magisters/linear_mixin.py:55-83`
- Problem: Method maps status string but never fetches state_id or calls LinearClient API
- Fix: Use `self.linear_client.get_states(team_id)` → find state_id by name → `self.linear_client.update_issue(issue_id, state_id)`

**A2. Apply LinearMixin to V2 Magisters**
- ContentMagisterV2 (`content_magister_v2.py`)
- AdsMagisterV2 (`ads_magister_v2.py`)
- AnalyticsMagisterV2 (`analytics_magister_v2.py`)
- Pattern: Same as SEOMagisterV2 integration — add `LinearMixin` inheritance, `linear_client`/`linear_enabled` params, progress tracking in `execute_workflow()`

**A3. Verify integration**
- Run `scripts/test_linear_mock.py` — ensure all 6 Magisters create tasks
- Run `scripts/test_linear_integration.py` with real API key

### Part B: Client Web Dashboard (4-6h)

**B1. Create dashboard layout**
- File: `AIM/frontend/app/(dashboard)/layout.tsx` (NEW)
- Sidebar nav: Tasks, Billing, Contracts, Onboarding, Analytics
- Auth guard: NextAuth session check, redirect to login if unauthenticated
- Tenant check: Only show data for current tenant

**B2. Create /dashboard/tasks page**
- File: `AIM/frontend/app/(dashboard)/tasks/page.tsx` (NEW)
- Fetch tasks from Linear API for the client's project
- Show: task title, status, assignee, due date
- Filter: All / In Progress / Done
- Uses `LINAR_API_KEY` server-side or client-side via API route

**B3. Create /api/dashboard/progress endpoint**
- File: `AIM/frontend/app/api/dashboard/progress/route.ts` (NEW)
- Returns: tasks progress, budget utilization, timeline status
- Uses `ProgressTracker` from `src/meai/tracking/progress_tracker.py`
- Tenant-scoped: only returns data for authenticated client's project

**B4. Replace mock data in existing pages**
- `billing/page.tsx`: Replace hardcoded `customerEmail = "ivan@dentaplus.ru"` with session email
- `contracts/page.tsx`: Replace 4 mock contracts with real data from API
- `onboarding/page.tsx`: Wire to real onboarding flow

**B5. Wire dashboard navigation**
- Add `<DashboardNav />` component
- Links between billing → contracts → tasks → onboarding
- Active state highlighting

---

## Task Breakdown

| ID | Task | Est. | Depends |
|----|------|------|---------|
| 14-A1 | Fix update_linear_status() no-op in LinearMixin | 30min | — |
| 14-A2 | Apply LinearMixin to ContentMagisterV2 | 30min | A1 |
| 14-A3 | Apply LinearMixin to AdsMagisterV2 | 30min | A1 |
| 14-A4 | Apply LinearMixin to AnalyticsMagisterV2 | 30min | A1 |
| 14-A5 | Verify with mock test | 30min | A2-A4 |
| 14-B1 | Create dashboard layout + auth guard | 1h | — |
| 14-B2 | Create /dashboard/tasks page | 1.5h | B1 |
| 14-B3 | Create /api/dashboard/progress endpoint | 1h | — |
| 14-B4 | Replace mock data in billing/contracts/onboarding | 1.5h | B1 |
| 14-B5 | Dashboard navigation component | 30min | B1-B4 |
| 14-B6 | Final E2E verify (auth → dashboard → tasks → billing) | 30min | All |

**Total:** 8 hours (Part A: 2.5h + Part B: 5.5h)

---

## Success Criteria

After Phase 14, the following MUST be true:

1. **Operator → Linear flow works end-to-end:**
   - Delegate task → Linear issue created (all 6 Magister teams)
   - Magister starts work → Linear status updated to "In Progress"
   - Magister completes → Linear status updated to "Done" + summary comment

2. **Client can log in and see their project:**
   - Auth works (NextAuth with tenant isolation)
   - `/dashboard/tasks` shows real tasks from Linear
   - `/dashboard/billing` shows real billing data (not hardcoded email)
   - Navigation between dashboard pages works

3. **No more hardcoded mock data in dashboard pages:**
   - `customerEmail` from session, not string literal
   - Contracts from API, not mock array
   - Progress from ProgressTracker, not stub endpoints

---

## What's NOT in Scope

- Full client onboarding flow (DEV-14 — post-MVP)
- Marketing campaigns (MKT-1..MKT-8 — post-MVP)
- Landing page polish (Миша делает сам)
- Linear webhooks for bidirectional sync (Phase 15 enhancement)
- Real-time dashboard updates via WebSocket (Phase 15 enhancement)
