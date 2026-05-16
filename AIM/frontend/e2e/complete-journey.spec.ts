import { test, expect } from '@playwright/test';
import * as path from 'path';

/**
 * E2E Test: Complete User Journey (End-to-End Integration)
 *
 * Full Flow:
 * 1. Landing page → Contact form → Lead scoring
 * 2. Email sequence triggered
 * 3. Payment → Invoice generation
 * 4. Document upload → AI processing
 * 5. BAA signature → Onboarding complete
 *
 * This test validates the entire system integration.
 */

test.describe('Complete User Journey', () => {
  test('should complete full onboarding flow from landing to completion', async ({ page }) => {
    // ============================================
    // STEP 1: Landing Page → Contact Form
    // ============================================
    await page.goto('/');

    // Verify landing page loaded
    await expect(page.locator('h1')).toContainText('AI-маркетинг для медицинских клиник');

    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Fill contact form
    await page.fill('input[name="name"]', 'Иван Петров');
    await page.fill('input[name="phone"]', '+79991234567');
    await page.fill('input[name="email"]', 'ivan.petrov.test@dentaplus.ru');
    await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
    await page.selectOption('select[name="specialty"]', 'dentistry');
    await page.fill('textarea[name="message"]', 'Ищем агентство для продвижения клиники. Бюджет 300K/месяц.');

    // Accept consent
    await page.check('input[type="checkbox"][name="consent"]');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for success
    await expect(page.locator('text=Спасибо за заявку')).toBeVisible({ timeout: 10000 });

    // ============================================
    // STEP 2: Lead Scoring (happens in background)
    // ============================================
    // Lead scored as HOT (dentistry + Moscow + high budget)
    // Email sequence triggered automatically
    // Linear issue created automatically

    // Wait for background processing
    await page.waitForTimeout(2000);

    // ============================================
    // STEP 3: Navigate to Billing
    // ============================================
    await page.goto('/billing');

    // Verify billing page loaded
    await expect(page.locator('h1')).toContainText('Оплата');

    // Select Professional plan (250K RUB/month)
    await page.click('button:has-text("Выбрать Professional")');

    // Fill payment form
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
    await page.fill('input[placeholder="MM/YY"]', '12/25');
    await page.fill('input[placeholder="123"]', '123');
    await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');

    // Submit payment
    await page.click('button[type="submit"]:has-text("Оплатить")');

    // Wait for payment processing
    await expect(page.locator('text=Платёж успешно выполнен')).toBeVisible({ timeout: 10000 });

    // Verify invoice created
    await expect(page.locator('text=AIM-2026-')).toBeVisible();
    await expect(page.locator('text=300 000 ₽')).toBeVisible(); // Professional with VAT

    // ============================================
    // STEP 4: Navigate to Onboarding
    // ============================================
    await page.goto('/onboarding');

    // Verify onboarding page loaded
    await expect(page.locator('h1')).toContainText('Онбординг');

    // Upload clinic info document
    const clinicFile = path.join(__dirname, 'fixtures/clinic-info.pdf');
    const clinicInput = page.locator('input[type="file"]').first();
    await clinicInput.setInputFiles(clinicFile);

    // Wait for AI processing
    await expect(page.locator('text=Обработка')).toBeVisible();
    await expect(page.locator('text=Документ обработан')).toBeVisible({ timeout: 15000 });

    // Upload analytics access document
    const analyticsFile = path.join(__dirname, 'fixtures/analytics-access.pdf');
    const analyticsInput = page.locator('input[type="file"]').nth(1);
    await analyticsInput.setInputFiles(analyticsFile);
    await page.waitForTimeout(3000);

    // Upload ads access document
    const adsFile = path.join(__dirname, 'fixtures/ads-access.pdf');
    const adsInput = page.locator('input[type="file"]').nth(2);
    await adsInput.setInputFiles(adsFile);
    await page.waitForTimeout(3000);

    // Verify all documents uploaded
    await expect(page.locator('text=clinic-info.pdf')).toBeVisible();
    await expect(page.locator('text=analytics-access.pdf')).toBeVisible();
    await expect(page.locator('text=ads-access.pdf')).toBeVisible();

    // ============================================
    // STEP 5: BAA Signature
    // ============================================
    // Scroll to BAA section
    await page.locator('text=Подписание договора').scrollIntoViewIfNeeded();

    // Fill signer details
    await page.fill('input[name="signerName"]', 'Иван Петров');
    await page.fill('input[name="signerEmail"]', 'ivan.petrov.test@dentaplus.ru');
    await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');

    // Send for signature
    await page.click('button:has-text("Отправить на подпись")');

    // Verify BAA sent
    await expect(page.locator('text=Договор отправлен на email')).toBeVisible({ timeout: 5000 });

    // ============================================
    // STEP 6: Simulate BAA Signed (for E2E test)
    // ============================================
    // In production, user would sign via DocuSign
    // For E2E test, we simulate the signed status
    await page.evaluate(() => {
      localStorage.setItem('onboarding_baa_signed', 'true');
    });
    await page.reload();

    // ============================================
    // STEP 7: Onboarding Complete
    // ============================================
    await expect(page.locator('text=Онбординг завершён')).toBeVisible();
    await expect(page.locator('text=Добро пожаловать в AIM Agency')).toBeVisible();

    // Verify next steps visible
    await expect(page.locator('text=Следующие шаги')).toBeVisible();
    await expect(page.locator('button:has-text("Перейти в панель управления")')).toBeVisible();

    // ============================================
    // VERIFICATION: Check all data persisted
    // ============================================
    // Navigate to analytics dashboard
    await page.goto('/analytics');

    // Verify lead appears in analytics
    await expect(page.locator('text=Всего лидов')).toBeVisible();
    await expect(page.locator('text=Горячие лиды')).toBeVisible();

    // Navigate back to billing
    await page.goto('/billing');

    // Verify payment history shows invoice
    await expect(page.locator('text=AIM-2026-')).toBeVisible();
    await expect(page.locator('text=Оплачено')).toBeVisible();

    // ============================================
    // SUCCESS: Full journey completed
    // ============================================
    console.log('✅ Complete user journey test passed!');
  });

  test('should handle errors gracefully throughout the journey', async ({ page }) => {
    // ============================================
    // Test error handling at each step
    // ============================================

    // STEP 1: Invalid contact form submission
    await page.goto('/');
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Обязательное поле')).toBeVisible();

    // STEP 2: Invalid payment card
    await page.goto('/billing');
    await page.click('button:has-text("Выбрать Starter")');
    await page.fill('input[placeholder="1234 5678 9012 3456"]', '1234567890123456');
    await page.blur('input[placeholder="1234 5678 9012 3456"]');
    await expect(page.locator('text=Неверный номер карты')).toBeVisible();

    // STEP 3: Invalid file upload
    await page.goto('/onboarding');
    const invalidFile = path.join(__dirname, 'fixtures/test-image.jpg');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(invalidFile);
    await expect(page.locator('text=Неверный формат файла')).toBeVisible({ timeout: 3000 });

    // STEP 4: Corrupted file processing
    const corruptedFile = path.join(__dirname, 'fixtures/corrupted.pdf');
    await fileInput.setInputFiles(corruptedFile);
    await expect(page.locator('text=Ошибка обработки')).toBeVisible({ timeout: 10000 });

    console.log('✅ Error handling test passed!');
  });

  test('should maintain state across page reloads', async ({ page }) => {
    // ============================================
    // Test state persistence
    // ============================================

    // Fill contact form partially
    await page.goto('/');
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
    await page.fill('input[name="name"]', 'Иван Петров');
    await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
    await page.waitForTimeout(2000); // Wait for auto-save

    // Reload page
    await page.reload();
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Verify draft restored
    await expect(page.locator('input[name="name"]')).toHaveValue('Иван Петров');
    await expect(page.locator('input[name="email"]')).toHaveValue('ivan@dentaplus.ru');

    console.log('✅ State persistence test passed!');
  });
});

test.describe('Performance and Accessibility', () => {
  test('should load landing page within 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;

    // Verify page loaded
    await expect(page.locator('h1')).toBeVisible();

    // Check load time
    expect(loadTime).toBeLessThan(3000);
    console.log(`✅ Landing page loaded in ${loadTime}ms`);
  });

  test('should have accessible form labels', async ({ page }) => {
    await page.goto('/');
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Check for accessible labels
    const nameInput = page.locator('input[name="name"]');
    const nameLabel = await nameInput.getAttribute('aria-label');
    expect(nameLabel).toBeTruthy();

    const emailInput = page.locator('input[name="email"]');
    const emailLabel = await emailInput.getAttribute('aria-label');
    expect(emailLabel).toBeTruthy();

    console.log('✅ Accessibility test passed!');
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    // Check h1 exists and is unique
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBe(1);

    // Check h2 headings exist
    const h2Count = await page.locator('h2').count();
    expect(h2Count).toBeGreaterThan(0);

    console.log('✅ Heading hierarchy test passed!');
  });
});
