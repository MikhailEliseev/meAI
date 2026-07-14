# Phase 3: Перенос тулов + tool-calling — Context

**Gathered:** 2026-07-14
**Status:** Ready for planning (Wave 1 first)
**Source:** Backup разведка + Spec раздел 4.3 + Phase 1/2 results

<domain>
## Phase Boundary

Модель `glm-5.2` получает возможность ВЫЗЫВАТЬ инструменты через нативный OpenAI tool-calling (`tools=` / `tool_calls`). Переносятся тулы из бэкапа старого hermes. Цель — модель может вызвать любой тул по описанию.

**Wave 1 (эта итерация):** registry + tool-calling цикл + 6 HTTP-тулов (Perplexity ×3, Apify, Firecrawl, find_competitors-подключение).
**Wave 2 (следующая):** run_pagespeed (Playwright) + generate_html_report (WordPress) + 2 прокси-тула (ci_analysis, seo_audit).

</domain>

<decisions>
## Implementation Decisions (locked)

### Свой registry (НЕ hermes-agent)
`tools.registry` — чужой код (часть hermes-agent==0.14.0). v2 не использует hermes-agent → пишем свой минимальный registry: `app/tools/registry.py`, dict `name → {schema, handler, is_async}`. Методы `register()`, `get_openai_tools()` (возвращает список schemas для `tools=`), `get_handler(name)`, `execute(name, args)`.

### Tool-calling цикл в main.py
Расширить `/api/chat/stream`:
1. Вызвать LLM с `tools=registry.get_openai_tools()`, `stream=False` (для tool_calls нужен non-streaming первый вызов).
2. Если `response.choices[0].message.tool_calls` → стримить SSE `tool-progress` → выполнить handler → добавить `tool` role message → повторный LLM-вызов (streaming) → стримить ответ.
3. Если нет tool_calls → стримить ответ как в Phase 2.

### Perplexity-клиент общий
`app/lib/perplexity.py` — единый `async perplexity_search(query, model="sonar-pro")` через `openai.AsyncClient(base_url="https://api.perplexity.ai")`. Заменяет дублирование в 4 местах.

### Зависимости (Wave 1)
Добавить в requirements: `openai` (уже есть), `pymysql` (Wave 2). Wave 1 НЕ добавляет playwright/lighthouse (это Wave 2).

### Ключи
- PERPLEXITY_API_KEY — env (есть в .env.production)
- FIRECRAWL — через key_bank (14 ключей в env FIRECRAWL_API_KEY_01..14)
- Apify — `/opt/data/apify_keys.json` (mount общего файла :ro)

</decisions>

<canonical_refs>
- Backup: `~/Desktop/Dev/meAI_1-backups/extracted/aim-chat-system-20260714-133205/hermes-container-code/app/tools/` — 7 тулов + 5 зависимостей
- Разведка: ключи подтверждены (PERPLEXITY в env, FIRECRAWL 14 шт, apify dict)
- Spec раздел 4.3 — таблица 10 тулов
</canonical_refs>

<deferred>
- run_pagespeed (Wave 2 — Playwright тяжёлый)
- generate_html_report (Wave 2 — Phase 5 нужнее)
- run_ci_analysis, run_seo_audit (Wave 2 — прокси к aim-app)
- Суммаризация истории (Phase 4+)
- mode_gate фильтрация (Phase 4+ — сейчас все тулы доступны)
</deferred>
