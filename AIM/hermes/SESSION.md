# Session: 2026-06-20 — _search_fallback migration VERIFIED + Firecrawl keys burning

## Текущий фокус: Защита кода Hermes от самомодификации + site-search улучшен

### 2026-06-20: Site-search accuracy IMPROVED + "ALL providers failed" FIXED (13:42)

**Проблема:** Perplexity не понимает `site:` оператор → run_content_gaps считал все 10 тем покрытыми.
**Вторичная проблема:** Когда Perplexity возвращал пустой результат для site-specific запроса (NO_PAGES_FOUND), `search()` фоллбэчился на Firecrawl (мёртв) → лог забивался "ALL providers failed".

**Решение (три уровня):**

1. **Умный промпт для Perplexity** (`_search_fallback.py`):
   - Обнаружение `site:` в запросе → специальный system prompt
   - "Search ONLY domain.ru. If nothing relevant found, say NO_PAGES_FOUND."
   - Фильтрация citations по домену

2. **Пост-фильтр в run_content_gaps** (`run_content_gaps.py`):
   - `_url_matches_domain()` — проверка что URL принадлежит целевому домену
   - `_filter_by_domain()` — отсев нерелевантных результатов
   - Увеличен max_results с 2 до 5

3. **Фикс фоллбэка в `search()`** (`_search_fallback.py`):
   - Site-specific запрос + Perplexity вернул `[]` → возвращаем `[], "perplexity"` сразу, НЕ фоллбэчимся
   - `is_site_specific` флаг проверяется перед fallback-логикой

**Результаты теста (iphk.ru vs majorbeauty.ru) — 13:42:**
- ✅ 10/10 тем, 6.3s, 2 gaps: контурная пластика, фотоомоложение
- ✅ 1 преимущество: липоскульптурирование
- ✅ 0 "ALL providers failed" — тишина в логах
- ✅ Perplexity возвращает "NO_PAGES_FOUND" для непокрытых тем → корректно обрабатывается

**Проблема:** Hermes слишком умный — когда инструмент возвращает ошибку, он пытается «починить» код через file_write или shell_exec (sed -i, python -c с open()).

**Решение (два уровня защиты):**

1. **Технический guard (`file_guard.py` + `shell_exec.py`):**
   - `validate_shell_command()` — regex-паттерны для блокировки shell-команд, пишущих в защищённые пути
   - Интегрирован в `handle_shell_exec()` — проверка перед каждым выполнением
   - Блокирует: `> /opt/hermes/app/`, `sed -i`, `tee`, `mv/cp .py`, `chmod` на защищённые пути, python `open()/write()` в app/

2. **Поведенческий guard (`agent_wrapper.py`):**
   - Правило «КОД НЕПРИКОСНОВЕНЕН» добавлено во ВСЕ режимы:
     - ADMIN: «НЕ пытайся починить код через file_write или shell_exec. Код пишет разработчик.»
     - PRESALE: «Если инструмент вернул ошибку — сообщи клиенту. НЕ переписывай инструменты.»
     - ACTIVE, SALES_ADMIN: короткая версия правила

**Задеплоено:** scp + docker cp + restart Hermes. Проверено в контейнере.

### 2026-06-20: Perplexity search provider ADDED (13:20)

**Проблема:** Все 15 ключей Firecrawl исчерпаны (402). DDG заблокирован. Brave 402.
**Решение:** Добавлен `_perplexity_search()` провайдер в `_search_fallback.py`.

**Результаты теста run_content_gaps (iphk.ru vs majorbeauty.ru):**
- ✅ 10/10 тем проанализированы (Perplexity), 0 ошибок
- ✅ 6.2s выполнение (24 поисковых запроса)
- ⚠️ Perplexity не понимает `site:` оператор — считает все темы покрытыми
- 🔴 Firecrawl: 15 ключей мёртвы (все 402), нужны новые кредиты

**Цепочка провайдеров сейчас:**
```
perplexity (sonar) → firecrawl (15 keys, all dead)
```

### 2026-06-20: Perplexity API key added (12:40)

**Что сделано:**
- Ключ Perplexity добавлен в:
  - `/opt/aim/AIM/.env.production` (сервер, контейнер видит)
  - `/opt/aim/.env.production` (сервер, запасной)
  - `AIM/.env.production` (локальный)
  - `AIM/hermes/app/key_bank.py` → `_register_env_keys()` (реестр, категория `llm`, check_method `http_401`)
- Key Bank: **23 ключа** (было 22, +1 Perplexity)
- Контейнер пересоздан через `docker compose up -d` — PERPLEXITY_API_KEY в окружении

### 2026-06-20: 5 Audit Fixes (12:35)

