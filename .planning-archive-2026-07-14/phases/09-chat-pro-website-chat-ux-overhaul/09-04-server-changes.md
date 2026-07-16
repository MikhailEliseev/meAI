# Server Changes for Plan 09-04

## Task 1: AIM Services Catalogue

**File created:** `/opt/data/services.md` on server (ssh aim)

**Line count:** 159 lines

**Content:** 7 AIM services with prices, descriptions, problem-solution mapping, ideal niches:
1. SEO Optimization (180K ₽)
2. Instagram Content Production (120K ₽/месяц)
3. Яндекс.Директ Campaign (80K ₽/месяц)
4. Technical Site Optimization (60K ₽)
5. Reputation Management (40K ₽/месяц)
6. Content Strategy + Blogging (90K ₽/месяц)
7. Whitefields Analysis + Strategy (150K ₽)

**Verification:** `ssh aim "test -f /opt/data/services.md && wc -l /opt/data/services.md"`

## Task 4: Frontend Validation for Contact Collection

**Files modified:**
- `/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/chat.js`
- `/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/chat.css`

**Changes to chat.js:**
- Added `isValidEmail(email)` function with regex validation
- Added `isValidName(name)` function (non-empty after trim)
- Added `showValidationError(msg)` function to display error bubbles
- Functions inserted after `generateSessionId()` function

**Changes to chat.css:**
- Added `.tp-message.error-message` styling:
  - Light theme: `rgba(220, 38, 38, 0.1)` background
  - Dark theme: `rgba(220, 38, 38, 0.15)` background
  - Red left border: `3px solid #DC2626`
  - Fade-in animation on display

**Verification:** `ssh aim "grep -c isValidEmail /var/www/iamaim.ru/wp-content/themes/aim-theme/chat/chat.js"` (returns 1)
