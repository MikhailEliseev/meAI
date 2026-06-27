# Phase 8: Multi-tenant Frontend Platform - Research

**Researched:** 2026-05-15
**Domain:** Full-stack multi-tenant SaaS platform (Next.js + FastAPI)
**Confidence:** HIGH

## Summary

Phase 8 focuses on building a production-ready multi-tenant SaaS platform with three distinct user-facing applications: a public landing page, authenticated client dashboards, and an admin panel. The architecture leverages Next.js 15 App Router for the frontend with FastAPI backend integration.

**Key Findings:**
- **Multi-tenancy Pattern:** Shared schema with tenant_id column + Row-Level Security (RLS) is optimal for medical marketing SaaS
- **Authentication:** Session-based auth with HTTP-only cookies (more secure than JWT for web apps)
- **Frontend Architecture:** Next.js 15 App Router with Server Components for performance, Client Components for interactivity
- **State Management:** React Query for server state, Zustand for client state
- **Component Library:** shadcn/ui (Radix UI primitives + Tailwind CSS) - production-ready, accessible
- **Backend Integration:** FastAPI CORS middleware + shared session validation

**Primary recommendation:** Build with Next.js 15 App Router + shadcn/ui + FastAPI backend, deploy frontend to Vercel, backend to existing VPS (138.16.224.188).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Public landing page | Next.js SSG | CDN (Vercel Edge) | Static generation for SEO, edge caching for performance |
| User authentication | FastAPI Backend | Next.js Middleware | Backend owns session creation/validation, middleware enforces routes |
| Client dashboard UI | Next.js App Router | — | Server Components for data fetching, Client Components for interactivity |
| Admin panel UI | Next.js App Router | — | Same as client dashboard, role-based access control |
| API endpoints | FastAPI Backend | — | Business logic, database access, multi-tenant isolation |
| Real-time updates | FastAPI WebSocket | Next.js Client | Backend pushes updates, frontend subscribes via WebSocket |
| Multi-tenant isolation | PostgreSQL RLS | FastAPI Middleware | Database enforces row-level security, middleware sets tenant context |
| File uploads | FastAPI Backend | CDN (for serving) | Backend handles upload validation, CDN serves static assets |
| Analytics tracking | Client-side (GA4) | FastAPI (server events) | Client tracks page views, backend tracks business events |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 15.1.x | React framework with App Router | Industry standard for production SaaS, excellent DX, Vercel optimization |
| React | 19.x | UI library | Required by Next.js, Server Components support |
| TypeScript | 5.3.x | Type safety | Prevents runtime errors, better IDE support, industry standard |
| Tailwind CSS | 3.4.x | Utility-first CSS | Fast development, consistent design, small bundle size |
| shadcn/ui | latest | Component library | Accessible (Radix UI), customizable, copy-paste (no npm bloat) |
| FastAPI | 0.109.x | Python backend framework | Already deployed, async support, automatic OpenAPI docs |
| PostgreSQL | 15.x | Database | Row-Level Security support, production-ready, better than SQLite for multi-tenant |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tanstack/react-query | 5.x | Server state management | Data fetching, caching, synchronization with FastAPI |
| zustand | 4.x | Client state management | UI state (modals, forms), simpler than Redux |
| zod | 3.x | Schema validation | Form validation, API response validation |
| react-hook-form | 7.x | Form management | Complex forms with validation |
| next-auth | 5.x (beta) | Authentication | If not using custom FastAPI auth (alternative approach) |
| jose | 5.x | JWT handling | If using JWT tokens (alternative to sessions) |
| axios | 1.x | HTTP client | Alternative to fetch, better error handling |
| socket.io-client | 4.x | WebSocket client | Real-time updates from FastAPI |
| date-fns | 3.x | Date manipulation | Lighter than moment.js |
| recharts | 2.x | Charts library | Dashboard analytics visualization |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Next.js | Remix, SvelteKit | Next.js has better Vercel integration, larger ecosystem |
| shadcn/ui | Material-UI, Ant Design | shadcn/ui is more customizable, no npm dependency bloat |
| PostgreSQL | MySQL, MongoDB | PostgreSQL has native RLS, better for multi-tenant |
| React Query | SWR, Apollo Client | React Query more flexible, better DevTools |
| Zustand | Redux, Jotai | Zustand simpler API, less boilerplate |
| Session auth | JWT tokens | Sessions more secure for web (HTTP-only cookies), JWT better for mobile |

