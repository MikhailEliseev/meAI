# Phase 15: Hermes AIM Integration — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 15-Hermes AIM Integration
**Areas discussed:** Deployment, Chat-proxy, Tools, Telegram, Skill Auto-improvement, Security & Access, Monitoring & Alerting, Error Handling & Resilience

---

## Deployment

| Option | Description | Selected |
|--------|-------------|----------|
| Docker-контейнер в docker-compose | Контейнер в существующем стеке, единое управление | ✓ |
| Отдельный VPS | Изолированный сервер для Hermes | |
| systemd на основном сервере | Установка как системного сервиса | |

**Notes:** Свой Dockerfile на Python 3.11, skills в AIM/hermes/, MCP server режим, Anthropic через OmniRoute proxy, Docker volume для данных, внутренний порт, Docker restart policy.

## Chat-proxy

| Option | Description | Selected |
|--------|-------------|----------|
| FastAPI HTTP wrapper | Тонкая прослойка в Hermes для HTTP-коммуникации с Next.js | ✓ |
| MCP напрямую | Next.js подключается к MCP (stdio/SSE) | |
| WebSocket | Постоянное соединение | |

**Notes:** Hermes — единственный LLM-шлюз, DeepSeek удаляется полностью, OPERATOR_PROMPT → SOUL.md.

## Tools

| Option | Description | Selected |
|--------|-------------|----------|
| HTTP API между контейнерами | Hermes MCP tools вызывают AIM API по HTTP | ✓ |
| Прямые Python вызовы | Импорт AIM модулей в Hermes | |
| Event Bus | Асинхронная очередь событий | |

**Notes:** 6 инструментов как MCP tools, реальные вызовы AIM API (не stubs).

## Telegram

| Option | Description | Selected |
|--------|-------------|----------|
| Bot API + Telethon | Bot для входящих, user-client для исходящих/поиска | ✓ |
| Только Bot API | Только приём сообщений через бота | |
| Только Telethon | Полноценный user-client | |

**Notes:** Единый чат (один Operator), tg://deep link для привязки сессии, Telethon как MCP tools.

## Skill Auto-improvement

| Option | Description | Selected |
|--------|-------------|----------|
| Ответы на частые вопросы | Оптимизация ответов для повышения конверсии | ✓ |
| Технические знания | Улучшение знаний о медицинском маркетинге | |
| Стиль общения | Адаптация tone of voice | |

**Notes:** Conversion rate как метрика, автоматическое создание skills, порог 5 повторений, единая директория хранения.

## Security & Access

| Option | Description | Selected |
|--------|-------------|----------|
| API ключ (Bearer token) | Статичный ключ в .env, заголовок Authorization | ✓ |
| JWT токен | Подписанный токен с контекстом | |
| Без аутентификации | Доверие внутри Docker-сети | |

**Notes:** Next.js определяет режим (PRESALE/ACTIVE/ADMIN) и передаёт в заголовке, ADMIN защищён проверкой NextAuth role=admin.

## Monitoring & Alerting

| Option | Description | Selected |
|--------|-------------|----------|
| Health endpoint | /health в FastAPI, Prometheus скрапит | ✓ |
| Push в Prometheus | Hermes активно пушит метрики | |
| Docker healthcheck | Встроенный механизм Docker | |

**Notes:** RED метрики (Rate, Errors, Duration), алерты только на downtime (60s+), доставка в Telegram + Email.

## Error Handling & Resilience

| Option | Description | Selected |
|--------|-------------|----------|
| Очередь с retry | Redis очередь, 3 попытки с экспоненциальной задержкой | ✓ |
| Graceful degradation | "Operator temporarily unavailable" | |
| Fallback LLM провайдер | Запасной провайдер через OmniRoute (уже есть) | |

**Notes:** OmniRoute обеспечивает LLM fallback на своей стороне. Таймаут 30s, retry 5s/15s/45s, после исчерпания — сохранение в БД + уведомление клиента.

## Deferred Ideas

- LLM-специфичные метрики (токены, стоимость) — позже в Grafana
- Бизнес-метрики чата — отдельная аналитика
- Авторотация API ключей — избыточно для внутренней сети
- Circuit breaker для AIM API — при росте нагрузки
