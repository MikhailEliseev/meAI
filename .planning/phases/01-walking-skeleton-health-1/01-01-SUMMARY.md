# Phase 1: Walking Skeleton — Summary

**Phase:** 01-walking-skeleton-health-1
**Plan:** 01-01
**Completed:** 2026-07-14
**Status:** ✅ COMPLETE — all must_haves truths proven by measurement

---

## Что сделано

Новый контейнер `aim-hermes-v2` поднят на проде и доказал end-to-end работоспособность: FastAPI с `/health` и одним тулом `find_competitors` (прозрачный HTTP-прокси к `aim-app:8000`), упакованный в компактный Docker-образ (247 MB).

Walking Skeleton доказывает, что вся инфраструктура (docker network, env, связность с aim-app) работает. Старый контейнер `aim-hermes` не тронут — страховка отката на месте.

---

## Доказательства (evidence, measured)

### Контейнер жив
- `aim-hermes-v2` создан `2026-07-14T16:39:30Z`, статус **healthy** (за 15с после up).
- Образ `aim-hermes-v2:latest` — 247 MB (компактный, без playwright/heavy deps).

### /health (INFRA-03)
```
GET localhost:8000/health → {"status":"ok","service":"hermes-v2"}
```

### find_competitors — РЕАЛЬНЫЕ данные (INFRA-04, TOLS-02)
```
POST /tools/find-competitors {"url":"https://stomus.ru","count":3}
→ competitors: 3
  - Клиника 57 ГРАНЕЙ   | rating: 4.9 | reviews: 91
  - Хорошая стоматология | rating: 4.8 | reviews: 50
  - Credus              | rating: 5.0 | reviews: 118
```
Это прозрачный passthrough ответа `aim-app:8000/api/competitors/find` (через Apify Google Maps). Прокси не трансформирует данные.

### Связность в docker-сети (INFRA-05)
Логи `aim-hermes-v2` содержат 4 записи:
```
httpx: HTTP Request: POST http://aim-app:8000/api/competitors/find "HTTP/1.1 200 OK"
```
Доказывает: `AIM_API_BASE=http://aim-app:8000` корректно резолвится в docker network `aim-network`.

### Старый сервис не тронут (rollback safety)
- `aim-hermes` → Health.Status = **healthy**
- `aim-app` → Health.Status = **healthy**
- `docker compose config --services` парсит все 14 сервисов без ошибок.

### Диск (INFRA-02 context)
- До/после build: 14G свободно (80% занят) — образ поместился, тяжёлых deps нет.

---

## Артефакты

| Файл | Назначение |
|---|---|
| `AIM/hermes-v2/app/main.py` | FastAPI: `GET /health`, `POST /tools/find-competitors` |
| `AIM/hermes-v2/app/config.py` | env-чтение (AIM_API_BASE + заготовки Phase 2-5) |
| `AIM/hermes-v2/app/tools/competitors.py` | `async find_competitors(url, count=3)` — httpx-прокси к aim-app |
| `AIM/hermes-v2/requirements.txt` | fastapi, uvicorn, httpx==0.28.1 (минимум) |
| `AIM/hermes-v2/Dockerfile` | python:3.11-slim + curl + HEALTHCHECK |
| `AIM/hermes-v2/tests/test_competitors.py` | 3 unit-теста прокси (URL/payload, passthrough, error-as-dict) |
| `AIM/docker-compose.yml` | добавлен сервис `hermes-v2` (additively, после `hermes:`, перед `frontend:`) |

На сервере: `/opt/aim/AIM/hermes-v2/` (rsync), `/opt/aim/AIM/docker-compose.yml` (вставлен блок), backup `docker-compose.yml.bak-20260714-193757`.

---

## Покрытые требования

| ID | Требование | Покрытие |
|---|---|---|
| INFRA-01 | Новый Docker-сервис hermes-v2 | ✅ в compose |
| INFRA-02 | Dockerfile + базовые deps | ✅ частично (Python 3.11-slim + fastapi/uvicorn/httpx; тяжёлые deps — Phase 3) |
| INFRA-03 | /health endpoint | ✅ 200 + status:ok |
| INFRA-04 | find_competitors реальный HTTP к aim-app | ✅ 3 конкурента |
| INFRA-05 | env AIM_API_BASE + docker network | ✅ резолвится |
| TOLS-02 | find_competitors thin-wrapper | ✅ transparent proxy |

---

## Замечания / нюансы (для следующих фаз)

1. **gmtdclinic.ru возвращает 0 конкурентов** — это ответ upstream aim-app (`is_megalopolis: false`), не баг прокси. `stomus.ru` работает. В Phase 4 надо учитывать, что не все URL дают конкурентов — нужен fallback-текст в базе.
2. **find_competitors медленный** (~60-90с на stomus.ru через Apify). Phase 4 цель «база ≤4 мин» — выполнима (quick_overview + find_competitors параллельно).
3. **Server compose ≠ local compose** (OMNIROUTE_URL и др. расходятся). Деплой делал additively — не перезаписывал. Этот паттерн сохранить для Phase 6.

---

## Rollback план

Если v2 надо откатить (контейнер проблемный):

```bash
ssh aim "cd /opt/aim/AIM && docker compose stop hermes-v2 && docker compose rm -f hermes-v2"
# восстановить compose из backup:
ssh aim "cp /opt/aim/AIM/docker-compose.yml.bak-20260714-193757 /opt/aim/AIM/docker-compose.yml"
# удалить код (опционально):
ssh aim "rm -rf /opt/aim/AIM/hermes-v2"
# старый aim-hermes НЕ затронут — продолжает работать
```

nginx НЕ переключался (Phase 6) — клиенты v2 не видят. Полный откат занимает <2 минуты.

---

## Что дальше (Phase 2)

Диалоговый сервер: `POST /api/chat/stream` (SSE) + deepseek-chat через Z.AI + системный промпт + SQLite-сессии. Контейнер начинает «разговаривать». Фундамент (образ, сеть, health, прокси-паттерн) готов — Phase 2 надстраивается без пересмотра решений Phase 1.

---

*Phase 01 — Plan 01-01 — COMPLETE*
