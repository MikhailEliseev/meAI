# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: complete-journey.spec.ts >> Complete User Journey >> should complete full onboarding flow from landing to completion
- Location: e2e/complete-journey.spec.ts:18:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import * as path from 'path';
  3   | 
  4   | /**
  5   |  * E2E Test: Complete User Journey (End-to-End Integration)
  6   |  *
  7   |  * Full Flow:
  8   |  * 1. Landing page → Contact form → Lead scoring
  9   |  * 2. Email sequence triggered
  10  |  * 3. Payment → Invoice generation
  11  |  * 4. Document upload → AI processing
  12  |  * 5. BAA signature → Onboarding complete
  13  |  *
  14  |  * This test validates the entire system integration.
  15  |  */
  16  | 
  17  | test.describe('Complete User Journey', () => {
  18  |   test('should complete full onboarding flow from landing to completion', async ({ page }) => {
  19  |     // ============================================
  20  |     // STEP 1: Landing Page → Contact Form
  21  |     // ============================================
> 22  |     await page.goto('/');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  23  | 
  24  |     // Verify landing page loaded
  25  |     await expect(page.locator('h1')).toContainText('AI-маркетинг для медицинских клиник');
  26  | 
  27  |     // Scroll to contact form
  28  |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  29  | 
  30  |     // Fill contact form
  31  |     await page.fill('input[name="name"]', 'Иван Петров');
  32  |     await page.fill('input[name="phone"]', '+79991234567');
  33  |     await page.fill('input[name="email"]', 'ivan.petrov.test@dentaplus.ru');
  34  |     await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
  35  |     await page.selectOption('select[name="specialty"]', 'dentistry');
  36  |     await page.fill('textarea[name="message"]', 'Ищем агентство для продвижения клиники. Бюджет 300K/месяц.');
  37  | 
  38  |     // Accept consent
  39  |     await page.check('input[type="checkbox"][name="consent"]');
  40  | 
  41  |     // Submit form
  42  |     await page.click('button[type="submit"]');
  43  | 
  44  |     // Wait for success
  45  |     await expect(page.locator('text=Спасибо за заявку')).toBeVisible({ timeout: 10000 });
  46  | 
  47  |     // ============================================
  48  |     // STEP 2: Lead Scoring (happens in background)
  49  |     // ============================================
  50  |     // Lead scored as HOT (dentistry + Moscow + high budget)
  51  |     // Email sequence triggered automatically
  52  |     // Linear issue created automatically
  53  | 
  54  |     // Wait for background processing
  55  |     await page.waitForTimeout(2000);
  56  | 
  57  |     // ============================================
  58  |     // STEP 3: Navigate to Billing
  59  |     // ============================================
  60  |     await page.goto('/billing');
  61  | 
  62  |     // Verify billing page loaded
  63  |     await expect(page.locator('h1')).toContainText('Оплата');
  64  | 
  65  |     // Select Professional plan (250K RUB/month)
  66  |     await page.click('button:has-text("Выбрать Professional")');
  67  | 
  68  |     // Fill payment form
  69  |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
  70  |     await page.fill('input[placeholder="MM/YY"]', '12/25');
  71  |     await page.fill('input[placeholder="123"]', '123');
  72  |     await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');
  73  | 
  74  |     // Submit payment
  75  |     await page.click('button[type="submit"]:has-text("Оплатить")');
  76  | 
  77  |     // Wait for payment processing
  78  |     await expect(page.locator('text=Платёж успешно выполнен')).toBeVisible({ timeout: 10000 });
  79  | 
  80  |     // Verify invoice created
  81  |     await expect(page.locator('text=AIM-2026-')).toBeVisible();
  82  |     await expect(page.locator('text=300 000 ₽')).toBeVisible(); // Professional with VAT
  83  | 
  84  |     // ============================================
  85  |     // STEP 4: Navigate to Onboarding
  86  |     // ============================================
  87  |     await page.goto('/onboarding');
  88  | 
  89  |     // Verify onboarding page loaded
  90  |     await expect(page.locator('h1')).toContainText('Онбординг');
  91  | 
  92  |     // Upload clinic info document
  93  |     const clinicFile = path.join(__dirname, 'fixtures/clinic-info.pdf');
  94  |     const clinicInput = page.locator('input[type="file"]').first();
  95  |     await clinicInput.setInputFiles(clinicFile);
  96  | 
  97  |     // Wait for AI processing
  98  |     await expect(page.locator('text=Обработка')).toBeVisible();
  99  |     await expect(page.locator('text=Документ обработан')).toBeVisible({ timeout: 15000 });
  100 | 
  101 |     // Upload analytics access document
  102 |     const analyticsFile = path.join(__dirname, 'fixtures/analytics-access.pdf');
  103 |     const analyticsInput = page.locator('input[type="file"]').nth(1);
  104 |     await analyticsInput.setInputFiles(analyticsFile);
  105 |     await page.waitForTimeout(3000);
  106 | 
  107 |     // Upload ads access document
  108 |     const adsFile = path.join(__dirname, 'fixtures/ads-access.pdf');
  109 |     const adsInput = page.locator('input[type="file"]').nth(2);
  110 |     await adsInput.setInputFiles(adsFile);
  111 |     await page.waitForTimeout(3000);
  112 | 
  113 |     // Verify all documents uploaded
  114 |     await expect(page.locator('text=clinic-info.pdf')).toBeVisible();
  115 |     await expect(page.locator('text=analytics-access.pdf')).toBeVisible();
  116 |     await expect(page.locator('text=ads-access.pdf')).toBeVisible();
  117 | 
  118 |     // ============================================
  119 |     // STEP 5: BAA Signature
  120 |     // ============================================
  121 |     // Scroll to BAA section
  122 |     await page.locator('text=Подписание договора').scrollIntoViewIfNeeded();
```