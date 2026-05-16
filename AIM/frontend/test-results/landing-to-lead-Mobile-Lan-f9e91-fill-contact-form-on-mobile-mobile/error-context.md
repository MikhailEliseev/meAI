# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: landing-to-lead.spec.ts >> Mobile Landing Page >> should fill contact form on mobile
- Location: e2e/landing-to-lead.spec.ts:194:7

# Error details

```
Error: page.goto: Could not connect to the server.
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
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
  119 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  120 | 
  121 |     // Fill invalid phone
  122 |     await page.fill('input[name="phone"]', '123');
  123 |     await page.blur('input[name="phone"]');
  124 | 
  125 |     // Validation error visible
  126 |     await expect(page.locator('text=Неверный формат телефона')).toBeVisible();
  127 | 
  128 |     // Fill valid phone
  129 |     await page.fill('input[name="phone"]', '+79991234567');
  130 |     await page.blur('input[name="phone"]');
  131 | 
  132 |     // Error gone
  133 |     await expect(page.locator('text=Неверный формат телефона')).not.toBeVisible();
  134 |   });
  135 | 
  136 |   test('should validate email format', async ({ page }) => {
  137 |     // Scroll to contact form
  138 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  139 | 
  140 |     // Fill invalid email
  141 |     await page.fill('input[name="email"]', 'invalid-email');
  142 |     await page.blur('input[name="email"]');
  143 | 
  144 |     // Validation error visible
  145 |     await expect(page.locator('text=Неверный формат email')).toBeVisible();
  146 | 
  147 |     // Fill valid email
  148 |     await page.fill('input[name="email"]', 'test@example.com');
  149 |     await page.blur('input[name="email"]');
  150 | 
  151 |     // Error gone
  152 |     await expect(page.locator('text=Неверный формат email')).not.toBeVisible();
  153 |   });
  154 | 
  155 |   test('should restore draft from localStorage', async ({ page }) => {
  156 |     // Scroll to contact form
  157 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  158 | 
  159 |     // Fill form partially
  160 |     await page.fill('input[name="name"]', 'Иван Петров');
  161 |     await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
  162 | 
  163 |     // Wait for auto-save
  164 |     await page.waitForTimeout(2000);
  165 | 
  166 |     // Reload page
  167 |     await page.reload();
  168 | 
  169 |     // Scroll to contact form again
  170 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  171 | 
  172 |     // Draft restored
  173 |     await expect(page.locator('input[name="name"]')).toHaveValue('Иван Петров');
  174 |     await expect(page.locator('input[name="email"]')).toHaveValue('ivan@dentaplus.ru');
  175 |   });
  176 | });
  177 | 
  178 | test.describe('Mobile Landing Page', () => {
  179 |   test.use({ viewport: { width: 375, height: 667 } });
  180 | 
  181 |   test('should display mobile-optimized layout', async ({ page }) => {
  182 |     await page.goto('/');
  183 | 
  184 |     // Hero section visible
  185 |     await expect(page.locator('h1')).toBeVisible();
  186 | 
  187 |     // Mobile menu button visible (if hamburger menu exists)
  188 |     // await expect(page.locator('button[aria-label="Menu"]')).toBeVisible();
  189 | 
  190 |     // CTA button visible
  191 |     await expect(page.locator('button:has-text("Получить консультацию")').first()).toBeVisible();
  192 |   });
  193 | 
  194 |   test('should fill contact form on mobile', async ({ page }) => {
> 195 |     await page.goto('/');
      |                ^ Error: page.goto: Could not connect to the server.
  196 | 
  197 |     // Scroll to contact form
  198 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  199 | 
  200 |     // Fill form
  201 |     await page.fill('input[name="name"]', 'Иван Петров');
  202 |     await page.fill('input[name="phone"]', '+79991234567');
  203 |     await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
  204 |     await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
  205 |     await page.selectOption('select[name="specialty"]', 'dentistry');
  206 | 
  207 |     // Accept consent
  208 |     await page.check('input[type="checkbox"][name="consent"]');
  209 | 
  210 |     // Submit
  211 |     await page.click('button[type="submit"]');
  212 | 
  213 |     // Success message
  214 |     await expect(page.locator('text=Спасибо за заявку')).toBeVisible({ timeout: 10000 });
  215 |   });
  216 | });
  217 | 
```