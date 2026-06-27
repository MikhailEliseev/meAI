# ФТЗ: PM-Skill для Hermes Agent (AIM)

**Версия:** 1.0.0
**Цель:** Multi-tenant Project Management для Hermes Agent — работа в изолированных Telegram-чатах, каждый чат = один проект одного клиента.

---

## 1. ОБЩАЯ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────┐
│                  Hermes Gateway                  │
│  Telegram Bot (один, встроен в gateway)         │
└───────────────┬─────────────────────────────────┘
                │
    ┌───────────┼───────────────┐
    ▼           ▼               ▼
┌────────┐ ┌────────┐     ┌────────┐
│ Чат A  │ │ Чат B  │ ... │ Чат N  │  ← Изолированные Telegram-группы
│Проект 1│ │Проект 2│     │Проект N│
└───┬────┘ └───┬────┘     └───┬────┘
    │          │              │
    ▼          ▼              ▼
┌─────────────────────────────────────────────────┐
│           Hermes Agent (один инстанс)            │
│                                                  │
│  PM Skill: определяет проект по chat_id         │
│  → подгружает контекст, данные, скиллы          │
└─────────────────────────────────────────────────┘
```

### Ключевые принципы

1. **Один бот, много чатов** — один Telegram-бот работает во всех группах
2. **chat_id = идентификатор проекта** — по chat_id определяем, с каким проектом работаем
3. **Клиент может иметь несколько проектов** — один клиент в нескольких группах
4. **Данные клиента общие** — врачи, финансы, конкуренты доступны из любого проекта этого клиента
5. **Изоляция на уровне контекста** — не глобальная изоляция памяти, а логическая: я знаю, с каким проектом работаю, и действую только в его папке
6. **Никакой супергруппы** — только отдельные группы, клиенты не видят друг друга

---

## 2. PROJECT REGISTRY (реестр проектов)

### Файл: `/root/.hermes/projects-registry.json`

Хранит маппинг `chat_id → client_slug + project_slug`.

```json
{
  "version": 1,
  "projects": {
    "-1001234567890": {
      "client_slug": "atlas-esthetics",
      "client_name": "Atlas Esthetics",
      "project_slug": "presale-atlas-2026",
      "project_name": "Presale Atlas 2026",
      "created_at": "2026-06-07T12:00:00Z",
      "last_active": "2026-06-07T14:00:00Z",
      "status": "active",
      "members": [
        {"user_id": 322367335, "role": "manager", "name": "Михаил Елисеев"},
        {"user_id": 123456, "role": "client", "name": "Представитель клиента"}
      ],
      "skills": ["presale-pipeline", "second-brain", "doctor-content-analysis"],
      "workdir": "/root/projects/atlas-esthetics/presale-atlas-2026/"
    }
  },
  "clients": {
    "atlas-esthetics": {
      "name": "Atlas Esthetics",
      "projects": ["presale-atlas-2026", "smm-atlas-2026"]
    }
  }
}
```

### CLI для управления реестром: `/root/bin/pm-registry.py`

```bash
# Создать проект + привязать чат
pm-registry.py add-chat \
  --chat-id="-1001234567890" \
  --client-slug="atlas-esthetics" \
  --client-name="Atlas Esthetics" \
  --project-slug="presale-atlas-2026" \
  --project-name="Presale Atlas 2026"

# Список проектов клиента
pm-registry.py list-client --client-slug="atlas-esthetics"

# Получить информацию по chat_id
pm-registry.py get --chat-id="-1001234567890"

# Обновить статус
pm-registry.py update --chat-id="-1001234567890" --status="paused"

# Список всех проектов
pm-registry.py list-all

