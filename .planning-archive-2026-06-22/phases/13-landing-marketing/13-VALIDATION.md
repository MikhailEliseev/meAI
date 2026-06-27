---
phase: 13-landing-marketing
type: validation
subsystem: marketing
tags: [nyquist, validation, tests]
status: complete
completed: 2026-05-20
---

# Phase 13-02 Validation Strategy

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.4.0 + pytest-asyncio >=0.21.0 |
| Config file | AIM/tests/conftest.py |
| Quick run | `pytest AIM/tests/unit/test_ads_campaign_creator_agent.py -x` |
| Full suite | `pytest AIM/tests/ -x --timeout=60` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAND-04 | A/B test variant assignment via middleware | unit | `pytest AIM/tests/unit/test_ab_middleware.py::test_variant_assignment -x` | ❌ Wave 0 |
| LAND-04 | A/B test cookie sticky assignment | unit | `pytest AIM/tests/unit/test_ab_middleware.py::test_cookie_sticky -x` | ❌ Wave 0 |
| LAND-04 | Statistical significance calculation | unit | `pytest AIM/tests/unit/test_ab_test_engine.py::test_chi_square_significance -x` | ❌ Wave 0 |
| LAND-04 | A/B test sample size calculator | unit | `pytest AIM/tests/unit/test_ab_test_engine.py::test_sample_size_calculation -x` | ❌ Wave 0 |
| MKTG-01 | Yandex Direct campaign stats (real, not MOCK) | unit | `pytest AIM/tests/unit/test_yandex_direct_stats.py::test_real_tsv_parsing -x` | ❌ Wave 0 |
| MKTG-01 | VK Ads campaign creation | unit | `pytest AIM/tests/subagents/test_vk_ads_client.py::test_create_campaign -x` | ❌ Wave 0 |
| MKTG-02 | UTM-to-lead attribution | integration | `pytest AIM/tests/integration/test_attribution_pipeline.py::test_utm_to_lead_link -x` | ❌ Wave 0 |
| MKTG-02 | Campaign-to-conversion tracking | integration | `pytest AIM/tests/integration/test_attribution_pipeline.py::test_conversion_attribution -x` | ❌ Wave 0 |
| MKTG-03 | ROI calculation from cost + revenue | unit | `pytest AIM/tests/unit/test_roi_calculator.py::test_roas_calculation -x` | ❌ Wave 0 |
| MKTG-03 | ROI breakdown by channel | unit | `pytest AIM/tests/unit/test_roi_calculator.py::test_channel_breakdown -x` | ❌ Wave 0 |

## Sampling Rate

- **Per task commit:** `pytest AIM/tests/unit/test_ads_campaign_creator_agent.py AIM/tests/unit/test_ads_magister.py -x`
- **Per wave merge:** `pytest AIM/tests/ -x --timeout=60`
- **Phase gate:** Full suite green before `/gsd-verify-work`

## Wave 0 Gaps (8 tests — must be created before implementation)

- [ ] `AIM/tests/unit/test_ab_middleware.py` — LAND-04 variant serving (cookie assignment, sticky sessions, 50/50 split)
- [ ] `AIM/tests/unit/test_ab_test_engine.py` — LAND-04 A/B statistical analysis
- [ ] `AIM/tests/unit/test_yandex_direct_stats.py` — MKTG-01 real stats (fixes MOCK)
- [ ] `AIM/tests/unit/test_vk_ads_client.py` — MKTG-01 VK Ads integration
- [ ] `AIM/tests/unit/test_roi_calculator.py` — MKTG-03 ROI calculation
- [ ] `AIM/tests/integration/test_attribution_pipeline.py` — MKTG-02 attribution
- [ ] `AIM/tests/conftest.py` — add fixtures: yandex_direct_token, vk_ads_token, sample_campaign, sample_lead_with_utm
