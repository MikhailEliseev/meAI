# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: websocket.spec.ts >> WebSocket Infrastructure >> handles offline state gracefully
- Location: tests/e2e/websocket.spec.ts:32:7

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected: "http://localhost:3000/"
Received: "http://localhost:3000/login?callbackUrl=%2F"
Timeout:  5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    13 × unexpected value "http://localhost:3000/login?callbackUrl=%2F"

```

```yaml
- heading "AIM Client Portal" [level=2]
- paragraph: Sign in to view your projects
- text: Email
- textbox "Email":
  - /placeholder: client@example.com
- text: Password
- textbox "Password":
  - /placeholder: ••••••••
- button "Sign in"
- paragraph: "Demo credentials:"
- paragraph: client@example.com / password123
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('WebSocket Infrastructure', () => {
  4  |   test('page loads with WebSocket support', async ({ page }) => {
  5  |     await page.goto('/');
  6  |     await page.waitForLoadState('networkidle');
  7  | 
  8  |     // Check that WebSocket global is available
  9  |     const hasWebSocket = await page.evaluate(() => {
  10 |       return typeof WebSocket !== 'undefined';
  11 |     });
  12 | 
  13 |     expect(hasWebSocket).toBe(true);
  14 |   });
  15 | 
  16 |   test('can create WebSocket connection', async ({ page }) => {
  17 |     await page.goto('/');
  18 | 
  19 |     // Check that WebSocket constructor is available
  20 |     const canCreateWS = await page.evaluate(() => {
  21 |       try {
  22 |         // Just check constructor exists, don't actually connect
  23 |         return typeof WebSocket === 'function';
  24 |       } catch (e) {
  25 |         return false;
  26 |       }
  27 |     });
  28 | 
  29 |     expect(canCreateWS).toBe(true);
  30 |   });
  31 | 
  32 |   test('handles offline state gracefully', async ({ page, context }) => {
  33 |     // Go offline
  34 |     await context.setOffline(true);
  35 | 
  36 |     // Try to load page
  37 |     await page.goto('/').catch(() => {
  38 |       // Expected to fail offline
  39 |     });
  40 | 
  41 |     // Go back online
  42 |     await context.setOffline(false);
  43 | 
  44 |     // Should be able to load now
  45 |     await page.goto('/');
> 46 |     await expect(page).toHaveURL('/');
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  47 |   });
  48 | });
  49 | 
```