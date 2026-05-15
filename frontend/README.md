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
- ✅ Real-time updates (WebSocket)
- ✅ Linear webhook integration (HMAC verification)
- ✅ Toast notifications for real-time events
- ✅ Comprehensive testing (Unit, Integration, E2E)

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
LINEAR_WEBHOOK_SECRET=your-webhook-secret-here
```

### Development

```bash
# Start dev server (with WebSocket support)
npm run dev

# Open http://localhost:3000
```

### Testing

```bash
# Run unit and integration tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage

# Run E2E tests (requires browsers)
npx playwright install  # First time only
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui
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
│   │   ├── projects/      # Projects routes
│   │   └── tasks/         # Tasks routes
│   ├── api/               # API routes
│   │   ├── auth/          # NextAuth endpoints
│   │   ├── linear/        # Linear API endpoints
│   │   └── webhooks/      # Webhook handlers
│   ├── login/             # Login page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── dashboard/         # Dashboard components
│   │   └── WebSocketProvider.tsx  # WebSocket provider
│   ├── shared/            # Shared components
│   │   └── Toaster.tsx    # Toast notifications
│   └── ui/                # UI components
├── hooks/                 # Custom React hooks
│   ├── useWebSocket.ts    # WebSocket connection
│   ├── useNotifications.ts # Toast notifications
│   ├── useProjects.ts     # Projects data
│   └── useIssues.ts       # Issues data
├── lib/                   # Utilities
│   ├── auth.ts            # NextAuth configuration
│   ├── apollo-client.ts   # GraphQL client
│   └── websocket-server.ts # WebSocket server
├── tests/                 # Test files
│   ├── unit/              # Unit tests (27 tests)
│   ├── integration/       # Integration tests (4 tests)
│   └── e2e/               # E2E tests (9 tests)
├── docs/                  # Documentation
│   ├── TESTING.md         # Testing guide
│   ├── WEBSOCKET.md       # WebSocket documentation
│   └── DEPLOYMENT.md      # Deployment guide
├── types/                 # TypeScript types
│   └── next-auth.d.ts     # NextAuth type extensions
├── server.ts              # Custom Next.js server (WebSocket)
├── proxy.ts               # Next.js proxy middleware
├── vitest.config.ts       # Vitest configuration
├── playwright.config.ts   # Playwright configuration
└── package.json
```

## Development Status

**Phase 8: Multi-Tenant Frontend** - COMPLETED ✅

- ✅ Next.js 16+ setup
- ✅ Authentication (NextAuth.js)
- ✅ Dashboard layout
- ✅ Login page
- ✅ Proxy middleware
- ✅ Multi-tenant architecture
- ✅ Linear API integration
- ✅ Projects & tasks views
- ✅ Real-time WebSocket updates
- ✅ Linear webhook integration
- ✅ Toast notifications
- ✅ Comprehensive testing (Unit, Integration, E2E)
- ✅ Documentation (Testing, WebSocket, Deployment)

## Documentation

- [Testing Guide](docs/TESTING.md) - How to write and run tests
- [WebSocket Documentation](docs/WEBSOCKET.md) - Real-time updates architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions

## Key Features

### Real-Time Updates

WebSocket integration provides instant updates from Linear:

```typescript
// Automatic real-time updates
const { projects } = useProjects(); // Auto-updates via WebSocket
const { issues } = useIssues(projectId); // Auto-updates via WebSocket

// Toast notifications for events
useNotifications(); // Shows toasts for task changes
```

### Linear Webhook Integration

Secure webhook handler with HMAC SHA256 verification:

```bash
# Configure in Linear Settings → API → Webhooks
URL: https://your-domain.com/api/webhooks/linear
Secret: [LINEAR_WEBHOOK_SECRET]
Events: Issue, Project, Comment
```

### Testing

Comprehensive test coverage:
- **27 unit tests** - Components and hooks
- **4 integration tests** - API routes and webhooks
- **9 E2E tests** - User flows across 5 browsers

---

**Last Updated:** 2026-05-15
