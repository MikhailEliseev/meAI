# Phase 09 React Chat Deployment — 2026-06-28 10:53 MSK

**Status:** ✅ DEPLOYED
**Commit:** 5b3bc13 `feat(chat): Phase 09 integration into homepage React chat`

---

## What Was Done

### 1. Created 3 New Components

| Component | Size | Purpose |
|-----------|------|---------|
| `PhaseTracker.jsx` | 71 lines | 8-phase progress panel with pending/working/done states, live counters |
| `ReportPreview.jsx` | 52 lines | WOW card with badge "✓ Отчёт готов", stats grid, 2 CTA buttons |
| `FallbackForm.jsx` | 85 lines | Modal form for email/Telegram collection, POST to /wp-json/aim/v1/fallback |

### 2. Modified Existing Files

**useStreamChat.js:**
- Added `phases` state (8 phases initialized as 'pending')
- Added `reportData` state (null until finish event with report_url)
- Added `updatePhase(stage, message)` callback — detects phase by stage, updates status, extracts counter
- Modified SSE event handler:
  - `tool-progress` → calls `updatePhase(event.stage, event.message)`
  - `finish` → extracts `report_url`, sets `reportData`, marks all phases as 'done'
- Return `phases` and `reportData` in hook output

**index.jsx:**
- Import Phase 09 components
- Destructure `phases`, `reportData`, `sessionId` from `useStreamChat()`
- Add `showFallback` state (boolean)
- Conditional render:
  - PhaseTracker: `{phases.some(p => p.status !== 'pending') && <PhaseTracker />}`
  - ReportPreview: `{reportData && <ReportPreview onRequestEmail={() => setShowFallback(true)} />}`
  - FallbackForm: `{showFallback && <FallbackForm sessionId={sessionId} reportUrl={reportData?.url} onClose={() => setShowFallback(false)} />}`

**chat.css:**
- Added `@keyframes pulse` for Phase Tracker spinner
- Added `@keyframes revealUp` for Report Preview reveal animation
- Added `.fallback-backdrop` with `backdrop-filter: blur(4px)`

### 3. Build & Deploy

**Local:**
```bash
npm run build
# Output: dist/chat-bundle.js (22KB), dist/chat-bundle.css (721B)
```

**Server:**
```bash
mkdir -p /var/www/iamaim.ru/wp-content/themes/aim-theme/assets/js/
scp dist/chat-bundle.* aim:/var/www/.../assets/js/
```

**Backup:**
- Local: `phase09-react-backup-20260628-104946.tar.gz` (11KB)
- Contains: `src/`, `dist/`, `package.json`, `esbuild.config.mjs` (pre-Phase 09 version)

---

## How It Works

### Phase Tracker Flow

1. User sends URL → Hermes starts presale
2. Hermes emits `tool-progress` events with `stage` field:
   ```json
   {"type": "tool-progress", "stage": "run_prescan", "message": "Анализ сайта завершён"}
   ```
3. `useStreamChat.updatePhase()` detects phase from stage via STAGE_TO_PHASE mapping
4. Phase state updates: `{id: 1, status: 'working', counter: null}`
5. PhaseTracker renders phase card with spinner icon
6. When tool completes, phase transitions to 'done' (green checkmark)

**Stage to Phase Mapping:**
```javascript
const PHASES = [
  { id: 1, stages: ['run_prescan', 'prescan'] },
  { id: 2, stages: ['find_company_financials', 'financials', 'finance'] },
  { id: 3, stages: ['find_doctor_handles', 'doctors', 'run_instagram_content', 'instagram'] },
  { id: 4, stages: ['find_competitors', 'competitors', 'run_ci_analysis', 'ci_analysis'] },
  { id: 5, stages: ['run_review_platforms', 'reviews', 'run_forum_pains', 'forum_pains'] },
  { id: 6, stages: ['run_media_urls', 'media', 'smi'] },
  { id: 7, stages: ['run_tech_seo_audit', 'tech_seo', 'run_seo_audit', 'seo', 'run_lighthouse'] },
  { id: 8, stages: ['generate_html_report', 'html_report', 'report'] },
];
```

### Report Preview Flow

1. Hermes completes presale, calls `generate_html_report` tool
2. Backend (main.py lines 573-610) extracts `report_url` from tool result
3. SSE finish event includes:
   ```json
   {
     "type": "finish",
     "session_id": "sess_...",
     "report_url": "https://iamaim.ru/wp-json/aim/v1/session/abc123",
     "report_title": "Разведка клиники XYZ"
   }
   ```
4. `useStreamChat` sets `reportData` state
5. ReportPreview renders with fadeIn animation
6. Two CTAs:
   - Primary: "Открыть полный отчёт" → opens `report_url` in new tab
   - Secondary: "Прислать на почту/TG" → opens FallbackForm

