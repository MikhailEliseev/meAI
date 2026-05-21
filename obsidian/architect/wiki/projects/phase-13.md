# Phase 13: Landing + Marketing Campaigns

**Status:** ✅ Complete (4/4 plans)
**Period:** 2026-05-16 → 2026-05-21

## Plans

### 13-01: Landing Page (iamaim.ru)
- Next.js лендинг с конверсионной оптимизацией
- reCAPTCHA v3 + AJAX form
- SEO мета-теги, Schema.org (MedicalOrganization)

### 13-02: Marketing Campaigns — Real Stats + ФЗ-38
- Yandex Direct Reports API: реальный TSV парсинг (csv.DictReader)
- Async polling: 201/202 → retryIn header → 200
- Micros → RUB конверсия (cost / 1_000_000)
- ФЗ-38 compliance: disclaimer, prohibited claims (8), age 18+, ЕРИР
- Campaign DB sync (upsert: external_id + platform)

### 13-03: VK Ads + Telegram Ads API Clients
- VKAdsClient: VK Marketing API v5.199, kopecks→RUB
- TelegramAdsClient: Telegram Bot API
- Оба с sync_campaigns_to_db()
- 8 тестов

### 13-04: Campaign Models + Attribution Pipeline
- Campaign, AdGroup, Ad, CampaignMetric models
- Daily campaign stat collection
- Multi-platform attribution (cost per lead)

## Key Files

```
AIM/src/aim/subagents/ads/
├── yandex_direct_client.py    # Yandex Direct API v5 (597 lines)
├── vk_ads_client.py           # VK Ads API (228 lines)
├── telegram_ads_client.py     # Telegram Bot API (231 lines)
├── ad_copy_generator.py       # ФЗ-38 compliant ad copy
└── config/settings.py         # AdsSettings (all platforms)

AIM/src/aim/models/
└── campaign_models.py         # Campaign, AdGroup, Ad, CampaignMetric

AIM/tests/
├── unit/test_yandex_direct_stats.py     # 3 tests
├── unit/test_ad_copy_compliance.py      # 7 tests
├── subagents/test_vk_ads_client.py      # 4 tests
└── subagents/test_telegram_ads_client.py # 4 tests
```

## Ad Platforms Coverage

| Platform | Client | Auth | Budget Unit | Status |
|----------|--------|------|-------------|--------|
| Yandex Direct | YandexDirectAPIClient | OAuth token | Micros (÷1M→RUB) | ✅ |
| VK Ads | VKAdsClient | Access token | Kopecks (÷100→RUB) | ✅ |
| Telegram Ads | TelegramAdsClient | Bot token | RUB | ✅ |
| Google Ads | (planned) | OAuth2 | Micros | ⏳ |
| Facebook Ads | (planned) | OAuth2 | Cents | ⏳ |
