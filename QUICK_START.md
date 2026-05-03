# Quick Start Cheat Sheet

## 🚀 Начало новой сессии

```bash
# 1. Восстанови контекст
cat CHECKPOINTS.md | tail -100

# 2. Проверь текущее состояние
grep -A 20 "## Current State" CHECKPOINTS.md

# 3. Посмотри приоритеты
grep -A 10 "Следующие приоритеты" CHECKPOINTS.md
```

## 📋 Текущие приоритеты (2026-05-03)

**Priority 1 (сегодня):**
- [ ] Протестировать Teacher Agent
- [ ] Создать остальных магистров (Content, Ads, AI)

**Priority 2 (эта неделя):**
- [ ] Реализовать Monitor Level 2 (автоматическое создание wiki)
- [ ] Реализовать Synthesis Agent (синтез инсайтов)
- [ ] Интегрировать Teacher с Architect wiki

**Priority 3 (2 недели):**
- [ ] Создать базы знаний для субагентов
- [ ] Реализовать специализированных агентов (SEO, Content, Ads)
- [ ] Добавить метрики и dashboard

## 🏗️ Архитектура (текущее состояние)

```
YOU (Собственник)
  ↕
OPERATOR (Операционный директор) ✅
  ↕
TEACHER (Ректор) ✅ НОВОЕ!
  ↕
MAGISTERS (SEO, Content, Ads, AI) ⏳ структура создана
  ↕
SUBAGENTS (узкоспециализированные) ⏳ следующий шаг
```

## 📁 Ключевые файлы

**Для восстановления контекста:**
- `CHECKPOINTS.md` - лог разработки (НАЧНИ ОТСЮДА!)
- `CLAUDE.md` - project instructions
- `obsidian/architect/wiki/index.md` - каталог знаний

**Код:**
- `scripts/teacher_agent.py` - Teacher Agent
- `scripts/gatekeeper_agent.py` - Gatekeeper Agent
- `scripts/architect_inbox_monitor.py` - Monitor
- `src/meai/agents/operator.py` - Operator
- `src/meai/core/architect.py` - Architect

**Obsidian:**
- `obsidian/teacher/` - Teacher vault
- `obsidian/magisters/seo-magister/` - SEO Magister vault
- `obsidian/architect/wiki/` - Architect wiki

## 🔑 Ключевые концепции

1. **LLM Wiki Pattern** - ЗАКОН для всех vaults
   - raw/ → wiki/ → decisions/
   - 8 категорий wiki
   - Frontmatter: `status: processed` + `output: [[wiki-file]]`

2. **Иерархия системы**
   - YOU → Architect → Operator → Teacher → Magisters → Subagents

3. **Event-driven коммуникация**
   - Event Bus для всех коммуникаций
   - Приоритеты: P0 (critical) → P3 (low)

4. **Feedback Loop**
   - Subagent → Magister → Teacher → Operator → YOU

5. **Teacher НЕ обучает субагентов напрямую**
   - Только через магистров
   - Magisters адаптируют знания "на пальцах"

## 🧪 Как протестировать Teacher Agent

```bash
# 1. Активировать venv
source venv/bin/activate

# 2. Запустить Teacher Agent
python scripts/teacher_agent.py

# 3. В другом терминале - создать тестовое событие
# (TODO: создать скрипт для тестирования)
```

## 📝 Как создать новый чекпоинт

1. Открой `CHECKPOINTS.md`
2. Скопируй шаблон последнего чекпоинта
3. Увеличь номер (Checkpoint #6)
4. Заполни все секции:
   - Что сделано (с ✅)
   - Ключевые файлы
   - Контекст для продолжения
   - Следующий шаг
5. Обнови "Current State"
6. Закоммить в git

## 🎯 Критерии для нового чекпоинта

Создавай чекпоинт когда:
- ✅ Завершена крупная фаза (новый агент, система)
- ✅ Реализован новый компонент с кодом
- ✅ Изменена архитектура
- ✅ Создана документация (>5 файлов)
- ✅ Сессия длится >2 часа

## 🔄 Workflow разработки

```
1. Прочитай CHECKPOINTS.md
   ↓
2. Выбери задачу из приоритетов
   ↓
3. Реализуй задачу
   ↓
4. Обнови документацию
   ↓
5. Протестируй
   ↓
6. Создай чекпоинт (если критерии выполнены)
   ↓
7. Закоммить в git
```

## 🆘 Если потерял контекст

```bash
# Быстрое восстановление
cat CHECKPOINTS.md | grep -A 50 "## Checkpoint #5"

# Полное восстановление
cat CHECKPOINTS.md
cat CHECKPOINTS_GUIDE.md
cat CLAUDE.md
```

---

**Используй этот файл как шпаргалку при каждой сессии!**

**Last updated:** 2026-05-03T08:45:00Z