### Fallback Form Flow

1. User clicks secondary CTA → `setShowFallback(true)`
2. Modal opens with input field (email or @telegram)
3. User submits → POST `/wp-json/aim/v1/fallback`:
   ```json
   {
     "contact": "user@example.com",
     "session_id": "sess_...",
     "report_url": "https://..."
   }
   ```
4. Backend (aim-pro-endpoints.php) saves contact, sends Telegram/email notifications
5. Success animation → modal closes after 2s

---

## Testing Checklist

### Phase Tracker
- [ ] Open https://iamaim.ru
- [ ] Send clinic URL (e.g., "стоматология-смайл.рф")
- [ ] Verify Phase Tracker appears when first tool-progress event arrives
- [ ] Verify phases change state: pending (gray) → working (spinner) → done (green checkmark)
- [ ] Verify progress counter updates: "1/8", "2/8", ..., "8/8"
- [ ] Verify live counters appear if message contains numbers ("5 конкурентов", "12 врачей")

### Report Preview
- [ ] Wait for presale completion (~2-5 min)
- [ ] Verify Report Preview appears with fadeIn animation
- [ ] Verify badge "✓ Отчёт готов" is visible
- [ ] Verify title and stats are displayed (may be empty if Hermes doesn't send stats)
- [ ] Click "Открыть полный отчёт" → new tab opens with report
- [ ] Click "Прислать на почту/TG" → Fallback Form opens

### Fallback Form
- [ ] Enter email (e.g., "test@example.com")
- [ ] Submit → success animation plays
- [ ] Modal closes after 2s
- [ ] Check server logs: contact saved to wp_options, Telegram/email notifications sent
- [ ] Repeat with Telegram username (e.g., "@testuser")

### Edge Cases
- [ ] Refresh page during presale → Phase Tracker state lost (expected, OK)
- [ ] Multiple sessions → Phase Tracker resets for new session
- [ ] Presale completes WITHOUT report_url → Report Preview doesn't appear (OK)
- [ ] Network error during fallback submit → error message displays

---

## Rollback Instructions

If Phase 09 breaks the chat:

### 1. Restore Local Backup
```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/theme/chat/
tar -xzf phase09-react-backup-20260628-104946.tar.gz
npm run build
```

### 2. Rollback Git Commit
```bash
git revert 5b3bc13
# OR
git reset --hard HEAD~1  # WARNING: loses commit
```

### 3. Restore Server Bundle
```bash
# No backup exists on server (first deployment)
# Redeploy from local backup:
scp dist/chat-bundle.* aim:/var/www/iamaim.ru/wp-content/themes/aim-theme/assets/js/
```

### 4. Clear Browser Cache
Ctrl+Shift+R on https://iamaim.ru to force reload.

---

## Known Limitations

1. **Phase Tracker state не персистится** — при перезагрузке страницы прогресс теряется. Это OK для 2-5 минутных сессий.

2. **Stats в Report Preview могут быть пустыми** — если Hermes backend не возвращает статистики в finish event. Для полных статистик нужно добавить их в Hermes (BACKLOG).

3. **Resume функциональность отсутствует** — если пользователь закрыл страницу и вернулся, Phase Tracker начинается с нуля. Для resume нужен endpoint `GET /wp-json/aim/v1/session/<id>/progress` (BACKLOG).

4. **Telegram notifications требуют настройки** — `aim_telegram_bot_token` и `aim_telegram_admin_chat_id` должны быть установлены в WordPress options.

---

## Files Modified

| File | Status | Changes |
|------|--------|---------|
| `src/components/PhaseTracker.jsx` | NEW | 71 lines, 8-phase progress panel |
| `src/components/ReportPreview.jsx` | NEW | 52 lines, WOW card with CTAs |
| `src/components/FallbackForm.jsx` | NEW | 85 lines, modal form |
| `src/useStreamChat.js` | MODIFIED | +47 lines (phases state, updatePhase, tool-progress handler) |
| `src/index.jsx` | MODIFIED | +18 lines (import components, conditional render) |
| `src/chat.css` | MODIFIED | +16 lines (Phase 09 animations) |
| `dist/chat-bundle.js` | REBUILT | 22KB (was empty before) |
| `dist/chat-bundle.css` | REBUILT | 721B (was empty before) |

---

## Next Steps

1. **Test Phase 09 end-to-end** — run full presale через https://iamaim.ru, verify all 3 features work
2. **Update Task #2** — mark as completed after successful test
3. **Monitor errors** — check browser console and server logs for JavaScript errors
4. **Optimize if needed** — if bundle size grows, consider code splitting

---

**Deployment complete. Chat widget on https://iamaim.ru now has Phase 09 features.**