# Перенести проект в папку другого клиента
pm-registry.py move-project --project-slug="presale-atlas-2026" --new-client-slug="..."
```

---

## 3. СТРУКТУРА ПРОЕКТА НА ДИСКЕ

### Корень проектов: `/root/projects/`

```
/root/projects/
├── {client_slug}/
│   ├── shared/                          # Общие данные клиента (все проекты)
│   │   ├── doctors.json                 # Врачи клиники
│   │   ├── financials.json              # Финансы (из ФНС)
│   │   ├── competitors.json             # Конкуренты
│   │   └── site-meta.json               # Метаданные сайта
│   │
│   ├── {project_slug}/                  # Конкретный проект
│   │   ├── .project-meta.json           # Метаданные проекта
│   │   ├── context.json                 # Текущий контекст (фаза, last message)
│   │   ├── data.json                    # Собранные данные (как в presale)
│   │   ├── notes/                       # Заметки по проекту
│   │   ├── files/                       # Файлы, скрапы, медиа
│   │   │   ├── reels/
│   │   │   ├── transcripts/
│   │   │   └── reports/
│   │   ├── skills/                      # Скиллы только для этого проекта
│   │   │   └── project-custom/          # Кастомные скиллы
│   │   ├── knowledge/                   # Знания, собранные в проекте
│   │   │   └── findings.md
│   │   └── deliverables/                # Результаты (КП, отчёты)
│   │       └── index.html
│   │
│   └── logs/                            # Логи активности по клиенту
│       └── activity.log
```

### `.project-meta.json`

```json
{
  "slug": "presale-atlas-2026",
  "name": "Presale Atlas 2026",
  "client_slug": "atlas-esthetics",
  "client_name": "Atlas Esthetics",
  "created_at": "2026-06-07T12:00:00Z",
  "status": "active",
  "phases_completed": ["0-deep-research", "1-clinic-collect"],
  "current_phase": "2-competitors-ci",
  "telegram_chat_id": "-1001234567890",
  "team": [
    {"user_id": 322367335, "role": "manager"},
    {"user_id": 123456, "role": "client_rep"}
  ]
}
```

### `context.json`

```json
{
  "last_active": "2026-06-07T14:30:00Z",
  "last_topic": "Сбор врачей клиники",
  "last_data_refs": {
    "doctors_scraped": "/root/projects/atlas-esthetics/presale-atlas-2026/files/doctors.md",
    "instagram_reels": "/root/projects/atlas-esthetics/presale-atlas-2026/files/reels/"
  },
  "pending_tasks": [
    {"id": "t1", "description": "Проверить Instagram Atlas", "status": "completed"},
    {"id": "t2", "description": "Собрать конкурентов", "status": "in_progress"}
  ],
  "key_findings": [
    "Наталья Алифер — 135K подписчиков, ключевой актив",
    "Сайт на Bitrix — нужен browser для парсинга"
  ]
}
```

---

## 4. PM SKILL — ЛОГИКА РАБОТЫ

### 4.1 Инициализация сессии (entry point)

При получении сообщения в Telegram-группе:

```
1. Определить chat_id из входящего сообщения
2. Проверить /root/.hermes/projects-registry.json:
   - Если chat_id найден → загрузить client_slug + project_slug
   - Если не найден → сообщить: "Проект не привязан. Используйте /project bind"
3. Загрузить data.json из /root/projects/{client_slug}/{project_slug}/
4. Загрузить .project-meta.json
5. Подгрузить привязанные скиллы из поля skills (если есть)
6. Проверить context.json — если есть незавершённые задачи, напомнить
7. Установить HERMES_PROJECT_SLUG, HERMES_CLIENT_SLUG, HERMES_PROJECT_DIR в окружение
```

### 4.2 Определение chat_id в Hermes

Входящее сообщение от Telegram gateway содержит `telegram_chat_id` и `telegram_thread_id` (для топиков) в метаданных. Нужно:

```python
# Из метаданных сообщения
chat_id = str(metadata.get("telegram_chat_id", ""))
```

### 4.3 Slash-команды PM-скилла (через /commands в чате)

| Команда | Описание |
|---------|----------|
| `/project status` | Текущее состояние проекта: фаза, задачи, дата |
| `/project summary` | Краткая сводка проекта для клиента |
| `/project note <текст>` | Добавить заметку в notes/findings.md |
| `/project doctor <фамилия>` | Найти информацию о враче в shared/doctors |
| `/project skill <name>` | Привязать скилл к проекту |
| `/project add-task <текст>` | Добавить задачу в context.json |
| `/project done <task_id>` | Закрыть задачу |
| `/project log` | Последние действия по проекту |
| `/project bind <client_slug> <project_slug>` | Привязать текущий чат к проекту (только для админа) |
| `/project create <slug> <name>` | Создать новый проект (только для админа) |

### 4.4 Работа с Second Brain

PM-скилл должен иметь доступ ко Второму Мозгу:

```python
# Поиск по всему Second Brain
search-kb "{query}"

