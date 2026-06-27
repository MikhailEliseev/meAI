# Phase 9: Chat Pro — Website Chat UX Overhaul - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Переработка чата iamaim.ru для превращения его в wow-эффект sales инструмент с живым стримингом работы Hermes, промежуточными комментариями-инсайтами, финальной страницей отчёта, нативным сбором контактов и ассистентом продаж услуг AIM.

**Внутри scope:**
- Real-time прогресс-стриминг: отображение текущей стадии работы Hermes (как в Telegram — floating status)
- Wow-commentary: LLM генерирует бизнес-инсайты после каждого инструмента («Ого, ваша главная страница не оптимизирована», «У конкурента доктор с 500K подписчиков»)
- Фиксированная страница отчёта: HTML-рендеринг по каноническому шаблону из design-showcase-dual-theme.html (текущий generate_html_report.py ломает вёрстку)
- Нативный сбор контакта: диалоговый флоу в чате без форм
- Ассистент продаж услуг AIM: LLM знает services.md, матчит находки с услугами, рекомендует релевантные решения с ценами

**Вне scope:**
- Редизайн существующей визуальной темы (dual theme остаётся)
- Изменение backend архитектуры Hermes (SSE streaming уже работает)
- Новые инструменты для Hermes (Phase 3-6 закрыты)
- Интеграция с другими каналами (Telegram, WhatsApp)
- A/B тестирование разных вариантов UX

</domain>

<decisions>
## Implementation Decisions

### Progress Display Pattern

- **D-01:** Telegram-style floating status — одно сообщение обновляется по мере прогресса, не множество отдельных сообщений
- **D-02:** Визуальная иерархия: Stage (крупно, жирным) → Message (детали, обычным шрифтом) → Competitor (если есть, мелким шрифтом)
- **D-03:** Backend уже отправляет `{"type": "tool-progress", "stage": "...", "message": "...", "competitor": "..."}` через SSE — frontend должен обрабатывать эти события
- **D-04:** Используется `push_tool_progress()` из `AIM/hermes/app/main.py:87-130` (thread-safe dispatcher)
- **D-05:** Визуальные индикаторы: spinner/loading icon во время работы, галочка при завершении стадии
- **D-06:** Прогресс показывается в нижней части чата, не блокирует прокрутку истории

### Wow-Commentary Logic

- **D-07:** LLM генерирует wow-комментарии после каждого успешного вызова инструмента, используя собранные данные
- **D-08:** Новый SSE event type: `{"type": "wow-comment", "insight": "...", "severity": "info|warning|critical"}`
- **D-09:** Бизнес-язык (INT-03 из Phase 5): «каждая секунда задержки теряет пациентов», а не «LCP 7.3s»
- **D-10:** Severity mapping: `info` — позитивная находка (✅), `warning` — точка роста (📍), `critical` — критичный пробел (🔴)
- **D-11:** Wow-комментарии отображаются как отдельные message bubbles от Hermes (не floating status)
- **D-12:** Tone: как менеджер по маркетингу, который работает вместе с клиентом — не робот, не формальный отчёт
- **D-13:** Примеры wow-комментариев: «Ого, у вас главная страница не оптимизирована — теряете пациентов на первых секундах загрузки», «У конкурента доктор с 500K подписчиков в Instagram — серьёзное преимущество в привлечении аудитории»

### Report Page Generation (Fix HTML Layout)

- **D-14:** Canonical template approach: LLM генерирует только content (текст, данные), Python собирает HTML по фиксированной структуре из design-showcase-dual-theme.html
- **D-15:** Два файла: `report-template.html` (структура + CSS из design-showcase) и `generate_html_report.py` (рендеринг с Jinja2 или string formatting)
- **D-16:** Публикация в WordPress через REST API: `POST /wp-json/wp/v2/pages` с `status=publish`, slug pattern `/report/{client-slug}/`
- **D-17:** Dual theme support: data-theme атрибут, localStorage ключ `aim-theme`, toggle button в header
- **D-18:** Секции отчёта (10 из референса ИПХиК): Клиника (метрики), Конкуренты (карточки), Instagram врачей (ТОП-5), Контент-анализ, Whitefields (матрица), SEO, Реклама, Техаудит, Стратегия (5 направлений), Offer (что AIM может сделать)
- **D-19:** После завершения пресейла: Hermes отправляет `{"type": "report-ready", "url": "https://iamaim.ru/report/{client-slug}/"}` через SSE
- **D-20:** Frontend показывает красивый CTA: «Ваш отчёт готов 🎉 [Открыть отчёт]» с линком на опубликованную страницу

