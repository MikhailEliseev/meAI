# meAI Assistant

## Session Recovery (READ THIS FIRST!)

**⚠️ ВАЖНО: Компакт-саммари может ВРАТЬ!**
После компакта сессии саммари смешивает задачи из разных сессий и может выставить неправильные приоритеты. НЕ доверяй тегам CRITICAL в саммари слепо. SESSION.md — твой единственный надёжный источник.

**При обрыве сессии (СТРОГИЙ ПОРЯДОК):**

1. **Читай `SESSION.md`** — секция «Текущий фокус» = что ты делаешь ПРЯМО СЕЙЧАС. Это ИСТИНА.
2. **Читай `.current-task`** — одна строка, дубль SESSION.md, иммунна к компакту
3. **Если SESSION.md и компакт-саммари противоречат друг другу** — верь SESSION.md, игнорируй саммари
4. **CHECKPOINTS.md** — только если нужна историческая справка (85KB, не для быстрого восстановления)
5. **Auto-memory загружается автоматически** — знания о проекте

**Цель:** Восстановление контекста за < 30 секунд

**ЖЁСТКОЕ ПРАВИЛО:** Обновляй `SESSION.md` и `.current-task` при КАЖДОМ переходе к новой задаче. Без исключений.

---

## Project Overview

**meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru).

```
meAI/                           # Command Center
├── src/meai/                   # Framework (core, agents, events, memory, storage)
├── AIM/                        # Agency (приложение)
│   ├── src/aim/                # magisters/, subagents/, services/
│   ├── hermes/                 # Hermes AI agent (FastAPI + hermes-agent)
│   ├── obsidian/               # Vaults агентов (LLM Wiki)
│   └── frontend/               # Next.js landing
├── obsidian/architect/         # Твой vault
└── SESSION.md                  # Текущая работа
```

**User Role:** Medical marketer building AI-first agency
**Stack:** Python 3.11+, FastAPI, PostgreSQL, Redis, Docker, Next.js
**Deploy:** Docker на Polish server 78.17.128.169 (`ssh aim`) — см. auto-memory `deploy-target.md`

---

## Development Philosophy

### Deep & Correct
Делаем всё глубоко и правильно, без спешки. Полная автономность компонентов. Каждый агент — код с логикой, не просто vault. Никаких заглушек.

### Quality Over Speed
Качество важнее скорости. Поверхностный анализ = катастрофа. Если есть выбор между "быстро" и "качественно" → всегда качественно.

### Complete Before Next
Доводим до 100% перед переходом к следующей задаче. Не предлагаем варианты, пока текущая не завершена. Запрещено оставлять stubs "на потом".

### Mock Data Rule
Никаких mock данных в production коде. Агент запрашивает у пользователя или получает реальные данные из источника. Исключения: unit тесты (только в `tests/`).

### Large File Write Rule
Write tool имеет ограничение ~20-30 KB. Файлы 200+ строк разбивай на части: Write для первых 150-200 строк, Bash append для остального.

### Spec Writer Rule
При создании спецификаций агентов всегда используй spec-writer skill (`/spec-writer`). Skill делает deep research и даёт больше деталей, чем твои знания.

### Teacher Agent Rule

**Teacher Agent — Chief Learning Officer системы.** Его задача: следить за источниками знаний и обучать агентов, чтобы система не устаревала.

**ЗАПРЕЩЕНО:**
- ❌ Copy-paste одинаковых паттернов во все субагенты
- ❌ «Обучение» без deep research для каждого субагента
- ❌ Общие решения (Circuit Breaker, Retry, Rate Limiting) для всех
- ❌ Пропускать GitHub search специализированных решений

**ОБЯЗАТЕЛЬНО для каждого субагента:**
- ✅ Индивидуальное deep research
- ✅ GitHub search с правильными запросами (например: «yandex direct api python» для Ads)
- ✅ Клонирование и изучение кода из топовых репо
- ✅ Извлечение специфичных для домена паттернов