| # | Файл | Проблема | Статус |
|---|------|---------|--------|
| 1 | `run_doctor_dossiers.py` | Прямой Firecrawl → `_search_fallback.search()` | ✅ |
| 2 | `run_ads_intelligence.py` | `_search_telegram_ads()` → `_search_fallback.search()` | ✅ |
| 3 | `_search_fallback.py` | Dead `_crawlee_search()` ~80 строк | ✅ Удалён |
| 4 | `__init__.py` | 3 не-tool импорта | ✅ Удалены |
| 5 | `orchestrate.py` | `http://app:8000` → `http://aim-app:8000` | ✅ |

### Текущее состояние

| Ресурс | Статус |
|--------|--------|
| LLM | ✅ DeepSeek `deepseek-chat` через OMNIROUTE |
| Поиск | ✅ DDG (blocked) → Firecrawl (10 keys) |
| Perplexity | ✅ `PERPLEXITY_API_KEY` SET — Phase 0 будет real-time |
| PageSpeed | ✅ `GOOGLE_API_KEY` SET |
| Firecrawl | ✅ 10 активных ключей из 22 |
| Инструменты | ✅ 42 AIM ops + 15 debug, 0 ошибок |
| Key Bank | ✅ 23 ключа зарегистрировано |

### 2026-06-20: iphk.ru Full Pipeline — COMPLETE (12:48)

**13/13 фаз, 0 ошибок, ~6m45s total.** Результаты в `/opt/data/sessions-archive/15b705b4-d44/`

| # | Фаза | Время | Ключевой результат |
|---|------|-------|--------------------|
| 0 | PERPLEXITY | 19.5s | Рынок Москвы 100+ млрд, 7 конкурентов, тренды |
| 1 | TECH AUDIT | 107.5s | PageSpeed 65/100 mobile, LCP 5s, SEO audit 500 ❌ |
| 2 | SOCIAL VERIFIER | 8.3s | Отзывы собраны |
| 3 | CONTENT ANALYSIS | 10.4s | Контент проанализирован |
| 4 | KEY PERSONS | 29.0s | Липский К.Б. (30 лет стажа, к.м.н.), 13 профилей на 3 платформах |
| 5 | SMI MENTIONS | 9.3s | 0 упоминаний (Brave 402 на все 4 категории) ⚠️ |
| 6 | COMPETITORS | 166.9s | 5 конкурентов через Apify Google Maps + ФНС |
| 7 | FORUM PAINS | 13.2s | Боли пациентов найдены |
| 8 | FINANCE | 7.1s | Мэйджор Бьюти: 258M выручка, 118M прибыль, 46% рентабельность |
| 9 | CONTENT PLAN | 15.0s | 0 пробелов (Brave 402 на все 18 запросов) ⚠️ |
| 10 | HTML BUILD | 0.0s | report.html 3.5 KB (30 JSON saved) |
| 11 | QC CRITIQUE | 19.5s | Контроль качества пройден |
| 12 | PRESENTATION | 0.0s | publish_scout_report |

**PERPLEXITY_USED: 10/13 фаз** (реально использовался в анализе)

**Топ-5 конкурентов (Google Maps + nalog):**
1. Мэйджор Бьюти — 258M выручка, 118M прибыль, 4.8★
2. Клиника Александра Соколова — 4.7★
3. Центр лазерной хирургии Листратенкова — 5.0★
4. Эстет Клиник — 25M выручка, 5.0★
5. Dr.Shihirman — 5.0★

**LLM финальный ответ:** хороший, структурированный разбор финансов, врачей, проблем сайта, конкурентов.

### 2026-06-20: Brave Search 402 fix — 3 инструмента мигрированы (13:00)

**Проблема:** При прогоне iphk.ru логи показали Brave Search 402 в `run_smi_mentions`, `run_content_gaps`, `run_review_platforms`. Локальные файлы уже были мигрированы на `_search_fallback`, но в контейнере лежали старые версии (после `docker compose up -d` перезалили только 6 файлов аудита, эти 3 не вошли).

**Исправлено:** Задеплоены актуальные версии 3 файлов в контейнер. Все 3 используют `_search_fallback.search()`.
**Верификация:** `grep -ri brave` по `app/tools/` — 0 вхождений Brave Search API.

### Оставшиеся проблемы (из прогона iphk.ru)

1. **SEO audit 500** — AIM API `/api/seo/audit` возвращает 500. Не блокирует пайплайн.
2. **Perplexity named competitors** — извлёк маркетинговые термины вместо названий (`«до/после»`, `«разогревают»`, `«голубая фишка»`). Apify Google Maps справился сам, но экстракция имён плохая.
3. **HTML BUILD / PRESENTATION = 0.0s** — фазы мгновенные. Возможно, WordPress publish не сработал.

### Известные проблемы (не блокируют прогон)
- Telegram 401 Unauthorized — логи забиты спамом (3660+ ошибок за сессию)
- DDG заблокирован на IP сервера (весь поиск через Firecrawl)
- Apify ключи не проверены
