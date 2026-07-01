# 01 — Executive Summary

**AIM (iamaim.ru)** — AI-first marketing agency для медицинских клиник. LLM-агент Hermes общается с клиентами, проводит разведку сайтов конкурентов, формирует отчёты пресейла и собирает лиды.

---

## Что проект из себя представляет

**Одно ключевое действие пользователя:** клиент пишет в чат на iamaim.ru → Hermes вызывает инструменты (prescan, find_competitors, ci_analysis, seo_audit) → формирует отчёт → собирает контакт.

**Архитектура:**
```
Клиент → iamaim.ru (Nginx)
       → WordPress (PHP, лендинг + чат-интерфейс)
       → Hermes FastAPI (Python, port 8000)
       → hermes-agent library (LLM orchestrator)
       → 67 tools → AIM app (FastAPI, port 8000)
                  → PostgreSQL, Redis, внешние API
```

**16 Docker-контейнеров**, ~13 GB образов, 24 GB занято на диске (из 69 GB).

---

## Текущее состояние (одной строкой)

**Чат-продукт Hermes работает (46 запросов за 24h, smoke test проходит). Backend-сервисы для CRM/leads/analytics формально запущены, но БД недоступна из-за нарушенной авторизации — все endpoints пишут в "пустоту" с ошибкой auth failed.**

---

## Топ-3 блокирующих проблемы

### 🔴 1. PostgreSQL auth сломан
```
aim-app → postgres:5432 → InvalidPasswordError for user "aim_user"
```
- `/ready` endpoint возвращает `database: false`
- В PostgreSQL 45 таблиц создано, но **все пустые** (4 строки в event_bus_messages за всё время)
- Причина: docker volume создан с одним паролем, в `.env.production` пароль другой
- Влияние: leads, sales, onboarding, analytics, gdpr — endpoints не работают при реальном использовании

### 🔴 2. SESSION.md / .current-task описывают несуществующее состояние
- `.current-task` говорит: "Phase 09 deployed. Test hermes-chat-pro.html"
- Реальность: `hermes-chat-pro.html` возвращает **404** — файл не задеплоен
- В SESSION.md подробно описана HeadroomGuard интеграция — **контейнера нет в docker ps -a**
- LLM_MODEL в SESSION.md = `glm-5`, реальность = `deepseek-v4-pro`

### 🟡 3. SOUL.md рассинхронизирован между образом и данными
- `/opt/data/SOUL.md` (runtime, реально используется): 106 KB, 1411 строк, name=`aim-operator`
- `/opt/hermes/skills/aim/SOUL.md` (в Docker образе): 47 KB, 760 строк, name=`aim-operator-v4`
- `copy_soul.sh` НЕ обновляет при наличии файла — данные в volume "застряли" на старой версии
- md5 суммы разные, описание архитектуры кардинально отличается

---

## Топ-3 zombie/мёртвого кода

### 🟡 1. Магистры и субагенты (152 файла, ~3 MB)
- 19 файлов в `src/aim/magisters/` (ads_magister, content_magister, seo_magister + 4 variant каждый)
- 133 файла в `src/aim/subagents/` (ci-orchestrator с 23 агентами, 16 фазами)
- **В Hermes tools ни одного импорта** magisters/subagents
- В `aim-app/main.py` импортируется только `SalesAdminMagister` (и то в try/except)
- CLAUDE.md явно: "Магистры deprecated, CI Orchestrator заменён прямым вызовом инструментов"

### 🟡 2. Дубликат meai framework
- `/opt/aim/src/meai` — 868 KB
- `/opt/aim/AIM/src/meai` — 820 KB
- Структура идентична (одни и те же директории: agents, core, events, ...)
- Один из них не нужен

### 🟢 3. Backup-артefacts и кеш (300+ MB)
- `/opt/aim/AIM/.venv` — **236 MB** (дублирует Docker образы)
- `/opt/aim/AIM/logs/app.log` — **62 MB** (один файл без ротации)
- `/opt/aim/AIM/logs/nginx/` — **25 MB** (на хосте, дублирует nginx в контейнере)
- `/opt/aim/AIM/frontend` — 3.5 MB (локальная копия Next.js, дублирует Docker образ)
- `aim-theme/node_modules` — **15.7 MB** (в WordPress volume, должен быть только build-time)
- `/opt/data/bin/tirith` — **22 MB** (бинарник неизвестного назначения)
- ~30 `*.bak` / `*.backup-*` файлов в разных точках

---

## Цифры по проекту

| Метрика | Значение |
|---|---|
| Docker контейнеры (running) | 15 + 1 paperclip = **16** |
| Docker образы | 14, **13.1 GB** общий размер |
| Persistent volumes | 11, 886 MB |
| Контейнер `aim-paperclip` | 2.76 GB образ, роль не задокументирована |
| Hermes tools зарегистрировано | **67** (33 в CLAUDE.md) |
| Hermes skills | 5 (`aim`, `aim-scout`, `client-onboarding-pipeline`, `deep-research-phase-0`, `software-development`) |
| Hermes SQLite sessions | 32 сессии, 161 сообщение |
| REST endpoints aim-app | 53 (по OpenAPI) |
| Таблицы в PostgreSQL | 45 (все пустые) |
| WordPress страниц | 90 |
| Python файлов в `src/aim/` | 134 + 76 тестов |
| Markdown файлов в корне AIM | 233 |
| Активность за 24h | 46 chat calls, 58 tool calls |
| Memory usage (avg) | aim-app: 290 MB, aim-hermes: 122 MB, aim-paperclip: 171 MB |
| Disk usage | 24G / 69G (36%) |
| Server uptime | 2 days 10 hours |
| Load average | 0.29 / 0.25 / 0.26 (низкая) |

---

## Что работает хорошо

1. **LLM-оркестрация** — Hermes сам решает, какие tools вызывать, без жёсткого pipeline
2. **Persistent state Hermes** — SQLite `/opt/data/state.db`, 32 сессии пережили рестарт
3. **Мониторинг полный** — Prometheus + Grafana + Alertmanager + node/postgres exporters
4. **Docker compose декларативный** — 367 строк, всё в одном месте
5. **WordPress как CMS** — 90 страниц контента, активная тема aim-theme v2.1.76
6. **Nginx routing** — чёткие location-блоки для /api/, /chat, /wp-content, /wp-admin

## Что плохо (одной строкой каждое)

1. PostgreSQL настроен, но app не может подключиться → backend не работает
2. SESSION.md / .current-task описывают состояние, которого нет
3. SOUL.md рассинхронизирован между образом и volume
4. 152 файла мёртвого кода (magisters + subagents) в проекте
5. meai framework дублирован в двух местах
6. 236 MB `.venv` на хосте дублируют Docker
7. Backup-файлы не очищаются (`*.bak`, `*.backup-*`)
8. `aim-paperclip` (2.76 GB) работает, но что делает — непонятно

---

## Что делать дальше

Прочитать `09-REFACTOR-ROADMAP.md` для плана. Ключевые направления:
- **Phase A:** Стабилизация (починить PG auth, синхронизировать SOUL.md)
- **Phase B:** Удаление мёртвого кода (magisters, subagents, EventBus)
- **Phase C:** Целевая архитектура (clean LLM-orchestrator)
