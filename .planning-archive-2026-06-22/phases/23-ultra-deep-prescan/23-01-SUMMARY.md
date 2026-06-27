# 23-01 SUMMARY — Database Layer

**Plan:** 23-01 — CompanyProfile model + Pydantic schemas + REST API
**Status:** COMPLETED
**Date:** 2026-06-03

## Completed Tasks

### Task 1: SQLAlchemy Model + Pydantic Schemas ✅
- `AIM/src/aim/models/company_profile.py` — CompanyProfileModel, composite unique key (url, inn), JSON profile_data
- `AIM/src/aim/schemas/company_profile.py` — CompanyProfileCreate, CompanyProfileResponse, CompanyProfileFound, CompanyProfileNotFound
- `AIM/src/aim/models/__init__.py` — added CompanyProfileModel to imports + __all__
- `AIM/src/aim/database.py` — registered in _import_models()
- `AIM/tests/conftest.py` — registered for test DB table creation

### Task 2: REST API Endpoints + Tests ✅
- `AIM/src/aim/api/company_profiles.py` — GET /by-url, POST /upsert
- `AIM/src/aim/main.py` — router registered
- `AIM/tests/api/test_company_profiles.py` — 10 integration tests, all passing

### Bonus: Fixed pre-existing test infrastructure bug
- `AIM/src/aim/models/sales.py` — `JSONB` → `JSON` (PostgreSQL-specific type broke SQLite tests)

## Test Results
```
10 passed in 0.34s
```

## Changes Summary
| File | Action | Lines |
|------|--------|-------|
| AIM/src/aim/models/company_profile.py | NEW | 50 |
| AIM/src/aim/schemas/company_profile.py | NEW | 41 |
| AIM/src/aim/api/company_profiles.py | NEW | 129 |
| AIM/tests/api/test_company_profiles.py | NEW | 157 |
| AIM/src/aim/models/__init__.py | MODIFIED | +1 line (CompanyProfileModel) |
| AIM/src/aim/database.py | MODIFIED | +1 line (_import_models) |
| AIM/src/aim/main.py | MODIFIED | +2 lines (import + include_router) |
| AIM/tests/conftest.py | MODIFIED | +1 line (model registration) |
| AIM/src/aim/models/sales.py | MODIFIED | JSONB→JSON fix |

## Next: Plan 23-02 — Staged Pipeline (PrescanOrchestrator)
