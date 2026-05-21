---
phase: 13-landing-marketing
plan: 02
status: complete
completed_at: 2026-05-21
---

# Phase 13-02: Marketing Campaigns — Real Stats + ФЗ-38 Compliance

## Summary

Replaced MOCK Yandex Direct stats with real TSV report parsing, added ФЗ-38 medical advertising compliance to AdCopyGenerator, wrote 10 tests, and added `sync_campaigns_to_db()` for campaign DB sync.

## Completed Tasks

### Task 1: Replace MOCK stats with real Yandex Direct Reports API TSV parsing
- **File:** `AIM/src/aim/subagents/ads/yandex_direct_client.py`
- Replaced hardcoded CampaignStats with real Reports API implementation
- Added `csv.DictReader` with `delimiter='\t'` for TSV parsing
- Handles async report generation (201/202 → poll → 200)
- Cost/Cpc/Cpa conversion from micros to RUB (divide by 1_000_000)
- Max 10 polling iterations with `retryIn` header respect
- Empty TSV returns `[]`

### Task 2: Add ФЗ-38 medical advertising compliance to AdCopyGenerator
- **File:** `AIM/src/aim/subagents/ads/ad_copy_generator.py`
- Added `FZ38_MANDATORY_DISCLAIMER`, `MEDICAL_KEYWORDS` (17 terms), `PROHIBITED_MEDICAL_CLAIMS` (8 claims)
- Extended `_check_compliance()` with:
  - Medical ad detection via keyword matching
  - Mandatory disclaimer check (ФЗ-38 ст.24 ч.1)
  - Prohibited efficacy claims block (ФЗ-38 ст.24 ч.7-8)
  - Age restriction warnings (must be 18+, not 0+/6+/12+/16+)
  - ЕРИР token warning (ФЗ-347)
- Removed 2 duplicate `generate_hashtags` functions (was 3 → now 1)

### Task 3: Write tests
- **Files:** `AIM/tests/unit/test_yandex_direct_stats.py` (3 tests), `AIM/tests/unit/test_ad_copy_compliance.py` (7 tests)
- TSV parsing: real data, empty response, async polling
- Compliance: disclaimer required/present, non-medical skip, prohibited claims, age 16+/18+, ЕРИР

### Task 4: Add sync_campaigns_to_db()
- **File:** `AIM/src/aim/subagents/ads/yandex_direct_client.py`
- Upsert pattern: SELECT by external_id + platform, then INSERT or UPDATE
- Returns count of synced campaigns
- Uses `db_session_factory` callable (same pattern as AttributionPipeline)

## Acceptance Criteria

- `grep -c "Mock stats" yandex_direct_client.py` → 0 ✅
- `grep -c "def generate_hashtags" ad_copy_generator.py` → 1 ✅
- `grep -c "async def sync_campaigns_to_db" yandex_direct_client.py` → 1 ✅
- Все 10 тестов проходят ✅
- Метод содержит `csv.DictReader` с `delimiter='\t'` ✅
- Метод содержит конверсию `Cost / 1_000_000` (micros → RUB) ✅
- Метод содержит `while response.status_code in (201, 202)` для async polling ✅

## Threat Model Verification

| Threat | Disposition | Status |
|--------|-------------|--------|
| T-13-02-01: TSV parsing tampering | Mitigated: csv.DictReader with strict field access | ✅ |
| T-13-02-02: ФЗ-38 non-compliance | Mitigated: disclaimer injection, claims blocklist, age enforcement | ✅ |
| T-13-02-03: Missing ЕРИР token | Mitigated: warning generated on missing token | ✅ |
| T-13-02-04: Async polling DoS | Mitigated: max 10 iterations with retryIn timeout | ✅ |
| T-13-02-05: API token in logs | Mitigated: structlog configured without API response body logging | ✅ |
