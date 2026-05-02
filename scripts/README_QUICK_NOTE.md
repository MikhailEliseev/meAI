# Architect Raw Inbox - Quick Setup Guide

**Статус:** ✅ Полностью настроено и работает  
**Дата:** 2026-05-02

---

## 🎯 Что это?

Автоматическая система обработки твоих идей и заметок для улучшения meAI.

**Принцип:** Ты кидаешь идею → Система обрабатывает → Wiki растёт → Решения принимаются

---

## 🚀 Быстрый старт

### 1. Создать заметку (3 способа)

```bash
# Способ 1: Быстрая заметка (РЕКОМЕНДУЕТСЯ)
./scripts/quick_note.sh "Твоя идея здесь"

# Способ 2: Вручную
echo "Твоя идея" > obsidian/architect/raw/$(date +%Y%m%d-%H%M)-topic.md

# Способ 3: Через Obsidian
# Просто создай файл в папке obsidian/architect/raw/
```

### 2. Обработать заметки

```bash
# Автоматически (рекомендуется)
source venv/bin/activate
python scripts/architect_inbox_monitor.py --once

# Или запустить непрерывный мониторинг
python scripts/architect_inbox_monitor.py
```

### 3. Посмотреть результат

```bash
# Открыть в Obsidian
open obsidian/architect/

# Или посмотреть лог
cat obsidian/architect/wiki/log.md

# Или посмотреть конкретную заметку
ls obsidian/architect/wiki/
```

---

## 📁 Структура

```
obsidian/architect/
├── raw/                    # 📥 Твои заметки (inbox)
│   ├── *.md               # Новые заметки (status: new)
│   └── *.md               # Обработанные (status: processed)
│
├── wiki/                   # 📚 Структурированное знание
│   ├── log.md             # Хронология всех операций
│   ├── *.md               # Анализы и заметки
│   └── ...
│
├── decisions/              # 🎯 Стратегические решения
│   └── *.md               # Решения от Architect
│
└── .inbox_state.yaml      # 🔄 Состояние обработки
```

---

## 🤖 Как работает автоматизация

### Монитор делает:

1. **Отслеживает** новые файлы в `raw/`
2. **Классифицирует** по типам:
   - `strategy` → передаёт Architect
   - `question` → определяет кому делегировать
   - `idea` → оценивает потенциал
   - `technical` → создаёт техническую заметку
   - `note` → структурирует
3. **Генерирует промпт** для Claude
4. **Сохраняет состояние** (не обрабатывает дважды)
5. **Логирует** в `wiki/log.md`

### Я (Claude) делаю:

1. **Читаю** новую заметку
2. **Анализирую** содержимое
3. **Извлекаю** ключевые инсайты
4. **Создаю** структурированные заметки в `wiki/`
5. **Принимаю решения** (если нужно) в `decisions/`
6. **Обновляю** метаданные в `raw/` (status: processed)
7. **Логирую** операцию в `wiki/log.md`

---

## 📊 Примеры обработки

### Пример 1: Идея (сегодня)

**Вход:**
```bash
./scripts/quick_note.sh "Идея: AI-агент для анализа медицинских статей"
```

**Обработка:**
```bash
python scripts/architect_inbox_monitor.py --once
```

**Результат:**
- ✅ Создан: `wiki/medical-content-analysis-agent.md`
- ✅ Оценка: HIGH priority
- ✅ Решение: ОДОБРЕНО для MVP
- ✅ Архитектура: 5-layer pipeline
- ✅ Next steps: Proof of Concept на этой неделе

### Пример 2: Стратегический документ (сегодня)

**Вход:**
```
raw/Как BlackHat-агентство выводит iGaming сайты в топ.md
```

**Результат:**
- ✅ Создан: `wiki/blackhat-seo-igaming-analysis.md` (полный анализ)
- ✅ Создан: `decisions/2026-05-02-ai-agents-for-seo.md` (решение)
- ✅ Ключевой инсайт: AI + процессы > люди
- ✅ Решение: Приоритизируем AI-агенты над наймом

---

## 🛠️ Команды

### Основные

```bash
# Создать заметку
./scripts/quick_note.sh "Твоя идея"

# Проверить inbox один раз
source venv/bin/activate
python scripts/architect_inbox_monitor.py --once

# Запустить непрерывный мониторинг (каждые 60 сек)
python scripts/architect_inbox_monitor.py

# Кастомный интервал (каждые 5 минут)
python scripts/architect_inbox_monitor.py --interval 300
```

### Просмотр

```bash
# Посмотреть лог операций
cat obsidian/architect/wiki/log.md

# Посмотреть состояние
cat obsidian/architect/.inbox_state.yaml

# Найти необработанные файлы
grep -l "status: new" obsidian/architect/raw/*.md

# Открыть в Obsidian
open obsidian/architect/
```

---

## 🎨 Алиасы (опционально)

Добавь в `~/.zshrc`:

```bash
# Architect shortcuts
alias note='~/Desktop/Dev/!meAI/scripts/quick_note.sh'
alias inbox-check='cd ~/Desktop/Dev/!meAI && source venv/bin/activate && python scripts/architect_inbox_monitor.py --once'
alias inbox-monitor='cd ~/Desktop/Dev/!meAI && source venv/bin/activate && python scripts/architect_inbox_monitor.py'
alias inbox-log='cat ~/Desktop/Dev/!meAI/obsidian/architect/wiki/log.md'
```

Перезагрузи shell:
```bash
source ~/.zshrc
```

Теперь:
```bash
note "Твоя идея"      # Создать заметку
inbox-check           # Проверить inbox
inbox-monitor         # Запустить мониторинг
inbox-log             # Посмотреть лог
```

---

## 📈 Статистика (сегодня)

**Обработано заметок:** 2
- ✅ BlackHat SEO анализ (стратегия)
- ✅ Medical Content Agent (идея)

**Создано документов:** 3
- `wiki/blackhat-seo-igaming-analysis.md`
- `decisions/2026-05-02-ai-agents-for-seo.md`
- `wiki/medical-content-analysis-agent.md`

**Принято решений:** 2
- Приоритизируем AI-агенты над наймом
- Medical Content Agent одобрен для MVP

---

## 🔥 Что дальше?

### Сейчас работает:
- ✅ Автоматический мониторинг `raw/`
- ✅ Классификация по типам
- ✅ Генерация промптов для Claude
- ✅ Отслеживание состояния
- ✅ Логирование операций

### Можно улучшить:
- [ ] Интеграция с Claude API (полная автоматизация)
- [ ] Telegram bot для быстрого захвата
- [ ] Email → raw/ интеграция
- [ ] Voice notes → транскрипция
- [ ] Web UI для просмотра

---

## 💡 Ключевая идея

**Знания компилируются один раз и поддерживаются актуальными.**

Не нужно каждый раз переоткрывать - связи уже есть, решения уже приняты, синтез уже сделан.

Wiki растёт с каждой заметкой. Connections укрепляются. Решения накапливаются.

---

**Начни прямо сейчас!** 🎯

```bash
./scripts/quick_note.sh "Моя первая идея для meAI"
```