**Installation:**
```bash
# Frontend (Next.js)
npx create-next-app@latest iamaim-frontend --typescript --tailwind --app
cd iamaim-frontend
npm install @tanstack/react-query zustand zod react-hook-form
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install date-fns recharts axios

# Backend (FastAPI) - already installed
pip install fastapi[all] sqlalchemy asyncpg python-jose passlib
```

**Version verification:**
```bash
# Verified 2026-05-15
npm view next version          # 15.1.11
npm view react version         # 19.0.0
npm view @tanstack/react-query version  # 5.28.4
npm view zustand version       # 4.5.2
npm view zod version           # 3.22.4
```

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─── GET / (landing page)
             │    └─> Next.js SSG → Static HTML (cached at edge)
             │
             ├─── GET /app/* (client dashboard)
             │    └─> Next.js Middleware (check session cookie)
             │        ├─ No session → redirect /login
             │        └─ Valid session → render dashboard
             │            └─> Server Component fetches data from FastAPI
             │                └─> Client Component for interactivity
             │
             ├─── GET /admin/* (admin panel)
             │    └─> Next.js Middleware (check session + role)
             │        ├─ Not admin → 403 Forbidden
             │        └─ Admin role → render admin panel
             │
             └─── POST /api/auth/login
                  └─> FastAPI /api/auth/login
                      ├─> Validate credentials
                      ├─> Create session in DB
                      ├─> Set HTTP-only cookie
                      └─> Return user data

┌─────────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND                            │
│  (Deployed on Vercel)                                            │
├─────────────────────────────────────────────────────────────────┤
│  middleware.ts                                                   │
│    ├─ Check session cookie on protected routes                  │
│    ├─ Set tenant context from session                           │
│    └─ Redirect unauthenticated users                            │
│                                                                  │
│  app/                                                            │
│    ├─ (public)/                                                 │
│    │   ├─ page.tsx          # Landing page (SSG)               │
│    │   ├─ login/page.tsx    # Login form                       │
│    │   └─ signup/page.tsx   # Signup form                      │
│    │                                                             │
│    ├─ (authenticated)/                                          │
│    │   └─ app/                                                  │
│    │       ├─ layout.tsx    # Dashboard layout                 │
│    │       ├─ page.tsx      # Dashboard home                   │
│    │       ├─ projects/     # Projects management              │
│    │       └─ settings/     # User settings                    │
│    │                                                             │
│    └─ (admin)/                                                  │
│        └─ admin/                                                │
│            ├─ layout.tsx    # Admin layout                     │
│            ├─ page.tsx      # Admin dashboard                  │
│            ├─ users/        # User management                  │
│            └─ tenants/      # Tenant management                │
└─────────────────────────────────────────────────────────────────┘
             │
             │ HTTP/WebSocket
             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  (Deployed on 138.16.224.188)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Middleware Stack:                                               │
│    ├─ CORS (allow Vercel domain)                               │
│    ├─ Session validation (check cookie)                        │
│    ├─ Tenant context (set from session)                        │
│    └─ Rate limiting                                             │
│                                                                  │
│  Routes:                                                         │
│    ├─ /api/auth/*          # Authentication                    │
│    ├─ /api/v1/projects/*   # Projects CRUD                     │
│    ├─ /api/v1/analytics/*  # Analytics data                    │
│    └─ /ws                  # WebSocket for real-time           │
└─────────────────────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                         │
│  (Row-Level Security enabled)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Tables:                                                         │
│    ├─ tenants (id, name, domain, plan, created_at)            │
│    ├─ users (id, tenant_id, email, role, password_hash)       │
│    ├─ sessions (id, user_id, token, expires_at)               │
│    ├─ projects (id, tenant_id, name, status)                  │
│    └─ analytics (id, tenant_id, project_id, metrics)          │
│                                                                  │
│  RLS Policies:                                                   │
│    ├─ SELECT: WHERE tenant_id = current_setting('app.tenant')│
│    ├─ INSERT: SET tenant_id = current_setting('app.tenant')  │
│    └─ UPDATE/DELETE: WHERE tenant_id = current_setting(...)  │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
iamaim-frontend/                    # Next.js frontend
├── src/
│   ├── app/                        # App Router pages
│   │   ├── (public)/              # Public routes (no auth)
│   │   │   ├── page.tsx           # Landing page
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── (authenticated)/       # Protected routes
│   │   │   └── app/               # Client dashboard
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       ├── projects/
│   │   │       └── settings/
│   │   └── (admin)/               # Admin-only routes
│   │       └── admin/
│   │           ├── layout.tsx
│   │           ├── users/
│   │           └── tenants/
│   ├── components/                 # Reusable components
│   │   ├── ui/                    # shadcn/ui components
│   │   ├── dashboard/             # Dashboard-specific
│   │   └── admin/                 # Admin-specific
│   ├── lib/                        # Utilities
│   │   ├── api.ts                 # API client (axios/fetch)
│   │   ├── auth.ts                # Auth helpers
│   │   └── utils.ts               # General utilities
│   ├── hooks/                      # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   └── useWebSocket.ts
│   ├── stores/                     # Zustand stores
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   └── middleware.ts               # Next.js middleware (auth)
├── public/                         # Static assets
└── package.json

AIM/                                # FastAPI backend (existing)
├── src/aim/
│   ├── api/                        # NEW: API routes
│   │   ├── v1/
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── projects.py        # Projects CRUD
│   │   │   ├── analytics.py       # Analytics endpoints
│   │   │   └── admin.py           # Admin endpoints
│   │   └── deps.py                # Dependencies (get_current_user, etc.)
│   ├── middleware/                 # NEW: Middleware
│   │   ├── tenant.py              # Tenant context
│   │   └── session.py             # Session validation
│   ├── models/                     # NEW: Database models
│   │   ├── tenant.py
│   │   ├── user.py
│   │   └── session.py
│   └── main.py                     # FastAPI app (update with new routes)
└── alembic/                        # Database migrations
```

### Pattern 1: Multi-Tenant Isolation with Row-Level Security

**What:** Database-level tenant isolation using PostgreSQL Row-Level Security (RLS) policies.

**When to use:** When multiple tenants share the same database schema but must never see each other's data.

**Example:**
```sql
-- Source: PostgreSQL official docs + production SaaS patterns

-- 1. Enable RLS on tenant-scoped tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;

-- 2. Create policy: users can only see their tenant's data
CREATE POLICY tenant_isolation_policy ON projects
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE POLICY tenant_isolation_policy ON analytics
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- 3. Set tenant context in FastAPI middleware
-- middleware/tenant.py
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

async def set_tenant_context(request: Request, db: AsyncSession):
    """Set tenant context from authenticated user session"""
    user = request.state.user  # Set by auth middleware
    
    # Set PostgreSQL session variable
    await db.execute(
        text("SET LOCAL app.tenant_id = :tenant_id"),
        {"tenant_id": str(user.tenant_id)}
    )
```

**Benefits:**
- Database enforces isolation (can't bypass in application code)
- No need to add WHERE tenant_id = ? to every query
- Prevents accidental cross-tenant data leaks
- Works with ORMs (SQLAlchemy respects RLS)

### Pattern 2: Session-Based Authentication with HTTP-Only Cookies

**What:** Secure authentication using server-side sessions stored in database, with session ID in HTTP-only cookie.

**When to use:** Web applications where security is critical (medical data). More secure than JWT for browser-based apps.

**Example:**
```typescript
// Source: Next.js official auth guide + Vercel patterns

// lib/auth.ts - Next.js frontend
export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Send cookies
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) throw new Error('Login failed');
  
  // Cookie is set by backend (HTTP-only, Secure, SameSite)
  return response.json();
}

// middleware.ts - Next.js middleware
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const sessionCookie = request.cookies.get('session');
  
  // Protected routes
  if (request.nextUrl.pathname.startsWith('/app')) {
    if (!sessionCookie) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
    
    // Validate session with backend
    const response = await fetch(`${API_URL}/api/auth/validate`, {
      headers: { 'Cookie': `session=${sessionCookie.value}` }
    });
    
    if (!response.ok) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/app/:path*', '/admin/:path*']
};
```

```python
# Source: FastAPI security best practices

# api/v1/auth.py - FastAPI backend
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import secrets

router = APIRouter()

@router.post("/login")
async def login(
    credentials: LoginSchema,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate credentials
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 2. Create session in database
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    session = Session(
        user_id=user.id,
        token=session_token,
        expires_at=expires_at
    )
    db.add(session)
    await db.commit()
    
    # 3. Set HTTP-only cookie
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,      # Prevents JavaScript access (XSS protection)
        secure=True,        # HTTPS only
        samesite="lax",     # CSRF protection
        max_age=7*24*60*60, # 7 days
        domain=".iamaim.ru" # Share across subdomains
    )
    
    return {"user": user.to_dict()}

@router.post("/logout")
async def logout(
    response: Response,
    session: Session = Depends(get_current_session)
):
    # Delete session from database
    await db.delete(session)
    await db.commit()
    
    # Clear cookie
    response.delete_cookie("session")
    return {"message": "Logged out"}
```

**Benefits:**
- More secure than JWT (can't be stolen from localStorage)
- Can revoke sessions immediately (delete from DB)
- No token refresh complexity
- Works seamlessly with Next.js middleware

### Pattern 3: Server Components + Client Components Strategy

**What:** Use React Server Components for data fetching, Client Components for interactivity.

**When to use:** Always in Next.js 15 App Router. Reduces JavaScript bundle, improves performance.

**Example:**
```typescript
// Source: Next.js 15 official docs

// app/app/projects/page.tsx - Server Component (default)
import { ProjectList } from '@/components/ProjectList';
import { getProjects } from '@/lib/api';

export default async function ProjectsPage() {
  // Fetch data on server (no loading state needed)
  const projects = await getProjects();
  
  return (
    <div>
      <h1>Projects</h1>
      {/* Pass data to Client Component */}
      <ProjectList initialProjects={projects} />
    </div>
  );
}

