# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: onboarding-flow.spec.ts >> Document Upload and AI Processing >> should handle processing errors gracefully
- Location: e2e/onboarding-flow.spec.ts:170:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/onboarding
Call log:
  - navigating to "http://localhost:3000/onboarding", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import * as path from 'path';
  3   | 
  4   | /**
  5   |  * E2E Test: Document Upload → AI Processing → Onboarding Workflow
  6   |  *
  7   |  * User Journey:
  8   |  * 1. Navigate to onboarding page
  9   |  * 2. Upload documents (clinic info, analytics, ads)
  10  |  * 3. AI processes documents
  11  |  * 4. See extracted data
  12  |  * 5. Sign BAA (Business Associate Agreement)
  13  |  * 6. Complete onboarding
  14  |  */
  15  | 
  16  | test.describe('Document Upload and AI Processing', () => {
  17  |   test.beforeEach(async ({ page }) => {
  18  |     // Navigate to onboarding page (stub URL for Phase 11)
> 19  |     await page.goto('/onboarding');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/onboarding
  20  |   });
  21  | 
  22  |   test('should display onboarding page with upload areas', async ({ page }) => {
  23  |     // Page title
  24  |     await expect(page.locator('h1')).toContainText('Онбординг');
  25  | 
  26  |     // Upload areas visible
  27  |     await expect(page.locator('text=Загрузите документы клиники')).toBeVisible();
  28  |     await expect(page.locator('text=Информация о клинике')).toBeVisible();
  29  |     await expect(page.locator('text=Доступы к аналитике')).toBeVisible();
  30  |     await expect(page.locator('text=Доступы к рекламе')).toBeVisible();
  31  |   });
  32  | 
  33  |   test('should upload clinic info document', async ({ page }) => {
  34  |     // Create test file
  35  |     const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  36  | 
  37  |     // Upload file
  38  |     const fileInput = page.locator('input[type="file"][accept*="pdf"]').first();
  39  |     await fileInput.setInputFiles(testFile);
  40  | 
  41  |     // File uploaded message
  42  |     await expect(page.locator('text=clinic-info.pdf')).toBeVisible({ timeout: 5000 });
  43  | 
  44  |     // Processing indicator
  45  |     await expect(page.locator('text=Обработка')).toBeVisible();
  46  | 
  47  |     // Wait for AI processing
  48  |     await page.waitForTimeout(3000);
  49  | 
  50  |     // Success message
  51  |     await expect(page.locator('text=Документ обработан')).toBeVisible({ timeout: 10000 });
  52  |   });
  53  | 
  54  |   test('should display extracted data from clinic info', async ({ page }) => {
  55  |     // Upload and process document
  56  |     const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  57  |     const fileInput = page.locator('input[type="file"][accept*="pdf"]').first();
  58  |     await fileInput.setInputFiles(testFile);
  59  | 
  60  |     // Wait for processing
  61  |     await page.waitForTimeout(5000);
  62  | 
  63  |     // Extracted data visible
  64  |     await expect(page.locator('text=Извлечённые данные')).toBeVisible();
  65  | 
  66  |     // Clinic details
  67  |     await expect(page.locator('text=Название клиники')).toBeVisible();
  68  |     await expect(page.locator('text=Специализация')).toBeVisible();
  69  |     await expect(page.locator('text=Контакты')).toBeVisible();
  70  |   });
  71  | 
  72  |   test('should validate file type', async ({ page }) => {
  73  |     // Try to upload invalid file type
  74  |     const invalidFile = path.join(__dirname, '../fixtures/test-image.jpg');
  75  |     const fileInput = page.locator('input[type="file"][accept*="pdf"]').first();
  76  | 
  77  |     // Upload should be rejected or show error
  78  |     await fileInput.setInputFiles(invalidFile);
  79  | 
  80  |     // Error message
  81  |     await expect(page.locator('text=Неверный формат файла')).toBeVisible({ timeout: 3000 });
  82  |   });
  83  | 
  84  |   test('should validate file size', async ({ page }) => {
  85  |     // Try to upload large file (>10MB)
  86  |     // Note: This test requires a large test file
  87  |     // For now, we'll skip actual upload and test the UI validation
  88  | 
  89  |     // File size limit message visible
  90  |     await expect(page.locator('text=Максимальный размер файла: 10 МБ')).toBeVisible();
  91  |   });
  92  | 
  93  |   test('should upload multiple documents', async ({ page }) => {
  94  |     // Upload clinic info
  95  |     const clinicFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  96  |     const clinicInput = page.locator('input[type="file"]').first();
  97  |     await clinicInput.setInputFiles(clinicFile);
  98  |     await page.waitForTimeout(2000);
  99  | 
  100 |     // Upload analytics access
  101 |     const analyticsFile = path.join(__dirname, '../fixtures/analytics-access.pdf');
  102 |     const analyticsInput = page.locator('input[type="file"]').nth(1);
  103 |     await analyticsInput.setInputFiles(analyticsFile);
  104 |     await page.waitForTimeout(2000);
  105 | 
  106 |     // Upload ads access
  107 |     const adsFile = path.join(__dirname, '../fixtures/ads-access.pdf');
  108 |     const adsInput = page.locator('input[type="file"]').nth(2);
  109 |     await adsInput.setInputFiles(adsFile);
  110 |     await page.waitForTimeout(2000);
  111 | 
  112 |     // All files uploaded
  113 |     await expect(page.locator('text=clinic-info.pdf')).toBeVisible();
  114 |     await expect(page.locator('text=analytics-access.pdf')).toBeVisible();
  115 |     await expect(page.locator('text=ads-access.pdf')).toBeVisible();
  116 |   });
  117 | 
  118 |   test('should show AI processing progress', async ({ page }) => {
  119 |     // Upload document
```