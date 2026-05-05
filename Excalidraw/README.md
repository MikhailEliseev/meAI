# Excalidraw Диаграммы AIM Agency

**Создано:** 2026-05-05T10:52 GMT+3

## Созданные диаграммы

### 1. AIM Agency Architecture
**Файл:** `AIM-Agency-Architecture.excalidraw.md`

**Что показывает:**
- Полная иерархия системы: YOU → Architect → Operator → Magisters → Subagents
- 4 Magisters (SEO, Content, Ads, AI)
- 16 Subagents (по 4 на каждого Magister)
- CI System (15 агентов конкурентной разведки)
- Инфраструктура (Event Bus, Obsidian, Database)
- Интерфейсы (/architect, CLI, Telegram Bot)

**Элементы:**
- 66 элементов на диаграмме
- Цветовое кодирование по уровням
- Все связи и стрелки
- Легенда с статистикой

### 2. CI System Architecture
**Файл:** `CI-System-Architecture.excalidraw.md`

**Что показывает:**
- CI Orchestrator (координатор 16 фаз)
- 15 CI агентов с описанием задач
- 3 tier системы (Quick/Deep/Full)
- Интеграция с Magisters (SEO, Content, Ads)
- Инфраструктура (Event Bus, Obsidian vaults, JSON results)

**Фазы CI:**
- **Phase 1:** CI Scout (поиск и кластеризация)
- **Phase 2-3:** CI Auditor (глубокий аудит)
- **Phase 4:** CI Reputation (анализ репутации)
- **Phase 5:** 7 агентов (Finance, Vacancies, Tech, Site Crawler, Content, Pricing, Ecosystem)
- **Phase 6:** CI Factchecker (проверка фактов)
- **Phase 7-8:** CI Strategist (стратегический синтез)
- **Phase 9:** CI Prioritizer (приоритизация)
- **Phase 10:** CI Marketing Strategy (маркетинговая стратегия)
- **Phase 16:** CI Offer Generator (генерация КП)

**3 Tier системы:**
- **Quick Tier:** Фазы 1-4 (30 минут)
- **Deep Tier:** Фазы 1-9 (2-3 часа)
- **Full Tier:** Фазы 1-16 (1 день)

## Как открыть

### Вариант 1: Через Obsidian
1. Открой любой vault в Obsidian (например, `obsidian/architect/`)
2. Перейди в папку `../../Excalidraw/`
3. Открой файл `.excalidraw.md`
4. Переключись в режим Excalidraw (кнопка в правом верхнем углу)

### Вариант 2: Напрямую
1. Открой файл в любом текстовом редакторе
2. Скопируй JSON из секции `## Drawing`
3. Вставь на https://excalidraw.com

### Вариант 3: Через Finder
1. Открой папку `Excalidraw/` в Finder
2. Двойной клик на файл `.excalidraw.md`
3. Откроется в Obsidian (если установлен плагин Excalidraw)

## Технические детали

**Формат файлов:**
- Markdown с frontmatter
- JSON диаграмма в code block
- Совместимость с Obsidian Excalidraw plugin

**Цветовая схема:**
- 🔵 Синий (#a5d8ff) - YOU, интерфейсы
- 🟡 Жёлтый (#ffd43b) - Architect (стратегия)
- 🔵 Голубой (#74c0fc) - Operator (тактика)
- 🟢 Зелёный (#b2f2bb) - SEO Magister
- 🟡 Жёлтый (#ffec99) - Content Magister
- 🔴 Красный (#ffc9c9) - Ads Magister
- 🟣 Фиолетовый (#d0bfff) - AI Magister
- ⚪ Светлый (#e7f5ff) - Subagents

**Статистика:**
- 2 полные диаграммы
- 116+ элементов всего
- Все компоненты системы визуализированы
- Готовы к редактированию

## Что дальше?

Диаграммы можно:
- Редактировать в Obsidian (добавлять элементы, менять связи)
- Экспортировать в PNG/SVG
- Использовать в презентациях
- Обновлять по мере развития системы

---

**Создано:** Claude Code + Python
**Дата:** 2026-05-05
**Проект:** meAI / AIM Agency
