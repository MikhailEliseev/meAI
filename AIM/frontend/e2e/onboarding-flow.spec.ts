import { test, expect } from '@playwright/test';
import * as path from 'path';

/**
 * E2E Test: Document Upload → AI Processing → Onboarding Workflow
 *
 * User Journey:
 * 1. Navigate to onboarding page
 * 2. Upload documents (clinic info, analytics, ads)
 * 3. AI processes documents
 * 4. See extracted data
 * 5. Sign BAA (Business Associate Agreement)
 * 6. Complete onboarding
 */

test.describe('Document Upload and AI Processing', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to onboarding page (stub URL for Phase 11)
    await page.goto('/onboarding');
  });

  test('should display onboarding page with upload areas', async ({ page }) => {
    // Page title
    await expect(page.locator('h1')).toContainText('Онбординг');

    // Upload areas visible
    await expect(page.locator('text=Загрузите документы клиники')).toBeVisible();
    await expect(page.locator('text=Информация о клинике')).toBeVisible();
    await expect(page.locator('text=Доступы к аналитике')).toBeVisible();
    await expect(page.locator('text=Доступы к рекламе')).toBeVisible();
  });

  test('should upload clinic info document', async ({ page }) => {
    // Create test file
    const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');

    // Upload file
    const fileInput = page.locator('input[type="file"][accept*="pdf"]').first();
    await fileInput.setInputFiles(testFile);

    // File uploaded message
    await expect(page.locator('text=clinic-info.pdf')).toBeVisible({ timeout: 5000 });

    // Processing indicator
    await expect(page.locator('text=Обработка')).toBeVisible();

    // Wait for AI processing
    await page.waitForTimeout(3000);

    // Success message
    await expect(page.locator('text=Документ обработан')).toBeVisible({ timeout: 10000 });
  });

  test('should display extracted data from clinic info', async ({ page }) => {
    // Upload and process document
    const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
    const fileInput = page.locator('input[type="file"][accept*="pdf"]').first();
    await fileInput.setInputFiles(testFile);

    // Wait for processing
    await page.waitForTimeout(5000);

    // Extracted data visible
    await expect(page.locator('text=Извлечённые данные')).toBeVisible();

    // Clinic details
    await expect(page.locator('text=Название клиники')).toBeVisible();
    await expect(page.locator('text=Специализация')).toBeVisible();
    await expect(page.locator('text=Контакты')).toBeVisible();
  });

  test('should validate file type', async ({ page }) => {
    // Try to upload invalid file type
    const invalidFile = path.join(__dirname, '../fixtures/test-image.jpg');
    const fileInput = page.locator('input[type="file"][accept*="pdf"]').first();

    // Upload should be rejected or show error
    await fileInput.setInputFiles(invalidFile);

    // Error message
    await expect(page.locator('text=Неверный формат файла')).toBeVisible({ timeout: 3000 });
  });

  test('should validate file size', async ({ page }) => {
    // Try to upload large file (>10MB)
    // Note: This test requires a large test file
    // For now, we'll skip actual upload and test the UI validation

    // File size limit message visible
    await expect(page.locator('text=Максимальный размер файла: 10 МБ')).toBeVisible();
  });

  test('should upload multiple documents', async ({ page }) => {
    // Upload clinic info
    const clinicFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
    const clinicInput = page.locator('input[type="file"]').first();
    await clinicInput.setInputFiles(clinicFile);
    await page.waitForTimeout(2000);

    // Upload analytics access
    const analyticsFile = path.join(__dirname, '../fixtures/analytics-access.pdf');
    const analyticsInput = page.locator('input[type="file"]').nth(1);
    await analyticsInput.setInputFiles(analyticsFile);
    await page.waitForTimeout(2000);

    // Upload ads access
    const adsFile = path.join(__dirname, '../fixtures/ads-access.pdf');
    const adsInput = page.locator('input[type="file"]').nth(2);
    await adsInput.setInputFiles(adsFile);
    await page.waitForTimeout(2000);

    // All files uploaded
    await expect(page.locator('text=clinic-info.pdf')).toBeVisible();
    await expect(page.locator('text=analytics-access.pdf')).toBeVisible();
    await expect(page.locator('text=ads-access.pdf')).toBeVisible();
  });

  test('should show AI processing progress', async ({ page }) => {
    // Upload document
    const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testFile);

    // Processing stages visible
    await expect(page.locator('text=Загрузка')).toBeVisible();
    await expect(page.locator('text=Извлечение текста')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=AI анализ')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Готово')).toBeVisible({ timeout: 10000 });
  });

  test('should allow editing extracted data', async ({ page }) => {
    // Upload and process document
    const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testFile);
    await page.waitForTimeout(5000);

    // Click edit button
    await page.click('button:has-text("Редактировать")');

    // Edit form visible
    await expect(page.locator('input[name="clinicName"]')).toBeVisible();

    // Edit clinic name
    await page.fill('input[name="clinicName"]', 'Стоматология Новая');

    // Save changes
    await page.click('button:has-text("Сохранить")');

    // Updated data visible
    await expect(page.locator('text=Стоматология Новая')).toBeVisible();
  });

  test('should display confidence scores', async ({ page }) => {
    // Upload and process document
    const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testFile);
    await page.waitForTimeout(5000);

    // Confidence scores visible
    await expect(page.locator('text=Уверенность:')).toBeVisible();
    await expect(page.locator('text=%')).toBeVisible();

    // High confidence (>80%) shown in green
    const highConfidence = page.locator('text=95%').first();
    await expect(highConfidence).toHaveClass(/text-green/);
  });

  test('should handle processing errors gracefully', async ({ page }) => {
    // Upload corrupted file
    const corruptedFile = path.join(__dirname, '../fixtures/corrupted.pdf');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(corruptedFile);

    // Wait for processing attempt
    await page.waitForTimeout(3000);

    // Error message visible
    await expect(page.locator('text=Ошибка обработки')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Попробуйте загрузить другой файл')).toBeVisible();

    // Retry button visible
    await expect(page.locator('button:has-text("Попробовать снова")')).toBeVisible();
  });
});