// components/ProjectList.tsx - Client Component
'use client'; // Mark as Client Component

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

export function ProjectList({ initialProjects }) {
  const [filter, setFilter] = useState('all');
  
  // React Query for client-side updates
  const { data: projects } = useQuery({
    queryKey: ['projects', filter],
    queryFn: () => fetchProjects(filter),
    initialData: initialProjects
  });
  
  return (
    <div>
      {/* Interactive filter (needs client-side JS) */}
      <select value={filter} onChange={(e) => setFilter(e.target.value)}>
        <option value="all">All</option>
        <option value="active">Active</option>
      </select>
      
      {/* Render projects */}
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

**Decision tree:**
- Need interactivity (onClick, useState, useEffect)? → Client Component
- Just rendering data? → Server Component
- Fetching data? → Server Component (faster, no loading state)
- Using browser APIs (localStorage, window)? → Client Component

### Pattern 4: Optimistic UI Updates with React Query

**What:** Update UI immediately, then sync with server. Rollback if server fails.

**When to use:** Actions that should feel instant (like, favorite, toggle status).

**Example:**
```typescript
// Source: TanStack Query official docs

// hooks/useProjects.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useUpdateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (project: Project) => 
      fetch(`/api/v1/projects/${project.id}`, {
        method: 'PATCH',
        body: JSON.stringify(project)
      }),
    
    // Optimistic update
    onMutate: async (updatedProject) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['projects'] });
      
      // Snapshot previous value
      const previousProjects = queryClient.getQueryData(['projects']);
      
      // Optimistically update cache
      queryClient.setQueryData(['projects'], (old: Project[]) =>
        old.map(p => p.id === updatedProject.id ? updatedProject : p)
      );
      
      // Return context with snapshot
      return { previousProjects };
    },
    
    // Rollback on error
    onError: (err, updatedProject, context) => {
      queryClient.setQueryData(['projects'], context.previousProjects);
    },
    
    // Refetch on success
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    }
  });
}

// Usage in component
function ProjectCard({ project }) {
  const updateProject = useUpdateProject();
  
  const handleToggleStatus = () => {
    // UI updates immediately, syncs with server in background
    updateProject.mutate({
      ...project,
      status: project.status === 'active' ? 'paused' : 'active'
    });
  };
  
  return (
    <button onClick={handleToggleStatus}>
      {project.status}
    </button>
  );
}
```

### Anti-Patterns to Avoid

- **Anti-pattern:** Storing tenant_id in JWT token
  - **Why bad:** Can't revoke access if tenant is deleted, token can be reused
  - **Do instead:** Store session in database, validate tenant on each request

- **Anti-pattern:** Using localStorage for sensitive data
  - **Why bad:** Accessible by JavaScript (XSS vulnerability)
  - **Do instead:** Use HTTP-only cookies for session tokens

- **Anti-pattern:** Client Components everywhere
  - **Why bad:** Large JavaScript bundle, slower page loads
  - **Do instead:** Server Components by default, Client Components only when needed

- **Anti-pattern:** Fetching data in useEffect
  - **Why bad:** Loading states, race conditions, no caching
  - **Do instead:** React Query for client-side, Server Components for initial data

- **Anti-pattern:** Manual WHERE tenant_id = ? in every query
  - **Why bad:** Easy to forget, security risk
  - **Do instead:** PostgreSQL Row-Level Security (enforced at DB level)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Authentication | Custom auth system | FastAPI session + Next.js middleware | Security is hard, sessions prevent XSS/CSRF |
| Form validation | Manual validation | react-hook-form + zod | Handles edge cases, better UX, type-safe |
| Data fetching | fetch + useState | React Query | Caching, deduplication, background refetch |
| UI components | Custom components | shadcn/ui (Radix UI) | Accessible, tested, customizable |
| Date handling | String manipulation | date-fns | Timezones, locales, edge cases |
| WebSocket reconnection | Manual reconnect logic | socket.io-client | Auto-reconnect, fallback transports |
| Multi-tenant isolation | Application-level filtering | PostgreSQL RLS | Database-enforced, can't bypass |
| CORS configuration | Manual headers | FastAPI CORSMiddleware | Handles preflight, credentials, origins |

**Key insight:** Multi-tenant SaaS has many security pitfalls. Use battle-tested libraries and database-level enforcement rather than application-level checks.

## Common Pitfalls

### Pitfall 1: Cross-Tenant Data Leaks

**What goes wrong:** User from Tenant A sees data from Tenant B due to missing tenant filter.

**Why it happens:** 
- Forgot to add WHERE tenant_id = ? in one query
- Used admin endpoint without tenant check
- Cached data across tenants

**How to avoid:**
```sql
-- Use PostgreSQL Row-Level Security (enforced at DB level)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

```python
# Set tenant context in middleware (every request)
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    if request.state.user:
        await db.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": str(request.state.user.tenant_id)}
        )
    return await call_next(request)
```

**Warning signs:**
- Query doesn't have tenant_id filter
- Admin can see all tenants (should be explicit opt-in)
- Cache key doesn't include tenant_id

### Pitfall 2: Session Fixation Attacks

**What goes wrong:** Attacker sets victim's session ID, then hijacks session after victim logs in.

**Why it happens:**
- Reusing session ID after login
- Not regenerating session token
- Session ID predictable

**How to avoid:**
```python
# ALWAYS regenerate session token after login
@router.post("/login")
async def login(credentials: LoginSchema, response: Response, db: AsyncSession):
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    # Generate NEW session token (not reuse old one)
    session_token = secrets.token_urlsafe(32)  # Cryptographically secure
    
    # Delete old sessions for this user (optional, for single-device login)
    await db.execute(
        delete(Session).where(Session.user_id == user.id)
    )
    
    # Create new session
    session = Session(user_id=user.id, token=session_token, ...)
    db.add(session)
    await db.commit()
    
    response.set_cookie("session", session_token, httponly=True, secure=True)
    return {"user": user.to_dict()}
```

**Warning signs:**
- Session token is predictable (sequential IDs, timestamps)
- Same session token before and after login
- No session expiration

### Pitfall 3: CORS Misconfiguration

**What goes wrong:** 
- Frontend can't call backend (CORS blocked)
- OR: Any origin can call backend (security risk)

**Why it happens:**
- Wildcard CORS (`Access-Control-Allow-Origin: *`) with credentials
- Wrong origin in CORS config
- Missing preflight handling

**How to avoid:**
```python
# FastAPI CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://iamaim.ru",           # Production frontend
        "https://www.iamaim.ru",       # www subdomain
        "http://localhost:3000"        # Local development
    ],
    allow_credentials=True,            # Allow cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600  # Cache preflight for 1 hour
)
```

```typescript
// Next.js API calls must include credentials
fetch(`${API_URL}/api/v1/projects`, {
  credentials: 'include'  // Send cookies with request
})
```

**Warning signs:**
- CORS error in browser console
- Cookies not sent with requests
- Preflight OPTIONS requests failing

### Pitfall 4: N+1 Query Problem in Server Components

**What goes wrong:** Fetching related data in a loop causes hundreds of database queries.

**Why it happens:**
- Fetching projects, then fetching owner for each project in loop
- No eager loading / joins

**How to avoid:**
```python
# BAD: N+1 queries
projects = await db.execute(select(Project))
for project in projects:
    owner = await db.execute(select(User).where(User.id == project.owner_id))
    # 1 query for projects + N queries for owners = N+1

# GOOD: Single query with join
projects = await db.execute(
    select(Project)
    .options(joinedload(Project.owner))  # Eager load relationship
)
# 1 query total
```

```typescript
// Next.js Server Component
export default async function ProjectsPage() {
  // Fetch with relationships in single query
  const projects = await fetch(`${API_URL}/api/v1/projects?include=owner,analytics`)
    .then(r => r.json());
  
  return <ProjectList projects={projects} />;
}
```

**Warning signs:**
- Slow page loads with many items
- Database query count scales with number of items
- Multiple queries for same data

