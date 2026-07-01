# 07 — Divergence from Documentation

Расхождения между CLAUDE.md / SESSION.md / `.current-task` и **реальным состоянием** сервера. Документы врут в нескольких местах.

---

## 🚨 Главное противоречие

**CLAUDE.md и SESSION.md описывают проект, которого нет.** Это не мелкие расхождения — это **систематическое отставание документации от реальности**.

Причины (предположительно):
1. Документы писались "впрок" (что должно быть), а не "по факту" (что есть)
2. Deploys откатывались, но документы не обновлялись
3. Architecture pivots (HeadroomGuard → DeepSeek direct, v7 pipeline → 3-message format) не отражены
4. Интеграции (Phase 09, paperclip) частично откатаны

---

## 📋 Построчное расхождение с CLAUDE.md

### Секция "Project Overview"

| CLAUDE.md говорит | Реальность |
|---|---|
| "16 контейнеров" (через `docker-compose.yml`) | В compose описано 13 + paperclip (отдельно) = реально 15 + 1 |
| "Hermes (FastAPI + hermes-agent)" | ✅ правда |
| "aim-frontend (Next.js landing)" | Next.js есть, но landing — это WordPress. Frontend на `/chat-test` и т.д. |
| "Docker на Polish server 78.17.128.169 (`ssh aim`)" | ✅ правда |

### Секция "Hermes v5 — Full Coverage Reports"

CLAUDE.md описывает проект как "переработка души (SOUL.md), пайплайна и оркестрации AI-агента Hermes для производства полных отчётов пресейла".

| CLAUDE.md говорит | Реальность |
|---|---|
| "3-проходный цикл: сбор → анализ пробелов → допосбор + финальная сборка" | В коде `agent_wrapper.py` переписан на **3-сообщений формат ответа**, не 3-проходный цикл |
| "Воспроизводит успешный паттерн v1" | v1 упоминается только в исторических документах |
| "Метрика успеха: QC-чек-лист покрытия 10-20 пунктов" | QC-чеклист не найден в коде |

### Секция "Constraints"

| CLAUDE.md говорит | Реальность |
|---|---|
| "Runtime: Docker-контейнер aim-hermes, нельзя ломать работающий пресейл-поток" | ✅ поток работает (46 запросов за 24h) |
| "Модель: DeepSeek V4 Pro, стримы рвутся на ~120с" | `LLM_MODEL=deepseek-v4-pro` ✅, SSE deadline 600s (не 420s) |
| "Деплой: Только через docker cp + перезапуск gateway" | `deploy-hermes.sh` скрипт есть, но и `docker-compose build` тоже работает |
| "Без даунтайма" | ✅ uptime 2 дня |
| "Бюджет: 1-2 месяца" | — |

### Секция "AIM Agency Context"

| CLAUDE.md говорит | Реальность |
|---|---|
| "Работаем ТОЛЬКО в коммерческой медицине" | ✅ фильтр в competitor_matcher.py |
| "Только: ООО, АО, ЗАО, ИП — частные коммерческие клиники" | ✅ `_is_state_healthcare()` в коде |
| "Российский рынок: ФЗ-152 (не HIPAA/GDPR)" | ✅ `fz152_audit_log_*` таблицы есть |
| "Платёжки: ЮKassa/CloudPayments (не Stripe)" | В services/payment/ — есть, но конкретная платёжка не подтверждена |

### Секция "Что НЕ использовать (deprecated)"

CLAUDE.md:
- ❌ Магистры (SEO, Content, Ads, Analytics)
- ❌ CI Orchestrator (23 агента, 16 фаз)
- ❌ EventBus
- ❌ Obsidian vaults для агентов (кроме teacher и architect)
- ❌ `.planning/`

