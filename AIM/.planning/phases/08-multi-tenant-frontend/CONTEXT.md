---
phase: 8
name: Multi-tenant Frontend Platform
status: planning
created: 2026-05-16T19:44:54Z
---

# Phase 8: Multi-tenant Frontend Platform

## Goal

Build complete frontend platform with landing page, client dashboards, and admin panel. Implement multi-tenant architecture with role-based access control.

## Context

**Current State:**
- ✅ Backend API operational (FastAPI)
- ✅ Database with SQLAlchemy async ORM
- ✅ Event Bus and Event Store
- ✅ Magisters and Subagents implemented
- ✅ Testing infrastructure complete (122 tests)
- ⏳ Phase 7 (Production Deployment) planned but not executed

**What We're Building:**
Full-stack multi-tenant SaaS platform for iamaim.ru with:
- Landing page (marketing, pricing, contact)
- Client dashboard (projects, analytics, workflows)
- Admin panel (user/tenant management, monitoring)
- Authentication system (JWT, RBAC)
- Multi-tenant backend (tenant isolation)

## Architecture

```
iamaim.ru/                    → Landing page (Next.js SSG)
iamaim.ru/app/                → Client dashboard (auth required)
iamaim.ru/admin/              → Admin panel (super-admin only)
iamaim.ru/api/                → API endpoints (FastAPI backend)
```

## Requirements

### Frontend Requirements

**Landing Page:**
- Hero section with value proposition
- Features showcase (AI-first agency capabilities)
- Pricing plans (tiered pricing for medical marketing)
- Contact form (lead capture)
- SEO optimization (meta tags, structured data)
- Performance: < 2s load time

**Authentication System:**
- JWT-based auth with httpOnly cookies
- Role-based access control (RBAC): client, admin, super-admin
- Multi-tenant user management
- Session management with refresh tokens
- Password reset flow
- Email verification

**Client Dashboard:**
- Project/campaign overview (active campaigns, metrics)
- Analytics and reports (SEO, Content, Ads performance)
- Workflow execution (trigger Magisters, view results)
- Settings and profile (user preferences, API keys)
- Real-time updates via WebSocket

**Admin Panel:**
- User management (CRUD, role assignment)
- Tenant management (create, configure, billing)
- System monitoring (health checks, metrics)
- Configuration (feature flags, limits)
- Audit logs

### Backend Requirements

**Multi-tenant Architecture:**
- Tenant isolation (tenant_id in all tables)
- RBAC middleware (check permissions on every request)
- API endpoints for frontend (REST + GraphQL optional)
- WebSocket for real-time updates
- Rate limiting per tenant

**Database Schema:**
```sql
-- Multi-tenant tables
users (id, tenant_id, email, role, ...)
tenants (id, name, plan, limits, ...)
projects (id, tenant_id, name, status, ...)
campaigns (id, project_id, type, metrics, ...)
```

## Tech Stack

**Frontend:**
- Next.js 14+ (App Router, Server Components)
- React 18+ (Hooks, Suspense)
- TypeScript (strict mode)
- Tailwind CSS (utility-first styling)
- shadcn/ui (component library)
- Radix UI (accessible primitives)

**State Management:**
- React Query (server state, caching)
- Zustand (client state)

**Backend:**
- FastAPI (existing, extend with new endpoints)
- SQLAlchemy async (multi-tenant queries)
- JWT tokens (python-jose)
- WebSocket (FastAPI WebSocket support)

**Deployment:**
- Frontend: Vercel (Next.js optimized)
- Backend: Docker + nginx (existing setup)
- Database: PostgreSQL (upgrade from SQLite)

## Success Metrics

**Performance:**
- [ ] Landing page loads < 2s
- [ ] Dashboard loads < 3s
- [ ] API response time < 200ms (p95)
- [ ] WebSocket latency < 100ms

**Functionality:**
- [ ] Authentication flow works end-to-end
- [ ] Client can create and manage projects
- [ ] Admin can manage multiple tenants
- [ ] All roles have correct permissions
- [ ] Real-time updates work via WebSocket

**Quality:**
- [ ] 80%+ test coverage (frontend + backend)
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] SEO score > 90 (Lighthouse)
- [ ] Security audit passed (OWASP Top 10)

## Constraints

**Time:** 12-16 hours estimated
**Scope:** MVP with core features, no advanced analytics yet
**Resources:** Solo developer + AI assistant
**Budget:** $0 (use free tiers: Vercel, Supabase optional)

## Dependencies

**External:**
- Next.js 14+
- React 18+
- Tailwind CSS 3+
- shadcn/ui
- FastAPI (existing)
- PostgreSQL (upgrade from SQLite)

**Internal:**
- ✅ Backend API operational
- ✅ Database schema (extend for multi-tenancy)
- ⏳ DNS configured for iamaim.ru
- ⏳ SSL certificates installed

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Multi-tenant complexity | High | Start with simple tenant_id isolation |
| WebSocket scaling | Medium | Use Redis pub/sub for multi-instance |
| Frontend state management | Medium | Use React Query for server state |
| Authentication security | High | Use battle-tested libraries (NextAuth.js) |
| Time overrun | Medium | Focus on MVP, defer advanced features |

## Out of Scope (Phase 8)

- Advanced analytics dashboards (Phase 9)
- Billing integration (Phase 10)
- Mobile app (future)
- Multi-language support (future)
- Advanced RBAC (custom permissions, Phase 9)

## Russian Market Adaptation

**Применяется:**
- ✅ Next.js, React, TypeScript (технические решения с Запада)
- ✅ JWT auth, RBAC (универсальные паттерны)
- ✅ Multi-tenant architecture (best practices)

**Адаптируется:**
- ⚠️ Payment integration → ЮKassa/CloudPayments (не Stripe)
- ⚠️ Email service → UniSender/SendPulse (или SendGrid, работает в РФ)
- ⚠️ Compliance → ФЗ-152 (не GDPR/HIPAA)

**Откладывается:**
- ⏸️ Payment processors (Phase 10)
- ⏸️ ЭЦП integration (Phase 11)

## Next Steps

1. **Research Phase** (optional, 1-2 hours):
   - Deep research: Next.js 14 App Router best practices
   - GitHub search: multi-tenant SaaS boilerplates
   - Study: shadcn/ui + Radix UI patterns

2. **Planning Phase** (this phase):
   - Break down into 4-6 sub-plans
   - Estimate time per plan
   - Define acceptance criteria

3. **Execution Phase** (12-16 hours):
   - Implement plans sequentially
   - Test each component
   - Deploy to staging

## References

- ROADMAP.md: Phase 8 overview
- CLAUDE.md: Russian Market Adaptation Rule
- SESSION.md: Current project status
