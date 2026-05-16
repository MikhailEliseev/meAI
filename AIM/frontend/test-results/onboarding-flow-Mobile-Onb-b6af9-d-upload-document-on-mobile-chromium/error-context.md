# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: onboarding-flow.spec.ts >> Mobile Onboarding >> should upload document on mobile
- Location: e2e/onboarding-flow.spec.ts:294:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/onboarding
Call log:
  - navigating to "http://localhost:3000/onboarding", waiting until "load"

```

# Test source

```ts
  195 |       localStorage.setItem('onboarding_documents_uploaded', 'true');
  196 |     });
  197 |     await page.reload();
  198 |   });
  199 | 
  200 |   test('should display BAA signature section after documents uploaded', async ({ page }) => {
  201 |     // BAA section visible
  202 |     await expect(page.locator('text=Подписание договора')).toBeVisible();
  203 |     await expect(page.locator('text=Business Associate Agreement')).toBeVisible();
  204 |   });
  205 | 
  206 |   test('should display BAA document preview', async ({ page }) => {
  207 |     // BAA preview visible
  208 |     await expect(page.locator('text=Предварительный просмотр договора')).toBeVisible();
  209 | 
  210 |     // Key sections visible
  211 |     await expect(page.locator('text=Конфиденциальность данных')).toBeVisible();
  212 |     await expect(page.locator('text=Обязательства сторон')).toBeVisible();
  213 |   });
  214 | 
  215 |   test('should send BAA for signature', async ({ page }) => {
  216 |     // Fill signer details
  217 |     await page.fill('input[name="signerName"]', 'Иван Петров');
  218 |     await page.fill('input[name="signerEmail"]', 'ivan@dentaplus.ru');
  219 |     await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
  220 | 
  221 |     // Send for signature
  222 |     await page.click('button:has-text("Отправить на подпись")');
  223 | 
  224 |     // Success message
  225 |     await expect(page.locator('text=Договор отправлен на email')).toBeVisible({ timeout: 5000 });
  226 | 
  227 |     // DocuSign link visible
  228 |     await expect(page.locator('text=Проверьте почту')).toBeVisible();
  229 |   });
  230 | 
  231 |   test('should track BAA signature status', async ({ page }) => {
  232 |     // Send BAA
  233 |     await page.fill('input[name="signerName"]', 'Иван Петров');
  234 |     await page.fill('input[name="signerEmail"]', 'ivan@dentaplus.ru');
  235 |     await page.fill('input[name="clinicName"]', 'Стоматология Дента Плюс');
  236 |     await page.click('button:has-text("Отправить на подпись")');
  237 |     await page.waitForTimeout(2000);
  238 | 
  239 |     // Status tracking visible
  240 |     await expect(page.locator('text=Статус подписания')).toBeVisible();
  241 | 
  242 |     // Status: Sent
  243 |     await expect(page.locator('text=Отправлено')).toBeVisible();
  244 | 
  245 |     // Refresh status button
  246 |     await expect(page.locator('button:has-text("Обновить статус")')).toBeVisible();
  247 |   });
  248 | 
  249 |   test('should complete onboarding after BAA signed', async ({ page }) => {
  250 |     // Simulate BAA signed (stub)
  251 |     await page.evaluate(() => {
  252 |       localStorage.setItem('onboarding_baa_signed', 'true');
  253 |     });
  254 |     await page.reload();
  255 | 
  256 |     // Completion message
  257 |     await expect(page.locator('text=Онбординг завершён')).toBeVisible();
  258 |     await expect(page.locator('text=Добро пожаловать в AIM Agency')).toBeVisible();
  259 | 
  260 |     // Next steps visible
  261 |     await expect(page.locator('text=Следующие шаги')).toBeVisible();
  262 |     await expect(page.locator('button:has-text("Перейти в панель управления")')).toBeVisible();
  263 |   });
  264 | 
  265 |   test('should display onboarding progress', async ({ page }) => {
  266 |     // Progress bar visible
  267 |     await expect(page.locator('text=Прогресс онбординга')).toBeVisible();
  268 | 
  269 |     // Steps visible
  270 |     await expect(page.locator('text=1. Загрузка документов')).toBeVisible();
  271 |     await expect(page.locator('text=2. Проверка данных')).toBeVisible();
  272 |     await expect(page.locator('text=3. Подписание договора')).toBeVisible();
  273 |     await expect(page.locator('text=4. Завершение')).toBeVisible();
  274 | 
  275 |     // Current step highlighted
  276 |     const currentStep = page.locator('text=1. Загрузка документов').first();
  277 |     await expect(currentStep).toHaveClass(/font-bold/);
  278 |   });
  279 | });
  280 | 
  281 | test.describe('Mobile Onboarding', () => {
  282 |   test.use({ viewport: { width: 375, height: 667 } });
  283 | 
  284 |   test('should display mobile-optimized onboarding', async ({ page }) => {
  285 |     await page.goto('/onboarding');
  286 | 
  287 |     // Page title visible
  288 |     await expect(page.locator('h1')).toContainText('Онбординг');
  289 | 
  290 |     // Upload areas stacked vertically
  291 |     await expect(page.locator('text=Информация о клинике')).toBeVisible();
  292 |   });
  293 | 
  294 |   test('should upload document on mobile', async ({ page }) => {
> 295 |     await page.goto('/onboarding');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/onboarding
  296 | 
  297 |     // Upload file
  298 |     const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  299 |     const fileInput = page.locator('input[type="file"]').first();
  300 |     await fileInput.setInputFiles(testFile);
  301 | 
  302 |     // File uploaded
  303 |     await expect(page.locator('text=clinic-info.pdf')).toBeVisible({ timeout: 5000 });
  304 |   });
  305 | });
  306 | 
```