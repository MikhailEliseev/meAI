# Testing Guide

## Overview

This project uses a comprehensive testing strategy with unit, integration, and E2E tests.

## Test Stack

- **Unit/Integration Tests:** Vitest + React Testing Library
- **E2E Tests:** Playwright
- **Coverage:** v8

## Running Tests

```bash
# Run all unit tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e:ui
```

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── useWebSocket.test.ts
│   ├── useProjects.test.ts
│   ├── useIssues.test.ts
│   ├── WebSocketProvider.test.tsx
│   └── Toaster.test.tsx
├── integration/             # Integration tests
│   └── webhook-api.test.ts
└── e2e/                     # E2E tests
    ├── dashboard.spec.ts
    ├── api-routes.spec.ts
    └── websocket.spec.ts
```

## Test Coverage

Current coverage (as of 2026-05-15):

```
Statements   : 58.58% ( 116/198 )
Branches     : 38.82% ( 33/85 )
Functions    : 50% ( 17/34 )
Lines        : 58.58% ( 116/198 )
```

### Coverage by Component

| Component | Statements | Branches | Functions | Lines |
|-----------|-----------|----------|-----------|-------|
| useWebSocket.ts | 44.57% | 35.48% | 38.46% | 45.12% |
| useProjects.ts | 70% | 50% | 50% | 72.41% |
| useIssues.ts | 63.88% | 35.71% | 42.85% | 67.64% |
| WebSocketProvider.tsx | 100% | 50% | 100% | 100% |
| webhook route | 60.86% | 38.46% | 60% | 60.86% |

## Unit Tests (27 tests)

### useWebSocket Hook (8 tests)
- ✅ Initializes with disconnected status
- ✅ Provides send function
- ✅ Provides connect function
- ✅ Provides disconnect function
- ✅ Tracks reconnection attempts
- ✅ Accepts onConnect callback
- ✅ Accepts onMessage callback
- ✅ Accepts onDisconnect callback

### useProjects Hook (6 tests)
- ✅ Fetches projects on mount
- ✅ Handles loading state
- ✅ Handles error state
- ✅ Provides refetch function
- ✅ Updates on WebSocket message
- ✅ Filters by tenant

### useIssues Hook (6 tests)
- ✅ Fetches issues for project
- ✅ Handles loading state
- ✅ Handles error state
- ✅ Provides refetch function
- ✅ Updates on WebSocket message
- ✅ Adds new tasks on create event

### WebSocketProvider (3 tests)
- ✅ Renders children
- ✅ Shows connection status
- ✅ Handles connection errors

### Toaster (2 tests)
- ✅ Renders toast container
- ✅ Applies custom styling

### Webhook API (2 tests)
- ✅ Validates webhook signature
- ✅ Handles webhook events

## E2E Tests (25 passing)

### Dashboard Tests
- ✅ Loads homepage
- ✅ Loads without console errors
- ✅ Shows projects list
- ✅ Shows project details
- ✅ Shows tasks view

### API Routes Tests
- ✅ Rejects invalid signature
- ✅ Handles missing webhook secret
- ✅ Processes valid webhooks

### WebSocket Tests
- ✅ Connects to WebSocket server
- ✅ Receives real-time updates
- ✅ Handles offline state gracefully

## Writing Tests

### Unit Test Example

```typescript
import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('useWebSocket', () => {
  it('initializes with disconnected status', () => {
    const { result } = renderHook(() => useWebSocket());
    expect(result.current.status).toBe('disconnected');
  });
});
```

### E2E Test Example

```typescript
import { test, expect } from '@playwright/test';

test('loads homepage', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

## Mocking

### Mock WebSocket

```typescript
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    status: 'connected',
    isConnected: true,
    send: vi.fn(),
  })),
}));
```

### Mock Next-Auth

```typescript
vi.mock('next-auth/react', () => ({
  useSession: () => ({
    data: { user: { id: 'user-1' } },
    status: 'authenticated',
  }),
}));
```

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Push to main branch
- Pre-commit hooks (optional)

## Troubleshooting

### E2E Tests Failing

1. **Dev server not running:**
   ```bash
   npm run dev
   ```

2. **Port already in use:**
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

3. **Browser not installed:**
   ```bash
   npx playwright install
   ```

### Unit Tests Failing

1. **Clear cache:**
   ```bash
   npm run test -- --clearCache
   ```

2. **Update snapshots:**
   ```bash
   npm run test -- -u
   ```

## Best Practices

1. **Test behavior, not implementation**
   - Focus on what the user sees and does
   - Avoid testing internal state

2. **Keep tests isolated**
   - Each test should be independent
   - Use beforeEach/afterEach for setup/cleanup

3. **Use meaningful test names**
   - Describe what the test does
   - Use "should" or "it" format

4. **Mock external dependencies**
   - API calls
   - WebSocket connections
   - Third-party libraries

5. **Test edge cases**
   - Error states
   - Loading states
   - Empty states

## Future Improvements

- [ ] Increase coverage to 80%+
- [ ] Add visual regression tests
- [ ] Add performance tests
- [ ] Add accessibility tests (axe-core)
- [ ] Add mutation testing
- [ ] Add contract tests for API
