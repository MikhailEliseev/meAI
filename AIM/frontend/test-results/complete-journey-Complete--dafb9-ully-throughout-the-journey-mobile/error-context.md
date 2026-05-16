# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: complete-journey.spec.ts >> Complete User Journey >> should handle errors gracefully throughout the journey
- Location: e2e/complete-journey.spec.ts:178:7

# Error details

```
Error: page.goto: Could not connect to the server.
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
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
  123 | 
  124 |     // Fill signer details
  125 |     await page.fill('input[name="signerName"]', 'Иван Петров');
  126 |     await page.fill('input[name="signerEmail"]', 'ivan.petrov.test@dentaplus.ru');
  127 |     await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
  128 | 
  129 |     // Send for signature
  130 |     await page.click('button:has-text("Отправить на подпись")');
  131 | 
  132 |     // Verify BAA sent
  133 |     await expect(page.locator('text=Договор отправлен на email')).toBeVisible({ timeout: 5000 });
  134 | 
  135 |     // ============================================
  136 |     // STEP 6: Simulate BAA Signed (for E2E test)
  137 |     // ============================================
  138 |     // In production, user would sign via DocuSign
  139 |     // For E2E test, we simulate the signed status
  140 |     await page.evaluate(() => {
  141 |       localStorage.setItem('onboarding_baa_signed', 'true');
  142 |     });
  143 |     await page.reload();
  144 | 
  145 |     // ============================================
  146 |     // STEP 7: Onboarding Complete
  147 |     // ============================================
  148 |     await expect(page.locator('text=Онбординг завершён')).toBeVisible();
  149 |     await expect(page.locator('text=Добро пожаловать в AIM Agency')).toBeVisible();
  150 | 
  151 |     // Verify next steps visible
  152 |     await expect(page.locator('text=Следующие шаги')).toBeVisible();
  153 |     await expect(page.locator('button:has-text("Перейти в панель управления")')).toBeVisible();
  154 | 
  155 |     // ============================================
  156 |     // VERIFICATION: Check all data persisted
  157 |     // ============================================
  158 |     // Navigate to analytics dashboard
  159 |     await page.goto('/analytics');
  160 | 
  161 |     // Verify lead appears in analytics
  162 |     await expect(page.locator('text=Всего лидов')).toBeVisible();
  163 |     await expect(page.locator('text=Горячие лиды')).toBeVisible();
  164 | 
  165 |     // Navigate back to billing
  166 |     await page.goto('/billing');
  167 | 
  168 |     // Verify payment history shows invoice
  169 |     await expect(page.locator('text=AIM-2026-')).toBeVisible();
  170 |     await expect(page.locator('text=Оплачено')).toBeVisible();
  171 | 
  172 |     // ============================================
  173 |     // SUCCESS: Full journey completed
  174 |     // ============================================
  175 |     console.log('✅ Complete user journey test passed!');
  176 |   });
  177 | 
  178 |   test('should handle errors gracefully throughout the journey', async ({ page }) => {
  179 |     // ============================================
  180 |     // Test error handling at each step
  181 |     // ============================================
  182 | 
  183 |     // STEP 1: Invalid contact form submission
> 184 |     await page.goto('/');
      |                ^ Error: page.goto: Could not connect to the server.
  185 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  186 |     await page.click('button[type="submit"]');
  187 |     await expect(page.locator('text=Обязательное поле')).toBeVisible();
  188 | 
  189 |     // STEP 2: Invalid payment card
  190 |     await page.goto('/billing');
  191 |     await page.click('button:has-text("Выбрать Starter")');
  192 |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '1234567890123456');
  193 |     await page.blur('input[placeholder="1234 5678 9012 3456"]');
  194 |     await expect(page.locator('text=Неверный номер карты')).toBeVisible();
  195 | 
  196 |     // STEP 3: Invalid file upload
  197 |     await page.goto('/onboarding');
  198 |     const invalidFile = path.join(__dirname, 'fixtures/test-image.jpg');
  199 |     const fileInput = page.locator('input[type="file"]').first();
  200 |     await fileInput.setInputFiles(invalidFile);
  201 |     await expect(page.locator('text=Неверный формат файла')).toBeVisible({ timeout: 3000 });
  202 | 
  203 |     // STEP 4: Corrupted file processing
  204 |     const corruptedFile = path.join(__dirname, 'fixtures/corrupted.pdf');
  205 |     await fileInput.setInputFiles(corruptedFile);
  206 |     await expect(page.locator('text=Ошибка обработки')).toBeVisible({ timeout: 10000 });
  207 | 
  208 |     console.log('✅ Error handling test passed!');
  209 |   });
  210 | 
  211 |   test('should maintain state across page reloads', async ({ page }) => {
  212 |     // ============================================
  213 |     // Test state persistence
  214 |     // ============================================
  215 | 
  216 |     // Fill contact form partially
  217 |     await page.goto('/');
  218 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  219 |     await page.fill('input[name="name"]', 'Иван Петров');
  220 |     await page.fill('input[name="email"]', 'ivan@dentaplus.ru');
  221 |     await page.waitForTimeout(2000); // Wait for auto-save
  222 | 
  223 |     // Reload page
  224 |     await page.reload();
  225 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  226 | 
  227 |     // Verify draft restored
  228 |     await expect(page.locator('input[name="name"]')).toHaveValue('Иван Петров');
  229 |     await expect(page.locator('input[name="email"]')).toHaveValue('ivan@dentaplus.ru');
  230 | 
  231 |     console.log('✅ State persistence test passed!');
  232 |   });
  233 | });
  234 | 
  235 | test.describe('Performance and Accessibility', () => {
  236 |   test('should load landing page within 3 seconds', async ({ page }) => {
  237 |     const startTime = Date.now();
  238 |     await page.goto('/');
  239 |     const loadTime = Date.now() - startTime;
  240 | 
  241 |     // Verify page loaded
  242 |     await expect(page.locator('h1')).toBeVisible();
  243 | 
  244 |     // Check load time
  245 |     expect(loadTime).toBeLessThan(3000);
  246 |     console.log(`✅ Landing page loaded in ${loadTime}ms`);
  247 |   });
  248 | 
  249 |   test('should have accessible form labels', async ({ page }) => {
  250 |     await page.goto('/');
  251 |     await page.locator('text=Оставьте заявку').scrollIntoViewIfNeeded();
  252 | 
  253 |     // Check for accessible labels
  254 |     const nameInput = page.locator('input[name="name"]');
  255 |     const nameLabel = await nameInput.getAttribute('aria-label');
  256 |     expect(nameLabel).toBeTruthy();
  257 | 
  258 |     const emailInput = page.locator('input[name="email"]');
  259 |     const emailLabel = await emailInput.getAttribute('aria-label');
  260 |     expect(emailLabel).toBeTruthy();
  261 | 
  262 |     console.log('✅ Accessibility test passed!');
  263 |   });
  264 | 
  265 |   test('should have proper heading hierarchy', async ({ page }) => {
  266 |     await page.goto('/');
  267 | 
  268 |     // Check h1 exists and is unique
  269 |     const h1Count = await page.locator('h1').count();
  270 |     expect(h1Count).toBe(1);
  271 | 
  272 |     // Check h2 headings exist
  273 |     const h2Count = await page.locator('h2').count();
  274 |     expect(h2Count).toBeGreaterThan(0);
  275 | 
  276 |     console.log('✅ Heading hierarchy test passed!');
  277 |   });
  278 | });
  279 | 
```