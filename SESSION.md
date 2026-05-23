# Session: 2026-05-23

## Phase 19: Competitor Discovery Quality — COMPLETED ✅

**Date:** 2026-05-23 15:30 GMT+3
**Status:** Все 7 задач выполнены, 63 теста проходят

### Результаты
- ✅ C1: Specialization detection → dominance-based (вместо first-match-wins)
- ✅ C3: Service detection → negation filter (исключает «противопоказания к имплантации»)
- ✅ S3: City detection → JSON-LD/schema.org + убрано ограничение [:5000]
- ✅ S1/S2/M1: Веса перебалансированы + чистый Jaccard (TF-IDF удалён)
- ✅ S4: named_competitors в API + Hermes tool
- ✅ Проверено: 63 теста (26 service_extractor + 37 competitor_matcher_scoring)

### Ключевые файлы
- `AIM/src/aim/services/service_extractor.py` — C1, C3, S3
- `AIM/src/aim/services/competitor_matcher.py` — S1, S2, M1, S4
- `AIM/src/aim/api/competitors.py` — S4 (API)
- `AIM/hermes/app/tools/find_competitors.py` — S4 (Hermes)
- `AIM/tests/services/test_service_extractor.py` — 26 tests
- `AIM/tests/services/test_competitor_matcher_scoring.py` — 37 tests

### Next
- Push на сервер + integration test
- Google Places API key — требуется проверка

---

## PRODUCTION DEPLOYED 🚀

**Date:** 2026-05-19 14:20 GMT+3
**Server:** 138.16.224.188
**Domain:** https://iamaim.ru

### Deployed Services (all healthy):
- ✅ aim-app (FastAPI backend)
- ✅ aim-frontend (Next.js 14 — 21 pages)
- ✅ aim-hermes (Hermes AIAgent operator)
- ✅ aim-postgres (PostgreSQL 16)
- ✅ aim-redis (Redis 7)
- ✅ aim-nginx (SSL via Let's Encrypt)
- ✅ aim-prometheus + grafana + alertmanager + postgres-exporter + node-exporter

### Pending:
- ⚠️ Telegram webhook — Telegram DNS ещё не видит iamaim.ru
- ⚠️ TELEGRAM_API_ID + TELEGRAM_API_HASH
- ⚠️ Alertmanager Telegram chat_id + SendGrid API key
- ⚠️ POSTGRES_PASSWORD warning в docker-compose — косметическое
