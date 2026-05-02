---
title: "Architect Wiki - Структура по паттерну LLM Wiki"
type: design
created: 2026-05-02
priority: high
status: draft
source: "Andrej Karpathy's LLM Wiki pattern"
tags:
  - architect
  - wiki
  - structure
  - knowledge-base
---

# Architect Wiki - Структура по паттерну LLM Wiki

## Проблема

**Текущее состояние:**
```
obsidian/architect/wiki/
├── blackhat-seo-igaming-analysis.md
├── claude-design-practical-guide.md
├── medical-content-analysis-agent.md
├── inbox-improvements-after-mistake.md
├── gatekeeper-fact-checker.md
├── index.md
└── log.md
```

**Проблема:** Всё в кучу, как в raw/  
**Но:** raw/ = свалка (это нормально), wiki/ = структурированное знание (должно быть организовано)

---

## Идеи Карпатого (LLM Wiki Pattern)

### Ключевая идея:

> **Wiki = persistent, compounding artifact**

Не RAG (retrieve каждый раз), а **compiled knowledge** (скомпилировано один раз, поддерживается актуальным).

### Три слоя:

1. **Raw sources** (immutable) - источники, не трогаем
2. **Wiki** (LLM-generated) - структурированное знание
3. **Schema** (CLAUDE.md) - правила и конвенции

### Операции:

1. **Ingest** - обработка источника → обновление wiki
2. **Query** - вопросы → ответы с цитатами → новые страницы
3. **Lint** - проверка здоровья wiki (противоречия, orphans, gaps)

### Специальные файлы:

- **index.md** - content-oriented каталог (что есть)
- **log.md** - chronological запись (что происходило)

---

## Применение к Architect Wiki

### Предлагаемая структура:

```
obsidian/architect/
├── raw/                          # Слой 1: Источники (immutable)
│   ├── *.md                      # Необработанные заметки
│   └── assets/                   # Изображения, файлы
│
├── wiki/                         # Слой 2: Структурированное знание
│   ├── index.md                  # Каталог всех страниц
│   ├── log.md                    # Хронология операций
│   ├── overview.md               # Общий обзор системы
│   │
│   ├── concepts/                 # Концепции и паттерны
│   │   ├── ai-agents.md
│   │   ├── automation.md
│   │   ├── llm-wiki-pattern.md
│   │   └── ai-first-agency.md
│   │
│   ├── technologies/             # Технологии и инструменты
│   │   ├── claude-design.md
│   │   ├── claude-code.md
│   │   ├── obsidian.md
│   │   └── python-fastapi.md
│   │
│   ├── strategies/               # Стратегии и методы
│   │   ├── seo-automation.md
│   │   ├── content-generation.md
│   │   └── medical-marketing.md
│   │
│   ├── agents/                   # Агенты системы
│   │   ├── medical-content-agent.md
│   │   ├── seo-agent.md
│   │   ├── content-agent.md
│   │   └── gatekeeper-agent.md
│   │
│   ├── workflows/                # Процессы и workflow
│   │   ├── inbox-processing.md
│   │   ├── synthesis-workflow.md
│   │   └── quality-control.md
│   │
│   ├── projects/                 # Проекты
│   │   ├── meai-system.md
│   │   └── aim-agency.md
│   │
│   ├── sources/                  # Обработанные источники
│   │   ├── 2026-05-02-blackhat-seo.md
│   │   └── 2026-05-02-claude-design.md
│   │
│   └── connections/              # Связи и синтезы
│       └── aim-agency-functionality.md
│
├── decisions/                    # Слой 3: Стратегические решения
│   └── *.md
│
├── quarantine/                   # Отклонённые файлы
│   └── *.md
│
└── ARCHITECT-WIKI.md            # Schema (правила и конвенции)
```

---

## Категории wiki/

### 1. concepts/ - Концепции

**Что:** Ключевые идеи, паттерны, принципы

