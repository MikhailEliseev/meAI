# ФУНДАМЕНТАЛЬНАЯ ДИАГНОСТИКА ПРОЕКТА meAI / AIM

**Дата исследования:** 6 июля 2026
**Метод:** nmt-diagnose skill — глубокий аудит документации, кода, истории
**Исследователь:** Claude (ZCode session)

---

## 🎯 EXECUTIVE SUMMARY

### Что это за проект?

**AIM (AI-first Medical Marketing Agency)** — продукт для владельцев частных медицинских клиник в России. Клиент даёт URL своей клиники → через 5-8 минут получает красивый HTML-отчёт с анализом рынка, конкурентов, слабых мест.

**meAI** — это фреймворк-обёртка над AIM, задумывавшийся как "CEO-архитектор", иерархическая система AI-агентов (Architect → Operator → Magisters → Subagents).

### Текущий статус (в одной фразе)

**Pipeline v5 работает end-to-end** (3 реальных клиента протестировано: arclinic.ru, mira-med.ru, iphk.ru). Но проект находится в состоянии **архитектурного кризиса** между двумя параллельными реальностями.

---

## 🔀 ГЛАВНАЯ ПРОБЛЕМА: ДВЕ ПАРАЛЛЕЛЬНЫЕ РЕАЛЬНОСТИ

### Реальность A: "meAI University Framework" (май 2026)

**Описано в:** `README.md`, `PROJECT_SUMMARY.md`, `NEW-SESSION-INSTRUCTIONS.md`

**Архитектура:**
```
Architect (стратегия)
  ↓
Operator (тактика)
  ↓
Teacher (управление знаниями)
  ↓
6 Magisters (SEO, Content, Ads, Analytics, Social, Intelligence)
  ↓
Subagents (специализированные исполнители)
```

**Компоненты:**
- Hierarchical Learning System (Teacher → Magisters → Subagents)
- Gatekeeper Agent (7 проверок качества)
- LLM Wiki Pattern (Karpathy) — Obsidian vaults
- Experience Learning (tracker, quality updater)
- Hybrid Search (Local Cache → Qdrant → Researcher)
- Event Bus для async коммуникации

**Код:** `/src/meai/` — 16 Python модулей, агенты, события, память, обучение

**Статус:** 
- ✅ Код написан (6 Magisters, 110 тестов passing)
- ❌ НЕ используется в production
- ❌ НЕ интегрирован с Hermes

---

### Реальность B: "AIM Scout Pipeline v6" (июнь-июль 2026)

**Описано в:** `rewrite-v2/00-MASTER.md`, `.current-task`, git commits

**Архитектура:**
```
Client URL
  ↓
Hermes FastAPI (LLM-оркестратор)
  ↓
run_full_scout tool
  ↓
PipelineEngine (13 sequential phases)
  ↓
generate_html_report
  ↓
publish_scout_report (WordPress)
  ↓
https://iamaim.ru/{8-char-slug}
```

**Компоненты:**
- Hermes (FastAPI + hermes-agent library)
- 67 registered tools
- PipelineEngine v7 (13 фаз: prescan → competitors → tech → reviews → content → doctors → smi → forums → finances → content-gaps → build → qc → publish)
- WordPress theme `aim-theme` с dual-theme дизайн-системой
- SQLite для сессий, MariaDB для WordPress

**Код:** `/AIM/hermes/` — production implementation

**Статус:**
- ✅ Pipeline v5 E2E WORKING (зафиксировано в `.current-task`)
- ✅ 3 реальных клиента протестированы
- ✅ Отчёты публикуются на iamaim.ru
- 🟡 Pipeline v6 в разработке (улучшения качества)

---

### Конфликт

**meAI framework** (~5 MB кода) существует параллельно с **AIM production** (~10+ MB кода), но они **НЕ соединены**.

- meAI framework НЕ импортируется в Hermes
- Magisters НЕ вызываются из pipeline
- Event Bus НЕ используется
- Teacher/Researcher агенты НЕ задействованы

**Вывод:** Это два РАЗНЫХ проекта в одном репо.

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ (детально)

### Что РАБОТАЕТ (Production на iamaim.ru)

