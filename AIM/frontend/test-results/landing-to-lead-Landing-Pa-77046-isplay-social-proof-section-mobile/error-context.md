# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: landing-to-lead.spec.ts >> Landing Page to Lead Generation >> should display social proof section
- Location: e2e/landing-to-lead.spec.ts:34:7

# Error details

```
Error: page.goto: Could not connect to the server.
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | /**
  4   |  * E2E Test: Landing Page → Contact Form → Lead Scoring → Email Sequence
  5   |  *
  6   |  * User Journey:
  7   |  * 1. Visit landing page
  8   |  * 2. See hero section with CTA
  9   |  * 3. See social proof (case studies, testimonials)
  10  |  * 4. See process steps
  11  |  * 5. Read FAQ
  12  |  * 6. Fill contact form
  13  |  * 7. Submit form → Lead scored → Email sequence triggered
  14  |  */
  15  | 
  16  | test.describe('Landing Page to Lead Generation', () => {
  17  |   test.beforeEach(async ({ page }) => {
> 18  |     await page.goto('/');
      |                ^ Error: page.goto: Could not connect to the server.
  19  |   });
  20  | 
  21  |   test('should display hero section with CTA', async ({ page }) => {
  22  |     // Hero section visible
  23  |     await expect(page.locator('h1')).toContainText('AI-маркетинг для медицинских клиник');
  24  | 
  25  |     // CTA button visible
  26  |     const ctaButton = page.locator('button:has-text("Получить консультацию")').first();
  27  |     await expect(ctaButton).toBeVisible();
  28  | 
  29  |     // Trust badges visible
  30  |     await expect(page.locator('text=ФЗ-152')).toBeVisible();
  31  |     await expect(page.locator('text=Яндекс Партнёр')).toBeVisible();
  32  |   });
  33  | 
  34  |   test('should display social proof section', async ({ page }) => {
  35  |     // Case studies visible
  36  |     await expect(page.locator('text=Кейсы клиентов')).toBeVisible();
  37  |     await expect(page.locator('text=Стоматология «Дента Плюс»')).toBeVisible();
  38  | 
  39  |     // Testimonials visible
  40  |     await expect(page.locator('text=Отзывы клиентов')).toBeVisible();
  41  | 
  42  |     // Awards visible
  43  |     await expect(page.locator('text=Награды и сертификаты')).toBeVisible();
  44  |   });
  45  | 
  46  |   test('should display process steps', async ({ page }) => {
  47  |     // Process section visible
  48  |     await expect(page.locator('text=Как мы работаем')).toBeVisible();
  49  | 
  50  |     // 3 steps visible
  51  |     await expect(page.locator('text=Бесплатная консультация')).toBeVisible();
  52  |     await expect(page.locator('text=Персональная стратегия')).toBeVisible();
  53  |     await expect(page.locator('text=Реализация и результат')).toBeVisible();
  54  |   });
  55  | 
  56  |   test('should display and interact with FAQ', async ({ page }) => {
  57  |     // FAQ section visible
  58  |     await expect(page.locator('text=Часто задаваемые вопросы')).toBeVisible();
  59  | 
  60  |     // Click first FAQ
  61  |     const firstFaq = page.locator('button:has-text("Как вы обеспечиваете безопасность данных")').first();
  62  |     await firstFaq.click();
  63  | 
  64  |     // Answer visible
  65  |     await expect(page.locator('text=ФЗ-152')).toBeVisible();
  66  |   });
  67  | 
  68  |   test('should scroll to contact form on CTA click', async ({ page }) => {
  69  |     // Click CTA button
  70  |     const ctaButton = page.locator('button:has-text("Получить консультацию")').first();
  71  |     await ctaButton.click();
  72  | 
  73  |     // Wait for scroll
  74  |     await page.waitForTimeout(1000);
  75  | 
  76  |     // Contact form visible in viewport
  77  |     const contactForm = page.locator('form');
  78  |     await expect(contactForm).toBeInViewport();
  79  |   });
  80  | 
  81  |   test('should fill and submit contact form successfully', async ({ page }) => {
  82  |     // Scroll to contact form
  83  |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  84  | 
  85  |     // Fill form
  86  |     await page.fill('input[name="name"]', 'Иван Петров');
  87  |     await page.fill('input[name="phone"]', '+79991234567');
  88  |     await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
  89  |     await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
  90  |     await page.selectOption('select[name="specialty"]', 'dentistry');
  91  |     await page.fill('textarea[name="message"]', 'Ищем агентство для продвижения клиники');
  92  | 
  93  |     // Accept ФЗ-152 consent
  94  |     await page.check('input[type="checkbox"][name="consent"]');
  95  | 
  96  |     // Submit form
  97  |     await page.click('button[type="submit"]');
  98  | 
  99  |     // Wait for success message
  100 |     await expect(page.locator('text=Спасибо за заявку')).toBeVisible({ timeout: 10000 });
  101 | 
  102 |     // Success message contains details
  103 |     await expect(page.locator('text=Мы свяжемся с вами')).toBeVisible();
  104 |   });
  105 | 
  106 |   test('should validate form fields', async ({ page }) => {
  107 |     // Scroll to contact form
  108 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  109 | 
  110 |     // Try to submit empty form
  111 |     await page.click('button[type="submit"]');
  112 | 
  113 |     // Validation errors visible
  114 |     await expect(page.locator('text=Обязательное поле')).toHaveCount(5); // name, phone, email, clinic, consent
  115 |   });
  116 | 
  117 |   test('should validate phone number format', async ({ page }) => {
  118 |     // Scroll to contact form
```