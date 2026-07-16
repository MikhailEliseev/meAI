# Architect Raw Inbox - Quick Start

**Created:** 2026-05-02  
**Status:** Ready to use!

---

## 🎯 Что это?

**Architect Raw Inbox** - персональная база знаний для улучшения системы meAI.

**Принцип:** Ты кидаешь любые мысли/идеи → Architect обрабатывает → Wiki растёт

**Паттерн:** LLM Wiki от Карпатого - знания компилируются один раз и поддерживаются актуальными, а не переоткрываются каждый раз.

---

## 🚀 Как использовать

### 1. Добавить заметку

```bash
# Вариант 1: Quick note (самый быстрый!)
qnote "Твоя идея здесь"

# Или из буфера обмена
pbpaste | qnote

# Вариант 2: Через echo
cd obsidian/architect/raw
echo "Твоя идея здесь" > $(date +%Y%m%d-%H%M)-topic.md

# Вариант 3: Через редактор
vim 20260502-2300-my-idea.md

# Вариант 4: Через Obsidian
# Просто создай файл в папке raw/
```

**Формат имени:** `YYYYMMDD-HHMM-topic.md` (с timestamp)

**Setup для qnote:**
```bash
# Добавь в ~/.zshrc (уже сделано!)
alias qnote='/Users/mikhaileliseev/Desktop/Dev/!meAI/scripts/quick_note.sh'

# Перезагрузи shell
source ~/.zshrc
```

### 2. Обработать заметки

```bash
# Интерактивный режим (обсуждает каждую заметку)
python scripts/architect_ingest.py

# Batch режим (обрабатывает всё молча)
python scripts/architect_ingest.py --batch
```

### 3. Смотреть результат

```bash
# Открой в Obsidian
open obsidian/architect/

# Или просто читай
cat obsidian/architect/wiki/index.md
cat obsidian/architect/wiki/log.md
```

---

## 📁 Структура

```
obsidian/architect/
├── raw/                    # 📥 Твои заметки (inbox)
│   └── YYYYMMDD-HHMM-topic.md
│
├── wiki/                   # 📚 Compiled knowledge
│   ├── index.md           # Каталог всех страниц
│   ├── log.md             # Хронология операций
│   ├── overview.md        # Общий обзор
│   ├── concepts/          # Концепции
│   ├── improvements/      # Идеи улучшений
│   ├── decisions/         # Архитектурные решения
│   └── connections/       # Связи между идеями
│
├── assets/                # 🖼️ Картинки, файлы
│
├── README.md              # Этот файл
└── ARCHITECT-WIKI.md      # Полная схема (500+ строк)
```

---

## 💡 Примеры заметок

### Пример 1: Идея улучшения

```markdown
# Exponential Backoff for Retries

**Type:** Improvement

## Problem
Fixed 5-second delay is not optimal

## Idea
Use exponential backoff: 1s, 2s, 4s with jitter

## Benefits
- Reduces load during outages
- Faster recovery

## Priority
High
```

### Пример 2: Архитектурное решение

```markdown
# Why Event-Driven Architecture

**Type:** Decision

## Context
Need async communication between agents

## Decision
Use Event Bus with priority queue

## Rationale
- Decouples agents
- Supports priorities
- Easy to monitor

## Status
Implemented
```

### Пример 3: Концепция

```markdown
# Hybrid Search Pattern

**Type:** Concept

## Definition
3-level search: Local → Teacher → Researcher

## Why It Matters
Balances speed and coverage

## Current State
Implemented in all Magisters
```

---

## 🔄 Операции

### Ingest (Обработка заметок)

**Что делает:**
1. Сканирует `raw/` на новые заметки
2. Читает каждую заметку
3. Извлекает insights
4. Создаёт/обновляет страницы в wiki
5. Обновляет index.md и log.md

**Команда:**
```bash
python scripts/architect_ingest.py
```

### Query (Вопросы)

**Что делает:**
1. Ищет в wiki/index.md
2. Читает релевантные страницы
3. Синтезирует ответ с цитатами

**Пример:**
```
Q: "Какие у нас идеи по улучшению retry logic?"
A: Architect читает wiki и отвечает с ссылками
```

### Lint (Проверка здоровья)

**Что делает:**
1. Ищет противоречия
2. Находит устаревшие данные
3. Ищет orphan pages (без ссылок)
4. Предлагает новые вопросы

**Команда:**
```bash
# TODO: будет реализовано
python scripts/architect_lint.py
```

---

## 📊 Типы страниц

### Concepts (`wiki/concepts/`)
Ключевые концепции, паттерны, принципы

