# Ads Magister

**Type:** Magister (управляющий агент)
**Domain:** Реклама (Яндекс.Директ, VK Ads, Telegram Ads)
**Status:** ✅ Implemented (Phase 13)

## Responsibility

Управляет рекламными кампаниями медицинских клиник на трёх платформах:
- Яндекс.Директ (поисковая + медийная реклама)
- VK Ads (социальная реклама)
- Telegram Ads (продвигаемые сообщения в каналах)

## Subagents

| Subagent | File | Purpose |
|----------|------|---------|
| YandexDirectAPIClient | `subagents/ads/yandex_direct_client.py` | Кампании + статистика Яндекс.Директ |
| VKAdsClient | `subagents/ads/vk_ads_client.py` | Кампании + статистика VK Ads |
| TelegramAdsClient | `subagents/ads/telegram_ads_client.py` | Продвигаемые сообщения Telegram |
| AdCopyGenerator | `subagents/ads/ad_copy_generator.py` | Генерация рекламных текстов с ФЗ-38 |
| CampaignAttribution | (in ads magister) | Атрибуция и ROI по кампаниям |

## Key APIs

- Yandex Direct API v5: `https://api.direct.yandex.com/json/v5`
- VK Ads API v5.199: `https://api.vk.com/method/ads.*`
- Telegram Bot API: `https://api.telegram.org/bot<token>/<method>`

## ФЗ-38 Compliance

Все рекламные тексты проходят автоматическую проверку:
- Обязательный disclaimer: «ИМЕЮТСЯ ПРОТИВОПОКАЗАНИЯ, НЕОБХОДИМА КОНСУЛЬТАЦИЯ СПЕЦИАЛИСТА»
- 8 запрещённых утверждений эффективности
- Возрастное ограничение 18+ (не 0+/6+/12+/16+)
- Предупреждение об отсутствии ЕРИР токена (ФЗ-347)

## Database Sync

Все клиенты имеют метод `sync_campaigns_to_db()`:
- Upsert pattern: SELECT по external_id + platform, затем INSERT или UPDATE
- VK: platform="vk", start_time через `datetime.fromtimestamp()`
- Telegram: platform="telegram", title→name mapping
- Yandex: platform="yandex", даты через `datetime.fromisoformat()`

## Vault

`AIM/obsidian/ads-magister/` — LLM Wiki паттерн (raw/ + wiki/ + decisions/)
