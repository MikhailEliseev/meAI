# Phase 15: Hermes AIM Integration — Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

## Phase Boundary

Интеграция Hermes Agent (v0.14.0, Nous Research) как фундамента для Operator-системы AIM. Hermes становится единым AI-интерфейсом агентства: принимает чаты с сайта и Telegram, вызывает Magisters через MCP-инструменты, самообучается на успешных диалогах.

## Implementation Decisions

### Deployment
- **D-01:** Docker-контейнер в существующем docker-compose.yml (рядом с app, redis, nginx, prometheus, grafana, postgres)
- **D-02:** Свой Dockerfile на основе Python 3.11 (не готовый образ Hermes)
- **D-03:** Skills хранятся в репозитории `AIM/hermes/skills/`, копируются в образ через `COPY` при сборке
- **D-04:** Hermes запускается в режиме MCP server
- **D-05:** LLM-провайдер: Anthropic (Claude) через OmniRoute proxy (193.111.152.14:7451, HTTP, login: U9pjtK, password: hxtlqz)
- **D-06:** Данные Hermes: Docker volume (persistent)
- **D-07:** Порт: только внутренняя Docker-сеть, не exposed наружу
- **D-08:** Docker restart policy (`unless-stopped`) заменяет systemd
- **D-09:** OmniRoute обеспечивает fallback между LLM-провайдерами на своей стороне

### Chat-proxy (Next.js ↔ Hermes)
- **D-10:** FastAPI HTTP wrapper внутри Hermes-контейнера для связи с Next.js (MCP работает через stdio/SSE, не подходит для Next.js)
- **D-11:** Hermes — единственный LLM-шлюз. DeepSeek полностью убирается из `route.ts`
- **D-12:** OPERATOR_PROMPT (3 режима: PRESALE/ACTIVE/ADMIN) переносится из `route.ts` в SOUL.md как Hermes skill

### Tools (Hermes MCP tools → AIM API)
- **D-13:** 6 кастомных инструментов (run_seo_audit, run_content_analysis, run_ads_report, show_project_status, collect_contact, show_all_leads) определены как MCP tools в Hermes-контейнере
- **D-14:** Инструменты вызывают AIM API через HTTP между Docker-контейнерами (внутренняя сеть)
- **D-15:** Реальные вызовы AIM API endpoints, без stubs

### Telegram Gateway
- **D-16:** Гибридная архитектура: Bot API (webhook, входящие сообщения от клиентов) + Telethon user-client (исходящие, поиск по каналам, мониторинг)
- **D-17:** Единый чат — один Operator обслуживает и веб, и Telegram
- **D-18:** Привязка сессии: tg://deep link с сайта (клиент жмёт кнопку в веб-чате → переходит в Telegram → бот знает кто это)
- **D-19:** Telethon интегрирован как MCP tools в Hermes (поиск по чатам, чтение каналов, отправка сообщений как пользователь)

### Skill Auto-improvement
- **D-20:** Фокус авто-улучшения: оптимизация ответов на частые вопросы (повышение конверсии)
- **D-21:** Измерение улучшения: conversion rate (% лидов → onboarding/оплата)
- **D-22:** Создание skills: полностью автоматическое (Hermes решает сам)
- **D-23:** Порог: 5 успешных повторений паттерна → создаётся skill
- **D-24:** Авто-генерируемые skills хранятся в той же директории `AIM/hermes/skills/aim/` что и ручные

### Security & Access
- **D-25:** Аутентификация: Bearer API ключ в заголовке `Authorization`. Next.js передаёт, Hermes проверяет.
- **D-26:** Разграничение режимов: Next.js определяет режим (PRESALE/ACTIVE/ADMIN) по статусу клиента в БД и передаёт в заголовке. Hermes доверяет.
- **D-27:** Управление ключом: статичный `HERMES_API_KEY` в `.env`, генерируется один раз
- **D-28:** Защита ADMIN: проверка `role=admin` в Next.js (NextAuth). Hermes не обслуживает ADMIN-запросы от веб-чата без этой проверки.

