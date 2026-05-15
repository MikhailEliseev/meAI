# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard >> loads homepage
- Location: tests/e2e/dashboard.spec.ts:4:7

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected: "http://localhost:3000/"
Received: "http://localhost:3000/login?callbackUrl=%2F"
Timeout:  5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    14 × unexpected value "http://localhost:3000/login?callbackUrl=%2F"

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
  3  | test.describe('Dashboard', () => {
  4  |   test('loads homepage', async ({ page }) => {
  5  |     await page.goto('/');
  6  | 
  7  |     // Should load without errors
> 8  |     await expect(page).toHaveURL('/');
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  9  |   });
  10 | 
  11 |   test('has basic HTML structure', async ({ page }) => {
  12 |     await page.goto('/');
  13 | 
  14 |     // Check for basic HTML elements
  15 |     await expect(page.locator('html')).toBeVisible();
  16 |     await expect(page.locator('body')).toBeVisible();
  17 |   });
  18 | 
  19 |   test('loads without console errors', async ({ page }) => {
  20 |     const errors: string[] = [];
  21 | 
  22 |     page.on('console', (msg) => {
  23 |       if (msg.type() === 'error') {
  24 |         errors.push(msg.text());
  25 |       }
  26 |     });
  27 | 
  28 |     await page.goto('/');
  29 |     await page.waitForLoadState('networkidle');
  30 | 
  31 |     // Filter out known acceptable errors (like auth redirects)
  32 |     const criticalErrors = errors.filter(
  33 |       (error) => !error.includes('auth') && !error.includes('session')
  34 |     );
  35 | 
  36 |     expect(criticalErrors.length).toBe(0);
  37 |   });
  38 | 
  39 |   test('has proper meta tags', async ({ page }) => {
  40 |     await page.goto('/');
  41 | 
  42 |     // Check for viewport meta tag
  43 |     const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
  44 |     expect(viewport).toBeTruthy();
  45 |   });
  46 | });
  47 | 
```