#### 1. Hermes Chat ✅
- FastAPI сервер (port 8000 internal)
- `/api/chat` и `/api/chat/stream` (SSE)
- Telegram gateway (webhook + polling)
- Session persistence (SQLite `/opt/data/state.db`, 32 сессии, 161 сообщение)
- DeepSeek V4 Pro как primary LLM
- 67 tools зарегистрировано

#### 2. Pipeline v5 ✅
- 13 фаз последовательного исполнения
- Время прогона: 3-8 минут (зависит от клиники)
- Реальные источники данных:
  - Perplexity (market research)
  - Apify (14 keys rotation) — поиск конкурентов
  - Firecrawl (15 keys rotation) — scraping
  - Lighthouse — tech audit
  - 2ГИС, Яндекс.Карты, ПроДокторов — отзывы
  - nalog.ru — финансы компании
  - Brave Search — СМИ-упоминания

#### 3. WordPress Stack ✅
- WordPress 6.x + MariaDB 10.11
- Theme `aim-theme` v2.1.76
- 90 страниц (27 в draft после cleanup)
- Custom page template для scout-постов
- Privacy filters (scout-privacy.php v2)

#### 4. Design System ✅
- Canonical reference: `design-showcase-dual-theme.html` (2521 строка)
- Dual theme (light + dark)
- Glassmorphism effects
- Playfair Display + Jost fonts
- Metric tags, surface blocks, glass cards

---

### Что СЛОМАНО или НЕ ДОДЕЛАНО

#### 🔴 Критично (блокирует MVP)

##### 1. Три разных генератора HTML отчётов
| Файл | Строк | Статус | Проблема |
|------|-------|--------|----------|
| `generate_html_report.py` | 698 | Используется pipeline | Старый дизайн, БЕЗ glass cards |
| `post_report.py` | 363 | НЕ подключен | Новый, но шрифт **Inter** (неправильно) |
| `migrate_scout_design.py` | 508 | Для миграции | Базовая дизайн-система |

**Pipeline использует СТАРЫЙ генератор** → отчёты выглядят плохо.

##### 2. SOUL.md рассинхрон
- `/opt/data/SOUL.md` (runtime): 106 KB, 1411 строк, описывает "армию AI-агентов"
- `/opt/hermes/skills/aim/SOUL.md` (в образе): 47 KB, 760 строк, описывает "aim-operator-v4"
- LLM видит смешанные инструкции → когнитивный диссонанс

##### 3. 67 tools — слишком много
- LLM путается в выборе
- Много дублирующих функций
- 9 firecrawl variants, 3 scraping approaches
- Цель: сократить до 15-20 tools

#### 🟡 Важно (не блокирует MVP)

##### 4. PostgreSQL auth сломан
- `aim-app → postgres:5432` → InvalidPasswordError
- Backend endpoints (leads, sales, onboarding) падают
- **НЕ критично:** pipeline использует SQLite

##### 5. session_archive баг
- 14 ошибок "failed to save" за pipeline прогон
- Данные между фазами теряются
- **НЕ критично:** pipeline работает в памяти

##### 6. Двойной путь (LLM-driven vs Python-driven)
- LLM может вызывать отдельные tools
- Python pipeline автоматически прогоняет 13 фаз
- PRESALE промпт говорит "вызови ТОЛЬКО run_full_scout", но LLM иногда игнорирует

---

### ZOMBIE КОД (не используется, занимает место)

#### Magisters (19 файлов, ~3 MB)
`AIM/src/aim/magisters/` — ads_magister, content_magister, seo_magister и т.д.
**НИ ОДНОГО импорта в Hermes tools.** CLAUDE.md явно: "Магистры deprecated".

#### Subagents (133 файла, ~5 MB)
`AIM/src/aim/subagents/` — множество специализированных агентов
**НИ ОДНОГО импорта в Hermes tools.**

#### EventBus (2692 строки)
`AIM/src/aim/events/` — реализован, но НЕ используется в pipeline

#### aim-paperclip (2.76 GB образ)
Container работает, но назначение неизвестно. Михаил решил: **УДАЛИТЬ**.

#### aim-frontend (Next.js)
Container на порту 3099, дублирует WordPress landing. Михаил: **УДАЛИТЬ**.

#### Дубликат meai framework
- `/opt/aim/src/meai` — 868 KB
- `/opt/aim/AIM/src/meai` — 820 KB
Структура идентична, один не нужен.