**Примеры:**
- `ai-agents.md` - Что такое AI-агенты, как работают
- `automation.md` - Принципы автоматизации
- `llm-wiki-pattern.md` - Паттерн Карпатого
- `ai-first-agency.md` - Концепция AI-first подхода

**Формат:**
```markdown
# Концепция: AI-агенты

## Определение
...

## Ключевые принципы
...

## Применение в нашей системе
...

## Связанные концепции
- [[automation]]
- [[ai-first-agency]]

## Источники
- [[2026-05-02-blackhat-seo]]
```

### 2. technologies/ - Технологии

**Что:** Инструменты, фреймворки, платформы

**Примеры:**
- `claude-design.md` - Claude Design возможности
- `claude-code.md` - Claude Code workflow
- `obsidian.md` - Obsidian для wiki
- `python-fastapi.md` - Python + FastAPI стек

**Формат:**
```markdown
# Технология: Claude Design

## Что это
...

## Возможности
...

## Как используем
...

## Экономика
- Раньше: 100,000₽
- Сейчас: 0₽

## Связанные технологии
- [[claude-code]]
- [[obsidian]]

## Источники
- [[2026-05-02-claude-design]]
```

### 3. strategies/ - Стратегии

**Что:** Методы, подходы, тактики

**Примеры:**
- `seo-automation.md` - SEO через AI
- `content-generation.md` - Генерация контента
- `medical-marketing.md` - Медицинский маркетинг

**Формат:**
```markdown
# Стратегия: SEO-автоматизация

## Суть
...

## Методы
1. Автоматический мониторинг
2. Генерация контента
3. Семантическое SEO

## Что применяем (WhiteHat)
...

## Что НЕ применяем (BlackHat)
...

## Связанные стратегии
- [[content-generation]]

## Источники
- [[2026-05-02-blackhat-seo]]
```

### 4. agents/ - Агенты

**Что:** Описание агентов системы

**Примеры:**
- `medical-content-agent.md`
- `seo-agent.md`
- `gatekeeper-agent.md`

**Формат:**
```markdown
# Агент: Medical Content Agent

## Роль
...

## Возможности
...

## Архитектура
...

## Статус
MVP approved, HIGH priority

## Связанные агенты
- [[content-agent]]
- [[seo-agent]]

## Источники
- [[2026-05-02-medical-content-idea]]
```

### 5. workflows/ - Процессы

**Что:** Workflow, процессы, операции

**Примеры:**
- `inbox-processing.md` - Обработка raw/
- `synthesis-workflow.md` - Синтез знаний
- `quality-control.md` - Gatekeeper

**Формат:**
```markdown
# Workflow: Inbox Processing

## Этапы
1. Gatekeeper (проверка)
2. Классификация
3. Обработка
4. Индексация
5. Синтез

## Диаграмма
...

## Улучшения
- 2026-05-02: Добавлен Gatekeeper

## Связанные workflow
- [[synthesis-workflow]]
- [[quality-control]]
```

### 6. projects/ - Проекты

**Что:** Описание проектов

**Примеры:**
- `meai-system.md` - meAI система
- `aim-agency.md` - AIM Agency

**Формат:**
```markdown
# Проект: AIM Agency

## Описание
AI-first медицинское маркетинговое агентство

## Позиционирование
...

## Функционал
...

## Roadmap
...

## Связанные проекты
- [[meai-system]]

## Решения
- [[2026-05-02-aim-agency-functionality]]
```

### 7. sources/ - Источники

**Что:** Обработанные источники (summary)

**Примеры:**
- `2026-05-02-blackhat-seo.md`
- `2026-05-02-claude-design.md`

**Формат:**
```markdown
# Источник: BlackHat SEO для iGaming

## Метаданные
- Дата: 2026-05-02
- Тип: video transcript
- URL: https://...

## Ключевые инсайты
...

## Что применили
...

## Что отклонили
...

## Обновлённые страницы
- [[ai-agents]]
- [[seo-automation]]
- [[aim-agency]]
```

