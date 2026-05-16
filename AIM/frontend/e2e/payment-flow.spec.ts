import { test, expect } from '@playwright/test';

/**
 * E2E Test: Payment Flow → Invoice Generation → Webhook Handling
 *
 * User Journey:
 * 1. Navigate to billing page
 * 2. See pricing plans
 * 3. Fill payment form
 * 4. Submit payment → Invoice generated
 * 5. See payment history
 * 6. Download invoice
 */

test.describe('Payment Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/billing');
  });

  test('should display billing page with payment form and history', async ({ page }) => {
    // Page title
    await expect(page.locator('h1')).toContainText('Оплата');

    // Payment form visible
    await expect(page.locator('text=Выберите тариф')).toBeVisible();

    // Payment history visible
    await expect(page.locator('text=История платежей')).toBeVisible();
  });

  test('should display three pricing plans', async ({ page }) => {
    // Starter plan
    await expect(page.locator('text=Starter')).toBeVisible();
    await expect(page.locator('text=150 000 ₽')).toBeVisible();

    // Professional plan (recommended)
    await expect(page.locator('text=Professional')).toBeVisible();
    await expect(page.locator('text=250 000 ₽')).toBeVisible();
    await expect(page.locator('text=Рекомендуем')).toBeVisible();

    // Enterprise plan
    await expect(page.locator('text=Enterprise')).toBeVisible();
    await expect(page.locator('text=500 000 ₽')).toBeVisible();
  });

  test('should select plan and fill payment form', async ({ page }) => {
    // Select Professional plan
    await page.click('button:has-text("Выбрать Professional")');

    // Payment form visible
    await expect(page.locator('text=Оплата тарифа Professional')).toBeVisible();

    // Fill card details
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
    await page.fill('input[placeholder="MM/YY"]', '12/25');
    await page.fill('input[placeholder="123"]', '123');
    await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');

    // Card number formatted
    await expect(page.locator('input[placeholder="1234 5678 9012 3456"]')).toHaveValue('4111 1111 1111 1111');

    // Expiry formatted
    await expect(page.locator('input[placeholder="MM/YY"]')).toHaveValue('12/25');
  });

  test('should validate card number with Luhn algorithm', async ({ page }) => {
    // Select plan
    await page.click('button:has-text("Выбрать Starter")');

    // Fill invalid card number
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '1234567890123456');
    await page.blur('input[placeholder="1234 5678 9012 3456"]');

    // Validation error
    await expect(page.locator('text=Неверный номер карты')).toBeVisible();

    // Fill valid card number (Visa test card)
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
    await page.blur('input[placeholder="1234 5678 9012 3456"]');

    // Error gone
    await expect(page.locator('text=Неверный номер карты')).not.toBeVisible();
  });

  test('should validate expiry date', async ({ page }) => {
    // Select plan
    await page.click('button:has-text("Выбрать Starter")');

    // Fill expired date
    await page.fill('input[placeholder="MM/YY"]', '01/20');
    await page.blur('input[placeholder="MM/YY"]');

    // Validation error
    await expect(page.locator('text=Карта просрочена')).toBeVisible();

    // Fill future date
    await page.fill('input[placeholder="MM/YY"]', '12/30');
    await page.blur('input[placeholder="MM/YY"]');

    // Error gone
    await expect(page.locator('text=Карта просрочена')).not.toBeVisible();
  });

  test('should validate CVV', async ({ page }) => {
    // Select plan
    await page.click('button:has-text("Выбрать Starter")');

    // Fill invalid CVV (too short)
    await page.fill('input[placeholder="123"]', '12');
    await page.blur('input[placeholder="123"]');

    // Validation error
    await expect(page.locator('text=CVV должен быть 3-4 цифры')).toBeVisible();

    // Fill valid CVV
    await page.fill('input[placeholder="123"]', '123');
    await page.blur('input[placeholder="123"]');

    // Error gone
    await expect(page.locator('text=CVV должен быть 3-4 цифры')).not.toBeVisible();
  });

  test('should submit payment and generate invoice', async ({ page }) => {
    // Select plan
    await page.click('button:has-text("Выбрать Professional")');

    // Fill payment form
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
    await page.fill('input[placeholder="MM/YY"]', '12/25');
    await page.fill('input[placeholder="123"]', '123');
    await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');

    // Submit payment
    await page.click('button[type="submit"]:has-text("Оплатить")');

    // Loading state
    await expect(page.locator('text=Обработка платежа')).toBeVisible();

    // Success message
    await expect(page.locator('text=Платёж успешно выполнен')).toBeVisible({ timeout: 10000 });

    // Invoice appears in history
    await expect(page.locator('text=AIM-2026-')).toBeVisible();
    await expect(page.locator('text=300 000 ₽')).toBeVisible(); // Professional with VAT
  });

  test('should display payment history with invoices', async ({ page }) => {
    // Payment history section visible
    await expect(page.locator('text=История платежей')).toBeVisible();

    // Filter buttons visible
    await expect(page.locator('button:has-text("Все")')).toBeVisible();
    await expect(page.locator('button:has-text("Оплачено")')).toBeVisible();
    await expect(page.locator('button:has-text("Ожидает оплаты")')).toBeVisible();
    await expect(page.locator('button:has-text("Просрочено")')).toBeVisible();
  });

  test('should filter payment history', async ({ page }) => {
    // Click "Оплачено" filter
    await page.click('button:has-text("Оплачено")');

    // Only paid invoices visible
    await expect(page.locator('text=Оплачено')).toBeVisible();

    // Click "Ожидает оплаты" filter
    await page.click('button:has-text("Ожидает оплаты")');

    // Only pending invoices visible (or empty state)
    const pendingInvoices = page.locator('text=Ожидает оплаты');
    const emptyState = page.locator('text=Нет счетов');
    await expect(pendingInvoices.or(emptyState)).toBeVisible();
  });

  test('should expand invoice details', async ({ page }) => {
    // Submit payment first to have invoice
    await page.click('button:has-text("Выбрать Starter")');
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
    await page.fill('input[placeholder="MM/YY"]', '12/25');
    await page.fill('input[placeholder="123"]', '123');
    await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');
    await page.click('button[type="submit"]:has-text("Оплатить")');
    await page.waitForTimeout(3000);

    // Click invoice to expand
    const invoice = page.locator('text=AIM-2026-').first();
    await invoice.click();

    // Invoice details visible
    await expect(page.locator('text=Детали счёта')).toBeVisible();
    await expect(page.locator('text=Подписка Starter')).toBeVisible();
    await expect(page.locator('text=Итого с НДС')).toBeVisible();
  });

  test('should display security notice', async ({ page }) => {
    // Select plan
    await page.click('button:has-text("Выбрать Starter")');

    // Security notice visible
    await expect(page.locator('text=Защищено ЮKassa')).toBeVisible();
    await expect(page.locator('text=PCI DSS')).toBeVisible();
  });

  test('should display STUB notice in development', async ({ page }) => {
    // Select plan
    await page.click('button:has-text("Выбрать Starter")');

    // STUB notice visible
    await expect(page.locator('text=STUB')).toBeVisible();
    await expect(page.locator('text=Используйте любые данные')).toBeVisible();
  });
});

test.describe('Mobile Payment Flow', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should display mobile-optimized billing page', async ({ page }) => {
    await page.goto('/billing');

    // Page title visible
    await expect(page.locator('h1')).toContainText('Оплата');

    // Pricing plans visible (stacked vertically)
    await expect(page.locator('text=Starter')).toBeVisible();
    await expect(page.locator('text=Professional')).toBeVisible();
    await expect(page.locator('text=Enterprise')).toBeVisible();
  });

  test('should fill payment form on mobile', async ({ page }) => {
    await page.goto('/billing');

    // Select plan
    await page.click('button:has-text("Выбрать Starter")');

    // Fill form
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
    await page.fill('input[placeholder="MM/YY"]', '12/25');
    await page.fill('input[placeholder="123"]', '123');
    await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');

    // Submit
    await page.click('button[type="submit"]:has-text("Оплатить")');

    // Success message
    await expect(page.locator('text=Платёж успешно выполнен')).toBeVisible({ timeout: 10000 });
  });
});