---

## 🎭 ИСТОРИЯ ПРОЕКТА (timeline)

### Май 2026: "University Infrastructure"
- Создание meAI framework (Architect, Operator, Teacher, Magisters)
- Qdrant integration для vector search
- Obsidian vaults для knowledge management
- Hierarchical Learning System
- **Результат:** Красивая архитектура, 110 тестов passing, но НЕ production-ready

### Июнь 2026: Pivot к простому pipeline
- Отказ от мультиагентности
- Фокус на "один LLM, один pipeline"
- PipelineEngine с 13 фазами
- Интеграция реальных data sources
- **Результат:** Что-то начало работать, но куча багов

### 27-29 июня 2026: Критические фиксы
- Фикс: `run_prescan` → `run_full_scout` в PRESALE промпте
- Увеличение SSE deadline с 420s до 600s
- v7.1 report builder
- **Результат:** Pipeline стабилизировался

### 30 июня - 1 июля 2026: Cleanup
- Удаление 63 fragment scout-постов (draft)
- Privacy v2 (sitemap, REST API protection)
- WordPress index.php для raw HTML render
- Миграция 17 постов в новую дизайн-систему

### 1 июля 2026: **MOMENT OF TRUTH**
Михаил создал папку `rewrite-v2/` — 8 документов (00-MASTER до 07-SUCCESS-CRITERIA).

**Вердикт:**
> "После 2 месяцев разработки (1 мая → 30 июня 2026) результат = **ноль**. Чат работает, дизайн готов, инструменты зарегистрированы — но **финального продукта, который получит клиент, НЕТ**. За 2 месяца потрачено "куча денег" на токены, перебрано несколько моделей, написано 2078 коммитов. Доверие к Claude Code = 0."

Это документ-якорь для **ПОЛНОЙ ПЕРЕДЕЛКИ**.

### 2-3 июля 2026: Прорыв
- Pipeline v5 E2E working
- 3 реальных клиента протестированы
- git tag `pipeline-v5-working-e2e`
- Backup создан
- **Статус зафиксирован в `.current-task`**