**Реальность:** все эти компоненты **физически присутствуют в коде**:
- `src/aim/magisters/` — 19 файлов
- `src/aim/subagents/` — 133 файла (включая ci_orchestrator с 23 агентами)
- `src/aim/orchestration/shared_event_bus.py` — EventBus код
- `obsidian/` — 30 vaults (7.1 MB), включая ci-* которые CLAUDE.md явно говорит не использовать
- `.planning/` — 3.1 MB, физически есть

Документация и код **не совпадают**. Документация правильная (это deprecated), но код не почищен.

### Секция "Инструменты Hermes (17 штук)"

CLAUDE.md перечисляет **15 aim-operations tools + 11 hermes-debug = 26 всего**.

**Реальность:** зарегистрировано **67 tools**:
- aim-operations: ~42 (включая run_* для 14 фаз scout)
- hermes-debug: ~25 (включая 9 firecrawl variants)

CLAUDE.md устарел на 2-3×. В нём перечислены только базовые tools, но не добавлены:
- `run_full_scout`, `run_aim_scout`, `run_aim_scout`
- `run_tech_seo_audit`
- `run_content_gaps`, `run_doctor_dossiers`, `run_hh_analysis`, `run_smi_mentions`
- `run_instagram_content`, `run_review_platforms`
- `run_geo_audit`
- `finalize_research`, `orchestrate`
- `generate_html_report`, `post_report`, `publish_scout_report`, `read_report_reference`
- `perplexity_search`, `perplexity_deep_analyze`
- Все firecrawl variants (9 шт)
- `crawlee_scrape`, `crawlee_search`, `scrapy_crawl`
- `bitrix_scrape`
- `search_telegram_chats`, `send_telegram_message`, `send_telegram_file`
- `restart_myself`, `pip_install`

### Секция "Architecture: LLM-First Tool Orchestration"

CLAUDE.md:
> "AIM — это набор инструментов (tools), которые LLM (Hermes) вызывает по своему усмотрению. Никакой хардкод-оркестрации. Модель решает, что и когда вызывать."

**Реальность:** ✅ подтверждено. Hermes сам решает какие tools вызывать.

> "Клиент пишет в чат на iamaim.ru → Hermes получает сообщение + tools → LLM решает"

**Реальность:** ✅ подтверждено smoke test'ом.

### Секция "Смена модели"

CLAUDE.md: "Меняется одна переменная: LLM_MODEL в .env. Всё остальное работает без изменений."

**Реальность:** ✅ правда.

### Секция "Design System"

CLAUDE.md ссылается на `design-showcase-dual-theme.html`.

**Реальность:** файл существует (102 KB), доступен по URL, метрики цветов и шрифтов соответствуют описанию.

### Секция "Hermes Backup"

CLAUDE.md: "Локальный архив: `hermes-backup-20260618/`"

**Реальность:** мы **удалили** эту директорию в коммите `017acba` (240 files cleanup). В CLAUDE.md до сих пор ссылается.

### Секция "Project Structure"

CLAUDE.md описывает:
```
src/meai/           # Framework (переиспользуемый)
├── core/, agents/, events/, memory/, storage/
AIM/                # Application
├── src/aim/, hermes/, obsidian/, frontend/
└── ...
```

**Реальность:** ✅ структура такая, **но `meai` есть в двух местах** (дубликат):
- `/opt/aim/src/meai`
- `/opt/aim/AIM/src/meai`

CLAUDE.md этого не упоминает.

### Секция "Auto-Commit Before Deploy Rule"

CLAUDE.md:
> "КРИТИЧНО: Любые изменения в `AIM/hermes/` или `AIM/theme/` ОБЯЗАТЕЛЬНО коммитятся перед деплоем на сервер."

**Реальность:**
- ✅ `scripts/auto-commit-deploy.sh` существует
- ✅ `.git/hooks/pre-push` есть
- ❌ Backup-файлы `main.py.backup-phase09-*` (2 шт) не были удалены после деплоя
- ❌ Изменения в WordPress теме (через `docker exec`) вообще не попадают в git

