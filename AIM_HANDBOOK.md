# AIM System Handbook for Hermes

> Всё, что работает. Без архитектурного мусора.
> Последнее обновление: 2026-06-04

---

## 1. Архитектура (6 контейнеров)

```
internet → nginx (80/443) → frontend:3099  (Next.js)
                           → app:8000      (FastAPI — основной backend)
                           → hermes:8000   (Hermes AI agent)
                postgres:5432
                redis:6379
```

**nginx** маршрутизирует по путям:
- `/api/chat/` → frontend:3099 (SSE streaming)
- `/api/` → app:8000 (все AIM API)
- `/telegram/webhook` → hermes:8000
- `/health`, `/metrics` → app:8000
- всё остальное → frontend:3099

Все контейнеры в одной Docker-сети `aim-network`. Запуск: `docker compose -f AIM/docker-compose.yml up -d`

---

## 2. Prescan — сбор данных о клинике

**Endpoint:** `POST /api/presale/prescan-staged` (на app:8000)

Три стадии с прогресс-коллбэками:

| Стадия | Что собирает | Время |
|--------|-------------|-------|
| Stage 1 | Специализация, город, ИНН/ОГРН, выручка (nalog.ru), юрлицо (DaData) | 20-30s |
| Stage 2 | Лицензии Росздравнадзора, учредители, SEO, отзывы (Яндекс/2ГИС/ProDoctors), соцсети | 40-60s |
| Stage 3 | Конкуренты рядом, многолетняя выручка, контент-аудит | 60-90+s |

**Результат кешируется** в `company_profiles` (PostgreSQL). Повторный запрос с `?cached=true` возвращает мгновенно.

