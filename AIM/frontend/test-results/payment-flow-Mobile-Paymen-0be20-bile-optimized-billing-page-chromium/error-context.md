# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: payment-flow.spec.ts >> Mobile Payment Flow >> should display mobile-optimized billing page
- Location: e2e/payment-flow.spec.ts:216:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/billing
Call log:
  - navigating to "http://localhost:3000/billing", waiting until "load"

```

# Test source

```ts
  117 |     await page.blur('input[placeholder="123"]');
  118 | 
  119 |     // Error gone
  120 |     await expect(page.locator('text=CVV должен быть 3-4 цифры')).not.toBeVisible();
  121 |   });
  122 | 
  123 |   test('should submit payment and generate invoice', async ({ page }) => {
  124 |     // Select plan
  125 |     await page.click('button:has-text("Выбрать Professional")');
  126 | 
  127 |     // Fill payment form
  128 |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
  129 |     await page.fill('input[placeholder="MM/YY"]', '12/25');
  130 |     await page.fill('input[placeholder="123"]', '123');
  131 |     await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');
  132 | 
  133 |     // Submit payment
  134 |     await page.click('button[type="submit"]:has-text("Оплатить")');
  135 | 
  136 |     // Loading state
  137 |     await expect(page.locator('text=Обработка платежа')).toBeVisible();
  138 | 
  139 |     // Success message
  140 |     await expect(page.locator('text=Платёж успешно выполнен')).toBeVisible({ timeout: 10000 });
  141 | 
  142 |     // Invoice appears in history
  143 |     await expect(page.locator('text=AIM-2026-')).toBeVisible();
  144 |     await expect(page.locator('text=300 000 ₽')).toBeVisible(); // Professional with VAT
  145 |   });
  146 | 
  147 |   test('should display payment history with invoices', async ({ page }) => {
  148 |     // Payment history section visible
  149 |     await expect(page.locator('text=История платежей')).toBeVisible();
  150 | 
  151 |     // Filter buttons visible
  152 |     await expect(page.locator('button:has-text("Все")')).toBeVisible();
  153 |     await expect(page.locator('button:has-text("Оплачено")')).toBeVisible();
  154 |     await expect(page.locator('button:has-text("Ожидает оплаты")')).toBeVisible();
  155 |     await expect(page.locator('button:has-text("Просрочено")')).toBeVisible();
  156 |   });
  157 | 
  158 |   test('should filter payment history', async ({ page }) => {
  159 |     // Click "Оплачено" filter
  160 |     await page.click('button:has-text("Оплачено")');
  161 | 
  162 |     // Only paid invoices visible
  163 |     await expect(page.locator('text=Оплачено')).toBeVisible();
  164 | 
  165 |     // Click "Ожидает оплаты" filter
  166 |     await page.click('button:has-text("Ожидает оплаты")');
  167 | 
  168 |     // Only pending invoices visible (or empty state)
  169 |     const pendingInvoices = page.locator('text=Ожидает оплаты');
  170 |     const emptyState = page.locator('text=Нет счетов');
  171 |     await expect(pendingInvoices.or(emptyState)).toBeVisible();
  172 |   });
  173 | 
  174 |   test('should expand invoice details', async ({ page }) => {
  175 |     // Submit payment first to have invoice
  176 |     await page.click('button:has-text("Выбрать Starter")');
  177 |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
  178 |     await page.fill('input[placeholder="MM/YY"]', '12/25');
  179 |     await page.fill('input[placeholder="123"]', '123');
  180 |     await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');
  181 |     await page.click('button[type="submit"]:has-text("Оплатить")');
  182 |     await page.waitForTimeout(3000);
  183 | 
  184 |     // Click invoice to expand
  185 |     const invoice = page.locator('text=AIM-2026-').first();
  186 |     await invoice.click();
  187 | 
  188 |     // Invoice details visible
  189 |     await expect(page.locator('text=Детали счёта')).toBeVisible();
  190 |     await expect(page.locator('text=Подписка Starter')).toBeVisible();
  191 |     await expect(page.locator('text=Итого с НДС')).toBeVisible();
  192 |   });
  193 | 
  194 |   test('should display security notice', async ({ page }) => {
  195 |     // Select plan
  196 |     await page.click('button:has-text("Выбрать Starter")');
  197 | 
  198 |     // Security notice visible
  199 |     await expect(page.locator('text=Защищено ЮKassa')).toBeVisible();
  200 |     await expect(page.locator('text=PCI DSS')).toBeVisible();
  201 |   });
  202 | 
  203 |   test('should display STUB notice in development', async ({ page }) => {
  204 |     // Select plan
  205 |     await page.click('button:has-text("Выбрать Starter")');
  206 | 
  207 |     // STUB notice visible
  208 |     await expect(page.locator('text=STUB')).toBeVisible();
  209 |     await expect(page.locator('text=Используйте любые данные')).toBeVisible();
  210 |   });
  211 | });
  212 | 
  213 | test.describe('Mobile Payment Flow', () => {
  214 |   test.use({ viewport: { width: 375, height: 667 } });
  215 | 
  216 |   test('should display mobile-optimized billing page', async ({ page }) => {
> 217 |     await page.goto('/billing');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/billing
  218 | 
  219 |     // Page title visible
  220 |     await expect(page.locator('h1')).toContainText('Оплата');
  221 | 
  222 |     // Pricing plans visible (stacked vertically)
  223 |     await expect(page.locator('text=Starter')).toBeVisible();
  224 |     await expect(page.locator('text=Professional')).toBeVisible();
  225 |     await expect(page.locator('text=Enterprise')).toBeVisible();
  226 |   });
  227 | 
  228 |   test('should fill payment form on mobile', async ({ page }) => {
  229 |     await page.goto('/billing');
  230 | 
  231 |     // Select plan
  232 |     await page.click('button:has-text("Выбрать Starter")');
  233 | 
  234 |     // Fill form
  235 |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
  236 |     await page.fill('input[placeholder="MM/YY"]', '12/25');
  237 |     await page.fill('input[placeholder="123"]', '123');
  238 |     await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');
  239 | 
  240 |     // Submit
  241 |     await page.click('button[type="submit"]:has-text("Оплатить")');
  242 | 
  243 |     // Success message
  244 |     await expect(page.locator('text=Платёж успешно выполнен')).toBeVisible({ timeout: 10000 });
  245 |   });
  246 | });
  247 | 
```