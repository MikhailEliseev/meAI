# Phase 1: Walking Skeleton — Context

**Gathered:** 2026-07-14
**Status:** Ready for planning
**Source:** Brainstorming session + spec `docs/superpowers/specs/2026-07-14-hermes-interactive-redesign-design.md`

<domain>
## Phase Boundary

Минимальный end-to-end рабочий срез нового контейнера `aim-hermes-v2`. Цель фазы — доказать, что инфраструктура работает, а не построить весь Гермес.

**Что входит в Phase 1:**
- Новый Docker-сервис `hermes-v2` в `docker-compose.yml`
- `Dockerfile` + минимальное FastAPI-приложение с `/health`
- ОДИН рабочий тул: `find_competitors` — thin-wrapper (HTTP-прокси) к `aim-app:8000/api/competitors/find`
- Эндпоинт `/tools/find-competitors` для ручной проверки (не chat, просто HTTP)
- Env-переменные и доступ к docker-сети

**Что НЕ входит в Phase 1 (явно):**
- Диалог/чат/LLM (Phase 2)
- Перенос остальных 9 тулов (Phase 3)
- Кнопки, suggestions, отчёты (Phase 4-5)
- Деплой на прод (Phase 6)
- Telegram-бот (out of scope вообще)

</domain>

<decisions>
## Implementation Decisions (locked)

### Структура кода
- Новый каталог: `AIM/hermes-v2/` (рядом с существующим `AIM/hermes/`, НЕ внутри)
- Python 3.11, FastAPI, httpx (без heavyweight зависимостей на этой фазе)
- Структура: `app/main.py` (FastAPI + endpoints), `app/tools/competitors.py` (find_competitors), `app/config.py` (env reading)

### Docker
- Сервис `hermes-v2` в `/opt/aim/AIM/docker-compose.yml` (на проде) — копия структуры существующего `hermes` сервиса с адаптацией
- Образ `aim-hermes-v2:latest`, контейнер `aim-hermes-v2`
- `expose: ["8000"]`, сеть `aim-network`, `depends_on: app (healthy)` + НЕ зависит от redis (redis нужен Phase 2 для сессий)
- Healthcheck: `curl -f http://localhost:8000/health`, interval 30s
- Volume `/opt/hermes-v2-data:/opt/data` (отдельный от старого hermes-data)

### find_competitors — thin wrapper
- Endpoint: `POST /tools/find-competitors` с body `{url: str, count: int = 3}`
- Handler делает `httpx.post(f"{AIM_API_BASE}/api/competitors/find", json={"url": url, "count": 3})` где `AIM_API_BASE=http://aim-app:8000`
- Возвращает JSON-ответ aim-app как есть (прозрачный прокси)
- На этой фазе НЕТ tool-calling/LLM — просто HTTP-прокси для проверки связности

### Env (минимум для Phase 1)
- `AIM_API_BASE=http://aim-app:8000` — единственный обязательный для Phase 1
- Остальные (OMNIROUTE_URL, PERPLEXITY_API_KEY, etc.) добавятся в Phase 2-3, но их можно уже заложить в `config.py` со значениями по умолчанию/empty

### Путь к тестированию
- Локально: `docker compose up -d hermes-v2` → `curl localhost:8000/health` (если порт проброшен) или `docker exec aim-hermes-v2 curl localhost:8000/health`
- Ручная проверка find_competitors: `curl -X POST localhost:8000/tools/find-competitors -H 'Content-Type: application/json' -d '{"url":"https://stomatology-example.ru"}'`

### Развёртывание
- Локально в `~/Desktop/Dev/meAI_1/AIM/hermes-v2/`
- `rsync` на сервер в `/opt/aim/AIM/hermes-v2/`
- `docker compose build hermes-v2 && docker compose up -d hermes-v2` (на сервере)
- На Phase 1 НЕ трогаем nginx — v2 недоступен извне, только из docker-сети

### Claude's Discretion
- Конкретные зависимости в requirements.txt (версии httpx, fastapi, uvicorn)
- Структура Dockerfile (multi-stage vs простой)
- Формат healthcheck-ответа ({"status": "ok"} vs более детальный)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Спека и контекст
- `docs/superpowers/specs/2026-07-14-hermes-interactive-redesign-design.md` — полная дизайн-спека (разделы 4.2, 4.4 — состав контейнера и docker-compose)
- `.planning/PROJECT.md` — контекст проекта
- `.planning/REQUIREMENTS.md` — все требования (Phase 1 покрывает INFRA-01..05, TOLS-02)

### Существующий код (для копирования паттернов)
- Бэкап старого hermes: `~/Desktop/Dev/meAI_1-backups/extracted/aim-chat-system-20260714-133205/hermes-container-code/`
  - `app/tools/find_competitors.py:293` — РЕАЛЬНЫЙ пример HTTP-вызова к `aim-app:8000/api/competitors/find` (паттерн для thin-wrapper)
  - `config.yaml`, `requirements.txt` — зависимости и конфиг старого hermes (референс)
- На сервере: `ssh aim` → `/opt/aim/AIM/docker-compose.yml` — РЕАЛЬНЫЙ docker-compose (текущий сервис `hermes:` как шаблон для `hermes-v2:`)
- На сервере: `/opt/aim/AIM/hermes/Dockerfile` — референс Dockerfile

### aim-app endpoint (живой)
- `POST http://aim-app:8000/api/competitors/find` с body `{"url": "...", "count": 3}` — возвращает `{competitors: [{brand_name, website, rating, reviews_count, match_reason, ...}]}`. Это endpoint, который наш thin-wrapper будет проксировать.

</canonical_refs>

<specifics>
## Specific Ideas

- Контейнер должен быть максимально тонким на Phase 1 — никаких лишних зависимостей. Цель: доказать работоспособность инфраструктуры за минимальное время.
- `find_competitors` уже возвращает `match_reason` (однострочник «почему конкурент») — это поле важно для базы в Phase 4.
- Старый сервис `hermes` в docker-compose НЕ трогаем и НЕ удаляем — он остаётся работать.
- Сервер: диск 80% занят (14G свободно) — новый образ должен быть компактным (без playwright и тяжёлых deps на Phase 1).

</specifics>

<deferred>
## Deferred Ideas (не в Phase 1)

- LLM/dialogue (Phase 2)
- Остальные 9 тулов (Phase 3)
- Кнопки suggestions в SSE (Phase 4)
- Сборка HTML-отчёта (Phase 5)
- Деплой/переключение nginx (Phase 6)
- Telegram-бот (out of scope)

</deferred>

---

*Phase: 01-walking-skeleton-health-1*
*Context gathered: 2026-07-14*
