# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: api-routes.spec.ts >> Webhook API >> rejects invalid signature
- Location: tests/e2e/api-routes.spec.ts:4:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 401
Received: 200
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Webhook API', () => {
  4  |   test('rejects invalid signature', async ({ request }) => {
  5  |     const payload = {
  6  |       action: 'create',
  7  |       type: 'Issue',
  8  |       data: { id: 'issue-1', title: 'Test' },
  9  |       organizationId: 'org-1',
  10 |       webhookTimestamp: Date.now(),
  11 |       webhookId: 'webhook-1',
  12 |     };
  13 | 
  14 |     const response = await request.post('/api/webhooks/linear', {
  15 |       headers: {
  16 |         'linear-signature': 'a'.repeat(64), // Invalid signature
  17 |         'content-type': 'application/json',
  18 |       },
  19 |       data: JSON.stringify(payload),
  20 |     });
  21 | 
> 22 |     expect(response.status()).toBe(401);
     |                               ^ Error: expect(received).toBe(expected) // Object.is equality
  23 |     const data = await response.json();
  24 |     expect(data.error).toContain('Invalid signature');
  25 |   });
  26 | 
  27 |   test('handles missing webhook secret', async ({ request }) => {
  28 |     const payload = {
  29 |       action: 'create',
  30 |       type: 'Issue',
  31 |       data: { id: 'issue-1', title: 'Test' },
  32 |       organizationId: 'org-1',
  33 |       webhookTimestamp: Date.now(),
  34 |       webhookId: 'webhook-1',
  35 |     };
  36 | 
  37 |     // This test assumes LINEAR_WEBHOOK_SECRET is set in .env
  38 |     // If not set, should return 500
  39 |     const response = await request.post('/api/webhooks/linear', {
  40 |       headers: {
  41 |         'content-type': 'application/json',
  42 |       },
  43 |       data: JSON.stringify(payload),
  44 |     });
  45 | 
  46 |     // Either 200 (secret is set and no signature check) or 500 (secret not set)
  47 |     expect([200, 500]).toContain(response.status());
  48 |   });
  49 | });
  50 | 
```