# Поиск только по проекту
search-kb --path /root/projects/{client_slug}/knowledge "{query}"

# Сохранение в Second Brain
python3 /root/.knowledge/scripts/ingest-clinic.py {slug} "{name}" ...
```

### 4.5 Автоматическое сохранение контекста

После каждого значимого действия:

```python
# Сохранить context.json
{
  "last_active": "now",
  "last_topic": "описание последнего действия",
  "pending_tasks": [...]
}
```

---

## 5. КОМПОНЕНТЫ ДЛЯ РЕАЛИЗАЦИИ

### 5.1. PM Registry CLI (`/root/bin/pm-registry.py`)

Утилита для управления реестром проектов.

**Аргументы:**
- `add-chat` — привязать chat_id к проекту
- `get --chat-id X` — получить информацию
- `list-client --slug X` — проекты клиента
- `list-all` — все проекты
- `update` — обновить статус/поля
- `remove --chat-id X` — отвязать чат

**Формат вывода:** JSON (машиночитаемый) + human-readable summary.

### 5.2. PM Context Manager (`/root/bin/pm-context.py`)

Утилита для управления контекстом проекта.

**Аргументы:**
- `set --chat-id X --key KEY --value VAL` — установить поле в context.json
- `get --chat-id X` — показать context.json
- `save --chat-id X` — создать чекпоинт (копия context.json с датой)
- `restore --chat-id X --checkpoint DATE` — откатить контекст
- `add-note --chat-id X --text "..."` — добавить заметку
- `add-task --chat-id X --text "..."` — добавить задачу
- `done-task --chat-id X --task-id ID` — закрыть задачу

### 5.3. PM Project Creator (`/root/bin/pm-create-project.py`)

Скрипт для инициализации нового проекта.

```bash
pm-create-project.py \
  --client-slug="atlas-esthetics" \
  --client-name="Atlas Esthetics" \
  --project-slug="smm-atlas-2026" \
  --project-name="SMM-стратегия Atlas 2026"
```

**Что делает:**
1. Создаёт `/root/projects/{client_slug}/{project_slug}/`
2. Создаёт `.project-meta.json`
3. Создаёт пустой `context.json`
4. Создаёт директории: `files/`, `notes/`, `skills/`, `knowledge/`, `deliverables/`
5. Если `shared/` нет — создаёт и её
6. Регистрирует проект в `clients` секции registry

### 5.4. PM Telegram Router (gateway plugin или хук)

Механизм, который при входящем сообщении:
1. Извлекает `chat_id`
2. Вызывает `pm-registry.py get --chat-id {chat_id}`
3. Устанавливает переменные окружения:
   - `HERMES_PROJECT_CHAT_ID`
   - `HERMES_PROJECT_CLIENT_SLUG`
   - `HERMES_PROJECT_SLUG`
   - `HERMES_PROJECT_DIR`
4. Эти переменные читаются PM-скиллом при инициализации

**Можно реализовать через `pre_gateway_dispatch` hook.**

### 5.5. PM Skill SKILL.md

Сам скилл, который загружается в Hermes.

**Frontmatter:**
```yaml
name: project-management
description: "Multi-tenant Project Management для AIM — изолированная работа по проектам в Telegram-чатах"
version: 1.0.0
trigger: "при получении сообщения в Telegram-группе с проектом"
depends_on:
  - second-brain
  - context-preservation
  - presale-pipeline