### Contact Collection Flow

- **D-21:** Диалоговый флоу: Hermes запрашивает контакты нативно в чате («Чтобы отправить вам отчёт, могу я узнать ваше имя и email?»)
- **D-22:** Используется существующий инструмент `collect_contact` из `AIM/hermes/app/tools/collect_contact.py`
- **D-23:** Timing: после завершения основного анализа, перед показом финального offer
- **D-24:** Поля: имя (обязательно), email (обязательно), телефон (опционально, если клиент даёт)
- **D-25:** Валидация на frontend: email regex, имя не пустое
- **D-26:** Сохранение в PostgreSQL через AIM API: `POST /api/leads` (уже существует)
- **D-27:** Если клиент отказывается — продолжаем без блокировки, но отмечаем в логах

### Services Sales Assistant

- **D-28:** LLM читает `/opt/data/services.md` (catalogue AIM услуг с ценами, описаниями, нишами)
- **D-29:** Semantic matching: после анализа LLM матчит находки (пробелы в SEO, контенте, Instagram, рекламе) с релевантными услугами AIM
- **D-30:** Offer generation: LLM создаёт персонализированное предложение с 3-5 конкретными услугами + ориентировочные цены
- **D-31:** Tone: консультативный, не агрессивный — «Мы можем помочь решить это с помощью...», не «Купите наш пакет X»
- **D-32:** Timing: после wow-commentary финальной стадии, перед выдачей ссылки на отчёт
- **D-33:** Структура offer message: «Ого, у вас тут дыры в [X] и [Y]. Мы можем предложить: 1) [Услуга A] — [цена] — [что даёт], 2) [Услуга B] — [цена] — [что даёт]. Хотите обсудить детали?»
- **D-34:** CTA: кнопка «Обсудить с менеджером» → `escalate_to_manager` tool → уведомление админу в Telegram

### Implementation Split

- **D-35:** 4 плана:
  - **09-01:** Progress streaming UI (frontend + SSE event handling)
  - **09-02:** Wow-commentary generation (LLM prompt engineering + new SSE event type)
  - **09-03:** Report page template + WordPress publishing (fix generate_html_report.py)
  - **09-04:** Contact collection + services sales assistant (dialog flow + offer matching)

### Claude's Discretion

- Точные CSS transitions и animations для progress UI
- Формат wow-комментариев (длина, структура message bubbles)
- Jinja2 template engine vs f-string formatting для HTML generation
- Semantic matching алгоритм для services (keyword-based vs LLM embedding similarity)
- Error handling для случаев, когда WordPress API недоступен или publish fails

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design System & Frontend
- `/var/www/iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html` — ЕДИНСТВЕННЫЙ канон дизайна AIM, dual theme reference (78KB on server)
- `/var/www/iamaim.ru/wp-content/themes/aim-theme/theme.css` — CSS-переменные, типографика, glass cards, dual theme
- `/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat.html` — текущий чат (нужно переработать SSE event handling)

### Backend Architecture
- `AIM/hermes/app/main.py` — FastAPI endpoints, SSE streaming, push_tool_progress() (line 87-130)
- `AIM/hermes/app/agent_wrapper.py` — AIAgent lifecycle, session persistence, prompt assembly
- `AIM/hermes/app/agent_wrapper_optimized.py` — mode-specific prompts (PRESALE, ACTIVE, ADMIN, SALES_ADMIN)
- `AIM/hermes/app/tools/collect_contact.py` — существующий инструмент для сбора контактов

### Report Generation (Broken — Needs Fix)
- `AIM/hermes/scripts/generate_html_report.py` — текущий генератор HTML (производит «полный крах вёрстки»)
- `/Users/mikhaileliseev/Downloads/ИПХиК (2).html` — референс отчёта (10 секций, 965 строк, 78KB) для style comparison

### Services & Business Logic
- `/opt/data/services.md` — catalogue услуг AIM (описания, цены, ниши) — должен быть на сервере, если нет — создать из актуальной инфы с iamaim.ru/pricing

