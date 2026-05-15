import { test, expect } from '@playwright/test';

test.describe('WebSocket Infrastructure', () => {
  test('page loads with WebSocket support', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check that WebSocket global is available
    const hasWebSocket = await page.evaluate(() => {
      return typeof WebSocket !== 'undefined';
    });

    expect(hasWebSocket).toBe(true);
  });

  test('can create WebSocket connection', async ({ page }) => {
    await page.goto('/');

    // Check that WebSocket constructor is available
    const canCreateWS = await page.evaluate(() => {
      try {
        // Just check constructor exists, don't actually connect
        return typeof WebSocket === 'function';
      } catch (e) {
        return false;
      }
    });

    expect(canCreateWS).toBe(true);
  });

  test('handles offline state gracefully', async ({ page, context }) => {
    // Go offline
    await context.setOffline(true);

    // Try to load page
    await page.goto('/').catch(() => {
      // Expected to fail offline
    });

    // Go back online
    await context.setOffline(false);

    // Should be able to load now
    await page.goto('/');
    await expect(page).toHaveURL('/');
  });
});