**Цикл обучения (каждые 2-4 недели):**
1. Проверить дату последнего обучения субагента
2. GitHub Search: новые топовые репо, обновления существующих
3. Deep Research: новые best practices, API updates
4. Gap Analysis: что есть в топовых решениях, но нет у нас
5. Learning Report с приоритетами: 🔴 CRITICAL (внедрить немедленно), 🟡 HIGH (запланировать), 🟢 LOW (backlog)

**Метрики:** Coverage (% субагентов проверено), Freshness (знания < 4 недель), Impact (% рекомендаций внедрено)

---

## Architecture: LLM-First Tool Orchestration

AIM — это набор инструментов (tools), которые LLM (Hermes) вызывает по своему усмотрению. Никакой хардкод-оркестрации. Модель решает, что и когда вызывать.

### Как это работает
1. Клиент пишет в чат на iamaim.ru
2. Hermes (LLM) получает сообщение + полный список инструментов (17 штук)
3. LLM сама решает, какой инструмент вызвать, в каком порядке
4. Результат инструмента возвращается LLM
5. LLM формирует ответ клиенту

### Смена модели
Меняется одна переменная: `LLM_MODEL` в `.env`. Всё остальное работает без изменений.

### Инструменты Hermes (17 штук)

**aim-operations (15 tools):**
| Tool | Что делает | Timeout |
|------|-----------|---------|
| `run_prescan` | Запускает prescan сайта (3 стадии) | 300s |
| `find_competitors` | Поиск конкурентов (Apify) | 600s |
| `present_competitors` | Форматирует конкурентов для клиента | 30s |
| `run_ci_analysis` | Глубокий анализ конкурентов | 300s |
| `run_seo_audit` | SEO-аудит | 120s |
| `run_content_analysis` | Контент-анализ | 120s |
| `run_ads_report` | Отчёт по рекламе | 120s |
| `show_project_status` | Статус проекта | 10s |
| `collect_contact` | Сбор контакта (имя, телефон, email) | 10s |
| `qualify_lead` | Квалификация лида | 10s |
| `escalate_to_manager` | Передача менеджеру | 10s |
| `show_all_leads` | Все лиды (для ADMIN) | 10s |
| `get_lead_pipeline` | Воронка лидов | 10s |
| `update_knowledge` | Запись знаний | 10s |
| `find_company_financials` | Финансы компании (nalog.ru) | 60s |

**hermes-debug (11 tools):**
`shell_exec`, `file_read`, `file_write`, `api_debug`, `web_fetch`, `web_search`, `firecrawl_web`, `bitrix_scrape`, `browser_screenshot`, `call_api`, `restart_myself`

### Что НЕ использовать (deprecated)
- **Магистры** (SEO, Content, Ads, Analytics) — архитектура избыточна, Hermes справляется сам
- **CI Orchestrator** (23 агента, 16 фаз) — заменён прямым вызовом инструментов
- **EventBus** — не используется в продакшене
- **Obsidian vaults для агентов** (кроме teacher и architect)
- **`.planning/`** — исторические планы, не актуальны

### AIM Agency Context

- **CRITICAL: Работаем ТОЛЬКО в коммерческой медицине.**
  - Никаких государственных учреждений (ГАУЗ, ГБУЗ, ГУЗ, МУЗ, МБУЗ)
  - Только: ООО, АО, ЗАО, ИП — частные коммерческие клиники
  - Фильтрация: `competitor_matcher.py:_is_state_healthcare()`
- AI-first approach, domain: iamaim.ru
- Российский рынок: Яндекс.Директ, Яндекс.Метрика, ФЗ-152 (не HIPAA/GDPR)
- Платёжки: ЮKassa/CloudPayments (не Stripe)
- Западные технические паттерны (AI, архитектура, CI/CD) применяются без изменений

---

