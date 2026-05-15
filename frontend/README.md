# AIM Client Portal - Frontend

Multi-tenant client dashboard for AIM (AI-first medical marketing agency).

## Tech Stack

- **Framework:** Next.js 16.2.6 (App Router, Turbopack)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4
- **Authentication:** NextAuth.js v5 (JWT)
- **State Management:** Zustand, TanStack Query
- **API:** GraphQL (@apollo/client), Linear API
- **Real-time:** WebSocket (ws)

## Features

- ✅ Authentication with NextAuth.js (JWT)
- ✅ Multi-tenant architecture (tenant isolation)
- ✅ Protected routes with proxy middleware
- ✅ Dashboard layout (sidebar, header)
- ✅ Responsive design (mobile-first)
- ✅ Linear API integration (GraphQL)
- ✅ Projects & tasks views
- ⏳ Real-time updates (WebSocket)

## Getting Started

### Prerequisites

- Node.js 20+
- npm

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local with your credentials
```

### Environment Variables

```bash
# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here

# Linear API
LINEAR_API_KEY=your-linear-api-key-here
```

### Development

```bash
# Start dev server
npm run dev

# Open http://localhost:3000
```

### Demo Credentials

```
Email: client@example.com
Password: password123
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── layout.tsx     # Dashboard layout
│   │   ├── page.tsx       # Dashboard home
│   │   ├── projects/      # Projects routes (TODO)
│   │   └── tasks/         # Tasks routes (TODO)
│   ├── api/               # API routes
│   │   └── auth/          # NextAuth endpoints
│   ├── login/             # Login page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── dashboard/         # Dashboard components
│   ├── ui/               # UI components (TODO)
│   └── shared/           # Shared components (TODO)
├── lib/                  # Utilities
│   └── auth.ts          # NextAuth configuration
├── types/               # TypeScript types
│   └── next-auth.d.ts   # NextAuth type extensions
├── proxy.ts             # Next.js proxy middleware
└── package.json
```

## Development Status

**Phase 8: Multi-Tenant Frontend** - IN PROGRESS

- ✅ Next.js 16+ setup
- ✅ Authentication (NextAuth.js)
- ✅ Dashboard layout
- ✅ Login page
- ✅ Proxy middleware
- ✅ Multi-tenant architecture
- ✅ Linear API integration
- ✅ Projects & tasks views
- ⏳ Real-time updates

---

**Last Updated:** 2026-05-15