### Секция "Teacher Agent Rule"

CLAUDE.md описывает Teacher Agent как "Chief Learning Officer системы".

**Реальность:**
- `src/aim/teacher/` существует (388 KB)
- В Hermes tools нет `teach_*` инструментов
- Нет цикла обучения (описанного в CLAUDE.md "каждые 2-4 недели")
- `obsidian/teacher/` vault есть, но активность не обнаружена

Teacher Agent — **формально существует, фактически не работает**.

---

## 📋 Построчное расхождение с SESSION.md

SESSION.md от 2026-06-28 — "Phase 09 Deployed". Содержит много устаревшего.

### Секция "Текущий фокус"

SESSION.md:
> "Phase 09 развёрнут и готов к тестированию"

**Реальность:** ❌ `hermes-chat-pro.html` возвращает 404. Не развёрнут.

SESSION.md:
> "✅ Hermes backend: report_url в finish event (main.py модифицирован, backup создан)"

**Реальность:**
- Backup-файлы есть (`main.py.backup-phase09-*` × 2)
- Сам main.py: проверить, есть ли там report_url в finish event
- Покрытие не подтверждено

SESSION.md:
> "✅ WordPress frontend: hermes-chat-pro.html с Phase Tracker (1020 строк)"

**Реальность:** файла нет на сервере.

SESSION.md:
> "✅ WordPress backend: aim-pro-endpoints.php с fallback REST API (172 строки)"

**Реальность:** файл `aim-pro-endpoints.php` существует в теме, длина 172 строки ✅.

SESSION.md:
> "✅ functions.php обновлён для подключения endpoints (backup создан)"

**Реальность:** `functions.php.bak` существует, основной functions.php presumably обновлён.

SESSION.md:
> "✅ Hermes контейнер перезапущен (04:56:47 UTC)"

**Реальность:** aim-hermes uptime 13h (с ~22:00 UTC 29 июня). Перезапуск был, но позже указанного.

### Секция "Текущая конфигурация production"

SESSION.md:
```yaml
HeadroomGuard:
  container: aim-headroom-proxy
  port: 8787
  upstream: https://api.z.ai/api/coding/paas/v4
  mode: optimize
  compress_tools: false
  keep_turns: 2

Hermes:
  container: aim-hermes
  OMNIROUTE_URL: http://headroom-proxy:8787/v1
  LLM_MODEL: glm-5
```

**Реальность (полное расхождение):**
- Контейнера `aim-headroom-proxy` НЕТ в `docker ps -a`
- `OMNIROUTE_URL=https://api.deepseek.com/v1` (прямой DeepSeek, не Z.AI, не headroom)
- `LLM_MODEL=deepseek-v4-pro` (не glm-5)
- HEADROOM_* env переменных нет

SESSION.md:
> "SOUL.md: 104KB (1410 строк)"

**Реальность:** `/opt/data/SOUL.md` — 106 KB, 1411 строк. ✅ примерно совпадает (но в образе 47 KB / 760 строк!).

SESSION.md:
> "AIM tools: 33 зарегистрировано"

**Реальность:** 67 tools зарегистрировано. В 2× больше.

### Секция "Что НЕ делать"

SESSION.md:
> "❌ Менять HEADROOM_COMPRESS_TOOLS на true (сломает tool calling)
> ❌ Удалять HeadroomGuard без тестирования rollback плана
> ❌ Деплоить без backup текущей конфигурации"

**Реальность:** Эти предупреждения **не актуальны** — HeadroomGuard'а нет. Удалять нечего.

---

## 📋 `.current-task` — полностью не актуален

```
$ cat .current-task
Phase 09 deployed. Test hermes-chat-pro.html end-to-end: https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat-pro.html
```

**Реальность:**
- URL возвращает 404
- Файла `hermes-chat-pro.html` нет ни в Docker volume, ни в theme
- Тестировать невозможно

