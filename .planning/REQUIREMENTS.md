# REQUIREMENTS.md — Гермес v2

**Дата:** 2026-07-14
**Источник:** спека `docs/superpowers/specs/2026-07-14-hermes-interactive-redesign-design.md`

---

## v1 Requirements

### Контейнер и инфраструктура (INFRA)
- [ ] **INFRA-01**: Новый Docker-сервис `hermes-v2` описан в `docker-compose.yml` (образ `aim-hermes-v2:latest`, expose 8000, сети aim-network, depends_on aim-app healthy)
- [ ] **INFRA-02**: `Dockerfile` для hermes-v2: Python 3.11 + зависимости из requirements.txt (openai, fastapi, httpx, playwright, apify-client, pymysql, ...)
- [ ] **INFRA-03**: Контейнер успешно проходит healthcheck (`GET /health` → 200)
- [ ] **INFRA-04**: Контейнер может обращаться к `aim-app:8000` (docker network) — проверка реальным запросом к `/api/competitors/find`
- [ ] **INFRA-05**: env-переменные (OMNIROUTE_URL, PERPLEXITY_API_KEY, APIFY_API_TOKEN, FIRECRAWL_API_KEY, WP_DB_*) передаются корректно

### Диалоговый сервер (DIALOG)
- [ ] **DIALOG-01**: `POST /api/chat/stream` — SSE-эндпоинт, совместимый с Theme-чатом (формат событий `text-delta`, `finish`, `error`, `phase-progress`, `report-ready`)
- [ ] **DIALOG-02**: Модель `deepseek-chat` через Z.AI-шлюз с нативным tool-calling (OpenAI `tools=` / `tool_calls`)
- [ ] **DIALOG-03**: Системный промпт задаёт политику «база → кнопки → по запросу» + питч услуг AIM
- [ ] **DIALOG-04**: История диалога хранится в SQLite (как в старом hermes), keyed by session_id
- [ ] **DIALOG-05**: Per-session состояние (не глобальная очередь, как баг в старом `main.py:47`)

### Инструменты (TOOLS)
- [ ] **TOOLS-01**: `quick_overview` (база) — глубокий поиск Perplexity, перенесён из старого кода
- [ ] **TOOLS-02**: `find_competitors` (база) — прокси к `aim-app:8000/api/competitors/find`, count=3
- [ ] **TOOLS-03**: `run_ci_analysis` (кнопка) — прокси к `aim-app:8000/api/competitors/analyze`
- [ ] **TOOLS-04**: `run_smi_mentions` (кнопка) — перенесён (Perplexity напрямую)
- [ ] **TOOLS-05**: `run_review_platforms` (кнопка) — перенесён (Perplexity напрямую)
- [ ] **TOOLS-06**: `run_instagram_content` (кнопка) — перенесён (Apify напрямую)
- [ ] **TOOLS-07**: `run_seo_audit` (кнопка) — прокси к `aim-app:8000/api/seo/audit`
- [ ] **TOOLS-08**: `run_pagespeed` (кнопка) — перенесён (Playwright локально)
- [ ] **TOOLS-09**: `run_ads_intelligence` (кнопка) — перенесён (Firecrawl напрямую)
- [ ] **TOOLS-10**: `generate_html_report` (финал) — перенесён (WordPress DB)
- [ ] **TOOLS-11**: Каждый tool имеет OpenAI function-schema с полем «когда вызывать» (when to call)
- [ ] **TOOLS-12**: Модель не вызывает `find_competitors` более одного раза за сессию (ограничение в промпте + логике)

### Чат-фронтенд (CHAT)
- [ ] **CHAT-01**: Новое SSE-событие `suggestions` с массивом кнопок `{label, tool}`
- [ ] **CHAT-02**: `useStreamChat.js` обрабатывает `suggestions` → `setActiveButtons`
- [ ] **CHAT-03**: `ChatBubble.jsx` рендерит кнопки (`.chat-btn-ghost` чипы) под сообщением ассистента
- [ ] **CHAT-04**: Клик по кнопке шлёт `label` текстом в `/api/chat/stream` (не structured payload)
- [ ] **CHAT-05**: После базы показывается 2-4 релевантные кнопки (адаптивно: плохой сайт → «тех.аудит», плохие отзывы → «анализ отзывов»)

### Базовый сценарий (FLOW)
- [ ] **FLOW-01**: Клиент шлёт URL → Гермес вызывает `quick_overview` + `find_competitors` (по одному разу)
- [ ] **FLOW-02**: Базовый ответ ≤4 минуты (рынок + top-3 конкурента по имени + rating + match_reason)
- [ ] **FLOW-03**: После базы — кнопки + свободный ввод текста
- [ ] **FLOW-04**: В конце базового ответа — короткий питч услуг AIM
- [ ] **FLOW-05**: По запросу клиента (кнопка/текст) — вызов нужного инструмента, ответ выжимкой
- [ ] **FLOW-06**: «Собрать отчёт» → `generate_html_report` читает session_archive → HTML-отчёт

### Отчёты и архив (REPORT)
- [ ] **REPORT-01**: Каждый tool-result пишется в `/opt/hermes-v2-data/sessions-archive/{hash}/`
- [ ] **REPORT-02**: `generate_html_report` публикует в WordPress (как старый) и возвращает URL
- [ ] **REPORT-03**: Отдельный volume `/opt/hermes-v2-data` (не мешаем со старым)

