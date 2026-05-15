# Testing Guide

## Overview

This project uses a comprehensive testing strategy with three layers:

1. **Unit Tests** - Component and hook testing with Vitest + React Testing Library
2. **Integration Tests** - API route testing with Vitest
3. **E2E Tests** - Full user flow testing with Playwright

## Test Structure

```
tests/
├── unit/                    # Unit tests for components and hooks
│   ├── useWebSocket.test.ts
│   ├── useProjects.test.ts
│   ├── useIssues.test.ts
│   ├── WebSocketProvider.test.tsx
│   └── Toaster.test.tsx
├── integration/             # Integration tests for API routes
│   └── webhook-api.test.ts
└── e2e/                     # End-to-end tests
    ├── api-routes.spec.ts
    ├── dashboard.spec.ts
    └── websocket.spec.ts
```

## Running Tests

### Unit & Integration Tests (Vitest)

```bash
# Run all unit and integration tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### E2E Tests (Playwright)

```bash
# Install browsers (first time only)
npx playwright install

# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run specific browser
npx playwright test --project=chromium
```

## Test Coverage

Current test coverage:

- **Unit Tests**: 27 tests passing
  - WebSocket hooks (useWebSocket, useNotifications)
  - Data hooks (useProjects, useIssues)
  - Components (WebSocketProvider, Toaster)

- **Integration Tests**: 4 tests passing
  - Webhook signature verification
  - Webhook payload processing

- **E2E Tests**: 9 tests across 5 browsers
  - Basic page loading
  - WebSocket infrastructure
  - Webhook API endpoints

## Writing Tests

### Unit Tests

Unit tests use Vitest and React Testing Library:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with disconnected status', () => {
    const { result } = renderHook(() => useWebSocket());
    expect(result.current.status).toBe('disconnected');
  });
});
```

### Integration Tests

Integration tests verify API routes:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { POST } from '@/app/api/webhooks/linear/route';
import { NextRequest } from 'next/server';

describe('POST /api/webhooks/linear', () => {
  it('processes webhook', async () => {
    const request = new NextRequest('http://localhost:3000/api/webhooks/linear', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    const response = await POST(request);
    expect(response.status).toBe(200);
  });
});
```

### E2E Tests

E2E tests use Playwright:

```typescript
import { test, expect } from '@playwright/test';

test('loads homepage', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL('/');
});
```

## Mocking

### Global Mocks

Global mocks are configured in `vitest.setup.ts`:

- Next.js router (useRouter, usePathname, useSearchParams)
- NextAuth (useSession, SessionProvider)
- WebSocket global

### Test-Specific Mocks

Use `vi.mock()` for test-specific mocks:

```typescript
vi.mock('@/lib/apollo-client', () => ({
  apolloClient: {
    query: vi.fn(),
  },
}));
```

## Environment Variables

Tests require these environment variables:

```bash
# .env.test
LINEAR_WEBHOOK_SECRET=test-secret
LINEAR_API_KEY=test-key
NEXTAUTH_SECRET=test-secret
```

## CI/CD Integration

Tests run automatically in CI:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: npm test -- --run

- name: Run E2E tests
  run: npm run test:e2e
```

## Debugging Tests

### Vitest UI

```bash
npm run test:ui
```

Opens interactive UI at http://localhost:51204

### Playwright UI

```bash
npm run test:e2e:ui
```

Opens Playwright UI with time-travel debugging

### VS Code Debugging

Add to `.vscode/launch.json`:

```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug Vitest Tests",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "test"],
  "console": "integratedTerminal"
}
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use `beforeEach` to reset mocks
3. **Descriptive Names**: Test names should describe behavior
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Mock External Dependencies**: Don't hit real APIs in tests
6. **Test User Behavior**: Focus on what users do, not implementation

## Troubleshooting

### "Cannot find module" errors

Run `npm install` to ensure all dependencies are installed.

### Playwright browser errors

Run `npx playwright install` to download browsers.

### WebSocket connection errors in tests

WebSocket is mocked in tests - check `vitest.setup.ts` for mock configuration.

### Next.js module import errors

Some Next.js modules can't be tested in Vitest - use E2E tests instead.

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