### Monitoring & Alerting
- **D-29:** Health check: `/health` endpoint в FastAPI wrapper, возвращает статус Hermes + LLM-провайдера. Prometheus скрапит.
- **D-30:** Метрики: стандартные RED (Rate, Errors, Duration) — request count, error rate, latency p50/p95/p99
- **D-31:** Алерты: только downtime (Hermes недоступен 60+ секунд)
- **D-32:** Доставка алертов: Telegram + Email через Alertmanager

### Error Handling & Resilience
- **D-33:** При недоступности Hermes: сообщение уходит в Redis-очередь. Next.js прозрачно ставит в очередь и ждёт.
- **D-34:** Таймаут: 30 секунд ожидания ответа от Hermes, затем сообщение → очередь
- **D-35:** Retry-стратегия: 3 попытки с экспоненциальной задержкой (5s, 15s, 45s)
- **D-36:** После исчерпания retry: сообщение сохраняется в БД, клиенту показывается "Оператор скоро ответит". При восстановлении Hermes — доставка.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Hermes Agent
- `AIM/hermes/skills/aim/SOUL.md` — Operator identity, 3 режима, знания агентства (будет дополнен)
- Hermes v0.14.0 source: `/Users/mikhaileliseev/temp/research-repos/hermes-agent/` (reference only)

### AIM Frontend (точки интеграции)
- `AIM/frontend/app/api/chat/send/route.ts` — Текущий чат-роут (будет заменён на прокси к Hermes)
- `AIM/frontend/app/(dashboard)/onboarding/page.tsx` — Onboarding flow
- `AIM/frontend/app/(dashboard)/contracts/page.tsx` — Contracts page

### Инфраструктура
- `AIM/docker-compose.yml` — Текущий стек (app, redis, nginx, prometheus, grafana, postgres)
- `.planning/phases/12-production-deployment/12-CONTEXT.md` — Production-контекст (сервер 138.16.224.188, Nginx TLS, ФЗ-152)
- `AIM/deploy/monitoring/prometheus.yml` — Prometheus конфигурация
- `AIM/deploy/monitoring/alertmanager.yml` — Alertmanager конфигурация

### Roadmap
- `.planning/ROADMAP.md` §Phase 15 — Success criteria (7 пунктов)

## Existing Code Insights

### Reusable Assets
- **Redis в docker-compose:** Уже есть в стеке — можно использовать для очереди сообщений (D-33)
- **Prometheus + Grafana:** Уже настроены — добавить Hermes как новый target (D-29)
- **Alertmanager:** Уже настроен — добавить правило downtime для Hermes (D-31, D-32)
- **Nginx:** TLS-терминатор — не требует изменений (Hermes не exposed наружу)

### Integration Points
- `AIM/frontend/app/api/chat/send/route.ts` → заменить прямые вызовы DeepSeek на прокси к Hermes FastAPI wrapper
- `AIM/docker-compose.yml` → добавить сервис `hermes` с внутренней сетью
- `AIM/deploy/monitoring/prometheus.yml` → добавить `hermes:8000` в scrape targets
- `AIM/frontend/.env` → добавить `HERMES_API_KEY` и `HERMES_URL=http://hermes:8000`

### Established Patterns
- Все сервисы в docker-compose общаются через внутреннюю Docker-сеть
- Nginx — единственная точка входа извне
- Prometheus скрапит `/metrics` и `/health` endpoints
- ФЗ-152 compliance уже верифицирован в Phase 12

## Deferred Ideas

- **LLM-специфичные метрики** (токены, стоимость) — можно добавить позже в Grafana
- **Бизнес-метрики чата** (конверсия, длительность сессии) — отдельная аналитическая задача
- **Автоматическая ротация API ключей** — избыточно для внутренней Docker-сети
- **Circuit breaker для AIM API** — можно добавить при росте нагрузки

---

*Phase: 15-Hermes AIM Integration*
*Context gathered: 2026-05-19*