### 8. connections/ - Связи

**Что:** Синтезы, связи между концепциями

**Примеры:**
- `aim-agency-functionality.md` - Синтез 3 источников

**Формат:**
```markdown
# Связь: AIM Agency Functionality

## Источники
- [[concepts/ai-agents]]
- [[technologies/claude-design]]
- [[agents/medical-content-agent]]

## Синтез
...

## Решения
...

## Результат
Стратегический план в decisions/
```

---

## Миграция текущих файлов

### Текущие файлы → Новая структура:

```
blackhat-seo-igaming-analysis.md
  → sources/2026-05-02-blackhat-seo.md
  → concepts/ai-agents.md (extract)
  → strategies/seo-automation.md (extract)

claude-design-practical-guide.md
  → sources/2026-05-02-claude-design.md
  → technologies/claude-design.md (extract)

medical-content-analysis-agent.md
  → agents/medical-content-agent.md

inbox-improvements-after-mistake.md
  → workflows/inbox-processing.md (merge)

gatekeeper-fact-checker.md
  → workflows/quality-control.md (rename)
  → agents/gatekeeper-agent.md (extract)
```

---

## Операции (по Карпатому)

### 1. Ingest (обработка источника)

**Workflow:**
```
1. Gatekeeper проверяет raw/
2. Читаю источник
3. Обсуждаю ключевые инсайты с тобой
4. Создаю/обновляю страницы:
   - sources/YYYY-MM-DD-title.md (summary)
   - concepts/*.md (extract concepts)
   - technologies/*.md (extract tech)
   - strategies/*.md (extract methods)
   - agents/*.md (extract agent ideas)
5. Обновляю index.md
6. Добавляю запись в log.md
```

**Пример:**
```
Источник: BlackHat SEO видео
  ↓
Создано/обновлено:
- sources/2026-05-02-blackhat-seo.md (NEW)
- concepts/ai-agents.md (UPDATED)
- strategies/seo-automation.md (NEW)
- technologies/cloudflare-pages.md (NEW)
- index.md (UPDATED)
- log.md (APPENDED)
```

### 2. Query (вопросы)

**Workflow:**
```
1. Ты задаёшь вопрос
2. Я читаю index.md → нахожу релевантные страницы
3. Читаю найденные страницы
4. Синтезирую ответ с цитатами
5. Если ответ ценный → создаю новую страницу
```

**Пример:**
```
Вопрос: "Какой функционал дать AIM Agency?"
  ↓
Читаю:
- concepts/ai-agents.md
- technologies/claude-design.md
- agents/medical-content-agent.md
  ↓
Синтезирую ответ
  ↓
Создаю:
- connections/aim-agency-functionality.md
- decisions/2026-05-02-aim-agency-functionality.md
```

### 3. Lint (проверка здоровья)

**Что проверять:**
- Противоречия между страницами
- Устаревшие данные
- Orphan pages (без входящих ссылок)
- Важные концепции без своей страницы
- Пропущенные cross-references
- Gaps в знаниях

**Команда:**
```
"Проверь здоровье wiki"
```

**Результат:**
```
⚠️  Найдено:
- Противоречие: concepts/ai-agents.md vs strategies/seo-automation.md
- Orphan: technologies/python-fastapi.md (нет входящих ссылок)
- Missing page: "Operator" упоминается, но нет страницы
- Gap: Нет информации про deployment
```

---

## index.md (обновлённый)

**Новая структура:**

