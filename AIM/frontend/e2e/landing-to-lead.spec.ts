import { test, expect } from '@playwright/test';

/**
 * E2E Test: Landing Page → Contact Form → Lead Scoring → Email Sequence
 *
 * User Journey:
 * 1. Visit landing page
 * 2. See hero section with CTA
 * 3. See social proof (case studies, testimonials)
 * 4. See process steps
 * 5. Read FAQ
 * 6. Fill contact form
 * 7. Submit form → Lead scored → Email sequence triggered
 */

test.describe('Landing Page to Lead Generation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display hero section with CTA', async ({ page }) => {
    // Hero section visible
    await expect(page.locator('h1')).toContainText('AI-маркетинг для медицинских клиник');

    // CTA button visible
    const ctaButton = page.locator('button:has-text("Получить консультацию")').first();
    await expect(ctaButton).toBeVisible();

    // Trust badges visible
    await expect(page.locator('text=ФЗ-152')).toBeVisible();
    await expect(page.locator('text=Яндекс Партнёр')).toBeVisible();
  });

  test('should display social proof section', async ({ page }) => {
    // Case studies visible
    await expect(page.locator('text=Кейсы клиентов')).toBeVisible();
    await expect(page.locator('text=Стоматология «Дента Плюс»')).toBeVisible();

    // Testimonials visible
    await expect(page.locator('text=Отзывы клиентов')).toBeVisible();

    // Awards visible
    await expect(page.locator('text=Награды и сертификаты')).toBeVisible();
  });

  test('should display process steps', async ({ page }) => {
    // Process section visible
    await expect(page.locator('text=Как мы работаем')).toBeVisible();

    // 3 steps visible
    await expect(page.locator('text=Бесплатная консультация')).toBeVisible();
    await expect(page.locator('text=Персональная стратегия')).toBeVisible();
    await expect(page.locator('text=Реализация и результат')).toBeVisible();
  });

  test('should display and interact with FAQ', async ({ page }) => {
    // FAQ section visible
    await expect(page.locator('text=Часто задаваемые вопросы')).toBeVisible();

    // Click first FAQ
    const firstFaq = page.locator('button:has-text("Как вы обеспечиваете безопасность данных")').first();
    await firstFaq.click();

    // Answer visible
    await expect(page.locator('text=ФЗ-152')).toBeVisible();
  });

  test('should scroll to contact form on CTA click', async ({ page }) => {
    // Click CTA button
    const ctaButton = page.locator('button:has-text("Получить консультацию")').first();
    await ctaButton.click();

    // Wait for scroll
    await page.waitForTimeout(1000);

    // Contact form visible in viewport
    const contactForm = page.locator('form');
    await expect(contactForm).toBeInViewport();
  });

  test('should fill and submit contact form successfully', async ({ page }) => {
    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Fill form
    await page.fill('input[name="name"]', 'Иван Петров');
    await page.fill('input[name="phone"]', '+79991234567');
    await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
    await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
    await page.selectOption('select[name="specialty"]', 'dentistry');
    await page.fill('textarea[name="message"]', 'Ищем агентство для продвижения клиники');

    // Accept ФЗ-152 consent
    await page.check('input[type="checkbox"][name="consent"]');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('text=Спасибо за заявку')).toBeVisible({ timeout: 10000 });

    // Success message contains details
    await expect(page.locator('text=Мы свяжемся с вами')).toBeVisible();
  });

  test('should validate form fields', async ({ page }) => {
    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Validation errors visible
    await expect(page.locator('text=Обязательное поле')).toHaveCount(5); // name, phone, email, clinic, consent
  });

  test('should validate phone number format', async ({ page }) => {
    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Fill invalid phone
    await page.fill('input[name="phone"]', '123');
    await page.blur('input[name="phone"]');

    // Validation error visible
    await expect(page.locator('text=Неверный формат телефона')).toBeVisible();

    // Fill valid phone
    await page.fill('input[name="phone"]', '+79991234567');
    await page.blur('input[name="phone"]');

    // Error gone
    await expect(page.locator('text=Неверный формат телефона')).not.toBeVisible();
  });

  test('should validate email format', async ({ page }) => {
    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Fill invalid email
    await page.fill('input[name="email"]', 'invalid-email');
    await page.blur('input[name="email"]');

    // Validation error visible
    await expect(page.locator('text=Неверный формат email')).toBeVisible();

    // Fill valid email
    await page.fill('input[name="email"]', 'test@example.com');
    await page.blur('input[name="email"]');

    // Error gone
    await expect(page.locator('text=Неверный формат email')).not.toBeVisible();
  });

  test('should restore draft from localStorage', async ({ page }) => {
    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Fill form partially
    await page.fill('input[name="name"]', 'Иван Петров');
    await page.fill('input[name="email"]', 'ivan@dentaplus.ru');

    // Wait for auto-save
    await page.waitForTimeout(2000);

    // Reload page
    await page.reload();

    // Scroll to contact form again
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Draft restored
    await expect(page.locator('input[name="name"]')).toHaveValue('Иван Петров');
    await expect(page.locator('input[name="email"]')).toHaveValue('ivan@dentaplus.ru');
  });
});

test.describe('Mobile Landing Page', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should display mobile-optimized layout', async ({ page }) => {
    await page.goto('/');

    // Hero section visible
    await expect(page.locator('h1')).toBeVisible();

    // Mobile menu button visible (if hamburger menu exists)
    // await expect(page.locator('button[aria-label="Menu"]')).toBeVisible();

    // CTA button visible
    await expect(page.locator('button:has-text("Получить консультацию")').first()).toBeVisible();
  });

  test('should fill contact form on mobile', async ({ page }) => {
    await page.goto('/');

    // Scroll to contact form
    await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();

    // Fill form
    await page.fill('input[name="name"]', 'Иван Петров');
    await page.fill('input[name="phone"]', '+79991234567');
    await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
    await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
    await page.selectOption('select[name="specialty"]', 'dentistry');

    // Accept consent
    await page.check('input[type="checkbox"][name="consent"]');

    // Submit
    await page.click('button[type="submit"]');

    // Success message
    await expect(page.locator('text=Спасибо за заявку')).toBeVisible({ timeout: 10000 });
  });
});
