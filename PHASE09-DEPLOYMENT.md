# Phase 09 Deployment Summary

**Date:** 2026-06-28 04:57 UTC (07:57 MSK)
**Status:** ✅ DEPLOYED

---

## What Was Deployed

### 1. Hermes Backend (FastAPI)
**File:** `/opt/aim/AIM/hermes/app/main.py`
- **Change:** Added report_url extraction in SSE finish event (lines 573-610)
- **Backup:** `main.py.backup-phase09-20260628-045438`
- **Status:** ✅ Deployed, container restarted

**What it does:**
- Parses `generate_html_report` tool result from agent_result
- Extracts `report_url`, `report_title`, `session_hash`
- Includes them in finish event: `{"type": "finish", "session_id": "...", "report_url": "...", ...}`

### 2. WordPress Chat Frontend
**File:** `/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat-pro.html`
- **Size:** 1020 lines
- **Status:** ✅ Deployed

**Features:**
- Phase Tracker panel (8 phases: prescan → financials → doctors → competitors → reviews → media → tech audit → report)
- Real-time phase detection from tool-progress events via STAGE_TO_PHASE mapping
- Phase states: pending (gray) → working (spinner, pulse) → done (green checkmark)
- Progress counter: "3/8" in panel header
- Live counters per phase: "5 конкурентов", "12 врачей", extracted from tool-progress messages

**Report Preview:**
- Appears when finish event contains report_url
- Badge "✓ Отчёт готов"
- Title, stats grid
- Two CTAs: "Открыть полный отчёт" (primary), "Прислать на почту/TG" (secondary)

**Fallback Form:**
- Email/Telegram input field
- POST to `/wp-json/aim/v1/fallback`
- Success animation on submit

### 3. WordPress Backend (REST API)
**File:** `/var/www/iamaim.ru/wp-content/themes/aim-theme/aim-pro-endpoints.php`
- **Size:** 172 lines
- **Status:** ✅ Deployed
- **Included in:** `functions.php` (backup created)

**Endpoints:**
1. `POST /wp-json/aim/v1/fallback`
   - Saves contact to `wp_options` (max 100 entries)
   - Detects type: email | telegram | other
   - Sends Telegram notification to admin (if configured)
   - Sends email to admin
   - Sends report email to user (if email + report_url ready)

2. `GET /wp-json/aim/v1/session-report/<session_id>`
   - Placeholder for resume functionality

---

## Testing Results

### ✅ Fallback Endpoint
```bash
curl -X POST https://iamaim.ru/wp-json/aim/v1/fallback \
  -H 'Content-Type: application/json' \
  -d '{"contact":"test@example.com","session_id":"test_session_123","report_url":"https://iamaim.ru/test-report"}'
```

**Response:**
```json
{
  "ok": true,
  "type": "email",
  "message": "Запрос сохранён. Отчёт будет отправлен после завершения анализа."
}
```

### ✅ Hermes Container
- Status: Up 15 minutes (healthy)
- Restarted successfully at 04:56:47 UTC
- Logs show clean startup, no errors

---

## Configuration Required

### Telegram Notifications (Optional)
WordPress options need to be set:
```php
update_option('aim_telegram_bot_token', 'YOUR_BOT_TOKEN');
update_option('aim_telegram_admin_chat_id', 'YOUR_CHAT_ID');
```

Without these, fallback form works but Telegram notifications are skipped.

---

## Access URLs

### New Chat (Phase 09)
- **Development:** `https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat-pro.html`
- **Production (after testing):** Replace `hermes-chat.html` with pro version

### Old Chat (Fallback)
- **Current:** `https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat.html`
- Unchanged, stable reference design

---

## Next Steps

### 1. End-to-End Testing (Task #2)
Run a real presale through the new chat:
1. Open `https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat-pro.html`
2. Submit a clinic URL
3. Verify:
   - Phase Tracker appears on first tool-progress event
   - Phases change state: pending → working → done
   - Progress counter updates
   - Report Preview appears when Hermes finishes
   - Fallback form works (submit email, check admin notifications)

### 2. Switch to Pro Version (After Testing)
```bash
ssh aim
cd /var/www/iamaim.ru/wp-content/themes/aim-theme/chat/
mv hermes-chat.html hermes-chat-legacy.html
mv hermes-chat-pro.html hermes-chat.html
```

Now Phase 09 version is default.

---

## Rollback Plan

If Phase 09 breaks something:

### 1. Restore Old Chat
```bash
ssh aim
cd /var/www/iamaim.ru/wp-content/themes/aim-theme/chat/
cp hermes-chat-legacy.html hermes-chat.html  # or delete hermes-chat-pro.html
```

### 2. Restore Hermes Backend
```bash
ssh aim
cd /opt/aim/AIM/hermes/app/
cp main.py.backup-phase09-20260628-045438 main.py
cd /opt/aim/AIM
docker compose restart hermes
```

### 3. Remove WordPress Endpoint
```bash
ssh aim
cd /var/www/iamaim.ru/wp-content/themes/aim-theme/
# Edit functions.php, remove the two lines:
# // Phase 09: AIM Pro endpoints...
# include_once get_template_directory() . '/aim-pro-endpoints.php';
nano functions.php
```

---

## Files Modified

| File | Change | Backup |
|------|--------|--------|
| `/opt/aim/AIM/hermes/app/main.py` | Added report_url extraction | `main.py.backup-phase09-20260628-045438` |
| `/var/www/.../functions.php` | Added include aim-pro-endpoints.php | `functions.php.backup-phase09-20260628-045643` |

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `/var/www/.../hermes-chat-pro.html` | 1020 lines | Phase 09 chat with tracker + report preview |
| `/var/www/.../aim-pro-endpoints.php` | 172 lines | Fallback form REST API |

---

## Session State

**Tasks:**
- [x] #3: Добавить report_url в finish event SSE stream
- [x] #4: Создать hermes-chat-pro.html с Phase Tracker
- [x] #1: Развернуть aim-pro-endpoints.php на сервер
- [ ] #2: Протестировать Phase 09 end-to-end

**SESSION.md:** Will be updated after testing confirms Phase 09 works.

---

## Known Limitations

1. **Telegram notifications require manual config** — bot token and chat ID must be set in WordPress options
2. **Session report endpoint is placeholder** — resume functionality not yet implemented
3. **No automated tests** — end-to-end testing is manual
4. **HeadroomGuard not yet tested with Phase 09** — streaming with compression needs validation

---

**Deployment complete. Ready for end-to-end testing.**