### Project-Level
- `.planning/PROJECT.md` — Core value: полнота данных через 3-pass LLM orchestrator
- `.planning/REQUIREMENTS.md` §Test (TST-01..05) — Phase 7 requirements (reference для тестирования Phase 9)
- `.planning/ROADMAP.md` — Phase 9 entry с success criteria
- `CLAUDE.md` — SSH convention, deploy pattern, dual theme canon

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **SSE streaming infrastructure**: `chat_stream` endpoint (`main.py:312`) — уже работает, стримит события в real-time
- **Tool progress dispatcher**: `push_tool_progress(stage, message, competitor)` — thread-safe, можно вызывать из любого инструмента
- **Session management**: `agent_wrapper.py` — per-session locks (asyncio.Lock для web, threading.Lock для Telegram), agent caching (24h TTL)
- **Telegram progress pattern**: `main.py:66-84` — `_telegram_progress_lines` accumulator, можно переиспользовать логику для floating status в web
- **Contact collection tool**: `collect_contact.py` — уже регистрирован в tools registry, принимает имя, телефон, email
- **WordPress integration**: AIM backend имеет endpoints для публикации (`/api/wordpress/publish` — если нет, создать)

### Established Patterns
- **LLM-first orchestration**: LLM решает, какие инструменты вызывать — нет hardcoded pipeline, всё через SOUL.md + mode prompts
- **Tool handlers**: `handle_<tool_name>` async pattern, return JSON error strings (never raise exceptions)
- **Mode-specific prompts**: `get_mode_prompt(mode)` из `agent_wrapper.py:130` — собирает system prompt по режиму (PRESALE, ACTIVE, ADMIN, SALES_ADMIN)
- **Dual theme switching**: `localStorage` ключ `aim-theme`, `data-theme="light"|"dark"` атрибут на `<html>`, sun/moon SVG toggle
- **Glass cards**: `backdrop-filter: blur(20px) saturate(1.4)`, card-breathe animation, 1px border-radius (острые углы)

### Integration Points
- **Frontend → Hermes**: `https://iamaim.ru/wp-json/aim/v1/chat/stream` — SSE endpoint через WordPress REST API proxy
- **Hermes → AIM app**: `http://app:8000` — internal Docker network, все инструменты делают HTTP calls сюда
- **Hermes → WordPress**: `http://wordpress:80` (или через nginx proxy) — публикация страниц отчётов
- **Event flow**: User message → FastAPI `/api/chat/stream` → AIAgent → tool handlers → push_tool_progress() → SSE queue → frontend EventSource
- **Report persistence**: `/opt/data/memories/proposals/{client-slug}/proposal.html` — сохраняется локально, потом публикуется в WordPress

</code_context>

<specifics>
## Specific Ideas

- **Telegram-style streaming**: Пользователь хочет «как стриминг в телеграме там гермес это делает» — одно сообщение обновляется, не множество
- **Wow-эффект**: «оу у конкурента доктор с 500к подписчиков» — конкретные инсайты с эмоцией, не сухая статистика
- **Живой менеджер**: «гермес должен быть как живой человек и запрашивать контакты нативно» — диалоговый флоу, не форма
- **Продавец услуг**: «гермес должен знать что умеет aim и мы кожаные и должен сказать 0 ого у вас тут дыры в том и этом - мы можем предложить решить это с помощью наших инструментов за такие то деньги»
- **Фикс вёрстки**: «сейчас он делает их как захочет с изменением и иной раз полным крахом верстки» — canonical template approach обязателен

</specifics>

<deferred>
## Deferred Ideas

- **A/B тестирование разных UX-подходов** — backlog (измерить conversion после запуска Phase 9)
- **Multi-language поддержка отчётов** (English) — backlog
- **Voice input в чате** — backlog (уже есть в Telegram через AssemblyAI, можно портировать)
- **Real-time preview отчёта** во время генерации — backlog (сложность в частичном рендеринге)
- **Персонализированные шаблоны отчётов** по нише (стоматология vs косметология) — backlog
- **Интеграция с CRM** для автоматического создания сделок при collect_contact — backlog

</deferred>

---

*Phase: 9-Chat Pro — Website Chat UX Overhaul*
*Context gathered: 2026-06-27*