### 3-6 июля 2026: Pipeline v6 improvements
- Качественные улучшения (FIX #1-#3)
- Deployed to production
- Документация обновлена

---

## 🧬 АРХИТЕКТУРНЫЙ АНАЛИЗ

### Текущая архитектура (Production)

```
┌─────────────────────────────────────────┐
│  NGINX (iamaim.ru, SSL termination)     │
└──────────┬──────────────────────┬───────┘
           │                      │
    /api/* │                      │ /*
           ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│  Hermes FastAPI  │   │  WordPress       │
│  (Python 3.11)   │   │  (PHP + MariaDB) │
│                  │   │                  │
│  - SOUL.md       │   │  - Landing       │
│  - 67 tools      │   │  - Scout reports │
│  - SessionDB     │   │  - Blog          │
└────────┬─────────┘   └─────────┬────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│  External APIs   │   │  MariaDB         │
│  - DeepSeek      │   │  (wp_posts)      │
│  - Apify (14)    │   └──────────────────┘
│  - Firecrawl(15) │
│  - Perplexity    │
│  - Brave Search  │
└──────────────────┘
```

**4 контейнера** (сейчас 16 running — много лишних)

### Целевая архитектура (из rewrite-v2/)

**Минимализация:**
- 4-5 контейнеров (Hermes + WordPress + MariaDB + Nginx + Redis опционально)
- 15-20 tools (вместо 67)
- 1 генератор отчётов (полная дизайн-система)
- 1 pipeline (упрощённый engine.py, 400-500 строк)
- SOUL.md 25-35 KB (вместо 106 KB)

**Удаление:**
- PostgreSQL (SQLite достаточно)
- aim-frontend (Next.js не нужен)
- aim-paperclip
- Magisters/Subagents код
- EventBus

---

## 💡 КЛЮЧЕВЫЕ ИНСАЙТЫ

### 1. Архитектурная overengineering

**Проблема:** meAI framework строился как "универсальная AI-операционная система" с иерархией агентов, event sourcing, vector search, hierarchical learning.

**Реальность:** Клиенту нужен простой pipeline: URL → 13 фаз → HTML отчёт.

**Вывод:** 80% написанного кода не используется в production.

### 2. Раздвоение между видением и реализацией

**Видение (01-PROJECT-ESSENCE.md):**
- "Hermes — AI-аналитик для медицинских клиник"
- "Без продаж, без слова пресейл"
- "Доверие через прозрачность"
- "Персонализация, не генерализация"

**Реальность (SOUL.md 106 KB):**
- "Армия AI-агентов"
- "Операционный директор"
- Упоминания магистров/субагентов
- Устаревшая identity

**Вывод:** LLM получает конфликтующие инструкции.

### 3. Недостаток фокуса

**Timeline показывает:**
- Май: строили "университет для AI" (Teacher, Magisters, Learning System)
- Июнь: переключились на simple pipeline
- Результат: ни то, ни другое не доведено до конца

**Цитата Михаила:**
> "Я больше денег тратить не хочу. Мне нужно хоть что-то получить."

**Вывод:** Перфекционизм убил MVP.

### 4. Trust crisis

**Факт:** После 2 месяцев и 2078 коммитов Михаил написал:
> "Доверие к Claude Code = 0"

**Причины:**
- 10+ раз слышал "всё готово" — каждый раз что-то не работало
- Куча денег потрачена на токены
- Финального продукта НЕТ

**CLAUDE.md правило #1:**
> "TRUST LEVEL: ZERO. Любое утверждение разработчика = факт из измерения. Не 'я думаю', не 'вероятно'."

### 5. Успех пришёл через упрощение

**Pipeline v5 заработал когда:**
- Отказались от мультиагентности
- Один LLM, один линейный pipeline
- Реальные data sources, не mock
- Фокус на одном продукте: URL → отчёт

**Вывод:** Простота побеждает сложность.

---

## 🎯 RECOMMENDATIONS

### Стратегический уровень

#### Рекомендация #1: Выбрать ОДНУ реальность

**Два пути вперёд:**

**Путь A: Продолжить meAI framework**
- Довести до конца иерархическую систему
- Интегрировать Magisters с production
- Реализовать Teacher/Researcher
- **Время:** 2-3 месяца дополнительно
- **Риск:** Может снова не дать продукта
- **Вердикт Михаила:** НЕТ (доверия нет, денег нет)

**Путь B: Признать meAI framework экспериментом** ✅ РЕКОМЕНДУЮ
- Архивировать `/src/meai/` как "исследовательская работа"
- Сфокусироваться на AIM production (Hermes + Pipeline)
- Довести до MVP по критериям из 07-SUCCESS-CRITERIA.md
- **Время:** 2-3 недели
- **Риск:** Низкий (уже v5 working)
- **Вердикт Михаила:** Да (см. rewrite-v2/)

#### Рекомендация #2: Следовать плану из rewrite-v2/

**План 06-IMPLEMENTATION-PLAN.md выглядит здравым:**

**Неделя 1 (4-5 дней): Чистка**
- Удалить zombie код (Magisters, Subagents, EventBus)
- Убрать лишние контейнеры (16 → 4)
- Синхронизировать SOUL.md
- Сократить tools (67 → 15-20)

**Неделя 2 (5-7 дней): Pipeline v2**
- Рефакторинг PipelineEngine (упростить)
- Довести все 13 фаз до production quality
- Smoke tests на 5 разных URLs

**Неделя 3 (4-6 дней): Дизайн-система**
- Создать `build_report.py` с полной canonical дизайн-системой
- Подключить к pipeline
- Мигрировать старые scout reports

**Неделя 4 (3-5 дней): UX**
- Обновить SOUL.md (identity = аналитик)
- Финальный PRESALE промпт (3 сообщения)
- Стабилизация

**Итого:** 17-23 дня до MVP

#### Рекомендация #3: Восстановить доверие через процесс

**Принципы работы:**

1. **Backup перед каждым изменением**
   ```bash
   ./scripts/auto-commit-deploy.sh
   ssh aim "tar -czf /opt/aim-backup-$(date +%Y%m%d-%H%M%S).tar.gz /opt/aim"
   ```

2. **Smoke test после каждого этапа**
   - Не переходить к следующему этапу без проверки
   - 3+ независимых теста
   - Документировать результаты

3. **Честная коммуникация**
   - Не говорить "готово" пока все 10 критериев MVP не выполнены
   - Лучше "не работает X, нужно Y дней" чем "всё готово"

4. **Инкрементальный прогресс**
   - Маленькие шаги
   - Каждый шаг = видимый результат
   - Регулярные demo Михаилу

---

### Тактический уровень

#### Quick Wins (можно сделать за 1-2 дня)

1. **Синхронизировать SOUL.md**
   - Выбрать canonical версию (47 KB)
   - Обновить runtime `/opt/data/SOUL.md`
   - Убрать упоминания "армии агентов", "оператора"
   - Новая identity: "Hermes — AI-аналитик"

2. **Удалить zombie код**
   - `rm -rf AIM/src/aim/magisters/` (19 файлов)
   - `rm -rf AIM/src/aim/subagents/` (133 файла)
   - `rm -rf AIM/src/aim/events/` (EventBus)
   - Освободить ~8 MB кода

3. **Остановить лишние контейнеры**
   - `docker stop aim-paperclip aim-frontend aim-postgres`
   - Обновить docker-compose.yml (4 сервиса)
   - `docker system prune -af`

4. **Сократить tools registry**
   - Скрыть от LLM внутренние tools
   - Оставить 15-20 user-facing
   - Обновить SOUL.md с актуальным списком

**Результат:** Проект станет понятнее, логи чище, LLM меньше путается.

#### Critical Path (блокирует MVP)

1. **Новый генератор отчётов `build_report.py`**
   - 600-800 строк Python
   - Полная canonical дизайн-система
   - Шрифт Jost (НЕ Inter)
   - Все компоненты из design-showcase
   - Подключить к pipeline фаза 10

2. **Удалить старые генераторы**
   - `rm generate_html_report.py` (698 строк)
   - `rm post_report.py` (363 строки)
   - Оставить только `build_report.py`

3. **Финализировать PRESALE промпт**
   - Жёсткое правило: "вызови ТОЛЬКО run_full_scout"
   - Формат: РОВНО 3 сообщения (контраст → точки роста → отчёт)
   - Запрещённые слова: пресейл, КП, купить, заказать
   - Тон: эксперт-аналитик, НЕ продавец

**Результат:** Отчёты выглядят красиво, LLM отвечает правильно.

---

## 🔮 ПРОГНОЗ И РИСКИ

### Если продолжить текущим путём (без изменений)

**Прогноз:** Проект останется в подвешенном состоянии.
- meAI framework будет занимать место, но не использоваться
- Pipeline v6 будет улучшаться инкрементально, но без чистки
- Технический долг будет расти
- Доверие Михаила не восстановится

**Вероятность MVP через 1 месяц:** 30-40%

### Если следовать плану rewrite-v2/

**Прогноз:** Реальный шанс достичь MVP.
- Чистая архитектура (4 контейнера, минимум кода)
- Понятный pipeline (один путь URL → отчёт)
- Красивые отчёты (canonical дизайн)
- Восстановление доверия через процесс

**Вероятность MVP через 3 недели:** 70-80%

### Главный риск

**Риск #1: Снова начать добавлять features**

Pipeline v5 работает. Соблазн: "А давай ещё добавим X, Y, Z!"

**Митигация:** Держать фокус на 10 критериях MVP из 07-SUCCESS-CRITERIA.md. 
Всё остальное — в backlog ПОСЛЕ MVP.

**Риск #2: Недооценить время на дизайн-систему**

Canonical дизайн сложный: dual theme, glassmorphism, бейджи, анимации.

**Митигация:** 
- Использовать design-showcase-dual-theme.html как reference
- Copy-paste CSS, не изобретать заново
- Smoke test на 5 браузерах

**Риск #3: LLM не подчиняется промпту**

Даже с жёстким PRESALE промптом LLM может вызывать не те tools.

**Митигация:**
- Удалить из registry tools, которые LLM НЕ должен вызывать
- Тестировать на 10+ разных URLs
- Если не работает — упростить ещё сильнее

---

## 📋 ACTIONABLE NEXT STEPS

### Для Михаила (решения)

**Вопрос #1: Что делать с meAI framework?**
- [ ] Option A: Архивировать (переместить в `/archive/meai-research/`)
- [ ] Option B: Удалить полностью
- [ ] Option C: Продолжить развивать (НЕ рекомендую)

**Вопрос #2: Следовать ли плану rewrite-v2/?**
- [ ] Да, следовать плану 06-IMPLEMENTATION-PLAN.md
- [ ] Нет, другой подход (какой?)

**Вопрос #3: Приоритет: скорость или качество?**
- [ ] Скорость: MVP за 2 недели, но с компромиссами
- [ ] Качество: MVP за 3-4 недели, но без технического долга
- [ ] Баланс: 2.5 недели, критичное качество

### Для разработчика (immediate actions)

**Сегодня (день 0):**
1. Прочитать полностью все 8 документов rewrite-v2/
2. Создать git branch `aim-v2-clean`
3. Backup сервера (полный)
4. Зафиксировать текущие working scout URLs для regression

**День 1-2: Quick wins**
1. Синхронизировать SOUL.md
2. Удалить zombie код
3. Остановить лишние контейнеры
4. Сократить tools registry

**День 3-9: Pipeline v2**
1. Рефакторинг engine.py
2. Smoke tests всех 13 фаз
3. Стабилизация

**День 10-15: Дизайн-система**
1. build_report.py
2. Подключить к pipeline
3. Миграция старых отчётов

**День 16-20: Финализация MVP**
1. UX polish
2. SOUL.md + PRESALE промпт
3. Финальный smoke test с Михаилом

---

## 🎯 SUCCESS METRICS

### Критерии "MVP достигнут"

Все 10 пунктов из 07-SUCCESS-CRITERIA.md:

1. ✅ End-to-end pipeline работает (13 фаз)
2. ✅ Отчёт публикуется на iamaim.ru
3. ✅ Canonical дизайн применён (dual theme, glass, бейджи)
4. ✅ Standalone HTML (без WordPress header/footer)
5. ✅ Финальные 3 сообщения Hermes (правильный тон)
6. ✅ Приватность (noindex, не в sitemap, REST API 403)
7. ✅ Время pipeline ≤ 8 минут
8. ✅ Lighthouse score ≥ 85
9. ✅ Responsive (mobile, tablet, desktop)
10. ✅ Браузерная совместимость (Chrome, Safari, Firefox, Edge)

**И главное:** Михаил говорит:
> "Да, окей, наконец-то мы хоть что-то получили."

---

## 💬 ЗАКЛЮЧЕНИЕ

### Текущее состояние (одной фразой)

**Pipeline v5 работает, но проект находится в архитектурном кризисе между грандиозным видением (meAI framework) и реальными потребностями (простой pipeline URL → отчёт).**

### Главный вывод

**Путь к MVP = упрощение, не усложнение.**

- Архивировать meAI framework как исследование
- Сфокусироваться на AIM production
- Следовать плану rewrite-v2/
- Восстановить доверие через процесс и результаты

### Главная рекомендация

**Начать с Этапа 0 и 1 из плана (3-5 дней):**
- Backup + branching
- Удаление zombie кода
- Синхронизация SOUL.md
- Сокращение tools

**После этого — оценить прогресс и решить продолжать или pivot.**

Если за 5 дней проект станет понятнее, чище, стабильнее — продолжать.
Если нет — нужна более радикальная перемена подхода.

---

**Дата:** 6 июля 2026, 13:26 GMT+3
**Исследование:** Завершено
**Статус:** Готово к обсуждению с Михаилом

---

## 📎 APPENDIX

### Ссылки на ключевые документы

- `rewrite-v2/00-MASTER.md` — точка входа в rewrite
- `rewrite-v2/01-PROJECT-ESSENCE.md` — суть продукта
- `rewrite-v2/02-CURRENT-STATE.md` — детальный аудит
- `rewrite-v2/03-TARGET-ARCHITECTURE.md` — целевая архитектура
- `rewrite-v2/06-IMPLEMENTATION-PLAN.md` — план работ
- `rewrite-v2/07-SUCCESS-CRITERIA.md` — критерии MVP
- `CLAUDE.md` — правила работы (TRUST LEVEL: ZERO)
- `.current-task` — текущий статус (Pipeline v5 working)

### Контакты

- **Владелец:** Михаил Елисеев
- **Production:** ssh aim (78.17.128.169)
- **Site:** https://iamaim.ru
- **Repo:** /Users/mikhaileliseev/Desktop/Dev/meAI_1

