import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('loads homepage', async ({ page }) => {
    await page.goto('/');

    // Should load without errors
    await expect(page).toHaveURL('/');
  });

  test('has basic HTML structure', async ({ page }) => {
    await page.goto('/');

    // Check for basic HTML elements
    await expect(page.locator('html')).toBeVisible();
    await expect(page.locator('body')).toBeVisible();
  });

  test('loads without console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors (like auth redirects)
    const criticalErrors = errors.filter(
      (error) => !error.includes('auth') && !error.includes('session')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('has proper meta tags', async ({ page }) => {
    await page.goto('/');

    // Check for viewport meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toBeTruthy();
  });
});