### Деплой и откат (DEPLOY)
- [ ] **DEPLOY-01**: Код разрабатывается локально в `AIM/hermes-v2/`
- [ ] **DEPLOY-02**: `rsync` на сервер в `/opt/aim/AIM/hermes-v2/`
- [ ] **DEPLOY-03**: `docker compose build hermes-v2 && docker compose up -d hermes-v2` работает
- [ ] **DEPLOY-04**: nginx переключаем `aim-hermes:8000` → `aim-hermes-v2:8000` (одна строка)
- [ ] **DEPLOY-05**: Старый `aim-hermes` выключен, но доступен для отката

## v2 Requirements (отложено)
- [ ] Миграция Telegram-бота на v2
- [ ] Удаление старого `aim-hermes` через неделю стабильности
- [ ] Перенос скиллов в v2

## Out of Scope
- Next.js-чат `/chat-test` — тестовый, не трогаем
- Telegram-бот миграция — отдельная задача
- Удаление старого контейнера — только после недели стабильности

## User Stories
- Как клиент, я присылаю сайт → быстро (≤4 мин) понимаю своё место на рынке + конкурентов
- Как клиент, я выбираю, что копать глубже (кнопками или текстом), а не жду 17 минут
- Как клиент, я получаю питч услуг AIM в конце базы
- Как клиент, я могу собрать всё в отчёт, когда насытился

## Acceptance Criteria (общие)
- Базовый ответ ≤4 мин (vs 17 мин сейчас)
- Кнопки работают (запускают инструменты)
- Свободный текст корректно триггерит тулзы
- Отчёт генерируется из данных сессии
- Откат на старый контейнер возможен в любой момент

## Traceability
(заполняется при создании roadmap)

---

## Phase 7 Requirements — V2 Competitor Pipeline: точность данных

### COMP-01: Резолв ИНН клиента
**User Story:** Как клиент, я хочу, чтобы мои конкуренты отбирались по реальному масштабу моего бизнеса, а не по оценке.
**Acceptance Criteria:**
- ИНН клиента резолвится через скрапинг сайта (footer/privacy/оферта) → bo.nalog search по названию → Perplexity fallback
- Клиентская выручка берётся из ФНС (bo.nalog gainSum), не из оценки
- Коридор отбора конкурентов 0.3×–3× от РЕАЛЬНОЙ выручки работает
- Тест IPHK: client_revenue из ФНС (миллиарды), не 80М оценка

### COMP-02: Instagram-колонка
**User Story:** Как клиент, я хочу видеть Instagram-аудиторию конкурентов в таблице.
**Acceptance Criteria:**
- Для топ-5 финальных конкурентов: скрапинг сайта → IG ссылка → Apify instagram-profile-scraper → followersCount
- instagram_followers заполнен для ≥3 из 5 конкурентов
- Instagram enrichment только для финального топ-5 (скорость)

### COMP-03: Число хирургов (дообогащение)
**User Story:** Как клиент, я хочу видеть масштаб команды конкурентов.
**Acceptance Criteria:**
- surgeons_count заполнен для ≥3 из 5 топ-конкурентов
- Источники: Perplexity оценка (из запроса конкурентов) → скрапинг раздела «Врачи/Команда» как fallback
- Если данные недоступны — null с пометкой в match_reason

### COMP-04: Нормализация брендов
**User Story:** Как клиент, я хочу видеть реальных операторов рынка, а не отделения.
**Acceptance Criteria:**
- Перед резолвом бренд → ИНН: удаление гео-привязок («на Ленинском», «на ул. X», «в Орловском переулке»)
- «Медиал на Ленинском проспекте» → «Медиал» → bo.nalog находит головное юрлицо
- Регулярные выражения для паттернов: «на <улица>», «в <переулок>», «<адрес>», «№N»
- Тест: после нормализации Perplexity-бренды резолвятся к тем же юрлицам что и clean-бренды

---

## Phase 8 Requirements — V2 Pipeline: стабильность и покрытие

### STAB-01: Retry при пустом Perplexity
**User Story:** Как клиент, я хочу стабильный результат — не пустой ответ из-за случайного сбоя LLM.
**Acceptance Criteria:**
- Если Perplexity вернул 0 брендов → retry с переформулированным промптом (до 2 попыток)
- Если после retry всё ещё 0 → fallback на SearXNG-only discovery
- Лог: `perplexity_retry: attempt=2 reason=empty_result`
- Тест: 3 последовательных запуска IPHK → каждый раз ≥5 конкурентов

### STAB-02: Overfetch кандидатов (12→5)
**User Story:** Как клиент, я хочу 5 конкурентов даже если часть брендов не резолвится.
**Acceptance Criteria:**
- Perplexity запрашивает 12 брендов (не 10)
- SearXNG тоже отдаёт больше (limit=20)
- После резолва и дедупа → топ-5 (текущий count)
- Если резолвится <5 → расширить коридор ещё больше

### STAB-03: Кэш bo.nalog запросов
**User Story:** Как клиент, я хочу быстрый повторный анализ той же клиники.
**Acceptance Criteria:**
- bo.nalog search и financials кешируются (TTL 1 час, уже есть в BfoNalogClient)
- Повторный запрос IPHK → кэш-хиты → <5с (вместо 15с)
- Лог: `nalog_cache_hit: search:iphk` на повторных запросах

### STAB-04: Дедуп сетей (многоточные клиники)
**User Story:** Как клиент, я не хочу видеть 2 записи одной сети (СМ-Клиника на двух адресах).
**Acceptance Criteria:**
- Дедуп по ИНН уже работает (Phase 7), но нужно проверить что СМ-Клиника Волгоградский и Сенежская (один ИНН 2367011265) → одна запись
- Если ИНН отличается но бренд один (разные юрлица одной сети) → оставить обе, но отметить в match_reason
- Тест: результат не содержит двух записей с одинаковым ИНН


