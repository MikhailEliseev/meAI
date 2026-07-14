# Walking Skeleton — Гермес v2

**Phase:** 1
**Generated:** 2026-07-14

## Capability Proven End-to-End

Из docker-сети `aim-network` можно выполнить `POST http://aim-hermes-v2:8000/tools/find-competitors` с URL клиники и получить реальный JSON-ответ с конкурентами (brand_name, rating), который новый контейнер прозрачно проксирует от `aim-app:8000/api/competitors/find`. Это доказывает, что весь стек — образ, docker network, env, связность с aim-app — работает.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastAPI + Uvicorn (ASGI) | Совместимость с Theme-чатом (SSE в Phase 2), паттерн уже работает в старом `aim-hermes` |
| Runtime | Python 3.11-slim (Docker) | Совпадает с прод-образом старого hermes (`/opt/aim/AIM/hermes/Dockerfile`), единая база |
| HTTP client | httpx 0.28.1 (async) | Та же версия, что в старом hermes; async-прокси к aim-app |
| Data layer | Нет на Phase 1 (SQLite добавляется в Phase 2 для сессий) | Walking Skeleton не требует персистентности — доказываем связность, не хранение |
| Auth | Нет на Phase 1 | Контейнер доступен только из docker-сети (не проброшен наружу, nginx не трогаем) |
| Deployment target | Docker-сервис `hermes-v2` в `/opt/aim/AIM/docker-compose.yml` на сервере `ssh aim` | Рядом со старым `hermes:`, тот же compose, та же сеть aim-network |
| Directory layout | `AIM/hermes-v2/app/{main.py,config.py,tools/competitors.py}` | Рядом с `AIM/hermes/`, НЕ внутри; чистый отдельный контейнер (подход A) |
| Tool calling | НЕТ на Phase 1 (просто HTTP-прокси) | LLM/tool-calling переносится в Phase 2; Phase 1 = инфраструктурное доказательство |

## Stack Touched in Phase 1

- [x] Project scaffold (FastAPI app, requirements.txt, Dockerfile) — минимальный, без тяжёлых зависимостей
- [x] Routing — два реальных маршрута: `GET /health`, `POST /tools/find-competitors`
- [ ] Database — НЕТ на Phase 1 (отложено в Phase 2: SQLite для сессий)
- [ ] UI — НЕТ на Phase 1 (чат-фронтенд в Phase 4-5)
- [x] Deployment — контейнер поднимается на прод-сервере в docker-сети; полный end-to-end run задокументирован (rsync → build → up → curl)

## Out of Scope (Deferred to Later Slices)

- LLM / диалог / SSE-стриминг (Phase 2)
- SQLite хранилище сессий (Phase 2)
- Перенос остальных 9 тулов — 7 толстых + 2 прокси (Phase 3)
- Tool-calling / OpenAI function-schema (Phase 2-3)
- Кнопки suggestions в SSE (Phase 4)
- Сборка HTML-отчёта (Phase 5)
- Деплой/переключение nginx — контейнер НЕ доступен извне до Phase 6 (Phase 1: только docker-сеть)
- Telegram-бот (out of scope вообще)
- Удаление/переименование старого `hermes:` сервиса (оставляем как есть для отката)

## Subsequent Slice Plan

Каждая следующая фаза надстраивает один вертикальный срез поверх этого скелета, не меняя архитектурных решений Phase 1:

- **Phase 2:** Диалоговый сервер — `POST /api/chat/stream` (SSE) + deepseek-chat через Z.AI + системный промпт + SQLite-сессии. Контейнер начинает «разговаривать».
- **Phase 3:** Перенос всех 10 тулов — 7 толстых модулей из бэкапа + 2 оставшихся прокси; tool-calling schema. Модель может вызывать инструменты.
- **Phase 4:** Базовый сценарий — URL → quick_overview + find_competitors → рынок + top-3 за ≤4 мин, кнопки suggestions.
- **Phase 5:** Кнопки в Theme-чате + сборка HTML-отчёта из session_archive.
- **Phase 6:** Деплой на прод — переключение nginx с `aim-hermes:8000` на `aim-hermes-v2:8000`, старый контейнер выключен но готов к откату.

## Key Facts Established (не пересматривать в следующих фазах)

- Сервис называется `hermes-v2` (образ `aim-hermes-v2:latest`, контейнер `aim-hermes-v2`)
- Volume данных: `/opt/hermes-v2-data:/opt/data` (ОТДЕЛЬНЫЙ от старого `/opt/hermes-data`)
- `AIM_API_BASE=http://aim-app:8000` — единственный обязательный env на Phase 1
- Контейнер НЕ зависит от redis на Phase 1 (redis понадобится в Phase 2)
- Healthcheck: `curl -f http://localhost:8000/health`, interval 30s (curl должен быть в образе)
- find_competitors — прозрачный прокси: возвращает JSON aim-app как есть, без трансформации