**Ключевой параметр:** `url` — сайт клиники (с http:// или без)

**Файлы:**
- `AIM/src/aim/api/presale.py` — API endpoint
- `AIM/src/aim/services/prescan_orchestrator.py` — оркестратор стадий

---

## 3. Competitor Discovery — поиск конкурентов

**Endpoint:** `POST /api/competitors/find` (на app:8000)

**Пайплайн:**
1. Извлечение профиля клиники (специализация, город) из URL
2. Запрос выручки клиники на bo.nalog.gov.ru (ГИР БО) по ИНН
3. Apify Google Maps — поиск конкурентов по специализации + городу
4. Фильтрация: убрать саму клинику, госучреждения (ГАУЗ/ГБУЗ/МУЗ)
5. Извлечение ИНН с сайтов конкурентов (статический HTTP + Playwright)
6. Обогащение финансовыми данными из bo.nalog.gov.ru (ФНС)
7. Скоринг по 7 факторам: выручка (0.22), локация (0.15), качество данных (0.15), чистота специализации (0.13), популярность (0.13), услуги (0.12), видимость (0.10)
8. Возврат top-N с человекочитаемыми `match_reason`

**Мегаполисы** (Москва, СПб): радиус расширяется с 7 км до 25 км.

**Таймаут:** 600 секунд (Apify долгий)

**Файлы:**
- `AIM/src/aim/api/competitors.py` — API endpoint
- `AIM/src/aim/services/competitor_matcher.py` — вся логика

---

## 4. P5-FIX — Presale Flow

**Логика в `hermes/app/agent_wrapper.py`:**

Когда клиент в чате отправляет URL (новый лид):

1. **Сброс сессии** — генерируется новый `session_id`, старый удаляется из кеша
2. **Принудительный prescan** — `_force_prescan(url)` вызывает `/api/presale/prescan-staged` синхронно (блокировка 60-120s)
3. **Инъекция результата** — prescan-результат вставляется в историю как выполненный `tool_call` (`force_prescan_1`)
4. **Ограничение инструментов** — агент создаётся ТОЛЬКО с `hermes-debug` (read-only). `find_competitors` физически недоступен на первом ходу
5. **Нарратив** — агент получает инструкцию «расскажи историю про бизнес, не список цифр»

На втором ходу — полные инструменты (`aim-operations`), включая `find_competitors`.

**Ключевое правило:** на первом ходу presale НИКОГДА не искать конкурентов. Только показать prescan.

---

## 5. Инструменты Hermes (tools)

### aim-operations (15 tools)
| Tool | Что делает | Timeout |
|------|-----------|---------|
| `run_prescan` | Запускает prescan сайта | 300s |
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

### hermes-debug (read-only, 11 tools)
`shell_exec`, `file_read`, `file_write`, `api_debug`, `web_fetch`, `web_search`, `firecrawl_web`, `bitrix_scrape`, `browser_screenshot`, `call_api`, `restart_myself`

**Файлы:**
- `AIM/hermes/app/tools/__init__.py` — регистрация всех инструментов
- `AIM/hermes/app/tools/run_prescan.py` — prescan tool
- `AIM/hermes/app/tools/find_competitors.py` — competitor tool

---

## 6. Режимы работы (Agent Modes)

| Mode | Для кого | Какие инструменты |
|------|---------|------------------|
| `PRESALE` | Потенциальный клиент в чате | aim-operations + hermes-debug |
| `ACTIVE` | Действующий клиент | aim-operations + hermes-debug |
| `ADMIN` | Михаил (основатель) | ВСЕ инструменты, полный доступ |
| `SALES_ADMIN` | Виртуальный админ клиники | aim-operations (ограниченно) |

**Промпты** для каждого режима задаются в `agent_wrapper.py:get_mode_prompt()`.

---

## 7. SOUL.md — Личность агента

**Файл:** `AIM/hermes/skills/aim/SOUL.md` (870 строк)

Определяет:
- **Идентичность:** AI-интерфейс агентства AIM, НЕ Михаил
- **7-шаговый PRESALE-диалог:** URL → prescan → конкуренты → CI → КП
- **Цены:** SEO-аудит (70 000 ₽), Контент-анализ (50 000 ₽), CI-анализ конкурентов (145 000 ₽), Полное КП (290 000 ₽)
- **KPI:** Conversion 25-40%, Churn 5-10%, MRR target
- **33 правила коммерческих предложений** (из реального фидбека клиентов)

---

## 8. База знаний

### Teacher Reports (обучающие материалы)
- `AIM/hermes/knowledge/learnings/commercial-proposal-masterclass.md` — урок создания КП на примере psyholog48.ru
- `AIM/hermes/knowledge/learnings/teacher-cp-quality-2026-06-03.md` — исследование framework'ов качества КП

### Auto-learnings (самообучение)
Агент автоматически записывает обучения в `/opt/data/memories/learnings/` после каждого ADMIN-сеанса с использованием инструментов.

**Файлы:**
- `AIM/hermes/knowledge/vault.py` — HermesKnowledgeVault (поиск по знаниям)

---

## 9. Важные технические детали

### Docker Network
- Все сервисы общаются по внутренним именам: `app`, `hermes`, `frontend`, `postgres`, `redis`
- nginx использует runtime DNS resolution: `resolver 127.0.0.11`

### SSL
- Продакшен: Let's Encrypt (certbot)
- Локальная разработка: self-signed сертификаты

### Таймауты
- nginx proxy_read_timeout: 600s для `/api/chat/`
- Hermes agent timeout: 300s
- SSE deadline: 420s (7 минут)
- find_competitors: 600s

### Базы данных
- PostgreSQL: компания, лиды, результаты prescan
- Redis: кеш, очереди
- SQLite: сессии Hermes-агента (`/opt/data/state.db`)

### OmniRoute
LLM-прокси: `http://omniroute:20128/v1`
Модель по умолчанию: `ds/deepseek-v4-pro`

---

## 10. Файловая структура (только важное)

```
AIM/
├── docker-compose.yml          # Все сервисы
├── Dockerfile                  # Backend (FastAPI)
├── .env.production             # Продакшен-переменные
├── src/aim/
│   ├── main.py                 # FastAPI приложение
│   ├── api/
│   │   ├── presale.py          # Prescan API
│   │   └── competitors.py      # Competitor API
│   └── services/
│       ├── prescan_orchestrator.py
│       └── competitor_matcher.py
├── hermes/
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py             # Hermes FastAPI (SSE, webhook)
│   │   ├── agent_wrapper.py    # P5-FIX, session management
│   │   └── tools/              # 17 инструментов
│   ├── skills/aim/SOUL.md      # Личность агента
│   └── knowledge/
│       ├── vault.py            # Knowledge vault
│       └── learnings/          # Teacher reports
├── frontend/
│   ├── Dockerfile
│   ├── app/                    # Next.js App Router
│   └── hooks/useStreamChat.ts  # SSE streaming client
└── deploy/nginx/iamaim.conf    # Nginx config
```

---

## 11. Что НЕ использовать (устарело/не работает)

- **Магистры** (SEO, Content, Ads, Analytics) — архитектура оказалась избыточной, Hermes справляется сам
- **CI Orchestrator** (23 агента, 16 фаз) — заменён прямым вызовом инструментов
- **EventBus** — не используется в продакшене
- **Obsidian vaults для 17 агентов** — работают только teacher и architect
- **`.planning/`** — исторические планы, не актуальны
