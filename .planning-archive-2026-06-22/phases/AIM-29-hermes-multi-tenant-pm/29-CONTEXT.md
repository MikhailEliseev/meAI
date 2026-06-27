# Phase 29: Hermes Multi-Tenant PM — Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Source:** PRD Express Path (pm-skill-fts.md)

<domain>
## Phase Boundary

Интеграция PM-скилла (Project Management) в Hermes для multi-tenant работы. Один инстанс Hermes обслуживает множество изолированных Telegram-групп: каждая группа = один проект одного клиента. chat_id → client_slug → project_slug. Полная изоляция контекста между проектами, общие данные клиента через shared/. Интеграция с presale-pipeline, Second Brain и context-preservation.

Компоненты:
- 4 CLI-скрипта: pm-registry.py, pm-create-project.py, pm-context.py, pm-detect-context.py
- PM SKILL.md как skill первого уровня в Hermes
- projects-registry.json с flock-блокировками
- Структура /root/projects/{client}/shared/ + /{project}/
- Интеграция с presale-pipeline (Phase 0), Second Brain, context-preservation
- Slash-команды в Telegram-чатах

</domain>

<decisions>
## Implementation Decisions

### Архитектура
- **D-01**: Один бот, много чатов — один Telegram-бот работает во всех группах. Никакой супергруппы, клиенты не видят друг друга.
- **D-02**: chat_id = primary key для идентификации проекта. По chat_id определяем client_slug + project_slug через projects-registry.json.
- **D-03**: 5-уровневая архитектура изоляции (без fork ядра): Telegram-группы → Project Registry → Per-project файлы → Second Brain (read-only) → Memory (только meta).
- **D-04**: Клиент может иметь несколько проектов. Данные клиента (врачи, финансы, конкуренты) в shared/ доступны всем проектам клиента.

### Project Registry
- **D-05**: projects-registry.json в /root/.hermes/ с маппингом chat_id → {client_slug, project_slug, status, members, skills, workdir}.
- **D-06**: flock-блокировка при записи в registry (race condition при параллельных чатах).
- **D-07**: При старте — автосоздание registry с `{"version": 1, "projects": {}, "clients": {}}`.

### Структура проекта
- **D-08**: /root/projects/{client_slug}/shared/ — общие данные клиента (doctors.json, financials.json, competitors.json, site-meta.json).
- **D-09**: /root/projects/{client_slug}/{project_slug}/ — конкретный проект (.project-meta.json, context.json, data.json, notes/, files/, skills/, knowledge/, deliverables/).

### PM-скрипты
- **D-10**: pm-registry.py — add-chat, get, list-client, list-all, update, remove, move-project. JSON + human-readable вывод.
- **D-11**: pm-create-project.py — создаёт структуру папок, .project-meta.json, пустой context.json, регистрирует в clients секции.
- **D-12**: pm-context.py — set, get, save (checkpoint), restore, add-note, add-task, done-task. Чекпоинты в files/checkpoints/{timestamp}.json.
- **D-13**: pm-detect-context.py — по chat_id определяет client_slug + project_slug, возвращает JSON {found, client_slug, project_slug, project_dir}.

### PM SKILL.md
- **D-14**: SKILL.md загружается как skill первого уровня — entry point при получении сообщения в Telegram-группе.
- **D-15**: Slash-команды: /project status, summary, note, doctor, skill, add-task, done, log, bind, create.
- **D-16**: Инициализация сессии: chat_id → registry lookup → загрузка data.json + .project-meta.json → подгрузка skills → проверка pending_tasks → установка HERMES_PROJECT_* переменных.

### Интеграции
- **D-17**: presale-pipeline: Phase 0 создаёт/проверяет проект, данные сохраняются в project_dir/data.json, HTML-КП в deliverables/.
- **D-18**: Second Brain: поиск через search-kb, сохранение через ingest-clinic.py. Клиентские данные дублируются в shared/.
- **D-19**: context-preservation: после /new → pm-detect-context → загрузка context.json, восстановление pending_tasks.

### Технические требования
- **D-20**: Python 3.10+, argparse, JSON I/O. Все пути абсолютные (от /). Обработка ошибок: exit code 1 + сообщение.
- **D-21**: Валидация входных данных перед записью. Все CLI-скрипты работают на Linux (сервер AIM).

### Claude's Discretion
- Размещение скриптов в кодовой базе meAI (AIM/hermes/ vs отдельная директория)
- Способ интеграции PM-skill в систему загрузки скиллов Hermes (skill_view или прямой импорт)
- Тестирование: unit-тесты на Python скрипты + интеграционный тест на полный цикл
- Формат и структура финального коммита в репозиторий meAI

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ФТЗ и исследования
- `.planning/phases/AIM-29-hermes-multi-tenant-pm/pm-skill-fts.md` — Полное функциональное ТЗ (21KB): архитектура, компоненты, интеграции, граничные случаи
- `.planning/phases/AIM-29-hermes-multi-tenant-pm/multi-tenant-research.md` — Исследование multi-tenant: GitHub #34352, почему не fork, 5-уровневая архитектура

### Существующие компоненты Hermes
- `AIM/hermes/` — Кодовая база Hermes: gateway, skills, tools
- `AIM/hermes/hermes-agent/` — Ядро Hermes agent
- `.planning/phases/AIM-25-presale-pipeline-tool-extraction/` — Как пресейл-скиллы извлекались в отдельные tools (аналогичный паттерн)
- `.planning/phases/AIM-26-presale-orchestration-fix/` — SKILL.md v3.0.0 orchestration layer (паттерн для parent skill)

</canonical_refs>

<specifics>
## Specific Ideas

Из ФТЗ (pm-skill-fts.md):
- 5-уровневая архитектура изоляции — не модифицируем ядро Hermes, только файловый уровень
- flock-блокировка registry — критично для параллельных чатов
- pre_gateway_dispatch hook для автоматического определения проекта при входящем сообщении
- Чекпоинты контекста с timestamp для возможности отката
- MVP → Production phased approach: сначала скрипты + SKILL.md, потом интеграции, потом production-фичи

</specifics>

<deferred>
## Deferred Ideas

- **Telegram gateway hook (pre_gateway_dispatch)** — Фаза 3 (Production) по ФТЗ, не в этом PR
- **Multi-tenant memory isolation** — ждём принятия GitHub PR #34352 в ядро Hermes
- **Dashboard/статистика проектов** — отдельная фича, не в scope этой фазы
- **Автоматическое логирование активности** — Фаза 3 (Production)

</deferred>

---

*Phase: 29-hermes-multi-tenant-pm*
*Context gathered: 2026-06-07 via PRD Express Path*
