# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: payment-flow.spec.ts >> Payment Flow >> should submit payment and generate invoice
- Location: e2e/payment-flow.spec.ts:123:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/billing
Call log:
  - navigating to "http://localhost:3000/billing", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | /**
  4   |  * E2E Test: Payment Flow → Invoice Generation → Webhook Handling
  5   |  *
  6   |  * User Journey:
  7   |  * 1. Navigate to billing page
  8   |  * 2. See pricing plans
  9   |  * 3. Fill payment form
  10  |  * 4. Submit payment → Invoice generated
  11  |  * 5. See payment history
  12  |  * 6. Download invoice
  13  |  */
  14  | 
  15  | test.describe('Payment Flow', () => {
  16  |   test.beforeEach(async ({ page }) => {
> 17  |     await page.goto('/billing');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/billing
  18  |   });
  19  | 
  20  |   test('should display billing page with payment form and history', async ({ page }) => {
  21  |     // Page title
  22  |     await expect(page.locator('h1')).toContainText('Оплата');
  23  | 
  24  |     // Payment form visible
  25  |     await expect(page.locator('text=Выберите тариф')).toBeVisible();
  26  | 
  27  |     // Payment history visible
  28  |     await expect(page.locator('text=История платежей')).toBeVisible();
  29  |   });
  30  | 
  31  |   test('should display three pricing plans', async ({ page }) => {
  32  |     // Starter plan
  33  |     await expect(page.locator('text=Starter')).toBeVisible();
  34  |     await expect(page.locator('text=150 000 ₽')).toBeVisible();
  35  | 
  36  |     // Professional plan (recommended)
  37  |     await expect(page.locator('text=Professional')).toBeVisible();
  38  |     await expect(page.locator('text=250 000 ₽')).toBeVisible();
  39  |     await expect(page.locator('text=Рекомендуем')).toBeVisible();
  40  | 
  41  |     // Enterprise plan
  42  |     await expect(page.locator('text=Enterprise')).toBeVisible();
  43  |     await expect(page.locator('text=500 000 ₽')).toBeVisible();
  44  |   });
  45  | 
  46  |   test('should select plan and fill payment form', async ({ page }) => {
  47  |     // Select Professional plan
  48  |     await page.click('button:has-text("Выбрать Professional")');
  49  | 
  50  |     // Payment form visible
  51  |     await expect(page.locator('text=Оплата тарифа Professional')).toBeVisible();
  52  | 
  53  |     // Fill card details
  54  |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
  55  |     await page.fill('input[placeholder="MM/YY"]', '12/25');
  56  |     await page.fill('input[placeholder="123"]', '123');
  57  |     await page.fill('input[placeholder="IVAN PETROV"]', 'IVAN PETROV');
  58  | 
  59  |     // Card number formatted
  60  |     await expect(page.locator('input[placeholder="1234 5678 9012 3456"]')).toHaveValue('4111 1111 1111 1111');
  61  | 
  62  |     // Expiry formatted
  63  |     await expect(page.locator('input[placeholder="MM/YY"]')).toHaveValue('12/25');
  64  |   });
  65  | 
  66  |   test('should validate card number with Luhn algorithm', async ({ page }) => {
  67  |     // Select plan
  68  |     await page.click('button:has-text("Выбрать Starter")');
  69  | 
  70  |     // Fill invalid card number
  71  |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '1234567890123456');
  72  |     await page.blur('input[placeholder="1234 5678 9012 3456"]');
  73  | 
  74  |     // Validation error
  75  |     await expect(page.locator('text=Неверный номер карты')).toBeVisible();
  76  | 
  77  |     // Fill valid card number (Visa test card)
  78  |     await page.fill('input[placeholder="1234 5678 9012 3456"]', '4111111111111111');
  79  |     await page.blur('input[placeholder="1234 5678 9012 3456"]');
  80  | 
  81  |     // Error gone
  82  |     await expect(page.locator('text=Неверный номер карты')).not.toBeVisible();
  83  |   });
  84  | 
  85  |   test('should validate expiry date', async ({ page }) => {
  86  |     // Select plan
  87  |     await page.click('button:has-text("Выбрать Starter")');
  88  | 
  89  |     // Fill expired date
  90  |     await page.fill('input[placeholder="MM/YY"]', '01/20');
  91  |     await page.blur('input[placeholder="MM/YY"]');
  92  | 
  93  |     // Validation error
  94  |     await expect(page.locator('text=Карта просрочена')).toBeVisible();
  95  | 
  96  |     // Fill future date
  97  |     await page.fill('input[placeholder="MM/YY"]', '12/30');
  98  |     await page.blur('input[placeholder="MM/YY"]');
  99  | 
  100 |     // Error gone
  101 |     await expect(page.locator('text=Карта просрочена')).not.toBeVisible();
  102 |   });
  103 | 
  104 |   test('should validate CVV', async ({ page }) => {
  105 |     // Select plan
  106 |     await page.click('button:has-text("Выбрать Starter")');
  107 | 
  108 |     // Fill invalid CVV (too short)
  109 |     await page.fill('input[placeholder="123"]', '12');
  110 |     await page.blur('input[placeholder="123"]');
  111 | 
  112 |     // Validation error
  113 |     await expect(page.locator('text=CVV должен быть 3-4 цифры')).toBeVisible();
  114 | 
  115 |     // Fill valid CVV
  116 |     await page.fill('input[placeholder="123"]', '123');
  117 |     await page.blur('input[placeholder="123"]');
```