---

## 📋 Roadmap из CLAUDE.md "Hermes v5 — Full Coverage Reports"

CLAUDE.md описывает:
```
Проход 1: СБОР — LLM вызывает инструменты по ситуации
Проход 2: ГЭП-АНАЛИЗ — LLM сравнивает собранное с чек-листом покрытия
Проход 3: ДОПОСБОР + СБОРКА — LLM заполняет пробелы, генерирует отчёт
```

**Реальность:** в коде этого НЕТ. Вместо этого в `agent_wrapper.py`:
- PRESALE mode prompt переписан на **3-сообщений формат ответа** (контраст → 3 точки роста с ценой → отчёт)
- Никаких "3 проходов" в коде не реализовано
- Pipeline v7 (которая могла бы это делать) — deprecated, не используется

CLAUDE.md описывает **будующее**, а не текущее.

---

## 📋 SKILL.md для aim-intel, aim-scout, impeccable

CLAUDE.md описывает 3 project skills:
- `aim-intel` — "Загрузка конкурентной разведки на сервер AIM"
- `aim-scout` — "Глубокая конкурентная разведка: 16 фаз сбора данных"
- `impeccable` — "frontend design improvement"

**Реальность:** эти skills доступны **в Claude Code** (только на машине разработчика), но **не на сервере**. На сервере в `~/.claude/skills/` их нет — это локальная разработка.

---

## 🎯 Причины расхождений (предположения)

1. **HeadroomGuard был развёрнут, потом откатан** — но SESSION.md не обновили
2. **Phase 09 была развёрнута, потом откатана** — backup-файлы остались, SESSION.md не обновили
3. **v7 pipeline был переписан на 3-сообщений формат** — CLAUDE.md не обновили
4. **Tools количество выросло** — CLAUDE.md не обновили
5. **Paperclip добавлен** — CLAUDE.md не описан
6. **`.venv` и `node_modules` накопились** — в .gitignore не попадают

---

## 🚨 Рекомендации по документации

1. **Обновить CLAUDE.md:**
   - Количество tools: 67 (не 17)
   - Контейнеры: 16 (с paperclip)
   - Убрать секцию Hermes Backup (удалена)
   - Обновить Project skills список (aim-intel/aim-scout/impeccable — это Claude Code skills, не серверные)
   - Секция "Что НЕ использовать" — заменить на "Что УДАЛИТЬ" с конкретным планом

2. **Обновить SESSION.md:**
   - Полностью переписать "Текущий фокус"
   - Удалить секцию HeadroomGuard (или пометить как "pause/uninstalled")
   - Удалить "Текущая конфигурация production" (или переписать с реальными env vars)
   - "Что НЕ делать" — убрать headroom-предупреждения

3. **Обновить `.current-task`:**
   - Заменить на актуальную задачу (не "Phase 09 test")

4. **Внедрить правило:** "сначала обновить SESSION.md, потом deploy". Любые изменения на сервере → синхронное обновление документов.

---

## 🟢 Что совпадает с документацией

Не всё плохо. Эти части CLAUDE.md **корректны**:
- ✅ LLM-first architecture (Hermes вызывает tools сам)
- ✅ Бизнес-логика (только коммерческая медицина)
- ✅ ФЗ-152 compliance
- ✅ Design system reference (`design-showcase-dual-theme.html`)
- ✅ Docker compose основная структура
- ✅ Greek naming conventions
- ✅ Локальная разработка workflow
- ✅ Auto-commit правило (но не всегда соблюдается)
- ✅ Stack (Python 3.11, FastAPI, PostgreSQL, Redis, Docker, Next.js)
- ✅ Deploy target (Polish server)
- ✅ Naming conventions (handle_<tool>, _lowercase, etc.)

---

*Этот документ — выявленные расхождения. После рефакторинга нужно обновить CLAUDE.md и SESSION.md.*