## Design System — Dual Theme (КАНОНИЧЕСКИЙ РЕФЕРЕНС)

**Файл:** `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html`
**URL:** https://iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html
**CSS-переменные:** `AIM/wordpress-core/wp-content/themes/aim-theme/theme.css`

Это ЕДИНСТВЕННЫЙ источник истины для дизайна AIM. При любой работе с фронтендом, вёрсткой, стилями — сверяться с этим файлом.

### Две темы

| | Light | Dark |
|---|-------|------|
| Фон | `#ffffff` | `#0d0d0d` |
| Текст | `#1A1A1A` | `#f5f0e8` |
| Акцент | `#1A1A1A` (чёрный) | `#c9a96e` (Art Deco gold) |
| Бордер | `#E0E0E0` | `rgba(201,169,110,0.18)` |
| Glass bg | `rgba(255,255,255,0.85)` | `rgba(13,13,13,0.85)` |

### Типографика
- **Заголовки:** Playfair Display, weight 400, letter-spacing -0.01em
- **Тело:** Jost, 16px, line-height 1.7
- **Логотип:** "AIM", Playfair Display 400, 1.875rem, letter-spacing -0.02em

### Шапка (Header)
- `position: fixed`, `backdrop-filter: blur(20px) saturate(1.4)`
- Glass-фон (`var(--glass-bg)`)
- Бордер снизу: `1px solid var(--border)` (в тёмной теме — золотой оттенок)
- Таглайн "AI-first маркетинг в медицине" — центрирован абсолютно, Jost 0.75rem uppercase
- Theme toggle: круглый, 28×28px, sun/moon SVG-иконки

### Ключевые компоненты
- **Glass cards:** `backdrop-filter: blur(20px) saturate(1.4)`, дышащая анимация `card-breathe`
- **Buttons:** uppercase, letter-spacing 0.1em, border-radius 1px (острые углы)
- **Metric tags:** 5 цветов (success green, warning yellow, danger red, info blue, neutral gray)
- **Card grids:** 1px gap, hover lift-эффект
- **Water ripples:** фон в светлой теме (скрыты в тёмной)

### Переключение темы
- `localStorage` ключ: `aim-theme`
- Атрибут: `data-theme="light"|"dark"` на `<html>`
- Sun SVG видна в тёмной теме, Moon SVG — в светлой

---

## Project Structure

```
src/meai/           # Framework (переиспользуемый)
├── core/           # Architect, Orchestrator, Decision Maker
├── agents/         # Operator, BaseMagister, BaseAgent
├── events/         # Event Bus, Event Store
├── memory/         # Obsidian integration
└── storage/        # Database

AIM/                # Application (агентство)
├── src/aim/        # magisters/, subagents/, services/
├── hermes/         # Hermes AI agent
├── obsidian/       # Vaults агентов
├── frontend/       # Next.js
└── docker-compose.yml
```

Импорты: `from meai.xxx` (framework), `from aim.xxx` (agency). Работаешь из корня `/Users/mikhaileliseev/Desktop/Dev/meAI`.

---

## Hermes Backup

**Локальный архив:** `hermes-backup-20260618/` в корне проекта
- `hermes_full_20260618_213733.tar.gz` — 417 KB, полный бекап Hermes (18.06.2026)
- Содержит: `.env` (все API-ключи), `config.yaml`, скиллы (`client-onboarding-pipeline` v6.0, `ui-ux-pro-max`), скрипты (`generate-report.py`, `seo-audit.py`, `rotate_keys.py`), ключи (`key_pool.json`, `rotation_state.json`), память (`MEMORY.md`, `USER.md`)
- На сервере: `/opt/hermes-data/backups/hermes_full_20260618_213733.tar.gz`

---

## Быстрый старт для Hermes

Прочитай `/opt/data/AIM_HANDBOOK.md` — там всё про инструменты, архитектуру, пресейл, competitors, и технические детали.
