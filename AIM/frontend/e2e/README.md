# E2E Testing Guide

## Overview

End-to-end tests validate the complete user journey through the AIM Agency platform using Playwright.

## Test Coverage

### 1. Landing to Lead Generation (`landing-to-lead.spec.ts`)
- Hero section display
- Social proof (case studies, testimonials, awards)
- Process steps visualization
- FAQ interaction
- Contact form submission
- Form validation (phone, email, required fields)
- Draft restoration from localStorage
- Mobile responsive layout

**Test Count:** 11 tests (desktop + mobile)

### 2. Payment Flow (`payment-flow.spec.ts`)
- Billing page display
- Pricing plans (Starter, Professional, Enterprise)
- Payment form with card validation (Luhn algorithm)
- Expiry date validation
- CVV validation
- Payment submission and invoice generation
- Payment history with filters
- Invoice details expansion
- Security notices
- Mobile responsive layout

**Test Count:** 12 tests (desktop + mobile)

### 3. Onboarding Flow (`onboarding-flow.spec.ts`)
- Document upload areas
- File type validation (PDF only)
- File size validation (max 10MB)
- Multiple document uploads
- AI processing progress
- Extracted data display
- Confidence scores
- Data editing
- Error handling (corrupted files)
- BAA signature workflow
- Signature status tracking
- Onboarding completion
- Progress tracking
- Mobile responsive layout

**Test Count:** 15 tests (desktop + mobile)

### 4. Complete Journey (`complete-journey.spec.ts`)
- Full user flow: Landing → Lead → Payment → Onboarding → Completion
- Error handling at each step
- State persistence across reloads
- Performance (page load < 3s)
- Accessibility (form labels, heading hierarchy)

**Test Count:** 5 tests

**Total E2E Tests:** 43 tests

## Setup

### Install Dependencies

```bash
cd /Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/frontend
npm install
```

### Install Playwright Browsers

```bash
npx playwright install
```

Or install specific browser:

```bash
npx playwright install chromium
```

## Running Tests

**IMPORTANT:** Due to the `!` character in the project path (`!meAI`), Playwright cannot auto-start the dev server. You must start it manually first.

### Step 1: Start Dev Server

In one terminal:
```bash
npm run dev
```

Wait for "Ready on http://localhost:3000"

### Step 2: Run E2E Tests

In another terminal:
```bash
npm run test:e2e
```

### Run with UI Mode (Interactive)

```bash
npm run test:e2e:ui
```

### Run in Headed Mode (See Browser)

```bash
npm run test:e2e:headed
```

### Run in Debug Mode

```bash
npm run test:e2e:debug
```

### Run Specific Test File

```bash
npx playwright test landing-to-lead.spec.ts
```

### Run Specific Test

```bash
npx playwright test -g "should fill and submit contact form"
```

### Run on Specific Browser

```bash
npx playwright test --project=chromium
npx playwright test --project=mobile
```

### View Test Report

```bash
npm run test:e2e:report
```

## Test Fixtures

Test files are located in `e2e/fixtures/`:

- `clinic-info.pdf` - Mock clinic information document
- `analytics-access.pdf` - Mock analytics access document
- `ads-access.pdf` - Mock advertising access document
- `corrupted.pdf` - Invalid PDF for error testing
- `test-image.jpg` - Image file for validation testing

## Configuration

Playwright configuration is in `playwright.config.ts`:

- **Base URL:** `http://localhost:3000`
- **Timeout:** 60 seconds per test
- **Retries:** 2 on CI, 0 locally
- **Browsers:** Chromium (desktop), iPhone 13 (mobile)
- **Screenshots:** On failure only
- **Videos:** On failure only
- **Traces:** On first retry

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices

### 1. Test Independence
- Each test should be independent
- Use `beforeEach` for setup
- Clean up state after tests

### 2. Selectors
- Prefer user-facing selectors (text, role, label)
- Avoid CSS selectors when possible
- Use `data-testid` for dynamic content

### 3. Waits
- Use `expect().toBeVisible()` instead of `waitForTimeout()`
- Set appropriate timeouts for async operations
- Use `page.waitForLoadState()` for navigation

### 4. Assertions
- Use specific assertions (`toContainText`, `toHaveValue`)
- Check both positive and negative cases
- Verify error messages

### 5. Mobile Testing
- Test responsive layouts
- Verify touch interactions
- Check viewport-specific features

## Debugging

### Debug Specific Test

```bash
npx playwright test --debug -g "should fill contact form"
```

### Inspect Element

```bash
npx playwright codegen http://localhost:3000
```

### View Trace

```bash
npx playwright show-trace trace.zip
```

### Console Logs

Add to test:
```typescript
page.on('console', msg => console.log(msg.text()));
```

## Common Issues

### Port Already in Use

Kill process on port 3000:
```bash
lsof -ti:3000 | xargs kill -9
```

### Browser Not Installed

```bash
npx playwright install chromium
```

### Test Timeout

Increase timeout in test:
```typescript
test.setTimeout(120000); // 2 minutes
```

### Flaky Tests

- Add explicit waits
- Check for race conditions
- Use `toBeVisible()` instead of `toHaveCount()`

## Performance Targets

- **Page Load:** < 3 seconds
- **Form Submission:** < 5 seconds
- **AI Processing:** < 15 seconds
- **Payment Processing:** < 10 seconds

## Accessibility Checks

Tests include basic accessibility validation:
- Form labels (aria-label)
- Heading hierarchy (h1, h2, h3)
- Keyboard navigation (TODO)
- Screen reader support (TODO)

## Next Steps

### Phase 4.2: Advanced E2E Tests (TODO)
- Keyboard navigation tests
- Screen reader compatibility
- Cross-browser testing (Firefox, Safari)
- Visual regression testing
- Load testing
- Security testing

### Phase 4.3: CI/CD Integration (TODO)
- GitHub Actions workflow
- Automated test runs on PR
- Test result reporting
- Slack notifications

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [CI/CD Guide](https://playwright.dev/docs/ci)