test.describe('BAA Signature Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/onboarding');

    // Upload documents first (stub)
    // In real test, would upload actual files
    await page.evaluate(() => {
      localStorage.setItem('onboarding_documents_uploaded', 'true');
    });
    await page.reload();
  });

  test('should display BAA signature section after documents uploaded', async ({ page }) => {
    // BAA section visible
    await expect(page.locator('text=Подписание договора')).toBeVisible();
    await expect(page.locator('text=Business Associate Agreement')).toBeVisible();
  });

  test('should display BAA document preview', async ({ page }) => {
    // BAA preview visible
    await expect(page.locator('text=Предварительный просмотр договора')).toBeVisible();

    // Key sections visible
    await expect(page.locator('text=Конфиденциальность данных')).toBeVisible();
    await expect(page.locator('text=Обязательства сторон')).toBeVisible();
  });

  test('should send BAA for signature', async ({ page }) => {
    // Fill signer details
    await page.fill('input[name="signerName"]', 'Иван Петров');
    await page.fill('input[name="signerEmail"]', 'ivan@dentaplus.ru');
    await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');

    // Send for signature
    await page.click('button:has-text("Отправить на подпись")');

    // Success message
    await expect(page.locator('text=Договор отправлен на email')).toBeVisible({ timeout: 5000 });

    // DocuSign link visible
    await expect(page.locator('text=Проверьте почту')).toBeVisible();
  });

  test('should track BAA signature status', async ({ page }) => {
    // Send BAA
    await page.fill('input[name="signerName"]', 'Иван Петров');
    await page.fill('input[name="signerEmail"]', 'ivan@dentaplus.ru');
    await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
    await page.click('button:has-text("Отправить на подпись")');
    await page.waitForTimeout(2000);

    // Status tracking visible
    await expect(page.locator('text=Статус подписания')).toBeVisible();

    // Status: Sent
    await expect(page.locator('text=Отправлено')).toBeVisible();

    // Refresh status button
    await expect(page.locator('button:has-text("Обновить статус")')).toBeVisible();
  });

  test('should complete onboarding after BAA signed', async ({ page }) => {
    // Simulate BAA signed (stub)
    await page.evaluate(() => {
      localStorage.setItem('onboarding_baa_signed', 'true');
    });
    await page.reload();

    // Completion message
    await expect(page.locator('text=Онбординг завершён')).toBeVisible();
    await expect(page.locator('text=Добро пожаловать в AIM Agency')).toBeVisible();

    // Next steps visible
    await expect(page.locator('text=Следующие шаги')).toBeVisible();
    await expect(page.locator('button:has-text("Перейти в панель управления")')).toBeVisible();
  });

  test('should display onboarding progress', async ({ page }) => {
    // Progress bar visible
    await expect(page.locator('text=Прогресс онбординга')).toBeVisible();

    // Steps visible
    await expect(page.locator('text=1. Загрузка документов')).toBeVisible();
    await expect(page.locator('text=2. Проверка данных')).toBeVisible();
    await expect(page.locator('text=3. Подписание договора')).toBeVisible();
    await expect(page.locator('text=4. Завершение')).toBeVisible();

    // Current step highlighted
    const currentStep = page.locator('text=1. Загрузка документов').first();
    await expect(currentStep).toHaveClass(/font-bold/);
  });
});

test.describe('Mobile Onboarding', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should display mobile-optimized onboarding', async ({ page }) => {
    await page.goto('/onboarding');

    // Page title visible
    await expect(page.locator('h1')).toContainText('Онбординг');

    // Upload areas stacked vertically
    await expect(page.locator('text=Информация о клинике')).toBeVisible();
  });

  test('should upload document on mobile', async ({ page }) => {
    await page.goto('/onboarding');

    // Upload file
    const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testFile);

    // File uploaded
    await expect(page.locator('text=clinic-info.pdf')).toBeVisible({ timeout: 5000 });
  });
});
