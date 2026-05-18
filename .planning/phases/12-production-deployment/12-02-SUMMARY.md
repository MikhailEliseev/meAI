# Plan 12-02: Контур.Диадок + PostgreSQL — Execution Summary

**Phase:** 12 Production Deployment
**Plan:** 02 of 03
**Completed:** 2026-05-18
**Status:** COMPLETE

## Tasks Completed

### Task 1: KontourAuth + KontourPoller
- `AIM/src/aim/services/contracts/kontour_auth.py` — OIDC Device Authorization Flow
  - Device flow: `/connect/deviceauthorization` → `/connect/token`
  - Auto-refresh via `refresh_token` (1h access, 24h refresh)
  - Scopes: `openid profile email offline_access Diadoc.PublicAPI`
- `AIM/src/aim/services/contracts/kontour_poller.py` — GetNewEvents (V8) polling
  - 30s active poll interval, 5min idle backoff
  - `on_event()` decorator for handler registration
  - Cursor-based polling via `afterIndexKey`
- `AIM/src/aim/services/contracts/__init__.py` — updated exports

### Task 2: KontourClient Real API Calls
- `AIM/src/aim/services/contracts/kontour_client.py` — fully rewritten
  - 0 STUB references (verified — grep returns 0)
  - Constructor: `client_id`, `client_secret`, `organization_inn`
  - Integrates KontourAuth for OIDC token lifecycle
  - Real httpx API calls: GetMyOrganizations, PostMessage, GetDocument, GetEntityContent, GetSignatureInfo, CancelSignatureRequest, ResendNotification, GetOrganizationsByInnKpp
  - `_get_box_id()` lazy init with INN lookup
  - KontourWebhookHandler marked DEPRECATED (polling, not webhooks)
  - `verify_webhook_signature()` kept for backward compat
  - `get_signature_type_for_amount()` preserved

### Task 3: DocuSignClient Deleted
- `AIM/src/aim/services/onboarding/docusign_client.py` — DELETED
- 0 DocuSign references remaining in `AIM/src/aim/` (verified)
- `workflow.py` updated: `docusign_client` → `kontour_client`, `self.docusign` → `self.kontour`
- `_send_baa()` uses `KontourClient.send_for_signature()` with signature type by amount
- `_initiate_payment()` updated: Helcim → ЮKassa, USD → RUB

### Task 4: PostgreSQL Migration + Alembic
- `database.py` — `DATABASE_URL` from env with SQLite fallback, pool config (20/10/pre_ping/recycle)
- `docker-compose.yml` — postgres:16-alpine with healthcheck, resource limits (2CPU/2GB), ru_RU.UTF-8 locale
- `alembic/env.py` — async_engine_from_config pattern, all models imported for autogenerate
- `alembic.ini` — postgresql+asyncpg URL
- `main.py` — lifespan for auto-migration (AUTO_MIGRATE=true)
- `scripts/migrate_sqlite_to_pg.py` — batch migration script
- `.env.example` — POSTGRES_*, KONTOUR_*, AUTO_MIGRATE vars
- `requirements.txt` — asyncpg>=0.29.0

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `AIM/src/aim/services/contracts/kontour_auth.py` | CREATED | ~120 |
| `AIM/src/aim/services/contracts/kontour_poller.py` | CREATED | ~110 |
| `AIM/src/aim/services/contracts/kontour_client.py` | REWRITTEN | ~280 |
| `AIM/src/aim/services/contracts/__init__.py` | UPDATED | +6 |
| `AIM/src/aim/services/onboarding/docusign_client.py` | DELETED | -504 |
| `AIM/src/aim/services/onboarding/workflow.py` | UPDATED | +10/-8 |
| `AIM/src/aim/database.py` | UPDATED | +12/-5 |
| `AIM/docker-compose.yml` | UPDATED | +31 |
| `AIM/alembic/alembic.ini` | UPDATED | 1 line |
| `AIM/alembic/env.py` | UPDATED | +10 |
| `AIM/src/aim/main.py` | UPDATED | +14 |
| `AIM/.env.example` | UPDATED | +22 |
| `AIM/requirements.txt` | UPDATED | +1 |
| `scripts/migrate_sqlite_to_pg.py` | CREATED | ~120 |

## Verification

All checks passed:
- Zero STUB references in kontour_client.py
- Zero DocuSign references in AIM/src/aim/
- All Python files compile without errors
- Docker Compose has postgres with healthcheck
- Alembic uses async_engine_from_config pattern
- All env vars documented in .env.example