```

**Структура SKILL.md:**
- Инициализация (определение проекта)
- Slash-команды
- Работа с контекстом
- Изоляция данных
- Интеграция с Second Brain
- Интеграция с presale-pipeline

**Scripts:**
- `scripts/init-project.py` — инициализация
- `scripts/detect-context.py` — определение проекта из chat_id

---

## 6. ИНТЕГРАЦИЯ С PRESALE-PIPELINE

Когда запускается presale для нового клиента:

1. В реестре проектов проверяется, есть ли уже проект для этого клиента
2. Если нет — создаётся новый проект через `pm-create-project.py`
3. Чат привязывается к проекту через `pm-registry.py add-chat`
4. Все данные presale сохраняются в `/root/projects/{client_slug}/{project_slug}/`
5. Врачи, конкуренты, финансы дублируются в `shared/` для доступа из других проектов

**Модификация presale-pipeline:**
- На Phase 0 (Pre-flight): создать/проверить проект
- После завершения presale: сохранить финальный data.json в project
- HTML-КП сохранять в `deliverables/`

---

## 7. ОБРАБОТКА ГРАНИЧНЫХ СЛУЧАЕВ

### 7.1 Чат без привязанного проекта
- Бот отвечает: «Этот чат не привязан к проекту. Напишите /project create или обратитесь к @mikhaileliseev»
- Не выполняет никаких действий, требующих контекста проекта

### 7.2 Один клиент в нескольких чатах
- Registry хранит список chat_id для каждого клиента
- При работе в любом из чатов — `shared/` один и тот же
- `data.json` раздельный (у каждого проекта своё)

### 7.3 Представитель клиента в нескольких проектах
- Определение по chat_id, а не по user_id
- В разных чатах представитель видит данные разных проектов
- Общие данные клиента доступны через `shared/` в обоих чатах

### 7.4 Бот добавлен в существующий чат
- Если registry не знает chat_id — бот просит привязать проект
- Админ (Михаил) пишет `/project bind {client_slug} {project_slug}`

### 7.5 Компактизация / потеря контекста
- context.json на диске — всегда актуальная копия
- После /new — загрузить context.json, восстановить pending_tasks
- PM-скилл вызывает context-preservation при старте

### 7.6 Смена модели/провайдера
- PM-скилл не привязан к модели — работает с любым провайдером
- Все данные на диске, не в памяти модели

---

## 8. ФАЙЛЫ ДЛЯ РЕАЛИЗАЦИИ (список)

| Файл | Назначение |
|------|-----------|
| `/root/bin/pm-registry.py` | CLI для реестра проектов |
| `/root/bin/pm-context.py` | CLI для управления контекстом |
| `/root/bin/pm-create-project.py` | CLI для создания проекта |
| `/root/.hermes/skills/software-development/project-management/SKILL.md` | PM-скилл |
| `/root/.hermes/skills/software-development/project-management/scripts/init-project.py` | Скрипт инициализации |
| `/root/.hermes/skills/software-development/project-management/scripts/detect-context.py` | Детектор контекста |
| `/root/.hermes/skills/software-development/project-management/templates/project-meta.json` | Шаблон метаданных проекта |
| `/root/.hermes/skills/software-development/project-management/templates/context.json` | Шаблон контекста |
| `/root/.hermes/projects-registry.json` | Реестр проектов (корневой) |
| `/root/projects/{client_slug}/{project_slug}/.project-meta.json` | Мета проекта |
| `/root/projects/{client_slug}/{project_slug}/context.json` | Контекст проекта |

---

## 9. ПОРЯДОК РЕАЛИЗАЦИИ (MVP → Production)

### Фаза 1 — MVP (сделать сейчас)
1. `pm-registry.py` — add-chat, get, list-all
2. `pm-create-project.py` — создание структуры папок
3. `pm-context.py` — set, get, add-task, done-task
4. `project-management/SKILL.md` — базовая логика
5. `detect-context.py` — определение проекта по chat_id

### Фаза 2 — Интеграция
1. Интеграция с presale-pipeline (Phase 0 создаёт проект)
2. Интеграция со Second Brain
3. Переменные окружения HERMES_PROJECT_*

### Фаза 3 — Production
1. Telegram gateway hook (pre_gateway_dispatch)
2. Multi-tenant memory isolation (если потребуется)
3. Dashboard/статистика проектов
4. Автоматическое логирование активности

---

## 10. ТРЕБОВАНИЯ К КОДУ

### Общие
- Все CLI-скрипты: Python 3.10+, argparse, JSON I/O
- Код должен работать на Linux (сервер AIM)
- Все пути абсолютные (от /)
- Обработка ошибок: любая ошибка → понятное сообщение, exit code 1
- Валидация входных данных перед записью

### pm-registry.py
- Файл блокируется flock при записи (race condition при параллельных чатах)
- При старте — создать файл, если не существует (с `{"version": 1, "projects": {}, "clients": {}}`)

### pm-context.py
- Читать `.project-meta.json` для определения client_slug по chat_id
- Чекпоинты: сохранять копии в `files/checkpoints/{timestamp}.json`

### SKILL.md
- Чёткие триггеры загрузки
- Инструкции для агента (меня) — что делать в каждом сценарии
- Примеры команд с пояснениями
