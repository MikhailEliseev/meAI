# Phase 3 (Wave 1): Перенос тулов + tool-calling — Summary

**Phase:** 03-tools-migration (Wave 1 of 2)
**Completed:** 2026-07-14
**Status:** ✅ Wave 1 COMPLETE — tool-calling работает, 7 тулов доступны модели

---

## Что сделано

Модель `glm-5.2` теперь сама **вызывает инструменты** через нативный OpenAI tool-calling. Перенесены 6 тулов + подключён find_competitors из Phase 1. Tool-calling цикл: модель → tool_calls → выполнить handler → результат обратно → модель → финальный streaming ответ.

**Главное доказательство** — запрос «Найди конкурентов для stomus.ru»:
1. Модель вызвала `quick_overview` (Perplexity) → узнала что stomus.ru это группа брендов
2. Модель вызвала `find_competitors` → получила 3 реальных конкурента
3. Выдала **842 токена** связного ответа: «Базовая разведка: stomus.ru... специализация...»

7 тулов: `find_competitors`, `quick_overview`, `perplexity_search`, `run_smi_mentions`, `run_review_platforms`, `run_instagram_content`, `run_ads_intelligence`.

---

## Доказательства (evidence)

### Tool-calling цикл (TOLS-01..12)
Логи: `chat_with_tools turn=0 tools=7 msgs=2` → tool_calls → `turn=1` → streaming ответ. SSE-события `tool-progress` (start/done) + `text-delta` + `finish`.

### 7 тулов зарегистрированы
`register_all: 7 tools — ['find_competitors', 'quick_overview', 'perplexity_search', 'run_smi_mentions', 'run_review_platforms', 'run_instagram_content', 'run_ads_intelligence']`

### Ключи работают
- PERPLEXITY_API_KEY: SET (Perplexity-тулы доступны)
- FIRECRAWL: 14 ключей в key_bank с ротацией
- apify_keys.json: смонтирован `/opt/data/apify_keys.json:ro`

### Регрессия Phase 1+2
health ✅, find_competitors direct ✅, chat «привет» (81 токен) ✅

---

## Архитектурные решения

1. **Свой registry** (`app/tools/registry.py`) — не тянем hermes-agent. ~90 строк: `register()`, `get_openai_tools()`, `execute()`.
2. **Общий Perplexity-клиент** (`app/lib/perplexity.py`) — замена дублирования в 4 местах старого кода.
3. **key_bank'и** (`app/lib/firecrawl_key_bank.py`, `apify_client.py`) — ротация ключей с exhausted-персистенцией.
4. **Tool-calling в llm.py** — `chat_with_tools()`: до 5 раундов tool-calling, non-streaming для разбора tool_calls + streaming для финального ответа.

## Найденные грабли (исправлены)

- **`${PERPLEXITY_API_KEY:-}` в compose** → интерполяция даёт пусто → перекрывает env_file. Решение: убрать из `environment:`, пусть env_file даёт значение (та же грабля что OMNIROUTE_URL в Phase 2).
- **apify_keys.json** нужен mount: `/opt/aim/AIM/data/apify_keys.json:/opt/data/apify_keys.json:ro`.

---

## Артефакты

| Файл | Назначение |
|---|---|
| `app/tools/registry.py` | свой минимальный registry (register/get_openai_tools/execute) |
| `app/tools/__init__.py` | register_all() — регистрирует 7 тулов при startup |
| `app/lib/perplexity.py` | общий Perplexity-клиент |
| `app/lib/firecrawl_key_bank.py` | ротация 14 Firecrawl-ключей |
| `app/lib/apify_client.py` | загрузка/ротация Apify-ключей |
| `app/tools/perplexity_tools.py` | 4 Perplexity-тула |
| `app/tools/run_instagram_content.py` | Instagram через Apify |
| `app/tools/run_ads_intelligence.py` | Ads через Firecrawl |
| `app/llm.py` | +chat_with_tools() (tool-calling цикл) |
| `app/main.py` | /api/chat/stream использует chat_with_tools, SSE tool-progress |

---

## Что осталось (Wave 2)

- `run_pagespeed` — Playwright + lighthouse (тяжёлый образ ~1.5GB)
- `generate_html_report` — WordPress DB (для Phase 5)
- Прокси-тулы: `run_ci_analysis`, `run_seo_audit` (к aim-app)

Wave 2 делается когда понадобится (Phase 4/5).

---

*Phase 03 Wave 1 — COMPLETE*
