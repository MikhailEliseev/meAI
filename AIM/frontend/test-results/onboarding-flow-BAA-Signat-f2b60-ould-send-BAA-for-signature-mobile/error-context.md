# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: onboarding-flow.spec.ts >> BAA Signature Workflow >> should send BAA for signature
- Location: e2e/onboarding-flow.spec.ts:215:7

# Error details

```
Error: page.goto: Could not connect to the server.
Call log:
  - navigating to "http://localhost:3000/onboarding", waiting until "load"

```

# Test source

```ts
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
  120 |     const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  121 |     const fileInput = page.locator('input[type="file"]').first();
  122 |     await fileInput.setInputFiles(testFile);
  123 | 
  124 |     // Processing stages visible
  125 |     await expect(page.locator('text=Загрузка')).toBeVisible();
  126 |     await expect(page.locator('text=Извлечение текста')).toBeVisible({ timeout: 5000 });
  127 |     await expect(page.locator('text=AI анализ')).toBeVisible({ timeout: 5000 });
  128 |     await expect(page.locator('text=Готово')).toBeVisible({ timeout: 10000 });
  129 |   });
  130 | 
  131 |   test('should allow editing extracted data', async ({ page }) => {
  132 |     // Upload and process document
  133 |     const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  134 |     const fileInput = page.locator('input[type="file"]').first();
  135 |     await fileInput.setInputFiles(testFile);
  136 |     await page.waitForTimeout(5000);
  137 | 
  138 |     // Click edit button
  139 |     await page.click('button:has-text("Редактировать")');
  140 | 
  141 |     // Edit form visible
  142 |     await expect(page.locator('input[name="clinicName"]')).toBeVisible();
  143 | 
  144 |     // Edit clinic name
  145 |     await page.fill('input[name="clinicName"]', 'Стоматология Новая');
  146 | 
  147 |     // Save changes
  148 |     await page.click('button:has-text("Сохранить")');
  149 | 
  150 |     // Updated data visible
  151 |     await expect(page.locator('text=Стоматология Новая')).toBeVisible();
  152 |   });
  153 | 
  154 |   test('should display confidence scores', async ({ page }) => {
  155 |     // Upload and process document
  156 |     const testFile = path.join(__dirname, '../fixtures/clinic-info.pdf');
  157 |     const fileInput = page.locator('input[type="file"]').first();
  158 |     await fileInput.setInputFiles(testFile);
  159 |     await page.waitForTimeout(5000);
  160 | 
  161 |     // Confidence scores visible
  162 |     await expect(page.locator('text=Уверенность:')).toBeVisible();
  163 |     await expect(page.locator('text=%')).toBeVisible();
  164 | 
  165 |     // High confidence (>80%) shown in green
  166 |     const highConfidence = page.locator('text=95%').first();
  167 |     await expect(highConfidence).toHaveClass(/text-green/);
  168 |   });
  169 | 
  170 |   test('should handle processing errors gracefully', async ({ page }) => {
  171 |     // Upload corrupted file
  172 |     const corruptedFile = path.join(__dirname, '../fixtures/corrupted.pdf');
  173 |     const fileInput = page.locator('input[type="file"]').first();
  174 |     await fileInput.setInputFiles(corruptedFile);
  175 | 
  176 |     // Wait for processing attempt
  177 |     await page.waitForTimeout(3000);
  178 | 
  179 |     // Error message visible
  180 |     await expect(page.locator('text=Ошибка обработки')).toBeVisible({ timeout: 10000 });
  181 |     await expect(page.locator('text=Попробуйте загрузить другой файл')).toBeVisible();
  182 | 
  183 |     // Retry button visible
  184 |     await expect(page.locator('button:has-text("Попробовать снова")')).toBeVisible();
  185 |   });
  186 | });
  187 | 
  188 | test.describe('BAA Signature Workflow', () => {
  189 |   test.beforeEach(async ({ page }) => {
> 190 |     await page.goto('/onboarding');
      |                ^ Error: page.goto: Could not connect to the server.
  191 | 
  192 |     // Upload documents first (stub)
  193 |     // In real test, would upload actual files
  194 |     await page.evaluate(() => {
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
```