```markdown
# Architect Wiki - Index

## Concepts (5)
- [[ai-agents]] - AI-агенты для автоматизации (3 sources)
- [[automation]] - Принципы автоматизации (2 sources)
- [[llm-wiki-pattern]] - Паттерн Карпатого (1 source)
- [[ai-first-agency]] - AI-first подход (2 sources)
- [[knowledge-compilation]] - Compiled vs Retrieved knowledge (1 source)

## Technologies (4)
- [[claude-design]] - Создание сайтов за 1 час (1 source)
- [[claude-code]] - Workflow разработки (0 sources)
- [[obsidian]] - Wiki система (1 source)
- [[python-fastapi]] - Backend стек (0 sources)

## Strategies (3)
- [[seo-automation]] - SEO через AI (1 source)
- [[content-generation]] - Генерация контента (2 sources)
- [[medical-marketing]] - Медицинский маркетинг (1 source)

## Agents (4)
- [[medical-content-agent]] - Анализ медицинских статей (HIGH)
- [[seo-agent]] - SEO мониторинг (TODO)
- [[content-agent]] - Генерация контента (TODO)
- [[gatekeeper-agent]] - Контроль качества (CRITICAL)

## Workflows (3)
- [[inbox-processing]] - Обработка raw/ (ACTIVE)
- [[synthesis-workflow]] - Синтез знаний (DESIGN)
- [[quality-control]] - Gatekeeper (DESIGN)

## Projects (2)
- [[meai-system]] - meAI архитектор (ACTIVE)
- [[aim-agency]] - AI-first агентство (MVP)

## Sources (2)
- [[2026-05-02-blackhat-seo]] - BlackHat SEO анализ
- [[2026-05-02-claude-design]] - Claude Design гайд

## Connections (1)
- [[aim-agency-functionality]] - Синтез 3 источников → стратегический план

---

**Stats:**
- Total pages: 22
- Sources processed: 2
- Concepts extracted: 5
- Agents designed: 4
- Decisions made: 4

**Last updated:** 2026-05-02T21:05:00Z
```

---

## log.md (формат)

**Формат записи:**
```
## [YYYY-MM-DD HH:MM] operation | Description
```

**Операции:**
- `ingest` - Обработка источника
- `query` - Ответ на вопрос
- `synthesis` - Синтез знаний
- `lint` - Проверка здоровья
- `improvement` - Улучшение системы
- `design` - Проектирование

**Пример:**
```markdown
## [2026-05-02 20:34] ingest | BlackHat SEO analysis
- Source: raw/blackhat-seo-video.md
- Created: sources/2026-05-02-blackhat-seo.md
- Updated: concepts/ai-agents.md, strategies/seo-automation.md
- Extracted: 15 key insights
- Status: Processed

## [2026-05-02 20:50] synthesis | AIM Agency Functionality
- Sources: 3 (blackhat-seo, claude-design, medical-content)
- Created: connections/aim-agency-functionality.md
- Decision: decisions/2026-05-02-aim-agency-functionality.md
- Status: Strategic plan approved

## [2026-05-02 20:59] design | Gatekeeper Agent
- Created: workflows/quality-control.md, agents/gatekeeper-agent.md
- Priority: CRITICAL
- Status: Design complete, ready for implementation
```

---

## Следующие шаги

### Priority 1: Реструктуризация (сегодня)

1. Создать структуру папок
2. Мигрировать текущие файлы
3. Обновить index.md
4. Обновить log.md

### Priority 2: Extraction (завтра)

1. Извлечь концепции из sources
2. Создать страницы concepts/
3. Создать страницы technologies/
4. Создать страницы strategies/

### Priority 3: Lint (эта неделя)

1. Проверить противоречия
2. Найти orphans
3. Добавить missing pages
4. Улучшить cross-references

---

## Вывод

**Проблема:** Wiki в кучу, как raw/  
**Решение:** Структура по паттерну Карпатого (8 категорий)  
**Результат:** Compiled knowledge, не RAG

**Ключевая идея:** Wiki = persistent, compounding artifact

**Следующий шаг:** Реструктуризация сегодня

---

**Architect Decision:** Применяем паттерн LLM Wiki от Карпатого. Приоритет: HIGH.
