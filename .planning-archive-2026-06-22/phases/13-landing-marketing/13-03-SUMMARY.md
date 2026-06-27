---
phase: 13-landing-marketing
plan: 03
status: complete
completed_at: 2026-05-21
---

# Phase 13-03: VK Ads + Telegram Ads API Clients

## Summary

Built VK Ads and Telegram Ads API clients following the YandexDirectAPIClient pattern (async httpx, dataclass models, structlog logging). Both clients include `sync_campaigns_to_db()` for Campaign DB table sync via upsert pattern. Added configuration fields and env var documentation.

## Completed Tasks

### Task 1: Build VK Ads API client
- **File:** `AIM/src/aim/subagents/ads/vk_ads_client.py` (228 lines)
- `VKCampaignInfo` dataclass (7 fields: id, name, status, daily_budget, start_time, end_time, platform)
- `VKAPIError` exception class
- `VKAdsClient` with `BASE_URL = "https://api.vk.com/method"`, `API_VERSION = "5.199"`
- Methods: `_call()`, `get_campaigns(account_id)`, `get_campaign_stats(account_id, campaign_ids, date_from, date_to)`, `create_campaign(account_id, name, daily_budget, start_time)`
- kopecks→RUB conversion: `daily_budget_kopecks / 100`
- Reuses `CampaignStats` from `yandex_direct_client` via lazy import

### Task 2: Build Telegram Ads API client
- **File:** `AIM/src/aim/subagents/ads/telegram_ads_client.py` (231 lines)
- `TelegramCampaignInfo` dataclass (11 fields)
- `TelegramAPIError` exception class
- `TelegramAdsClient` with `BASE_URL = "https://api.telegram.org"`
- Methods: `_call()`, `get_campaigns()`, `get_campaign_stats(campaign_ids, date_from, date_to)`, `create_campaign(channel_username, title, daily_budget, message_text)`
- JSON error handling via `{"ok": false}` pattern

### Task 3: Add settings fields, env vars, and tests
- **File:** `AIM/src/aim/subagents/ads/config/settings.py` — added `vk_ads_access_token`, `vk_ads_account_id`, `telegram_ads_bot_token` (all Optional, default None)
- **File:** `AIM/.env.example` — added VK Ads and Telegram Ads sections with setup instructions
- **File:** `AIM/tests/subagents/test_vk_ads_client.py` — 4 tests (get_campaigns, empty response, API error, stats)
- **File:** `AIM/tests/subagents/test_telegram_ads_client.py` — 4 tests (create_campaign, get_campaigns, stats, API error)

### Task 4: Add sync_campaigns_to_db() to both clients
- Both clients use upsert pattern: SELECT by `external_id + platform`, then INSERT or UPDATE
- VK stores `platform="vk"`, converts `start_time` via `datetime.fromtimestamp(ci.start_time, tz=timezone.utc)`
- Telegram stores `platform="telegram"`, maps `ci.title` → `name`, includes `total_spent`
- Both return `int` count of synced campaigns

## Acceptance Criteria

- `grep -c "vk_ads_access_token" settings.py` → 1 ✅
- `grep -c "telegram_ads_bot_token" settings.py` → 1 ✅
- `grep -c "VK_ADS_ACCESS_TOKEN" .env.example` → 2 ✅
- `grep -c "TELEGRAM_ADS_BOT_TOKEN" .env.example` → 2 ✅
- `grep -c "async def sync_campaigns_to_db" vk_ads_client.py` → 1 ✅
- `grep -c "async def sync_campaigns_to_db" telegram_ads_client.py` → 1 ✅
- Все 8 тестов проходят ✅

## Threat Model Verification

| Threat | Disposition | Status |
|--------|-------------|--------|
| T-13-03-01: Spoofed API responses | Mitigated: JSON structure verification in _call() | ✅ |
| T-13-03-02: Token in logs | Mitigated: structlog configured without API response body logging | ✅ |
| T-13-03-03: Budget tampering | Accepted: BudgetGuard deferred to future phase | ⚠️ |
| T-13-03-04: API rate limits | Accepted: resilience layer deferred | ⚠️ |
| T-13-03-05: Plaintext token in .env | Mitigated: .env gitignored, Docker secrets for prod | ✅ |