### Improvements (`wiki/improvements/`)
Идеи улучшений с приоритетами

### Decisions (`wiki/decisions/`)
Архитектурные решения с обоснованием

### Connections (`wiki/connections/`)
Связи между концепциями

---

## 🎨 Obsidian Tips

### Graph View
Визуализация связей между страницами

### Dataview Plugin
Запросы по frontmatter (метаданным)

### Marp Plugin
Генерация презентаций из markdown

### Web Clipper
Сохранение статей из браузера

---

## 🔥 Реальный пример

```bash
# 1. Тебе пришла идея
echo "Idea: Add circuit breaker pattern to prevent cascade failures" > \
  obsidian/architect/raw/$(date +%Y%m%d-%H%M)-circuit-breaker.md

# 2. Обработать
python scripts/architect_ingest.py

# Architect:
# - Читает заметку
# - Создаёт wiki/improvements/circuit-breaker.md
# - Обновляет wiki/concepts/resilience.md
# - Добавляет связь с retry-logic
# - Обновляет index.md
# - Логирует в log.md

# 3. Через неделю спрашиваешь
"Какие у нас идеи по resilience?"

# Architect:
# - Читает wiki/index.md
# - Находит improvements/circuit-breaker.md
# - Находит improvements/exponential-backoff.md
# - Находит concepts/resilience.md
# - Синтезирует ответ со всеми связями
```

---

## 🚀 Что дальше?

### Сейчас работает:
- ✅ Структура создана
- ✅ Схема определена (ARCHITECT-WIKI.md)
- ✅ Ingest workflow работает
- ✅ Пример заметки обработан

### TODO (опционально):
- [ ] Полная интеграция с LLM для анализа
- [ ] Query workflow (вопросы к wiki)
- [ ] Lint workflow (проверка здоровья)
- [ ] Search tool (qmd или custom)
- [ ] Obsidian plugins setup

---

## 💡 Ключевая идея

**Знания компилируются один раз и поддерживаются актуальными.**

Не нужно каждый раз переоткрывать - связи уже есть, противоречия уже найдены, синтез уже сделан.

Wiki растёт с каждой заметкой. Connections укрепляются. Знания накапливаются.

---

**Pattern credit:** Andrej Karpathy's LLM Wiki  
**Implementation:** meAI Architect  
**Status:** Ready to use! 🚀

---

## Quick Commands

```bash
# Add note (fastest!)
./scripts/quick_note.sh "Your idea"

# Or traditional way
echo "Your idea" > obsidian/architect/raw/$(date +%Y%m%d-%H%M)-topic.md

# Check inbox once
python scripts/architect_inbox_monitor.py --once

# Start monitoring (continuous)
python scripts/architect_inbox_monitor.py

# View
cat obsidian/architect/wiki/index.md

# Open in Obsidian
open obsidian/architect/
```

---

## 🤖 Автоматический мониторинг

### Запуск монитора

```bash
# Однократная проверка
python scripts/architect_inbox_monitor.py --once

# Непрерывный мониторинг (каждые 60 секунд)
python scripts/architect_inbox_monitor.py

# Кастомный интервал (каждые 5 минут)
python scripts/architect_inbox_monitor.py --interval 300
```

### Что делает монитор:

1. **Отслеживает новые файлы** в `raw/`
2. **Классифицирует** по типам (strategy, question, idea, technical, note)
3. **Генерирует промпты** для Claude
4. **Сохраняет состояние** в `.inbox_state.yaml`
5. **Логирует операции** в `wiki/log.md`

### Типы файлов:

- `strategy` - стратегические документы → передаёт Architect
- `question` - вопросы → определяет кому делегировать
- `idea` - идеи → оценивает и структурирует
- `technical` - технические документы → создаёт заметки
- `note` - обычные заметки → структурирует

### Алиасы для удобства

Добавь в `~/.zshrc`:

```bash
# Architect shortcuts
alias note='~/Desktop/Dev/!meAI/scripts/quick_note.sh'
alias inbox-check='python ~/Desktop/Dev/!meAI/scripts/architect_inbox_monitor.py --once'
alias inbox-monitor='python ~/Desktop/Dev/!meAI/scripts/architect_inbox_monitor.py'
```

Теперь:

```bash
# Быстро создать заметку
note "Идея: интеграция с Telegram"

# Проверить inbox
inbox-check

# Запустить мониторинг
inbox-monitor
```

---

**Начни прямо сейчас!** 🎯

**Обновлено:** 2026-05-02 23:37 - добавлен автоматический мониторинг
