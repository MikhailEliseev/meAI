# Phase 30: Chat Session Management - Context

**Gathered:** 2026-06-12 (assumptions mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

Ограничение одна сессия в день на пользователя с мягкой эскалацией к Михаилу. Browser fingerprint идентифицирует уникального пользователя (обход localStorage/cookies). При повторном визите в тот же день — мягкое сообщение с предложением контакта Михаила. UI: expandable tabs в header чата (🕐 История сессий, 🗑️ Очистить). localStorage хранит последние 3 дня сессий (архив для повторных клиентов).

</domain>

<decisions>
## Implementation Decisions

### Browser Fingerprinting
- **D-01:** FingerprintJS Open Source (MIT license) через jsDelivr CDN или self-hosted — НЕ FingerprintJS Pro
  - Pro заблокирован в России (CDN HTTP 502, API HTTP 403, санкции на платёжные системы)
  - Open Source accuracy ~60-80% достаточно для session tracking
  - Текущий чат использует простой `sess_${Date.now()}_${random}` (легко обходится через incognito)

- **D-02:** Fingerprint hash генерируется client-side при первом визите, сохраняется в localStorage как `hermes_fingerprint`
  - Используется для идентификации пользователя между сессиями
  - Не отправляется на сервер в MVP (только localStorage)

### Session Limit Enforcement
- **D-03:** Client-side soft escalation (JavaScript проверяет fingerprint + дату в localStorage) — НЕ server-side hard block
  - SOUL.md:60-66 указывает "мягкая эскалация" с предложением контакта Михаила
  - WordPress proxy stateless (functions.php:46-73), backend enforcement требует PostgreSQL + middleware (8h vs 2h)
  - Trade-off: возможен bypass через DevTools, но соответствует бизнес-требованию (мягкая эскалация, не блокировка)

- **D-04:** При повторном визите в тот же день: показать сообщение из SOUL.md:60-66, предложить контакт Михаила (+79684757766, @mikhaileliseev)
  - Не блокировать чат полностью
  - Пользователь может продолжить (но видит предупреждение)

### Daily Session Window
- **D-05:** "Один день" = календарный день 00:00-23:59 в timezone пользователя (via `Intl.DateTimeFormat().resolvedOptions().timeZone`) — НЕ server UTC
  - Success criteria: "00:00-23:59 по времени пользователя"
  - Россия: 11 часовых поясов (UTC+2 до UTC+12)
  - Server UTC = несправедливые edge cases (Москва 23:00 local → session expires 01:00 UTC = 2 часа)

- **D-06:** Хранить timestamp последней сессии + timezone в localStorage: `hermes_last_session_date` (ISO 8601 date only, no time)
  - При новом сообщении: сравнить текущую дату (user timezone) с сохранённой
  - Если та же дата → показать soft escalation message

### UI Component Architecture
- **D-07:** Expandable tabs компонент из design-showcase-dual-theme.html (lines 1415-1689) адаптировать в hermes-chat-glass.html header — НЕ React component
  - Текущий чат = standalone HTML + vanilla JS (no build step)
  - Design showcase имеет `.demo-tab-bar` CSS + toggle logic
  - Dual-theme CSS vars уже есть (`--bg`, `--surface`, `--glass-border`)
  - Success criteria: только "🕐 История сессий, 🗑️ Очистить" — два простых таба, без complex interactions

- **D-08:** Tabs размещаются в `.chat-header` (hermes-chat-glass.html:94-117) справа от `.header-title`
  - При клике на 🕐: показать список последних 3 дней сессий (дата, количество сообщений, кнопка "Загрузить")
  - При клике на 🗑️: очистить все сессии (localStorage.clear для hermes_* ключей), показать подтверждение

### Session Storage Architecture
- **D-09:** localStorage для session archive (3 дня истории) + fingerprint hash — НЕ PostgreSQL в MVP
  - Текущая реализация: `hermes_session`, `hermes_messages` (hermes-chat-glass.html:399-400)
  - Success criteria: "localStorage хранит последние 3 дня сессий"
  - Backend storage не упомянут в success criteria → scope creep для MVP

- **D-10:** Структура localStorage:
  ```javascript
  hermes_fingerprint: "fp_abc123..." // FingerprintJS visitorId
  hermes_last_session_date: "2026-06-12" // ISO 8601 date (no time)
  hermes_sessions: [{
    date: "2026-06-12",
    sessionId: "sess_...",
    messageCount: 5,
    messages: [...]
  }, ...]
  ```
  - Максимум 3 элемента в `hermes_sessions` (FIFO при добавлении нового)
  - Текущая сессия (`hermes_session`, `hermes_messages`) отдельно для быстрого доступа

### ФЗ-152 Compliance
- **D-11:** Consent banner ОБЯЗАТЕЛЕН перед fingerprinting — browser fingerprints = personal data (ФЗ-152 Article 3, 9)
  - Research: Article 9 требует explicit prior consent
  - Consent banner должен быть перед вызовом FingerprintJS.load()
  - Текст: "Мы используем fingerprinting для идентификации сессий. Продолжая, вы соглашаетесь."

- **D-12:** Data localization: fingerprints хранятся на Russian server (если добавляется backend storage) — ФЗ-152 Article 18.1
  - В MVP fingerprints только в localStorage (client-side) → compliance автоматически
  - Если Phase 30.5 добавит PostgreSQL storage → сервер 138.16.224.188 (уже Russian server)

- **D-13:** Retention period: 90 дней для fingerprint hashes (если добавляется backend) — industry standard, ФЗ-152 Article 21
  - В MVP: localStorage автоматически expires при очистке пользователем или браузером
  - Privacy policy должна disclosure: "fingerprinting для session continuity, 90 дней retention"

- **D-14:** Encryption: AES-256-GCM рекомендуется, но не mandatory (ФЗ-152 Article 19 requires "necessary measures", не explicit encryption)
  - В MVP: fingerprint hash уже хешированный (FingerprintJS output), дополнительная encryption = overkill
  - Если Phase 30.5 добавит PostgreSQL: шифрование fingerprint колонки рекомендуется (defensive measure)

### Claude's Discretion
- FingerprintJS CDN (jsDelivr) vs self-hosted bundle (performance vs control trade-off)
- Consent banner UI дизайн (соответствие dual-theme system)
- Session archive UI: dropdown vs modal vs sidebar (expandable tabs уже определены, но внутренняя структура списка сессий)
- Тестирование: timezone edge cases, localStorage quota limits, incognito mode behavior

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Существующий код
- `AIM/theme/chat/hermes-chat-glass.html` — Текущий чат: localStorage usage (lines 399-400), SSE streaming, dual-theme, header structure (lines 94-117)
- `AIM/frontend/design-showcase-dual-theme.html` — Expandable tabs component (lines 1415-1689): `.demo-tab-bar`, `.demo-tab`, hover/active states
- `AIM/hermes/skills/aim/SOUL.md` — Session limit soft escalation rule (lines 60-66): текст сообщения, предложение контакта Михаила
- `AIM/theme/functions.php` — WordPress REST proxy (lines 46-73): stateless streaming к Hermes API

### External libraries
- FingerprintJS Open Source: https://github.com/fingerprintjs/fingerprintjs (MIT license, jsDelivr CDN or self-hosted)
- ФЗ-152 compliance: https://www.consultant.ru/document/cons_doc_LAW_61801/ (Articles 3, 9, 18.1, 19, 21)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Dual-theme CSS system**: `:root` (light) + `[data-theme="dark"]` (art deco gold) — lines 11-36 hermes-chat-glass.html
- **localStorage pattern**: `hermes_session`, `hermes_messages` для persistence — lines 399-400
- **Theme toggle button**: `.theme-toggle` с localStorage sync — lines 51-74, 449-463
- **Expandable tabs CSS**: `.demo-tab-bar`, `.demo-tab`, cubic-bezier transitions — design-showcase lines 1415-1460

### Established Patterns
- **Standalone HTML + vanilla JS**: No React, no build step, inline styles — hermes-chat-glass.html structure
- **SSE streaming**: Real-time updates через WordPress proxy `/wp-json/aim/v1/chat/stream` — lines 498-550
- **Markdown parsing**: Client-side `parseMarkdown()` для форматирования — lines 409-447
- **Soft UX patterns**: Мягкие подсказки вместо hard blocks (SOUL.md philosophy)

### Integration Points
- **WordPress REST proxy**: functions.php прокси headers к Hermes API (Authorization, Content-Type) — lines 46-73
- **SOUL.md soft escalation**: Текст сообщения уже определён в SOUL.md:60-66 — нужно только trigger logic
- **localStorage migration**: Добавление новых ключей (`hermes_fingerprint`, `hermes_sessions`) к существующим

</code_context>

<specifics>
## Specific Ideas

### FingerprintJS Integration
- jsDelivr CDN для быстрого прототипирования: `<script src="https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@3/dist/fp.min.js"></script>`
- Self-hosted bundle для production (избежать CDN downtime)
- Вызов при page load: `FingerprintJS.load().then(fp => fp.get()).then(result => result.visitorId)`

### Consent Banner
- Минималистичный banner внизу экрана (не блокирует UI)
- Dual-theme styling (light/dark соответствие)
- Кнопки: "Согласен" (зелёная) + "Подробнее" (ссылка на privacy policy)
- Сохранять consent в localStorage: `hermes_consent_fingerprint: true`

### Session Archive UI
- Expandable dropdown под header (не modal — меньше friction)
- Список сессий: дата (human-readable), количество сообщений, кнопка "Загрузить"
- При клике "Загрузить": восстановить `hermes_session` + `hermes_messages` из архива, reload страницы
- При клике 🗑️: показать confirm dialog "Удалить все сессии? (3 дня истории)", затем `localStorage.removeItem()` для всех `hermes_*` ключей

### Timezone Edge Cases
- Пользователь меняет timezone во время сессии: сравнивать saved date string, игнорировать timezone change (date stays same)
- Daylight Saving Time transitions: `Intl.DateTimeFormat` автоматически handles DST
- User travels across timezones: использовать browser's current timezone (не сохранять timezone в localStorage)

</specifics>

<deferred>
## Deferred Ideas

### Server-Side Hard Limit (Phase 30.5 candidate)
- PostgreSQL `sessions` table: `fingerprint_hash`, `last_session_date`, `session_count`
- Middleware validation перед WordPress proxy: проверка rate limit
- Backend enforcement если client-side bypass становится проблемой
- Требует breaking stateless proxy pattern

### Cross-Device Session Sync (Phase 30.6 candidate)
- Backend storage fingerprints + session data
- User login для связывания devices
- Sync через WebSocket или polling
- Не упомянуто в success criteria → out of scope для Phase 30

### Advanced Abuse Prevention (Phase 30.7 candidate)
- FingerprintJS Pro Smart Signals (VPN detection, bot detection) — если Open Source accuracy недостаточна
- Rate limiting на backend (X sessions per fingerprint per week)
- CAPTCHA при подозрительной активности
- Зависит от actual abuse metrics после Phase 30 deploy

### Privacy Policy Page (Phase 30.8 candidate)
- Dedicated `/privacy` page с disclosure fingerprinting usage
- GDPR/ФЗ-152 compliance details
- User rights: data access, deletion requests
- Consent banner ссылается на эту страницу
- Не входит в Phase 30 (только banner)

</deferred>
